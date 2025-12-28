"""
OpenRouter API Client

Provides async HTTP client for OpenRouter API with retry logic,
rate limiting, and error handling.

Author: Integration Team Lead
Date: October 24, 2025
Epic: 2.2 - OpenRouter Integration
"""

import httpx
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import json

logger = logging.getLogger(__name__)


class OpenRouterAPIError(Exception):
    """Base exception for OpenRouter API errors"""
    pass


class OpenRouterRateLimitError(OpenRouterAPIError):
    """Raised when rate limit is exceeded"""
    pass


class OpenRouterAuthError(OpenRouterAPIError):
    """Raised when authentication fails"""
    pass


class OpenRouterClient:
    """
    Async HTTP client for OpenRouter API with intelligent retry logic.

    Features:
    - Exponential backoff retry (3 attempts)
    - Rate limit handling with automatic retry after delay
    - Request/response logging
    - Connection pooling for performance
    - Proper error classification
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1.0  # seconds
    MAX_RETRY_DELAY = 30.0     # seconds
    RETRY_BACKOFF_FACTOR = 2.0

    # Timeout configuration
    TIMEOUT = 30.0  # seconds

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenRouter API client.

        Args:
            api_key: OpenRouter API key (can be set per request)
        """
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None
        self._rate_limit_reset: Optional[datetime] = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def initialize(self):
        """Initialize HTTP client with connection pooling"""
        if not self._client:
            self._client = httpx.AsyncClient(
                timeout=self.TIMEOUT,
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20
                ),
                headers={
                    "HTTP-Referer": "https://your-domain.com",
                    "X-Title": "UC-Cloud Ops Center",
                    "Content-Type": "application/json"
                }
            )
            logger.info("OpenRouterClient initialized")

    async def close(self):
        """Close HTTP client and cleanup resources"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("OpenRouterClient closed")

    async def _check_rate_limit(self):
        """Check if we're currently rate limited"""
        if self._rate_limit_reset:
            if datetime.now() < self._rate_limit_reset:
                wait_seconds = (self._rate_limit_reset - datetime.now()).total_seconds()
                logger.warning(f"Rate limited. Waiting {wait_seconds:.1f}s")
                await asyncio.sleep(wait_seconds)
            else:
                self._rate_limit_reset = None

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/models")
            api_key: OpenRouter API key (overrides instance key)
            **kwargs: Additional arguments for httpx request

        Returns:
            JSON response data

        Raises:
            OpenRouterAPIError: For API errors
            OpenRouterAuthError: For authentication errors
            OpenRouterRateLimitError: For rate limit errors
        """
        if not self._client:
            await self.initialize()

        # Use provided API key or instance key
        key = api_key or self.api_key
        if not key:
            raise OpenRouterAuthError("No API key provided")

        # Build URL
        url = f"{self.BASE_URL}{endpoint}"

        # Add authorization header
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {key}"

        # Retry loop
        last_exception = None
        for attempt in range(self.MAX_RETRIES):
            try:
                # Check rate limit before making request
                await self._check_rate_limit()

                # Make request
                logger.debug(f"Request: {method} {endpoint} (attempt {attempt + 1}/{self.MAX_RETRIES})")
                response = await self._client.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs
                )

                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    self._rate_limit_reset = datetime.now() + timedelta(seconds=retry_after)

                    logger.warning(f"Rate limited (429). Retry after {retry_after}s")

                    if attempt < self.MAX_RETRIES - 1:
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        raise OpenRouterRateLimitError(
                            f"Rate limit exceeded. Retry after {retry_after}s"
                        )

                # Handle authentication errors (401, 403)
                if response.status_code in (401, 403):
                    error_data = response.json() if response.content else {}
                    raise OpenRouterAuthError(
                        f"Authentication failed: {error_data.get('error', {}).get('message', 'Invalid API key')}"
                    )

                # Raise for other HTTP errors
                response.raise_for_status()

                # Parse JSON response
                data = response.json()
                logger.debug(f"Response: {method} {endpoint} - {response.status_code}")

                return data

            except httpx.HTTPStatusError as e:
                last_exception = e
                error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
                logger.error(f"Request failed: {error_msg}")

                # Don't retry on client errors (4xx except 429)
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    raise OpenRouterAPIError(error_msg)

                # Retry on server errors (5xx)
                if attempt < self.MAX_RETRIES - 1:
                    delay = min(
                        self.INITIAL_RETRY_DELAY * (self.RETRY_BACKOFF_FACTOR ** attempt),
                        self.MAX_RETRY_DELAY
                    )
                    logger.info(f"Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)

            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_exception = e
                logger.error(f"Request error: {e}")

                # Retry on network errors
                if attempt < self.MAX_RETRIES - 1:
                    delay = min(
                        self.INITIAL_RETRY_DELAY * (self.RETRY_BACKOFF_FACTOR ** attempt),
                        self.MAX_RETRY_DELAY
                    )
                    logger.info(f"Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)

        # All retries exhausted
        raise OpenRouterAPIError(f"Request failed after {self.MAX_RETRIES} attempts: {last_exception}")

    async def get_models(self, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of available models from OpenRouter.

        Args:
            api_key: OpenRouter API key

        Returns:
            List of model dictionaries with pricing and metadata
        """
        response = await self._make_request("GET", "/models", api_key=api_key)
        return response.get("data", [])

    async def get_key_info(self, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about an API key including credit balance.

        Args:
            api_key: OpenRouter API key

        Returns:
            Key information dictionary with:
            - label: Key name
            - limit: Credit limit (or null for unlimited)
            - usage: Total usage
            - limit_remaining: Remaining credits
            - rate_limit: Rate limit info
        """
        response = await self._make_request("GET", "/auth/key", api_key=api_key)
        return response.get("data", {})

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        api_key: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion using OpenRouter.

        Args:
            model: Model ID (e.g., "meta-llama/llama-3.1-8b-instruct:free")
            messages: List of chat messages
            api_key: OpenRouter API key
            **kwargs: Additional OpenAI-compatible parameters

        Returns:
            OpenAI-compatible chat completion response
        """
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }

        return await self._make_request(
            "POST",
            "/chat/completions",
            api_key=api_key,
            json=payload
        )

    async def get_generation(
        self,
        generation_id: str,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get detailed information about a completed generation.

        Args:
            generation_id: Generation ID from X-OpenRouter-Generation-ID header
            api_key: OpenRouter API key

        Returns:
            Generation details including costs and token usage
        """
        return await self._make_request(
            "GET",
            f"/generation?id={generation_id}",
            api_key=api_key
        )


# Convenience function for single-use requests
async def make_openrouter_request(
    endpoint: str,
    api_key: str,
    method: str = "GET",
    **kwargs
) -> Dict[str, Any]:
    """
    Make a single OpenRouter API request (convenience function).

    Args:
        endpoint: API endpoint (e.g., "/models")
        api_key: OpenRouter API key
        method: HTTP method
        **kwargs: Additional request arguments

    Returns:
        JSON response data
    """
    async with OpenRouterClient(api_key) as client:
        return await client._make_request(method, endpoint, **kwargs)
