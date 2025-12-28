# Epic 1.8: Credit & Usage Metering System

**Date**: October 23, 2025
**Status**: 🚀 STARTING IMPLEMENTATION
**Priority**: HIGH (Revenue Model Foundation)
**Epic Type**: Backend + Frontend + Testing
**Estimated Time**: 2-3 days

---

## 🎯 Executive Summary

Implement a **hybrid credit and metering system** that supports both BYOK (Bring Your Own Key) and managed credit subscriptions. This enables flexible pricing tiers while automatically creating and managing OpenRouter accounts for users.

**Business Model**:
- **Free Tier**: Auto-created OpenRouter account with free models + micro-markup
- **Starter ($30/month)**: $30 in platform credits + managed OpenRouter
- **Professional ($50/month)**: $50 in credits OR BYOK option
- **Enterprise ($99/month)**: $100 in credits OR BYOK + 0% markup

---

## 📋 Requirements

### 1. Credit Tracking System

**Database Schema**:
- `user_credits` - User credit balances
- `credit_transactions` - Audit trail of all credit movements
- `credit_allocations` - Monthly credit allocation rules
- `openrouter_accounts` - Programmatically created OpenRouter accounts
- `coupon_codes` - Promotional codes system

**Features**:
- Track user credit balance in real-time
- Support multiple credit types (allocated, bonus, overage)
- Monthly credit reset with rollover rules
- Detailed transaction history
- Credit expiration policies

### 2. OpenRouter Automation

**Programmatic Account Creation**:
- Auto-create OpenRouter account for new users
- Store encrypted API keys
- Sync free credit balance from OpenRouter
- Manage account lifecycle

**Smart Routing**:
- Route requests through user's OpenRouter account
- Detect free vs paid models automatically
- Apply appropriate markup (0% free, 10% paid)
- Track usage per model
- Handle fallbacks and errors

### 3. Usage Metering

**Track All API Usage**:
- LiteLLM chat completions
- Embedding requests
- TTS requests
- Center-Deep searches
- Brigade agent invocations

**Metering Details**:
- Tokens used
- Cost from provider
- Platform markup
- Model used
- Timestamp
- User attribution

### 4. Coupon System

**Coupon Types**:
- `FREEMONTH` - Free month of service
- `WELCOME10` - $10 bonus credits
- `EARLYBIRD` - Percentage discounts
- Custom codes for partnerships

**Features**:
- Redemption tracking
- Max uses per code
- Expiration dates
- Per-user limits
- Admin creation interface

### 5. Tier Management

**Subscription Tiers**:
```
Free Tier:
  - Auto OpenRouter account
  - $10 free credits (OpenRouter)
  - Free models only
  - $0.001/1k token markup

Starter ($30/month):
  - Managed OpenRouter account
  - $30 platform credits
  - Free + paid models
  - 10% markup on paid models

Professional ($50/month):
  - Option A: $50 credits + 5% markup
  - Option B: BYOK (no markup)

Enterprise ($99/month):
  - Option A: $100 credits + 0% markup
  - Option B: BYOK (no markup)
  - Team features
```

---

## 🔧 Technical Implementation

### Backend APIs (20 endpoints)

**Credit Management**:
- `GET /api/v1/credits/balance` - Get current balance
- `POST /api/v1/credits/allocate` - Allocate credits (admin)
- `GET /api/v1/credits/transactions` - Transaction history
- `POST /api/v1/credits/deduct` - Deduct credits (internal)
- `POST /api/v1/credits/refund` - Refund credits (admin)

**OpenRouter Automation**:
- `POST /api/v1/openrouter/create-account` - Create account
- `GET /api/v1/openrouter/account` - Get account info
- `POST /api/v1/openrouter/sync-balance` - Sync free credits
- `DELETE /api/v1/openrouter/account` - Delete account

**Usage Metering**:
- `POST /api/v1/metering/track` - Track usage event
- `GET /api/v1/metering/summary` - Usage summary
- `GET /api/v1/metering/by-model` - Model breakdown
- `GET /api/v1/metering/by-date` - Daily/monthly usage
- `GET /api/v1/metering/free-tier` - Free tier usage

**Coupon System**:
- `POST /api/v1/coupons/redeem` - Redeem code
- `POST /api/v1/coupons/create` - Create code (admin)
- `GET /api/v1/coupons/validate` - Validate code
- `GET /api/v1/coupons/list` - List codes (admin)
- `DELETE /api/v1/coupons/{code}` - Delete code (admin)

**Tier Management**:
- `GET /api/v1/tiers/compare` - Compare tiers
- `POST /api/v1/tiers/switch` - Switch tier

### Frontend Components (8 new)

1. **CreditDashboard.jsx** - Main credit overview
2. **CreditTransactions.jsx** - Transaction history table
3. **UsageMetrics.jsx** - Usage charts and breakdown
4. **ModelUsageChart.jsx** - Per-model usage visualization
5. **CouponRedemption.jsx** - Redeem coupon codes
6. **TierComparison.jsx** - Pricing tier comparison
7. **CreditAllocation.jsx** - Admin credit allocation (admin only)
8. **OpenRouterAccountStatus.jsx** - OpenRouter account info

### Database Migrations

**New Tables** (5):
- `user_credits` (7 columns)
- `credit_transactions` (10 columns)
- `openrouter_accounts` (8 columns)
- `coupon_codes` (9 columns)
- `usage_events` (12 columns)

**Indexes**:
- 15 indexes for query optimization
- Foreign keys to users table
- Composite indexes for date range queries

---

## 🧪 Testing Requirements

### Unit Tests (60+ tests)
- Credit allocation logic
- Deduction and refund logic
- Coupon validation
- OpenRouter account creation
- Usage metering calculations
- Markup calculations (free vs paid models)

### Integration Tests (40+ tests)
- End-to-end credit flow
- OpenRouter API integration
- Multi-user scenarios
- Credit expiration
- Tier switching
- Coupon redemption

### Performance Tests (10+ tests)
- High-volume usage tracking
- Concurrent credit deductions
- Database query performance
- API response times

### Security Tests (20+ tests)
- API key encryption
- Authorization checks
- Rate limiting
- SQL injection prevention
- XSS prevention

---

## 📊 Success Criteria

### Backend
- [ ] All 20 API endpoints implemented
- [ ] Database migrations applied
- [ ] OpenRouter automation working
- [ ] Credit deduction atomic and accurate
- [ ] All tests passing (130+ tests)

### Frontend
- [ ] 8 new components created
- [ ] Credit dashboard showing real-time balance
- [ ] Usage charts with model breakdown
- [ ] Tier comparison page
- [ ] Coupon redemption flow

### Integration
- [ ] OpenRouter accounts auto-created
- [ ] Free models detected automatically
- [ ] Markup calculated correctly
- [ ] Credits deducted accurately
- [ ] Coupons redeemable

### Documentation
- [ ] API reference complete
- [ ] User guide for credit system
- [ ] Admin guide for credit allocation
- [ ] Coupon management guide

---

## 🚀 Implementation Strategy

### Hierarchical Agent Deployment

**3 Team Leads** (can spawn subagents):

1. **Backend Team Lead**
   - Database schema design
   - API implementation
   - OpenRouter integration
   - Can spawn: Database specialist, API developer, Integration engineer

2. **Frontend Team Lead**
   - Component design
   - Credit dashboard
   - Usage visualization
   - Can spawn: UI designer, Chart specialist, UX reviewer

3. **Testing & DevOps Team Lead**
   - Test suite creation
   - Database migrations
   - Documentation
   - Can spawn: Unit tester, Integration tester, Performance tester

Each team lead has full autonomy to spawn specialized subagents as needed for optimal implementation.

---

## 📈 Business Impact

**Revenue Model**:
- Free tier → Paid conversion via usage growth
- Multiple price points ($30, $50, $99)
- BYOK option for technical users
- Markup revenue on managed accounts

**Projected Revenue** (100 users):
- 50 Free users: $50-100/month (markup)
- 30 Starter users: $900/month
- 15 Professional: $750/month
- 5 Enterprise: $495/month
- **Total**: ~$2,200/month

**Costs** (100 users):
- OpenRouter credits: ~$800/month
- Server infrastructure: ~$200/month
- **Total**: ~$1,000/month

**Net Profit**: ~$1,200/month (55% margin)

---

## 🎯 Deliverables

1. **Backend Module**: `backend/credit_system.py` (800+ lines)
2. **Backend Module**: `backend/openrouter_automation.py` (600+ lines)
3. **Backend Module**: `backend/usage_metering.py` (500+ lines)
4. **Backend Module**: `backend/coupon_system.py` (400+ lines)
5. **API Router**: `backend/credit_api.py` (700+ lines)
6. **Database Migrations**: 5 SQL files
7. **Frontend Components**: 8 React components (2,500+ lines)
8. **Test Suite**: 130+ tests (2,000+ lines)
9. **Documentation**: 6 guides (3,000+ lines)

**Total Code**: ~9,000 lines
**Total Documentation**: ~3,000 lines

---

**Epic Owner**: Team Lead Coordination
**Start Date**: October 23, 2025
**Target Completion**: October 26, 2025 (3 days)
