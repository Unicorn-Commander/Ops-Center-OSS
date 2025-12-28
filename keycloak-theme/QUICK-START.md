# UC-1 Pro Keycloak Theme - Quick Start Guide

## 1-Minute Deployment

### Prerequisites
- Docker is running
- Keycloak container is running (name: `uchub-keycloak`)
- Theme files are in: `/home/muut/Production/UC-1-Pro/services/ops-center/keycloak-theme/uc-1-pro/`

### Deploy in 3 Steps

#### Step 1: Run Deployment Script
```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center
./deploy-keycloak-theme.sh
```

#### Step 2: Activate Theme
1. Go to: https://auth.your-domain.com/admin
2. Navigate to: **Realm Settings** → **Themes**
3. Set **Login Theme** to: `uc-1-pro`
4. Click **Save**

#### Step 3: Test
Visit: https://auth.your-domain.com/realms/YOUR-REALM/account

You should see:
- Purple gradient background
- Glassmorphic login card
- "Welcome to Unicorn Commander" title
- Purple/gold styling

## Optional: Add Logo

```bash
# Place your logo file
cp /path/to/colonel-logo.png keycloak-theme/uc-1-pro/login/resources/img/colonel-logo.png

# Redeploy
./deploy-keycloak-theme.sh
```

## Troubleshooting

### Theme not appearing?
```bash
# Check if theme exists in container
docker exec uchub-keycloak ls /opt/keycloak/themes/uc-1-pro

# Check Keycloak logs
docker logs uchub-keycloak | tail -50

# Restart Keycloak
docker restart uchub-keycloak
```

### Styles not applying?
- Clear browser cache: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
- Check browser console for errors (F12)

### Wrong container name?
Edit the script or set manually:
```bash
export KEYCLOAK_CONTAINER="your-container-name"
./deploy-keycloak-theme.sh
```

## Key Files

| File | Purpose |
|------|---------|
| `uc-1-pro/theme.properties` | Main theme config |
| `uc-1-pro/login/login.ftl` | Login page template |
| `uc-1-pro/login/resources/css/login.css` | Custom styles |
| `uc-1-pro/login/resources/img/` | Logo directory |

## Color Scheme

```
Purple Primary:  #8B5CF6
Gold Accent:     #F59E0B
Background:      Gradient from #3B0764 to #6D28D9
```

## Support

- Full docs: See `README.md`
- Installation guide: See `INSTALLATION.md`
- Deployment summary: See `DEPLOYMENT-SUMMARY.md`
- Issues: https://github.com/Unicorn-Commander/UC-1-Pro/issues

---

**Need help?** Email: support@magicunicorn.tech
