# Keycloak Theme Deployment Guide for UC-1 Pro

## Overview

This guide provides complete instructions for creating, deploying, and activating a custom Keycloak theme for the UC-1 Pro platform.

## Prerequisites

- Docker installed and running
- uchub-keycloak container running
- Access to Keycloak admin console
- Basic understanding of HTML/CSS for theme customization

## Quick Start

```bash
# Deploy the theme
cd /home/deploy/Production/UC-1-Pro/services/ops-center
./deploy-keycloak-theme.sh
```

## Theme Structure

The custom theme should be located at:
```
/home/deploy/Production/UC-1-Pro/services/ops-center/keycloak-theme/uc-1-pro/
```

### Standard Theme Directory Structure

```
uc-1-pro/
├── theme.properties          # Theme metadata and configuration
├── login/                    # Login page customization
│   ├── resources/
│   │   ├── css/
│   │   │   └── login.css    # Custom login styles
│   │   ├── img/             # Images and logos
│   │   └── js/              # Custom JavaScript
│   ├── messages/            # Internationalization
│   │   └── messages_en.properties
│   └── theme.properties     # Login-specific config
├── account/                 # Account management pages
│   ├── resources/
│   │   └── css/
│   │       └── account.css
│   └── theme.properties
├── email/                   # Email template customization
│   ├── html/
│   ├── text/
│   └── messages/
└── common/                  # Shared resources
    └── resources/
        ├── css/
        ├── img/
        └── js/
```

### Minimal Theme Configuration

The script will create a basic `theme.properties` if none exists:

```properties
# Parent theme to extend
parent=keycloak
import=common/keycloak

# Theme Metadata
name=UC-1 Pro Theme
version=1.0.0
author=Magic Unicorn Tech

# Styling
styles=css/login.css css/styles.css

# Supported locales
locales=en
```

## Deployment Process

### 1. Create Your Custom Theme

#### Option A: Start with Template (Auto-generated)

Run the deployment script - it will create a basic template:

```bash
./deploy-keycloak-theme.sh
```

#### Option B: Create Manually

```bash
# Create theme directory structure
mkdir -p keycloak-theme/uc-1-pro/{login,account,email,common}/resources/{css,img,js}

# Create theme.properties
cat > keycloak-theme/uc-1-pro/theme.properties << 'EOF'
parent=keycloak
import=common/keycloak
name=UC-1 Pro Theme
version=1.0.0
author=Magic Unicorn Tech
styles=css/login.css
locales=en
EOF
```

### 2. Customize Your Theme

#### Custom Login Page CSS Example

Create `login/resources/css/login.css`:

```css
/* UC-1 Pro Custom Login Theme */

/* Brand colors */
:root {
    --uc-primary: #7C3AED;      /* Purple */
    --uc-secondary: #F59E0B;    /* Gold */
    --uc-dark: #1F2937;         /* Dark gray */
    --uc-light: #F3F4F6;        /* Light gray */
}

/* Login container */
.login-pf body {
    background: linear-gradient(135deg, var(--uc-dark) 0%, var(--uc-primary) 100%);
}

/* Login card */
#kc-login {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    padding: 2rem;
}

/* Logo */
#kc-header-wrapper {
    text-align: center;
    margin-bottom: 2rem;
}

#kc-logo-wrapper img {
    max-width: 200px;
    height: auto;
}

/* Form elements */
.pf-c-form-control {
    border-radius: 8px;
    border: 2px solid var(--uc-light);
    padding: 0.75rem;
    transition: all 0.3s ease;
}

.pf-c-form-control:focus {
    border-color: var(--uc-primary);
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.1);
}

/* Buttons */
.pf-c-button.pf-m-primary {
    background-color: var(--uc-primary);
    border: none;
    border-radius: 8px;
    padding: 0.75rem 2rem;
    font-weight: 600;
    transition: all 0.3s ease;
}

.pf-c-button.pf-m-primary:hover {
    background-color: var(--uc-secondary);
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(124, 58, 237, 0.3);
}

/* Header text */
#kc-page-title {
    color: var(--uc-dark);
    font-size: 1.8rem;
    font-weight: 700;
    margin-bottom: 1rem;
}

/* Links */
#kc-form-options a {
    color: var(--uc-primary);
    text-decoration: none;
}

#kc-form-options a:hover {
    color: var(--uc-secondary);
    text-decoration: underline;
}
```

#### Custom Logo

Place your logo in the theme:

```bash
# Copy logo to theme resources
cp /path/to/your/logo.png keycloak-theme/uc-1-pro/login/resources/img/uc-logo.png
```

Update `login/theme.properties`:

```properties
parent=../base/login
import=common/keycloak
styles=css/login.css

# Custom logo
logo=/themes/uc-1-pro/login/resources/img/uc-logo.png
```

### 3. Deploy the Theme

Run the deployment script:

```bash
./deploy-keycloak-theme.sh
```

The script will:
1. Validate theme structure
2. Backup existing theme (if any)
3. Copy theme files to container
4. Set proper permissions
5. Restart Keycloak
6. Verify installation

## Activating the Theme in Keycloak

### Step-by-Step Instructions

#### 1. Access Keycloak Admin Console

**URL:** `http://localhost:9100/admin`
(Or your configured external URL)

**Credentials:**
- Username: `admin`
- Password: Your configured admin password

#### 2. Select Your Realm

- In the top-left dropdown, select your realm (default: **uchub**)
- Do NOT select "master" realm unless configuring master realm

#### 3. Navigate to Theme Settings

- Click **Realm Settings** in the left sidebar
- Click the **Themes** tab

#### 4. Configure Theme Settings

Set the following dropdowns:

| Setting | Value | Purpose |
|---------|-------|---------|
| **Login theme** | `uc-1-pro` | Login pages appearance |
| **Account theme** | `uc-1-pro` | User account management pages |
| **Admin console theme** | `uc-1-pro` (optional) | Admin UI appearance |
| **Email theme** | `uc-1-pro` (optional) | Email templates |

#### 5. Save Changes

- Click **Save** at the bottom
- You should see a success message

#### 6. Verify Theme Application

**Test the Login Page:**

1. Open a **new incognito/private browser window**
2. Navigate to your application's login URL
3. You should see the custom theme applied

**Example test URL:**
```
http://localhost:9100/realms/uchub/account
```

## Verification Commands

### Check Theme Files in Container

```bash
# List theme directory
docker exec uchub-keycloak ls -la /opt/keycloak/themes/uc-1-pro

# View theme properties
docker exec uchub-keycloak cat /opt/keycloak/themes/uc-1-pro/theme.properties

# Check login resources
docker exec uchub-keycloak ls -la /opt/keycloak/themes/uc-1-pro/login/resources/
```

### Check Keycloak Logs

```bash
# View recent logs
docker logs uchub-keycloak --tail 100

# Follow logs in real-time
docker logs uchub-keycloak --follow

# Search for theme-related errors
docker logs uchub-keycloak 2>&1 | grep -i theme
```

### Test Theme Loading

```bash
# Check if theme is recognized
curl -s http://localhost:9100/realms/uchub/account | grep -i "uc-1-pro"
```

## Troubleshooting

### Theme Not Appearing in Dropdown

**Possible Causes:**
1. Theme not properly installed
2. Invalid `theme.properties`
3. Keycloak cache not cleared

**Solutions:**

```bash
# 1. Verify theme installation
docker exec uchub-keycloak ls /opt/keycloak/themes/ | grep uc-1-pro

# 2. Check theme.properties syntax
docker exec uchub-keycloak cat /opt/keycloak/themes/uc-1-pro/theme.properties

# 3. Restart Keycloak to clear cache
docker restart uchub-keycloak

# 4. Wait for healthy status
docker ps | grep uchub-keycloak
```

### Theme Not Applying to Login Page

**Possible Causes:**
1. Browser cache
2. Theme selected for wrong realm
3. CSS not loading

**Solutions:**

```bash
# 1. Clear browser cache completely
# Use Ctrl+Shift+Delete or Cmd+Shift+Delete

# 2. Use incognito/private window
# This bypasses cache entirely

# 3. Check browser console for CSS errors
# Press F12 → Console tab

# 4. Verify theme is set in correct realm
# Admin Console → Select Realm → Realm Settings → Themes
```

### CSS Changes Not Reflecting

**Possible Causes:**
1. Browser cache
2. Keycloak cache
3. File not copied correctly

**Solutions:**

```bash
# 1. Redeploy theme
./deploy-keycloak-theme.sh

# 2. Hard refresh browser
# Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)

# 3. Check CSS file in container
docker exec uchub-keycloak cat /opt/keycloak/themes/uc-1-pro/login/resources/css/login.css

# 4. Verify file permissions
docker exec uchub-keycloak ls -la /opt/keycloak/themes/uc-1-pro/login/resources/css/
```

### Permission Denied Errors

**Possible Causes:**
1. Incorrect file ownership
2. Wrong permissions

**Solutions:**

```bash
# Fix ownership and permissions
docker exec uchub-keycloak chown -R keycloak:root /opt/keycloak/themes/uc-1-pro
docker exec uchub-keycloak chmod -R 755 /opt/keycloak/themes/uc-1-pro

# Restart Keycloak
docker restart uchub-keycloak
```

## Advanced Customization

### Custom Login Page Template

Override FreeMarker templates:

1. Create `login/login.ftl` in your theme:

```bash
mkdir -p keycloak-theme/uc-1-pro/login
```

2. Copy base template and customize:

```bash
# Get base template from Keycloak
docker exec uchub-keycloak cat /opt/keycloak/lib/lib/main/org.keycloak.keycloak-themes-*.jar
# Extract and modify login.ftl
```

### Custom JavaScript

Add custom behavior:

```javascript
// login/resources/js/custom.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('UC-1 Pro Theme Loaded');

    // Add custom animations
    const loginCard = document.getElementById('kc-login');
    if (loginCard) {
        loginCard.style.animation = 'fadeIn 0.5s ease-in';
    }
});
```

Include in `login/theme.properties`:

```properties
scripts=js/custom.js
```

### Internationalization

Add custom messages:

```bash
# Create messages file
cat > keycloak-theme/uc-1-pro/login/messages/messages_en.properties << 'EOF'
loginTitle=Welcome to UC-1 Pro
loginTitleHtml=<strong>UC-1 Pro</strong> Operations Center
doLogIn=Sign In to Continue
usernameOrEmail=Email or Username
password=Password
rememberMe=Keep me signed in
loginButton=Sign In
EOF
```

## Updating the Theme

### Making Changes

1. Edit theme files in source directory:
   ```bash
   cd /home/deploy/Production/UC-1-Pro/services/ops-center/keycloak-theme/uc-1-pro
   ```

2. Redeploy using script:
   ```bash
   cd /home/deploy/Production/UC-1-Pro/services/ops-center
   ./deploy-keycloak-theme.sh
   ```

3. Clear browser cache and refresh

### Version Control

Track theme changes in git:

```bash
cd /home/deploy/Production/UC-1-Pro
git add services/ops-center/keycloak-theme/
git commit -m "Update Keycloak theme: [description of changes]"
```

## Backup and Restore

### Backup Current Theme

The deployment script automatically creates backups:

```bash
# Backups are stored in:
/home/deploy/Production/UC-1-Pro/services/ops-center/keycloak-theme/backups/
```

### Manual Backup

```bash
# Export theme from container
docker cp uchub-keycloak:/opt/keycloak/themes/uc-1-pro \
  ./keycloak-theme/backups/uc-1-pro_manual_$(date +%Y%m%d_%H%M%S)
```

### Restore from Backup

```bash
# Copy backup to source directory
cp -r ./keycloak-theme/backups/[backup-name] ./keycloak-theme/uc-1-pro

# Redeploy
./deploy-keycloak-theme.sh
```

## Production Considerations

### Performance

1. **Minimize CSS/JS:** Minify resources for production
2. **Optimize Images:** Compress logos and backgrounds
3. **CDN Integration:** Consider external CSS frameworks via CDN

### Security

1. **No Sensitive Data:** Don't include secrets in theme files
2. **XSS Prevention:** Sanitize any custom JavaScript
3. **CSP Headers:** Ensure Content Security Policy compatibility

### Testing

Test theme across:
- Multiple browsers (Chrome, Firefox, Safari, Edge)
- Mobile devices (responsive design)
- Different screen sizes
- Light/dark mode preferences

## Resources

### Official Documentation

- [Keycloak Themes Documentation](https://www.keycloak.org/docs/latest/server_development/#_themes)
- [Server Developer Guide](https://www.keycloak.org/docs/latest/server_development/)

### Example Themes

- [Keycloak Default Themes](https://github.com/keycloak/keycloak/tree/main/themes/src/main/resources/theme)
- [Community Themes](https://github.com/topics/keycloak-theme)

## Support

For issues or questions:
- Check Keycloak logs: `docker logs uchub-keycloak`
- Review this guide's troubleshooting section
- Consult Keycloak documentation

---

**Created:** October 2025
**Version:** 1.0.0
**Author:** Magic Unicorn Unconventional Technology & Stuff Inc
**License:** MIT
