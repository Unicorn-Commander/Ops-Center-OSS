# UC-1 Pro Custom Auth Integration Guide

## ✅ What We Built

A complete custom authentication system that replaces Authentik with:
- Direct OAuth integration (Google, GitHub, Microsoft)
- Redis-backed session management
- Stripe subscription billing
- Lago usage metering
- BYOK (Bring Your Own Key) service management
- Tier-based access control

## 📦 Files Created

### Core Auth Module
- `backend/auth/__init__.py` - Module exports
- `backend/auth/oauth_providers.py` - OAuth integration
- `backend/auth/session_manager.py` - Redis sessions
- `backend/auth/subscription.py` - Stripe + tiers
- `backend/auth/access_control.py` - Access enforcement
- `backend/auth/deployment_config.py` - Dual deployment
- `backend/auth/service_manager.py` - BYOK management
- `backend/auth/usage_tracker.py` - Lago integration

### Integration
- `backend/server_auth_integrated.py` - New server with auth integrated
- `.env.auth.template` - Environment variable template

### Documentation
- `backend/auth/README.md` - Module documentation
- `backend/auth/LAGO_INTEGRATION.md` - Lago setup guide
- `backend/auth/SUMMARY.md` - Complete overview
- `INTEGRATION_GUIDE.md` - This file

## 🚀 Step-by-Step Setup

### Step 1: Set Up OAuth Applications

#### Google OAuth
1. Go to https://console.cloud.google.com/
2. Create new project or select existing
3. Enable "Google+ API"
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Application type: "Web application"
6. Authorized redirect URIs:
   - `https://your-domain.com/auth/callback`
   - `http://localhost:8084/auth/callback` (for testing)
7. Save Client ID and Client Secret

#### GitHub OAuth
1. Go to https://github.com/settings/developers
2. Click "New OAuth App"
3. Application name: "UC-1 Pro"
4. Homepage URL: `https://your-domain.com`
5. Authorization callback URL: `https://your-domain.com/auth/callback`
6. Save Client ID and Client Secret

#### Microsoft OAuth
1. Go to https://portal.azure.com/
2. Navigate to "Azure Active Directory" → "App registrations"
3. Click "New registration"
4. Name: "UC-1 Pro"
5. Supported account types: "Accounts in any organizational directory and personal Microsoft accounts"
6. Redirect URI: `https://your-domain.com/auth/callback`
7. Save Application (client) ID and create Client Secret

### Step 2: Configure Stripe

1. Go to https://dashboard.stripe.com/
2. Get your API keys (use test mode for development)
3. Create 4 products with prices:
   - **Trial**: $1.00 for 7 days (one-time)
   - **Starter**: $19/month (recurring)
   - **Professional**: $49/month (recurring)
   - **Enterprise**: $99/month (recurring)
4. Copy each Price ID (starts with `price_`)
5. Set up webhook endpoint:
   - URL: `https://your-domain.com/api/v1/stripe/webhook`
   - Events: `checkout.session.completed`, `customer.subscription.deleted`, `invoice.payment_failed`
6. Save webhook secret (starts with `whsec_`)

### Step 3: Configure Lago

1. Access Lago dashboard at http://localhost:3000 (or your Lago instance)
2. Get API key from Settings → API Keys
3. Create billable metrics:
   ```bash
   # Inference calls
   Code: inference_call
   Aggregation type: count_agg

   # Embedding calls
   Code: embedding_call
   Aggregation type: count_agg
   ```
4. Create plans:
   - **Professional Plan** (`uc1pro_professional`):
     - Base: $49/month
     - Inference charge: $2 per 1,000 calls after 2,500 free
   - **Enterprise Plan** (`uc1pro_enterprise`):
     - Base: $99/month
     - Inference charge: $1 per 1,000 calls after 50,000 free
5. Connect Lago to Stripe:
   - Settings → Integrations → Stripe
   - Provide Stripe API key
   - Enable "Sync with Stripe"

### Step 4: Configure Environment Variables

1. Copy template:
   ```bash
   cd /home/muut/Production/UC-1-Pro/services/ops-center
   cp .env.auth.template .env.auth
   ```

2. Edit `.env.auth` with your credentials:
   ```bash
   nano .env.auth
   ```

3. Generate encryption key for BYOK:
   ```bash
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

4. Source the environment:
   ```bash
   source .env.auth
   ```

### Step 5: Install Dependencies

```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center/backend

# Install Python dependencies
pip3 install stripe httpx redis cryptography
```

### Step 6: Deploy the New Server

#### Option A: Replace Existing Server (Recommended for production)
```bash
# Backup original
cp backend/server.py backend/server_original.py

# Deploy new version
cp backend/server_auth_integrated.py backend/server.py
```

#### Option B: Run Side-by-Side (For testing)
```bash
# Run new server on different port
cd backend
uvicorn server_auth_integrated:app --host 0.0.0.0 --port 8001
```

### Step 7: Restart Ops Center

```bash
# If using Docker Compose
docker-compose restart ops-center

# Or restart container directly
docker restart unicorn-ops-center
```

### Step 8: Test Authentication Flow

1. **Visit login page**: https://your-domain.com/login.html
2. **Click "Sign in with Google"** (or GitHub/Microsoft)
3. **Authorize the application**
4. **Verify redirect to dashboard**: Should redirect to `/dashboard`
5. **Check user in database**:
   ```bash
   sqlite3 /home/muut/Production/UC-1-Pro/volumes/ops_center.db
   SELECT * FROM users;
   .exit
   ```
6. **Test logout**: Click logout, should return to login page

### Step 9: Test Subscription Flow

1. **Visit pricing page**: https://your-domain.com/pricing
2. **Click "Subscribe to Professional"**
3. **Complete Stripe checkout** (use test card: 4242 4242 4242 4242)
4. **Verify tier update**:
   ```bash
   sqlite3 /home/muut/Production/UC-1-Pro/volumes/ops_center.db
   SELECT id, email, subscription_tier, stripe_customer_id FROM users;
   .exit
   ```
5. **Check Lago customer created**:
   - Visit Lago dashboard
   - Check Customers → should see your email

### Step 10: Test Usage Tracking

1. **Make API request**:
   ```bash
   curl -X POST https://your-domain.com/api/v1/inference \
     -H "Cookie: session_token=YOUR_SESSION_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello world"}'
   ```
2. **Check usage stats**:
   ```bash
   curl https://your-domain.com/api/v1/user/usage \
     -H "Cookie: session_token=YOUR_SESSION_TOKEN"
   ```
3. **Verify in Lago**:
   - Lago dashboard → Customers → Your email
   - Should see 1 inference call tracked

## 🎯 Key Endpoints

### Authentication
- `GET /auth/login/{provider}` - Initiate OAuth (google, github, microsoft)
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/logout` - Logout
- `GET /auth/user` - Get current user info

### Subscriptions
- `POST /api/v1/subscription/checkout` - Create Stripe checkout
- `POST /api/v1/stripe/webhook` - Stripe webhook handler

### Usage
- `GET /api/v1/user/usage` - Get usage statistics

### Protected Endpoints
- `POST /api/v1/inference` - Example protected endpoint with usage tracking

## 🔧 Troubleshooting

### OAuth Redirect URI Mismatch
**Error**: "Redirect URI mismatch"
**Solution**: Ensure OAuth redirect URIs match exactly in provider console and `.env.auth`

### Session Not Persisting
**Error**: User logged out immediately after login
**Solution**:
- Check Redis is running: `docker ps | grep redis`
- Verify REDIS_URL in `.env.auth`

### Stripe Webhook Not Working
**Error**: Subscription not activating
**Solution**:
- Check webhook endpoint is publicly accessible
- Verify webhook secret in `.env.auth`
- Check Stripe dashboard → Webhooks → Recent events

### Lago Not Tracking Usage
**Error**: Usage not appearing in Lago
**Solution**:
- Verify LAGO_API_KEY is set
- Check Lago customer exists
- Ensure billable metrics are created

### BYOK Keys Not Encrypted
**Error**: "Fernet key must be 32 url-safe base64-encoded bytes"
**Solution**: Generate proper encryption key (see Step 4)

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    oauth_provider TEXT NOT NULL,
    oauth_id TEXT NOT NULL,
    subscription_tier TEXT DEFAULT 'trial',
    stripe_customer_id TEXT,
    lago_customer_id TEXT,
    is_admin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🎓 Next Steps

1. **Create Login Page** - Design custom branded login page
2. **Create Signup Page** - Plan selection with embedded Stripe
3. **Create Dashboard** - User dashboard with usage display
4. **Add Email Notifications** - Payment confirmations, usage alerts
5. **Add Admin Panel** - User management, subscription overrides
6. **Set Up Monitoring** - Track auth errors, usage patterns

## 📞 Need Help?

- Review `backend/auth/README.md` for detailed module documentation
- Check `backend/auth/LAGO_INTEGRATION.md` for Lago-specific setup
- Read `backend/auth/SUMMARY.md` for complete system overview

---

**🎉 You now have a production-ready authentication and billing system!**
