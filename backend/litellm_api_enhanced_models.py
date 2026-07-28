"""
Enhanced Model Listing Endpoint - Separates BYOK from Platform Models

This module provides an enhanced model listing that clearly distinguishes:
- Models available via user's BYOK keys (no credit charges)
- Models available via platform keys (charged with credits)

Author: Backend Enhancement Team
Date: November 4, 2025
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

# This will be integrated into litellm_api.py


async def list_models_categorized(
    user_id: str,
    byok_manager,
    db_pool
):
    """
    List models categorized by access method (BYOK vs Platform)

    Returns:
        {
            "byok_models": [
                {
                    "provider": "openrouter",
                    "models": [...],
                    "count": 348,
                    "free": true,
                    "note": "Using your OpenRouter API key - no credits charged"
                }
            ],
            "platform_models": [
                {
                    "provider": "openai",
                    "models": [...],
                    "count": 10,
                    "credits_per_1m_tokens": 10.0,
                    "note": "Charged with credits from your account"
                }
            ],
            "summary": {
                "total_models": 358,
                "byok_count": 348,
                "platform_count": 10,
                "has_byok_keys": true,
                "byok_providers": ["openrouter", "huggingface"]
            }
        }
    """
    try:
        # Get user's BYOK providers
        byok_providers_list = await byok_manager.list_user_providers(user_id)
        byok_provider_names = {p['provider'].lower() for p in byok_providers_list if p.get('enabled')}

        # Get all models from database
        async with db_pool.acquire() as conn:
            # Get providers with their API key source
            providers_query = """
                SELECT
                    p.id,
                    p.name,
                    p.type,
                    p.enabled,
                    p.api_key_source,
                    COUNT(m.id) as model_count
                FROM llm_providers p
                LEFT JOIN llm_models m ON p.id = m.provider_id AND m.enabled = true
                WHERE p.enabled = true
                GROUP BY p.id, p.name, p.type, p.enabled, p.api_key_source
            """
            providers = await conn.fetch(providers_query)

            byok_models = []
            platform_models = []

            for provider in providers:
                provider_name = provider['name'].lower()
                provider_type = provider['type']
                model_count = provider['model_count']

                if model_count == 0:
                    continue

                # Get models for this provider
                models_query = """
                    SELECT
                        m.id::text as _uuid,
                        m.name,
                        m.display_name,
                        m.cost_per_1m_input_tokens,
                        m.cost_per_1m_output_tokens,
                        m.context_length,
                        m.enabled,
                        m.avg_latency_ms,
                        m.metadata
                    FROM llm_models m
                    WHERE m.provider_id = $1 AND m.enabled = true
                    ORDER BY m.name
                """
                models = await conn.fetch(models_query, provider['id'])

                models_list = []
                for model in models:
                    model_dict = dict(model)
                    # Add pricing info
                    input_cost = float(model['cost_per_1m_input_tokens'] or 0)
                    output_cost = float(model['cost_per_1m_output_tokens'] or 0)
                    model_dict['pricing'] = {
                        'input': input_cost / 1000000,  # Convert to per-token
                        'output': output_cost / 1000000
                    }
                    model_dict['id'] = model['name']
                    model_dict['object'] = 'model'
                    model_dict['provider'] = provider['name']
                    model_dict['provider_id'] = str(provider['id'])
                    models_list.append(model_dict)

                # Determine if this provider uses BYOK or platform keys
                is_byok = provider_name in byok_provider_names

                provider_info = {
                    'provider': provider['name'],
                    'provider_type': provider_type,
                    'models': models_list,
                    'count': len(models_list)
                }

                if is_byok:
                    provider_info['free'] = True
                    provider_info['note'] = f"Using your {provider['name']} API key - no credits charged"
                    provider_info['source'] = 'byok'
                    byok_models.append(provider_info)
                else:
                    # Calculate average cost
                    if models_list:
                        avg_input_cost = sum(m['pricing']['input'] for m in models_list) / len(models_list)
                        avg_output_cost = sum(m['pricing']['output'] for m in models_list) / len(models_list)
                        provider_info['avg_pricing'] = {
                            'input': avg_input_cost,
                            'output': avg_output_cost
                        }
                    provider_info['note'] = f"Charged with credits from your account"
                    provider_info['source'] = 'platform'
                    platform_models.append(provider_info)

            # Build summary
            total_byok = sum(p['count'] for p in byok_models)
            total_platform = sum(p['count'] for p in platform_models)

            return {
                'byok_models': byok_models,
                'platform_models': platform_models,
                'summary': {
                    'total_models': total_byok + total_platform,
                    'byok_count': total_byok,
                    'platform_count': total_platform,
                    'has_byok_keys': len(byok_provider_names) > 0,
                    'byok_providers': list(byok_provider_names)
                }
            }

    except Exception as e:
        logger.error(f"Error categorizing models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to categorize models")


# Endpoint definition to add to litellm_api.py router:
"""
@router.get("/models/categorized")
async def list_models_categorized_endpoint(
    user_id: str = Depends(get_user_id),
    byok_manager: BYOKManager = Depends(get_byok_manager)
):
    '''
    List models categorized by access method (BYOK vs Platform)

    This endpoint helps users understand:
    - Which models they can use for free (via their BYOK keys)
    - Which models will charge credits (via platform keys)
    - How many models are available in each category

    Returns:
        Dictionary with byok_models, platform_models, and summary
    '''
    return await list_models_categorized(user_id, byok_manager, get_db_pool())
"""
