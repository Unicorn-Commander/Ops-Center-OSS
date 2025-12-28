"""
Pydantic Models for Extensions Marketplace API

All request/response models for add-ons, cart, purchases, and admin operations.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID


# ============================================================================
# Add-On Models (Catalog)
# ============================================================================

class AddOnResponse(BaseModel):
    """Basic add-on information for catalog listings"""
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    category: str
    base_price: Decimal
    billing_type: str  # one_time, monthly, annually
    features: List[str] = []
    icon_url: Optional[str] = None
    is_featured: bool = False
    is_active: bool = True
    install_count: int = 0
    rating_avg: Decimal = Decimal('0.00')
    rating_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class AddOnDetailResponse(AddOnResponse):
    """Detailed add-on information including long description"""
    long_description: Optional[str] = None
    banner_url: Optional[str] = None
    documentation_url: Optional[str] = None
    support_url: Optional[str] = None
    metadata: Dict[str, Any] = {}
    trial_days: int = 0

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class AddOnCreateRequest(BaseModel):
    """Request body for creating a new add-on (admin)"""
    name: str = Field(..., min_length=3, max_length=255)
    slug: str = Field(..., min_length=3, max_length=255, regex=r'^[a-z0-9-]+$')
    description: Optional[str] = Field(None, max_length=500)
    long_description: Optional[str] = None
    category: str
    base_price: Decimal = Field(..., ge=0)
    billing_type: str = Field(default='one_time')
    trial_days: int = Field(default=0, ge=0)
    features: List[str] = []
    metadata: Dict[str, Any] = {}
    icon_url: Optional[str] = None
    banner_url: Optional[str] = None
    documentation_url: Optional[str] = None
    support_url: Optional[str] = None
    is_featured: bool = False
    is_active: bool = True
    is_public: bool = True

    @validator('category')
    def validate_category(cls, v):
        valid_categories = {'ai_tools', 'monitoring', 'storage', 'security',
                            'networking', 'analytics', 'integrations', 'utilities', 'other'}
        if v not in valid_categories:
            raise ValueError(f'Category must be one of {valid_categories}')
        return v

    @validator('billing_type')
    def validate_billing_type(cls, v):
        if v not in {'one_time', 'monthly', 'annually'}:
            raise ValueError('billing_type must be one_time, monthly, or annually')
        return v


class AddOnUpdateRequest(BaseModel):
    """Request body for updating an add-on (admin)"""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    long_description: Optional[str] = None
    category: Optional[str] = None
    base_price: Optional[Decimal] = Field(None, ge=0)
    billing_type: Optional[str] = None
    trial_days: Optional[int] = Field(None, ge=0)
    features: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    icon_url: Optional[str] = None
    banner_url: Optional[str] = None
    documentation_url: Optional[str] = None
    support_url: Optional[str] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class CategoryResponse(BaseModel):
    """Category information with add-on count"""
    name: str
    display_name: str
    addon_count: int
    icon: Optional[str] = None


# ============================================================================
# Cart Models
# ============================================================================

class CartItemResponse(BaseModel):
    """Cart item with add-on details"""
    id: UUID
    add_on: AddOnResponse
    quantity: int
    subtotal: Decimal
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class CartResponse(BaseModel):
    """Full cart response with items and totals"""
    items: List[CartItemResponse]
    subtotal: Decimal
    discount: Decimal = Decimal('0.00')
    total: Decimal
    promo_code: Optional[str] = None

    class Config:
        json_encoders = {
            UUID: str,
            Decimal: lambda v: float(v)
        }


class AddToCartRequest(BaseModel):
    """Request to add add-on to cart"""
    add_on_id: UUID
    quantity: int = Field(default=1, ge=1, le=10)


class UpdateCartItemRequest(BaseModel):
    """Request to update cart item quantity"""
    quantity: int = Field(..., ge=1, le=10)


# ============================================================================
# Purchase Models
# ============================================================================

class PurchaseResponse(BaseModel):
    """Purchase/subscription record"""
    id: UUID
    user_id: str
    add_on: AddOnResponse
    amount: Decimal
    currency: str = 'USD'
    billing_type: str
    status: str  # pending, active, canceled, expired, failed
    is_active: bool
    subscription_id: Optional[str] = None
    subscription_status: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    activated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    purchased_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class ActiveAddOnResponse(BaseModel):
    """Active add-on with feature details"""
    add_on: AddOnResponse
    purchase: PurchaseResponse
    features: List[Dict[str, Any]] = []

    class Config:
        json_encoders = {
            UUID: str,
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class CheckoutRequest(BaseModel):
    """Request to create Stripe Checkout Session"""
    cart_items: List[UUID] = []  # List of cart item IDs (empty = entire cart)
    promo_code: Optional[str] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutResponse(BaseModel):
    """Stripe Checkout Session response"""
    checkout_url: str
    session_id: str
    amount: Decimal
    currency: str = 'USD'

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class ActivatePurchaseResponse(BaseModel):
    """Response after activating a purchase"""
    success: bool
    purchase_id: UUID
    features_granted: List[str] = []
    message: Optional[str] = None

    class Config:
        json_encoders = {
            UUID: str
        }


class InvoiceResponse(BaseModel):
    """Invoice information"""
    id: UUID
    purchase_id: UUID
    amount: Decimal
    currency: str
    status: str
    invoice_date: datetime
    due_date: Optional[datetime] = None
    paid_date: Optional[datetime] = None
    stripe_invoice_id: Optional[str] = None
    download_url: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# Admin Models
# ============================================================================

class AnalyticsResponse(BaseModel):
    """Sales analytics data"""
    total_revenue: Decimal
    total_sales: int
    active_subscriptions: int
    top_sellers: List[Dict[str, Any]] = []
    revenue_by_category: Dict[str, Decimal] = {}
    sales_trend: List[Dict[str, Any]] = []  # Daily/weekly/monthly trend data

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class PromoCodeResponse(BaseModel):
    """Promotional code information"""
    id: UUID
    code: str
    discount_type: str  # percentage, fixed_amount
    discount_value: Decimal
    min_purchase_amount: Decimal = Decimal('0.00')
    max_uses: Optional[int] = None
    times_used: int = 0
    applicable_addon_ids: Optional[List[UUID]] = None
    is_active: bool = True
    expires_at: Optional[datetime] = None
    created_at: datetime
    created_by: str

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class PromoCodeCreateRequest(BaseModel):
    """Request to create promotional code"""
    code: str = Field(..., min_length=3, max_length=50, regex=r'^[A-Z0-9_-]+$')
    discount_type: str
    discount_value: Decimal = Field(..., gt=0)
    min_purchase_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    max_uses: Optional[int] = Field(None, gt=0)
    applicable_addon_ids: Optional[List[UUID]] = None
    expires_at: Optional[datetime] = None

    @validator('discount_type')
    def validate_discount_type(cls, v):
        if v not in {'percentage', 'fixed_amount'}:
            raise ValueError('discount_type must be percentage or fixed_amount')
        return v

    @validator('discount_value')
    def validate_discount_value(cls, v, values):
        if 'discount_type' in values and values['discount_type'] == 'percentage':
            if v > 100:
                raise ValueError('Percentage discount cannot exceed 100%')
        return v
