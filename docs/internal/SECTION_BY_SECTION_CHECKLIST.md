# Section-by-Section Review Checklist
**Date**: October 28, 2025
**Purpose**: Systematic review and refinement of all Ops-Center sections
**Status**: Ready for User Testing

---

## How to Use This Checklist

For each section:
1. ✅ **Navigate** to the page
2. ✅ **Test** all functionality
3. ✅ **Note** what works vs. what's broken
4. ✅ **Document** any errors or issues
5. ✅ **Mark** complete when verified

---

## Section 1: Authentication & Login

### Access Points
- [ ] https://your-domain.com (landing page)
- [ ] https://your-domain.com/admin (admin dashboard)
- [ ] https://your-domain.com/auth/login (OAuth flow)

### Test Cases
- [ ] Landing page loads without errors
- [ ] "Sign In" button visible
- [ ] Click "Sign In" → redirects to Keycloak
- [ ] OAuth providers visible (Google, GitHub, Microsoft)
- [ ] Login with OAuth works
- [ ] After login, redirects to dashboard
- [ ] Session cookie set correctly
- [ ] Logout works (clears session)

### What to Check
- Browser console (F12) → No JavaScript errors
- Network tab → /api/v1/auth/me returns 200 OK
- Cookies → session_token present

### Known Issues
- None currently

---

## Section 2: Dashboard (Main)

### Access Point
- [ ] /admin (default after login)
- [ ] /admin/dashboard

### Test Cases
- [ ] Page loads without errors
- [ ] Metric cards display:
  - [ ] Total Users
  - [ ] Active Services
  - [ ] System Health
  - [ ] API Calls Today
- [ ] Charts render (if any)
- [ ] Quick actions buttons work
- [ ] Service status cards show correct status
- [ ] No console errors

### Visual Check
- [ ] Glassmorphism styling visible
- [ ] Purple/gold theme colors
- [ ] Responsive layout (resize browser)
- [ ] All icons load correctly

### What to Check
- Do metrics show real data or 0?
- Do service status cards show green/red correctly?
- Are there any "undefined" or "NaN" values?

---

## Section 3: My Account

### 3.1 Profile & Preferences

**Access**: /admin/account/profile

- [ ] Page loads
- [ ] User info displays:
  - [ ] Username
  - [ ] Email
  - [ ] Full name
- [ ] Edit profile button works
- [ ] **Avatar upload** (recently fixed):
  - [ ] Click "Upload Avatar"
  - [ ] Select image file
  - [ ] Image previews
  - [ ] Click "Save"
  - [ ] Avatar updates successfully
  - [ ] No permission errors
- [ ] Theme selection dropdown
- [ ] Language preferences
- [ ] Save changes button works

**Expected Result**: Profile picture should save now (permissions fixed)

### 3.2 Security & Sessions

**Access**: /admin/account/security

- [ ] Page loads
- [ ] Active sessions list shows
- [ ] Current session highlighted
- [ ] "Revoke Session" button works
- [ ] "Revoke All Other Sessions" works
- [ ] Password change section (if applicable)
- [ ] 2FA status shown (if implemented)

### 3.3 API Keys (BYOK)

**Access**: /admin/account/api-keys

- [ ] Page loads
- [ ] "Add API Key" button visible
- [ ] Click "Add API Key"
- [ ] Modal/form appears
- [ ] Provider dropdown:
  - [ ] OpenAI
  - [ ] Anthropic
  - [ ] Google AI
  - [ ] OpenRouter
  - [ ] Azure OpenAI
- [ ] Enter API key
- [ ] (Optional) Test key validation
- [ ] Click "Save"
- [ ] Key saves successfully ✅ (2 keys already exist)
- [ ] Key shows in list (masked)
- [ ] "Edit" button works
- [ ] "Delete" button works
- [ ] "Test Connection" works (if available)

**Expected Result**: API key save should work (backend tested, 2 keys exist)

### 3.4 Notification Settings

**Access**: /admin/account/notification-settings

- [ ] Page loads
- [ ] Email notifications toggle
- [ ] Notification types:
  - [ ] System alerts
  - [ ] Usage warnings
  - [ ] Billing notifications
  - [ ] Security alerts
- [ ] Email address shown
- [ ] Save preferences works
- [ ] Test notification button (if available)

---

## Section 4: My Subscription

### 4.1 Current Plan

**Access**: /admin/subscription/plan

- [ ] Page loads
- [ ] Current plan shown (Trial, Starter, Pro, Enterprise)
- [ ] Plan features list
- [ ] Usage limits shown
- [ ] "Upgrade" button visible (if not on highest tier)
- [ ] "Change Plan" button works
- [ ] Billing cycle info (monthly/annual)

### 4.2 Usage & Limits

**Access**: /admin/subscription/usage

- [ ] Page loads
- [ ] Usage metrics display:
  - [ ] API calls used / limit
  - [ ] Credits used / remaining
  - [ ] Storage used / limit
- [ ] Usage charts/graphs
- [ ] Historical usage data
- [ ] Export usage report button

### 4.3 Billing & Invoices

**Access**: /admin/subscription/billing

- [ ] Page loads
- [ ] Invoice history table:
  - [ ] Invoice date
  - [ ] Amount
  - [ ] Status (Paid/Pending)
  - [ ] Download PDF button
- [ ] Next billing date shown
- [ ] Payment method on file
- [ ] "Update Payment Method" button

### 4.4 Payment Methods

**Access**: /admin/subscription/payment

- [ ] Page loads
- [ ] Current payment method shown
- [ ] Card details (last 4 digits)
- [ ] Expiration date
- [ ] "Add New Card" button
- [ ] "Set as Default" works
- [ ] "Remove Card" works

---

## Section 5: Organization Management

### 5.1 Organization Settings

**Access**: /admin/organization/settings

- [ ] Page loads
- [ ] Organization name displayed
- [ ] Edit organization name works
- [ ] Organization logo upload
- [ ] Organization description
- [ ] Save changes works

### 5.2 Team Members

**Access**: /admin/organization/team

- [ ] Page loads
- [ ] Member list displays:
  - [ ] Name
  - [ ] Email
  - [ ] Role
  - [ ] Status
- [ ] "Invite Member" button works
- [ ] Invite modal:
  - [ ] Email input
  - [ ] Role selection
  - [ ] Send invite button
- [ ] Edit member role works
- [ ] Remove member works
- [ ] Pending invitations shown

### 5.3 Roles & Permissions

**Access**: /admin/organization/roles

- [ ] Page loads
- [ ] Role list (Owner, Admin, Member)
- [ ] Permission matrix visible
- [ ] Create custom role button
- [ ] Edit role permissions
- [ ] Assign role to members

### 5.4 Organization Billing

**Access**: /admin/organization/billing

- [ ] Page loads (if org admin/owner)
- [ ] Organization subscription shown
- [ ] Team seats used / available
- [ ] Add more seats button
- [ ] Organization invoices

---

## Section 6: System Administration

**Note**: Only visible to platform admins (role: admin)

### 6.1 User Management

**Access**: /admin/system/users

- [ ] Page loads
- [ ] User list displays:
  - [ ] Username
  - [ ] Email
  - [ ] Role
  - [ ] Subscription tier
  - [ ] Status
  - [ ] Last login
- [ ] Search users works
- [ ] Filter by:
  - [ ] Tier
  - [ ] Role
  - [ ] Status
  - [ ] Organization
- [ ] Click user row → opens detail page
- [ ] Bulk operations toolbar:
  - [ ] Select multiple users
  - [ ] Bulk role assignment
  - [ ] Bulk suspend
  - [ ] Bulk tier change
- [ ] Export users to CSV
- [ ] Import users from CSV

**User Detail Page**: /admin/system/users/{user_id}

- [ ] Page loads
- [ ] User info section
- [ ] 6 tabs visible:
  - [ ] Overview
  - [ ] Activity
  - [ ] Subscription
  - [ ] API Keys
  - [ ] Sessions
  - [ ] Audit Log
- [ ] Charts render
- [ ] Edit user button works
- [ ] Impersonate user button (careful!)
- [ ] Reset password button
- [ ] Suspend user button

### 6.2 Linux/Local Users

**Access**: /admin/system/linux-users (or wherever this is)

**IMPORTANT**: User reported this doesn't come up

- [ ] **Find the correct URL** - Where should this page be?
- [ ] Is it Linux system users?
- [ ] Is it local database users?
- [ ] Is it something else?
- [ ] What error appears when accessing?

**User Action Needed**: Please provide the exact URL or menu path

### 6.3 Billing Dashboard (Admin)

**Access**: /admin/system/billing

- [ ] Page loads
- [ ] Revenue metrics:
  - [ ] MRR (Monthly Recurring Revenue)
  - [ ] Total revenue
  - [ ] Churn rate
- [ ] Subscription breakdown by tier
- [ ] Recent transactions
- [ ] Failed payments list
- [ ] Manage subscriptions
- [ ] Issue refunds

### 6.4 Organizations (Admin View)

**Access**: /admin/system/organizations

- [ ] Page loads
- [ ] Organization list:
  - [ ] Org name
  - [ ] Members count
  - [ ] Subscription tier
  - [ ] Created date
- [ ] Create organization button
- [ ] Search organizations
- [ ] Filter by tier/status
- [ ] Click org → detail view

---

## Section 7: Services Management

### 7.1 Services Overview

**Access**: /admin/services

- [ ] Page loads
- [ ] Service cards display:
  - [ ] Open-WebUI
  - [ ] Center-Deep
  - [ ] Brigade
  - [ ] vLLM
  - [ ] PostgreSQL
  - [ ] Redis
  - [ ] Traefik
- [ ] Service status (Running/Stopped)
- [ ] CPU/Memory usage
- [ ] Restart service button
- [ ] View logs button
- [ ] Service configuration

### 7.2 Service Logs

**Access**: /admin/services/{service}/logs

- [ ] Page loads
- [ ] Log stream displays
- [ ] Real-time updates (WebSocket)
- [ ] Filter by log level
- [ ] Search logs
- [ ] Download logs
- [ ] Clear logs button

### 7.3 Service Configuration

**Access**: /admin/services/{service}/config

- [ ] Page loads
- [ ] Configuration form
- [ ] Environment variables
- [ ] Resource limits
- [ ] Network settings
- [ ] Save configuration

---

## Section 8: LLM Management

### 8.1 Model Catalog

**Access**: /admin/llm/models

- [ ] Page loads
- [ ] Installed models list
- [ ] Available models list
- [ ] Install model button
- [ ] Model details:
  - [ ] Name
  - [ ] Provider
  - [ ] Context length
  - [ ] Cost per 1M tokens
- [ ] Uninstall model

### 8.2 Provider Settings

**Access**: /admin/llm/providers

- [ ] Page loads
- [ ] Provider list:
  - [ ] OpenAI
  - [ ] Anthropic
  - [ ] Google
  - [ ] OpenRouter
- [ ] Add provider button
- [ ] Configure provider:
  - [ ] API key (system-wide)
  - [ ] Base URL
  - [ ] Enabled toggle
- [ ] Test connection
- [ ] Save settings ✅ (User said "I think I set everything I needed to set")

### 8.3 LLM Usage Analytics

**Access**: /admin/llm/usage

- [ ] Page loads
- [ ] Usage charts:
  - [ ] Requests per day
  - [ ] Tokens consumed
  - [ ] Cost breakdown
- [ ] Usage by model
- [ ] Usage by user
- [ ] Export usage data

### 8.4 Routing Rules

**Access**: /admin/llm/routing

- [ ] Page loads
- [ ] Routing rule list
- [ ] Create rule button
- [ ] Rule conditions:
  - [ ] User tier
  - [ ] Model requested
  - [ ] Load balancing
- [ ] Save rule

---

## Section 9: Infrastructure

### 9.1 Network Configuration

**Access**: /admin/system/network

- [ ] Page loads
- [ ] Network interfaces list
- [ ] Docker networks
- [ ] Port mappings
- [ ] Firewall rules
- [ ] DNS configuration
- [ ] SSL/TLS certificates

### 9.2 Traefik Management

**Access**: /admin/system/traefik

- [ ] Page loads
- [ ] Routes list
- [ ] Middleware configuration
- [ ] SSL certificate status
- [ ] Metrics (requests/sec)
- [ ] Error rate
- [ ] Add route button

### 9.3 Storage & Backup

**Access**: /admin/system/storage

- [ ] Page loads
- [ ] Disk usage metrics
- [ ] Volume list
- [ ] Backup status:
  - [ ] Last backup date
  - [ ] Next scheduled backup
  - [ ] Backup size
- [ ] Create backup button
- [ ] Restore from backup
- [ ] Backup configuration:
  - [ ] Schedule
  - [ ] Retention policy
  - [ ] Cloud storage (rclone)

### 9.4 Logs & Monitoring

**Access**: /admin/system/logs

**Note**: Implementation pending (architecture ready)

- [ ] Page loads (or shows "Coming Soon")
- [ ] System logs stream
- [ ] Application logs
- [ ] Error logs
- [ ] Filter by:
  - [ ] Service
  - [ ] Level
  - [ ] Date range
- [ ] Search logs
- [ ] Export logs

---

## Section 10: Security

### 10.1 Email Settings

**Access**: /admin/system/email

- [ ] Page loads ✅ (User set this up)
- [ ] Email provider configured:
  - [ ] Microsoft 365 OAuth2
  - [ ] SMTP settings
- [ ] Send test email works
- [ ] Email templates
- [ ] Email logs

### 10.2 Cloudflare Integration

**Access**: /admin/system/cloudflare

- [ ] Page loads
- [ ] API token status
- [ ] DNS records list
- [ ] Sync DNS button
- [ ] Firewall rules
- [ ] SSL mode

### 10.3 2FA Management

**Access**: /admin/system/2fa

**Note**: Backend complete, frontend pending

- [ ] Page loads (or shows "Coming Soon")
- [ ] Role-based policies:
  - [ ] Admin requires 2FA
  - [ ] Moderator optional
- [ ] User 2FA status list
- [ ] Enforce 2FA button
- [ ] Reset user 2FA
- [ ] Exemptions list

---

## Section 11: Analytics & Reports

### 11.1 Usage Analytics

**Access**: /admin/analytics/usage

- [ ] Page loads
- [ ] Usage dashboard:
  - [ ] Daily active users
  - [ ] API calls
  - [ ] Service usage
- [ ] Charts and graphs
- [ ] Export report

### 11.2 Revenue Analytics

**Access**: /admin/analytics/revenue

- [ ] Page loads
- [ ] Revenue metrics:
  - [ ] MRR
  - [ ] ARR
  - [ ] ARPU
  - [ ] LTV
- [ ] Revenue charts
- [ ] Subscription breakdown
- [ ] Export financial report

### 11.3 User Analytics

**Access**: /admin/analytics/users

- [ ] Page loads
- [ ] User growth chart
- [ ] Churn rate
- [ ] Retention cohorts
- [ ] User activity heatmap
- [ ] Export user data

---

## Section 12: Integrations

### 12.1 Brigade Integration

**Access**: /admin/integrations/brigade

- [ ] Page loads
- [ ] Brigade status (connected/disconnected)
- [ ] Agent list
- [ ] Create agent button
- [ ] Test connection

### 12.2 Webhook Management

**Access**: /admin/integrations/webhooks

- [ ] Page loads (if implemented)
- [ ] Webhook list
- [ ] Create webhook button
- [ ] Webhook logs
- [ ] Test webhook

---

## Section 13: Settings

### 13.1 System Settings

**Access**: /admin/settings/system

- [ ] Page loads
- [ ] Site name
- [ ] Site URL
- [ ] Logo upload
- [ ] Maintenance mode toggle
- [ ] Feature flags
- [ ] Save settings

### 13.2 Email Templates

**Access**: /admin/settings/email-templates

- [ ] Page loads
- [ ] Template list:
  - [ ] Welcome email
  - [ ] Password reset
  - [ ] Invoice email
  - [ ] Low balance alert
- [ ] Edit template
- [ ] Preview template
- [ ] Send test email

### 13.3 API Documentation

**Access**: /admin/settings/api-docs or /api/v1/docs

- [ ] Page loads
- [ ] Swagger/OpenAPI UI
- [ ] All endpoints listed
- [ ] Try it out works
- [ ] Schema definitions

---

## Section 14: Navigation & Layout

### 14.1 Side Menu (Dynamic)

**Test**: The side menu should change based on user role

**As Admin User**:
- [ ] "Personal" section visible
- [ ] "My Account" submenu
- [ ] "My Subscription" submenu
- [ ] "Organization" section visible (if org member)
- [ ] "System" section visible ✅ (admin only)

**As Regular User** (if you have a test account):
- [ ] "Personal" section visible
- [ ] "My Account" submenu
- [ ] "My Subscription" submenu
- [ ] "Organization" section visible (if org member)
- [ ] "System" section **NOT visible** (not admin)

**Visual Check**:
- [ ] Sections collapsible (click to expand/collapse)
- [ ] Active page highlighted
- [ ] Icons display correctly
- [ ] Smooth animations
- [ ] Responsive (mobile view)

### 14.2 Top Bar

- [ ] Organization selector (if multi-org)
- [ ] Notification bell
- [ ] User avatar/menu
- [ ] Theme toggle (light/dark/magic unicorn)
- [ ] Logout button

### 14.3 Mobile Navigation

**Test on mobile** (or resize browser to <768px):
- [ ] Hamburger menu appears
- [ ] Side menu slides in
- [ ] Bottom nav bar visible
- [ ] Touch-friendly buttons
- [ ] All sections accessible

---

## Section 15: Error Handling

### Test Error Scenarios

- [ ] Navigate to /admin/nonexistent-page → 404 page
- [ ] Logout, then try /admin → Redirect to login
- [ ] Try to access admin page as non-admin → Access denied
- [ ] Submit form with invalid data → Validation errors
- [ ] Disconnect internet → Offline message
- [ ] Backend error → User-friendly error message

---

## Section 16: Performance

### Page Load Times

- [ ] Dashboard loads in < 2 seconds
- [ ] User list loads in < 3 seconds (with 100+ users)
- [ ] Charts render smoothly
- [ ] No lag when navigating
- [ ] Images optimized (WebP)

### Browser Compatibility

Test in:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Chrome (Android)
- [ ] Mobile Safari (iOS)

---

## Section 17: Data Accuracy

### Verify Metrics Are Correct

- [ ] User count matches Keycloak
- [ ] Active services count is accurate
- [ ] API call metrics match usage logs
- [ ] Credit balance is correct
- [ ] Invoice totals match Stripe
- [ ] Usage charts show real data

---

## Common Issues & Solutions

### Issue: Page Shows "Loading..." Forever

**Possible Causes**:
1. API endpoint returning error
2. Frontend expecting different data format
3. Authentication token expired

**How to Debug**:
1. Open DevTools (F12) → Console tab
2. Look for JavaScript errors
3. Go to Network tab
4. Find failed API call (red, 500/400 status)
5. Click it → Preview tab → See error message
6. Report error to me with:
   - Page URL
   - API endpoint that failed
   - Error message

### Issue: "Undefined" or "NaN" Displayed

**Cause**: Frontend expecting data field that doesn't exist

**How to Report**:
- Screenshot the page
- Note which field shows "undefined"
- Open Console → Look for errors

### Issue: Button Click Does Nothing

**Possible Causes**:
1. JavaScript error preventing action
2. Missing API endpoint
3. Permission issue

**How to Debug**:
- Click button
- Watch Console for errors
- Watch Network tab for API calls
- If no network request, it's a frontend issue
- If API call fails, it's a backend issue

---

## How to Report Issues

For each broken feature, provide:

1. **Page URL**: e.g., /admin/account/api-keys
2. **What you tried**: e.g., "Clicked Save button"
3. **What happened**: e.g., "Nothing, no response"
4. **Expected result**: e.g., "Should save and show success message"
5. **Error message**: From console or on screen
6. **Screenshot**: If visual issue

---

## Review Progress Tracking

Use this to track your progress:

```
[ ] Section 1: Authentication ✅
[ ] Section 2: Dashboard ✅
[ ] Section 3: My Account
  [ ] 3.1 Profile
  [ ] 3.2 Security
  [ ] 3.3 API Keys
  [ ] 3.4 Notifications
[ ] Section 4: My Subscription
  [ ] 4.1 Plan
  [ ] 4.2 Usage
  [ ] 4.3 Billing
  [ ] 4.4 Payment
[ ] Section 5: Organization
[ ] Section 6: System Admin
[ ] Section 7: Services
[ ] Section 8: LLM Management
[ ] Section 9: Infrastructure
[ ] Section 10: Security
[ ] Section 11: Analytics
[ ] Section 12: Integrations
[ ] Section 13: Settings
[ ] Section 14: Navigation
[ ] Section 15: Error Handling
[ ] Section 16: Performance
[ ] Section 17: Data Accuracy
```

---

## Next Steps After Review

1. **Compile Issues List**:
   - Critical (blocks usage)
   - High (major feature broken)
   - Medium (minor issue)
   - Low (cosmetic)

2. **Prioritize Fixes**:
   - Fix critical first
   - Then high priority
   - Batch similar fixes

3. **Retest After Fixes**:
   - Verify fix works
   - Test related functionality
   - Mark as complete

4. **Polish & Refine**:
   - UX improvements
   - Visual polish
   - Performance optimization

---

**Ready to Begin**: Start with Section 1 (Authentication) and work through systematically!
