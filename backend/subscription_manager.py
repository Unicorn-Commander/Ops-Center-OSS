"""
Subscription and Service Access Management for UC-1 Pro
Handles subscription tiers, service access control, and plan management
"""

from typing import Dict, List, Optional
from pydantic import BaseModel
from enum import Enum
import json
import os
import stripe
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class ServiceType(str, Enum):
    """Available services in UC-1 Pro"""
    OPS_CENTER = "ops-center"
    CHAT = "chat"  # Open-WebUI
    SEARCH = "search"  # Center Deep Pro
    TTS = "tts"  # Unicorn Orator
    STT = "stt"  # Unicorn Amanuensis
    BILLING = "billing"  # Lago
    LITELLM = "litellm"  # AI Gateway
    BOLT = "bolt"  # Bolt.DIY
    ADMIN = "admin"  # Admin Dashboard

class PermissionLevel(str, Enum):
    """Permission levels for users"""
    ADMIN = "admin"
    POWER_USER = "power_user"
    USER = "user"
    TRIAL = "trial"

class SubscriptionPlan(BaseModel):
    """Subscription plan configuration"""
    id: str
    name: str
    display_name: str
    price_monthly: float
    price_yearly: Optional[float] = None
    features: List[str]
    services: List[ServiceType]
    api_calls_limit: int  # -1 for unlimited
    byok_enabled: bool = False
    priority_support: bool = False
    team_seats: int = 1
    is_active: bool = True
    stripe_price_id: Optional[str] = None  # Monthly Stripe price ID
    stripe_annual_price_id: Optional[str] = None  # Annual Stripe price ID

class ServiceAccessConfig(BaseModel):
    """Service access configuration"""
    service: ServiceType
    display_name: str
    description: str
    icon: str  # Emoji or icon class
    url: str
    required_permission: PermissionLevel
    required_plans: List[str]  # Plan IDs that can access this service
    is_external: bool = False

# Default subscription plans
DEFAULT_PLANS = [
    SubscriptionPlan(
        id="trial",
        name="trial",
        display_name="Trial",
        price_monthly=1.00,
        price_yearly=52.00,
        features=[
            "7-day trial period",
            "Access to Open-WebUI",
            "Center-Deep Search",
            "Basic AI models",
            "BYOK support",
            "100 API calls/day"
        ],
        services=[ServiceType.OPS_CENTER, ServiceType.CHAT, ServiceType.SEARCH],
        api_calls_limit=700,  # 100/day * 7 days
        byok_enabled=True,
        stripe_price_id="price_1SI0FHDzk9HqAZnHbUgvaidP",  # Monthly
        stripe_annual_price_id="price_1SI0FHDzk9HqAZnHbUgvaidP"  # Weekly trial only (no annual)
    ),
    SubscriptionPlan(
        id="starter",
        name="starter",
        display_name="Starter",
        price_monthly=19.00,
        price_yearly=190.00,  # ~16.67/month
        features=[
            "Open-WebUI access",
            "Center Deep Pro search",
            "1,000 API calls/month",
            "BYOK support",
            "Community support"
        ],
        services=[ServiceType.OPS_CENTER, ServiceType.CHAT, ServiceType.SEARCH],
        api_calls_limit=1000,
        byok_enabled=True,
        stripe_price_id="price_1SI0FHDzk9HqAZnHAsMKY9tS",  # Monthly
        stripe_annual_price_id="price_1SI0FHDzk9HqAZnHAsMKY9tS"  # TODO: Create annual price in Stripe
    ),
    SubscriptionPlan(
        id="professional",
        name="professional",
        display_name="Professional",
        price_monthly=49.00,
        price_yearly=490.00,  # ~40.83/month
        features=[
            "All Starter features",
            "Unicorn Orator (TTS)",
            "Unicorn Amanuensis (STT)",
            "Billing dashboard access",
            "LiteLLM AI gateway",
            "10,000 API calls/month",
            "Priority support",
            "All AI models"
        ],
        services=[
            ServiceType.OPS_CENTER,
            ServiceType.CHAT,
            ServiceType.SEARCH,
            ServiceType.TTS,
            ServiceType.STT,
            ServiceType.BILLING,
            ServiceType.LITELLM
        ],
        api_calls_limit=10000,
        byok_enabled=True,
        priority_support=True,
        stripe_price_id="price_1SI0FIDzk9HqAZnHgA63KIpk",  # Monthly
        stripe_annual_price_id="price_1SI0FIDzk9HqAZnHgA63KIpk"  # TODO: Create annual price in Stripe
    ),
    SubscriptionPlan(
        id="founders-friend",
        name="founders_friend",
        display_name="Founder's Friend",
        price_monthly=49.00,
        price_yearly=490.00,
        features=[
            "Early Supporter Special",
            "All Professional features",
            "Unicorn Orator (TTS)",
            "Unicorn Amanuensis (STT)",
            "Billing dashboard access",
            "LiteLLM AI gateway",
            "BYOK support",
            "10,000 API calls/month",
            "Priority support",
            "All AI models",
            "Lock in this rate forever"
        ],
        services=[
            ServiceType.OPS_CENTER,
            ServiceType.CHAT,
            ServiceType.SEARCH,
            ServiceType.TTS,
            ServiceType.STT,
            ServiceType.BILLING,
            ServiceType.LITELLM
        ],
        api_calls_limit=10000,
        byok_enabled=True,
        priority_support=True,
        stripe_price_id="price_1SI0FIDzk9HqAZnHgA63KIpk",  # Same as Professional (monthly)
        stripe_annual_price_id="price_1SI0FIDzk9HqAZnHgA63KIpk"  # TODO: Create annual price in Stripe
    ),
    SubscriptionPlan(
        id="enterprise",
        name="enterprise",
        display_name="Enterprise",
        price_monthly=99.00,
        price_yearly=990.00,  # ~82.50/month
        features=[
            "All Professional features",
            "Bolt.DIY development environment",
            "Unlimited API calls",
            "Team management (up to 10 seats)",
            "SSO integration",
            "Audit logs",
            "Custom integrations",
            "Dedicated support"
        ],
        services=[
            ServiceType.OPS_CENTER,
            ServiceType.CHAT,
            ServiceType.SEARCH,
            ServiceType.TTS,
            ServiceType.STT,
            ServiceType.BILLING,
            ServiceType.LITELLM,
            ServiceType.BOLT
        ],
        api_calls_limit=-1,  # Unlimited
        byok_enabled=True,
        priority_support=True,
        team_seats=10,
        stripe_price_id="price_1SI0FIDzk9HqAZnHZFRzBjgP",  # Monthly
        stripe_annual_price_id="price_1SI0FIDzk9HqAZnHZFRzBjgP"  # TODO: Create annual price in Stripe
    )
]

# Service access configuration
SERVICE_ACCESS = [
    ServiceAccessConfig(
        service=ServiceType.OPS_CENTER,
        display_name="Ops Center",
        description="Operations dashboard and system management",
        icon="⚙️",
        url="/",
        required_permission=PermissionLevel.USER,
        required_plans=["trial", "starter", "professional", "enterprise"]
    ),
    ServiceAccessConfig(
        service=ServiceType.CHAT,
        display_name="Open-WebUI",
        description="Advanced AI chat interface with multi-model support",
        icon="💬",
        url="https://chat.unicorncommander.ai",
        required_permission=PermissionLevel.USER,
        required_plans=["trial", "starter", "professional", "enterprise"],
        is_external=True
    ),
    ServiceAccessConfig(
        service=ServiceType.SEARCH,
        display_name="Center-Deep Search",
        description="AI-powered metasearch platform with 70+ search engines",
        icon="🔍",
        url="https://search.unicorncommander.ai",
        required_permission=PermissionLevel.USER,
        required_plans=["starter", "professional", "enterprise"],
        is_external=True
    ),
    ServiceAccessConfig(
        service=ServiceType.TTS,
        display_name="Unicorn Orator",
        description="Professional AI voice synthesis with multiple voices",
        icon="🎙️",
        url="https://tts.unicorncommander.ai",
        required_permission=PermissionLevel.USER,
        required_plans=["professional", "enterprise"],
        is_external=True
    ),
    ServiceAccessConfig(
        service=ServiceType.STT,
        display_name="Unicorn Amanuensis",
        description="Advanced speech-to-text with speaker diarization",
        icon="🎤",
        url="https://stt.unicorncommander.ai",
        required_permission=PermissionLevel.USER,
        required_plans=["professional", "enterprise"],
        is_external=True
    ),
    ServiceAccessConfig(
        service=ServiceType.BILLING,
        display_name="Billing Dashboard",
        description="Usage tracking and billing management",
        icon="💳",
        url="https://billing.unicorncommander.ai",
        required_permission=PermissionLevel.USER,
        required_plans=["professional", "enterprise"],
        is_external=True
    ),
    ServiceAccessConfig(
        service=ServiceType.LITELLM,
        display_name="LiteLLM Gateway",
        description="AI model gateway with 50+ models",
        icon="🤖",
        url="https://ai.unicorncommander.ai",
        required_permission=PermissionLevel.USER,
        required_plans=["professional", "enterprise"],
        is_external=True
    ),
    ServiceAccessConfig(
        service=ServiceType.BOLT,
        display_name="Bolt.DIY",
        description="AI-powered development environment",
        icon="⚡",
        url="https://bolt.unicorncommander.ai",
        required_permission=PermissionLevel.USER,
        required_plans=["enterprise"],
        is_external=True
    ),
    ServiceAccessConfig(
        service=ServiceType.ADMIN,
        display_name="Admin Dashboard",
        description="System administration and configuration",
        icon="🔐",
        url="/admin",
        required_permission=PermissionLevel.ADMIN,
        required_plans=[]  # Only for admins
    )
]

class SubscriptionManager:
    """Manages subscription plans and service access"""

    def __init__(self, config_path: str = "/app/config/subscriptions.json"):
        self.config_path = config_path
        self.plans = self._load_plans()
        self.service_access = SERVICE_ACCESS

    def _load_plans(self) -> List[SubscriptionPlan]:
        """Load plans from config or use defaults"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    return [SubscriptionPlan(**plan) for plan in data]
            except Exception as e:
                print(f"Error loading plans: {e}, using defaults")
        return DEFAULT_PLANS

    def save_plans(self):
        """Save plans to config file"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump([plan.dict() for plan in self.plans], f, indent=2)

    def get_plan(self, plan_id: str) -> Optional[SubscriptionPlan]:
        """Get plan by ID"""
        for plan in self.plans:
            if plan.id == plan_id:
                return plan
        return None

    def get_all_plans(self) -> List[SubscriptionPlan]:
        """Get all active plans"""
        return [plan for plan in self.plans if plan.is_active]

    def create_plan(self, plan: SubscriptionPlan) -> SubscriptionPlan:
        """Create new subscription plan"""
        # Check if plan ID already exists
        if any(p.id == plan.id for p in self.plans):
            raise ValueError(f"Plan with ID {plan.id} already exists")

        self.plans.append(plan)
        self.save_plans()
        return plan

    def update_plan(self, plan_id: str, updates: Dict) -> Optional[SubscriptionPlan]:
        """Update existing plan"""
        for i, plan in enumerate(self.plans):
            if plan.id == plan_id:
                updated_plan = plan.copy(update=updates)
                self.plans[i] = updated_plan
                self.save_plans()
                return updated_plan
        return None

    def delete_plan(self, plan_id: str) -> bool:
        """Soft delete plan (mark as inactive)"""
        for plan in self.plans:
            if plan.id == plan_id:
                plan.is_active = False
                self.save_plans()
                return True
        return False

    def get_user_accessible_services(
        self,
        user_plan: str,
        user_role: str
    ) -> List[ServiceAccessConfig]:
        """Get services accessible to user based on plan and role"""
        accessible = []

        for service in self.service_access:
            # Admins get everything
            if user_role == PermissionLevel.ADMIN:
                accessible.append(service)
                continue

            # Check if user's permission level is sufficient
            if user_role == service.required_permission or user_role == PermissionLevel.ADMIN:
                # Check if user's plan includes this service
                if not service.required_plans or user_plan in service.required_plans:
                    accessible.append(service)

        return accessible

    def check_service_access(
        self,
        service: ServiceType,
        user_plan: str,
        user_role: str
    ) -> bool:
        """Check if user has access to specific service"""
        # Admins always have access
        if user_role == PermissionLevel.ADMIN:
            return True

        for svc in self.service_access:
            if svc.service == service:
                # Check permission level
                if user_role != svc.required_permission and user_role != PermissionLevel.ADMIN:
                    return False

                # Check plan
                if svc.required_plans and user_plan not in svc.required_plans:
                    return False

                return True

        return False

# Global subscription manager instance
subscription_manager = SubscriptionManager()


# ============================================================================
# Stripe Checkout Helper Functions
# ============================================================================

def create_upgrade_checkout_session(
    user_email: str,
    plan_code: str,
    success_url: str,
    cancel_url: str,
    user_metadata: Optional[Dict] = None
) -> Dict:
    """
    Create Stripe Checkout session for subscription upgrade

    Args:
        user_email: User's email address
        plan_code: Target subscription plan code
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if user cancels
        user_metadata: Additional metadata to attach to session

    Returns:
        Dict with checkout_url and session_id

    Raises:
        ValueError: If plan not found or Stripe Price ID not configured
        stripe.error.StripeError: If Stripe API call fails
    """
    # Find plan by code
    plan = subscription_manager.get_plan(plan_code)
    if not plan:
        raise ValueError(f"Plan '{plan_code}' not found")

    if not plan.stripe_price_id:
        raise ValueError(f"Stripe Price ID not configured for plan '{plan_code}'")

    # Prepare metadata
    metadata = {
        "plan_code": plan.id,
        "plan_name": plan.display_name,
        "user_email": user_email
    }
    if user_metadata:
        metadata.update(user_metadata)

    try:
        # Create Stripe Checkout Session
        session = stripe.checkout.Session.create(
            customer_email=user_email,
            payment_method_types=["card"],
            line_items=[{
                "price": plan.stripe_price_id,
                "quantity": 1
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
            subscription_data={
                "metadata": metadata
            }
        )

        logger.info(f"Created Stripe Checkout session for {user_email}: {session.id}")

        return {
            "checkout_url": session.url,
            "session_id": session.id,
            "plan": plan.dict()
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {str(e)}")
        raise


def get_stripe_price_ids() -> Dict[str, str]:
    """
    Get mapping of plan codes to Stripe Price IDs

    Returns:
        Dict mapping plan_code -> stripe_price_id
    """
    price_ids = {}
    for plan in subscription_manager.get_all_plans():
        if plan.stripe_price_id:
            price_ids[plan.id] = plan.stripe_price_id
    return price_ids


def validate_stripe_webhook_signature(payload: bytes, sig_header: str, webhook_secret: str) -> Dict:
    """
    Validate and parse Stripe webhook event

    Args:
        payload: Raw request body bytes
        sig_header: Stripe-Signature header value
        webhook_secret: Webhook signing secret

    Returns:
        Parsed Stripe event object

    Raises:
        ValueError: If signature validation fails
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        logger.info(f"Validated Stripe webhook event: {event['type']}")
        return event
    except ValueError as e:
        logger.error(f"Invalid Stripe webhook payload: {str(e)}")
        raise
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid Stripe webhook signature: {str(e)}")
        raise ValueError("Invalid webhook signature")
