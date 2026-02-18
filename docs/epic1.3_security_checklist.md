# Epic 1.3: Traefik Configuration Management - Security Implementation Checklist

**Date**: October 23, 2025
**Epic**: 1.3 - Traefik Configuration Management
**Purpose**: Practical security checklist for implementation team

---

## Critical Priority (P0) - MUST BE IMPLEMENTED BEFORE ANY DEPLOYMENT

### 1. Authentication & Authorization

- [ ] **Replace placeholder authentication** in `traefik_routes_api.py`, `traefik_ssl_manager.py`, `traefik_middlewares_api.py`, `traefik_services_api.py`
  ```python
  # CURRENT (INSECURE):
  def require_admin(user_info: Dict = Depends(lambda: {"role": "admin", "username": "admin"})):
      # TODO: Replace with actual Keycloak authentication

  # REQUIRED:
  from keycloak import KeycloakOpenID
  async def require_admin(authorization: str = Header(None)):
      # Verify JWT token with Keycloak
      # Check for admin role
      # Return user info
  ```

- [ ] **Add session management**
  - 30-minute idle timeout
  - 8-hour maximum session duration
  - Session invalidation on logout

- [ ] **Implement API key authentication** for programmatic access
  - Generate secure random keys (32+ characters)
  - Hash keys with bcrypt before storage
  - Support key rotation

**Files to Modify**:
- `backend/traefik_routes_api.py` (Line 79-84)
- `backend/traefik_ssl_manager.py` (Line 54-58)
- `backend/traefik_middlewares_api.py` (Line 49-53)
- `backend/traefik_services_api.py` (similar pattern)

**Acceptance Criteria**:
- ✅ All Traefik endpoints return 401 without valid Keycloak token
- ✅ Only users with "admin" role can access endpoints
- ✅ Invalid tokens are rejected with appropriate error messages
- ✅ Authentication failures are logged to audit log

---

### 2. SSL Certificate Protection

- [ ] **Encrypt acme.json at rest**

**Option A: LUKS Filesystem Encryption** (Recommended)
```bash
# Create encrypted partition
sudo dd if=/dev/zero of=/home/traefik-encrypted.img bs=1M count=1024
sudo cryptsetup luksFormat /home/traefik-encrypted.img
sudo cryptsetup luksOpen /home/traefik-encrypted.img traefik_secure
sudo mkfs.ext4 /dev/mapper/traefik_secure
sudo mkdir /secure/traefik
sudo mount /dev/mapper/traefik_secure /secure/traefik

# Move acme.json to encrypted partition
sudo mv /home/deploy/Infrastructure/traefik/acme/acme.json /secure/traefik/
sudo ln -s /secure/traefik/acme.json /home/deploy/Infrastructure/traefik/acme/acme.json

# Update Traefik docker-compose.yml
volumes:
  - /secure/traefik/acme.json:/acme/acme.json
```

**Option B: Application-Level Encryption**
```python
# Implement in backend/traefik_ssl_manager.py
from cryptography.fernet import Fernet

class EncryptedACMEStorage:
    def __init__(self, key_file="/secure/acme.key"):
        # Load encryption key
        # Encrypt/decrypt acme.json on read/write
```

- [ ] **Set correct file permissions**
  ```bash
  sudo chmod 0400 /home/deploy/Infrastructure/traefik/acme/acme.json
  sudo chown muut:traefik-admin /home/deploy/Infrastructure/traefik/acme/acme.json
  ```

**Acceptance Criteria**:
- ✅ acme.json is encrypted at rest
- ✅ File permissions are 0400 (owner read-only)
- ✅ Encryption key is stored securely (not in code/environment)
- ✅ Traefik can still read certificates (decryption works)

---

### 3. Secure Backups

- [ ] **Implement encrypted backups** in `traefik_config_manager.py`

```python
# Update backup_config() method
async def backup_config(self, filename: Optional[str] = None) -> str:
    """Create encrypted backup"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_id = f"backup_{timestamp}"

    # Create tar.gz archive
    import tarfile
    from io import BytesIO

    tar_buffer = BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
        for yaml_file in self.dynamic_dir.glob("*.yml"):
            tar.add(yaml_file, arcname=yaml_file.name)

    # Encrypt with Fernet
    from cryptography.fernet import Fernet
    encryption_key = os.getenv("BACKUP_ENCRYPTION_KEY")  # Load from secure location
    fernet = Fernet(encryption_key)
    encrypted_data = fernet.encrypt(tar_buffer.getvalue())

    # Write encrypted backup
    backup_path = self.backup_dir / f"{backup_id}.enc.tar.gz"
    with open(backup_path, 'wb') as f:
        f.write(encrypted_data)

    os.chmod(backup_path, 0o400)  # Read-only

    return backup_id
```

- [ ] **Set correct backup directory permissions**
  ```bash
  sudo chmod 0700 /home/deploy/Infrastructure/traefik/backups
  ```

- [ ] **Implement backup retention policy**
  - Keep daily backups for 7 days
  - Keep weekly backups for 4 weeks
  - Keep monthly backups for 12 months

**Acceptance Criteria**:
- ✅ All backups are encrypted
- ✅ Backup files have 0400 permissions
- ✅ Old backups are automatically deleted per retention policy
- ✅ Backup operations are logged to audit log

---

## High Priority (P1) - IMPLEMENT IN FIRST RELEASE

### 4. Enhanced Route Validation

- [ ] **Add internal service protection** in `traefik_routes_api.py`

```python
# Add at top of file
INTERNAL_SERVICES = [
    "unicorn-postgresql", "unicorn-redis", "uchub-keycloak",
    "unicorn-lago-api", "unicorn-lago-postgres", "unicorn-brigade",
    "ops-center-direct", "docker-socket-proxy"
]

INTERNAL_IP_RANGES = [
    "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.20.",
    "192.168.", "127.", "localhost"
]

ALLOWED_DOMAINS = [
    "unicorncommander.ai",
    "*.unicorncommander.ai"
]

# Update create_route() function
@router.post("", response_model=RouteInfo)
async def create_route(route: RouteCreate, admin: Dict = Depends(require_admin)):
    # SECURITY: Validate route doesn't expose internal services
    if route.service in INTERNAL_SERVICES:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot expose internal service: {route.service}"
        )

    # SECURITY: Check for internal IP addresses
    for ip_range in INTERNAL_IP_RANGES:
        if ip_range in route.service:
            raise HTTPException(
                status_code=400,
                detail="Cannot route to internal IP address"
            )

    # SECURITY: Validate domain ownership
    domain_valid = False
    for allowed in ALLOWED_DOMAINS:
        if allowed.startswith("*"):
            base = allowed.replace("*.", "")
            if base in route.rule:
                domain_valid = True
                break
        elif allowed in route.rule:
            domain_valid = True
            break

    if not domain_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Domain in rule must be under unicorncommander.ai"
        )

    # ... continue with existing route creation logic
```

**Acceptance Criteria**:
- ✅ Cannot create route to `unicorn-postgresql`
- ✅ Cannot create route to `http://172.20.0.5:5432`
- ✅ Cannot create route for `attacker.com`
- ✅ Can create route for `api.unicorncommander.ai`

---

### 5. Docker Socket Isolation

- [ ] **Deploy Docker Socket Proxy**

```yaml
# Add to docker-compose.direct.yml
services:
  docker-socket-proxy:
    image: tecnativa/docker-socket-proxy
    container_name: docker-socket-proxy
    restart: unless-stopped
    environment:
      CONTAINERS: 1     # Allow container listing
      SERVICES: 0       # Deny service access
      TASKS: 0          # Deny task access
      NETWORKS: 1       # Allow network listing
      VOLUMES: 0        # Deny volume access
      EVENTS: 0         # Deny event stream
      POST: 0           # Deny write operations
      DELETE: 0         # Deny delete operations
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - unicorn-network

  ops-center-direct:
    # Remove direct socket mount
    # volumes:
    #   - /var/run/docker.sock:/var/run/docker.sock:ro  # REMOVE THIS

    environment:
      # Use socket proxy instead
      DOCKER_HOST: tcp://docker-socket-proxy:2375
```

**Acceptance Criteria**:
- ✅ Ops-Center cannot access `/var/run/docker.sock` directly
- ✅ Ops-Center can list containers via proxy
- ✅ Ops-Center cannot create/delete containers
- ✅ Socket proxy logs all access attempts

---

### 6. Rate Limiting

- [ ] **Add per-endpoint rate limits** using `fastapi-limiter`

```bash
# Install dependency
pip install fastapi-limiter redis
```

```python
# In backend/server.py
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis

@app.on_event("startup")
async def startup():
    redis_client = redis.from_url("redis://unicorn-redis:6379", encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_client)

# In traefik_routes_api.py
@router.post("", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def create_route(...):
    """Create route - limited to 10 per minute per user"""
    pass

@router.delete("/{route_id}", dependencies=[Depends(RateLimiter(times=20, seconds=60))])
async def delete_route(...):
    """Delete route - limited to 20 per minute per user"""
    pass
```

- [ ] **Add Let's Encrypt rate limit protection**

```python
# In traefik_ssl_manager.py
class CertificateRateLimiter:
    def __init__(self):
        self.cert_requests = {}

    async def check_rate_limit(self, domain: str):
        """Enforce Let's Encrypt rate limits proactively"""
        # 50 certs per week, but enforce limit of 40 to leave buffer
        week_ago = datetime.now() - timedelta(days=7)
        recent_count = len([
            ts for ts in self.cert_requests.get(domain, [])
            if ts > week_ago
        ])

        if recent_count >= 40:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit: approaching Let's Encrypt weekly limit for {domain}"
            )

        # Record this request
        if domain not in self.cert_requests:
            self.cert_requests[domain] = []
        self.cert_requests[domain].append(datetime.now())
```

**Acceptance Criteria**:
- ✅ Routes API returns 429 after 10 requests in 1 minute
- ✅ Certificate requests blocked after 40 in 1 week per domain
- ✅ Rate limit resets work correctly
- ✅ Rate limit headers included in responses

---

### 7. CSRF Protection

- [ ] **Add CSRF tokens** using `fastapi-csrf-protect`

```bash
pip install fastapi-csrf-protect
```

```python
# In backend/server.py
from fastapi_csrf_protect import CsrfProtect

class CsrfSettings(BaseModel):
    secret_key: str = os.getenv("CSRF_SECRET_KEY")
    cookie_samesite: str = "strict"
    cookie_secure: bool = True

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

# In traefik_routes_api.py
@router.post("")
async def create_route(
    route: RouteCreate,
    admin: Dict = Depends(require_admin),
    csrf_protect: CsrfProtect = Depends()
):
    await csrf_protect.validate_csrf(request)
    # ... route creation logic
```

**Acceptance Criteria**:
- ✅ POST/PUT/DELETE requests require CSRF token
- ✅ Requests without CSRF token return 403
- ✅ CSRF tokens are unique per session
- ✅ CSRF tokens expire after 1 hour

---

## Medium Priority (P2) - IMPLEMENT AFTER LAUNCH

### 8. Enhanced Audit Logging

- [ ] **Log all configuration file access**

```python
# In traefik_config_manager.py
async def get_config_file(self, filename: str) -> Dict[str, Any]:
    # Log read access
    await audit_logger.log_action(
        action="traefik.config.read",
        user_id=current_user.id,  # Get from context
        resource_type="traefik_config",
        resource_id=filename,
        details={"filename": filename}
    )

    # ... existing code
```

- [ ] **Log SSL certificate access**

```python
# In traefik_ssl_manager.py
@router.get("/certificates", response_model=List[Certificate])
async def list_certificates(admin: Dict = Depends(require_admin)):
    # SECURITY: Log SSL access (critical security event)
    await audit_logger.log_action(
        action="ssl.certificate.list",
        user_id=admin.get("username"),
        resource_type="ssl_certificate",
        resource_id="all",
        details={"severity": "high"}
    )

    # Send immediate alert
    await send_security_alert(
        severity="high",
        event="SSL certificate access",
        user=admin.get("username")
    )

    # ... existing code
```

**Acceptance Criteria**:
- ✅ All config file reads/writes are logged
- ✅ SSL certificate access triggers alerts
- ✅ Failed operations are logged
- ✅ Audit logs include user ID, IP, timestamp

---

### 9. File Permissions Hardening

- [ ] **Set correct permissions** on all Traefik files

```bash
#!/bin/bash
# scripts/set_traefik_permissions.sh

# Create dedicated group
sudo groupadd traefik-admin
sudo usermod -a -G traefik-admin muut

# Set directory permissions
sudo chmod 0750 /home/deploy/Infrastructure/traefik/acme
sudo chmod 0750 /home/deploy/Infrastructure/traefik/dynamic
sudo chmod 0700 /home/deploy/Infrastructure/traefik/backups

# Set file permissions
sudo chmod 0400 /home/deploy/Infrastructure/traefik/acme/acme.json
sudo find /home/deploy/Infrastructure/traefik/dynamic -name "*.yml" -exec chmod 0640 {} \;

# Set ownership
sudo chown -R muut:traefik-admin /home/deploy/Infrastructure/traefik/

# Verify
echo "Verifying permissions..."
ls -la /home/deploy/Infrastructure/traefik/acme/
ls -la /home/deploy/Infrastructure/traefik/dynamic/
ls -la /home/deploy/Infrastructure/traefik/backups/

echo "✅ Permissions set successfully"
```

**Acceptance Criteria**:
- ✅ acme.json has permissions 0400
- ✅ Dynamic configs have permissions 0640
- ✅ Backup directory has permissions 0700
- ✅ All files owned by muut:traefik-admin

---

### 10. Monitoring & Alerting

- [ ] **Set up security alerts**

```python
# In backend/security_alerts.py
import os
import requests
import smtplib
from email.mime.text import MIMEText

class SecurityAlertManager:
    async def send_critical_alert(self, event: str, details: Dict):
        """Send immediate security alert"""

        # Email alert
        await self._send_email(
            to=["security@unicorncommander.ai"],
            subject=f"🚨 SECURITY ALERT: {event}",
            body=f"""
            Severity: CRITICAL
            Event: {event}
            Timestamp: {datetime.now().isoformat()}
            Details: {json.dumps(details, indent=2)}
            """
        )

        # Slack alert
        await self._send_slack(
            webhook_url=os.getenv("SLACK_SECURITY_WEBHOOK"),
            message={
                "text": f":rotating_light: SECURITY ALERT: {event}",
                "attachments": [{
                    "color": "danger",
                    "fields": [
                        {"title": "Event", "value": event},
                        {"title": "Details", "value": str(details)}
                    ]
                }]
            }
        )

        # Audit log
        await audit_logger.log_action(
            action="security.alert.sent",
            user_id="system",
            resource_type="security_alert",
            resource_id=event,
            details=details
        )
```

**Acceptance Criteria**:
- ✅ Critical events send email alerts
- ✅ Critical events send Slack notifications
- ✅ Alerts include event details and timestamp
- ✅ Alert system has < 1 minute latency

---

## Testing Requirements

### Security Tests

- [ ] **Authentication bypass tests**
  ```python
  async def test_route_creation_requires_auth():
      """Verify authentication is required"""
      response = await client.post("/api/v1/traefik/routes", json={...})
      assert response.status_code == 401
  ```

- [ ] **SQL injection tests**
  ```python
  async def test_sql_injection_in_route_name():
      """Verify SQL injection is prevented"""
      route = RouteCreate(name="'; DROP TABLE routes; --", ...)
      response = await client.post("/api/v1/traefik/routes", json=route.dict())
      assert response.status_code == 400
  ```

- [ ] **Path traversal tests**
  ```python
  async def test_path_traversal_in_backup():
      """Verify path traversal is prevented"""
      response = await client.post(
          "/api/v1/traefik/backups/restore",
          json={"backup_id": "../../../etc/passwd"}
      )
      assert response.status_code == 400
  ```

- [ ] **Internal service exposure tests**
  ```python
  async def test_cannot_expose_database():
      """Verify internal services cannot be exposed"""
      route = RouteCreate(
          name="db",
          rule="Host(`db.example.com`)",
          service="unicorn-postgresql"
      )
      response = await client.post("/api/v1/traefik/routes", json=route.dict())
      assert response.status_code == 400
      assert "internal service" in response.json()["detail"].lower()
  ```

- [ ] **Rate limit tests**
  ```python
  async def test_rate_limiting():
      """Verify rate limits work"""
      for i in range(15):
          response = await client.post("/api/v1/traefik/routes", json={...})

      assert response.status_code == 429  # Too Many Requests
  ```

**Test Coverage Target**: 90%+ for security-critical functions

---

## Pre-Deployment Checklist

Before deploying to production:

- [ ] All P0 (Critical) security controls implemented
- [ ] All P1 (High) security controls implemented
- [ ] Security tests pass with 90%+ coverage
- [ ] Penetration testing completed
- [ ] Security audit sign-off obtained
- [ ] File permissions verified
- [ ] Encryption keys generated and secured
- [ ] Monitoring alerts configured
- [ ] Incident response plan documented
- [ ] Security runbook created
- [ ] Team trained on security procedures

---

## Quick Reference: Priority Mapping

| Priority | Severity | Impact | Implement By |
|----------|----------|--------|--------------|
| **P0** | Critical | System compromise | Before any deployment |
| **P1** | High | Data breach possible | First release |
| **P2** | Medium | Security weakness | Second release |
| **P3** | Low | Best practice | Future enhancement |

---

## Emergency Contacts

- **Security Team**: security@unicorncommander.ai
- **On-Call Engineer**: [PagerDuty rotation]
- **Incident Response Lead**: [Name/Contact]

---

**Document Version**: 1.0
**Last Updated**: October 23, 2025
**Maintained By**: Security Team
**Next Review**: Weekly during development

---

## Sign-Off

**Implementation Team Lead**: _____________________ Date: _____
**Security Reviewer**: _____________________ Date: _____

---

**END OF SECURITY CHECKLIST**
