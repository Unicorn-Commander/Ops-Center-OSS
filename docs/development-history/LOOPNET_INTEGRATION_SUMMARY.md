# LoopNet Integration - Executive Summary

**Date**: November 12, 2025
**Status**: ✅ Integration Guide Complete
**Deliverable**: `LOOPNET_INTEGRATION_GUIDE.md` (2,100+ lines)

---

## What Was Delivered

A comprehensive **82-page integration guide** for the LoopNet agent to integrate with Ops-Center's organizational billing system.

**File Location**: `/opt/ops-center/LOOPNET_INTEGRATION_GUIDE.md`

---

## Guide Contents

### 1. Executive Summary
- What organizational billing is
- Why credit-based system
- Integration checklist

### 2. Architecture Overview
- High-level flow diagrams (ASCII art)
- Credit flow visualization
- Subscription plan comparison

### 3. Getting Started
- Prerequisites
- Base URL and required headers
- Quick test commands

### 4. Authentication & Authorization
- How Keycloak session works
- Extracting organization context
- Permission levels (Member/Admin/System Admin)

### 5. Credit System Explained
- What credits are (1 credit ≈ $0.001)
- Credit pricing examples
- Credit lifecycle and resets

### 6. API Endpoint Reference (17 Endpoints)

**Subscription Management (5)**:
- Create subscription
- Get subscription
- Upgrade subscription
- List subscriptions
- Cancel subscription

**Credit Management (6)**:
- Get credit pool
- Add credits to pool
- Allocate credits to user
- Get user allocation
- Deduct credits (internal)
- Get credit usage stats

**Billing Queries (3)**:
- User billing dashboard
- Org admin billing screen
- System admin overview

**Organization Management (3)**:
- List organizations
- Get org members
- Add member

### 7. Credit Deduction Service

**Complete Implementation**:
- When to deduct credits
- Database function usage
- Python integration class
- FastAPI endpoint example
- Error handling

**Example Operations**:
- Company enrichment (50-100 credits)
- Contact lookup (10 credits)
- Bulk export (5 credits per record)
- Intelligence cache (2 credits)

### 8. Usage Attribution

**Service Taxonomy**:
```
company_enrichment
contact_lookup
bulk_export
intelligence_cache_lookup
property_search
valuation
```

**Metadata Structure**: Complete JSON schema with examples

**Analytics Queries**: SQL examples for reporting

### 9. Organization Context

- Multi-org support
- Org selector implementation
- Verifying membership
- Context management class

### 10. Code Examples (4 Complete Examples)

**Example 1**: Simple credit check
```python
can_afford, message = await can_user_afford_operation(...)
```

**Example 2**: Company enrichment with credits
```python
result = await enrich_company_with_credits(...)
# Includes: check, operation, deduction, error handling
```

**Example 3**: Bulk operations
```python
result = await bulk_export_companies(...)
# Cost: 5 credits per record
```

**Example 4**: Intelligence cache lookup
```python
result = await lookup_cached_intelligence(...)
# Cost: 2 credits (cheaper than enrichment)
```

### 11. Error Handling

**5 Error Scenarios**:
1. Insufficient credits (402 Payment Required)
2. No credit allocation (403 Forbidden)
3. Not authenticated (401 Unauthorized)
4. Not organization member (403 Forbidden)
5. Rate limit exceeded (429 Too Many Requests)

**Error Response Format**: Standardized JSON structure

**Retry Strategy**: Exponential backoff with tenacity

### 12. Testing Guide

**Test Organization Setup**: Template for creating test org

**Testing Checklist**: 6-phase testing plan
- Phase 1: Authentication
- Phase 2: Credit checks
- Phase 3: Credit deduction
- Phase 4: Error handling
- Phase 5: Multi-operation testing
- Phase 6: Analytics

**Test Cases** (4 Complete):
1. Happy path test
2. Insufficient credits test
3. No allocation test
4. Operation failure test (no credit loss)

**Manual Testing**: cURL commands for all endpoints

### 13. Security Considerations

**7 Security Topics**:
1. Authentication order (auth before validation)
2. Rate limiting (20 POST/min, 100 GET/min)
3. CORS restrictions
4. Request ID tracking
5. Atomic operations (row-level locking)
6. Input validation
7. Sensitive data handling

### 14. FAQ (10 Questions)

Q1: What if user belongs to multiple organizations?
Q2: How do I know credit cost before operation?
Q3: What happens if operation fails after credit deduction?
Q4: Can I refund credits?
Q5: How often do credits reset?
Q6: Can users purchase credits directly?
Q7: What's the difference between allocated vs available?
Q8: How do I test without spending real credits?
Q9: What if database connection fails?
Q10: Can I deduct fractional credits?

### 15. Support & Resources

- Documentation links
- API reference
- Database access
- Example code repository
- Contact information

### Appendices

**A. Credit Pricing Reference**:
- LoopNet operations pricing table
- General operations pricing table

**B. Database Schema**:
- 5 tables with CREATE statements
- 4 stored functions with signatures

**C. Glossary**:
- 14 key terms defined

---

## Key Integration Points

### 1. Authentication Flow

```
User → Keycloak Login → Session Token Cookie
     → Ops-Center API (validates session)
     → Extracts user_id + org_id
     → Service can now make billing API calls
```

### 2. Credit Deduction Flow

```
1. Check credits (optional, for UX)
   ↓
2. Perform operation
   ↓
3. IF operation succeeds:
   → Deduct credits
   → Record attribution
   ELSE:
   → Do NOT deduct credits
```

### 3. Multi-Organization Support

```
User belongs to: [Org A, Org B, Org C]
                      ↓
Application: "Which organization?"
                      ↓
User selects: Org B
                      ↓
All operations use: org_id = Org B
```

---

## Technology Stack

**Backend**:
- FastAPI (Python 3.10+)
- PostgreSQL (unicorn_db)
- asyncpg (async database driver)

**Authentication**:
- Keycloak SSO
- Session token cookies

**Database Functions**:
- `has_sufficient_credits()`
- `deduct_credits()`
- `add_credits_to_pool()`
- `allocate_credits_to_user()`

---

## Credit Pricing Guide

### LoopNet Operations

| Operation | Credits | USD |
|-----------|---------|-----|
| Company Enrichment (Standard) | 50 | $0.05 |
| Company Enrichment (Full) | 100 | $0.10 |
| Contact Lookup | 10 | $0.01 |
| Bulk Export (per record) | 5 | $0.005 |
| Intelligence Cache | 2 | $0.002 |
| Property Valuation | 75 | $0.075 |
| Market Analysis | 150 | $0.15 |

### Subscription Plans

| Plan | Monthly | Description |
|------|---------|-------------|
| **Platform** | $50 | Managed credits, 1.5x markup |
| **BYOK** | $30 | Bring Your Own Keys, passthrough |
| **Hybrid** | $99 | Mix of managed + BYOK |

---

## Quick Start

### 1. Get Session Token

```python
session_token = request.cookies.get('session_token')
```

### 2. Get User's Organizations

```python
response = requests.get(
    'https://api.unicorncommander.ai/api/v1/org-billing/billing/user',
    cookies={'session_token': session_token}
)
orgs = response.json()['organizations']
org_id = orgs[0]['org_id']  # Or let user select
```

### 3. Check Credits (Optional)

```python
has_credits = await conn.fetchval(
    "SELECT has_sufficient_credits($1, $2, $3)",
    org_id, user_id, 50
)
```

### 4. Perform Operation

```python
result = await enrich_company(company_id)
```

### 5. Deduct Credits (After Success)

```python
await conn.execute(
    "SELECT deduct_credits($1, $2, $3, $4, $5, $6, $7::jsonb)",
    org_id, user_id, 50, 'company_enrichment',
    'LoopNet Company Enrichment v2',
    request_id, json.dumps(metadata)
)
```

---

## Common Pitfalls to Avoid

### ❌ DON'T: Deduct credits before operation

```python
# WRONG - credits deducted even if operation fails
await deduct_credits(50)
result = await enrich_company()  # Might fail
```

### ✅ DO: Deduct credits after operation succeeds

```python
# CORRECT - only deduct if operation succeeds
result = await enrich_company()
if result.success:
    await deduct_credits(50)
```

### ❌ DON'T: Use hardcoded org_id

```python
# WRONG - assumes user only has one org
org_id = "some-uuid"
```

### ✅ DO: Get org_id from user session

```python
# CORRECT - respects user's org selection
user_context = await get_user_org_context(session_token)
org_id = user_context['org_id']
```

### ❌ DON'T: Ignore insufficient credit errors

```python
# WRONG - operation proceeds even without credits
try:
    await deduct_credits(50)
except:
    pass  # Ignores error
await perform_operation()  # Runs without payment
```

### ✅ DO: Block operation if insufficient credits

```python
# CORRECT - check credits first, block if insufficient
has_credits = await check_sufficient_credits(org_id, user_id, 50)
if not has_credits:
    raise HTTPException(402, "Insufficient credits")
# Only perform operation if user has credits
await perform_operation()
await deduct_credits(50)
```

---

## Testing Resources

### Test Organization Request

Contact Ops-Center team to create test org:

```json
{
  "org_name": "test-loopnet-integration",
  "display_name": "LoopNet Test Organization",
  "subscription_plan": "platform",
  "initial_credits": 10000,
  "test_users": [
    {"email": "loopnet-test-1@example.com", "allocated_credits": 1000},
    {"email": "loopnet-test-2@example.com", "allocated_credits": 500}
  ]
}
```

### Database Queries for Testing

```bash
# View user allocations
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
  SELECT user_id, allocated_credits, used_credits, remaining_credits
  FROM user_credit_allocations
  WHERE org_id = 'TEST_ORG_UUID';"

# View recent credit usage
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
  SELECT service_type, credits_used, request_metadata->>'company_id',
         created_at
  FROM credit_usage_attribution
  WHERE org_id = 'TEST_ORG_UUID'
  ORDER BY created_at DESC LIMIT 10;"
```

---

## Success Metrics

### Integration is successful when:

- ✅ Can authenticate with Keycloak SSO
- ✅ Can retrieve user's organizations and credit status
- ✅ Can check if user has sufficient credits
- ✅ Can deduct credits after successful operations
- ✅ Credits NOT deducted if operation fails
- ✅ Attribution records created with correct metadata
- ✅ Can query usage analytics by service type
- ✅ Error handling returns appropriate HTTP status codes
- ✅ Rate limits respected (20 POST/min, 100 GET/min)
- ✅ Multi-org support works (user can switch orgs)

---

## Next Steps for LoopNet Agent

### Phase 1: Setup (Week 1)
1. Request test organization from Ops-Center team
2. Get test user credentials
3. Test authentication flow
4. Verify API connectivity

### Phase 2: Integration (Week 2)
1. Implement `get_user_org_context()` function
2. Implement `CreditDeductionService` class
3. Add credit checks to existing endpoints
4. Add credit deductions after operations

### Phase 3: Testing (Week 3)
1. Run automated test suite
2. Test all error scenarios
3. Verify attribution records
4. Load testing (concurrent operations)

### Phase 4: Production (Week 4)
1. Switch to production Ops-Center API
2. Monitor credit deductions in logs
3. Set up alerts for errors
4. Document internal integration

---

## Contact Information

**Ops-Center Integration Team**:
- **Email**: ops-center@unicorncommander.ai
- **Slack**: #ops-center-integration
- **GitHub**: https://github.com/Unicorn-Commander/Ops-Center

**For Urgent Issues**:
- Include `[URGENT]` in subject
- Provide `X-Request-ID` from headers
- Attach relevant logs

**Documentation**:
- **Full Guide**: `/opt/ops-center/LOOPNET_INTEGRATION_GUIDE.md`
- **Deployment Checklist**: `OPS_CENTER_DEPLOYMENT_CHECKLIST.md`
- **API Implementation**: `backend/org_billing_api.py`

---

## Conclusion

This integration guide provides **everything needed** for the LoopNet agent to integrate with Ops-Center's organizational billing system:

✅ **Architecture diagrams** - Understand the system
✅ **17 API endpoints** - Complete reference with examples
✅ **Credit deduction service** - Production-ready Python code
✅ **4 code examples** - Copy-paste-ready implementations
✅ **Testing guide** - Comprehensive test plan
✅ **Security best practices** - Avoid common pitfalls
✅ **FAQ** - Answers to 10 common questions
✅ **Pricing reference** - All credit costs documented

**Total Content**: 2,100+ lines of documentation

**Estimated Integration Time**: 3-4 weeks

**Difficulty Level**: Moderate (requires async Python, PostgreSQL, FastAPI knowledge)

---

**Guide Created**: November 12, 2025
**Version**: 1.0
**By**: Ops-Center Integration Team Lead
**For**: LoopNet Agent Development Team

Ready to integrate! 🚀
