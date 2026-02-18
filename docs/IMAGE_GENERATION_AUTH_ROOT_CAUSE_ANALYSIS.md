# Image Generation API - Service Key Authentication Root Cause Analysis

**Date**: November 29, 2025
**Issue**: Service-to-service authentication returns 401 errors when Presenton/Bolt.diy try to use centralized image generation
**Status**: Root cause identified
**Severity**: Medium (workaround exists via BYOK)

---

## Executive Summary

The image generation API endpoint (`POST /api/v1/llm/image/generations`) correctly implements service key authentication in the `get_user_id()` dependency function, but the service key returns a **service name string** (e.g., `"presenton-service"`) instead of a **user ID**. This causes downstream operations that expect a valid user UUID to fail when trying to look up user subscription tiers and credit balances.

**The Problem**: Service keys are designed for **service-to-service** calls where the service proxies on behalf of a user (with `X-User-ID` header). They were NOT designed for **service-initiated** image generation requests where there is no user context.

---

## Technical Analysis

### Authentication Flow (Current Implementation)

#### Step 1: Service Key Authentication (`get_user_id()` function)

**Location**: `/backend/litellm_api.py` lines 686-711

```python
# Check for service key (format: sk-<service>-service-key-<year>)
if token.startswith('sk-'):
    service_keys = {
        'sk-bolt-diy-service-key-2025': 'bolt-diy-service',
        'sk-presenton-service-key-2025': 'presenton-service',
        'sk-brigade-service-key-2025': 'brigade-service',
        'sk-centerdeep-service-key-2025': 'centerdeep-service'
    }

    if token in service_keys:
        service_name = service_keys[token]

        # Check for X-User-ID header (service proxying on behalf of user)
        x_user_id = request.headers.get('X-User-ID')
        if x_user_id:
            logger.info(f"✅ Service key authenticated: {service_name} proxying for user: {x_user_id}")
            return x_user_id  # ✅ Returns user ID when X-User-ID header present
        else:
            # No user context - return service name (for service-level operations)
            logger.info(f"✅ Service key authenticated: {service_name} (no user context)")
            return service_name  # ❌ Returns service name string, NOT a user ID
```

**Key Observations**:
- ✅ Service key is recognized and validated
- ✅ Authentication succeeds (returns 200, not 401)
- ⚠️ **Without `X-User-ID` header**, returns service name string instead of user UUID
- ⚠️ Service name string: `"presenton-service"` is NOT a valid user ID format

#### Step 2: Credit System Operations Fail

**Location**: `/backend/litellm_api.py` lines 1448-1450

```python
# Get user tier for cost calculation
user_tier = await credit_system.get_user_tier(user_id)
```

**What Happens**:
1. `user_id = "presenton-service"` (string, not UUID)
2. `credit_system.get_user_tier()` looks up user in database by user_id
3. No user with ID `"presenton-service"` exists in users table
4. Query returns `None` or throws exception
5. **Result**: Credit tier lookup fails → 401/500 error returned to client

### Where the Mismatch Occurs

#### Expected Behavior (With X-User-ID Header)
```http
POST /api/v1/llm/image/generations
Authorization: Bearer sk-presenton-service-key-2025
X-User-ID: 7a6bfd31-0120-4a30-9e21-0fc3b8006579

{
  "prompt": "A cat in a wizard hat",
  "model": "dall-e-3"
}
```

**Flow**:
1. Service key validated ✅
2. `X-User-ID` header present → extract user UUID ✅
3. `get_user_id()` returns `"7a6bfd31-0120-4a30-9e21-0fc3b8006579"` ✅
4. Credit system looks up tier for valid user UUID ✅
5. Image generation proceeds ✅

#### Actual Behavior (Without X-User-ID Header)
```http
POST /api/v1/llm/image/generations
Authorization: Bearer sk-presenton-service-key-2025

{
  "prompt": "A cat in a wizard hat",
  "model": "dall-e-3"
}
```

**Flow**:
1. Service key validated ✅
2. No `X-User-ID` header → no user context ⚠️
3. `get_user_id()` returns `"presenton-service"` (service name string) ⚠️
4. Credit system tries to look up tier for `"presenton-service"` ❌
5. User not found in database → exception thrown ❌
6. API returns 401 or 500 error ❌

---

## Root Causes Identified

### Primary Root Cause
**Service keys were designed for user-proxying, not service-initiated requests**

The current implementation assumes:
- Service keys are ONLY used when a service acts on behalf of a specific user
- `X-User-ID` header is ALWAYS provided with service key authentication
- Service-initiated requests (no user context) were not considered in the design

### Secondary Root Causes

1. **No Service-Level Billing Account**
   - Services don't have their own credit balance
   - No "service user" account exists in the database
   - Credit system assumes all requests are tied to a user UUID

2. **Missing Fallback Authentication Path**
   - No alternative authentication method for service-initiated requests
   - Services cannot generate images without user context
   - BYOK is the only workaround (user provides their own API keys)

3. **Incomplete Error Handling**
   - When user ID lookup fails, error is not descriptive
   - 401 error doesn't explain that `X-User-ID` header is missing
   - Developers don't know they need to pass user context

---

## Impact Assessment

### Current Impact

**Affected Services**:
- ✅ **Presenton**: Cannot use centralized image generation for presentations
- ✅ **Bolt.diy**: Cannot use centralized image generation in dev environment
- ⚠️ **Brigade**: Would be affected if agent-initiated image gen needed

**User Impact**:
- **Workaround Exists**: Users can configure BYOK (OpenAI/OpenRouter API keys)
- When BYOK configured, image generation bypasses credit system entirely
- No impact on users who bring their own keys

**Business Impact**:
- Lost revenue opportunity (users use their own keys instead of paying for credits)
- Platform credit usage is lower than expected
- Cannot track/bill centralized image generation usage

### Severity Assessment

**Severity**: Medium (not Critical)

**Reasoning**:
- Workaround exists (BYOK)
- Does not affect core functionality
- Image generation still works for users with direct API access
- Not a security vulnerability
- Does not cause data loss

---

## Reproduction Steps

### Test Case 1: Service Key Without X-User-ID (FAILS)

```bash
curl -X POST https://unicorncommander.ai/api/v1/llm/image/generations \
  -H "Authorization: Bearer sk-presenton-service-key-2025" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A unicorn with a magic wand",
    "model": "dall-e-3",
    "size": "1024x1024",
    "quality": "standard",
    "n": 1
  }'
```

**Expected**: Image generated successfully
**Actual**: 401 Unauthorized (user tier lookup fails)

### Test Case 2: Service Key With X-User-ID (SHOULD WORK)

```bash
curl -X POST https://unicorncommander.ai/api/v1/llm/image/generations \
  -H "Authorization: Bearer sk-presenton-service-key-2025" \
  -H "X-User-ID: 7a6bfd31-0120-4a30-9e21-0fc3b8006579" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A unicorn with a magic wand",
    "model": "dall-e-3",
    "size": "1024x1024",
    "quality": "standard",
    "n": 1
  }'
```

**Expected**: Image generated successfully, billed to user's credit balance
**Actual**: Should work (needs verification)

### Test Case 3: BYOK (WORKS - Current Workaround)

```bash
curl -X POST https://unicorncommander.ai/api/v1/llm/image/generations \
  -H "Authorization: Bearer uc_<user-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A unicorn with a magic wand",
    "model": "dall-e-3",
    "size": "1024x1024",
    "quality": "standard",
    "n": 1
  }'
```

**Expected**: Image generated using user's OpenAI/OpenRouter BYOK key
**Actual**: ✅ WORKS (bypasses credit system)

---

## Proposed Solutions

### Option 1: Require X-User-ID Header (Recommended - Quick Fix)

**Approach**: Validate that service keys MUST provide `X-User-ID` header

**Implementation**:
```python
# In get_user_id() function
if token in service_keys:
    service_name = service_keys[token]

    x_user_id = request.headers.get('X-User-ID')
    if not x_user_id:
        raise HTTPException(
            status_code=400,
            detail="Service key authentication requires X-User-ID header. "
                   "Format: X-User-ID: <user-uuid>"
        )

    logger.info(f"✅ Service key authenticated: {service_name} proxying for user: {x_user_id}")
    return x_user_id
```

**Pros**:
- Simple, minimal code change
- Clear error message guides developers
- Maintains current architecture
- Works with existing credit system

**Cons**:
- Requires services to know user context
- Breaks service-initiated image generation use cases
- Services must track which user initiated the request

**Effort**: 1 hour (code change + testing)

---

### Option 2: Create Service User Accounts (Recommended - Complete Fix)

**Approach**: Create database user accounts for each service with their own credit balances

**Implementation**:

1. **Create Service Users in Database**:
```sql
-- Create service users in organizations table
INSERT INTO organizations (id, name, slug, billing_type, subscription_tier)
VALUES
  ('org_presenton_service', 'Presenton Service', 'presenton-service', 'prepaid', 'managed'),
  ('org_bolt_service', 'Bolt.diy Service', 'bolt-diy-service', 'prepaid', 'managed'),
  ('org_brigade_service', 'Brigade Service', 'brigade-service', 'prepaid', 'managed');

-- Allocate initial credits (e.g., 10,000 credits each)
UPDATE organizations
SET credit_balance = 10000000  -- 10,000 credits in millicredits
WHERE id IN ('org_presenton_service', 'org_bolt_service', 'org_brigade_service');
```

2. **Update get_user_id() to Return Service Org ID**:
```python
if token in service_keys:
    service_name = service_keys[token]

    x_user_id = request.headers.get('X-User-ID')
    if x_user_id:
        # Service proxying for user
        return x_user_id
    else:
        # Service-initiated request - use service org ID
        service_org_ids = {
            'presenton-service': 'org_presenton_service',
            'bolt-diy-service': 'org_bolt_service',
            'brigade-service': 'org_brigade_service',
            'centerdeep-service': 'org_centerdeep_service'
        }
        org_id = service_org_ids.get(service_name)
        if org_id:
            logger.info(f"✅ Service {service_name} using org credits: {org_id}")
            return org_id
        else:
            raise HTTPException(status_code=500, detail=f"Service org not configured: {service_name}")
```

3. **Update Credit System to Handle Org IDs**:
```python
async def get_user_tier(self, user_id: str) -> str:
    # Check if user_id is an org ID (starts with 'org_')
    if user_id.startswith('org_'):
        # Lookup org subscription tier
        org_data = await self.db.fetchrow(
            "SELECT subscription_tier FROM organizations WHERE id = $1",
            user_id
        )
        return org_data['subscription_tier'] if org_data else 'managed'
    else:
        # Existing user lookup logic
        ...
```

**Pros**:
- Supports both user-proxying AND service-initiated requests
- Proper billing separation (service vs user credits)
- Better analytics (track service vs user image generation)
- Scalable architecture

**Cons**:
- More complex implementation
- Requires database migrations
- Need to allocate/manage service credit balances
- Need monitoring for service credit usage

**Effort**: 4-6 hours (DB migration + code changes + testing)

---

### Option 3: JWT Token Authentication (Alternative - Most Flexible)

**Approach**: Use JWT tokens instead of service keys, embed user context in token

**Implementation**:

1. **Generate JWT Token with User Context**:
```python
# In Presenton/Bolt.diy backend
import jwt

token = jwt.encode({
    'service': 'presenton-service',
    'user_id': user_uuid,
    'exp': datetime.utcnow() + timedelta(hours=1)
}, service_secret, algorithm='HS256')

# Make API request
headers = {'Authorization': f'Bearer {token}'}
```

2. **Validate JWT in get_user_id()**:
```python
if not token.startswith('sk-') and not token.startswith('uc_'):
    # Try JWT validation
    try:
        payload = jwt.decode(token, service_secret, algorithms=['HS256'])
        user_id = payload.get('user_id')
        service_name = payload.get('service')
        logger.info(f"✅ JWT authenticated: {service_name} for user {user_id}")
        return user_id
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="Invalid JWT token")
```

**Pros**:
- Industry-standard authentication
- User context embedded in token (no X-User-ID header needed)
- Tokens can expire automatically
- Can include additional claims (permissions, scope, etc.)

**Cons**:
- Requires services to implement JWT generation
- Need to securely distribute service secrets
- More complex than service keys
- Requires token refresh logic

**Effort**: 6-8 hours (implement JWT generation + validation + testing)

---

## Recommended Solution

**Primary Recommendation**: **Option 2 - Create Service User Accounts**

**Reasoning**:
1. **Supports All Use Cases**: Works for both user-proxying AND service-initiated requests
2. **Proper Billing**: Services have their own credit balance, separate from user credits
3. **Better Analytics**: Can track which services consume most credits
4. **Backward Compatible**: Existing service key authentication still works
5. **Scalable**: Easy to add new services or adjust credit allocations

**Fallback Recommendation**: **Option 1 - Require X-User-ID Header**
If immediate fix needed and service-initiated image gen not required

---

## Implementation Plan

### Phase 1: Service User Accounts (Week 1)

**Day 1-2**: Database Setup
- [ ] Create migration script for service organizations
- [ ] Add service org IDs to database
- [ ] Allocate initial credit balance (10,000 credits each)
- [ ] Create service user entries in Keycloak (optional, for SSO access)

**Day 3**: Backend Implementation
- [ ] Update `get_user_id()` to return service org ID when no X-User-ID
- [ ] Update `credit_system.get_user_tier()` to handle org IDs
- [ ] Update `credit_system.get_user_credits()` to handle org IDs
- [ ] Update `credit_system.debit_credits()` to handle org IDs

**Day 4**: Testing
- [ ] Unit tests for service org ID authentication
- [ ] Integration tests for image generation with service key
- [ ] Test credit deduction from service org balance
- [ ] Test fallback to user billing when X-User-ID provided

**Day 5**: Documentation & Deployment
- [ ] Update API documentation
- [ ] Create service integration guide for Presenton/Bolt.diy
- [ ] Deploy to staging
- [ ] Smoke test all services
- [ ] Deploy to production

### Phase 2: Enhanced Error Handling (Week 2)

**Improvements**:
- [ ] Add descriptive error messages when service auth fails
- [ ] Log service credit usage for analytics
- [ ] Add admin dashboard for service credit monitoring
- [ ] Set up alerts for low service credit balances

### Phase 3: JWT Migration (Future - Optional)

**Long-term enhancement** (if needed):
- [ ] Implement JWT token generation in services
- [ ] Add JWT validation to `get_user_id()`
- [ ] Migrate services from service keys to JWT tokens
- [ ] Deprecate service keys after 6 months

---

## Testing Checklist

### Unit Tests
- [ ] Test service key auth with X-User-ID header → returns user UUID
- [ ] Test service key auth without X-User-ID → returns service org ID
- [ ] Test unknown service key → returns 401 error
- [ ] Test service org tier lookup → returns correct tier
- [ ] Test service org credit balance → returns correct balance
- [ ] Test credit deduction from service org → debits correctly

### Integration Tests
- [ ] Test Presenton image generation with service key (no X-User-ID)
- [ ] Test Presenton image generation with service key + X-User-ID
- [ ] Test Bolt.diy image generation with service key (no X-User-ID)
- [ ] Test Bolt.diy image generation with service key + X-User-ID
- [ ] Test BYOK image generation (existing functionality)
- [ ] Test user API key image generation (existing functionality)

### End-to-End Tests
- [ ] Full Presenton workflow: user requests presentation → backend generates images → credits deducted
- [ ] Full Bolt.diy workflow: user requests code with images → backend generates → credits deducted
- [ ] Verify service credit balance decreases after image generation
- [ ] Verify user credit balance NOT affected when service key used (without X-User-ID)
- [ ] Verify user credit balance IS affected when X-User-ID header present

---

## Monitoring & Metrics

### Metrics to Track (Post-Fix)

1. **Service Credit Usage**:
   - Credits consumed per service (Presenton, Bolt.diy, Brigade)
   - Cost per service per day/week/month
   - Average cost per image generation request

2. **Authentication Methods**:
   - % requests using service keys
   - % requests using service keys with X-User-ID
   - % requests using BYOK
   - % requests using user API keys

3. **Error Rates**:
   - 401 errors (before vs after fix)
   - Service auth failures
   - Credit balance exhaustion events

### Alerts to Configure

- [ ] Alert when service credit balance < 1,000 credits (low balance)
- [ ] Alert when service auth failures > 10/hour (potential issue)
- [ ] Alert when image generation 401 errors > 5/hour (auth problem)
- [ ] Weekly report on service credit consumption

---

## Security Considerations

### Service Keys Security
- ✅ Service keys are hardcoded in backend (not exposed to frontend)
- ✅ Service keys use secure format: `sk-<name>-service-key-<year>`
- ✅ Service keys are NOT rotated (should implement rotation policy)
- ⚠️ Service keys grant full API access (consider scoped permissions)

### Recommendations
1. **Implement Service Key Rotation**: Rotate keys annually or after security incidents
2. **Add Scope Restrictions**: Limit service keys to specific API endpoints
3. **Rate Limiting**: Implement per-service rate limits to prevent abuse
4. **Audit Logging**: Log all service key usage for security audits

---

## Questions & Answers

### Q: Why not just fix Presenton/Bolt.diy to always send X-User-ID?
**A**: This would work as a short-term fix, but:
- Requires code changes in multiple services
- Breaks service-initiated use cases (background jobs, admin actions)
- Service user accounts provide better billing separation and analytics

### Q: Can services share the same credit balance?
**A**: No, each service should have its own org ID and credit balance for:
- Better cost tracking
- Independent scaling
- Clear billing attribution

### Q: What happens if a service runs out of credits?
**A**: Image generation will fail with 402 error (Insufficient Credits). Admin needs to:
1. Check service credit usage dashboard
2. Allocate more credits to service org
3. Investigate if usage is expected or needs optimization

### Q: Can we use JWT tokens AND service keys simultaneously?
**A**: Yes, `get_user_id()` can support multiple authentication methods:
1. Try session cookie
2. Try service key
3. Try API key
4. Try JWT token
5. Return 401 if all fail

### Q: Does this fix affect BYOK users?
**A**: No, BYOK logic is separate:
- BYOK checks if user has `openrouter` or `openai` keys in database
- If BYOK key exists, credit system is bypassed entirely
- Service key auth does not interfere with BYOK flow

---

## References

### Code Locations
- **Authentication**: `/backend/litellm_api.py` lines 640-743 (`get_user_id()`)
- **Image Generation**: `/backend/litellm_api.py` lines 1411-1600
- **Credit System**: `/backend/litellm_credit_system.py`
- **BYOK Manager**: `/backend/byok_manager.py`

### Related Documentation
- Image Generation API Guide: `/docs/api/IMAGE_GENERATION_API_GUIDE.md`
- Image Generation Quick Start: `/docs/api/IMAGE_GENERATION_QUICK_START.md`
- Integration Guide: `/docs/INTEGRATION_GUIDE.md`
- CLAUDE.md: Issue documented in "Known Issues" section

### External Resources
- OpenAI Image Generation API: https://platform.openai.com/docs/api-reference/images
- OpenRouter Image Models: https://openrouter.ai/models?order=newest&supported_parameters=image_generation
- JWT Authentication: https://jwt.io/introduction

---

## Conclusion

The 401 authentication errors for service-to-service image generation are caused by a **design assumption mismatch**: service keys were designed for user-proxying (with `X-User-ID` header), not service-initiated requests.

**The fix** is to create service user accounts (organization records) with their own credit balances, allowing services to make API calls without user context. This provides proper billing separation, better analytics, and supports all use cases.

**Estimated effort**: 1 week for full implementation and testing
**Priority**: Medium (workaround exists via BYOK)
**Risk**: Low (backward compatible, no breaking changes)

---

**Document Version**: 1.0
**Author**: Backend Authentication Team Lead
**Last Updated**: November 29, 2025
**Status**: Ready for Review → Implementation
