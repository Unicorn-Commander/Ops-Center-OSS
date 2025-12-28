# Credential Management Guide - Ops-Center

**Last Updated**: October 22, 2025
**Audience**: System Administrators, DevOps Engineers
**Status**: Production Operational Guide

---

## Overview

This guide covers the secure management of credentials in the Ops-Center system using the `SecretManager` module with Fernet encryption (AES-128-CBC).

---

## Architecture

### Encryption Flow

```
┌─────────────┐
│  User Input │ (Plaintext API Token)
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ SecretManager   │ (Fernet Encryption)
│ encrypt_secret()│
└──────┬──────────┘
       │
       ▼
┌──────────────────────┐
│ PostgreSQL Database  │ (encrypted_value column)
│ encrypted_credentials│
└──────┬───────────────┘
       │
       ▼ (When needed)
┌─────────────────┐
│ SecretManager   │ (Fernet Decryption)
│ decrypt_secret()│
└──────┬──────────┘
       │
       ▼
┌─────────────────────┐
│ Cloudflare/NameCheap│ (Use plaintext token)
│ API Call            │
└─────────────────────┘
```

### Storage Locations

| Item | Location | Format |
|------|----------|--------|
| Encrypted credentials | PostgreSQL `encrypted_credentials` table | Fernet-encrypted base64 |
| Encryption key | `ENCRYPTION_KEY` environment variable | 44-character base64 string |
| User API keys (hashed) | PostgreSQL `api_keys` table | bcrypt hash |

**IMPORTANT**: The encryption key is NEVER stored in the database or code. It must be in the environment.

---

## Setup

### 1. Generate Encryption Key

```bash
# Generate new Fernet encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Output example:
# XeVZP3F8K_Ry9QmNj2HfT6wL4vU7sD1aB5cE9gH3iJ0=
```

### 2. Add to Environment

Add to `/home/muut/Production/UC-Cloud/services/ops-center/.env.auth`:

```bash
# Secret Encryption Key (44 characters, base64-encoded)
ENCRYPTION_KEY=XeVZP3F8K_Ry9QmNj2HfT6wL4vU7sD1aB5cE9gH3iJ0=
```

### 3. Create Database Table

```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db << 'EOF'
CREATE TABLE IF NOT EXISTS encrypted_credentials (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    service VARCHAR(100) NOT NULL,
    credential_type VARCHAR(100) NOT NULL,
    encrypted_value TEXT NOT NULL,
    encrypted_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    UNIQUE(user_id, service, credential_type)
);

CREATE INDEX idx_encrypted_credentials_user ON encrypted_credentials(user_id);
CREATE INDEX idx_encrypted_credentials_service ON encrypted_credentials(service);
EOF
```

### 4. Verify Setup

```bash
# Test encryption/decryption
docker exec ops-center-direct python3 << 'EOF'
from secret_manager import SecretManager

manager = SecretManager()
print("✅ SecretManager initialized successfully")

# Test encryption
encrypted = manager.encrypt_secret("test_secret", "test")
print(f"✅ Encryption works: {encrypted['encrypted_value'][:50]}...")

# Test decryption
decrypted = manager.decrypt_secret(encrypted['encrypted_value'])
assert decrypted == "test_secret"
print("✅ Decryption works")
EOF
```

---

## Usage

### Store Cloudflare API Token

```python
from secret_manager import SecretManager
import psycopg2

# Initialize
manager = SecretManager()
db = psycopg2.connect(database="unicorn_db", user="unicorn", password="unicorn")

# Store encrypted token
result = manager.store_encrypted_credential(
    user_id="user@example.com",  # Keycloak user ID
    service="cloudflare",
    credential_type="api_token",
    secret="<CLOUDFLARE_API_TOKEN_REDACTED>",  # Plaintext token
    db_connection=db
)

print(f"✅ Credential stored: {result['masked_value']}")
# Output: ✅ Credential stored: 0LVX...egC_
```

### Retrieve Cloudflare API Token

```python
from secret_manager import SecretManager
import psycopg2

manager = SecretManager()
db = psycopg2.connect(database="unicorn_db", user="unicorn", password="unicorn")

# Retrieve and decrypt token
token = manager.retrieve_decrypted_credential(
    user_id="user@example.com",
    service="cloudflare",
    credential_type="api_token",
    db_connection=db
)

# Use token for API call
from cloudflare_manager import CloudflareManager
cf = CloudflareManager(api_token=token)
zones = cf.zones.list_zones()
```

### Store NameCheap API Key

```python
manager.store_encrypted_credential(
    user_id="user@example.com",
    service="namecheap",
    credential_type="api_key",
    secret="your-example-api-key",
    db_connection=db
)

manager.store_encrypted_credential(
    user_id="user@example.com",
    service="namecheap",
    credential_type="api_username",
    secret="SkyBehind",
    db_connection=db
)
```

### Retrieve NameCheap Credentials

```python
api_key = manager.retrieve_decrypted_credential(
    user_id="user@example.com",
    service="namecheap",
    credential_type="api_key",
    db_connection=db
)

username = manager.retrieve_decrypted_credential(
    user_id="user@example.com",
    service="namecheap",
    credential_type="api_username",
    db_connection=db
)

# Use credentials
from namecheap_manager import NameCheapManager, NameCheapCredentials
credentials = NameCheapCredentials(
    api_username=username,
    api_key=api_key,
    username=username,
    client_ip="YOUR_SERVER_IP"
)
nc = NameCheapManager(credentials)
```

---

## Credential Rotation

### Why Rotate Credentials?

- **Security**: Limits damage if credentials are compromised
- **Compliance**: Required by many security standards (SOC 2, PCI-DSS)
- **Best Practice**: Reduces risk window for exposed credentials

### Rotation Schedule

| Credential Type | Rotation Frequency | Automated? |
|-----------------|-------------------|------------|
| User API keys | 90 days | Yes (on user request) |
| Cloudflare API tokens | 30 days | No (manual) |
| NameCheap API keys | 30 days | No (manual) |
| Encryption key | Annually | No (requires re-encryption) |

### Rotate Cloudflare API Token

#### Step 1: Generate New Token

1. Login to Cloudflare Dashboard: https://dash.cloudflare.com
2. Navigate to **My Profile** → **API Tokens**
3. Click **Create Token**
4. Use **Edit zone DNS** template
5. Permissions:
   - Zone → DNS → Edit
   - Zone → Zone → Read
6. Zone Resources: **Include → All zones**
7. Click **Continue to summary** → **Create Token**
8. **Copy the new token** (you'll only see it once!)

#### Step 2: Test New Token

```bash
# Test new token
curl -H "Authorization: Bearer NEW_TOKEN_HERE" \
  https://api.cloudflare.com/client/v4/user/tokens/verify

# Expected response:
# {
#   "success": true,
#   "result": {
#     "id": "...",
#     "status": "active"
#   }
# }
```

#### Step 3: Update Database

```python
from secret_manager import SecretManager
import psycopg2

manager = SecretManager()
db = psycopg2.connect(database="unicorn_db", user="unicorn", password="unicorn")

# Delete old token
cursor = db.cursor()
cursor.execute(
    "DELETE FROM encrypted_credentials WHERE user_id = %s AND service = %s AND credential_type = %s",
    ("user@example.com", "cloudflare", "api_token")
)
db.commit()

# Store new token
manager.store_encrypted_credential(
    user_id="user@example.com",
    service="cloudflare",
    credential_type="api_token",
    secret="NEW_TOKEN_HERE",
    db_connection=db
)

print("✅ Cloudflare API token rotated successfully")
```

#### Step 4: Verify Services Still Work

```bash
# Test Cloudflare integration
docker exec ops-center-direct python3 << 'EOF'
from cloudflare_manager import CloudflareManager
from secret_manager import SecretManager
import psycopg2

db = psycopg2.connect(database="unicorn_db", user="unicorn", password="unicorn")
manager = SecretManager()

token = manager.retrieve_decrypted_credential(
    "user@example.com", "cloudflare", "api_token", db
)

cf = CloudflareManager(api_token=token)
status = cf.get_account_status()

assert status['api_connected'] == True
print("✅ Cloudflare API working with new token")
EOF
```

#### Step 5: Revoke Old Token

1. Go back to Cloudflare Dashboard → API Tokens
2. Find the old token
3. Click **Revoke**
4. Confirm revocation

---

### Rotate NameCheap API Key

**NOTE**: NameCheap doesn't allow self-service API key rotation. You must contact support.

#### Step 1: Contact NameCheap Support

Email: support@namecheap.com
Subject: "API Key Rotation Request"

```
Hello,

I would like to request a new API key for my account (username: SkyBehind).

Current API key (first 8 chars): 3bce8c1b...

Please generate a new key and revoke the old one.

Thank you.
```

#### Step 2: Receive New Key

NameCheap support will email you the new API key (typically within 24-48 hours).

#### Step 3: Update Database

```python
from secret_manager import SecretManager
import psycopg2

manager = SecretManager()
db = psycopg2.connect(database="unicorn_db", user="unicorn", password="unicorn")

# Update API key
cursor = db.cursor()
cursor.execute(
    "DELETE FROM encrypted_credentials WHERE user_id = %s AND service = %s AND credential_type = %s",
    ("user@example.com", "namecheap", "api_key")
)
db.commit()

manager.store_encrypted_credential(
    user_id="user@example.com",
    service="namecheap",
    credential_type="api_key",
    secret="NEW_NAMECHEAP_KEY_HERE",
    db_connection=db
)

print("✅ NameCheap API key rotated successfully")
```

---

### Rotate Encryption Key

**WARNING**: This requires re-encrypting ALL credentials in the database. Plan for downtime.

#### Step 1: Generate New Key

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Save this as NEW_ENCRYPTION_KEY
```

#### Step 2: Re-Encrypt All Credentials

```python
from secret_manager import SecretManager
import psycopg2
import os

# Old and new keys
old_key = os.getenv('ENCRYPTION_KEY')
new_key = "NEW_ENCRYPTION_KEY_HERE"

db = psycopg2.connect(database="unicorn_db", user="unicorn", password="unicorn")

manager = SecretManager()
result = manager.rotate_encryption_key(
    old_key=old_key,
    new_key=new_key,
    db_connection=db
)

print(f"✅ Key rotation complete:")
print(f"   - Total credentials: {result['total_credentials']}")
print(f"   - Rotated: {result['rotated']}")
print(f"   - Failed: {result['failed']}")
```

#### Step 3: Update Environment Variable

```bash
# Update .env.auth
vim /home/muut/Production/UC-Cloud/services/ops-center/.env.auth

# Change:
ENCRYPTION_KEY=OLD_KEY

# To:
ENCRYPTION_KEY=NEW_KEY
```

#### Step 4: Restart Services

```bash
docker restart ops-center-direct
```

#### Step 5: Verify

```bash
docker exec ops-center-direct python3 << 'EOF'
from secret_manager import SecretManager

manager = SecretManager()
encrypted = manager.encrypt_secret("test", "test")
decrypted = manager.decrypt_secret(encrypted['encrypted_value'])
assert decrypted == "test"
print("✅ New encryption key working")
EOF
```

---

## Credential Leak Response

### If Credentials Are Exposed

**IMMEDIATE ACTIONS** (within 1 hour):

1. **Revoke compromised credentials**:
   - Cloudflare: Dashboard → API Tokens → Revoke
   - NameCheap: Contact support to disable API access

2. **Generate new credentials** (see rotation procedures above)

3. **Update database** with new encrypted credentials

4. **Audit API usage**:
```bash
# Check for unauthorized API calls
docker logs ops-center-direct | grep -i "cloudflare" | grep -v "user@example.com"
```

5. **Check for data exfiltration**:
```bash
# Look for unusual DNS record changes
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c \
  "SELECT * FROM audit_logs WHERE action = 'dns_record_created' AND created_at > NOW() - INTERVAL '24 hours';"
```

6. **Notify affected users** (if personal data was accessed)

**FOLLOW-UP ACTIONS** (within 24 hours):

7. Document incident in security log
8. Review how credentials were exposed
9. Update security practices to prevent recurrence
10. Consider external security audit

---

## Monitoring & Auditing

### Credential Access Logs

```bash
# View credential access logs
docker logs ops-center-direct | grep "Credential retrieved"

# Count accesses per service
docker logs ops-center-direct | grep "Credential retrieved" | \
  awk '{print $NF}' | sort | uniq -c
```

### Suspicious Activity Alerts

Set up alerts for:
- **Excessive credential retrievals**: >100 per hour per user
- **Failed decryption attempts**: Any failed decrypt (indicates key mismatch or tampering)
- **Credential modifications**: Any UPDATE/DELETE on `encrypted_credentials` table
- **Encryption key access**: Any read of `ENCRYPTION_KEY` environment variable

---

## Backup & Recovery

### Backup Encrypted Credentials

```bash
# Backup encrypted_credentials table
docker exec unicorn-postgresql pg_dump -U unicorn -d unicorn_db \
  -t encrypted_credentials > encrypted_credentials_backup_$(date +%Y%m%d).sql

# Backup encryption key (secure location only!)
echo $ENCRYPTION_KEY > encryption_key_backup_$(date +%Y%m%d).txt
chmod 600 encryption_key_backup_*.txt
# Move to secure offline storage
```

### Restore Encrypted Credentials

```bash
# Restore table
docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db < encrypted_credentials_backup_20251022.sql

# Restore encryption key
export ENCRYPTION_KEY=$(cat encryption_key_backup_20251022.txt)

# Verify
docker exec ops-center-direct python3 -c "from secret_manager import SecretManager; SecretManager()"
```

---

## FAQ

### Q: Can I store the encryption key in the database?
**A**: NO. The encryption key must NEVER be in the database. If an attacker gets the database, they would have both the encrypted data and the key to decrypt it.

### Q: What if I lose the encryption key?
**A**: All encrypted credentials become unrecoverable. You must:
1. Generate new credentials from providers (Cloudflare, NameCheap)
2. Generate new encryption key
3. Re-encrypt and store new credentials

### Q: How often should I rotate credentials?
**A**:
- User API keys: 90 days
- Service credentials: 30 days
- Encryption key: Annually
- Or immediately if compromised

### Q: Can I use the same encryption key across environments?
**A**: NO. Use separate keys for:
- Production
- Staging
- Development

### Q: What encryption algorithm is used?
**A**: Fernet (AES-128-CBC with HMAC-SHA256 for authentication). Industry-standard symmetric encryption.

### Q: Are credentials encrypted in transit?
**A**: Yes, all API calls use HTTPS/TLS. Credentials are only decrypted in memory when needed.

---

## Support

**Security Issues**: security@your-domain.com
**Credential Problems**: Support team via Slack #ops-center
**Documentation**: This file is maintained in Git

---

**Last Updated**: October 22, 2025
**Next Review**: January 22, 2026 (Quarterly)
