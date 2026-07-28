# Quick Start Guide

Get up and running with the UC-1 Pro Admin Dashboard in minutes. This guide will walk you through your first login and essential tasks.

## Prerequisites

- UC-1 Pro system is installed and running
- Admin Dashboard service is active (port 8084)
- You have admin credentials

## Step 1: Access the Dashboard

1. Open your web browser
2. Navigate to your UC-1 Pro system:
   ```
   http://[your-uc1-pro-ip]:8084
   ```
   - For local access: `http://localhost:8084`
   - For network access: `http://192.168.1.x:8084` (replace with your IP)

## Step 2: Login

![Login Screen](../assets/images/login-screen.png)

1. You'll be presented with the login screen
2. Enter the default credentials:
   - **Username**: `ucladmin`
   - **Password**: `MagicUnicorn!8-)`
3. Click **Login**

!!! warning "Change Default Password"
    For security, change the default password immediately after first login via [Security & Access](../features/security.md).

## Step 3: Dashboard Overview

After successful login, you'll see the main dashboard with:

### Navigation Sidebar
- **Dashboard**: System overview and quick actions
- **AI Model Management**: LLM model controls
- **Services**: Container and service management
- **System Monitor**: Real-time performance metrics
- **Network & WiFi**: Network configuration
- **Storage & Backup**: Data management
- **Extensions**: Add-on marketplace
- **Logs & Diagnostics**: System logs
- **Security & Access**: User management
- **Settings**: System configuration

### Main Content Area
The dashboard shows:
- System health status
- Active services overview
- Resource utilization charts
- Recent activity feed
- Quick action buttons

## Step 4: Essential First Tasks

### Check System Health
1. Review the system status indicators
2. Ensure all critical services are running (green status)
3. Check GPU utilization and temperature

### Verify AI Models
1. Go to **AI Model Management**
2. Confirm your models are loaded and ready
3. Check model performance metrics

### Review Services
1. Navigate to **Services**
2. Verify all containers are healthy
3. Check service logs for any issues

### Configure Network (if needed)
1. Go to **Network & WiFi**
2. Verify network connectivity
3. Configure WiFi if using wireless

## Step 5: Explore Features

### Getting Help
- Press `?` anywhere in the interface for contextual help
- Click the **Help & Documentation** button in the sidebar
- Hover over elements for tooltips and guidance

### Keyboard Shortcuts
- `?` - Toggle help panel
- `Ctrl+/` - Search (when available)
- `Esc` - Close modals and panels

### Theme Switching
- Use the theme switcher at the bottom of the sidebar
- Available themes: Light, Dark, Unicorn (purple gradient)

## Common First-Time Tasks

### 1. Change Admin Password
1. Go to **Security & Access**
2. Click on your user profile
3. Update password and save

### 2. Add Additional Users
1. In **Security & Access**
2. Click **Add User**
3. Fill in user details and permissions

### 3. Configure Backups
1. Navigate to **Storage & Backup**
2. Set up automated backup schedule
3. Test backup functionality

### 4. Install Extensions
1. Visit **Extensions** marketplace
2. Browse available add-ons
3. Install desired extensions

### 5. Monitor System Performance
1. Check **System Monitor** regularly
2. Set up alerts for critical thresholds
3. Review performance trends

## Troubleshooting First Login

### Can't Access Dashboard
- Verify UC-1 Pro services are running
- Check network connectivity
- Ensure port 8084 is not blocked by firewall

### Login Fails
- Verify username/password (case sensitive)
- Check for caps lock
- Try refreshing the page

### Page Loads but Shows Errors
- Check browser console for JavaScript errors
- Try a different browser
- Clear browser cache and cookies

### Performance Issues
- Check system resources on host
- Verify GPU is not overloaded
- Review service logs for errors

## Next Steps

Now that you're logged in and familiar with the interface:

1. **Read the [UI Overview](ui-overview.md)** for detailed interface guidance
2. **Explore [Feature Documentation](../features/dashboard.md)** for specific functionality
3. **Set up [User Management](../admin/user-management.md)** for team access
4. **Configure [System Monitoring](../features/system-monitoring.md)** alerts

## Need Help?

- **Documentation**: Comprehensive guides for all features
- **Tooltips**: Hover over interface elements for quick help
- **Help Panel**: Press `?` for contextual assistance
- **Logs**: Check system logs for detailed error information

---

*Ready to dive deeper? Continue with the [Authentication Guide](authentication.md) or jump to [Feature Documentation](../features/dashboard.md).*