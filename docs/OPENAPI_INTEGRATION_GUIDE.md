# OpenAPI Integration Guide

## Overview

The Ops-Center API now has comprehensive OpenAPI 3.0 documentation available through multiple interfaces.

## Generated Documentation Files

### 1. OpenAPI Specification (YAML)
**Location**: `/docs/openapi.yaml`
- **Lines**: 10,516
- **Endpoints**: 310
- **Format**: OpenAPI 3.0

### 2. OpenAPI Specification (JSON)
**Location**: `/docs/openapi.json`
- **Format**: OpenAPI 3.0 JSON
- **Use**: Machine-readable specification

### 3. API Schemas Documentation
**Location**: `/docs/API_SCHEMAS.md`
- **Comprehensive schemas** with request/response examples
- **Authentication guide**
- **Error response documentation**
- **Best practices**

### 4. Endpoint Summary
**Location**: `/docs/API_ENDPOINTS_SUMMARY.md`
- Quick reference of all 310 endpoints
- Grouped by category
- Statistics by HTTP method

### 5. Raw Endpoint Data
**Location**: `/docs/endpoints_data.json`
- JSON export of all extracted endpoints
- Useful for tooling and automation

## FastAPI Built-in Documentation

FastAPI automatically provides interactive API documentation:

### Swagger UI
**URL**: http://localhost:8084/docs
- Interactive API explorer
- Try endpoints directly in browser
- View request/response schemas
- See authentication requirements

### ReDoc
**URL**: http://localhost:8084/redoc
- Clean, responsive documentation
- Three-panel layout
- Search functionality
- Print-friendly

### OpenAPI JSON
**URL**: http://localhost:8084/openapi.json
- Auto-generated from FastAPI routes
- Includes all Pydantic models
- Real-time updates when code changes

## Enhancing Auto-Generated Docs

To enhance the FastAPI auto-generated documentation, add this to `server.py`:

```python
# Add at the top of server.py
from openapi_config import get_custom_openapi_schema, openapi_metadata

# After creating the FastAPI app
app = FastAPI(
    title=openapi_metadata["title"],
    version=openapi_metadata["version"],
    description=openapi_metadata["description"],
    contact=openapi_metadata["contact"],
    license_info=openapi_metadata["license_info"],
    openapi_tags=openapi_metadata["openapi_tags"],
    servers=openapi_metadata["servers"]
)

# Override OpenAPI schema generation
app.openapi = lambda: get_custom_openapi_schema(app)
```

## Using the Documentation

### For API Consumers

1. **Start Here**: Read `/docs/API_SCHEMAS.md` for overview and common patterns
2. **Browse Endpoints**: Check `/docs/API_ENDPOINTS_SUMMARY.md` for quick reference
3. **Interactive Testing**: Use http://localhost:8084/docs for live testing
4. **Integration**: Download `/docs/openapi.yaml` for code generation tools

### For API Developers

1. **Endpoint Scanner**: Run `python3 backend/scripts/simple_endpoint_extractor.py` to regenerate docs
2. **Update Schemas**: Edit `/backend/openapi_config.py` for metadata changes
3. **Test Changes**: Visit http://localhost:8084/docs to see live updates
4. **Document New Endpoints**: Add docstrings to FastAPI route functions

## Code Generation Tools

Use the OpenAPI specification with code generation tools:

### OpenAPI Generator
```bash
# Install
npm install -g @openapitools/openapi-generator-cli

# Generate Python client
openapi-generator-cli generate \
  -i docs/openapi.yaml \
  -g python \
  -o clients/python

# Generate TypeScript client
openapi-generator-cli generate \
  -i docs/openapi.yaml \
  -g typescript-fetch \
  -o clients/typescript
```

### Swagger Codegen
```bash
# Generate Java client
swagger-codegen generate \
  -i docs/openapi.yaml \
  -l java \
  -o clients/java
```

## Testing with Postman

1. **Import**: Import `/docs/openapi.yaml` into Postman
2. **Environment**: Set base URL to `http://localhost:8084`
3. **Authentication**: Add Bearer token in Collection settings
4. **Test**: Execute requests directly from Postman

## API Statistics

### Endpoints by Category

| Category | Count | Description |
|----------|-------|-------------|
| Storage & Backup | 25 | Restic backup management |
| Traefik | 22 | Reverse proxy configuration |
| Local Users | 21 | Linux system user management |
| Credits | 21 | Credit system for API usage |
| Migration | 20 | Data import/export operations |
| LLM Configuration | 17 | Model configuration |
| Subscriptions | 17 | Subscription management |
| Cloudflare | 16 | DNS and security |
| LLM Management | 13 | LiteLLM routing |
| Network | 12 | Firewall rules |
| Email Notifications | 10 | Email preferences |
| LLM | 10 | AI inference endpoints |
| Organizations | 9 | Organization management |
| System Metrics | 9 | Resource monitoring |
| Billing | 8 | Invoice and payments |
| Admin | 7 | Admin operations |
| System Settings | 7 | System configuration |
| Keycloak Status | 6 | SSO status |
| Tier Check | 6 | Subscription tier enforcement |
| Traefik Metrics | 6 | Proxy performance |
| Usage | 6 | Usage tracking |
| Credentials | 6 | API credential management |
| BYOK | 5 | Bring Your Own Key |
| Billing (Lago) | 5 | Lago integration |
| LLM Providers | 5 | Provider management |
| Platform Settings | 5 | Platform config |
| Execution Servers | 4 | Server management |
| Traefik Middlewares | 4 | Middleware config |
| Traefik Routes | 4 | Route definitions |
| Traefik Services | 4 | Service backends |

**Total**: 310 endpoints

### Endpoints by HTTP Method

| Method | Count | Percentage |
|--------|-------|------------|
| GET | 158 | 51.0% |
| POST | 100 | 32.3% |
| DELETE | 28 | 9.0% |
| PUT | 23 | 7.4% |
| PATCH | 1 | 0.3% |

## Maintenance

### Regenerating Documentation

When endpoints are added or modified:

```bash
# Navigate to backend directory
cd /home/muut/Production/UC-Cloud/services/ops-center/backend

# Run endpoint extractor
python3 scripts/simple_endpoint_extractor.py

# Review generated files
ls -lh ../docs/openapi.yaml
ls -lh ../docs/API_ENDPOINTS_SUMMARY.md

# Commit changes
git add ../docs/
git commit -m "docs: Update API documentation"
```

### Keeping Docs in Sync

1. **Add Route**: Add new FastAPI endpoint in `*_api.py`
2. **Add Docstring**: Document with clear docstring
3. **Regenerate**: Run endpoint extractor script
4. **Review**: Check generated OpenAPI YAML
5. **Test**: Verify in Swagger UI at `/docs`
6. **Commit**: Commit both code and docs

## Security Considerations

### Authentication

All endpoints require JWT Bearer token:

```bash
curl -H "Authorization: Bearer <token>" \
  https://your-domain.com/api/v1/users
```

### Rate Limiting

Check headers in responses:

```
X-RateLimit-Limit: 10000
X-RateLimit-Remaining: 7543
X-RateLimit-Reset: 1730419200
```

### API Keys

For programmatic access, generate API keys:

```bash
POST /api/v1/admin/users/{user_id}/api-keys
{
  "name": "Production Key",
  "expires_in_days": 90,
  "scopes": ["llm:read", "llm:write"]
}
```

## Versioning

Current version: **v2.1.0**

All endpoints prefixed with `/api/v1/` to support future versioning.

### Version History

- **v2.1.0** (October 2025): Analytics, BYOK, bulk operations
- **v2.0.0** (September 2025): Lago billing, organizations
- **v1.0.0** (August 2025): Initial release

## Support

### Documentation
- **Main Docs**: `/docs/API_SCHEMAS.md`
- **Swagger UI**: http://localhost:8084/docs
- **ReDoc**: http://localhost:8084/redoc

### Contact
- **Email**: support@magicunicorn.tech
- **Website**: https://your-domain.com
- **GitHub**: https://github.com/Unicorn-Commander/UC-Cloud

---

**Generated**: October 25, 2025
**Ops-Center Version**: 2.1.0
**Total Endpoints**: 310
