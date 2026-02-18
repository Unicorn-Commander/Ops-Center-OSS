# Admin Subscription Management - Quick Start Guide

## Access the Admin Dashboard

1. **Login as Admin**
   - Go to https://unicorncommander.ai
   - Login with admin credentials
   - You'll be redirected to the main dashboard

2. **Navigate to Subscription Management**
   - Click the "Subscription Management" tile (👑 icon)
   - URL: https://unicorncommander.ai/admin/subscriptions.html

## Dashboard Overview

### Analytics Cards (Top Row)
- **Total Users**: All registered users
- **Active Subscriptions**: Users with active/trial status
- **MRR**: Monthly Recurring Revenue
- **Total API Calls**: Cumulative usage

### Subscription Table
- View all users and their subscriptions
- Search by email, username, or tier
- Sort by any column
- See real-time usage (usage/limit)

## Common Tasks

### View User Details
1. Find user in table
2. Click blue eye icon
3. View modal shows:
   - Email, username, name
   - Tier and status
   - API usage
   - BYOK providers
   - Join date, last login

### Edit Subscription
1. Click purple edit icon
2. Select new tier:
   - Free ($0/mo, 100 calls)
   - Trial ($1/mo, 1,000 calls)
   - Starter ($19/mo, 10,000 calls)
   - Professional ($49/mo, 100,000 calls)
   - Enterprise ($99/mo, 1,000,000 calls)
3. Select status (active, trial, cancelled, suspended)
4. Add admin notes (optional)
5. Click "Save Changes"

### Reset User Usage
1. Find user in table
2. Click green refresh icon
3. Confirm reset
4. User's API usage counter reset to 0

### Export Data
1. Click "Export CSV" button (top right)
2. CSV file downloads with all subscription data

## API Endpoints

All endpoints require admin authentication.

### Quick Reference

```bash
# Base URL
BASE=/api/v1/admin/subscriptions

# List all subscriptions
GET $BASE/list

# Get user details
GET $BASE/{email}

# Update subscription
PATCH $BASE/{email}
Body: {"tier": "professional", "status": "active", "notes": "..."}

# Reset usage
POST $BASE/{email}/reset-usage

# Analytics overview
GET $BASE/analytics/overview

# Revenue by tier
GET $BASE/analytics/revenue-by-tier

# Usage stats
GET $BASE/analytics/usage-stats
```

## Subscription Tiers

| Tier | Price | API Calls | BYOK |
|------|-------|-----------|------|
| Free | $0 | 100 | No |
| Trial | $1 | 1,000 | No |
| Starter | $19 | 10,000 | No |
| Professional | $49 | 100,000 | Yes |
| Enterprise | $99 | 1,000,000 | Yes |

## Subscription Statuses

- **active**: User can access all tier features
- **trial**: User on trial period
- **cancelled**: Subscription cancelled (access until period end)
- **suspended**: Temporarily disabled (payment issues, etc.)

## Search Tips

- Search by email: `@example.com`
- Search by tier: `professional`
- Search by status: `active`
- Search by username: `john`

## Troubleshooting

### Can't Access Dashboard
- Verify you're logged in as admin
- Check that your account has admin role in Authentik
- Try logging out and back in

### Analytics Not Loading
- Click "Refresh" button
- Check browser console for errors
- Verify Authentik API token is set

### Can't Update Subscription
- Verify user email is correct
- Check that tier and status are valid values
- View browser console for error details

### Usage Not Resetting
- Verify you clicked the correct user
- Check Authentik user attributes to confirm
- API usage updates may take a few minutes to reflect

## Support Workflows

### User Requests Upgrade
1. Navigate to subscription management
2. Find user by email
3. Click edit (purple pencil)
4. Change tier to requested level
5. Set status to "active"
6. Add note: "Upgraded per user request"
7. Save

### Resolve Billing Issue
1. Find user in table
2. Check current tier and usage
3. If payment failed:
   - Set status to "suspended"
   - Add note with details
4. After payment resolved:
   - Set status back to "active"
   - Consider resetting usage if fair

### Grant Trial Extension
1. Find user in table
2. Click edit
3. Keep tier as "trial"
4. Add note: "Trial extended - reason"
5. Optionally reset usage

### Support Emergency Access
1. Find user in table
2. Click edit
3. Upgrade to "enterprise" tier temporarily
4. Set status to "active"
5. Add note with ticket number and end date
6. Remember to revert after support window

## Best Practices

1. **Always Add Notes**: Document why you made changes
2. **Check Before Reset**: Verify user identity before resetting usage
3. **Export Regularly**: Download CSV backups of subscription data
4. **Monitor Analytics**: Review MRR and tier distribution weekly
5. **Investigate Anomalies**: Check users with unusual usage patterns

## Keyboard Shortcuts

- **Ctrl/Cmd + F**: Search subscriptions
- **Esc**: Close modals
- **Enter**: Submit forms

## Mobile Access

The dashboard is mobile-responsive:
- Analytics cards stack vertically
- Table scrolls horizontally
- Modals adapt to screen size
- Touch-friendly buttons

## Security Notes

- All actions are logged
- Your admin email is recorded with changes
- BYOK keys are encrypted (only provider names shown)
- Session timeout after 30 minutes of inactivity

## Quick Links

- **Dashboard**: `/admin/subscriptions.html`
- **API Docs**: `/docs/admin-subscription-api.md`
- **Implementation**: `/docs/ADMIN_SUBSCRIPTION_IMPLEMENTATION.md`
- **Tests**: `/backend/tests/test_admin_subscriptions.py`

---

Need help? Contact the development team or check the full documentation.
