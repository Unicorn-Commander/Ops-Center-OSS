# Cloudflare DNS Management Setup Guide

**Epic 1.6 - Cloudflare DNS Integration**
**Last Updated**: October 30, 2025
**Status**: Documentation Complete

---

## Overview

This guide explains how to configure Cloudflare DNS management in UC-Cloud Ops-Center.

## Prerequisites

- Active Cloudflare account (Free plan or higher)
- Domain(s) registered with any registrar
- Admin access to Ops-Center

---

## Step 1: Generate Cloudflare API Token

### Option A: Using Cloudflare Dashboard (Recommended)

1. **Login to Cloudflare Dashboard**
   - Visit: https://dash.cloudflare.com/
   - Login with your account

2. **Navigate to API Tokens**
   - Click on your profile icon (top right)
   - Select "My Profile"
   - Click "API Tokens" tab
   - Click "Create Token"

3. **Create Custom Token**
   - Click "Create Custom Token"
   - **Token name**: `UC-Cloud Ops-Center DNS Management`

4. **Set Permissions**
   ```
   Permissions:
   - Zone / Zone / Read
   - Zone / DNS / Edit

   Zone Resources:
   - Include / All zones

   Client IP Address Filtering (optional):
   - Add your server IP: your-server-ip

   TTL (optional):
   - Leave blank for no expiration
   ```

5. **Create and Save Token**
   - Click "Continue to summary"
   - Click "Create Token"
   - **IMPORTANT**: Copy the token immediately (you won't see it again)
   - Example: `your-cloudflare-api-token`

### Option B: Using API Token Template

1. Go to: https://dash.cloudflare.com/profile/api-tokens
2. Click "Create Token"
3. Select **"Edit zone DNS"** template
4. Choose zones: All zones or specific zones
5. Create token and copy it

---

## Step 2: Configure Ops-Center

### Method A: Environment File (Recommended)

1. **Edit Environment File**
   ```bash
   cd /opt/ops-center
   vim .env.auth
   ```

2. **Update Cloudflare Configuration**
   ```bash
   # === Cloudflare DNS Management (Epic 1.6) ===
   CLOUDFLARE_API_TOKEN=YOUR_TOKEN_HERE
   CLOUDFLARE_ACCOUNT_ID=  # Optional - auto-detected if left blank
   CLOUDFLARE_API_BASE_URL=https://api.cloudflare.com/client/v4
   ```

3. **Restart Ops-Center**
   ```bash
   docker restart ops-center-direct
   ```

4. **Verify Configuration**
   ```bash
   # Check API token is loaded
   docker exec ops-center-direct printenv | grep CLOUDFLARE_API_TOKEN

   # Test connectivity
   curl http://localhost:8084/api/v1/cloudflare/health
   ```

   Expected response:
   ```json
   {
     "status": "healthy",
     "cloudflare_api_connected": true,
     "timestamp": "2025-10-30T..."
   }
   ```

### Method B: Credential Manager (In Ops-Center UI)

**Coming Soon**: UI-based credential management will be available in Phase 2.

---

## Step 3: Verify Integration

### Test API Connectivity

```bash
# Health check
curl http://localhost:8084/api/v1/cloudflare/health

# List zones (requires authentication)
curl -H "Cookie: session=YOUR_SESSION" \
  http://localhost:8084/api/v1/cloudflare/zones
```

### Access UI

1. Open Ops-Center: https://unicorncommander.ai
2. Navigate to: **Network → Cloudflare DNS**
3. You should see:
   - Zone list (if configured correctly)
   - OR setup instructions (if token not configured)

---

## Troubleshooting

### Error: "Failed to load zones: Request failed with status code 403"

**Cause**: Invalid or missing API token

**Solutions**:

1. **Check token is set**:
   ```bash
   docker exec ops-center-direct printenv CLOUDFLARE_API_TOKEN
   ```

2. **Verify token has correct permissions**:
   - Go to: https://dash.cloudflare.com/profile/api-tokens
   - Find your token
   - Verify permissions include:
     - ✅ Zone / Zone / Read
     - ✅ Zone / DNS / Edit

3. **Regenerate token if invalid**:
   - Revoke old token
   - Create new token following Step 1
   - Update `.env.auth`
   - Restart container: `docker restart ops-center-direct`

### Error: "Authentication failed: API token invalid"

**Cause**: Token was revoked or expired

**Solution**: Generate new token and update configuration

### Error: "'NoneType' object has no attribute 'check_connectivity'"

**Cause**: Backend failed to initialize Cloudflare manager

**Solution**:
```bash
# Check backend logs
docker logs ops-center-direct --tail 100

# Verify token is not empty
docker exec ops-center-direct python3 -c "import os; print(f'Token length: {len(os.getenv(\"CLOUDFLARE_API_TOKEN\", \"\"))}')"

# Should output: Token length: 40
# If 0, token not loaded properly
```

### Zone Creation Fails: "Zone limit exceeded"

**Cause**: Free plan allows maximum 3 pending zones simultaneously

**Solution**:
- Wait for pending zones to activate (update nameservers at registrar)
- OR use Priority Queue feature:
  - Set priority to "high" or "critical"
  - Zone will be queued and created automatically when slot available

---

## API Token Security

### Best Practices

1. **Use Minimum Required Permissions**
   - Only grant DNS edit permissions
   - Don't use Global API Key (too powerful)

2. **IP Filtering** (Optional but recommended)
   ```
   Client IP Address Filtering:
   - your-server-ip (your server IP)
   ```

3. **Token Rotation**
   - Rotate tokens every 90 days
   - Revoke old tokens after rotation

4. **Environment Variables**
   - Never commit `.env.auth` to git
   - Use secrets management for production

### Revoking Compromised Tokens

If your token is compromised:

1. **Revoke immediately**:
   - Go to: https://dash.cloudflare.com/profile/api-tokens
   - Click "View" next to compromised token
   - Click "Roll" or "Revoke"

2. **Generate new token**:
   - Follow Step 1 above
   - Use different token name

3. **Update configuration**:
   - Update `.env.auth`
   - Restart ops-center

---

## Advanced Configuration

### Account ID (Optional)

If you manage multiple Cloudflare accounts:

1. **Find Account ID**:
   - Go to: https://dash.cloudflare.com
   - Select any domain
   - Look in right sidebar: "Account ID"
   - Example: `e9c5241afff445e1972bf5c53cdc64f0`

2. **Add to Configuration**:
   ```bash
   CLOUDFLARE_ACCOUNT_ID=e9c5241afff445e1972bf5c53cdc64f0
   ```

### Custom API Base URL

For Cloudflare Enterprise customers with custom endpoints:

```bash
CLOUDFLARE_API_BASE_URL=https://custom-api.cloudflare.com/client/v4
```

### Rate Limiting

Ops-Center automatically handles Cloudflare rate limits:

- **Read operations**: 30 requests/minute
- **Write operations**: 5 requests/minute

Requests exceeding limits are automatically queued and retried.

---

## Testing Your Setup

### Quick Test Script

```bash
#!/bin/bash
# Test Cloudflare API integration

echo "1. Testing health endpoint..."
curl -s http://localhost:8084/api/v1/cloudflare/health | jq

echo -e "\n2. Checking environment..."
docker exec ops-center-direct printenv | grep CLOUDFLARE

echo -e "\n3. Testing connectivity..."
docker exec ops-center-direct python3 -c "
from cloudflare_manager import CloudflareManager
import os
token = os.getenv('CLOUDFLARE_API_TOKEN')
print(f'Token configured: {bool(token)}')
print(f'Token length: {len(token) if token else 0}')
"

echo -e "\nSetup complete!"
```

Save as `test-cloudflare.sh`, make executable, and run:
```bash
chmod +x test-cloudflare.sh
./test-cloudflare.sh
```

---

## Next Steps

Once Cloudflare is configured:

1. **Add Your First Zone**:
   - Navigate to: Network → Cloudflare DNS
   - Click "Create Zone"
   - Enter your domain (e.g., `example.com`)
   - Click "Create"

2. **Update Nameservers**:
   - Cloudflare will assign nameservers (e.g., `ns1.cloudflare.com`)
   - Update nameservers at your domain registrar
   - Wait 1-24 hours for propagation

3. **Manage DNS Records**:
   - Click on your zone
   - Add DNS records (A, AAAA, CNAME, MX, TXT, etc.)
   - Enable/disable Cloudflare proxy (orange cloud)

---

## Support

### Documentation

- Cloudflare API Docs: https://developers.cloudflare.com/api/
- Ops-Center Docs: `/services/ops-center/docs/`
- Epic 1.6 Spec: `/services/ops-center/docs/epic1.6_cloudflare_architecture_spec.md`

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| 403 Forbidden | Invalid token | Regenerate token with correct permissions |
| 401 Unauthorized | Missing token | Add token to `.env.auth` |
| 429 Rate Limited | Too many requests | Wait for rate limit reset (automatic) |
| Zone limit exceeded | 3 pending zones | Use priority queue or wait for activation |

---

## Changelog

- **2025-10-30**: Initial documentation created
- **2025-10-22**: Epic 1.6 Phase 1 implementation completed

---

**End of Cloudflare Setup Guide**
