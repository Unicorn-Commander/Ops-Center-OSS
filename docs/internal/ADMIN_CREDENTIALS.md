# 🔐 Admin Login Credentials

**Created:** October 8, 2025  
**Status:** ✅ Ready to use

---

## 👤 Your Admin Account

**Login URL:** https://your-domain.com

**Credentials:**
- **Username:** `aaron`
- **Email:** `admin@example.com`
- **Password:** `UnicornCommander2025!`

**Role:** Administrator (full access)

---

## 🧪 How to Login

1. Visit **https://your-domain.com**
2. Click **"Sign In to UC Cloud"**
3. On Keycloak login page, enter:
   - **Username or Email:** `aaron`
   - **Password:** `UnicornCommander2025!`
4. Click **Sign In**
5. Should redirect to **/admin** dashboard

---

## 🎯 What You'll See After Login

### Admin Dashboard Features:
- **User Management** - `/admin/users`
  - Create, edit, delete users
  - Assign roles
  - View active sessions
  - Force logout users
  
- **Billing Dashboard** - `/admin/billing`
  - Revenue statistics
  - Subscription analytics
  - Customer management
  - Payment history

- **System Status** - `/admin`
  - Service health monitoring
  - Resource usage
  - GPU metrics

---

## 🔒 Security Notes

1. **Change your password** after first login:
   - Visit Keycloak account settings
   - Or use password reset in Ops Center

2. **Enable 2FA** (optional but recommended):
   - Go to Keycloak account console
   - Security → Two-Factor Authentication

3. **Your password is stored in Keycloak**, not Ops Center
   - Keycloak handles all authentication
   - Ops Center just validates tokens

---

## 🛠️ Troubleshooting

### If login still fails:

**Check container logs:**
```bash
docker logs ops-center-direct --tail 50 | grep ERROR
```

**Verify user in Keycloak:**
```bash
python3 /tmp/create-admin-user.py
# Should say "User already exists"
```

**Reset password again:**
```bash
python3 /tmp/reset-keycloak-password.py
```

---

## 📊 Account Details

**Keycloak User ID:** `00a665e2-8703-4c06-a6b1-ec25cfcb98ef`  
**Realm:** `uchub`  
**Roles:** `admin`  
**Email Verified:** Yes  
**Account Status:** Enabled

---

## 🎉 Next Steps After Login

1. **Explore User Management** - Create test users
2. **Check Billing Dashboard** - View subscription analytics
3. **Configure Stripe** - Set up payment processing (optional)
4. **Set up Email** - Configure Office 365 SMTP (optional)
5. **Customize Settings** - Adjust system preferences

---

**You're all set! Login and enjoy your new admin dashboard! 🚀💜✨**
