# Ops Center Role Mapping Documentation

## Overview

The ops-center backend now integrates with Keycloak/Authentik for role-based access control (RBAC). User roles are automatically mapped from Keycloak groups and roles to ops-center's role hierarchy.

## Role Hierarchy

Ops-center uses a four-tier role system:

1. **admin** - Full system access, all administrative capabilities
2. **power_user** - Advanced features and configuration access
3. **user** - Standard user access to core features
4. **viewer** - Read-only access (default fallback)

## Keycloak/Authentik Configuration

### Required Setup in Keycloak/Authentik

To assign roles to users, create groups or roles in Keycloak/Authentik with the following names:

#### Admin Role
- Group: `admins`, `administrators`, or `ops-center-admin`
- Role: `admin`

#### Power User Role
- Group: `power_users`, `powerusers`, or `ops-center-poweruser`
- Role: `power_user`

#### User Role
- Group: `users`, `standard_users`, or `ops-center-user`
- Role: `user`

#### Viewer Role
- Group: `viewers`, `read_only`, or `ops-center-viewer`
- Role: `viewer`

### Group Assignment in Authentik

1. Navigate to **Directory** > **Groups** in Authentik admin panel
2. Create groups with names matching the role mappings above
3. Add users to appropriate groups
4. Users will automatically receive the corresponding role upon login

### Role Assignment in Keycloak

1. Navigate to **Realm Roles** or **Client Roles** in Keycloak
2. Create roles matching the names above
3. Assign roles to users via **Users** > **Role Mappings**
4. Users will receive the role upon next login

## Role Mapping Logic

### Priority Order

When a user has multiple groups/roles, the highest priority role is assigned:

1. **admin** (highest priority)
2. **power_user**
3. **user**
4. **viewer** (lowest priority)

### Example

If a user is in both `users` and `power_users` groups, they will be assigned the `power_user` role.

### Data Sources

The role mapper checks multiple data sources in the Keycloak/Authentik userinfo response:

1. **groups** - Standard OIDC groups claim
2. **ak_groups** - Authentik-specific groups claim
3. **realm_access.roles** - Keycloak realm roles
4. **resource_access.[client].roles** - Keycloak client-specific roles

### Default Fallback

If no matching groups or roles are found, users are assigned the **viewer** role by default. This ensures:
- New users have limited access by default
- Security by default (principle of least privilege)
- No users are accidentally granted admin access

## Implementation Details

### Files Modified

1. **role_mapper.py** - New module for role mapping logic
   - Location: `/home/deploy/Production/UC-1-Pro/services/ops-center/backend/role_mapper.py`
   - Functions:
     - `map_keycloak_role(user_info)` - Maps Keycloak data to role
     - `add_role_to_user_info(user_info)` - Adds role to user data
     - `extract_groups_from_user_info(user_info)` - Extracts all groups/roles

2. **server.py** - Updated authentication functions
   - Line 49: Import role_mapper functions
   - Line 867-888: Updated `get_current_user()` to use role mapper
   - Line 3115-3119: OAuth callback role mapping (first location)
   - Line 3216-3220: OAuth callback role mapping (second location)

### Authentication Flow

1. User authenticates via Keycloak/Authentik
2. OAuth callback receives access token
3. Backend fetches user info from `/application/o/userinfo/` endpoint
4. `add_role_to_user_info()` maps Keycloak groups/roles to ops-center role
5. Role is stored in session data
6. Subsequent requests use cached role from session
7. Role is logged for audit purposes

### Logging

All role assignments are logged for debugging and audit:

```
INFO: User 'john.doe' mapped to role 'power_user' via group/role 'power_users'
INFO: OAuth callback: User 'john.doe' logged in with role 'power_user'
```

## Testing

### Manual Testing

1. Create test users in Authentik/Keycloak
2. Assign different groups to each user
3. Login via ops-center
4. Check logs for role assignment
5. Verify access to different endpoints based on role

### Automated Tests

Run the role mapper test suite:

```bash
cd /home/deploy/Production/UC-1-Pro/services/ops-center/backend
python3 role_mapper.py
```

Expected output:
```
Running role mapper tests...

✓ Admin user with groups: expected 'admin', got 'admin'
✓ Power user with Authentik groups: expected 'power_user', got 'power_user'
✓ Standard user: expected 'user', got 'user'
✓ User with no groups (default viewer): expected 'viewer', got 'viewer'
✓ User with Keycloak realm roles: expected 'admin', got 'admin'
```

## API Endpoints & Role Requirements

### Admin Only
- System configuration
- User management
- Service deployment
- Security settings

### Power User & Admin
- Advanced configurations
- Docker service management
- Network settings
- Extension management

### User, Power User & Admin
- Basic operations
- File uploads
- Log viewing
- Dashboard access

### All Roles (including Viewer)
- View system status
- Read logs
- View dashboard (read-only)

## Troubleshooting

### Issue: User always gets 'viewer' role

**Cause**: No matching groups found in Keycloak/Authentik

**Solution**:
1. Check user's group membership in Keycloak/Authentik
2. Verify group names match the mapping (case-insensitive)
3. Check logs for debug output showing available groups
4. Ensure groups are included in the userinfo endpoint response

### Issue: Role not updating after group change

**Cause**: Role is cached in session

**Solution**:
1. User needs to logout and login again
2. Clear session cookie
3. Or restart the backend service to clear all sessions

### Issue: Cannot access admin endpoints

**Cause**: User role is not 'admin'

**Solution**:
1. Add user to 'admins' group in Keycloak/Authentik
2. Verify group assignment in admin panel
3. Logout and login again
4. Check logs for role assignment

## Security Considerations

### Principle of Least Privilege

- Default role is 'viewer' (read-only)
- Users must be explicitly granted higher roles
- No automatic admin assignment

### Session Security

- Roles are stored in session, not in cookies
- Session tokens are secure random values
- Sessions expire after 24 hours
- HTTPS-only cookies in production

### Audit Trail

- All role assignments are logged
- Login events include username and assigned role
- Failed authentication attempts are logged

## Future Enhancements

### Planned Features

1. **Dynamic Role Management** - Admin UI to manage role mappings
2. **Custom Role Definitions** - Define custom roles beyond the four defaults
3. **Fine-grained Permissions** - Per-endpoint permission control
4. **Role Expiration** - Time-limited role assignments
5. **Multi-factor Requirements** - Require MFA for admin role

### API Enhancements

1. **GET /api/auth/roles** - List available roles
2. **GET /api/auth/user/role** - Get current user's role
3. **GET /api/auth/permissions** - List permissions for current role
4. **POST /api/auth/role/override** - Admin can temporarily elevate user role

## References

- Keycloak Documentation: https://www.keycloak.org/docs/latest/server_admin/
- Authentik Documentation: https://goauthentik.io/docs/
- OIDC Standard: https://openid.net/connect/
- UC-1 Pro Docs: https://github.com/Unicorn-Commander/UC-1-Pro

## Support

For issues or questions:
1. Check logs: `docker logs unicorn-ops-center`
2. Review Authentik logs: `docker logs authentik-server`
3. Run role mapper tests: `python3 role_mapper.py`
4. Contact: admin@example.com
