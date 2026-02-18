# Broken Features - Investigation & Fix List
**Date**: October 28, 2025
**Status**: INVESTIGATION IN PROGRESS
**Priority**: CRITICAL - Fix before adding new features

---

## User-Reported Issues

### 1. Frontend GUI Not Updating
**Status**: INVESTIGATING
**User Report**: "I'm not sure I saw the frontend gui updated. or the side menu."
**Expected**: Modernized dashboard with glassmorphism design
**Actual**: User not seeing visual updates

**Investigation Steps**:
- [x] Verify files deployed to public/ directory
- [x] Check React root div exists in index.html
- [ ] Test with hard refresh (Ctrl+Shift+R)
- [ ] Check browser console for errors
- [ ] Verify correct index.html being served
- [ ] Check for service worker caching issues

**Possible Causes**:
- Browser caching (most likely)
- Service worker caching old version
- User looking at different page/URL
- Static file serving issue

### 2. Local Users Doesn't Come Up
**Status**: NEEDS TESTING
**User Report**: "local users doesn't come up (though it used to)"
**Location**: Likely `/admin/system/linux-users` or similar
**Expected**: List of Linux system users
**Actual**: Page doesn't load or shows error

**Investigation Steps**:
- [ ] Navigate to Local Users page
- [ ] Check browser console for errors
- [ ] Check API endpoint: `/api/v1/users/local` or `/api/v1/system/linux-users`
- [ ] Check backend logs for errors
- [ ] Verify database connection
- [ ] Test API endpoint with curl

**Possible Causes**:
- API endpoint broken/changed
- Frontend route broken
- Database connection issue
- Permission/authentication issue
- Backend module not loaded

### 3. Can't Save Profile Pictures
**Status**: NEEDS TESTING
**User Report**: "I can't save my profile pics"
**Location**: Likely `/admin/account/profile` or user settings
**Expected**: Upload avatar image, save successfully
**Actual**: Save fails (error message unknown)

**Investigation Steps**:
- [ ] Navigate to profile/account page
- [ ] Try uploading profile picture
- [ ] Check browser console for errors
- [ ] Check Network tab for failed requests
- [ ] Check API endpoint for avatar upload
- [ ] Check file permissions on avatars directory
- [ ] Verify backend upload handler exists

**Known Issue**: Avatar directory is owned by root (discovered during deployment)
```bash
drwxr-xr-x 2 root root 4096 Oct 28 00:11 avatars
```

**Possible Causes**:
- File permission issue (root owns avatars/)
- API endpoint not implemented
- File upload size limit
- Backend storage handler broken
- Frontend upload component broken

### 4. Can't Save API Keys
**Status**: NEEDS TESTING
**User Report**: "I can't save api keys"
**Location**: Likely `/admin/account/api-keys` or `/admin/system/api-keys`
**Expected**: Generate API key, save to database
**Actual**: Save fails (error message unknown)

**Investigation Steps**:
- [ ] Navigate to API Keys page
- [ ] Try generating new API key
- [ ] Try saving/updating API key
- [ ] Check browser console for errors
- [ ] Check Network tab for failed requests
- [ ] Check database table: `api_keys`
- [ ] Check API endpoint: `/api/v1/admin/users/{user_id}/api-keys`
- [ ] Verify backend API key module loaded

**Backend Module**: `backend/user_api_keys.py` (577 lines, created in Phase 1)

**Possible Causes**:
- Database table missing
- API endpoint not registered
- Frontend component broken
- Permission/authentication issue
- bcrypt hashing issue

### 5. Other Things Not Working
**Status**: USER TO SPECIFY
**User Report**: "etc. etc."
**Expected**: User to provide more specific examples

**Investigation Needed**:
- [ ] Ask user for specific list of broken features
- [ ] Systematically test each section
- [ ] Create comprehensive test plan

---

## 2FA Implementation Approach (User Question)

### User Question
"how will 2fa be executed (with email or something)? I don't want to make 2fa mandatory right now."

### Answer

**How 2FA Works in This System**:

#### 1. Keycloak TOTP (Time-Based One-Time Password) - **RECOMMENDED**
- **Method**: Authenticator app (Google Authenticator, Authy, Microsoft Authenticator)
- **How**: User scans QR code with phone app, enters 6-digit code to verify
- **Pros**: Industry standard, secure, works offline
- **Cons**: Requires smartphone app

**Setup Flow**:
1. User goes to Keycloak account console
2. Clicks "Configure Authenticator"
3. Scans QR code with phone app
4. Enters verification code
5. 2FA enabled

#### 2. Keycloak WebAuthn (FIDO2) - **MOST SECURE**
- **Method**: Security keys (YubiKey) or biometrics (fingerprint, Face ID)
- **How**: User registers hardware key or biometric
- **Pros**: Most secure, phishing-resistant
- **Cons**: Requires hardware key or compatible device

#### 3. Email-Based OTP - **NOT NATIVELY SUPPORTED**
- **Status**: Keycloak does NOT support email 2FA natively
- **Workaround**: Would require custom Keycloak extension or external service
- **Recommendation**: Use TOTP instead (more secure anyway)

### 2FA Policy Configuration (Role-Based)

**Important**: 2FA is **OPTIONAL** by default, NOT mandatory!

The 2FA backend we deployed allows **role-based policies**:

```javascript
// Example: Require 2FA for admins only, 7-day grace period
{
  "role": "admin",
  "require_2fa": true,
  "grace_period_days": 7,
  "enforcement_date": "2025-11-04"  // 7 days from now
}

// Example: Optional 2FA for regular users
{
  "role": "viewer",
  "require_2fa": false,  // Optional, not required
  "grace_period_days": 0
}
```

**Default Behavior**:
- 2FA is **OPTIONAL** for all users
- Admin can configure role-based requirements
- Grace period allows transition time
- Users can enable 2FA voluntarily via Keycloak account console

**User Voluntary Setup**:
Users can enable 2FA themselves without admin requirement:
1. Visit: https://auth.unicorncommander.ai/realms/uchub/account
2. Login with their credentials
3. Go to "Account Security" → "Signing In"
4. Click "Set up Authenticator Application"
5. Follow QR code setup

**Admin Enforcement** (via 2FA UI we're building):
- Admin sets policy: "Admins must enable 2FA by Nov 4, 2025"
- Users in admin role get notified
- After Nov 4, admin users must set up 2FA to continue
- Regular users not affected

### Recommendation

**Phase 1 (Now)**:
- Leave 2FA **OPTIONAL** for all roles
- Complete the 2FA frontend UI (4-6 hours)
- Test the optional 2FA flow
- Document user setup instructions

**Phase 2 (Later, when ready)**:
- Enable 2FA requirement for admin role ONLY
- 30-day grace period for transition
- Email notifications to affected users
- Keep regular users optional

**Phase 3 (Future, optional)**:
- Consider requiring 2FA for all paid tiers (professional+)
- Keep trial/starter optional
- Market as security feature

---

## Systematic Testing Plan

### Section 1: Authentication & Access
- [ ] Login with OAuth (Google/GitHub/Microsoft)
- [ ] Login with email/password
- [ ] Logout works correctly
- [ ] Session persists across page refresh
- [ ] Unauthorized access redirects to login

### Section 2: Dashboard
- [ ] Main dashboard loads
- [ ] All metrics cards show data
- [ ] Charts render correctly
- [ ] No console errors
- [ ] Visual styling matches expectations

### Section 3: User Management
- [ ] User list loads with data
- [ ] Search/filter works
- [ ] Click user row opens detail page
- [ ] User detail tabs load
- [ ] Edit user works
- [ ] Bulk operations toolbar appears

### Section 4: Account Settings
- [ ] Profile page loads
- [ ] Can edit profile info
- [ ] **BROKEN**: Can't save profile picture
- [ ] Password change works (if applicable)
- [ ] Security settings load

### Section 5: API Keys Management
- [ ] API Keys page loads
- [ ] **BROKEN**: Can't save/generate API keys
- [ ] Can view existing keys
- [ ] Can delete keys
- [ ] Rate limiting works

### Section 6: System Management
- [ ] **BROKEN**: Local users doesn't come up
- [ ] Services page loads
- [ ] Network configuration loads
- [ ] Traefik management works
- [ ] Storage & backup loads

### Section 7: Billing
- [ ] Subscription page loads
- [ ] Usage metrics show
- [ ] Invoice history loads
- [ ] Payment methods page works
- [ ] Plan upgrade/downgrade flow

### Section 8: Organizations
- [ ] Organization list loads
- [ ] Create organization works
- [ ] Organization detail pages load
- [ ] Team management works
- [ ] Invite members works

### Section 9: LLM Management
- [ ] LLM models page loads
- [ ] Provider settings work
- [ ] Model catalog loads
- [ ] Usage analytics show
- [ ] Configuration saves

### Section 10: Integrations
- [ ] Email provider settings work
- [ ] Cloudflare integration works
- [ ] Brigade integration shows
- [ ] External services load

---

## Priority Fix Order

### Priority 1: Critical User-Facing Issues (Fix First)
1. **Can't save profile pictures** - User can't customize profile
2. **Can't save API keys** - Blocks API access configuration
3. **Local users doesn't come up** - System management broken
4. **Frontend not updating** - User not seeing fixes

### Priority 2: Important Functionality
5. Test all sections systematically
6. Fix any broken API endpoints
7. Fix any database connectivity issues
8. Fix permission issues (avatars directory)

### Priority 3: Polish & Enhancement
9. Complete 2FA frontend UI (after fixing broken features)
10. Implement Logs & Alerts (after core functionality stable)
11. Add real API keys for external services
12. Performance optimization

---

## Investigation Methodology

For each broken feature, follow this process:

### 1. Reproduce the Issue
- Navigate to the page
- Attempt the action
- Document exact error message
- Screenshot if helpful

### 2. Check Frontend
- Open browser DevTools (F12)
- Check Console tab for JavaScript errors
- Check Network tab for failed API requests
- Check Elements tab for missing UI components

### 3. Check Backend
- Check backend logs: `docker logs ops-center-direct --tail 100`
- Test API endpoint directly with curl
- Verify endpoint is registered in server.py
- Check database table exists

### 4. Check Database
- Connect to PostgreSQL: `docker exec unicorn-postgresql psql -U unicorn -d unicorn_db`
- Verify table exists: `\dt table_name`
- Check table structure: `\d table_name`
- Test sample query

### 5. Check Permissions
- File permissions: `ls -la path/to/file`
- User permissions in Keycloak
- API endpoint authorization requirements

### 6. Fix & Test
- Apply fix (backend or frontend)
- Rebuild if needed: `npm run build` or `docker restart`
- Test fix works
- Document what was fixed

### 7. Document
- Add to DEPLOYMENT_SUMMARY or new doc
- Note what was broken
- Note what fixed it
- Add to test plan for regression testing

---

## Next Steps

**Immediate Actions**:
1. **User to provide more details on broken features**:
   - Exact page URLs that don't work
   - Error messages seen
   - Screenshots if possible

2. **Systematic testing**:
   - Go through test plan section by section
   - Document what works vs. what's broken
   - Prioritize fixes

3. **Fix broken features first**:
   - Don't add new features until core functionality stable
   - Focus on user-reported issues
   - Test fixes thoroughly

4. **Section-by-section refinement** (per user request):
   - Once core features working, go section by section
   - Polish each section before moving to next
   - Ensure quality over quantity

---

## Questions for User

1. **Frontend Updates**:
   - Which URL are you accessing? (https://unicorncommander.ai or localhost:8084?)
   - Have you tried hard refresh? (Ctrl+Shift+F5)
   - Which browser are you using?

2. **Local Users**:
   - What's the exact URL where local users should appear?
   - What error message do you see (if any)?
   - Is it Linux users, Keycloak users, or database users?

3. **Profile Pictures**:
   - Where are you trying to upload? (Account settings?)
   - What happens when you click save? (Error message?)
   - What file format are you uploading? (PNG, JPG?)

4. **API Keys**:
   - Which API keys? (User API keys, LLM provider keys, or system keys?)
   - Where are you trying to save them?
   - What error do you see?

5. **Other Broken Features**:
   - Can you list 3-5 more specific features that don't work?
   - Which sections of the admin panel work correctly?
   - Which sections are completely broken?

---

## Notes

- User requested: "let's continue with what we need to first, just make note of all these other things"
- User wants systematic section-by-section refinement
- User prefers fixing over adding new features
- User has real API keys ready to plug in once interfaces work

---

**Status**: Waiting for user input on specific broken features
**Next Action**: Systematic testing of each section to identify all issues
