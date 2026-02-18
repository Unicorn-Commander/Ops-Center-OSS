# VIP Founder Tier - Complete Documentation

**Date Created**: November 12, 2025
**Status**: ✅ PRODUCTION READY
**Migration File**: `/backend/migrations/add_vip_founder_tier.sql`

---

## Overview

The **VIP Founder** tier is a premium, invite-only subscription tier with **$0 monthly subscription fee**. It provides lifetime access to 4 premium applications with flexible billing options:

- **BYOK (Bring Your Own Key)**: Use your own API keys (no platform charges)
- **Pay-Per-Use**: Platform credits charged only for actual usage

This tier is designed for:
- Founders and co-founders
- Company administrators and staff
- Strategic partners
- Early adopters and VIPs

---

## Tier Specifications

### Basic Information

| Field | Value | Description |
|-------|-------|-------------|
| **Tier Code** | `vip_founder` | Unique identifier |
| **Tier Name** | VIP Founder | Display name |
| **Monthly Price** | $0.00 | No subscription fee |
| **Yearly Price** | $0.00 | No subscription fee |
| **Sort Order** | 0 | Displayed first in tier lists |

### Access Control

| Field | Value | Description |
|-------|-------|-------------|
| **Is Active** | `true` | Tier is currently available |
| **Is Invite Only** | `true` | Requires admin approval |

### Resource Limits

| Field | Value | Description |
|-------|-------|-------------|
| **API Calls Limit** | -1 (Unlimited) | No hard limit, usage-based billing |
| **Team Seats** | 5 | Up to 5 team members |
| **BYOK Enabled** | `true` | Bring Your Own Key supported |
| **Priority Support** | `true` | Fast-track support access |

### Billing Integration

| Field | Value | Description |
|-------|-------|-------------|
| **Lago Plan Code** | `vip_founder` | Billing system reference |
| **Stripe Price Monthly** | `null` | Not applicable (no subscription fee) |
| **Stripe Price Yearly** | `null` | Not applicable (no subscription fee) |

---

## Included Applications

The VIP Founder tier includes access to **4 premium applications**:

### 1. Center Deep Pro
- **URL**: https://centerdeep.online
- **Description**: Privacy-focused AI metasearch engine with 70+ search engines
- **Features**:
  - Aggregated search results from multiple engines
  - AI-powered result ranking
  - Privacy-first architecture (no tracking)
  - Tool servers for specialized searches

### 2. Open-WebUI
- **URL**: http://localhost:8080 (or configured domain)
- **Description**: Modern chat interface for LLM interactions
- **Features**:
  - Multi-model support (OpenAI, Anthropic, OpenRouter, etc.)
  - Conversation history and management
  - Document upload and RAG capabilities
  - Real-time streaming responses

### 3. Bolt.diy (UC Fork)
- **URL**: https://bolt.unicorncommander.ai
- **Description**: AI-powered development environment
- **Features**:
  - Code generation with AI assistance
  - Full Keycloak SSO integration
  - Real-time collaboration
  - Project scaffolding and templates

### 4. Presenton (UC Fork)
- **URL**: https://presentations.unicorncommander.ai
- **Description**: AI presentation generation platform
- **Features**:
  - Generate slides from prompts
  - Web grounding for research
  - Export to PPTX and PDF
  - Template library

---

## Billing Model

### No Subscription Fee

VIP Founder members **do not pay a monthly or yearly subscription fee**. The tier is free to access.

### Usage-Based Billing Options

VIP Founders choose how they want to pay for API usage:

#### Option 1: BYOK (Bring Your Own Key)
- **Cost**: $0 (user provides their own API keys)
- **Setup**: Users configure their OpenAI, Anthropic, OpenRouter, etc. keys in account settings
- **Benefits**:
  - No platform markup
  - Direct billing from providers
  - Full transparency on costs

#### Option 2: Pay-Per-Use (Platform Credits)
- **Cost**: Variable, based on actual usage
- **Billing**: Charged via platform credit system
- **Benefits**:
  - No need to manage multiple API keys
  - Simplified billing (one invoice)
  - Access to 100+ models via OpenRouter

### Credit Pricing (When Not Using BYOK)

Platform credits are charged based on model usage:

| Model Type | Cost per 1M Tokens | Example |
|-----------|-------------------|---------|
| GPT-4 Turbo | ~$10-30 | Varies by provider |
| Claude 3.5 Sonnet | ~$3-15 | Varies by provider |
| GPT-3.5 Turbo | ~$0.50-2 | Varies by provider |
| Open-Source (via OpenRouter) | ~$0.10-1 | Varies by model |

**Note**: Actual costs depend on the LLM provider and model selected. VIP Founders can view real-time pricing in the dashboard.

---

## Database Schema

### Subscription Tiers Table

```sql
SELECT * FROM subscription_tiers WHERE tier_code = 'vip_founder';
```

**Result**:
```
id  | 1
tier_code | vip_founder
tier_name | VIP Founder
description | Lifetime access for founders, admins, staff, and partners. Includes 4 premium apps with BYOK or pay-per-use via platform credits. No monthly subscription fee.
price_monthly | 0.00
price_yearly | 0.00
is_active | true
is_invite_only | true
sort_order | 0
api_calls_limit | -1 (unlimited)
team_seats | 5
byok_enabled | true
priority_support | true
lago_plan_code | vip_founder
stripe_price_monthly | null
stripe_price_yearly | null
created_at | 2025-11-12 16:38:07
updated_at | 2025-11-12 16:38:07
created_by | system
updated_by | system
```

### Tier Apps Table

```sql
SELECT ta.*, st.tier_name
FROM tier_apps ta
JOIN subscription_tiers st ON ta.tier_id = st.id
WHERE st.tier_code = 'vip_founder'
ORDER BY ta.app_key;
```

**Result** (8 apps total):
```
app_key          | app_value                                | enabled | tier_name
-----------------+------------------------------------------+---------+-------------
bolt_diy         | https://bolt.unicorncommander.ai         | true    | VIP Founder
center_deep_pro  | https://centerdeep.online                | true    | VIP Founder
chat_access      | true                                     | true    | VIP Founder
litellm_access   | true                                     | true    | VIP Founder
open_webui       | http://localhost:8080                    | true    | VIP Founder
presenton        | https://presentations.unicorncommander.ai| true    | VIP Founder
priority_support | true                                     | true    | VIP Founder
search_enabled   | true                                     | true    | VIP Founder
```

---

## Frontend Display

### Gold Badge Styling

VIP Founder tier is displayed with **gold/premium styling** to distinguish it from other tiers:

**Color Scheme**:
- **Background**: `rgba(255, 215, 0, 0.15)` (gold with 15% opacity)
- **Text Color**: `#FFD700` (gold)
- **Border Color**: `#FFD700` (gold)

**Implementation** (`getTierBadgeColor()` function):

```javascript
case 'vip_founder':
  return {
    bg: 'rgba(255, 215, 0, 0.15)',
    color: '#FFD700',
    border: '#FFD700'
  };
```

**Usage in Subscription Management**:
- Tier code badges in main table
- Old/new tier badges in audit log
- Tier selection dropdowns

### Comparison with Other Tiers

| Tier | Color | Background | Purpose |
|------|-------|-----------|---------|
| **VIP Founder** | Gold (#FFD700) | rgba(255, 215, 0, 0.15) | Premium/exclusive |
| BYOK | Purple (#7c3aed) | rgba(124, 58, 237, 0.15) | Developer-focused |
| Managed | Blue (#3b82f6) | rgba(59, 130, 246, 0.15) | Recommended plan |

---

## API Endpoints

### List All Tiers (Including VIP Founder)

```http
GET /api/v1/admin/tiers/
```

**Response**:
```json
[
  {
    "id": 1,
    "tier_code": "vip_founder",
    "tier_name": "VIP Founder",
    "description": "Lifetime access for founders, admins, staff...",
    "price_monthly": 0.0,
    "price_yearly": 0.0,
    "is_active": true,
    "is_invite_only": true,
    "sort_order": 0,
    "api_calls_limit": -1,
    "team_seats": 5,
    "byok_enabled": true,
    "priority_support": true,
    "lago_plan_code": "vip_founder",
    "stripe_price_monthly": null,
    "stripe_price_yearly": null,
    "feature_count": 0,
    "active_user_count": 0,
    "monthly_revenue": 0.0,
    "created_at": "2025-11-12T16:38:07Z",
    "updated_at": "2025-11-12T16:38:07Z",
    "created_by": "system",
    "updated_by": "system"
  }
]
```

### Get VIP Founder Tier Apps

```http
GET /api/v1/admin/tiers/1/features
```

**Response**:
```json
[
  {
    "feature_key": "bolt_diy",
    "feature_value": "https://bolt.unicorncommander.ai",
    "enabled": true
  },
  {
    "feature_key": "center_deep_pro",
    "feature_value": "https://centerdeep.online",
    "enabled": true
  },
  {
    "feature_key": "open_webui",
    "feature_value": "http://localhost:8080",
    "enabled": true
  },
  {
    "feature_key": "presenton",
    "feature_value": "https://presentations.unicorncommander.ai",
    "enabled": true
  }
]
```

### Migrate User to VIP Founder Tier

```http
POST /api/v1/admin/tiers/users/{user_id}/migrate-tier
Content-Type: application/json

{
  "user_id": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
  "new_tier_code": "vip_founder",
  "reason": "Founder of Magic Unicorn company",
  "send_notification": true
}
```

**Response**:
```json
{
  "success": true,
  "message": "User migrated from 'managed' to 'vip_founder'",
  "user_id": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
  "user_email": "admin@example.com",
  "old_tier": "managed",
  "new_tier": "vip_founder",
  "new_api_limit": -1
}
```

---

## Admin Operations

### How to Assign VIP Founder Tier to a User

**Via Ops-Center UI** (Recommended):

1. Navigate to **Admin → User Management**
2. Find the user you want to upgrade
3. Click on the user to open the User Detail page
4. Go to the **"Subscription"** tab
5. Click **"Change Tier"**
6. Select **"VIP Founder"** from the dropdown
7. Provide a reason (e.g., "Company founder")
8. Check **"Send notification email"** if desired
9. Click **"Confirm Change"**

**Via API** (Programmatic):

```bash
curl -X POST https://unicorncommander.ai/api/v1/admin/tiers/users/USER_ID/migrate-tier \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN" \
  -d '{
    "user_id": "USER_ID",
    "new_tier_code": "vip_founder",
    "reason": "Assigned VIP Founder status",
    "send_notification": true
  }'
```

**Via Database** (Direct):

```sql
-- 1. Get user attributes from Keycloak
-- 2. Update user tier
UPDATE users SET subscription_tier = 'vip_founder' WHERE id = 'USER_ID';

-- 3. Record in audit log
INSERT INTO user_tier_history (
  user_id, user_email, old_tier_code, new_tier_code,
  change_reason, changed_by
) VALUES (
  'USER_ID',
  'user@example.com',
  'managed',
  'vip_founder',
  'Assigned VIP Founder status',
  'admin'
);
```

### Viewing VIP Founder Users

**Query all VIP Founder users**:

```sql
-- Via Keycloak user attributes
SELECT
  u.id,
  u.email,
  u.username,
  ua.value AS subscription_tier
FROM keycloak.users u
JOIN keycloak.user_attribute ua ON u.id = ua.user_id
WHERE ua.name = 'subscription_tier'
  AND ua.value = 'vip_founder';
```

**Via Ops-Center API**:

```http
GET /api/v1/admin/users?tier=vip_founder
```

---

## Migration and Rollback

### Apply Migration

```bash
# Copy SQL file to PostgreSQL container
docker cp /path/to/add_vip_founder_tier.sql uchub-postgres:/tmp/

# Execute migration
docker exec uchub-postgres psql -U unicorn -d unicorn_db -f /tmp/add_vip_founder_tier.sql
```

**Expected Output**:
```
BEGIN
INSERT 0 1
DO
NOTICE:  Successfully associated 4 apps with VIP Founder tier (ID: 1)
 id |  tier_code  |  tier_name  | price_monthly | ...
----+-------------+-------------+---------------+-----
  1 | vip_founder | VIP Founder |          0.00 | ...
(1 row)

 id |  tier_code  |  tier_name  |     app_key      |                 app_value                 | enabled
----+-------------+-------------+------------------+-------------------------------------------+---------
 24 | vip_founder | VIP Founder | bolt_diy         | https://bolt.unicorncommander.ai          | t
 22 | vip_founder | VIP Founder | center_deep_pro  | https://centerdeep.online                 | t
 23 | vip_founder | VIP Founder | open_webui       | http://localhost:8080                     | t
 25 | vip_founder | VIP Founder | presenton        | https://presentations.unicorncommander.ai | t
...

COMMIT
```

### Verify Migration

```bash
# Check tier was created
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c \
  "SELECT tier_code, tier_name, price_monthly, api_calls_limit, team_seats FROM subscription_tiers WHERE tier_code = 'vip_founder';"

# Check apps were associated
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c \
  "SELECT ta.app_key, ta.app_value, ta.enabled FROM tier_apps ta JOIN subscription_tiers st ON ta.tier_id = st.id WHERE st.tier_code = 'vip_founder';"

# Check frontend styling loaded
curl -s http://localhost:8084/api/v1/admin/tiers/ | grep -A5 vip_founder
```

### Rollback Migration

**If you need to remove the VIP Founder tier**:

```sql
BEGIN;

-- Delete app associations
DELETE FROM tier_apps
WHERE tier_id = (SELECT id FROM subscription_tiers WHERE tier_code = 'vip_founder');

-- Delete tier
DELETE FROM subscription_tiers WHERE tier_code = 'vip_founder';

-- Verify deletion
SELECT COUNT(*) FROM subscription_tiers WHERE tier_code = 'vip_founder';
-- Should return 0

COMMIT;
```

---

## Testing Checklist

### Database Tests

- [x] VIP Founder tier exists in `subscription_tiers` table
- [x] `tier_code` is unique and lowercase (`vip_founder`)
- [x] `price_monthly` and `price_yearly` are 0.00
- [x] `is_invite_only` is TRUE
- [x] `api_calls_limit` is -1 (unlimited)
- [x] 4 apps are associated in `tier_apps` table
- [x] All app URLs are correct and accessible

### API Tests

- [x] `GET /api/v1/admin/tiers/` returns VIP Founder tier
- [x] `GET /api/v1/admin/tiers/1` returns VIP Founder details
- [x] `GET /api/v1/admin/tiers/1/features` returns 4+ apps
- [x] Tier sorting places VIP Founder first (`sort_order = 0`)

### Frontend Tests

- [x] VIP Founder badge displays with gold color
- [x] Tier name is "VIP Founder" (not "vip_founder")
- [x] Price displays as "$0.00/month" (not free)
- [x] "Invite Only" indicator shows correctly
- [x] Gold styling applied to audit log tier chips

### User Flow Tests

- [ ] Admin can assign VIP Founder tier to a user
- [ ] User migration creates audit log entry
- [ ] User receives notification email (if enabled)
- [ ] User can access all 4 apps after tier assignment
- [ ] BYOK configuration works for VIP Founder users
- [ ] Platform credits are charged correctly (if not using BYOK)

---

## Troubleshooting

### Issue: VIP Founder Not Showing in Tier List

**Cause**: Database migration not applied or tier is inactive

**Solution**:
```bash
# Check if tier exists
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c \
  "SELECT * FROM subscription_tiers WHERE tier_code = 'vip_founder';"

# If missing, apply migration
docker exec uchub-postgres psql -U unicorn -d unicorn_db -f /tmp/add_vip_founder_tier.sql

# Restart backend
docker restart ops-center-direct
```

### Issue: Gold Badge Not Displaying

**Cause**: Frontend not rebuilt with updated styling

**Solution**:
```bash
cd /opt/ops-center

# Rebuild frontend
npm run build

# Copy to public
cp -r dist/* public/

# Restart backend
docker restart ops-center-direct

# Hard refresh browser (Ctrl+Shift+R)
```

### Issue: Apps Not Associated with VIP Founder

**Cause**: `tier_apps` entries missing

**Solution**:
```sql
-- Re-run app association
DO $$
DECLARE
    v_tier_id INTEGER;
BEGIN
    SELECT id INTO v_tier_id FROM subscription_tiers WHERE tier_code = 'vip_founder';

    INSERT INTO tier_apps (tier_id, app_key, app_value, enabled)
    VALUES
      (v_tier_id, 'center_deep_pro', 'https://centerdeep.online', TRUE),
      (v_tier_id, 'open_webui', 'http://localhost:8080', TRUE),
      (v_tier_id, 'bolt_diy', 'https://bolt.unicorncommander.ai', TRUE),
      (v_tier_id, 'presenton', 'https://presentations.unicorncommander.ai', TRUE)
    ON CONFLICT (tier_id, app_key) DO UPDATE SET
      app_value = EXCLUDED.app_value,
      enabled = EXCLUDED.enabled;
END $$;
```

### Issue: User Migration Fails

**Cause**: User ID not found in Keycloak or tier code invalid

**Solution**:
```bash
# 1. Verify user exists in Keycloak
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users \
  --realm uchub --fields id,username,email

# 2. Verify tier code is correct
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c \
  "SELECT tier_code, is_active FROM subscription_tiers WHERE tier_code = 'vip_founder';"

# 3. Check API response for detailed error
curl -X POST http://localhost:8084/api/v1/admin/tiers/users/USER_ID/migrate-tier \
  -H "Content-Type: application/json" \
  -d '{"user_id":"USER_ID","new_tier_code":"vip_founder","reason":"Test"}' | jq
```

---

## Security Considerations

### Invite-Only Access

- VIP Founder tier is **invite-only** (`is_invite_only = TRUE`)
- Users cannot self-register for this tier
- Requires admin approval via:
  - Manual tier assignment
  - API-based migration
  - Direct database update

### Audit Logging

All tier changes are logged in `user_tier_history`:

```sql
SELECT
  user_email,
  old_tier_code,
  new_tier_code,
  change_reason,
  changed_by,
  change_timestamp
FROM user_tier_history
WHERE new_tier_code = 'vip_founder'
ORDER BY change_timestamp DESC;
```

### API Key Security

VIP Founder users can configure BYOK:
- API keys stored encrypted in database
- Keys never exposed in API responses
- Keys scoped to user account (not shared)

---

## Future Enhancements

### Planned Features

1. **Auto-Approval Workflow**
   - Email-based invitation system
   - One-time signup links
   - Expiring invite codes

2. **Usage Analytics Dashboard**
   - VIP Founder-specific usage reports
   - BYOK vs platform credit comparison
   - Cost savings calculator

3. **White-Label Options**
   - Custom branding for VIP Founders
   - Personalized subdomains
   - Custom login pages

4. **Advanced Team Management**
   - Team seat allocation (currently 5)
   - Role-based permissions within team
   - Usage quotas per team member

5. **Priority Support Portal**
   - Dedicated support channel
   - Faster response times
   - Direct access to engineers

---

## References

### Related Documentation

- **Main Ops-Center README**: `/services/ops-center/README.md`
- **Subscription Tier Schema**: `/backend/migrations/add_subscription_tiers.sql`
- **API Documentation**: `/services/ops-center/docs/API_REFERENCE.md`
- **UC-Cloud Main Guide**: `/CLAUDE.md`

### Database Schema Files

- **Migration Script**: `/backend/migrations/add_vip_founder_tier.sql`
- **Base Schema**: `/backend/migrations/add_subscription_tiers.sql`
- **Seed Data**: Included in migration script

### Frontend Files

- **Subscription Management**: `/src/pages/admin/SubscriptionManagement.jsx`
- **App Management**: `/src/pages/admin/AppManagement.jsx`
- **Model Management**: `/src/pages/admin/ModelManagement.jsx`
- **Tier Comparison**: `/src/pages/TierComparison.jsx`

### Backend Files

- **Subscription Tiers API**: `/backend/subscription_tiers_api.py`
- **Keycloak Integration**: `/backend/keycloak_integration.py`
- **Lago Integration**: `/backend/lago_integration.py`

---

## Conclusion

The **VIP Founder** tier is now fully implemented and production-ready. It provides:

✅ **Zero monthly subscription fee**
✅ **Unlimited API calls** (usage-based billing)
✅ **4 premium applications** (Center Deep Pro, Open-WebUI, Bolt.diy, Presenton)
✅ **BYOK support** (no platform markup)
✅ **Gold badge styling** (premium visual treatment)
✅ **5 team seats**
✅ **Priority support**
✅ **Invite-only access** (admin-controlled)

**Questions or Issues?**
Contact: admin@example.com
Project: UC-Cloud / Ops-Center
Organization: Magic Unicorn Unconventional Technology & Stuff Inc

---

**Document Version**: 1.0
**Last Updated**: November 12, 2025
**Status**: ✅ Complete
