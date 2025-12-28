# Navigation Migration Guide - User Guide

**Version:** 1.0
**Date:** October 13, 2025
**Audience:** End Users (All Roles)

---

## What's Changed?

The Ops-Center navigation has been reorganized to provide a clearer, more intuitive experience. Instead of a flat list of 14 menu items, the navigation is now organized into **three logical sections** based on what you're managing:

1. **Personal** - Your account, subscription, and preferences
2. **Organization** - Team management and organization settings (for org admins)
3. **System** - Platform administration (for system administrators)

---

## Quick Summary

### New Features Now Available
- **Team Members** - Manage your organization's team (previously hidden!)
- **API Keys (BYOK)** - Bring Your Own Key management now easier to find
- **Usage & Limits** - See your API usage at a glance
- **Security & Sessions** - Manage passwords, 2FA, and active sessions
- **Notifications** - Configure email and notification preferences
- **Organization Settings** - Configure organization-wide preferences

### What Moved Where

| Old Location | New Location |
|-------------|-------------|
| User Settings | My Account → Profile |
| Billing | My Subscription → Current Plan |
| Models & AI | System → AI Models |
| Services | System → Services |
| Resources (System) | System → Resources |
| Storage | System → Storage & Backup |
| Logs | System → System Logs |
| Settings | System → System Settings (admin only) |
| **NEW:** User Management | Organization → Team Members |

---

## Navigation Structure Overview

### Before (Old Navigation)

```
📋 Flat List (14 items):
├─ Dashboard
├─ User Settings
├─ Billing
├─ Models & AI
├─ Services
├─ Resources
├─ Network
├─ Storage
├─ Logs
├─ Security
├─ Authentication
├─ Extensions
├─ Landing Page
└─ Settings
```

### After (New Navigation)

```
┌─────────────────────────────────────┐
│  PERSONAL                           │
├─────────────────────────────────────┤
│  🏠 Dashboard                       │
│  👤 My Account              ▼       │
│     ├─ Profile                      │
│     ├─ Notifications                │
│     ├─ Security                     │
│     └─ API Keys (BYOK)              │
│  💳 My Subscription         ▼       │
│     ├─ Current Plan                 │
│     ├─ Usage & Limits               │
│     ├─ Billing History              │
│     └─ Payment Methods              │
│                                     │
├─────────────────────────────────────┤
│  ORGANIZATION (Admins Only)         │
├─────────────────────────────────────┤
│  🏢 Organization            ▼       │
│     ├─ Team Members         ⭐ NEW  │
│     ├─ Roles & Permissions          │
│     ├─ Organization Settings        │
│     └─ Organization Billing         │
│                                     │
├─────────────────────────────────────┤
│  SYSTEM (Platform Admins Only)      │
├─────────────────────────────────────┤
│  ⚙️ System                  ▼       │
│     ├─ AI Models                    │
│     ├─ Services                     │
│     ├─ Resources                    │
│     ├─ Network                      │
│     ├─ Storage & Backup             │
│     ├─ Security                     │
│     ├─ Authentication               │
│     ├─ Extensions                   │
│     ├─ System Logs                  │
│     └─ Landing Page                 │
└─────────────────────────────────────┘
```

---

## How to Find Moved Features

### Personal Features (All Users)

#### Updating Your Profile
**Old:** Click "User Settings"
**New:** Click "My Account" → "Profile"

**What you'll find:**
- Personal information
- Email address
- Display name
- Avatar/profile picture
- Timezone preferences

---

#### Managing Notifications
**Old:** Not available separately
**New:** Click "My Account" → "Notifications"

**What you'll find:**
- Email notification preferences
- Push notification settings
- Alert frequency
- Notification categories

---

#### Security Settings
**Old:** Part of "User Settings"
**New:** Click "My Account" → "Security"

**What you'll find:**
- Change password
- Two-factor authentication (2FA)
- Active sessions
- Login history
- Security alerts

---

#### API Keys (BYOK)
**Old:** Part of "User Settings" or hidden
**New:** Click "My Account" → "API Keys"

**What you'll find:**
- OpenAI API keys
- Anthropic API keys
- HuggingFace tokens
- Custom endpoint keys
- Key encryption status

---

#### Viewing Your Subscription
**Old:** Click "Billing"
**New:** Click "My Subscription" → "Current Plan"

**What you'll find:**
- Current subscription tier (Trial, Starter, Pro, Enterprise)
- Plan features and limits
- Upgrade/downgrade options
- Trial remaining days
- Plan renewal date

---

#### Checking Usage
**Old:** Part of "Billing" page
**New:** Click "My Subscription" → "Usage & Limits"

**What you'll find:**
- API calls used this month
- API call limits
- Overage status
- Usage graphs
- Service-specific usage (Chat, Search, TTS, STT)

---

#### Managing Billing
**Old:** Click "Billing"
**New:** Click "My Subscription" → "Billing History"

**What you'll find:**
- Invoice history
- Payment receipts
- Download invoices (PDF)
- Billing contact information

---

#### Payment Methods
**Old:** Part of "Billing" page
**New:** Click "My Subscription" → "Payment Methods"

**What you'll find:**
- Credit/debit cards on file
- Add new payment method
- Set default payment method
- Remove payment methods

---

### Organization Features (Org Admins/Owners Only)

#### Managing Team Members
**Old:** **Not accessible!** (UserManagement page existed but wasn't in navigation)
**New:** Click "Organization" → "Team Members" ⭐

**What you'll find:**
- List of all team members
- Add new team members
- Remove team members
- Change member roles (Viewer, User, Power User, Admin)
- Invite pending users
- View member activity

**Why this is important:** This was a critical missing feature. You can now properly manage your team!

---

#### Roles & Permissions
**Old:** Not available
**New:** Click "Organization" → "Roles & Permissions"

**What you'll find:**
- Define custom roles
- Set permission levels
- Role assignment rules
- Permission matrix

---

#### Organization Settings
**Old:** Mixed with system settings
**New:** Click "Organization" → "Organization Settings"

**What you'll find:**
- Organization name
- Organization logo/branding
- Shared preferences
- Default settings for new members
- Organization metadata

---

#### Organization Billing (Owner Only)
**Old:** Part of "Billing" page
**New:** Click "Organization" → "Organization Billing"

**What you'll find:**
- Organization-wide usage
- Team seat management
- Consolidated billing
- Organization invoices
- Cost allocation

---

### System Features (Platform Admins Only)

All system administration features have moved under the **System** section with clearer names:

| Feature | New Location |
|---------|-------------|
| Models & AI | System → AI Models |
| Services | System → Services |
| Resources | System → Resources |
| Network | System → Network |
| Storage | System → Storage & Backup |
| Security | System → Security |
| Authentication | System → Authentication |
| Extensions | System → Extensions |
| Logs | System → System Logs |
| Landing Page | System → Landing Page |

---

## Using the New Navigation

### Expanding Sections

Click on any section header (My Account, My Subscription, Organization, System) to expand or collapse the submenu:

```
👤 My Account              ▼    ← Click to expand
   ├─ Profile
   ├─ Notifications
   ├─ Security
   └─ API Keys
```

### Active Page Highlighting

The current page is highlighted in the navigation:

```
👤 My Account              ▼
   ├─ Profile
   ├─ Notifications         ← You are here (highlighted)
   ├─ Security
   └─ API Keys
```

### Mobile Navigation

On mobile devices:
- Tap the **hamburger menu** (☰) to open navigation
- Same hierarchical structure as desktop
- **Bottom tabs** for quick access:
  - Dashboard
  - My Account
  - Organization (if admin)
  - System (if platform admin)

---

## Role-Based Visibility

What you see in the navigation depends on your role:

### All Users (Viewer, User, Power User, Admin)
- ✅ Dashboard
- ✅ My Account (all sub-items)
- ✅ My Subscription (all sub-items)

### Organization Admins/Owners Only
- ✅ Organization section (all sub-items)
- ✅ Team Members
- ✅ Roles & Permissions
- ✅ Organization Settings
- ✅ Organization Billing (Owner only)

### Platform Administrators Only
- ✅ System section (all sub-items)
- ✅ AI Models
- ✅ Services
- ✅ Resources
- ✅ Network
- ✅ Storage & Backup
- ✅ Security
- ✅ Authentication
- ✅ Extensions
- ✅ System Logs
- ✅ Landing Page

---

## Frequently Asked Questions

### Q: Why did the navigation change?

**A:** The old navigation was a flat list that made it hard to find features, and it was missing critical pages like "Team Members" (UserManagement). The new structure organizes features logically and makes everything easier to find.

---

### Q: Can I still use old bookmarks?

**A:** Yes! Old URLs automatically redirect to the new locations. For example:
- `/admin/models` redirects to `/admin/system/models`
- `/admin/billing` redirects to `/admin/subscription/plan`

---

### Q: I can't find the "Settings" page anymore. Where did it go?

**A:**
- **Personal settings** → "My Account" → "Profile"
- **System settings** (admin only) → "System" → System Settings (formerly just "Settings")

---

### Q: Where is "User Management"? I couldn't find it before.

**A:** This was a known issue! The UserManagement page existed but wasn't in the navigation. Now it's properly accessible at:

**Organization → Team Members**

---

### Q: Why can't I see the "Organization" section?

**A:** The Organization section is only visible to users with organization admin or owner roles. If you're a regular user or viewer, you won't see this section. Contact your organization administrator if you need access.

---

### Q: Why can't I see the "System" section?

**A:** The System section is only visible to platform administrators (system admins). If you're an organization admin, you won't see system-level features. This is intentional for security and clarity.

---

### Q: Can I collapse sections to reduce clutter?

**A:** Yes! Click any section header to collapse or expand it. Your preference is saved automatically, so collapsed sections stay collapsed when you reload the page.

---

### Q: Does this work on mobile devices?

**A:** Yes! The navigation is fully responsive:
- **Mobile**: Hamburger menu with same hierarchy
- **Tablet**: Full sidebar navigation
- **Desktop**: Full sidebar navigation

---

### Q: Will the old URLs still work?

**A:** Yes, for at least 4 weeks after launch. Old URLs redirect to new locations automatically. However, we recommend updating bookmarks to the new URLs.

---

## Getting Help

### Need Assistance?

If you have trouble finding a feature or using the new navigation:

1. **Check this guide** - Use Ctrl+F to search for the feature name
2. **Hover over menu items** - Tooltips provide descriptions
3. **Contact Support** - Click "Help & Documentation" in the sidebar
4. **Report Issues** - Click "Feedback" to report navigation issues

### Feedback

We want to hear from you! If you have suggestions for improving the navigation:

1. Click "Help & Documentation" → "Feedback"
2. Email: support@magicunicorn.tech
3. Submit feature requests via GitHub Issues

---

## What's Next?

### Phase 2 Enhancements (Coming Soon)

- **Global Search** - Search across all pages and features
- **Favorites** - Pin frequently used pages to the top
- **Keyboard Shortcuts** - Navigate faster with hotkeys
- **Customizable Layout** - Drag-and-drop menu organization
- **Quick Actions** - Context menu for common tasks

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Oct 13, 2025 | Initial navigation restructure |

---

**Document Maintained By:** Magic Unicorn Unconventional Technology & Stuff Inc
**Last Updated:** October 13, 2025
**Questions?** support@magicunicorn.tech
