# WilmerAI Routing Logic Documentation

**Date**: October 20, 2025
**Author**: Ops-Center Backend Team
**Version**: 1.0

---

## Overview

WilmerAI is an intelligent LLM provider routing engine that selects optimal providers based on multiple factors including privacy, latency, budget, task type, and quality requirements.

### Key Benefits

- **Cost Optimization**: Automatically uses cheapest provider meeting requirements
- **Privacy Protection**: Routes sensitive requests to local models
- **Performance Optimization**: Selects fastest provider for latency-critical tasks
- **Quality Assurance**: Ensures best models for high-quality requirements
- **BYOK Support**: Automatically uses user's API keys when available (free credits)

---

## Architecture

### Components

1. **WilmerRouter** (`wilmer_router.py`) - Core routing engine
2. **ModelSelector** (`model_selector.py`) - Model selection utilities
3. **ProviderHealthChecker** (`provider_health.py`) - Provider health monitoring
4. **LiteLLMIntegration** (`litellm_integration.py`) - BYOK integration

### Routing Decision Flow

```
1. Check Privacy Requirements
   ├── Privacy Required? → Local Models
   └── No Privacy Required → Continue

2. Check BYOK Keys
   ├── User has BYOK? → Use User's Key (Free)
   └── No BYOK → Continue

3. Check Latency SLO
   ├── Instant (<500ms)? → Groq
   └── Normal → Continue

4. Check Budget
   ├── Free Tier / Low Credits? → Free Providers
   └── Has Credits → Continue

5. Check Power Level
   ├── Eco → Minimize Cost
   ├── Balanced → Balance Cost/Quality
   └── Precision → Maximize Quality

6. Task-Specific Routing
   ├── Code → Qwen/Claude
   ├── Creative → Claude/GPT-4o
   ├── RAG → Mixtral (long context)
   └── Default → Balanced provider
```

---

## Provider Tiers

### Tier 0: Free (Always Available)

| Provider | Model | Cost | Speed | Use Case |
|----------|-------|------|-------|----------|
| Local | Qwen 2.5 32B | $0 | Medium | Code, privacy |
| Local | Llama 3 8B | $0 | Fast | Chat, basic |
| Groq | Llama 3 70B | $0 | Ultrafast | Quick QA |
| HuggingFace | Mixtral 8x7B | $0 | Slow | Long context |

### Tier 1: Starter ($19/mo + usage)

| Provider | Model | Cost/1K | Speed | Use Case |
|----------|-------|---------|-------|----------|
| Together | Mixtral 8x22B | $0.002 | Fast | Balanced tasks |
| Fireworks | Qwen 72B | $0.002 | Fast | Code tasks |
| DeepInfra | Llama 3 70B | $0.003 | Medium | General |

### Tier 2: Professional ($49/mo + usage)

| Provider | Model | Cost/1K | Speed | Use Case |
|----------|-------|---------|-------|----------|
| OpenRouter | Claude 3.5 | $0.008 | Medium | Premium tasks |
| OpenRouter | GPT-4o | $0.010 | Medium | Best quality |

### Tier 3: Enterprise ($99/mo + usage)

| Provider | Model | Cost/1K | Speed | Use Case |
|----------|-------|---------|-------|----------|
| Anthropic | Claude 3.5 Sonnet | $0.015 | Fast | Direct access |
| OpenAI | GPT-4o | $0.015 | Fast | Direct access |

---

## Usage

### Basic Usage

```python
from wilmer_router import (
    WilmerRouter,
    RoutingRequest,
    TaskType,
    LatencySLO,
    PowerLevel,
    QualityRequirement,
    get_wilmer_router
)

# Get router instance
router = get_wilmer_router(byok_service, cache_service)

# Create routing request
request = RoutingRequest(
    task_type=TaskType.CODE,
    estimated_tokens=2000,
    latency_slo=LatencySLO.FAST,
    privacy_required=False,
    user_tier="professional",
    credits_remaining=10.0,
    quality_requirement=QualityRequirement.BEST,
    power_level=PowerLevel.BALANCED,
    user_id="user@example.com"
)

# Get provider choice
choice = await router.select_provider(request, user_byok_providers=["openai"])

print(f"Selected: {choice.provider}/{choice.model}")
print(f"Estimated cost: ${choice.estimated_cost:.4f}")
print(f"Reasoning: {choice.reasoning}")
print(f"Fallbacks: {choice.fallback_chain}")
```

### Power Levels

```python
# Eco Mode - Minimize cost
request = RoutingRequest(
    power_level=PowerLevel.ECO,
    # ... other params
)
# Will prefer: local → groq → huggingface

# Balanced Mode - Balance cost/quality
request = RoutingRequest(
    power_level=PowerLevel.BALANCED,
    # ... other params
)
# Will prefer: together → fireworks → openrouter

# Precision Mode - Maximize quality
request = RoutingRequest(
    power_level=PowerLevel.PRECISION,
    # ... other params
)
# Will prefer: anthropic → openai → openrouter
```

### Task-Specific Routing

```python
# Code generation
request = RoutingRequest(
    task_type=TaskType.CODE,
    quality_requirement=QualityRequirement.BEST,
    # ... other params
)
# Routes to: Claude 3.5 or Qwen 72B

# Creative writing
request = RoutingRequest(
    task_type=TaskType.CREATIVE,
    quality_requirement=QualityRequirement.BEST,
    # ... other params
)
# Routes to: Claude 3.5 or GPT-4o

# RAG / Long context
request = RoutingRequest(
    task_type=TaskType.RAG,
    estimated_tokens=50000,
    # ... other params
)
# Routes to: Mixtral 8x22B (65K context)
```

### BYOK Integration

```python
# User has OpenAI API key
user_byok_providers = ["openai", "anthropic"]

# Router will automatically use BYOK if available
choice = await router.select_provider(request, user_byok_providers)

if choice.is_byok:
    print("Using user's API key - free credits!")
    print(f"Estimated cost: ${choice.estimated_cost:.4f}")  # Will be 0.0
```

---

## Model Selection Utilities

### Select Model by Task

```python
from model_selector import select_model_for_task

model = select_model_for_task(
    task_type="code",
    power_level="balanced",
    max_cost=0.01,
    required_capabilities=["code_generation", "function_calling"],
    min_quality=0.8
)

print(f"Selected: {model['key']}")
print(f"Score: {model['score']:.2f}")
print(f"Alternatives: {model['alternatives']}")
```

### Get Models by Capability

```python
from model_selector import get_models_by_capability, ModelCapability

# Find all models with code generation capability
code_models = get_models_by_capability(
    capability="code_generation",
    max_cost=0.01
)

for model in code_models:
    print(f"{model['key']}: {model['quality_score']:.2f} quality")
```

### Compare Models

```python
from model_selector import compare_models

comparison = compare_models([
    "openrouter/claude-3.5",
    "openrouter/gpt-4o",
    "fireworks/qwen-72b"
])

for model in comparison:
    print(f"{model['key']}")
    print(f"  Quality: {model['quality_score']:.2f}")
    print(f"  Speed: {model['speed_score']:.2f}")
    print(f"  Cost: ${model['cost_per_1k']:.4f}/1K")
```

---

## Provider Health Monitoring

### Basic Health Check

```python
from provider_health import get_health_checker

checker = get_health_checker(redis_client)

# Start continuous monitoring
await checker.start_monitoring()

# Get health status
health = await checker.get_health_summary()
print(f"Healthy providers: {health['healthy_providers']}/{health['total_providers']}")

# Check specific provider
is_healthy = await checker.is_provider_healthy("groq")
if is_healthy:
    print("Groq is operational")
```

### Get Healthy Providers

```python
# Get list of currently healthy providers
healthy = await checker.get_healthy_providers()
print(f"Available providers: {healthy}")

# Use in routing decision
if "groq" not in healthy:
    # Fall back to alternative
    pass
```

### Provider Latency

```python
# Get average latency for provider
latency = checker.get_provider_latency("openai")
print(f"OpenAI avg latency: {latency}ms")
```

---

## Fallback Strategy

### Automatic Fallbacks

When a provider fails, WilmerRouter automatically tries fallbacks:

```python
choice = await router.select_provider(request)

# Primary provider
print(f"Primary: {choice.provider}/{choice.model}")

# Fallback chain (automatically used if primary fails)
print(f"Fallbacks: {choice.fallback_chain}")
# Example: ['together/mixtral-8x22b', 'fireworks/qwen-72b', 'local/qwen-32b']
```

### Manual Fallback Selection

```python
# Get fallback chain for specific provider
fallbacks = router.get_fallback_chain("openrouter/claude-3.5", request)

# Try primary, then fallbacks
for provider_key in [choice.provider + "/" + choice.model] + fallbacks:
    try:
        result = await call_llm(provider_key, request)
        break
    except Exception as e:
        logger.warning(f"{provider_key} failed: {e}, trying fallback")
```

---

## Cost Estimation

### Before Making Request

```python
# Estimate cost before execution
estimated_cost = await router.estimate_cost(
    request,
    provider_key="openrouter/claude-3.5"
)

print(f"Estimated cost: ${estimated_cost:.4f}")

# Check if user has enough credits
if request.credits_remaining < estimated_cost:
    # Prompt user to add credits or switch to cheaper provider
    pass
```

### Tier-Based Recommendations

```python
from model_selector import get_tier_recommendations

# Get recommended models for user's tier
recommendations = get_tier_recommendations("professional")

print("Recommended for code tasks:", recommendations["code_tasks"])
print("Recommended for creative:", recommendations["creative_tasks"])
print("Recommended for instant:", recommendations["instant_responses"])
```

---

## Caching

### Routing Decision Cache

WilmerRouter caches routing decisions for 5 minutes to improve performance:

```python
# First request (cache miss)
choice1 = await router.select_provider(request)  # ~50ms

# Identical request (cache hit)
choice2 = await router.select_provider(request)  # ~1ms
```

Cache key includes:
- Task type
- Latency SLO
- Privacy requirement
- User tier
- Power level
- Quality requirement
- Estimated tokens

---

## Configuration

### Add New Provider

To add a new provider, update `PROVIDER_CONFIGS` in `wilmer_router.py`:

```python
PROVIDER_CONFIGS = {
    "new-provider/model-name": {
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

Then add capability info in `model_selector.py`:

```python
MODEL_CAPABILITIES = {
    "new-provider/model-name": {
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

## Performance Optimization

### Redis Caching

Enable Redis caching for improved performance:

```python
import redis.asyncio as redis

# Create Redis client
redis_client = await redis.from_url("redis://unicorn-redis:6379")

# Create router with caching
router = get_wilmer_router(
    byok_service=byok_service,
    cache_service=redis_client
)
```

### Preload Provider Health

Start health monitoring on app startup:

```python
# In app startup
health_checker = get_health_checker(redis_client)
await health_checker.start_monitoring()

# Now routing decisions can use real-time health data
```

---

## Error Handling

### Handle Provider Failures

```python
from wilmer_router import WilmerRouter, RoutingRequest

router = get_wilmer_router()

try:
    choice = await router.select_provider(request)

    # Try primary provider
    result = await call_llm(choice.provider, choice.model, messages)

except Exception as e:
    logger.error(f"Primary provider failed: {e}")

    # Try fallbacks
    for fallback_key in choice.fallback_chain:
        try:
            provider, model = fallback_key.split("/", 1)
            result = await call_llm(provider, model, messages)
            break
        except Exception as fallback_error:
            logger.warning(f"Fallback {fallback_key} failed: {fallback_error}")
            continue
    else:
        raise Exception("All providers failed")
```

---

## Testing

### Unit Tests

```python
import pytest
from wilmer_router import WilmerRouter, RoutingRequest, TaskType, PowerLevel

@pytest.mark.asyncio
async def test_privacy_routing():
    router = WilmerRouter()

    request = RoutingRequest(
        task_type=TaskType.CODE,
        estimated_tokens=2000,
        latency_slo=LatencySLO.NORMAL,
        privacy_required=True,  # Force local
        user_tier="professional",
        credits_remaining=100.0,
        quality_requirement=QualityRequirement.BEST,
        power_level=PowerLevel.BALANCED
    )

    choice = await router.select_provider(request)

    assert choice.provider == "local"
    assert choice.estimated_cost == 0.0
    assert "privacy" in choice.reasoning.lower()
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_byok_override():
    router = WilmerRouter(byok_service=mock_byok_service)

    request = RoutingRequest(
        task_type=TaskType.CREATIVE,
        estimated_tokens=1000,
        latency_slo=LatencySLO.NORMAL,
        privacy_required=False,
        user_tier="professional",
        credits_remaining=10.0,
        quality_requirement=QualityRequirement.BEST,
        power_level=PowerLevel.PRECISION
    )

    # User has OpenAI BYOK
    choice = await router.select_provider(
        request,
        user_byok_providers=["openai"]
    )

    assert choice.is_byok is True
    assert choice.provider == "openai"
    assert choice.estimated_cost == 0.0  # Using user's key
```

---

## Metrics & Logging

### Log Routing Decisions

All routing decisions are logged with context:

```
INFO: Routing decision requested: task=code, latency=fast, privacy=False, tier=professional, power=balanced
INFO: Task routing: Selected fireworks/qwen-72b (cost: $0.0040, quality: best)
```

### Track Provider Usage

```python
# Get provider usage statistics
from collections import defaultdict

provider_usage = defaultdict(int)

# In routing loop
choice = await router.select_provider(request)
provider_usage[choice.provider] += 1

# Log statistics
for provider, count in provider_usage.items():
    print(f"{provider}: {count} requests")
```

---

## Best Practices

1. **Always check BYOK first** - Free credits for users with own keys
2. **Use privacy mode for sensitive data** - Routes to local models
3. **Set realistic latency SLOs** - Instant mode limited to <8K tokens
4. **Monitor provider health** - Start health checker on app startup
5. **Cache routing decisions** - Significant performance improvement
6. **Implement fallbacks** - Handle provider failures gracefully
7. **Estimate costs upfront** - Prevent unexpected credit exhaustion
8. **Use power levels** - Simple UX instead of complex configs

---

## Troubleshooting

### Provider Always Returns Local

**Problem**: Router always selects local models even with credits

**Solution**: Check privacy_required flag
```python
request = RoutingRequest(
    privacy_required=False,  # Make sure this is False
    # ...
)
```

### High Costs

**Problem**: Costs higher than expected

**Solution**: Check power level and quality requirements
```python
request = RoutingRequest(
    power_level=PowerLevel.ECO,  # Use eco mode
    quality_requirement=QualityRequirement.GOOD,  # Not "best"
    # ...
)
```

### Slow Responses

**Problem**: Responses taking too long

**Solution**: Set instant latency SLO
```python
request = RoutingRequest(
    latency_slo=LatencySLO.INSTANT,  # Forces Groq
    estimated_tokens=4000,  # Keep under 8K for Groq
    # ...
)
```

---

## Future Enhancements

1. **ML-Based Routing**: Learn user preferences over time
2. **A/B Testing**: Compare provider quality for same requests
3. **Cost Prediction**: Historical cost analysis for better estimates
4. **Quality Feedback Loop**: Adjust routing based on user ratings
5. **Multi-Provider Responses**: Get responses from multiple providers, return best
6. **Auto-Scaling**: Increase/decrease provider usage based on demand

---

**Last Updated**: October 20, 2025
**Status**: Production Ready
**Next Review**: November 2025
