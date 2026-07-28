---
name: litellm-management
description: Check LiteLLM status, list models, and assist with key rotation
actions:
  - name: health_check
    description: Check LiteLLM proxy health endpoint
    confirmation_required: false
    parameters: {}

  - name: list_models
    description: List models from LiteLLM /v1/models
    confirmation_required: false
    parameters: {}

  - name: generate_master_key
    description: Generate a new LiteLLM master key (does not apply it)
    confirmation_required: false
    parameters: {}
---
LiteLLM management for unicorn-litellm-wilmer and the Wilmer router.
Uses the proxy API on port 4000 for health and model listing.

Safety level: Low (read-only; key generation is non-destructive).

Example invocations:
- "Check LiteLLM health"
- "List LiteLLM models"
- "Generate a new LiteLLM master key"

Expected outputs:
- Health status JSON
- Model list payload (OpenAI-compatible)
- Newly generated key string with next steps
