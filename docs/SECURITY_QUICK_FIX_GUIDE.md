# Security Quick Fix Guide - RBAC Implementation
## Immediate Actions for Ops-Center

**Status:** CRITICAL VULNERABILITIES IDENTIFIED
**Timeline:** Deploy within 24 hours
**Priority:** BLOCKER for production deployment

---

## Quick Summary

The Ops-Center has **54+ unprotected admin endpoints** that anyone can access without authentication. This guide provides copy-paste code to fix the most critical issues.

---

## Fix #1: Add Authentication to Service Management Endpoints

**File:** `/home/muut/Production/UC-1-Pro/services/ops-center/backend/server.py`

### Current Code (Line 1263):
```python
@app.get("/api/v1/services")
async def get_services():
    """Get all Docker services"""
    try:
        services = await docker_manager.get_services_with_health()
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Fixed Code:
```python
@app.get("/api/v1/services")
async def get_services(current_user: dict = Depends(get_current_user)):
    """Get all Docker services (authenticated users only)"""
    try:
        services = await docker_manager.get_services_with_health()
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Current Code (Line 1317):
```python
@app.post("/api/v1/services/{container_name}/action")
async def service_action(container_name: str, action: ServiceAction):
    """Start, stop, or restart a service"""
```

### Fixed Code:
```python
@app.post("/api/v1/services/{container_name}/action")
async def service_action(
    container_name: str,
    action: ServiceAction,
    current_user: dict = Depends(require_admin)  # ADMIN ONLY!
):
    """Start, stop, or restart a service (admin only)"""
```

---

## Fix #2: Add Authentication to AI Model Management

**File:** `/home/muut/Production/UC-1-Pro/services/ops-center/backend/server.py`

### Lines to Update:

```python
# Line 1453 - View models (all authenticated users)
@app.get("/api/v1/models")
async def get_models(current_user: dict = Depends(get_current_user)):

# Line 1426 - Download models (admin/power_user only)
@app.post("/api/v1/models/download")
async def download_model(
    model: ModelDownload,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_admin)  # Change to require_power_user later
):

# Line 1472 - Delete models (admin only)
@app.delete("/api/v1/models/{model_id:path}")
async def delete_model(
    model_id: str,
    current_user: dict = Depends(require_admin)
):

# Line 1491 - Activate model (admin/power_user only)
@app.post("/api/v1/models/active")
async def set_active_model(
    active: ActiveModel,
    current_user: dict = Depends(require_admin)  # Change to require_power_user later
):

# Line 1752 - Switch vLLM model (admin only)
@app.post("/api/v1/vllm/switch-model")
async def switch_vllm_model(
    model_id: str,
    current_user: dict = Depends(require_admin)
):
```

---

## Fix #3: Add Authentication to Network Configuration

**File:** `/home/muut/Production/UC-1-Pro/services/ops-center/backend/server.py`

### Lines to Update:

```python
# Line 1809 - View network status (authenticated users)
@app.get("/api/v1/network/status")
async def get_network_status(current_user: dict = Depends(get_current_user)):

# Line 1910 - Connect to WiFi (admin only)
@app.post("/api/v1/network/wifi/connect")
async def wifi_connect(
    config: dict,
    current_user: dict = Depends(require_admin)
):

# Line 1944 - Configure network (admin only)
@app.post("/api/v1/network/configure")
async def configure_network(
    config: NetworkConfig,
    current_user: dict = Depends(require_admin)
):
```

---

## Fix #4: Add Authentication to Backup & Storage

**File:** `/home/muut/Production/UC-1-Pro/services/ops-center/backend/server.py`

### Lines to Update:

```python
# Line 2171 - View storage (authenticated users)
@app.get("/api/v1/storage", response_model=StorageInfo)
async def get_storage_info(current_user: dict = Depends(get_current_user)):

# Line 2198 - Create backup (admin only)
@app.post("/api/v1/backup/create")
async def create_backup(
    config: BackupConfig,
    current_user: dict = Depends(require_admin)
):

# Line 2207 - Restore backup (admin only)
@app.post("/api/v1/backup/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    current_user: dict = Depends(require_admin)
):

# Line 2221 - Delete backup (admin only)
@app.delete("/api/v1/backup/{backup_id}")
async def delete_backup(
    backup_id: str,
    current_user: dict = Depends(require_admin)
):
```

---

## Fix #5: Add Authentication to Extensions

**File:** `/home/muut/Production/UC-1-Pro/services/ops-center/backend/server.py`

### Lines to Update:

```python
# Line 2044 - Get extensions (authenticated users)
@app.get("/api/v1/extensions")
async def get_extensions(current_user: dict = Depends(get_current_user)):

# Line 2261 - Install extension (admin only)
@app.post("/api/v1/extensions/install")
async def install_extension(
    request: ExtensionInstallRequest,
    current_user: dict = Depends(require_admin)
):

# Line 2273 - Delete extension (admin only)
@app.delete("/api/v1/extensions/{extension_id}")
async def delete_extension(
    extension_id: str,
    current_user: dict = Depends(require_admin)
):

# Line 2285 - Control extension (admin only)
@app.post("/api/v1/extensions/{extension_id}/control")
async def control_extension(
    extension_id: str,
    action: ExtensionActionRequest,
    current_user: dict = Depends(require_admin)
):
```

---

## Fix #6: Add Authentication to System Updates

**File:** `/home/muut/Production/UC-1-Pro/services/ops-center/backend/server.py`

### Lines to Update:

```python
# Line 2637 - Check update status (authenticated users)
@app.get("/api/v1/updates/status")
async def get_update_status(current_user: dict = Depends(get_current_user)):

# Line 2645 - Check for updates (authenticated users)
@app.post("/api/v1/updates/check")
async def check_updates(current_user: dict = Depends(get_current_user)):

# Line 2654 - Apply updates (admin only)
@app.post("/api/v1/updates/apply")
async def apply_update(
    version: str = None,
    current_user: dict = Depends(require_admin)
):
```

---

## Fix #7: Add Authentication to Logs

**File:** `/home/muut/Production/UC-1-Pro/services/ops-center/backend/server.py`

### Lines to Update:

```python
# Line 2322 - Get log sources (authenticated users)
@app.get("/api/v1/logs/sources")
async def get_log_sources(current_user: dict = Depends(get_current_user)):

# Line 2331 - Get log stats (authenticated users)
@app.get("/api/v1/logs/stats")
async def get_log_stats(current_user: dict = Depends(get_current_user)):

# Line 2340 - Search logs (authenticated users)
@app.post("/api/v1/logs/search")
async def search_logs(
    filter: LogFilter,
    current_user: dict = Depends(get_current_user)
):

# Line 2349 - Export logs (admin only)
@app.post("/api/v1/logs/export")
async def export_logs(
    export_request: LogExportRequest,
    current_user: dict = Depends(require_admin)
):
```

---

## Fix #8: Add Authentication to Landing Page Customization

**File:** `/home/muut/Production/UC-1-Pro/services/ops-center/backend/server.py`

### Lines to Update:

```python
# Line 1097 - Get landing config (public - no auth needed)
@app.get("/api/v1/landing/config")
async def get_landing_config():
    # This can stay public for landing page display

# Line 1105 - Update landing config (admin only)
@app.post("/api/v1/landing/config")
async def update_landing_config(
    config: dict,
    current_user: dict = Depends(require_admin)
):

# Line 1117 - Apply theme preset (admin only)
@app.post("/api/v1/landing/theme/{preset}")
async def apply_theme_preset(
    preset: str,
    current_user: dict = Depends(require_admin)
):

# Line 1174 - Toggle service visibility (admin only)
@app.post("/api/v1/landing/service/{service_id}")
async def toggle_service(
    service_id: str,
    visibility: dict,
    current_user: dict = Depends(require_admin)
):
```

---

## Fix #9: Add Role Hierarchy Support

**File:** `/home/muut/Production/UC-1-Pro/services/ops-center/backend/server.py`

### Add after line 2406:

```python
async def require_admin(current_user: dict = Depends(get_current_user)):
    """Require admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# ADD THIS NEW FUNCTION:
async def require_power_user(current_user: dict = Depends(get_current_user)):
    """Require power_user or admin role"""
    role = current_user.get("role", "viewer")
    if role not in ["admin", "power_user"]:
        raise HTTPException(
            status_code=403,
            detail="Power user or admin access required"
        )
    return current_user

# ADD THIS NEW FUNCTION:
async def require_user(current_user: dict = Depends(get_current_user)):
    """Require user, power_user, or admin role (excludes viewers)"""
    role = current_user.get("role", "viewer")
    if role not in ["admin", "power_user", "user"]:
        raise HTTPException(
            status_code=403,
            detail="User access required"
        )
    return current_user
```

---

## Fix #10: Update Frontend Navigation Filtering

**File:** `/home/muut/Production/UC-1-Pro/services/ops-center/src/components/Layout.jsx`

### Replace lines 25-38:

```javascript
const navigation = [
  { name: 'Dashboard', href: '/admin/', icon: HomeIcon, roles: ['admin', 'power_user', 'user', 'viewer'] },
  { name: 'Models & AI', href: '/admin/models', icon: CubeIcon, roles: ['admin', 'power_user'] },
  { name: 'Services', href: '/admin/services', icon: ServerIcon, roles: ['admin'] },
  { name: 'Resources', href: '/admin/system', icon: ChartBarIcon, roles: ['admin'] },
  { name: 'Network', href: '/admin/network', icon: WifiIcon, roles: ['admin'] },
  { name: 'Storage', href: '/admin/storage', icon: ArchiveBoxIcon, roles: ['admin', 'power_user'] },
  { name: 'Logs', href: '/admin/logs', icon: DocumentTextIcon, roles: ['admin', 'power_user', 'user'] },
  { name: 'Security', href: '/admin/security', icon: ShieldCheckIcon, roles: ['admin'] },
  { name: 'Authentication', href: '/admin/authentication', icon: KeyIcon, roles: ['admin'] },
  { name: 'Extensions', href: '/admin/extensions', icon: PuzzlePieceIcon, roles: ['admin', 'power_user'] },
  { name: 'Landing Page', href: '/admin/landing', icon: PaintBrushIcon, roles: ['admin'] },
  { name: 'Settings', href: '/admin/settings', icon: CogIcon, roles: ['admin', 'power_user', 'user'] },
];
```

### Add after line 52:

```javascript
const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
const userRole = userInfo.role || 'viewer';

// Filter navigation items based on user role
const filteredNavigation = navigation.filter(item =>
  item.roles && item.roles.includes(userRole)
);
```

### Update line 107:

```javascript
{/* OLD: navigation.map((item) => { */}
{filteredNavigation.map((item) => {
  const isActive = location.pathname === item.href;
  return (
    <Link
```

---

## Testing the Fixes

### 1. Test Authentication:
```bash
# Should return 401 Unauthorized
curl http://localhost:8084/api/v1/services

# Should return services list
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8084/api/v1/services
```

### 2. Test Role-Based Access:
```bash
# Login as regular user
TOKEN=$(curl -X POST http://localhost:8084/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password"}' \
  | jq -r '.access_token')

# Should return 403 Forbidden
curl -H "Authorization: Bearer $TOKEN" \
  -X POST http://localhost:8084/api/v1/services/unicorn-postgres/action \
  -H "Content-Type: application/json" \
  -d '{"action":"restart"}'
```

### 3. Test Admin Access:
```bash
# Login as admin
ADMIN_TOKEN=$(curl -X POST http://localhost:8084/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"ucadmin","password":"your-admin-password"}' \
  | jq -r '.access_token')

# Should succeed
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  -X POST http://localhost:8084/api/v1/services/unicorn-postgres/action \
  -H "Content-Type: application/json" \
  -d '{"action":"restart"}'
```

---

## Deployment Checklist

- [ ] Backup current server.py before making changes
- [ ] Apply all authentication fixes to endpoints
- [ ] Add role hierarchy functions (require_power_user, require_user)
- [ ] Update frontend navigation filtering
- [ ] Test authentication with curl commands
- [ ] Test role-based access control
- [ ] Verify admin can access all features
- [ ] Verify non-admin users are blocked from admin actions
- [ ] Monitor logs for authentication errors
- [ ] Update API documentation

---

## Complete Endpoint Protection Summary

After applying all fixes, your endpoints should be protected as follows:

| Endpoint Category | Auth Level | Accessible By |
|------------------|------------|---------------|
| System Status | Authenticated | All logged-in users |
| Service Management | Admin | Admin only |
| Model Viewing | Authenticated | All logged-in users |
| Model Download/Activation | Power User | Admin, Power User |
| Model Deletion | Admin | Admin only |
| Network Viewing | Authenticated | All logged-in users |
| Network Configuration | Admin | Admin only |
| Storage Viewing | Authenticated | All logged-in users |
| Backup Creation | Power User | Admin, Power User |
| Backup Restore/Delete | Admin | Admin only |
| Extension Viewing | Authenticated | All logged-in users |
| Extension Install/Remove | Admin | Admin only |
| Log Viewing | Authenticated | All logged-in users |
| Log Export | Admin | Admin only |
| User Management | Admin | Admin only |
| System Updates | Admin | Admin only |
| Landing Customization | Admin | Admin only |

---

## Emergency Rollback

If issues occur after deployment:

```bash
# Stop the service
cd /home/muut/Production/UC-1-Pro/services/ops-center
docker-compose down

# Restore backup
cp backend/server.py.backup backend/server.py
cp src/components/Layout.jsx.backup src/components/Layout.jsx

# Restart service
docker-compose up -d
```

---

## Next Steps

After implementing these immediate fixes:

1. Add CSRF protection (Week 1)
2. Implement rate limiting (Week 1)
3. Strengthen password policy (Week 2)
4. Add audit logging (Week 3)
5. Implement permission-based access control (Month 1)

See full Security Review document for detailed implementation guides.

---

**Last Updated:** October 9, 2025
**Review Required After Changes:** Yes
**Estimated Implementation Time:** 2-4 hours
