# Backend API Endpoint Quick Reference

**Total Endpoints**: 452
**Last Updated**: October 28, 2025

---

## Quick Navigation

- [Storage & Backup](#storage--backup-25-endpoints)
- [System Monitoring](#system-monitoring-9-endpoints)
- [Billing & Subscriptions](#billing--subscriptions-47-endpoints)
- [User Management](#user-management-24-endpoints)
- [LLM & AI](#llm--ai-104-endpoints)
- [Traefik Management](#traefik-management-27-endpoints)
- [Cloudflare](#cloudflare-16-endpoints)
- [Migration Tools](#migration-tools-20-endpoints)

---

## Storage & Backup (25 endpoints)

### Storage Management
```
GET    /api/v1/storage/info              # Storage overview
GET    /api/v1/storage/volumes            # List Docker volumes
GET    /api/v1/storage/volumes/{name}     # Volume details
POST   /api/v1/storage/cleanup            # Clean Docker/logs/cache
POST   /api/v1/storage/optimize           # Compress logs, verify
GET    /api/v1/storage/health             # Health check
```

### Backup Operations
```
GET    /api/v1/backups                    # List all backups
POST   /api/v1/backups/create             # Create backup
POST   /api/v1/backups/{id}/restore       # Restore backup
POST   /api/v1/backups/verify/{id}        # Verify integrity
DELETE /api/v1/backups/{id}               # Delete backup
GET    /api/v1/backups/{id}/download      # Download archive
GET    /api/v1/backups/config             # Get config
PUT    /api/v1/backups/config             # Update config
```

### Rclone Cloud Sync
```
POST   /api/v1/backups/rclone/configure   # Add S3/Drive/etc.
GET    /api/v1/backups/rclone/remotes     # List remotes
POST   /api/v1/backups/rclone/sync        # Sync to cloud
POST   /api/v1/backups/rclone/copy        # Copy files
POST   /api/v1/backups/rclone/move        # Move files
POST   /api/v1/backups/rclone/delete      # Delete remote files
GET    /api/v1/backups/rclone/list        # List remote files
GET    /api/v1/backups/rclone/size        # Calculate size
GET    /api/v1/backups/rclone/providers   # List 40+ providers
POST   /api/v1/backups/rclone/mount       # Mount as filesystem
POST   /api/v1/backups/rclone/check       # Test connection
```

---

## System Monitoring (9 endpoints)

```
GET    /api/v1/system/metrics             # CPU/memory/disk/network/GPU
GET    /api/v1/system/services/status     # Docker container stats
GET    /api/v1/system/processes           # Top processes
GET    /api/v1/system/temperature         # Thermal sensors
GET    /api/v1/system/health-score        # Health score 0-100
GET    /api/v1/system/alerts               # Active alerts
POST   /api/v1/system/alerts/{id}/dismiss  # Dismiss alert
GET    /api/v1/system/alerts/history       # Alert history
GET    /api/v1/system/alerts/summary       # Alert counts
```

---

## Billing & Subscriptions (47 endpoints)

### Subscriptions
```
GET    /api/v1/subscriptions/plans                    # List plans
GET    /api/v1/subscriptions/plans/{id}               # Plan details
GET    /api/v1/subscriptions/current                  # Current subscription
POST   /api/v1/subscriptions/upgrade                  # Upgrade tier
POST   /api/v1/subscriptions/downgrade                # Downgrade tier
POST   /api/v1/subscriptions/cancel                   # Cancel subscription
GET    /api/v1/subscriptions/preview-change           # Proration preview
POST   /api/v1/subscriptions/confirm-upgrade          # Confirm after payment
GET    /api/v1/subscriptions/my-access                # User's services
POST   /api/v1/subscriptions/check-access/{service}   # Check access
```

### Billing
```
GET    /api/v1/billing/invoices           # Invoice history
GET    /api/v1/billing/cycle               # Current billing cycle
GET    /api/v1/billing/payment-methods     # Payment methods
POST   /api/v1/billing/download-invoice/{id} # Download PDF
GET    /api/v1/billing/summary             # Billing stats
```

### Usage Tracking
```
GET    /api/v1/usage/current               # Current usage
GET    /api/v1/usage/history               # Usage history
GET    /api/v1/usage/by-service            # Per-service usage
GET    /api/v1/usage/export                # Export usage data
POST   /api/v1/usage/log                   # Log usage event
GET    /api/v1/usage/limits                # Quota limits
```

### Credits (21 endpoints - partial list)
```
GET    /api/v1/credits/balance             # Credit balance
POST   /api/v1/credits/add                 # Add credits
POST   /api/v1/credits/deduct              # Deduct credits
GET    /api/v1/credits/history             # Transaction history
GET    /api/v1/credits/usage               # Usage analytics
```

---

## User Management (24 endpoints)

### User CRUD
```
GET    /api/v1/admin/users                 # List users (filtering)
GET    /api/v1/admin/users/{id}            # User details
POST   /api/v1/admin/users/comprehensive   # Create user
PUT    /api/v1/admin/users/{id}            # Update user
DELETE /api/v1/admin/users/{id}            # Delete user
```

### Bulk Operations
```
POST   /api/v1/admin/users/bulk/import     # CSV import
GET    /api/v1/admin/users/export          # CSV export
POST   /api/v1/admin/users/bulk/assign-roles # Bulk roles
POST   /api/v1/admin/users/bulk/suspend    # Bulk suspend
POST   /api/v1/admin/users/bulk/delete     # Bulk delete
POST   /api/v1/admin/users/bulk/set-tier   # Bulk tier change
```

### Roles & Permissions
```
GET    /api/v1/admin/users/{id}/roles             # Get roles
POST   /api/v1/admin/users/{id}/roles/assign      # Assign role
DELETE /api/v1/admin/users/{id}/roles/{role}      # Remove role
GET    /api/v1/admin/users/roles/available        # List roles
GET    /api/v1/admin/users/roles/hierarchy        # Role hierarchy
GET    /api/v1/admin/users/roles/permissions      # Permission matrix
GET    /api/v1/admin/users/{id}/roles/effective   # Effective perms
```

### Sessions & Impersonation
```
GET    /api/v1/admin/users/{id}/sessions           # Active sessions
DELETE /api/v1/admin/users/{id}/sessions/{id}      # Revoke session
POST   /api/v1/admin/users/{id}/impersonate/start  # Start impersonation
POST   /api/v1/admin/users/{id}/impersonate/stop   # Stop impersonation
```

### Analytics
```
GET    /api/v1/admin/users/analytics/summary   # User statistics
GET    /api/v1/admin/users/{id}/activity       # Activity timeline
```

---

## LLM & AI (104 endpoints)

### LiteLLM Proxy (20 endpoints - partial list)
```
POST   /api/v1/llm/chat/completions        # OpenAI-compatible chat
GET    /api/v1/llm/models                  # List models
GET    /api/v1/llm/models/{id}             # Model details
POST   /api/v1/llm/models/deploy           # Deploy model
GET    /api/v1/llm/usage                   # Usage stats
GET    /api/v1/llm/providers               # Available providers
```

### Model Management (14 endpoints - partial list)
```
GET    /api/v1/models/catalog              # Model catalog
POST   /api/v1/models/download             # Download model
DELETE /api/v1/models/{id}                 # Remove model
GET    /api/v1/models/{id}/status          # Model status
```

### Provider Management (20 endpoints - partial list)
```
GET    /api/v1/providers/keys              # List API keys
POST   /api/v1/providers/keys              # Add API key
DELETE /api/v1/providers/keys/{id}         # Remove API key
POST   /api/v1/providers/keys/{id}/test    # Test API key
GET    /api/v1/providers/health            # Provider health
```

### BYOK (6 endpoints)
```
POST   /api/v1/byok/keys                   # Add user key (encrypted)
GET    /api/v1/byok/keys                   # List user keys
PUT    /api/v1/byok/keys/{id}              # Update key
DELETE /api/v1/byok/keys/{id}              # Remove key
POST   /api/v1/byok/keys/{id}/test         # Test key
GET    /api/v1/byok/providers              # Supported providers
```

---

## Traefik Management (27 endpoints)

### Routes
```
GET    /api/v1/traefik/routes              # List routes
POST   /api/v1/traefik/routes              # Create route
GET    /api/v1/traefik/routes/{name}       # Route details
PUT    /api/v1/traefik/routes/{name}       # Update route
DELETE /api/v1/traefik/routes/{name}       # Delete route
```

### Services
```
GET    /api/v1/traefik/services            # List services
POST   /api/v1/traefik/services            # Register service
GET    /api/v1/traefik/services/{name}     # Service details
PUT    /api/v1/traefik/services/{name}     # Update service
DELETE /api/v1/traefik/services/{name}     # Deregister service
GET    /api/v1/traefik/services/{name}/health # Health check
```

### SSL/TLS
```
GET    /api/v1/traefik/certificates        # List certificates
POST   /api/v1/traefik/certificates/request # Request Let's Encrypt
GET    /api/v1/traefik/certificates/{domain} # Certificate details
DELETE /api/v1/traefik/certificates/{domain} # Revoke certificate
POST   /api/v1/traefik/certificates/renew  # Manual renewal
```

### Middlewares
```
GET    /api/v1/traefik/middlewares         # List middlewares
POST   /api/v1/traefik/middlewares         # Create middleware
GET    /api/v1/traefik/middlewares/{name}  # Middleware details
PUT    /api/v1/traefik/middlewares/{name}  # Update middleware
DELETE /api/v1/traefik/middlewares/{name}  # Delete middleware
```

### Metrics
```
GET    /api/v1/traefik/metrics             # Request metrics
GET    /api/v1/traefik/metrics/requests    # Request rate/latency
GET    /api/v1/traefik/metrics/errors      # Error rates
GET    /api/v1/traefik/metrics/services    # Per-service metrics
GET    /api/v1/traefik/metrics/uptime      # Uptime stats
GET    /api/v1/traefik/metrics/export      # Prometheus export
```

---

## Cloudflare (16 endpoints)

### DNS Management
```
GET    /api/v1/cloudflare/zones            # List zones
GET    /api/v1/cloudflare/zones/{id}/records # DNS records
POST   /api/v1/cloudflare/zones/{id}/records # Create record
PUT    /api/v1/cloudflare/zones/{id}/records/{record_id} # Update record
DELETE /api/v1/cloudflare/zones/{id}/records/{record_id} # Delete record
```

### SSL/TLS
```
GET    /api/v1/cloudflare/ssl/{zone_id}    # SSL settings
PUT    /api/v1/cloudflare/ssl/{zone_id}    # Update SSL mode
POST   /api/v1/cloudflare/ssl/{zone_id}/origin-cert # Generate cert
```

### Firewall & CDN
```
GET    /api/v1/cloudflare/firewall/{zone_id} # Firewall rules
POST   /api/v1/cloudflare/firewall/{zone_id} # Create rule
GET    /api/v1/cloudflare/cache/{zone_id}  # Cache settings
POST   /api/v1/cloudflare/cache/{zone_id}/purge # Purge cache
GET    /api/v1/cloudflare/analytics/{zone_id} # Analytics
```

---

## Migration Tools (20 endpoints)

### Pre-migration
```
GET    /api/v1/migration/namecheap/domains # List Namecheap domains
GET    /api/v1/migration/namecheap/records/{domain} # DNS records
POST   /api/v1/migration/validate          # Validate readiness
```

### Migration Execution
```
POST   /api/v1/migration/start             # Start migration
GET    /api/v1/migration/status/{id}       # Migration status
POST   /api/v1/migration/pause/{id}        # Pause migration
POST   /api/v1/migration/resume/{id}       # Resume migration
POST   /api/v1/migration/rollback/{id}     # Rollback migration
```

### Post-migration
```
GET    /api/v1/migration/verification/{id} # Verify migration
POST   /api/v1/migration/finalize/{id}     # Finalize migration
GET    /api/v1/migration/report/{id}       # Migration report
```

### Batch Operations
```
POST   /api/v1/migration/batch/start       # Batch migration
GET    /api/v1/migration/batch/status/{id} # Batch status
POST   /api/v1/migration/batch/schedule    # Schedule migration
GET    /api/v1/migration/history           # Migration history
```

---

## Organizations (10 endpoints)

```
GET    /api/v1/organizations               # List organizations
POST   /api/v1/organizations               # Create organization
GET    /api/v1/organizations/{id}          # Organization details
PUT    /api/v1/organizations/{id}          # Update organization
DELETE /api/v1/organizations/{id}          # Delete organization
GET    /api/v1/organizations/{id}/members  # List members
POST   /api/v1/organizations/{id}/invite   # Invite member
DELETE /api/v1/organizations/{id}/members/{user_id} # Remove member
PUT    /api/v1/organizations/{id}/members/{user_id}/role # Update role
GET    /api/v1/organizations/{id}/billing  # Billing info
```

---

## Security & Auth (35+ endpoints)

### Firewall (12 endpoints)
```
GET    /api/v1/firewall/rules              # List rules
POST   /api/v1/firewall/rules              # Create rule
PUT    /api/v1/firewall/rules/{id}         # Update rule
DELETE /api/v1/firewall/rules/{id}         # Delete rule
POST   /api/v1/firewall/rules/{id}/enable  # Enable rule
POST   /api/v1/firewall/rules/{id}/disable # Disable rule
```

### Credentials (8 endpoints)
```
GET    /api/v1/credentials                 # List credentials
POST   /api/v1/credentials                 # Store credential
GET    /api/v1/credentials/{id}            # Retrieve credential
PUT    /api/v1/credentials/{id}            # Update credential
DELETE /api/v1/credentials/{id}            # Delete credential
POST   /api/v1/credentials/{id}/rotate     # Rotate credential
```

### Keycloak Status (6 endpoints)
```
GET    /api/v1/keycloak/status             # Keycloak status
GET    /api/v1/keycloak/realms             # List realms
GET    /api/v1/keycloak/clients            # List clients
GET    /api/v1/keycloak/identity-providers # List IdPs
POST   /api/v1/keycloak/sync-users         # Sync users
GET    /api/v1/keycloak/config             # Configuration
```

---

## Email & Notifications (19 endpoints)

### Email Provider (9 endpoints)
```
GET    /api/v1/email/providers             # List providers
POST   /api/v1/email/providers             # Add provider
GET    /api/v1/email/providers/{id}        # Provider details
PUT    /api/v1/email/providers/{id}        # Update provider
DELETE /api/v1/email/providers/{id}        # Delete provider
POST   /api/v1/email/providers/{id}/test   # Test provider
GET    /api/v1/email/providers/active      # Active provider
POST   /api/v1/email/providers/{id}/activate # Activate provider
GET    /api/v1/email/providers/supported   # Supported types
```

### Email Notifications (10 endpoints)
```
POST   /api/v1/notifications/send          # Send notification
GET    /api/v1/notifications/templates     # List templates
POST   /api/v1/notifications/templates     # Create template
PUT    /api/v1/notifications/templates/{id} # Update template
DELETE /api/v1/notifications/templates/{id} # Delete template
GET    /api/v1/notifications/history       # Notification history
GET    /api/v1/notifications/config        # Notification config
PUT    /api/v1/notifications/config        # Update config
POST   /api/v1/notifications/test          # Test notification
GET    /api/v1/notifications/status/{id}   # Notification status
```

---

## Additional APIs

### Platform Settings (5 endpoints)
```
GET    /api/v1/platform/settings           # Platform settings
PUT    /api/v1/platform/settings           # Update settings
GET    /api/v1/platform/features           # Feature flags
PUT    /api/v1/platform/features/{id}      # Toggle feature
GET    /api/v1/platform/deployment         # Deployment config
```

### Testing Lab (4 endpoints)
```
POST   /api/v1/testing/scenario            # Create test scenario
GET    /api/v1/testing/scenarios           # List scenarios
POST   /api/v1/testing/execute/{id}        # Execute test
GET    /api/v1/testing/results/{id}        # Test results
```

### Tier Check (6 endpoints)
```
GET    /api/v1/tier/check                  # Check user tier
GET    /api/v1/tier/limits                 # Get tier limits
POST   /api/v1/tier/validate               # Validate access
GET    /api/v1/tier/upgrade-path           # Upgrade options
POST   /api/v1/tier/request-upgrade        # Request upgrade
GET    /api/v1/tier/comparison             # Compare tiers
```

---

**Full Audit Report**: `/home/muut/Production/UC-Cloud/services/ops-center/BACKEND_AUDIT_REPORT.md`
**Summary**: `/home/muut/Production/UC-Cloud/services/ops-center/BACKEND_AUDIT_SUMMARY.md`

**Total Endpoints**: 452
**Backend Completion**: 92%
**Last Updated**: October 28, 2025
