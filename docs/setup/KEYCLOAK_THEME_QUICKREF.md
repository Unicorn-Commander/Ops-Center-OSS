# Keycloak Theme Quick Reference

## One-Command Deployment

```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center && ./deploy-keycloak-theme.sh
```

## Essential Commands

### Deploy Theme
```bash
./deploy-keycloak-theme.sh
```

### Verify Installation
```bash
./verify-keycloak-theme.sh
```

### Manual Verification
```bash
# Check theme exists in container
docker exec uchub-keycloak ls -la /opt/keycloak/themes/uc-1-pro

# View theme contents
docker exec uchub-keycloak find /opt/keycloak/themes/uc-1-pro -type f

# Check Keycloak logs
docker logs uchub-keycloak --tail 50
```

## Activation Steps

1. **Access Admin Console**
   ```
   http://localhost:9100/admin
   ```

2. **Select Realm**: `uchub` (not master)

3. **Navigate**: `Realm Settings → Themes`

4. **Configure**:
   - Login Theme: `uc-1-pro`
   - Account Theme: `uc-1-pro` (optional)
   - Email Theme: `uc-1-pro` (optional)

5. **Save** changes

6. **Test**: Open incognito window
   ```
   http://localhost:9100/realms/uchub/account
   ```

## Theme Customization

### Update Colors

Edit: `keycloak-theme/uc-1-pro/login/resources/css/login.css`

```css
:root {
    --uc-primary: #7C3AED;      /* Purple */
    --uc-secondary: #F59E0B;    /* Gold */
}
```

### Add Logo

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

## Troubleshooting

### Theme Not Appearing

```bash
# Restart Keycloak
docker restart uchub-keycloak

# Wait for healthy status
docker ps | grep uchub-keycloak

# Clear browser cache
# Ctrl+Shift+Delete (Windows/Linux)
# Cmd+Shift+Delete (Mac)
```

### CSS Not Loading

```bash
# Redeploy theme
./deploy-keycloak-theme.sh

# Hard refresh browser
# Ctrl+Shift+R (Windows/Linux)
# Cmd+Shift+R (Mac)

# Check CSS file exists
docker exec uchub-keycloak cat /opt/keycloak/themes/uc-1-pro/login/resources/css/login.css
```

### Permission Issues

```bash
# Fix permissions
docker exec uchub-keycloak chown -R keycloak:root /opt/keycloak/themes/uc-1-pro
docker exec uchub-keycloak chmod -R 755 /opt/keycloak/themes/uc-1-pro

# Restart
docker restart uchub-keycloak
```

## File Locations

### Source Files
```
/home/muut/Production/UC-1-Pro/services/ops-center/keycloak-theme/uc-1-pro/
├── theme.properties
└── login/
    ├── theme.properties
    └── resources/
        ├── css/login.css
        ├── img/
        └── js/
```

### Container Files
```
/opt/keycloak/themes/uc-1-pro/
```

### Scripts
```
/home/muut/Production/UC-1-Pro/services/ops-center/
├── deploy-keycloak-theme.sh       # Deploy theme
├── verify-keycloak-theme.sh       # Verify installation
├── KEYCLOAK_THEME_GUIDE.md        # Full documentation
└── KEYCLOAK_THEME_QUICKREF.md     # This file
```

## Container Info

- **Container Name**: `uchub-keycloak`
- **Keycloak Version**: 26.0
- **Themes Directory**: `/opt/keycloak/themes/`
- **Admin Console**: `http://localhost:9100/admin`
- **Health Check**: `docker inspect --format='{{.State.Health.Status}}' uchub-keycloak`

## Common Workflows

### First-Time Setup
```bash
# 1. Deploy theme
./deploy-keycloak-theme.sh

# 2. Verify installation
./verify-keycloak-theme.sh

# 3. Access admin console
open http://localhost:9100/admin

# 4. Configure realm theme (see Activation Steps above)

# 5. Test in incognito window
open http://localhost:9100/realms/uchub/account
```

### Update Theme After Changes
```bash
# 1. Edit theme files
nano keycloak-theme/uc-1-pro/login/resources/css/login.css

# 2. Redeploy
./deploy-keycloak-theme.sh

# 3. Hard refresh browser (Ctrl+Shift+R)
```

### Restore from Backup
```bash
# List backups
ls -la keycloak-theme/backups/

# Copy backup to source
cp -r keycloak-theme/backups/[backup-name] keycloak-theme/uc-1-pro

# Redeploy
./deploy-keycloak-theme.sh
```

## Testing

### Check Theme Applied
```bash
# Login page should show custom theme
curl -s http://localhost:9100/realms/uchub/account | grep -i "uc-1-pro"
```

### Browser DevTools Check
1. Open login page
2. Press F12
3. Go to Elements/Inspector tab
4. Check for custom CSS classes (`.uc1-card`, `.uc1-logo`, etc.)
5. Go to Network tab
6. Refresh (Ctrl+R)
7. Look for `/themes/uc-1-pro/login/resources/css/login.css`

## Support

- **Full Guide**: [KEYCLOAK_THEME_GUIDE.md](KEYCLOAK_THEME_GUIDE.md)
- **Theme README**: [keycloak-theme/README.md](keycloak-theme/README.md)
- **Keycloak Docs**: https://www.keycloak.org/docs/latest/server_development/#_themes

---

**Quick Deploy**: `cd /home/muut/Production/UC-1-Pro/services/ops-center && ./deploy-keycloak-theme.sh`
