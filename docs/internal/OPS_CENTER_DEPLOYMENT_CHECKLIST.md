# Ops-Center Organizational Billing - Deployment Checklist

**Date**: November 12, 2025
**Goal**: Deploy complete organizational billing system to production
**Status**: Backend complete + Security hardened → Ready for deployment

---

## ✅ Pre-Deployment Status

### Backend (COMPLETE)
- ✅ **org_billing_api.py** (1,194 lines) - 17 REST API endpoints
- ✅ **auth_dependencies.py** (216 lines) - FastAPI auth dependencies
- ✅ **request_id_middleware.py** (121 lines) - Request tracking
- ✅ **server.py** - CORS hardening + rate limiting configured
- ✅ **Security hardened** - 91% test pass rate, 0 critical issues

### Database (READY)
- ✅ **create_org_billing.sql** (501 lines) - Migration script ready
  - 5 tables
  - 4 stored functions
  - 4 views
  - Indexes and constraints

### Testing (PENDING)
- ⏳ Database migration execution
- ⏳ API endpoint validation
- ⏳ Test organization setup
- ⏳ Credit allocation testing

### Frontend (NOT STARTED)
- ❌ React components (Phase 2)
- ❌ Organization dashboard
- ❌ Credit management UI

---

## Phase 1: Database Deployment (PRIORITY)

### Task 1.1: Database Connection Verification
- [ ] Verify `unicorn-postgresql` container is running
- [ ] Test connection from `ops-center-direct` to database
- [ ] Verify `unicorn_db` database exists
- [ ] Check for conflicting table names

### Task 1.2: Run Database Migration
- [ ] Backup current database (safety first)
- [ ] Copy `create_org_billing.sql` to database container
- [ ] Execute migration script
- [ ] Verify all 5 tables created:
  - `organization_subscriptions`
  - `organization_credit_pools`
  - `user_credit_allocations`
  - `credit_usage_attribution`
  - `org_billing_history`
- [ ] Verify all 4 stored functions created:
  - `has_sufficient_credits()`
  - `deduct_credits()`
  - `add_credits_to_pool()`
  - `allocate_credits_to_user()`
- [ ] Verify all 4 views created:
  - `v_org_billing_summary`
  - `v_user_credit_status`
  - `v_org_member_allocations`
  - `v_credit_usage_by_service`
- [ ] Verify indexes created
- [ ] Test stored functions with sample data

### Task 1.3: Database Validation
- [ ] Check table row counts (should be 0 initially)
- [ ] Test foreign key constraints
- [ ] Test row-level locking (FOR UPDATE)
- [ ] Verify transaction isolation

---

## Phase 2: Backend Validation (PRIORITY)

### Task 2.1: Container Health Check
- [ ] Verify `ops-center-direct` container running
- [ ] Check container logs for startup errors
- [ ] Verify port 8084 accessible
- [ ] Test `/health` endpoint (if exists)

### Task 2.2: API Endpoint Testing (17 endpoints)

**Subscription Management (5 endpoints)**
- [ ] `POST /api/v1/org-billing/subscriptions` - Create subscription
- [ ] `GET /api/v1/org-billing/subscriptions/{subscription_id}` - Get subscription
- [ ] `GET /api/v1/org-billing/subscriptions/org/{org_id}` - List org subscriptions
- [ ] `PUT /api/v1/org-billing/subscriptions/{subscription_id}` - Update subscription
- [ ] `DELETE /api/v1/org-billing/subscriptions/{subscription_id}` - Cancel subscription

**Credit Management (6 endpoints)**
- [ ] `POST /api/v1/org-billing/credits/{org_id}/add` - Add credits to pool
- [ ] `GET /api/v1/org-billing/credits/{org_id}` - Get credit pool balance
- [ ] `POST /api/v1/org-billing/credits/{org_id}/allocate` - Allocate credits to user
- [ ] `GET /api/v1/org-billing/credits/user/{user_id}` - Get user allocation
- [ ] `POST /api/v1/org-billing/credits/deduct` - Deduct credits (internal)
- [ ] `GET /api/v1/org-billing/credits/{org_id}/usage` - Get usage history

**Billing Queries (3 endpoints)**
- [ ] `GET /api/v1/org-billing/billing/user` - Get user's billing dashboard
- [ ] `GET /api/v1/org-billing/billing/org/{org_id}` - Get org billing summary
- [ ] `GET /api/v1/org-billing/billing/system` - System-wide billing (admin only)

**Organization Management (3 endpoints)**
- [ ] `GET /api/v1/org-billing/organizations` - List user's organizations
- [ ] `GET /api/v1/org-billing/organizations/{org_id}/members` - List org members
- [ ] `POST /api/v1/org-billing/organizations/{org_id}/members` - Add member

### Task 2.3: Authentication Testing
- [ ] Test unauthenticated requests (should return 401)
- [ ] Test with valid session token
- [ ] Test admin-only endpoints (non-admin should get 403)
- [ ] Test org admin permissions
- [ ] Verify auth happens BEFORE body validation (security fix)

### Task 2.4: Security Testing
- [ ] Test rate limiting (should see 429 after threshold)
- [ ] Test CORS restrictions (malicious origins blocked)
- [ ] Test request ID tracking (X-Request-ID header present)
- [ ] Test SQL injection protection
- [ ] Test XSS protection
- [ ] Test negative credits validation (should return 400, not 500)

---

## Phase 3: Test Data Creation

### Task 3.1: Create Test Organization
- [ ] Create organization: "Test Org Alpha"
- [ ] Set org admin user
- [ ] Verify organization record created

### Task 3.2: Create Test Subscription
- [ ] Create Platform plan subscription ($50/mo)
- [ ] Verify subscription_id returned
- [ ] Check organization_subscriptions table
- [ ] Verify billing_cycle = "monthly"
- [ ] Verify trial_days if applicable

### Task 3.3: Add Credits to Pool
- [ ] Add 10,000 credits to test org
- [ ] Verify organization_credit_pools.total_credits = 10,000
- [ ] Verify organization_credit_pools.available_credits = 10,000
- [ ] Check org_billing_history for transaction

### Task 3.4: Allocate Credits to User
- [ ] Allocate 1,000 credits to test user
- [ ] Verify user_credit_allocations record created
- [ ] Verify available_credits = 10,000 - 1,000 = 9,000
- [ ] Check allocation history

### Task 3.5: Test Credit Deduction
- [ ] Deduct 50 credits for test service (e.g., "company_enrichment")
- [ ] Verify user allocation reduced by 50
- [ ] Verify credit_usage_attribution record created
- [ ] Check deduction was atomic (no race conditions)

### Task 3.6: Test Multi-User Scenario
- [ ] Add second user to organization
- [ ] Allocate 500 credits to second user
- [ ] Verify both users have independent allocations
- [ ] Test concurrent credit deductions

---

## Phase 4: Integration Points (For LoopNet Agent)

### Task 4.1: Document API Integration
- [ ] Create `ORG_BILLING_INTEGRATION_GUIDE.md`
- [ ] Document authentication flow
- [ ] Document credit deduction flow
- [ ] Provide code examples

### Task 4.2: Credit Deduction Service
- [ ] Document how to deduct credits from service layer
- [ ] Example: Company enrichment costs 50 credits
- [ ] Example: Contact lookup costs 10 credits
- [ ] Example: Bulk operations cost calculation

### Task 4.3: Usage Attribution
- [ ] Document service_name taxonomy
  - `company_enrichment`
  - `contact_lookup`
  - `bulk_export`
  - `intelligence_cache_lookup`
- [ ] Document metadata structure (JSON)
- [ ] Example attribution records

### Task 4.4: Organization Context
- [ ] Document how services get org_id from user session
- [ ] Document how to check user's org membership
- [ ] Document how to verify credit availability before operations

---

## Phase 5: Frontend Development (Phase 2 - Future)

### Task 5.1: Organization Dashboard
- [ ] Organization overview card
- [ ] Current subscription plan display
- [ ] Credit pool balance
- [ ] Usage graphs (last 30 days)
- [ ] Member list with allocations

### Task 5.2: Credit Management UI
- [ ] Admin: Add credits to pool
- [ ] Admin: Allocate credits to users
- [ ] Admin: View usage by user
- [ ] User: View own allocation
- [ ] User: View own usage history

### Task 5.3: Subscription Management UI
- [ ] View current plan
- [ ] Compare plans (Platform, BYOK, Hybrid)
- [ ] Upgrade/downgrade flow
- [ ] Cancel subscription flow
- [ ] Payment method management

---

## Phase 6: Monitoring & Logging

### Task 6.1: Database Monitoring
- [ ] Monitor credit_usage_attribution table growth
- [ ] Monitor query performance
- [ ] Set up alerts for low credits
- [ ] Set up alerts for failed transactions

### Task 6.2: Application Logging
- [ ] Verify request IDs in logs
- [ ] Verify credit deduction logs include:
  - user_id
  - org_id
  - service_name
  - credits_deducted
  - request_id
- [ ] Set up log aggregation

### Task 6.3: Security Monitoring
- [ ] Monitor rate limit violations (429 responses)
- [ ] Monitor authentication failures (401 responses)
- [ ] Monitor authorization failures (403 responses)
- [ ] Set up alerts for suspicious activity

---

## Phase 7: Production Readiness

### Task 7.1: Performance Testing
- [ ] Load test credit deduction (100 concurrent requests)
- [ ] Test transaction isolation under high load
- [ ] Measure response times for all endpoints
- [ ] Verify no deadlocks occur

### Task 7.2: Backup & Recovery
- [ ] Set up automated database backups
- [ ] Document restore procedure
- [ ] Test restore from backup
- [ ] Document rollback procedure

### Task 7.3: Documentation
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Database schema documentation
- [ ] Deployment runbook
- [ ] Troubleshooting guide

### Task 7.4: Handoff to LoopNet Agent
- [ ] Create `LOOPNET_INTEGRATION_INSTRUCTIONS.md`
- [ ] Document working endpoints
- [ ] Provide test credentials
- [ ] Share integration guide

---

## Success Criteria

### ✅ Phase 1 Complete When:
- All database tables, functions, views created
- Database migration runs without errors
- Sample data can be inserted

### ✅ Phase 2 Complete When:
- All 17 API endpoints respond correctly
- Authentication works (401 for unauthenticated)
- Authorization works (403 for unauthorized)
- Security tests pass (91%+ pass rate maintained)

### ✅ Phase 3 Complete When:
- Test organization exists with active subscription
- Credits can be added, allocated, and deducted
- Usage attribution records created correctly

### ✅ Phase 4 Complete When:
- Integration guide created
- LoopNet agent has clear instructions
- Code examples provided

### ✅ Production Ready When:
- All tests pass
- Performance benchmarks met
- Monitoring configured
- Documentation complete

---

## Team Assignments (Subagent Teamleads)

### Database Team Lead
**Responsibility**: Phase 1 (Database Deployment)
- Execute migration script
- Validate schema
- Create test data
- Monitor performance

### Backend Testing Team Lead
**Responsibility**: Phase 2 (Backend Validation)
- Test all 17 API endpoints
- Run security tests
- Validate authentication/authorization
- Document any issues

### Integration Team Lead
**Responsibility**: Phase 4 (Integration Points)
- Create integration guide
- Document credit deduction flow
- Provide code examples
- Prepare handoff to LoopNet agent

### Monitoring Team Lead
**Responsibility**: Phase 6 (Monitoring & Logging)
- Set up log aggregation
- Configure alerts
- Monitor system health
- Track key metrics

---

## Current Status: READY TO DEPLOY

**Backend**: ✅ Complete (1,194 lines + security hardened)
**Database**: ✅ Migration ready (501 lines)
**Testing**: ⏳ Pending
**Frontend**: ❌ Phase 2 (future work)

**Next Step**: Launch Database Team Lead to execute Phase 1

---

## Notes

- Security fixes already applied (91% pass rate, 0 critical issues)
- Rate limiting configured (20/min POST, 100/min GET)
- CORS restricted to known domains
- Request ID tracking enabled
- Auth dependency injection working correctly

**Created**: November 12, 2025
**Updated**: November 12, 2025
**Version**: 1.0
