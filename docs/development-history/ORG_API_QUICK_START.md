# Organization API - Quick Start Guide

**Status**: ✅ Ready for Integration
**Last Updated**: October 22, 2025

---

## 🚀 Integration in 3 Steps

### Step 1: Add Import to server.py

```python
# Add this line around line 70-80 with other imports
from org_api import router as org_router
```

### Step 2: Register Router in server.py

```python
# Add this line around line 290-330 with other router registrations
app.include_router(org_router)
```

### Step 3: Restart Service

```bash
docker restart ops-center-direct
```

**That's it!** ✅ All 9 endpoints are now live.

---

## 🧪 Quick Test

```bash
# Test that the API is working
curl http://localhost:8084/api/v1/org/roles
```

**Expected Response**:
```json
{
  "roles": [
    {"id": "owner", "name": "Owner", ...},
    {"id": "billing_admin", "name": "Billing Admin", ...},
    {"id": "member", "name": "Member", ...}
  ]
}
```

---

## 📋 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/org/roles` | None | List available roles |
| GET | `/api/v1/org/{org_id}/members` | Member+ | List members |
| POST | `/api/v1/org/{org_id}/members` | Owner | Add member |
| PUT | `/api/v1/org/{org_id}/members/{user_id}/role` | Owner | Update role |
| DELETE | `/api/v1/org/{org_id}/members/{user_id}` | Owner | Remove member |
| GET | `/api/v1/org/{org_id}/stats` | Member+ | Get statistics |
| GET | `/api/v1/org/{org_id}/billing` | Billing+ | Get billing info |
| GET | `/api/v1/org/{org_id}/settings` | Member+ | Get settings |
| PUT | `/api/v1/org/{org_id}/settings` | Owner | Update settings |

---

## 🔑 Role Hierarchy

```
owner           → Full control (all permissions)
  └── billing_admin → Billing + view
      └── member      → View only
```

---

## 💡 Example Usage

### List Members
```bash
curl http://localhost:8084/api/v1/org/org_12345/members \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN"
```

### Add Member
```bash
curl -X POST http://localhost:8084/api/v1/org/org_12345/members \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN" \
  -d '{"user_id": "newuser@example.com", "role": "member"}'
```

### Update Role
```bash
curl -X PUT http://localhost:8084/api/v1/org/org_12345/members/user@example.com/role \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN" \
  -d '{"role": "billing_admin"}'
```

---

## 📁 Files Created

1. **API Implementation**: `backend/org_api.py` (598 lines)
2. **Integration Guide**: `ORG_API_INTEGRATION.md` (450+ lines)
3. **Implementation Summary**: `ORG_API_IMPLEMENTATION_SUMMARY.md` (600+ lines)
4. **Quick Start**: `ORG_API_QUICK_START.md` (this file)

---

## 🐛 Troubleshooting

### Import Error
```bash
# Check file exists
docker exec ops-center-direct ls -l /app/org_api.py
```

### 404 Not Found
```bash
# Verify router registered
docker exec ops-center-direct grep "org_router" /app/server.py
```

### Check Logs
```bash
docker logs ops-center-direct --tail 50 -f
```

---

## ✅ Verification Checklist

- [ ] Added import to server.py
- [ ] Registered router in server.py
- [ ] Restarted service
- [ ] Tested `/api/v1/org/roles` endpoint
- [ ] Verified no errors in logs

---

## 📚 Full Documentation

For detailed information, see:
- `ORG_API_INTEGRATION.md` - Complete integration guide
- `ORG_API_IMPLEMENTATION_SUMMARY.md` - Full implementation details
- `backend/org_api.py` - Source code with inline documentation

---

**Status**: ✅ PRODUCTION READY

**Developer**: Backend Developer Agent
**Date**: October 22, 2025
