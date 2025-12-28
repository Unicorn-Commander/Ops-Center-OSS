# User Profile API Specification

**File**: `backend/profile_api.py`
**Purpose**: FastAPI router for user profile and preferences management
**Base Path**: `/api/v1/users/me`
**Authentication**: Required (Keycloak SSO)
**Authorization**: User can only manage their own profile

## Purpose

The Profile API provides endpoints for users to:
1. View and update their personal profile information
2. Manage user preferences (theme, notifications, etc.)
3. View account security settings
4. Manage display settings and preferences

This is separate from the admin user management API which allows admins to manage all users.

## Dependencies

- **Authentication**: Keycloak SSO
- **Storage**: Keycloak user attributes
- **Audit Logging**: `audit_logger.py`
- **Integration**: `keycloak_integration.py`

## Endpoints (8 total)

### 1. Profile Management (4 endpoints)

#### GET /api/v1/users/me/profile
**Purpose**: Get current user's profile
**Auth**: Authenticated user
**Returns**:
```json
{
  "id": "user_abc123",
  "email": "user@example.com",
  "username": "user123",
  "email_verified": true,
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "created_at": "2025-10-01T12:00:00Z",
  "last_login": "2025-10-21T08:30:00Z",
  "attributes": {
    "phone": "+1-555-1234",
    "company": "Acme Corp",
    "job_title": "Developer"
  }
}
```
**Source**: Keycloak user data + custom attributes

#### PUT /api/v1/users/me/profile
**Purpose**: Update current user's profile
**Auth**: Authenticated user
**Request Body**:
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1-555-1234",
  "company": "Acme Corp",
  "job_title": "Senior Developer"
}
```
**Logic**:
- Updates Keycloak user profile
- Updates custom attributes
- Returns updated profile
**Restrictions**: Cannot update email, username, roles

#### GET /api/v1/users/me/avatar
**Purpose**: Get user avatar URL
**Auth**: Authenticated user
**Returns**:
```json
{
  "avatar_url": "https://gravatar.com/...",
  "avatar_type": "gravatar"  // gravatar, custom, default
}
```

#### POST /api/v1/users/me/avatar
**Purpose**: Upload custom avatar
**Auth**: Authenticated user
**Request**: Multipart form with image file
**Logic**:
- Validate image format (JPG, PNG)
- Resize to 256x256
- Store in S3 or local storage
- Update user attribute `avatar_url`

---

### 2. Preferences Management (4 endpoints)

#### GET /api/v1/users/me/preferences
**Purpose**: Get user preferences
**Auth**: Authenticated user
**Returns**:
```json
{
  "theme": "galaxy",  // dark, light, unicorn, galaxy
  "language": "en",
  "timezone": "America/Los_Angeles",
  "date_format": "YYYY-MM-DD",
  "time_format": "12h",  // 12h or 24h
  "notifications": {
    "email": true,
    "browser": true,
    "slack": false
  },
  "dashboard": {
    "default_view": "overview",  // overview, analytics, services
    "widgets": ["services", "metrics", "alerts"]
  }
}
```
**Source**: Keycloak user attributes (stored as JSON)

#### PUT /api/v1/users/me/preferences
**Purpose**: Update user preferences
**Auth**: Authenticated user
**Request Body**: Partial updates allowed
```json
{
  "theme": "galaxy",
  "notifications": {
    "email": false
  }
}
```
**Logic**:
- Merge with existing preferences
- Store in Keycloak user attributes
- Return updated preferences

#### POST /api/v1/users/me/preferences/reset
**Purpose**: Reset preferences to defaults
**Auth**: Authenticated user
**Logic**: Sets preferences to system defaults

#### GET /api/v1/users/me/preferences/defaults
**Purpose**: Get system default preferences
**Auth**: Public (no auth required)
**Returns**: Default preference values

---

## Pydantic Models

```python
class UserProfile(BaseModel):
    id: str
    email: str
    username: str
    email_verified: bool
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    attributes: Dict[str, Any]

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, regex=r"^\+?[1-9]\d{1,14}$")
    company: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=100)

class UserPreferences(BaseModel):
    theme: str = Field(default="dark", regex="^(dark|light|unicorn|galaxy)$")
    language: str = Field(default="en", regex="^[a-z]{2}$")
    timezone: str = Field(default="UTC")
    date_format: str = Field(default="YYYY-MM-DD")
    time_format: str = Field(default="24h", regex="^(12h|24h)$")
    notifications: Dict[str, bool] = Field(default_factory=dict)
    dashboard: Dict[str, Any] = Field(default_factory=dict)

class PreferencesUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    date_format: Optional[str] = None
    time_format: Optional[str] = None
    notifications: Optional[Dict[str, bool]] = None
    dashboard: Optional[Dict[str, Any]] = None

class AvatarResponse(BaseModel):
    avatar_url: str
    avatar_type: str  # gravatar, custom, default

class AvatarUploadRequest(BaseModel):
    file: bytes
    content_type: str
```

---

## Helper Functions

```python
async def get_current_user_from_session(request: Request) -> Dict:
    """
    Get current user from session token.

    Returns:
        User dict with id, email, username, roles, etc.

    Raises:
        HTTPException: 401 if not authenticated
    """
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sessions = getattr(request.app.state, "sessions", {})
    session_data = sessions.get(session_token)

    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    return session_data.get("user", {})


async def get_user_preferences_from_keycloak(user_id: str) -> Dict:
    """
    Get user preferences from Keycloak user attributes.

    Args:
        user_id: Keycloak user ID

    Returns:
        User preferences dict
    """
    from keycloak_integration import get_user_by_id

    user = await get_user_by_id(user_id)
    if not user:
        return get_default_preferences()

    # Get preferences from user attributes
    attributes = user.get("attributes", {})
    preferences_json = attributes.get("preferences", ["{}"])[0]

    try:
        preferences = json.loads(preferences_json)
        return merge_with_defaults(preferences)
    except:
        return get_default_preferences()


async def update_user_preferences_in_keycloak(
    user_id: str,
    preferences: Dict
) -> bool:
    """
    Update user preferences in Keycloak.

    Args:
        user_id: Keycloak user ID
        preferences: Preferences dict to store

    Returns:
        True if successful
    """
    from keycloak_integration import update_user_attributes

    # Get existing preferences
    existing = await get_user_preferences_from_keycloak(user_id)

    # Merge with new preferences
    merged = {**existing, **preferences}

    # Store as JSON in user attributes
    preferences_json = json.dumps(merged)

    return await update_user_attributes(
        user_id,
        {"preferences": [preferences_json]}
    )


def get_default_preferences() -> Dict:
    """Get system default preferences"""
    return {
        "theme": "dark",
        "language": "en",
        "timezone": "UTC",
        "date_format": "YYYY-MM-DD",
        "time_format": "24h",
        "notifications": {
            "email": True,
            "browser": True,
            "slack": False
        },
        "dashboard": {
            "default_view": "overview",
            "widgets": ["services", "metrics", "alerts"]
        }
    }


def merge_with_defaults(preferences: Dict) -> Dict:
    """Merge user preferences with defaults for missing keys"""
    defaults = get_default_preferences()
    return {**defaults, **preferences}


async def get_gravatar_url(email: str, size: int = 256) -> str:
    """
    Get Gravatar URL for email.

    Args:
        email: User email
        size: Image size (default 256)

    Returns:
        Gravatar URL
    """
    import hashlib
    email_hash = hashlib.md5(email.lower().encode()).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon"
```

---

## Keycloak Integration

### User Attributes Schema

The following custom attributes should be stored in Keycloak:

```python
{
    "phone": ["<value>"],  # Array format required by Keycloak
    "company": ["<value>"],
    "job_title": ["<value>"],
    "preferences": ["{...json...}"],  # JSON string
    "avatar_url": ["<value>"]
}
```

### Keycloak User Profile Configuration

In Keycloak 26.0+, custom attributes must be declared in **User Profile**:

1. Go to: Realm Settings → User Profile
2. Add these attributes:
   - `phone` (string, optional)
   - `company` (string, optional)
   - `job_title` (string, optional)
   - `preferences` (string, optional)
   - `avatar_url` (string, optional)

---

## Audit Logging

Log all profile/preference changes:

```python
await audit_logger.log_custom(
    user_id=user_id,
    action="update_profile",
    resource_type="user_profile",
    resource_id=user_id,
    details={
        "fields_updated": ["first_name", "last_name", "phone"],
        "new_values": {...}  # Don't log sensitive data
    }
)
```

---

## Error Handling

- **401 Unauthorized**: Not authenticated
- **400 Bad Request**: Invalid input data
- **413 Payload Too Large**: Avatar file too large (>2MB)
- **415 Unsupported Media Type**: Invalid avatar format
- **500 Internal Server Error**: Server error

---

## Testing Checklist

- [ ] Get user profile (authenticated user)
- [ ] Update profile (first_name, last_name, phone)
- [ ] Get user avatar (returns Gravatar by default)
- [ ] Upload custom avatar (validates format and size)
- [ ] Get user preferences (returns defaults if not set)
- [ ] Update preferences (theme, notifications, dashboard)
- [ ] Partial preference update (only theme changed)
- [ ] Reset preferences to defaults
- [ ] Get default preferences (public endpoint)
- [ ] Preferences persist across sessions
- [ ] Audit logs created for profile changes
- [ ] Cannot update email/username via profile API
- [ ] Unauthenticated request returns 401

---

## Integration with Frontend

The frontend should:

1. **Load preferences on app start**:
   ```javascript
   const preferences = await fetch('/api/v1/users/me/preferences').then(r => r.json())
   applyTheme(preferences.theme)
   ```

2. **Update theme immediately**:
   ```javascript
   await fetch('/api/v1/users/me/preferences', {
     method: 'PUT',
     body: JSON.stringify({ theme: 'galaxy' })
   })
   ```

3. **Sync with localStorage**:
   - Store theme in localStorage for instant load
   - Sync with backend on change
   - Backend is source of truth

---

## Future Enhancements

1. **Two-Factor Authentication**: Enable/disable 2FA
2. **Security Log**: View login history and sessions
3. **API Keys**: User-generated API keys (already exists separately)
4. **Webhooks**: User-configured webhooks for events
5. **Integrations**: Connect third-party services (Slack, Discord)
