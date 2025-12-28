# Where to Configure Cloudflare API Token

**Issue**: Getting "Failed to load zones: Request failed with status code 403"
**Solution**: Configure your Cloudflare API token in Platform Settings

---

## Option 1: Platform Settings Page (GUI) ⭐ RECOMMENDED

### Access the Platform Settings

1. **Navigate to**: https://your-domain.com/admin/platform/settings
2. **Or via sidebar**:
   - Click "Platform" section (bottom of sidebar)
   - Click "Platform Settings"

### Configure Cloudflare Token

1. **Expand**: "Cloudflare DNS" section (click the accordion)
2. **Find**: `CLOUDFLARE_API_TOKEN` field
3. **Current value**: Should show `0LVXYAz...egC_` (masked)
4. **Click**: Eye icon to show full value, or just start typing
5. **Paste**: Your Cloudflare API token
6. **Click**: "Save & Restart" button (bottom of page)
7. **Wait**: 5-10 seconds for container restart
8. **Verify**: Go back to Cloudflare DNS page and refresh

### Expected Result

After saving and restarting:
- ✅ Cloudflare DNS page loads zones successfully
- ✅ No more 403 errors
- ✅ DNS records display correctly

---

## Option 2: Manual Configuration (Alternative)

If Platform Settings page isn't accessible:

```bash
# Edit environment file
vim /home/muut/Production/UC-Cloud/services/ops-center/.env.auth

# Find line (around line 30-35):
CLOUDFLARE_API_TOKEN=0LVXYAzHsGRtxn1Qe0_ItTlCFGxW9iogQCmsegC_

# Replace with your token
CLOUDFLARE_API_TOKEN=your_actual_cloudflare_token_here

# Save and restart container
docker restart ops-center-direct
```

---

## Troubleshooting

### Issue: "Platform Settings not in sidebar"

**Check**: Look for "Platform" section at the bottom of the sidebar
- Should contain: Brigade, Center-Deep, Email Settings, **Platform Settings**

**If missing**: Frontend may need rebuild
```bash
cd /home/muut/Production/UC-Cloud/services/ops-center
npm run build && cp -r dist/* public/
docker restart ops-center-direct
```

### Issue: "Still getting 403 after saving"

1. **Verify token is valid**:
   - Go to https://dash.cloudflare.com/profile/api-tokens
   - Check token hasn't been revoked
   - Verify token has "Zone → DNS → Edit" permissions

2. **Check token is loaded**:
   ```bash
   docker exec ops-center-direct printenv CLOUDFLARE_API_TOKEN
   ```

3. **Test token manually**:
   ```bash
   docker exec ops-center-direct python3 -c "
   import os, requests
   token = os.environ.get('CLOUDFLARE_API_TOKEN')
   headers = {'Authorization': f'Bearer {token}'}
   r = requests.get('https://api.cloudflare.com/client/v4/zones', headers=headers)
   print(f'Status: {r.status_code}')
   if r.status_code == 200:
       print(f'Zones: {len(r.json()[\"result\"])}')
   else:
       print(f'Error: {r.text}')
   "
   ```

---

## Quick Navigation

**Platform Settings Page**:
```
Sidebar → Platform (section) → Platform Settings
```

**Direct URL**:
```
https://your-domain.com/admin/platform/settings
```

**Cloudflare DNS Page**:
```
Sidebar → Infrastructure → Cloudflare DNS
```

**Direct URL**:
```
https://your-domain.com/admin/infrastructure/cloudflare
```

---

**Note**: Token rotation is deferred until actual production deployment.
Current token will continue to work for development/testing purposes.
