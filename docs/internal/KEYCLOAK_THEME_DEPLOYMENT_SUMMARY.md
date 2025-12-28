# Keycloak Theme Deployment - Complete Package

## Summary

A complete Keycloak theme deployment system has been created for UC-1 Pro with automated scripts, comprehensive documentation, and a custom purple/gold themed login interface.

## What Was Created

### 🚀 Deployment Scripts

#### 1. Main Deployment Script
**File**: `/home/muut/Production/UC-1-Pro/services/ops-center/deploy-keycloak-theme.sh`
- **Size**: 12K
- **Permissions**: Executable (755)
- **Purpose**: Automated theme deployment to uchub-keycloak container

**Features**:
- Pre-flight checks (Docker, container, source files)
- Automatic backup of existing theme
- File copying with proper permissions
- Container restart with health monitoring
- Comprehensive error handling
- Colored output and progress indicators
- Step-by-step success confirmation

#### 2. Verification Script
**File**: `/home/muut/Production/UC-1-Pro/services/ops-center/verify-keycloak-theme.sh`
- **Size**: 4.1K
- **Permissions**: Executable (755)
- **Purpose**: Verify theme installation and configuration

**Features**:
- Container status check
- Theme file verification
- Permission validation
- Ownership confirmation
- Health status monitoring
- File structure listing

### 📚 Documentation

#### 1. Complete Theme Guide
**File**: `/home/muut/Production/UC-1-Pro/services/ops-center/KEYCLOAK_THEME_GUIDE.md`
- **Size**: 13K
- **Content**: Comprehensive documentation covering:
  - Theme structure and organization
  - Step-by-step deployment instructions
  - Admin UI activation guide
  - Customization examples (CSS, logos, JavaScript)
  - Troubleshooting section
  - Advanced features (i18n, custom templates)
  - Production considerations

#### 2. Quick Reference Card
**File**: `/home/muut/Production/UC-1-Pro/services/ops-center/KEYCLOAK_THEME_QUICKREF.md`
- **Size**: 4.7K
- **Content**: Essential commands and quick workflows:
  - One-command deployment
  - Common troubleshooting steps
  - File locations reference
  - Testing procedures
  - Quick activation steps

#### 3. Theme README
**File**: `/home/muut/Production/UC-1-Pro/services/ops-center/keycloak-theme/README.md`
- **Size**: Updated with deployment script info
- **Content**: Theme-specific documentation

### 🎨 Custom Theme Files

#### Theme Structure
```
/home/muut/Production/UC-1-Pro/services/ops-center/keycloak-theme/uc-1-pro/
├── theme.properties                    (484 bytes)  - Main theme config
└── login/
    ├── theme.properties                (360 bytes)  - Login config
    ├── login.ftl                       (11K)        - Custom login template
    └── resources/
        ├── css/
        │   └── login.css              (14K)        - Custom styles
        ├── img/
        │   └── README.txt             (435 bytes)  - Logo instructions
        └── js/
            └── (empty, ready for custom JS)
```

#### Theme Features

**Visual Design**:
- Purple gradient background with animated overlay
- Glassmorphic login card with backdrop blur
- Purple (#7C3AED) and Gold (#F59E0B) color scheme
- Responsive design (mobile, tablet, desktop)
- Modern animations and transitions

**Customization**:
- CSS variables for easy color changes
- Logo support with glow effects
- Custom FreeMarker template
- Placeholder for custom JavaScript
- Support for custom images

**Accessibility**:
- WCAG 2.1 compliant
- Keyboard navigation support
- Screen reader friendly
- High contrast mode support
- Reduced motion support
- Proper ARIA labels

**Technical Features**:
- Extends base Keycloak theme
- Compatible with Keycloak 26.0
- Proper autofill styling
- Loading states
- Error animations
- Print-friendly styles

## How to Use

### Quick Start (One Command)

```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center
./deploy-keycloak-theme.sh
```

### Full Workflow

1. **Deploy Theme**:
   ```bash
   cd /home/muut/Production/UC-1-Pro/services/ops-center
   ./deploy-keycloak-theme.sh
   ```

2. **Verify Installation**:
   ```bash
   ./verify-keycloak-theme.sh
   ```

3. **Activate in Keycloak**:
   - Go to: `http://localhost:9100/admin`
   - Login with admin credentials
   - Select realm: `uchub`
   - Navigate: `Realm Settings → Themes`
   - Set Login Theme: `uc-1-pro`
   - Click Save

4. **Test**:
   - Open incognito window
   - Visit: `http://localhost:9100/realms/uchub/account`
   - Verify custom theme is displayed

## Configuration Details

### Target Container
- **Name**: `uchub-keycloak`
- **Image**: `quay.io/keycloak/keycloak:26.0`
- **Themes Directory**: `/opt/keycloak/themes/`

### Theme Installation Path
- **Container**: `/opt/keycloak/themes/uc-1-pro/`
- **Owner**: `keycloak:root`
- **Permissions**: `755`

### Deployment Process

1. **Validation**:
   - Checks Docker availability
   - Verifies container is running
   - Validates source theme structure
   - Confirms theme.properties exists

2. **Backup**:
   - Creates timestamped backup if theme exists
   - Stored in: `keycloak-theme/backups/`

3. **Deployment**:
   - Copies theme files to container
   - Sets proper ownership (keycloak:root)
   - Sets permissions (755)
   - Verifies installation

4. **Restart**:
   - Restarts Keycloak container
   - Waits for healthy status
   - Confirms theme availability

## Customization Guide

### Change Brand Colors

Edit: `keycloak-theme/uc-1-pro/login/resources/css/login.css`

```css
:root {
    --uc-primary: #7C3AED;      /* Your primary color */
    --uc-secondary: #F59E0B;    /* Your secondary color */
    --uc-dark: #1F2937;         /* Dark background */
}
```

Then redeploy:
```bash
./deploy-keycloak-theme.sh
```

### Add Custom Logo

1. Copy logo to theme:
   ```bash
   cp /path/to/logo.png keycloak-theme/uc-1-pro/login/resources/img/
   ```

2. Update `login/theme.properties`:
   ```properties
   logo=/themes/uc-1-pro/login/resources/img/logo.png
   ```

3. Redeploy:
   ```bash
   ./deploy-keycloak-theme.sh
   ```

### Add Custom JavaScript

1. Create JS file:
   ```bash
   nano keycloak-theme/uc-1-pro/login/resources/js/custom.js
   ```

2. Update `login/theme.properties`:
   ```properties
   scripts=js/custom.js
   ```

3. Redeploy:
   ```bash
   ./deploy-keycloak-theme.sh
   ```

## Troubleshooting

### Theme Not Appearing

**Problem**: Theme doesn't show in Keycloak admin dropdown

**Solution**:
```bash
# Restart Keycloak
docker restart uchub-keycloak

# Verify theme files
./verify-keycloak-theme.sh

# Check Keycloak logs
docker logs uchub-keycloak --tail 50
```

### CSS Not Loading

**Problem**: Styles not applied to login page

**Solution**:
```bash
# Clear browser cache completely
# Use Ctrl+Shift+Delete

# Hard refresh page
# Ctrl+Shift+R (Windows/Linux)
# Cmd+Shift+R (Mac)

# Redeploy theme
./deploy-keycloak-theme.sh
```

### Permission Errors

**Problem**: Permission denied errors in logs

**Solution**:
```bash
# Fix permissions manually
docker exec uchub-keycloak chown -R keycloak:root /opt/keycloak/themes/uc-1-pro
docker exec uchub-keycloak chmod -R 755 /opt/keycloak/themes/uc-1-pro

# Restart Keycloak
docker restart uchub-keycloak
```

## File Locations Reference

### Scripts
```
/home/muut/Production/UC-1-Pro/services/ops-center/
├── deploy-keycloak-theme.sh              # Main deployment script
├── verify-keycloak-theme.sh              # Verification script
├── KEYCLOAK_THEME_GUIDE.md              # Complete guide
├── KEYCLOAK_THEME_QUICKREF.md           # Quick reference
└── KEYCLOAK_THEME_DEPLOYMENT_SUMMARY.md # This file
```

### Theme Files
```
/home/muut/Production/UC-1-Pro/services/ops-center/keycloak-theme/
├── README.md                             # Theme documentation
├── backups/                              # Automatic backups
└── uc-1-pro/                            # Theme source
    ├── theme.properties
    └── login/
        ├── theme.properties
        ├── login.ftl
        └── resources/
            ├── css/login.css
            ├── img/
            └── js/
```

### Container Paths
```
/opt/keycloak/themes/uc-1-pro/           # Deployed theme location
```

## Maintenance

### Update Theme After Changes

```bash
# 1. Edit theme files
nano keycloak-theme/uc-1-pro/login/resources/css/login.css

# 2. Redeploy
./deploy-keycloak-theme.sh

# 3. Clear browser cache and refresh
```

### Backup Theme

Automatic backups are created on each deployment to:
```
keycloak-theme/backups/uc-1-pro_backup_YYYYMMDD_HHMMSS/
```

Manual backup:
```bash
docker cp uchub-keycloak:/opt/keycloak/themes/uc-1-pro \
  keycloak-theme/backups/manual_$(date +%Y%m%d_%H%M%S)
```

### Restore from Backup

```bash
# 1. Copy backup to source
cp -r keycloak-theme/backups/[backup-name] keycloak-theme/uc-1-pro

# 2. Redeploy
./deploy-keycloak-theme.sh
```

## Testing Checklist

- [ ] Deploy theme: `./deploy-keycloak-theme.sh`
- [ ] Verify installation: `./verify-keycloak-theme.sh`
- [ ] Check container logs for errors
- [ ] Access admin console: `http://localhost:9100/admin`
- [ ] Configure theme in realm settings
- [ ] Test login page in incognito window
- [ ] Verify responsive design (mobile, tablet, desktop)
- [ ] Test keyboard navigation
- [ ] Verify form validation and error states
- [ ] Check browser console for errors

## Support Resources

### Documentation
- **Complete Guide**: [KEYCLOAK_THEME_GUIDE.md](KEYCLOAK_THEME_GUIDE.md)
- **Quick Reference**: [KEYCLOAK_THEME_QUICKREF.md](KEYCLOAK_THEME_QUICKREF.md)
- **Theme README**: [keycloak-theme/README.md](keycloak-theme/README.md)

### External Resources
- [Keycloak Themes Documentation](https://www.keycloak.org/docs/latest/server_development/#_themes)
- [Keycloak Server Development Guide](https://www.keycloak.org/docs/latest/server_development/)

### Container Commands
```bash
# Check container status
docker ps | grep keycloak

# View logs
docker logs uchub-keycloak --tail 100

# Access container shell
docker exec -it uchub-keycloak bash

# List themes
docker exec uchub-keycloak ls /opt/keycloak/themes/
```

## Success Criteria

✅ **Deployment Complete When**:
1. `deploy-keycloak-theme.sh` exits successfully
2. `verify-keycloak-theme.sh` shows all checks passing
3. Theme appears in Keycloak admin dropdown
4. Login page displays custom styling
5. No errors in browser console
6. No errors in Keycloak container logs

## Version Information

- **Theme Version**: 1.0.0
- **Keycloak Version**: 26.0
- **Creation Date**: October 2025
- **Author**: Magic Unicorn Unconventional Technology & Stuff Inc
- **License**: MIT

---

## Quick Command Reference

```bash
# Deploy theme
cd /home/muut/Production/UC-1-Pro/services/ops-center
./deploy-keycloak-theme.sh

# Verify installation
./verify-keycloak-theme.sh

# View this summary
cat KEYCLOAK_THEME_DEPLOYMENT_SUMMARY.md

# Access admin console
open http://localhost:9100/admin

# Test login page
open http://localhost:9100/realms/uchub/account
```

---

**Status**: ✅ Ready for Deployment
**Next Step**: Run `./deploy-keycloak-theme.sh` to install the theme
