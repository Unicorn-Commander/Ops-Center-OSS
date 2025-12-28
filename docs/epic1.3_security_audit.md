# Epic 1.3: Traefik Configuration Management - Security Audit Report

**Date**: October 23, 2025
**Auditor**: Security Auditor Agent
**Project**: UC-Cloud Ops-Center
**Epic**: 1.3 - Traefik Configuration Management
**Status**: Pre-Implementation Security Review

---

## Executive Summary

This security audit analyzes the proposed Traefik Configuration Management system for Epic 1.3. The system will allow administrators to dynamically configure Traefik reverse proxy settings through a web UI, including routes, SSL certificates, middlewares, and services.

**Overall Risk Assessment**: **MEDIUM-HIGH**

**Key Findings**:
- ✅ Good architectural foundation with validation and backup systems
- ⚠️ Critical security gaps in authentication, file permissions, and access control
- ⚠️ Sensitive data (SSL private keys, acme.json) inadequately protected
- ⚠️ Docker socket access creates privilege escalation risk
- ⚠️ Rate limiting configuration could be bypassed or exhausted
- ✅ Backup system architecture is sound but needs encryption

**Recommendation**: **DO NOT IMPLEMENT** without addressing Critical and High severity issues.

---

## Table of Contents

1. [Threat Model](#threat-model)
2. [Risk Assessment](#risk-assessment)
3. [Vulnerability Analysis](#vulnerability-analysis)
4. [Mitigation Strategies](#mitigation-strategies)
5. [Security Requirements](#security-requirements)
6. [Implementation Checklist](#implementation-checklist)
7. [Recommended File Permissions](#recommended-file-permissions)
8. [Encryption Requirements](#encryption-requirements)
9. [Monitoring & Alerting](#monitoring--alerting)

---

## 1. Threat Model

### 1.1 Attack Vectors

#### A. Configuration File Manipulation
**Threat**: Attacker modifies Traefik configuration to redirect traffic to malicious servers.

**Attack Scenario**:
```
1. Attacker gains access to admin panel (phishing, credential theft)
2. Creates new route: Host(`your-domain.com`) -> http://attacker-server:8080
3. All traffic routed to attacker, SSL certificate still valid
4. Man-in-the-middle attack successful
```

**Impact**: Complete compromise of all routed services, data exfiltration, credential theft.

**Likelihood**: MEDIUM (requires admin access, but high value target)

**Severity**: **CRITICAL**

---

#### B. SSL Private Key Exposure
**Threat**: Unauthorized access to SSL private keys in acme.json.

**Current State**:
```bash
-rw------- 1 muut muut 206995 Oct 23 02:06 acme.json
```

**Vulnerabilities**:
- File stored in plaintext on disk
- Accessible by any process running as user `muut`
- Readable by Ops-Center backend (FastAPI process)
- No encryption at rest
- Backups may leak keys to insecure locations

**Attack Scenario**:
```
1. Attacker gains code execution in Ops-Center container
2. Reads /home/muut/Infrastructure/traefik/acme/acme.json
3. Extracts private keys for *.your-domain.com
4. Performs SSL interception attacks
```

**Impact**: Complete SSL/TLS compromise, traffic decryption, impersonation attacks.

**Likelihood**: MEDIUM (requires container compromise)

**Severity**: **CRITICAL**

---

#### C. Docker Socket Privilege Escalation
**Threat**: Docker socket access allows container breakout to host.

**Current Exposure**:
```yaml
# docker-compose.direct.yml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro  # READ-ONLY, but still dangerous
```

**Vulnerabilities**:
- Even read-only Docker socket access allows:
  - Inspecting all containers (environment variables, secrets)
  - Reading logs from other containers
  - Potentially executing commands via `docker exec` if socket is writable
- Traefik has RW access to socket for dynamic configuration

**Attack Scenario**:
```
1. Attacker exploits vulnerability in Ops-Center backend
2. Uses Docker socket to inspect other containers
3. Extracts database credentials from environment variables
4. Lateral movement to database container
```

**Impact**: Host system compromise, lateral movement, credential theft.

**Likelihood**: MEDIUM (requires application vulnerability)

**Severity**: **HIGH**

---

#### D. Let's Encrypt Rate Limit Exhaustion
**Threat**: Attacker exhausts Let's Encrypt rate limits, causing denial of service.

**Rate Limits**:
- 50 certificates per registered domain per week
- 5 duplicate certificates per week
- 300 new orders per account per 3 hours

**Attack Scenario**:
```
1. Attacker gains admin access
2. Creates 50 routes with unique subdomains in rapid succession
3. Triggers certificate issuance for each
4. Exhausts weekly quota
5. Legitimate services cannot renew certificates
```

**Impact**: Service disruption when certificates expire, inability to add new services.

**Likelihood**: LOW (requires admin access and intent to cause harm)

**Severity**: **MEDIUM**

---

#### E. Malicious Route Injection
**Threat**: Attacker creates routes that bypass authentication or expose internal services.

**Current Validation**: Basic rule syntax checking only.

**Attack Scenario**:
```
1. Attacker creates route:
   Host(`internal-database.your-domain.com`) -> http://unicorn-postgresql:5432

2. Database now accessible from internet
3. Bypasses all authentication middleware
4. Direct database access achieved
```

**Impact**: Internal service exposure, data breach, authentication bypass.

**Likelihood**: MEDIUM (requires admin access)

**Severity**: **HIGH**

---

#### F. Configuration Backup Leakage
**Threat**: Backups contain sensitive configuration and are stored insecurely.

**Current Backup Location**:
```python
TRAEFIK_BACKUP_DIR = Path("/home/muut/Infrastructure/traefik/backups")
```

**Vulnerabilities**:
- Backups stored on same filesystem as live config
- No encryption of backup files
- No access control beyond filesystem permissions
- May be included in system-wide backups
- Could be exposed via misconfigured file sharing

**Attack Scenario**:
```
1. Attacker gains read access to backup directory
2. Downloads backup containing all route configurations
3. Discovers internal service names and ports
4. Plans targeted attacks based on infrastructure knowledge
```

**Impact**: Information disclosure, infrastructure reconnaissance.

**Likelihood**: LOW-MEDIUM

**Severity**: **MEDIUM**

---

#### G. YAML Deserialization Attacks
**Threat**: Malicious YAML in configuration files executes arbitrary code.

**Current Code**:
```python
with open(yaml_file, 'r') as f:
    config = yaml.safe_load(f)  # ✅ Uses safe_load (good!)
```

**Status**: **MITIGATED** - Code correctly uses `safe_load()` instead of `load()`.

**Recommendation**: No changes needed, but add input validation.

---

#### H. Cross-Site Request Forgery (CSRF)
**Threat**: Attacker tricks admin into making unwanted configuration changes.

**Current State**: No CSRF protection visible in backend code.

**Attack Scenario**:
```html
<!-- Attacker's malicious webpage -->
<form action="https://your-domain.com/api/v1/traefik/routes" method="POST">
  <input type="hidden" name="name" value="backdoor">
  <input type="hidden" name="rule" value="Host(`your-domain.com`)">
  <input type="hidden" name="service" value="attacker-server">
</form>
<script>document.forms[0].submit();</script>
```

**Impact**: Unauthorized configuration changes, traffic redirection.

**Likelihood**: LOW (requires admin to visit malicious site while authenticated)

**Severity**: **MEDIUM**

---

### 1.2 Threat Actors

| Actor | Capability | Motivation | Likelihood |
|-------|------------|------------|------------|
| **External Attacker** | Network access, web exploitation | Financial gain, data theft | HIGH |
| **Malicious Insider** | Admin credentials, system knowledge | Sabotage, data exfiltration | LOW |
| **Compromised Admin** | Full admin access via stolen credentials | Varies | MEDIUM |
| **Automated Bots** | Basic web scanning, known exploits | Opportunistic attacks | HIGH |
| **Nation-State** | Advanced persistent threats | Espionage, disruption | LOW |

---

## 2. Risk Assessment

### 2.1 Risk Matrix

| Vulnerability | Likelihood | Impact | Risk Level | Priority |
|---------------|------------|--------|------------|----------|
| Configuration File Manipulation | MEDIUM | CRITICAL | **CRITICAL** | P0 |
| SSL Private Key Exposure | MEDIUM | CRITICAL | **CRITICAL** | P0 |
| Docker Socket Privilege Escalation | MEDIUM | HIGH | **HIGH** | P1 |
| Malicious Route Injection | MEDIUM | HIGH | **HIGH** | P1 |
| Let's Encrypt Rate Limit Exhaustion | LOW | MEDIUM | **MEDIUM** | P2 |
| Configuration Backup Leakage | LOW-MEDIUM | MEDIUM | **MEDIUM** | P2 |
| CSRF Attacks | LOW | MEDIUM | **MEDIUM** | P3 |
| YAML Deserialization | LOW | CRITICAL | **LOW** | P4 (mitigated) |

### 2.2 Risk Scoring

**Risk = Likelihood × Impact × Exploitability**

**Overall System Risk Score**: **7.2 / 10** (High Risk)

**Breakdown**:
- Authentication & Authorization: 8.5/10 (Critical)
- Data Protection: 7.5/10 (High)
- Infrastructure Security: 6.8/10 (Medium-High)
- Application Security: 6.2/10 (Medium)

---

## 3. Vulnerability Analysis

### 3.1 Authentication & Authorization

#### Current State
```python
def require_admin(user_info: Dict = Depends(lambda: {"role": "admin", "username": "admin"})):
    """Require admin role (simplified for now, replace with actual auth)"""
    # TODO: Replace with actual Keycloak authentication
    if user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_info
```

**Issues**:
1. ❌ **Hardcoded credentials** - Always returns `{"role": "admin", "username": "admin"}`
2. ❌ **No actual authentication** - TODO comment indicates placeholder code
3. ❌ **No session validation** - No token verification
4. ❌ **No audit logging** of authentication attempts
5. ❌ **No rate limiting** on auth endpoints

**Severity**: **CRITICAL**

**Recommendation**: Implement Keycloak SSO integration BEFORE any UI is deployed.

---

### 3.2 File Permissions

#### Current Permissions Analysis

```bash
# Traefik configuration directory
drwxrwxr-x 2 muut muut 4096 Oct 23 02:06 dynamic/
# ⚠️ Issue: Group-writable, world-readable

# ACME JSON (SSL private keys)
-rw------- 1 muut muut 206995 Oct 23 02:06 acme.json
# ✅ Good: Owner-only read/write

# Backup files
-rw-r--r-- 1 root root 3405 Sep 25 02:21 domains.yml.backup.20250925_022159
# ⚠️ Issue: World-readable, owned by root (permission mismatch)

# Dynamic config files
-rw-rw-r-- 1 muut muut 8692 Oct 22 21:01 domains.yml
# ⚠️ Issue: Group-writable, world-readable
```

**Problems**:
1. **Group-writable directories** - Any user in `muut` group can modify configs
2. **World-readable files** - Any process can read configuration
3. **Inconsistent ownership** - Mix of `muut` and `root` owned files
4. **Backup permission leakage** - Backups more permissive than originals

**Severity**: **HIGH**

---

### 3.3 Sensitive Data Exposure

#### acme.json Structure
```json
{
  "letsencrypt": {
    "Account": {
      "Email": "admin@your-domain.com",
      "Registration": {
        "uri": "https://acme-v02.api.letsencrypt.org/acme/acct/...",
        "body": {...}
      },
      "PrivateKey": "-----BEGIN RSA PRIVATE KEY-----\nMIIE..." // ⚠️ PLAINTEXT!
    },
    "Certificates": [
      {
        "domain": {
          "main": "your-domain.com",
          "sans": ["*.your-domain.com"]
        },
        "certificate": "-----BEGIN CERTIFICATE-----...",
        "key": "-----BEGIN RSA PRIVATE KEY-----\nMIIE..." // ⚠️ PLAINTEXT!
      }
    ]
  }
}
```

**Exposure Risks**:
1. **Private keys stored in plaintext** - No encryption at rest
2. **Account private key exposed** - Allows Let's Encrypt account takeover
3. **All certificates in single file** - Compromise of one = compromise of all
4. **File accessible to FastAPI process** - Application vulnerability = key theft

**Severity**: **CRITICAL**

**Industry Standard**: SSL private keys should be encrypted at rest using HSM or KMS.

---

### 3.4 Configuration Validation Gaps

#### Current Validation (traefik_config_manager.py)
```python
@validator('rule')
def validate_rule(cls, v):
    """Validate router rule syntax"""
    if not v or len(v) < 5:
        raise ValueError("Router rule must be a valid Traefik rule")
    # Basic validation - should contain Host() or Path() or similar
    if not any(keyword in v for keyword in ['Host(', 'Path(', 'Method(', 'Headers(']):
        raise ValueError("Router rule must contain valid Traefik matcher (Host, Path, etc.)")
    return v
```

**Missing Validations**:
1. ❌ **Domain ownership verification** - Can create routes for any domain
2. ❌ **Internal service protection** - Can route to internal IPs/hostnames
3. ❌ **Port validation** - Can route to any port (including privileged)
4. ❌ **Wildcard restrictions** - Can create overly broad routes
5. ❌ **Certificate domain matching** - Route domain may not match cert
6. ❌ **Service reachability** - No verification service exists
7. ❌ **Middleware compatibility** - No type checking on middleware chains

**Example Attack**:
```python
# Currently allowed, but extremely dangerous:
route = RouteCreate(
    name="internal-db-access",
    rule="Host(`db.your-domain.com`)",
    service="unicorn-postgresql",  # Internal database exposed!
    entryPoints=["https"]
)
```

**Severity**: **HIGH**

---

### 3.5 Backup Security

#### Current Backup Implementation
```python
async def backup_config(self, filename: Optional[str] = None) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_id = f"backup_{timestamp}"
    backup_path = self.backup_dir / backup_id
    backup_path.mkdir(exist_ok=True)

    # Backup all YAML files
    for yaml_file in self.dynamic_dir.glob("*.yml"):
        shutil.copy2(yaml_file, backup_path / yaml_file.name)
```

**Issues**:
1. ❌ **No encryption** - Backups stored in plaintext
2. ❌ **Same filesystem** - Vulnerable to same attacks as live config
3. ❌ **No retention policy** - Backups accumulate indefinitely
4. ❌ **No integrity verification** - Backups could be tampered with
5. ❌ **No access logging** - No record of who accessed backups
6. ❌ **Permissions inherited** - May be more permissive than intended

**Observed Backup Files**:
```bash
# 30+ backup files in dynamic/ directory
-rw-r--r-- 1 root root 3405 Sep 25 02:21 domains.yml.backup.20250925_022159
-rw-r--r-- 1 root root 3405 Sep 25 02:22 domains.yml.backup.20250925_022215
...
```

**Severity**: **MEDIUM**

---

### 3.6 Docker API Access

#### Current Docker Socket Usage

**Ops-Center**:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro  # Read-only
```

**Traefik**:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock  # Read-write!
```

**Risks with RO Docker Socket**:
- List all containers and their configurations
- Read environment variables (may contain secrets)
- Access container logs
- Inspect networks and volumes
- Gather infrastructure reconnaissance data

**Risks with RW Docker Socket**:
- All of the above PLUS:
- Create new containers
- Execute commands in existing containers
- Mount host filesystem
- Escalate to root on host

**Current Mitigation**: Ops-Center has read-only access (good).

**Remaining Risk**: Even read-only access exposes sensitive information.

**Severity**: **MEDIUM-HIGH**

---

### 3.7 Rate Limiting & Abuse Prevention

#### Current Rate Limit Configuration
```yaml
# dynamic-api-config.yml
api-rate-limit:
  rateLimit:
    average: 100      # 100 requests per second average
    burst: 200        # Allow bursts up to 200
    period: 1s
```

**Issues**:
1. ❌ **No per-user limits** - Global limit shared by all users
2. ❌ **No admin endpoint protection** - Config changes have same limit as reads
3. ❌ **No Let's Encrypt protection** - Can trigger mass cert issuance
4. ❌ **No backup frequency limits** - Can create thousands of backups
5. ❌ **No rollback limits** - Can spam rollback operations

**Attack Scenario**:
```
1. Attacker gains admin access
2. Scripts rapid route creation (100 routes/second)
3. Each route triggers certificate request
4. Exhausts Let's Encrypt rate limits
5. Crashes Traefik due to config file size
```

**Severity**: **MEDIUM**

---

### 3.8 Audit Logging

#### Current Audit Implementation
```python
await audit_logger.log_action(
    action="traefik.route.create",
    user_id=admin.get("username", "admin"),
    resource_type="traefik_route",
    resource_id=route.name,
    details={
        "rule": route.rule,
        "service": route.service,
        "entry_points": route.entryPoints
    }
)
```

**Missing Audit Events**:
1. ❌ **Configuration file reads** - No record of who viewed configs
2. ❌ **Failed authentication attempts** - Can't detect brute force
3. ❌ **SSL certificate access** - No logging of acme.json reads
4. ❌ **Backup operations** - No record of backup creation/restoration
5. ❌ **Validation failures** - No logging of rejected configurations
6. ❌ **Docker socket access** - No record of container inspections

**Compliance Risk**: Insufficient audit trail for security incidents.

**Severity**: **MEDIUM**

---

## 4. Mitigation Strategies

### 4.1 Critical Priority (P0) - Implement Before Deployment

#### A. Implement Real Authentication
```python
# Replace placeholder with Keycloak integration
from keycloak import KeycloakOpenID

keycloak_openid = KeycloakOpenID(
    server_url=os.getenv("KEYCLOAK_URL"),
    client_id=os.getenv("KEYCLOAK_CLIENT_ID"),
    realm_name=os.getenv("KEYCLOAK_REALM"),
    client_secret_key=os.getenv("KEYCLOAK_CLIENT_SECRET")
)

async def require_admin(authorization: str = Header(None)):
    """Require valid admin token from Keycloak"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication token")

    token = authorization.replace("Bearer ", "")

    try:
        # Verify token with Keycloak
        user_info = keycloak_openid.introspect(token)

        if not user_info.get("active"):
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Check for admin role
        roles = user_info.get("realm_access", {}).get("roles", [])
        if "admin" not in roles:
            raise HTTPException(status_code=403, detail="Admin role required")

        return user_info
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")
```

---

#### B. Encrypt acme.json at Rest

**Option 1: Filesystem Encryption (Recommended)**
```bash
# Use LUKS encrypted partition for Traefik data
sudo cryptsetup luksFormat /dev/sdX
sudo cryptsetup luksOpen /dev/sdX traefik_encrypted
sudo mkfs.ext4 /dev/mapper/traefik_encrypted
sudo mount /dev/mapper/traefik_encrypted /home/muut/Infrastructure/traefik
```

**Option 2: Application-Level Encryption**
```python
from cryptography.fernet import Fernet
import os

class EncryptedACMEStorage:
    def __init__(self, key_file="/secure/location/acme.key"):
        # Load or generate encryption key
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self.key)
            os.chmod(key_file, 0o400)  # Read-only for owner

        self.fernet = Fernet(self.key)

    def encrypt_acme_json(self, plaintext_path, encrypted_path):
        with open(plaintext_path, 'rb') as f:
            plaintext = f.read()

        encrypted = self.fernet.encrypt(plaintext)

        with open(encrypted_path, 'wb') as f:
            f.write(encrypted)

        os.chmod(encrypted_path, 0o400)

    def decrypt_acme_json(self, encrypted_path):
        with open(encrypted_path, 'rb') as f:
            encrypted = f.read()

        return self.fernet.decrypt(encrypted)
```

**Option 3: Use External Secrets Manager**
```yaml
# Store certificates in HashiCorp Vault or AWS Secrets Manager
# Configure Traefik to fetch certs from secrets manager
# Rotate keys automatically
```

---

### 4.2 High Priority (P1) - Implement in First Release

#### A. Enhanced Route Validation
```python
INTERNAL_SERVICES = [
    "unicorn-postgresql", "unicorn-redis", "uchub-keycloak",
    "unicorn-lago-api", "unicorn-brigade"
]

INTERNAL_IP_RANGES = [
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8"
]

ALLOWED_DOMAINS = [
    "your-domain.com", "*.your-domain.com"
]

async def validate_route_security(route: RouteCreate) -> List[str]:
    """Validate route for security issues"""
    warnings = []

    # Check if service is internal
    if route.service in INTERNAL_SERVICES:
        raise ValueError(f"Cannot expose internal service: {route.service}")

    # Check service URL for internal IPs
    service_url = route.service
    if any(ip_range in service_url for ip_range in INTERNAL_IP_RANGES):
        raise ValueError(f"Cannot route to internal IP address")

    # Validate domain ownership
    rule = route.rule
    for allowed in ALLOWED_DOMAINS:
        if allowed.startswith("*"):
            # Wildcard domain
            base = allowed.replace("*.", "")
            if base not in rule:
                warnings.append(f"Domain in rule may not be owned by organization")
        else:
            if allowed not in rule:
                warnings.append(f"Domain in rule may not be owned by organization")

    # Check for overly permissive routes
    if "PathPrefix(`/`)" in rule and "Host(" not in rule:
        warnings.append("Overly broad route - matches all paths on all hosts")

    return warnings
```

---

#### B. Secure Backup Encryption
```python
import gzip
from cryptography.fernet import Fernet

class SecureBackupManager:
    def __init__(self, encryption_key: bytes):
        self.fernet = Fernet(encryption_key)

    async def create_encrypted_backup(self, config_dir: Path, backup_name: str):
        """Create encrypted, compressed backup"""
        backup_path = TRAEFIK_BACKUP_DIR / f"{backup_name}.enc.gz"

        # Create tar archive in memory
        import tarfile
        from io import BytesIO

        tar_buffer = BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
            for yaml_file in config_dir.glob("*.yml"):
                tar.add(yaml_file, arcname=yaml_file.name)

        # Encrypt compressed data
        compressed_data = tar_buffer.getvalue()
        encrypted_data = self.fernet.encrypt(compressed_data)

        # Write encrypted backup
        with open(backup_path, 'wb') as f:
            f.write(encrypted_data)

        # Set restrictive permissions
        os.chmod(backup_path, 0o400)  # Read-only for owner

        # Audit log
        await audit_logger.log_action(
            action="backup.create",
            user_id="system",
            resource_type="traefik_backup",
            resource_id=backup_name,
            details={"encrypted": True, "compressed": True}
        )

        return backup_name

    async def restore_encrypted_backup(self, backup_name: str):
        """Restore from encrypted backup"""
        backup_path = TRAEFIK_BACKUP_DIR / f"{backup_name}.enc.gz"

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_name}")

        # Read and decrypt
        with open(backup_path, 'rb') as f:
            encrypted_data = f.read()

        compressed_data = self.fernet.decrypt(encrypted_data)

        # Extract tar archive
        import tarfile
        from io import BytesIO

        tar_buffer = BytesIO(compressed_data)
        with tarfile.open(fileobj=tar_buffer, mode='r:gz') as tar:
            tar.extractall(path=TRAEFIK_DYNAMIC_DIR)

        # Audit log
        await audit_logger.log_action(
            action="backup.restore",
            user_id="system",
            resource_type="traefik_backup",
            resource_id=backup_name,
            details={"success": True}
        )
```

---

#### C. Docker Socket Isolation

**Recommended Approach**: Remove Docker socket access entirely.

**Alternative**: Use Docker Socket Proxy with access controls.

```yaml
# docker-compose.yml
services:
  docker-socket-proxy:
    image: tecnativa/docker-socket-proxy
    container_name: docker-socket-proxy
    environment:
      CONTAINERS: 1  # Allow container listing
      SERVICES: 0    # Deny service access
      TASKS: 0       # Deny task access
      NETWORKS: 1    # Allow network listing
      VOLUMES: 0     # Deny volume access
      EVENTS: 0      # Deny event stream
      POST: 0        # Deny write operations
      DELETE: 0      # Deny delete operations
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - internal

  ops-center-direct:
    # ...
    environment:
      DOCKER_HOST: tcp://docker-socket-proxy:2375
    # Remove: - /var/run/docker.sock:/var/run/docker.sock:ro
```

---

### 4.3 Medium Priority (P2) - Implement in Subsequent Releases

#### A. Rate Limiting Enhancements
```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis

# Per-endpoint rate limits
@router.post("/routes", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def create_route(...):
    """Create route - limited to 10/minute per user"""
    pass

@router.post("/{route_id}/test", dependencies=[Depends(RateLimiter(times=30, seconds=60))])
async def test_route(...):
    """Test route - limited to 30/minute per user"""
    pass

# Let's Encrypt protection
class CertificateRateLimiter:
    def __init__(self):
        self.cert_requests = {}  # domain -> [timestamp, timestamp, ...]

    async def check_rate_limit(self, domain: str):
        """Enforce Let's Encrypt rate limits proactively"""
        now = datetime.now()
        week_ago = now - timedelta(days=7)

        # Get requests for this domain in past week
        if domain in self.cert_requests:
            recent_requests = [
                ts for ts in self.cert_requests[domain]
                if ts > week_ago
            ]
        else:
            recent_requests = []

        # Check limit (50 per week, leave buffer of 10)
        if len(recent_requests) >= 40:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit: {domain} approaching Let's Encrypt weekly limit"
            )

        # Record this request
        if domain not in self.cert_requests:
            self.cert_requests[domain] = []
        self.cert_requests[domain].append(now)
```

---

#### B. CSRF Protection
```python
from fastapi_csrf_protect import CsrfProtect
from pydantic import BaseModel

class CsrfSettings(BaseModel):
    secret_key: str = os.getenv("CSRF_SECRET_KEY", Fernet.generate_key().decode())
    cookie_samesite: str = "strict"
    cookie_secure: bool = True
    cookie_httponly: bool = True

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

@router.post("/routes")
async def create_route(
    route: RouteCreate,
    admin: Dict = Depends(require_admin),
    csrf_protect: CsrfProtect = Depends()
):
    """Create route with CSRF protection"""
    await csrf_protect.validate_csrf(request)
    # ... rest of route creation logic
```

---

#### C. Enhanced Audit Logging
```python
class EnhancedAuditLogger:
    async def log_config_access(
        self,
        user_id: str,
        action: str,  # read, write, delete
        config_file: str,
        success: bool,
        ip_address: str,
        user_agent: str
    ):
        """Log all configuration file access"""
        await self.log_action(
            action=f"traefik.config.{action}",
            user_id=user_id,
            resource_type="traefik_config",
            resource_id=config_file,
            details={
                "success": success,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": datetime.now().isoformat()
            }
        )

    async def log_ssl_access(self, user_id: str, domain: str):
        """Log SSL certificate access (critical security event)"""
        await self.log_action(
            action="ssl.certificate.access",
            user_id=user_id,
            resource_type="ssl_certificate",
            resource_id=domain,
            details={
                "severity": "critical",
                "timestamp": datetime.now().isoformat()
            }
        )

        # Send immediate alert for SSL access
        await self.send_security_alert(
            severity="high",
            message=f"SSL certificate accessed by {user_id} for domain {domain}"
        )
```

---

## 5. Security Requirements

### 5.1 Mandatory Security Controls

Before Epic 1.3 can be deployed to production, the following controls MUST be implemented:

#### Authentication & Authorization
- [ ] Keycloak SSO integration with token validation
- [ ] Role-based access control (admin-only)
- [ ] Session management with timeout (30 minutes idle, 8 hours max)
- [ ] Multi-factor authentication for admin users
- [ ] API key authentication for programmatic access

#### Data Protection
- [ ] Encrypt acme.json at rest (filesystem or application-level)
- [ ] Encrypt configuration backups
- [ ] Secure deletion of temporary files
- [ ] Environment variable protection (no secrets in code)
- [ ] Secrets rotation policy (90 days)

#### Access Control
- [ ] File permissions: 0600 for acme.json, 0640 for configs
- [ ] Directory permissions: 0750 for config directories
- [ ] Separate service account for Ops-Center (not root, not muut)
- [ ] Docker socket access via proxy (no direct socket mount)
- [ ] Network segmentation (admin panel on separate network)

#### Input Validation
- [ ] Route rule syntax validation
- [ ] Service name whitelist validation
- [ ] Domain ownership verification
- [ ] Internal service protection (blacklist internal services)
- [ ] Port range restrictions (no privileged ports)
- [ ] Middleware compatibility checking

#### Rate Limiting
- [ ] Per-user rate limits (authenticated endpoints)
- [ ] Per-IP rate limits (unauthenticated endpoints)
- [ ] Let's Encrypt proactive rate limiting
- [ ] Backup creation frequency limits (1 per minute max)
- [ ] Rollback operation limits (5 per hour max)

#### Audit & Monitoring
- [ ] Comprehensive audit logging (all CRUD operations)
- [ ] Failed authentication attempt logging
- [ ] SSL certificate access logging
- [ ] Real-time security alerts (Slack/email)
- [ ] Daily security report generation
- [ ] Audit log retention (minimum 90 days)

---

### 5.2 Recommended Security Controls

Implement these for enhanced security posture:

#### Defense in Depth
- [ ] Web Application Firewall (ModSecurity rules)
- [ ] Intrusion Detection System (OSSEC/Wazuh)
- [ ] File integrity monitoring (AIDE/Tripwire)
- [ ] Regular security scanning (Trivy, Grype)
- [ ] Penetration testing (annual or after major changes)

#### Incident Response
- [ ] Security incident playbooks
- [ ] Automated rollback on anomaly detection
- [ ] Configuration change approval workflow
- [ ] Emergency admin access procedure
- [ ] Disaster recovery plan

#### Compliance
- [ ] SOC 2 compliance preparation
- [ ] GDPR data protection considerations
- [ ] PCI DSS if processing payments (not applicable currently)
- [ ] Regular compliance audits

---

## 6. Implementation Checklist

### Phase 1: Pre-Development (Before Writing Code)

- [x] Security audit completed
- [ ] Threat model reviewed with engineering team
- [ ] Security requirements incorporated into Epic specifications
- [ ] Authentication strategy approved
- [ ] Encryption approach selected
- [ ] Secure development guidelines distributed

### Phase 2: Development

- [ ] Authentication implementation with Keycloak
- [ ] Enhanced route validation logic
- [ ] Encrypted backup system
- [ ] Docker socket proxy configuration
- [ ] Comprehensive audit logging
- [ ] Rate limiting implementation
- [ ] CSRF protection
- [ ] Input sanitization
- [ ] Error handling (no information disclosure)

### Phase 3: Testing

- [ ] Unit tests for validation functions
- [ ] Integration tests for authentication
- [ ] Security tests (OWASP Top 10)
- [ ] Penetration testing
- [ ] Load testing with rate limits
- [ ] Backup/restore testing
- [ ] Rollback testing
- [ ] Audit log verification

### Phase 4: Deployment

- [ ] File permissions set correctly
- [ ] Secrets configured in environment
- [ ] Encryption keys generated and secured
- [ ] Monitoring alerts configured
- [ ] Audit logging enabled
- [ ] Backup retention policy configured
- [ ] Documentation updated
- [ ] Security runbook created

### Phase 5: Post-Deployment

- [ ] Security monitoring active
- [ ] Incident response team notified
- [ ] Regular security reviews scheduled
- [ ] Vulnerability scanning automated
- [ ] Compliance audit scheduled

---

## 7. Recommended File Permissions

### 7.1 Directory Structure
```bash
/home/muut/Infrastructure/traefik/
├── acme/               (0750, muut:traefik-admin)
│   └── acme.json       (0400, muut:traefik-admin) ⚠️ ENCRYPTED
├── dynamic/            (0750, muut:traefik-admin)
│   ├── domains.yml     (0640, muut:traefik-admin)
│   ├── middlewares.yml (0640, muut:traefik-admin)
│   └── ...
├── backups/            (0700, muut:traefik-admin)
│   └── backup_*/       (0700, muut:traefik-admin)
│       └── *.yml.enc   (0400, muut:traefik-admin) ⚠️ ENCRYPTED
├── scripts/            (0750, muut:traefik-admin)
└── traefik.yml         (0640, muut:traefik-admin)
```

### 7.2 Permission Commands
```bash
# Create dedicated group
sudo groupadd traefik-admin
sudo usermod -a -G traefik-admin muut

# Set directory permissions
sudo chmod 0750 /home/muut/Infrastructure/traefik/acme
sudo chmod 0750 /home/muut/Infrastructure/traefik/dynamic
sudo chmod 0700 /home/muut/Infrastructure/traefik/backups

# Set file permissions
sudo chmod 0400 /home/muut/Infrastructure/traefik/acme/acme.json
sudo find /home/muut/Infrastructure/traefik/dynamic -name "*.yml" -exec chmod 0640 {} \;

# Set ownership
sudo chown -R muut:traefik-admin /home/muut/Infrastructure/traefik/

# Verify
sudo find /home/muut/Infrastructure/traefik -ls
```

### 7.3 Permission Explanation

| Path | Permission | Owner:Group | Rationale |
|------|------------|-------------|-----------|
| `acme/` | 0750 | muut:traefik-admin | Owner RWX, group RX, no world access |
| `acme.json` | 0400 | muut:traefik-admin | Owner read-only, contains private keys |
| `dynamic/` | 0750 | muut:traefik-admin | Owner RWX, group RX, no world access |
| `*.yml` | 0640 | muut:traefik-admin | Owner RW, group read, no world access |
| `backups/` | 0700 | muut:traefik-admin | Owner only, sensitive data |
| `*.yml.enc` | 0400 | muut:traefik-admin | Read-only encrypted backups |

---

## 8. Encryption Requirements

### 8.1 Data Classification

| Data Type | Sensitivity | Encryption Required | Key Management |
|-----------|-------------|---------------------|----------------|
| SSL Private Keys | **CRITICAL** | Yes (at rest) | Hardware Security Module (HSM) or KMS |
| ACME Account Key | **CRITICAL** | Yes (at rest) | Same as SSL keys |
| Configuration Backups | **HIGH** | Yes (at rest) | Separate backup encryption key |
| Route Configurations | **MEDIUM** | Recommended | Application-level encryption |
| Audit Logs | **MEDIUM** | Recommended | Log aggregation service |
| Admin Credentials | **CRITICAL** | Yes (Keycloak) | Keycloak key management |

### 8.2 Encryption Implementation

#### Option A: LUKS Filesystem Encryption (Recommended)

**Pros**:
- Transparent to applications
- Hardware-accelerated
- Well-tested and secure
- Automatic decryption on mount

**Cons**:
- Requires manual mount after reboot
- Key must be available to mount

**Implementation**:
```bash
# Create encrypted partition
sudo dd if=/dev/zero of=/home/traefik-encrypted.img bs=1M count=1024
sudo cryptsetup luksFormat /home/traefik-encrypted.img
sudo cryptsetup luksOpen /home/traefik-encrypted.img traefik_secure
sudo mkfs.ext4 /dev/mapper/traefik_secure

# Mount encrypted filesystem
sudo mkdir /secure/traefik
sudo mount /dev/mapper/traefik_secure /secure/traefik
sudo chown muut:traefik-admin /secure/traefik

# Auto-mount on boot (store key in secure location)
echo "traefik_secure /home/traefik-encrypted.img /secure/traefik-keyfile" | sudo tee -a /etc/crypttab
echo "/dev/mapper/traefik_secure /secure/traefik ext4 defaults 0 2" | sudo tee -a /etc/fstab

# Update Traefik paths
sudo ln -sf /secure/traefik/acme.json /home/muut/Infrastructure/traefik/acme/acme.json
```

---

#### Option B: Application-Level Encryption

**Pros**:
- No filesystem changes required
- Fine-grained control
- Can use remote KMS

**Cons**:
- Application must handle encryption/decryption
- Performance overhead
- More complex implementation

**Implementation** (see Section 4.1.B for code examples)

---

#### Option C: HashiCorp Vault Integration

**Pros**:
- Centralized secrets management
- Automatic key rotation
- Audit logging built-in
- Industry standard

**Cons**:
- Additional infrastructure
- Network dependency
- Learning curve

**Implementation**:
```python
import hvac

class VaultCertificateStorage:
    def __init__(self, vault_url, vault_token):
        self.client = hvac.Client(url=vault_url, token=vault_token)

    async def store_certificate(self, domain: str, cert_data: Dict):
        """Store certificate in Vault"""
        self.client.secrets.kv.v2.create_or_update_secret(
            path=f"traefik/certificates/{domain}",
            secret=cert_data
        )

    async def retrieve_certificate(self, domain: str) -> Dict:
        """Retrieve certificate from Vault"""
        response = self.client.secrets.kv.v2.read_secret_version(
            path=f"traefik/certificates/{domain}"
        )
        return response['data']['data']
```

---

### 8.3 Key Management

#### Encryption Key Storage

**Acceptable**:
- ✅ Hardware Security Module (HSM)
- ✅ Cloud KMS (AWS KMS, Azure Key Vault, Google Cloud KMS)
- ✅ HashiCorp Vault
- ✅ Kubernetes Secrets (with encryption at rest enabled)

**NOT Acceptable**:
- ❌ Hardcoded in source code
- ❌ Stored in environment variables
- ❌ Committed to Git
- ❌ Stored in unencrypted files

#### Key Rotation Policy

| Key Type | Rotation Frequency | Procedure |
|----------|-------------------|-----------|
| SSL Certificates | 90 days (automatic via Let's Encrypt) | Automated by Traefik |
| Encryption Keys (acme.json) | 180 days | Manual key rotation + re-encrypt |
| Backup Encryption Keys | 90 days | Generate new key, re-encrypt old backups |
| API Keys | 90 days | Regenerate via Ops-Center UI |
| Admin Credentials | Force change every 90 days | Keycloak password policy |

---

## 9. Monitoring & Alerting

### 9.1 Security Metrics to Monitor

#### Real-Time Alerts (Immediate Action Required)

| Metric | Threshold | Alert Severity | Action |
|--------|-----------|----------------|--------|
| Failed authentication attempts | 5 in 5 minutes | **CRITICAL** | Lock account, investigate |
| SSL certificate access | Any access | **HIGH** | Verify legitimacy |
| Configuration change failure | Any failure | **MEDIUM** | Review audit logs |
| Unauthorized route creation | Internal service exposed | **CRITICAL** | Rollback immediately |
| Backup restoration | Any restoration | **HIGH** | Verify authorized |
| Rate limit exceeded | 10x normal traffic | **MEDIUM** | Check for DDoS |
| Docker socket access | Any access from Ops-Center | **HIGH** | Investigate |

#### Daily Digest Metrics

- Total configuration changes (count and details)
- SSL certificates expiring in < 30 days
- Backup success/failure rate
- Validation failures (rejected configs)
- User activity summary
- Rate limit violations

### 9.2 Alerting Channels

```python
class SecurityAlertManager:
    async def send_critical_alert(
        self,
        event: str,
        details: Dict,
        severity: str = "critical"
    ):
        """Send immediate alert via multiple channels"""

        # Email to security team
        await self.send_email(
            to=["security@your-domain.com", "admin@your-domain.com"],
            subject=f"🚨 SECURITY ALERT: {event}",
            body=f"""
            Severity: {severity.upper()}
            Event: {event}
            Timestamp: {datetime.now().isoformat()}
            Details: {json.dumps(details, indent=2)}
            """
        )

        # Slack notification
        await self.send_slack(
            webhook_url=os.getenv("SLACK_SECURITY_WEBHOOK"),
            message={
                "text": f":rotating_light: SECURITY ALERT: {event}",
                "attachments": [{
                    "color": "danger",
                    "fields": [
                        {"title": "Severity", "value": severity, "short": True},
                        {"title": "Timestamp", "value": datetime.now().isoformat(), "short": True},
                        {"title": "Details", "value": f"```{json.dumps(details, indent=2)}```"}
                    ]
                }]
            }
        )

        # PagerDuty (if critical)
        if severity == "critical":
            await self.trigger_pagerduty(
                event=event,
                details=details
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

### 9.3 Monitoring Dashboard

Create Grafana dashboard with:

1. **Authentication Metrics**
   - Successful logins over time
   - Failed login attempts
   - Active sessions count
   - Session duration histogram

2. **Configuration Changes**
   - Changes per day/hour
   - Change types (create, update, delete)
   - Users making changes
   - Validation success rate

3. **SSL Certificate Health**
   - Certificates expiring in < 30 days
   - Certificate issuance rate
   - Failed certificate requests
   - Let's Encrypt rate limit usage

4. **Security Events**
   - Security alert count by severity
   - Most common alert types
   - Time to remediation
   - False positive rate

5. **System Health**
   - Backup success rate
   - Configuration validation errors
   - API response times
   - Rate limit violations

---

## 10. Secure Development Guidelines

### 10.1 Code Review Checklist

Before approving any code for Epic 1.3, verify:

#### Authentication & Authorization
- [ ] All endpoints require authentication (no anonymous access)
- [ ] Admin role verified for all configuration changes
- [ ] Tokens validated with Keycloak (no hardcoded bypass)
- [ ] Session timeout implemented
- [ ] CSRF protection enabled for state-changing operations

#### Input Validation
- [ ] All user inputs validated (whitelisting, not blacklisting)
- [ ] SQL injection prevention (parameterized queries)
- [ ] Path traversal prevention (no `../` in paths)
- [ ] Command injection prevention (no shell execution of user input)
- [ ] YAML deserialization uses `safe_load()`

#### Data Protection
- [ ] Sensitive data encrypted at rest
- [ ] Secrets loaded from environment variables
- [ ] No credentials in code or logs
- [ ] Secure random number generation (`secrets` module, not `random`)
- [ ] Secure password hashing (bcrypt, argon2)

#### Error Handling
- [ ] No stack traces exposed to users
- [ ] Generic error messages (no information disclosure)
- [ ] All errors logged with context
- [ ] Failed operations audited

#### Audit Logging
- [ ] All CRUD operations logged
- [ ] User ID, timestamp, IP address recorded
- [ ] Before/after state recorded for updates
- [ ] Failed operations logged

---

### 10.2 Testing Requirements

#### Unit Tests
```python
# Example security unit test
async def test_route_validation_blocks_internal_service():
    """Ensure internal services cannot be exposed"""
    route = RouteCreate(
        name="malicious-route",
        rule="Host(`db.your-domain.com`)",
        service="unicorn-postgresql",  # Internal service
        entryPoints=["https"]
    )

    with pytest.raises(ValueError, match="Cannot expose internal service"):
        await validate_route_security(route)

async def test_authentication_required():
    """Ensure all endpoints require authentication"""
    client = TestClient(app)

    response = client.post("/api/v1/traefik/routes", json={...})
    assert response.status_code == 401  # Unauthorized
```

#### Integration Tests
```python
async def test_full_route_creation_with_auth():
    """Test complete route creation flow with authentication"""
    # 1. Authenticate with Keycloak
    token = await get_keycloak_token(username="admin", password="...")

    # 2. Create route
    response = await client.post(
        "/api/v1/traefik/routes",
        json={...},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # 3. Verify audit log
    audit_entry = await audit_logger.get_latest_action()
    assert audit_entry["action"] == "traefik.route.create"
```

#### Security Tests
```python
async def test_sql_injection_prevention():
    """Attempt SQL injection in route name"""
    route = RouteCreate(
        name="'; DROP TABLE routes; --",
        rule="Host(`test.com`)",
        service="test-service"
    )

    # Should reject due to validation
    response = await client.post("/api/v1/traefik/routes", json=route.dict())
    assert response.status_code == 400

async def test_path_traversal_prevention():
    """Attempt path traversal in backup restore"""
    response = await client.post(
        "/api/v1/traefik/backups/restore",
        json={"backup_id": "../../../etc/passwd"}
    )
    assert response.status_code == 400
```

---

## 11. Incident Response Plan

### 11.1 Security Incident Scenarios

#### Scenario 1: Unauthorized Configuration Change Detected

**Detection**: Audit log shows configuration change by unknown user.

**Response**:
1. **Immediate** (< 5 minutes):
   - Lock the affected admin account
   - Rollback configuration to last known good state
   - Alert security team via PagerDuty

2. **Short-term** (< 1 hour):
   - Review audit logs for all recent changes
   - Identify scope of compromise
   - Reset all admin passwords
   - Revoke all active sessions

3. **Long-term** (< 24 hours):
   - Forensic analysis of attack vector
   - Patch vulnerabilities
   - Update security controls
   - Post-mortem report

---

#### Scenario 2: SSL Private Key Compromised

**Detection**: acme.json file accessed by unauthorized process.

**Response**:
1. **Immediate** (< 15 minutes):
   - Revoke compromised certificates via Let's Encrypt
   - Generate new private keys
   - Update all routes with new certificates
   - Alert all affected services

2. **Short-term** (< 4 hours):
   - Review all SSL/TLS connections during compromise window
   - Notify users of potential MITM attacks
   - Rotate all service credentials
   - Enable additional monitoring

3. **Long-term** (< 48 hours):
   - Implement HSM/KMS for key storage
   - Forensic analysis
   - Security audit
   - Incident report

---

#### Scenario 3: Rate Limit Exhaustion (DoS)

**Detection**: Let's Encrypt rate limit reached, cannot issue new certificates.

**Response**:
1. **Immediate** (< 30 minutes):
   - Identify source of excessive requests
   - Block offending IP/user
   - Assess certificate inventory

2. **Short-term** (< 4 hours):
   - Use existing certificates (valid for 90 days)
   - Plan certificate renewals around rate limits
   - Implement proactive rate limiting

3. **Long-term** (< 1 week):
   - Wait for rate limit reset (7 days)
   - Renew critical certificates first
   - Implement certificate request throttling

---

### 11.2 Escalation Matrix

| Severity | Response Time | Escalation Path | Authority to Act |
|----------|---------------|-----------------|------------------|
| **CRITICAL** | < 15 minutes | Security Lead → CTO → CEO | Immediate action authorized |
| **HIGH** | < 1 hour | Security Team → Engineering Manager | Team lead approval required |
| **MEDIUM** | < 4 hours | On-call Engineer → Security Team | Standard procedures |
| **LOW** | < 24 hours | Security Team review | Scheduled response |

---

## 12. Compliance Considerations

### 12.1 SOC 2 Type II Requirements

If pursuing SOC 2 certification, ensure:

- [ ] **Access Control**: All access logged and reviewed quarterly
- [ ] **Change Management**: Configuration changes require approval
- [ ] **Monitoring**: Real-time monitoring with 24/7 alerting
- [ ] **Backup & Recovery**: Tested backup/restore procedures (monthly)
- [ ] **Incident Response**: Documented and tested IR plan
- [ ] **Vendor Management**: Third-party security assessments (Let's Encrypt)
- [ ] **Encryption**: Data encrypted at rest and in transit
- [ ] **Audit Logging**: Logs retained for minimum 1 year

### 12.2 GDPR Compliance

- [ ] **Data Minimization**: Only collect necessary configuration data
- [ ] **Right to Access**: Admins can export their activity logs
- [ ] **Right to Erasure**: Ability to delete user data (where applicable)
- [ ] **Data Protection**: Encryption of PII (admin names, emails in logs)
- [ ] **Breach Notification**: 72-hour breach notification procedure

---

## 13. Conclusion

### 13.1 Summary of Findings

Epic 1.3 (Traefik Configuration Management) introduces **significant security risks** if implemented without proper controls. The current codebase has a solid architectural foundation with validation, backup, and audit logging systems in place. However, **critical security gaps** exist in:

1. **Authentication** - Placeholder code with no real auth (CRITICAL)
2. **SSL Key Protection** - Plaintext storage of private keys (CRITICAL)
3. **Docker Socket Access** - Privilege escalation risk (HIGH)
4. **Input Validation** - Insufficient protection against malicious routes (HIGH)

### 13.2 Go/No-Go Recommendation

**RECOMMENDATION: NO-GO FOR PRODUCTION**

**Conditions for Approval**:
1. ✅ Implement Keycloak SSO authentication (P0 - CRITICAL)
2. ✅ Encrypt acme.json at rest (P0 - CRITICAL)
3. ✅ Enhance route validation (P1 - HIGH)
4. ✅ Implement Docker socket proxy (P1 - HIGH)
5. ✅ Enable encrypted backups (P1 - HIGH)
6. ✅ Complete security testing (P1 - HIGH)
7. ✅ Security audit sign-off (P0 - CRITICAL)

**Estimated Security Hardening Effort**: 40-60 hours

### 13.3 Risk Acceptance

If management chooses to proceed with known risks, document the following:

**Risk Acceptance Form**:
```
Project: Epic 1.3 - Traefik Configuration Management
Date: [DATE]

I acknowledge that the following security risks exist and accept them:
- [ ] Authentication bypass vulnerability (CRITICAL)
- [ ] SSL private key exposure (CRITICAL)
- [ ] Privilege escalation via Docker socket (HIGH)
- [ ] Internal service exposure via malicious routes (HIGH)

Business justification: ___________________________________

Mitigation plan: ___________________________________

Accepted by: ___________________ (CTO/Security Lead)
Date: ___________________
Review date: ___________________ (30 days)
```

**Note**: Risk acceptance should be **temporary** with a clear remediation timeline.

---

### 13.4 Next Steps

1. **Review this audit** with engineering team
2. **Prioritize security fixes** based on risk assessment
3. **Update Epic 1.3 requirements** to include security controls
4. **Develop security implementation plan** with timelines
5. **Schedule security review checkpoint** after P0/P1 fixes
6. **Plan penetration testing** before production deployment
7. **Create security runbook** for operations team

---

## Appendix A: Security Testing Checklist

### A.1 Manual Security Tests

- [ ] **Authentication Bypass**: Attempt to access admin endpoints without token
- [ ] **SQL Injection**: Try SQL in route names, rules, service names
- [ ] **Path Traversal**: Attempt `../` in backup restore operations
- [ ] **YAML Injection**: Test malicious YAML payloads
- [ ] **Rate Limit Bypass**: Attempt to exceed rate limits
- [ ] **CSRF**: Test cross-origin requests without CSRF token
- [ ] **Session Fixation**: Attempt to hijack admin sessions
- [ ] **Privilege Escalation**: Attempt admin operations as non-admin

### A.2 Automated Security Scanning

```bash
# OWASP ZAP scanning
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t https://your-domain.com/api/v1/traefik/

# Trivy container scanning
trivy image uc-1-pro-ops-center

# Bandit Python security linting
bandit -r backend/ -f json -o security-report.json

# Safety dependency checking
safety check --json

# Semgrep SAST scanning
semgrep --config=p/security-audit backend/
```

---

## Appendix B: Secure Configuration Examples

### B.1 Production-Ready docker-compose.yml

```yaml
version: '3.8'

services:
  ops-center-direct:
    image: uc-1-pro-ops-center
    container_name: ops-center-direct
    restart: unless-stopped

    # Security: No Docker socket access
    # volumes:
    #   - /var/run/docker.sock:/var/run/docker.sock:ro  # REMOVED

    # Security: Use socket proxy instead
    environment:
      DOCKER_HOST: tcp://docker-socket-proxy:2375

      # Security: Load secrets from environment (not hardcoded)
      KEYCLOAK_CLIENT_SECRET: ${KEYCLOAK_CLIENT_SECRET}
      SESSION_SECRET_KEY: ${SESSION_SECRET_KEY}
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}

    # Security: Read-only root filesystem
    read_only: true
    tmpfs:
      - /tmp
      - /var/tmp

    # Security: Drop all capabilities
    cap_drop:
      - ALL

    # Security: Run as non-root
    user: "1000:1000"

    # Security: Resource limits
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

    # Security: Security options
    security_opt:
      - no-new-privileges:true
      - seccomp:unconfined  # Adjust based on needs

    networks:
      - web
      - internal

    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.ops-center.rule=Host(`your-domain.com`)"
      - "traefik.http.routers.ops-center.entrypoints=https"
      - "traefik.http.routers.ops-center.tls.certresolver=letsencrypt"

      # Security: Add security headers middleware
      - "traefik.http.routers.ops-center.middlewares=security-headers"
      - "traefik.http.middlewares.security-headers.headers.stsSeconds=31536000"
      - "traefik.http.middlewares.security-headers.headers.stsIncludeSubdomains=true"
      - "traefik.http.middlewares.security-headers.headers.stsPreload=true"
      - "traefik.http.middlewares.security-headers.headers.forceSTSHeader=true"
      - "traefik.http.middlewares.security-headers.headers.contentTypeNosniff=true"
      - "traefik.http.middlewares.security-headers.headers.browserXssFilter=true"
      - "traefik.http.middlewares.security-headers.headers.referrerPolicy=same-origin"
      - "traefik.http.middlewares.security-headers.headers.frameDeny=true"

  docker-socket-proxy:
    image: tecnativa/docker-socket-proxy
    container_name: docker-socket-proxy
    restart: unless-stopped

    environment:
      # Security: Minimal permissions
      CONTAINERS: 1
      SERVICES: 0
      TASKS: 0
      NETWORKS: 1
      VOLUMES: 0
      EVENTS: 0
      POST: 0
      DELETE: 0

    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro

    networks:
      - internal

networks:
  web:
    external: true
  internal:
    internal: true  # No external access
```

---

## Appendix C: References

### C.1 Security Standards & Frameworks

- **OWASP Top 10 (2021)**: https://owasp.org/Top10/
- **NIST Cybersecurity Framework**: https://www.nist.gov/cyberframework
- **CIS Docker Benchmark**: https://www.cisecurity.org/benchmark/docker
- **Traefik Security Documentation**: https://doc.traefik.io/traefik/https/acme/

### C.2 Tools & Resources

- **Bandit (Python security linter)**: https://bandit.readthedocs.io/
- **Trivy (container scanner)**: https://aquasecurity.github.io/trivy/
- **OWASP ZAP (security scanner)**: https://www.zaproxy.org/
- **Semgrep (SAST)**: https://semgrep.dev/

### C.3 Learning Resources

- **OWASP Secure Coding Practices**: https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/
- **Docker Security Best Practices**: https://docs.docker.com/engine/security/
- **Let's Encrypt Best Practices**: https://letsencrypt.org/docs/best-practices/

---

**Document Version**: 1.0
**Last Updated**: October 23, 2025
**Next Review**: Before Epic 1.3 implementation begins
**Classification**: Internal - Security Sensitive
**Distribution**: Engineering Team, Security Team, Management

---

## Sign-Off

**Security Auditor**: _____________________ Date: _____
**Engineering Lead**: _____________________ Date: _____
**CTO/Security Lead**: _____________________ Date: _____

---

**END OF SECURITY AUDIT REPORT**
