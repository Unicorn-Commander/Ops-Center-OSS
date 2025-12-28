# LLM Pricing Calculator
**Quick Reference for Cost Calculations**

---

## 📊 Base Costs (per 1K tokens)

### Free Tier Models
- **Local**: $0.000 (Qwen 32B, Llama 3 8B)
- **Groq**: $0.000 (Llama 3 70B, Mixtral 8x7B)
- **HuggingFace**: $0.000 (Community models)

### Low-Cost Tier
- **Together AI**: $0.002 (Mixtral 8x22B, Llama 3 70B, Qwen 72B)
- **Fireworks AI**: $0.002 (Qwen 72B, Llama 3 70B)
- **DeepInfra**: $0.003 (Llama 3 70B, Mixtral 8x7B)

### OpenRouter Multi-Provider
- **Mixtral 8x7B**: $0.003
- **Claude 3.5 Sonnet**: $0.008
- **GPT-4o**: $0.010

### Premium Direct
- **Anthropic Claude**: $0.015 (direct API)
- **OpenAI GPT-4**: $0.015 (direct API)

---

## 💰 Markup Multipliers

| Tier | Markup % | Multiplier | Example |
|------|----------|-----------|---------|
| **Free** | 0% | 1.0x | $0.010 → $0.010 |
| **Starter** | 40% | 1.4x | $0.010 → $0.014 |
| **Professional** | 60% | 1.6x | $0.010 → $0.016 |
| **Enterprise** | 80% | 1.8x | $0.010 → $0.018 |

---

## 🧮 Quick Calculations

### Scenario 1: Professional User - GPT-4o (10K tokens)

```
Base Cost: $0.010 per 1K tokens
Tokens: 10,000 (10K tokens)
Tier: Professional (60% markup, 1.6x multiplier)

Calculation:
  Provider charges you: 10 * $0.010 = $0.10
  Your markup: 60%
  User pays: $0.10 * 1.6 = $0.16
  Your profit: $0.16 - $0.10 = $0.06

Profit Margin: 60%
Credits deducted: 160 credits (since 1 credit = $0.001)
```

### Scenario 2: Starter User - Claude 3.5 (50K tokens)

```
Base Cost: $0.008 per 1K tokens
Tokens: 50,000 (50K tokens)
Tier: Starter (40% markup, 1.4x multiplier)

Calculation:
  Provider charges you: 50 * $0.008 = $0.40
  Your markup: 40%
  User pays: $0.40 * 1.4 = $0.56
  Your profit: $0.56 - $0.40 = $0.16

Profit Margin: 40%
Credits deducted: 560 credits
```

### Scenario 3: Enterprise User - Mixtral (100K tokens)

```
Base Cost: $0.003 per 1K tokens
Tokens: 100,000 (100K tokens)
Tier: Enterprise (80% markup, 1.8x multiplier)

Calculation:
  Provider charges you: 100 * $0.003 = $0.30
  Your markup: 80%
  User pays: $0.30 * 1.8 = $0.54
  Your profit: $0.54 - $0.30 = $0.24

Profit Margin: 80%
Credits deducted: 540 credits
```

### Scenario 4: Free User - Any Model (Loss Leader)

```
Base Cost: $0.010 per 1K tokens
Tokens: 5,000 (5K tokens)
Tier: Free (0% markup, 1.0x multiplier)

Calculation:
  Provider charges you: 5 * $0.010 = $0.05
  Your markup: 0%
  User pays: $0.05 * 1.0 = $0.05
  Your profit: $0.05 - $0.05 = $0.00

Profit Margin: 0% (customer acquisition cost)
Credits deducted: 50 credits (from free allowance)
```

---

## 📈 Monthly Revenue Examples

### Conservative Scenario (100 Users)

**User Distribution**:
- 60 Free users
- 25 Starter users ($19/mo)
- 12 Professional users ($49/mo)
- 3 Enterprise users ($99/mo)

**Monthly Subscription Revenue**: $1,260

**API Usage** (conservative):
- Starter: 5,000 API calls @ $0.01 avg = $50 cost → $70 charge → $20 profit each = **$500 total**
- Professional: 20,000 API calls @ $0.01 avg = $200 cost → $320 charge → $120 profit each = **$1,440 total**
- Enterprise: 80,000 API calls @ $0.01 avg = $800 cost → $1,440 charge → $640 profit each = **$1,920 total**

**Total Revenue**: $5,120/mo
**Total Costs**: ~$800/mo (free users + infrastructure)
**Net Profit**: $4,320/mo

### Aggressive Scenario (500 Users)

**User Distribution**:
- 250 Free users
- 150 Starter users ($19/mo)
- 80 Professional users ($49/mo)
- 20 Enterprise users ($99/mo)

**Monthly Subscription Revenue**: $8,750

**API Usage** (conservative):
- Starter: 10,000 calls @ $0.01 = $100 cost → $140 charge → $40 profit each = **$6,000 total**
- Professional: 30,000 calls @ $0.01 = $300 cost → $480 charge → $180 profit each = **$14,400 total**
- Enterprise: 150,000 calls @ $0.01 = $1,500 cost → $2,700 charge → $1,200 profit each = **$24,000 total**

**Total Revenue**: $53,150/mo
**Total Costs**: ~$4,000/mo (free users + infrastructure)
**Net Profit**: $49,150/mo 🎉

---

## 🎯 Profit Margin by Model Type

### Free Models (0% margin)
- You pay: $0.00
- User pays: $0.00
- Your profit: $0.00
- **Use Case**: Free tier users only

### Low-Cost Models (40-80% margin)
- You pay: $0.002-$0.003
- Starter user pays: $0.0028-$0.0042 (40% markup)
- Professional pays: $0.0032-$0.0048 (60% markup)
- Enterprise pays: $0.0036-$0.0054 (80% markup)
- **Use Case**: High-volume, cost-sensitive users

### OpenRouter Models (40-80% margin)
- You pay: $0.008-$0.010
- Starter user pays: $0.0112-$0.014 (40% markup)
- Professional pays: $0.0128-$0.016 (60% markup)
- Enterprise pays: $0.0144-$0.018 (80% markup)
- **Use Case**: Most users (GPT-4, Claude 3.5)

### Premium Direct (40-80% margin)
- You pay: $0.015
- Starter user pays: $0.021 (40% markup)
- Professional pays: $0.024 (60% markup)
- Enterprise pays: $0.027 (80% markup)
- **Use Case**: Enterprise users, critical workloads

---

## 💡 Optimization Tips

### 1. Steer Users to Cost-Effective Models

**Good**:
- Groq (free, ultrafast)
- Together AI ($0.002, fast)
- OpenRouter Mixtral ($0.003, good quality)

**Expensive**:
- Direct OpenAI ($0.015)
- Direct Anthropic ($0.015)

**Recommendation**: Default to Groq/Together for free users, allow premium models for paid tiers.

### 2. Implement Smart Model Selection

```python
# In user settings
if user.tier == "free":
    allowed_models = ["groq/*", "local/*", "huggingface/*"]
elif user.tier == "starter":
    allowed_models = ["groq/*", "together/*", "openrouter:mixtral"]
elif user.tier == "professional":
    allowed_models = ["*"]  # All models except premium direct
else:  # enterprise
    allowed_models = ["**"]  # All models including premium
```

### 3. Set Cost Limits per Tier

```python
MAX_COST_PER_REQUEST = {
    "free": 0.001,       # $0.001 max per request
    "starter": 0.01,     # $0.01 max per request
    "professional": 0.1, # $0.10 max per request
    "enterprise": 1.0    # $1.00 max per request
}
```

---

## 🚀 Recommended Launch Strategy

### Phase 1: Validate (Weeks 1-4)
- Set conservative quotas (1K API calls/mo for free tier)
- Monitor costs closely (daily OpenRouter bill check)
- Focus on converting free → starter users
- **Goal**: Break even or slight loss (customer acquisition)

### Phase 2: Optimize (Weeks 5-8)
- Increase quotas for paid tiers
- Test price elasticity (can you raise prices 10%?)
- Add volume discounts for high-usage users
- **Goal**: 50% gross margin

### Phase 3: Scale (Weeks 9+)
- Focus on enterprise customers (highest margin)
- Introduce annual plans (2 months free = 16% discount)
- Add overage pricing for users exceeding quotas
- **Goal**: 70%+ gross margin, profitable growth

---

## 📊 Break-Even Analysis

### To Break Even with Current Markup

**Monthly Fixed Costs**: ~$500 (infrastructure)
**Free User Costs**: ~$500 (assuming 50 free users @ $10/mo usage)

**Total Monthly Costs**: $1,000

**Revenue Needed**:
```
Subscriptions + API Profit = $1,000

If you have 30 Starter users ($19/mo):
  Subscription revenue: $570
  Need from API profit: $430

If each Starter user generates $0.40 in API profit:
  30 users * $40 = $1,200 API profit

Total: $570 + $1,200 = $1,770
Break even at ~15 Starter users!
```

**Conclusion**: You can break even with just **15 paying Starter users** if they have moderate API usage.

---

## 🔥 Key Insights

1. **Enterprise users are 2x more profitable** than Starter users (80% vs 40% margin)
2. **Free users cost you ~$10/mo** if they use the platform actively
3. **Break even is achievable** with 15-20 paying customers
4. **Scale is profitable** - 100 paying customers = $10K+/mo profit potential
5. **Markup is already configured** - no changes needed to launch!

---

**Ready to Launch?** Your pricing is set, markup is configured, and the system is operational. Time to invite beta users! 🎉
