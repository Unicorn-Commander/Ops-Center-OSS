# Quick Start: LiteLLM Provider Management

**URL**: https://unicorncommander.ai/admin/litellm-providers

---

## 🚀 Quick Access

1. Login to Ops-Center: https://unicorncommander.ai
2. Navigate to: **Services** → **LiteLLM Providers**
3. Or directly: https://unicorncommander.ai/admin/litellm-providers

---

## ➕ Add Your First Provider

### OpenRouter (Recommended for Cost Optimization)

1. Get API key: https://openrouter.ai/keys
2. Click **"Add Provider"** button
3. Select **"OpenRouter"** from dropdown
4. Paste your API key: `sk-or-v1-...`
5. Click **"Test Connection"**
6. If successful, click **"Add Provider"**

**Cost**: $0.20-$2.00 per 1M tokens (depending on model)

### OpenAI (High Quality)

1. Get API key: https://platform.openai.com/api-keys
2. Click **"Add Provider"** button
3. Select **"OpenAI"** from dropdown
4. Paste your API key: `sk-...`
5. Click **"Test Connection"**
6. Click **"Add Provider"**

**Cost**: $1.00-$60.00 per 1M tokens (depending on model)

### Anthropic (Claude Models)

1. Get API key: https://console.anthropic.com/
2. Click **"Add Provider"** button
3. Select **"Anthropic"** from dropdown
4. Paste your API key: `sk-ant-...`
5. Click **"Test Connection"**
6. Click **"Add Provider"**

**Cost**: $3.00-$75.00 per 1M tokens (depending on model)

---

## ⚙️ Configure Routing Strategy

### Cost Optimized (Best for High Volume)
- Always uses cheapest available model
- Example: llama-3-8b, mixtral-8x7b
- Average cost: $0.20/1M tokens

### Balanced (Recommended Default)
- Mix of quality and cost
- Example: gpt-4o-mini, claude-haiku
- Average cost: $1.00/1M tokens

### Quality Optimized (Best for Complex Tasks)
- Uses best available models
- Example: gpt-4, claude-opus
- Average cost: $5.00/1M tokens

**To Change**:
1. Scroll to "Routing Strategy" panel
2. Select your preferred strategy
3. Saves automatically

---

## 📊 View Analytics

### Usage Over Time
- See API calls by day/week/month
- Line chart shows trends
- Switch between: 7 days, 30 days, 90 days, All Time

### Cost by Provider
- Pie chart shows cost breakdown
- Identify most expensive providers
- Optimize based on usage patterns

**Refresh**:
- Stats auto-update every 30 seconds
- Manual refresh: Change time range selector

---

## 🔑 BYOK (Bring Your Own Key)

**What is BYOK?**
- Let users provide their own API keys
- Users pay their own LLM costs
- You don't pay for their usage

**Benefits**:
- Reduce infrastructure costs
- Give users flexibility
- Track savings in dashboard

**Current Status**:
- View BYOK users in "BYOK Management" panel
- See total cost saved
- Monitor active BYOK accounts

---

## 🎯 User Power Levels

Set different quality/cost tiers for users:

### Eco Mode ($0.20/1M tokens)
- Best for: High-volume, simple tasks
- Models: llama-3-8b, mixtral-8x7b
- Use case: Bulk data processing, simple Q&A

### Balanced Mode ($1.00/1M tokens)
- Best for: General purpose
- Models: gpt-4o-mini, claude-haiku
- Use case: Most user interactions

### Precision Mode ($5.00/1M tokens)
- Best for: Complex reasoning
- Models: gpt-4, claude-opus
- Use case: Advanced analysis, coding, research

---

## 🧪 Test a Provider

1. Find provider card in grid
2. Click green **"Test"** button (⚡ icon)
3. Alert shows:
   - ✅ Success: Connection successful! (142ms)
   - ❌ Error: Invalid API key

**Why Test?**
- Verify API key is valid
- Check provider availability
- Measure latency

---

## 🗑️ Remove a Provider

1. Find provider card in grid
2. Click red **"Delete"** button (🗑️ icon)
3. Confirm deletion
4. Provider removed immediately

**Warning**: Deleting a provider may cause failures if it's being actively used!

---

## 📈 Statistics Dashboard

### Top Cards (Auto-Update Every 30s)

1. **Total Providers**: Number of configured providers
2. **Active Models**: Total models available across all providers
3. **API Calls (30d)**: Total calls in last 30 days (+8% trend)
4. **Total Cost (30d)**: Total spend in last 30 days (-5% trend)

### Trends
- 🟢 Green arrow up: Increase from last month
- 🔴 Red arrow down: Decrease from last month

---

## 🛠️ Provider Actions

Each provider card has 3 action buttons:

1. **⚙️ Configure** (Blue)
   - Edit provider settings
   - Update API key
   - Change priority

2. **⚡ Test** (Green)
   - Test connection
   - Verify API key
   - Check latency

3. **🗑️ Delete** (Red)
   - Remove provider
   - Requires confirmation
   - Cannot be undone

---

## 💡 Best Practices

### 1. Start with OpenRouter
- Cheapest option ($0.20-$2.00/1M tokens)
- Access to 50+ models
- Great for testing

### 2. Use Multiple Providers
- Automatic fallback if one fails
- Load balancing
- Cost optimization

### 3. Set Priority Correctly
- Higher priority = used first
- Range: 1-100
- Default: 50

### 4. Enable Auto-Fallback
- Automatically switch if primary fails
- Improve reliability
- Reduce downtime

### 5. Monitor Usage
- Check analytics weekly
- Optimize based on patterns
- Identify cost savings

### 6. Test Before Production
- Use "Test" button first
- Verify all providers work
- Check latency

---

## 🆘 Troubleshooting

### Provider Test Fails

**"Invalid API key"**
- Check API key is correct
- Verify no extra spaces
- Regenerate key if needed

**"Connection timeout"**
- Check internet connection
- Provider may be down
- Try again in a few minutes

**"Rate limit exceeded"**
- You hit provider's rate limit
- Wait before testing again
- Check provider dashboard

### Provider Not Showing

**Check**:
1. Did "Add Provider" succeed?
2. Refresh the page (Ctrl+R)
3. Check backend logs: `docker logs ops-center-direct`

### Charts Not Loading

**Solutions**:
1. Select different time range
2. Refresh page
3. Check if backend is running
4. Verify API endpoint: `/api/v1/llm/usage`

### Stats Not Updating

**Check**:
1. Wait 30 seconds (auto-refresh interval)
2. Manually change time range
3. Backend may be restarting
4. Check browser console for errors

---

## 🔗 Related Documentation

- **Main Documentation**: `LITELLM_MANAGEMENT_PAGE.md`
- **Ops-Center Docs**: `/services/ops-center/CLAUDE.md`
- **UC-Cloud Docs**: `/CLAUDE.md`
- **LiteLLM Official**: https://docs.litellm.ai/

---

## 📞 Support

**Issues?**
1. Check browser console (F12)
2. Check backend logs: `docker logs ops-center-direct --tail 100`
3. Verify authentication token
4. Test API endpoints manually

**For Development**:
- Source: `/services/ops-center/src/pages/LiteLLMManagement.jsx`
- Rebuild: `npm run build && cp -r dist/* public/`
- Restart: `docker restart ops-center-direct`

---

**Last Updated**: October 23, 2025
**Status**: ✅ Production Ready
