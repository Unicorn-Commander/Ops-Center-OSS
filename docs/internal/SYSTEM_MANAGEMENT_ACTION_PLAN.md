# System Management Pages - Action Plan

**Generated**: October 9, 2025
**Priority**: Address before production deployment

---

## Quick Summary

18 issues found across 4 system management pages:
- **3 Critical** - Must fix immediately
- **6 High** - Fix before production
- **6 Medium** - Important but not blocking
- **3 Low** - Nice to have

---

## CRITICAL Issues (Fix Immediately)

### 1. WebSocket Log Streaming Not Implemented
**File**: Backend `server.py` + Frontend `Logs.jsx`
**Impact**: Live log streaming completely broken

**Action Required**:
```python
# Add to backend/server.py

@app.websocket("/ws/logs/{source_id}")
async def websocket_logs(
    websocket: WebSocket,
    source_id: str,
    current_user: dict = Depends(get_current_user_ws)
):
    await websocket.accept()

    try:
        # Parse query params for filters
        levels = websocket.query_params.get("levels")
        search = websocket.query_params.get("search")

        filters = LogFilter(
            levels=[levels] if levels else None,
            search=search
        )

        # Stream logs
        async for log_line in log_manager.stream_logs(source_id, filters):
            await websocket.send_text(log_line)

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from log stream: {source_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()
```

**Also Fix**: Line 154 in `Logs.jsx` - Make WebSocket URL dynamic:
```javascript
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const host = window.location.host;
const wsUrl = new URL(`${protocol}//${host}/ws/logs/${encodeURIComponent(selectedSource)}`);
```

---

### 2. Network Reconfiguration Doesn't Apply Changes
**File**: Backend `server.py` - Network endpoint
**Impact**: Network settings saved but not applied to system

**Current State**: Backend saves JSON but doesn't modify system files

**Action Required**:
```python
# In backend/server.py - Update PUT /api/v1/system/network

async def apply_network_config(config: dict):
    """Apply network configuration to system"""

    if config['method'] == 'dhcp':
        netplan_config = {
            'network': {
                'version': 2,
                'ethernets': {
                    config['interface']: {
                        'dhcp4': True
                    }
                }
            }
        }
    else:
        netplan_config = {
            'network': {
                'version': 2,
                'ethernets': {
                    config['interface']: {
                        'addresses': [f"{config['address']}/{config['netmask']}"],
                        'gateway4': config['gateway'],
                        'nameservers': {
                            'addresses': config.get('dns_servers', [])
                        }
                    }
                }
            }
        }

    # Write to netplan config
    config_file = f"/etc/netplan/50-{config['interface']}.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(netplan_config, f)

    # Apply configuration
    subprocess.run(['netplan', 'apply'], check=True)
```

**Warning**: Test thoroughly on non-production system first!

---

### 3. Storage Manager Path Mismatch
**File**: Backend `storage_manager.py`
**Impact**: Won't find volumes or backups on production system

**Current**:
```python
BACKUP_LOCATION = "/home/ucadmin/UC-1-Pro/backups"
VOLUMES_PATH = "/home/ucadmin/UC-1-Pro/volumes"
```

**Fix**:
```python
import os

# Get base path from environment or default
BASE_PATH = os.getenv('UC1_BASE_PATH', '/home/muut/Production/UC-1-Pro')

STORAGE_CONFIG_PATH = os.path.join(BASE_PATH, "volumes/storage_config.json")
BACKUP_CONFIG_PATH = os.path.join(BASE_PATH, "volumes/backup_config.json")
BACKUP_LOCATION = os.path.join(BASE_PATH, "backups")
VOLUMES_PATH = os.path.join(BASE_PATH, "volumes")
```

**Environment Variable**: Add to docker-compose or .env:
```bash
UC1_BASE_PATH=/home/muut/Production/UC-1-Pro
```

---

## HIGH Priority Issues (Fix Before Production)

### 4. Network Test Endpoint Missing
**File**: Backend `server.py`
**Impact**: Connectivity test button fails

**Add Endpoint**:
```python
@app.post("/api/v1/system/network/test")
async def test_network_connectivity(current_user: dict = Depends(get_current_user)):
    """Test network connectivity"""
    results = {
        'gateway_ping': False,
        'dns_resolution': False,
        'internet_connectivity': False,
        'details': {}
    }

    try:
        # Test gateway ping
        gateway = subprocess.run(
            ['ip', 'route', 'show', 'default'],
            capture_output=True, text=True
        )
        gateway_ip = gateway.stdout.split()[2] if gateway.returncode == 0 else None

        if gateway_ip:
            ping_result = subprocess.run(
                ['ping', '-c', '2', '-W', '2', gateway_ip],
                capture_output=True
            )
            results['gateway_ping'] = ping_result.returncode == 0
            results['details']['gateway'] = gateway_ip

        # Test DNS resolution
        dns_result = subprocess.run(
            ['nslookup', 'google.com'],
            capture_output=True
        )
        results['dns_resolution'] = dns_result.returncode == 0

        # Test internet connectivity
        internet_result = subprocess.run(
            ['curl', '-s', '--max-time', '5', 'https://www.google.com'],
            capture_output=True
        )
        results['internet_connectivity'] = internet_result.returncode == 0

        results['success'] = all([
            results['gateway_ping'],
            results['dns_resolution'],
            results['internet_connectivity']
        ])

        return results

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
```

---

### 5. Log Export Returns Wrong Format
**File**: Backend `log_manager.py` line 309-353
**Impact**: Export doesn't provide downloadable file

**Fix**: Modify to return file content or use FileResponse:
```python
# In backend/server.py

from fastapi.responses import FileResponse

@app.post("/api/v1/logs/export")
async def export_logs(
    request: LogExportRequest,
    current_user: dict = Depends(get_current_user)
):
    """Export logs to downloadable file"""
    try:
        result = await log_manager.export_logs(request)

        if result['success']:
            # Return file as download
            return FileResponse(
                path=result['path'],
                filename=result['filename'],
                media_type='application/octet-stream'
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error'))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

### 6. Backup Scheduling Not Applied
**File**: Backend `storage_manager.py`
**Impact**: Backup schedule saved but never runs

**Two Options**:

**Option A - Systemd Timer** (Recommended):
```bash
# Create /etc/systemd/system/uc1-backup.service
[Unit]
Description=UC-1 Pro Backup Service
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /path/to/run_backup.py
User=muut

# Create /etc/systemd/system/uc1-backup.timer
[Unit]
Description=UC-1 Pro Backup Timer

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

**Option B - Cron Integration**:
```python
# Add to storage_manager.py

def apply_backup_schedule(self):
    """Apply backup schedule to cron"""
    cron_command = f"{self.backup_config.schedule} /usr/bin/python3 /path/to/run_backup.py"

    # Update crontab
    subprocess.run([
        'crontab', '-l',
        '|', 'grep', '-v', 'run_backup.py',
        '|', 'crontab', '-'
    ])
    subprocess.run([
        'echo', f'"{cron_command}"',
        '|', 'crontab', '-'
    ])
```

---

### 7. Standardize Error Handling
**Files**: All 4 pages
**Impact**: Inconsistent user experience

**Add Global Error Handler**:
```javascript
// src/contexts/ErrorContext.jsx
import React, { createContext, useContext, useState } from 'react';

const ErrorContext = createContext();

export function ErrorProvider({ children }) {
  const [errors, setErrors] = useState([]);

  const addError = (message, type = 'error') => {
    const id = Date.now();
    setErrors(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setErrors(prev => prev.filter(e => e.id !== id));
    }, 5000);
  };

  return (
    <ErrorContext.Provider value={{ errors, addError }}>
      {children}
    </ErrorContext.Provider>
  );
}

export const useError = () => useContext(ErrorContext);
```

**Use in Pages**:
```javascript
const { addError } = useError();

try {
  // API call
} catch (error) {
  addError(`Failed to load data: ${error.message}`);
}
```

---

## MEDIUM Priority Issues

### 8. Populate Network Statistics (System.jsx)
- Add real-time network bandwidth to system status endpoint
- Calculate bytes in/out per second
- Update historical charts

### 9. Implement Log History Tab (Logs.jsx)
- Add date/time range picker
- Implement historical search API
- Add pagination for large results

### 10. Wire Volume Actions (StorageBackup.jsx)
- Connect backup button to `storage_manager.create_backup()`
- Implement volume deletion with safety checks
- Add confirmation dialogs

### 11-13. See full report for details

---

## LOW Priority Issues

### 14-16. Polish and UX improvements
- Add CPU temperature monitoring
- Add backup progress indicators
- Optimize for mobile devices

---

## Quick Wins (Easy Fixes)

1. **Fix hardcoded paths** (5 minutes)
   - Update storage_manager.py with environment variables

2. **Remove broken features** (10 minutes)
   - Remove "Network" tab from System.jsx (line 378)
   - Or add "Coming Soon" badge

3. **Fix WebSocket URL** (5 minutes)
   - Make dynamic based on window.location (Logs.jsx line 154)

4. **Add loading states** (15 minutes)
   - Add spinners to all async operations

---

## Testing Checklist

Before deploying fixes:

### Critical Tests
- [ ] WebSocket streaming connects and displays logs
- [ ] Network configuration changes are applied to system
- [ ] Storage manager finds volumes at correct path
- [ ] Backups are created successfully

### High Priority Tests
- [ ] Network test shows correct connectivity status
- [ ] Log export downloads valid files
- [ ] Backup schedule is applied (check cron/systemd)
- [ ] Error notifications appear on failures

### Integration Tests
- [ ] Full backup → restore cycle works
- [ ] Network change → system restart → still accessible
- [ ] Log streaming → filter → export chain works
- [ ] All pages load without console errors

---

## Deployment Steps

1. **Backup Current System**
   ```bash
   # Full backup before changes
   cd /home/muut/Production/UC-1-Pro
   tar -czf ../uc1-backup-$(date +%Y%m%d).tar.gz .
   ```

2. **Apply Critical Fixes**
   - Update storage_manager.py paths
   - Add WebSocket endpoint
   - Test on staging environment

3. **Update Environment**
   ```bash
   # Add to .env or docker-compose.yml
   echo "UC1_BASE_PATH=/home/muut/Production/UC-1-Pro" >> .env
   ```

4. **Restart Services**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

5. **Verify Functionality**
   - Test each page manually
   - Check browser console for errors
   - Monitor backend logs

---

## Resources

- **Full Audit Report**: `SYSTEM_MANAGEMENT_AUDIT_REPORT.md`
- **Backend Modules**:
  - `/backend/storage_manager.py`
  - `/backend/log_manager.py`
  - `/backend/server.py`
- **Frontend Pages**:
  - `/src/pages/System.jsx`
  - `/src/pages/Network.jsx`
  - `/src/pages/StorageBackup.jsx`
  - `/src/pages/Logs.jsx`

---

## Support

For questions or issues:
1. Review full audit report for detailed analysis
2. Check backend logs: `docker logs unicorn-ops-center`
3. Test in development environment first
4. Document any changes made

---

**Next Steps**: Start with Critical Issues #1-3, then proceed to High Priority issues #4-7.

**Estimated Time**:
- Critical fixes: 4-6 hours
- High priority: 6-8 hours
- Medium priority: 8-10 hours
- Total: ~20-24 hours of development work
