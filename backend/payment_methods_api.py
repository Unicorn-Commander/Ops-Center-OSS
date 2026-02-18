"""
Payment Methods API Router
RESTful API endpoints for managing user payment methods
"""

import logging
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from payment_methods_manager import PaymentMethodsManager
from dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payment-methods", tags=["payment-methods"])

# Initialize payment methods manager (Lago client optional for now)
payment_methods_manager = PaymentMethodsManager(lago_client=None)


# Request/Response Models
class SetupIntentRequest(BaseModel):
    """Request to create a SetupIntent"""
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict)


class SetupIntentResponse(BaseModel):
    """Response with SetupIntent client secret"""
    client_secret: str
    setup_intent_id: str


class SetDefaultRequest(BaseModel):
    """Request to set default payment method"""
    pass  # payment_method_id comes from path


class RemovePaymentMethodRequest(BaseModel):
    """Request to remove payment method"""
    pass  # payment_method_id comes from path


class BillingAddress(BaseModel):
    """Billing address model"""
    line1: str = Field(..., min_length=1, max_length=200)
    line2: Optional[str] = Field(None, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(default="US", min_length=2, max_length=2)


class UpdateBillingAddressRequest(BaseModel):
    """Request to update billing address"""
    address: BillingAddress


class PaymentMethodResponse(BaseModel):
    """Payment method details"""
    id: str
    brand: str
    last4: str
    exp_month: int
    exp_year: int
    is_default: bool
    expires_soon: bool
    country: Optional[str]
    funding: Optional[str]
    created: int


class PaymentMethodsListResponse(BaseModel):
    """List of payment methods"""
    payment_methods: list[PaymentMethodResponse]
    default_payment_method_id: Optional[str]
    count: int


class UpcomingInvoiceResponse(BaseModel):
    """Upcoming invoice details"""
    amount_due: int
    amount_remaining: int
    currency: str
    next_payment_attempt: Optional[int]
    period_start: int
    period_end: int
    default_payment_method: Optional[Dict]
    lines: list[Dict]
    subtotal: int
    tax: Optional[int]
    total: int


# Dependency: Get PaymentMethodsManager
def get_payment_methods_manager() -> PaymentMethodsManager:
    """Get configured PaymentMethodsManager instance"""
    # Using global payment_methods_manager instance (initialized at module level)
    return payment_methods_manager


@router.get(
    "",
    response_model=PaymentMethodsListResponse,
    summary="List Payment Methods",
    description="Get all payment methods for the current user"
)
async def list_payment_methods(
    user: Dict = Depends(get_current_user),
    pm_manager: PaymentMethodsManager = Depends(get_payment_methods_manager)
):
    """
    List all payment methods for authenticated user

    Returns:
        PaymentMethodsListResponse with all cards and default
    """
    try:
        # Get user's email
        user_email = user.get("user", {}).get("email") or user.get("email")
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User email not found"
            )

        # Get Stripe customer ID from Lago
        stripe_customer_id = await pm_manager.get_stripe_customer_id(user_email)
        if not stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found in billing system"
            )

        # Fetch payment methods from Stripe
        result = await pm_manager.list_payment_methods(stripe_customer_id)

        return PaymentMethodsListResponse(
            payment_methods=[
                PaymentMethodResponse(**pm) for pm in result["payment_methods"]
            ],
            default_payment_method_id=result["default_payment_method_id"],
            count=result["count"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing payment methods: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve payment methods: {str(e)}"
        )


@router.post(
    "/setup-intent",
    response_model=SetupIntentResponse,
    summary="Create Setup Intent",
    description="Create a Stripe SetupIntent for adding a new payment method"
)
async def create_setup_intent(
    request: SetupIntentRequest = None,
    user: Dict = Depends(get_current_user),
    pm_manager: PaymentMethodsManager = Depends(get_payment_methods_manager)
):
    """
    Create a SetupIntent for adding a new payment method

    The client_secret returned should be used with Stripe Elements
    to collect and confirm the payment method.

    Returns:
        SetupIntentResponse with client_secret
    """
    try:
        # Get user's email
        user_email = user.get("user", {}).get("email") or user.get("email")
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User email not found"
            )

        # Get Stripe customer ID from Lago
        stripe_customer_id = await pm_manager.get_stripe_customer_id(user_email)
        if not stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found in billing system"
            )

        # Create SetupIntent
        metadata = request.metadata if request else {}
        metadata["user_email"] = user_email

        result = await pm_manager.create_setup_intent(
            stripe_customer_id=stripe_customer_id,
            metadata=metadata
        )

        return SetupIntentResponse(
            client_secret=result["client_secret"],
            setup_intent_id=result["setup_intent_id"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating SetupIntent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment setup: {str(e)}"
        )


@router.post(
    "/{payment_method_id}/set-default",
    summary="Set Default Payment Method",
    description="Set a payment method as the default for future invoices"
)
async def set_default_payment_method(
    payment_method_id: str,
    user: Dict = Depends(get_current_user),
    pm_manager: PaymentMethodsManager = Depends(get_payment_methods_manager)
):
    """
    Set a payment method as the default for invoices

    Args:
        payment_method_id: Stripe payment method ID

    Returns:
        Success message
    """
    try:
        # Get user's email
        user_email = user.get("user", {}).get("email") or user.get("email")
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User email not found"
            )

        # Get Stripe customer ID from Lago
        stripe_customer_id = await pm_manager.get_stripe_customer_id(user_email)
        if not stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found in billing system"
            )

        # Set as default
        success = await pm_manager.set_default_payment_method(
            stripe_customer_id=stripe_customer_id,
            payment_method_id=payment_method_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set default payment method"
            )

        return {
            "success": True,
            "message": "Default payment method updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting default payment method: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set default payment method: {str(e)}"
        )


@router.delete(
    "/{payment_method_id}",
    summary="Remove Payment Method",
    description="Remove a payment method from the customer"
)
async def remove_payment_method(
    payment_method_id: str,
    user: Dict = Depends(get_current_user),
    pm_manager: PaymentMethodsManager = Depends(get_payment_methods_manager)
):
    """
    Remove a payment method

    Cannot remove the last payment method if subscription is active.

    Args:
        payment_method_id: Stripe payment method ID

    Returns:
        Success message
    """
    try:
        # Get user's email
        user_email = user.get("user", {}).get("email") or user.get("email")
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User email not found"
            )

        # Get Stripe customer ID from Lago
        stripe_customer_id = await pm_manager.get_stripe_customer_id(user_email)
        if not stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found in billing system"
            )

        # Remove payment method
        success = await pm_manager.remove_payment_method(
            stripe_customer_id=stripe_customer_id,
            payment_method_id=payment_method_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove payment method"
            )

        return {
            "success": True,
            "message": "Payment method removed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing payment method: {e}")

        # Check for specific error about last payment method
        if "last payment method" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove payment method: {str(e)}"
        )


@router.put(
    "/billing-address",
    summary="Update Billing Address",
    description="Update the billing address for the customer"
)
async def update_billing_address(
    request: UpdateBillingAddressRequest,
    user: Dict = Depends(get_current_user),
    pm_manager: PaymentMethodsManager = Depends(get_payment_methods_manager)
):
    """
    Update billing address

    Updates address in both Stripe and Lago.

    Returns:
        Success message
    """
    try:
        # Get user's email
        user_email = user.get("user", {}).get("email") or user.get("email")
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User email not found"
            )

        # Get Stripe customer ID from Lago
        stripe_customer_id = await pm_manager.get_stripe_customer_id(user_email)
        if not stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found in billing system"
            )

        # Update billing address
        address_dict = request.address.dict()
        success = await pm_manager.update_billing_address(
            stripe_customer_id=stripe_customer_id,
            address=address_dict
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update billing address"
            )

        return {
            "success": True,
            "message": "Billing address updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating billing address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update billing address: {str(e)}"
        )


@router.get(
    "/upcoming-invoice",
    response_model=UpcomingInvoiceResponse,
    summary="Get Upcoming Invoice",
    description="Get the next invoice that will be charged"
)
async def get_upcoming_invoice(
    user: Dict = Depends(get_current_user),
    pm_manager: PaymentMethodsManager = Depends(get_payment_methods_manager)
):
    """
    Get upcoming invoice

    Shows the next charge amount, date, and payment method.

    Returns:
        UpcomingInvoiceResponse with invoice details
    """
    try:
        # Get user's email
        user_email = user.get("user", {}).get("email") or user.get("email")
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User email not found"
            )

        # Get Stripe customer ID from Lago
        stripe_customer_id = await pm_manager.get_stripe_customer_id(user_email)
        if not stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found in billing system"
            )

        # Get upcoming invoice
        invoice = await pm_manager.get_upcoming_invoice(stripe_customer_id)

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No upcoming invoice found. You may not have an active subscription."
            )

        return UpcomingInvoiceResponse(**invoice)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching upcoming invoice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve upcoming invoice: {str(e)}"
        )


@router.get(
    "/{payment_method_id}/details",
    summary="Get Payment Method Details",
    description="Get detailed information about a specific payment method"
)
async def get_payment_method_details(
    payment_method_id: str,
    user: Dict = Depends(get_current_user),
    pm_manager: PaymentMethodsManager = Depends(get_payment_methods_manager)
):
    """
    Get payment method details

    Args:
        payment_method_id: Stripe payment method ID

    Returns:
        Payment method details
    """
    try:
        # Get user's email
        user_email = user.get("user", {}).get("email") or user.get("email")
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User email not found"
            )

        # Get Stripe customer ID from Lago
        stripe_customer_id = await pm_manager.get_stripe_customer_id(user_email)
        if not stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found in billing system"
            )

        # Get payment method details
        details = await pm_manager.get_payment_method_details(payment_method_id)

        if not details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment method not found"
            )

        # Verify it belongs to the customer
        if details.get("customer") != stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Payment method does not belong to this customer"
            )

        return details

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching payment method details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve payment method details: {str(e)}"
        )
