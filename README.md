# Ops-Center

<div align="center">

<img src="public/logos/The_Colonel.png" alt="Ops-Center" width="120" />

### The AI Infrastructure Command Center

**Manage users, billing, LLMs, and services from one dashboard.**

[![GitHub stars](https://img.shields.io/github/stars/Unicorn-Commander/Ops-Center-OSS?style=social)](https://github.com/Unicorn-Commander/Ops-Center-OSS/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Unicorn-Commander/Ops-Center-OSS?style=social)](https://github.com/Unicorn-Commander/Ops-Center-OSS/network/members)

[![Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-yellow.svg)](https://python.org)
[![React 18](https://img.shields.io/badge/react-18-61dafb.svg)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/fastapi-modern-009688.svg)](https://fastapi.tiangolo.com)

[Quick Start](#quick-start) · [Features](#features) · [Roadmap](#roadmap) · [Used in Production](#used-in-production) · [Documentation](#documentation)

</div>

---

## What is Ops-Center?

Ops-Center is an open source operations dashboard for AI infrastructure. It provides centralized management for users, subscriptions, LLM routing, and integrated services.

Think of it as your infrastructure control panel: user management, billing, API routing, and service orchestration in one place.

<p align="center">
  <img src="docs/screenshots/analytics.png" alt="Analytics Dashboard" width="100%" />
</p>

---

## Why Ops-Center?

Building an AI SaaS typically requires stitching together a dozen services. Ops-Center consolidates them into one self-hosted platform.

### What It Replaces

<table>
<tr>
<th>Category</th>
<th>Ops-Center Feature</th>
<th>Replaces</th>
<th>Typical Cost</th>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/LLM-Routing-blueviolet?style=flat-square" alt="LLM"/></td>
<td>LiteLLM integration</td>
<td>OpenRouter, Portkey, Helicone</td>
<td>$50-500/mo + API markup</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Auth-SSO-blue?style=flat-square" alt="Auth"/></td>
<td>Keycloak SSO</td>
<td>Auth0, Okta, Clerk, Cognito</td>
<td>$100-1000+/mo</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Billing-Usage-green?style=flat-square" alt="Billing"/></td>
<td>Lago + Stripe</td>
<td>Metronome, Orb, Amberflo</td>
<td>$500-2000+/mo</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Analytics-Metrics-orange?style=flat-square" alt="Analytics"/></td>
<td>Built-in dashboards</td>
<td>Datadog, Splunk, Mixpanel</td>
<td>$100-1000+/mo</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/API-Gateway-red?style=flat-square" alt="API"/></td>
<td>Rate limiting, keys</td>
<td>Kong, Apigee, AWS API Gateway</td>
<td>$200-500+/mo</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Admin-Panel-purple?style=flat-square" alt="Admin"/></td>
<td>Full admin UI</td>
<td>Retool, Appsmith, custom dev</td>
<td>$50-500/mo</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/DNS-Management-cyan?style=flat-square" alt="DNS"/></td>
<td>Cloudflare + Namecheap</td>
<td>Multiple dashboards</td>
<td>Management overhead</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Infra-Monitoring-yellow?style=flat-square" alt="Infra"/></td>
<td>Prometheus + Grafana</td>
<td>Datadog, Grafana Cloud</td>
<td>$50-500/mo</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/User-Portal-pink?style=flat-square" alt="Portal"/></td>
<td>Self-service dashboard</td>
<td>Custom user portals, Stripe Portal</td>
<td>Dev time</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/RBAC-Permissions-lightgrey?style=flat-square" alt="RBAC"/></td>
<td>Role-based access control</td>
<td>Permit.io, Oso, custom RBAC</td>
<td>$100-500/mo</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Apps-Launcher-teal?style=flat-square" alt="Apps"/></td>
<td>Apps dashboard with SSO</td>
<td>Okta Dashboard, custom app portals</td>
<td>$50-200/mo</td>
</tr>
</table>

### Cost Comparison

<table>
<tr>
<td width="50%" valign="top">

**Without Ops-Center**

| Service | Monthly Cost |
|---------|-------------|
| Auth0 / Clerk | $200 |
| OpenRouter | API markup fees |
| Metronome / Orb | $500 |
| Datadog | $200 |
| Retool | $100 |
| Kong / API Gateway | $200 |
| Custom integration | Dev time |
| **Total** | **$1,200+ /mo** |

</td>
<td width="50%" valign="top">

**With Ops-Center**

| Component | Cost |
|-----------|------|
| Self-hosted | $0 |
| Your infrastructure | Your servers |
| No per-seat fees | $0 |
| No API markup | $0 |
| No vendor lock-in | $0 |
| **Total** | **$0 platform fees*** |

</td>
</tr>
</table>

<sub>*You pay only for your own infrastructure and any LLM provider API costs (OpenAI, Anthropic, etc.)</sub>

### What Makes It Different

<table>
<tr>
<td align="center" width="25%">
<img src="https://img.shields.io/badge/BYOK-Bring%20Your%20Own%20Key-success?style=for-the-badge" alt="BYOK"/>
<br/><br/>
<strong>BYOK Support</strong><br/>
Let users bring their own API keys. No platform markup. Unique feature most platforms lack.
</td>
<td align="center" width="25%">
<img src="https://img.shields.io/badge/Unified-LLM%20%2B%20Billing-blue?style=for-the-badge" alt="Unified"/>
<br/><br/>
<strong>Unified System</strong><br/>
Credit system tied directly to LLM usage with automatic cost tracking per user and org.
</td>
<td align="center" width="25%">
<img src="https://img.shields.io/badge/Tier--Based-App%20Access-purple?style=for-the-badge" alt="Tiers"/>
<br/><br/>
<strong>Dynamic Access</strong><br/>
Apps appear based on subscription tier. Database-driven, no code deploys needed.
</td>
<td align="center" width="25%">
<img src="https://img.shields.io/badge/Single-Dashboard-orange?style=for-the-badge" alt="Single"/>
<br/><br/>
<strong>One Interface</strong><br/>
DNS, users, billing, LLMs, services. One dashboard instead of 10 browser tabs.
</td>
</tr>
</table>

---

## Features

### Identity and Access
- Keycloak SSO with Google, GitHub, and Microsoft providers
- Role-based access control (RBAC) with 5-tier permission hierarchy
- Multi-tenant organization and team management
- User impersonation for admin support
- Complete audit logging across all operations

### User Self-Service
- Personal dashboard with usage stats and activity
- Self-service profile and account management
- API key generation and management
- Subscription upgrades, downgrades, and cancellations
- Invoice history and payment method management

### LLM Management
- 1500+ models via LiteLLM (OpenAI, Anthropic, Google, Meta, and more)*
- BYOK support: bring your own API keys with no platform markup
- Credit system with automatic usage tracking
- Image generation with DALL-E and Stable Diffusion
- Smart routing to cheapest or fastest provider

<sub>*Model availability depends on configured providers (OpenRouter, direct API keys, self-hosted models, etc.)</sub>

### Billing and Subscriptions
- Lago + Stripe integration
- Usage-based billing with real-time metering
- Tiered subscription plans with feature gating
- Per-user and per-organization cost tracking
- Automated invoicing and payment processing

### Apps Dashboard
- Centralized launcher for all integrated services
- Dynamic tier-based access control
- Single sign-on across all apps
- Admin control over which tiers access which apps
- Database-driven configuration (no code deploys needed)

### Infrastructure
- Cloudflare DNS management and zone control
- Namecheap domain management with migration support
- Traefik reverse proxy integration
- Prometheus and Grafana monitoring
- Docker-native deployment

---

## Screenshots

<table>
<tr>
<td width="50%">
<p align="center"><strong>Apps Marketplace</strong></p>
<img src="docs/screenshots/landing-page.png" alt="Apps Marketplace" />
</td>
<td width="50%">
<p align="center"><strong>LLM Model Catalog</strong></p>
<img src="docs/screenshots/llm-management.png" alt="LLM Management" />
</td>
</tr>
<tr>
<td width="50%">
<p align="center"><strong>User Management</strong></p>
<img src="docs/screenshots/user-management.png" alt="User Management" />
</td>
<td width="50%">
<p align="center"><strong>BYOK API Keys</strong></p>
<img src="docs/screenshots/byok.png" alt="BYOK" />
</td>
</tr>
<tr>
<td width="50%">
<p align="center"><strong>Billing & Subscriptions</strong></p>
<img src="docs/screenshots/billing.png" alt="Billing" />
</td>
<td width="50%">
<p align="center"><strong>SSO Login</strong></p>
<img src="docs/screenshots/sso-login.png" alt="SSO Login" />
</td>
</tr>
</table>

---

## Quick Start

<table>
<tr>
<td>

### Prerequisites

| Requirement | Included |
|-------------|----------|
| Docker & Docker Compose | Required |
| PostgreSQL | ✅ In compose |
| Redis | ✅ In compose |
| Keycloak | Configure yours |

</td>
<td>

### System Requirements

| Resource | Minimum |
|----------|---------|
| CPU | 2 cores |
| RAM | 4 GB |
| Disk | 20 GB |
| OS | Linux, macOS, Windows (WSL2) |

</td>
</tr>
</table>

<br/>

<table>
<tr>
<td width="33%" align="center">

### <img src="https://img.shields.io/badge/1-Clone-blue?style=for-the-badge" alt="Step 1"/>

```bash
git clone https://github.com/Unicorn-Commander/Ops-Center-OSS.git
cd Ops-Center-OSS
```

</td>
<td width="33%" align="center">

### <img src="https://img.shields.io/badge/2-Configure-purple?style=for-the-badge" alt="Step 2"/>

```bash
cp .env.example .env.auth
# Edit .env.auth with your settings
```

</td>
<td width="33%" align="center">

### <img src="https://img.shields.io/badge/3-Launch-green?style=for-the-badge" alt="Step 3"/>

```bash
docker compose -f docker-compose.direct.yml up -d
```

</td>
</tr>
</table>

<div align="center">

### 🎉 Access your dashboard at `http://localhost:8084`

</div>

---

## Keycloak Setup

Ops-Center requires Keycloak for authentication. You can use an existing Keycloak instance or deploy one alongside.

<table>
<tr>
<td width="50%" valign="top">

### Manual Setup

| Step | Action |
|------|--------|
| 1 | Create Realm: `ops-center` |
| 2 | Create Client: `ops-center` (confidential, OIDC) |
| 3 | Set Valid Redirect URIs: `http://localhost:8084/*` |
| 4 | Set Web Origins: `http://localhost:8084` |
| 5 | Enable identity providers (Google, GitHub, Microsoft) |
| 6 | Create realm roles: `admin`, `user`, `org-admin` |
| 7 | Copy Client Secret → `KEYCLOAK_CLIENT_SECRET` in `.env.auth` |

</td>
<td width="50%" valign="top">

### Quick Import (Recommended)

```bash
# Import pre-configured realm
docker exec -it keycloak \
  /opt/keycloak/bin/kc.sh import \
  --file /tmp/realm-export.json
```

The included `keycloak/realm-export.json` provides:
- ✅ Pre-configured `ops-center` client
- ✅ Google, GitHub, Microsoft providers (add your keys)
- ✅ Default roles and permissions
- ✅ Recommended session settings

</td>
</tr>
</table>

> **Tip:** For local development, you can run Keycloak in Docker:
> ```bash
> docker run -d --name keycloak -p 8080:8080 \
>   -e KEYCLOAK_ADMIN=admin -e KEYCLOAK_ADMIN_PASSWORD=admin \
>   quay.io/keycloak/keycloak:latest start-dev
> ```

---

## Deployment Options

Choose the right configuration for your use case:

| Goal | Command | Description |
|------|---------|-------------|
| **Local Development** | `docker compose -f docker-compose.direct.yml up -d` | Fastest setup, direct port access |
| **Behind Traefik** | `docker compose -f docker-compose.traefik.yml up -d` | Reverse proxy with automatic TLS |
| **With Monitoring** | `docker compose -f docker-compose.monitoring.yml up -d` | Adds Prometheus + Grafana |
| **With LiteLLM** | `docker compose -f docker-compose.litellm.yml up -d` | Includes LiteLLM proxy container |
| **Production** | `docker compose -f docker-compose.prod.yml up -d` | Optimized for production |
| **CenterDeep** | `docker compose -f docker-compose.centerdeep.yml up -d` | Specialized search configuration |

You can combine configurations:
```bash
docker compose -f docker-compose.direct.yml -f docker-compose.monitoring.yml up -d
```

---

## Ports & URLs

| Service | Port | Default URL | Notes |
|---------|------|-------------|-------|
| **Dashboard** | 8084 | http://localhost:8084 | Main Ops-Center UI |
| **Frontend Dev** | 5173 | http://localhost:5173 | Vite dev server (npm run dev) |
| **API Docs** | 8084 | http://localhost:8084/docs | FastAPI OpenAPI docs |
| **Keycloak** | 8080 | http://localhost:8080 | Your Keycloak instance |
| **PostgreSQL** | 5432 | - | Internal, not exposed by default |
| **Redis** | 6379 | - | Internal, not exposed by default |
| **Prometheus** | 9090 | http://localhost:9090 | With monitoring compose |
| **Grafana** | 3000 | http://localhost:3000 | With monitoring compose |

---

## Security Notes

<table>
<tr>
<td width="50%">

### ⚠️ Production Checklist

- [ ] Run behind TLS/HTTPS (use Traefik or nginx)
- [ ] Never expose PostgreSQL/Redis to public internet
- [ ] Use strong, unique values for all secrets
- [ ] Configure Keycloak on a private network
- [ ] Enable rate limiting on public endpoints
- [ ] Review [SECURITY.md](SECURITY.md) before deploying

</td>
<td width="50%">

### 🔐 Secret Management

```bash
# Generate secure secrets
openssl rand -hex 32  # SESSION_SECRET_KEY
openssl rand -hex 32  # ENCRYPTION_KEY

# Never commit .env files
echo ".env*" >> .gitignore
```

Store production secrets in:
- Environment variables
- Docker secrets
- Vault/AWS Secrets Manager

</td>
</tr>
</table>

---

## Configuration

<table>
<tr>
<td width="50%" valign="top">

### <img src="https://img.shields.io/badge/Required-Configuration-critical?style=flat-square" alt="Required"/>

```bash
# 🔐 Authentication (Keycloak)
KEYCLOAK_URL=http://your-keycloak:8080
KEYCLOAK_REALM=your-realm
KEYCLOAK_CLIENT_ID=ops-center
KEYCLOAK_CLIENT_SECRET=your-secret

# 🐘 Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=ops
POSTGRES_PASSWORD=secure-password
POSTGRES_DB=ops_center
```

</td>
<td width="50%" valign="top">

### <img src="https://img.shields.io/badge/Optional-Configuration-blue?style=flat-square" alt="Optional"/>

```bash
# 💳 Billing
LAGO_API_KEY=your-lago-key
STRIPE_SECRET_KEY=your-stripe-key

# 🤖 LLM Proxy
LITELLM_MASTER_KEY=your-litellm-key
OPENROUTER_API_KEY=your-openrouter-key

# ☁️ DNS Management
CLOUDFLARE_API_TOKEN=your-cloudflare-token
NAMECHEAP_API_KEY=your-namecheap-key
```

</td>
</tr>
</table>

<div align="center">

📄 See **[.env.example](.env.example)** for all configuration options

</div>

---

## Architecture

```mermaid
flowchart TB
    subgraph External["External Services"]
        KC[("🔐 Keycloak<br/>SSO")]
        LAGO[("💳 Lago<br/>Billing")]
        STRIPE[("💰 Stripe<br/>Payments")]
        LLM[("🤖 LiteLLM<br/>1500+ Models")]
        CF[("☁️ Cloudflare<br/>DNS")]
    end

    subgraph OpsCenter["Ops-Center"]
        direction TB
        API["⚡ FastAPI Backend"]
        UI["🎨 React Dashboard"]

        subgraph Features["Core Features"]
            AUTH["🔑 Auth & RBAC"]
            BILL["📊 Usage & Credits"]
            APPS["📱 Apps Launcher"]
            USERS["👥 User Management"]
            ADMIN["⚙️ Admin Panel"]
        end
    end

    subgraph Data["Data Layer"]
        PG[("🐘 PostgreSQL")]
        REDIS[("⚡ Redis")]
    end

    subgraph UserApps["Integrated Apps"]
        CHAT["💬 Chat UI"]
        SEARCH["🔍 Search"]
        AGENTS["🤖 Agents"]
        CUSTOM["📦 Your Apps"]
    end

    KC --> API
    LAGO --> API
    STRIPE --> API
    LLM --> API
    CF --> API

    API --> PG
    API --> REDIS
    API --> UI

    UI --> Features

    API --> UserApps

    style OpsCenter fill:#1a1a2e,stroke:#8b5cf6,stroke-width:2px
    style External fill:#0d1117,stroke:#30363d,stroke-width:1px
    style Data fill:#0d1117,stroke:#30363d,stroke-width:1px
    style UserApps fill:#0d1117,stroke:#30363d,stroke-width:1px
    style Features fill:#2d1b4e,stroke:#8b5cf6,stroke-width:1px
```

### Stack

<table>
<tr>
<td align="center"><strong>Backend</strong></td>
<td>
<img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
<img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
<img src="https://img.shields.io/badge/Pydantic-E92063?style=flat-square&logo=pydantic&logoColor=white" alt="Pydantic"/>
<img src="https://img.shields.io/badge/LiteLLM-000000?style=flat-square" alt="LiteLLM"/>
</td>
</tr>
<tr>
<td align="center"><strong>Frontend</strong></td>
<td>
<img src="https://img.shields.io/badge/React_18-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React"/>
<img src="https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white" alt="Vite"/>
<img src="https://img.shields.io/badge/MUI-007FFF?style=flat-square&logo=mui&logoColor=white" alt="MUI"/>
<img src="https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript"/>
</td>
</tr>
<tr>
<td align="center"><strong>Database</strong></td>
<td>
<img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
<img src="https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white" alt="Redis"/>
</td>
</tr>
<tr>
<td align="center"><strong>Auth</strong></td>
<td>
<img src="https://img.shields.io/badge/Keycloak-4D4D4D?style=flat-square&logo=keycloak&logoColor=white" alt="Keycloak"/>
<img src="https://img.shields.io/badge/OpenID_Connect-F78C40?style=flat-square&logo=openid&logoColor=white" alt="OIDC"/>
</td>
</tr>
<tr>
<td align="center"><strong>Billing</strong></td>
<td>
<img src="https://img.shields.io/badge/Stripe-008CDD?style=flat-square&logo=stripe&logoColor=white" alt="Stripe"/>
<img src="https://img.shields.io/badge/Lago-000000?style=flat-square" alt="Lago"/>
</td>
</tr>
<tr>
<td align="center"><strong>Infrastructure</strong></td>
<td>
<img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"/>
<img src="https://img.shields.io/badge/Traefik-24A1C1?style=flat-square&logo=traefikproxy&logoColor=white" alt="Traefik"/>
<img src="https://img.shields.io/badge/Nginx-009639?style=flat-square&logo=nginx&logoColor=white" alt="Nginx"/>
</td>
</tr>
</table>

---

## Integrations

<table>
<tr>
<th>Service</th>
<th>Purpose</th>
<th>Integration</th>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Keycloak-4D4D4D?style=flat-square&logo=keycloak&logoColor=white" alt="Keycloak"/></td>
<td>Identity and SSO</td>
<td><code>Native OIDC</code></td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Lago-6C5CE7?style=flat-square" alt="Lago"/></td>
<td>Usage-based billing</td>
<td><code>REST API</code></td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Stripe-008CDD?style=flat-square&logo=stripe&logoColor=white" alt="Stripe"/></td>
<td>Payment processing</td>
<td><code>Webhooks</code></td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/LiteLLM-10B981?style=flat-square" alt="LiteLLM"/></td>
<td>LLM routing (1500+ models)</td>
<td><code>OpenAI-compatible</code></td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Cloudflare-F38020?style=flat-square&logo=cloudflare&logoColor=white" alt="Cloudflare"/></td>
<td>DNS management</td>
<td><code>REST API</code></td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Namecheap-DE3723?style=flat-square&logo=namecheap&logoColor=white" alt="Namecheap"/></td>
<td>Domain management</td>
<td><code>REST API</code></td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Prometheus-E6522C?style=flat-square&logo=prometheus&logoColor=white" alt="Prometheus"/></td>
<td>Metrics collection</td>
<td><code>/metrics endpoint</code></td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Grafana-F46800?style=flat-square&logo=grafana&logoColor=white" alt="Grafana"/></td>
<td>Dashboards</td>
<td><code>Prometheus datasource</code></td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Traefik-24A1C1?style=flat-square&logo=traefikproxy&logoColor=white" alt="Traefik"/></td>
<td>Reverse proxy</td>
<td><code>Docker labels</code></td>
</tr>
</table>

---

## Development

<table>
<tr>
<td width="50%" valign="top">

### <img src="https://img.shields.io/badge/🔧-Local_Development-blue?style=flat-square" alt="Local"/>

**Frontend** (hot reload)
```bash
npm install
npm run dev  # http://localhost:5173
```

**Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8084
```

</td>
<td width="50%" valign="top">

### <img src="https://img.shields.io/badge/🚀-Production_Build-green?style=flat-square" alt="Production"/>

**Build and Deploy**
```bash
npm run build
docker compose -f docker-compose.direct.yml up -d --build
```

**Verify**
```bash
docker ps | grep ops-center
curl http://localhost:8084/health
```

</td>
</tr>
</table>

### Project Structure

```
ops-center/
├── 📂 backend/               # FastAPI application
│   ├── 📄 server.py          # Main entry point
│   ├── 📄 *_api.py           # API routers (50+ modules)
│   └── 📂 migrations/        # Database migrations
├── 📂 src/                   # React frontend
│   ├── 📂 pages/             # Page components
│   ├── 📂 components/        # Reusable components
│   └── 📂 contexts/          # React contexts
├── 📂 public/                # Static assets
├── 📂 docs/                  # Documentation
│   └── 📂 screenshots/       # App screenshots
└── 🐳 docker-compose.*.yml   # Docker configurations
```

---

## Documentation

<table>
<tr>
<td align="center">
<a href="CLAUDE.md">
<img src="https://img.shields.io/badge/📘-Technical_Reference-blue?style=for-the-badge" alt="Technical"/>
</a>
<br/><strong>CLAUDE.md</strong>
</td>
<td align="center">
<a href="CHANGELOG.md">
<img src="https://img.shields.io/badge/📋-Changelog-green?style=for-the-badge" alt="Changelog"/>
</a>
<br/><strong>Version History</strong>
</td>
<td align="center">
<a href="CONTRIBUTING.md">
<img src="https://img.shields.io/badge/🤝-Contributing-purple?style=for-the-badge" alt="Contributing"/>
</a>
<br/><strong>Guidelines</strong>
</td>
<td align="center">
<a href="docs/">
<img src="https://img.shields.io/badge/📚-All_Docs-orange?style=for-the-badge" alt="Docs"/>
</a>
<br/><strong>Full Documentation</strong>
</td>
</tr>
</table>

---

## Roadmap

<div align="center">

**🎖️ Coming Soon: The Colonel Agent**

*An AI Platform Engineer that integrates apps, configures billing, and manages organizations—via conversation.*

> "Colonel, set up a new client with org-admin, manager, and user tiers."

</div>

<table>
<tr>
<td width="25%" align="center">

**Phase 1**
<br/>Foundation

- CLI tool
- Webhooks
- Docker Hub images

</td>
<td width="25%" align="center">

**Phase 2**
<br/>Intelligence

- 🎖️ **The Colonel v1**
- Smart alerts
- Cost optimization

</td>
<td width="25%" align="center">

**Phase 3**
<br/>Scale

- Multi-server mgmt
- Kubernetes
- Terraform/IaC

</td>
<td width="25%" align="center">

**Phase 4**
<br/>Enterprise

- Mobile app
- Advanced RBAC
- HA deployment

</td>
</tr>
</table>

<div align="center">

📍 **[View Full Roadmap →](ROADMAP.md)**

</div>

---

## Contributing

<div align="center">

**We welcome contributions!** See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

</div>

```mermaid
flowchart LR
    A[🍴 Fork] --> B[🌿 Branch]
    B --> C[💻 Code]
    C --> D[✅ Test]
    D --> E[📤 Push]
    E --> F[🔀 PR]

    style A fill:#6366f1,color:#fff
    style B fill:#8b5cf6,color:#fff
    style C fill:#a855f7,color:#fff
    style D fill:#d946ef,color:#fff
    style E fill:#ec4899,color:#fff
    style F fill:#f43f5e,color:#fff
```

```bash
git checkout -b feature/your-feature    # Create branch
# Make your changes
git commit -m 'feat: add your feature'  # Commit
git push origin feature/your-feature    # Push
# Open a Pull Request on GitHub
```

---

## Star History

<div align="center">

<a href="https://star-history.com/#Unicorn-Commander/Ops-Center-OSS&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=Unicorn-Commander/Ops-Center-OSS&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Unicorn-Commander/Ops-Center-OSS&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Unicorn-Commander/Ops-Center-OSS&type=Date" width="600" />
  </picture>
</a>

<br/><br/>

[![Star this repo](https://img.shields.io/badge/⭐_Star_This_Repo-8b5cf6?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Unicorn-Commander/Ops-Center-OSS)

**If Ops-Center helps you, give it a star! It helps others discover the project.**

</div>

---

## Used in Production

<div align="center">

**Ops-Center powers real infrastructure serving real users.**

</div>

<table>
<tr>
<td align="center" width="50%">

<a href="https://centerdeep.online">
<img src="https://img.shields.io/badge/Center_Deep-Hosted_Search_&_Analytics-667eea?style=for-the-badge" alt="Center Deep"/>
</a>

**[centerdeep.online](https://centerdeep.online)**

Hosted AI-powered search and data analytics platform running on Ops-Center infrastructure.

</td>
<td align="center" width="50%">

<a href="https://unicorncommander.ai">
<img src="https://img.shields.io/badge/Unicorn_Commander-Production_Apps-8b5cf6?style=for-the-badge" alt="Unicorn Commander"/>
</a>

**[unicorncommander.ai](https://unicorncommander.ai)**

Production AI applications and services managed through Ops-Center.

</td>
</tr>
</table>

---

## Support the Project

<div align="center">

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-EA4AAA?style=for-the-badge&logo=github-sponsors&logoColor=white)](https://github.com/sponsors/Unicorn-Commander)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy_Me_A_Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/aaronyo)

</div>

---

## License

<div align="center">

<img src="https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge" alt="Apache 2.0"/>

**Open source under the [Apache License 2.0](LICENSE)**

Copyright 2025 **Magic Unicorn Unconventional Technology & Stuff Inc**

</div>

---

<div align="center">

<br/>

<a href="https://unicorncommander.com">
<img src="https://img.shields.io/badge/🦄_Product_Page-unicorncommander.com-8b5cf6?style=for-the-badge" alt="Product Page"/>
</a>
&nbsp;&nbsp;
<a href="https://centerdeep.ai">
<img src="https://img.shields.io/badge/🔍_Center_Deep-centerdeep.ai-667eea?style=for-the-badge" alt="Center Deep"/>
</a>
&nbsp;&nbsp;
<a href="https://magicunicorn.tech">
<img src="https://img.shields.io/badge/🏢_Company-Magic_Unicorn_Tech-ff6b6b?style=for-the-badge" alt="Magic Unicorn Tech"/>
</a>

<br/><br/>

<img src="public/logos/magic_unicorn_logo.png" alt="Magic Unicorn" width="60" />

**Built with 🦄 by Magic Unicorn Unconventional Technology & Stuff Inc**

</div>
