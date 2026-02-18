# Founder-Friend Tier Configuration

**Date**: 2025-11-18
**Status**: ✅ Backend Ready - Awaiting User Account Setup
**Deployment**: Production UC-Cloud / Ops-Center

---

## Overview

The **founder-friend** tier has been created as an invite-only subscription tier for friends of the founders. This tier provides:

- **Free monthly subscription** ($0.00/month)
- **Metered AI usage** (users still pay for LLM API calls via credits)
- **All premium services** access
- **Priority support**
- **BYOK enabled** (Bring Your Own Key)

---

## Tier Configuration

### Database Details

```sql
tier_code:        founder-friend
tier_name:        Founder Friend
description:      Invite-only tier for friends of the founders - Free monthly access with metered AI usage
price_monthly:    $0.00
price_yearly:     $0.00
is_active:        TRUE
is_invite_only:   TRUE
api_calls_limit:  -1 (unlimited API calls, but metered billing applies)
team_seats:       5
byok_enabled:     TRUE
priority_support: TRUE
```

### Service Access

The founder-friend tier includes access to:

1. **Center Deep** (search.centerdeep.online)
   - AI-powered metasearch engine
   - 70+ search engines
   - Privacy-focused

2. **Open-WebUI** (chat.unicorncommander.ai)
   - Chat interface for LLM models
   - Document upload and RAG
   - Multi-model support

3. **Bolt.DIY** (bolt.unicorncommander.ai)
   - AI-powered development environment
   - Code generation and editing
   - SSO integration

4. **Presenton** (presentations.unicorncommander.ai)
   - AI presentation generation
   - Web grounding and templates
   - PPTX/PDF export

5. **Forgejo** (git.unicorncommander.ai)
   - Self-hosted Git server
   - Repository management
   - CI/CD integration

---

## Genesis Flow Organization

### Organization Details

```
Organization Name: Genesis Flow
Organization Slug: genesis-flow
Plan Tier:         founder-friend
Max Seats:         10
Status:            active
```

### Organization Purpose

Genesis Flow is created specifically for Shafen Khan and team members who will use the UC-Cloud platform under the founder-friend tier.

---

## Remaining Setup Steps

### 1. Find or Create Shafen's User Account

**Expected Email**: `connect@shafenkhan.com` (or similar)

**To search for existing account**:
```bash
# Search Keycloak uchub realm
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 --realm master \
  --user admin --password your-admin-password

docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users \
  --realm uchub --query email=connect@shafenkhan.com
```

**If account doesn't exist, create via API**:
```bash
# Create user via Keycloak API
curl -X POST http://uchub-keycloak:8080/admin/realms/uchub/users \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "connect@shafenkhan.com",
    "username": "shafen",
    "firstName": "Shafen",
    "lastName": "Khan",
    "enabled": true,
    "emailVerified": true,
    "attributes": {
      "subscription_tier": ["founder-friend"],
      "subscription_status": ["active"],
      "api_calls_limit": ["-1"]
    }
  }'
```

### 2. Assign Shafen to Founder-Friend Tier

**Update Keycloak user attributes**:
```bash
# Get Shafen's Keycloak user ID
SHAFEN_ID=$(docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users \
  --realm uchub --query email=connect@shafenkhan.com \
  | grep '"id"' | head -1 | cut -d'"' -f4)

# Update attributes
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh update users/$SHAFEN_ID \
  --realm uchub \
  --set 'attributes.subscription_tier=["founder-friend"]' \
  --set 'attributes.subscription_status=["active"]' \
  --set 'attributes.api_calls_limit=["-1"]'
```

### 3. Add Shafen as Organization Admin

**Add to Genesis Flow organization**:
```sql
-- Get organization ID
SELECT id FROM organizations WHERE name = 'genesis-flow';

-- Add Shafen as organization admin
INSERT INTO organization_members (org_id, user_id, role, invited_by)
VALUES (
  (SELECT id FROM organizations WHERE name = 'genesis-flow'),
  '<SHAFEN_KEYCLOAK_USER_ID>',
  'admin',
  'system'
);
```

### 4. Update Admin's Account (Add Forgejo Access)

**Check Admin's current tier**:
```sql
-- Find Admin's tier in Keycloak attributes
-- Then add Forgejo to that tier's apps if not already present
```

**If Aaron is on vip_founder tier**:
```sql
-- Get vip_founder tier ID
DO $$
DECLARE
    tier_id_val INTEGER;
BEGIN
    SELECT id INTO tier_id_val FROM subscription_tiers WHERE tier_code = 'vip_founder';

    -- Add Forgejo if not present
    INSERT INTO tier_apps (tier_id, app_key, enabled)
    VALUES (tier_id_val, 'forgejo', TRUE)
    ON CONFLICT DO NOTHING;
END $$;
```

---

## Service Access Control

### How Service Access Works

1. **Tier → Service Mapping**: The `tier_apps` table maps subscription tiers to enabled services
2. **User → Tier Assignment**: Users get their tier via Keycloak attribute `subscription_tier`
3. **Service Checks Tier**: Each service checks if user's tier includes that service in `tier_apps`

### Service Access Middleware

The backend middleware (`tier_enforcement_middleware.py`) checks service access:

```python
# Pseudocode
user_tier = get_user_attribute("subscription_tier")
allowed_services = query_tier_apps(user_tier)

if requested_service not in allowed_services:
    return 403 Forbidden
```

---

## Credit System & Metered Billing

### How Metered Billing Works

Even though founder-friend is **free monthly**, users still pay for actual AI usage:

1. **Credit System**: Users purchase credits or use credits provided by organization
2. **LLM Usage**: Each LLM API call deducts credits based on tokens used
3. **Credit Tracking**: `litellm_credit_system.py` tracks usage per user/organization
4. **Billing**: Month-end invoices generated via Lago based on actual usage

### Founder-Friend Pricing Model

```
Monthly Subscription:  $0.00 (FREE)
AI Usage (LLM):        Metered (credits deducted per API call)
Services Access:       Full access to all 5 services
Support:               Priority support included
```

**Example**:
- Shafen pays $0/month for the platform
- But if he uses GPT-4, credits are deducted: ~5-11 credits per 1K tokens
- At month end, Lago bills for actual credits consumed

---

## Center Deep Access Configuration

### Special Note: Center Deep Redirect

As requested, **Center Deep should redirect to search.centerdeep.online** (not search.unicorncommander.ai).

**Current Configuration**:
```env
# .env.centerdeep
CENTER_DEEP_EXTERNAL_URL=https://search.centerdeep.online
```

**Service URL Mapping**:
- Unicorn Commander deployment → https://chat.unicorncommander.ai (Open-WebUI)
- Center Deep deployment → https://search.centerdeep.online (Center Deep Pro)
- Both share Keycloak SSO via federation

---

## Verification Commands

### Verify Tier Created
```sql
SELECT tier_code, tier_name, price_monthly, is_invite_only, api_calls_limit
FROM subscription_tiers
WHERE tier_code = 'founder-friend';
```

### Verify Services Mapped
```sql
SELECT st.tier_name, ta.app_key, ta.enabled
FROM subscription_tiers st
LEFT JOIN tier_apps ta ON st.id = ta.tier_id
WHERE st.tier_code = 'founder-friend'
ORDER BY ta.app_key;
```

### Verify Organization Created
```sql
SELECT id, name, display_name, plan_tier, max_seats, status
FROM organizations
WHERE name = 'genesis-flow';
```

### Check User Tier Assignment (once Shafen account exists)
```bash
# Via Keycloak API
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users \
  --realm uchub --query email=connect@shafenkhan.com \
  | grep -A5 "attributes"
```

---

## API Endpoints for Managing Tiers

### List All Tiers
```bash
GET /api/v1/admin/tiers
```

### Get Founder-Friend Tier Details
```bash
GET /api/v1/admin/tiers?tier_code=founder-friend
```

### Update Tier Features
```bash
PUT /api/v1/admin/tiers/{tier_id}/apps
{
  "features": [
    {"feature_key": "centerdeep", "enabled": true},
    {"feature_key": "openwebui", "enabled": true},
    {"feature_key": "bolt", "enabled": true},
    {"feature_key": "presenton", "enabled": true},
    {"feature_key": "forgejo", "enabled": true}
  ]
}
```

### Migrate User to Founder-Friend Tier
```bash
POST /api/v1/admin/tiers/users/{user_id}/migrate-tier
{
  "new_tier_code": "founder-friend",
  "reason": "Invited as founder friend - Shafen Khan",
  "send_notification": true
}
```

---

## Security Considerations

### Invite-Only Enforcement

The `is_invite_only` flag prevents self-service signup:

```sql
is_invite_only: TRUE
```

**Implications**:
- Users cannot select this tier during signup
- Only admins can assign users to this tier
- Tier will not appear in public pricing pages

### Service Access Control

Each service checks tier permissions before allowing access:

```python
# Example from tier_enforcement_middleware.py
if service_key not in user_allowed_services:
    raise HTTPException(status_code=403, detail="Service not included in your tier")
```

---

## Troubleshooting

### Issue: User can't access service

**Check**:
1. User's tier assignment in Keycloak: `subscription_tier` attribute
2. Tier has service enabled: `SELECT * FROM tier_apps WHERE tier_id = ...`
3. Service key matches: Check app_key in tier_apps matches service identifier

### Issue: Center Deep redirects to wrong domain

**Fix**:
1. Check `.env.centerdeep` has correct `CENTER_DEEP_EXTERNAL_URL`
2. Verify Traefik routing rules in `docker-compose.centerdeep.yml`
3. Restart container: `docker restart unicorn-centerdeep`

### Issue: Credits not being deducted

**Check**:
1. Organization has credit pool: `SELECT * FROM organization_credit_pools WHERE org_id = ...`
2. LiteLLM integration enabled: Check `litellm_credit_system.py` middleware
3. Logs for credit deduction: `docker logs ops-center-direct | grep credit`

---

## Next Steps Checklist

- [ ] Find Shafen's email (confirm: connect@shafenkhan.com or provide correct email)
- [ ] Create or locate Shafen's Keycloak account
- [ ] Assign subscription_tier = 'founder-friend' to Shafen
- [ ] Add Shafen to Genesis Flow organization as admin
- [ ] Verify Admin has Forgejo access (add to vip_founder tier if needed)
- [ ] Test service access for founder-friend tier:
  - [ ] Center Deep (search.centerdeep.online)
  - [ ] Open-WebUI (chat.unicorncommander.ai)
  - [ ] Bolt.DIY (bolt.unicorncommander.ai)
  - [ ] Presenton (presentations.unicorncommander.ai)
  - [ ] Forgejo (git.unicorncommander.ai)
- [ ] Document founder-friend tier in public docs (if desired)

---

## Files Modified

### Database
- `subscription_tiers` table - Added founder-friend tier
- `tier_apps` table - Mapped 5 services to founder-friend
- `organizations` table - Created Genesis Flow organization

### Documentation
- `/services/ops-center/FOUNDER_FRIEND_TIER_SETUP.md` - This file
- `/tmp/founder_friend_implementation.sql` - SQL implementation script

---

## Contact & Support

**Tier Configuration**: Managed via Ops-Center `/admin/system/tiers`
**User Management**: Ops-Center `/admin/system/users`
**Organization Management**: Ops-Center `/admin/organizations`

**Questions**: Contact system administrator or check:
- `CLAUDE.md` - Project documentation
- `ops-center/CLAUDE.md` - Ops-Center specific docs

---

**Created**: 2025-11-18
**Status**: ✅ Backend Configuration Complete
**Pending**: User account setup and assignment
