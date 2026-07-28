"""
Rate Limiting Tests

Test suite for the rate limiting functionality.

Run with: pytest tests/test_rate_limiting.py -v
"""

import asyncio
import time
import pytest
from fastapi import Request, FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

# Import rate limiter components
from rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    rate_limit,
    check_rate_limit_manual,
    RateLimitMiddleware,
)


@pytest.fixture
def test_config():
    """Create a test configuration"""
    config = RateLimitConfig()
    config.enabled = True
    config.redis_url = "redis://localhost:6379/15"  # Use test database
    config.fail_open = True
    config.limits = {
        "auth": (5, 60),  # 5 per minute
        "admin": (100, 60),  # 100 per minute
        "read": (200, 60),  # 200 per minute
        "write": (50, 60),  # 50 per minute
    }
    return config


@pytest.fixture
async def rate_limiter(test_config):
    """Create and initialize rate limiter"""
    limiter = RateLimiter(test_config)
    await limiter.initialize()
    yield limiter
    await limiter.close()


@pytest.fixture
def mock_request():
    """Create a mock request object"""
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "192.168.1.100"
    request.headers = {}
    return request


class TestRateLimitConfig:
    """Test rate limit configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = RateLimitConfig()
        assert config.enabled is True
        assert config.redis_url == "redis://unicorn-redis:6379/0"
        assert config.strategy in ["sliding_window", "token_bucket"]

    def test_parse_limit(self):
        """Test limit string parsing"""
        config = RateLimitConfig()

        # Test different formats
        assert config._parse_limit("5/minute") == (5, 60)
        assert config._parse_limit("100/hour") == (100, 3600)
        assert config._parse_limit("10/second") == (10, 1)
        assert config._parse_limit("1000/day") == (1000, 86400)

    def test_parse_invalid_limit(self):
        """Test invalid limit string handling"""
        config = RateLimitConfig()
        # Should return default
        count, seconds = config._parse_limit("invalid")
        assert count == 100
        assert seconds == 60


class TestRateLimiter:
    """Test rate limiter functionality"""

    @pytest.mark.asyncio
    async def test_initialization(self, test_config):
        """Test rate limiter initialization"""
        limiter = RateLimiter(test_config)
        await limiter.initialize()
        assert limiter._initialized is True
        await limiter.close()

    @pytest.mark.asyncio
    async def test_get_key(self, rate_limiter):
        """Test Redis key generation"""
        key = rate_limiter._get_key("192.168.1.100:user123", "read")
        assert "ratelimit:read:192.168.1.100:user123" in key

    @pytest.mark.asyncio
    async def test_get_identifier(self, rate_limiter, mock_request):
        """Test identifier generation"""
        # IP only
        identifier = rate_limiter.get_identifier(mock_request)
        assert identifier == "192.168.1.100"

        # IP + user ID
        identifier = rate_limiter.get_identifier(mock_request, "user123")
        assert identifier == "192.168.1.100:user123"

    @pytest.mark.asyncio
    async def test_get_identifier_with_proxy(self, rate_limiter, mock_request):
        """Test identifier with X-Forwarded-For header"""
        mock_request.headers = {"X-Forwarded-For": "10.0.0.5, 192.168.1.100"}
        identifier = rate_limiter.get_identifier(mock_request)
        assert identifier == "10.0.0.5"

    @pytest.mark.asyncio
    async def test_sliding_window_allow(self, rate_limiter):
        """Test sliding window allows requests within limit"""
        key = "test:read:client1"

        # Should allow up to limit
        for i in range(5):
            allowed, current, retry_after = await rate_limiter._check_sliding_window(
                key, 5, 60
            )
            assert allowed is True
            assert retry_after == 0

    @pytest.mark.asyncio
    async def test_sliding_window_deny(self, rate_limiter):
        """Test sliding window denies requests exceeding limit"""
        key = "test:read:client2"

        # Fill up the limit
        for i in range(5):
            await rate_limiter._check_sliding_window(key, 5, 60)

        # Next request should be denied
        allowed, current, retry_after = await rate_limiter._check_sliding_window(
            key, 5, 60
        )
        assert allowed is False
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_sliding_window_reset(self, rate_limiter):
        """Test sliding window resets after time period"""
        key = "test:read:client3"

        # Use short window for testing
        window = 2  # 2 seconds

        # Fill up the limit
        for i in range(3):
            await rate_limiter._check_sliding_window(key, 3, window)

        # Should be denied
        allowed, _, _ = await rate_limiter._check_sliding_window(key, 3, window)
        assert allowed is False

        # Wait for window to expire
        await asyncio.sleep(window + 0.5)

        # Should be allowed again
        allowed, _, _ = await rate_limiter._check_sliding_window(key, 3, window)
        assert allowed is True

    @pytest.mark.asyncio
    async def test_token_bucket_allow(self, rate_limiter):
        """Test token bucket allows requests"""
        rate_limiter.config.strategy = "token_bucket"
        key = "test:bucket:client1"

        # Should allow up to capacity
        for i in range(5):
            allowed, tokens, retry_after = await rate_limiter._check_token_bucket(
                key, 10, 60
            )
            assert allowed is True
            assert retry_after == 0

    @pytest.mark.asyncio
    async def test_token_bucket_deny(self, rate_limiter):
        """Test token bucket denies when empty"""
        rate_limiter.config.strategy = "token_bucket"
        key = "test:bucket:client2"

        # Drain all tokens
        for i in range(10):
            await rate_limiter._check_token_bucket(key, 10, 60)

        # Should be denied
        allowed, tokens, retry_after = await rate_limiter._check_token_bucket(
            key, 10, 60
        )
        assert allowed is False
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_disabled(self, test_config):
        """Test rate limiting when disabled"""
        test_config.enabled = False
        limiter = RateLimiter(test_config)

        allowed, metadata = await limiter.check_rate_limit("client1", "read")
        assert allowed is True
        assert metadata == {}

    @pytest.mark.asyncio
    async def test_check_rate_limit_admin_bypass(self, rate_limiter):
        """Test admin bypass functionality"""
        rate_limiter.config.admin_bypass = True

        allowed, metadata = await rate_limiter.check_rate_limit(
            "admin1", "write", is_admin=True
        )
        assert allowed is True
        assert metadata.get("bypassed") is True

    @pytest.mark.asyncio
    async def test_check_rate_limit_no_limit_category(self, rate_limiter):
        """Test category with no limit configured"""
        allowed, metadata = await rate_limiter.check_rate_limit(
            "client1", "health"
        )
        assert allowed is True
        assert metadata == {}

    @pytest.mark.asyncio
    async def test_check_rate_limit_metadata(self, rate_limiter):
        """Test metadata returned by check_rate_limit"""
        identifier = "client1"
        category = "auth"

        allowed, metadata = await rate_limiter.check_rate_limit(identifier, category)

        assert "limit" in metadata
        assert "window" in metadata
        assert "current" in metadata
        assert "remaining" in metadata
        assert "reset" in metadata

        assert metadata["limit"] == 5
        assert metadata["window"] == 60


class TestRateLimitDecorator:
    """Test rate limit decorator"""

    @pytest.mark.asyncio
    async def test_decorator_with_request(self, rate_limiter, mock_request):
        """Test decorator with request argument"""

        @rate_limit("read")
        async def test_endpoint(request: Request):
            return {"status": "ok"}

        # Should work
        result = await test_endpoint(mock_request)
        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_decorator_without_request(self):
        """Test decorator without request argument"""

        @rate_limit("read")
        async def test_endpoint():
            return {"status": "ok"}

        # Should work (skip rate limiting)
        result = await test_endpoint()
        assert result == {"status": "ok"}


class TestManualCheck:
    """Test manual rate limit checks"""

    @pytest.mark.asyncio
    async def test_manual_check_allowed(self, rate_limiter, mock_request):
        """Test manual check allows request"""
        # Should not raise exception
        await check_rate_limit_manual(mock_request, "read")

    @pytest.mark.asyncio
    async def test_manual_check_denied(self, rate_limiter, mock_request):
        """Test manual check denies request"""
        from fastapi import HTTPException

        # Fill up limit
        identifier = rate_limiter.get_identifier(mock_request)
        for i in range(5):
            await rate_limiter.check_rate_limit(identifier, "auth")

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await check_rate_limit_manual(mock_request, "auth")

        assert exc_info.value.status_code == 429
        assert "rate_limit_exceeded" in str(exc_info.value.detail)


class TestIntegration:
    """Integration tests with FastAPI"""

    @pytest.fixture
    def app(self, rate_limiter):
        """Create test FastAPI app"""
        app = FastAPI()

        @app.on_event("startup")
        async def startup():
            await rate_limiter.initialize()

        @app.on_event("shutdown")
        async def shutdown():
            await rate_limiter.close()

        @app.get("/test-read")
        @rate_limit("read")
        async def test_read(request: Request):
            return {"status": "ok"}

        @app.post("/test-write")
        @rate_limit("write")
        async def test_write(request: Request):
            return {"status": "ok"}

        @app.post("/test-auth")
        @rate_limit("auth")
        async def test_auth(request: Request):
            return {"status": "ok"}

        return app

    def test_endpoint_rate_limiting(self, app):
        """Test rate limiting on endpoints"""
        client = TestClient(app)

        # Auth endpoint should have low limit (5/minute)
        responses = []
        for i in range(10):
            response = client.post("/test-auth")
            responses.append(response.status_code)

        # Some should be 200, some should be 429
        assert 200 in responses
        assert 429 in responses

    def test_rate_limit_headers(self, app):
        """Test rate limit headers in response"""
        client = TestClient(app)

        response = client.get("/test-read")
        assert response.status_code == 200

        # Check headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_retry_after_header(self, app):
        """Test Retry-After header on 429 response"""
        client = TestClient(app)

        # Exhaust limit
        for i in range(10):
            response = client.post("/test-auth")
            if response.status_code == 429:
                assert "Retry-After" in response.headers
                retry_after = int(response.headers["Retry-After"])
                assert retry_after > 0
                break


class TestFailureScenarios:
    """Test graceful failure scenarios"""

    @pytest.mark.asyncio
    async def test_redis_unavailable_fail_open(self):
        """Test fail open when Redis is unavailable"""
        config = RateLimitConfig()
        config.enabled = True
        config.fail_open = True
        config.redis_url = "redis://invalid-host:6379/0"

        limiter = RateLimiter(config)

        # Should not raise exception
        try:
            await limiter.initialize()
        except:
            pass

        # Should allow requests
        allowed, metadata = await limiter.check_rate_limit("client1", "read")
        assert allowed is True

    @pytest.mark.asyncio
    async def test_redis_unavailable_fail_closed(self):
        """Test fail closed when Redis is unavailable"""
        config = RateLimitConfig()
        config.enabled = True
        config.fail_open = False
        config.redis_url = "redis://invalid-host:6379/0"

        limiter = RateLimiter(config)

        # Should raise exception
        with pytest.raises(Exception):
            await limiter.initialize()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
