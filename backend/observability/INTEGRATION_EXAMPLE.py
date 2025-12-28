"""
Observability Integration Example

This file shows how to integrate the observability system into server.py.

STEP-BY-STEP INTEGRATION:

1. Add imports at the top of server.py (after existing imports):

   from observability import setup_observability, get_logger, log_context

2. Replace existing logging setup with observability setup:

   # OLD CODE (remove):
   # logging.basicConfig(level=logging.INFO)
   # logger = logging.getLogger(__name__)

   # NEW CODE (add):
   logger = get_logger(__name__)

3. Add observability setup after app creation:

   app = FastAPI(title="Ops-Center API")

   # Setup observability (one line!)
   observability_config = setup_observability(app)
   logger.info("Observability initialized", config=observability_config)

4. Use structured logging throughout:

   # OLD CODE:
   # logger.info(f"User {user_id} logged in")

   # NEW CODE:
   logger.info("User logged in", user_id=user_id, method="sso")

5. Add correlation IDs to request handlers:

   @app.middleware("http")
   async def add_correlation_id(request: Request, call_next):
       correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

       with log_context(correlation_id=correlation_id):
           response = await call_next(request)
           response.headers["X-Correlation-ID"] = correlation_id
           return response

6. Log business events:

   logger.business_event(
       "credit_purchase",
       user_id=user_id,
       amount=1000,
       payment_method="stripe"
   )

7. Record custom metrics:

   from observability import metrics

   metrics.credit_transactions_total.labels(
       transaction_type="purchase",
       user_id=user_id,
       organization_id=org_id
   ).inc()

8. Add tracing to critical functions:

   from observability import trace_request, add_span_attribute

   @trace_request("process_payment")
   async def process_payment(user_id: str, amount: float):
       add_span_attribute("payment.amount", amount)
       # ... payment logic
       return result
"""

# ============================================================================
# COMPLETE EXAMPLE: Minimal server.py changes
# ============================================================================

"""
from fastapi import FastAPI, Request
from observability import setup_observability, get_logger, log_context
import uuid

# Create logger (replaces standard logging)
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(title="Ops-Center API")

# Setup observability (SINGLE LINE!)
observability_config = setup_observability(app)
logger.info("Observability system initialized", config=observability_config)

# Add correlation ID middleware
@app.middleware("http")
async def add_correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

    # Set correlation ID for all logs in this request
    with log_context(correlation_id=correlation_id):
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

# Continue with existing routes...
@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Ops-Center API"}

# That's it! You now have:
# - Structured JSON logging
# - 40+ Prometheus metrics at /metrics
# - Health checks at /health, /health/ready, /health/detailed
# - Distributed tracing (if configured)
"""

# ============================================================================
# EXAMPLE: Using observability features in existing code
# ============================================================================

"""
from observability import get_logger, log_context, metrics, trace_request, add_span_attribute

logger = get_logger(__name__)

# Example 1: Credit purchase with full observability
@trace_request("purchase_credits")
async def purchase_credits(user_id: str, amount: int, org_id: str, tier: str):
    # Set log context for this operation
    with log_context(user_id=user_id):
        # Add trace attributes
        add_span_attribute("credit.amount", amount)
        add_span_attribute("organization.id", org_id)

        # Log business event
        logger.business_event(
            "credit_purchase_initiated",
            user_id=user_id,
            amount=amount,
            organization_id=org_id
        )

        try:
            # Process payment
            payment = await process_stripe_payment(user_id, amount)

            # Update credits
            new_balance = await add_credits_to_user(user_id, amount)

            # Record metrics
            metrics.credit_transactions_total.labels(
                transaction_type="purchase",
                user_id=user_id,
                organization_id=org_id
            ).inc()

            metrics.credit_balance.labels(
                user_id=user_id,
                organization_id=org_id,
                tier=tier
            ).set(new_balance)

            # Log success
            logger.business_event(
                "credit_purchase_completed",
                user_id=user_id,
                amount=amount,
                new_balance=new_balance
            )

            return {"success": True, "balance": new_balance}

        except Exception as e:
            # Log error
            logger.error(
                "Credit purchase failed",
                user_id=user_id,
                amount=amount,
                error=str(e)
            )

            # Record error metric
            metrics.payment_transactions_total.labels(
                status="failed",
                payment_method="stripe",
                tier=tier
            ).inc()

            raise

# Example 2: LLM request with metrics
from observability.metrics import record_llm_usage

@trace_request("llm_chat_completion")
async def llm_chat_completion(model: str, messages: list, user_id: str, org_id: str):
    start_time = time.time()

    try:
        # Call LiteLLM
        response = await litellm.acompletion(model=model, messages=messages)

        # Calculate metrics
        duration = time.time() - start_time
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        cost_credits = calculate_cost(model, prompt_tokens, completion_tokens)

        # Record comprehensive LLM metrics (helper function)
        record_llm_usage(
            model=model,
            provider=response.model.split('/')[0],
            user_id=user_id,
            organization_id=org_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            duration_seconds=duration,
            cost_credits=cost_credits,
            status="success"
        )

        return response

    except Exception as e:
        duration = time.time() - start_time

        # Record error
        record_llm_usage(
            model=model,
            provider="unknown",
            user_id=user_id,
            organization_id=org_id,
            prompt_tokens=0,
            completion_tokens=0,
            duration_seconds=duration,
            cost_credits=0,
            status="error"
        )

        logger.error("LLM request failed", model=model, error=str(e))
        raise
"""

# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================

"""
Add to .env.auth or set in Docker environment:

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Tracing (optional)
OTEL_EXPORTER_TYPE=console  # Options: console, jaeger, otlp
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Service info
OPS_CENTER_VERSION=2.3.0
GIT_COMMIT=abc123
BUILD_DATE=2025-11-12
ENVIRONMENT=production
"""

# ============================================================================
# VERIFICATION
# ============================================================================

"""
After integration, verify observability is working:

1. Check health endpoints:
   curl http://localhost:8084/health
   curl http://localhost:8084/health/ready
   curl http://localhost:8084/health/detailed | jq

2. Check metrics:
   curl http://localhost:8084/metrics

3. Check logs (JSON format):
   docker logs ops-center-direct --tail 20

4. Generate traffic:
   curl http://localhost:8084/api/v1/admin/users
   curl http://localhost:8084/api/v1/billing/plans

5. Check metrics updated:
   curl http://localhost:8084/metrics | grep ops_center_http_requests_total

6. Check correlation IDs in logs:
   docker logs ops-center-direct | jq '.correlation_id'

SUCCESS! You now have full observability!
"""

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
If something doesn't work:

1. Dependencies not installed:
   cd backend && pip install -r requirements.txt

2. Import errors:
   - Check observability/ directory exists
   - Check __init__.py is present
   - Try: python -c "from observability import setup_observability; print('OK')"

3. Health checks return 503:
   - Check PostgreSQL is running: docker ps | grep postgresql
   - Check Redis is running: docker ps | grep redis
   - Check Keycloak is running: docker ps | grep keycloak

4. Metrics not updating:
   - Generate traffic to endpoints
   - Metrics are only recorded when requests are made

5. Logs not in JSON format:
   - Check setup_observability() was called
   - Check LOG_LEVEL environment variable

6. Tracing not working:
   - OpenTelemetry is optional, system works without it
   - Check OTEL_EXPORTER_TYPE is set
   - Try OTEL_EXPORTER_TYPE=console to see traces in logs

For more help, see docs/OBSERVABILITY_GUIDE.md
"""
