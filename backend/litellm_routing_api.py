"""
LiteLLM Routing and Provider Management API

This module provides comprehensive multi-provider LLM routing with:
- WilmerAI-style cost/latency optimization
- BYOK (Bring Your Own Key) support
- User power levels (Eco/Balanced/Precision)
- Provider health monitoring
- Usage analytics and cost tracking
- Dynamic routing rules

Author: Backend API Developer
Date: October 23, 2025
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import asyncio

from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel, Field, validator
import httpx
from cryptography.fernet import Fernet
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import redis

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/v1/llm", tags=["LLM Management"])

# Environment variables
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "unicorn-postgresql")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "unicorn")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "unicorn")
POSTGRES_DB = os.getenv("POSTGRES_DB", "unicorn_db")

REDIS_HOST = os.getenv("REDIS_HOST", "unicorn-lago-redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

LITELLM_PROXY_URL = os.getenv("LITELLM_PROXY_URL", "http://unicorn-litellm:4000")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())

# Encryption handler
cipher_suite = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

# Redis client
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
except Exception as e:
    logger.error(f"Redis connection failed: {e}")
    redis_client = None


# ============================================================================
# Database Schema Initialization
# ============================================================================

def init_database():
    """Initialize database tables for LiteLLM routing"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Providers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_providers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100) NOT NULL,
                type VARCHAR(50) NOT NULL,
                api_key_encrypted TEXT,
                api_base_url TEXT,
                enabled BOOLEAN DEFAULT true,
                priority INTEGER DEFAULT 0,
                config JSONB DEFAULT '{}',
                health_status VARCHAR(20) DEFAULT 'unknown',
                last_health_check TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(name, type)
            )
        """)

        # Models table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_models (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                provider_id UUID REFERENCES llm_providers(id) ON DELETE CASCADE,
                name VARCHAR(200) NOT NULL,
                display_name VARCHAR(200),
                cost_per_1m_input_tokens DECIMAL(10, 4),
                cost_per_1m_output_tokens DECIMAL(10, 4),
                context_length INTEGER,
                enabled BOOLEAN DEFAULT true,
                metadata JSONB DEFAULT '{}',
                avg_latency_ms INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(provider_id, name)
            )
        """)

        # Routing rules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_routing_rules (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                strategy VARCHAR(50) NOT NULL DEFAULT 'balanced',
                fallback_providers UUID[] DEFAULT '{}',
                model_aliases JSONB DEFAULT '{}',
                config JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # User LLM settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_llm_settings (
                user_id VARCHAR(100) PRIMARY KEY,
                power_level VARCHAR(20) DEFAULT 'balanced',
                byok_providers JSONB DEFAULT '{}',
                credit_balance DECIMAL(10, 2) DEFAULT 0,
                preferences JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Usage tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_usage_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(100) NOT NULL,
                provider_id UUID REFERENCES llm_providers(id),
                model_name VARCHAR(200),
                input_tokens INTEGER,
                output_tokens INTEGER,
                cost DECIMAL(10, 6),
                latency_ms INTEGER,
                power_level VARCHAR(20),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_providers_enabled ON llm_providers(enabled)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_models_enabled ON llm_models(enabled)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_usage_user ON llm_usage_logs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_usage_created ON llm_usage_logs(created_at)")

        # Insert default routing rule if none exists
        cursor.execute("SELECT COUNT(*) FROM llm_routing_rules")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO llm_routing_rules (strategy, config)
                VALUES ('balanced', %s)
            """, (Json({
                "cost_weight": 0.4,
                "latency_weight": 0.4,
                "quality_weight": 0.2,
                "max_retries": 3,
                "retry_delay_ms": 500
            }),))

        conn.commit()
        logger.info("LiteLLM routing database tables initialized successfully")

    except Exception as e:
        conn.rollback()
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def get_db_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB
    )


# ============================================================================
# Request/Response Models
# ============================================================================

class ProviderType:
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    TOGETHER = "together"
    HUGGINGFACE = "huggingface"
    GOOGLE = "google"
    COHERE = "cohere"
    CUSTOM = "custom"


class PowerLevel:
    ECO = "eco"           # Cost optimized
    BALANCED = "balanced" # Balance cost and quality
    PRECISION = "precision" # Quality optimized


class ProviderCreate(BaseModel):
    name: str = Field(..., description="Provider name")
    type: str = Field(..., description="Provider type (openrouter, openai, anthropic, etc.)")
    api_key: str = Field(..., description="API key (will be encrypted)")
    api_base_url: Optional[str] = Field(None, description="Custom API base URL")
    enabled: bool = Field(True, description="Enable provider")
    priority: int = Field(0, description="Routing priority (higher = more preferred)")
    config: Dict = Field(default_factory=dict, description="Provider-specific configuration")

    @validator('type')
    def validate_type(cls, v):
        valid_types = [ProviderType.OPENROUTER, ProviderType.OPENAI, ProviderType.ANTHROPIC,
                      ProviderType.TOGETHER, ProviderType.HUGGINGFACE, ProviderType.GOOGLE,
                      ProviderType.COHERE, ProviderType.CUSTOM]
        if v not in valid_types:
            raise ValueError(f"Invalid provider type. Must be one of: {', '.join(valid_types)}")
        return v


class ProviderUpdate(BaseModel):
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    config: Optional[Dict] = None


class ProviderResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str
    models: int
    avg_cost_per_1m: Optional[float]
    enabled_models: List[str]
    priority: int
    health_status: str
    last_health_check: Optional[datetime]


class ModelCreate(BaseModel):
    provider_id: str
    name: str
    display_name: Optional[str] = None
    cost_per_1m_input_tokens: Decimal
    cost_per_1m_output_tokens: Decimal
    context_length: int
    enabled: bool = True
    metadata: Dict = Field(default_factory=dict)


class ModelResponse(BaseModel):
    id: str
    provider_id: str
    provider_name: str
    name: str
    display_name: str
    cost_per_1m_input: float
    cost_per_1m_output: float
    context_length: int
    enabled: bool
    avg_latency_ms: Optional[int]


class RoutingStrategy:
    COST = "cost"         # Cheapest model
    LATENCY = "latency"   # Fastest model
    BALANCED = "balanced" # Balance cost and latency
    CUSTOM = "custom"     # Custom weighted scoring


class RoutingRulesUpdate(BaseModel):
    strategy: str = Field(..., description="Routing strategy")
    fallback_providers: List[str] = Field(default_factory=list, description="Fallback provider IDs")
    model_aliases: Dict[str, str] = Field(default_factory=dict, description="Model alias mappings")
    config: Dict = Field(default_factory=dict, description="Strategy-specific configuration")

    @validator('strategy')
    def validate_strategy(cls, v):
        valid_strategies = [RoutingStrategy.COST, RoutingStrategy.LATENCY,
                          RoutingStrategy.BALANCED, RoutingStrategy.CUSTOM]
        if v not in valid_strategies:
            raise ValueError(f"Invalid strategy. Must be one of: {', '.join(valid_strategies)}")
        return v


class UserBYOKUpdate(BaseModel):
    provider_type: str
    api_key: str
    enabled: bool = True
    preferences: Dict = Field(default_factory=dict)


class ProviderTestRequest(BaseModel):
    provider_id: str
    model: Optional[str] = None


# ============================================================================
# Provider Management Endpoints
# ============================================================================

@router.get("/providers", response_model=List[ProviderResponse])
async def list_providers(
    enabled_only: bool = False,
    request: Request = None
):
    """
    List all configured LLM providers

    Query Parameters:
        enabled_only: Only return enabled providers

    Returns:
        List of providers with statistics
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        query = """
            SELECT
                p.id,
                p.name,
                p.type,
                p.enabled,
                p.priority,
                p.health_status,
                p.last_health_check,
                COUNT(m.id) as model_count,
                AVG((m.cost_per_1m_input_tokens + m.cost_per_1m_output_tokens) / 2) as avg_cost,
                ARRAY_AGG(m.name) FILTER (WHERE m.enabled = true) as enabled_models
            FROM llm_providers p
            LEFT JOIN llm_models m ON p.id = m.provider_id
        """

        if enabled_only:
            query += " WHERE p.enabled = true"

        query += """
            GROUP BY p.id, p.name, p.type, p.enabled, p.priority, p.health_status, p.last_health_check
            ORDER BY p.priority DESC, p.name
        """

        cursor.execute(query)
        providers = cursor.fetchall()

        result = []
        for p in providers:
            result.append(ProviderResponse(
                id=str(p['id']),
                name=p['name'],
                type=p['type'],
                status='active' if p['enabled'] else 'disabled',
                models=p['model_count'] or 0,
                avg_cost_per_1m=float(p['avg_cost']) if p['avg_cost'] else None,
                enabled_models=p['enabled_models'] or [],
                priority=p['priority'],
                health_status=p['health_status'] or 'unknown',
                last_health_check=p['last_health_check']
            ))

        return result

    finally:
        cursor.close()
        conn.close()


@router.post("/providers", response_model=Dict)
async def create_provider(provider: ProviderCreate):
    """
    Add new LLM provider with encrypted API key

    Body:
        ProviderCreate schema

    Returns:
        Created provider with ID
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Encrypt API key
        encrypted_key = cipher_suite.encrypt(provider.api_key.encode()).decode()

        # Determine API base URL if not provided
        api_base_url = provider.api_base_url
        if not api_base_url:
            api_base_url = get_default_base_url(provider.type)

        cursor.execute("""
            INSERT INTO llm_providers (name, type, api_key_encrypted, api_base_url, enabled, priority, config)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, name, type, enabled, priority
        """, (
            provider.name,
            provider.type,
            encrypted_key,
            api_base_url,
            provider.enabled,
            provider.priority,
            Json(provider.config)
        ))

        result = cursor.fetchone()
        conn.commit()

        # Test provider connection
        provider_id = str(result['id'])
        asyncio.create_task(test_provider_health(provider_id))

        return {
            "id": provider_id,
            "name": result['name'],
            "type": result['type'],
            "enabled": result['enabled'],
            "priority": result['priority'],
            "message": "Provider created successfully. Testing connection..."
        }

    except psycopg2.IntegrityError as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Provider with this name and type already exists")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to create provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.put("/providers/{provider_id}", response_model=Dict)
async def update_provider(provider_id: str, update: ProviderUpdate):
    """
    Update provider configuration

    Path Parameters:
        provider_id: Provider UUID

    Body:
        ProviderUpdate schema

    Returns:
        Updated provider info
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Build update query dynamically
        updates = []
        params = []

        if update.api_key is not None:
            encrypted_key = cipher_suite.encrypt(update.api_key.encode()).decode()
            updates.append("api_key_encrypted = %s")
            params.append(encrypted_key)

        if update.api_base_url is not None:
            updates.append("api_base_url = %s")
            params.append(update.api_base_url)

        if update.enabled is not None:
            updates.append("enabled = %s")
            params.append(update.enabled)

        if update.priority is not None:
            updates.append("priority = %s")
            params.append(update.priority)

        if update.config is not None:
            updates.append("config = %s")
            params.append(Json(update.config))

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = NOW()")
        params.append(provider_id)

        query = f"""
            UPDATE llm_providers
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING id, name, type, enabled, priority
        """

        cursor.execute(query, params)
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Provider not found")

        conn.commit()

        return {
            "id": str(result['id']),
            "name": result['name'],
            "type": result['type'],
            "enabled": result['enabled'],
            "priority": result['priority'],
            "message": "Provider updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.delete("/providers/{provider_id}")
async def delete_provider(provider_id: str):
    """
    Remove provider (will cascade delete associated models)

    Path Parameters:
        provider_id: Provider UUID

    Returns:
        Deletion confirmation
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM llm_providers WHERE id = %s RETURNING id", (provider_id,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Provider not found")

        conn.commit()

        return {"message": "Provider deleted successfully", "id": provider_id}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to delete provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# ============================================================================
# Model Management Endpoints
# ============================================================================

@router.get("/models")
async def list_models(
    provider_id: Optional[str] = None,
    enabled_only: bool = False,
    sort_by: str = "cost",  # cost, latency, name, context, popularity
    search: Optional[str] = None,
    min_cost: Optional[float] = None,
    max_cost: Optional[float] = None,
    min_context: Optional[int] = None,
    max_context: Optional[int] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    List all available LLM models across providers with advanced filtering

    Query Parameters:
        provider_id: Filter by provider UUID
        enabled_only: Only return enabled models (default: false)
        sort_by: Sort by cost, latency, name, context, or popularity (default: cost)
        search: Search model names (case-insensitive)
        min_cost: Minimum cost per 1M tokens (input + output average)
        max_cost: Maximum cost per 1M tokens (input + output average)
        min_context: Minimum context length
        max_context: Maximum context length
        limit: Maximum results to return (default: 100)
        offset: Results offset for pagination (default: 0)

    Returns:
        List of models with pricing and performance data

    Examples:
        /api/v1/llm/models?search=gpt&max_cost=5.0&min_context=100000
        /api/v1/llm/models?enabled_only=true&sort_by=context&limit=20
        /api/v1/llm/models?provider_id=xxx&sort_by=cost&max_cost=1.0
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        query = """
            SELECT
                m.id,
                m.provider_id,
                p.name as provider_name,
                m.name,
                m.display_name,
                m.cost_per_1m_input_tokens,
                m.cost_per_1m_output_tokens,
                (m.cost_per_1m_input_tokens + m.cost_per_1m_output_tokens) / 2 as avg_cost,
                m.context_length,
                m.enabled,
                m.avg_latency_ms,
                m.metadata
            FROM llm_models m
            JOIN llm_providers p ON m.provider_id = p.id
            WHERE 1=1
        """

        params = []

        # Provider filter
        if provider_id:
            query += " AND m.provider_id = %s"
            params.append(provider_id)

        # Enabled filter
        if enabled_only:
            query += " AND m.enabled = true AND p.enabled = true"

        # Search filter (name or display_name)
        if search:
            query += " AND (m.name ILIKE %s OR m.display_name ILIKE %s)"
            search_pattern = f"%{search}%"
            params.append(search_pattern)
            params.append(search_pattern)

        # Cost filters (using average of input + output)
        if min_cost is not None:
            query += " AND (m.cost_per_1m_input_tokens + m.cost_per_1m_output_tokens) / 2 >= %s"
            params.append(min_cost)

        if max_cost is not None:
            query += " AND (m.cost_per_1m_input_tokens + m.cost_per_1m_output_tokens) / 2 <= %s"
            params.append(max_cost)

        # Context length filters
        if min_context is not None:
            query += " AND m.context_length >= %s"
            params.append(min_context)

        if max_context is not None:
            query += " AND m.context_length <= %s"
            params.append(max_context)

        # Sort
        if sort_by == "cost":
            query += " ORDER BY avg_cost ASC"
        elif sort_by == "latency":
            query += " ORDER BY m.avg_latency_ms ASC NULLS LAST"
        elif sort_by == "context":
            query += " ORDER BY m.context_length DESC"
        elif sort_by == "popularity":
            # Sort by name for now (could add usage stats later)
            query += " ORDER BY m.name"
        else:  # name
            query += " ORDER BY m.name"

        # Pagination
        query += " LIMIT %s OFFSET %s"
        params.append(limit)
        params.append(offset)

        cursor.execute(query, params)
        models = cursor.fetchall()

        result = []
        for m in models:
            model_data = {
                'id': m['name'],  # Use model name as ID (OpenAI standard)
                'object': 'model',
                'name': m['name'],
                'display_name': m['display_name'] or m['name'],
                'provider': m['provider_name'],
                'provider_id': str(m['provider_id']),
                'pricing': {
                    'input': float(m['cost_per_1m_input_tokens']),
                    'output': float(m['cost_per_1m_output_tokens'])
                },
                'context_length': m['context_length'],
                'enabled': m['enabled'],
                'avg_latency_ms': m['avg_latency_ms'],
                '_uuid': str(m['id'])  # Keep UUID for internal use
            }
            result.append(model_data)

        # Return OpenAI-compatible format
        return {
            'object': 'list',
            'data': result
        }

    finally:
        cursor.close()
        conn.close()


@router.post("/models", response_model=Dict)
async def create_model(model: ModelCreate):
    """
    Add new model to provider

    Body:
        ModelCreate schema

    Returns:
        Created model with ID
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            INSERT INTO llm_models
            (provider_id, name, display_name, cost_per_1m_input_tokens,
             cost_per_1m_output_tokens, context_length, enabled, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, name, display_name
        """, (
            model.provider_id,
            model.name,
            model.display_name or model.name,
            model.cost_per_1m_input_tokens,
            model.cost_per_1m_output_tokens,
            model.context_length,
            model.enabled,
            Json(model.metadata)
        ))

        result = cursor.fetchone()
        conn.commit()

        return {
            "id": str(result['id']),
            "name": result['name'],
            "display_name": result['display_name'],
            "message": "Model created successfully"
        }

    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Model with this name already exists for provider")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to create model: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# ============================================================================
# Routing Rules Endpoints
# ============================================================================

@router.get("/routing/rules")
async def get_routing_rules():
    """
    Get current routing configuration

    Returns:
        Routing strategy, fallback rules, model aliases
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("SELECT * FROM llm_routing_rules ORDER BY created_at DESC LIMIT 1")
        rules = cursor.fetchone()

        if not rules:
            return {
                "strategy": "balanced",
                "fallback_providers": [],
                "model_aliases": {},
                "config": {},
                "power_levels": {
                    "eco": "Use cheapest models (OpenRouter budget tier)",
                    "balanced": "Balance cost and quality (mix of providers)",
                    "precision": "Use best models (OpenAI, Anthropic direct)"
                }
            }

        return {
            "id": str(rules['id']),
            "strategy": rules['strategy'],
            "fallback_providers": rules['fallback_providers'],
            "model_aliases": rules['model_aliases'],
            "config": rules['config'],
            "power_levels": {
                "eco": "Use cheapest models (OpenRouter budget tier)",
                "balanced": "Balance cost and quality (mix of providers)",
                "precision": "Use best models (OpenAI, Anthropic direct)"
            }
        }

    finally:
        cursor.close()
        conn.close()


@router.put("/routing/rules")
async def update_routing_rules(rules: RoutingRulesUpdate):
    """
    Update routing configuration

    Body:
        RoutingRulesUpdate schema

    Returns:
        Updated routing rules
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Validate fallback providers exist
        if rules.fallback_providers:
            cursor.execute(
                "SELECT COUNT(*) FROM llm_providers WHERE id = ANY(%s)",
                (rules.fallback_providers,)
            )
            count = cursor.fetchone()[0]
            if count != len(rules.fallback_providers):
                raise HTTPException(status_code=400, detail="One or more fallback providers not found")

        # Update or insert
        cursor.execute("""
            INSERT INTO llm_routing_rules (strategy, fallback_providers, model_aliases, config)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                strategy = EXCLUDED.strategy,
                fallback_providers = EXCLUDED.fallback_providers,
                model_aliases = EXCLUDED.model_aliases,
                config = EXCLUDED.config,
                updated_at = NOW()
            RETURNING id, strategy, fallback_providers, model_aliases, config
        """, (
            rules.strategy,
            rules.fallback_providers,
            Json(rules.model_aliases),
            Json(rules.config)
        ))

        result = cursor.fetchone()
        conn.commit()

        # Clear routing cache
        if redis_client:
            redis_client.delete("routing:rules")

        return {
            "id": str(result['id']),
            "strategy": result['strategy'],
            "fallback_providers": result['fallback_providers'],
            "model_aliases": result['model_aliases'],
            "config": result['config'],
            "message": "Routing rules updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update routing rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# ============================================================================
# Usage Analytics Endpoints
# ============================================================================

@router.get("/usage")
async def get_usage_analytics(
    user_id: Optional[str] = None,
    days: int = 7,
    provider_id: Optional[str] = None
):
    """
    Get LLM usage analytics

    Query Parameters:
        user_id: Filter by user (admin only without user_id)
        days: Number of days to analyze (default 7)
        provider_id: Filter by provider

    Returns:
        Usage statistics with cost breakdown
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        query = """
            SELECT
                COUNT(*) as total_requests,
                SUM(input_tokens + output_tokens) as total_tokens,
                SUM(cost) as total_cost,
                AVG(cost) as avg_cost_per_request,
                AVG(latency_ms) as avg_latency,
                p.name as provider_name,
                p.id as provider_id,
                COUNT(DISTINCT l.user_id) as unique_users
            FROM llm_usage_logs l
            LEFT JOIN llm_providers p ON l.provider_id = p.id
            WHERE l.created_at >= NOW() - INTERVAL '%s days'
        """

        params = [days]

        if user_id:
            query += " AND l.user_id = %s"
            params.append(user_id)

        if provider_id:
            query += " AND l.provider_id = %s"
            params.append(provider_id)

        query += " GROUP BY p.name, p.id"

        cursor.execute(query, params)
        provider_stats = cursor.fetchall()

        # Overall stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_requests,
                SUM(input_tokens + output_tokens) as total_tokens,
                SUM(cost) as total_cost,
                AVG(cost) as avg_cost_per_request
            FROM llm_usage_logs
            WHERE created_at >= NOW() - INTERVAL %s
        """ + (" AND user_id = %s" if user_id else ""),
            [f"{days} days", user_id] if user_id else [f"{days} days"]
        )

        overall = cursor.fetchone()

        return {
            "total_requests": overall['total_requests'] or 0,
            "total_tokens": int(overall['total_tokens'] or 0),
            "total_cost": float(overall['total_cost'] or 0),
            "avg_cost_per_request": float(overall['avg_cost_per_request'] or 0),
            "providers": [
                {
                    "provider_id": str(p['provider_id']) if p['provider_id'] else None,
                    "provider_name": p['provider_name'] or "Unknown",
                    "requests": p['total_requests'],
                    "tokens": int(p['total_tokens'] or 0),
                    "cost": float(p['total_cost'] or 0),
                    "avg_latency_ms": int(p['avg_latency'] or 0),
                    "unique_users": p['unique_users']
                }
                for p in provider_stats
            ],
            "period_days": days
        }

    finally:
        cursor.close()
        conn.close()


# ============================================================================
# User BYOK Endpoints
# ============================================================================

@router.post("/users/{user_id}/byok")
async def set_user_byok(user_id: str, byok: UserBYOKUpdate):
    """
    Set user's Bring Your Own Key configuration

    Path Parameters:
        user_id: User identifier

    Body:
        UserBYOKUpdate schema

    Returns:
        Updated BYOK configuration
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Encrypt API key
        encrypted_key = cipher_suite.encrypt(byok.api_key.encode()).decode()

        # Get current BYOK providers
        cursor.execute("SELECT byok_providers FROM user_llm_settings WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()

        current_byok = row['byok_providers'] if row else {}

        # Update BYOK for this provider type
        current_byok[byok.provider_type] = {
            "encrypted_key": encrypted_key,
            "enabled": byok.enabled,
            "preferences": byok.preferences,
            "updated_at": datetime.now().isoformat()
        }

        # Upsert user settings
        cursor.execute("""
            INSERT INTO user_llm_settings (user_id, byok_providers)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                byok_providers = %s,
                updated_at = NOW()
            RETURNING user_id, power_level, credit_balance
        """, (user_id, Json(current_byok), Json(current_byok)))

        result = cursor.fetchone()
        conn.commit()

        return {
            "user_id": result['user_id'],
            "provider_type": byok.provider_type,
            "enabled": byok.enabled,
            "power_level": result['power_level'],
            "credit_balance": float(result['credit_balance']),
            "message": "BYOK configuration updated successfully"
        }

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update BYOK: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.get("/users/{user_id}/byok")
async def get_user_byok(user_id: str):
    """
    Get user's BYOK configuration (API keys masked)

    Path Parameters:
        user_id: User identifier

    Returns:
        BYOK configuration with masked keys
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT byok_providers, power_level, credit_balance, preferences
            FROM user_llm_settings
            WHERE user_id = %s
        """, (user_id,))

        row = cursor.fetchone()

        if not row:
            return {
                "user_id": user_id,
                "byok_providers": {},
                "power_level": "balanced",
                "credit_balance": 0.0,
                "preferences": {}
            }

        # Mask API keys
        byok_providers = row['byok_providers'] or {}
        masked_byok = {}

        for provider, config in byok_providers.items():
            masked_byok[provider] = {
                "enabled": config.get("enabled", False),
                "preferences": config.get("preferences", {}),
                "updated_at": config.get("updated_at"),
                "api_key": "sk-...****"  # Masked
            }

        return {
            "user_id": user_id,
            "byok_providers": masked_byok,
            "power_level": row['power_level'],
            "credit_balance": float(row['credit_balance']),
            "preferences": row['preferences'] or {}
        }

    finally:
        cursor.close()
        conn.close()


# ============================================================================
# Credit System Endpoints
# ============================================================================

@router.get("/credits")
async def get_credit_status(user_id: str):
    """
    Get user's credit balance and usage

    Query Parameters:
        user_id: User identifier

    Returns:
        Credit balance, tier, usage limits
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT
                user_id,
                power_level,
                credit_balance,
                preferences
            FROM user_llm_settings
            WHERE user_id = %s
        """, (user_id,))

        row = cursor.fetchone()

        if not row:
            return {
                "user_id": user_id,
                "credits_remaining": 0.0,
                "power_level": "balanced",
                "monthly_cap": None
            }

        return {
            "user_id": row['user_id'],
            "credits_remaining": float(row['credit_balance']),
            "power_level": row['power_level'],
            "monthly_cap": row['preferences'].get('monthly_cap') if row['preferences'] else None
        }

    finally:
        cursor.close()
        conn.close()


# ============================================================================
# Provider Testing Endpoint
# ============================================================================

@router.post("/test")
async def test_provider_connection(test_req: ProviderTestRequest):
    """
    Test provider connection with sample request

    Body:
        ProviderTestRequest schema

    Returns:
        Test results with latency and status
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Get provider details
        cursor.execute("""
            SELECT api_key_encrypted, api_base_url, type, name
            FROM llm_providers
            WHERE id = %s
        """, (test_req.provider_id,))

        provider = cursor.fetchone()

        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")

        # Decrypt API key
        api_key = cipher_suite.decrypt(provider['api_key_encrypted'].encode()).decode()

        # Perform test request
        start_time = datetime.now()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if provider['type'] == 'openai':
                    response = await client.post(
                        f"{provider['api_base_url']}/v1/chat/completions",
                        json={
                            "model": test_req.model or "gpt-3.5-turbo",
                            "messages": [{"role": "user", "content": "Test"}],
                            "max_tokens": 5
                        },
                        headers={"Authorization": f"Bearer {api_key}"}
                    )
                elif provider['type'] == 'anthropic':
                    response = await client.post(
                        f"{provider['api_base_url']}/v1/messages",
                        json={
                            "model": test_req.model or "claude-3-haiku-20240307",
                            "messages": [{"role": "user", "content": "Test"}],
                            "max_tokens": 5
                        },
                        headers={
                            "x-api-key": api_key,
                            "anthropic-version": "2023-06-01"
                        }
                    )
                else:
                    # OpenRouter and others use OpenAI format
                    response = await client.post(
                        f"{provider['api_base_url']}/v1/chat/completions",
                        json={
                            "model": test_req.model or "openai/gpt-3.5-turbo",
                            "messages": [{"role": "user", "content": "Test"}],
                            "max_tokens": 5
                        },
                        headers={"Authorization": f"Bearer {api_key}"}
                    )

                latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                if response.status_code == 200:
                    # Update health status
                    cursor.execute("""
                        UPDATE llm_providers
                        SET health_status = 'healthy',
                            last_health_check = NOW()
                        WHERE id = %s
                    """, (test_req.provider_id,))
                    conn.commit()

                    return {
                        "provider_id": test_req.provider_id,
                        "provider_name": provider['name'],
                        "status": "success",
                        "latency_ms": latency_ms,
                        "message": "Provider connection successful"
                    }
                else:
                    raise HTTPException(status_code=response.status_code, detail=response.text)

        except httpx.HTTPError as e:
            # Update health status
            cursor.execute("""
                UPDATE llm_providers
                SET health_status = 'unhealthy',
                    last_health_check = NOW()
                WHERE id = %s
            """, (test_req.provider_id,))
            conn.commit()

            return {
                "provider_id": test_req.provider_id,
                "provider_name": provider['name'],
                "status": "failed",
                "error": str(e),
                "message": "Provider connection failed"
            }

    finally:
        cursor.close()
        conn.close()


# ============================================================================
# Helper Functions
# ============================================================================

def get_default_base_url(provider_type: str) -> str:
    """Get default API base URL for provider type"""
    urls = {
        ProviderType.OPENROUTER: "https://openrouter.ai/api",
        ProviderType.OPENAI: "https://api.openai.com",
        ProviderType.ANTHROPIC: "https://api.anthropic.com",
        ProviderType.TOGETHER: "https://api.together.xyz",
        ProviderType.HUGGINGFACE: "https://api-inference.huggingface.co",
        ProviderType.GOOGLE: "https://generativelanguage.googleapis.com",
        ProviderType.COHERE: "https://api.cohere.ai"
    }
    return urls.get(provider_type, "")


async def test_provider_health(provider_id: str):
    """Background task to test provider health"""
    try:
        await test_provider_connection(ProviderTestRequest(provider_id=provider_id))
    except Exception as e:
        logger.error(f"Provider health check failed for {provider_id}: {e}")


# Initialize database on import
try:
    init_database()
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
