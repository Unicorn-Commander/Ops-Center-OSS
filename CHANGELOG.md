# Changelog

All notable changes to Ops-Center will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.0] - 2025-11-09

### Major Refactoring: Feature → App Terminology

**Breaking Changes**:
- API endpoint `/api/v1/admin/features` renamed to `/api/v1/admin/apps`
- Frontend route `/admin/system/feature-management` renamed to `/admin/system/app-management`

### Changed

#### Database Schema
- **Table Renamed**: `feature_definitions` → `app_definitions`
- **Table Renamed**: `tier_features` → `tier_apps`
- **Column Renamed** (app_definitions): `feature_key` → `app_key`, `feature_name` → `app_name`, `feature_description` → `app_description`, `feature_icon` → `app_icon`
- **Column Renamed** (tier_apps): `feature_key` → `app_key`, `feature_value` → `app_value`
- **Backward Compatibility**: Created views `feature_definitions` and `tier_features` as aliases for transition period

#### Backend API
- **New File**: `backend/app_definitions_api.py` - App management endpoints
- **Updated**: `backend/tier_features_api.py` - Updated to use `tier_apps` table
- **Updated**: `backend/server.py` - Router registration updated
- **Updated**: `backend/subscription_tiers_api.py` - Updated JOIN to use `tier_apps`
- **Updated**: `backend/my_apps_api.py` - Updated terminology throughout

#### Frontend
- **Renamed**: `FeatureManagement.jsx` → `AppManagement.jsx` (16.15 KB)
- **Updated**: `App.jsx` - Route and import updated
- **Updated**: `Layout.jsx` - Navigation menu updated
- **Updated**: `SubscriptionManagement.jsx` - API calls and data mapping updated
- **UI Text**: All instances of "Feature" changed to "App" throughout interface

### Added
- **Migration Script**: `backend/migrations/rename_features_to_apps.sql` (1.8 KB)
- **Documentation**: `FEATURE_TO_APP_REFACTORING_COMPLETE.md` - Comprehensive refactoring guide
- **API Endpoints**: 4 new endpoints under `/api/v1/admin/apps/*`

### Fixed
- **Terminology Confusion**: Eliminated ambiguity between tier properties (e.g., `is_active`, `byok_enabled`) and user-facing services/applications (e.g., Brigade, Bolt, Chat)
- **Consistent Naming**: Database, backend, and frontend now use consistent "app" terminology

### Migration Guide

**For API Clients**:
```bash
# Old endpoint (deprecated but still works via backward-compatible views)
GET /api/v1/admin/features

# New endpoint (recommended)
GET /api/v1/admin/apps
```

**For Users**:
- Bookmark update: `/admin/system/feature-management` → `/admin/system/app-management`

**Database Migration** (automatic):
```sql
-- Backward-compatible views created automatically
-- Old code continues to work during transition period
SELECT * FROM feature_definitions;  -- Still works (view → app_definitions)
SELECT * FROM tier_features;        -- Still works (view → tier_apps)
```

### Data Preservation
- ✅ **100% Data Integrity**: All 17 apps and 21 tier-app associations preserved
- ✅ **Zero Downtime**: Backward-compatible views ensure old code continues working
- ✅ **Rollback Ready**: Complete rollback procedure documented if needed

---

## [2.2.0] - 2025-11-04

### Added
- **Image Generation API**: OpenAI-compatible `/api/v1/llm/image/generations` endpoint
  - Support for DALL-E 2/3, Stable Diffusion XL/3 via OpenRouter
  - BYOK support (no credits charged when using own API keys)
  - Tier-based pricing with automatic cost calculation
  - Quality options (standard/HD) and batch generation (up to 10 images)
  - OpenAI SDK compatible

- **Model Categorization**: New `/api/v1/llm/models/categorized` endpoint
  - Separates BYOK models (free) from Platform models (charged)
  - Smart provider detection based on user's API keys
  - Detailed provider-level summaries
  - Integration guide for Bolt/Presenton/Open-WebUI

### Documentation
- `docs/api/IMAGE_GENERATION_API_GUIDE.md` - Complete image generation guide (20+ pages)
- `docs/api/IMAGE_GENERATION_QUICK_START.md` - Quick start guide
- `docs/INTEGRATION_GUIDE.md` - Bolt/Presenton/Open-WebUI integration (800+ lines)

---

## [2.1.0] - 2025-10-29

### Fixed
- **Credit System Authentication**: Fixed user session integration
  - Replaced test user fallback with real Keycloak session authentication
  - Added automatic field mapping: Keycloak `sub` → application `user_id`
  - Fixed circular import in `credit_api.py`

- **Credit Display Formatting**: Removed misleading dollar signs
  - Changed display from "$10,000" to "10,000 credits"
  - Created `formatCredits()` function with comma separators
  - Updated 4 display locations in Credit Dashboard

### Added
- **Organization Setup**: Created "Magic Unicorn" organization with professional tier
- **Credit Allocation**: Allocated 10,000 credits to admin user
- **OpenRouter Integration**: Verified API key configuration in LiteLLM proxy

### Documentation
- `CREDIT_BALANCE_EXPLAINED.md` - Guide to understanding credit vs OpenRouter balances
- `CREDIT_API_USER_ID_FIX.md` - Authentication fix documentation
- `CREDIT_DISPLAY_FIX.md` - Display formatting documentation
- `FINAL_CREDIT_FIX_SUMMARY.md` - Complete technical summary

---

## [2.0.0] - 2025-10-15

### Added - Phase 1: User Management & Billing Dashboard

#### User Management System (Complete)
- **Bulk Operations**: CSV import/export, bulk role assignment, bulk suspend/delete, bulk tier changes
- **Advanced Filtering**: 10+ filter options (tier, role, status, org, date ranges, BYOK, email verified)
- **User Detail Page**: Comprehensive 6-tab profile view with charts and activity timeline
- **Enhanced Role Management**: Dual-panel UI with visual permission matrix
- **API Key Management**: Full CRUD for user API keys with bcrypt hashing
- **User Impersonation**: Admin "login as user" feature with 24hr sessions
- **Activity Timeline**: Color-coded audit log with expandable details

#### Billing Dashboard (Complete)
- **Subscription Plans**: Trial ($1/week), Starter ($19/mo), Professional ($49/mo), Enterprise ($99/mo)
- **Lago Integration**: Full billing system with GraphQL API
- **Stripe Integration**: Payment processing with 7 webhook events
- **Invoice Management**: History, payment tracking, usage metering
- **Webhook Handling**: Automated subscription lifecycle management

#### New Components
- `UserDetail.jsx` - 6-tab user profile page (1,078 lines)
- `RoleManagementModal.jsx` - Enhanced role UI (534 lines)
- `PermissionMatrix.jsx` - Visual permission grid (177 lines)
- `BulkActionsToolbar.jsx` - Bulk operations UI
- `ImportCSVModal.jsx` - CSV import wizard
- `APIKeysManager.jsx` - API key management (493 lines)
- `ActivityTimeline.jsx` - Activity audit log (418 lines)

#### New API Endpoints
- User Management: 15+ new endpoints for bulk operations, impersonation, API keys
- Role Management: 4 new endpoints for hierarchy, permissions, effective permissions
- Session Management: 3 endpoints for session tracking and revocation

### Changed
- **User Management**: Enhanced with advanced filtering (10+ parameters)
- **Keycloak Integration**: Automatic user attribute population for 9 users
- **Frontend Build**: Added dependencies: `react-chartjs-2`, `chart.js`

### Documentation
- `USER_MANAGEMENT_GAP_ANALYSIS.md` - Feature gap analysis
- `DEPLOYMENT_VERIFICATION_GUIDE.md` - 82-page testing guide
- `docs/API_REFERENCE.md` - OpenAPI-style API documentation
- `docs/ADMIN_OPERATIONS_HANDBOOK.md` - Practical admin guide
- `CODE_REVIEW_REPORT.md` - Quality assessment (B+ grade)
- `NEXT_PHASE_ROADMAP.md` - Strategic roadmap (Phases 2-4)

---

## [1.0.0] - 2025-09-01

### Initial Release
- Basic user management
- Service management dashboard
- Keycloak SSO integration
- LLM management via LiteLLM
- Docker deployment configuration
