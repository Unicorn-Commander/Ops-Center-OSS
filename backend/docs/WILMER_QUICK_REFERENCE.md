# WilmerAI Quick Reference Guide

**Last Updated**: October 20, 2025

---

## 30-Second Overview

WilmerAI intelligently routes LLM requests to optimal providers based on:
- **Privacy** (local models for sensitive data)
- **Speed** (Groq for <500ms responses)
- **Cost** (free tier when possible)
- **Quality** (best models when needed)
- **BYOK** (user's own API keys = free credits)

---

## Quick Start

```python
from wilmer_router import (
    WilmerRouter, RoutingRequest, TaskType,
    LatencySLO, PowerLevel, QualityRequirement,
    get_wilmer_router
)

# Initialize router
router = get_wilmer_router()

# Create request
request = RoutingRequest(
    task_type=TaskType.CODE,           # code, chat, rag, creative, analysis
    estimated_tokens=2000,
    latency_slo=LatencySLO.FAST,       # instant, fast, normal, slow
    privacy_required=False,
    user_tier="professional",          # free, starter, professional, enterprise
    credits_remaining=10.0,
    quality_requirement=QualityRequirement.BEST,  # basic, good, best
    power_level=PowerLevel.BALANCED,   # eco, balanced, precision
    user_id="user@example.com"
)

# Get provider choice
choice = await router.select_provider(request)

# Use result
print(f"Provider: {choice.provider}")
print(f"Model: {choice.model}")
print(f"Cost: ${choice.estimated_cost:.4f}")
```

---

## Provider Selection Cheat Sheet

### By Priority

1. **Privacy Required?** → Local models (Qwen 32B, Llama 3 8B)
2. **User has BYOK?** → User's API key (free credits)
3. **Need <500ms?** → Groq (Llama 3 70B)
4. **Free tier / No credits?** → Local or Groq
5. **Code task?** → Qwen 72B or Claude 3.5
6. **Creative task?** → Claude 3.5 or GPT-4o
7. **Long context (>30K)?** → Mixtral 8x22B
8. **Default** → Based on power level

### By Power Level

| Power Level | Preferred Providers | Max Cost | Use Case |
|-------------|-------------------|----------|----------|
| **ECO** | local → groq → huggingface | $0.001 | Minimize cost |
| **BALANCED** | together → fireworks → openrouter | $0.01 | Balance cost/quality |
| **PRECISION** | anthropic → openai → openrouter | $0.1 | Maximize quality |

---

## Task Type → Provider Mapping

| Task Type | Best Provider | Alternative | Free Option |
|-----------|--------------|-------------|-------------|
| **CODE** | Claude 3.5 | Qwen 72B | Local Qwen 32B |
| **CREATIVE** | Claude 3.5 | GPT-4o | Groq Llama 3 70B |
| **CHAT** | GPT-4o | Llama 3 70B | Groq |
| **RAG** | Mixtral 8x22B | GPT-4o | Local Qwen 32B |
| **REASONING** | Claude 3.5 | Local Qwen 32B | Local Qwen 32B |
| **ANALYSIS** | GPT-4o | Llama 3 70B | Groq |

---

## Common Patterns

### Privacy-First (Sensitive Data)

```python
request = RoutingRequest(
    privacy_required=True,  # ← Forces local models
    # ... other params
)
```

### Ultra-Fast Responses

```python
request = RoutingRequest(
    latency_slo=LatencySLO.INSTANT,  # ← Routes to Groq
    estimated_tokens=4000,           # Keep under 8K
    # ... other params
)
```

### Best Quality

```python
request = RoutingRequest(
    quality_requirement=QualityRequirement.BEST,  # ← Top models
    power_level=PowerLevel.PRECISION,             # ← Don't worry about cost
    # ... other params
)
```

### Minimize Cost

```python
request = RoutingRequest(
    power_level=PowerLevel.ECO,  # ← Cheapest options
    quality_requirement=QualityRequirement.BASIC,
    # ... other params
)
```

### BYOK (User's Key)

```python
choice = await router.select_provider(
    request,
    user_byok_providers=["openai", "anthropic"]  # ← User's keys
)
# choice.is_byok == True
# choice.estimated_cost == 0.0
```

---

## Provider Costs

| Provider | Model | Cost/1K | Speed | Quality |
|----------|-------|---------|-------|---------|
| **Free Tier** |
| Local | Qwen 32B | $0 | Medium | 0.85 |
| Local | Llama 3 8B | $0 | Fast | 0.70 |
| Groq | Llama 3 70B | $0 | Ultrafast | 0.80 |
| HuggingFace | Mixtral 8x7B | $0 | Slow | 0.75 |
| **Paid Low Cost** |
| Together | Mixtral 8x22B | $0.002 | Fast | 0.85 |
| Fireworks | Qwen 72B | $0.002 | Fast | 0.87 |
| DeepInfra | Llama 3 70B | $0.003 | Medium | 0.80 |
| **Premium** |
| OpenRouter | Claude 3.5 | $0.008 | Medium | 0.95 |
| OpenRouter | GPT-4o | $0.010 | Medium | 0.93 |
| Anthropic | Claude 3.5 | $0.015 | Fast | 0.97 |
| OpenAI | GPT-4o | $0.015 | Fast | 0.95 |

---

## Utility Functions

### Estimate Cost

```python
cost = await router.estimate_cost(request, "openrouter/claude-3.5")
print(f"Estimated: ${cost:.4f}")
```

### Get Fallback Chain

```python
fallbacks = router.get_fallback_chain("openrouter/claude-3.5", request)
print(f"Fallbacks: {fallbacks}")
```

### Get Available Models

```python
models = router.get_available_models_for_tier("professional")
for model in models:
    print(f"{model['key']}: ${model['cost_per_1k']:.4f}/1K")
```

---

## Model Selection

### Select by Task

```python
from model_selector import select_model_for_task

model = select_model_for_task(
    task_type="code",
    power_level="balanced",
    max_cost=0.01
)
print(f"Selected: {model['key']}")
```

### Get by Capability

```python
from model_selector import get_models_by_capability

models = get_models_by_capability("code_generation", max_cost=0.01)
for m in models:
    print(f"{m['key']}: quality={m['quality_score']:.2f}")
```

### Compare Models

```python
from model_selector import compare_models

comparison = compare_models([
    "openrouter/claude-3.5",
    "fireworks/qwen-72b",
    "local/qwen-32b"
])
```

---

## Health Monitoring

### Check Provider Health

```python
from provider_health import get_health_checker

checker = get_health_checker()

# Start monitoring
await checker.start_monitoring()

# Check health
is_healthy = await checker.is_provider_healthy("groq")

# Get summary
summary = await checker.get_health_summary()
print(f"Healthy: {summary['healthy_providers']}/{summary['total_providers']}")
```

---

## Configuration

### Add New Provider

**In `wilmer_router.py`:**

```python
PROVIDER_CONFIGS = {
    "new-provider/model": {
        "provider": "new-provider",
        "model": "new-provider/model-name",
        "cost_per_1k": 0.005,
        "max_tokens": 8192,
        "avg_latency_ms": 2000,
        "strengths": ["code", "reasoning"],
        "requires_tier": "starter"
    }
}
```

**In `model_selector.py`:**

```python
MODEL_CAPABILITIES = {
    "new-provider/model": {
        "capabilities": [
            ModelCapability.CODE_GENERATION,
            ModelCapability.REASONING
        ],
        "quality_score": 0.85,
        "speed_score": 0.80,
        "cost_score": 0.75
    }
}
```

---

## Decision Tree

```
Request Received
    ↓
Privacy Required?
    Yes → Local Models
    No ↓
BYOK Available?
    Yes → User's Key
    No ↓
Instant Latency?
    Yes → Groq (if <8K tokens)
    No ↓
Free Tier / No Credits?
    Yes → Free Providers
    No ↓
Task Type?
    Code → Qwen 72B / Claude 3.5
    Creative → Claude 3.5 / GPT-4o
    RAG → Mixtral 8x22B
    Default ↓
Power Level?
    Eco → Cheapest meeting requirements
    Balanced → Best cost/quality ratio
    Precision → Highest quality available
```

---

## Error Handling

### Use Fallback Chain

```python
choice = await router.select_provider(request)

# Try primary
try:
    result = await call_llm(choice.provider, choice.model, messages)
except Exception as e:
    # Try fallbacks
    for fallback in choice.fallback_chain:
        try:
            provider, model = fallback.split("/", 1)
            result = await call_llm(provider, model, messages)
            break
        except:
            continue
```

---

## Files

- **`wilmer_router.py`** (734 lines) - Core routing engine
- **`model_selector.py`** (488 lines) - Model selection utilities
- **`provider_health.py`** (466 lines) - Health monitoring
- **`docs/WILMER_ROUTING_LOGIC.md`** (665 lines) - Full documentation
- **`examples/wilmer_routing_examples.py`** (547 lines) - Usage examples

---

## Integration with Ops-Center

### API Endpoint

```python
# In llm_api.py or server.py
from wilmer_router import get_wilmer_router, RoutingRequest

router = get_wilmer_router(byok_service, redis_client)

@app.post("/api/v1/llm/chat/completions")
async def chat_completions(request: ChatRequest):
    # Build routing request
    routing_req = RoutingRequest(
        task_type=TaskType(request.task_type or "chat"),
        estimated_tokens=estimate_tokens(request.messages),
        latency_slo=LatencySLO(request.latency_slo or "normal"),
        privacy_required=request.privacy_required or False,
        user_tier=user.subscription_tier,
        credits_remaining=user.credits,
        quality_requirement=QualityRequirement(request.quality or "good"),
        power_level=PowerLevel(request.power_level or "balanced"),
        user_id=user.id
    )

    # Get provider
    choice = await router.select_provider(routing_req, user_byok_providers)

    # Call LLM via LiteLLM
    result = await litellm_client.chat_completion(
        model=choice.model,
        messages=request.messages,
        max_tokens=choice.max_tokens,
        temperature=choice.temperature
    )

    # Log usage and cost
    await log_usage(user.id, choice.provider, choice.estimated_cost)

    return result
```

---

## Performance Tips

1. **Enable Redis caching** - 5-minute TTL for routing decisions
2. **Start health monitoring** - Real-time provider health data
3. **Use BYOK when available** - Free credits for users
4. **Batch similar requests** - Caching benefits
5. **Set realistic latency SLOs** - Don't force "instant" unless needed

---

**For full documentation, see**: `docs/WILMER_ROUTING_LOGIC.md`
**For usage examples, see**: `examples/wilmer_routing_examples.py`
