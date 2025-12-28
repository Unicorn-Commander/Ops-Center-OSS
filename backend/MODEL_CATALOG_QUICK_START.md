# Model Catalog API - Quick Start Guide

## Testing the API (Copy & Paste)

### 1. Get Statistics

```bash
curl -s "http://localhost:8084/api/v1/llm/models/stats" | jq '.'
```

**Expected Output**:
```json
{
  "total_models": 351,
  "enabled_count": 345,
  "disabled_count": 6,
  "avg_price_per_1m": 1.98,
  "most_used": [],
  "providers": {
    "openrouter": {
      "total": 346,
      "enabled": 345
    },
    "anthropic": {
      "total": 5,
      "enabled": 0
    }
  }
}
```

---

### 2. List First 10 Models

```bash
curl -s "http://localhost:8084/api/v1/llm/models?limit=10" | jq '.models[] | {id, name, provider, enabled, pricing}'
```

**Expected Output**: 10 models with pricing

---

### 3. Search for Claude Models

```bash
curl -s "http://localhost:8084/api/v1/llm/models?search=claude&limit=5" | jq '.models[] | {name, pricing, capabilities}'
```

**Expected Output**: Claude models with capabilities

---

### 4. Get Cheapest Models

```bash
curl -s "http://localhost:8084/api/v1/llm/models?sort=price&limit=10" | jq '.models[] | {name, input_price: .pricing.input, output_price: .pricing.output}'
```

**Expected Output**: Models sorted by price (cheapest first)

---

### 5. Vision-Capable Models Only

```bash
curl -s "http://localhost:8084/api/v1/llm/models?capability=vision&limit=10" | jq '.models[] | {name, capabilities, context_length}'
```

**Expected Output**: Models with vision capability

---

### 6. OpenRouter Models Only

```bash
curl -s "http://localhost:8084/api/v1/llm/models?provider=openrouter&limit=10" | jq '.models[] | .name'
```

**Expected Output**: OpenRouter model names

---

### 7. Enabled Models Only

```bash
curl -s "http://localhost:8084/api/v1/llm/models?enabled=true&limit=10" | jq '.total'
```

**Expected Output**: Number of enabled models (~345)

---

### 8. Get Claude 3.5 Sonnet Details

```bash
curl -s "http://localhost:8084/api/v1/llm/models/anthropic/claude-3-5-sonnet-20241022" | jq '.'
```

**Expected Output**: Full Claude 3.5 Sonnet details with usage stats

---

### 9. List All Providers

```bash
curl -s "http://localhost:8084/api/v1/llm/providers" | jq '.providers[] | {name, display_name, total_models, enabled_models}'
```

**Expected Output**:
```json
{
  "name": "openrouter",
  "display_name": "OpenRouter",
  "total_models": 346,
  "enabled_models": 345
}
{
  "name": "anthropic",
  "display_name": "Anthropic",
  "total_models": 5,
  "enabled_models": 0
}
```

---

### 10. Combined Filters

```bash
curl -s "http://localhost:8084/api/v1/llm/models?provider=openrouter&capability=vision&enabled=true&sort=price&limit=5" | jq '.models[] | {name, pricing: .pricing.input}'
```

**Expected Output**: OpenRouter vision models, enabled, sorted by price

---

## Admin Operations (Requires Auth)

### Enable a Model

```bash
# First, get session token by logging in via browser
# Then use it here

curl -X POST "http://localhost:8084/api/v1/llm/models/anthropic/claude-3-5-sonnet-20241022/toggle" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}' \
  --cookie "session_token=YOUR_SESSION_TOKEN" | jq '.'
```

**Expected Output**:
```json
{
  "success": true,
  "model_id": "anthropic/claude-3-5-sonnet-20241022",
  "enabled": true,
  "message": "Model enabled successfully"
}
```

---

### Refresh Model Catalog

```bash
curl -X POST "http://localhost:8084/api/v1/llm/models/refresh" \
  --cookie "session_token=YOUR_SESSION_TOKEN" | jq '.'
```

**Expected Output**:
```json
{
  "success": true,
  "total_models": 351,
  "message": "Model catalog refreshed successfully"
}
```

---

## Useful jq Filters

### Top 10 Cheapest Models

```bash
curl -s "http://localhost:8084/api/v1/llm/models?limit=100" | jq '.models | sort_by(.pricing.input) | .[:10] | .[] | {name, price: .pricing.input}'
```

---

### Models by Context Length

```bash
curl -s "http://localhost:8084/api/v1/llm/models?limit=100" | jq '.models | sort_by(.context_length) | reverse | .[:10] | .[] | {name, context_length}'
```

---

### Count Models by Provider

```bash
curl -s "http://localhost:8084/api/v1/llm/models" | jq '.models | group_by(.provider) | .[] | {provider: .[0].provider, count: length}'
```

---

### Vision + Function Calling Models

```bash
curl -s "http://localhost:8084/api/v1/llm/models" | jq '.models | .[] | select((.capabilities | contains(["vision"])) and (.capabilities | contains(["function_calling"]))) | {name, capabilities}'
```

---

## Performance Testing

### Measure Cold Start

```bash
time curl -s "http://localhost:8084/api/v1/llm/models/refresh" --cookie "session_token=YOUR_TOKEN" > /dev/null
```

**Expected**: ~2-5 seconds

---

### Measure Cached Request

```bash
time curl -s "http://localhost:8084/api/v1/llm/models" > /dev/null
```

**Expected**: <0.1 seconds

---

## Frontend Integration Example

### JavaScript/React

```javascript
// Fetch all models
const response = await fetch('/api/v1/llm/models?limit=50&sort=price');
const data = await response.json();

console.log(`Total models: ${data.total}`);
data.models.forEach(model => {
  console.log(`${model.name} - $${model.pricing.input}/1M tokens`);
});

// Filter by provider
const openrouterModels = await fetch('/api/v1/llm/models?provider=openrouter');

// Search
const claudeModels = await fetch('/api/v1/llm/models?search=claude');

// Toggle model (admin only)
await fetch(`/api/v1/llm/models/${modelId}/toggle`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ enabled: true }),
  credentials: 'include'  // Include session cookie
});
```

---

## Troubleshooting

### No models returned

```bash
# Check if API is responding
curl -I http://localhost:8084/api/v1/llm/models/stats

# Check logs
docker logs ops-center-direct | grep model_catalog
```

---

### "Model not found" error

```bash
# List all models to find correct ID
curl -s "http://localhost:8084/api/v1/llm/models?search=YOUR_SEARCH" | jq '.models[] | .id'
```

---

### Slow response

```bash
# Force cache refresh
curl -X POST "http://localhost:8084/api/v1/llm/models/refresh" \
  --cookie "session_token=YOUR_TOKEN"
```

---

## Next Steps

1. **Run Full Test Suite**: `./test_model_catalog.sh`
2. **Read Integration Guide**: `MODEL_CATALOG_INTEGRATION.md`
3. **Build Frontend**: See `MODEL_CATALOG_README.md` for frontend requirements

---

**Last Updated**: October 27, 2025
