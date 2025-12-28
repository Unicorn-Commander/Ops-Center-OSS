# New Billing Model Specification

**Date**: October 28, 2025
**Status**: Requirements Defined - Ready for Implementation

---

## User Requirements

Per user request on October 28, 2025:

> "Maybe we should have the admin on a Free plan as far as subscription (admin can assign it, but it's not available to be selected), and then they only have to charge their account for credits and stuff. For everyone else, BYOK is $30/month and Everyone else is $50 a month (comes with a certain amount of tokens, and both byok and "managed" can charge up tokens through Unicorn Commander, at any time)."

---

## Billing Model Overview

### Three-Tier Structure

1. **Admin Plan** (Free - Admin Only)
2. **BYOK Plan** (Bring Your Own Key) - $30/month
3. **Managed Plan** - $50/month (includes tokens)

---

## Plan Details

### 1. Admin Plan (Free)

**Price**: $0/month

**Who Gets It**:
- Platform administrators only
- Cannot be selected by regular users
- Can only be assigned by admin

**Features**:
- Full system access
- No subscription fees
- Pay-as-you-go for usage
- Credits charged to account when consumed
- All admin features included

**Credit System**:
- Must charge credits to account
- Credits consumed as services are used
- Billing for actual usage only
- No monthly minimum

**Availability**:
- Not visible in plan selection UI for regular users
- Only assignable via admin dashboard
- Identified by: `tier: "admin"` or `tier: "free-admin"`

---

### 2. BYOK Plan (Bring Your Own Key)

**Price**: $30/month

**Target Users**:
- Users who have their own API keys
- Technical users who want control
- Cost-conscious users with existing keys

**Features**:
- Use your own LLM API keys (OpenAI, Anthropic, Google, etc.)
- Access to all platform features
- UI/UX for managing API workflows
- Credit system available for platform services

**API Key Management**:
- Users provide their own:
  - OpenAI API key
  - Anthropic API key
  - Google AI API key
  - OpenRouter API key
  - Any other provider keys
- Keys stored encrypted in database
- User responsible for API key costs directly with provider

**Credit System**:
- Can purchase credits for:
  - Platform services (STT, TTS, OCR, Search, etc.)
  - Infrastructure usage beyond free tier
  - Premium features
- Credits charged to Unicorn Commander account
- Separate from LLM API costs (paid direct to provider)

**Monthly Billing**:
- $30/month subscription fee
- Billed monthly via Stripe
- Auto-renewal
- Includes platform access, no included LLM usage

---

### 3. Managed Plan

**Price**: $50/month

**Target Users**:
- Users who want simplicity
- Don't want to manage API keys
- Want predictable pricing with included usage

**Features**:
- All platform features
- Managed LLM API keys (we handle providers)
- Included token allowance
- No API key management required

**Included Tokens** (to be defined):
- Option A: 1,000,000 tokens/month (~$10-20 value depending on model)
- Option B: $25 credit towards LLM usage
- Option C: Based on tier rules (e.g., 10K API calls as per current system)

**Credit System**:
- Included token/credit allowance each month
- Can purchase additional credits anytime
- Credits roll over (or expire monthly - to be decided)
- Same credit pricing as BYOK users

**Monthly Billing**:
- $50/month subscription fee
- Billed monthly via Stripe
- Includes base token allowance
- Additional usage billed as credits

---

## Credit System (Universal)

**Applies to**: All three plans

**How It Works**:
1. Users can purchase credits anytime
2. Credits used for:
   - LLM API calls (Managed plan)
   - STT/TTS services
   - OCR/document processing
   - Search queries
   - Any metered service
3. Credits charged from account as consumed
4. Low balance notifications
5. Auto-recharge option (optional)

**Credit Pricing** (to be defined):
- $10 = X credits
- $25 = Y credits
- $50 = Z credits
- $100 = W credits (best value)

**Credit Usage Rates** (to be defined):
- LLM API call: X credits per 1K tokens
- STT: X credits per minute
- TTS: X credits per 1K characters
- OCR: X credits per page
- Search: X credits per query

---

## Implementation Checklist

### Phase 1: Database Schema

- [ ] Add `admin` tier to valid tier constraint
- [ ] Or create `free-admin` tier distinct from `free`
- [ ] Update tier rules table
- [ ] Create migration script

### Phase 2: Lago Billing Integration

**Create New Plans**:

1. **Admin Plan**:
   - Plan code: `admin-free`
   - Amount: $0.00/month
   - Interval: monthly
   - Billable metrics: Credits only
   - NOT visible in public plan list

2. **BYOK Plan**:
   - Plan code: `byok`
   - Amount: $30.00/month
   - Interval: monthly
   - Billable metrics: Credits
   - Features: BYOK enabled
   - Public: Yes

3. **Managed Plan**:
   - Plan code: `managed`
   - Amount: $50.00/month
   - Interval: monthly
   - Billable metrics: Credits + included allowance
   - Features: All features
   - Public: Yes

**Configure Credits**:
- Add credit purchase packages
- Define credit usage rates
- Set up metering events
- Configure low-balance alerts

### Phase 3: Frontend Updates

**Plan Selection Page** (`/plans.html` or React component):

```jsx
// Pseudo-code
const publicPlans = [
  {
    name: "BYOK",
    price: "$30/month",
    description: "Bring your own API keys",
    features: [
      "Use your own LLM API keys",
      "All platform features",
      "Purchase credits for platform services",
      "Encrypted key storage"
    ]
  },
  {
    name: "Managed",
    price: "$50/month",
    description: "We handle everything",
    features: [
      "X,XXX included tokens/month",
      "Managed API keys",
      "All platform features",
      "Purchase additional credits anytime",
      "No key management required"
    ],
    recommended: true
  }
];

// Admin plan NOT shown here
```

**Admin Dashboard** - Plan Assignment:
- Admin can assign "Admin Free" plan to users
- Regular users cannot select it
- UI shows "Admin Assigned" for these users

**Account Settings** - For BYOK users:
- Add "Manage API Keys" section
- Show provider keys UI
- Add/edit/delete keys
- Test key validity

**Credit Management** (all plans):
- Show current credit balance
- "Purchase Credits" button
- Credit usage history
- Auto-recharge toggle

### Phase 4: Backend Updates

**Subscription Manager** (`backend/subscription_manager.py`):

```python
TIER_FEATURES = {
    "admin": {
        "monthly_fee": 0,
        "byok_enabled": True,
        "managed_keys": True,
        "included_credits": 0,
        "can_purchase_credits": True,
        "admin_only": True  # NEW FLAG
    },
    "byok": {
        "monthly_fee": 30,
        "byok_enabled": True,
        "managed_keys": False,
        "included_credits": 0,
        "can_purchase_credits": True,
        "stripe_price_id": "price_XXXXXXXXXX"
    },
    "managed": {
        "monthly_fee": 50,
        "byok_enabled": False,
        "managed_keys": True,
        "included_credits": 25.00,  # $25 in credits
        "can_purchase_credits": True,
        "stripe_price_id": "price_YYYYYYYYYY"
    }
}
```

**API Endpoints**:

```python
# Admin-only endpoint
@router.post("/api/v1/admin/users/{user_id}/assign-admin-plan")
async def assign_admin_plan(user_id: str, admin: dict = Depends(require_admin)):
    """Assign free admin plan to user (admin only)"""
    pass

# Credit purchase
@router.post("/api/v1/credits/purchase")
async def purchase_credits(
    amount: Decimal,
    user: dict = Depends(get_current_user)
):
    """Purchase credits for account"""
    # Create Stripe checkout session
    # Add credits to user account
    pass

# BYOK key management (already exists)
@router.post("/api/v1/byok/providers/{provider}/key")
async def save_provider_key(provider: str, api_key: str, ...):
    """Save encrypted API key for provider"""
    pass
```

### Phase 5: Stripe Configuration

**Create Products**:
1. BYOK Plan - $30/month recurring
2. Managed Plan - $50/month recurring
3. Credits (one-time purchase, multiple tiers)

**Create Prices**:
- BYOK: `price_byok_monthly_30usd`
- Managed: `price_managed_monthly_50usd`
- Credits $10: `price_credits_10usd`
- Credits $25: `price_credits_25usd`
- Credits $50: `price_credits_50usd`
- Credits $100: `price_credits_100usd`

**Webhooks**:
- `customer.subscription.created` - Assign tier
- `customer.subscription.updated` - Update tier
- `customer.subscription.deleted` - Downgrade tier
- `checkout.session.completed` - Add credits if one-time purchase

### Phase 6: Migration Plan

**For Existing Users**:

1. **Current Free Tier Users**:
   - Notify of new pricing
   - 30-day grace period
   - Choose BYOK or Managed
   - Or contact admin for Admin plan

2. **Current Trial Users**:
   - Complete trial
   - Choose BYOK or Managed
   - Apply trial discount if converting

3. **Current Paid Users** (Starter, Pro, Enterprise):
   - Map to new tiers:
     - Starter → BYOK (if using own keys) or Managed
     - Professional → Managed
     - Enterprise → Custom (contact sales)

**Migration SQL**:
```sql
-- Update admin users to free-admin tier
UPDATE user_credits
SET tier = 'admin'
WHERE user_id IN (SELECT user_id FROM keycloak_users WHERE role = 'admin');

-- Notify users of tier changes
-- (via email/notification system)
```

---

## Pricing Comparison

| Feature | Admin | BYOK | Managed |
|---------|-------|------|---------|
| **Monthly Fee** | $0 | $30 | $50 |
| **LLM API Keys** | Own | Own | Managed |
| **Included Tokens** | 0 | 0 | XXX,XXX |
| **Purchase Credits** | ✅ | ✅ | ✅ |
| **Platform Access** | ✅ | ✅ | ✅ |
| **STT/TTS** | Credits | Credits | Credits |
| **Who Gets It** | Admins only | Anyone | Anyone |
| **Key Management** | Optional | Required | Not needed |

---

## Credit Packages (Proposed)

| Package | Price | Credits | Bonus | Value |
|---------|-------|---------|-------|-------|
| Starter | $10 | 100 | 0% | - |
| Standard | $25 | 275 | 10% | $2.50 |
| Pro | $50 | 600 | 20% | $10.00 |
| Enterprise | $100 | 1,300 | 30% | $30.00 |

**Credit Usage Examples**:
- 1M GPT-4 tokens = ~50 credits (~$5)
- 1 hour STT = ~10 credits (~$1)
- 10K TTS chars = ~5 credits (~$0.50)
- 100 OCR pages = ~20 credits (~$2)

---

## User Flows

### Flow 1: New User - BYOK Plan

1. User visits your-domain.com
2. Clicks "Sign Up"
3. Chooses "BYOK - $30/month"
4. OAuth login (Google/GitHub/Microsoft)
5. Redirected to Stripe checkout
6. Pays $30/month
7. Account created with tier: `byok`
8. Redirected to dashboard
9. Prompted: "Add your API keys to get started"
10. Navigates to Settings → API Keys
11. Adds OpenAI key, saves (encrypted)
12. Can now use platform with own keys

### Flow 2: New User - Managed Plan

1. User visits your-domain.com
2. Clicks "Sign Up"
3. Chooses "Managed - $50/month" (recommended)
4. OAuth login
5. Redirected to Stripe checkout
6. Pays $50/month
7. Account created with tier: `managed`
8. XXX,XXX credits added to account
9. Redirected to dashboard
10. Can immediately start using platform
11. Credits deducted as they use services

### Flow 3: Admin Assigns Free Plan

1. Admin logs into admin dashboard
2. Goes to User Management
3. Finds user (e.g., team member)
4. Clicks "Edit User"
5. Changes tier to "Admin Free"
6. Confirms assignment
7. User notified via email
8. User's tier updated to `admin`
9. User pays $0/month
10. User can purchase credits for usage

### Flow 4: Purchasing Credits (Any Plan)

1. User in dashboard sees "Credits: 25.50 remaining"
2. Clicks "Purchase Credits"
3. Modal shows credit packages
4. Selects "$50 - 600 credits + 20% bonus"
5. Redirected to Stripe checkout
6. Pays $50
7. 600 credits added to account
8. Returns to dashboard
9. Balance now shows "625.50 credits"

---

## Business Logic

### Tier Access Control

```python
def can_use_byok(user):
    return user.tier in ["admin", "byok"]

def can_use_managed_keys(user):
    return user.tier in ["admin", "managed"]

def can_assign_admin_plan(user):
    return user.role == "admin"

def get_monthly_included_credits(user):
    if user.tier == "managed":
        return 25.00  # $25 in credits
    return 0

def can_purchase_credits(user):
    return True  # All tiers can purchase credits
```

### Credit Deduction

```python
async def consume_credits(user_id: str, amount: Decimal, service: str):
    user_credits = await get_user_credits(user_id)

    if user_credits.credits_remaining < amount:
        raise InsufficientCreditsError(
            f"Need {amount} credits, have {user_credits.credits_remaining}"
        )

    # Deduct credits
    user_credits.credits_remaining -= amount
    await update_user_credits(user_credits)

    # Log transaction
    await log_credit_transaction(
        user_id=user_id,
        amount=-amount,
        transaction_type="usage",
        service=service,
        balance_after=user_credits.credits_remaining
    )

    # Check if low balance
    if user_credits.credits_remaining < 10:
        await send_low_balance_notification(user_id)
```

---

## Testing Checklist

### Admin Plan

- [ ] Admin can assign "Admin Free" plan to users
- [ ] Regular users cannot select Admin plan in signup
- [ ] Admin plan users pay $0/month
- [ ] Admin users can purchase credits
- [ ] Credits deducted correctly for usage

### BYOK Plan

- [ ] Users can select BYOK plan at signup
- [ ] Stripe charges $30/month correctly
- [ ] Users can add/edit/delete API keys
- [ ] API keys encrypted in database
- [ ] LLM calls use user's API keys
- [ ] Credits can be purchased
- [ ] Platform services charge credits correctly

### Managed Plan

- [ ] Users can select Managed plan at signup
- [ ] Stripe charges $50/month correctly
- [ ] Users receive included credits monthly
- [ ] LLM calls use platform's managed keys
- [ ] Credits deducted from user account
- [ ] Additional credits can be purchased
- [ ] Low balance notifications work

### Credit System

- [ ] Credit purchase flow works
- [ ] Credits added to account correctly
- [ ] Credits deducted on service usage
- [ ] Credit transaction history logged
- [ ] Low balance alerts sent
- [ ] Credit balance displayed accurately

---

## Future Enhancements

### Auto-Recharge

- Allow users to enable auto-recharge
- When credits drop below threshold, auto-purchase
- E.g., "When below 50 credits, auto-purchase $25"

### Credit Expiration

- Decide: Do credits expire?
- Option A: Never expire
- Option B: Expire after 12 months
- Option C: Expire at end of subscription period

### Volume Discounts

- Higher tiers get better credit rates
- Bulk credit purchases get bonuses
- Annual subscriptions get credit bonus

### Referral Program

- Refer a friend, get $10 in credits
- Friend gets $5 credit bonus on signup
- Tracked via referral codes

---

## Documentation Needed

1. **User Guide**: "Understanding Plans and Credits"
2. **BYOK Setup Guide**: "How to Add Your API Keys"
3. **Credit System Guide**: "How Credits Work"
4. **Admin Guide**: "Assigning the Admin Free Plan"
5. **Migration Guide**: "Transitioning to New Billing"

---

## Timeline Estimate

- **Phase 1** (Database): 2 hours
- **Phase 2** (Lago Config): 4 hours
- **Phase 3** (Frontend): 8 hours
- **Phase 4** (Backend): 6 hours
- **Phase 5** (Stripe): 3 hours
- **Phase 6** (Migration): 4 hours
- **Testing**: 8 hours

**Total**: ~35 hours (~1 week with 1 developer)

---

## Questions to Resolve

1. **Included Tokens for Managed Plan**:
   - How many tokens per month?
   - What models count towards limit?
   - Do tokens roll over or reset monthly?

2. **Credit Pricing**:
   - What's the credit-to-dollar ratio?
   - What's the credit cost per service?

3. **Admin Plan Access**:
   - How many admin seats needed?
   - Can admins create other admins?

4. **BYOK Security**:
   - Key rotation policy?
   - Key sharing restrictions?

5. **Managed Plan Overages**:
   - What happens when included tokens exhausted?
   - Auto-purchase or stop service?

---

**Status**: Ready for stakeholder review and decision on open questions
**Next Step**: Review with product/business team, finalize pricing, begin implementation
