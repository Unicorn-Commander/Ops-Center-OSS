# Local User Management UI - Quick Reference Guide

**Created**: October 20, 2025
**Status**: Production Ready
**Access**: `/admin/system/local-users`

---

## Overview

The Local User Management interface provides a comprehensive UI for managing Linux users on the Ops-Center server. This is designed for **system administrators** to manage server access and permissions.

**Key Features**:
- Create/delete Linux users
- Reset passwords with strength meter
- Manage SSH keys
- Grant/revoke sudo privileges
- Real-time statistics dashboard
- Search and pagination

---

## UI Components

### 1. Header & Actions

**Location**: Top of page

**Elements**:
- **Page Title**: "Local User Management" with icon
- **Refresh Button**: Reload user list
- **Create User Button**: Open create user modal

### 2. Statistics Cards (3 Cards)

| Card | Metric | Description |
|------|--------|-------------|
| **Total Users** | Count | All Linux users on system |
| **Active Sessions** | Count | Users logged in within 24 hours |
| **Sudo Users** | Count | Users with sudo privileges |

**Icons**:
- Total Users: PeopleIcon (blue)
- Active Sessions: CheckCircleIcon (green)
- Sudo Users: AdminIcon (orange)

### 3. Search Bar

**Functionality**:
- Real-time filtering by username
- Case-insensitive search
- Updates table dynamically

### 4. User Table

**Columns**:
1. **Username** - Login name with terminal icon
2. **UID** - User ID as chip badge
3. **Groups** - Comma-separated group list
4. **Sudo** - Badge showing sudo status (Warning chip for sudo, Outlined for user)
5. **Home Directory** - Full path with folder icon
6. **Shell** - Default shell (e.g., /bin/bash)
7. **Last Login** - Timestamp or "Never"
8. **Actions** - 4 icon buttons

**Action Buttons** (per row):
- **Reset Password** (PasswordIcon) - Opens password reset modal
- **Manage SSH Keys** (VpnKeyIcon) - Opens SSH key management modal
- **Grant/Revoke Sudo** (SecurityIcon) - Toggle sudo access (orange if sudo active)
- **Delete User** (DeleteIcon, red) - Opens confirmation dialog

**Table Features**:
- Hover effect on rows
- Pagination controls (10, 25, 50, 100 per page)
- Loading spinner when fetching data
- Empty state messages

---

## Modals & Dialogs

### 1. Create User Modal

**Trigger**: "Create User" button in header

**Form Fields**:
- **Username** (required) - Linux username, lowercase, no spaces
- **Password** (required) - Password with show/hide toggle
- **Home Directory** (optional) - Default: /home/{username}
- **Shell** (dropdown) - Options: bash, sh, zsh, fish, nologin
- **Grant sudo privileges** (toggle) - Checkbox for sudo access

**Actions**:
- **Cancel** - Close without saving
- **Create User** - Submit form (disabled if username/password empty)

**Validation**:
- Username and password are required
- Home directory placeholder: `/home/username`
- Default shell: `/bin/bash`

---

### 2. Password Reset Modal

**Trigger**: Click "Reset Password" icon on user row

**Features**:
- **Info Alert**: Shows username being reset
- **Password Input**: Text field with show/hide toggle
- **Password Strength Meter**:
  - Visual progress bar (red < 40%, orange < 70%, green ≥ 70%)
  - Percentage display
  - Criteria:
    - Length ≥ 8: +25%
    - Length ≥ 12: +25%
    - Mixed case: +25%
    - Numbers: +15%
    - Special chars: +10%

**Actions**:
- **Cancel** - Close without resetting
- **Reset Password** (warning color) - Submit new password

---

### 3. SSH Key Management Modal

**Trigger**: Click "Manage SSH Keys" icon on user row

**Title**: "SSH Keys - {username}"

**Sections**:

#### Current SSH Keys
- **Display**: List of existing keys
- **Format**: First 60 characters + "..." in monospace font
- **Actions**: Delete button (red) for each key
- **Empty State**: Info alert "No SSH keys configured"

#### Add New SSH Key
- **Text Area**: Multi-line input (4 rows)
- **Placeholder**: `ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...`
- **Helper Text**: "Paste the public key (starts with ssh-rsa, ssh-ed25519, etc.)"
- **Add Button**: Disabled if textarea empty

**Actions**:
- **Close** - Exit modal

**API Calls**:
- Loads keys on modal open: `GET /api/v1/local-users/{username}/ssh-keys`
- Add key: `POST /api/v1/local-users/{username}/ssh-keys`
- Delete key: `DELETE /api/v1/local-users/{username}/ssh-keys/{index}`

---

### 4. Delete Confirmation Modal

**Trigger**: Click "Delete User" icon on user row

**Warning Level**: HIGH (Error severity)

**Content**:
- **Error Alert**: "This action cannot be undone!"
- **Confirmation Text**: "Are you sure you want to delete the user **{username}**?"
- **Warning Text**: "This will remove the user account and may delete their home directory and files."

**Actions**:
- **Cancel** - Close without deleting
- **Delete User** (red, destructive) - Confirm deletion

---

## API Integration

All API calls use `credentials: 'include'` for authentication.

### Endpoints Used

```javascript
// Fetch users
GET /api/v1/local-users

// Create user
POST /api/v1/local-users
Body: { username, password, sudo, home_directory?, shell? }

// Reset password
PUT /api/v1/local-users/{username}/password
Body: { password }

// SSH key management
GET    /api/v1/local-users/{username}/ssh-keys
POST   /api/v1/local-users/{username}/ssh-keys
       Body: { key }
DELETE /api/v1/local-users/{username}/ssh-keys/{index}

// Sudo operations
POST /api/v1/local-users/{username}/grant-sudo
POST /api/v1/local-users/{username}/revoke-sudo

// Delete user
DELETE /api/v1/local-users/{username}
```

### Error Handling

All API errors display toast notifications:
- **Success**: Green toast (e.g., "User created successfully")
- **Error**: Red toast with error message from API
- **Info**: Blue toast for informational messages

---

## Theme Support

The UI automatically adapts to the current Ops-Center theme:

### Unicorn Theme
- Background: Purple/pink gradient
- Paper: White/10 with backdrop blur
- Text: White
- Buttons: Purple to pink gradient

### Light Theme
- Background: Gray-50
- Paper: White
- Text: Gray-900
- Buttons: Blue-600

### Dark Theme
- Background: Slate-900
- Paper: Slate-800
- Text: White
- Buttons: Blue-600

**Theme Detection**: Uses `useTheme()` context from `ThemeContext.jsx`

---

## Security Features

### Client-Side Validation
- Username/password required before submission
- SSH key format checked client-side (basic validation)
- Password strength calculated and displayed

### Confirmation Dialogs
- **Delete User**: Requires explicit confirmation with warning
- **Sudo Operations**: Visual indicators (orange chip) for sudo users

### Password Handling
- Password fields have show/hide toggle
- Passwords never displayed in logs or error messages
- Strong password encouraged via strength meter

---

## User Experience

### Loading States
- **Initial Load**: CircularProgress spinner in table center
- **Empty State**: "No users found" message if list empty
- **Search Results**: "No users found matching your search" if search yields no results

### Toast Notifications
- **Position**: Bottom-right corner
- **Duration**: 6 seconds auto-hide
- **Close Button**: Manual dismiss option
- **Severity Colors**:
  - Success: Green
  - Error: Red
  - Info: Blue
  - Warning: Orange

### Responsive Design
- **Mobile Friendly**: Table scrolls horizontally on small screens
- **Stats Cards**: Stack vertically on mobile (Grid breakpoints)
- **Modals**: Full-width on small screens

---

## File Locations

### Frontend
- **Page Component**: `/src/pages/LocalUsers.jsx` (761 lines)
- **Route Definition**: `/src/App.jsx` (line 259)
- **Navigation Link**: `/src/components/Layout.jsx` (lines 314-319)

### Backend
- **API Endpoints**: `/backend/local_user_api.py`
- **Documentation**: `/backend/docs/LOCAL_USER_API.md`

---

## Testing Checklist

### Basic Operations
- [ ] Page loads without errors
- [ ] Stats cards display correct counts
- [ ] User table populates from API
- [ ] Search filters users correctly
- [ ] Pagination works (change rows per page)

### Create User
- [ ] Modal opens when clicking "Create User"
- [ ] Form validation works (required fields)
- [ ] Password show/hide toggle works
- [ ] Shell dropdown has all options
- [ ] Sudo checkbox toggles correctly
- [ ] User created successfully and appears in list
- [ ] Toast notification shows success

### Password Reset
- [ ] Modal opens with correct username
- [ ] Password strength meter updates dynamically
- [ ] Show/hide password works
- [ ] Reset succeeds and shows toast

### SSH Keys
- [ ] Modal opens and loads existing keys
- [ ] Keys display correctly (truncated)
- [ ] Add key textarea accepts paste
- [ ] Add button enabled when key entered
- [ ] Delete key works with confirmation
- [ ] Toast notifications for add/delete

### Sudo Operations
- [ ] Grant sudo adds orange badge
- [ ] Revoke sudo removes badge
- [ ] Toast confirms action

### Delete User
- [ ] Confirmation modal appears
- [ ] Warning alert displays
- [ ] Cancel closes without deleting
- [ ] Delete removes user from list
- [ ] Toast confirms deletion

### Error Handling
- [ ] API errors show in toast
- [ ] Network errors handled gracefully
- [ ] Empty states display correctly
- [ ] Invalid SSH keys rejected

---

## Known Limitations

1. **No Bulk Operations**: Currently one user at a time
2. **No User Groups Management**: Only displays groups, cannot modify
3. **No Home Directory Customization**: Cannot change after creation
4. **No Shell Change**: Shell set at creation, cannot modify later
5. **No User Disable**: Only delete option (no suspend/enable)

**Future Enhancements**:
- Bulk user creation via CSV
- Group membership management
- User activity logs
- Shell modification post-creation
- Temporary account suspension

---

## Troubleshooting

### Users Not Loading
**Symptom**: Empty table or loading spinner indefinitely

**Solutions**:
1. Check browser console for API errors
2. Verify backend is running: `docker ps | grep ops-center`
3. Check API endpoint: `curl http://localhost:8084/api/v1/local-users`
4. Review backend logs: `docker logs ops-center-direct -f`

### Create User Fails
**Symptom**: Toast shows "Failed to create user"

**Common Causes**:
- Username already exists
- Invalid characters in username
- Password doesn't meet system requirements
- Insufficient permissions on server

**Check**:
- Backend logs for specific error
- Ensure username is lowercase, no spaces
- Try different username

### SSH Keys Won't Add
**Symptom**: "Failed to add SSH key" error

**Common Causes**:
- Invalid SSH key format
- Key already exists
- .ssh directory doesn't exist
- Permission issues

**Validation**:
- Key must start with: `ssh-rsa`, `ssh-ed25519`, `ecdsa-sha2-nistp256`, etc.
- Ensure key is complete (no truncation)

### Sudo Toggle Fails
**Symptom**: "Failed to modify sudo privileges"

**Common Causes**:
- User is already in sudoers
- `/etc/sudoers.d/` directory not writable
- User is root (cannot modify root sudo)

**Check**:
- Backend has sufficient permissions
- Not trying to modify system users (root, systemd, etc.)

---

## Maintenance

### Regular Tasks
1. **Monitor User Count**: Check stats dashboard regularly
2. **Review Sudo Users**: Audit who has sudo access monthly
3. **Clean Inactive Users**: Remove users with no recent login
4. **Audit SSH Keys**: Review authorized_keys periodically

### Best Practices
- Use strong passwords (≥70% strength)
- Document user purposes in external system
- Rotate passwords quarterly
- Remove SSH keys when no longer needed
- Grant sudo sparingly (principle of least privilege)

---

## Support

**Documentation**:
- Backend API: `/backend/docs/LOCAL_USER_API.md`
- UC-Cloud Docs: `/opt/uc-cloud/CLAUDE.md`
- Ops-Center Docs: `/services/ops-center/CLAUDE.md`

**For Issues**:
1. Check backend logs: `docker logs ops-center-direct`
2. Test API directly: `curl -X GET http://localhost:8084/api/v1/local-users`
3. Review browser console for frontend errors
4. Check Keycloak authentication status

---

**Remember**: This interface manages **actual Linux users** on the server. Deletions are permanent and may remove user data. Always confirm before destructive operations!
