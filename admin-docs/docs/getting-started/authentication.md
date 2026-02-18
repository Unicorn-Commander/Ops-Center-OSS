# Authentication & Login

The UC-1 Pro Admin Dashboard uses secure JWT-based authentication to protect access to your AI infrastructure. This guide covers login, user management, and security best practices.

## Login Process

### Default Credentials
The system comes with a default administrator account:
- **Username**: `ucladmin`
- **Password**: `MagicUnicorn!8-)`

!!! danger "Security Warning"
    **Change the default password immediately** after first login. Using default credentials in production is a security risk.

### Login Flow
1. Navigate to the dashboard URL
2. Enter username and password
3. System validates credentials
4. JWT token is generated and stored
5. User is redirected to the main dashboard

![Login Process](../assets/images/login-flow.png)

## Authentication Features

### JWT Token-Based Security
- **Secure**: Industry-standard JSON Web Tokens
- **Stateless**: No server-side session storage required
- **Expirable**: Tokens automatically expire for security
- **Revocable**: Tokens can be invalidated if compromised

### Session Management
- **Auto-Logout**: Sessions expire after 1 hour of inactivity
- **Token Refresh**: Automatic token renewal for active users
- **Concurrent Sessions**: Multiple device login support
- **Session Monitoring**: Track active sessions per user

### Password Security
- **Bcrypt Hashing**: Military-grade password encryption
- **Salt Protection**: Unique salt per password
- **Complexity Requirements**: Enforced strong passwords
- **Breach Detection**: Monitor for compromised credentials

## User Interface Elements

### Login Screen
The login interface features:
- **Branded Design**: UC-1 Pro styling with company logos
- **Error Handling**: Clear feedback for login failures
- **Remember Credentials**: Browser password manager support
- **Responsive Design**: Works on all device sizes

### Navigation Elements
Once logged in:
- **User Profile**: Shows current user in sidebar
- **Logout Button**: Secure session termination
- **Session Timeout**: Automatic logout warning
- **Role Indicators**: Visual role identification

## User Roles & Permissions

### Administrator Role
Full system access including:
- User management and creation
- System configuration changes
- Service control and management
- Security settings modification
- API key generation and management

### Standard User Role (Future)
Limited access for regular users:
- Read-only dashboard access
- Basic monitoring capabilities
- Limited service information
- No administrative functions

## Security Best Practices

### Password Requirements
Strong passwords must include:
- Minimum 12 characters length
- Mix of uppercase and lowercase letters
- At least one number
- At least one special character
- No common dictionary words

### Account Security
- **Change Default Password**: Immediately after first login
- **Regular Updates**: Change passwords quarterly
- **Unique Passwords**: Don't reuse passwords
- **Two-Factor Authentication**: Enable when available

### Session Security
- **Logout When Done**: Always logout from shared computers
- **Monitor Sessions**: Check active sessions regularly
- **Report Suspicious Activity**: Contact admin for unusual access
- **Use HTTPS**: Always access over secure connections

## Managing Authentication

### Changing Your Password
1. Navigate to **Security & Access**
2. Click on your user profile
3. Select "Change Password"
4. Enter current password
5. Enter new password (twice)
6. Save changes

### Adding New Users
1. Go to **Security & Access** > **Users**
2. Click **Add User** button
3. Fill in user details:
   - Username (unique)
   - Email address
   - Full name
   - Initial password
   - Role assignment
4. Save user

### Managing User Sessions
1. In **Security & Access** > **Sessions**
2. View active sessions
3. Force logout suspicious sessions
4. Monitor login patterns

## API Authentication

### Using API Keys
For programmatic access:
1. Generate API key in **Security & Access**
2. Include in request headers:
   ```bash
   Authorization: Bearer your-api-key-here
   ```
3. Monitor API key usage
4. Rotate keys regularly

### JWT Tokens
For web applications:
1. Obtain token via login endpoint
2. Include in Authorization header
3. Handle token refresh
4. Implement logout cleanup

## Troubleshooting Authentication

### Common Login Issues

#### "Invalid Username or Password"
- Verify credentials are correct
- Check for typos and caps lock
- Ensure user account exists and is active

#### "Session Expired"
- Normal after 1 hour of inactivity
- Simply login again
- Consider extending session if needed

#### "Account Locked"
- Contact administrator
- Review security logs
- May indicate security incident

#### "Connection Error"
- Check network connectivity
- Verify dashboard service is running
- Try refreshing the page

### Browser Issues
- **Clear Cache**: Remove stored credentials
- **Disable Extensions**: Test with clean browser
- **Try Incognito**: Test private browsing mode
- **Update Browser**: Ensure modern browser version

### Network Issues
- **Firewall**: Ensure port 8084 is accessible
- **SSL/TLS**: Verify certificate validity
- **Proxy**: Check proxy configuration
- **DNS**: Verify hostname resolution

## Advanced Authentication

### LDAP Integration (Future)
- Active Directory integration
- Single sign-on (SSO) support
- Group-based permissions
- Centralized user management

### OAuth2 Support (Future)
- Google/Microsoft authentication
- Enterprise identity providers
- Social login options
- Federated identity management

### Multi-Factor Authentication (Future)
- TOTP authenticator apps
- SMS verification codes
- Hardware security keys
- Biometric authentication

## Security Monitoring

### Login Audit Trail
The system logs:
- Successful login attempts
- Failed login attempts
- Password change events
- Account lockout events
- Session expiration events

### Security Alerts
Monitor for:
- Multiple failed login attempts
- Unusual login locations
- Concurrent session anomalies
- Password brute force attacks
- Token manipulation attempts

### Best Practices
- **Regular Audits**: Review authentication logs
- **Monitor Metrics**: Track login patterns
- **Update Policies**: Keep security policies current
- **Train Users**: Educate on security practices
- **Incident Response**: Have procedures ready

---

*Next: Learn about the [User Interface Overview](ui-overview.md) or jump to [User Management](../admin/user-management.md) for detailed user administration.*