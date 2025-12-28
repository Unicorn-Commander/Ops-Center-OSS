# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.x.x   | :white_check_mark: |
| 1.x.x   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in Ops-Center, please report it responsibly.

### How to Report

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please email us at: **security@magicunicorn.tech**

Include in your report:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (optional)

### What to Expect

1. **Acknowledgment**: We'll acknowledge your report within 48 hours
2. **Assessment**: We'll assess the severity and impact within 7 days
3. **Updates**: We'll keep you informed of our progress
4. **Fix**: We'll work on a fix and coordinate disclosure with you
5. **Credit**: We'll credit you in the security advisory (unless you prefer anonymity)

### Scope

The following are in scope:
- Ops-Center codebase
- Authentication/authorization bypasses
- Data exposure vulnerabilities
- Injection attacks (SQL, XSS, etc.)
- Privilege escalation
- Cryptographic weaknesses

Out of scope:
- Third-party dependencies (report to the respective project)
- Social engineering attacks
- Physical attacks
- Denial of service attacks

## Security Best Practices

When deploying Ops-Center:

### Authentication
- Use strong Keycloak admin passwords
- Enable MFA for admin accounts
- Regularly rotate client secrets
- Use HTTPS in production

### Database
- Use strong, unique database passwords
- Restrict database access to application containers only
- Enable PostgreSQL SSL connections
- Regular backups with encryption

### API Keys
- Never commit API keys to version control
- Rotate API keys periodically
- Use environment variables for all secrets
- Set appropriate key scopes and limits

### Infrastructure
- Keep Docker and dependencies updated
- Use network isolation (Docker networks)
- Enable and review audit logs
- Configure rate limiting

### Environment Variables

Never commit these to version control:
- `KEYCLOAK_CLIENT_SECRET`
- `POSTGRES_PASSWORD`
- `STRIPE_SECRET_KEY`
- `LAGO_API_KEY`
- `LITELLM_MASTER_KEY`
- `SECRET_KEY`
- `JWT_SECRET`

Use `.env.auth` (gitignored) or environment-specific secrets management.

## Security Features

Ops-Center includes:

- **SSO Authentication**: Keycloak with industry-standard OIDC
- **Role-Based Access Control**: 5-tier permission hierarchy
- **Audit Logging**: Complete activity tracking
- **API Key Hashing**: bcrypt for secure storage
- **Input Validation**: Pydantic models throughout
- **SQL Injection Protection**: Parameterized queries via asyncpg
- **XSS Protection**: React's built-in escaping
- **HTTPS/TLS**: Via Traefik reverse proxy
- **PCI Compliance**: Stripe handles all card data

## Acknowledgments

We thank the following for responsibly disclosing vulnerabilities:

*No vulnerabilities reported yet.*

---

Thank you for helping keep Ops-Center secure!
