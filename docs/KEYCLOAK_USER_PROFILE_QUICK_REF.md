# Keycloak User Profile - Quick Reference

**Last Updated**: November 29, 2025

---

## Quick Commands

### Check Configuration Status
```bash
docker exec ops-center-direct python3 /app/scripts/configure_keycloak_user_profile.py
```

### Populate User Attributes
```bash
docker exec ops-center-direct python3 /app/scripts/quick_populate_users.py
```

### Verify Persistence
```bash
docker exec ops-center-direct python3 /app/scripts/verify_user_attributes.py
```

### View User Attributes (CLI)
```bash
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 --realm master --user admin --password your-admin-password

docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users -r uchub \
  --fields username,attributes --limit 5
```

---

## 5 Required Attributes

| Attribute Name | Type | Example Value | Description |
|----------------|------|---------------|-------------|
| `subscription_tier` | Enum | `professional` | User's subscription level |
| `subscription_status` | Enum | `active` | Account status |
| `api_calls_limit` | Integer | `10000` | API call quota per cycle |
| `api_calls_used` | Integer | `150` | Current API usage |
| `api_calls_reset_date` | String | `2025-11-29` | When quota resets |

---

## Subscription Tier Values

```
trial              - 7-day trial (700 API calls)
free               - Free tier (limited features)
starter            - $19/mo (1,000 API calls)
professional       - $49/mo (10,000 API calls)
enterprise         - $99/mo (unlimited API calls)
vip_founder        - VIP founder tier (unlimited)
founder_friend     - Founder friend tier (custom)
byok               - Bring Your Own Key tier
managed            - Managed service tier
```

---

## Subscription Status Values

```
active     - Subscription active and paid
inactive   - Subscription inactive (trial expired, payment failed)
suspended  - Account suspended (manual admin action)
cancelled  - User cancelled subscription
pending    - Payment or activation pending
```

---

## Web UI Configuration (One-Time Setup)

1. **Login**: https://auth.your-domain.com/admin/uchub/console
   - User: `admin` / Pass: `your-admin-password`

2. **Navigate**: Realm Settings → User Profile

3. **Add 5 Attributes** (click "Add attribute" for each):

   **subscription_tier**
   - Validator: Options (9 values: trial, free, starter, professional, enterprise, vip_founder, founder_friend, byok, managed)
   - Permissions: View (user, admin) | Edit (admin only)

   **subscription_status**
   - Validator: Options (5 values: active, inactive, suspended, cancelled, pending)
   - Permissions: View (user, admin) | Edit (admin only)

   **api_calls_limit**
   - Validator: Integer (min: 0, max: 1000000)
   - Permissions: View (user, admin) | Edit (admin only)

   **api_calls_used**
   - Validator: Integer (min: 0, max: 1000000)
   - Permissions: View (user, admin) | Edit (admin only)

   **api_calls_reset_date**
   - Validator: None (ISO 8601 date string)
   - Permissions: View (user, admin) | Edit (admin only)

4. **Save** configuration

5. **Run**: `docker exec ops-center-direct python3 /app/scripts/quick_populate_users.py`

---

## Expected Outcomes

**After Configuration**:
- ✓ User Management dashboard shows correct metrics (users, tiers, active count)
- ✓ Subscription tier persists across logout/login
- ✓ API usage tracking works correctly
- ✓ Billing integration functional
- ✓ Rate limiting enforced based on tier

**Before Configuration**:
- ✗ User metrics show 0 or incorrect values
- ✗ Subscription tier resets after logout
- ✗ API usage not tracked
- ✗ Billing integration broken

---

## Troubleshooting

### Metrics Still Show 0

**Check**:
```bash
# Verify attributes exist in Keycloak
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 --realm master --user admin --password your-admin-password

docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users -r uchub \
  --query email=admin@example.com --fields attributes
```

**Fix**:
1. Re-run population: `docker exec ops-center-direct python3 /app/scripts/quick_populate_users.py`
2. Clear browser cache: Ctrl+Shift+R
3. Restart Ops-Center: `docker restart ops-center-direct`

### Attributes Don't Persist

**Verify User Profile Enabled**:
```bash
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get realms/uchub \
  --fields attributes.userProfileEnabled
```

**Should Return**: `"userProfileEnabled" : "true"`

**If Not Enabled**:
```bash
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh update realms/uchub \
  -s 'attributes.userProfileEnabled=true'
```

### Web UI Not Accessible

**Check Keycloak Container**:
```bash
docker ps | grep keycloak
docker logs uchub-keycloak --tail 50
```

**Restart Keycloak**:
```bash
docker restart uchub-keycloak
# Wait 30 seconds for startup
sleep 30
```

---

## Validation Script Output

**Success**:
```
✓ User Profile feature is enabled
✓ All attributes correct after creation
✓ All attributes persist after logout
✓ All attributes persist after re-login

✓ SUCCESS: All attributes persist correctly across sessions!
```

**Failure**:
```
✓ User Profile feature is enabled
✗ Some attributes incorrect after logout

✗ FAILURE: Attributes not persisting correctly
User Profile may need manual configuration via Keycloak Admin Console.
```

---

## Files Reference

**Configuration Scripts**:
- `/home/muut/Production/UC-Cloud/services/ops-center/backend/scripts/configure_keycloak_user_profile.py`
- `/home/muut/Production/UC-Cloud/services/ops-center/backend/scripts/verify_user_attributes.py`
- `/home/muut/Production/UC-Cloud/services/ops-center/backend/scripts/quick_populate_users.py`

**Documentation**:
- Full Guide: `/home/muut/Production/UC-Cloud/services/ops-center/docs/KEYCLOAK_USER_PROFILE_SETUP.md`
- Quick Ref: `/home/muut/Production/UC-Cloud/services/ops-center/docs/KEYCLOAK_USER_PROFILE_QUICK_REF.md`

**Backend Integration**:
- `/home/muut/Production/UC-Cloud/services/ops-center/backend/keycloak_integration.py`
- Lines 352-417: Tier-specific helper functions

---

## Next Steps After Configuration

1. **Verify Metrics**: Go to https://your-domain.com/admin/system/users
   - Should show correct user counts, tier distribution

2. **Test User Journey**:
   - Login as user
   - Check subscription tier in profile
   - Logout
   - Login again
   - Verify tier still correct

3. **Monitor Logs**:
   ```bash
   docker logs ops-center-direct -f | grep -i "tier\|subscription"
   ```

4. **Update Documentation**: Mark User Profile as configured in your deployment docs

---

**Status**: Manual Web UI configuration required (one-time, 10-15 minutes)
**Priority**: High (blocks user metrics and billing integration)
**Difficulty**: Beginner-friendly (Web UI)
