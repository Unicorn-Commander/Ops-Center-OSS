"""
Lago Billing Integration for UC-1 Pro
Handles organization-based billing with Lago API
Uses org_id as the primary customer identifier instead of user_id
"""

import httpx
import os
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

# Import universal credential helper
from get_credential import get_credential

logger = logging.getLogger(__name__)

# Lago Configuration - read credentials from database first, then environment
LAGO_API_URL = os.getenv("LAGO_API_URL", "http://unicorn-lago-api:3000")
LAGO_API_KEY = get_credential("LAGO_API_KEY")

# Timeout for API calls
API_TIMEOUT = 30.0


class LagoIntegrationError(Exception):
    """Custom exception for Lago integration errors"""
    pass


# ============================================
# Customer Management (Org-based)
# ============================================

async def create_org_customer(
    org_id: str,
    org_name: str,
    email: str,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a customer in Lago for an organization.

    Args:
        org_id: Organization ID (used as external_id in Lago)
        org_name: Organization name
        email: Organization contact email
        user_id: User ID who created the org (stored in metadata)
        metadata: Additional metadata to store

    Returns:
        Customer data from Lago API

    Raises:
        LagoIntegrationError: If customer creation fails
    """
    if not LAGO_API_KEY:
        raise LagoIntegrationError("LAGO_API_KEY not configured")

    # Prepare metadata
    customer_metadata = metadata or {}
    if user_id:
        customer_metadata["created_by_user_id"] = user_id
    customer_metadata["created_at"] = datetime.utcnow().isoformat()
    customer_metadata["billing_type"] = "organization"

    customer_data = {
        "customer": {
            "external_id": org_id,  # Organization ID as customer identifier
            "name": org_name,
            "email": email,
            "metadata": customer_metadata
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LAGO_API_URL}/api/v1/customers",
                headers={
                    "Authorization": f"Bearer {LAGO_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=customer_data,
                timeout=API_TIMEOUT
            )

            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Created Lago customer for org: {org_id} ({org_name})")
                return result.get("customer", result)
            elif response.status_code == 422:
                # Customer might already exist
                logger.warning(f"Customer already exists for org: {org_id}")
                return await get_customer(org_id)
            else:
                error_msg = f"Failed to create customer: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise LagoIntegrationError(error_msg)

    except httpx.RequestError as e:
        error_msg = f"Network error creating customer: {e}"
        logger.error(error_msg)
        raise LagoIntegrationError(error_msg)


async def get_customer(org_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve customer information from Lago by organization ID.

    Args:
        org_id: Organization ID (external_id in Lago)

    Returns:
        Customer data or None if not found
    """
    if not LAGO_API_KEY:
        logger.error("LAGO_API_KEY not configured")
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{LAGO_API_URL}/api/v1/customers/{org_id}",
                headers={"Authorization": f"Bearer {LAGO_API_KEY}"},
                timeout=API_TIMEOUT
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("customer", result)
            elif response.status_code == 404:
                logger.info(f"Customer not found for org: {org_id}")
                return None
            else:
                logger.error(f"Failed to get customer: {response.status_code} - {response.text}")
                return None

    except httpx.RequestError as e:
        logger.error(f"Network error getting customer: {e}")
        return None


async def update_org_customer(
    org_id: str,
    org_name: Optional[str] = None,
    email: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update organization customer information in Lago.

    Args:
        org_id: Organization ID
        org_name: Updated organization name
        email: Updated email
        metadata: Additional metadata to update

    Returns:
        Updated customer data

    Raises:
        LagoIntegrationError: If update fails
    """
    if not LAGO_API_KEY:
        raise LagoIntegrationError("LAGO_API_KEY not configured")

    update_data = {"customer": {}}

    if org_name:
        update_data["customer"]["name"] = org_name
    if email:
        update_data["customer"]["email"] = email
    if metadata:
        update_data["customer"]["metadata"] = metadata

    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{LAGO_API_URL}/api/v1/customers/{org_id}",
                headers={
                    "Authorization": f"Bearer {LAGO_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=update_data,
                timeout=API_TIMEOUT
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Updated Lago customer for org: {org_id}")
                return result.get("customer", result)
            else:
                error_msg = f"Failed to update customer: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise LagoIntegrationError(error_msg)

    except httpx.RequestError as e:
        error_msg = f"Network error updating customer: {e}"
        logger.error(error_msg)
        raise LagoIntegrationError(error_msg)


async def get_or_create_customer(
    org_id: str,
    org_name: str,
    email: str,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get existing customer or create new one for organization.
    This is the main entry point for ensuring a customer exists.

    Args:
        org_id: Organization ID
        org_name: Organization name
        email: Organization contact email
        user_id: User ID who owns/created the org
        metadata: Additional metadata

    Returns:
        Customer data from Lago

    Raises:
        LagoIntegrationError: If operation fails
    """
    # Try to get existing customer
    customer = await get_customer(org_id)

    if customer:
        logger.info(f"Found existing Lago customer for org: {org_id}")
        return customer

    # Customer doesn't exist, create new one
    logger.info(f"Creating new Lago customer for org: {org_id}")
    return await create_org_customer(org_id, org_name, email, user_id, metadata)


# ============================================
# Subscription Management
# ============================================

async def create_subscription(
    org_id: str,
    plan_code: str,
    billing_time: str = "anniversary",
    subscription_at: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a subscription for an organization.

    Args:
        org_id: Organization ID (customer external_id)
        plan_code: Lago plan code (e.g., "professional_monthly")
        billing_time: When to bill ("calendar" or "anniversary")
        subscription_at: Start date (ISO format), defaults to now

    Returns:
        Subscription data from Lago

    Raises:
        LagoIntegrationError: If subscription creation fails
    """
    if not LAGO_API_KEY:
        raise LagoIntegrationError("LAGO_API_KEY not configured")

    subscription_data = {
        "subscription": {
            "external_customer_id": org_id,
            "external_id": f"{org_id}_{plan_code}_{int(datetime.utcnow().timestamp())}",  # Unique subscription ID
            "plan_code": plan_code,
            "billing_time": billing_time
        }
    }

    if subscription_at:
        subscription_data["subscription"]["subscription_at"] = subscription_at

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LAGO_API_URL}/api/v1/subscriptions",
                headers={
                    "Authorization": f"Bearer {LAGO_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=subscription_data,
                timeout=API_TIMEOUT
            )

            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Created subscription for org {org_id}: {plan_code}")
                return result.get("subscription", result)
            else:
                error_msg = f"Failed to create subscription: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise LagoIntegrationError(error_msg)

    except httpx.RequestError as e:
        error_msg = f"Network error creating subscription: {e}"
        logger.error(error_msg)
        raise LagoIntegrationError(error_msg)


async def subscribe_org_to_plan(
    org_id: str,
    plan_code: str,
    org_name: str,
    email: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Subscribe an organization to a plan (creates customer if needed).
    This is a convenience function that handles both customer and subscription creation.

    Args:
        org_id: Organization ID
        plan_code: Lago plan code
        org_name: Organization name
        email: Contact email
        user_id: User ID who owns the org

    Returns:
        Subscription data

    Raises:
        LagoIntegrationError: If operation fails
    """
    # Ensure customer exists
    await get_or_create_customer(org_id, org_name, email, user_id)

    # Create subscription
    return await create_subscription(org_id, plan_code)


async def get_subscription(org_id: str) -> Optional[Dict[str, Any]]:
    """
    Get active subscription for an organization.

    Args:
        org_id: Organization ID

    Returns:
        Subscription data or None if no active subscription
    """
    if not LAGO_API_KEY:
        logger.error("LAGO_API_KEY not configured")
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{LAGO_API_URL}/api/v1/subscriptions",
                headers={"Authorization": f"Bearer {LAGO_API_KEY}"},
                params={"external_customer_id": org_id},
                timeout=API_TIMEOUT
            )

            if response.status_code == 200:
                result = response.json()
                subscriptions = result.get("subscriptions", [])
                # Return first active subscription
                for sub in subscriptions:
                    if sub.get("status") == "active":
                        return sub
                return None
            else:
                logger.error(f"Failed to get subscription: {response.status_code} - {response.text}")
                return None

    except httpx.RequestError as e:
        logger.error(f"Network error getting subscription: {e}")
        return None


async def terminate_subscription(
    org_id: str,
    subscription_id: Optional[str] = None
) -> bool:
    """
    Terminate/cancel a subscription for an organization.

    Args:
        org_id: Organization ID
        subscription_id: Specific subscription ID (optional, will find active if not provided)

    Returns:
        True if successful, False otherwise
    """
    if not LAGO_API_KEY:
        logger.error("LAGO_API_KEY not configured")
        return False

    # If no subscription_id provided, find active subscription
    if not subscription_id:
        subscription = await get_subscription(org_id)
        if not subscription:
            logger.warning(f"No active subscription found for org: {org_id}")
            return False
        subscription_id = subscription.get("lago_id")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{LAGO_API_URL}/api/v1/subscriptions/{subscription_id}",
                headers={"Authorization": f"Bearer {LAGO_API_KEY}"},
                timeout=API_TIMEOUT
            )

            if response.status_code in [200, 204]:
                logger.info(f"Terminated subscription {subscription_id} for org: {org_id}")
                return True
            else:
                logger.error(f"Failed to terminate subscription: {response.status_code} - {response.text}")
                return False

    except httpx.RequestError as e:
        logger.error(f"Network error terminating subscription: {e}")
        return False


# ============================================
# Usage/Event Recording
# ============================================

async def record_usage(
    org_id: str,
    event_code: str,
    transaction_id: str,
    properties: Optional[Dict[str, Any]] = None,
    timestamp: Optional[int] = None
) -> bool:
    """
    Record a usage event for an organization.

    Args:
        org_id: Organization ID
        event_code: Event code defined in Lago plan
        transaction_id: Unique transaction identifier
        properties: Event properties (e.g., {"tokens": 1500, "model": "gpt-4"})
        timestamp: Unix timestamp (defaults to now)

    Returns:
        True if successful, False otherwise
    """
    if not LAGO_API_KEY:
        logger.error("LAGO_API_KEY not configured")
        return False

    event_data = {
        "event": {
            "transaction_id": transaction_id,
            "external_customer_id": org_id,
            "code": event_code,
            "timestamp": timestamp or int(datetime.utcnow().timestamp()),
            "properties": properties or {}
        }
    }

    # Add org_id to properties for filtering/reporting
    event_data["event"]["properties"]["org_id"] = org_id

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LAGO_API_URL}/api/v1/events",
                headers={
                    "Authorization": f"Bearer {LAGO_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=event_data,
                timeout=API_TIMEOUT
            )

            if response.status_code in [200, 201]:
                logger.debug(f"Recorded usage event {event_code} for org: {org_id}")
                return True
            else:
                logger.error(f"Failed to record usage: {response.status_code} - {response.text}")
                return False

    except httpx.RequestError as e:
        logger.error(f"Network error recording usage: {e}")
        return False


async def record_api_call(
    org_id: str,
    transaction_id: str,
    endpoint: str,
    user_id: Optional[str] = None,
    tokens: int = 0,
    model: Optional[str] = None
) -> bool:
    """
    Record an API call usage event.
    Convenience wrapper for record_usage with API-specific properties.

    Args:
        org_id: Organization ID
        transaction_id: Unique transaction ID
        endpoint: API endpoint called
        user_id: User who made the call (for attribution)
        tokens: Number of tokens used
        model: AI model used (if applicable)

    Returns:
        True if successful, False otherwise
    """
    properties = {
        "endpoint": endpoint,
        "user_id": user_id or "unknown",
        "tokens": tokens,
    }

    if model:
        properties["model"] = model

    return await record_usage(org_id, "api_call", transaction_id, properties)


# ============================================
# Invoice and Billing Info
# ============================================

async def get_invoices(org_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get invoices for an organization.

    Args:
        org_id: Organization ID
        limit: Maximum number of invoices to return

    Returns:
        List of invoice data
    """
    if not LAGO_API_KEY:
        logger.error("LAGO_API_KEY not configured")
        return []

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{LAGO_API_URL}/api/v1/invoices",
                headers={"Authorization": f"Bearer {LAGO_API_KEY}"},
                params={"external_customer_id": org_id, "per_page": limit},
                timeout=API_TIMEOUT
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("invoices", [])
            else:
                logger.error(f"Failed to get invoices: {response.status_code} - {response.text}")
                return []

    except httpx.RequestError as e:
        logger.error(f"Network error getting invoices: {e}")
        return []


async def get_current_usage(org_id: str) -> Dict[str, Any]:
    """
    Get current billing period usage for an organization.

    Args:
        org_id: Organization ID

    Returns:
        Usage data with breakdown by event type
    """
    if not LAGO_API_KEY:
        logger.error("LAGO_API_KEY not configured")
        return {}

    subscription = await get_subscription(org_id)
    if not subscription:
        logger.warning(f"No active subscription for org: {org_id}")
        return {}

    subscription_id = subscription.get("lago_id")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{LAGO_API_URL}/api/v1/subscriptions/{subscription_id}/usage",
                headers={"Authorization": f"Bearer {LAGO_API_KEY}"},
                timeout=API_TIMEOUT
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get usage: {response.status_code} - {response.text}")
                return {}

    except httpx.RequestError as e:
        logger.error(f"Network error getting usage: {e}")
        return {}


# ============================================
# Migration Helpers
# ============================================

async def migrate_user_to_org(
    user_id: str,
    org_id: str,
    org_name: str,
    email: str
) -> bool:
    """
    Migrate an existing user-based customer to org-based customer.
    This is for backward compatibility during migration.

    Args:
        user_id: Old user-based customer ID
        org_id: New organization ID
        org_name: Organization name
        email: Email address

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Migrating customer from user_id {user_id} to org_id {org_id}")

    # Check if user-based customer exists
    old_customer = await get_customer(user_id)

    if not old_customer:
        logger.info(f"No existing customer for user_id {user_id}, creating new org customer")
        try:
            await create_org_customer(org_id, org_name, email, user_id=user_id)
            return True
        except LagoIntegrationError as e:
            logger.error(f"Failed to create org customer: {e}")
            return False

    # Customer exists with user_id, need to create org customer and migrate
    logger.info(f"Found existing customer {user_id}, creating org customer {org_id}")

    try:
        # Create new org customer
        metadata = old_customer.get("metadata", {})
        metadata["migrated_from_user_id"] = user_id
        metadata["migration_date"] = datetime.utcnow().isoformat()

        await create_org_customer(org_id, org_name, email, user_id=user_id, metadata=metadata)

        # Note: Manual migration of subscriptions may be needed
        # This depends on Lago's capabilities and business requirements
        logger.warning(f"Created org customer {org_id}. Manual subscription migration may be needed from {user_id}")

        return True

    except LagoIntegrationError as e:
        logger.error(f"Failed to migrate customer: {e}")
        return False


def is_org_customer(external_id: str) -> bool:
    """
    Check if an external_id is an org_id or user_id based on format.
    This is a helper for backward compatibility.

    Args:
        external_id: Customer external ID

    Returns:
        True if it appears to be an org_id, False if user_id
    """
    # Implement based on your ID format
    # Example: org IDs start with "org_", user IDs start with "user_"
    if external_id.startswith("org_"):
        return True
    elif external_id.startswith("user_"):
        return False
    else:
        # Default assumption based on length or other heuristics
        # Adjust based on your actual ID formats
        logger.warning(f"Cannot determine if {external_id} is org or user ID")
        return len(external_id) > 20  # Example heuristic


# ============================================
# Health Check
# ============================================

async def check_lago_health() -> Dict[str, Any]:
    """
    Check if Lago API is accessible and responding.

    Returns:
        Health status dictionary
    """
    if not LAGO_API_KEY:
        return {
            "status": "error",
            "message": "LAGO_API_KEY not configured"
        }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{LAGO_API_URL}/health",
                timeout=5.0
            )

            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "api_url": LAGO_API_URL,
                    "message": "Lago API is accessible"
                }
            else:
                return {
                    "status": "unhealthy",
                    "api_url": LAGO_API_URL,
                    "message": f"Lago API returned {response.status_code}"
                }

    except httpx.RequestError as e:
        return {
            "status": "error",
            "api_url": LAGO_API_URL,
            "message": f"Cannot connect to Lago API: {e}"
        }


# ============================================
# NEW METHODS: Epic 2.4 - Subscription Changes
# ============================================

async def update_subscription_plan(
    org_id: str,
    new_plan_code: str,
    effective_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing subscription to a new plan.
    This is the recommended way to change plans (vs terminate+create).

    Args:
        org_id: Organization ID
        new_plan_code: New Lago plan code (e.g., "professional_monthly")
        effective_date: When change takes effect (ISO format), defaults to now

    Returns:
        Updated subscription data

    Raises:
        LagoIntegrationError: If update fails
    """
    if not LAGO_API_KEY:
        raise LagoIntegrationError("LAGO_API_KEY not configured")

    # Get current subscription
    current_sub = await get_subscription(org_id)
    if not current_sub:
        raise LagoIntegrationError(f"No active subscription for org {org_id}")

    subscription_id = current_sub.get("external_id")

    update_data = {
        "subscription": {
            "plan_code": new_plan_code
        }
    }

    if effective_date:
        update_data["subscription"]["subscription_at"] = effective_date

    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{LAGO_API_URL}/api/v1/subscriptions/{subscription_id}",
                headers={
                    "Authorization": f"Bearer {LAGO_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=update_data,
                timeout=API_TIMEOUT
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Updated subscription for org {org_id} to plan {new_plan_code}")
                return result.get("subscription", result)
            else:
                error_msg = f"Failed to update subscription: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise LagoIntegrationError(error_msg)

    except httpx.RequestError as e:
        error_msg = f"Network error updating subscription: {e}"
        logger.error(error_msg)
        raise LagoIntegrationError(error_msg)


async def schedule_plan_change(
    org_id: str,
    new_plan_code: str,
    effective_date: str
) -> bool:
    """
    Schedule a subscription plan change for future date.
    Note: Lago doesn't natively support scheduled changes, so we store
    this in our database and process it via scheduled job.

    Args:
        org_id: Organization ID
        new_plan_code: New plan code
        effective_date: When change takes effect (ISO format)

    Returns:
        True if scheduled successfully

    Raises:
        LagoIntegrationError: If scheduling fails
    """
    logger.info(f"Scheduling plan change for {org_id} to {new_plan_code} on {effective_date}")

    # This would be handled by the database layer in subscription_api.py
    # Just validate the plan exists in Lago
    # In production, you'd query Lago for plan availability

    # For now, just log and return success
    # The actual scheduling is done in the subscription_api downgrade endpoint
    return True


async def calculate_proration(
    org_id: str,
    current_plan_code: str,
    new_plan_code: str,
    days_remaining: int
) -> Dict[str, float]:
    """
    Calculate proration amount for plan change.
    This is a simple calculation - Stripe handles actual billing.

    Args:
        org_id: Organization ID
        current_plan_code: Current plan code
        new_plan_code: New plan code
        days_remaining: Days remaining in current period

    Returns:
        Dict with proration amounts
    """
    # This is a simple calculation
    # In production, you'd query plan prices from Lago or subscription_manager

    # For now, return placeholder values
    # Actual proration is handled by Stripe
    return {
        "current_plan": current_plan_code,
        "new_plan": new_plan_code,
        "days_remaining": days_remaining,
        "proration_amount": 0.0,
        "note": "Proration calculated by Stripe"
    }
