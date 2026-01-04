# Keycloak Configuration for Ops-Center

This directory contains pre-configured Keycloak realm settings for Ops-Center.

## Quick Start

### Option 1: Import via Admin Console

1. Log into Keycloak Admin Console (`http://localhost:8080/admin`)
2. Select "Create realm" from the realm dropdown
3. Click "Browse..." and select `realm-export.json`
4. Click "Create"

### Option 2: Import via CLI

```bash
# Copy file to container
docker cp keycloak/realm-export.json keycloak:/tmp/realm-export.json

# Import realm
docker exec -it keycloak /opt/keycloak/bin/kc.sh import --file /tmp/realm-export.json
```

### Option 3: Mount at startup

```yaml
# docker-compose.yml
services:
  keycloak:
    image: quay.io/keycloak/keycloak:latest
    volumes:
      - ./keycloak/realm-export.json:/opt/keycloak/data/import/realm-export.json
    command: start-dev --import-realm
```

## After Import: Required Steps

### 1. Generate New Client Secrets

The export contains placeholder secrets. Generate new ones:

```bash
# In Keycloak Admin Console:
# 1. Go to Clients > ops-center > Credentials
# 2. Click "Regenerate"
# 3. Copy the new secret to your .env.auth file
```

### 2. Configure Identity Providers

The export includes disabled identity provider stubs. To enable:

**Google:**
1. Create OAuth credentials at [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Set redirect URI: `https://your-keycloak-url/realms/ops-center/broker/google/endpoint`
3. In Keycloak: Identity Providers > google > Enter Client ID/Secret > Enable

**GitHub:**
1. Create OAuth App at [GitHub Developer Settings](https://github.com/settings/developers)
2. Set callback URL: `https://your-keycloak-url/realms/ops-center/broker/github/endpoint`
3. In Keycloak: Identity Providers > github > Enter Client ID/Secret > Enable

**Microsoft:**
1. Register app at [Azure Portal](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps)
2. Set redirect URI: `https://your-keycloak-url/realms/ops-center/broker/microsoft/endpoint`
3. In Keycloak: Identity Providers > microsoft > Enter Client ID/Secret > Enable

### 3. Update Redirect URIs for Production

In Clients > ops-center > Settings, update:
- Valid Redirect URIs: `https://your-domain.com/*`
- Web Origins: `https://your-domain.com`

## What's Included

### Clients
- `ops-center` - Main application client (confidential)
- `ops-center-api` - Service account for backend operations

### Roles
| Role | Description |
|------|-------------|
| `admin` | Full administrative access |
| `user` | Standard user access |
| `org-admin` | Organization administrator |
| `developer` | Developer with API permissions |
| `viewer` | Read-only access |

### Groups
- `/Admins` - Users with admin role
- `/Users` - Standard users
- `/Developers` - Developer accounts

### Protocol Mappers
Custom claims added to tokens:
- `subscription_tier` - User's subscription tier
- `organization_id` - User's organization
- `roles` - Realm roles

### Session Settings
| Setting | Value | Description |
|---------|-------|-------------|
| SSO Session Idle | 30 min | Idle timeout |
| SSO Session Max | 10 hours | Maximum session |
| Remember Me Idle | 7 days | With "Remember Me" |
| Access Token | 5 min | Token lifespan |

### Security
- Brute force protection enabled (5 failures = lockout)
- Password policy: 8+ chars, 1 digit, 1 uppercase, 1 special
- Security headers configured
- Event logging enabled

## Customization

### Adding Custom Attributes

To add user attributes that appear in tokens:

1. Go to Realm Settings > User Profile
2. Add new attribute
3. Go to Clients > ops-center > Client scopes > dedicated
4. Add mapper for the attribute

### Theming

To customize the login page:
1. Create theme in `themes/` directory
2. Mount to `/opt/keycloak/themes/`
3. Set in Realm Settings > Themes

## Troubleshooting

### "Realm already exists" error
```bash
# Delete existing realm first (loses all data!)
docker exec keycloak /opt/keycloak/bin/kc.sh delete-realm --realm ops-center
```

### Can't log in after import
- Verify client secret matches `.env.auth`
- Check redirect URIs include your app URL
- Ensure identity providers have correct callback URLs

### Tokens missing custom claims
- Verify protocol mappers exist in client
- Check "Add to ID token" and "Add to access token" are enabled
