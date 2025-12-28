"""Shared pytest fixtures for Extensions Marketplace tests"""

import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import Dict, List

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_user() -> Dict:
    """Create test user"""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "username": "testuser",
        "tier": "professional",
        "credits": 10000,
        "subscription_status": "active",
    }


@pytest.fixture
def test_trial_user() -> Dict:
    """Create trial tier test user"""
    return {
        "user_id": "trial-user-456",
        "email": "trial@example.com",
        "username": "trialuser",
        "tier": "trial",
        "credits": 100,
        "subscription_status": "active",
    }


@pytest.fixture
def test_enterprise_user() -> Dict:
    """Create enterprise tier test user"""
    return {
        "user_id": "enterprise-user-789",
        "email": "enterprise@example.com",
        "username": "enterpriseuser",
        "tier": "enterprise",
        "credits": -1,  # Unlimited
        "subscription_status": "active",
    }


@pytest.fixture
def test_addons() -> List[Dict]:
    """Return list of test add-ons"""
    addons_file = TEST_DATA_DIR / "test_addons.json"
    if addons_file.exists():
        with open(addons_file, "r") as f:
            return json.load(f)

    # Fallback if file doesn't exist
    return [
        {
            "id": "tts-premium",
            "name": "TTS Premium Service",
            "description": "Advanced text-to-speech with emotion control",
            "category": "ai-services",
            "base_price": 9.99,
            "billing_type": "monthly",
            "features": ["tts_enabled", "voice_customization", "emotion_control"],
            "icon_url": "/assets/addons/tts-premium.png",
            "is_active": True,
        },
        {
            "id": "stt-professional",
            "name": "STT Professional",
            "description": "Professional speech-to-text with speaker diarization",
            "category": "ai-services",
            "base_price": 9.99,
            "billing_type": "monthly",
            "features": ["stt_enabled", "speaker_diarization", "100_languages"],
            "icon_url": "/assets/addons/stt-professional.png",
            "is_active": True,
        },
        {
            "id": "storage-100gb",
            "name": "Storage Expansion 100GB",
            "description": "Additional 100GB storage with automatic backups",
            "category": "storage",
            "base_price": 4.99,
            "billing_type": "monthly",
            "features": ["storage_100gb", "automatic_backups"],
            "icon_url": "/assets/addons/storage.png",
            "is_active": True,
        },
    ]


@pytest.fixture
def test_promo_codes() -> List[Dict]:
    """Return list of test promo codes"""
    promos_file = TEST_DATA_DIR / "test_promo_codes.json"
    if promos_file.exists():
        with open(promos_file, "r") as f:
            return json.load(f)

    # Fallback if file doesn't exist
    return [
        {
            "code": "SAVE15",
            "discount_type": "percentage",
            "discount_value": 15.00,
            "is_active": True,
            "expires_at": (datetime.now() + timedelta(days=90)).isoformat(),
        },
        {
            "code": "WELCOME10",
            "discount_type": "fixed_amount",
            "discount_value": 10.00,
            "is_active": True,
            "expires_at": (datetime.now() + timedelta(days=90)).isoformat(),
        },
        {
            "code": "EXPIRED",
            "discount_type": "percentage",
            "discount_value": 20.00,
            "is_active": False,
            "expires_at": "2024-01-01T00:00:00",
        },
    ]


@pytest.fixture
def test_cart(test_user, test_addons) -> Dict:
    """Create test shopping cart"""
    return {
        "user_id": test_user["user_id"],
        "items": [
            {
                "addon_id": test_addons[0]["id"],
                "addon_name": test_addons[0]["name"],
                "quantity": 1,
                "price": test_addons[0]["base_price"],
                "billing_type": test_addons[0]["billing_type"],
            }
        ],
        "promo_code": None,
        "discount_amount": 0.0,
        "subtotal": test_addons[0]["base_price"],
        "total": test_addons[0]["base_price"],
        "created_at": datetime.now().isoformat(),
    }


@pytest.fixture
def mock_stripe():
    """Mock Stripe API"""
    with patch("stripe.checkout.Session") as mock_session, \
         patch("stripe.Webhook") as mock_webhook:

        # Mock checkout session creation
        mock_session.create.return_value = Mock(
            id="cs_test_123456789",
            url="https://checkout.stripe.com/c/pay/cs_test_123456789",
            status="open",
            payment_status="unpaid",
            metadata={}
        )

        # Mock webhook signature verification
        mock_webhook.construct_event.return_value = {
            "id": "evt_test_123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123456789",
                    "payment_status": "paid",
                    "metadata": {
                        "user_id": "test-user-123",
                        "cart_id": "cart-123"
                    }
                }
            }
        }

        yield {
            "session": mock_session,
            "webhook": mock_webhook
        }


@pytest.fixture
def stripe_test_cards() -> Dict:
    """Return Stripe test card numbers"""
    return {
        "success": {
            "visa": "4242424242424242",
            "mastercard": "5555555555554444",
        },
        "declined": {
            "card_declined": "4000000000000002",
            "insufficient_funds": "4000000000000009",
        },
        "requires_auth": {
            "3d_secure": "4000002500003155",
        }
    }


@pytest.fixture
def test_webhook_event() -> Dict:
    """Create test Stripe webhook event"""
    return {
        "id": "evt_test_123",
        "object": "event",
        "type": "checkout.session.completed",
        "created": int(datetime.now().timestamp()),
        "data": {
            "object": {
                "id": "cs_test_123456789",
                "object": "checkout.session",
                "amount_total": 999,  # $9.99 in cents
                "currency": "usd",
                "customer": "cus_test_123",
                "payment_status": "paid",
                "status": "complete",
                "metadata": {
                    "user_id": "test-user-123",
                    "cart_id": "cart-123",
                    "addon_ids": '["tts-premium"]'
                }
            }
        }
    }


@pytest.fixture
async def test_db():
    """Create test database (mock for now)"""
    # This would typically create a real test database
    # For now, we'll use a mock
    db = Mock()
    db.query = Mock(return_value=[])
    db.execute = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    yield db


@pytest.fixture
def mock_redis():
    """Mock Redis cache"""
    redis_mock = Mock()
    redis_mock.get = Mock(return_value=None)
    redis_mock.set = Mock(return_value=True)
    redis_mock.delete = Mock(return_value=True)
    redis_mock.exists = Mock(return_value=False)
    return redis_mock


@pytest.fixture
def sample_purchase_history() -> List[Dict]:
    """Sample purchase history for a user"""
    return [
        {
            "id": "purch-1",
            "user_id": "test-user-123",
            "addon_id": "tts-premium",
            "addon_name": "TTS Premium Service",
            "amount_paid": 9.99,
            "purchase_date": (datetime.now() - timedelta(days=30)).isoformat(),
            "billing_type": "monthly",
            "status": "active",
        },
        {
            "id": "purch-2",
            "user_id": "test-user-123",
            "addon_id": "stt-professional",
            "addon_name": "STT Professional",
            "amount_paid": 9.99,
            "purchase_date": (datetime.now() - timedelta(days=15)).isoformat(),
            "billing_type": "monthly",
            "status": "active",
        }
    ]


# Helper functions

def create_test_addon(**kwargs) -> Dict:
    """Create a test add-on with custom attributes"""
    default = {
        "id": "test-addon-" + str(kwargs.get("id", "1")),
        "name": "Test Add-On",
        "description": "A test add-on for unit testing",
        "category": "test",
        "base_price": 9.99,
        "billing_type": "monthly",
        "features": ["test_feature"],
        "icon_url": "/assets/addons/test.png",
        "is_active": True,
    }
    default.update(kwargs)
    return default


def create_test_cart_item(addon: Dict, quantity: int = 1) -> Dict:
    """Create a test cart item from an add-on"""
    return {
        "addon_id": addon["id"],
        "addon_name": addon["name"],
        "quantity": quantity,
        "price": addon["base_price"],
        "billing_type": addon["billing_type"],
    }


# Pytest hooks

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "stripe: Stripe API tests")
