## Security Best Practices - Ops-Center

**Last Updated**: October 22, 2025
**Audience**: Developers, DevOps, Security Team
**Status**: Production Operational Guide

---

## Overview

This document provides ongoing security guidelines for operating and maintaining the Ops-Center infrastructure. All team members must follow these practices to maintain our **Grade A** security posture.

---

## 1. Credential Management

### API Keys & Tokens

**Storage**:
- ✅ **DO**: Store all credentials encrypted in database using `SecretManager`
- ❌ **DON'T**: Store credentials in plaintext, code, or configuration files
- ❌ **DON'T**: Log credentials (even masked versions in production)

**Access**:
```python
from secret_manager import SecretManager

# ✅ Correct: Decrypt only when needed
manager = SecretManager()
token = manager.retrieve_decrypted_credential(user_id, "cloudflare", "api_token", db)
cloudflare_api.authenticate(token)

# ❌ Wrong: Store decrypted token in variable
cloudflare_token = "..."  # Never do this
```

**Rotation Schedule**:
- **User API keys**: 90 days or on user request
- **Service credentials** (Cloudflare/NameCheap): 30 days
- **Encryption key**: Annually (requires re-encryption of all secrets)

### Rotation Procedure

```bash
# 1. Generate new Cloudflare API token
# Login to Cloudflare Dashboard → My Profile → API Tokens → Create Token

# 2. Test new token
curl -H "Authorization: Bearer NEW_TOKEN" \
  https://api.cloudflare.com/client/v4/user/tokens/verify

# 3. Update encrypted credential
python3 scripts/rotate_credential.py \
  --service cloudflare \
  --type api_token \
  --new-value "NEW_TOKEN"

# 4. Revoke old token in Cloudflare Dashboard

# 5. Verify services still work
./scripts/health-check-detailed.sh
```

---

## 2. Input Validation

### Domain Names

**Always use secure validators**:
```python
from security_validators import validate_domain_secure

# ✅ Correct: Validate before use
try:
    domain = validate_domain_secure(user_input, allow_idn=False)
except (SecurityValidationError, ValueError) as e:
    return {"error": str(e)}

# ❌ Wrong: Trust user input
domain = user_input  # Vulnerable to IDN attacks
```

**Blocked Patterns**:
- Punycode domains (`xn--`)
- Consecutive hyphens (`--`)
- Invalid characters (spaces, special chars)
- Overlong domains (>253 chars)

### IP Addresses

**Always check for private IPs**:
```python
from security_validators import validate_public_ip, is_private_ip

# ✅ Correct: Block private IPs
if is_private_ip(ip_address):
    raise ValidationError("Private IP addresses not allowed (DNS rebinding protection)")

# ✅ Correct: Validate before DNS record creation
validated_ip = validate_public_ip(ip_address, allow_private=False)

# ❌ Wrong: Allow any IP
dns_record.create(type="A", content=user_input)  # Vulnerable to DNS rebinding
```

### Database Queries

**Always use parameterized queries**:
```python
# ✅ Correct: Parameterized query
cursor.execute(
    "SELECT * FROM users WHERE email = %s AND domain = %s",
    (email, domain)
)

# ❌ Wrong: String concatenation (SQL injection!)
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

---

## 3. Domain Migration Security

### Pre-Migration Checklist

1. **Domain Ownership Verification**:
   ```python
   from domain_verification import DomainVerificationManager

   verifier = DomainVerificationManager(redis)

   # Generate verification code
   code = verifier.generate_verification_code(domain, user_id)

   # User adds TXT record: _uc-verify.domain.com = uc-verify-abc123...

   # Verify ownership
   result = verifier.verify_domain_ownership(domain, user_id)
   if not result["verified"]:
       raise Forbidden("Domain ownership not verified")
   ```

2. **DNS Record Validation**:
   - All A/AAAA records checked for private IPs
   - CNAME records validated for format
   - TXT records scanned for XSS/SQL injection

3. **Rate Limiting**:
   - Max 3 verification attempts per 5 minutes
   - Max 10 total attempts per code
   - Cloudflare API calls throttled (1200/5min)
   - NameCheap API calls throttled (50/min)

### Migration Workflow

```
1. User initiates migration
   ↓
2. System validates domain format
   ↓
3. System generates verification code
   ↓
4. User adds TXT record to domain
   ↓
5. System verifies ownership (DNS query)
   ↓
6. IF VERIFIED: Export DNS from NameCheap
   ↓
7. Validate all DNS records (block private IPs)
   ↓
8. Create Cloudflare zone
   ↓
9. Import validated DNS records
   ↓
10. User updates nameservers
```

---

## 4. Error Handling

### Production vs Debug Mode

**Production** (Deployed System):
```python
# ✅ Generic error message
try:
    cloudflare_api.create_zone(domain)
except CloudflareAPIError as e:
    logger.error(f"Cloudflare API error: {e}")  # Log details
    return {"error": "Failed to create zone. Please try again later."}  # User sees this
```

**Debug Mode** (Local Development):
```python
# ✅ Detailed error message
try:
    cloudflare_api.create_zone(domain)
except CloudflareAPIError as e:
    if settings.DEBUG:
        return {"error": str(e), "traceback": traceback.format_exc()}
    else:
        return {"error": "Failed to create zone"}
```

### Never Expose

- ❌ File paths (`/var/lib/postgresql/data/users.db`)
- ❌ SQL table/column names (`Table 'users' doesn't exist`)
- ❌ Internal IP addresses (`Database at 10.0.0.5 unreachable`)
- ❌ Stack traces (production)
- ❌ API tokens (even masked)

---

## 5. Security Headers

### Required Headers (Already Configured)

All responses include:
```http
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; ...
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

### Testing Headers

```bash
# Check security headers
curl -I https://unicorncommander.ai/api/v1/system/status

# Or use security header analyzer
https://securityheaders.com/?q=unicorncommander.ai
```

---

## 6. Rate Limiting

### Current Limits

| Endpoint Pattern | Rate Limit | Scope |
|------------------|------------|-------|
| `/api/v1/admin/*` | 100/min | Per IP |
| `/api/v1/migration/*` | 50/min | Per user |
| `/api/v1/dns/*` | 200/min | Per user |
| Cloudflare API | 1200/5min | System-wide |
| NameCheap API | 50/min | System-wide |

### Implementing New Limits

```python
from security_middleware import BasicRateLimitMiddleware

# Per-endpoint rate limiting
@app.get("/api/v1/sensitive-operation")
@rate_limit(max_requests=10, window=60)  # 10 requests per minute
async def sensitive_operation():
    ...
```

---

## 7. Logging & Monitoring

### What to Log

✅ **DO log**:
- Authentication attempts (success/failure)
- API calls with user_id and endpoint
- Rate limit violations
- Domain verification attempts
- DNS record changes
- Credential access (NOT the credential itself)

❌ **DON'T log**:
- API tokens/keys (even masked)
- Passwords
- Encryption keys
- Credit card numbers
- Personal health information (PHI)

### Log Format

```python
# ✅ Correct logging
logger.info(
    f"User {user_id} accessed Cloudflare API token at {timestamp}"
)

# ❌ Wrong: Logs credential
logger.info(f"Using token: {token}")  # NEVER DO THIS
```

### Monitoring Alerts

Set up alerts for:
- Failed authentication attempts (>5 per user per hour)
- Rate limit violations (>10 per IP per hour)
- DNS rebinding attempts (any private IP in DNS)
- SQL injection attempts (any pattern match)
- Unusual API usage (>1000 calls per user per day)

---

## 8. HTTPS & SSL/TLS

### Certificate Management

```bash
# Check SSL certificate expiration
openssl s_client -connect unicorncommander.ai:443 -servername unicorncommander.ai \
  </dev/null 2>/dev/null | openssl x509 -noout -dates

# Renew Let's Encrypt certificate (Traefik does this automatically)
# But verify auto-renewal works:
docker logs traefik | grep -i "certificate"
```

### HSTS Configuration

Current configuration:
```http
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

**HSTS Preload List**: Submit domain to [hstspreload.org](https://hstspreload.org/) after 6 months of successful HSTS operation.

---

## 9. Database Security

### Connection Security

```python
# ✅ Correct: Use connection pooling + SSL
DATABASE_URL = "postgresql://user:pass@host:5432/db?sslmode=require"

# ✅ Correct: Parameterized queries
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# ❌ Wrong: Expose password
DATABASE_URL = "postgresql://admin:password123@..."  # Use env var
```

### Row-Level Security

```python
# ✅ Correct: Filter by user_id
def get_user_credentials(user_id: str, service: str):
    cursor.execute(
        "SELECT * FROM encrypted_credentials WHERE user_id = %s AND service = %s",
        (user_id, service)
    )

# ❌ Wrong: No user filtering (data leak)
def get_credentials(service: str):
    cursor.execute(f"SELECT * FROM encrypted_credentials WHERE service = '{service}'")
```

---

## 10. Incident Response

### Security Incident Procedure

1. **Detect**: Monitor logs, user reports, security alerts
2. **Contain**: Revoke compromised credentials, block malicious IPs
3. **Investigate**: Analyze logs, determine scope of breach
4. **Remediate**: Patch vulnerabilities, rotate credentials
5. **Document**: Write incident report, update security practices
6. **Notify**: Inform affected users (if personal data compromised)

### Emergency Contacts

- **Security Team Lead**: [Contact Info]
- **DevOps On-Call**: [PagerDuty/Slack]
- **Infrastructure Admin**: [Contact Info]

### Credential Compromise

If credentials are compromised:
```bash
# 1. Immediately revoke credentials
# Cloudflare: Dashboard → API Tokens → Revoke
# NameCheap: Account → API Access → Disable

# 2. Generate new credentials
# 3. Update encrypted credentials in database
# 4. Audit all API calls with old credentials
# 5. Check for unauthorized access

# 6. Review logs
grep "compromised_token" /var/log/ops-center/*.log
```

---

## 11. Dependency Management

### Vulnerability Scanning

```bash
# Scan Python dependencies
pip3 install safety
safety check

# Scan for known vulnerabilities
pip3 install pip-audit
pip-audit

# Update dependencies
pip3 list --outdated
```

### Update Policy

- **Critical vulnerabilities**: Patch within 24 hours
- **High vulnerabilities**: Patch within 1 week
- **Medium vulnerabilities**: Patch within 30 days
- **Low vulnerabilities**: Patch on next release cycle

---

## 12. Security Checklist for New Features

Before deploying new features, verify:

- [ ] All user inputs validated with `security_validators.py`
- [ ] All database queries use parameterized queries
- [ ] All API credentials stored encrypted
- [ ] All sensitive endpoints require authentication
- [ ] All RBAC checks verify user permissions
- [ ] All error messages are generic (no internal details)
- [ ] All security headers present in responses
- [ ] All rate limits configured
- [ ] All logging excludes sensitive data
- [ ] All dependencies scanned for vulnerabilities
- [ ] All changes peer-reviewed for security
- [ ] All security tests pass

---

## 13. Code Review Guidelines

### Security-Focused Code Review

Reviewers must check for:

1. **Input Validation**:
   - Are all user inputs validated?
   - Are domain names checked for IDN attacks?
   - Are IP addresses checked for private ranges?

2. **Authentication/Authorization**:
   - Are endpoints protected with auth checks?
   - Are RBAC roles verified?
   - Is user_id used in all queries?

3. **Secret Management**:
   - Are credentials encrypted?
   - Are credentials logged?
   - Are credentials hardcoded?

4. **SQL Injection**:
   - Are parameterized queries used?
   - Are user inputs concatenated into SQL?

5. **Error Handling**:
   - Are error messages generic?
   - Are stack traces hidden in production?

---

## 14. Compliance & Auditing

### Security Audit Schedule

- **Weekly**: Automated vulnerability scans
- **Monthly**: Review access logs for anomalies
- **Quarterly**: Full security audit by external team
- **Annually**: Penetration testing

### Compliance Requirements

- **GDPR**: Right to erasure implemented (delete user data)
- **PCI-DSS**: No credit card storage (Stripe handles)
- **HIPAA**: N/A (no health information)
- **SOC 2**: Audit logging, access controls, encryption at rest

---

## 15. Training & Awareness

### Required Training

All developers must complete:
- [ ] OWASP Top 10 training
- [ ] Secure coding practices workshop
- [ ] Ops-Center security architecture review
- [ ] Incident response simulation

### Resources

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- CWE Top 25: https://cwe.mitre.org/top25/
- SANS Security Training: https://www.sans.org/

---

## Contact & Support

**Security Issues**: security@unicorncommander.ai
**Documentation Updates**: Update this file via pull request
**Questions**: Slack #security-team

---

**Last Reviewed**: October 22, 2025
**Next Review**: January 22, 2026 (Quarterly)
