# UC-1 Pro Keycloak Theme

Custom Keycloak theme for UC-1 Pro Operations Center with purple and gold branding.

## Quick Start

Deploy the theme to Keycloak:

```bash
cd /home/deploy/Production/UC-1-Pro/services/ops-center
./deploy-keycloak-theme.sh
```

## Features

- **Purple gradient background** with animated overlay
- **Glassmorphic login card** with backdrop blur effect
- **The Colonel logo** with glowing effect
- **Responsive design** for all screen sizes
- **Accessibility support** (WCAG 2.1 compliant)
- **Modern animations** and transitions
- **Purple/gold color scheme** matching UC-1 Pro branding

## Theme Structure

```
uc-1-pro/
├── theme.properties              # Main theme configuration
└── login/                        # Login page customization
    ├── theme.properties          # Login-specific config
    └── resources/
        ├── css/
        │   └── login.css        # Custom login styles
        ├── img/                 # Logo and images
        └── js/                  # Custom JavaScript
```

## Installation

### Automated Deployment (Recommended)

Use the provided deployment script:

```bash
cd /home/deploy/Production/UC-1-Pro/services/ops-center
./deploy-keycloak-theme.sh
```

The script will:
1. Validate theme structure
2. Backup existing theme (if any)
3. Copy theme to uchub-keycloak container
4. Set proper permissions
5. Restart Keycloak
6. Verify installation

### Option 1: Docker Volume Mount (For Development)

1. Add volume mount to your Keycloak container in `docker-compose.yml`:

```yaml
services:
  keycloak:
    image: quay.io/keycloak/keycloak:latest
    volumes:
      - ./keycloak-theme/uc1-pro:/opt/keycloak/themes/uc1-pro
    environment:
      KC_HOSTNAME: auth.unicorncommander.ai
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: your-admin-password
    command:
      - start
      - --hostname-strict=false
```

2. Restart Keycloak:
```bash
docker restart keycloak
```

### Option 2: Build into Docker Image (Recommended for Production)

Create a custom Dockerfile:

```dockerfile
FROM quay.io/keycloak/keycloak:latest

# Copy custom theme
COPY keycloak-theme/uc1-pro /opt/keycloak/themes/uc1-pro

# Set permissions
USER root
RUN chown -R keycloak:keycloak /opt/keycloak/themes/uc1-pro
USER keycloak

# Build optimized version
RUN /opt/keycloak/bin/kc.sh build
```

Build and run:
```bash
docker build -t keycloak-uc1pro .
docker run -p 8080:8080 keycloak-uc1pro
```

### Option 3: JAR Archive (Traditional Method)

1. Create JAR archive:
```bash
cd keycloak-theme
jar -cvf uc1-pro.jar -C uc1-pro .
```

2. Copy to Keycloak deployments:
```bash
cp uc1-pro.jar /opt/keycloak/providers/
```

3. Restart Keycloak

## Activation

1. Log in to Keycloak Admin Console: `https://auth.unicorncommander.ai/admin`

2. Navigate to: **Realm Settings** → **Themes** tab

3. Set the following themes:
   - **Login Theme**: `uc1-pro`
   - **Account Theme**: `uc1-pro` (if account theme is added)
   - **Email Theme**: `keycloak` (or create custom email theme)

4. Click **Save**

5. Test by visiting login page: `https://auth.unicorncommander.ai/realms/your-realm/account`

## Adding The Colonel Logo

1. Obtain the Colonel logo image (PNG with transparent background recommended)

2. Copy to theme directory:
```bash
cp colonel-logo.png /home/deploy/Production/UC-1-Pro/services/ops-center/keycloak-theme/uc1-pro/login/resources/img/
```

3. If using Docker volume mount, the change will be reflected immediately

4. If using JAR/Docker image, rebuild and redeploy

## Customization

### Colors

Edit `/login/resources/css/login.css` and modify the CSS variables:

```css
:root {
    --uc1-purple-primary: #8B5CF6;    /* Main purple */
    --uc1-purple-light: #A78BFA;      /* Light purple */
    --uc1-purple-dark: #6D28D9;       /* Dark purple */
    --uc1-gold-primary: #F59E0B;      /* Gold accent */
    --uc1-gold-light: #FBBF24;        /* Light gold */
}
```

### Background

Replace the gradient in `.uc1-background`:

```css
.uc1-background {
    background: radial-gradient(
        ellipse at top,
        #YourColor1 0%,
        #YourColor2 50%,
        #YourColor3 100%
    );
}
```

### Text Content

Edit `/login/login.ftl` and modify:

```html
<h1 class="uc1-title">Your Custom Title</h1>
<p class="uc1-subtitle">Your Custom Subtitle</p>
```

### Logo Size

Edit CSS to adjust logo size:

```css
.uc1-logo {
    max-width: 120px;  /* Adjust as needed */
}
```

## Theme Structure

```
uc1-pro/
├── theme.properties           # Theme configuration
├── login/
│   ├── login.ftl             # Login page template
│   ├── resources/
│   │   ├── css/
│   │   │   └── login.css     # Custom styles
│   │   ├── img/
│   │   │   └── colonel-logo.png
│   │   └── js/               # Optional JavaScript
│   └── messages/             # Optional translations
└── README.md                 # This file
```

## Supported Keycloak Versions

- Keycloak 22.x
- Keycloak 23.x
- Keycloak 24.x
- Keycloak 25.x (latest)

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Opera 76+

## Accessibility Features

- WCAG 2.1 Level AA compliant
- Keyboard navigation support
- Screen reader friendly
- High contrast mode support
- Reduced motion support
- Proper ARIA labels

## Troubleshooting

### Theme not showing up

1. Check theme is properly copied to Keycloak themes directory
2. Verify file permissions: `chown -R keycloak:keycloak /opt/keycloak/themes/uc1-pro`
3. Clear browser cache
4. Check Keycloak logs: `docker logs keycloak`

### Logo not displaying

1. Verify image exists at: `/login/resources/img/colonel-logo.png`
2. Check image format (PNG, JPG, SVG supported)
3. Verify file permissions
4. Check browser console for 404 errors

### Styles not applying

1. Clear browser cache (Ctrl+Shift+R / Cmd+Shift+R)
2. Check `theme.properties` has correct CSS path
3. Verify CSS file exists and has no syntax errors
4. Check browser console for CSS errors

### OAuth/OIDC issues

1. Ensure redirect URIs are properly configured in Keycloak
2. Check client settings in Keycloak admin console
3. Verify realm settings match your application

## Advanced Customization

### Adding Custom Pages

Add additional FreeMarker templates to `/login/`:

- `register.ftl` - Registration page
- `login-reset-password.ftl` - Password reset
- `login-update-password.ftl` - Password update
- `error.ftl` - Error page
- `info.ftl` - Info page

### Internationalization

Create translations in `/login/messages/`:

- `messages_en.properties` - English
- `messages_es.properties` - Spanish
- `messages_fr.properties` - French

Example:
```properties
loginTitle=Welcome to Unicorn Commander
doLogIn=Sign In
username=Username
password=Password
```

### Custom JavaScript

Add interactive features in `/login/resources/js/`:

```javascript
// login.js
document.addEventListener('DOMContentLoaded', function() {
    // Add loading state to submit button
    const form = document.getElementById('kc-form-login');
    const submitBtn = document.getElementById('kc-login');

    form.addEventListener('submit', function() {
        submitBtn.classList.add('loading');
    });
});
```

Reference in `theme.properties`:
```properties
scripts=js/login.js
```

## Support

For issues, questions, or contributions:

- GitHub: https://github.com/Unicorn-Commander/UC-1-Pro
- Email: support@magicunicorn.tech
- Documentation: https://unicorncommander.com/docs

## License

MIT License - Copyright 2025 Magic Unicorn Unconventional Technology & Stuff Inc

## Credits

- Designed for UC-1 Pro Operations Center
- Built with Keycloak theming framework
- Inspired by modern glassmorphic design principles
