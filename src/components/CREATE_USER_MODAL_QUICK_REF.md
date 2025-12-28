# CreateUserModal - Quick Reference Card

## 🚀 Quick Start

```bash
# 1. Install dependency
cd /home/muut/Production/UC-Cloud/services/ops-center
npm install zxcvbn

# 2. Import in UserManagement.jsx
import CreateUserModal from '../components/CreateUserModal';

# 3. Add state
const [createUserModalOpen, setCreateUserModalOpen] = useState(false);

# 4. Update button handler
const handleCreateUser = () => {
  setCreateUserModalOpen(true);
};

# 5. Add component (replace old modal)
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
```

## 📋 Component Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `open` | boolean | Yes | Controls modal visibility |
| `onClose` | function | Yes | Called when user clicks cancel/close |
| `onUserCreated` | function | Yes | Called with new user data on success |

## 🎨 Features Overview

### Tab 1: Basic Information ✅
- ✉️ Email (validated)
- 👤 Username (min 3 chars)
- 🔒 Password (strength indicator)
- ✔️ Confirm Password
- 🎚️ Enabled/Verified toggles
- 📧 Send welcome email

### Tab 2: Organization & Roles 🏢
- 🏛️ Organization dropdown + create new
- 🎖️ Brigade roles (5 types)
- 🔑 Keycloak roles (dynamic)

### Tab 3: Subscription & Billing 💳
- 💰 Tier selection (Free → Enterprise)
- 📅 Billing start date
- 💳 Payment method
- 🔢 API limit override
- 💎 Initial credits

### Tab 4: Access & Permissions 🔐
- ✅ Service access (5 services)
- 🚩 Feature flags (BYOK, API, Webhooks)
- ⏱️ Rate limits (per min/day)

### Tab 5: Metadata 🏷️
- 🏷️ Tags (chip input)
- 📝 Internal notes
- 📊 Account source

## 🔌 Required API Endpoints

```
POST   /api/v1/admin/users/comprehensive   Create user (main endpoint)
GET    /api/v1/organizations                List organizations
POST   /api/v1/organizations                Create organization
GET    /api/v1/admin/users/roles/available  List Keycloak roles
```

## 📦 Request Body Example

```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePassword123!",
  "subscriptionTier": "professional",
  "organizationId": "org-uuid",
  "brigadeRoles": ["brigade-agent-user"],
  "keycloakRoles": ["user"],
  "serviceAccess": {
    "openWebUI": true,
    "centerDeep": true
  },
  "featureFlags": {
    "byokEnabled": false,
    "apiAccessEnabled": true
  },
  "rateLimits": {
    "callsPerMinute": 60,
    "callsPerDay": 10000
  },
  "tags": ["VIP"],
  "accountSource": "admin-created"
}
```

## ✅ Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| Email | Required, format | "Email is required" / "Invalid email format" |
| Username | Required, min 3 chars | "Username must be at least 3 characters" |
| Password | Required, min 8 chars, score ≥ 2 | "Password is too weak" |
| Confirm Password | Must match password | "Passwords do not match" |

## 🎯 Subscription Tiers

| Tier | Price | Calls/Day | Default Limits |
|------|-------|-----------|----------------|
| Free | $0/month | 100 | 60/min, 100/day |
| Trial | $1/week | 700 | 60/min, 700/day |
| Starter | $19/month | 1,000 | 60/min, 1000/day |
| Professional | $49/month | 10,000 | 60/min, 10000/day |
| Enterprise | $99/month | Unlimited | 60/min, 999999/day |

## 🏢 Brigade Roles

- `brigade-platform-admin` - Full platform control
- `brigade-developer` - Develop custom agents
- `brigade-agent-creator` - Create/edit agents
- `brigade-agent-user` - Use existing agents
- `brigade-viewer` - Read-only access

## 🛠️ Services

- ✅ Open-WebUI (default: enabled)
- 🔍 Center-Deep (search)
- 🎖️ Unicorn Brigade (agents)
- 🔊 Unicorn Orator (TTS)
- 🎙️ Unicorn Amanuensis (STT)

## 🚩 Feature Flags

- 🔑 BYOK - Bring Your Own Key for LLM API
- 🔌 API Access - Enable REST API access
- 🔗 Webhook Access - Allow webhook configuration

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| zxcvbn error | `npm install zxcvbn` |
| Orgs not loading | Check `/api/v1/organizations` endpoint |
| Roles not loading | Check `/api/v1/admin/users/roles/available` |
| 404 on submit | Implement `/api/v1/admin/users/comprehensive` |
| Modal won't close | Check `onUserCreated` callback |

## 💡 Tips

1. **Password Strength**: Uses zxcvbn library (0-4 scale, requires ≥2)
2. **Tab Navigation**: Validates before allowing next tab
3. **Submit Button**: Disabled until all required fields valid
4. **Organization**: Can create new org without leaving modal
5. **Rate Limits**: Auto-updated when tier changes
6. **Tags**: Press Enter or click Add button
7. **Defaults**: Free tier, enabled, OpenWebUI access

## 🎨 Theming

Matches Ops-Center purple/gold theme:
```css
Primary: #667eea → #764ba2 gradient
Success: Green
Warning: Orange
Error: Red
```

## 📱 Responsive

- ✅ Desktop (optimal)
- ✅ Tablet (works)
- ✅ Mobile (functional)

## 🔄 Workflow

```
User clicks "Create User"
  ↓
Modal opens → Tab 1 (Basic Info)
  ↓
Fill required fields
  ↓
Click "Next" → Tab 2 (Org & Roles)
  ↓
Optional: Create org, select roles
  ↓
Click "Next" → Tab 3 (Subscription)
  ↓
Select tier, payment method
  ↓
Click "Next" → Tab 4 (Access)
  ↓
Configure services, features, limits
  ↓
Click "Next" → Tab 5 (Metadata)
  ↓
Add tags, notes
  ↓
Click "Create User"
  ↓
API call → POST /api/v1/admin/users/comprehensive
  ↓
Success: Modal closes, toast shown, table refreshes
Error: Alert shown, modal stays open
```

## 📚 Documentation

- Full integration guide: `CREATE_USER_MODAL_INTEGRATION.md`
- Component file: `CreateUserModal.jsx`
- Parent component: `UserManagement.jsx`

---

**Version:** 1.0.0 | **Updated:** Oct 15, 2025
