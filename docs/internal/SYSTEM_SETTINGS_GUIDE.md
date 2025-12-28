# System Settings - GUI Environment Variable Management

**Created**: October 20, 2025
**Access**: `/admin/system/system-settings` (Admin only)

## Overview

The System Settings feature allows administrators to manage environment variables through a user-friendly GUI instead of manually editing `.env` files. This provides:

- **Security**: Sensitive values (API keys, secrets) are automatically masked
- **Validation**: Real-time validation of key formats and required fields
- **Testing**: Test API connections directly from the UI
- **Organization**: Settings categorized by type (Security, Billing, LLM, Email, Storage)
- **Audit Trail**: Track when settings were created and last updated

## Features

### 1. Settings Table
- **View All Settings**: Browse all environment variables in a table view
- **Search**: Filter settings by key name or description
- **Category Tabs**: Filter by category (All, Security, Billing, LLM, Email, Storage)
- **Masked Values**: Sensitive values show only last 8 characters (e.g., "••••••••xyz12345")
- **Show/Hide Toggle**: Click eye icon to temporarily reveal full value
- **Copy to Clipboard**: Quick copy button for each value

### 2. Add/Edit Settings
- **Quick Templates**: Pre-filled templates for common settings (e.g., STRIPE_SECRET_KEY, OPENAI_API_KEY)
- **Category Selection**: Choose from 5 categories
- **Key Validation**: Enforces UPPERCASE_WITH_UNDERSCORES format
- **Description**: Add helpful descriptions for each setting
- **Sensitive Flag**: Mark values as sensitive to auto-mask in UI

### 3. Test Connections
- **API Key Testing**: Test LLM API keys (OpenRouter, OpenAI, Anthropic)
- **Email Validation**: Validate SMTP configuration
- **Billing Integration**: Verify Stripe/Lago keys
- **One-Click Testing**: Click cable icon to test connection

### 4. Delete Settings
- **Confirmation Dialog**: Prevent accidental deletions
- **Cascade Updates**: Automatically updates .env file on delete

## Usage

### Adding a New Setting

1. Click **Add Setting** button
2. Select **Category** (e.g., "LLM")
3. Click a **Quick Template** chip (e.g., "OPENAI_API_KEY") or enter manually
4. Enter the **Value** (use show/hide icon if needed)
5. Add a **Description** (optional)
6. Toggle **Sensitive** if value should be masked
7. Click **Create**

**Example - Adding OpenAI API Key**:
```
Category: LLM
Key: OPENAI_API_KEY
Value: sk-proj-abc123xyz...
Description: OpenAI API key for GPT-4 access
Sensitive: ✓ (checked)
```

### Editing an Existing Setting

1. Click **Edit** icon (pencil) on the row
2. Modify **Value**, **Description**, **Category**, or **Sensitive** flag
3. Click **Update**

**Note**: The Key cannot be changed after creation. Delete and recreate if needed.

### Testing a Connection

1. Find the setting in the table (e.g., OPENROUTER_API_KEY)
2. Click the **Cable** icon in the Actions column
3. Wait for test result notification
   - ✅ Success: "OpenRouter API key is valid"
   - ❌ Failure: "OpenRouter API returned status 401"

**Supported Tests**:
- `OPENROUTER_API_KEY` → Tests OpenRouter API
- `OPENAI_API_KEY` → Tests OpenAI API
- `ANTHROPIC_API_KEY` → Tests Anthropic Claude API
- `SMTP_*` → Validates SMTP configuration (format check)
- `STRIPE_*`, `LAGO_*` → Validates billing keys (format check)

### Deleting a Setting

1. Click **Delete** icon (trash) on the row
2. Confirm in the dialog: "Are you sure you want to delete..."
3. Setting is removed from database and .env file

## Backend API

All settings are stored in `/app/data/system_settings.json` and automatically synced to `/app/.env.settings`.

**API Endpoints**:
- `GET /api/v1/admin/system-settings` - List all settings
- `GET /api/v1/admin/system-settings/{key}` - Get specific setting
- `POST /api/v1/admin/system-settings` - Create new setting
- `PUT /api/v1/admin/system-settings/{key}` - Update setting
- `DELETE /api/v1/admin/system-settings/{key}` - Delete setting
- `POST /api/v1/admin/system-settings/{key}/test` - Test connection

## Security Considerations

1. **Admin Only**: Only users with `role: admin` can access this page
2. **Masked Display**: Sensitive values are masked by default (show last 8 chars)
3. **Secure Storage**: Values stored in JSON file with restricted permissions
4. **No Plaintext Logs**: API keys are never logged in full
5. **HTTPS Recommended**: Use HTTPS in production to encrypt data in transit

## Common Settings by Category

### Security
- `BYOK_ENCRYPTION_KEY` - Encryption key for BYOK (Bring Your Own Key)
- `JWT_SECRET_KEY` - Secret key for JWT token signing
- `SESSION_SECRET` - Session encryption secret

### Billing
- `STRIPE_SECRET_KEY` - Stripe API secret key
- `STRIPE_PUBLISHABLE_KEY` - Stripe publishable key
- `LAGO_API_KEY` - Lago billing API key
- `LAGO_API_URL` - Lago API endpoint URL

### LLM
- `OPENROUTER_API_KEY` - OpenRouter API key for LLM access
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic Claude API key
- `LITELLM_MASTER_KEY` - LiteLLM proxy master key

### Email
- `SMTP_USERNAME` - SMTP server username
- `SMTP_PASSWORD` - SMTP server password
- `SMTP_HOST` - SMTP server hostname
- `SMTP_PORT` - SMTP server port (e.g., 587)

### Storage
- `AWS_ACCESS_KEY_ID` - AWS access key for S3 storage
- `AWS_SECRET_ACCESS_KEY` - AWS secret access key
- `S3_BUCKET_NAME` - S3 bucket name for file storage

## File Structure

**Frontend**:
- `/src/pages/SystemSettings.jsx` (800 lines) - Main page
- `/src/components/SystemSettingCard.jsx` (250 lines) - Table row component
- `/src/components/EditSettingModal.jsx` (350 lines) - Add/Edit modal

**Backend**:
- `/backend/system_settings_api.py` - FastAPI router with CRUD endpoints
- `/app/data/system_settings.json` - Persistent storage (created automatically)
- `/app/.env.settings` - Auto-generated .env file (synced on changes)

## Troubleshooting

### Settings not loading
**Problem**: Table shows "Failed to load settings"
**Solution**:
1. Check backend logs: `docker logs ops-center-direct`
2. Verify API endpoint is accessible: `curl http://localhost:8084/api/v1/admin/system-settings`
3. Check file permissions on `/app/data/`

### Cannot create setting
**Problem**: "Key must be uppercase with underscores"
**Solution**: Use format like `MY_API_KEY`, not `my-api-key` or `myApiKey`

### Test connection fails
**Problem**: "OpenAI test failed: Connection timeout"
**Solution**:
1. Verify API key is correct
2. Check network connectivity from container
3. Ensure API service is not rate-limiting

### Setting deleted but still in environment
**Problem**: Variable still set after deletion
**Solution**:
1. Restart the ops-center container: `docker restart ops-center-direct`
2. Check `/app/.env.settings` file was updated
3. May need to reload environment in running services

## Best Practices

1. **Use Descriptive Keys**: `OPENAI_GPT4_KEY` is better than `KEY1`
2. **Add Descriptions**: Help future admins understand what each setting does
3. **Test Before Saving**: Use test connection before deploying to production
4. **Mark Sensitive Data**: Always mark API keys/secrets as sensitive
5. **Regular Backups**: Settings are in `/app/data/system_settings.json` - include in backups
6. **Audit Changes**: Check "Last Updated" column to track recent changes
7. **Environment-Specific**: Consider separate settings for dev/staging/prod

## Integration with Other Services

The System Settings feature integrates with:

- **LLM Management**: API keys used for LLM provider authentication
- **Email Settings**: SMTP credentials from system settings
- **Billing Dashboard**: Stripe/Lago keys for payment processing
- **BYOK System**: Encryption keys for Bring Your Own Key feature

Changes to settings take effect immediately for new API calls. Some services may require restart to pick up new values.

## Future Enhancements

Planned features for future versions:

- [ ] **Environment Profiles**: Separate settings for dev/staging/production
- [ ] **Import/Export**: Bulk import settings from .env files
- [ ] **Version History**: Track changes over time with rollback capability
- [ ] **Secret Rotation**: Automated API key rotation schedules
- [ ] **Webhook Notifications**: Alert on setting changes
- [ ] **Encrypted Storage**: Encrypt values at rest using master key
- [ ] **RBAC**: Fine-grained permissions per setting
- [ ] **Batch Operations**: Update multiple settings at once

---

**Support**: For issues or questions, check the main Ops-Center documentation or contact the platform administrator.
