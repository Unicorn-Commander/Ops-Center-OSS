# Agent 2: Billing Integration Specialist - C06 Task

**Mission**: Enable subscription functionality in TierComparison.jsx

**Files**:
- Frontend: `/opt/ops-center/src/pages/TierComparison.jsx`
- Backend: Already exists! (`/api/v1/subscriptions/plans`, `/api/v1/billing/subscriptions/checkout`)

**Duration**: 6-8 hours (Backend already done, focus on frontend integration)

---

## Current Issues

1. **Hardcoded Tier Data** (Lines 12-97): All subscription plan data is static
2. **Non-functional Buttons** (Lines 214-223): Buttons use `href` navigation, not Stripe integration
3. **No API Integration**: No connection to Lago billing or Stripe Checkout

---

## Backend Endpoints (ALREADY EXIST!)

### 1. Get Subscription Plans
**Endpoint**: `GET /api/v1/subscriptions/plans`
**Response**:
```json
{
  "plans": [
    {
      "id": "free",
      "name": "Free",
      "description": "Perfect for testing...",
      "price_monthly": 0,
      "price_yearly": 0,
      "features": [...],
      "limits": {...}
    },
    // ... more plans
  ]
}
```

### 2. Create Stripe Checkout Session
**Endpoint**: `POST /api/v1/billing/subscriptions/checkout`
**Request**:
```json
{
  "tier_id": "professional",
  "billing_cycle": "monthly"
}
```
**Response**:
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_..."
}
```

---

## Frontend Changes Required

### 1. Replace Hardcoded Tiers with API Data

**Add state and useEffect**:
```jsx
import React, { useState, useEffect } from 'react';

export default function TierComparison() {
  const { currentTheme } = useTheme();
  const [tiers, setTiers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentTier, setCurrentTier] = useState(null);

  useEffect(() => {
    loadPlans();
    loadCurrentSubscription();
  }, []);

  const loadPlans = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/subscriptions/plans', {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to load subscription plans');
      }

      const data = await response.json();

      // Transform API data to match component format
      const transformedTiers = data.plans.map(plan => ({
        name: plan.name,
        price: plan.price_monthly || 0,
        credits: plan.limits?.api_calls_per_month || 0,
        billingPeriod: 'month',
        description: plan.description,
        features: plan.features || [],
        limitations: plan.limitations || [],
        cta: plan.price_monthly === 0 ? 'Get Started' : `Upgrade to ${plan.name}`,
        popular: plan.id === 'professional', // Mark Pro as popular
        planId: plan.id
      }));

      setTiers(transformedTiers);
    } catch (error) {
      console.error('Failed to load plans:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const loadCurrentSubscription = async () => {
    try {
      const response = await fetch('/api/v1/subscriptions/current', {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentTier(data.plan?.id || null);
      }
    } catch (error) {
      console.error('Failed to load current subscription:', error);
      // Not critical, user may not be logged in
    }
  };
```

### 2. Implement Stripe Checkout Flow

**Replace Button Component**:
```jsx
// OLD (Line 214-223):
<Button
  variant={tier.popular ? 'contained' : 'outlined'}
  fullWidth
  size="large"
  endIcon={<ArrowForward />}
  href={tier.ctaHref}  // ❌ This doesn't work!
  sx={{ mt: 3 }}
>
  {tier.cta}
</Button>

// NEW:
<Button
  variant={tier.popular ? 'contained' : 'outlined'}
  fullWidth
  size="large"
  endIcon={<ArrowForward />}
  onClick={() => handleSelectPlan(tier)}
  disabled={currentTier === tier.planId} // Disable if already subscribed
  sx={{ mt: 3 }}
>
  {currentTier === tier.planId ? 'Current Plan' : tier.cta}
</Button>
```

**Add Handler Function**:
```jsx
const handleSelectPlan = async (tier) => {
  // Free tier - no payment required
  if (tier.price === 0) {
    window.location.href = '/signup'; // Or wherever signup is
    return;
  }

  // Enterprise - contact sales
  if (tier.planId === 'enterprise') {
    window.location.href = 'mailto:sales@magicunicorn.tech';
    return;
  }

  // Paid tiers - Stripe Checkout
  try {
    setLoading(true);

    const response = await fetch('/api/v1/billing/subscriptions/checkout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        tier_id: tier.planId,
        billing_cycle: 'monthly' // Could add toggle for monthly/yearly
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create checkout session');
    }

    const data = await response.json();

    if (data.checkout_url) {
      // Redirect to Stripe Checkout
      window.location.href = data.checkout_url;
    } else {
      throw new Error('No checkout URL received');
    }
  } catch (error) {
    console.error('Checkout error:', error);
    alert(`Failed to start checkout: ${error.message}`); // TODO: Replace with toast
  } finally {
    setLoading(false);
  }
};
```

### 3. Add Loading and Error States

**Loading State**:
```jsx
if (loading && tiers.length === 0) {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <CircularProgress />
        <Typography variant="body1" sx={{ mt: 2 }}>
          Loading subscription plans...
        </Typography>
      </Box>
    </Container>
  );
}
```

**Error State**:
```jsx
if (error) {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography variant="h5" color="error" gutterBottom>
          Failed to Load Plans
        </Typography>
        <Typography variant="body1" color="textSecondary" sx={{ mb: 3 }}>
          {error}
        </Typography>
        <Button variant="contained" onClick={loadPlans}>
          Retry
        </Button>
      </Box>
    </Container>
  );
}
```

### 4. Highlight Current Subscription

**Add Visual Indicator**:
```jsx
<Card
  sx={{
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    position: 'relative',
    border: tier.popular ? '2px solid' : '1px solid',
    borderColor: currentTier === tier.planId
      ? 'success.main'  // Green border for current plan
      : tier.popular
      ? 'primary.main'
      : 'divider',
    // ... rest of sx
  }}
>
  {currentTier === tier.planId && (
    <Chip
      label="Current Plan"
      color="success"
      size="small"
      sx={{
        position: 'absolute',
        top: 8,
        right: 8,
      }}
    />
  )}

  {/* ... rest of card content */}
</Card>
```

---

## Import Statements Needed

Add these to the top of the file:

```jsx
import { useState, useEffect } from 'react';
import { CircularProgress } from '@mui/material';
```

---

## Acceptance Criteria

- [ ] Subscription plans load from `/api/v1/subscriptions/plans` API
- [ ] Loading state shows while fetching plans
- [ ] Error state shows if API fails with retry button
- [ ] "Select Plan" button creates Stripe Checkout session
- [ ] User redirects to Stripe Checkout page
- [ ] Free tier button navigates to signup (no payment)
- [ ] Enterprise button opens email client (contact sales)
- [ ] Current subscription tier is highlighted
- [ ] "Current Plan" button is disabled
- [ ] No hardcoded tier data remains

---

## Testing Checklist

```bash
# 1. Build and deploy
cd /opt/ops-center
npm run build
cp -r dist/* public/
docker restart ops-center-direct

# 2. Test API endpoints
curl http://localhost:8084/api/v1/subscriptions/plans
# Should return plans data

# 3. Test in browser (logged OUT)
# Visit: https://unicorncommander.ai/admin/subscription/plan
# - Plans should load from API
# - Click "Select Plan" → Should redirect to /signup or show login prompt

# 4. Test in browser (logged IN)
# - Current tier should be highlighted
# - Click "Select Plan" (Starter/Pro) → Should redirect to Stripe Checkout
# - Click "Contact Sales" (Enterprise) → Should open email
```

---

## Error Handling Scenarios

1. **API Returns 401 (Not Authenticated)**:
   - Redirect to login page
   - Show "Please log in to view subscription options"

2. **API Returns 500 (Server Error)**:
   - Show error state with retry button
   - Log error details to console

3. **Stripe Checkout Creation Fails**:
   - Show error message to user
   - Don't navigate away from page
   - Allow user to retry

4. **User Already Has Subscription**:
   - Disable "Select Plan" button for current tier
   - Show "Current Plan" label
   - Allow upgrades/downgrades (if different tier)

---

## Deliverables

1. Modified `src/pages/TierComparison.jsx` with:
   - API integration for plans
   - Stripe Checkout integration
   - Loading/error states
   - Current tier highlighting
2. All hardcoded data removed
3. Working end-to-end subscription flow
4. Test report showing successful Stripe redirect
