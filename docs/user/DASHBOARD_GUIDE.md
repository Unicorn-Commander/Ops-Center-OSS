# User Dashboard Guide

**Last Updated**: February 22, 2026
**Audience**: Regular users (non-admin)
**Version**: 1.0.0

---

## Table of Contents

1. [Overview](#overview)
2. [Dashboard Sections](#dashboard-sections)
3. [Quick Actions](#quick-actions)
4. [Apps Marketplace](#apps-marketplace)
5. [Account Settings](#account-settings)
6. [Subscription Management](#subscription-management)
7. [Organization](#organization)
8. [Tips](#tips)
9. [Need Help?](#need-help)

---

## Overview

Your personal dashboard at `/admin/my-dashboard` gives you a quick view of your account status, usage, and available actions.

**How to Access:**
1. Go to https://unicorncommander.ai
2. Login via Keycloak SSO (Google, GitHub, Microsoft, or email)
3. You will land on the User Dashboard automatically

**Direct URL:** https://unicorncommander.ai/admin/my-dashboard

---

## Dashboard Sections

### Credit Balance

- Shows your current credit balance with a visual progress bar
- Credits are consumed when using AI models through the platform
- Warning indicators appear at 75% and 90% usage thresholds
- To add credits, use the **Upgrade** quick action or visit **Subscription > Plan**

```
+-------------------------------------+
| Current Balance: 9,850 credits      |
| Monthly Allocation: 10,000 credits  |
| [================>     ] 85% used   |
| Next Reset: Mar 1, 2026            |
+-------------------------------------+
```

**What Each Field Means:**

- **Current Balance** - Credits available right now
- **Monthly Allocation** - Credits you receive each billing cycle
- **Progress Bar** - Visual indicator of how many credits you have used
- **Next Reset** - When your credits replenish to full

**Warning Thresholds:**
- **75% used** - Yellow warning indicator appears
- **90% used** - Red urgent warning indicator appears
- **100% used** - API requests will be rate-limited until reset or upgrade

### Monthly Usage

- Displays API calls used this billing period
- Breakdown by model (top 5 most-used models shown)
- Breakdown by service type (chat, image generation, embeddings, etc.)

```
+-------------------------------------+
| Monthly Usage                       |
| API Calls: 847 / 10,000            |
|                                     |
| Top Models:                         |
|  1. GPT-4            320 calls     |
|  2. Claude 3.5       215 calls     |
|  3. Gemini 2.0       180 calls     |
|  4. DALL-E 3          82 calls     |
|  5. Stable Diff XL    50 calls     |
|                                     |
| By Service:                         |
|  Chat:        715 calls (84%)      |
|  Images:      132 calls (16%)      |
+-------------------------------------+
```

### Subscription Info

- Your current tier (Trial, Starter, Professional, Enterprise)
- Renewal date and billing cycle
- Quick link to change plans

```
+-------------------------------------+
| Subscription: Professional          |
| Status: Active                      |
| Renewal: March 15, 2026            |
| Billing Cycle: Monthly              |
|                                     |
| [Change Plan]                       |
+-------------------------------------+
```

### Recent Transactions

- Last 10 credit transactions
- Shows model used, credits consumed, and timestamp

```
+-------------------------------------------------------------+
| Recent Transactions                                          |
+----------+---------------------------+--------+--------------+
| Time     | Model                     | Credits| Service      |
+----------+---------------------------+--------+--------------+
| 2:15 PM  | anthropic/claude-3.5      | 12     | chat         |
| 1:48 PM  | openai/gpt-4              | 18     | chat         |
| 1:22 PM  | dall-e-3 (1024x1024)      | 48     | image        |
| 12:55 PM | google/gemini-2.0-flash   | 3      | chat         |
+----------+---------------------------+--------+--------------+
```

---

## Quick Actions

Quick actions are located at the top of the dashboard for fast navigation.

| Action | What It Does |
|--------|-------------|
| **API Keys** | Manage your API keys for programmatic access |
| **Upgrade** | View and change subscription plans |
| **Invoices** | View billing history and download invoices |
| **Payment Methods** | Manage credit cards and payment options |

All quick actions use SPA (single-page application) routing, so navigation is instant with no page reloads.

---

## Apps Marketplace

Visit `/admin/apps` to see all applications available to you based on your subscription tier. Available apps may include:

- **Open-WebUI** - AI chat interface with support for 100+ models
- **Center-Deep** - Privacy-focused AI metasearch engine (70+ search engines)
- **Bolt.diy** - AI development environment for building web applications
- **Presenton** - AI presentation generation with PPTX/PDF export
- **Forgejo** - Self-hosted Git server with GitHub-like features

Your tier determines which apps you can access. Apps appear as cards with a launch button that opens the service in a new tab.

**How Access Works:**

Your available apps are determined by two factors:
1. **Your subscription tier** - Each tier includes a set of default apps
2. **Organization grants** - Your admin may grant additional apps to your organization

If you need access to an app that does not appear in your marketplace, contact your organization administrator to request access or consider upgrading your subscription tier.

---

## Account Settings

### Profile (`/admin/account/profile`)

- Update your display name and avatar
- View your email and organization membership
- See your current subscription tier

### Security (`/admin/account/security`)

- Change your password
- View active sessions and revoke them if needed
- Monitor login activity

**Revoking Sessions:**
If you notice a session you do not recognize, click **Revoke** next to it immediately. This will log out that session and invalidate its tokens.

### API Keys (`/admin/account/api-keys`)

**Platform API Keys:**
- Generate API keys for programmatic access to UC-Cloud services
- Each key can be named for easy identification
- Keys are shown only once at creation time -- store them securely

**Bring Your Own Key (BYOK):**
- Add API keys from providers like OpenRouter, OpenAI, Anthropic, HuggingFace
- BYOK models are free (no platform credits charged)
- Your keys are encrypted at rest and never logged or displayed after entry

**Supported BYOK Providers:**

| Provider | Key Format | Free Signup Credits |
|----------|-----------|-------------------|
| OpenRouter | `sk-or-v1-...` | $5 free |
| OpenAI | `sk-...` | None (requires payment) |
| Anthropic | `sk-ant-...` | None (requires payment) |
| HuggingFace | `hf_...` | Many free models |
| Google (Gemini) | `AI...` | $150/month free tier |

### Notifications (`/admin/account/notifications`)

- Configure email notification preferences
- Set alerts for usage thresholds and billing events
- Choose which types of notifications you want to receive

---

## Subscription Management

### View Current Plan (`/admin/subscription/plan`)

- Compare all available plans side-by-side
- See features included in each tier
- Upgrade or downgrade your subscription

**Available Plans:**

| Feature | Trial | Starter | Professional | Enterprise |
|---------|-------|---------|--------------|------------|
| **Price** | $1/week | $19/mo | $49/mo | $99/mo |
| **Credits** | 700/week | 1,000/mo | 10,000/mo | Unlimited |
| **BYOK** | No | Yes | Yes | Yes |
| **Priority Support** | No | No | Yes | Yes |
| **Team Seats** | 1 | 1 | 1 | 5 |

### Usage Tracking (`/admin/subscription/usage`)

- Detailed usage analytics with charts
- Daily, weekly, and monthly breakdowns
- Export usage data to CSV

**Charts Available:**
- Daily usage trend (line chart)
- Service type breakdown (pie chart)
- Model usage distribution (bar chart)
- Credit consumption rate

### Billing History (`/admin/subscription/billing`)

- View all invoices
- Download PDF invoices
- See payment status for each invoice

### Payment Methods (`/admin/subscription/payment`)

- Add or remove credit cards
- Set default payment method
- Update billing address
- View upcoming invoice preview

**Supported Payment Methods:**
- Credit/debit cards (Visa, Mastercard, Amex, Discover)
- Apple Pay
- Google Pay

**Card Safety:**
All payment information is handled through Stripe and is PCI-compliant. Ops-Center never stores or sees your full card number.

---

## Organization

If you belong to an organization, you can access additional features.

### Team (`/admin/organization/team`)

- View organization members and their roles
- Invite new members (if you have permission)
- See role assignments (owner, admin, billing_admin, member)

### Billing (`/admin/organization/billing`)

- View organization-level billing
- See shared credit pool balance
- View team usage breakdown

---

## Tips

- **BYOK saves money**: Bring your own API keys from OpenRouter or OpenAI to use models without consuming platform credits. OpenRouter offers $5 free on signup and access to 300+ models.

- **Monitor usage**: Check your usage dashboard regularly to avoid hitting tier limits. The dashboard shows your credit consumption rate so you can predict when you will run out.

- **Choose models wisely**: Use faster, cheaper models (like Gemini 2.0 Flash or GPT-3.5) for everyday tasks, and reserve expensive models (like GPT-4 or Claude 3.5 Sonnet) for important work.

- **Keyboard shortcuts**: Use browser navigation (Back/Forward) -- the dashboard uses SPA routing for instant page transitions without full reloads.

- **Session security**: Review active sessions periodically under **Account > Security** and revoke any you do not recognize.

- **Export your data**: Use the CSV export feature in the usage dashboard to keep records of your AI usage for expense tracking or reporting.

---

## Need Help?

- **Email support**: support@unicorncommander.com
- **Documentation portal**: https://unicorncommander.ai/docs
- **API guides**: Available under the documentation portal

**For billing or subscription issues:**
- Include your account email address
- Include the invoice number (if applicable)
- Describe the issue clearly

**Response Times by Tier:**

| Tier | Response Time |
|------|--------------|
| Trial / Starter | 24-48 hours |
| Professional | 12-24 hours |
| Enterprise | 1-4 hours (priority support) |

**For app access issues:**
Contact your organization administrator for tier upgrades or app access grants.

---

**Last Updated:** February 22, 2026
**Version:** 1.0.0
