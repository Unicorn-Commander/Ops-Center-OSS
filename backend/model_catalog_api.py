"""
Model Catalog API - Enhanced model management for LLM Hub

This module provides comprehensive model catalog endpoints:
- List all models from all providers (OpenRouter, OpenAI, Anthropic, Google)
- Advanced filtering and search
- Model details with capabilities and pricing
- Toggle model enable/disable status
- Model usage statistics and analytics
- Provider aggregation and management
- Model caching for performance

Author: Backend Developer
Date: October 27, 2025
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from functools import lru_cache
import time
import json

import httpx
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from pydantic import BaseModel, Field
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/v1/llm", tags=["Model Catalog"])

# Encryption key for API keys
BYOK_ENCRYPTION_KEY = os.getenv('BYOK_ENCRYPTION_KEY')

# ============================================================================
# Provider Configurations
# ============================================================================

PROVIDER_CONFIGS = {
    'openrouter': {
        'base_url': 'https://openrouter.ai/api/v1',
        'api_url': 'https://openrouter.ai/api/v1/models',
        'requires_auth': False,  # Public API
        'default_headers': {
            'HTTP-Referer': 'https://your-domain.com',
            'X-Title': 'UC-1 Pro Ops Center'
        },
        'display_name': 'OpenRouter',
        'description': 'Universal LLM proxy - 200+ models'
    },
    'openai': {
        'base_url': 'https://api.openai.com/v1',
        'api_url': 'https://api.openai.com/v1/models',
        'requires_auth': True,
        'default_headers': {},
        'display_name': 'OpenAI',
        'description': 'GPT-4, GPT-4o, o1, DALL-E 3'
    },
    'anthropic': {
        'base_url': 'https://api.anthropic.com/v1',
        'api_url': None,  # Hardcoded models
        'requires_auth': False,
        'default_headers': {
            'anthropic-version': '2023-06-01'
        },
        'display_name': 'Anthropic',
        'description': 'Claude 3.5 Sonnet, Opus, Haiku'
    },
    'google': {
        'base_url': 'https://generativelanguage.googleapis.com/v1beta',
        'api_url': 'https://generativelanguage.googleapis.com/v1beta/models',
        'requires_auth': True,
        'default_headers': {},
        'display_name': 'Google AI',
        'description': 'Gemini 2.0 Flash, 1.5 Pro'
    }
}

# Hardcoded Anthropic models (no public API)
ANTHROPIC_MODELS = [
    {
        'id': 'claude-3-5-sonnet-20241022',
        'name': 'Claude 3.5 Sonnet',
        'description': 'Most intelligent Claude model with improved agentic coding and vision capabilities',
        'context_length': 200000,
        'capabilities': ['text', 'vision', 'function_calling'],
        'pricing': {'input': 3.00, 'output': 15.00}  # Per 1M tokens
    },
    {
        'id': 'claude-3-5-haiku-20241022',
        'name': 'Claude 3.5 Haiku',
        'description': 'Fastest and most compact Claude model for near-instant responsiveness',
        'context_length': 200000,
        'capabilities': ['text', 'vision', 'function_calling'],
        'pricing': {'input': 1.00, 'output': 5.00}
    },
    {
        'id': 'claude-3-opus-20240229',
        'name': 'Claude 3 Opus',
        'description': 'Powerful model for highly complex tasks',
        'context_length': 200000,
        'capabilities': ['text', 'vision'],
        'pricing': {'input': 15.00, 'output': 75.00}
    },
    {
        'id': 'claude-3-sonnet-20240229',
        'name': 'Claude 3 Sonnet',
        'description': 'Balance of intelligence and speed',
        'context_length': 200000,
        'capabilities': ['text', 'vision'],
        'pricing': {'input': 3.00, 'output': 15.00}
    },
    {
        'id': 'claude-3-haiku-20240307',
        'name': 'Claude 3 Haiku',
        'description': 'Fastest and most compact Claude model',
        'context_length': 200000,
        'capabilities': ['text', 'vision'],
        'pricing': {'input': 0.25, 'output': 1.25}
    }
]

# ============================================================================
# Request/Response Models
# ============================================================================

class ModelFilters(BaseModel):
    """Model filtering parameters"""
    provider: Optional[str] = Field(None, description="Filter by provider (openrouter, openai, anthropic, google)")
    search: Optional[str] = Field(None, description="Search model name or description")
    capability: Optional[str] = Field(None, description="Filter by capability (vision, function_calling, streaming)")
    enabled: Optional[bool] = Field(None, description="Filter by enabled status")
    sort: str = Field("name", description="Sort by: name, price, context_length, popularity")
    limit: int = Field(100, ge=1, le=1000, description="Results per page")
    offset: int = Field(0, ge=0, description="Pagination offset")


class ModelDetail(BaseModel):
    """Detailed model information"""
    id: str
    provider: str
    name: str
    description: Optional[str]
    capabilities: List[str]
    context_length: int
    pricing: Dict[str, float]
    enabled: bool
    access_level: Optional[str] = None
    top_provider: Optional[Dict] = None
    architecture: Optional[str] = None


class ModelStats(BaseModel):
    """Model catalog statistics"""
    total_models: int
    enabled_count: int
    disabled_count: int
    avg_price_per_1m: float
    most_used: List[Dict]
    providers: List[str]


# ============================================================================
# Database Helper Functions
# ============================================================================

async def get_db_pool(request: Request):
    """Get database pool from app state"""
    credit_system = request.app.state.credit_system
    return credit_system.db_pool


async def get_provider_id_by_name(pool, provider_name: str) -> Optional[str]:
    """Get provider ID by name"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id FROM llm_providers
            WHERE LOWER(name) = LOWER($1)
        """, provider_name)
        return str(row['id']) if row else None


async def get_models_from_db(pool) -> List[Dict]:
    """Get all models from database with enabled status"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                m.name,
                m.enabled,
                m.cost_per_1m_input_tokens,
                m.cost_per_1m_output_tokens,
                m.context_length,
                m.metadata,
                p.name as provider_name,
                p.id as provider_id
            FROM llm_models m
            JOIN llm_providers p ON m.provider_id = p.id
            WHERE p.enabled = TRUE
        """)

        return [
            {
                'name': row['name'],
                'enabled': row['enabled'],
                'cost_per_1m_input': float(row['cost_per_1m_input_tokens']) if row['cost_per_1m_input_tokens'] else 0,
                'cost_per_1m_output': float(row['cost_per_1m_output_tokens']) if row['cost_per_1m_output_tokens'] else 0,
                'context_length': row['context_length'] or 0,
                'metadata': row['metadata'] or {},
                'provider_name': row['provider_name'],
                'provider_id': str(row['provider_id'])
            }
            for row in rows
        ]


async def get_model_usage_stats(pool, days: int = 30) -> Dict[str, int]:
    """Get model usage statistics"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                model_name,
                COUNT(*) as usage_count,
                SUM(total_tokens) as total_tokens,
                SUM(cost) as total_cost
            FROM llm_usage_logs
            WHERE created_at >= NOW() - INTERVAL '%s days'
            GROUP BY model_name
            ORDER BY usage_count DESC
            LIMIT 10
        """ % days)

        return {
            row['model_name']: {
                'usage_count': row['usage_count'],
                'total_tokens': row['total_tokens'] or 0,
                'total_cost': float(row['total_cost']) if row['total_cost'] else 0.0
            }
            for row in rows
        }


# ============================================================================
# Provider Fetching Functions
# ============================================================================

async def fetch_openrouter_models() -> List[Dict]:
    """Fetch models from OpenRouter API"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                PROVIDER_CONFIGS['openrouter']['api_url'],
                headers=PROVIDER_CONFIGS['openrouter']['default_headers']
            )

            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.status_code}")
                return []

            data = response.json().get('data', [])

            models = []
            for model in data:
                pricing = model.get('pricing', {})
                architecture = model.get('architecture', {})

                # Parse capabilities from architecture
                capabilities = ['text']  # All models support text
                modality = architecture.get('modality', '').lower()
                if 'vision' in modality or 'multimodal' in modality:
                    capabilities.append('vision')
                if 'tool' in modality or 'function' in modality:
                    capabilities.append('function_calling')

                models.append({
                    'id': f"openrouter/{model.get('id')}",
                    'provider': 'openrouter',
                    'name': model.get('name', model.get('id')),
                    'description': model.get('description', ''),
                    'context_length': model.get('context_length', 0),
                    'pricing': {
                        'input': float(pricing.get('prompt', 0)) * 1_000_000,  # Convert to per 1M
                        'output': float(pricing.get('completion', 0)) * 1_000_000
                    },
                    'capabilities': capabilities,
                    'top_provider': model.get('top_provider', {}),
                    'architecture': architecture.get('modality', 'text')
                })

            logger.info(f"Fetched {len(models)} models from OpenRouter")
            return models

    except Exception as e:
        logger.error(f"Failed to fetch OpenRouter models: {e}")
        return []


async def fetch_openai_models(api_key: str) -> List[Dict]:
    """Fetch models from OpenAI API (if key configured)"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                PROVIDER_CONFIGS['openai']['api_url'],
                headers={'Authorization': f'Bearer {api_key}'}
            )

            if response.status_code != 200:
                logger.warning(f"OpenAI API error: {response.status_code}")
                return []

            data = response.json().get('data', [])

            models = []
            for model in data:
                model_id = model.get('id')

                # Only include chat models
                if not any(x in model_id for x in ['gpt-', 'o1-', 'o3-']):
                    continue

                # Determine capabilities
                capabilities = ['text']
                if 'vision' in model_id or 'gpt-4o' in model_id:
                    capabilities.append('vision')
                if 'gpt-4' in model_id or 'gpt-3.5' in model_id:
                    capabilities.append('function_calling')

                # Estimate pricing (hardcoded - OpenAI doesn't provide this via API)
                pricing = {'input': 0, 'output': 0}
                if 'gpt-4o' in model_id:
                    pricing = {'input': 5.00, 'output': 15.00}
                elif 'gpt-4' in model_id:
                    pricing = {'input': 30.00, 'output': 60.00}
                elif 'gpt-3.5' in model_id:
                    pricing = {'input': 0.50, 'output': 1.50}
                elif 'o1' in model_id:
                    pricing = {'input': 15.00, 'output': 60.00}

                models.append({
                    'id': f"openai/{model_id}",
                    'provider': 'openai',
                    'name': model_id,
                    'description': f"OpenAI {model_id}",
                    'context_length': model.get('context_length', 8192),
                    'pricing': pricing,
                    'capabilities': capabilities,
                    'top_provider': None,
                    'architecture': 'text'
                })

            logger.info(f"Fetched {len(models)} models from OpenAI")
            return models

    except Exception as e:
        logger.error(f"Failed to fetch OpenAI models: {e}")
        return []


async def fetch_anthropic_models() -> List[Dict]:
    """Fetch Anthropic models (hardcoded list)"""
    models = []
    for model in ANTHROPIC_MODELS:
        models.append({
            'id': f"anthropic/{model['id']}",
            'provider': 'anthropic',
            'name': model['name'],
            'description': model['description'],
            'context_length': model['context_length'],
            'pricing': {
                'input': model['pricing']['input'],
                'output': model['pricing']['output']
            },
            'capabilities': model['capabilities'],
            'top_provider': None,
            'architecture': 'multimodal' if 'vision' in model['capabilities'] else 'text'
        })

    logger.info(f"Loaded {len(models)} Anthropic models")
    return models


async def fetch_google_models(api_key: str) -> List[Dict]:
    """Fetch models from Google AI API (if key configured)"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{PROVIDER_CONFIGS['google']['api_url']}?key={api_key}"
            )

            if response.status_code != 200:
                logger.warning(f"Google AI API error: {response.status_code}")
                return []

            data = response.json().get('models', [])

            models = []
            for model in data:
                model_id = model.get('name', '').replace('models/', '')

                # Only include Gemini models
                if not model_id.startswith('gemini'):
                    continue

                # Determine capabilities
                capabilities = ['text']
                supported_methods = model.get('supportedGenerationMethods', [])
                if 'generateContent' in supported_methods:
                    capabilities.append('vision')

                # Estimate pricing (hardcoded)
                pricing = {'input': 0, 'output': 0}
                if 'gemini-2.0' in model_id:
                    pricing = {'input': 0.075, 'output': 0.30}
                elif 'gemini-1.5-pro' in model_id:
                    pricing = {'input': 3.50, 'output': 10.50}
                elif 'gemini-1.5-flash' in model_id:
                    pricing = {'input': 0.075, 'output': 0.30}

                models.append({
                    'id': f"google/{model_id}",
                    'provider': 'google',
                    'name': model.get('displayName', model_id),
                    'description': model.get('description', ''),
                    'context_length': model.get('inputTokenLimit', 32768),
                    'pricing': pricing,
                    'capabilities': capabilities,
                    'top_provider': None,
                    'architecture': 'multimodal'
                })

            logger.info(f"Fetched {len(models)} models from Google AI")
            return models

    except Exception as e:
        logger.error(f"Failed to fetch Google AI models: {e}")
        return []


async def get_provider_api_key(pool, provider_name: str) -> Optional[str]:
    """Get provider API key from database (encrypted)"""
    if not BYOK_ENCRYPTION_KEY:
        logger.warning("BYOK_ENCRYPTION_KEY not configured")
        return None

    try:
        cipher = Fernet(BYOK_ENCRYPTION_KEY.encode())

        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT api_key_encrypted, name
                FROM llm_providers
                WHERE LOWER(name) = LOWER($1) AND enabled = TRUE
            """, provider_name)

            if not row or not row['api_key_encrypted']:
                # Try environment variable fallback
                env_var = f"{provider_name.upper().replace('-', '_')}_API_KEY"
                return os.getenv(env_var)

            # Decrypt
            return cipher.decrypt(row['api_key_encrypted'].encode()).decode()

    except Exception as e:
        logger.error(f"Failed to get API key for {provider_name}: {e}")
        return None


# ============================================================================
# Caching Layer
# ============================================================================

# Cache for model catalog (5-minute TTL)
_model_cache = {
    'timestamp': 0,
    'models': [],
    'ttl': 300  # 5 minutes
}


async def get_all_models_cached(pool, force_refresh: bool = False) -> List[Dict]:
    """
    Get all models from all providers with caching

    Cache TTL: 5 minutes
    """
    global _model_cache

    now = time.time()
    cache_valid = (now - _model_cache['timestamp']) < _model_cache['ttl']

    if cache_valid and not force_refresh and _model_cache['models']:
        logger.info(f"Using cached models ({len(_model_cache['models'])} models)")
        return _model_cache['models']

    # Fetch fresh data
    logger.info("Fetching fresh model catalog...")
    models = []

    # Always fetch OpenRouter (public API)
    models.extend(await fetch_openrouter_models())

    # Always fetch Anthropic (hardcoded)
    models.extend(await fetch_anthropic_models())

    # Fetch OpenAI if key configured
    openai_key = await get_provider_api_key(pool, 'openai')
    if openai_key:
        models.extend(await fetch_openai_models(openai_key))

    # Fetch Google if key configured
    google_key = await get_provider_api_key(pool, 'google')
    if google_key:
        models.extend(await fetch_google_models(google_key))

    # Merge with database status (enabled/disabled)
    db_models = await get_models_from_db(pool)
    db_models_dict = {m['name']: m for m in db_models}

    for model in models:
        # Try to match by full ID or just the model part
        model_id = model['id']
        model_name = model_id.split('/', 1)[1] if '/' in model_id else model_id

        db_match = db_models_dict.get(model_id) or db_models_dict.get(model_name)

        if db_match:
            model['enabled'] = db_match['enabled']
            # Override pricing if set in DB
            if db_match['cost_per_1m_input'] > 0:
                model['pricing']['input'] = db_match['cost_per_1m_input']
            if db_match['cost_per_1m_output'] > 0:
                model['pricing']['output'] = db_match['cost_per_1m_output']
        else:
            # Not in DB yet - default to disabled
            model['enabled'] = False

    # Update cache
    _model_cache['timestamp'] = now
    _model_cache['models'] = models

    logger.info(f"Cached {len(models)} models from all providers")
    return models


# ============================================================================
# Admin Session Authentication
# ============================================================================

async def require_admin(request: Request) -> Dict:
    """Require admin role from session"""
    session_token = request.cookies.get("session_token")

    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sessions = getattr(request.app.state, "sessions", {})
    session_data = sessions.get(session_token)

    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = session_data.get("user", {})
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/models/stats")
async def get_model_stats(request: Request):
    """
    Get model catalog statistics

    Returns:
        - Total models
        - Enabled/disabled counts
        - Average pricing
        - Most used models
        - Provider breakdown

    Example:
        GET /api/v1/llm/models/stats
    """
    try:
        pool = await get_db_pool(request)

        # Get all models
        all_models = await get_all_models_cached(pool)

        # Calculate stats
        total_models = len(all_models)
        enabled_count = sum(1 for m in all_models if m['enabled'])
        disabled_count = total_models - enabled_count

        # Calculate average price (only models with pricing > 0)
        prices = [m['pricing'].get('input', 0) for m in all_models if m['pricing'].get('input', 0) > 0]
        avg_price_per_1m = sum(prices) / len(prices) if prices else 0.0

        # Get usage stats
        usage_stats = await get_model_usage_stats(pool, days=30)
        most_used = [
            {
                'model_id': model_name,
                'usage_count': stats['usage_count'],
                'total_tokens': stats['total_tokens'],
                'total_cost': stats['total_cost']
            }
            for model_name, stats in sorted(
                usage_stats.items(),
                key=lambda x: x[1]['usage_count'],
                reverse=True
            )[:10]
        ]

        # Provider breakdown
        provider_counts = {}
        for model in all_models:
            provider = model['provider']
            if provider not in provider_counts:
                provider_counts[provider] = {'total': 0, 'enabled': 0}
            provider_counts[provider]['total'] += 1
            if model['enabled']:
                provider_counts[provider]['enabled'] += 1

        return {
            'total_models': total_models,
            'enabled_count': enabled_count,
            'disabled_count': disabled_count,
            'avg_price_per_1m': round(avg_price_per_1m, 2),
            'most_used': most_used,
            'providers': provider_counts
        }

    except Exception as e:
        logger.error(f"Error getting model stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/models")
async def list_models(
    request: Request,
    provider: Optional[str] = Query(None, description="Filter by provider"),
    search: Optional[str] = Query(None, description="Search name/description"),
    capability: Optional[str] = Query(None, description="Filter by capability"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    sort: str = Query("name", description="Sort by: name, price, context_length"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    List all models from all configured providers

    Fetches models from:
    - OpenRouter (always, public API)
    - Anthropic (always, hardcoded list)
    - OpenAI (if key configured)
    - Google AI (if key configured)

    Returns unified list with enabled status from database

    Example:
        GET /api/v1/llm/models?provider=openrouter&capability=vision&enabled=true&sort=price
    """
    try:
        pool = await get_db_pool(request)

        # Get all models (cached)
        all_models = await get_all_models_cached(pool)

        # Apply filters
        filtered_models = all_models.copy()

        if provider:
            filtered_models = [m for m in filtered_models if m['provider'] == provider.lower()]

        if search:
            search_lower = search.lower()
            filtered_models = [
                m for m in filtered_models
                if search_lower in m['name'].lower() or search_lower in m.get('description', '').lower()
            ]

        if capability:
            filtered_models = [
                m for m in filtered_models
                if capability.lower() in [c.lower() for c in m.get('capabilities', [])]
            ]

        if enabled is not None:
            filtered_models = [m for m in filtered_models if m['enabled'] == enabled]

        # Sort
        if sort == 'price':
            filtered_models.sort(key=lambda m: m['pricing'].get('input', 0))
        elif sort == 'context_length':
            filtered_models.sort(key=lambda m: m.get('context_length', 0), reverse=True)
        else:  # name
            filtered_models.sort(key=lambda m: m['name'].lower())

        # Pagination
        total = len(filtered_models)
        paginated_models = filtered_models[offset:offset + limit]

        # Get unique providers
        providers = list(set(m['provider'] for m in all_models))

        # Return OpenAI-compatible format
        return {
            'object': 'list',
            'data': paginated_models,
            'total': total,
            'limit': limit,
            'offset': offset,
            'providers': sorted(providers)
        }

    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.get("/models/{model_id:path}")
async def get_model_details(
    model_id: str,
    request: Request
):
    """
    Get detailed information about a specific model

    Args:
        model_id: Model identifier (format: "provider/model-name" or just "model-name")

    Returns:
        Detailed model information including specs, pricing, capabilities

    Example:
        GET /api/v1/llm/models/openrouter/anthropic/claude-3.5-sonnet
    """
    try:
        pool = await get_db_pool(request)

        # Get all models
        all_models = await get_all_models_cached(pool)

        # Find model
        model = next((m for m in all_models if m['id'] == model_id), None)

        if not model:
            # Try without provider prefix
            model = next((m for m in all_models if m['id'].endswith(f"/{model_id}")), None)

        if not model:
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

        # Get usage stats for this model
        usage_stats = await get_model_usage_stats(pool, days=30)
        model_usage = usage_stats.get(model['id'], usage_stats.get(model_id, {}))

        return {
            **model,
            'usage_stats': {
                'usage_count': model_usage.get('usage_count', 0),
                'total_tokens': model_usage.get('total_tokens', 0),
                'total_cost': model_usage.get('total_cost', 0.0)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get model details: {str(e)}")


@router.post("/models/{model_id:path}/toggle")
async def toggle_model(
    model_id: str,
    enabled: bool,
    request: Request,
    admin: Dict = Depends(require_admin)
):
    """
    Enable or disable a model (admin only)

    Args:
        model_id: Model identifier
        enabled: New enabled status

    Returns:
        Updated model status

    Example:
        POST /api/v1/llm/models/openrouter/anthropic/claude-3.5-sonnet/toggle
        Body: {"enabled": true}
    """
    try:
        pool = await get_db_pool(request)

        # Extract provider and model name
        if '/' in model_id:
            parts = model_id.split('/', 1)
            provider_name = parts[0]
            model_name = parts[1] if len(parts) > 1 else model_id
        else:
            provider_name = 'openrouter'  # Default
            model_name = model_id

        # Get provider ID
        provider_id = await get_provider_id_by_name(pool, provider_name)
        if not provider_id:
            raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")

        async with pool.acquire() as conn:
            # Check if model exists in DB
            existing = await conn.fetchrow("""
                SELECT id, enabled FROM llm_models
                WHERE provider_id = $1 AND name = $2
            """, provider_id, model_name)

            if existing:
                # Update existing model
                await conn.execute("""
                    UPDATE llm_models
                    SET enabled = $1, updated_at = NOW()
                    WHERE provider_id = $2 AND name = $3
                """, enabled, provider_id, model_name)

                logger.info(f"Admin {admin.get('email')} {'enabled' if enabled else 'disabled'} model {model_id}")
            else:
                # Insert new model
                await conn.execute("""
                    INSERT INTO llm_models (
                        provider_id, name, display_name, enabled, created_at, updated_at
                    )
                    VALUES ($1, $2, $2, $3, NOW(), NOW())
                """, provider_id, model_name, enabled)

                logger.info(f"Admin {admin.get('email')} created and {'enabled' if enabled else 'disabled'} model {model_id}")

        # Clear cache to force refresh
        global _model_cache
        _model_cache['timestamp'] = 0

        return {
            'success': True,
            'model_id': model_id,
            'enabled': enabled,
            'message': f"Model {'enabled' if enabled else 'disabled'} successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling model {model_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to toggle model: {str(e)}")


@router.post("/models/refresh")
async def refresh_model_catalog(
    request: Request,
    admin: Dict = Depends(require_admin)
):
    """
    Force refresh model catalog cache (admin only)

    Returns:
        Number of models refreshed

    Example:
        POST /api/v1/llm/models/refresh
    """
    try:
        pool = await get_db_pool(request)

        # Force refresh
        models = await get_all_models_cached(pool, force_refresh=True)

        logger.info(f"Admin {admin.get('email')} refreshed model catalog ({len(models)} models)")

        return {
            'success': True,
            'total_models': len(models),
            'message': 'Model catalog refreshed successfully'
        }

    except Exception as e:
        logger.error(f"Error refreshing model catalog: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to refresh catalog: {str(e)}")


@router.get("/providers")
async def list_providers(request: Request):
    """
    List all supported providers with configuration details

    Returns provider information including:
    - Display name
    - Description
    - API configuration status
    - Available models count

    Example:
        GET /api/v1/llm/providers
    """
    try:
        pool = await get_db_pool(request)

        providers = []
        for provider_key, config in PROVIDER_CONFIGS.items():
            # Check if API key is configured
            api_key = await get_provider_api_key(pool, provider_key)
            has_key = api_key is not None

            # Get model count for this provider
            all_models = await get_all_models_cached(pool)
            model_count = sum(1 for m in all_models if m['provider'] == provider_key)
            enabled_count = sum(1 for m in all_models if m['provider'] == provider_key and m['enabled'])

            providers.append({
                'name': provider_key,
                'display_name': config['display_name'],
                'description': config['description'],
                'requires_auth': config['requires_auth'],
                'has_api_key': has_key,
                'total_models': model_count,
                'enabled_models': enabled_count,
                'base_url': config['base_url']
            })

        return {'providers': providers}

    except Exception as e:
        logger.error(f"Error listing providers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list providers: {str(e)}")
