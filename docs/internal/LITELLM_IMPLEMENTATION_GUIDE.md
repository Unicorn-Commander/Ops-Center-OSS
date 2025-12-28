# LiteLLM + WilmerAI Implementation Guide

**Status**: ✅ Architecture Complete - Ready for Implementation
**Version**: 1.0.0
**Date**: October 20, 2025

---

## Quick Start for Implementation Teams

This guide provides a fast-track to implementing the LiteLLM + WilmerAI multi-provider LLM routing system.

---

## Architecture Deliverables

All architecture specifications have been completed and are ready for implementation:

### 1. **Docker Configuration** ✅
**File**: `/services/ops-center/docker-compose.litellm.yml`
- LiteLLM proxy container configuration
- WilmerAI router container configuration
- Network and volume setup
- Environment variable references

### 2. **LiteLLM Configuration** ✅
**File**: `/services/ops-center/litellm_config.yaml`
- 25+ models across 9 providers configured
- Free tier: Local (vLLM, Ollama), Groq, HuggingFace
- Starter tier: Together AI, Fireworks AI, DeepInfra
- Professional tier: OpenRouter (Claude, GPT-4)
- Enterprise tier: Direct Anthropic, OpenAI access
- Fallback chains for all use cases
- Rate limiting per subscription tier
- Cost tracking and logging

### 3. **Provider Strategy** ✅
**File**: `/docs/LITELLM_PROVIDER_STRATEGY.md` (20KB)
- Provider tier breakdown (Free, Starter, Pro, Enterprise)
- Selection decision matrix by task type
- Use case routing rules (code, chat, RAG, creative, analysis)
- Cost optimization strategies
- Performance benchmarks
- Fallback chain specifications
- BYOK integration strategy

### 4. **WilmerAI Router Specification** ✅
**File**: `/docs/LITELLM_WILMER_ROUTING_SPEC.md` (40KB)
- Complete router architecture
- Decision tree pseudocode (production-ready)
- Power level mappings (Eco, Balanced, Precision)
- Credit calculation formulas
- 5 example routing scenarios
- Quality feedback loop design
- Implementation module specifications

### 5. **Final Architecture** ✅
**File**: `/docs/LITELLM_ARCHITECTURE_FINAL.md` (60KB)
- System overview and component architecture
- Complete data flow diagrams
- Integration points with Ops-Center
- Database schema (4 new tables)
- API specifications (10+ endpoints)
- Security & compliance guidelines
- Deployment architecture
- Monitoring & observability setup
- 4-week implementation roadmap

---

## Implementation Phases

### **Phase 1: Infrastructure Setup** (Days 1-3)

#### Backend Team Tasks:

**1. Create Database Tables**
```bash
# Run migration script
cd /home/muut/Production/UC-Cloud/services/ops-center
docker exec ops-center-direct psql -U unicorn -d unicorn_db -f migrations/001_litellm_tables.sql
```

**SQL to execute** (see architecture doc for full schema):
```sql
CREATE TABLE user_credits (...);
CREATE TABLE credit_transactions (...);
CREATE TABLE credit_reservations (...);
CREATE TABLE llm_quality_metrics (...);
CREATE TABLE provider_health (...);
```

**2. Set Environment Variables**
```bash
# Add to .env.litellm
LITELLM_MASTER_KEY=<generate-secure-key>
OPENROUTER_API_KEY=<obtain-from-openrouter>
TOGETHER_API_KEY=<obtain-from-together>
FIREWORKS_API_KEY=<obtain-from-fireworks>
GROQ_API_KEY=<obtain-from-groq>
DEEPINFRA_API_KEY=<obtain-from-deepinfra>
HUGGINGFACE_API_KEY=<obtain-from-huggingface>
OPENAI_API_KEY=<optional-for-enterprise>
ANTHROPIC_API_KEY=<optional-for-enterprise>
```

**3. Deploy LiteLLM Proxy**
```bash
cd /home/muut/Production/UC-Cloud/services/ops-center
docker compose -f docker-compose.litellm.yml up -d litellm-proxy

# Verify
curl http://localhost:4000/health
```

**4. Test LiteLLM**
```bash
# Test free tier (Groq)
curl -X POST http://localhost:4000/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "groq/llama3-70b-8192",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# Test local model
curl -X POST http://localhost:4000/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/Qwen2.5-32B-Instruct-AWQ",
    "messages": [{"role": "user", "content": "Write a Python function"}]
  }'
```

---

### **Phase 2: WilmerAI Router** (Days 4-7)

#### Backend Team Tasks:

**1. Create WilmerAI Directory Structure**
```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/backend
mkdir -p wilmer
cd wilmer

# Create module files (see routing spec for pseudocode)
touch __init__.py
touch context_analyzer.py    # Request analysis
touch user_context.py         # User data retrieval
touch router.py               # Main routing logic
touch cost_calculator.py      # Credit calculations
touch litellm_client.py       # LiteLLM proxy client
touch quality_tracker.py      # Quality metrics
```

**2. Implement Core Modules**

Reference the pseudocode in `LITELLM_WILMER_ROUTING_SPEC.md` sections:
- **Decision Tree Pseudocode** → `router.py`
- **Power Level Mappings** → `router.py`
- **Credit Calculation Formulas** → `cost_calculator.py`

**3. Create WilmerAI API**
```python
# wilmer/server.py
from fastapi import FastAPI
from router import WilmerRouter

app = FastAPI()
router = WilmerRouter()

@app.post("/route")
async def route_request(request: RoutingRequest):
    decision = router.route_request(request)
    return decision

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

**4. Create Dockerfile for WilmerAI**
```dockerfile
# backend/Dockerfile.wilmer
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY wilmer/ ./wilmer/
CMD ["uvicorn", "wilmer.server:app", "--host", "0.0.0.0", "--port", "4001"]
```

**5. Deploy WilmerAI Router**
```bash
docker compose -f docker-compose.litellm.yml up -d wilmer-router

# Test
curl http://localhost:4001/health
```

---

### **Phase 3: Credits System** (Days 8-10)

#### Backend Team Tasks:

**1. Implement Credit Manager**
```python
# backend/credits_manager.py

class CreditManager:
    async def get_balance(self, user_id: str) -> float:
        """Get user's current credit balance"""
        pass

    async def reserve_credits(self, user_id: str, amount: float) -> str:
        """Reserve credits before request (returns reservation_id)"""
        pass

    async def deduct_credits(self, reservation_id: str, actual_cost: float):
        """Deduct actual credits after completion"""
        pass

    async def purchase_credits(self, user_id: str, amount: float, payment_method_id: str):
        """Purchase credits via Stripe"""
        pass
```

**2. Integrate with Lago**
```python
# In credits_manager.py
from lago_integration import LagoClient

async def sync_usage_to_lago(self, user_id: str):
    """Send usage events to Lago for billing"""
    usage = await self.get_usage_summary(user_id, period="month")

    await self.lago.send_usage_event(
        external_customer_id=user_id,
        transaction_id=f"llm_{user_id}_{month}",
        code="llm_tokens",
        properties={
            "tokens_used": usage.total_tokens,
            "api_calls": usage.total_requests,
            "cost": usage.total_cost
        }
    )
```

---

### **Phase 4: Ops-Center Integration** (Days 11-14)

#### Backend Team Tasks:

**1. Add LLM Endpoints to server.py**
```python
# backend/server.py

from wilmer.router import WilmerRouter
from credits_manager import CreditManager

router = WilmerRouter()
credit_mgr = CreditManager()

@app.post("/api/v1/llm/chat/completions")
async def llm_chat_completions(
    request: ChatCompletionRequest,
    user: dict = Depends(get_current_user)
):
    """OpenAI-compatible endpoint with WilmerAI routing"""
    # See architecture doc for full implementation
    pass

@app.get("/api/v1/llm/models")
async def list_models(user: dict = Depends(get_current_user)):
    """List available models for user's tier"""
    pass

@app.get("/api/v1/llm/usage")
async def get_usage(
    period: str = "month",
    user: dict = Depends(get_current_user)
):
    """Get usage statistics"""
    pass

@app.post("/api/v1/credits/purchase")
async def purchase_credits(
    request: PurchaseRequest,
    user: dict = Depends(get_current_user)
):
    """Purchase credits via Stripe"""
    pass

@app.get("/api/v1/credits/balance")
async def get_credit_balance(user: dict = Depends(get_current_user)):
    """Get current credit balance"""
    pass
```

**2. Test Integration**
```bash
# Test routing through Ops-Center
curl -X POST https://your-domain.com/api/v1/llm/chat/completions \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Write Python code to sort a list"}],
    "power_level": "balanced"
  }'
```

---

### **Phase 5: Frontend** (Days 15-18)

#### Frontend Team Tasks:

**1. Create LLM Management Page**
```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/src/pages
touch LLMManagement.jsx
```

**Components needed**:
- **Provider Status Cards** - Show all 9 providers, health, latency
- **Model Selector** - Dropdown to select specific model (or "auto")
- **Usage Dashboard** - Charts showing usage by provider, cost trends
- **Credit Balance Widget** - Display current balance, monthly budget

**2. Create Power Level Selector Component**
```jsx
// src/components/PowerLevelSelector.jsx

export default function PowerLevelSelector({ value, onChange }) {
  return (
    <div className="power-level-selector">
      <button
        className={value === 'eco' ? 'active' : ''}
        onClick={() => onChange('eco')}
      >
        Eco Mode
        <span className="cost">$0.001/req</span>
      </button>
      <button
        className={value === 'balanced' ? 'active' : ''}
        onClick={() => onChange('balanced')}
      >
        Balanced Mode
        <span className="cost">$0.01/req</span>
      </button>
      <button
        className={value === 'precision' ? 'active' : ''}
        onClick={() => onChange('precision')}
      >
        Precision Mode
        <span className="cost">$0.1/req</span>
      </button>
    </div>
  );
}
```

**3. Add LLM Chat Interface**
```jsx
// src/components/LLMChat.jsx

import { useState } from 'react';
import PowerLevelSelector from './PowerLevelSelector';

export default function LLMChat() {
  const [messages, setMessages] = useState([]);
  const [powerLevel, setPowerLevel] = useState('balanced');
  const [input, setInput] = useState('');

  const sendMessage = async () => {
    const response = await fetch('/api/v1/llm/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        messages: [...messages, { role: 'user', content: input }],
        power_level: powerLevel
      })
    });

    const data = await response.json();
    const providerUsed = response.headers.get('X-Provider-Used');
    const costIncurred = response.headers.get('X-Cost-Incurred');

    // Add to messages with metadata
    setMessages([
      ...messages,
      { role: 'user', content: input },
      {
        role: 'assistant',
        content: data.choices[0].message.content,
        metadata: { provider: providerUsed, cost: costIncurred }
      }
    ]);
  };

  return (
    <div>
      <PowerLevelSelector value={powerLevel} onChange={setPowerLevel} />
      {/* Chat UI */}
    </div>
  );
}
```

**4. Build and Deploy**
```bash
cd /home/muut/Production/UC-Cloud/services/ops-center
npm run build
cp -r dist/* public/
docker restart ops-center-direct
```

---

## Testing Checklist

### Unit Tests
- [ ] Context analyzer detects task types correctly
- [ ] Cost calculator computes credits accurately
- [ ] Router selects correct provider for each scenario
- [ ] Credit reservations prevent overspend
- [ ] BYOK keys used when available

### Integration Tests
- [ ] LiteLLM proxy routes to all 9 providers
- [ ] WilmerAI router communicates with LiteLLM
- [ ] Credits deducted correctly after requests
- [ ] Fallback chains work on provider failure
- [ ] Quality metrics logged properly

### End-to-End Tests
- [ ] Free user gets free models only
- [ ] Starter user accesses mid-tier models
- [ ] Professional user gets premium models
- [ ] Enterprise user uses direct APIs
- [ ] BYOK user routes to their providers
- [ ] Power levels change routing behavior
- [ ] Credit purchases update balance
- [ ] Monthly budget caps enforced

---

## Launch Checklist

### Pre-Launch
- [ ] All 9 provider API keys configured
- [ ] Database tables created and indexed
- [ ] LiteLLM proxy deployed and healthy
- [ ] WilmerAI router deployed and healthy
- [ ] Ops-Center endpoints functional
- [ ] Frontend UI complete
- [ ] Documentation published
- [ ] Monitoring dashboards configured
- [ ] Alerts set up

### Launch Day
- [ ] Enable LLM features for beta users
- [ ] Monitor error rates closely
- [ ] Track cost vs revenue
- [ ] Collect user feedback
- [ ] Fix critical bugs immediately

### Post-Launch (Week 1)
- [ ] Analyze usage patterns
- [ ] Optimize routing weights
- [ ] Adjust pricing if needed
- [ ] Roll out to all users
- [ ] Publish success metrics

---

## Key Metrics to Track

### Business
- Monthly recurring revenue from LLM features
- Credits purchased per user tier
- BYOK adoption rate
- User satisfaction (NPS, ratings)

### Technical
- Average cost per request by tier
- Platform cost vs user revenue (target: <50%)
- P95 latency by provider
- Error rate by provider
- Cache hit rate

### User Behavior
- Power level distribution (eco/balanced/precision)
- Popular models by use case
- Task type distribution
- Average tokens per request

---

## Support Resources

### Documentation
- **Provider Strategy**: `/docs/LITELLM_PROVIDER_STRATEGY.md`
- **Router Spec**: `/docs/LITELLM_WILMER_ROUTING_SPEC.md`
- **Architecture**: `/docs/LITELLM_ARCHITECTURE_FINAL.md`
- **Docker Config**: `/services/ops-center/docker-compose.litellm.yml`
- **LiteLLM Config**: `/services/ops-center/litellm_config.yaml`

### Troubleshooting
- **Provider fails**: Check API key in `.env.litellm`
- **Routing incorrect**: Review WilmerAI logs at `/app/logs/wilmer.log`
- **Credits not deducting**: Check PostgreSQL `credit_reservations` table
- **High latency**: Check LiteLLM metrics at `http://localhost:4000/metrics`

### Getting Help
- Architecture questions: See architecture docs
- Implementation questions: See routing spec pseudocode
- Integration questions: See architecture integration section
- Deployment questions: See docker-compose.litellm.yml

---

## Success Criteria

### Phase 1 Complete When:
- ✅ LiteLLM proxy healthy and routing to all providers
- ✅ All database tables created
- ✅ Environment variables configured

### Phase 2 Complete When:
- ✅ WilmerAI router making intelligent routing decisions
- ✅ All power levels working correctly
- ✅ Quality metrics being tracked

### Phase 3 Complete When:
- ✅ Credits system functional
- ✅ Lago integration syncing usage
- ✅ Stripe purchases working

### Phase 4 Complete When:
- ✅ Ops-Center `/api/v1/llm/*` endpoints working
- ✅ BYOK integration functional
- ✅ End-to-end flow tested

### Phase 5 Complete When:
- ✅ Frontend UI complete
- ✅ Users can chat with power level selection
- ✅ Usage dashboard showing statistics
- ✅ Credit balance widget displaying correctly

### LAUNCH READY When:
- ✅ All phases complete
- ✅ All tests passing
- ✅ Monitoring operational
- ✅ Documentation published
- ✅ Beta users onboarded successfully

---

## Revenue Projections

### Conservative (3 months)
- 100 paid users
- Average $20/month spend
- **Total**: $2,000/month revenue

### Moderate (6 months)
- 300 paid users
- Average $35/month spend
- **Total**: $10,500/month revenue

### Aggressive (12 months)
- 1,000 paid users
- Average $50/month spend
- **Total**: $50,000/month revenue

**Platform costs** (assuming 50% margin):
- 3-month: $1,000/month
- 6-month: $5,250/month
- 12-month: $25,000/month

---

## Questions?

All specifications are complete and stored in memory for agent coordination.

**Architecture ready for implementation!** 🚀

**Next Steps**:
1. Backend team starts Phase 1 (database + LiteLLM deployment)
2. Backend team continues with Phase 2 (WilmerAI router)
3. Frontend team prepares for Phase 5 (UI components)
4. DevOps monitors deployments

**Target Launch**: 4 weeks from start

---

**Document Status**: ✅ IMPLEMENTATION READY
