# Forgejo Git Server Integration

**Integration Date**: November 8, 2025
**Status**: ✅ Production Ready
**Version**: 1.0.0

---

## Overview

Ops-Center includes full integration with Forgejo, a self-hosted Git server. This integration provides centralized management of Git repositories, organizations, and development workflows directly from the Ops-Center dashboard.

**Forgejo Instance**: https://git.unicorncommander.ai

---

## Features

### 1. Service Monitoring
- **Live Health Status**: Real-time Forgejo server health check
- **Version Information**: Display Forgejo version and status
- **Auto-Refresh**: Service status updates every 30 seconds
- **Quick Access**: Direct link to Forgejo web interface

### 2. Repository Management
- **Repository Browser**: View all repositories across all organizations
- **Organization View**: Filter repositories by organization
- **Repository Details**: Name, description, visibility, last updated
- **Quick Actions**: Clone URL, web URL, settings access

### 3. Organization Management
- **Organization List**: View all Forgejo organizations
- **Member Count**: See organization size and activity
- **Repository Count**: Track repos per organization
- **Access Control**: Organization-level permissions

### 4. Statistics Dashboard
- **Total Organizations**: Platform-wide organization count
- **Total Repositories**: Aggregate repository statistics
- **Growth Metrics**: Track repository and organization growth
- **Instance Overview**: Complete Forgejo instance information

---

## Access Points

### For Users

**Service Card** (Main Services Page)
- Location: `/services` or main dashboard
- Features:
  - Live status indicator (Online/Offline)
  - Organization count
  - Repository count
  - Direct link to Forgejo web UI

**Quick Access**:
```
https://unicorncommander.ai/services → Click "Forgejo" card → Opens https://git.unicorncommander.ai
```

### For Administrators

**Admin Dashboard** (System Management)
- Location: `/admin/system/forgejo`
- Features:
  - Complete instance overview
  - Organization management
  - Repository browser with filters
  - Statistics and metrics
  - Health monitoring

**Navigation**:
```
Admin Menu → Infrastructure → Forgejo (Git)
```

---

## API Endpoints

Ops-Center provides a RESTful API for Forgejo integration:

### Health & Status

```http
GET /api/v1/forgejo/health
```
**Response**:
```json
{
  "service": "Forgejo",
  "url": "https://git.unicorncommander.ai",
  "online": true,
  "version": "8.0.0",
  "status": "healthy"
}
```

### Statistics

```http
GET /api/v1/forgejo/stats
```
**Response**:
```json
{
  "total_organizations": 5,
  "total_repositories": 17,
  "instance_url": "https://git.unicorncommander.ai"
}
```

### Organizations

```http
GET /api/v1/forgejo/orgs
```
**Response**:
```json
{
  "organizations": [
    {
      "id": 1,
      "username": "UnicornCommander",
      "full_name": "Unicorn Commander Organization",
      "description": "Main UC-Cloud organization",
      "website": "https://unicorncommander.ai",
      "location": "",
      "visibility": "public",
      "repo_admin_change_team_access": false
    }
  ],
  "count": 1
}
```

### Organization Repositories

```http
GET /api/v1/forgejo/orgs/{org_name}/repos
```
**Response**:
```json
{
  "organization": "UnicornCommander",
  "repositories": [
    {
      "id": 1,
      "name": "UC-Cloud",
      "full_name": "UnicornCommander/UC-Cloud",
      "description": "Enterprise AI Platform as a Service",
      "private": true,
      "fork": false,
      "size": 450000,
      "html_url": "https://git.unicorncommander.ai/UnicornCommander/UC-Cloud",
      "clone_url": "https://git.unicorncommander.ai/UnicornCommander/UC-Cloud.git",
      "updated_at": "2025-11-08T10:30:00Z"
    }
  ],
  "count": 1
}
```

### Instance Information

```http
GET /api/v1/forgejo/info
```
**Response**:
```json
{
  "instance_url": "https://git.unicorncommander.ai",
  "api_base": "https://git.unicorncommander.ai/api/v1",
  "admin_url": "https://git.unicorncommander.ai/admin",
  "status": "healthy",
  "online": true,
  "version": "8.0.0",
  "statistics": {
    "total_organizations": 5,
    "total_repositories": 17
  }
}
```

### User Repositories (Future - Phase 2)

```http
GET /api/v1/forgejo/user/repos
Authorization: Bearer {token}
```
**Note**: Currently returns empty list. User token integration coming in Phase 2.

---

## Repository URLs

All UC-Cloud repositories have been migrated from GitHub to Forgejo:

### Main Repositories

| Repository | Forgejo URL | Description |
|------------|-------------|-------------|
| **UC-Cloud** | https://git.unicorncommander.ai/UnicornCommander/UC-Cloud | Main platform repository |
| **Ops-Center** | https://git.unicorncommander.ai/UnicornCommander/Ops-Center | Operations dashboard (submodule) |
| **Center-Deep-Pro** | https://git.unicorncommander.ai/UnicornCommander/Center-Deep-Pro | AI metasearch engine (submodule) |
| **Unicorn-Brigade** | https://git.unicorncommander.ai/UnicornCommander/Unicorn-Brigade | Agent platform (submodule) |
| **Bolt-DIY-Fork** | https://git.unicorncommander.ai/UnicornCommander/Bolt-DIY-Fork | AI development environment |
| **Presenton-Fork** | https://git.unicorncommander.ai/UnicornCommander/Presenton-Fork | AI presentation generation |

### Cloning Repositories

**With Submodules** (Recommended):
```bash
git clone --recurse-submodules https://git.unicorncommander.ai/UnicornCommander/UC-Cloud.git
cd UC-Cloud
```

**Individual Repository**:
```bash
git clone https://git.unicorncommander.ai/UnicornCommander/Ops-Center.git
cd Ops-Center
```

---

## Configuration

### Environment Variables

Forgejo integration is configured in Ops-Center's backend:

**File**: `backend/services/forgejo_client.py`

```python
base_url = "https://git.unicorncommander.ai"
admin_token = "4d79a6bef5c793c89b13400115188ea935fc31b5"  # Admin API token
timeout = 10  # Request timeout in seconds
```

### Forgejo Server Configuration

**Instance**: Running in Docker container `unicorn-forgejo`
**Port**: 3003 (internal), exposed via Traefik on HTTPS
**Admin Access**: https://git.unicorncommander.ai/admin
**API Base**: https://git.unicorncommander.ai/api/v1

---

## Future Enhancements (Phase 2)

### User Token Management
- **Personal Repositories**: Users can connect their own Forgejo accounts
- **Token Storage**: Encrypted storage of user API tokens in database
- **Permission Scoping**: Fine-grained repository access control
- **Private Repos**: Support for user's private repositories

### Webhook Integration
- **Push Notifications**: Real-time updates when code is pushed
- **CI/CD Triggers**: Automatic deployment workflows
- **Issue Tracking**: Synchronize Forgejo issues with Ops-Center
- **Pull Request Management**: Review and merge PRs from dashboard

### Advanced Features
- **Repository Templates**: Quick-start templates for new projects
- **Code Review**: Built-in code review interface
- **Analytics**: Commit frequency, contributor statistics, code coverage
- **Backup Management**: Automated repository backups

---

## Technical Architecture

### Backend Components

**Forgejo Client** (`backend/services/forgejo_client.py`):
- Async HTTP client using `httpx`
- Admin token authentication
- Health checking and error handling
- Statistics aggregation across organizations

**API Router** (`backend/routers/forgejo.py`):
- FastAPI router with 6 RESTful endpoints
- Error handling with HTTP status codes
- Logging integration for debugging
- Admin-only access controls

**Server Integration** (`backend/server.py`):
- Router registration at `/api/v1/forgejo`
- Startup logging for endpoint availability
- CORS configuration for frontend access

### Frontend Components

**Service Card** (`src/components/ForgejoCard.jsx`):
- Real-time health monitoring (30-second refresh)
- Organization and repository counts
- Status indicators (Online/Offline)
- Direct link to Forgejo web interface
- 6.5 KB component with Material-UI design

**Admin Dashboard** (`src/pages/admin/ForgejoManagement.jsx`):
- Comprehensive instance overview
- Organization and repository browser
- Tabbed interface for different views
- Data grid with sorting and filtering
- 27 KB component (450+ lines)
- Auto-refresh functionality

**Routing** (`src/App.jsx`):
- Lazy loading for performance
- Route: `/admin/system/forgejo`
- Protected by admin authentication

**Navigation** (`src/components/Layout.jsx`):
- Infrastructure section menu item
- Icon: CodeBracketIcon
- Label: "Forgejo (Git)"

---

## Troubleshooting

### Service Card Shows "Offline"

**Symptoms**: Forgejo service card displays offline status even when Forgejo is running

**Diagnosis**:
```bash
# Check Forgejo container status
docker ps | grep forgejo

# Check Forgejo logs
docker logs unicorn-forgejo --tail 50

# Test API endpoint directly
curl https://git.unicorncommander.ai/api/v1/version
```

**Common Causes**:
1. Forgejo container not running
2. Network connectivity issues
3. Traefik misconfiguration
4. API timeout (>10 seconds)

**Solution**:
```bash
# Restart Forgejo
docker restart unicorn-forgejo

# Check Traefik routes
docker logs traefik | grep forgejo

# Verify DNS resolution
nslookup git.unicorncommander.ai
```

### Statistics Show 0 Repositories

**Symptoms**: Repository count shows 0 even though repositories exist

**Diagnosis**:
```bash
# Check Forgejo API directly
curl -H "Authorization: token 4d79a6bef5c793c89b13400115188ea935fc31b5" \
  https://git.unicorncommander.ai/api/v1/orgs

# Check Ops-Center logs
docker logs ops-center-direct | grep forgejo
```

**Common Causes**:
1. Admin token expired or invalid
2. Organizations not visible with current token
3. API endpoint returning empty results
4. Network timeout during stats aggregation

**Solution**:
```bash
# Verify admin token is valid
curl -H "Authorization: token 4d79a6bef5c793c89b13400115188ea935fc31b5" \
  https://git.unicorncommander.ai/api/v1/user

# Check organization visibility settings in Forgejo admin panel
# https://git.unicorncommander.ai/admin/orgs
```

### Admin Dashboard Not Loading

**Symptoms**: `/admin/system/forgejo` page shows blank or errors

**Diagnosis**:
```bash
# Check browser console for errors (F12)
# Look for failed API calls or JavaScript errors

# Check Ops-Center backend logs
docker logs ops-center-direct | grep "forgejo"

# Verify API endpoints are registered
curl http://localhost:8084/api/v1/forgejo/health
```

**Common Causes**:
1. Frontend build issues
2. API endpoints not accessible
3. CORS configuration problems
4. Authentication/authorization failures

**Solution**:
```bash
# Rebuild frontend
cd /opt/ops-center
npm run build
cp -r dist/* public/

# Restart Ops-Center
docker restart ops-center-direct

# Clear browser cache and reload
```

---

## Security Considerations

### API Token Security

**Admin Token Storage**:
- Hardcoded in `forgejo_client.py` (for now)
- **Future**: Move to environment variables or secrets management
- **Best Practice**: Rotate tokens regularly

**Token Permissions**:
- Current token has full admin access
- **Future**: Implement scoped tokens per functionality
- **Recommendation**: Create separate tokens for read-only operations

### Access Control

**Current Implementation**:
- All endpoints require Ops-Center authentication
- No direct user token support (coming in Phase 2)
- Admin-only access to management features

**Future Enhancements**:
- User-specific API tokens
- Role-based access control (RBAC)
- Organization-level permissions
- Audit logging for all Git operations

---

## Related Documentation

- **Complete Integration Guide**: `/tmp/FORGEJO_INTEGRATION_COMPLETE.md`
- **UC-Cloud Main README**: `/opt/uc-cloud/README.md`
- **Ops-Center README**: `/opt/ops-center/README.md`
- **Forgejo Official Docs**: https://forgejo.org/docs/latest/

---

## Support

**Forgejo Instance Issues**:
- Admin Panel: https://git.unicorncommander.ai/admin
- Forgejo Docs: https://forgejo.org/docs/latest/

**Ops-Center Integration Issues**:
- Ops-Center Issues: https://git.unicorncommander.ai/UnicornCommander/Ops-Center/issues
- UC-Cloud Issues: https://git.unicorncommander.ai/UnicornCommander/UC-Cloud/issues

**Contact**:
- Email: support@magicunicorn.tech
- Website: https://unicorncommander.ai

---

**Magic Unicorn Unconventional Technology & Stuff Inc**
*Making Git management magical* 🦄✨
