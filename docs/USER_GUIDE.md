# Ops-Center User Guide

**Version**: 2.1.1
**Last Updated**: October 30, 2025
**Status**: Production Ready

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Dashboard Overview](#dashboard-overview)
4. [User Management vs Local Users](#user-management-vs-local-users)
5. [Services Management](#services-management)
6. [Hardware Monitoring](#hardware-monitoring)
7. [Analytics & Reports](#analytics--reports)
8. [Settings & Configuration](#settings--configuration)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

---

## Introduction

Ops-Center is the **centralized management hub** for the UC-Cloud ecosystem. It provides a comprehensive administrative interface for managing users, billing, services, organizations, and LLM infrastructure.

### Think of it like:
- **Ops-Center** = AWS Console (infrastructure management)
- **Brigade** = GitHub (agent repository)
- **Open-WebUI** = VS Code (where you actually work)
- **Center-Deep** = Google Search (research tool)

### Key Features:
- User management (Keycloak SSO users)
- Billing & subscription management (Lago integration)
- Service monitoring and control (Docker containers)
- Hardware monitoring (GPU, CPU, memory, storage)
- LLM management (models, providers, usage tracking)
- Organization management (multi-tenancy)

---

## Getting Started

### Logging In

1. Navigate to **https://unicorncommander.ai**
2. You'll be redirected to Keycloak SSO login
3. Choose your authentication method:
   - **Email/Password** (manual registration)
   - **Google** (SSO)
   - **GitHub** (SSO)
   - **Microsoft** (SSO)

### First-Time Setup

After logging in for the first time:

1. **Complete Your Profile**:
   - Go to **Account → Profile & Preferences**
   - Add your name, profile picture, and contact information
   - Set your timezone and language preferences

2. **Review Your Subscription**:
   - Go to **My Subscription → Current Plan**
   - Check your subscription tier (Trial, Starter, Professional, Enterprise)
   - Review your usage limits and billing information

3. **Set Up Notifications**:
   - Go to **Account → Notification Preferences**
   - Choose which events you want to be notified about
   - Configure email delivery settings

4. **Explore the Dashboard**:
   - Familiarize yourself with the main sections
   - Check out the quick action tiles
   - Review the service status cards

---

## Dashboard Overview

The main dashboard provides an at-a-glance view of your system health and activity.

### Dashboard Sections:

#### 1. Quick Actions
- **Start/Stop Services**: Control running services
- **View Analytics**: Jump to analytics dashboards
- **Manage Users**: Access user management
- **View Logs**: Check system logs

#### 2. Service Status Cards
- Shows all running services (Docker containers)
- Color-coded status indicators:
  - **Green**: Healthy/Running
  - **Blue**: Starting/Restarting
  - **Yellow**: Warning/Degraded
  - **Red**: Stopped/Error
  - **Gray**: Stopped (intentional)

#### 3. Resource Overview
- **CPU Usage**: Current and historical CPU utilization
- **Memory Usage**: RAM consumption
- **GPU Usage**: GPU utilization (if available)
- **Storage**: Disk space usage

#### 4. Recent Activity
- Latest user logins
- Service state changes
- System events
- Billing transactions

---

## User Management vs Local Users

**This is the #1 source of confusion** - let's clarify the difference:

### User Management (Application Users)
**Location**: `/admin/system/users`

**What it shows**:
- Application users who log in via Keycloak SSO
- Users authenticated with Google, GitHub, Microsoft, or email/password
- Users with subscriptions, API keys, and organization memberships

**What you can do**:
- Invite new users
- Assign roles (admin, moderator, developer, analyst, viewer)
- Manage subscriptions and billing
- View user activity and sessions
- Issue API keys for programmatic access

**When to use**:
- Adding team members to your organization
- Controlling who can access the application
- Managing billing and subscriptions
- Reviewing user activity

### Local Users (Container System Users)
**Location**: `/admin/system/local-users` or `/admin/infrastructure/local-users`

**What it shows**:
- Linux system users inside the Docker container (ops-center-direct)
- Users like "nobody", "root", "www-data", "muut"
- System accounts used for process isolation and security

**What you can do**:
- Create Linux users for SSH access
- Grant sudo permissions
- Manage SSH keys for remote access
- Control system-level access

**When to use**:
- Setting up SSH access to the container
- Debugging infrastructure issues
- Managing system-level permissions
- Configuring service accounts

**Important**: These are **NOT** the same as application users. If you want to add a user who can log into the application, use **User Management**, not **Local Users**.

---

## Services Management

**Location**: `/admin/services`

### Overview

The Services page shows all Docker containers running in the UC-Cloud ecosystem.

**What you can do**:
- **View service status**: See which services are running, stopped, or have errors
- **Control services**: Start, stop, or restart containers
- **Monitor resources**: Check CPU, memory, and GPU usage per service
- **View logs**: Access real-time logs for troubleshooting
- **Access service UIs**: Click on service cards to open their web interfaces

### Service Types:

#### Core Services:
- **ops-center-direct**: This admin dashboard
- **uchub-keycloak**: Authentication (SSO)
- **unicorn-postgresql**: Database
- **unicorn-redis**: Cache and sessions

#### Application Services:
- **Open-WebUI**: Chat interface for LLMs
- **Center-Deep**: AI-powered metasearch engine
- **Unicorn Brigade**: Agent infrastructure platform

#### Infrastructure Services:
- **Traefik**: Reverse proxy with SSL/TLS
- **Grafana**: Monitoring dashboards
- **Prometheus**: Metrics collection

#### Optional Services:
- **ComfyUI**: Image generation
- **Portainer**: Container management
- **n8n**: Workflow automation

### Service Actions:

#### Start Service
Starts a stopped service. The service will go through initialization and health checks.

#### Stop Service
Gracefully stops a running service. Ongoing requests will complete before shutdown.

#### Restart Service
Stops and then starts the service. Useful for applying configuration changes.

#### View Logs
Opens a real-time log viewer showing the last 100 lines and streaming new logs.

#### Access UI
Opens the service's web interface in a new tab (if applicable).

**Help Tooltip**: The Services page includes contextual help explaining:
- What Docker containers are
- The difference between service types
- Resource usage indicators
- When to start/stop/restart services

---

## Hardware Monitoring

**Location**: `/admin/infrastructure/hardware`

### What This Page Shows

The Hardware Management page displays physical and virtual hardware resources detected by the system.

**Resources monitored**:
- **CPU**: Utilization, temperature, frequency
- **Memory (RAM)**: Usage, available, swap
- **GPU**: Utilization, memory, temperature (NVIDIA, AMD, Intel)
- **Storage**: Disk usage, I/O rates, free space
- **Network**: Bandwidth usage, packet rates

### GPU Monitoring

If you have a GPU (NVIDIA RTX, AMD, or Intel iGPU):
- **GPU Utilization**: Percentage of compute being used
- **GPU Memory**: VRAM usage (total, used, free)
- **GPU Temperature**: Current temp with warning thresholds
- **GPU Power**: Power consumption in watts

**Help Tooltip**: Hardware Management includes help explaining:
- What "physical hardware" means (vs virtual resources)
- How to interpret utilization percentages
- Warning thresholds for temperature and usage
- When to be concerned about resource usage

---

## Analytics & Reports

**Location**: `/admin/analytics`

### Available Analytics:

#### 1. Analytics Dashboard
**What it shows**:
- User growth trends
- API usage over time
- Service availability metrics
- Billing revenue charts

**Filters**:
- Date range selection
- Group by: Day, Week, Month
- Filter by service or user

#### 2. LLM Analytics
**Location**: `/admin/llm/usage`

**What it shows**:
- LLM API calls per model
- Token usage and costs
- Response times and latency
- Error rates

#### 3. User Analytics
**Location**: `/admin/system/analytics`

**What it shows**:
- User registrations over time
- Active users (daily, weekly, monthly)
- User retention rates
- Authentication methods used

#### 4. Billing Analytics
**Location**: `/admin/system/billing`

**What it shows**:
- Revenue trends
- Subscription distribution by tier
- Churn rate
- Average revenue per user (ARPU)

#### 5. Usage Metrics
**Location**: `/admin/system/usage-metrics`

**What it shows**:
- API calls per endpoint
- Bandwidth usage
- Storage consumption
- Credit usage (for BYOK users)

---

## Settings & Configuration

### Account Settings

**Location**: `/admin/account/*`

#### Profile & Preferences
- Update your personal information
- Change your email or username
- Set timezone and language
- Upload profile picture

#### Security & Sessions
- Change password
- Enable two-factor authentication (2FA)
- View active sessions
- Revoke sessions

#### API Keys (BYOK)
- Generate API keys for programmatic access
- Bring Your Own Key (BYOK) for LLM providers
- View API key usage statistics
- Revoke compromised keys

#### Notification Preferences
- Configure email notifications
- Set webhook endpoints for events
- Choose notification frequency
- Customize event filters

### Subscription Management

**Location**: `/admin/subscription/*`

#### Current Plan
- View your subscription tier
- See included features
- Check renewal date
- Upgrade or downgrade

#### Usage & Limits
- API call usage vs limits
- Storage usage
- Credit balance (BYOK)
- Overage charges (if applicable)

#### Billing History
- View past invoices
- Download PDF receipts
- See payment history
- Track credits and refunds

#### Payment Methods
- Add/remove credit cards
- Set default payment method
- Update billing address
- Enable auto-pay

### Organization Settings (Admins Only)

**Location**: `/admin/org/*`

#### Team Members
- Invite team members via email
- Assign roles and permissions
- View member activity
- Remove members

#### Roles & Permissions
- Create custom roles
- Define permission sets
- Assign roles to users
- View role hierarchy

#### Organization Settings
- Update organization name and details
- Set organization-wide policies
- Configure SSO settings
- Manage API access

#### Organization Billing (Owners Only)
- View organization invoices
- Manage payment methods
- Allocate budgets to teams
- Export billing reports

### Platform Settings (Platform Admins Only)

**Location**: `/admin/platform/*`

#### Email Settings
- Configure email provider (Microsoft 365, SMTP)
- Test email delivery
- Manage email templates
- View email delivery logs

#### Platform Settings
- System-wide configuration
- Feature flags
- Rate limiting
- Security policies

#### System Provider Keys
- Configure system-level API keys
- OpenAI, Anthropic, Cohere keys
- LiteLLM proxy configuration
- Key rotation policies

---

## Troubleshooting

### Common Issues

#### 1. "401 Unauthorized" Errors

**Symptoms**: API calls fail with 401 status

**Solutions**:
- Log out and log back in to refresh your session
- Check if your session has expired (default: 24 hours)
- Verify you have the required role for the action
- Clear browser cache and cookies

#### 2. Services Won't Start

**Symptoms**: Service stuck in "Starting" state

**Solutions**:
- Check Docker logs for error messages
- Verify sufficient system resources (CPU, RAM, disk)
- Ensure required ports are not in use
- Restart Docker daemon if needed

#### 3. Metrics Showing 0

**Symptoms**: User metrics cards show 0 even though users exist

**Solutions**:
- Keycloak users may not have custom attributes populated
- Run attribute population script:
  ```bash
  docker exec ops-center-direct python3 /app/scripts/quick_populate_users.py
  ```
- Configure Keycloak User Profile (see admin guide)

#### 4. GPU Not Detected

**Symptoms**: Hardware page shows no GPU

**Solutions**:
- Verify GPU is physically installed
- Check NVIDIA/AMD drivers are installed
- Ensure Docker has GPU access:
  ```bash
  docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
  ```
- Restart container with GPU passthrough

#### 5. Frontend Not Loading

**Symptoms**: White screen or React errors

**Solutions**:
- Check browser console for JavaScript errors
- Hard reload: Ctrl + Shift + R
- Clear browser cache completely
- Verify frontend files exist in public/assets/
- Check container logs for errors

---

## FAQ

### General Questions

**Q: What is Ops-Center?**
A: Ops-Center is the centralized admin dashboard for UC-Cloud. It manages users, billing, services, and infrastructure.

**Q: Do I need to be a system admin to use Ops-Center?**
A: No. Different sections are available based on your role:
- **All users**: Account settings, subscription management
- **Org admins**: Organization management, team settings
- **Platform admins**: System administration, infrastructure management

**Q: Is my data secure?**
A: Yes. Ops-Center uses:
- Keycloak SSO with industry-standard authentication
- Encrypted API keys (bcrypt hashing)
- HTTPS/SSL for all connections
- Role-based access control (RBAC)
- Audit logging for compliance

### User Management

**Q: How do I add a new team member?**
A: Go to **User Management** (`/admin/system/users`) and click "Invite User". Enter their email and assign a role.

**Q: What's the difference between User Management and Local Users?**
A: **User Management** shows application users (Keycloak SSO). **Local Users** shows Linux system users inside the Docker container. See [User Management vs Local Users](#user-management-vs-local-users) for details.

**Q: Can I bulk import users?**
A: Yes. Go to User Management, click the bulk actions menu, and select "Import from CSV". Follow the template format.

**Q: How do I reset a user's password?**
A: Users must reset their own passwords via the Keycloak login page. Admins cannot see or reset passwords directly (by design for security).

### Billing & Subscriptions

**Q: What subscription tiers are available?**
A:
- **Trial**: $1/week (7 days)
- **Starter**: $19/month (1,000 API calls)
- **Professional**: $49/month (10,000 API calls) ⭐ Most Popular
- **Enterprise**: $99/month (Unlimited API calls)

**Q: How do I upgrade my plan?**
A: Go to **My Subscription → Current Plan** and click "Upgrade". Choose your new tier and complete payment.

**Q: What is BYOK (Bring Your Own Key)?**
A: BYOK allows you to use your own API keys for LLM providers (OpenAI, Anthropic, etc.) instead of consuming platform credits. Available on Professional and Enterprise tiers.

**Q: How do credits work?**
A: Credits are usage quotas. Each API call consumes credits. When you run out, you either upgrade or purchase more credits. BYOK users aren't charged credits when using their own keys.

### Services & Infrastructure

**Q: Can I deploy my own services?**
A: Yes, but you'll need to modify Docker Compose files. This requires system admin access and Docker knowledge.

**Q: How do I access service logs?**
A: Go to **Services**, find your service, and click the "View Logs" button. Logs stream in real-time.

**Q: Why can't I start a service?**
A: Common reasons:
- Insufficient resources (RAM, CPU)
- Port conflict (port already in use)
- Missing dependencies
- Configuration error (check logs)

**Q: What is Traefik?**
A: Traefik is a reverse proxy that handles:
- SSL/TLS certificates (Let's Encrypt)
- Routing traffic to services
- Load balancing
- Automatic service discovery

### LLM & AI

**Q: What LLM models are available?**
A: 100+ models via OpenRouter, including:
- OpenAI: GPT-4, GPT-3.5
- Anthropic: Claude 3 (Opus, Sonnet, Haiku)
- Google: Gemini Pro
- Meta: Llama 2, Llama 3
- Mistral: Mistral 7B, Mixtral 8x7B

**Q: How do I add a custom model?**
A: Go to **LLM Management** → **LLM Providers** and configure your provider. Add your API key and select models.

**Q: What is the LLM Hub?**
A: LLM Hub is the centralized interface for managing:
- Model catalog (browse available models)
- Provider configuration (API keys, endpoints)
- Usage tracking (costs, token counts)
- Routing logic (fallbacks, load balancing)

**Q: Can I use my own GPU for inference?**
A: Yes, but this requires custom setup. You'll need to:
1. Configure vLLM with your GPU
2. Update Docker Compose GPU passthrough
3. Ensure CUDA drivers are compatible

### Organizations

**Q: What is an organization?**
A: Organizations allow multi-tenancy:
- Multiple users under one account
- Shared resources and billing
- Centralized administration
- Team collaboration

**Q: How do I create an organization?**
A: Platform admins can create organizations via **Organizations** → **Create Organization**.

**Q: Can a user belong to multiple organizations?**
A: Yes. Users can be members of multiple organizations with different roles in each.

**Q: Who can manage an organization?**
A:
- **Owner**: Full control (billing, team, settings)
- **Admin**: Team and settings (no billing)
- **Member**: Access organization resources

### Troubleshooting

**Q: Why am I seeing "Failed to load data" errors?**
A: This usually means:
1. Backend is down (check Services page)
2. Session expired (log out and log back in)
3. Network issue (check browser console)
4. API endpoint error (check container logs)

**Q: How do I report a bug?**
A: Create an issue on GitHub: https://github.com/Unicorn-Commander/UC-Cloud/issues

**Q: Where can I find logs?**
A:
- **Application logs**: Services page → View Logs button
- **Container logs**: `docker logs ops-center-direct`
- **Audit logs**: Database `audit_logs` table

**Q: How do I contact support?**
A:
- **Community**: GitHub Discussions
- **Email**: support@unicorncommander.com (Enterprise tier)
- **Documentation**: https://unicorncommander.com/docs

---

## Screenshots

### Dashboard
_Main dashboard showing service status, resource usage, and quick actions_

### User Management
_User list with advanced filtering, bulk operations, and role assignment_

### Local Users vs User Management
_Side-by-side comparison showing the difference between container users and application users_

### Services Management
_Service cards with status indicators, resource usage, and control actions_

### Hardware Monitoring
_Real-time GPU, CPU, memory, and storage metrics with historical charts_

### Analytics Dashboard
_Charts showing user growth, API usage, and revenue trends_

### Subscription Management
_Current plan details, usage limits, and billing history_

---

## Additional Resources

- **UC-Cloud Main Docs**: `/opt/uc-cloud/CLAUDE.md`
- **Brigade Integration**: `/opt/uc-cloud/Unicorn-Brigade/UC-CLOUD-INTEGRATION.md`
- **Lago Billing Docs**: `/home/deploy/Production/UC-1-Pro/docs/BILLING_ARCHITECTURE_FINAL.md`
- **API Reference**: `/admin/platform/api-docs`
- **Keycloak Docs**: https://www.keycloak.org/documentation

---

## Changelog

### Version 2.1.1 (October 30, 2025)
- Added comprehensive user guide
- Created USER_GUIDE.md with screenshots and FAQs
- Enhanced LocalUserManagement with info banner and help tooltips
- Improved HelpTooltip component with theme support
- Added contextual help to confusing sections

### Version 2.1.0 (October 29, 2025)
- Fixed credit system authentication
- Removed misleading dollar signs from credit display
- Created organization "Magic Unicorn" with 10,000 credits
- Verified OpenRouter API key integration

### Version 2.0.0 (October 15, 2025)
- Completed Phase 1: User Management & Billing Dashboard
- Added bulk operations for user management
- Enhanced role management with visual permission matrix
- Integrated Lago billing system
- Added API key management
- Created user detail page with 6 tabs

---

**Need help?** Check the [FAQ](#faq) or contact support at support@unicorncommander.com

**Found a bug?** Report it on [GitHub Issues](https://github.com/Unicorn-Commander/UC-Cloud/issues)

**Want to contribute?** See our [Contributing Guide](https://github.com/Unicorn-Commander/UC-Cloud/blob/main/CONTRIBUTING.md)
