# Migration Wizard Quick Start Guide

**Epic 1.7: NameCheap to Cloudflare Domain Migration**

**Last Updated**: October 23, 2025
**Status**: Production Ready

---

## What is the Migration Wizard?

The Migration Wizard is an automated tool for migrating domains from NameCheap to Cloudflare. It provides a 5-step guided workflow that:

1. **Discovers** domains from your NameCheap account
2. **Exports** DNS records and configuration
3. **Validates** migration readiness
4. **Migrates** domains with zero downtime
5. **Verifies** successful migration

**Key Features**:
- ✅ Automated DNS record export
- ✅ Email service detection (Microsoft 365, Google Workspace, etc.)
- ✅ Zero-downtime migration
- ✅ Automatic rollback on errors
- ✅ Bulk domain migration
- ✅ Real-time progress tracking

---

## Quick Start (5 Minutes)

### Prerequisites

**Required Access**:
- Admin role in Ops-Center
- Keycloak SSO authentication

**Required Credentials**:
- NameCheap API key and username
- Cloudflare API token
- Client IP address (whitelisted in NameCheap)

### Step 1: Access the Wizard

**URL**: `https://your-domain.com/admin/infrastructure/migration`

**Navigation**:
1. Login to Ops-Center: `https://your-domain.com/auth/login`
2. Click "Infrastructure" in sidebar (if navigation updated)
3. Click "Domain Migration"
4. **Or** navigate directly to: `/admin/infrastructure/migration`

### Step 2: Configure API Credentials (First Time Only)

**NameCheap Setup**:

1. Go to NameCheap API settings:
   - URL: `https://ap.www.namecheap.com/settings/tools/apiaccess/`
   - Enable API access
   - Generate API key
   - Whitelist your server IP

2. Update `.env.auth` file:
   ```bash
   NAMECHEAP_API_USERNAME=YourUsername
   NAMECHEAP_API_KEY=YourAPIKey
   NAMECHEAP_USERNAME=YourUsername
   NAMECHEAP_CLIENT_IP=YourServerIP
   NAMECHEAP_SANDBOX=false
   ```

3. Restart Ops-Center:
   ```bash
   docker restart ops-center-direct
   ```

**Cloudflare Setup**:

1. Go to Cloudflare API tokens:
   - URL: `https://dash.cloudflare.com/profile/api-tokens`
   - Create token with "Edit zone DNS" permissions
   - Copy token

2. Update `.env.auth` file:
   ```bash
   CLOUDFLARE_API_TOKEN=YourAPIToken
   ```

3. Restart Ops-Center (if not already done above)

### Step 3: Verify Health Status

**Check API Connections**:

```bash
curl https://your-domain.com/api/v1/migration/health
```

**Expected Output**:
```json
{
  "status": "healthy",
  "namecheap_api_connected": true,
  "cloudflare_api_connected": true,
  "timestamp": "2025-10-23T00:10:00.000000"
}
```

**If Status is "degraded"**:
- Check credentials in `.env.auth`
- Verify IP is whitelisted in NameCheap
- Restart container: `docker restart ops-center-direct`
- Check logs: `docker logs ops-center-direct | grep -i migration`

### Step 4: Run Your First Migration

**Open the Wizard**:
- URL: `https://your-domain.com/admin/infrastructure/migration`

**Follow the 5-Step Workflow**:

**Step 1: Discover Domains**
- Click "Connect to NameCheap"
- Wizard automatically fetches your domains
- Review domain list
- Select domains to migrate

**Step 2: Export DNS Records**
- Click "Export DNS Records"
- Wizard exports DNS for selected domains
- Review DNS records table
- Check for email services (MX records)
- Download DNS backup (optional)

**Step 3: Validate Migration**
- Click "Validate Migration"
- Wizard checks for issues:
  - DNS conflicts
  - Email service compatibility
  - SSL certificate conflicts
  - Website health
- Review validation results
- Fix any warnings before proceeding

**Step 4: Execute Migration**
- Review migration plan
- Click "Start Migration"
- Wizard performs in order:
  1. Adds domains to Cloudflare
  2. Exports DNS to Cloudflare
  3. Updates nameservers at NameCheap
  4. Waits for DNS propagation
  5. Verifies successful migration
- Monitor real-time progress

**Step 5: Verify & Complete**
- Wizard runs automated health checks:
  - DNS resolution
  - SSL certificate
  - Email delivery
  - Website accessibility
- Review verification results
- Download migration report
- Click "Complete Migration"

**Duration**:
- Single domain: 5-15 minutes
- Bulk migration: 10-30 minutes
- DNS propagation: 24-48 hours (full worldwide propagation)

---

## Using the API (Programmatic Migration)

### Authentication

All API endpoints require admin authentication:

```bash
# Get auth token (via Keycloak SSO)
TOKEN=$(curl -s -X POST "https://your-domain.com/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}' \
  | jq -r '.access_token')
```

### List Domains

**Endpoint**: `GET /api/v1/migration/namecheap/domains`

```bash
curl -X GET "https://your-domain.com/api/v1/migration/namecheap/domains" \
  -H "Authorization: Bearer $TOKEN" \
  -H "accept: application/json"
```

**Response**:
```json
{
  "domains": [
    {
      "name": "example.com",
      "id": "12345678",
      "is_premium": false,
      "is_our_dns": true,
      "created": "2023-01-15",
      "expires": "2025-01-15",
      "auto_renew": true
    }
  ],
  "total": 1
}
```

### Get Domain Details

**Endpoint**: `GET /api/v1/migration/namecheap/domains/{domain}`

```bash
curl -X GET "https://your-domain.com/api/v1/migration/namecheap/domains/example.com" \
  -H "Authorization: Bearer $TOKEN" \
  -H "accept: application/json"
```

**Response**:
```json
{
  "domain": "example.com",
  "nameservers": ["dns1.registrar-servers.com", "dns2.registrar-servers.com"],
  "dns_records": [...],
  "email_service": {
    "provider": "microsoft365",
    "mx_records": [...],
    "active": true
  },
  "ssl_status": "active",
  "last_updated": "2025-10-23T00:00:00Z"
}
```

### Export DNS Records

**Endpoint**: `GET /api/v1/migration/namecheap/domains/{domain}/dns`

```bash
curl -X GET "https://your-domain.com/api/v1/migration/namecheap/domains/example.com/dns" \
  -H "Authorization: Bearer $TOKEN" \
  -H "accept: application/json"
```

**Response**:
```json
{
  "domain": "example.com",
  "records": [
    {
      "type": "A",
      "name": "@",
      "content": "192.0.2.1",
      "ttl": 3600,
      "priority": null
    },
    {
      "type": "MX",
      "name": "@",
      "content": "mail.example.com",
      "ttl": 3600,
      "priority": 10
    }
  ],
  "total": 2
}
```

### Preview Migration

**Endpoint**: `POST /api/v1/migration/migration/preview`

```bash
curl -X POST "https://your-domain.com/api/v1/migration/migration/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domains": ["example.com", "example.org"],
    "preserve_email": true,
    "preserve_ssl": true,
    "auto_rollback": true
  }'
```

**Response**:
```json
{
  "migration_id": "mig_abc123",
  "domains": ["example.com", "example.org"],
  "estimated_time": "15 minutes",
  "warnings": [
    {
      "domain": "example.com",
      "type": "email_service",
      "message": "Microsoft 365 email detected - MX records will be preserved"
    }
  ],
  "risks": [],
  "ready": true
}
```

### Execute Migration

**Endpoint**: `POST /api/v1/migration/migration/execute`

```bash
curl -X POST "https://your-domain.com/api/v1/migration/migration/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "migration_id": "mig_abc123",
    "confirm": true,
    "parallel": false
  }'
```

**Response**:
```json
{
  "migration_id": "mig_abc123",
  "status": "in_progress",
  "started_at": "2025-10-23T00:15:00Z",
  "domains_total": 2,
  "domains_completed": 0,
  "current_phase": "adding_cf"
}
```

### Check Migration Status

**Endpoint**: `GET /api/v1/migration/migration/{migration_id}/status`

```bash
curl -X GET "https://your-domain.com/api/v1/migration/migration/mig_abc123/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "accept: application/json"
```

**Response**:
```json
{
  "migration_id": "mig_abc123",
  "status": "in_progress",
  "progress": 50,
  "domains": [
    {
      "domain": "example.com",
      "status": "complete",
      "phase": "complete",
      "cloudflare_zone_id": "abc123"
    },
    {
      "domain": "example.org",
      "status": "in_progress",
      "phase": "updating_ns",
      "cloudflare_zone_id": "def456"
    }
  ],
  "started_at": "2025-10-23T00:15:00Z",
  "estimated_completion": "2025-10-23T00:30:00Z"
}
```

### Pause/Resume Migration

**Pause**:
```bash
curl -X POST "https://your-domain.com/api/v1/migration/migration/mig_abc123/pause" \
  -H "Authorization: Bearer $TOKEN"
```

**Resume**:
```bash
curl -X POST "https://your-domain.com/api/v1/migration/migration/mig_abc123/resume" \
  -H "Authorization: Bearer $TOKEN"
```

### Rollback Migration

**Endpoint**: `POST /api/v1/migration/migration/{migration_id}/rollback`

```bash
curl -X POST "https://your-domain.com/api/v1/migration/migration/mig_abc123/rollback" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Testing rollback procedure",
    "confirm": true
  }'
```

**Response**:
```json
{
  "migration_id": "mig_abc123",
  "rollback_status": "in_progress",
  "actions": [
    "Reverting nameservers to NameCheap",
    "Removing zones from Cloudflare"
  ]
}
```

---

## Best Practices

### Before Migration

1. **Backup Everything**
   - Export DNS records: Click "Download DNS Backup" in wizard
   - Screenshot current DNS settings
   - Document email configuration
   - Save SSL certificate info

2. **Test with One Domain First**
   - Choose a non-critical domain
   - Run full migration workflow
   - Verify all services work
   - Wait 24 hours for propagation
   - Then migrate production domains

3. **Check Email Configuration**
   - Identify email provider (Microsoft 365, Google Workspace, etc.)
   - Document MX records
   - Verify SPF, DKIM, DMARC records
   - Test email before and after migration

4. **Review SSL Certificates**
   - Check if using Cloudflare SSL or custom certificate
   - Document SSL configuration
   - Plan for certificate renewal

### During Migration

1. **Monitor Progress**
   - Keep wizard tab open
   - Watch real-time status updates
   - Don't close browser during migration
   - Note any warnings or errors

2. **Don't Make Changes**
   - Don't modify DNS at NameCheap during migration
   - Don't modify DNS at Cloudflare during migration
   - Wait for migration to complete

3. **Respond to Warnings**
   - Review validation warnings
   - Fix issues before proceeding
   - Don't ignore email service warnings

### After Migration

1. **Verify Everything Works**
   - Test website: `https://yourdomain.com`
   - Test email: Send and receive test emails
   - Test subdomains: All A/CNAME records
   - Test SSL: Check certificate validity

2. **Monitor for 24-48 Hours**
   - DNS propagation takes time
   - Some users may still see old nameservers
   - Monitor email delivery
   - Check website analytics for issues

3. **Document the Migration**
   - Download migration report from wizard
   - Save DNS records from Cloudflare
   - Update internal documentation
   - Notify team of changes

4. **Clean Up**
   - Review DNS records at Cloudflare
   - Remove duplicate records (if any)
   - Optimize TTL values
   - Enable Cloudflare features (proxy, caching, etc.)

---

## Troubleshooting

### Common Issues

#### 1. Health Check Shows "Degraded"

**Symptom**: `/api/v1/migration/health` returns `"namecheap_api_connected": false`

**Causes**:
- Invalid API key
- IP address not whitelisted
- API access not enabled in NameCheap
- Credentials not loaded by container

**Solutions**:
```bash
# 1. Verify credentials in .env.auth
cat /home/muut/Production/UC-Cloud/services/ops-center/.env.auth | grep NAMECHEAP

# 2. Restart container to reload credentials
docker restart ops-center-direct

# 3. Wait 10 seconds for startup
sleep 10

# 4. Check health again
docker exec ops-center-direct curl -s http://localhost:8084/api/v1/migration/health
```

#### 2. "Failed to Fetch Domains" Error

**Symptom**: Wizard shows error when clicking "Connect to NameCheap"

**Causes**:
- NameCheap API rate limit exceeded
- Invalid credentials
- Network connectivity issues

**Solutions**:
```bash
# Test API connection manually
curl -X GET "https://your-domain.com/api/v1/migration/namecheap/domains" \
  -H "Authorization: Bearer $TOKEN"

# Check backend logs
docker logs ops-center-direct | grep -i namecheap
```

#### 3. DNS Records Not Exported

**Symptom**: "Export DNS Records" step shows empty table

**Causes**:
- Domain not using NameCheap DNS
- NameCheap API doesn't return DNS for this domain type
- API rate limit

**Solutions**:
1. Verify domain uses NameCheap nameservers:
   ```bash
   dig NS yourdomain.com
   ```
2. Check if domain is premium or special type
3. Try exporting DNS manually from NameCheap panel

#### 4. Migration Stuck at "Updating Nameservers"

**Symptom**: Progress bar stuck at 50% for >5 minutes

**Causes**:
- NameCheap API slow response
- NameCheap nameserver update pending approval
- API rate limit

**Solutions**:
1. **Wait**: Nameserver updates can take 5-10 minutes
2. **Check Status**: Click "Refresh Status"
3. **Manual Check**: Login to NameCheap, verify nameservers were updated
4. **Pause & Resume**: If stuck >15 minutes, pause migration, check logs, resume

#### 5. Email Stopped Working After Migration

**Symptom**: Email bounce or not delivered after migration

**Causes**:
- MX records not copied correctly
- Email provider IP changed
- SPF/DKIM records missing

**Solutions**:
1. **Check MX Records**:
   ```bash
   dig MX yourdomain.com
   ```
2. **Compare with Backup**: Check DNS backup downloaded before migration
3. **Add Missing Records**: Manually add MX, SPF, DKIM records in Cloudflare
4. **Rollback**: If critical, use rollback feature to revert nameservers

#### 6. Website Shows Cloudflare Error Page

**Symptom**: "Error 521 - Web Server is Down" after migration

**Causes**:
- Origin IP not configured
- Cloudflare proxy enabled but origin unreachable
- SSL/TLS mode mismatch

**Solutions**:
1. **Check DNS Record**: Ensure A record points to correct IP
2. **Disable Proxy**: Click orange cloud icon in Cloudflare to disable proxy temporarily
3. **SSL Mode**: Change to "Flexible" or "Full" in Cloudflare SSL settings
4. **Wait for Propagation**: DNS changes take time

---

## API Rate Limits

### NameCheap API Limits

**Per-User Limits**:
- 20 calls per minute
- 700 calls per day

**Wizard Behavior**:
- Automatically throttles requests
- Shows warning if rate limit approached
- Pauses if limit exceeded
- Resumes after cooldown period

**Manual Override**:
```bash
# If you hit rate limit, wait 1 minute:
sleep 60
# Then retry operation
```

### Cloudflare API Limits

**Per-Account Limits**:
- 1,200 requests per 5 minutes
- 12,000 requests per hour

**Much Higher Than NameCheap**: Rarely an issue for typical migrations

---

## Advanced Features

### Bulk Domain Migration

**Use Case**: Migrate 10+ domains at once

**Steps**:
1. Export domain list to CSV:
   ```bash
   curl -X GET "https://your-domain.com/api/v1/migration/namecheap/domains" \
     -H "Authorization: Bearer $TOKEN" \
     | jq -r '.domains[] | .name' > domains.txt
   ```

2. Use bulk export API:
   ```bash
   curl -X POST "https://your-domain.com/api/v1/migration/namecheap/domains/bulk-export" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"domains": ["domain1.com", "domain2.com", "domain3.com"]}'
   ```

3. Use wizard for bulk migration:
   - Select multiple domains in Step 1
   - Export DNS for all in Step 2
   - Execute migration in Step 4 (sequential processing)

**Note**: Bulk migrations process sequentially to avoid rate limits

### Email Service Detection

**Automatically Detected Providers**:
- Microsoft 365 (Office 365)
- Google Workspace (G Suite)
- NameCheap Private Email
- Email forwarding

**How It Works**:
1. Wizard reads MX records
2. Matches against provider patterns
3. Shows warning if email service detected
4. Preserves MX records during migration

**Manual Email Configuration**:
If wizard doesn't detect your email provider:
1. Note current MX records before migration
2. After migration, manually add MX records in Cloudflare
3. Verify email works before completing migration

### Custom DNS Migration

**Use Case**: Migrate only some DNS records, not all

**Steps**:
1. Export DNS via API
2. Filter records you want to migrate
3. Manually create records in Cloudflare
4. Update nameservers when ready

**Not Supported in Wizard**: Wizard migrates all DNS records

### SSL Certificate Migration

**Auto-Detected**:
- Cloudflare Universal SSL (default for all domains)
- Custom SSL uploaded to NameCheap

**Wizard Actions**:
1. Checks if domain has SSL at NameCheap
2. Enables Cloudflare Universal SSL automatically
3. Sets SSL mode to "Flexible" or "Full" based on origin

**Custom Certificates**:
If you have a custom SSL certificate:
1. Upload to Cloudflare before migration
2. Or use Cloudflare Universal SSL (recommended)

---

## Security & Compliance

### Data Protection

**DNS Data**:
- Exported DNS records stored temporarily (in-memory)
- Not persisted to database
- Available for download during migration only

**API Credentials**:
- Stored in `.env.auth` (encrypted container volume)
- Never logged in plain text
- Transmitted over HTTPS only

**Audit Logging**:
- All migration actions logged (when audit system fixed)
- Admin actions tracked
- Keycloak SSO audit trail

### Rollback Safety

**Automatic Rollback**:
- Triggered on critical errors
- Reverts nameservers to NameCheap
- Removes Cloudflare zones
- No data loss

**Manual Rollback**:
- Available at any time during migration
- Use wizard "Rollback" button
- Or use API: `POST /api/v1/migration/migration/{id}/rollback`

### Rate Limit Protection

**NameCheap Throttling**:
- Automatic delay between API calls
- Respects 20 calls/min limit
- Pauses if approaching daily limit

**User Notification**:
- Warning shown in wizard
- Estimated completion time updated
- Option to pause and resume later

---

## Next Steps

### After Your First Migration

1. **Explore Cloudflare Features**
   - Enable caching for faster website
   - Set up firewall rules
   - Configure page rules
   - Enable auto-HTTPS

2. **Optimize DNS Settings**
   - Review TTL values (lower for faster propagation)
   - Enable Cloudflare proxy (orange cloud)
   - Configure load balancing (Enterprise)

3. **Migrate More Domains**
   - Use bulk migration for efficiency
   - Migrate in batches (5-10 at a time)
   - Monitor each batch before next

4. **Set Up Monitoring**
   - Cloudflare Analytics
   - Email delivery monitoring
   - Website uptime monitoring
   - SSL certificate expiry alerts

### Get Help

**Documentation**:
- Deployment guide: `/docs/EPIC_1.7_DEPLOYMENT_COMPLETE.md`
- API summary: `/backend/MIGRATION_API_SUMMARY.md`
- Architecture spec: `/docs/epic1.7_namecheap_migration_architecture_spec.md`

**Support**:
- Check logs: `docker logs ops-center-direct | grep -i migration`
- API health: `curl https://your-domain.com/api/v1/migration/health`
- Swagger docs: `https://your-domain.com/docs`

**Community**:
- UC-Cloud documentation: `/home/muut/Production/UC-Cloud/CLAUDE.md`
- GitHub issues: [Repository URL]

---

**Happy Migrating!** 🚀

Your domains are in good hands with the Migration Wizard. If you encounter any issues, refer to the Troubleshooting section above or check the deployment documentation.
