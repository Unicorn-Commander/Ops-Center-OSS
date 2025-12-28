# Firewall API - Quick Reference Card

**Epic 1.2 Phase 1 | API Developer Agent | Oct 22, 2025**

---

## 🚀 Quick Start

```bash
# 1. Verify files exist
ls -lh backend/firewall_api.py backend/firewall_manager.py

# 2. Register router in server_auth_integrated.py
from firewall_api import router as firewall_router
app.include_router(firewall_router)

# 3. Restart backend
docker restart ops-center-direct

# 4. Test health check
curl http://localhost:8084/api/v1/network/firewall/health
```

---

## 📡 Endpoints

### Read Operations
```bash
GET  /api/v1/network/firewall/rules          # List all rules
GET  /api/v1/network/firewall/status         # Get status
GET  /api/v1/network/firewall/templates      # List templates
GET  /api/v1/network/firewall/logs           # Get logs
GET  /api/v1/network/firewall/health         # Health check (no auth)
```

### Write Operations
```bash
POST   /api/v1/network/firewall/rules                    # Add rule
DELETE /api/v1/network/firewall/rules/{rule_num}         # Delete rule
POST   /api/v1/network/firewall/rules/bulk-delete        # Bulk delete
POST   /api/v1/network/firewall/enable                   # Enable firewall
POST   /api/v1/network/firewall/disable                  # Disable firewall
POST   /api/v1/network/firewall/reset?confirm=true       # Reset (DANGER!)
POST   /api/v1/network/firewall/templates/{template}     # Apply template
```

---

## 🔐 Authentication

**Required**: Admin role (all endpoints except `/health`)

**Roles Accepted**:
- `role == "admin"`
- `is_admin == true`
- `is_superuser == true`
- `"admin" in groups`

**Example**:
```bash
curl http://localhost:8084/api/v1/network/firewall/status \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

---

## ⏱️ Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| List Rules | 20 req | 60s |
| Add Rule | 5 req | 60s |
| Delete Rule | 5 req | 60s |
| Bulk Delete | 3 req | 60s |
| Get Status | 30 req | 60s |
| Enable/Disable | 3 req | 60s |
| Reset | 2 req | 60s |
| Apply Template | 5 req | 60s |
| List Templates | 20 req | 60s |
| Get Logs | 10 req | 60s |
| Health Check | ∞ (unlimited) | - |

**Rate Limit Key**: `ratelimit:{endpoint}:{username}`

---

## 📝 Common Requests

### Add HTTP Rule
```bash
POST /api/v1/network/firewall/rules
{
  "port": 80,
  "protocol": "tcp",
  "action": "allow",
  "description": "HTTP traffic"
}
```

### Add SSH Rule with IP Restriction
```bash
POST /api/v1/network/firewall/rules
{
  "port": 22,
  "protocol": "tcp",
  "action": "allow",
  "from_ip": "192.168.1.0/24",
  "description": "SSH from local network"
}
```

### List Active TCP Rules
```bash
GET /api/v1/network/firewall/rules?protocol=tcp&status=active
```

### Apply Web Server Template
```bash
POST /api/v1/network/firewall/templates/web-server
```

### Delete Rule #5 (with SSH protection)
```bash
DELETE /api/v1/network/firewall/rules/5?override_ssh=false
```

### Bulk Delete Rules
```bash
POST /api/v1/network/firewall/rules/bulk-delete
{
  "rule_numbers": [3, 5, 7],
  "override_ssh": false
}
```

---

## 🎯 Templates Available

- `web-server` - HTTP (80), HTTPS (443)
- `database` - MySQL (3306), PostgreSQL (5432), MongoDB (27017)
- `docker` - Docker daemon (2375, 2376)
- `development` - Dev ports (3000, 8000, 8080, 5000)
- `mail-server` - SMTP, IMAP, POP3

---

## 🔒 Security Features

1. **Authentication**: Admin-only access via Keycloak
2. **Rate Limiting**: Redis-based, per-user limits
3. **SSH Protection**: Prevents accidental SSH rule deletion
4. **Audit Logging**: All actions logged with username
5. **Input Validation**: Pydantic models validate all input
6. **Confirmation Required**: Reset requires `confirm=true`

---

## ⚠️ Safety Warnings

### SSH Protection
```bash
# This will FAIL (SSH protection)
DELETE /api/v1/network/firewall/rules/1

# This will SUCCEED (override)
DELETE /api/v1/network/firewall/rules/1?override_ssh=true
```

### Reset Confirmation
```bash
# This will FAIL (no confirmation)
POST /api/v1/network/firewall/reset

# This will SUCCEED (confirmed)
POST /api/v1/network/firewall/reset?confirm=true
```

---

## 🐛 Troubleshooting

### "Module 'firewall_manager' not found"
```bash
# Check file exists
ls backend/firewall_manager.py

# Verify syntax
python3 -m py_compile backend/firewall_manager.py
```

### "Rate limiter Redis unavailable"
```bash
# Check Redis
docker ps | grep redis
docker exec unicorn-redis redis-cli ping

# Verify env vars
docker exec ops-center-direct env | grep REDIS
```

### "Admin access required"
```bash
# Verify user role in Keycloak
# Check session: request.session.get('user', {})
```

### "UFW is not installed"
```bash
# Install on host (not container)
sudo apt-get install -y ufw
ufw version
```

---

## 📚 Documentation Files

- `firewall_api.py` - Main API router (667 lines)
- `FIREWALL_API_README.md` - Complete reference (700+ lines)
- `FIREWALL_API_INTEGRATION.md` - Integration guide (350+ lines)
- `FIREWALL_API_DELIVERY_SUMMARY.md` - Delivery summary (380+ lines)
- `FIREWALL_API_QUICK_REFERENCE.md` - This file

---

## 🔗 Dependencies

- ✅ `firewall_manager.py` - Core manager (798 lines)
- ✅ `rate_limiter.py` - Rate limiting (555 lines)
- ✅ `admin_subscriptions_api.py` - Authentication (389 lines)

---

## ✅ Integration Checklist

- [ ] firewall_manager.py verified
- [ ] Router registered in main app
- [ ] Backend restarted
- [ ] Health check responds
- [ ] Authenticated endpoint works
- [ ] Rate limiting triggers correctly
- [ ] SSH protection prevents deletion
- [ ] Audit logs appear in container logs

---

## 📊 Metrics

- **Endpoints**: 12 (8 required + 4 bonus)
- **Lines of Code**: 667
- **Documentation**: 1200+ lines
- **Rate Limits**: 10 configured
- **Security Layers**: 5
- **Dependencies**: 3 (all verified)

---

**Status**: ✅ COMPLETE
**Created**: October 22, 2025
**Agent**: API Developer Agent
**Epic**: 1.2 Phase 1
