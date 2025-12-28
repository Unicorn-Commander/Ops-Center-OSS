"""
Test fixtures and mock data for LiteLLM Multi-Provider Routing tests.
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any
from cryptography.fernet import Fernet


# Mock Encryption Key
TEST_ENCRYPTION_KEY = Fernet.generate_key()


# Mock Provider Configurations
MOCK_PROVIDERS = [
    {
        "id": "provider-1",
        "name": "OpenAI",
        "provider_type": "openai",
        "api_endpoint": "https://api.openai.com/v1",
        "enabled": True,
        "health_status": "healthy",
        "priority": 1,
        "models": [
            {
                "model_id": "gpt-4o",
                "display_name": "GPT-4o",
                "power_level": "precision",
                "cost_per_1k_tokens": 0.015,
                "context_window": 128000
            },
            {
                "model_id": "gpt-4o-mini",
                "display_name": "GPT-4o Mini",
                "power_level": "balanced",
                "cost_per_1k_tokens": 0.0005,
                "context_window": 128000
            },
            {
                "model_id": "gpt-3.5-turbo",
                "display_name": "GPT-3.5 Turbo",
                "power_level": "eco",
                "cost_per_1k_tokens": 0.0001,
                "context_window": 16385
            }
        ]
    },
    {
        "id": "provider-2",
        "name": "Anthropic",
        "provider_type": "anthropic",
        "api_endpoint": "https://api.anthropic.com/v1",
        "enabled": True,
        "health_status": "healthy",
        "priority": 2,
        "models": [
            {
                "model_id": "claude-3-5-sonnet-20241022",
                "display_name": "Claude 3.5 Sonnet",
                "power_level": "precision",
                "cost_per_1k_tokens": 0.015,
                "context_window": 200000
            },
            {
                "model_id": "claude-3-5-haiku-20241022",
                "display_name": "Claude 3.5 Haiku",
                "power_level": "balanced",
                "cost_per_1k_tokens": 0.004,
                "context_window": 200000
            }
        ]
    },
    {
        "id": "provider-3",
        "name": "Google Gemini",
        "provider_type": "google",
        "api_endpoint": "https://generativelanguage.googleapis.com/v1",
        "enabled": True,
        "health_status": "healthy",
        "priority": 3,
        "models": [
            {
                "model_id": "gemini-2.0-flash-exp",
                "display_name": "Gemini 2.0 Flash",
                "power_level": "balanced",
                "cost_per_1k_tokens": 0.0002,
                "context_window": 1000000
            },
            {
                "model_id": "gemini-1.5-flash",
                "display_name": "Gemini 1.5 Flash",
                "power_level": "eco",
                "cost_per_1k_tokens": 0.00005,
                "context_window": 1000000
            }
        ]
    },
    {
        "id": "provider-4",
        "name": "Platform vLLM",
        "provider_type": "vllm",
        "api_endpoint": "http://unicorn-vllm:8000/v1",
        "enabled": True,
        "health_status": "healthy",
        "priority": 4,
        "models": [
            {
                "model_id": "Qwen/Qwen2.5-32B-Instruct-AWQ",
                "display_name": "Qwen 2.5 32B",
                "power_level": "eco",
                "cost_per_1k_tokens": 0.0,
                "context_window": 32768
            }
        ]
    }
]


# Mock User API Keys (Encrypted)
def get_mock_user_keys() -> List[Dict[str, Any]]:
    """Generate mock encrypted API keys for testing."""
    fernet = Fernet(TEST_ENCRYPTION_KEY)

    return [
        {
            "user_id": "user-123",
            "provider_id": "provider-1",
            "provider_name": "OpenAI",
            "encrypted_key": fernet.encrypt(b"sk-test-openai-key-abc123").decode(),
            "key_name": "My OpenAI Key",
            "created_at": datetime.utcnow() - timedelta(days=7),
            "last_used": datetime.utcnow() - timedelta(hours=2),
            "is_active": True
        },
        {
            "user_id": "user-123",
            "provider_id": "provider-2",
            "provider_name": "Anthropic",
            "encrypted_key": fernet.encrypt(b"sk-ant-test-key-xyz789").decode(),
            "key_name": "My Anthropic Key",
            "created_at": datetime.utcnow() - timedelta(days=3),
            "last_used": datetime.utcnow() - timedelta(hours=5),
            "is_active": True
        },
        {
            "user_id": "user-456",
            "provider_id": "provider-1",
            "provider_name": "OpenAI",
            "encrypted_key": fernet.encrypt(b"sk-test-openai-key-def456").decode(),
            "key_name": "Work OpenAI Key",
            "created_at": datetime.utcnow() - timedelta(days=14),
            "last_used": None,
            "is_active": False
        }
    ]


# Mock LLM Responses
MOCK_LLM_RESPONSES = {
    "openai": {
        "success": {
            "id": "chatcmpl-abc123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4o",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "This is a test response from OpenAI."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        },
        "error_invalid_key": {
            "error": {
                "message": "Incorrect API key provided",
                "type": "invalid_request_error",
                "code": "invalid_api_key"
            }
        },
        "error_rate_limit": {
            "error": {
                "message": "Rate limit exceeded",
                "type": "rate_limit_error",
                "code": "rate_limit_exceeded"
            }
        }
    },
    "anthropic": {
        "success": {
            "id": "msg_abc123",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "This is a test response from Anthropic."
                }
            ],
            "model": "claude-3-5-sonnet-20241022",
            "usage": {
                "input_tokens": 15,
                "output_tokens": 25
            }
        },
        "error_invalid_key": {
            "error": {
                "type": "authentication_error",
                "message": "Invalid API key"
            }
        }
    },
    "google": {
        "success": {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "This is a test response from Google Gemini."
                            }
                        ],
                        "role": "model"
                    },
                    "finishReason": "STOP"
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 12,
                "candidatesTokenCount": 18,
                "totalTokenCount": 30
            }
        }
    }
}


# Mock Usage Logs
def get_mock_usage_logs() -> List[Dict[str, Any]]:
    """Generate mock usage logs for analytics testing."""
    base_time = datetime.utcnow() - timedelta(days=30)

    logs = []
    for i in range(100):
        log_time = base_time + timedelta(hours=i * 7)
        provider = MOCK_PROVIDERS[i % len(MOCK_PROVIDERS)]
        model = provider["models"][i % len(provider["models"])]

        logs.append({
            "id": f"log-{i}",
            "user_id": f"user-{i % 3}",
            "provider_id": provider["id"],
            "provider_name": provider["name"],
            "model_id": model["model_id"],
            "power_level": model["power_level"],
            "prompt_tokens": 10 + (i % 50),
            "completion_tokens": 20 + (i % 100),
            "total_tokens": 30 + (i % 150),
            "cost": (30 + (i % 150)) * model["cost_per_1k_tokens"] / 1000,
            "latency_ms": 500 + (i % 1000),
            "used_byok": i % 3 == 0,
            "created_at": log_time,
            "status": "success" if i % 10 != 0 else "error"
        })

    return logs


# Mock Routing Rules
MOCK_ROUTING_RULES = [
    {
        "id": "rule-1",
        "power_level": "eco",
        "preferred_providers": ["provider-4", "provider-3"],
        "fallback_order": ["provider-1", "provider-2"],
        "max_cost_per_request": 0.001
    },
    {
        "id": "rule-2",
        "power_level": "balanced",
        "preferred_providers": ["provider-2", "provider-3"],
        "fallback_order": ["provider-1", "provider-4"],
        "max_cost_per_request": 0.01
    },
    {
        "id": "rule-3",
        "power_level": "precision",
        "preferred_providers": ["provider-1", "provider-2"],
        "fallback_order": ["provider-3", "provider-4"],
        "max_cost_per_request": 0.05
    }
]


# Pytest Fixtures
@pytest.fixture
def mock_encryption_key():
    """Provide mock encryption key."""
    return TEST_ENCRYPTION_KEY


@pytest.fixture
def mock_providers():
    """Provide mock provider configurations."""
    return MOCK_PROVIDERS.copy()


@pytest.fixture
def mock_user_keys():
    """Provide mock user API keys."""
    return get_mock_user_keys()


@pytest.fixture
def mock_llm_responses():
    """Provide mock LLM responses."""
    return MOCK_LLM_RESPONSES.copy()


@pytest.fixture
def mock_usage_logs():
    """Provide mock usage logs."""
    return get_mock_usage_logs()


@pytest.fixture
def mock_routing_rules():
    """Provide mock routing rules."""
    return MOCK_ROUTING_RULES.copy()


@pytest.fixture
def mock_db_session():
    """Provide mock database session."""
    from unittest.mock import MagicMock
    session = MagicMock()
    return session


@pytest.fixture
def mock_keycloak_admin():
    """Provide mock Keycloak admin client."""
    from unittest.mock import MagicMock

    admin = MagicMock()
    admin.get_user.return_value = {
        "id": "user-123",
        "username": "testuser",
        "email": "test@example.com",
        "attributes": {
            "llm_api_keys": []
        }
    }
    return admin
