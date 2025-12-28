"""
Pytest Configuration and Shared Fixtures
Provides common test fixtures and utilities for all test files
"""

import pytest
import asyncio
import os
import sys
import httpx
from typing import Dict, Generator

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (require full stack)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (require services)"
    )
    config.addinivalue_line(
        "markers", "unit: Unit tests (no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow-running tests"
    )
    config.addinivalue_line(
        "markers", "stripe: Tests requiring Stripe API"
    )
    config.addinivalue_line(
        "markers", "keycloak: Tests requiring Keycloak"
    )


# ============================================================================
# EVENT LOOP FIXTURE
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# HTTP CLIENT FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def base_url() -> str:
    """Get base URL for API tests"""
    return os.getenv("BASE_URL", "http://localhost:8084")


@pytest.fixture(scope="session")
async def http_client() -> Generator[httpx.AsyncClient, None, None]:
    """HTTP client for API requests"""
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        yield client


@pytest.fixture(scope="function")
async def authenticated_client(http_client, base_url) -> httpx.AsyncClient:
    """HTTP client with authentication cookies"""
    # TODO: Implement authentication flow
    # For now, return unauthenticated client
    return http_client


# ============================================================================
# KEYCLOAK FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def keycloak_config() -> Dict[str, str]:
    """Keycloak configuration"""
    return {
        "url": os.getenv("KEYCLOAK_URL", "https://auth.your-domain.com"),
        "realm": os.getenv("KEYCLOAK_REALM", "uchub"),
        "admin_username": os.getenv("KEYCLOAK_ADMIN_USERNAME", "admin"),
        "admin_password": os.getenv("KEYCLOAK_ADMIN_PASSWORD", ""),
        "client_id": os.getenv("KEYCLOAK_CLIENT_ID", "admin-cli")
    }


@pytest.fixture(scope="session")
async def keycloak_admin_token(keycloak_config):
    """Get Keycloak admin token"""
    from keycloak_integration import get_admin_token
    try:
        token = await get_admin_token()
        return token
    except Exception as e:
        pytest.skip(f"Cannot get Keycloak admin token: {e}")


# ============================================================================
# STRIPE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def stripe_config() -> Dict[str, str]:
    """Stripe configuration"""
    return {
        "secret_key": os.getenv("STRIPE_SECRET_KEY", ""),
        "publishable_key": os.getenv("STRIPE_PUBLISHABLE_KEY", ""),
        "webhook_secret": os.getenv("STRIPE_WEBHOOK_SECRET", ""),
        "test_mode": True
    }


@pytest.fixture(scope="session")
def stripe_client(stripe_config):
    """Stripe client for API calls"""
    if not stripe_config["secret_key"]:
        pytest.skip("STRIPE_SECRET_KEY not configured")

    from billing.stripe_client import StripeClient
    return StripeClient(api_key=stripe_config["secret_key"])


@pytest.fixture
def stripe_test_cards() -> Dict[str, str]:
    """Stripe test card numbers"""
    return {
        "success": "4242424242424242",
        "decline": "4000000000000002",
        "insufficient_funds": "4000000000009995",
        "requires_auth": "4000002500003155",
        "expired": "4000000000000069"
    }


# ============================================================================
# TEST USER FIXTURES
# ============================================================================

@pytest.fixture
def test_users() -> Dict[str, Dict]:
    """Test user data for all tiers"""
    return {
        "trial": {
            "email": "test-trial@example.com",
            "username": "test_trial",
            "tier": "trial",
            "first_name": "Trial",
            "last_name": "User"
        },
        "starter": {
            "email": "test-starter@example.com",
            "username": "test_starter",
            "tier": "starter",
            "first_name": "Starter",
            "last_name": "User"
        },
        "professional": {
            "email": "test-professional@example.com",
            "username": "test_professional",
            "tier": "professional",
            "first_name": "Professional",
            "last_name": "User"
        },
        "enterprise": {
            "email": "test-enterprise@example.com",
            "username": "test_enterprise",
            "tier": "enterprise",
            "first_name": "Enterprise",
            "last_name": "User"
        }
    }


@pytest.fixture(scope="function")
async def cleanup_test_users(test_users):
    """Cleanup test users before and after test"""
    from keycloak_integration import delete_user

    # Cleanup before test
    for tier, user_data in test_users.items():
        try:
            await delete_user(user_data["email"])
        except:
            pass

    yield

    # Cleanup after test
    for tier, user_data in test_users.items():
        try:
            await delete_user(user_data["email"])
        except:
            pass


# ============================================================================
# WEBHOOK FIXTURES
# ============================================================================

@pytest.fixture
def lago_webhook_payloads() -> Dict[str, Dict]:
    """Sample Lago webhook payloads"""
    return {
        "subscription_created": {
            "webhook_type": "subscription.created",
            "subscription": {
                "lago_id": "test_sub_123",
                "plan_code": "starter_monthly",
                "status": "active"
            },
            "customer": {
                "email": "test@example.com"
            }
        },
        "subscription_updated": {
            "webhook_type": "subscription.updated",
            "subscription": {
                "lago_id": "test_sub_123",
                "plan_code": "professional_monthly",
                "status": "active"
            },
            "customer": {
                "email": "test@example.com"
            }
        },
        "subscription_cancelled": {
            "webhook_type": "subscription.cancelled",
            "subscription": {
                "lago_id": "test_sub_123"
            },
            "customer": {
                "email": "test@example.com"
            }
        },
        "invoice_paid": {
            "webhook_type": "invoice.paid",
            "invoice": {
                "lago_id": "invoice_123",
                "amount_cents": 1900,
                "currency": "USD"
            },
            "customer": {
                "email": "test@example.com"
            }
        }
    }


@pytest.fixture
def stripe_webhook_payloads() -> Dict[str, Dict]:
    """Sample Stripe webhook payloads"""
    return {
        "customer_subscription_created": {
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_test_123",
                    "customer": "cus_test_123",
                    "status": "active",
                    "metadata": {
                        "tier": "starter"
                    }
                }
            }
        },
        "customer_subscription_deleted": {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_test_123",
                    "customer": "cus_test_123",
                    "status": "canceled"
                }
            }
        },
        "invoice_paid": {
            "type": "invoice.paid",
            "data": {
                "object": {
                    "id": "in_test_123",
                    "customer": "cus_test_123",
                    "amount_paid": 1900,
                    "currency": "usd"
                }
            }
        }
    }


# ============================================================================
# TIER CONFIGURATION FIXTURES
# ============================================================================

@pytest.fixture
def tier_limits() -> Dict[str, Dict]:
    """API limits for each tier"""
    return {
        "trial": {
            "api_calls_limit": 100,
            "byok_enabled": False,
            "services": ["openwebui"]
        },
        "starter": {
            "api_calls_limit": 10000,
            "byok_enabled": True,
            "services": ["openwebui", "search"]
        },
        "professional": {
            "api_calls_limit": 100000,
            "byok_enabled": True,
            "services": ["openwebui", "search", "embeddings", "reranker"]
        },
        "enterprise": {
            "api_calls_limit": 1000000,
            "byok_enabled": True,
            "services": ["all"]
        }
    }


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def mock_api_keys() -> Dict[str, str]:
    """Mock API keys for testing"""
    return {
        "openai": "sk-test-mock-openai-key-123456",
        "anthropic": "sk-ant-test-mock-key-123456",
        "huggingface": "hf_test_mock_key_123456",
        "cohere": "test-mock-cohere-key-123456",
        "groq": "gsk_test_mock_key_123456"
    }


@pytest.fixture
def encryption_key() -> str:
    """Encryption key for BYOK tests"""
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        # Generate temporary key for testing
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
    return key


# ============================================================================
# REPORT FIXTURES
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def test_report_header(request):
    """Print test report header"""
    print("\n" + "="*80)
    print("UC-1 PRO BILLING SYSTEM - TEST SUITE")
    print("="*80)
    print(f"Base URL: {os.getenv('BASE_URL', 'http://localhost:8084')}")
    print(f"Keycloak: {os.getenv('KEYCLOAK_URL', 'https://auth.your-domain.com')}")
    print(f"Stripe Test Mode: True")
    print("="*80 + "\n")


@pytest.fixture(scope="function", autouse=True)
def test_info(request):
    """Print test info before each test"""
    print(f"\nRunning: {request.node.name}")
    yield
    print(f"Completed: {request.node.name}")


# ============================================================================
# SKIP CONDITIONS
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add skip conditions"""
    skip_stripe = pytest.mark.skip(reason="STRIPE_SECRET_KEY not configured")
    skip_keycloak = pytest.mark.skip(reason="KEYCLOAK_URL not configured")

    for item in items:
        if "stripe" in item.keywords and not os.getenv("STRIPE_SECRET_KEY"):
            item.add_marker(skip_stripe)

        if "keycloak" in item.keywords and not os.getenv("KEYCLOAK_URL"):
            item.add_marker(skip_keycloak)
