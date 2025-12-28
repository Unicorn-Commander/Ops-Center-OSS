# Model List Management Feature - Master Checklist

**Created**: November 19, 2025
**Status**: 🔄 In Progress
**Priority**: High

---

## Overview

Implement centralized model list management in Ops-Center that allows admins to create and manage app-specific curated model lists (Bolt, Presenton, Open-WebUI, etc.) through a GUI without code deployments.

---

## Phase 1: Database Schema ⬜

### Tables to Create
- [ ] `app_model_lists` - App-specific curated list definitions
- [ ] `app_model_list_items` - Models in each curated list
- [ ] `user_model_preferences` - User favorites and hidden models
- [ ] `model_access_audit` - Audit trail for changes

### Migration
- [ ] Create SQL migration script
- [ ] Apply migration to unicorn_db
- [ ] Verify tables created successfully
- [ ] Add indexes for performance

---

## Phase 2: Backend API ⬜

### Admin Endpoints
- [ ] `GET /api/v1/admin/model-lists` - List all app model lists
- [ ] `POST /api/v1/admin/model-lists` - Create new model list
- [ ] `GET /api/v1/admin/model-lists/{id}` - Get model list details
- [ ] `PUT /api/v1/admin/model-lists/{id}` - Update model list
- [ ] `DELETE /api/v1/admin/model-lists/{id}` - Delete model list

### Model Management Endpoints
- [ ] `GET /api/v1/admin/model-lists/{id}/models` - Get models in list
- [ ] `POST /api/v1/admin/model-lists/{id}/models` - Add model to list
- [ ] `PUT /api/v1/admin/model-lists/{id}/models/{model_id}` - Update model in list
- [ ] `DELETE /api/v1/admin/model-lists/{id}/models/{model_id}` - Remove model
- [ ] `PUT /api/v1/admin/model-lists/{id}/reorder` - Reorder models

### Public Endpoints (Updated)
- [ ] `GET /api/v1/llm/models/curated?app={app_slug}` - Get app-specific curated list
- [ ] `GET /api/v1/llm/models/curated` - Get global curated list (fallback)

### User Preference Endpoints
- [ ] `GET /api/v1/user/model-preferences` - Get user preferences
- [ ] `PUT /api/v1/user/model-preferences/{model_id}` - Update preference

### Backend Files
- [ ] Create `backend/model_list_api.py` - Main API router
- [ ] Create `backend/model_list_manager.py` - Business logic
- [ ] Update `backend/server.py` - Register new router
- [ ] Update `backend/litellm_api.py` - Modify curated endpoint

---

## Phase 3: Frontend Admin GUI ⬜

### Pages
- [ ] Create `src/pages/admin/ModelListManagement.jsx` - Main management page

### Components
- [ ] App tab selector (Bolt, Presenton, Open-WebUI, Global)
- [ ] Model list table with drag-and-drop reordering
- [ ] Add model dialog with search
- [ ] Edit model dialog (category, description, tier access)
- [ ] Category filter/assignment
- [ ] Tier access checkboxes
- [ ] "Preview as Tier" dropdown
- [ ] Import/Export buttons

### Features
- [ ] Real-time model search from OpenRouter catalog
- [ ] Drag-and-drop reordering with optimistic updates
- [ ] Bulk actions (delete, change category)
- [ ] Category color coding
- [ ] FREE model indicator
- [ ] Context length display
- [ ] Provider grouping

### Navigation
- [ ] Add to sidebar under System Settings
- [ ] Add route in `App.jsx`
- [ ] Add to admin menu

---

## Phase 4: Initial Data Seeding ⬜

### Curated Lists to Create
- [ ] **Global Default** - Best FREE models for all apps
- [ ] **Bolt.diy Coding** - Coding-focused models (Qwen3 Coder, DeepSeek R1, etc.)
- [ ] **Presenton Content** - Content generation models (DeepSeek Chat, Gemini, Claude Haiku)
- [ ] **Open-WebUI General** - General purpose models

### Seed Data
- [ ] Create seeding script `backend/scripts/seed_model_lists.py`
- [ ] Run seeding script
- [ ] Verify data in database

---

## Phase 5: Integration & Testing ⬜

### Bolt.diy Integration
- [ ] Update `unicorn-commander.ts` to pass `app=bolt-diy` parameter
- [ ] Test curated models appear correctly
- [ ] Verify category sorting works

### Presenton Integration
- [ ] Update Presenton to call `/models/curated?app=presenton`
- [ ] Test model selection in Presenton

### Admin Testing
- [ ] Create new model list
- [ ] Add/remove models from list
- [ ] Reorder models via drag-and-drop
- [ ] Change model categories
- [ ] Set tier access permissions
- [ ] Preview as different tiers
- [ ] Import/Export functionality

### User Testing
- [ ] Verify correct models appear per app
- [ ] Test tier filtering works
- [ ] Verify BYOK models always available
- [ ] Test favorites/hidden preferences

---

## Phase 6: Documentation ⬜

- [ ] Update Ops-Center CLAUDE.md with new endpoints
- [ ] Create admin user guide for model list management
- [ ] Document API endpoints with examples
- [ ] Add to CHANGELOG.md

---

## Success Criteria

1. ✅ Admin can create/edit/delete app-specific model lists via GUI
2. ✅ Admin can drag-and-drop reorder models
3. ✅ Admin can assign categories to models
4. ✅ Admin can set tier access per model
5. ✅ Changes reflect immediately without code deployment
6. ✅ Apps receive correct curated list when calling API
7. ✅ Users see filtered list based on their tier
8. ✅ BYOK models always available regardless of lists
9. ✅ Audit trail tracks all changes

---

## Technical Notes

### Filtering Hierarchy
```
Platform Models (OpenRouter 1,300+)
    ↓
Tier Filtering (Trial/Starter/Pro/Enterprise)
    ↓
App-Specific List (Bolt, Presenton, Open-WebUI)
    ↓
User Preferences (Favorites/Hidden)
    ↓
BYOK Injection (Always available)
```

### Database Connection
- Host: unicorn-postgresql
- Database: unicorn_db
- User: unicorn

### API Router Prefix
- Admin: `/api/v1/admin/model-lists`
- Public: `/api/v1/llm/models/curated`
- User: `/api/v1/user/model-preferences`

---

## Files to Create/Modify

### New Files
- `backend/model_list_api.py`
- `backend/model_list_manager.py`
- `backend/scripts/seed_model_lists.py`
- `backend/migrations/model_lists_schema.sql`
- `src/pages/admin/ModelListManagement.jsx`

### Modified Files
- `backend/server.py` - Register new router
- `backend/litellm_api.py` - Update curated endpoint
- `src/App.jsx` - Add route
- `src/components/Layout.jsx` - Add navigation item

---

## Estimated Effort

- Database Schema: 30 min
- Backend API: 2-3 hours
- Frontend GUI: 3-4 hours
- Testing: 1-2 hours
- Documentation: 30 min

**Total**: ~8-10 hours

---

## Dependencies

- PostgreSQL database access
- React + MUI frontend
- FastAPI backend
- Existing Ops-Center authentication

---

## Risk Mitigation

1. **Data Migration**: No existing data to migrate (new feature)
2. **Breaking Changes**: None (additive only)
3. **Performance**: Add indexes on frequently queried columns
4. **Rollback**: Can delete tables if needed (no dependencies)

---

**Next Action**: Start Phase 1 - Create database schema
