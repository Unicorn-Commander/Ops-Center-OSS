# Getting Started with Billing

**Welcome to Ops-Center Billing!**

This guide will help you understand how billing works, how to view your credits, manage your subscription, and make the most of your account.

---

## Table of Contents

1. [Understanding Credits](#understanding-credits)
2. [Viewing Your Credit Balance](#viewing-your-credit-balance)
3. [Subscription Tiers](#subscription-tiers)
4. [Managing Your Subscription](#managing-your-subscription)
5. [Understanding BYOK (Bring Your Own Key)](#understanding-byok)
6. [Viewing Invoices](#viewing-invoices)
7. [FAQ](#faq)

---

## Understanding Credits

### What are Credits?

**Credits are the currency of Ops-Center.** Everything you do that consumes resources (AI model inference, API calls, etc.) costs credits.

**Key Points:**
- **1 credit ≈ $0.001** (approximately 1/10th of a cent)
- Credits are **usage quotas**, not real money
- Credits reset **monthly** on your subscription anniversary date
- Unused credits **do not roll over** (use them or lose them!)

### Example: What Do Credits Buy?

| Service | Model | Cost per Request |
|---------|-------|------------------|
| LLM Chat | GPT-4 (10k tokens) | ~50 credits |
| LLM Chat | Claude 3.5 Sonnet (10k tokens) | ~55 credits |
| Image Generation | DALL-E 3 (1024x1024) | ~48 credits |
| Image Generation | Stable Diffusion XL | ~6 credits |
| Embedding | text-embedding-ada-002 (1M tokens) | ~10 credits |

**Professional Tier (10,000 credits/month):**
- ~200 GPT-4 conversations (50 messages each)
- ~200 images with DALL-E 3
- ~1,600 images with Stable Diffusion XL

**Tip:** Mix and match! Use expensive models for important tasks, cheaper models for everyday use.

---

## Viewing Your Credit Balance

### Step 1: Login

1. Go to https://your-domain.com
2. Click **Login** in the top right
3. Authenticate via Keycloak SSO (Google, GitHub, Microsoft, or email)

### Step 2: Access Credit Dashboard

Once logged in:

**Option A: Navigation Menu**
1. Click **Credits** in the left sidebar
2. View your credit balance on the dashboard

**Option B: Direct URL**
- Go to https://your-domain.com/admin/credits

### Step 3: Understanding the Dashboard

Your credit dashboard shows:

**Credit Balance Card:**
```
┌─────────────────────────────────────┐
│ Current Balance: 9,850 credits     │
│ Monthly Allocation: 10,000 credits │
│ Bonus Credits: 0 credits           │
│ Next Reset: Feb 1, 2025            │
└─────────────────────────────────────┘
```

**What Each Field Means:**

- **Current Balance** - Credits available right now
- **Monthly Allocation** - Credits you receive each month
- **Bonus Credits** - Promotional credits (don't expire on reset)
- **Next Reset** - When your credits replenish

**Progress Bar:**
- Shows usage: 🟩🟩🟩⬜⬜⬜⬜⬜⬜⬜ (15% used)

---

## Subscription Tiers

### Available Plans

#### 🆓 Trial - $1.00/week
**Best for: Testing the platform**

- **Credits:** 700 credits/week (100/day)
- **Duration:** 7 days
- **Features:**
  - ✅ Open-WebUI access
  - ✅ Basic AI models
  - ✅ Community support
  - ❌ Advanced features
  - ❌ BYOK support

**Use Case:** Trying out the platform before committing.

---

#### 🚀 Starter - $19/month
**Best for: Individual developers**

- **Credits:** 1,000 credits/month
- **Features:**
  - ✅ All AI models
  - ✅ Open-WebUI + Center-Deep search
  - ✅ BYOK support (save money!)
  - ✅ Email support
  - ❌ Team management
  - ❌ Priority support

**Use Case:** Personal projects, learning, experimentation.

---

#### ⭐ Professional - $49/month (Most Popular)
**Best for: Professionals and small teams**

- **Credits:** 10,000 credits/month
- **Features:**
  - ✅ All services (Chat, Search, TTS, STT)
  - ✅ BYOK support
  - ✅ Billing dashboard
  - ✅ Priority email support
  - ✅ Usage analytics
  - ❌ White-label options

**Use Case:** Production applications, consulting work, small businesses.

**Why Popular?**
- **10x more credits** than Starter for 2.5x the price
- Best value for active users
- Sufficient for most production use cases

---

#### 🏢 Enterprise - $99/month
**Best for: Teams and organizations**

- **Credits:** Unlimited
- **Features:**
  - ✅ Team management (5 seats)
  - ✅ Custom integrations
  - ✅ 24/7 dedicated support
  - ✅ White-label options
  - ✅ Custom SLAs
  - ✅ Dedicated account manager

**Use Case:** Large-scale applications, enterprise deployments, agencies.

**Why Enterprise?**
- No credit limits (truly unlimited usage)
- Support for multiple team members
- Custom features and integrations

---

### Comparing Plans

| Feature | Trial | Starter | Professional | Enterprise |
|---------|-------|---------|--------------|------------|
| **Price** | $1/week | $19/mo | $49/mo | $99/mo |
| **Credits** | 700/week | 1,000/mo | 10,000/mo | Unlimited |
| **BYOK** | ❌ | ✅ | ✅ | ✅ |
| **Priority Support** | ❌ | ❌ | ✅ | ✅ |
| **Team Seats** | 1 | 1 | 1 | 5 |
| **Custom Features** | ❌ | ❌ | ❌ | ✅ |

---

## Managing Your Subscription

### Upgrading Your Plan

#### Step 1: View Plans

1. Go to **Subscription** → **Plan** in the sidebar
2. Click **View Plans** button
3. Compare features and pricing

#### Step 2: Select New Plan

1. Click **Upgrade to Professional** (or your chosen plan)
2. Review the upgrade preview:
   ```
   Current Plan: Starter ($19/month)
   New Plan: Professional ($49/month)
   Proration: $15.00 (for remaining 15 days)
   Next Billing: Feb 1, 2025 at $49/month
   ```

#### Step 3: Complete Payment

1. Click **Proceed to Checkout**
2. You'll be redirected to **Stripe Checkout**
3. Enter payment details:
   - **Card Number**
   - **Expiration Date**
   - **CVC**
   - **Billing Address**
4. Click **Subscribe**

#### Step 4: Confirmation

- You'll be redirected back to Ops-Center
- Your credits will be **immediately updated**
- You'll receive an email confirmation

**What Happens Next?**
- ✅ Credits allocated instantly (10,000 for Professional)
- ✅ Access to all features unlocked
- ✅ First charge is prorated for current month
- ✅ Full $49/month starts next billing cycle

---

### Downgrading Your Plan

**Important:** Downgrades take effect at the **end of your billing period**.

#### Step 1: Request Downgrade

1. Go to **Subscription** → **Plan**
2. Click **Change Plan**
3. Select lower tier (e.g., Professional → Starter)

#### Step 2: Review Changes

```
Current Plan: Professional ($49/month)
New Plan: Starter ($19/month)
Effective Date: Jan 31, 2025 (end of current period)
You'll keep Professional access until: Jan 31, 2025
```

#### Step 3: Confirm

1. Click **Schedule Downgrade**
2. Confirm by typing the plan name
3. You'll receive a confirmation email

**What Happens?**
- ✅ Continue to use Professional until Jan 31
- ✅ Credits remain available until reset
- ⏰ Downgrade activates Feb 1
- 💰 Next invoice will be $19 instead of $49

---

### Canceling Your Subscription

#### Step 1: Cancel

1. Go to **Subscription** → **Plan**
2. Scroll to bottom
3. Click **Cancel Subscription** button
4. Confirm cancellation

#### Step 2: What Happens

- ✅ Access continues until **end of billing period**
- ✅ Credits remain available until period ends
- ❌ Subscription will **not renew** next month
- ❌ Credits will **expire** at period end

**Example:**
```
Subscription Canceled: Jan 15, 2025
Access Until: Jan 31, 2025
Next Billing: None (subscription ended)
```

#### Step 3: Reactivating

To reactivate:
1. Visit **Subscription** → **Plan**
2. Click **Reactivate Subscription**
3. Your previous plan will resume immediately

---

## Understanding BYOK (Bring Your Own Key)

### What is BYOK?

**BYOK = Bring Your Own Key**

Instead of using Ops-Center's managed AI models (which cost credits), you can **use your own API keys** from:

- **OpenRouter** - 300+ models, best value
- **OpenAI** - GPT-4, GPT-3.5, DALL-E
- **Anthropic** - Claude 3.5 Sonnet, Haiku, Opus
- **HuggingFace** - Open source models

### Why Use BYOK?

**💰 Cost Savings:**
- **Managed Tier**: 10,000 tokens = 50 credits (~$0.05)
- **BYOK Tier**: 10,000 tokens = 5 credits (~$0.005) + provider cost
- **Savings**: Up to 90% on credit costs!

**🔑 Your Keys, Your Control:**
- Keep your own API keys
- Track usage directly with providers
- No platform markup on provider costs
- Only pay minimal Ops-Center fee (5-10%)

### How to Set Up BYOK

#### Step 1: Get Provider API Key

**Option A: OpenRouter (Recommended)**
1. Go to https://openrouter.ai
2. Sign up for free account
3. Get $5 in free credits
4. Copy your API key

**Option B: OpenAI**
1. Go to https://platform.openai.com
2. Sign up and add payment method
3. Navigate to **API Keys**
4. Click **Create new secret key**
5. Copy the key (starts with `sk-`)

#### Step 2: Add to Ops-Center

1. Go to **Settings** → **BYOK Providers**
2. Click **Add Provider**
3. Select **OpenRouter** (or other provider)
4. Paste your API key
5. Click **Save**

#### Step 3: Verify

```
✅ OpenRouter Connected
   - Key: sk-or-v1-***************
   - Balance: $4.85 remaining
   - Status: Active
```

#### Step 4: Use It!

When making AI requests:
1. Models with 🔑 icon use BYOK (much cheaper!)
2. Models without icon use managed tier (costs more credits)

**Cost Comparison in UI:**
```
Model: anthropic/claude-3-5-sonnet
┌─────────────────────────────────────────┐
│ BYOK: 5 credits + provider cost        │
│ Managed: 55 credits                     │
│ 💰 You save: 50 credits per request     │
└─────────────────────────────────────────┘
```

---

## Viewing Invoices

### Access Invoice History

1. Go to **Billing** → **Invoices** in sidebar
2. View list of all invoices

### Invoice List

```
┌─────────────────────────────────────────────────────────┐
│ Invoice #     │ Date       │ Amount  │ Status  │ PDF   │
├───────────────┼────────────┼─────────┼─────────┼───────┤
│ INV-2025-001  │ Jan 1, 25  │ $49.00  │ Paid    │ ⬇️    │
│ INV-2024-012  │ Dec 1, 24  │ $49.00  │ Paid    │ ⬇️    │
│ INV-2024-011  │ Nov 1, 24  │ $49.00  │ Paid    │ ⬇️    │
│ INV-2024-010  │ Oct 1, 24  │ $19.00  │ Paid    │ ⬇️    │
└─────────────────────────────────────────────────────────┘
```

### Download Invoice PDF

1. Click the ⬇️ (download) icon
2. PDF will open in new tab
3. Save to your computer

**Invoice includes:**
- Invoice number and date
- Billing period
- Itemized charges
- Payment status
- Payment method
- Company details (for tax purposes)

---

## FAQ

### Credits & Usage

**Q: What happens to unused credits at month end?**

A: Unused credits **expire and do not roll over**. Your balance resets to your monthly allocation on your subscription anniversary date.

**Exception:** Bonus credits from promotions do not expire on reset.

---

**Q: Can I buy extra credits?**

A: Not yet, but credit packages are coming soon! For now, you can:
1. Upgrade to a higher tier for more monthly credits
2. Use BYOK to reduce credit consumption

---

**Q: How do I know when I'm running low on credits?**

A: You'll receive email notifications at:
- **75% used** - Warning
- **90% used** - Urgent warning
- **100% used** - Out of credits

You can also check your balance anytime in the **Credits** dashboard.

---

**Q: What happens if I run out of credits?**

A: Your API requests will be **rate-limited** or **rejected** until:
1. Your credits reset (at start of next billing period)
2. You upgrade to a higher tier
3. You enable BYOK (uses your provider keys instead)

---

### Subscriptions

**Q: Can I change plans mid-month?**

A: **Yes!**
- **Upgrades** - Effective immediately, you're charged prorated amount
- **Downgrades** - Scheduled for end of billing period

---

**Q: What happens if my payment fails?**

A: If payment fails:
1. You'll receive email notification
2. We'll retry payment in 3 days
3. If still failing, your subscription will be **suspended**
4. You'll have **grace period** of 7 days to update payment

During suspension:
- ❌ API access blocked
- ❌ Credits frozen
- ✅ Account data preserved
- ✅ Can update payment method

---

**Q: How do I update my payment method?**

A: Currently managed through Stripe:
1. Check your email for Stripe customer portal link
2. Or contact support@magicunicorn.tech

**Coming Soon:** Self-service payment method management in dashboard.

---

**Q: Can I get a refund?**

A: Refunds are handled case-by-case. Contact support@magicunicorn.tech with:
- Your account email
- Invoice number
- Reason for refund request

We typically approve refunds for:
- ✅ Service outages
- ✅ Billing errors
- ✅ Duplicate charges
- ❌ Unused credits (credits don't roll over)

---

### BYOK (Bring Your Own Key)

**Q: Does BYOK cost credits?**

A: **Yes, but much less!** BYOK charges a small markup (5-10%) for platform infrastructure:

```
Example: 10,000 token Claude request
- Provider cost: $0.003 (OpenRouter)
- Platform markup: $0.0003 (10%)
- Total: $0.0033 (3.3 credits)

vs. Managed Tier: $0.055 (55 credits)
Savings: 94%!
```

---

**Q: Which BYOK provider should I use?**

A: **Recommendations:**

**Best Overall: OpenRouter**
- ✅ 300+ models in one API
- ✅ Cheapest prices (aggregates providers)
- ✅ $5 free credits
- ✅ No commitment required

**Best for OpenAI models: OpenAI Direct**
- ✅ Direct access to GPT-4, GPT-3.5
- ✅ Fastest response times
- ❌ No free tier
- ❌ Requires payment method

**Best for Open Source: HuggingFace**
- ✅ Thousands of open source models
- ✅ Many free models
- ❌ More complex setup
- ❌ Variable quality

---

**Q: Can I use multiple BYOK providers?**

A: **Yes!** You can add keys for:
- OpenRouter
- OpenAI
- Anthropic
- HuggingFace
- And more

The system will automatically use the cheapest provider for each request.

---

**Q: Is my API key secure?**

A: **Yes!** Your API keys are:
- ✅ Encrypted at rest (AES-256)
- ✅ Never stored in plaintext
- ✅ Never logged or displayed
- ✅ Only used for your requests
- ✅ Can be deleted anytime

---

### Billing & Invoices

**Q: When will I be charged?**

A: Charges occur on your **subscription anniversary date**:

```
Example:
- Signed up: Jan 15, 2025
- First charge: Jan 15, 2025 ($49)
- Next charge: Feb 15, 2025 ($49)
- Subsequent charges: 15th of each month
```

---

**Q: What payment methods do you accept?**

A: We accept all major payment methods via Stripe:
- ✅ Credit cards (Visa, Mastercard, Amex, Discover)
- ✅ Debit cards
- ✅ Apple Pay
- ✅ Google Pay
- ✅ Bank transfers (Enterprise only)

---

**Q: Do you offer annual billing?**

A: **Coming soon!** Annual billing with discounts:
- Starter: $190/year (save $38, 17% off)
- Professional: $490/year (save $98, 17% off)
- Enterprise: $990/year (save $198, 17% off)

---

**Q: Can I get a receipt for tax purposes?**

A: Yes! Every invoice includes:
- Invoice number
- Company details
- Tax information (if applicable)
- Itemized charges

Download PDF from **Billing** → **Invoices**.

---

## Need Help?

**📧 Email Support:** support@magicunicorn.tech
**📚 Documentation:** https://your-domain.com/docs
**💬 Community:** https://discord.gg/unicorncommander

**For Billing Issues:**
- Include your account email
- Include invoice number (if applicable)
- Describe the issue clearly

**Response Times:**
- **Trial/Starter:** 24-48 hours
- **Professional:** 12-24 hours
- **Enterprise:** 1-4 hours (priority support)

---

**Last Updated:** November 12, 2025
**Version:** 1.0.0
