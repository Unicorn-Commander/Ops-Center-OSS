# Model List Management - Quick Reference

## Overview

Manage app-specific curated model lists through the admin GUI without code deployments.

## Access

**Admin GUI**: https://unicorncommander.ai/admin/system/model-lists

## Curated Lists (Default)

| List | Slug | Models | Focus |
|------|------|--------|-------|
| Global Default | `global` | 6 | Fallback for all apps |
| Bolt.diy Coding | `bolt-diy` | 6 | Coding specialists |
| Presenton Content | `presenton` | 5 | Content generation |
| Open-WebUI General | `open-webui` | 5 | General purpose |

## Common Tasks

### View Models for an App
```bash
curl "http://localhost:8084/api/v1/llm/models/curated?app=bolt-diy"
```

### Add Model to List
```bash
curl -X POST "http://localhost:8084/api/v1/admin/model-lists/2/models" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "anthropic/claude-3-haiku:free",
    "display_name": "Claude 3 Haiku (FREE)",
    "category": "fast",
    "is_free": true
  }'
```

### Reorder Models
```bash
curl -X PUT "http://localhost:8084/api/v1/admin/model-lists/2/reorder" \
  -H "Content-Type: application/json" \
  -d '[
    {"model_id": "model1", "sort_order": 0},
    {"model_id": "model2", "sort_order": 1}
  ]'
```

### List All Model Lists
```bash
curl "http://localhost:8084/api/v1/admin/model-lists"
```

### Get List Details
```bash
curl "http://localhost:8084/api/v1/admin/model-lists/2"
```

### Create New List
```bash
curl -X POST "http://localhost:8084/api/v1/admin/model-lists" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Custom App Models",
    "app_slug": "custom-app",
    "description": "Models for custom application",
    "is_default": false
  }'
```

### Update Model in List
```bash
curl -X PUT "http://localhost:8084/api/v1/admin/model-lists/2/models/google%2Fgemini-2.0-flash-exp:free" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Updated Display Name",
    "category": "reasoning"
  }'
```

### Remove Model from List
```bash
curl -X DELETE "http://localhost:8084/api/v1/admin/model-lists/2/models/google%2Fgemini-2.0-flash-exp:free"
```

## Database Tables

- `app_model_lists` - List definitions
- `app_model_list_items` - Models with tier access
- `user_model_preferences` - User favorites
- `model_access_audit` - Change audit trail

## Integration with Apps

Apps call the curated endpoint with their identifier:

**Bolt.diy**: `?app=bolt-diy`
**Presenton**: `?app=presenton`
**Open-WebUI**: `?app=open-webui`

Returns `source: "database"` when using managed lists.

## Category Color Coding

| Category | Color | Use Case |
|----------|-------|----------|
| coding | Blue | Code generation, debugging |
| reasoning | Purple | Complex analysis, problem-solving |
| general | Gray | General purpose, conversation |
| fast | Yellow | Quick responses, real-time |

## Tier Access Control

Models can be restricted to specific subscription tiers:

- **trial** - Basic models only
- **starter** - Standard models
- **professional** - Advanced models
- **enterprise** - All models including premium

Set `tier_required` when adding a model to restrict access.

## API Response Format

### Curated Models Response
```json
{
  "models": [
    {
      "id": "google/gemini-2.0-flash-exp:free",
      "display_name": "Gemini 2.0 Flash (FREE)",
      "description": "Fast, free model for coding",
      "category": "fast",
      "is_free": true,
      "provider": "google",
      "context_length": 1048576,
      "sort_order": 0
    }
  ],
  "source": "database",
  "list_name": "Bolt.diy Coding Models",
  "total": 6
}
```

### List Details Response
```json
{
  "id": 2,
  "name": "Bolt.diy Coding Models",
  "app_slug": "bolt-diy",
  "description": "Models optimized for coding in Bolt.diy",
  "is_default": false,
  "created_at": "2025-11-19T00:00:00Z",
  "updated_at": "2025-11-19T00:00:00Z",
  "model_count": 6
}
```

## Troubleshooting

### Models Not Loading in App
1. Check app slug matches exactly: `bolt-diy`, `presenton`, `open-webui`
2. Verify list exists in database
3. Check API response for `source: "database"` vs `source: "hardcoded"`

### Fallback to Hardcoded Models
If database query fails, system falls back to hardcoded defaults. Check:
- Database connectivity
- Model list exists for the app
- List is not empty

### Tier Restrictions Not Working
1. Verify `tier_required` field is set on model
2. Check user's `subscription_tier` in session
3. Ensure tier comparison logic matches database values

## Admin GUI Features

### Tab Navigation
- **Global** - Default models for all apps
- **Bolt.diy** - Coding-focused models
- **Presenton** - Content generation models
- **Open-WebUI** - General conversation models

### Actions
- **Add Model** - Search OpenRouter catalog and add
- **Edit Model** - Change display name, category, tier
- **Delete Model** - Remove from list
- **Reorder** - Drag and drop to change order
- **Import** - Load models from JSON
- **Export** - Download list as JSON

## Files Reference

| File | Description |
|------|-------------|
| `backend/model_list_api.py` | REST API endpoints |
| `backend/model_list_manager.py` | Business logic |
| `backend/migrations/model_lists_schema.sql` | Database schema |
| `backend/scripts/seed_model_lists.py` | Initial data seed |
| `src/pages/admin/ModelListManagement.jsx` | Admin GUI component |
| `docs/MODEL_LIST_MANAGEMENT_CHECKLIST.md` | Implementation checklist |

## Related Documentation

- **Integration Guide**: `docs/INTEGRATION_GUIDE.md`
- **LLM API Guide**: `docs/api/IMAGE_GENERATION_API_GUIDE.md`
- **Main CLAUDE.md**: Contains full API documentation
