# Ops-Center User Management - Manual Testing Guide

**Quick Reference for Browser Testing**

---

## TL;DR - What You Need to Do

1. **Open Browser**: Go to https://your-domain.com/admin/system/users
2. **Login**: Authenticate with Keycloak SSO if needed
3. **Test Features**: Follow checklist below
4. **Report Results**: Use the template at the bottom

**Backend Status**: ✅ Verified operational (all APIs working)
**Frontend Status**: ⏳ Needs your testing

---

## Quick Test Checklist

### Part 1: User List Page (5 min)

**URL**: https://your-domain.com/admin/system/users

- [ ] Page loads without errors
- [ ] User table shows data (not empty)
- [ ] Metrics cards show numbers (not 0)
- [ ] Search box works
- [ ] Filter dropdowns work (Tier, Role, Status)
- [ ] Click user row → Opens detail page

**Check Browser Console** (F12):
- [ ] No red errors
- [ ] Network tab shows `200 OK` for `/api/v1/admin/users`

### Part 2: User Detail Page (5 min)

**Access**: Click any user from list

- [ ] Page loads with 6 tabs (Overview, Roles, Sessions, API Keys, Activity, Impersonate)
- [ ] Overview tab shows user info
- [ ] Roles tab displays roles
- [ ] Can click "Manage Roles" button
- [ ] API Keys tab functional
- [ ] No "Can't interact" errors

**Check Browser Console**:
- [ ] No red errors
- [ ] Network tab shows `200 OK` for `/api/v1/admin/users/{userId}`

### Part 3: Test One Operation (5 min)

Pick **one** to test:

**Option A: Generate API Key**
1. Go to API Keys tab on user detail page
2. Click "Generate API Key"
3. Enter name and expiration
4. Verify key is created and displayed

**Option B: Assign Role**
1. Go to Roles tab on user detail page
2. Click "Manage Roles"
3. Try assigning a role (e.g., "developer")
4. Verify role appears in list

**Option C: CSV Export**
1. Go back to user list page
2. Click "Export CSV" button
3. Verify file downloads
4. Open CSV and check data

---

## Detailed Testing Procedure

### Setup (Required)

1. **Ensure You're Logged In**:
   - Go to: https://your-domain.com
   - If you see a login page, authenticate via Keycloak SSO
   - You should land on the dashboard after login

2. **Open Browser DevTools**:
   - Press `F12` (Chrome, Firefox, Edge)
   - Keep it open during testing
   - Switch to "Console" tab to watch for errors

3. **Verify Admin Access**:
   - Your account must have `admin` or `moderator` role
   - If unsure, check with Keycloak admin:
     - URL: https://auth.your-domain.com/admin/uchub/console
     - Login: `admin` / `your-admin-password`
     - Navigate to Users → Find your user → Check Role Mappings

### Test 1: User List Page

**Navigate**: https://your-domain.com/admin/system/users

#### What to Check:

**Visual Elements**:
- [ ] Page renders (not blank/white screen)
- [ ] Top metrics cards visible
- [ ] User table with columns: Email, Name, Tier, Status, Actions
- [ ] Search box at top
- [ ] Filter dropdowns: Tier, Role, Status
- [ ] Pagination controls (if >50 users)
- [ ] "Export CSV" button
- [ ] "Import Users" button

**Metrics Cards**:
- [ ] "Total Users" shows a number (not 0)
- [ ] "Active Users" shows a number
- [ ] "Tier Distribution" shows breakdown (trial, starter, pro, enterprise)

**Functionality**:
1. **Search**:
   - Type an email or username in search box
   - Verify user list filters to matching users
   - Clear search → Verify all users return

2. **Filters**:
   - Select "professional" from Tier dropdown
   - Verify only professional tier users shown
   - Select "admin" from Role dropdown
   - Verify only admin users shown
   - Clear filters → Verify all users return

3. **User Row Click**:
   - Click on any user row
   - Verify it navigates to `/admin/system/users/{userId}`
   - Verify user detail page loads

**Browser Console Check** (F12 → Console):
- [ ] No red error messages
- [ ] No `404 Not Found` errors
- [ ] No `CORS policy` errors

**Network Tab Check** (F12 → Network):
- [ ] Filter by "Fetch/XHR"
- [ ] Look for: `GET /api/v1/admin/users`
- [ ] Status should be: **200 OK** (not 401, 403, 404, 500)
- [ ] Response should contain: `{"users": [...], "total": N}`

**Screenshot**: Take a screenshot if errors occur

---

### Test 2: User Detail Page

**Navigate**: Click any user from the list

#### What to Check:

**Visual Elements**:
- [ ] Page renders with user info at top
- [ ] 6 tabs visible: Overview, Roles, Sessions, API Keys, Activity, Impersonate
- [ ] User profile card on left (avatar, name, email)
- [ ] Charts and stats on right

**Tab Navigation**:
1. **Overview Tab**:
   - [ ] User info card shows: email, name, created date
   - [ ] Subscription card shows: tier, status
   - [ ] API usage chart renders (if data available)
   - [ ] Action buttons: Reset Password, Enable/Disable, Delete

2. **Roles Tab**:
   - [ ] Current roles listed
   - [ ] "Manage Roles" button visible
   - [ ] Click "Manage Roles" → Modal opens
   - [ ] Modal shows: Available roles, Assigned roles, Permission matrix
   - [ ] Can select roles in modal
   - [ ] Modal has "Save" and "Cancel" buttons

3. **Sessions Tab**:
   - [ ] Active sessions listed (if any)
   - [ ] Shows: Session ID, IP, Device, Last Active
   - [ ] "Revoke" button for each session
   - [ ] "Revoke All Sessions" button at top

4. **API Keys Tab**:
   - [ ] Existing API keys listed (if any)
   - [ ] "Generate API Key" button visible
   - [ ] Click "Generate API Key" → Modal opens
   - [ ] Modal has: Name field, Expiration dropdown
   - [ ] Modal has "Generate" and "Cancel" buttons

5. **Activity Tab**:
   - [ ] Activity timeline renders
   - [ ] Events color-coded by type
   - [ ] Shows: Timestamp, Event type, Description
   - [ ] Can expand event for details

6. **Impersonate Tab**:
   - [ ] "Start Impersonation" button visible
   - [ ] Warning message displayed
   - [ ] Duration selector (hours)

**Functionality Tests**:

**Test A: Generate API Key**:
1. Go to "API Keys" tab
2. Click "Generate API Key"
3. Enter name: "Test Key"
4. Select expiration: "30 days"
5. Click "Generate"
6. Verify:
   - [ ] Success message appears
   - [ ] New key displayed (one-time view)
   - [ ] Key appears in list

**Test B: Assign Role**:
1. Go to "Roles" tab
2. Click "Manage Roles"
3. Select a role (e.g., "developer")
4. Click "Save"
5. Verify:
   - [ ] Success message appears
   - [ ] Role appears in "Current Roles" list
   - [ ] Modal closes

**Browser Console Check**:
- [ ] No red errors
- [ ] Network tab shows multiple `200 OK` responses:
  - `GET /api/v1/admin/users/{userId}`
  - `GET /api/v1/admin/users/{userId}/roles`
  - `GET /api/v1/admin/users/{userId}/sessions`
  - `GET /api/v1/admin/users/{userId}/api-keys`
  - `GET /api/v1/admin/users/{userId}/activity`

**Screenshot**: Capture user detail page (all 6 tabs visible)

---

### Test 3: Bulk Operations

**Navigate**: Back to user list page

#### What to Check:

**Selection**:
1. Click checkboxes next to 2-3 users
2. Verify:
   - [ ] Bulk actions toolbar appears at top
   - [ ] Shows: "X users selected"
   - [ ] Shows action buttons: Assign Roles, Change Tier, Suspend, Delete

**Test: Bulk Role Assignment**:
1. Select 2 users
2. Click "Assign Roles" from bulk toolbar
3. Verify:
   - [ ] Modal opens
   - [ ] Shows selected users
   - [ ] Role dropdown available
4. Select role: "analyst"
5. Click "Apply"
6. Verify:
   - [ ] Confirmation dialog appears
   - [ ] Shows: "Assign 'analyst' to 2 users?"
7. Click "Confirm"
8. Verify:
   - [ ] Success message: "Roles assigned successfully"
   - [ ] User list refreshes
   - [ ] Selection cleared

**Test: CSV Export**:
1. Click "Export CSV" button
2. Verify:
   - [ ] File download starts
   - [ ] Filename: `users_YYYYMMDD_HHMMSS.csv`
3. Open downloaded CSV
4. Verify:
   - [ ] Contains user data
   - [ ] Columns: id, username, email, firstName, lastName, tier, status

**Test: CSV Import**:
1. Click "Import Users" button
2. Verify:
   - [ ] Upload modal opens
   - [ ] File input visible
   - [ ] "Upload" and "Cancel" buttons
3. **Skip actual upload** (unless you have test CSV ready)

**Browser Console Check**:
- [ ] No errors during bulk operations
- [ ] Network tab shows POST requests with `200 OK`

---

### Test 4: Error Handling

**Test: Unauthorized Access**:
1. Open new incognito/private window
2. Go to: https://your-domain.com/admin/system/users
3. Verify:
   - [ ] Redirects to login page (not blank page)
   - [ ] Can authenticate via Keycloak
   - [ ] After login, returns to user list page

**Test: Session Expiry**:
1. Clear `localStorage` in browser console:
   ```javascript
   localStorage.clear()
   ```
2. Reload page
3. Verify:
   - [ ] Redirects to login (not 401 error displayed)
   - [ ] Can re-authenticate
   - [ ] Returns to working state

---

## What to Report

### If Everything Works ✅

**Copy this template**:

```
✅ User Management Testing - ALL PASSED

Test Date: [YYYY-MM-DD]
Tester: [Your Name]
Browser: [Chrome/Firefox/Edge] [Version]

Results:
✅ User list loads correctly
✅ Metrics display accurate data (X total users)
✅ Filters work (search, tier, role, status)
✅ User detail page opens and functions
✅ All 6 tabs render correctly
✅ API key generation works
✅ Role assignment works
✅ Bulk operations functional
✅ CSV export downloads
✅ No console errors
✅ All API calls return 200 OK

Screenshots attached: [Yes/No]

Status: PRODUCTION READY ✅
```

### If Issues Found ❌

**Copy this template**:

```
❌ User Management Testing - ISSUES FOUND

Test Date: [YYYY-MM-DD]
Tester: [Your Name]
Browser: [Chrome/Firefox/Edge] [Version]

Issues:

1. [Feature Name]
   Status: ❌ Failed
   Error: [Exact error message from console]
   Steps to reproduce:
   1. [Step 1]
   2. [Step 2]
   HTTP Status: [404/500/etc from Network tab]
   Screenshot: [Attached/Not attached]

2. [Feature Name]
   Status: 🟡 Partial
   Issue: [Description of problem]
   Impact: [High/Medium/Low]

Working Features:
✅ [List features that work]

Status: NEEDS FIXES ❌
```

---

## Common Issues & Quick Fixes

### Issue 1: Metrics Show 0

**Symptom**: Total users = 0, even though users exist

**Fix**:
```bash
docker exec ops-center-direct python3 /app/scripts/quick_populate_users.py
```

Then refresh page.

### Issue 2: 401 Unauthorized Errors

**Symptom**: All API calls fail with 401

**Fix**:
1. Go to: https://your-domain.com/auth/login
2. Re-authenticate
3. Hard reload: `Ctrl + Shift + R`

### Issue 3: Blank/White Screen

**Symptom**: Page loads but shows nothing

**Fix**:
1. Clear browser cache: `Ctrl + Shift + Delete`
2. Hard reload: `Ctrl + Shift + R`
3. If still broken, check console for errors

### Issue 4: "Can't interact" Error

**Symptom**: Detail page shows error message

**Check**:
1. Browser console for specific error
2. Network tab for failed API calls (404, 500)
3. Report exact error message

### Issue 5: CORS Errors

**Symptom**: Console shows "CORS policy blocked"

**This is a backend issue** - report it immediately with:
- Full error message
- Which API endpoint
- Browser and version

---

## Quick Reference

### Important URLs

- **User List**: https://your-domain.com/admin/system/users
- **Login**: https://your-domain.com/auth/login
- **Keycloak Admin**: https://auth.your-domain.com/admin/uchub/console
- **API Docs**: http://localhost:8084/docs (local only)

### Keyboard Shortcuts

- **Open DevTools**: `F12`
- **Hard Reload**: `Ctrl + Shift + R`
- **Clear Cache**: `Ctrl + Shift + Delete`

### Browser Console Commands

```javascript
// Check authentication
localStorage.getItem('authToken')

// Check user info
localStorage.getItem('user')

// Clear session
localStorage.clear()
```

---

## Time Estimate

- **Quick Test** (essentials only): 15 minutes
- **Full Test** (all features): 40 minutes
- **Comprehensive** (with screenshots): 60 minutes

---

## Next Steps After Testing

1. **Document Results**: Use templates above
2. **Share Findings**: Report via issue tracker or email
3. **If All Pass**: Mark user management as production-ready
4. **If Issues Found**: Prioritize fixes (P0 = critical, P1 = important, P2 = nice-to-have)

---

## Support & Documentation

**Need Help?**

- Backend verified working: See `TEST_RESULTS_SUMMARY.md`
- Full test report: See `API_CONNECTIVITY_TEST_REPORT.md`
- API reference: See `/services/ops-center/docs/API_REFERENCE.md`
- Admin guide: See `/services/ops-center/docs/ADMIN_OPERATIONS_HANDBOOK.md`

**Backend Commands**:

```bash
# Check container status
docker ps | grep ops-center

# View logs
docker logs ops-center-direct --tail 100

# Restart service
docker restart ops-center-direct

# Populate user attributes
docker exec ops-center-direct python3 /app/scripts/quick_populate_users.py
```

---

**Status**: Ready for manual testing
**Backend**: ✅ Verified operational
**Frontend**: ⏳ Awaiting your test results

**Happy Testing!** 🧪
