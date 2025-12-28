# Keycloak API Credentials

**Created**: 2025-10-23
**Purpose**: Programmatic management of Keycloak uchub realm

## API Service Account

**Client ID**: `ops-center-api`
**Client Secret**: `OpsCenterAPIKey2025MagicUnicorn`
**Realm**: `uchub`
**Permissions**: `manage-clients`

## Getting an Access Token

```bash
curl -X POST http://uchub-keycloak:8080/realms/uchub/protocol/openid-connect/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'client_id=ops-center-api' \
  -d 'client_secret=OpsCenterAPIKey2025MagicUnicorn' \
  -d 'grant_type=client_credentials'
```

## Example Usage

### Get Access Token
```bash
TOKEN=$(curl -s -X POST http://uchub-keycloak:8080/realms/uchub/protocol/openid-connect/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'client_id=ops-center-api' \
  -d 'client_secret=OpsCenterAPIKey2025MagicUnicorn' \
  -d 'grant_type=client_credentials' | jq -r '.access_token')
```

### List Clients
```bash
curl -s http://uchub-keycloak:8080/admin/realms/uchub/clients \
  -H "Authorization: Bearer $TOKEN"
```

### Update Client
```bash
CLIENT_ID="1c85fa2e-f379-46c4-b24a-a269c7d4bdef"  # ops-center client
curl -X PUT http://uchub-keycloak:8080/admin/realms/uchub/clients/$CLIENT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "redirectUris": ["https://your-domain.com/auth/callback"],
    "webOrigins": ["https://your-domain.com"]
  }'
```

## Security Notes

- **KEEP THIS FILE SECURE**: Contains sensitive credentials
- Token expires after 300 seconds (5 minutes)
- Refresh token not available for client_credentials grant
- Service account has limited permissions (manage-clients only)

## ops-center Client Configuration

**Client UUID**: `1c85fa2e-f379-46c4-b24a-a269c7d4bdef`
**Redirect URIs**:
- `https://your-domain.com/auth/callback`
- `http://localhost:8000/auth/callback`

**Web Origins**:
- `https://your-domain.com`
- `http://localhost:8000`
