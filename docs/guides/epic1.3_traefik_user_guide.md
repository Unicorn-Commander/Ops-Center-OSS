# Traefik Configuration Management - User Guide

**Epic 1.3 - System Administrator Documentation**
**Version**: 1.0.0
**Last Updated**: October 23, 2025
**Audience**: System Administrators (Technical)

---

## Table of Contents

1. [Overview](#overview)
2. [Accessing Traefik Configuration](#accessing-traefik-configuration)
3. [SSL Certificate Management](#ssl-certificate-management)
4. [Route Management](#route-management)
5. [Middleware Management](#middleware-management)
6. [Configuration Management](#configuration-management)
7. [Best Practices](#best-practices)
8. [Security Considerations](#security-considerations)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Topics](#advanced-topics)

---

## Overview

### What is Traefik?

Traefik is a modern HTTP reverse proxy and load balancer that makes deploying microservices easy. It automatically discovers services in your infrastructure and configures routes to them dynamically.

### What Does This Interface Do?

The Ops-Center Traefik Configuration Management interface provides a web-based control panel for:

- **SSL/TLS Certificate Management**: Request, monitor, and renew Let's Encrypt certificates
- **Route Configuration**: Define how traffic reaches your services
- **Middleware Setup**: Add authentication, rate limiting, compression, and more
- **Configuration Backup/Restore**: Safe configuration changes with rollback capability
- **Visual Dashboard**: Monitor routing status and certificate health

### Who Should Use This?

This interface is designed for:
- System administrators managing UC-Cloud infrastructure
- DevOps engineers configuring service routing
- Security teams managing SSL certificates
- Operations teams monitoring service health

### Prerequisites

Before using this interface, ensure you have:
- Admin access to Ops-Center
- Understanding of DNS and domain management
- Basic knowledge of HTTP routing concepts
- Familiarity with Docker services in your infrastructure

---

## Accessing Traefik Configuration

### Navigation

1. **Login to Ops-Center**
   - Navigate to `https://yourdomain.com` (or your configured URL)
   - Authenticate using Keycloak SSO

2. **Access Admin Dashboard**
   - Click the hamburger menu (☰) in the top-left
   - Select **"Admin"** → **"System"**
   - Click **"Traefik Configuration"**

3. **Interface Layout**
   - **Top Navigation**: Four main tabs (SSL Certificates, Routes, Middleware, Configuration)
   - **Action Buttons**: Add/Edit/Delete operations in each tab
   - **Status Indicators**: Real-time health and status icons
   - **Search/Filter**: Find specific configurations quickly

### Permissions Required

You must have one of the following roles:
- **Admin**: Full access to all Traefik features
- **System Manager**: Can view and modify routes/middleware
- **Security Manager**: Can manage SSL certificates

Users without these roles will see a permission denied error.

---

## SSL Certificate Management

SSL certificates enable secure HTTPS connections to your services. This interface integrates with Let's Encrypt for free, automated certificate provisioning.

### Understanding Certificate Status

The interface displays certificates with color-coded status indicators:

| Status | Color | Meaning | Action Required |
|--------|-------|---------|-----------------|
| **Valid** | 🟢 Green | Certificate is active and valid | None |
| **Expiring Soon** | 🟡 Yellow | Less than 30 days until expiry | Monitor (auto-renewal should trigger) |
| **Expired** | 🔴 Red | Certificate has expired | Request new certificate |
| **Revoked** | ⚫ Black | Certificate was manually revoked | Request new certificate |
| **Pending** | 🔵 Blue | Certificate request in progress | Wait 2-5 minutes |

### Requesting a New Certificate

**Step-by-Step Process:**

1. **Navigate to SSL Certificates Tab**
   - Click "SSL Certificates" in the top navigation
   - You'll see a list of existing certificates

2. **Click "Request Certificate"**
   - Green button in the top-right corner

3. **Fill in Certificate Details**
   ```
   Domain Name: example.com
   Admin Email: admin@example.com
   Certificate Type: [Single Domain] or [Wildcard]
   ```

   **Important Notes:**
   - Domain must point to your server's IP address
   - Email receives expiry notifications
   - Wildcard certs (*.example.com) cover all subdomains

4. **Submit Request**
   - Click "Request Certificate"
   - Status changes to "Pending"
   - Let's Encrypt initiates HTTP-01 challenge

5. **Wait for Validation**
   - Takes 2-5 minutes typically
   - Traefik serves validation file automatically
   - Status updates to "Valid" when complete

### What Happens Behind the Scenes?

When you request a certificate:

1. **DNS Check**: Traefik verifies domain points to your server
2. **ACME Challenge**: Let's Encrypt requests a validation file
3. **HTTP-01 Validation**: Traefik serves `.well-known/acme-challenge/` file
4. **Certificate Issuance**: Let's Encrypt signs and returns certificate
5. **Auto-Renewal Setup**: Traefik configures renewal 30 days before expiry

### Viewing Certificate Details

Click on any certificate in the list to view:

- **Common Name**: Primary domain
- **Subject Alternative Names (SANs)**: Additional domains covered
- **Issuer**: Let's Encrypt Authority
- **Valid From**: Certificate start date
- **Valid Until**: Expiry date
- **Renewal Date**: When auto-renewal triggers
- **Certificate Chain**: Full chain including intermediates

### Revoking a Certificate

⚠️ **Warning**: Only revoke certificates if compromised or no longer needed.

1. Click the **Revoke** button (🗑️) next to the certificate
2. Confirm in the dialog: "Are you sure you want to revoke this certificate?"
3. Certificate status changes to "Revoked"
4. HTTPS connections using this cert will fail

**When to Revoke:**
- Private key compromised or leaked
- Domain no longer owned by your organization
- Certificate issued in error
- Migrating to a different CA

### Auto-Renewal

Traefik automatically renews certificates:

- **Renewal Window**: 30 days before expiry
- **Renewal Attempts**: Up to 3 times if initial attempt fails
- **Notification**: Email sent to admin address if renewal fails
- **Monitoring**: Status indicator turns yellow when in renewal window

**No action required** - renewal is fully automatic!

### Wildcard Certificates

Wildcard certificates (*.example.com) cover all subdomains:

**Benefits:**
- Single certificate for unlimited subdomains
- Simplified certificate management
- Faster deployment of new services

**DNS Challenge Required:**
- Wildcard certs require DNS-01 challenge (not HTTP-01)
- You must configure DNS API credentials in Traefik
- See [Configuration Management](#configuration-management) for DNS provider setup

**Example Domains Covered:**
```
*.example.com covers:
- api.example.com
- chat.example.com
- admin.example.com
- anything.example.com
```

### Troubleshooting Certificate Requests

#### Problem: Certificate request fails with "Rate limit exceeded"

**Cause**: Let's Encrypt limits 50 certificates per registered domain per week.

**Solution:**
- Check current usage: https://crt.sh/?q=yourdomain.com
- Wait until next week, or
- Use Let's Encrypt staging environment for testing:
  ```yaml
  # In Traefik config
  certificatesResolvers:
    letsencrypt:
      acme:
        caServer: https://acme-staging-v02.api.letsencrypt.org/directory
  ```

#### Problem: Domain validation fails

**Cause**: DNS not pointing to your server.

**Solution:**
1. Check DNS propagation: `dig example.com` or https://dnschecker.org
2. Ensure A record points to your server IP
3. Wait for DNS propagation (up to 48 hours)
4. Retry certificate request

#### Problem: Certificate shows "untrusted" in browser

**Cause**: Certificate may still be provisioning, or browser cache issue.

**Solution:**
1. Wait 5 minutes and hard refresh (Ctrl+Shift+R)
2. Check certificate status in interface (should be "Valid")
3. Clear browser cache and cookies
4. Verify certificate chain is complete

#### Problem: Auto-renewal failed

**Cause**: Service downtime, network issues, or DNS changes.

**Solution:**
1. Check Traefik logs: `docker logs unicorn-traefik`
2. Verify domain DNS still points to your server
3. Manually request new certificate
4. Check email for Let's Encrypt notifications

---

## Route Management

Routes define how incoming traffic reaches your services. Each route consists of a **rule** (matching condition), a **service** (destination), and optional **middleware** (transformations).

### Understanding Routes

A route has three key components:

1. **Rule**: Condition that must match (e.g., `Host(\`example.com\`)`)
2. **Service**: Docker service name to route traffic to
3. **Middleware**: Optional processing (auth, rate limiting, etc.)

**Example Flow:**
```
Browser Request: https://api.example.com/users
    ↓
Route Rule: Host(`api.example.com`) && PathPrefix(`/users`)
    ↓
Middleware: rate-limit-100 (check request rate)
    ↓
Service: api-backend (Docker service)
    ↓
Response: User data JSON
```

### Viewing Existing Routes

Navigate to the **"Routes"** tab to see:

| Column | Description |
|--------|-------------|
| **Name** | Unique route identifier |
| **Rule** | Matching condition |
| **Service** | Destination service |
| **Middleware** | Applied transformations |
| **Status** | Active, Error, or Disabled |
| **Actions** | Edit, Delete, Test buttons |

### Creating a New Route

**Scenario**: Route traffic for `app.example.com` to Docker service `my-app`

**Step-by-Step:**

1. **Click "Add Route"**
   - Green button in top-right of Routes tab

2. **Fill in Route Details**
   ```
   Name: my-app-route
   Rule: Host(`app.example.com`)
   Service: my-app
   Priority: 1
   Middleware: [None] or select from dropdown
   ```

   **Field Descriptions:**
   - **Name**: Alphanumeric + hyphens, must be unique
   - **Rule**: Traefik rule syntax (see examples below)
   - **Service**: Exact Docker service name (case-sensitive)
   - **Priority**: Higher number = higher priority (default: 1)
   - **Middleware**: Chain of middleware to apply

3. **Click "Create Route"**
   - Route is validated and created
   - Traefik reloads configuration automatically
   - Status updates to "Active" within seconds

4. **Verify Route**
   - Click "Test" button to send a test request
   - Check service is accessible at configured domain
   - Monitor Traefik logs for any errors

### Route Rule Examples

Traefik uses a powerful rule syntax for matching requests:

#### Basic Host Matching
```
Host(`example.com`)
# Matches: https://example.com/anything
```

#### Multiple Domains
```
Host(`example.com`) || Host(`www.example.com`)
# Matches: Both example.com and www.example.com
```

#### Path Prefix
```
Host(`example.com`) && PathPrefix(`/api`)
# Matches: https://example.com/api/anything
# Does NOT match: https://example.com/web
```

#### Exact Path
```
Host(`example.com`) && Path(`/api/v1/users`)
# Matches: Only https://example.com/api/v1/users
```

#### Headers
```
Host(`example.com`) && Headers(`X-Custom-Header`, `value`)
# Matches: Requests with specific header
```

#### Method
```
Host(`example.com`) && Method(`POST`, `PUT`)
# Matches: Only POST and PUT requests
```

#### Query Parameters
```
Host(`example.com`) && Query(`key=value`)
# Matches: https://example.com?key=value
```

#### Complex Rules
```
(Host(`api.example.com`) && PathPrefix(`/v1`)) || (Host(`legacy.example.com`) && PathPrefix(`/api`))
# Matches: api.example.com/v1/* OR legacy.example.com/api/*
```

### Editing a Route

1. **Find Route in Table**
   - Use search box to filter by name
   - Or scroll through the list

2. **Click Edit Icon** (✏️)
   - Route details load into form

3. **Modify Fields**
   - Change rule, service, or middleware
   - All fields are editable

4. **Click "Save Changes"**
   - Validation runs automatically
   - Traefik reloads with new configuration
   - Changes take effect within 1-2 seconds

**Best Practice**: Test changes in a staging environment first!

### Deleting a Route

⚠️ **Warning**: Deleting a route makes the service inaccessible via that domain/path!

1. **Click Delete Icon** (🗑️) next to route
2. **Confirm Deletion**
   - Dialog appears: "Are you sure you want to delete route 'my-app-route'?"
3. **Route Removed**
   - Configuration reloaded immediately
   - Service no longer accessible via deleted route
   - Any bookmarks or links will return 404

**Recommended**: Disable route temporarily before deleting to test impact.

### Route Priority

When multiple routes match a request, priority determines which route handles it:

- **Higher Number = Higher Priority**
- **Default Priority**: 1
- **Range**: -1000 to 1000

**Example:**
```
Route 1: Host(`example.com`), Priority: 100
Route 2: Host(`example.com`) && PathPrefix(`/api`), Priority: 200

Request: https://example.com/api/users
Result: Route 2 handles it (higher priority)
```

### Service Discovery

Routes connect to Docker services by name. Ensure:

1. **Service Exists**: Use `docker ps` to verify service name
2. **Network**: Service is on same Docker network as Traefik
3. **Port**: Service exposes a port (defined in docker-compose.yml)
4. **Labels**: No conflicting Traefik labels on service

**Example docker-compose.yml:**
```yaml
services:
  my-app:
    image: myapp:latest
    networks:
      - web
    expose:
      - 8080
    labels:
      - "traefik.enable=true"
```

---

## Middleware Management

Middleware modifies requests and responses as they pass through Traefik. Think of middleware as "plugins" that add functionality to your routes.

### Understanding Middleware

Middleware processes requests in a **chain**:

```
Request → Middleware 1 → Middleware 2 → ... → Service → ... → Middleware 2 → Middleware 1 → Response
```

**Common Use Cases:**
- Add authentication
- Rate limit requests
- Redirect HTTP to HTTPS
- Compress responses
- Add security headers
- Strip path prefixes

### Middleware Types

The interface supports these middleware types:

#### 1. Basic Authentication

Require username/password to access service.

**Configuration:**
```json
{
  "users": [
    "admin:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/",
    "user:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/"
  ]
}
```

**Generating Password Hash:**
```bash
echo $(htpasswd -nb admin password)
# Output: admin:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/
```

**Use Cases:**
- Admin panels
- Internal tools
- Development environments

#### 2. Rate Limiting

Limit number of requests per IP address.

**Configuration:**
```json
{
  "average": 100,
  "period": "1m",
  "burst": 50
}
```

**Parameters:**
- **average**: Maximum requests per period
- **period**: Time window (1s, 1m, 1h)
- **burst**: Temporary spike allowance

**Use Cases:**
- API endpoints
- Public-facing services
- Preventing abuse/DDoS

#### 3. Redirect Scheme

Force HTTPS by redirecting HTTP requests.

**Configuration:**
```json
{
  "scheme": "https",
  "permanent": true
}
```

**Parameters:**
- **scheme**: Target scheme (https)
- **permanent**: Use 301 (permanent) vs 302 (temporary)

**Use Cases:**
- Force SSL on all routes
- Security compliance
- SEO benefits

#### 4. Compress

Gzip compression for responses.

**Configuration:**
```json
{
  "excludedContentTypes": ["image/png", "image/jpeg"]
}
```

**Parameters:**
- **excludedContentTypes**: Content types NOT to compress

**Use Cases:**
- Reduce bandwidth usage
- Faster page loads
- Cost savings on data transfer

#### 5. Headers

Add, modify, or remove HTTP headers.

**Configuration:**
```json
{
  "customRequestHeaders": {
    "X-Custom-Header": "value"
  },
  "customResponseHeaders": {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block"
  }
}
```

**Use Cases:**
- Security headers (HSTS, CSP, etc.)
- Custom application headers
- CORS configuration

#### 6. Strip Prefix

Remove path prefix before sending to service.

**Configuration:**
```json
{
  "prefixes": ["/api/v1"]
}
```

**Example:**
```
Request: /api/v1/users
After StripPrefix: /users
Service receives: /users
```

**Use Cases:**
- API versioning
- Service path normalization

#### 7. Add Prefix

Add path prefix before sending to service.

**Configuration:**
```json
{
  "prefix": "/api"
}
```

**Use Cases:**
- Path rewriting
- Service integration

#### 8. Circuit Breaker

Stop sending requests to failing service.

**Configuration:**
```json
{
  "expression": "NetworkErrorRatio() > 0.30"
}
```

**Use Cases:**
- Service resilience
- Prevent cascade failures

### Creating Middleware

**Example**: Create rate limiting middleware (100 requests/minute per IP)

1. **Navigate to Middleware Tab**

2. **Click "Add Middleware"**

3. **Fill in Details**
   ```
   Name: rate-limit-100
   Type: [Rate Limit]
   Description: Limit 100 requests per minute

   Configuration:
   {
     "average": 100,
     "period": "1m",
     "burst": 50
   }
   ```

4. **Click "Create Middleware"**
   - Validation checks JSON syntax
   - Middleware saved to configuration
   - Available for routes immediately

### Applying Middleware to Routes

**Option 1: When Creating Route**
- Select middleware from dropdown in route creation form

**Option 2: Edit Existing Route**
1. Click Edit on route
2. Select middleware from dropdown (multiple allowed)
3. Save changes

**Middleware Chain Order**:
Middleware applies in the order selected:
```
[auth] → [rate-limit] → [compress] → Service
```

**Best Practice**: Order matters!
- Authentication before rate limiting
- Rate limiting before compression
- Headers last (closest to service)

### Editing Middleware

1. Click Edit icon (✏️) next to middleware
2. Modify configuration JSON
3. Click "Save Changes"
4. All routes using this middleware are updated automatically

⚠️ **Warning**: Changes affect ALL routes using this middleware!

### Deleting Middleware

1. Click Delete icon (🗑️)
2. System checks if middleware is in use
3. If in use, warning appears: "Middleware used by 3 routes. Remove from routes first."
4. If not in use, confirms deletion
5. Middleware removed from configuration

### Testing Middleware

Use the built-in test tool:

1. Select middleware in table
2. Click "Test" button
3. Send sample request
4. View middleware behavior in response

**Example Test Results:**
```json
{
  "middleware": "rate-limit-100",
  "request": "GET /test HTTP/1.1",
  "status": 200,
  "headers": {
    "X-RateLimit-Limit": "100",
    "X-RateLimit-Remaining": "99"
  },
  "processing_time": "12ms"
}
```

---

## Configuration Management

The Configuration tab provides direct access to Traefik's `traefik.yml` configuration file for advanced customization.

### Viewing Current Configuration

1. **Navigate to Configuration Tab**
2. **Current Config Display**
   - Syntax-highlighted YAML
   - Read-only view by default
   - Shows full traefik.yml content

### Understanding Configuration Structure

```yaml
# Entry Points (ports Traefik listens on)
entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

# Certificate Resolvers
certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web

# Providers (where Traefik discovers services)
providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
  file:
    filename: /config/dynamic.yml

# API & Dashboard
api:
  dashboard: true
  insecure: false

# Logging
log:
  level: INFO
```

### Editing Configuration

⚠️ **Advanced Users Only** - Incorrect configuration can break routing!

**Step-by-Step:**

1. **Click "Edit Configuration"**
   - YAML editor becomes editable
   - Syntax highlighting active

2. **Make Changes**
   - Edit YAML directly
   - Add new sections
   - Modify existing values

3. **Click "Validate"**
   - Syntax check runs
   - Required fields verified
   - Error messages displayed if invalid

4. **Click "Apply"**
   - Automatic backup created first
   - Configuration saved to traefik.yml
   - Traefik reloads gracefully

### Configuration Validation

The validator checks:

1. **YAML Syntax**: Valid YAML structure
2. **Required Fields**: entryPoints, providers must exist
3. **Type Checking**: Values match expected types
4. **References**: Middleware/services referenced exist
5. **Certificate Resolvers**: Email and storage configured

**Example Validation Error:**
```
Error: entryPoints.websecure.address must be a string
Line 5: address: 443
Expected: address: ":443"
```

### Backup & Restore

Every configuration change triggers an automatic backup.

#### Creating Manual Backups

1. Click **"Create Backup"** button
2. Backup saved with timestamp: `traefik_backup_20251023_143052.yml`
3. Stored in `/home/muut/Production/UC-Cloud/services/ops-center/backups/traefik/`
4. Confirmation message appears

#### Restoring from Backup

1. Click **"Restore from Backup"** button
2. Dropdown appears with available backups
3. Select backup by timestamp
4. Preview shows config diff (what will change)
5. Click **"Confirm Restore"**
6. Configuration restored
7. Traefik reloads automatically

**Backup Retention:**
- Automatic backups: 30 days
- Manual backups: 90 days
- Oldest backups deleted automatically
- Critical: Never delete backups manually!

### Reloading Traefik

Traefik watches for configuration changes and reloads automatically. Manual reload:

1. **Click "Reload Traefik"** button
2. **Reload Type Selection**:
   - **Graceful**: No downtime, ongoing requests complete (recommended)
   - **Hard**: Immediate restart, drops connections (use for emergencies)

3. **Monitor Reload**
   - Status indicator shows progress
   - Logs display reload messages
   - Completion notification appears

**Reload Time:**
- Graceful: 1-3 seconds
- Hard: 5-10 seconds

### Dynamic Configuration

Traefik supports dynamic configuration via file provider:

**File**: `/config/dynamic.yml`

**Use Cases:**
- Routes not managed by Docker labels
- Complex middleware chains
- HTTP to HTTPS redirects
- Custom services (non-Docker)

**Example dynamic.yml:**
```yaml
http:
  routers:
    custom-route:
      rule: "Host(`custom.example.com`)"
      service: custom-service
      middlewares:
        - auth
        - rate-limit

  services:
    custom-service:
      loadBalancer:
        servers:
          - url: "http://192.168.1.100:8080"

  middlewares:
    auth:
      basicAuth:
        users:
          - "admin:$apr1$..."
```

**Editing Dynamic Config:**
1. Download current dynamic.yml
2. Edit locally
3. Upload via "Upload Dynamic Config" button
4. Validation runs automatically
5. Traefik reloads with new config

---

## Best Practices

### SSL Certificate Best Practices

1. **Use Wildcard Certificates**
   - Single cert for all subdomains: `*.example.com`
   - Reduces certificate management overhead
   - Faster deployment of new services

2. **Monitor Expiry Dates**
   - Check dashboard weekly
   - Investigate yellow "Expiring Soon" status
   - Ensure auto-renewal is working

3. **Keep Admin Email Current**
   - Let's Encrypt sends expiry warnings
   - Update email in configuration if changed
   - Monitor spam folder for notifications

4. **Test with Staging First**
   - Use Let's Encrypt staging for testing
   - Avoids rate limits (50 certs/week)
   - Switch to production when ready

5. **Backup Certificate Storage**
   - Backup `/letsencrypt/acme.json` regularly
   - Include in disaster recovery plan
   - Store encrypted backup offsite

### Route Best Practices

1. **Use Descriptive Names**
   - Good: `api-production-route`, `admin-dashboard-route`
   - Bad: `route1`, `test`, `temp`

2. **Document Complex Rules**
   - Add comments in dynamic.yml
   - Explain why rule exists
   - Include examples of matching URLs

3. **Test in Staging First**
   - Never test routes in production
   - Use separate domain for staging
   - Verify before deploying to production

4. **Set Appropriate Priorities**
   - Specific routes = higher priority
   - General routes = lower priority
   - Document priority scheme

5. **Monitor Route Performance**
   - Check Traefik metrics
   - Identify slow routes
   - Optimize as needed

### Middleware Best Practices

1. **Apply Rate Limiting to Public APIs**
   - Prevent abuse and DDoS
   - Set reasonable limits (100-1000 req/min)
   - Monitor and adjust based on traffic

2. **Always Force HTTPS**
   - Use redirect scheme middleware
   - Apply to all routes
   - SEO and security benefits

3. **Use Basic Auth for Admin Panels**
   - Additional layer of security
   - Cheap and effective
   - Rotate passwords regularly

4. **Compress Responses**
   - Reduce bandwidth by 60-80%
   - Faster page loads
   - Exclude images/videos

5. **Keep Middleware Minimal**
   - Each middleware adds latency
   - Only apply what's needed
   - Measure performance impact

### Configuration Best Practices

1. **Always Validate Before Applying**
   - Use built-in validator
   - Test in staging first
   - Review diff before confirming

2. **Create Manual Backups Before Major Changes**
   - Don't rely only on auto-backups
   - Name backups descriptively
   - Document what changed

3. **Keep Configuration Simple**
   - Avoid overly complex rules
   - Split complex routes into multiple simpler ones
   - Document any complexity

4. **Use Version Control**
   - Store traefik.yml in Git
   - Track changes over time
   - Easier rollback

5. **Test Configuration Syntax**
   - Use online YAML validators
   - Check Traefik docs for examples
   - Test locally before deploying

---

## Security Considerations

### SSL/TLS Security

#### 1. Use Only TLS 1.2 and Above

**Why**: TLS 1.0 and 1.1 have known vulnerabilities.

**Configuration:**
```yaml
entryPoints:
  websecure:
    address: ":443"
    http:
      tls:
        options: modern
```

**TLS Options:**
```yaml
tls:
  options:
    modern:
      minVersion: VersionTLS12
      cipherSuites:
        - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
        - TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
```

#### 2. Enable HSTS

HTTP Strict Transport Security forces browsers to use HTTPS.

**Middleware:**
```json
{
  "customResponseHeaders": {
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload"
  }
}
```

**Apply to all routes** for maximum security.

#### 3. Monitor Certificate Transparency Logs

Check if unauthorized certificates are issued for your domains:
- https://crt.sh/
- https://transparencyreport.google.com/https/certificates

Set up alerts for new certificate issuance.

#### 4. Rotate Certificates Proactively

Don't wait for expiry:
- Request new cert 60 days before expiry
- Test new cert in staging
- Deploy to production
- Revoke old cert after migration

### Access Control

#### 1. Restrict Traefik Dashboard

**Never expose dashboard publicly!**

**Recommended:**
```yaml
api:
  dashboard: true
  insecure: false  # Disable insecure access
```

**Apply Basic Auth:**
```json
{
  "users": ["admin:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/"]
}
```

**Limit by IP:**
```yaml
http:
  middlewares:
    admin-whitelist:
      ipWhiteList:
        sourceRange:
          - "10.0.0.0/8"
          - "192.168.0.0/16"
```

#### 2. Use Strong Authentication

For basic auth:
- Minimum 16 characters
- Mix of upper/lower/numbers/symbols
- Rotate every 90 days
- Never reuse passwords

**Generate Strong Passwords:**
```bash
openssl rand -base64 24
```

#### 3. Monitor Audit Logs

Enable access logging:
```yaml
accessLog:
  filePath: "/logs/access.log"
  format: json
```

**Monitor for:**
- Failed authentication attempts
- Unusual traffic patterns
- Requests from unexpected IPs
- Certificate errors

#### 4. Implement API Token Rotation

If using Traefik API:
- Generate tokens with limited scope
- Rotate every 30 days
- Revoke unused tokens
- Monitor token usage

### Configuration Security

#### 1. Never Commit Secrets to Git

**Bad:**
```yaml
acme:
  email: admin@example.com
  dnsChallenge:
    provider: cloudflare
    credentials:
      CF_API_KEY: abc123  # NEVER DO THIS!
```

**Good:**
```yaml
acme:
  email: admin@example.com
  dnsChallenge:
    provider: cloudflare
    credentials:
      CF_API_KEY: ${CF_API_KEY}  # Environment variable
```

**Use `.env` file:**
```bash
CF_API_KEY=abc123
```

**Add to `.gitignore`:**
```
.env
acme.json
```

#### 2. Encrypt Backup Files

Backups contain sensitive data:

```bash
# Encrypt backup
gpg --encrypt --recipient admin@example.com traefik_backup.yml

# Decrypt backup
gpg --decrypt traefik_backup.yml.gpg > traefik_backup.yml
```

#### 3. Restrict File Permissions

```bash
# Traefik config (read-only for Traefik user)
chmod 600 /config/traefik.yml
chown traefik:traefik /config/traefik.yml

# ACME storage (critical - contains private keys!)
chmod 600 /letsencrypt/acme.json
chown traefik:traefik /letsencrypt/acme.json
```

#### 4. Use Separate Environments

**Never test in production!**

- **Development**: Local testing
- **Staging**: Pre-production testing with staging certs
- **Production**: Live environment

**Staging Configuration:**
```yaml
certificatesResolvers:
  letsencrypt-staging:
    acme:
      caServer: https://acme-staging-v02.api.letsencrypt.org/directory
      email: admin@example.com
      storage: /letsencrypt/acme-staging.json
```

### Network Security

#### 1. Isolate Traefik Network

```yaml
networks:
  web:
    driver: bridge
    internal: false  # External-facing
  internal:
    driver: bridge
    internal: true   # Internal-only
```

**Services:**
- Traefik: `web` network (external)
- Backend services: `internal` network (isolated)
- Bridge: Only via Traefik

#### 2. Enable Rate Limiting

Prevent DDoS and abuse:

```json
{
  "average": 100,
  "period": "1m",
  "burst": 50,
  "sourceCriterion": {
    "requestHeaderName": "X-Forwarded-For"
  }
}
```

**Apply to:**
- All public-facing routes
- API endpoints (stricter limits)
- Login pages (very strict limits)

#### 3. Implement Request Size Limits

Prevent memory exhaustion:

```yaml
http:
  middlewares:
    limit-request-size:
      buffering:
        maxRequestBodyBytes: 10485760  # 10 MB
```

#### 4. Use Fail2Ban Integration

Ban IPs after repeated failures:

```bash
# /etc/fail2ban/filter.d/traefik-auth.conf
[Definition]
failregex = ^.*Error while authenticating.*clientIP=<HOST>.*$
ignoreregex =
```

```bash
# /etc/fail2ban/jail.local
[traefik-auth]
enabled = true
port = http,https
filter = traefik-auth
logpath = /var/log/traefik/access.log
maxretry = 5
bantime = 3600
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Routes Not Working After Creation

**Symptoms:**
- Route created successfully
- Service returns 404 or 503 error
- Traefik dashboard shows route as "inactive"

**Diagnosis:**
```bash
# Check if service exists
docker ps | grep my-service

# Check service network
docker inspect my-service | grep NetworkMode

# Check Traefik logs
docker logs traefik | grep "my-app-route"
```

**Solutions:**

1. **Service name mismatch**
   - Route service: `my-app`
   - Actual service: `my_app` (underscore vs hyphen)
   - **Fix**: Edit route, correct service name

2. **Service not on correct network**
   ```bash
   docker network connect web my-service
   docker restart my-service
   ```

3. **Service not exposing port**
   - Add to docker-compose.yml:
     ```yaml
     expose:
       - "8080"
     ```
   - Restart service

4. **Conflicting Docker labels**
   - Remove manual Traefik labels from service
   - Let Ops-Center manage routing

#### Issue 2: SSL Certificate Shows "Untrusted"

**Symptoms:**
- Browser warning: "Your connection is not private"
- Certificate status shows "Valid" in interface
- Cert issued by Let's Encrypt

**Diagnosis:**
```bash
# Check certificate in browser
openssl s_client -connect example.com:443 -servername example.com

# Check certificate file
docker exec traefik cat /letsencrypt/acme.json | jq '.letsencrypt.Certificates'
```

**Solutions:**

1. **Certificate still provisioning**
   - Wait 5 minutes
   - Hard refresh browser (Ctrl+Shift+R)
   - Check status in interface

2. **Incomplete certificate chain**
   - Let's Encrypt cert must include intermediates
   - Check acme.json for full chain
   - Re-request certificate if incomplete

3. **Browser cache issue**
   - Clear browser cache completely
   - Try incognito/private window
   - Try different browser

4. **Wrong certificate served**
   - Multiple certs for same domain
   - Check Traefik dashboard for conflicts
   - Delete duplicate/old certificates

#### Issue 3: Middleware Not Applying to Route

**Symptoms:**
- Middleware configured correctly
- Route shows middleware attached
- Middleware behavior not observed (no auth, no rate limiting, etc.)

**Diagnosis:**
```bash
# Check Traefik configuration
docker exec traefik cat /config/dynamic.yml

# Test with curl
curl -I https://example.com/api
```

**Solutions:**

1. **Middleware created after route**
   - Edit route
   - Re-select middleware from dropdown
   - Save changes

2. **Middleware configuration invalid**
   - Check JSON syntax in middleware config
   - Validate against Traefik docs
   - Fix configuration errors

3. **Middleware name mismatch**
   - Route references: `rate-limit-100`
   - Actual middleware: `ratelimit-100`
   - **Fix**: Match names exactly (case-sensitive!)

4. **Middleware order wrong**
   - Auth middleware must be before others
   - Reorder middleware chain in route config

#### Issue 4: Configuration Reload Fails

**Symptoms:**
- "Reload failed" error message
- Traefik not responding after config change
- Routes suddenly returning 503

**Diagnosis:**
```bash
# Check Traefik container status
docker ps | grep traefik

# Check Traefik logs for errors
docker logs traefik --tail 100

# Validate configuration manually
docker exec traefik traefik validate --configFile=/config/traefik.yml
```

**Solutions:**

1. **Syntax error in configuration**
   ```
   Error: yaml: line 15: mapping values are not allowed in this context
   ```
   - Restore from backup
   - Fix syntax error
   - Validate before applying

2. **Missing required fields**
   ```
   Error: entryPoints is required
   ```
   - Restore from backup
   - Ensure all required sections present

3. **Invalid middleware reference**
   ```
   Error: middleware "nonexistent" not found
   ```
   - Remove reference to deleted middleware
   - Or recreate missing middleware

4. **Traefik container crashed**
   ```bash
   docker restart traefik
   docker logs traefik  # Check for startup errors
   ```

#### Issue 5: Auto-Renewal Failed

**Symptoms:**
- Certificate status "Expiring Soon" for > 7 days
- Email notification from Let's Encrypt
- No new certificate issued

**Diagnosis:**
```bash
# Check renewal logs
docker logs traefik | grep -i renew

# Check ACME storage
docker exec traefik cat /letsencrypt/acme.json | jq '.letsencrypt.Certificates[] | select(.domain.main=="example.com")'

# Test ACME challenge
curl http://example.com/.well-known/acme-challenge/test
```

**Solutions:**

1. **Service downtime during renewal window**
   - Traefik must be running 24/7
   - Check uptime: `docker ps | grep traefik`
   - Ensure no scheduled maintenance during renewal

2. **DNS changed**
   - Domain no longer points to your server
   - Check DNS: `dig example.com`
   - Update DNS records if changed

3. **Network connectivity issues**
   - Check internet connectivity
   - Test: `docker exec traefik ping -c 3 acme-v02.api.letsencrypt.org`
   - Check firewall rules

4. **Rate limit hit**
   - Too many renewal attempts
   - Check rate limit status: https://crt.sh/?q=example.com
   - Wait 7 days for rate limit reset

**Manual Renewal:**
```bash
# Force renewal (use sparingly!)
docker exec traefik rm /letsencrypt/acme.json
docker restart traefik
# Request certificate again via interface
```

#### Issue 6: High Latency Through Traefik

**Symptoms:**
- Slow response times
- Timeout errors
- Normal speed when accessing service directly

**Diagnosis:**
```bash
# Check Traefik resource usage
docker stats traefik

# Test direct service access
curl -w "@curl-format.txt" -s http://backend:8080/api

# Test via Traefik
curl -w "@curl-format.txt" -s https://example.com/api
```

**curl-format.txt:**
```
time_namelookup:  %{time_namelookup}\n
time_connect:  %{time_connect}\n
time_appconnect:  %{time_appconnect}\n
time_pretransfer:  %{time_pretransfer}\n
time_redirect:  %{time_redirect}\n
time_starttransfer:  %{time_starttransfer}\n
time_total:  %{time_total}\n
```

**Solutions:**

1. **Too many middleware**
   - Each adds 5-20ms latency
   - Remove unnecessary middleware
   - Combine similar middleware

2. **Resource constraints**
   - Traefik CPU/memory limited
   - Increase Docker resource limits:
     ```yaml
     deploy:
       resources:
         limits:
           cpus: '2'
           memory: 2G
     ```

3. **Inefficient route rules**
   - Complex regex rules slow matching
   - Simplify rules where possible
   - Use exact matches over regex

4. **Network bottleneck**
   - Check Docker network mode
   - Use `host` network for performance (less secure)
   - Optimize Docker network settings

### Getting Help

If troubleshooting doesn't resolve your issue:

1. **Check Traefik Logs**
   ```bash
   docker logs traefik --tail 1000 > traefik_logs.txt
   ```

2. **Export Configuration**
   - Download current traefik.yml
   - Export routes/middleware list
   - Take screenshots of error messages

3. **Document Issue**
   - What were you trying to do?
   - What happened instead?
   - Error messages (exact text)
   - Steps to reproduce

4. **Contact Support**
   - Email: ops-support@your-domain.com
   - Include: logs, config, documentation
   - Response time: 24 hours (business days)

---

## Advanced Topics

### DNS Challenge for Wildcard Certificates

Wildcard certificates (*.example.com) require DNS-01 challenge instead of HTTP-01.

**Configuration Example (Cloudflare):**

```yaml
certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: /letsencrypt/acme.json
      dnsChallenge:
        provider: cloudflare
        delayBeforeCheck: 30
```

**Environment Variables:**
```bash
CF_API_EMAIL=admin@example.com
CF_API_KEY=your_cloudflare_api_key
```

**Supported DNS Providers:**
- Cloudflare
- AWS Route53
- Google Cloud DNS
- DigitalOcean
- And 50+ others

**Setup Steps:**
1. Get API credentials from DNS provider
2. Add to Traefik environment variables
3. Update traefik.yml with dnsChallenge config
4. Request wildcard certificate

### Custom Certificate Authorities

Use internal CA instead of Let's Encrypt:

```yaml
tls:
  certificates:
    - certFile: /certs/custom.crt
      keyFile: /certs/custom.key
```

**Steps:**
1. Generate certificate with internal CA
2. Mount cert files into Traefik container
3. Configure in traefik.yml
4. Import CA root cert into client browsers

### Load Balancing

Distribute traffic across multiple backend instances:

**Configuration:**
```yaml
http:
  services:
    my-app:
      loadBalancer:
        servers:
          - url: "http://app-1:8080"
          - url: "http://app-2:8080"
          - url: "http://app-3:8080"
        healthCheck:
          path: /health
          interval: 30s
          timeout: 5s
```

**Load Balancing Algorithms:**
- `wrr`: Weighted Round Robin (default)
- `drr`: Dynamic Round Robin

### Circuit Breaker Pattern

Prevent cascade failures:

```json
{
  "expression": "NetworkErrorRatio() > 0.30 || ResponseCodeRatio(500, 600, 0, 600) > 0.20"
}
```

**Triggers:**
- 30% network errors
- OR 20% 5xx responses

**Behavior:**
- Stops sending requests to failing service
- Returns 503 immediately
- Retries after cooldown period

### Request Retries

Automatically retry failed requests:

```json
{
  "attempts": 3,
  "initialInterval": "100ms"
}
```

**Use Cases:**
- Transient network errors
- Service temporarily unavailable
- Improves reliability

### IP Whitelisting

Restrict access by source IP:

```json
{
  "sourceRange": [
    "192.168.1.0/24",
    "10.0.0.0/8"
  ]
}
```

**Use Cases:**
- Admin panels (office IP only)
- Internal APIs
- Staging environments

### Custom Error Pages

Serve custom HTML for errors:

```yaml
http:
  middlewares:
    custom-errors:
      errors:
        status:
          - "404"
          - "500-599"
        service: error-page-service
        query: /{status}.html
```

**Service:**
```yaml
services:
  error-page-service:
    loadBalancer:
      servers:
        - url: "http://error-pages:80"
```

### Metrics & Monitoring

Export metrics to Prometheus:

```yaml
metrics:
  prometheus:
    entryPoint: metrics
    addEntryPointsLabels: true
    addServicesLabels: true
```

**Grafana Dashboard:**
- Import Traefik dashboard #4475
- Monitor request rate, latency, errors
- Set up alerts for issues

---

## Summary

This guide covered:

✅ **SSL Certificate Management**: Request, monitor, and auto-renew Let's Encrypt certificates
✅ **Route Configuration**: Define traffic routing with powerful rule syntax
✅ **Middleware Setup**: Add authentication, rate limiting, compression, and more
✅ **Configuration Management**: Safely edit and backup Traefik configuration
✅ **Best Practices**: Security, performance, and operational recommendations
✅ **Troubleshooting**: Common issues and solutions
✅ **Advanced Topics**: DNS challenges, load balancing, monitoring

### Next Steps

1. **Explore the Interface**: Familiarize yourself with the tabs and features
2. **Request a Test Certificate**: Use staging environment to practice
3. **Create Your First Route**: Connect a service using the route wizard
4. **Apply Middleware**: Add rate limiting or basic auth to a route
5. **Set Up Monitoring**: Configure Prometheus metrics

### Additional Resources

- **API Reference**: `/docs/epic1.3_api_reference.md` - Programmatic access
- **Traefik Documentation**: https://doc.traefik.io/traefik/
- **Let's Encrypt**: https://letsencrypt.org/docs/
- **Ops-Center Support**: ops-support@your-domain.com

---

**Document Version**: 1.0.0
**Last Updated**: October 23, 2025
**Maintained By**: Ops-Center Documentation Team
