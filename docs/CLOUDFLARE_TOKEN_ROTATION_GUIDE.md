# Cloudflare API Token Rotation Guide

**Date**: October 23, 2025
**Status**: 🚨 **URGENT - SECURITY ISSUE**
**Priority**: P0
**Estimated Time**: 30 minutes

---

## Why This Is Urgent

The current Cloudflare API token (`your-cloudflare-api-token`) has been exposed in **17 files** across the codebase, including:

- ✅ Documentation files (public)
- ✅ Test files
- ✅ Backend code files
- ✅ Environment configuration

**Risk**: Anyone with access to these files or documentation has full DNS/zone control over your Cloudflare account.

**Exposed Capabilities**:
- Create, modify, delete DNS records
- Modify zone settings
- Access SSL/TLS certificates
- Configure firewall rules
- View all zone data

---

## Files Containing Exposed Token

### Configuration Files (CRITICAL)
1. `/opt/ops-center/.env.auth`
2. `/opt/ops-center/backend/cloudflare_manager.py`
3. `/opt/ops-center/backend/secret_manager.py`

### Documentation Files
4. `EPIC_1.6_DEPLOYMENT_COMPLETE.md`
5. `EPIC_1.6_TEST_REPORT.md`
6. `NEXT_DEVELOPMENT_PRIORITIES.md`
7. `CREDENTIAL_MANAGEMENT_IMPLEMENTATION_REPORT.md`
8. `backend/docs/CREDENTIAL_API.md`
9. `docs/CREDENTIAL_EXPLORATION_INDEX.md`
10. `docs/CREDENTIAL_CODE_REFERENCE.md`
11. `docs/CREDENTIAL_MANAGEMENT_ANALYSIS.md`
12. `CREDENTIAL_MANAGEMENT.md`
13. `SECURITY_FIXES_APPLIED.md`
14. `MASTER_CHECKLIST.md`
15. `tests/CLOUDFLARE_TESTS_README.md`

### Test Files
16. `tests/security/test_security.py`
17. `tests/unit/test_cloudflare_manager.py`

---

## Step 1: Generate New Cloudflare API Token

### Access Cloudflare Dashboard

1. **Login**: Go to https://dash.cloudflare.com/profile/api-tokens
2. **Authenticate**: Use your Cloudflare credentials

### Create New Token

**Click**: "Create Token" button

**Select Template**: "Edit zone DNS" (or create custom)

**Configure Permissions**:
- ✅ Zone → DNS → Edit
- ✅ Zone → Zone → Read
- ✅ Zone → Zone Settings → Read

**Select Zones**:
- Option 1: All zones (recommended for flexibility)
- Option 2: Specific zones only (more secure)

**IP Address Filtering** (Optional but recommended):
- Add your server's IP address: `[YOUR_SERVER_IP]`
- This restricts token usage to your server only

**TTL** (Optional):
- Set expiration date for automatic revocation
- Recommended: 1 year from today

**Click**: "Continue to summary" → "Create Token"

### Save New Token

**IMPORTANT**: Copy the token immediately. It's shown only once!

```
New Token: cf_xyz123abc456def789ghi012jkl345mno678pqr901stu234vwx567yza890
```

**Token Format**: Starts with `cf_` (if using new format) or similar to old format

---

## Step 2: Update Ops-Center Configuration

### Option A: Use Platform Settings GUI (Recommended)

1. **Navigate**: https://unicorncommander.ai/admin/platform/settings
2. **Login**: Authenticate as admin
3. **Expand**: Cloudflare section
4. **Update**: CLOUDFLARE_API_TOKEN field
5. **Paste**: New token
6. **Click**: "Save & Restart"
7. **Confirm**: Wait 5-10 seconds for restart

### Option B: Manual Configuration

#### Update Environment File

**File**: `/opt/ops-center/.env.auth`

```bash
# Edit file
vim /opt/ops-center/.env.auth

# Find line with CLOUDFLARE_API_TOKEN
# Change from:
CLOUDFLARE_API_TOKEN=your-cloudflare-api-token

# To:
CLOUDFLARE_API_TOKEN=cf_xyz123abc456def789ghi012jkl345mno678pqr901stu234vwx567yza890
```

#### Restart Container

```bash
cd /opt/ops-center
docker restart ops-center-direct
```

---

## Step 3: Verify New Token Works

### Test API Connectivity

```bash
# Test Cloudflare API with new token
docker exec ops-center-direct python3 -c "
import os
import requests

token = os.environ.get('CLOUDFLARE_API_TOKEN')
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('https://api.cloudflare.com/client/v4/zones', headers=headers)

if response.status_code == 200:
    print('✅ New token works! Zones:', len(response.json()['result']))
else:
    print('❌ Token failed:', response.status_code, response.text)
"
```

### Test Cloudflare DNS Page

1. **Navigate**: https://unicorncommander.ai/admin/infrastructure/cloudflare
2. **Verify**: Zone list loads successfully
3. **Test**: Click on a zone to view DNS records
4. **Confirm**: No errors appear

---

## Step 4: Revoke Old Token

**IMPORTANT**: Only revoke the old token AFTER verifying the new one works!

### Revoke via Cloudflare Dashboard

1. **Go to**: https://dash.cloudflare.com/profile/api-tokens
2. **Find**: Token ending in `...egC_`
3. **Click**: "Revoke" button
4. **Confirm**: Click "Revoke" in confirmation dialog

**Success Message**: "Token revoked successfully"

---

## Step 5: Clean Up Documentation

### Automated Cleanup Script

Run this script to replace the exposed token in all documentation files:

```bash
#!/bin/bash
# cleanup-token-references.sh

OLD_TOKEN="your-cloudflare-api-token"
NEW_PLACEHOLDER="<CLOUDFLARE_API_TOKEN_REDACTED>"

# Files to update (documentation only, not config)
FILES=(
  "EPIC_1.6_DEPLOYMENT_COMPLETE.md"
  "EPIC_1.6_TEST_REPORT.md"
  "NEXT_DEVELOPMENT_PRIORITIES.md"
  "CREDENTIAL_MANAGEMENT_IMPLEMENTATION_REPORT.md"
  "backend/docs/CREDENTIAL_API.md"
  "docs/CREDENTIAL_EXPLORATION_INDEX.md"
  "docs/CREDENTIAL_CODE_REFERENCE.md"
  "docs/CREDENTIAL_MANAGEMENT_ANALYSIS.md"
  "CREDENTIAL_MANAGEMENT.md"
  "SECURITY_FIXES_APPLIED.md"
  "MASTER_CHECKLIST.md"
  "tests/CLOUDFLARE_TESTS_README.md"
  "tests/security/test_security.py"
  "tests/unit/test_cloudflare_manager.py"
)

cd /opt/ops-center

for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "Updating $file..."
    sed -i "s/$OLD_TOKEN/$NEW_PLACEHOLDER/g" "$file"
  fi
done

echo "✅ Documentation cleanup complete!"
echo "⚠️  NOTE: .env.auth and backend code files NOT modified"
echo "⚠️  You already updated those with the new token in Step 2"
```

### Run Cleanup

```bash
cd /opt/ops-center
chmod +x cleanup-token-references.sh
./cleanup-token-references.sh
```

---

## Step 6: Verify Security

### Check for Remaining Exposures

```bash
# Search for old token (should only appear in this guide now)
cd /opt/ops-center
grep -r "your-cloudflare-api-token" . --exclude-dir=node_modules

# Expected result: Only this guide (CLOUDFLARE_TOKEN_ROTATION_GUIDE.md)
```

### Security Checklist

- [ ] New token generated with proper permissions
- [ ] New token configured in .env.auth or Platform Settings
- [ ] Container restarted with new token
- [ ] Cloudflare API connectivity verified
- [ ] Cloudflare DNS page functional
- [ ] Old token revoked in Cloudflare dashboard
- [ ] Documentation cleaned up (14+ files)
- [ ] No remaining references to old token (except this guide)
- [ ] New token NOT committed to git (if using version control)

---

## Git Considerations

**IMPORTANT**: If this repository is pushed to GitHub or any public git repository:

### Check Git History

```bash
cd /opt/ops-center

# Search git history for exposed token
git log -S "your-cloudflare-api-token" --all --pretty=format:"%H %s"

# If found, consider using git-filter-repo to clean history
# WARNING: This rewrites git history and requires force push
```

### Prevent Future Exposure

Add to `.gitignore`:

```bash
# .gitignore
.env.auth
.env.local
.env.*.local
**/secrets/
**/credentials/
```

### Use Environment Variables

Instead of hardcoding tokens in files:

```python
# GOOD: Load from environment
import os
cloudflare_token = os.environ.get('CLOUDFLARE_API_TOKEN')

# BAD: Hardcoded in code
cloudflare_token = "your-cloudflare-api-token"
```

---

## Monitoring & Alerts

### Set Up Monitoring

**Cloudflare Dashboard**:
1. Go to: https://dash.cloudflare.com/profile/audit-log
2. Monitor API token usage
3. Set up alerts for unusual activity

**Recommended Alerts**:
- API token used from unexpected IP addresses
- Unusual spike in API requests
- Failed authentication attempts

### Regular Rotation Schedule

**Best Practice**: Rotate API tokens every 90 days

**Set Calendar Reminder**:
- Next rotation: January 23, 2026
- Frequency: Quarterly
- Owner: System Administrator

---

## Troubleshooting

### New Token Doesn't Work

**Error**: "Invalid API token" or "Unauthorized"

**Solutions**:
1. Check token was copied correctly (no extra spaces)
2. Verify token has correct permissions (Zone → DNS → Edit)
3. Check token hasn't expired
4. Verify token is for correct Cloudflare account

### Container Restart Failed

**Error**: Container won't start after token update

**Solutions**:
```bash
# Check container logs
docker logs ops-center-direct --tail 50

# Verify environment variable is set
docker exec ops-center-direct printenv | grep CLOUDFLARE_API_TOKEN

# Rebuild if needed
cd /opt/ops-center
docker compose -f docker-compose.direct.yml build
docker compose -f docker-compose.direct.yml up -d
```

### DNS Page Shows Errors

**Error**: "Failed to load zones" or similar

**Solutions**:
1. Check backend logs: `docker logs ops-center-direct | grep -i cloudflare`
2. Test token manually (see Step 3)
3. Verify Cloudflare API is accessible (not rate-limited)
4. Check network connectivity

---

## Summary

### What You Did

1. ✅ Generated new Cloudflare API token with proper permissions
2. ✅ Updated Ops-Center configuration (via GUI or .env.auth)
3. ✅ Restarted container with new token
4. ✅ Verified new token works
5. ✅ Revoked old exposed token
6. ✅ Cleaned up documentation (14+ files)
7. ✅ Verified no remaining exposures

### Security Improvements

- **Before**: Token exposed in 17 files, public documentation
- **After**: Token secured in environment variables only
- **Risk Reduction**: 95%+ (from critical to minimal)

### Time Taken

- **Estimated**: 30 minutes
- **Actual**: [Fill in after completion]

---

## Next Steps

### Immediate (Today)

- [ ] Complete this token rotation process
- [ ] Verify Cloudflare DNS management still works
- [ ] Update any external documentation that references the old token

### Short Term (This Week)

- [ ] Set up Cloudflare API monitoring and alerts
- [ ] Review other API tokens for similar exposures
- [ ] Implement token rotation policy (90-day schedule)

### Long Term (This Month)

- [ ] Migrate all secrets to secure vault (HashiCorp Vault, AWS Secrets Manager)
- [ ] Implement automated secret rotation
- [ ] Add git pre-commit hooks to prevent secret commits

---

**Rotation Date**: October 23, 2025
**Completed By**: [Your Name]
**Next Rotation**: January 23, 2026
**Status**: 🔒 **SECURED**
