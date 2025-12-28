# Ops-Center LLM API - Quick Reference Card

**Deployment**: centerdeep.online
**Updated**: November 14, 2025

---

## 🔗 Endpoints

| Type | URL |
|------|-----|
| **Internal** | `http://ops-center-centerdeep:8084/api/v1/llm` |
| **External** | `https://ops.centerdeep.online/api/v1/llm` |

---

## 🔑 Authentication

**Service Key** (Recommended for internal services):
```
Authorization: Bearer sk-loopnet-service-key-2025
```

**User API Key**:
```
Authorization: Bearer uc_a1b2c3d4e5f6...
```

**Session Cookie** (Browser):
```
Cookie: session_token=xyz123...
```

---

## 📡 Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat/completions` | POST | Chat with LLM (OpenAI-compatible) |
| `/image/generations` | POST | Generate images |
| `/models` | GET | List available models |
| `/credits` | GET | Check credit balance |
| `/usage` | GET | Usage statistics |

---

## 💬 Chat Completion Request

```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 500,
  "power_level": "balanced"
}
```

**Power Levels**:
- `eco` - 50% cheaper, good quality
- `balanced` - Standard pricing (default)
- `precision` - 2x cost, best quality

---

## 🎯 Common Use Cases

### Company Enrichment
```bash
curl -X POST http://ops-center-centerdeep:8084/api/v1/llm/chat/completions \
  -H "Authorization: Bearer sk-loopnet-service-key-2025" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {
        "role": "system",
        "content": "Extract company name, industry, location as JSON."
      },
      {
        "role": "user",
        "content": "Acme Corp is a tech company in SF..."
      }
    ],
    "power_level": "eco",
    "temperature": 0.3
  }'
```

### AI Search Summary
```bash
curl -X POST http://ops-center-centerdeep:8084/api/v1/llm/chat/completions \
  -H "Authorization: Bearer sk-centerdeep-service-key-2025" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {
        "role": "system",
        "content": "Summarize search results concisely."
      },
      {
        "role": "user",
        "content": "Search results:\n1. Title: ...\n2. Title: ..."
      }
    ],
    "power_level": "balanced"
  }'
```

---

## 📊 Response Headers

```
X-Provider-Used: openai
X-Cost-Incurred: 0.003
X-Credits-Remaining: 9997.000
X-RateLimit-Limit: 10000
X-RateLimit-Remaining: 9850
X-RateLimit-Reset: 1733097600
```

---

## 💰 Pricing & Rate Limits

| Tier | Daily Limit | Monthly Limit | Cost |
|------|-------------|---------------|------|
| Trial | 100 | 700 | $1/week |
| Starter | 34 | 1,000 | $19/month |
| Professional | 334 | 10,000 | $49/month |
| Enterprise | Unlimited | Unlimited | $99/month |
| BYOK | Unlimited | Unlimited | Provider pricing |

---

## ⚠️ Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad Request | Fix request format |
| 401 | Unauthorized | Check API key |
| 402 | Insufficient Credits | Add credits or upgrade |
| 429 | Rate Limit Exceeded | Wait for quota reset |
| 500 | Server Error | Retry with backoff |

---

## 🔧 Python Quick Start

```python
import requests

API_BASE = "http://ops-center-centerdeep:8084/api/v1/llm"
SERVICE_KEY = "sk-loopnet-service-key-2025"

response = requests.post(
    f"{API_BASE}/chat/completions",
    headers={"Authorization": f"Bearer {SERVICE_KEY}"},
    json={
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Hello!"}
        ]
    }
)

result = response.json()
print(result['choices'][0]['message']['content'])
```

---

## 🔧 Node.js Quick Start

```javascript
const axios = require('axios');

const API_BASE = 'http://ops-center-centerdeep:8084/api/v1/llm';
const SERVICE_KEY = 'sk-loopnet-service-key-2025';

const response = await axios.post(
  `${API_BASE}/chat/completions`,
  {
    model: 'gpt-4o-mini',
    messages: [
      { role: 'user', content: 'Hello!' }
    ]
  },
  {
    headers: {
      'Authorization': `Bearer ${SERVICE_KEY}`
    }
  }
);

console.log(response.data.choices[0].message.content);
```

---

## 🔧 Curl Quick Start

```bash
curl -X POST http://ops-center-centerdeep:8084/api/v1/llm/chat/completions \
  -H "Authorization: Bearer sk-loopnet-service-key-2025" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## 📚 Available Models

**Free Tier**: llama3-8b-local, qwen-32b-local
**Starter**: mixtral-8x22b-together, llama3-70b-deepinfra
**Professional**: claude-3.5-sonnet-openrouter, gpt-4o-openrouter
**Enterprise**: claude-3.5-sonnet, gpt-4o, o1-preview

**BYOK**: All 100+ models via OpenRouter (free API calls)

---

## 🛠️ Troubleshooting

**Connection Refused**:
```bash
# Check container running
docker ps | grep ops-center-centerdeep

# Check network
docker network inspect unicorn-network | grep ops-center
```

**401 Unauthorized**:
- Verify service key added to `litellm_api.py` line 566-570
- Restart container: `docker restart ops-center-centerdeep`

**429 Rate Limit**:
- Check quota: `GET /api/v1/llm/credits`
- Wait for reset (shown in `X-RateLimit-Reset` header)

**Slow Response**:
- Use internal endpoint (faster than HTTPS)
- Set `power_level: "eco"` for cheaper/faster
- Reduce `max_tokens`

---

## 📞 Support

**Documentation**: `/tmp/OPS_CENTER_INTEGRATION_GUIDE.md`
**Container**: `ops-center-centerdeep`
**Database**: `unicorn_db@unicorn-postgresql`
**Logs**: `docker logs ops-center-centerdeep -f`

---

## 🚀 Integration Checklist

- [ ] Add service key to `litellm_api.py`
- [ ] Restart Ops-Center container
- [ ] Create organization in database
- [ ] Allocate credits to organization
- [ ] Test basic chat completion
- [ ] Monitor usage via API
- [ ] Implement error handling with retry logic

---

**Quick Test**:
```bash
curl http://ops-center-centerdeep:8084/api/v1/llm/credits \
  -H "Authorization: Bearer sk-loopnet-service-key-2025"
```

Expected: `{"user_id": "...", "credits_remaining": 10000000.0, ...}`
