# Traefik Configuration Management - User Guide

**Version**: 1.0.0
**Epic**: 1.3 - Traefik Configuration Management
**Last Updated**: October 24, 2025
**Target Audience**: System Administrators

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Getting Started](#2-getting-started)
3. [Managing SSL Certificates](#3-managing-ssl-certificates)
4. [Managing Routes](#4-managing-routes)
5. [Managing Middleware](#5-managing-middleware)
6. [Configuration Management](#6-configuration-management)
7. [Best Practices](#7-best-practices)
8. [Troubleshooting](#8-troubleshooting)
9. [FAQ](#9-faq)

---

## 1. Introduction

### 1.1 What is Traefik?

Traefik is a modern reverse proxy and load balancer designed for microservices and containerized applications. It acts as the entry point for all HTTP/HTTPS traffic to your UC-Cloud infrastructure, providing:

- **Dynamic Routing**: Automatically routes requests to backend services based on rules
- **SSL/TLS Termination**: Handles HTTPS encryption using Let's Encrypt certificates
- **Load Balancing**: Distributes traffic across multiple backend instances
- **Middleware**: Adds functionality like authentication, rate limiting, and header modification
- **Service Discovery**: Automatically detects Docker containers and configures routes

### 1.2 Why Manage Traefik via Ops-Center?

The Ops-Center Traefik Configuration Management feature provides a user-friendly web interface for managing Traefik without manually editing YAML files. Benefits include:

- **Visual Management**: Point-and-click interface for common operations
- **Error Prevention**: Built-in validation prevents configuration mistakes
- **Automatic Backups**: Every change is automatically backed up
- **Rollback Support**: Quickly restore previous configurations if needed
- **Audit Trail**: Track who made what changes and when
- **Certificate Management**: Request and manage Let's Encrypt SSL certificates
- **Real-time Updates**: Changes are applied immediately without container restarts

### 1.3 Feature Overview

The Traefik Configuration Management feature is organized into four main sections:

1. **SSL Certificates**: Request, view, and revoke Let's Encrypt SSL certificates
2. **Routes**: Define rules for routing HTTP/HTTPS traffic to backend services
3. **Middleware**: Configure authentication, rate limiting, headers, and other request processing
4. **Configuration**: Advanced YAML editor with backup and restore capabilities

---

## 2. Getting Started

### 2.1 Accessing the Feature

**URL**: https://your-domain.com/admin/system/traefik

**Prerequisites**:
- You must be logged in to Ops-Center via Keycloak SSO
- Your user account must have the `admin` or `moderator` role
- Traefik must be running (part of UC-Cloud infrastructure)

**Navigation**:
1. Log in to Ops-Center at https://your-domain.com
2. Click on **Admin** in the top navigation bar
3. Select **System** from the admin menu
4. Click **Traefik Configuration**

### 2.2 Dashboard Overview

The Traefik Configuration page has four tabs at the top:

#### SSL Certificates Tab
Shows all Let's Encrypt certificates with:
- Domain name
- Status (Valid, Expiring Soon, Expired)
- Expiry date
- Issuer information
- Actions (Revoke)

#### Routes Tab
Lists all HTTP/HTTPS routing rules with:
- Route name
- Traefik rule (e.g., `Host(\`example.com\`)`)
- Backend service
- Applied middleware
- Actions (Edit, Delete)

#### Middleware Tab
Shows configured middleware components with:
- Middleware name
- Type (Basic Auth, Rate Limit, Compress, etc.)
- Status (Active, Disabled)
- Actions (Edit, Delete)

#### Configuration Tab
Raw YAML configuration editor with:
- View/Edit configuration files
- Validate YAML syntax
- Create backups
- Restore from backups
- Reload Traefik

### 2.3 Permissions Required

**Role Requirements**:
- **Admin**: Full access to all features (create, edit, delete)
- **Moderator**: Read-only access (view only, no modifications)
- **Developer**: No access (feature requires elevated privileges)

**Authentication**:
- All API requests require a valid authentication token
- Tokens are automatically managed by the Ops-Center frontend
- Sessions expire after 24 hours of inactivity
- You'll be redirected to login if your session expires

---

## 3. Managing SSL Certificates

### 3.1 Understanding SSL Certificates

SSL/TLS certificates encrypt traffic between clients and your server. Traefik uses **Let's Encrypt** to automatically obtain free, trusted SSL certificates that work in all browsers.

**Certificate Lifecycle**:
1. **Request**: You specify a domain and contact email
2. **Validation**: Let's Encrypt verifies you control the domain (HTTP-01 challenge)
3. **Issuance**: Certificate is issued and stored in Traefik
4. **Renewal**: Traefik automatically renews certificates 30 days before expiry
5. **Expiry**: Certificates are valid for 90 days

**Certificate Status**:
- **Valid**: Certificate is active and has more than 30 days until expiry
- **Expiring Soon**: Less than 30 days until expiry (automatic renewal will occur)
- **Expired**: Certificate has expired and needs to be re-requested
- **Pending**: Certificate request is in progress (waiting for DNS propagation)

### 3.2 Viewing Certificates

**To view all certificates**:

1. Navigate to **Admin → System → Traefik Configuration**
2. Ensure the **SSL Certificates** tab is selected (default)
3. You'll see a table with all certificates

**Certificate Information Displayed**:
- **Domain**: Main domain name (e.g., `your-domain.com`)
- **Status**: Visual indicator (green = valid, yellow = expiring soon, red = expired)
- **Expiry Date**: When the certificate expires
- **Issuer**: Typically "Let's Encrypt Authority X3"
- **Actions**: Button to revoke the certificate

**Refreshing the List**:
- Click the **refresh icon** (circular arrow) in the top-right corner
- The list automatically refreshes every 60 seconds

### 3.3 Requesting a New Certificate

**Prerequisites**:
- Domain DNS must point to your server's IP address
- Domain must be publicly accessible on port 80 (for HTTP-01 validation)
- You must have a valid email address for renewal notifications

**Steps to Request a Certificate**:

1. Click the **Request Certificate** button (top-right corner)

2. In the dialog that appears, fill in:
   - **Domain**: The full domain name (e.g., `chat.your-domain.com`)
   - **Email**: Your contact email (e.g., `admin@your-domain.com`)

3. Click **Request Certificate**

4. The certificate request is submitted to Let's Encrypt

5. Traefik automatically completes the HTTP-01 challenge:
   - Let's Encrypt requests a specific file at `http://yourdomain/.well-known/acme-challenge/TOKEN`
   - Traefik serves this file automatically
   - Let's Encrypt verifies and issues the certificate

**Validation Time**:
- Typically completes in 30-60 seconds
- May take up to 5 minutes if DNS has not fully propagated
- Certificate appears in the list with "Valid" status once issued

**Common Issues**:
- **DNS not propagated**: Wait 10-15 minutes after creating DNS records
- **Port 80 blocked**: Ensure your firewall allows inbound traffic on port 80
- **Domain not publicly accessible**: Let's Encrypt cannot reach servers behind VPNs or on private networks
- **Rate limits**: Let's Encrypt limits 50 certificates per domain per week

### 3.4 Revoking a Certificate

**When to Revoke**:
- You no longer control the domain
- Private key has been compromised
- Domain is being transferred to another owner
- You want to force renewal with new settings

**Steps to Revoke**:

1. Locate the certificate in the list

2. Click the **trash icon** in the Actions column

3. Confirm the revocation in the dialog:
   - Read the warning: "This action cannot be undone!"
   - Verify the domain name is correct
   - Click **Revoke**

4. The certificate is removed from Traefik's storage

**What Happens After Revocation**:
- The certificate is immediately removed from `acme.json`
- Any routes using this certificate will fail to load over HTTPS
- Let's Encrypt is NOT notified (removal is local only)
- You can immediately request a new certificate for the same domain

**Important Notes**:
- Revocation does not add the certificate to a Certificate Revocation List (CRL)
- Browsers may continue to trust the old certificate until it expires
- For security compromises, also request revocation through Let's Encrypt directly

### 3.5 Certificate Auto-Renewal

**Automatic Renewal Process**:
- Traefik checks certificate expiry dates every 24 hours
- When a certificate has less than 30 days until expiry, renewal begins
- Renewal uses the same ACME challenge method (HTTP-01)
- New certificate replaces the old one seamlessly (zero downtime)

**Monitoring Renewals**:
- Check the **Expiry Date** column in the certificates list
- Look for certificates with "Expiring Soon" status
- Review Traefik logs for renewal activity:
  ```bash
  docker logs traefik | grep -i acme
  ```

**Renewal Failures**:
If automatic renewal fails, you'll see:
- Certificate status changes to "Expired"
- Traefik logs contain ACME error messages
- Affected domains show SSL certificate warnings in browsers

**Manual Renewal**:
If auto-renewal fails:
1. Revoke the expired certificate
2. Request a new certificate for the same domain
3. Verify DNS and port 80 accessibility

---

## 4. Managing Routes

### 4.1 Understanding Routes

A **route** (also called a router in Traefik terminology) defines how incoming HTTP/HTTPS requests are matched and forwarded to backend services.

**Route Components**:
- **Name**: Unique identifier (e.g., `ops-center-route`)
- **Rule**: Matching criteria (e.g., `Host(\`your-domain.com\`)`)
- **Service**: Backend service name (e.g., `ops-center-svc`)
- **Entry Points**: Network listeners (e.g., `web` = HTTP, `websecure` = HTTPS)
- **Middleware**: Optional processing chain (e.g., authentication, rate limiting)
- **Priority**: Order of evaluation (higher = checked first)
- **TLS**: Whether HTTPS is enabled

**How Routes Work**:
1. Client makes HTTP/HTTPS request
2. Traefik evaluates routes in priority order
3. First matching rule is selected
4. Request is forwarded to the specified backend service
5. Response is returned to the client

### 4.2 Viewing Routes

**To view all routes**:

1. Navigate to **Admin → System → Traefik Configuration**
2. Click the **Routes** tab
3. You'll see a table with all configured routes

**Route Information Displayed**:
- **Name**: Unique route identifier
- **Rule**: Traefik matching rule (e.g., `Host(\`example.com\`) && PathPrefix(\`/api\`)`)
- **Service**: Backend service name (colored chip)
- **Middleware**: List of applied middleware (outlined chips)
- **Actions**: Edit and Delete buttons

**Searching Routes**:
- Use the search box in the top-right corner
- Search matches route names and rules
- Results filter automatically as you type

**Refreshing the List**:
- Click the **Refresh** button
- Routes auto-refresh every 60 seconds when the tab is active

### 4.3 Creating a New Route

**Steps to Create a Route**:

1. Click the **Add Route** button (purple gradient button, top-left)

2. Fill in the route details:

   **Name** (required):
   - Lowercase letters, numbers, and hyphens only
   - Must be unique across all routes
   - Example: `chat-service-route`

   **Rule** (required):
   - Traefik rule syntax (see Rule Syntax section below)
   - Example: `Host(\`chat.your-domain.com\`)`
   - Can be multi-line for complex rules

   **Service** (required):
   - Select from dropdown of available backend services
   - Services are auto-discovered from Docker containers
   - Example: `unicorn-openwebui`

   **Middleware** (optional):
   - Select multiple middleware from dropdown
   - Middleware are applied in the order specified
   - Example: `rate-limit`, `auth-middleware`

3. Click **Create**

4. The route is saved to `/traefik/dynamic/routes.yml`

5. Traefik automatically detects the change and applies it (typically within 1-2 seconds)

**Verification**:
- Test the route by visiting the domain in a browser
- Check for expected behavior (correct backend service responds)
- Verify SSL certificate if using HTTPS

### 4.4 Editing a Route

**Steps to Edit a Route**:

1. Locate the route in the table

2. Click the **edit icon** (pencil) in the Actions column

3. Modify the route details:
   - **Name** is read-only (cannot be changed)
   - Update **Rule**, **Service**, or **Middleware** as needed

4. Click **Update**

5. Changes are saved and applied immediately

**Common Edit Scenarios**:
- **Change backend service**: Update the Service dropdown
- **Add authentication**: Add an auth middleware to the Middleware list
- **Modify matching rule**: Update the Rule field (e.g., add path prefix)
- **Add rate limiting**: Add a rate-limit middleware

### 4.5 Deleting a Route

**When to Delete a Route**:
- Service has been decommissioned
- Domain is no longer in use
- Route is being replaced with a new configuration

**Steps to Delete**:

1. Click the **trash icon** in the Actions column

2. Confirm deletion in the dialog

3. Route is removed from `routes.yml`

**What Happens After Deletion**:
- Incoming requests to the domain will receive 404 Not Found errors
- Backend service continues running (only the route is removed)
- SSL certificate is NOT affected (remains in `acme.json`)

**Best Practice**:
- Create a new route before deleting the old one (zero-downtime migration)
- Test the new route thoroughly
- Delete the old route only after verifying the new one works

### 4.6 Route Rule Syntax

Traefik uses a powerful rule language to match requests. Rules can be combined using `&&` (AND) and `||` (OR).

#### Basic Host Matching

Match requests to a specific domain:
```
Host(`example.com`)
```

Match requests to multiple domains:
```
Host(`example.com`, `www.example.com`)
```

Match wildcard subdomains:
```
HostRegexp(`{subdomain:[a-z]+}.example.com`)
```

#### Path Matching

Match requests starting with a path:
```
PathPrefix(`/api`)
```

Match exact path:
```
Path(`/api/users`)
```

Match multiple paths:
```
PathPrefix(`/api`, `/v1`)
```

#### Combining Rules

Host AND path:
```
Host(`example.com`) && PathPrefix(`/api`)
```

Multiple hosts OR conditions:
```
Host(`example.com`) || Host(`www.example.com`)
```

Complex combinations:
```
(Host(`example.com`) || Host(`www.example.com`)) && (PathPrefix(`/api`) || PathPrefix(`/v1`))
```

#### HTTP Method Matching

Match specific HTTP methods:
```
Method(`GET`, `POST`)
```

#### Header Matching

Match requests with specific headers:
```
Headers(`Content-Type`, `application/json`)
```

Header with regex:
```
HeadersRegexp(`User-Agent`, `.*Chrome.*`)
```

#### Query Parameter Matching

Match requests with query parameters:
```
Query(`debug`, `true`)
```

#### Examples for Common Scenarios

**Scenario 1**: Route all traffic for `chat.example.com` to OpenWebUI service
```
Host(`chat.your-domain.com`)
```

**Scenario 2**: Route API requests to backend service, web requests to frontend
```
Rule 1: Host(`example.com`) && PathPrefix(`/api`)  → backend-service
Rule 2: Host(`example.com`)                         → frontend-service
```
*Note: Set Rule 1 priority higher (e.g., 100) so it's checked first*

**Scenario 3**: Route subdomain-based tenant isolation
```
HostRegexp(`{tenant:[a-z0-9-]+}.example.com`) → multi-tenant-service
```

**Scenario 4**: Route versioned API endpoints
```
PathPrefix(`/v1`) → api-v1-service
PathPrefix(`/v2`) → api-v2-service
```

### 4.7 Route Priority

**How Priority Works**:
- Routes with **higher priority numbers** are evaluated first
- Default priority is 0
- Priority range: 0-1000

**When to Set Priority**:
- When rules overlap (e.g., `/api` and `/api/admin`)
- When more specific rules need precedence over general rules

**Example**:
```
Route 1: Host(`example.com`) && PathPrefix(`/admin`)  Priority: 100
Route 2: Host(`example.com`)                          Priority: 50
```
Request to `example.com/admin` matches Route 1 (checked first due to higher priority)

---

## 5. Managing Middleware

### 5.1 Understanding Middleware

**Middleware** adds functionality to the request/response pipeline. It processes requests before they reach the backend service and can modify responses before they're sent to the client.

**Common Middleware Types**:
1. **Basic Auth**: Username/password authentication
2. **Rate Limit**: Limit requests per client per time period
3. **Redirect**: HTTP to HTTPS redirection
4. **Compress**: Gzip compression for responses
5. **Headers**: Add/modify HTTP headers
6. **Forward Auth**: External authentication service integration
7. **Strip Prefix**: Remove path prefix before forwarding
8. **Add Prefix**: Add path prefix when forwarding
9. **IP Whitelist**: Allow only specific IP addresses

**Middleware Chain**:
Middleware can be chained together. They execute in the order specified on the route:
```
Client → Rate Limit → Basic Auth → Compress → Backend Service
```

### 5.2 Viewing Middleware

**To view all middleware**:

1. Navigate to **Admin → System → Traefik Configuration**
2. Click the **Middleware** tab
3. You'll see a table with all configured middleware

**Middleware Information Displayed**:
- **Name**: Unique middleware identifier
- **Type**: Middleware type (colored chip)
- **Status**: Active or Disabled
- **Actions**: Edit and Delete buttons

**Refreshing the List**:
- Click the **Refresh** button
- Middleware list auto-refreshes every 60 seconds

### 5.3 Creating Middleware

**Steps to Create Middleware**:

1. Click the **Add Middleware** button (purple gradient button, top-left)

2. Fill in the middleware details:

   **Name** (required):
   - Lowercase letters, numbers, and hyphens only
   - Must be unique
   - Example: `api-rate-limit`

   **Type** (required):
   - Select from dropdown:
     - Basic Auth
     - Rate Limit
     - Redirect
     - Compress
     - Headers

3. Click **Create**

**Note**: The simplified UI creates a basic middleware configuration. For advanced configuration (specific rate limits, custom headers, etc.), use the **Configuration** tab to edit the YAML directly.

### 5.4 Middleware Configuration Examples

While the UI creates basic middleware, here are common configuration patterns you can apply via the Configuration tab:

#### Rate Limiting

Limit to 100 requests per minute per client:
```yaml
http:
  middlewares:
    rate-limit:
      rateLimit:
        average: 100
        period: 1m
        burst: 50
```

#### Basic Authentication

Username/password protection (passwords must be hashed with htpasswd):
```yaml
http:
  middlewares:
    basic-auth:
      basicAuth:
        users:
          - "admin:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/"
```

To generate password hash:
```bash
htpasswd -nb admin password123
```

#### HTTPS Redirect

Force all HTTP traffic to HTTPS:
```yaml
http:
  middlewares:
    https-redirect:
      redirectScheme:
        scheme: https
        permanent: true
```

#### Compression

Enable gzip compression for responses:
```yaml
http:
  middlewares:
    compress:
      compress: {}
```

#### Custom Headers

Add security headers:
```yaml
http:
  middlewares:
    security-headers:
      headers:
        customResponseHeaders:
          X-Frame-Options: "SAMEORIGIN"
          X-Content-Type-Options: "nosniff"
          X-XSS-Protection: "1; mode=block"
          Strict-Transport-Security: "max-age=31536000"
```

#### IP Whitelist

Allow only specific IP addresses:
```yaml
http:
  middlewares:
    ip-whitelist:
      ipWhiteList:
        sourceRange:
          - "192.168.1.0/24"
          - "10.0.0.0/8"
```

#### Forward Authentication

Integrate with external auth service (e.g., Authelia, Keycloak):
```yaml
http:
  middlewares:
    forward-auth:
      forwardAuth:
        address: "http://authelia:9091/api/verify?rd=https://auth.example.com"
        trustForwardHeader: true
        authResponseHeaders:
          - "Remote-User"
          - "Remote-Groups"
```

### 5.5 Applying Middleware to Routes

**To apply middleware to a route**:

1. Edit the route (see Section 4.4)
2. In the **Middleware** dropdown, select one or more middleware
3. Click **Update**

**Middleware Execution Order**:
Middleware execute in the order they appear in the Middleware list:
```
Middleware: ["rate-limit", "basic-auth", "compress"]

Execution order:
1. Rate limit check
2. Basic authentication
3. Response compression
```

**Best Practices**:
- Apply rate limiting BEFORE authentication (prevent auth brute-force)
- Apply authentication BEFORE backend forwarding (security)
- Apply compression LAST (compress final response)

**Example Middleware Chain**:
```
Client Request
    ↓
Rate Limit (100 req/min)
    ↓
IP Whitelist (allow 10.0.0.0/8)
    ↓
Basic Auth (username/password)
    ↓
Custom Headers (security headers)
    ↓
Backend Service
    ↓
Compress (gzip response)
    ↓
Client Response
```

### 5.6 Editing Middleware

**Steps to Edit Middleware**:

1. Click the **edit icon** in the Actions column

2. Modify the middleware:
   - **Name** is read-only
   - **Type** can be changed

3. Click **Update**

**For Advanced Configuration**:
1. Go to the **Configuration** tab
2. Locate the middleware in the YAML
3. Edit the configuration directly
4. Validate and save

### 5.7 Deleting Middleware

**Before Deleting**:
- Check which routes use this middleware
- Update or remove middleware from affected routes first

**Steps to Delete**:

1. Click the **trash icon** in the Actions column
2. Confirm deletion
3. Middleware is removed from `middleware.yml`

**What Happens to Routes Using This Middleware**:
- Routes referencing the deleted middleware will fail to load
- Traefik logs will show warnings about missing middleware
- Update routes to remove the reference or point to a different middleware

---

## 6. Configuration Management

### 6.1 Understanding Configuration Files

Traefik uses two types of configuration:

**Static Configuration** (`traefik.yml`):
- Entry points (ports: 80, 443)
- Certificate resolvers (Let's Encrypt settings)
- Providers (Docker, file-based)
- Logging and metrics
- Requires Traefik restart to apply changes

**Dynamic Configuration** (`dynamic/*.yml`):
- Routes (routers)
- Services (backend definitions)
- Middleware
- TLS configurations
- Auto-reloaded by Traefik (no restart needed)

### 6.2 Viewing Configuration

**To view configuration**:

1. Navigate to **Admin → System → Traefik Configuration**
2. Click the **Configuration** tab
3. The current configuration is displayed in a dark code editor

**Configuration Display**:
- Syntax highlighted YAML
- Read-only view by default
- Scrollable for large configurations
- Monospace font for readability

### 6.3 Editing Configuration

**When to Edit Configuration**:
- Advanced settings not available in the UI
- Bulk changes to multiple routes
- Complex middleware configurations
- Fine-tuning performance settings

**Steps to Edit**:

1. Click the **Edit Config** button (purple gradient button)

2. The editor becomes editable (light text area with borders)

3. Make your changes directly in YAML

4. **Validate** your changes:
   - Click the **Validate** button
   - Wait for validation result
   - Fix any syntax errors shown

5. **Save** the configuration:
   - Click the **Save** button
   - Configuration is written to file
   - Traefik automatically reloads (1-2 seconds)

6. Verify changes:
   - Test affected routes in browser
   - Check Traefik logs for errors

**Validation Features**:
- YAML syntax checking
- Traefik-specific structure validation
- Prevents saving invalid configurations
- Shows clear error messages

**Auto-Backup**:
- Every edit automatically creates a timestamped backup
- Backups are stored in `/traefik/backups/`
- Last 10 backups are retained

### 6.4 Creating Backups

**Automatic Backups**:
- Created automatically before every edit operation
- Created before restoring from backup (safety backup)
- Timestamp format: `traefik_backup_YYYYMMDD_HHMMSS`

**Manual Backups**:

1. Click the **Backup** button (top action bar)

2. Backup is created immediately

3. Toast notification confirms success

4. Backup appears in the "Recent Backups" section

**What's Backed Up**:
- `traefik.yml` (static configuration)
- `dynamic/*.yml` (all dynamic configuration files)
- `acme.json` (SSL certificates)
- `manifest.json` (backup metadata)

**Backup Location**:
```
/home/muut/Production/UC-Cloud/traefik/backups/
  traefik_backup_20251024_150530/
    traefik.yml
    dynamic/
      routes.yml
      middleware.yml
      services.yml
    acme.json
    manifest.json
```

### 6.5 Restoring from Backup

**When to Restore**:
- Configuration error caused service outage
- Accidental deletion of critical routes
- Testing changes and need to revert
- Recovering from corruption

**Steps to Restore**:

1. Click the **Restore** button (top action bar)

2. In the dialog, select a backup from the dropdown:
   - Backups are listed by timestamp (newest first)
   - Example: `traefik_backup_20251024_150530`

3. **Warning**: Read the alert - "This will replace the current configuration!"

4. Click **Restore**

5. Restoration process:
   - Current configuration is backed up (safety backup)
   - Selected backup is extracted
   - Files are copied to their original locations
   - Traefik is reloaded

6. Verify restoration:
   - Check the Configuration tab (should show restored config)
   - Test routes to ensure they work as expected

**Safety Backup**:
- Before restoring, a safety backup of current configuration is created
- If restoration causes issues, you can restore the safety backup
- Safety backup name: `traefik_backup_YYYYMMDD_HHMMSS` (latest timestamp)

**Backup Retention**:
- Last 10 backups are kept automatically
- Older backups are automatically deleted
- Manual backups can be archived separately (see Backup Location)

### 6.6 Reloading Traefik

**When to Reload**:
- After making changes via Configuration tab
- If Traefik is not picking up dynamic configuration changes
- To force re-evaluation of all routes

**Steps to Reload**:

1. Click the **Reload Traefik** button (orange/warning color)

2. Reload is triggered via Docker healthcheck

3. Toast notification confirms success

**What Happens During Reload**:
- Traefik re-reads all configuration files
- Routes are re-evaluated
- New configurations are applied
- Existing connections are NOT dropped (graceful reload)

**Reload vs Restart**:
- **Reload**: Re-reads configuration, no downtime
- **Restart**: Restarts the Traefik container, brief downtime

**Note**: For most changes, reload is automatic. Manual reload is rarely needed unless Traefik appears "stuck" with old configuration.

### 6.7 Configuration Validation

**Validation Checks**:

**YAML Syntax**:
- Proper indentation (2 spaces per level)
- Valid YAML structure
- Quoted strings where needed
- No duplicate keys

**Traefik Structure**:
- Valid top-level keys (`http`, `tcp`, `udp`, `tls`)
- Routers must have `rule` and `service`
- Services must have `loadBalancer` with `servers`
- Middleware must have a valid type

**Common Validation Errors**:

**Invalid YAML syntax**:
```
Error: "YAML indentation error at line 15"
Fix: Check indentation is consistent (2 spaces per level)
```

**Missing required field**:
```
Error: "Router 'my-route' missing 'rule'"
Fix: Add rule field: rule: Host(`example.com`)
```

**Unknown middleware**:
```
Error: "Middleware 'unknown-mw' not found"
Fix: Create the middleware or remove reference from route
```

**Invalid rule syntax**:
```
Error: "Invalid rule syntax: Host(example.com)"
Fix: Add backticks: Host(`example.com`)
```

---

## 7. Best Practices

### 7.1 Route Design

**Use Descriptive Names**:
```
Good: ops-center-main-route
Bad: route1
```

**Organize by Service**:
```
ops-center-main-route
ops-center-api-route
brigade-frontend-route
brigade-api-route
```

**Use Consistent Naming**:
```
{service}-{purpose}-route
{service}-{purpose}-middleware
{service}-{purpose}-service
```

### 7.2 Middleware Strategy

**Apply Middleware in Logical Order**:
1. Rate limiting (first line of defense)
2. IP whitelisting (network security)
3. Authentication (user verification)
4. Authorization (permission checks)
5. Custom headers (response modification)
6. Compression (last, compress final response)

**Create Reusable Middleware**:
```yaml
# Instead of duplicating config on each route
http:
  middlewares:
    standard-security:
      chain:
        middlewares:
          - rate-limit
          - https-redirect
          - security-headers
```

**Use Specific Middleware for Specific Routes**:
```
Public routes: rate-limit, compress
API routes: rate-limit, api-auth, compress
Admin routes: rate-limit, admin-auth, ip-whitelist, compress
```

### 7.3 Certificate Management

**Request Certificates Early**:
- Request certificates during setup, not when going live
- Allows time for DNS propagation
- Lets Let's Encrypt complete validation

**Use Wildcard Certificates (When Appropriate)**:
- Request `*.example.com` for multiple subdomains
- Reduces number of certificates to manage
- Note: Wildcard certificates require DNS-01 challenge (not supported in basic UI)

**Monitor Expiry Dates**:
- Check certificates monthly
- Verify auto-renewal is working
- Set up alerts for expiry warnings

**Keep Contact Email Updated**:
- Let's Encrypt sends expiry notifications to this email
- Use a monitored email address
- Use a team alias, not personal email

### 7.4 Backup Strategy

**Backup Before Major Changes**:
- Creating multiple routes at once
- Editing middleware configurations
- Modifying the static configuration

**Test in Development First**:
- Set up a test Traefik instance
- Test configuration changes
- Deploy to production after verification

**Document Your Changes**:
- Add comments to YAML explaining complex rules
- Keep a changelog of major configuration changes
- Note the reason for each middleware application

**Archive Important Backups**:
```bash
# Copy backup to archive location
cp -r /traefik/backups/traefik_backup_20251024_150530 \
      /archive/traefik-backups/
```

### 7.5 Security Best Practices

**Use HTTPS Everywhere**:
- Redirect all HTTP to HTTPS
- Apply HTTPS redirect middleware globally

**Implement Rate Limiting**:
- Protect all public endpoints from abuse
- Use stricter limits for sensitive endpoints (login, registration)

**Add Security Headers**:
```yaml
X-Frame-Options: SAMEORIGIN          # Prevent clickjacking
X-Content-Type-Options: nosniff      # Prevent MIME sniffing
X-XSS-Protection: 1; mode=block      # Enable XSS protection
Strict-Transport-Security: max-age=31536000  # Force HTTPS
```

**Restrict Admin Access**:
- Use IP whitelisting for admin panels
- Require authentication for sensitive routes
- Use forward auth with external auth provider (Keycloak, Authelia)

**Regularly Review Routes**:
- Monthly audit of all routes
- Remove unused routes
- Verify middleware is correctly applied

### 7.6 Performance Optimization

**Use HTTP/2**:
- Automatically enabled with HTTPS
- Improves performance for multi-resource pages

**Enable Compression**:
- Apply compression middleware to all routes
- Reduces bandwidth usage
- Improves page load times

**Set Appropriate Rate Limits**:
- Too strict: legitimate users blocked
- Too loose: allows abuse
- Monitor actual traffic and adjust

**Use Connection Pooling**:
- Configure backend services to handle persistent connections
- Reduces connection overhead

**Monitor Performance**:
- Use Traefik metrics (Prometheus integration)
- Track request latency
- Identify bottlenecks

---

## 8. Troubleshooting

### 8.1 Certificate Issues

#### Certificate Not Issued

**Symptoms**:
- Certificate shows "Pending" status for more than 5 minutes
- Domain shows SSL certificate error in browser

**Causes & Solutions**:

**DNS not propagated**:
```bash
# Check if DNS resolves to your server
dig +short example.com

# Should return your server's IP address
# If not, wait 10-15 minutes for DNS propagation
```

**Port 80 not accessible**:
```bash
# Test if port 80 is reachable
curl -I http://example.com/.well-known/acme-challenge/test

# Should return 404 Not Found (Traefik responds)
# If connection timeout, check firewall
```

**Let's Encrypt rate limit hit**:
- Wait 1 week before requesting more certificates
- Use staging environment for testing
- Check Let's Encrypt rate limits: https://letsencrypt.org/docs/rate-limits/

#### Certificate Expired

**Symptoms**:
- Browser shows "Certificate Expired" warning
- Certificate status shows "Expired"

**Causes & Solutions**:

**Auto-renewal failed**:
```bash
# Check Traefik logs for ACME errors
docker logs traefik | grep -i acme | grep -i error

# Common errors:
# - DNS changed (update DNS)
# - Port 80 blocked (check firewall)
# - Traefik not running during renewal window (ensure uptime)
```

**Fix**:
1. Revoke the expired certificate
2. Request a new certificate
3. Verify the new certificate is issued

#### Wrong Certificate Served

**Symptoms**:
- Browser shows certificate for wrong domain
- Certificate mismatch warning

**Causes & Solutions**:

**Multiple routes with same domain**:
```bash
# Check for duplicate Host rules
grep -r "Host(\`example.com\`)" /traefik/dynamic/
```

**Fix**: Ensure each domain has only one route, or use priorities correctly

**SNI not working**:
- Check that client supports SNI (Server Name Indication)
- Modern browsers support SNI by default

### 8.2 Route Issues

#### Route Not Working (404 Not Found)

**Symptoms**:
- Accessing domain returns "404 page not found"
- Traefik dashboard shows "No routes matched"

**Troubleshooting Steps**:

**1. Verify Route Exists**:
- Check Routes tab in UI
- Confirm route is listed

**2. Check Rule Syntax**:
```
Correct: Host(`example.com`)
Wrong: Host("example.com")  # Use backticks, not quotes
Wrong: Host(example.com)    # Missing backticks
```

**3. Verify DNS**:
```bash
# Ensure DNS points to Traefik server
dig +short example.com
```

**4. Check Backend Service**:
```bash
# Verify backend service is running
docker ps | grep service-name
```

**5. Review Traefik Logs**:
```bash
docker logs traefik --tail 100 | grep -i error
```

#### Route Matches Wrong Backend

**Symptoms**:
- Request goes to wrong service
- Unexpected response or behavior

**Troubleshooting**:

**1. Check Route Priority**:
- More specific routes need higher priority
- Example: `/api/admin` (priority 100) before `/api` (priority 50)

**2. Review Rule Overlap**:
```
Route 1: Host(`example.com`)                          # Catches all
Route 2: Host(`example.com`) && PathPrefix(`/api`)    # Never matches (Route 1 matches first)

Fix: Set Route 2 priority higher than Route 1
```

**3. Test Rule Matching**:
```bash
# Enable debug logging (Configuration tab)
log:
  level: DEBUG

# Check logs to see which route matched
docker logs traefik | grep -i "matched route"
```

#### HTTPS Not Working

**Symptoms**:
- HTTPS URL times out
- Browser shows "connection refused"
- HTTP works, HTTPS doesn't

**Troubleshooting**:

**1. Verify TLS Configuration**:
- Route must have `tls` section in YAML
- Certificate must exist for the domain

**2. Check Entry Points**:
```yaml
# Route must include 'websecure' entry point
routers:
  my-route:
    rule: Host(`example.com`)
    service: my-service
    entryPoints:
      - websecure  # HTTPS
```

**3. Verify Certificate**:
```bash
# Test SSL certificate
curl -vI https://example.com

# Look for:
# - SSL certificate successfully verified
# - Certificate subject matches domain
```

**4. Check Firewall**:
```bash
# Ensure port 443 is open
sudo iptables -L -n | grep 443
```

### 8.3 Middleware Issues

#### Middleware Not Applied

**Symptoms**:
- Expected middleware behavior not occurring
- No authentication prompt when expected

**Troubleshooting**:

**1. Verify Middleware Exists**:
- Check Middleware tab
- Confirm middleware name spelling

**2. Check Route Configuration**:
```yaml
# Middleware must be listed on route
routers:
  my-route:
    rule: Host(`example.com`)
    service: my-service
    middlewares:
      - my-middleware  # Must match middleware name exactly
```

**3. Check Middleware Definition**:
```yaml
# Middleware must be properly defined
middlewares:
  my-middleware:
    basicAuth:
      users:
        - "user:hashedpassword"
```

**4. Review Logs**:
```bash
# Check for middleware errors
docker logs traefik | grep -i middleware
```

#### Rate Limit Not Working

**Symptoms**:
- Requests not being rate limited
- Can exceed configured limit

**Troubleshooting**:

**1. Verify Rate Limit Configuration**:
```yaml
middlewares:
  rate-limit:
    rateLimit:
      average: 100  # Average requests per period
      period: 1m    # Time period
      burst: 50     # Allowed burst above average
```

**2. Check Client IP Detection**:
- Rate limiting is per client IP
- If behind a load balancer, configure `X-Forwarded-For` trust

**3. Test from Different IP**:
```bash
# Make repeated requests
for i in {1..150}; do
  curl -I https://example.com
  sleep 0.1
done

# Should see 429 Too Many Requests after limit hit
```

#### Authentication Not Working

**Symptoms**:
- No authentication prompt
- Wrong username/password not rejected

**Troubleshooting**:

**1. Verify Password Hash**:
```bash
# Generate proper hash
htpasswd -nb username password

# Output should look like:
# username:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/
```

**2. Check Middleware Configuration**:
```yaml
middlewares:
  basic-auth:
    basicAuth:
      users:
        - "username:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/"
      realm: "Protected Area"
```

**3. Verify Middleware Applied to Route**:
- Check Routes tab
- Confirm `basic-auth` is listed in Middleware column

### 8.4 Configuration Issues

#### Validation Errors

**Symptoms**:
- Cannot save configuration
- "Configuration validation failed" error

**Common Errors**:

**YAML Indentation Error**:
```yaml
# Wrong (mixing spaces and tabs)
http:
  routers:
      my-route:  # 6 spaces (wrong)

# Correct (consistent 2 spaces)
http:
  routers:
    my-route:  # 2 spaces
```

**Missing Required Field**:
```yaml
# Wrong (missing 'rule')
routers:
  my-route:
    service: my-service

# Correct
routers:
  my-route:
    rule: Host(`example.com`)
    service: my-service
```

**Invalid Rule Syntax**:
```yaml
# Wrong
rule: Host("example.com")  # Double quotes

# Correct
rule: Host(`example.com`)  # Backticks
```

#### Changes Not Applied

**Symptoms**:
- Configuration saved successfully
- But changes don't take effect

**Troubleshooting**:

**1. Check Traefik Logs**:
```bash
# Look for reload confirmation
docker logs traefik | grep -i "configuration reload"
```

**2. Manual Reload**:
- Click **Reload Traefik** button
- Wait 2-3 seconds
- Test again

**3. Verify File Contents**:
```bash
# Check if file was actually written
cat /traefik/dynamic/routes.yml
```

**4. Restart Traefik (Last Resort)**:
```bash
docker restart traefik
```

### 8.5 Performance Issues

#### Slow Response Times

**Symptoms**:
- Requests take longer than expected
- Intermittent timeouts

**Troubleshooting**:

**1. Check Backend Service**:
```bash
# Test backend directly (bypass Traefik)
curl -w "@curl-format.txt" http://backend-service:8080

# curl-format.txt:
time_total: %{time_total}
time_connect: %{time_connect}
time_starttransfer: %{time_starttransfer}
```

**2. Review Middleware Chain**:
- Too many middleware can add latency
- Remove unnecessary middleware

**3. Check Rate Limiting**:
- Aggressive rate limits can cause delays
- Adjust limits or remove rate limit middleware temporarily

**4. Monitor Traefik Resources**:
```bash
# Check CPU and memory usage
docker stats traefik
```

#### High Memory Usage

**Symptoms**:
- Traefik container using excessive memory
- Server running out of memory

**Troubleshooting**:

**1. Check Certificate Cache**:
- Large number of certificates uses more memory
- Consider using wildcard certificates

**2. Review Access Logs**:
- If enabled, access logs can consume memory
- Disable or rotate logs more frequently

**3. Restart Traefik**:
```bash
# Temporary fix
docker restart traefik
```

### 8.6 Getting Help

**Check Logs**:
```bash
# Traefik logs
docker logs traefik --tail 100

# Follow logs in real-time
docker logs traefik -f

# Search for errors
docker logs traefik | grep -i error

# Search for specific route
docker logs traefik | grep "my-route"
```

**Enable Debug Logging**:
1. Go to Configuration tab
2. Add debug logging:
```yaml
log:
  level: DEBUG
```
3. Save configuration
4. Check logs for detailed information

**Verify Traefik Status**:
```bash
# Check if Traefik is running
docker ps | grep traefik

# Check Traefik healthcheck
docker exec traefik traefik healthcheck
```

**Contact Support**:
- Email: support@magicunicorn.tech
- Include:
  - Error messages
  - Relevant log snippets
  - Configuration (sanitize sensitive data)
  - Steps to reproduce

---

## 9. FAQ

### 9.1 General Questions

**Q: Do I need to restart Traefik after making changes?**

A: No. Traefik automatically reloads dynamic configuration (routes, middleware, services) within 1-2 seconds. The UI triggers a reload after each change. Only changes to `traefik.yml` (static configuration) require a restart.

**Q: Can I edit configuration files directly instead of using the UI?**

A: Yes. Traefik monitors the `/traefik/dynamic/` directory for changes. You can edit YAML files directly, and Traefik will detect and apply changes automatically. However, the UI provides validation and automatic backups.

**Q: How many routes can Traefik handle?**

A: Traefik can efficiently handle thousands of routes. Performance depends on rule complexity and server resources. For typical deployments (10-100 routes), performance impact is negligible.

**Q: Can I use Traefik with non-Docker services?**

A: Yes. Use the file provider instead of Docker provider. Define services with explicit backend URLs:
```yaml
http:
  services:
    external-service:
      loadBalancer:
        servers:
          - url: "http://192.168.1.100:8080"
```

### 9.2 Certificate Questions

**Q: How long are Let's Encrypt certificates valid?**

A: 90 days. Traefik automatically renews certificates 30 days before expiry.

**Q: Can I use custom SSL certificates instead of Let's Encrypt?**

A: Yes. Place certificate files in `/traefik/certs/` and reference them in TLS configuration:
```yaml
tls:
  certificates:
    - certFile: /traefik/certs/example.com.crt
      keyFile: /traefik/certs/example.com.key
```

**Q: Can I get wildcard certificates (*.example.com)?**

A: Yes, but requires DNS-01 challenge instead of HTTP-01. This requires configuring DNS provider credentials in `traefik.yml`. Not supported in the basic UI - requires manual configuration.

**Q: What happens if certificate renewal fails?**

A: Traefik retries renewal daily. If it continues to fail, the certificate will eventually expire, and browsers will show SSL warnings. Monitor the Certificates tab and Traefik logs for renewal issues.

### 9.3 Route Questions

**Q: Can I have multiple routes for the same domain?**

A: Yes. Use path prefixes or priorities to differentiate:
```
Route 1: Host(`example.com`) && PathPrefix(`/api`) → backend
Route 2: Host(`example.com`) → frontend
```

**Q: How do I route based on subdomain?**

A: Use separate Host rules:
```
Host(`chat.example.com`) → chat-service
Host(`api.example.com`) → api-service
```

**Q: Can routes match query parameters?**

A: Yes. Use Query matcher:
```
Host(`example.com`) && Query(`version`, `2`) → v2-service
```

**Q: What's the difference between PathPrefix and Path?**

A:
- `PathPrefix(\`/api\`)`: Matches `/api`, `/api/users`, `/api/users/123`
- `Path(\`/api\`)`: Only matches `/api` exactly

### 9.4 Middleware Questions

**Q: Can I apply multiple middleware to one route?**

A: Yes. List multiple middleware in order:
```yaml
middlewares:
  - rate-limit
  - basic-auth
  - compress
```

**Q: How do I create middleware chains?**

A: Use the chain middleware type:
```yaml
middlewares:
  security-chain:
    chain:
      middlewares:
        - https-redirect
        - rate-limit
        - security-headers
```

**Q: Can middleware modify the request before forwarding?**

A: Yes. Use stripPrefix, addPrefix, or headers middleware to modify requests.

**Q: How do I implement custom authentication?**

A: Use Forward Auth middleware pointing to your auth service (Keycloak, Authelia, custom service).

### 9.5 Backup/Restore Questions

**Q: Where are backups stored?**

A: `/home/muut/Production/UC-Cloud/traefik/backups/`

**Q: How long are backups kept?**

A: Last 10 backups are kept automatically. Older backups are deleted. To keep backups longer, manually copy them to an archive location.

**Q: What's included in a backup?**

A: Everything: `traefik.yml`, `dynamic/*.yml`, `acme.json` (certificates), and a manifest file.

**Q: Can I restore individual files from a backup?**

A: Yes. Backups are unencrypted directories. You can manually copy individual files from backup directories.

### 9.6 Performance Questions

**Q: Does Traefik add latency?**

A: Minimal. Traefik adds 1-5ms latency depending on middleware complexity. Compression middleware may add more latency but improves overall page load time.

**Q: How do I optimize Traefik performance?**

A:
- Use simple route rules (avoid complex regex)
- Limit middleware chains (remove unnecessary middleware)
- Enable HTTP/2
- Use connection pooling on backend services
- Monitor metrics and identify bottlenecks

**Q: Can Traefik handle WebSocket connections?**

A: Yes. WebSocket connections work automatically when using HTTP/HTTPS entry points. No special configuration needed.

**Q: Does Traefik support load balancing?**

A: Yes. Define multiple servers in a service:
```yaml
services:
  my-service:
    loadBalancer:
      servers:
        - url: "http://backend1:8080"
        - url: "http://backend2:8080"
```

### 9.7 Security Questions

**Q: Is it safe to expose Traefik dashboard?**

A: No. The Traefik dashboard (port 8080) should not be publicly accessible. Use IP whitelisting or forward auth to protect it.

**Q: How do I protect against DDoS?**

A: Use rate limiting middleware on all public routes. For advanced DDoS protection, use a service like Cloudflare in front of Traefik.

**Q: Can Traefik integrate with WAF (Web Application Firewall)?**

A: Not directly. Place a WAF (like ModSecurity) in front of Traefik, or use a cloud WAF service.

**Q: How are passwords stored in Basic Auth?**

A: Passwords are bcrypt hashed. Never store plaintext passwords. Use `htpasswd` to generate hashes.

---

## Appendix A: Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Refresh current tab | `Ctrl + R` or `Cmd + R` |
| Search routes | Click search box, type query |
| Save configuration | Click Save button (no keyboard shortcut) |
| Close dialog | `Esc` |

---

## Appendix B: Glossary

**ACME**: Automatic Certificate Management Environment - Protocol used by Let's Encrypt

**Backend**: The actual service that handles requests (e.g., your web application)

**Certificate Resolver**: Configuration for obtaining SSL certificates from Let's Encrypt

**Dynamic Configuration**: Configuration that can be changed without restarting Traefik

**Entry Point**: Network listener (e.g., port 80 for HTTP, port 443 for HTTPS)

**Frontend**: Synonym for route/router in older Traefik versions

**Let's Encrypt**: Free certificate authority providing SSL/TLS certificates

**Middleware**: Component that processes requests/responses in the pipeline

**Router**: See Route

**Route**: Rule that matches incoming requests and forwards to a backend service

**Rule**: Matching criteria for a route (e.g., `Host(\`example.com\`)`)

**Service**: Definition of backend servers that handle requests

**SNI**: Server Name Indication - TLS extension for multiple SSL certificates on one IP

**Static Configuration**: Configuration that requires Traefik restart to apply

**TLS**: Transport Layer Security - Protocol for encrypted HTTPS connections

---

## Appendix C: Common Error Messages

### "Configuration validation failed"
**Cause**: YAML syntax error or invalid Traefik structure
**Fix**: Check indentation, quotes, and required fields

### "Certificate request failed"
**Cause**: DNS not configured, port 80 blocked, or rate limit hit
**Fix**: Verify DNS, check firewall, wait if rate limited

### "Route already exists"
**Cause**: Attempting to create a route with a name that already exists
**Fix**: Use a different route name or edit the existing route

### "Middleware not found"
**Cause**: Route references a middleware that doesn't exist
**Fix**: Create the middleware or remove the reference

### "Service not found"
**Cause**: Route references a service that doesn't exist
**Fix**: Create the service definition or correct the service name

### "Failed to reload Traefik"
**Cause**: Traefik container not responding or not running
**Fix**: Check if Traefik container is running with `docker ps`

---

## Appendix D: Support Resources

**Documentation**:
- Traefik Official Docs: https://doc.traefik.io/traefik/
- Let's Encrypt Docs: https://letsencrypt.org/docs/
- UC-Cloud Docs: `/home/muut/Production/UC-Cloud/services/ops-center/docs/`

**Community**:
- Traefik Community Forum: https://community.traefik.io/
- Traefik GitHub: https://github.com/traefik/traefik

**Contact**:
- Email: support@magicunicorn.tech
- Website: https://your-domain.com

---

**Document Version**: 1.0.0
**Last Updated**: October 24, 2025
**Feedback**: Submit feedback to support@magicunicorn.tech
