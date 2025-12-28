# Ops-Center - Open Source Operations & Management Dashboard

**Version**: 2.4.0
**License**: MIT
**Last Updated**: November 19, 2025

---

## Project Overview

Ops-Center is a comprehensive **operations and management hub** designed for cloud infrastructure, AI/LLM platforms, and SaaS applications. It provides centralized user management, billing integration, service orchestration, and LLM API routing.

### What is Ops-Center?

Think of Ops-Center as your **infrastructure control panel** - similar to AWS Console or Heroku Dashboard, but purpose-built for AI/LLM platforms with built-in billing, usage tracking, and multi-tenancy.

**Key Capabilities**:
- **User Management**: Advanced user administration with roles, permissions, bulk operations
- **Billing Integration**: Lago + Stripe integration with subscription tiers and usage tracking
- **LLM API Proxy**: LiteLLM-based routing with credit system and usage metering
- **Multi-Tenancy**: Organizations, teams, and tier-based access control
- **Service Orchestration**: Manage and monitor multiple integrated services
- **SSO Integration**: Keycloak OIDC/OAuth2 authentication

---

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL 14+
- **Cache**: Redis 7+
- **Authentication**: Keycloak SSO (OIDC/OAuth2)
- **Billing**: Lago + Stripe
- **LLM Proxy**: LiteLLM

### Frontend
- **Framework**: React 18 + Vite
- **UI Library**: Material-UI (MUI v5)
- **Routing**: React Router v6
- **State Management**: React Context API
- **Charts**: react-chartjs-2 + Chart.js
- **HTTP Client**: Axios

### Infrastructure
- **Container**: Docker + Docker Compose
- **Reverse Proxy**: Traefik or Nginx (configurable)
- **Networks**: Internal service mesh

---

## Architecture

### Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Ops-Center                               │
│         (Frontend + Backend API)                             │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────▼───────┐   ┌──────▼──────┐
            │   Backend API  │   │  Frontend    │
            │  (FastAPI)     │   │  (React SPA) │
            │  Port 8084     │   │  Nginx       │
            └───────┬────────┘   └──────────────┘
                    │
        ┌───────────┼───────────────────┐
        │           │                   │
    ┌───▼───┐  ┌───▼───┐          ┌────▼────┐
    │Keycloak│ │PostgreSQL│        │  Redis  │
    │  SSO   │ │  Users  │         │  Cache  │
    └────────┘ └─────────┘         └─────────┘
        │
        └─── Identity Providers: Google, GitHub, Microsoft
```

### Database Schema

**Core Tables** (PostgreSQL):
- `organizations` - Organization/tenant management
- `organization_members` - User-organization relationships
- `organization_invitations` - Pending invites
- `api_keys` - User API keys (bcrypt hashed)
- `audit_logs` - System-wide audit trail
- `subscription_tiers` - Tier definitions (Trial, Starter, Pro, Enterprise)
- `tier_features` - Feature access control per tier
- `add_ons` - App/service definitions
- `app_model_lists` - Curated model lists per app
- `app_model_list_items` - Models with tier access control

**Keycloak** (uchub realm):
- Users and authentication
- Roles and permissions
- Sessions and tokens
- User attributes (subscription_tier, api_calls_limit, etc.)

**Lago** (billing database):
- Customers (synced with Keycloak users)
- Subscriptions
- Invoices and payments
- Usage metering events

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- PostgreSQL 14+ (or use Docker)
- Redis 7+ (or use Docker)
- Keycloak 26+ (or use Docker)
- Node.js 18+ (for frontend development)
- Python 3.10+ (for backend development)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/ops-center.git
cd ops-center
```

### 2. Environment Configuration

Create `.env` file:

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=ops_user
POSTGRES_PASSWORD=ops_password
POSTGRES_DB=ops_center_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Keycloak SSO
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=ops-center
KEYCLOAK_CLIENT_ID=ops-center
KEYCLOAK_CLIENT_SECRET=your-client-secret
KEYCLOAK_ADMIN_PASSWORD=admin-password

# Application
SESSION_SECRET_KEY=your-session-secret-key
SESSION_COOKIE_DOMAIN=localhost
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Billing (Optional - Lago + Stripe)
LAGO_API_KEY=your-lago-api-key
LAGO_API_URL=http://localhost:3000
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...

# LiteLLM Proxy (Optional)
LITELLM_MASTER_KEY=your-litellm-key
LITELLM_PROXY_URL=http://localhost:4000
```

### 3. Start with Docker Compose

```bash
# Start all services (PostgreSQL, Redis, Keycloak, Ops-Center)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f ops-center
```

### 4. Initialize Database

```bash
# Run migrations
docker-compose exec ops-center python /app/scripts/migrate.py

# Create admin user (via Keycloak)
# Access Keycloak: http://localhost:8080/admin
# Create user in realm: ops-center
# Assign role: admin
```

### 5. Access Application

- **Frontend**: http://localhost:8084
- **API Docs**: http://localhost:8084/docs (FastAPI auto-generated)
- **Keycloak**: http://localhost:8080/admin

---

## Development Setup

### Backend Development

```bash
# Navigate to backend directory
cd backend/

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run backend in development mode
uvicorn server:app --reload --host 0.0.0.0 --port 8084
```

### Frontend Development

```bash
# Navigate to frontend directory (project root)
cd ops-center/

# Install dependencies
npm install

# Run development server (Vite)
npm run dev  # Runs on port 5173

# Build for production
npm run build

# Preview production build
npm run preview
```

### Hot Reload Development

**Backend**: FastAPI auto-reloads on code changes when running with `--reload` flag.

**Frontend**: Vite provides instant HMR (Hot Module Replacement).

**Recommended Workflow**:
1. Run backend: `uvicorn server:app --reload`
2. Run frontend: `npm run dev`
3. Access app: `http://localhost:5173` (proxies API to backend)

---

## Project Structure

```
ops-center/
├── backend/                    # FastAPI backend
│   ├── server.py              # Main FastAPI app
│   ├── routers/               # API route modules
│   │   ├── user_management_api.py
│   │   ├── billing_analytics_api.py
│   │   ├── org_api.py
│   │   ├── litellm_api.py
│   │   └── model_list_api.py
│   ├── services/              # Business logic services
│   │   ├── keycloak_integration.py
│   │   ├── lago_integration.py
│   │   ├── subscription_manager.py
│   │   └── model_list_manager.py
│   ├── scripts/               # Utility scripts
│   │   ├── migrate.py
│   │   ├── seed_model_lists.py
│   │   └── quick_populate_users.py
│   ├── migrations/            # SQL migrations
│   └── requirements.txt       # Python dependencies
├── src/                       # React frontend
│   ├── App.jsx               # Main app with routes
│   ├── pages/
│   │   ├── UserManagement.jsx
│   │   ├── UserDetail.jsx
│   │   ├── BillingDashboard.jsx
│   │   ├── Dashboard.jsx
│   │   ├── Services.jsx
│   │   ├── LLMManagement.jsx
│   │   ├── account/          # Account settings
│   │   ├── subscription/     # Subscription management
│   │   ├── organization/     # Organization management
│   │   └── admin/            # Admin-only pages
│   ├── components/
│   │   ├── Layout.jsx
│   │   ├── RoleManagementModal.jsx
│   │   ├── PermissionMatrix.jsx
│   │   ├── BulkActionsToolbar.jsx
│   │   └── ActivityTimeline.jsx
│   ├── contexts/
│   │   ├── SystemContext.jsx
│   │   ├── ThemeContext.jsx
│   │   └── OrganizationContext.jsx
│   └── config/
│       └── routes.js
├── public/                    # Static assets
│   ├── index.html
│   └── logos/
├── docker-compose.yml         # Docker orchestration
├── Dockerfile                 # Container definition
├── .env                       # Environment variables
├── package.json               # Frontend dependencies
├── vite.config.js             # Vite build config
└── README.md                  # Project documentation
```

---

## API Reference

### Authentication

All API endpoints require authentication via:
1. **Session Cookie** (web browser)
2. **Bearer Token** (API clients)

**Login Endpoint**:
```
GET /auth/login           # Redirect to Keycloak SSO
GET /auth/callback        # OAuth callback handler
POST /auth/logout         # Logout and clear session
```

### User Management API

**Base Path**: `/api/v1/admin/users`

#### User CRUD
```python
GET    /api/v1/admin/users                    # List users (with filtering)
GET    /api/v1/admin/users/{user_id}          # Get user details
POST   /api/v1/admin/users/comprehensive      # Create user
PUT    /api/v1/admin/users/{user_id}          # Update user
DELETE /api/v1/admin/users/{user_id}          # Delete user
```

#### Bulk Operations
```python
POST   /api/v1/admin/users/bulk/import        # Import from CSV
GET    /api/v1/admin/users/export             # Export to CSV
POST   /api/v1/admin/users/bulk/assign-roles  # Bulk role assignment
POST   /api/v1/admin/users/bulk/suspend       # Bulk suspend
POST   /api/v1/admin/users/bulk/delete        # Bulk delete
POST   /api/v1/admin/users/bulk/set-tier      # Bulk tier changes
```

#### Role Management
```python
GET    /api/v1/admin/users/{user_id}/roles             # Get user roles
POST   /api/v1/admin/users/{user_id}/roles/assign      # Assign role
DELETE /api/v1/admin/users/{user_id}/roles/{role}      # Remove role
GET    /api/v1/admin/users/roles/hierarchy             # Role hierarchy
GET    /api/v1/admin/users/roles/permissions           # Role permissions
```

#### Advanced Filtering

```python
# Filter users by multiple criteria
GET /api/v1/admin/users?search=john&tier=professional&role=admin&status=enabled

# Query Parameters:
# - search: email/username
# - tier: trial, starter, professional, enterprise
# - role: admin, moderator, developer, analyst, viewer
# - status: enabled, disabled, suspended
# - org_id: organization filter
# - created_from / created_to: date range
# - email_verified: true/false
# - byok_enabled: true/false
# - limit / offset: pagination
```

### Billing API

**Base Path**: `/api/v1/billing`

```python
GET  /api/v1/billing/plans                    # List subscription plans
GET  /api/v1/billing/subscriptions/current    # Current subscription
POST /api/v1/billing/subscriptions/create     # Create subscription
POST /api/v1/billing/subscriptions/cancel     # Cancel subscription
POST /api/v1/billing/subscriptions/upgrade    # Upgrade tier
POST /api/v1/billing/subscriptions/downgrade  # Downgrade tier
GET  /api/v1/billing/invoices                 # Invoice history
```

### Organization API

**Base Path**: `/api/v1/organizations`

```python
GET    /api/v1/organizations                  # List organizations
POST   /api/v1/organizations                  # Create organization
GET    /api/v1/organizations/{org_id}         # Get org details
PUT    /api/v1/organizations/{org_id}         # Update organization
DELETE /api/v1/organizations/{org_id}         # Delete organization
GET    /api/v1/organizations/{org_id}/members # List members
POST   /api/v1/organizations/{org_id}/invite  # Invite member
```

### LLM API (LiteLLM Proxy)

**Base Path**: `/api/v1/llm`

```python
POST /api/v1/llm/chat/completions       # OpenAI-compatible chat
GET  /api/v1/llm/models                  # List all models
GET  /api/v1/llm/models/curated          # Curated models (app/tier)
GET  /api/v1/llm/models/categorized      # BYOK vs platform models
POST /api/v1/llm/image/generations       # Image generation
GET  /api/v1/llm/usage                   # Usage statistics
```

### Model List Management API

**Admin Endpoints**: `/api/v1/admin/model-lists`

```python
GET    /api/v1/admin/model-lists                    # List all
POST   /api/v1/admin/model-lists                    # Create list
GET    /api/v1/admin/model-lists/{id}               # Get details
PUT    /api/v1/admin/model-lists/{id}               # Update list
DELETE /api/v1/admin/model-lists/{id}               # Delete list
GET    /api/v1/admin/model-lists/{id}/models        # Get models
POST   /api/v1/admin/model-lists/{id}/models        # Add model
DELETE /api/v1/admin/model-lists/{id}/models/{mid}  # Remove model
PUT    /api/v1/admin/model-lists/{id}/reorder       # Reorder models
```

---

## Configuration

### Environment Variables

**Database Configuration**:
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=ops_user
POSTGRES_PASSWORD=ops_password
POSTGRES_DB=ops_center_db
```

**Redis Configuration**:
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Optional
```

**Keycloak SSO**:
```bash
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=ops-center
KEYCLOAK_CLIENT_ID=ops-center
KEYCLOAK_CLIENT_SECRET=your-client-secret
KEYCLOAK_ADMIN_PASSWORD=admin-password
```

**Application Settings**:
```bash
SESSION_SECRET_KEY=your-random-secret-key
SESSION_COOKIE_DOMAIN=localhost
SESSION_COOKIE_SECURE=false  # Set to true in production
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**Billing (Optional)**:
```bash
# Lago Billing
LAGO_API_KEY=your-lago-api-key
LAGO_API_URL=http://localhost:3000

# Stripe Payment Processing
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

**LLM Proxy (Optional)**:
```bash
LITELLM_MASTER_KEY=your-litellm-key
LITELLM_PROXY_URL=http://localhost:4000
OPENROUTER_API_KEY=your-openrouter-key  # For model pricing
```

---

## Testing

### Backend Tests

```bash
cd backend/

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_user_management.py
```

### Frontend Tests

```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

### Integration Tests

```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/

# Cleanup
docker-compose -f docker-compose.test.yml down
```

---

## Deployment

### Production Build

**Backend**:
```bash
# Build Docker image
docker build -t ops-center-backend:latest .

# Run container
docker run -d \
  --name ops-center \
  -p 8084:8084 \
  --env-file .env \
  ops-center-backend:latest
```

**Frontend**:
```bash
# Build production assets
npm run build

# Output: dist/ directory with static files
# Deploy to web server (Nginx, Apache, etc.)
```

### Docker Compose Production

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment-Specific Configs

Create separate `.env` files:
- `.env.development` - Local development
- `.env.staging` - Staging environment
- `.env.production` - Production environment

Load with:
```bash
docker-compose --env-file .env.production up -d
```

---

## Common Tasks

### Adding a New User

**Via UI**:
1. Navigate to `/admin/system/users`
2. Click "Add User" button
3. Fill in user details
4. Assign role and tier
5. Click "Create"

**Via API**:
```bash
curl -X POST http://localhost:8084/api/v1/admin/users/comprehensive \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "user",
    "firstName": "John",
    "lastName": "Doe",
    "tier": "professional",
    "role": "developer"
  }'
```

### Adding a Subscription Tier

**Database Insert**:
```sql
INSERT INTO subscription_tiers (
  tier_code, tier_name, monthly_price, annual_price,
  api_calls_limit, llm_markup_percentage
) VALUES (
  'custom', 'Custom Tier', 29.00, 290.00,
  5000, 15.00
);
```

**Enable Features for Tier**:
```sql
-- Enable specific features for this tier
INSERT INTO tier_features (tier_id, feature_key, enabled)
SELECT id, 'feature_name', true
FROM subscription_tiers
WHERE tier_code = 'custom';
```

### Adding a New App/Service

**Database Insert**:
```sql
INSERT INTO add_ons (
  name, slug, description, launch_url,
  category, feature_key, icon_url, is_active
) VALUES (
  'My Service',
  'my-service',
  'Description of service',
  'https://myservice.example.com',
  'tools',
  'my_service_access',
  '/logos/myservice.svg',
  true
);
```

**Enable for Tiers**:
```sql
-- Enable for specific tiers
INSERT INTO tier_features (tier_id, feature_key, enabled)
SELECT id, 'my_service_access', true
FROM subscription_tiers
WHERE tier_code IN ('professional', 'enterprise');
```

### Creating a Curated Model List

**Via Admin UI**:
1. Navigate to `/admin/system/model-lists`
2. Click "Create New List"
3. Set app filter (e.g., "bolt-diy")
4. Add models with tier access
5. Drag to reorder
6. Save

**Via API**:
```bash
curl -X POST http://localhost:8084/api/v1/admin/model-lists \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "app_filter": "my-app",
    "tier_filter": null,
    "name": "My App Models",
    "description": "Curated models for my app"
  }'
```

---

## Troubleshooting

### Database Connection Errors

**Problem**: Cannot connect to PostgreSQL

**Solutions**:
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
docker exec -it postgres psql -U ops_user -d ops_center_db

# Check environment variables
docker exec ops-center env | grep POSTGRES

# Restart PostgreSQL
docker restart postgres
```

### Keycloak SSO Errors

**Problem**: 401 Unauthorized or redirect loop

**Solutions**:
```bash
# Verify Keycloak is running
docker ps | grep keycloak

# Check client configuration
# Go to: http://localhost:8080/admin
# Verify redirect URIs match your app URL

# Check environment variables
docker exec ops-center env | grep KEYCLOAK

# Clear browser cookies and retry
```

### Frontend Not Loading

**Problem**: White screen or React errors

**Solutions**:
```bash
# Clear Vite cache
rm -rf node_modules/.vite dist/

# Reinstall dependencies
npm install

# Rebuild frontend
npm run build

# Check for build errors in console

# Clear browser cache (Ctrl + Shift + R)
```

### API 500 Errors

**Problem**: Internal server errors

**Solutions**:
```bash
# Check backend logs
docker logs ops-center --tail 100

# Check database connectivity
docker exec ops-center python -c "import psycopg2; print('DB OK')"

# Check Redis connectivity
docker exec ops-center python -c "import redis; r=redis.Redis(); print(r.ping())"

# Restart backend
docker restart ops-center
```

---

## Contributing

We welcome contributions! Please follow these guidelines:

### Code Style

- **Python**: Follow PEP 8, use `black` for formatting
- **JavaScript**: Use ESLint + Prettier
- **Commits**: Conventional commits format (`feat:`, `fix:`, `docs:`)

### Development Workflow

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes and test locally
4. Commit with descriptive message
5. Push to your fork
6. Open pull request

### Testing Requirements

- All new features must include tests
- Maintain >80% code coverage
- Pass all CI/CD checks

### Documentation

- Update API documentation for new endpoints
- Add JSDoc comments for functions
- Update README for major features

---

## License

MIT License - see LICENSE file for details

---

## Support

- **Documentation**: See `docs/` directory
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

## Acknowledgments

Built with:
- FastAPI
- React
- Keycloak
- Lago
- LiteLLM
- Material-UI

---

**For Developers**: This is an open-source project designed for self-hosting and customization. All production-specific references, credentials, and URLs have been removed. Configure your own environment variables for deployment.
