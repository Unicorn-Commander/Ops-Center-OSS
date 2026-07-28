"""
LLM Infrastructure Database Models

This module defines SQLAlchemy models for LiteLLM multi-provider routing:
- LLM Providers (OpenAI, Anthropic, Google, etc.)
- LLM Models (GPT-4, Claude, Gemini, etc.)
- User API Keys (BYOK - Bring Your Own Key)
- Routing Rules (Power level mappings)
- Usage Logs (Billing integration)

Author: Backend API Developer
Epic: 3.1 - LiteLLM Multi-Provider Routing
Date: October 23, 2025
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, Text,
    ForeignKey, UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Optional, Dict, Any, List

Base = declarative_base()


# ============================================================================
# Provider Models
# ============================================================================

class LLMProvider(Base):
    """
    LLM Provider (OpenAI, Anthropic, Google, etc.)

    Represents an AI model provider that can serve LLM requests.
    Each provider has a base URL, authentication method, and rate limits.
    """
    __tablename__ = 'llm_providers'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Provider Details
    provider_name = Column(String(100), unique=True, nullable=False, index=True)
    provider_slug = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Configuration
    base_url = Column(String(500), nullable=True)  # API endpoint
    auth_type = Column(String(50), nullable=False, default='api_key')  # api_key, oauth2, etc.
    supports_streaming = Column(Boolean, default=True)
    supports_function_calling = Column(Boolean, default=False)
    supports_vision = Column(Boolean, default=False)

    # Rate Limits
    rate_limit_rpm = Column(Integer, nullable=True)  # Requests per minute
    rate_limit_tpm = Column(Integer, nullable=True)  # Tokens per minute
    rate_limit_rpd = Column(Integer, nullable=True)  # Requests per day

    # Provider Status
    is_active = Column(Boolean, default=True, index=True)
    is_byok_supported = Column(Boolean, default=True)  # Supports Bring Your Own Key
    is_system_provider = Column(Boolean, default=False)  # System-managed (always available)

    # Metadata
    api_key_format = Column(String(100), nullable=True)  # e.g., "sk-*", "Bearer *"
    documentation_url = Column(String(500), nullable=True)
    pricing_url = Column(String(500), nullable=True)
    status_page_url = Column(String(500), nullable=True)

    # Provider Health
    health_status = Column(String(50), default='unknown')  # healthy, degraded, down, unknown
    health_last_checked = Column(DateTime, nullable=True)
    health_response_time_ms = Column(Integer, nullable=True)

    # Tier Access Control
    min_tier_required = Column(String(50), default='free')  # free, starter, professional, enterprise

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    models = relationship('LLMModel', back_populates='provider', cascade='all, delete-orphan')
    user_keys = relationship('UserAPIKey', back_populates='provider', cascade='all, delete-orphan')
    usage_logs = relationship('LLMUsageLog', back_populates='provider')

    def __repr__(self):
        return f"<LLMProvider(id={self.id}, name='{self.provider_name}', active={self.is_active})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'provider_name': self.provider_name,
            'provider_slug': self.provider_slug,
            'display_name': self.display_name,
            'description': self.description,
            'base_url': self.base_url,
            'auth_type': self.auth_type,
            'supports_streaming': self.supports_streaming,
            'supports_function_calling': self.supports_function_calling,
            'supports_vision': self.supports_vision,
            'rate_limit_rpm': self.rate_limit_rpm,
            'rate_limit_tpm': self.rate_limit_tpm,
            'rate_limit_rpd': self.rate_limit_rpd,
            'is_active': self.is_active,
            'is_byok_supported': self.is_byok_supported,
            'is_system_provider': self.is_system_provider,
            'health_status': self.health_status,
            'health_last_checked': self.health_last_checked.isoformat() if self.health_last_checked else None,
            'health_response_time_ms': self.health_response_time_ms,
            'min_tier_required': self.min_tier_required,
            'documentation_url': self.documentation_url,
            'pricing_url': self.pricing_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class LLMModel(Base):
    """
    LLM Model (GPT-4, Claude-3.5-Sonnet, Gemini-Pro, etc.)

    Represents a specific AI model from a provider.
    Includes pricing, capabilities, and power level mappings.
    """
    __tablename__ = 'llm_models'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    provider_id = Column(Integer, ForeignKey('llm_providers.id', ondelete='CASCADE'), nullable=False, index=True)

    # Model Details
    model_name = Column(String(200), nullable=False, index=True)
    model_id = Column(String(200), nullable=False)  # API identifier (e.g., "gpt-4-turbo")
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Model Capabilities
    max_tokens = Column(Integer, nullable=False, default=4096)
    context_window = Column(Integer, nullable=False, default=8192)
    supports_streaming = Column(Boolean, default=True)
    supports_function_calling = Column(Boolean, default=False)
    supports_vision = Column(Boolean, default=False)
    supports_json_mode = Column(Boolean, default=False)

    # Pricing (per 1M tokens)
    cost_per_1m_input_tokens = Column(Float, nullable=True)  # USD
    cost_per_1m_output_tokens = Column(Float, nullable=True)  # USD
    cost_per_1m_tokens_cached = Column(Float, nullable=True)  # For prompt caching

    # Power Level Mapping (eco, balanced, precision)
    power_level = Column(String(50), nullable=True, index=True)  # eco, balanced, precision
    power_level_priority = Column(Integer, default=999)  # Lower = higher priority

    # Model Status
    is_active = Column(Boolean, default=True, index=True)
    is_deprecated = Column(Boolean, default=False)
    deprecation_date = Column(DateTime, nullable=True)
    replacement_model_id = Column(Integer, ForeignKey('llm_models.id'), nullable=True)

    # Tier Access Control
    min_tier_required = Column(String(50), default='free')  # free, starter, professional, enterprise

    # Performance Metrics
    avg_latency_ms = Column(Integer, nullable=True)
    avg_tokens_per_second = Column(Float, nullable=True)

    # Metadata
    model_version = Column(String(50), nullable=True)
    release_date = Column(DateTime, nullable=True)
    training_cutoff = Column(String(100), nullable=True)  # "2023-10" for knowledge cutoff

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    provider = relationship('LLMProvider', back_populates='models')
    routing_rules = relationship('LLMRoutingRule', back_populates='model', cascade='all, delete-orphan')
    usage_logs = relationship('LLMUsageLog', back_populates='model')

    # Indexes
    __table_args__ = (
        Index('idx_model_provider_active', provider_id, is_active),
        Index('idx_model_power_level', power_level, is_active),
        UniqueConstraint('provider_id', 'model_id', name='uq_provider_model'),
    )

    def __repr__(self):
        return f"<LLMModel(id={self.id}, name='{self.model_name}', provider_id={self.provider_id})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'provider_id': self.provider_id,
            'model_name': self.model_name,
            'model_id': self.model_id,
            'display_name': self.display_name,
            'description': self.description,
            'max_tokens': self.max_tokens,
            'context_window': self.context_window,
            'supports_streaming': self.supports_streaming,
            'supports_function_calling': self.supports_function_calling,
            'supports_vision': self.supports_vision,
            'supports_json_mode': self.supports_json_mode,
            'cost_per_1m_input_tokens': self.cost_per_1m_input_tokens,
            'cost_per_1m_output_tokens': self.cost_per_1m_output_tokens,
            'cost_per_1m_tokens_cached': self.cost_per_1m_tokens_cached,
            'power_level': self.power_level,
            'power_level_priority': self.power_level_priority,
            'is_active': self.is_active,
            'is_deprecated': self.is_deprecated,
            'deprecation_date': self.deprecation_date.isoformat() if self.deprecation_date else None,
            'min_tier_required': self.min_tier_required,
            'avg_latency_ms': self.avg_latency_ms,
            'avg_tokens_per_second': self.avg_tokens_per_second,
            'model_version': self.model_version,
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'training_cutoff': self.training_cutoff,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


# ============================================================================
# BYOK (Bring Your Own Key) Models
# ============================================================================

class UserAPIKey(Base):
    """
    User API Key (BYOK - Bring Your Own Key)

    Stores encrypted user API keys for various providers.
    Users can supply their own OpenAI, Anthropic, Google keys.
    """
    __tablename__ = 'user_api_keys'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id = Column(String(255), nullable=False, index=True)  # Keycloak user ID
    provider_id = Column(Integer, ForeignKey('llm_providers.id', ondelete='CASCADE'), nullable=False, index=True)

    # Key Details
    key_name = Column(String(200), nullable=True)  # User-friendly label
    encrypted_api_key = Column(Text, nullable=False)  # Encrypted using secret_manager.py
    key_prefix = Column(String(20), nullable=True)  # First 8 chars for display (e.g., "sk-proj-1234")
    key_suffix = Column(String(20), nullable=True)  # Last 4 chars for display

    # Key Status
    is_active = Column(Boolean, default=True, index=True)
    is_validated = Column(Boolean, default=False)  # Has key been tested?
    validation_error = Column(Text, nullable=True)
    last_validated_at = Column(DateTime, nullable=True)

    # Usage Stats
    total_requests = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)
    last_used_at = Column(DateTime, nullable=True)

    # Security
    created_ip = Column(String(100), nullable=True)
    last_rotated_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    provider = relationship('LLMProvider', back_populates='user_keys')
    usage_logs = relationship('LLMUsageLog', back_populates='user_key')

    # Indexes
    __table_args__ = (
        Index('idx_user_provider_active', user_id, provider_id, is_active),
        UniqueConstraint('user_id', 'provider_id', name='uq_user_provider_key'),
    )

    def __repr__(self):
        return f"<UserAPIKey(id={self.id}, user_id='{self.user_id}', provider_id={self.provider_id})>"

    def to_dict(self, include_key: bool = False) -> Dict[str, Any]:
        """
        Convert to dictionary for API responses

        Args:
            include_key: If True, include encrypted_api_key (admin only)
        """
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'provider_id': self.provider_id,
            'key_name': self.key_name,
            'key_prefix': self.key_prefix,
            'key_suffix': self.key_suffix,
            'is_active': self.is_active,
            'is_validated': self.is_validated,
            'validation_error': self.validation_error,
            'last_validated_at': self.last_validated_at.isoformat() if self.last_validated_at else None,
            'total_requests': self.total_requests,
            'total_tokens': self.total_tokens,
            'total_cost_usd': self.total_cost_usd,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

        if include_key:
            result['encrypted_api_key'] = self.encrypted_api_key

        return result


# ============================================================================
# Routing Rules
# ============================================================================

class LLMRoutingRule(Base):
    """
    LLM Routing Rule

    Defines how requests are routed to models based on:
    - Power level (eco, balanced, precision)
    - User tier (free, starter, professional, enterprise)
    - Task type (code, chat, rag, creative)
    """
    __tablename__ = 'llm_routing_rules'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    model_id = Column(Integer, ForeignKey('llm_models.id', ondelete='CASCADE'), nullable=False, index=True)

    # Routing Criteria
    power_level = Column(String(50), nullable=False, index=True)  # eco, balanced, precision
    user_tier = Column(String(50), nullable=False, index=True)  # free, starter, professional, enterprise
    task_type = Column(String(50), nullable=True, index=True)  # code, chat, rag, creative, general

    # Routing Priority
    priority = Column(Integer, default=100)  # Lower = higher priority
    weight = Column(Integer, default=100)  # For load balancing (higher = more likely)

    # Routing Conditions
    min_tokens = Column(Integer, nullable=True)  # Minimum tokens to use this model
    max_tokens = Column(Integer, nullable=True)  # Maximum tokens allowed
    requires_byok = Column(Boolean, default=False)  # Requires user's own API key

    # Fallback Configuration
    is_fallback = Column(Boolean, default=False)  # Use if primary fails
    fallback_order = Column(Integer, default=999)  # Fallback sequence

    # Rule Status
    is_active = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    model = relationship('LLMModel', back_populates='routing_rules')

    # Indexes
    __table_args__ = (
        Index('idx_routing_power_tier_task', power_level, user_tier, task_type, is_active),
        Index('idx_routing_priority', priority, is_active),
    )

    def __repr__(self):
        return f"<LLMRoutingRule(id={self.id}, power='{self.power_level}', tier='{self.user_tier}', model_id={self.model_id})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'model_id': self.model_id,
            'power_level': self.power_level,
            'user_tier': self.user_tier,
            'task_type': self.task_type,
            'priority': self.priority,
            'weight': self.weight,
            'min_tokens': self.min_tokens,
            'max_tokens': self.max_tokens,
            'requires_byok': self.requires_byok,
            'is_fallback': self.is_fallback,
            'fallback_order': self.fallback_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


# ============================================================================
# Usage Tracking
# ============================================================================

class LLMUsageLog(Base):
    """
    LLM Usage Log

    Tracks every LLM API call for billing, analytics, and debugging.
    Integrates with Lago billing system.
    """
    __tablename__ = 'llm_usage_logs'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id = Column(String(255), nullable=False, index=True)  # Keycloak user ID
    provider_id = Column(Integer, ForeignKey('llm_providers.id', ondelete='SET NULL'), nullable=True, index=True)
    model_id = Column(Integer, ForeignKey('llm_models.id', ondelete='SET NULL'), nullable=True, index=True)
    user_key_id = Column(Integer, ForeignKey('user_api_keys.id', ondelete='SET NULL'), nullable=True)

    # Request Details
    request_id = Column(String(100), unique=True, index=True)  # UUID for tracking
    power_level = Column(String(50), nullable=True)  # eco, balanced, precision
    task_type = Column(String(50), nullable=True)  # code, chat, rag, creative

    # Usage Metrics
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0, index=True)
    cached_tokens = Column(Integer, default=0)  # Prompt caching

    # Cost Calculation
    cost_input_usd = Column(Float, default=0.0)
    cost_output_usd = Column(Float, default=0.0)
    cost_total_usd = Column(Float, default=0.0, index=True)
    used_byok = Column(Boolean, default=False)  # Used user's own key?

    # Performance Metrics
    latency_ms = Column(Integer, nullable=True)
    tokens_per_second = Column(Float, nullable=True)

    # Response Details
    status_code = Column(Integer, nullable=True)  # HTTP status
    error_message = Column(Text, nullable=True)
    was_fallback = Column(Boolean, default=False)  # Used fallback model?
    fallback_reason = Column(String(200), nullable=True)

    # Billing Integration
    lago_event_id = Column(String(100), nullable=True, unique=True)  # Lago billing event ID
    billed_at = Column(DateTime, nullable=True)

    # Request Metadata
    request_ip = Column(String(100), nullable=True)
    user_agent = Column(String(500), nullable=True)
    session_id = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    provider = relationship('LLMProvider', back_populates='usage_logs')
    model = relationship('LLMModel', back_populates='usage_logs')
    user_key = relationship('UserAPIKey', back_populates='usage_logs')

    # Indexes
    __table_args__ = (
        Index('idx_usage_user_date', user_id, created_at),
        Index('idx_usage_provider_date', provider_id, created_at),
        Index('idx_usage_cost', cost_total_usd, created_at),
    )

    def __repr__(self):
        return f"<LLMUsageLog(id={self.id}, user_id='{self.user_id}', tokens={self.total_tokens}, cost=${self.cost_total_usd:.6f})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'provider_id': self.provider_id,
            'model_id': self.model_id,
            'user_key_id': self.user_key_id,
            'request_id': self.request_id,
            'power_level': self.power_level,
            'task_type': self.task_type,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens,
            'cached_tokens': self.cached_tokens,
            'cost_input_usd': self.cost_input_usd,
            'cost_output_usd': self.cost_output_usd,
            'cost_total_usd': self.cost_total_usd,
            'used_byok': self.used_byok,
            'latency_ms': self.latency_ms,
            'tokens_per_second': self.tokens_per_second,
            'status_code': self.status_code,
            'error_message': self.error_message,
            'was_fallback': self.was_fallback,
            'fallback_reason': self.fallback_reason,
            'lago_event_id': self.lago_event_id,
            'billed_at': self.billed_at.isoformat() if self.billed_at else None,
            'created_at': self.created_at.isoformat()
        }


# ============================================================================
# Database Initialization SQL
# ============================================================================

# SQL statements for table creation (if using raw SQL instead of Alembic)
CREATE_TABLES_SQL = """
-- Enable pgcrypto for UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- LLM Providers Table
CREATE TABLE IF NOT EXISTS llm_providers (
    id SERIAL PRIMARY KEY,
    provider_name VARCHAR(100) UNIQUE NOT NULL,
    provider_slug VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    base_url VARCHAR(500),
    auth_type VARCHAR(50) DEFAULT 'api_key',
    supports_streaming BOOLEAN DEFAULT TRUE,
    supports_function_calling BOOLEAN DEFAULT FALSE,
    supports_vision BOOLEAN DEFAULT FALSE,
    rate_limit_rpm INTEGER,
    rate_limit_tpm INTEGER,
    rate_limit_rpd INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    is_byok_supported BOOLEAN DEFAULT TRUE,
    is_system_provider BOOLEAN DEFAULT FALSE,
    api_key_format VARCHAR(100),
    documentation_url VARCHAR(500),
    pricing_url VARCHAR(500),
    status_page_url VARCHAR(500),
    health_status VARCHAR(50) DEFAULT 'unknown',
    health_last_checked TIMESTAMP,
    health_response_time_ms INTEGER,
    min_tier_required VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_llm_providers_active ON llm_providers(is_active);
CREATE INDEX idx_llm_providers_slug ON llm_providers(provider_slug);

-- LLM Models Table
CREATE TABLE IF NOT EXISTS llm_models (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES llm_providers(id) ON DELETE CASCADE,
    model_name VARCHAR(200) NOT NULL,
    model_id VARCHAR(200) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    max_tokens INTEGER DEFAULT 4096,
    context_window INTEGER DEFAULT 8192,
    supports_streaming BOOLEAN DEFAULT TRUE,
    supports_function_calling BOOLEAN DEFAULT FALSE,
    supports_vision BOOLEAN DEFAULT FALSE,
    supports_json_mode BOOLEAN DEFAULT FALSE,
    cost_per_1m_input_tokens FLOAT,
    cost_per_1m_output_tokens FLOAT,
    cost_per_1m_tokens_cached FLOAT,
    power_level VARCHAR(50),
    power_level_priority INTEGER DEFAULT 999,
    is_active BOOLEAN DEFAULT TRUE,
    is_deprecated BOOLEAN DEFAULT FALSE,
    deprecation_date TIMESTAMP,
    replacement_model_id INTEGER REFERENCES llm_models(id),
    min_tier_required VARCHAR(50) DEFAULT 'free',
    avg_latency_ms INTEGER,
    avg_tokens_per_second FLOAT,
    model_version VARCHAR(50),
    release_date TIMESTAMP,
    training_cutoff VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider_id, model_id)
);

CREATE INDEX idx_llm_models_provider ON llm_models(provider_id, is_active);
CREATE INDEX idx_llm_models_power_level ON llm_models(power_level, is_active);

-- User API Keys Table (BYOK)
CREATE TABLE IF NOT EXISTS user_api_keys (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    provider_id INTEGER REFERENCES llm_providers(id) ON DELETE CASCADE,
    key_name VARCHAR(200),
    encrypted_api_key TEXT NOT NULL,
    key_prefix VARCHAR(20),
    key_suffix VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    is_validated BOOLEAN DEFAULT FALSE,
    validation_error TEXT,
    last_validated_at TIMESTAMP,
    total_requests INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd FLOAT DEFAULT 0.0,
    last_used_at TIMESTAMP,
    created_ip VARCHAR(100),
    last_rotated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, provider_id)
);

CREATE INDEX idx_user_api_keys_user ON user_api_keys(user_id, is_active);
CREATE INDEX idx_user_api_keys_provider ON user_api_keys(provider_id);

-- Routing Rules Table
CREATE TABLE IF NOT EXISTS llm_routing_rules (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES llm_models(id) ON DELETE CASCADE,
    power_level VARCHAR(50) NOT NULL,
    user_tier VARCHAR(50) NOT NULL,
    task_type VARCHAR(50),
    priority INTEGER DEFAULT 100,
    weight INTEGER DEFAULT 100,
    min_tokens INTEGER,
    max_tokens INTEGER,
    requires_byok BOOLEAN DEFAULT FALSE,
    is_fallback BOOLEAN DEFAULT FALSE,
    fallback_order INTEGER DEFAULT 999,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_routing_rules_lookup ON llm_routing_rules(power_level, user_tier, task_type, is_active);
CREATE INDEX idx_routing_rules_priority ON llm_routing_rules(priority, is_active);

-- Usage Logs Table
CREATE TABLE IF NOT EXISTS llm_usage_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    provider_id INTEGER REFERENCES llm_providers(id) ON DELETE SET NULL,
    model_id INTEGER REFERENCES llm_models(id) ON DELETE SET NULL,
    user_key_id INTEGER REFERENCES user_api_keys(id) ON DELETE SET NULL,
    request_id VARCHAR(100) UNIQUE,
    power_level VARCHAR(50),
    task_type VARCHAR(50),
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cached_tokens INTEGER DEFAULT 0,
    cost_input_usd FLOAT DEFAULT 0.0,
    cost_output_usd FLOAT DEFAULT 0.0,
    cost_total_usd FLOAT DEFAULT 0.0,
    used_byok BOOLEAN DEFAULT FALSE,
    latency_ms INTEGER,
    tokens_per_second FLOAT,
    status_code INTEGER,
    error_message TEXT,
    was_fallback BOOLEAN DEFAULT FALSE,
    fallback_reason VARCHAR(200),
    lago_event_id VARCHAR(100) UNIQUE,
    billed_at TIMESTAMP,
    request_ip VARCHAR(100),
    user_agent VARCHAR(500),
    session_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_usage_logs_user_date ON llm_usage_logs(user_id, created_at);
CREATE INDEX idx_usage_logs_provider_date ON llm_usage_logs(provider_id, created_at);
CREATE INDEX idx_usage_logs_cost ON llm_usage_logs(cost_total_usd, created_at);
CREATE INDEX idx_usage_logs_request_id ON llm_usage_logs(request_id);
"""
