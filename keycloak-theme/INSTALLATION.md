# Quick Installation Guide - UC-1 Pro Keycloak Theme

## Step 1: Verify Theme Files

Ensure all files are in place:
```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center/keycloak-theme
tree uc1-pro
```

Expected structure:
```
uc1-pro/
├── theme.properties
└── login/
    ├── login.ftl
    └── resources/
        ├── css/
        │   └── login.css
        └── img/
            └── colonel-logo.png (you need to add this)
```

## Step 2: Add The Colonel Logo

Copy your logo to:
```bash
cp /path/to/colonel-logo.png uc1-pro/login/resources/img/colonel-logo.png
```

## Step 3: Deploy to Keycloak

### Method A: Docker Volume Mount (Easiest)

Add to your `docker-compose.yml`:

```yaml
services:
  keycloak:
    image: quay.io/keycloak/keycloak:25.0
    container_name: keycloak
    volumes:
      - /home/muut/Production/UC-1-Pro/services/ops-center/keycloak-theme/uc1-pro:/opt/keycloak/themes/uc1-pro:ro
    environment:
      KC_HOSTNAME: auth.your-domain.com
      KC_HOSTNAME_STRICT: false
      KC_HTTP_ENABLED: true
      KC_PROXY: edge
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://keycloak-db:5432/keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD: ${KEYCLOAK_DB_PASSWORD}
    command:
      - start
      - --optimized
    networks:
      - unicorn-network
      - web
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.keycloak.rule=Host(`auth.your-domain.com`)"
      - "traefik.http.routers.keycloak.entrypoints=websecure"
      - "traefik.http.routers.keycloak.tls=true"
      - "traefik.http.routers.keycloak.tls.certresolver=letsencrypt"
      - "traefik.http.services.keycloak.loadbalancer.server.port=8080"
```

Restart Keycloak:
```bash
docker compose up -d keycloak
```

### Method B: Build Custom Image

Create `Dockerfile.keycloak`:

```dockerfile
FROM quay.io/keycloak/keycloak:25.0

# Copy custom theme
COPY keycloak-theme/uc1-pro /opt/keycloak/themes/uc1-pro

# Set ownership
USER root
RUN chown -R keycloak:keycloak /opt/keycloak/themes/uc1-pro
USER keycloak

# Build optimized
RUN /opt/keycloak/bin/kc.sh build
```

Build and deploy:
```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center
docker build -f Dockerfile.keycloak -t keycloak-uc1pro:latest .
```

Update docker-compose.yml to use custom image:
```yaml
services:
  keycloak:
    image: keycloak-uc1pro:latest
    # ... rest of configuration
```

## Step 4: Activate Theme in Keycloak

1. Access Keycloak Admin Console:
   ```
   https://auth.your-domain.com/admin
   ```

2. Login with admin credentials

3. Select your realm (or create new one)

4. Navigate to: **Realm Settings** → **Themes** tab

5. Set themes:
   - **Login theme**: `uc1-pro`
   - Click **Save**

6. Test the login page:
   ```
   https://auth.your-domain.com/realms/your-realm/account
   ```

## Step 5: Verify Installation

Check theme is working:

1. **Visual Check**: Visit login page and verify:
   - Purple gradient background appears
   - Glassmorphic card with blur effect
   - Logo displays with glow
   - "Welcome to Unicorn Commander" title
   - Purple/gold styling

2. **Console Check**: Open browser DevTools (F12):
   - No 404 errors for CSS or images
   - No JavaScript errors
   - CSS animations working

3. **Container Check**:
   ```bash
   # Check theme files exist in container
   docker exec keycloak ls -la /opt/keycloak/themes/uc1-pro

   # Check Keycloak logs
   docker logs keycloak | grep -i theme
   ```

## Troubleshooting

### Theme not appearing in dropdown

1. Check file permissions:
   ```bash
   chmod -R 755 uc1-pro
   ```

2. Verify theme structure:
   ```bash
   ls -la uc1-pro/theme.properties
   ```

3. Restart Keycloak:
   ```bash
   docker restart keycloak
   ```

### Logo not showing

1. Verify logo exists:
   ```bash
   ls -la uc1-pro/login/resources/img/colonel-logo.png
   ```

2. Check browser console for 404 errors

3. Try different image format (PNG, JPG, SVG)

### Styles not applying

1. Clear browser cache (Ctrl+Shift+R)

2. Check CSS file loaded:
   - Open DevTools → Network tab
   - Filter by "CSS"
   - Verify login.css loads with 200 status

3. Verify theme.properties:
   ```bash
   cat uc1-pro/theme.properties
   ```

### Container permission issues

Fix ownership:
```bash
docker exec -u root keycloak chown -R keycloak:keycloak /opt/keycloak/themes/uc1-pro
docker restart keycloak
```

## Next Steps

1. **Configure OAuth/OIDC clients** for your applications
2. **Set up user federation** (LDAP, Active Directory)
3. **Customize email templates** with UC-1 Pro branding
4. **Enable two-factor authentication**
5. **Configure realm roles and permissions**

## Testing Checklist

- [ ] Theme appears in Keycloak admin dropdown
- [ ] Login page displays with purple gradient
- [ ] Glassmorphic card effect visible
- [ ] Logo displays with glow effect
- [ ] Form fields styled correctly
- [ ] Login button has gradient and hover effects
- [ ] Error messages display with proper styling
- [ ] Responsive design works on mobile
- [ ] No console errors
- [ ] Authentication flow works end-to-end

## Support

Issues or questions:
- GitHub: https://github.com/Unicorn-Commander/UC-1-Pro/issues
- Email: support@magicunicorn.tech

## Quick Commands Reference

```bash
# View Keycloak logs
docker logs keycloak -f

# Restart Keycloak
docker restart keycloak

# Check theme files in container
docker exec keycloak ls -la /opt/keycloak/themes/uc1-pro

# Access Keycloak bash
docker exec -it keycloak bash

# Test login endpoint
curl -I https://auth.your-domain.com/realms/master/account

# Check Keycloak health
curl https://auth.your-domain.com/health
```
