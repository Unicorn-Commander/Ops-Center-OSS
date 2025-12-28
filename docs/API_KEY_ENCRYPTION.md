# API Key Encryption System - BYOK Implementation

## Overview

The BYOK (Bring Your Own Key) system securely encrypts user API keys using Fernet symmetric encryption and stores them in Authentik user attributes. This provides enhanced security and cross-device access to API keys.

## Architecture

### Components

1. **key_encryption.py** - Encryption/decryption utility using Fernet
2. **authentik_keys.py** - Authentik integration for user attribute storage
3. **api_keys_router.py** - REST API endpoints for key management
4. **UserSettings.jsx** - Frontend interface for managing keys

### Security Features

- **Fernet Symmetric Encryption**: Industry-standard encryption (AES-128-CBC + HMAC)
- **Environment-based Key**: Encryption key stored securely in environment variables
- **Authentik Storage**: Keys stored in Authentik user attributes (encrypted at rest)
- **Minimal Exposure**: Keys only decrypted when explicitly requested
- **Masked Display**: Keys shown masked by default (e.g., "sk-1234...5678")

## API Endpoints

### POST /api/v1/user/api-keys
Save a new encrypted API key

**Request:**
```json
{
  "provider": "openai",
  "api_key": "sk-1234567890abcdef",
  "name": "My OpenAI Key (Optional)"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "API key for openai saved successfully",
  "provider": "openai"
}
```

### GET /api/v1/user/api-keys
List all API keys (masked)

**Response:**
```json
{
  "keys": [
    {
      "provider": "openai",
      "name": "My OpenAI Key",
      "masked_key": "sk-12...ef",
      "created_at": "2025-10-02T12:00:00Z",
      "updated_at": "2025-10-02T12:00:00Z"
    }
  ],
  "count": 1
}
```

### GET /api/v1/user/api-keys/{provider}
Get decrypted API key for specific provider

**Response:**
```json
{
  "provider": "openai",
  "api_key": "sk-1234567890abcdef",
  "name": "My OpenAI Key"
}
```

### PUT /api/v1/user/api-keys/{provider}
Update an existing API key

**Request:**
```json
{
  "api_key": "sk-newkey123456",  // optional
  "name": "Updated Name"         // optional
}
```

### DELETE /api/v1/user/api-keys/{provider}
Delete an API key

**Response:**
```json
{
  "status": "success",
  "message": "API key for openai deleted successfully",
  "provider": "openai"
}
```

## Environment Configuration

### Required Environment Variables

Add to `/home/muut/Production/UC-1-Pro/.env`:

```bash
# Encryption key for API keys (generate with command below)
ENCRYPTION_KEY=pXfS-0VwQPilpOvRaQOivJIBFUOrgT9toMtjyr2NZqo=

# Authentik API token (from Authentik admin panel)
AUTHENTIK_API_TOKEN=ak_f3c1ae010853720d0e37e3efa95d5afb51201285

# Authentik URL (internal Docker network)
AUTHENTIK_URL=http://authentik-server:9000
```

### Generate Encryption Key

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Generate Authentik API Token

1. Visit: https://auth.your-domain.com/if/admin/#/core/tokens
2. Click "Create"
3. User: Select your admin user
4. Expiry: Set to never expire (or desired expiry)
5. Copy the generated token

## Frontend Integration

The UserSettings.jsx component provides:

- **Add API Key**: Modal dialog to add new provider keys
- **List Keys**: Display all keys with masked values
- **View Key**: Click eye icon to decrypt and view key
- **Edit Key**: Update key name or value
- **Delete Key**: Remove key from storage
- **Security Notice**: Green info box explaining encryption

## Supported Providers

- **OpenAI** (sk-...)
- **Anthropic** (sk-ant-...)
- **Cohere** (cohere-...)
- **HuggingFace** (hf_...)
- **OpenRouter** (sk-or-...)
- **Together AI** (together-...)
- **Replicate** (r8_...)
- **Custom Endpoint** (http://...)

## Data Flow

### Saving a Key

1. User enters API key in UserSettings.jsx
2. Frontend POSTs to `/api/v1/user/api-keys`
3. Backend encrypts key using `KeyEncryption.encrypt_key()`
4. Backend saves encrypted key to Authentik user attributes via API
5. Authentik stores in PostgreSQL (encrypted at rest)

### Retrieving a Key

1. User clicks eye icon to view key
2. Frontend GETs from `/api/v1/user/api-keys/{provider}`
3. Backend retrieves encrypted key from Authentik
4. Backend decrypts key using `KeyEncryption.decrypt_key()`
5. Frontend temporarily stores decrypted key for display
6. Key hidden again when user clicks eye icon

### Listing Keys

1. Frontend GETs from `/api/v1/user/api-keys`
2. Backend retrieves all encrypted keys from Authentik
3. Backend decrypts each key only to create masked version
4. Frontend displays masked keys (e.g., "sk-12...ef")

## Testing

### Manual Testing

```bash
# 1. Start ops-center service
docker-compose up -d unicorn-ops-center

# 2. Check logs for router registration
docker logs unicorn-ops-center | grep "API Keys router"
# Should see: "✓ API Keys router registered at /api/v1/user/api-keys"

# 3. Access UserSettings page
# Open: https://your-domain.com/admin/settings
# Navigate to "API Keys (BYOK)" tab

# 4. Add a test key
# Provider: openai
# Key: sk-test1234567890abcdef
# Name: Test OpenAI Key

# 5. Verify in Authentik
# Visit: https://auth.your-domain.com/if/admin/#/core/users
# Click your user -> Attributes tab
# Should see: byok_api_keys.openai with encrypted_key field
```

### API Testing

```bash
# Set session cookie (replace with actual cookie from browser)
COOKIE="sessionid=YOUR_SESSION_COOKIE"

# Add API key
curl -X POST https://your-domain.com/api/v1/user/api-keys \
  -H "Cookie: $COOKIE" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_key": "sk-test1234567890",
    "name": "My Test Key"
  }'

# List API keys
curl https://your-domain.com/api/v1/user/api-keys \
  -H "Cookie: $COOKIE"

# Get decrypted key
curl https://your-domain.com/api/v1/user/api-keys/openai \
  -H "Cookie: $COOKIE"

# Update key
curl -X PUT https://your-domain.com/api/v1/user/api-keys/openai \
  -H "Cookie: $COOKIE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Key Name"
  }'

# Delete key
curl -X DELETE https://your-domain.com/api/v1/user/api-keys/openai \
  -H "Cookie: $COOKIE"
```

## Deployment

### Rebuild Frontend

```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center
npm run build
```

### Restart Services

```bash
docker-compose restart unicorn-ops-center
```

### Verify Deployment

```bash
# Check container logs
docker logs unicorn-ops-center

# Should see:
# ✓ API Keys router registered at /api/v1/user/api-keys
```

## Security Considerations

1. **Encryption Key Protection**
   - Store ENCRYPTION_KEY in environment variables only
   - Never commit to version control
   - Use different keys for dev/staging/production
   - Rotate keys periodically (requires re-encrypting all keys)

2. **Authentik API Token**
   - Use minimal required permissions
   - Set expiry date for production tokens
   - Rotate tokens regularly
   - Monitor token usage in Authentik logs

3. **Key Exposure**
   - Keys only decrypted on explicit user request
   - Decrypted keys not stored in frontend state
   - API responses with decrypted keys only sent over HTTPS
   - No logging of decrypted keys

4. **Database Security**
   - Authentik PostgreSQL should use encrypted storage
   - Regular backups of Authentik database
   - Access logs for user attribute changes

## Troubleshooting

### Router not registered
**Symptom**: API endpoints return 404

**Solution**:
```bash
# Check server.py imports
grep "api_keys_router" /home/muut/Production/UC-1-Pro/services/ops-center/backend/server.py

# Should see:
# from api_keys_router import router as api_keys_router
# app.include_router(api_keys_router)
```

### Encryption key error
**Symptom**: "ENCRYPTION_KEY environment variable not set"

**Solution**:
```bash
# Add to .env file
echo "ENCRYPTION_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" >> .env

# Restart service
docker-compose restart unicorn-ops-center
```

### Authentik API token error
**Symptom**: "Error saving API key: 403 Forbidden"

**Solution**:
1. Verify token is valid in Authentik admin panel
2. Check token has permissions to read/write user attributes
3. Ensure AUTHENTIK_API_TOKEN is set in .env
4. Restart ops-center service

### Keys not persisting
**Symptom**: Keys disappear after page reload

**Solution**:
1. Check browser console for API errors
2. Verify Authentik connection: `curl http://authentik-server:9000/api/v3/core/users/`
3. Check Authentik user attributes in admin panel
4. Verify user is authenticated (session cookie set)

## Migration from localStorage

For users who have existing keys in localStorage:

1. Keys will be read from localStorage on first load
2. Manually re-add each key through the UI
3. Keys will be encrypted and saved to Authentik
4. Old localStorage keys can be cleared:
   ```javascript
   localStorage.removeItem('uc1_byok_keys');
   ```

## Future Enhancements

- [ ] Automatic migration from localStorage to Authentik
- [ ] Key expiry dates and rotation reminders
- [ ] Multiple keys per provider (dev/staging/prod)
- [ ] Key usage tracking and analytics
- [ ] Audit log of key access events
- [ ] Role-based access for team accounts
- [ ] Integration with OpenWebUI and other services
- [ ] Key validation on save (test API call)
- [ ] Encrypted export/import of keys
