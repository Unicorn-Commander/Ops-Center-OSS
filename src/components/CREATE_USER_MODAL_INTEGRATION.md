# CreateUserModal Integration Guide

## Overview

This guide provides step-by-step instructions for integrating the enhanced multi-tab `CreateUserModal` component into the existing `UserManagement.jsx` page.

## Prerequisites

### 1. Install Required Dependencies

The component requires the `zxcvbn` package for password strength validation:

```bash
cd /opt/ops-center
npm install zxcvbn
```

## Integration Steps

### Step 1: Import the Component

At the top of `/opt/ops-center/src/pages/UserManagement.jsx`, add the import:

```javascript
// Add this import near the top with other imports
import CreateUserModal from '../components/CreateUserModal';
```

### Step 2: Replace the Existing Modal State

The existing code uses `createEditModalOpen` state. We need to add a separate state for the new modal:

```javascript
// Add this state (around line 71)
const [createUserModalOpen, setCreateUserModalOpen] = useState(false);
```

### Step 3: Update the Create User Button Handler

Replace the existing `handleCreateUser` function (around line 199):

```javascript
// OLD CODE (lines 199-211):
const handleCreateUser = () => {
  setIsEditMode(false);
  setFormData({
    email: '',
    username: '',
    firstName: '',
    lastName: '',
    password: '',
    enabled: true,
    emailVerified: false,
  });
  setCreateEditModalOpen(true);
};

// NEW CODE:
const handleCreateUser = () => {
  setCreateUserModalOpen(true);
};
```

### Step 4: Add the New Modal Component

Replace the existing "Create/Edit User Modal" (lines 687-784) with:

```jsx
{/* Enhanced Create User Modal */}
<CreateUserModal
  open={createUserModalOpen}
  onClose={() => setCreateUserModalOpen(false)}
  onUserCreated={(newUser) => {
    showToast('User created successfully');
    setCreateUserModalOpen(false);
    fetchUsers();
    fetchStats();
  }}
/>

{/* Keep the existing Edit User Modal for editing */}
<Dialog
  open={createEditModalOpen && isEditMode}
  onClose={() => setCreateEditModalOpen(false)}
  maxWidth="sm"
  fullWidth>
  <DialogTitle>Edit User</DialogTitle>
  <DialogContent>
    <Box sx={{ pt: 2 }}>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="First Name"
            value={formData.firstName}
            onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Last Name"
            value={formData.lastName}
            onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
          />
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Email"
            type="email"
            required
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          />
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Username"
            required
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <FormControlLabel
            control={
              <Switch
                checked={formData.enabled}
                onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
              />
            }
            label="Enabled"
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <FormControlLabel
            control={
              <Switch
                checked={formData.emailVerified}
                onChange={(e) => setFormData({ ...formData, emailVerified: e.target.checked })}
              />
            }
            label="Email Verified"
          />
        </Grid>
      </Grid>
    </Box>
  </DialogContent>
  <DialogActions>
    <Button onClick={() => setCreateEditModalOpen(false)}>
      Cancel
    </Button>
    <Button
      variant="contained"
      onClick={handleSaveUser}
      disabled={!formData.email || !formData.username}
    >
      Update
    </Button>
  </DialogActions>
</Dialog>
```

## Backend API Endpoint

### Required Endpoint

The component expects a comprehensive user creation endpoint:

**POST** `/api/v1/admin/users/comprehensive`

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "firstName": "John",
  "lastName": "Doe",
  "password": "SecurePassword123!",
  "confirmPassword": "SecurePassword123!",
  "enabled": true,
  "emailVerified": false,
  "sendWelcomeEmail": true,
  "organizationId": "org-uuid-here",
  "brigadeRoles": ["brigade-agent-user", "brigade-viewer"],
  "keycloakRoles": ["user", "viewer"],
  "subscriptionTier": "professional",
  "billingStartDate": "2025-10-15",
  "paymentMethod": "skip",
  "apiCallLimitOverride": null,
  "initialCredits": 0,
  "serviceAccess": {
    "openWebUI": true,
    "centerDeep": true,
    "unicornBrigade": true,
    "unicornOrator": false,
    "unicornAmanuensis": false
  },
  "featureFlags": {
    "byokEnabled": false,
    "apiAccessEnabled": true,
    "webhookAccess": false
  },
  "rateLimits": {
    "callsPerMinute": 60,
    "callsPerDay": 10000
  },
  "tags": ["VIP", "Beta"],
  "internalNotes": "Important customer",
  "accountSource": "admin-created"
}
```

**Response (Success - 201 Created):**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "firstName": "John",
  "lastName": "Doe",
  "enabled": true,
  "emailVerified": false,
  "createdAt": "2025-10-15T12:00:00Z",
  "organization": {
    "id": "org-uuid",
    "name": "Example Org"
  },
  "roles": ["brigade-agent-user", "brigade-viewer", "user", "viewer"],
  "subscription": {
    "tier": "professional",
    "status": "active"
  }
}
```

**Response (Error - 400 Bad Request):**
```json
{
  "message": "Email already exists",
  "errors": {
    "email": "A user with this email already exists"
  }
}
```

### Backend Implementation Example (Python/FastAPI)

```python
# File: /opt/ops-center/backend/user_management_api.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict

router = APIRouter()

class ComprehensiveUserCreate(BaseModel):
    # Basic Info
    email: EmailStr
    username: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    password: str
    confirmPassword: str
    enabled: bool = True
    emailVerified: bool = False
    sendWelcomeEmail: bool = True

    # Organization & Roles
    organizationId: Optional[str] = None
    brigadeRoles: List[str] = []
    keycloakRoles: List[str] = []

    # Subscription
    subscriptionTier: str = "free"
    billingStartDate: str
    paymentMethod: str = "skip"
    apiCallLimitOverride: Optional[int] = None
    initialCredits: int = 0

    # Access
    serviceAccess: Dict[str, bool]
    featureFlags: Dict[str, bool]
    rateLimits: Dict[str, int]

    # Metadata
    tags: List[str] = []
    internalNotes: Optional[str] = None
    accountSource: str = "admin-created"

@router.post("/api/v1/admin/users/comprehensive")
async def create_comprehensive_user(data: ComprehensiveUserCreate):
    """
    Create a new user with comprehensive configuration
    """
    # Validate passwords match
    if data.password != data.confirmPassword:
        raise HTTPException(400, detail="Passwords do not match")

    # Check if user exists
    existing_user = await check_user_exists(data.email, data.username)
    if existing_user:
        raise HTTPException(400, detail="User already exists")

    try:
        # 1. Create user in Keycloak
        keycloak_user_id = await create_keycloak_user({
            "email": data.email,
            "username": data.username,
            "firstName": data.firstName,
            "lastName": data.lastName,
            "enabled": data.enabled,
            "emailVerified": data.emailVerified,
        }, data.password)

        # 2. Assign Keycloak roles
        if data.keycloakRoles:
            await assign_keycloak_roles(keycloak_user_id, data.keycloakRoles)

        # 3. Create user in local database
        user_id = await create_local_user({
            "keycloak_id": keycloak_user_id,
            "email": data.email,
            "username": data.username,
            "first_name": data.firstName,
            "last_name": data.lastName,
            "organization_id": data.organizationId,
            "tags": data.tags,
            "internal_notes": data.internalNotes,
            "account_source": data.accountSource,
        })

        # 4. Assign Brigade roles (stored in local DB)
        if data.brigadeRoles:
            await assign_brigade_roles(user_id, data.brigadeRoles)

        # 5. Create subscription in Lago
        if data.subscriptionTier != "free":
            await create_lago_subscription({
                "external_id": data.email,
                "plan_code": data.subscriptionTier,
                "billing_time": "anniversary",
                "subscription_at": data.billingStartDate,
            })

        # 6. Set service access permissions
        await set_service_permissions(user_id, data.serviceAccess)

        # 7. Set feature flags
        await set_feature_flags(user_id, data.featureFlags)

        # 8. Set rate limits
        await set_rate_limits(user_id, data.rateLimits)

        # 9. Add initial credits if specified
        if data.initialCredits > 0:
            await add_credits(user_id, data.initialCredits)

        # 10. Send welcome email if requested
        if data.sendWelcomeEmail:
            await send_welcome_email(data.email, {
                "username": data.username,
                "firstName": data.firstName,
                "tier": data.subscriptionTier,
            })

        # Return created user
        user = await get_user_by_id(user_id)
        return user

    except Exception as e:
        # Rollback: delete Keycloak user if created
        if keycloak_user_id:
            await delete_keycloak_user(keycloak_user_id)
        raise HTTPException(500, detail=str(e))
```

### Required Helper Endpoints

The component also expects these existing endpoints:

1. **GET** `/api/v1/organizations` - List all organizations
   ```json
   {
     "organizations": [
       { "id": "org-1", "name": "Example Org", "domain": "example.com" }
     ]
   }
   ```

2. **POST** `/api/v1/organizations` - Create new organization
   ```json
   {
     "name": "New Organization",
     "description": "Organization description",
     "domain": "neworg.com"
   }
   ```

3. **GET** `/api/v1/admin/users/roles/available` - List available Keycloak roles
   ```json
   {
     "roles": ["user", "admin", "viewer", "manager"]
   }
   ```

## Component Features

### Tab 1: Basic Information
- Email validation (format check)
- Username validation (minimum 3 characters)
- Password strength indicator (using zxcvbn library)
- Password confirmation matching
- Toggle switches for enabled/verified status
- Send welcome email option

### Tab 2: Organization & Roles
- Organization dropdown with "Create New Organization" button
- Sub-modal for creating organizations
- Brigade roles checkboxes (5 predefined roles)
- Keycloak roles checkboxes (fetched from API)

### Tab 3: Subscription & Billing
- 5 subscription tiers with pricing display
- Billing start date picker (defaults to today)
- Payment method radio buttons (Skip/Stripe/Invoice)
- API call limit override (optional)
- Initial credits field

### Tab 4: Access & Permissions
- Service access checkboxes (5 services)
- Feature flags (BYOK, API Access, Webhooks)
- Rate limits (calls per minute/day)

### Tab 5: Metadata
- Tag management with chip input
- Internal notes textarea
- Account source dropdown

### Validation
- Tab-level validation prevents navigation to next tab
- Real-time password strength feedback
- Email format validation
- Password matching validation
- All required fields enforced
- Submit button disabled until all validations pass

### Styling
- Purple/gold gradient theme matching Ops-Center
- Material-UI components throughout
- Responsive design (works on mobile)
- Loading states during submission
- Clear error messages with Alert components

## Testing

### Manual Testing Steps

1. **Open Modal**
   ```
   - Click "Create User" button
   - Modal should open on Tab 1
   ```

2. **Tab 1 Validation**
   ```
   - Try navigating to Tab 2 without filling required fields
   - Should show validation errors
   - Enter weak password -> See "Weak" indicator
   - Enter strong password -> See "Strong" indicator
   - Mismatched passwords -> Cannot proceed
   ```

3. **Tab 2 - Organization**
   ```
   - Click "New Org" button
   - Create organization sub-modal opens
   - Create organization
   - Should appear in dropdown
   - Select organization
   - Check Brigade roles
   - Check Keycloak roles
   ```

4. **Tab 3 - Subscription**
   ```
   - Select different tiers
   - Verify price displays correctly
   - Change billing start date
   - Select payment methods
   - Enter override limits
   ```

5. **Tab 4 - Access**
   ```
   - Toggle service access
   - Toggle feature flags
   - Modify rate limits
   ```

6. **Tab 5 - Metadata**
   ```
   - Add tags by typing and pressing Enter
   - Delete tags by clicking X
   - Enter internal notes
   - Select account source
   ```

7. **Submit**
   ```
   - Click "Create User" button
   - Should show loading spinner
   - On success: Modal closes, toast shown, user list refreshes
   - On error: Error alert shown, modal stays open
   ```

## Troubleshooting

### Issue: "zxcvbn is not defined"
**Solution:** Install the package:
```bash
npm install zxcvbn
```

### Issue: "Organizations not loading"
**Solution:** Check the `/api/v1/organizations` endpoint is responding correctly

### Issue: "Roles not loading"
**Solution:** Check the `/api/v1/admin/users/roles/available` endpoint

### Issue: "Create user fails with 404"
**Solution:** Implement the `/api/v1/admin/users/comprehensive` endpoint in the backend

### Issue: "Validation errors not showing"
**Solution:** Check browser console for JavaScript errors. Ensure Material-UI is properly installed.

### Issue: "Modal doesn't close after creating user"
**Solution:** Ensure `onUserCreated` callback is properly calling `setCreateUserModalOpen(false)`

## Future Enhancements

- Stripe Elements integration for card entry
- Avatar upload for user profile
- Bulk user import via CSV
- Template-based user creation
- Email template customization
- Audit log integration
- Real-time username availability check
- Password policy configuration

## Support

For issues or questions:
1. Check backend logs: `docker logs ops-center-direct`
2. Check browser console for frontend errors
3. Verify API endpoints are responding correctly
4. Review integration guide steps

---

**Created:** October 15, 2025
**Component:** CreateUserModal.jsx
**Author:** Claude Code
**Version:** 1.0.0
