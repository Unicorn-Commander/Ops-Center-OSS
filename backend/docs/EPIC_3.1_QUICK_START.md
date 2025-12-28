# Epic 3.1: LiteLLM Multi-Provider Routing - Quick Start Guide

**Last Updated**: October 23, 2025
**For**: Backend Developers
**Epic**: 3.1 - LiteLLM Multi-Provider Routing

---

## Overview

This guide helps you quickly get started with the LiteLLM Multi-Provider Routing system.

---

## Installation

### 1. Database Migration

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/backend

# Create migration
alembic revision --autogenerate -m "Add LLM infrastructure tables"

# Review migration
cat alembic/versions/XXXX_add_llm_infrastructure_tables.py

# Apply migration
alembic upgrade head

# Verify tables
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt llm_*"
```

### 2. Environment Variables

Add to `.env.auth`:
```bash
# LiteLLM Configuration
LITELLM_PROXY_URL=http://unicorn-litellm:4000
LITELLM_MASTER_KEY=<your-master-key>

# Encryption (for BYOK)
ENCRYPTION_KEY=<your-encryption-key>
```

---

## Quick Examples

### 1. Create a Provider

```python
from sqlalchemy.orm import Session
from models.llm_models import LLMProvider
from datetime import datetime

def create_openai_provider(db: Session):
    provider = LLMProvider(
        provider_name='OpenAI',
        provider_slug='openai',
        display_name='OpenAI',
        description='OpenAI LLM provider',
        base_url='https://api.openai.com/v1',
        auth_type='bearer',
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        is_active=True,
        is_byok_supported=True,
        is_system_provider=True,
        api_key_format='sk-*',
        documentation_url='https://platform.openai.com/docs',
        pricing_url='https://openai.com/pricing',
        min_tier_required='free',
        health_status='unknown',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(provider)
    db.commit()
    db.refresh(provider)

    return provider
```

### 2. Create a Model

```python
from models.llm_models import LLMModel

def create_gpt4_model(db: Session, provider_id: int):
    model = LLMModel(
        provider_id=provider_id,
        model_name='GPT-4 Turbo',
        model_id='gpt-4-turbo-preview',
        display_name='GPT-4 Turbo',
        description='Latest GPT-4 Turbo model',
        max_tokens=4096,
        context_window=128000,
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=False,
        supports_json_mode=True,
        cost_per_1m_input_tokens=10.00,    # $10 per 1M tokens
        cost_per_1m_output_tokens=30.00,   # $30 per 1M tokens
        power_level='precision',
        power_level_priority=1,  # Highest priority
        is_active=True,
        is_deprecated=False,
        min_tier_required='professional',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(model)
    db.commit()
    db.refresh(model)

    return model
```

### 3. Create Routing Rule

```python
from models.llm_models import LLMRoutingRule

def create_routing_rule(db: Session, model_id: int):
    rule = LLMRoutingRule(
        model_id=model_id,
        power_level='precision',
        user_tier='professional',
        task_type='code',
        priority=1,
        weight=100,
        min_tokens=None,
        max_tokens=None,
        requires_byok=False,
        is_fallback=False,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)

    return rule
```

### 4. Use Routing Engine

```python
from llm_routing_engine import LLMRoutingEngine

def route_llm_request(db: Session, user_id: str):
    # Initialize routing engine
    engine = LLMRoutingEngine(db)

    # Select model
    model, api_key, key_source = engine.select_model(
        user_id=user_id,
        user_tier='professional',
        power_level='balanced',
        task_type='chat',
        estimated_tokens=1000,
        require_streaming=True
    )

    if not model:
        print("No model available")
        return

    print(f"Selected: {model.model_name}")
    print(f"Provider: {model.provider.provider_name}")
    print(f"Key source: {key_source}")

    # Calculate estimated cost
    cost = engine.calculate_cost(
        model=model,
        prompt_tokens=800,
        completion_tokens=200,
        cached_tokens=0
    )

    print(f"Estimated cost: ${cost['cost_total_usd']:.6f}")

    return model, api_key, key_source
```

### 5. Add User API Key (BYOK)

```python
from models.llm_models import UserAPIKey
from secret_manager import get_secret_manager

def add_user_api_key(db: Session, user_id: str, provider_id: int, api_key: str):
    # Encrypt API key
    secret_mgr = get_secret_manager()
    encrypted = secret_mgr.encrypt_secret(
        secret=api_key,
        secret_type='user_api_key',
        metadata={'user_id': user_id, 'provider_id': provider_id}
    )

    # Store in database
    user_key = UserAPIKey(
        user_id=user_id,
        provider_id=provider_id,
        key_name='My OpenAI Key',
        encrypted_api_key=encrypted['encrypted_value'],
        key_prefix=api_key[:8],
        key_suffix=api_key[-4:],
        is_active=True,
        is_validated=False,  # Validate separately
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(user_key)
    db.commit()
    db.refresh(user_key)

    return user_key
```

### 6. Log Usage

```python
from llm_routing_engine import LLMRoutingEngine
import uuid

def log_llm_usage(db: Session, user_id: str, model, prompt_tokens: int, completion_tokens: int):
    engine = LLMRoutingEngine(db)

    # Calculate cost
    cost = engine.calculate_cost(
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cached_tokens=0
    )

    # Log usage
    usage_log_id = engine.log_usage(
        user_id=user_id,
        model=model,
        request_id=str(uuid.uuid4()),
        power_level='balanced',
        task_type='chat',
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cached_tokens=0,
        cost_breakdown=cost,
        used_byok=False,
        user_key_id=None,
        latency_ms=1500,
        status_code=200,
        request_ip='192.168.1.1',
        user_agent='Mozilla/5.0'
    )

    print(f"Usage logged with ID: {usage_log_id}")
    return usage_log_id
```

---

## API Usage

### List Providers

```bash
curl -X GET "http://localhost:8084/api/v1/admin/llm/providers" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Create Provider

```bash
curl -X POST "http://localhost:8084/api/v1/admin/llm/providers" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_name": "Anthropic",
    "provider_slug": "anthropic",
    "display_name": "Anthropic",
    "base_url": "https://api.anthropic.com/v1",
    "auth_type": "api_key",
    "supports_streaming": true,
    "supports_function_calling": true,
    "is_byok_supported": true,
    "min_tier_required": "starter"
  }'
```

### Check Provider Health

```bash
curl -X GET "http://localhost:8084/api/v1/admin/llm/providers/1/health" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## Database Queries

### Find Models by Power Level

```sql
SELECT m.model_name, m.power_level, p.provider_name
FROM llm_models m
JOIN llm_providers p ON m.provider_id = p.id
WHERE m.power_level = 'balanced'
  AND m.is_active = true
ORDER BY m.power_level_priority;
```

### User Usage Statistics

```sql
SELECT
    user_id,
    COUNT(*) as total_requests,
    SUM(total_tokens) as total_tokens,
    SUM(cost_total_usd) as total_cost,
    AVG(latency_ms) as avg_latency,
    SUM(CASE WHEN used_byok THEN 1 ELSE 0 END) as byok_requests
FROM llm_usage_logs
WHERE user_id = 'user-uuid'
  AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY user_id;
```

### Top Cost Models

```sql
SELECT
    m.model_name,
    p.provider_name,
    COUNT(*) as request_count,
    SUM(l.cost_total_usd) as total_cost,
    AVG(l.cost_total_usd) as avg_cost_per_request
FROM llm_usage_logs l
JOIN llm_models m ON l.model_id = m.id
JOIN llm_providers p ON m.provider_id = p.id
WHERE l.created_at >= NOW() - INTERVAL '7 days'
GROUP BY m.model_name, p.provider_name
ORDER BY total_cost DESC
LIMIT 10;
```

### Routing Rules for User Tier

```sql
SELECT
    r.power_level,
    r.user_tier,
    r.task_type,
    r.priority,
    m.model_name,
    p.provider_name
FROM llm_routing_rules r
JOIN llm_models m ON r.model_id = m.id
JOIN llm_providers p ON m.provider_id = p.id
WHERE r.user_tier = 'professional'
  AND r.is_active = true
ORDER BY r.power_level, r.priority;
```

---

## Common Tasks

### Seed Initial Data

```python
def seed_llm_data(db: Session):
    """Seed initial LLM providers, models, and routing rules"""

    # 1. Create OpenAI provider
    openai = create_openai_provider(db)

    # 2. Create GPT-4 model
    gpt4 = create_gpt4_model(db, openai.id)

    # 3. Create routing rules for all tiers
    for tier in ['free', 'starter', 'professional', 'enterprise']:
        for power_level in ['eco', 'balanced', 'precision']:
            priority = {'eco': 3, 'balanced': 2, 'precision': 1}[power_level]

            rule = LLMRoutingRule(
                model_id=gpt4.id,
                power_level=power_level,
                user_tier=tier,
                task_type='general',
                priority=priority,
                weight=100,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(rule)

    db.commit()
    print("✅ Seeded LLM data")
```

### Update Model Pricing

```python
def update_model_pricing(db: Session, model_id: int, input_cost: float, output_cost: float):
    """Update model pricing"""

    model = db.query(LLMModel).filter(LLMModel.id == model_id).first()
    if not model:
        print(f"Model {model_id} not found")
        return

    model.cost_per_1m_input_tokens = input_cost
    model.cost_per_1m_output_tokens = output_cost
    model.updated_at = datetime.utcnow()

    db.commit()
    print(f"✅ Updated pricing for {model.model_name}")
```

### Deprecate Old Model

```python
def deprecate_model(db: Session, old_model_id: int, new_model_id: int):
    """Deprecate old model and suggest replacement"""

    old_model = db.query(LLMModel).filter(LLMModel.id == old_model_id).first()
    if not old_model:
        print(f"Model {old_model_id} not found")
        return

    old_model.is_deprecated = True
    old_model.deprecation_date = datetime.utcnow()
    old_model.replacement_model_id = new_model_id
    old_model.is_active = False  # Disable routing
    old_model.updated_at = datetime.utcnow()

    db.commit()
    print(f"✅ Deprecated {old_model.model_name}")
```

---

## Troubleshooting

### No Models Selected

**Problem**: `select_model()` returns `None`

**Solutions**:
1. Check routing rules exist:
   ```sql
   SELECT * FROM llm_routing_rules WHERE is_active = true;
   ```

2. Verify models are active:
   ```sql
   SELECT * FROM llm_models WHERE is_active = true;
   ```

3. Check power level constraints:
   ```python
   # Eco power level has strict cost limits ($0.50/1M tokens)
   # Try 'balanced' instead
   model, _, _ = engine.select_model(user_id, 'professional', 'balanced')
   ```

---

### BYOK Key Not Working

**Problem**: User's API key not being used

**Solutions**:
1. Verify key is validated:
   ```sql
   SELECT * FROM user_api_keys WHERE user_id = 'user-uuid' AND is_validated = true;
   ```

2. Test key manually:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $USER_API_KEY"
   ```

3. Re-validate key:
   ```python
   user_key.is_validated = True
   user_key.last_validated_at = datetime.utcnow()
   db.commit()
   ```

---

### High Costs

**Problem**: Unexpected high costs

**Solutions**:
1. Analyze usage by model:
   ```sql
   SELECT model_id, SUM(cost_total_usd) as total_cost
   FROM llm_usage_logs
   WHERE created_at >= NOW() - INTERVAL '7 days'
   GROUP BY model_id
   ORDER BY total_cost DESC;
   ```

2. Switch to eco power level:
   ```python
   model, _, _ = engine.select_model(user_id, user_tier, 'eco')  # Force cheaper models
   ```

3. Adjust routing priorities to prefer cheaper models

---

## Testing

### Unit Test Example

```python
def test_routing_engine_select_model():
    """Test model selection"""
    from llm_routing_engine import LLMRoutingEngine

    # Setup
    db = get_test_db()
    provider = create_openai_provider(db)
    model = create_gpt4_model(db, provider.id)
    rule = create_routing_rule(db, model.id)

    # Execute
    engine = LLMRoutingEngine(db)
    selected_model, api_key, key_source = engine.select_model(
        user_id='test-user',
        user_tier='professional',
        power_level='precision',
        task_type='code'
    )

    # Assert
    assert selected_model is not None
    assert selected_model.id == model.id
    assert key_source in ['system', 'byok']
```

---

## Next Steps

1. **Implement remaining APIs**:
   - Model Management API
   - BYOK API
   - Enhanced LiteLLM Proxy

2. **Create frontend**:
   - Provider management UI
   - Model configuration UI
   - BYOK configuration UI

3. **Set up monitoring**:
   - Usage dashboards
   - Cost alerts
   - Performance metrics

---

## Resources

- **Full Documentation**: `EPIC_3.1_BACKEND_IMPLEMENTATION.md`
- **Database Models**: `backend/models/llm_models.py`
- **Routing Engine**: `backend/llm_routing_engine.py`
- **Provider API**: `backend/llm_provider_management_api.py`

---

**Last Updated**: October 23, 2025
**Author**: Backend API Developer
