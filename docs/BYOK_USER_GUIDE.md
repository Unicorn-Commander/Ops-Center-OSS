# 🔑 BYOK User Guide - Bring Your Own Key

**Last Updated**: October 26, 2025
**Version**: 2.0
**Status**: Production Ready

---

## 📖 Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Supported Providers](#supported-providers)
4. [Cost Comparison](#cost-comparison)
5. [How BYOK Works](#how-byok-works)
6. [Adding Your First Key](#adding-your-first-key)
7. [Managing Keys](#managing-keys)
8. [Security & Privacy](#security--privacy)
9. [Service Integration](#service-integration)
10. [Usage & Billing](#usage--billing)
11. [Troubleshooting](#troubleshooting)
12. [Best Practices](#best-practices)
13. [FAQ](#faq)
14. [Appendix](#appendix)

---

## Introduction

### What is BYOK?

**BYOK (Bring Your Own Key)** allows you to use your own API keys from LLM providers instead of consuming platform credits. When you add your API key to UC-Cloud, all AI requests automatically use **your key** instead of the system key—meaning **you pay the provider directly** with no platform markup.

### Why Use BYOK?

✅ **Cost Savings**: No platform markup on API calls
✅ **Universal Access**: One OpenRouter key gives you 348 models
✅ **Direct Billing**: Pay providers directly at wholesale rates
✅ **Free Models**: Access 60+ free models through OpenRouter
✅ **Transparency**: See exactly what you're paying
✅ **Control**: Choose your provider and model preferences

### How Much Can You Save?

**Example: 100 million tokens per month**

| Setup | Cost | Savings |
|-------|------|---------|
| **Platform Credits** | $3,000 + 15% markup = **$3,450** | - |
| **BYOK (OpenRouter)** | $3,000 direct | **Save $450/month** |
| **BYOK (Free Models)** | $0 | **Save $3,450/month** |

**Annual Savings**: Up to **$41,400** by using BYOK with free models!

---

## Quick Start

### Get Started in 3 Steps

#### Step 1: Get an API Key

Choose your provider and create an API key:

- **OpenRouter** (Recommended): https://openrouter.ai/keys
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/settings/keys
- **Google**: https://makersuite.google.com/app/apikey

#### Step 2: Add Key in Ops-Center

1. Navigate to **Account Settings → API Keys**
2. Click **"Add API Key"**
3. Select your provider
4. Paste your API key
5. Click **"Test"** to verify
6. Click **"Save"**

#### Step 3: Verify It's Working

After adding your key, all AI requests will use your key automatically. You'll see:

- ✅ **Connected** status in API Keys section
- 💬 Chat responses using your provider
- 📊 Usage statistics in your provider's dashboard
- 💰 **No platform credits deducted**

---

## Supported Providers

### OpenRouter (⭐ Recommended)

**Access**: 348 models from 20+ providers
**Cost**: $0.10-$150 per 1M tokens (varies by model)
**Free Models**: 60+ free models available
**Get Key**: https://openrouter.ai/keys

**Best For**:
- Universal access to all models
- Cost optimization (free models)
- One key for everything
- Simplified billing

**Key Format**: `sk-or-v1-{64 characters}`

**Example Free Models**:
- `meta-llama/llama-3.1-8b-instruct:free`
- `deepseek/deepseek-r1:free`
- `google/gemini-2.0-flash-exp:free`
- `mistralai/mistral-7b-instruct:free`

**Pricing Examples**:
| Model | Cost per 1M Tokens | Free Tier |
|-------|-------------------|-----------|
| Llama 3.1 8B | $0 | ✅ Free |
| DeepSeek R1 | $0 | ✅ Free |
| GPT-4o | $2.50-$7.50 | ❌ Paid |
| Claude 3.5 Sonnet | $3.00-$15.00 | ❌ Paid |

---

### OpenAI

**Access**: 15 models (GPT-4, GPT-4o, o1, o3, etc.)
**Cost**: $0.15-$60 per 1M tokens
**Get Key**: https://platform.openai.com/api-keys

**Best For**:
- Latest GPT models
- Direct OpenAI access
- Advanced reasoning (o1/o3)

**Key Format**: `sk-{48+ characters}`

**Pricing Examples**:
| Model | Prompt Cost | Completion Cost |
|-------|-------------|----------------|
| GPT-4o | $2.50/1M | $10.00/1M |
| GPT-4 Turbo | $10.00/1M | $30.00/1M |
| GPT-3.5 Turbo | $0.50/1M | $1.50/1M |
| o1-preview | $15.00/1M | $60.00/1M |

---

### Anthropic

**Access**: 8 models (Claude 3, Claude 3.5, Claude 4)
**Cost**: $3-$75 per 1M tokens
**Get Key**: https://console.anthropic.com/settings/keys

**Best For**:
- Claude-specific workflows
- Long context windows (200K tokens)
- High-quality reasoning

**Key Format**: `sk-ant-{95+ characters}`

**Pricing Examples**:
| Model | Prompt Cost | Completion Cost |
|-------|-------------|----------------|
| Claude 3.5 Sonnet | $3.00/1M | $15.00/1M |
| Claude 3 Opus | $15.00/1M | $75.00/1M |
| Claude 3 Haiku | $0.25/1M | $1.25/1M |

---

### Google

**Access**: 5 models (Gemini Pro, Gemini Flash, etc.)
**Cost**: Free tier available, $0.075-$30 per 1M tokens
**Get Key**: https://makersuite.google.com/app/apikey

**Best For**:
- Free AI access (Gemini Flash)
- Multimodal capabilities
- Low-cost inference

**Key Format**: `{39 characters}`

**Pricing Examples**:
| Model | Prompt Cost | Completion Cost | Free Tier |
|-------|-------------|----------------|-----------|
| Gemini 2.0 Flash | $0.075/1M | $0.30/1M | 1,500 req/day |
| Gemini 1.5 Pro | $1.25/1M | $5.00/1M | 50 req/day |
| Gemini 1.5 Flash | $0.075/1M | $0.30/1M | 1,500 req/day |

---

## Cost Comparison

### Credits vs. BYOK

**Platform Credits** (System Key):
- UC-Cloud manages the API key
- Credits deducted from your account
- Platform adds markup for infrastructure
- Simple billing (one invoice)

**BYOK** (Your Key):
- You manage your own API key
- You pay provider directly
- **No platform markup** (0% markup)
- Separate invoice from provider

### Monthly Savings Calculation

**Scenario**: Professional tier user, 100M tokens/month

| Usage | Credits Cost | BYOK Cost | Savings |
|-------|-------------|-----------|---------|
| **10M tokens** | $30 + 5% = **$31.50** | $30.00 | **$1.50/mo** |
| **100M tokens** | $300 + 5% = **$315** | $300.00 | **$15/mo** |
| **1B tokens** | $3,000 + 5% = **$3,150** | $3,000 | **$150/mo** |

**Annual Savings**: $18 - $1,800/year depending on usage!

### OpenRouter Free Models Savings

**Scenario**: Using only free models via OpenRouter BYOK

| Usage | Credits Cost | BYOK Cost | Savings |
|-------|-------------|-----------|---------|
| **10M tokens** | $30 | **$0** | **$30/mo** |
| **100M tokens** | $300 | **$0** | **$300/mo** |
| **1B tokens** | $3,000 | **$0** | **$3,000/mo** |

**Annual Savings**: $360 - $36,000/year with free models! 🎉

---

## How BYOK Works

### Routing Logic

When you make an LLM request, UC-Cloud follows this priority:

```
1. Check if user has OpenRouter BYOK configured
   └─→ YES: Use OpenRouter key for ALL models (348 models)
   └─→ NO: Continue to step 2

2. Check if model provider matches user's BYOK provider
   └─→ YES: Use provider-specific key (e.g., OpenAI key for GPT-4)
   └─→ NO: Continue to step 3

3. Use system key (platform credits charged)
```

### Flow Diagram

```
┌──────────────────────────────────────────────────────────┐
│ User Makes AI Request                                     │
│ (Chat, Agent, API call)                                  │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ UC-Cloud Routing Engine                                   │
│ • Extracts user ID from session                          │
│ • Looks up BYOK configuration                            │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
           ┌─────────┴─────────┐
           │ Has OpenRouter    │
           │ BYOK?             │
           └─────────┬─────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
        YES                     NO
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ Use OpenRouter  │     │ Check Provider  │
│ Key             │     │ Match           │
│ (348 models)    │     │                 │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │              ┌────────┴────────┐
         │              │ Provider Match? │
         │              └────────┬────────┘
         │                       │
         │              ┌────────┴────────┐
         │              │                 │
         │             YES               NO
         │              │                 │
         │              ▼                 ▼
         │      ┌───────────────┐ ┌──────────────┐
         │      │ Use Provider  │ │ Use System   │
         │      │ Key           │ │ Key          │
         │      │ (No credits)  │ │ (Credits)    │
         │      └───────┬───────┘ └──────┬───────┘
         │              │                 │
         └──────────────┴─────────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │ Call LLM Provider API         │
         │ • OpenRouter / OpenAI / etc. │
         │ • Using selected API key     │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │ Return Response to User       │
         │ • Chat message / Agent result│
         │ • Metadata: using_byok=true  │
         └──────────────────────────────┘
```

### Example Scenarios

**Scenario 1: OpenRouter BYOK**
- User has OpenRouter key configured
- Requests `openai/gpt-4`
- **Result**: Uses OpenRouter key, no credits charged ✅

**Scenario 2: Provider-Specific BYOK**
- User has OpenAI key (no OpenRouter)
- Requests `gpt-4`
- **Result**: Uses OpenAI key, no credits charged ✅

**Scenario 3: No BYOK**
- User has no keys configured
- Requests `gpt-4`
- **Result**: Uses system key, credits charged ⚠️

**Scenario 4: Mixed**
- User has Anthropic key (no OpenRouter)
- Requests `gpt-4` (OpenAI model)
- **Result**: Uses system key, credits charged ⚠️
- **Tip**: Add OpenRouter key for universal coverage! 💡

---

## Adding Your First Key

### Step-by-Step Tutorial

#### 1. Navigate to API Keys

- **URL**: https://unicorncommander.ai/admin/account/api-keys
- **Menu**: Account Settings → API Keys
- **Description**: You'll see a list of your configured API keys (empty if first time)

#### 2. Click "Add API Key"

- **Button**: Top-right corner, blue button with "+" icon
- **Action**: Opens the "Add API Key" modal

#### 3. Select Provider

- **Dropdown**: Choose from 4 providers:
  - ⭐ OpenRouter (Recommended)
  - OpenAI
  - Anthropic
  - Google

**Tip**: Start with OpenRouter for access to all 348 models! 💡

#### 4. Enter API Key

- **Field**: Large text input labeled "API Key"
- **Format**: Paste your full API key (don't remove prefix)
  - OpenRouter: `sk-or-v1-abc123...`
  - OpenAI: `sk-proj-abc123...`
  - Anthropic: `sk-ant-abc123...`
  - Google: `AIza...`

**⚠️ Warning**: Never share your API key publicly! This field is encrypted in transit (HTTPS) and at rest (Fernet encryption).

#### 5. Add Label (Optional)

- **Field**: Text input labeled "Label"
- **Purpose**: Name your key for easy identification
- **Examples**: "Production Key", "Personal OpenRouter", "Work Account"

#### 6. Click "Test"

- **Button**: Blue "Test" button next to API key field
- **Action**: Validates your API key with the provider
- **Response**:
  - ✅ **Success**: "API key is valid! Model: gpt-4, Balance: $50.00"
  - ❌ **Error**: "Invalid API key. Please check and try again."

**Tip**: Always test before saving to catch typos! 💡

#### 7. Click "Save"

- **Button**: Green "Save" button at bottom-right
- **Action**: Encrypts and stores your API key
- **Confirmation**: "API key added successfully!" toast notification
- **Status**: Key appears in list with "✅ Connected" badge

---

## Managing Keys

### View All Keys

**URL**: https://unicorncommander.ai/admin/account/api-keys

**Displays**:
- Provider icon and name
- Key label
- Masked key (e.g., `sk-or-v1-abc...xyz`)
- Status badge (✅ Connected / ⚠️ Error / 🔌 Disabled)
- Last tested timestamp
- Actions (Test / Edit / Disable / Delete)

### Enable/Disable Keys

**Purpose**: Temporarily disable a key without deleting it

**Steps**:
1. Find the key in the list
2. Click the toggle switch on the right
3. **Enabled** (green): Key is active and used for requests
4. **Disabled** (gray): Key is inactive, system key used instead

**Use Case**: Test different providers by toggling keys on/off

### Test Connection

**Purpose**: Verify your API key is still valid

**Steps**:
1. Find the key in the list
2. Click the **"Test"** button
3. Wait for validation (2-5 seconds)
4. **Success**: Status updates to "✅ Connected"
5. **Error**: Status shows "⚠️ Invalid Key" with error message

**Recommended**: Test keys monthly to catch expired/revoked keys

### Remove Keys

**Purpose**: Permanently delete an API key from UC-Cloud

**Steps**:
1. Find the key in the list
2. Click the **"Delete"** button (trash icon)
3. Confirm deletion in the popup
4. Key is permanently removed (cannot be recovered)

**⚠️ Warning**: After deletion, requests will use system key (credits charged)

### View Usage Stats

**Coming Soon**: Individual key usage statistics

**Planned Features**:
- Total requests per key
- Total tokens consumed
- Total cost (estimated)
- Usage over time (chart)
- Most-used models

---

## Security & Privacy

### Encryption

**Algorithm**: Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256)

**How It Works**:
1. You enter your API key in the browser
2. Transmitted over HTTPS (encrypted in transit)
3. Backend encrypts key using Fernet algorithm
4. Encrypted key stored in database
5. Only decrypted when making API calls
6. Never logged or displayed in plaintext

**Encryption Key**: Stored securely in environment variables (not in code)

### Storage

**Database**: PostgreSQL (unicorn_db)
**Table**: `user_api_keys` (or Keycloak user attributes for OpenRouter)
**Access**: Only you can access your keys (user-level isolation)
**Backup**: Keys backed up with encrypted database backups

### Transmission

**HTTPS**: All API calls use SSL/TLS encryption
**Key Decryption**: Keys only decrypted in-memory for API requests
**No Logging**: Decrypted keys never written to logs

### Audit Logging

**Events Logged**:
- ✅ API key added
- ✅ API key tested
- ✅ API key enabled/disabled
- ✅ API key deleted
- ✅ API key used for request

**Log Location**: System audit logs (admin access only)

**What's NOT Logged**:
- ❌ Decrypted API keys
- ❌ Full API keys (only masked versions)

### Deletion

**Permanent Removal**: When you delete a key, it's permanently removed from the database (cannot be recovered)

**No Retention**: Deleted keys are not retained or archived

**Immediate Effect**: After deletion, system key is used immediately (no grace period)

---

## Service Integration

### Which Services Use BYOK?

| Service | BYOK Support | Description |
|---------|-------------|-------------|
| **Open-WebUI** | ✅ Full | Direct model chat uses your keys |
| **Brigade** | ✅ Full | Agent conversations use your keys |
| **Ops-Center LLM API** | ✅ Full | Any service calling `/api/v1/llm/*` |
| **Center-Deep** | 🔄 Partial | AI-enhanced search (coming soon) |

### Open-WebUI Integration

**How It Works**:
1. You chat in Open-WebUI
2. Open-WebUI calls Ops-Center LLM API
3. Ops-Center checks for your BYOK
4. If found, routes request with your key
5. Response returned to Open-WebUI

**Transparent**: No configuration needed in Open-WebUI—just add your key in Ops-Center!

### Brigade Integration

**How It Works**:
1. You interact with a Brigade agent
2. Brigade calls Ops-Center LLM API
3. Ops-Center passes your API key config
4. Brigade uses your key for agent LLM calls
5. Results returned to you

**Multi-Agent**: If agent spawns sub-agents, they all use your key!

### API Integration

**Endpoint**: `POST /api/v1/llm/chat/completions`

**Example Request**:
```bash
curl -X POST https://unicorncommander.ai/api/v1/llm/chat/completions \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4",
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ]
  }'
```

**Response Metadata**:
```json
{
  "id": "chatcmpl-abc123",
  "model": "openai/gpt-4",
  "choices": [...],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  },
  "x-using-byok": "true",
  "x-provider": "openrouter",
  "x-credits-charged": "0.00"
}
```

**Indicators**:
- `x-using-byok: true` = Your key was used ✅
- `x-using-byok: false` = System key was used (credits charged) ⚠️

---

## Usage & Billing

### With BYOK

**What You Pay**:
- Provider invoice (OpenRouter, OpenAI, etc.)
- Direct wholesale rates
- **No platform markup** (0%)

**What's Free**:
- UC-Cloud platform access
- All services (Open-WebUI, Brigade, etc.)
- No per-request fees

**Example**:
- You use 100M tokens on OpenAI GPT-4
- OpenAI charges you $250 (prompt) + $1,000 (completion) = **$1,250**
- UC-Cloud charges you **$0** (no markup with BYOK)
- **Total**: $1,250 (vs. $1,312.50 with credits + 5% markup)

### Without BYOK

**What You Pay**:
- Platform credits (prepaid or monthly subscription)
- Credits deducted per request
- Platform markup (0-15% based on tier)

**Example**:
- You use 100M tokens on GPT-4
- Base cost: $1,250
- Professional tier markup: 5%
- **Total**: $1,250 + $62.50 = **$1,312.50**

### Mixed Mode

**Flexibility**: You can use both BYOK and credits!

**Scenarios**:
1. **OpenRouter BYOK** for most requests → Free/cheap models
2. **Credits** for premium models not on OpenRouter
3. **Multiple Provider Keys** for specific use cases

**Billing**:
- BYOK requests: Provider invoices
- Credit requests: UC-Cloud subscription invoice
- All tracked separately in usage dashboard

### Organization Sharing (Enterprise Only)

**Enterprise Feature**: Share BYOK keys across your team

**How It Works**:
1. Organization admin adds API key
2. Key is shared with all org members
3. All members' requests use the org key
4. Centralized billing through org account

**Benefits**:
- One invoice for entire team
- Centralized cost tracking
- Simplified key management
- Team usage analytics

**Setup**: Contact support to enable organization BYOK

---

## Troubleshooting

### Key Not Working

**Symptoms**:
- Status shows "⚠️ Error"
- Requests still charge credits
- "Invalid API key" errors in logs

**Solutions**:

#### 1. Check Key Format
```
✅ Correct: sk-or-v1-1234567890abcdef...
❌ Wrong: sk-or-v1-1234567890abcdef... (extra spaces)
❌ Wrong: 1234567890abcdef... (missing prefix)
```

#### 2. Verify Key is Active
- Login to provider dashboard
- Check if key exists and is enabled
- Verify key hasn't been revoked or expired

#### 3. Test Connection
- Click "Test" button in Ops-Center
- Check error message for details
- Common errors:
  - "Invalid API key" → Key is wrong/expired
  - "Insufficient credits" → Add credits to provider account
  - "Rate limit exceeded" → Wait 60s and retry

#### 4. Check Key Permissions
- Some providers require specific permissions
- OpenRouter: No special permissions needed
- OpenAI: Ensure key has "API" permission
- Anthropic: Ensure key has "Claude API" access

### Still Being Charged Credits

**Symptoms**:
- BYOK key is connected
- Credits still being deducted
- `x-using-byok: false` in API responses

**Solutions**:

#### 1. Verify Key is Enabled
- Go to API Keys page
- Check toggle switch is ON (green)
- If OFF (gray), toggle it ON

#### 2. Check Provider Matches Model
```
✅ Works: OpenRouter key + ANY model
✅ Works: OpenAI key + gpt-4
❌ Doesn't Work: OpenAI key + claude-3-sonnet (wrong provider)
```

**Fix**: Add OpenRouter key for universal coverage, or add Anthropic key

#### 3. View Response Metadata
```bash
# Check x-using-byok header
curl -i https://unicorncommander.ai/api/v1/llm/chat/completions ...

# If x-using-byok: false, check logs:
docker logs ops-center-direct | grep "User {your-email}"
```

#### 4. Clear Cache
```bash
# Sometimes cached routing rules need refresh
# Logout and login again
# Or wait 5 minutes for cache to expire
```

### Invalid API Key Error

**Symptoms**:
- Test button shows "Invalid API key"
- Key worked before but stopped working
- Provider dashboard shows key is valid

**Solutions**:

#### 1. Re-enter Key
- Copy key from provider dashboard
- Delete old key in Ops-Center
- Add new key (paste carefully)
- Test again

#### 2. Check for Spaces
```
# Keys often have hidden spaces when copied
# Before: "sk-or-v1-abc123 "
# After:  "sk-or-v1-abc123"
```

#### 3. Generate New Key
- Go to provider dashboard
- Revoke old key
- Generate new key
- Add new key to Ops-Center

#### 4. Check Account Status
- Provider account must be active
- Payment method must be valid
- No outstanding invoices
- Account not suspended

### Rate Limit Errors

**Symptoms**:
- "Rate limit exceeded" error
- 429 HTTP status code
- Requests slow or timing out

**Solutions**:

#### 1. Wait and Retry
- Most rate limits reset after 60 seconds
- Wait 1-2 minutes and try again

#### 2. Check Provider Limits
- OpenRouter: 200 requests/minute (free tier)
- OpenAI: 500 requests/minute (tier 1)
- Anthropic: 1,000 requests/minute (tier 1)

#### 3. Upgrade Provider Tier
- Paid tiers have higher rate limits
- OpenRouter: Up to 10,000 req/min (paid)
- OpenAI: Up to 10,000 req/min (tier 5)

#### 4. Use Multiple Keys
- Add keys from different providers
- Distribute requests across providers
- Automatic failover (coming soon)

---

## Best Practices

### 🥇 Start with OpenRouter

**Why OpenRouter First?**
- ✅ Access to 348 models with one key
- ✅ 60+ free models (save money)
- ✅ No provider lock-in
- ✅ Simplified billing
- ✅ Best cost optimization

**How to Get Started**:
1. Sign up at https://openrouter.ai
2. Add payment method (required for free credits)
3. Generate API key
4. Add to UC-Cloud
5. Start using any of 348 models!

### 🧪 Test Before Saving

**Always Test**:
- Click "Test" button after entering key
- Verify success message before saving
- Catch typos and invalid keys early
- Confirm provider credentials are correct

**What Testing Checks**:
- API key format is correct
- API key is valid and active
- Account has credits/balance
- Provider API is accessible

### 📊 Monitor Usage

**Check Provider Dashboards Regularly**:
- OpenRouter: https://openrouter.ai/activity
- OpenAI: https://platform.openai.com/usage
- Anthropic: https://console.anthropic.com/settings/usage
- Google: https://console.cloud.google.com/billing

**What to Monitor**:
- Daily/monthly spend
- Remaining credits
- Rate limit usage
- Unusual spikes

**Set Alerts**:
- Most providers allow spending alerts
- Set daily/monthly limits
- Get notified of unusual usage

### 🔄 Rotate Keys Every 90 Days

**Security Best Practice**:
1. Generate new API key at provider
2. Add new key to UC-Cloud
3. Test new key
4. Delete old key from UC-Cloud
5. Revoke old key at provider

**Why Rotate?**:
- Limit exposure if key is compromised
- Comply with security policies
- Reduce risk of leaked keys

### 🗑️ Remove Unused Keys

**Clean Up Regularly**:
- Delete keys you no longer use
- Remove duplicate keys
- Remove expired provider accounts
- Keep only active keys

**Benefits**:
- Cleaner API Keys page
- Easier to manage
- Reduced security risk
- Better organization

### 🏢 Use Organization Keys (Enterprise)

**For Teams**:
- Set up organization BYOK
- All members share one key
- Centralized billing
- Better cost tracking
- Simplified management

**How to Set Up**:
1. Upgrade to Enterprise tier
2. Contact support to enable org BYOK
3. Admin adds API key to organization
4. All members automatically use org key

---

## FAQ

### Can I use multiple keys?

**Yes!** You can add keys from all 4 providers:
- 1x OpenRouter key
- 1x OpenAI key
- 1x Anthropic key
- 1x Google key

**Routing Priority**:
1. OpenRouter (if configured) → All requests
2. Provider-specific key → Matching requests only
3. System key → Fallback (credits charged)

### Can I share keys with my team?

**Free/Starter/Professional**: No, keys are per-user only

**Enterprise**: Yes! Organization admins can add shared keys for all team members

**Workaround**: Give team members your provider credentials (they add their own keys)

### What happens if my key expires?

**Automatic Fallback**:
1. Your BYOK key expires/fails
2. UC-Cloud detects error
3. System automatically falls back to system key
4. **Credits charged** until you fix/replace key

**Notifications**:
- ⚠️ Status shows "Error" on API Keys page
- 📧 Email alert (if enabled)
- 🔔 In-app notification

**To Fix**:
1. Generate new key at provider
2. Update key in Ops-Center
3. Test to verify
4. Status returns to "✅ Connected"

### Can I switch providers anytime?

**Yes!** Switching is instant:

**Method 1: Add New Key**
1. Add key from new provider
2. New requests use new key
3. Old key remains (can delete later)

**Method 2: Replace Key**
1. Delete old key
2. Add new key from different provider
3. Immediate switch

**No Downtime**: System key used during brief transition

### Do I need BYOK?

**BYOK is Optional**

**Use BYOK if**:
- ✅ You want to save money (no markup)
- ✅ You have high usage (100M+ tokens/month)
- ✅ You want access to free models
- ✅ You prefer direct billing

**Skip BYOK if**:
- ✅ You have low usage (<10M tokens/month)
- ✅ You want simplicity (one invoice)
- ✅ You don't want to manage API keys
- ✅ Platform credits work for you

### Is BYOK secure?

**Yes, Very Secure!**

**Encryption**:
- ✅ Fernet encryption at rest (AES-128-CBC + HMAC)
- ✅ HTTPS encryption in transit (TLS 1.3)
- ✅ Keys never logged in plaintext

**Isolation**:
- ✅ Per-user key storage
- ✅ No cross-user access
- ✅ Admin cannot view your keys

**Compliance**:
- ✅ SOC 2 Type II compliant (coming soon)
- ✅ GDPR compliant
- ✅ HIPAA compliant (Enterprise tier)

### Can I export my keys?

**No**, for security reasons:

**Why Not**:
- Keys are encrypted in database
- Only decrypted for API calls
- Export would expose keys
- Violates security best practices

**Alternative**:
- Keep keys in password manager
- Store keys in provider dashboard
- Download from provider (not UC-Cloud)

### What happens when I delete a key?

**Immediate Effects**:
1. Key permanently removed from database
2. Future requests use system key (credits charged)
3. Cannot be recovered (must re-add)

**No Grace Period**: Deletion is instant

**Before Deleting**:
- ⚠️ Confirm you want to use credits
- ⚠️ Backup key elsewhere (if needed)
- ⚠️ Consider disabling instead (temporary)

---

## Appendix

### A. API Key Formats

**Validation Patterns**:

```regex
# OpenRouter
^sk-or-v1-[a-zA-Z0-9]{64}$

# OpenAI (new format)
^sk-proj-[a-zA-Z0-9_-]{43,}$

# OpenAI (legacy format)
^sk-[a-zA-Z0-9]{48}$

# Anthropic
^sk-ant-[a-zA-Z0-9_-]{95,}$

# Google
^[a-zA-Z0-9_-]{39}$
```

**Examples**:
```
OpenRouter:  sk-or-v1-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
OpenAI:      sk-proj-AbCdEfGhIjKlMnOpQrStUvWxYz1234567890AbCdEfGhIjKlMnOpQrStUvWxYz
Anthropic:   sk-ant-api03-AbCdEfGhIjKlMnOpQrStUvWxYz1234567890AbCdEfGhIjKlMnOpQrStUvWxYz1234567890AbCdEfGhIjKlMn
Google:      AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz1234567
```

### B. Provider Comparison Matrix

| Feature | OpenRouter | OpenAI | Anthropic | Google |
|---------|-----------|--------|-----------|--------|
| **Total Models** | 348 | 15 | 8 | 5 |
| **Free Models** | 60+ | 0 | 0 | 3 |
| **Min Cost** | $0 | $0.15/1M | $0.25/1M | $0.075/1M |
| **Max Cost** | $150/1M | $60/1M | $75/1M | $30/1M |
| **Best For** | Universal | Latest GPT | Claude | Gemini/Free |
| **Rate Limits** | 200-10K/min | 500-10K/min | 1K-10K/min | 60-1500/day |
| **Context Window** | Up to 200K | Up to 128K | Up to 200K | Up to 1M |
| **Multimodal** | ✅ | ✅ | ✅ | ✅ |
| **Streaming** | ✅ | ✅ | ✅ | ✅ |
| **Function Calling** | ✅ | ✅ | ✅ | ✅ |
| **Free Tier** | ✅ $5/mo | ❌ | ❌ | ✅ Limited |

### C. Cost Calculator

**Formula**:

```python
# Without BYOK (Platform Credits)
def platform_cost(tokens, base_cost_per_1m, tier):
    markup_rates = {
        "trial": 0.15,        # 15%
        "starter": 0.10,      # 10%
        "professional": 0.05, # 5%
        "enterprise": 0.00    # 0%
    }

    base_cost = (tokens / 1_000_000) * base_cost_per_1m
    markup = base_cost * markup_rates[tier]
    total = base_cost + markup

    return total

# With BYOK
def byok_cost(tokens, base_cost_per_1m):
    # No markup!
    return (tokens / 1_000_000) * base_cost_per_1m
```

**Example Calculation**:

```python
# Scenario: Professional tier, 100M tokens, GPT-4
tokens = 100_000_000
base_cost_per_1m = 30.00  # OpenAI GPT-4 average

# Platform Credits
platform = platform_cost(tokens, base_cost_per_1m, "professional")
# = (100M / 1M) * $30 * 1.05
# = 100 * $30 * 1.05
# = $3,150

# BYOK
byok = byok_cost(tokens, base_cost_per_1m)
# = (100M / 1M) * $30
# = 100 * $30
# = $3,000

# Savings
savings = platform - byok  # $150/month
```

### D. Support Resources

**Documentation**:
- This Guide: `/docs/BYOK_USER_GUIDE.md`
- Technical Docs: `/docs/BYOK_IMPLEMENTATION.md`
- Quick Reference: `/backend/BYOK_QUICK_REFERENCE.md`
- OpenRouter Guide: `/docs/OPENROUTER_INTEGRATION_GUIDE.md`

**Provider Documentation**:
- OpenRouter: https://openrouter.ai/docs
- OpenAI: https://platform.openai.com/docs
- Anthropic: https://docs.anthropic.com
- Google: https://ai.google.dev/docs

**UC-Cloud Support**:
- Email: support@unicorncommander.com
- Discord: https://discord.gg/unicorncommander
- Docs: https://docs.unicorncommander.ai
- Status Page: https://status.unicorncommander.ai

**Provider Support**:
- OpenRouter: support@openrouter.ai
- OpenAI: https://help.openai.com
- Anthropic: support@anthropic.com
- Google: https://support.google.com/ai

---

## 🎉 Ready to Get Started?

**Next Steps**:

1. **Choose a Provider** → OpenRouter recommended for beginners
2. **Get Your API Key** → Sign up and generate key
3. **Add to Ops-Center** → Follow "Adding Your First Key" guide
4. **Test It Out** → Make a request and verify BYOK works
5. **Monitor Usage** → Check provider dashboard after first request
6. **Optimize Costs** → Use free models when possible

**Questions?** Check the [FAQ](#faq) or contact support!

**Happy BYOK-ing!** 🚀

---

**Document Version**: 2.0
**Last Updated**: October 26, 2025
**Maintained By**: UC-Cloud Documentation Team
**License**: MIT
