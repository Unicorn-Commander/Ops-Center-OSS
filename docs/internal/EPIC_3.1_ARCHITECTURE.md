# Epic 3.1: LiteLLM Multi-Provider Routing - System Architecture

**Version**: 1.0
**Date**: October 23, 2025
**Author**: System Architecture Designer
**Status**: Design Phase - Technical Specification

---

## Executive Summary

Epic 3.1 implements a comprehensive multi-provider LLM routing system with BYOK (Bring Your Own Key) support, power-level based routing, and intelligent cost optimization. This system enables users to:

1. **Add their own API keys** for OpenAI, Anthropic, Together, etc. (BYOK)
2. **Select power levels** (Eco, Balanced, Precision) for automatic model routing
3. **Optimize costs** through intelligent provider selection based on WilmerAI-style cost/latency/quality scoring
4. **Automatic fallback** when primary providers fail
5. **Usage tracking** for billing and quota enforcement

This architecture builds upon existing `litellm_routing_api.py` and `byok_manager.py` modules, extending them with frontend interfaces and enhanced routing logic.

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Database Schema Design](#2-database-schema-design)
3. [API Architecture](#3-api-architecture)
4. [Security Architecture](#4-security-architecture)
5. [Routing Logic Architecture](#5-routing-logic-architecture)
6. [Frontend Architecture](#6-frontend-architecture)
7. [Integration Architecture](#7-integration-architecture)
8. [Deployment Architecture](#8-deployment-architecture)

---

## 1. System Architecture Overview

### 1.1 High-Level Component Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                        Ops-Center Frontend                          │
│                     (React + Material-UI)                           │
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │  Provider Mgmt  │  │  BYOK Manager   │  │  Power Level UI  │  │
│  │  (Admin)        │  │  (User)         │  │  (User)          │  │
│  └─────────────────┘  └─────────────────┘  └──────────────────┘  │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
                               │ HTTPS (JSON)
                               │
┌──────────────────────────────▼─────────────────────────────────────┐
│                     Ops-Center Backend API                          │
│                         (FastAPI)                                   │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐   │
│  │  /api/v1/llm │  │  BYOK API    │  │  Routing Engine       │   │
│  │  /providers  │  │  /byok/*     │  │  (WilmerAI-style)     │   │
│  │  /models     │  │              │  │                       │   │
│  │  /routing    │  │              │  │  - Cost optimization  │   │
│  │  /usage      │  │              │  │  - Latency scoring    │   │
│  │              │  │              │  │  - Quality weighting  │   │
│  │              │  │              │  │  - Fallback handling  │   │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬───────────┘   │
│         │                 │                       │               │
└─────────┼─────────────────┼───────────────────────┼───────────────┘
          │                 │                       │
          │                 │                       │
   ┌──────▼──────┐   ┌──────▼───────┐     ┌────────▼────────┐
   │ PostgreSQL  │   │ SecretManager│     │  Redis Cache    │
   │             │   │ (Fernet)     │     │                 │
   │ - Providers │   │              │     │ - Routing rules │
   │ - Models    │   │ - BYOK keys  │     │ - Health status │
   │ - Rules     │   │ - API keys   │     │ - Rate limits   │
   │ - Usage     │   │ (encrypted)  │     │                 │
   └──────┬──────┘   └──────────────┘     └─────────────────┘
          │
          │
   ┌──────▼─────────────────────────────────────────────────┐
   │              LiteLLM Proxy                              │
   │         (unicorn-litellm-wilmer:4000)                   │
   │                                                          │
   │  ┌──────────────────────────────────────────────────┐  │
   │  │  /chat/completions (OpenAI-compatible)           │  │
   │  │  - Dynamic provider selection                    │  │
   │  │  - User API key injection (BYOK)                 │  │
   │  │  - Request routing based on power level          │  │
   │  └──────────────────────────────────────────────────┘  │
   └────────────┬─────────────────────────────────────────┬─┘
                │                                         │
      ┌─────────▼──────┐                      ┌──────────▼──────┐
      │  OpenRouter    │    ┌──────────┐      │  User BYOK APIs │
      │  (Free/Paid)   │    │ OpenAI   │      │  (Their keys)   │
      │                │    │ Anthropic│      │                 │
      │ 100+ models    │    │ Together │      │ - OpenAI        │
      └────────────────┘    │ Groq     │      │ - Anthropic     │
                            │ etc.     │      │ - Together      │
                            └──────────┘      │ - etc.          │
                                              └─────────────────┘
```

### 1.2 Data Flow Diagrams

#### 1.2.1 User Adds API Key (BYOK Flow)

```
User                Frontend           Backend API        SecretManager      PostgreSQL
 │                     │                    │                   │               │
 │ Enter API key       │                    │                   │               │
 ├────────────────────>│                    │                   │               │
 │                     │ POST /api/v1/llm/  │                   │               │
 │                     │ users/{id}/byok    │                   │               │
 │                     ├───────────────────>│                   │               │
 │                     │                    │ Validate key      │               │
 │                     │                    │ format            │               │
 │                     │                    ├──────────┐        │               │
 │                     │                    │          │        │               │
 │                     │                    │<─────────┘        │               │
 │                     │                    │                   │               │
 │                     │                    │ encrypt_secret()  │               │
 │                     │                    ├──────────────────>│               │
 │                     │                    │                   │ Fernet        │
 │                     │                    │                   │ encrypt       │
 │                     │                    │<──────────────────┤               │
 │                     │                    │ encrypted_value   │               │
 │                     │                    │                   │               │
 │                     │                    │ INSERT INTO       │               │
 │                     │                    │ user_provider_    │               │
 │                     │                    │ keys              │               │
 │                     │                    ├──────────────────────────────────>│
 │                     │                    │                   │               │
 │                     │                    │<──────────────────────────────────┤
 │                     │                    │ key_id            │               │
 │                     │ 201 Created        │                   │               │
 │                     │ {key_id, masked}   │                   │               │
 │                     │<───────────────────┤                   │               │
 │ "Key saved!"        │                    │                   │               │
 │<────────────────────┤                    │                   │               │
```

#### 1.2.2 User Makes LLM Request (Routing Flow)

```
User                Frontend           Backend API        Routing Engine    LiteLLM Proxy
 │                     │                    │                   │               │
 │ Submit prompt       │                    │                   │               │
 ├────────────────────>│                    │                   │               │
 │                     │ POST /api/v1/llm/  │                   │               │
 │                     │ chat/completions   │                   │               │
 │                     ├───────────────────>│                   │               │
 │                     │                    │ Get user power    │               │
 │                     │                    │ level (balanced)  │               │
 │                     │                    ├──────────┐        │               │
 │                     │                    │          │        │               │
 │                     │                    │<─────────┘        │               │
 │                     │                    │                   │               │
 │                     │                    │ Check BYOK keys   │               │
 │                     │                    │ for user          │               │
 │                     │                    ├──────────┐        │               │
 │                     │                    │          │        │               │
 │                     │                    │<─────────┘        │               │
 │                     │                    │                   │               │
 │                     │                    │ select_provider() │               │
 │                     │                    ├──────────────────>│               │
 │                     │                    │                   │ Score models: │
 │                     │                    │                   │ - Cost: 0.4   │
 │                     │                    │                   │ - Latency: 0.4│
 │                     │                    │                   │ - Quality: 0.2│
 │                     │                    │<──────────────────┤               │
 │                     │                    │ provider="openrouter"             │
 │                     │                    │ model="mixtral"   │               │
 │                     │                    │                   │               │
 │                     │                    │ Forward request   │               │
 │                     │                    ├──────────────────────────────────>│
 │                     │                    │ {model, messages, │               │
 │                     │                    │  user_api_key}    │               │
 │                     │                    │                   │               │
 │                     │                    │<──────────────────────────────────┤
 │                     │                    │ response + usage  │               │
 │                     │                    │                   │               │
 │                     │                    │ Track usage &     │               │
 │                     │                    │ deduct credits    │               │
 │                     │                    ├──────────┐        │               │
 │                     │                    │          │        │               │
 │                     │                    │<─────────┘        │               │
 │                     │ 200 OK             │                   │               │
 │                     │ + metadata         │                   │               │
 │                     │<───────────────────┤                   │               │
 │ Response displayed  │                    │                   │               │
 │<────────────────────┤                    │                   │               │
```

#### 1.2.3 Power Level Selection and Routing Logic

```
User Selects         Routing Engine       Provider Database      LiteLLM
Power Level          Logic
 │                       │                       │                  │
 │ "Eco"                 │                       │                  │
 ├──────────────────────>│                       │                  │
 │                       │ Query enabled models  │                  │
 │                       │ for "eco" tier        │                  │
 │                       ├──────────────────────>│                  │
 │                       │                       │                  │
 │                       │<──────────────────────┤                  │
 │                       │ [groq/llama3-70b,     │                  │
 │                       │  local/qwen-32b,      │                  │
 │                       │  hf/mixtral-8x7b]     │                  │
 │                       │                       │                  │
 │                       │ Calculate scores:     │                  │
 │                       │ ┌──────────────────┐  │                  │
 │                       │ │ groq: 0.95       │  │                  │
 │                       │ │ (free, fast)     │  │                  │
 │                       │ │ local: 0.90      │  │                  │
 │                       │ │ (free, slower)   │  │                  │
 │                       │ │ hf: 0.85         │  │                  │
 │                       │ │ (free, slowest)  │  │                  │
 │                       │ └──────────────────┘  │                  │
 │                       │                       │                  │
 │                       │ Selected: groq        │                  │
 │                       │                       │                  │
 │                       │ Route request         │                  │
 │                       ├──────────────────────────────────────────>│
 │                       │                       │                  │
 │                       │ (If groq fails)       │                  │
 │                       │ Fallback: local       │                  │
 │                       ├──────────────────────────────────────────>│
 │                       │                       │                  │
```

#### 1.2.4 Fallback Mechanisms When Primary Provider Fails

```
Request             Primary Provider    Fallback Logic      Secondary Provider    Response
  │                       │                   │                      │               │
  │ Chat request          │                   │                      │               │
  ├──────────────────────>│                   │                      │               │
  │                       │ Process...        │                      │               │
  │                       ├──────────┐        │                      │               │
  │                       │          │        │                      │               │
  │                       │<─────────┘        │                      │               │
  │                       │ 429 Rate Limited  │                      │               │
  │                       ├──────────────────>│                      │               │
  │                       │                   │ Check fallback list  │               │
  │                       │                   ├──────────┐           │               │
  │                       │                   │          │           │               │
  │                       │                   │<─────────┘           │               │
  │                       │                   │                      │               │
  │                       │                   │ Select next provider │               │
  │                       │                   ├─────────────────────>│               │
  │                       │                   │                      │ Process...    │
  │                       │                   │                      ├──────────┐    │
  │                       │                   │                      │          │    │
  │                       │                   │                      │<─────────┘    │
  │                       │                   │<─────────────────────┤               │
  │                       │                   │ 200 OK               │               │
  │                       │                   │                      │               │
  │<──────────────────────┴───────────────────┤                      │               │
  │ Response + metadata                       │                      │               │
  │ (used_provider: "secondary")              │                      │               │
```

---

## 2. Database Schema Design

### 2.1 PostgreSQL Tables

#### 2.1.1 `llm_providers` - Available LLM Providers

**Purpose**: Store configuration for all LLM providers (admin-managed).

```sql
CREATE TABLE IF NOT EXISTS llm_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,                    -- Display name (e.g., "OpenRouter")
    type VARCHAR(50) NOT NULL,                     -- Provider type (openrouter, openai, anthropic, etc.)
    api_key_encrypted TEXT,                        -- Platform API key (encrypted with Fernet)
    api_base_url TEXT NOT NULL,                    -- API endpoint URL
    enabled BOOLEAN DEFAULT true,                  -- Enable/disable provider
    priority INTEGER DEFAULT 0,                    -- Routing priority (higher = preferred)
    config JSONB DEFAULT '{}',                     -- Provider-specific config
    health_status VARCHAR(20) DEFAULT 'unknown',   -- healthy, unhealthy, unknown
    last_health_check TIMESTAMP,                   -- Last health check time
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(name, type)
);

-- Indexes
CREATE INDEX idx_llm_providers_enabled ON llm_providers(enabled);
CREATE INDEX idx_llm_providers_priority ON llm_providers(priority DESC);
CREATE INDEX idx_llm_providers_health ON llm_providers(health_status);
```

**Example Data**:
```sql
INSERT INTO llm_providers (name, type, api_key_encrypted, api_base_url, priority) VALUES
('OpenRouter', 'openrouter', 'gAAAAABl...', 'https://openrouter.ai/api', 90),
('Platform OpenAI', 'openai', 'gAAAAABl...', 'https://api.openai.com', 80),
('Platform Anthropic', 'anthropic', 'gAAAAABl...', 'https://api.anthropic.com', 80),
('Together AI', 'together', 'gAAAAABl...', 'https://api.together.xyz', 70),
('Groq', 'groq', NULL, 'https://api.groq.com', 60),
('Local vLLM', 'local', NULL, 'http://unicorn-vllm:8000', 100);
```

#### 2.1.2 `llm_models` - Available Models with Metadata

**Purpose**: Store model information including cost, context length, and performance metrics.

```sql
CREATE TABLE IF NOT EXISTS llm_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES llm_providers(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,                    -- Model identifier (e.g., "gpt-4o")
    display_name VARCHAR(200),                     -- Human-readable name
    cost_per_1m_input_tokens DECIMAL(10, 4),       -- Input token cost per 1M tokens
    cost_per_1m_output_tokens DECIMAL(10, 4),      -- Output token cost per 1M tokens
    context_length INTEGER,                        -- Max context window
    enabled BOOLEAN DEFAULT true,                  -- Enable/disable model
    metadata JSONB DEFAULT '{}',                   -- Additional metadata
    avg_latency_ms INTEGER,                        -- Average latency (milliseconds)
    quality_score DECIMAL(3, 2),                   -- Quality rating (0.00-1.00)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(provider_id, name)
);

-- Indexes
CREATE INDEX idx_llm_models_enabled ON llm_models(enabled);
CREATE INDEX idx_llm_models_provider ON llm_models(provider_id);
CREATE INDEX idx_llm_models_cost ON llm_models(cost_per_1m_input_tokens);
CREATE INDEX idx_llm_models_quality ON llm_models(quality_score DESC);
```

**Example Data**:
```sql
INSERT INTO llm_models (provider_id, name, display_name, cost_per_1m_input_tokens, cost_per_1m_output_tokens, context_length, quality_score, avg_latency_ms) VALUES
-- Free tier (OpenRouter)
('<openrouter_uuid>', 'openai/gpt-3.5-turbo', 'GPT-3.5 Turbo (OpenRouter)', 0.50, 1.50, 16385, 0.75, 800),
('<openrouter_uuid>', 'meta-llama/llama-3-70b', 'Llama 3 70B (OpenRouter)', 0.60, 0.80, 8192, 0.80, 1200),

-- Starter tier (Together AI)
('<together_uuid>', 'mistralai/Mixtral-8x22B-Instruct-v0.1', 'Mixtral 8x22B', 1.20, 1.20, 65536, 0.85, 1500),

-- Professional tier (Platform)
('<openai_uuid>', 'gpt-4o', 'GPT-4 Optimized', 5.00, 15.00, 128000, 0.95, 2000),
('<anthropic_uuid>', 'claude-3-5-sonnet-20241022', 'Claude 3.5 Sonnet', 3.00, 15.00, 200000, 0.98, 1800),

-- Local (Free)
('<local_uuid>', 'qwen-32b-awq', 'Qwen 2.5 32B (Local)', 0.00, 0.00, 32768, 0.85, 500);
```

#### 2.1.3 `user_provider_keys` - User BYOK Keys (Existing)

**Purpose**: Store user-provided API keys (BYOK).

**Note**: This table already exists in `byok_manager.py` implementation. Showing complete schema for reference.

```sql
CREATE TABLE IF NOT EXISTS user_provider_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,                 -- Keycloak user ID
    provider VARCHAR(50) NOT NULL,                 -- Provider type (openai, anthropic, etc.)
    api_key_encrypted TEXT NOT NULL,               -- Encrypted API key (Fernet)
    metadata JSONB DEFAULT '{}',                   -- User preferences for this provider
    enabled BOOLEAN DEFAULT true,                  -- Enable/disable this key
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(user_id, provider)
);

-- Indexes
CREATE INDEX idx_user_provider_keys_user ON user_provider_keys(user_id);
CREATE INDEX idx_user_provider_keys_enabled ON user_provider_keys(user_id, enabled);
```

**Example Data**:
```sql
INSERT INTO user_provider_keys (user_id, provider, api_key_encrypted, enabled) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'openai', 'gAAAAABl...sk-abc123...', true),
('550e8400-e29b-41d4-a716-446655440000', 'anthropic', 'gAAAAABl...sk-ant-xyz789...', true);
```

#### 2.1.4 `llm_routing_rules` - Routing Configuration

**Purpose**: Store global routing rules and strategies.

```sql
CREATE TABLE IF NOT EXISTS llm_routing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy VARCHAR(50) NOT NULL DEFAULT 'balanced',  -- cost, latency, balanced, custom
    fallback_providers UUID[] DEFAULT '{}',           -- Ordered list of fallback provider IDs
    model_aliases JSONB DEFAULT '{}',                 -- Model alias mappings
    config JSONB DEFAULT '{}',                        -- Strategy-specific config
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Default routing rule
INSERT INTO llm_routing_rules (strategy, config) VALUES
('balanced', '{
  "cost_weight": 0.4,
  "latency_weight": 0.4,
  "quality_weight": 0.2,
  "max_retries": 3,
  "retry_delay_ms": 500,
  "timeout_ms": 30000
}');
```

**Config Schema**:
```typescript
interface RoutingConfig {
  cost_weight: number;        // 0.0-1.0 (sum of weights = 1.0)
  latency_weight: number;     // 0.0-1.0
  quality_weight: number;     // 0.0-1.0
  max_retries: number;        // Max fallback attempts
  retry_delay_ms: number;     // Delay between retries
  timeout_ms: number;         // Request timeout
}
```

#### 2.1.5 `user_llm_settings` - User Preferences

**Purpose**: Store per-user LLM preferences (power level, preferences).

```sql
CREATE TABLE IF NOT EXISTS user_llm_settings (
    user_id VARCHAR(100) PRIMARY KEY,              -- Keycloak user ID
    power_level VARCHAR(20) DEFAULT 'balanced',    -- eco, balanced, precision
    credit_balance DECIMAL(10, 2) DEFAULT 0,       -- Remaining credits
    preferences JSONB DEFAULT '{}',                -- User-specific preferences
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_user_llm_settings_power ON user_llm_settings(power_level);
```

**Example Data**:
```sql
INSERT INTO user_llm_settings (user_id, power_level, credit_balance, preferences) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'balanced', 10.50, '{
  "preferred_providers": ["openai", "anthropic"],
  "max_cost_per_request": 0.05,
  "auto_fallback": true,
  "monthly_cap": 100.00
}');
```

#### 2.1.6 `llm_usage_logs` - Usage Tracking

**Purpose**: Track all LLM requests for billing and analytics.

```sql
CREATE TABLE IF NOT EXISTS llm_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,                 -- Keycloak user ID
    provider_id UUID REFERENCES llm_providers(id), -- Provider used
    model_name VARCHAR(200),                       -- Model used
    input_tokens INTEGER,                          -- Input token count
    output_tokens INTEGER,                         -- Output token count
    cost DECIMAL(10, 6),                           -- Cost incurred (credits)
    latency_ms INTEGER,                            -- Request latency
    power_level VARCHAR(20),                       -- User power level at time of request
    status VARCHAR(20),                            -- success, error, timeout
    error_message TEXT,                            -- Error details (if failed)
    metadata JSONB DEFAULT '{}',                   -- Request metadata
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_llm_usage_user ON llm_usage_logs(user_id);
CREATE INDEX idx_llm_usage_created ON llm_usage_logs(created_at DESC);
CREATE INDEX idx_llm_usage_provider ON llm_usage_logs(provider_id);
CREATE INDEX idx_llm_usage_status ON llm_usage_logs(status);

-- Partitioning by month (for large-scale deployments)
-- CREATE TABLE llm_usage_logs_2025_10 PARTITION OF llm_usage_logs
-- FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
```

### 2.2 Database Relationships

```
┌─────────────────┐
│ llm_providers   │
│ (Admin config)  │
└────────┬────────┘
         │
         │ 1:N
         │
┌────────▼────────┐       ┌─────────────────────┐
│ llm_models      │       │ user_provider_keys  │
│ (Model catalog) │       │ (User BYOK keys)    │
└─────────────────┘       └──────────┬──────────┘
                                     │
         ┌───────────────────────────┘
         │
         │ N:1
         │
┌────────▼────────────┐       ┌──────────────────┐
│ user_llm_settings   │       │ llm_routing_rules│
│ (User preferences)  │       │ (Global rules)   │
└────────┬────────────┘       └──────────────────┘
         │
         │ 1:N
         │
┌────────▼────────┐
│ llm_usage_logs  │
│ (Usage tracking)│
└─────────────────┘
```

---

## 3. API Architecture

### 3.1 API Endpoint Specifications

All endpoints use RESTful conventions and return JSON.

**Base Path**: `/api/v1/llm`

#### 3.1.1 Provider Management (Admin Only)

##### List Providers
```http
GET /api/v1/llm/providers?enabled_only=false
```

**Query Parameters**:
- `enabled_only` (boolean, optional): Filter to enabled providers only

**Response** (200 OK):
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "OpenRouter",
    "type": "openrouter",
    "status": "active",
    "models": 15,
    "avg_cost_per_1m": 1.25,
    "enabled_models": ["openai/gpt-3.5-turbo", "meta-llama/llama-3-70b"],
    "priority": 90,
    "health_status": "healthy",
    "last_health_check": "2025-10-23T10:30:00Z"
  }
]
```

##### Create Provider
```http
POST /api/v1/llm/providers
```

**Request Body**:
```json
{
  "name": "OpenRouter",
  "type": "openrouter",
  "api_key": "sk-or-v1-abc123...",
  "api_base_url": "https://openrouter.ai/api",
  "enabled": true,
  "priority": 90,
  "config": {
    "timeout": 30000,
    "max_retries": 3
  }
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "OpenRouter",
  "type": "openrouter",
  "enabled": true,
  "priority": 90,
  "message": "Provider created successfully. Testing connection..."
}
```

##### Update Provider
```http
PUT /api/v1/llm/providers/{provider_id}
```

**Request Body**:
```json
{
  "api_key": "sk-or-v1-new-key...",
  "enabled": false,
  "priority": 80
}
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "OpenRouter",
  "type": "openrouter",
  "enabled": false,
  "priority": 80,
  "message": "Provider updated successfully"
}
```

##### Delete Provider
```http
DELETE /api/v1/llm/providers/{provider_id}
```

**Response** (200 OK):
```json
{
  "message": "Provider deleted successfully",
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

##### Test Provider Connection
```http
POST /api/v1/llm/test
```

**Request Body**:
```json
{
  "provider_id": "550e8400-e29b-41d4-a716-446655440000",
  "model": "gpt-3.5-turbo"
}
```

**Response** (200 OK):
```json
{
  "provider_id": "550e8400-e29b-41d4-a716-446655440000",
  "provider_name": "OpenRouter",
  "status": "success",
  "latency_ms": 842,
  "message": "Provider connection successful"
}
```

#### 3.1.2 Model Management (Admin Only)

##### List Models
```http
GET /api/v1/llm/models?provider_id=<uuid>&enabled_only=true&sort_by=cost
```

**Query Parameters**:
- `provider_id` (UUID, optional): Filter by provider
- `enabled_only` (boolean, optional): Only enabled models
- `sort_by` (string, optional): Sort by `cost`, `latency`, or `name`

**Response** (200 OK):
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "provider_id": "550e8400-e29b-41d4-a716-446655440000",
    "provider_name": "OpenRouter",
    "name": "openai/gpt-3.5-turbo",
    "display_name": "GPT-3.5 Turbo",
    "cost_per_1m_input": 0.50,
    "cost_per_1m_output": 1.50,
    "context_length": 16385,
    "enabled": true,
    "avg_latency_ms": 800
  }
]
```

##### Create Model
```http
POST /api/v1/llm/models
```

**Request Body**:
```json
{
  "provider_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "openai/gpt-4o",
  "display_name": "GPT-4 Optimized",
  "cost_per_1m_input_tokens": 5.00,
  "cost_per_1m_output_tokens": 15.00,
  "context_length": 128000,
  "enabled": true,
  "metadata": {
    "supports_vision": true,
    "supports_function_calling": true
  }
}
```

**Response** (201 Created):
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "openai/gpt-4o",
  "display_name": "GPT-4 Optimized",
  "message": "Model created successfully"
}
```

#### 3.1.3 Routing Rules Management (Admin Only)

##### Get Routing Rules
```http
GET /api/v1/llm/routing/rules
```

**Response** (200 OK):
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "strategy": "balanced",
  "fallback_providers": [
    "550e8400-e29b-41d4-a716-446655440000",
    "660e8400-e29b-41d4-a716-446655440000"
  ],
  "model_aliases": {
    "gpt-4": "openai/gpt-4o",
    "claude": "anthropic/claude-3-5-sonnet-20241022"
  },
  "config": {
    "cost_weight": 0.4,
    "latency_weight": 0.4,
    "quality_weight": 0.2,
    "max_retries": 3,
    "retry_delay_ms": 500
  },
  "power_levels": {
    "eco": "Use cheapest models (OpenRouter budget tier)",
    "balanced": "Balance cost and quality (mix of providers)",
    "precision": "Use best models (OpenAI, Anthropic direct)"
  }
}
```

##### Update Routing Rules
```http
PUT /api/v1/llm/routing/rules
```

**Request Body**:
```json
{
  "strategy": "balanced",
  "fallback_providers": [
    "550e8400-e29b-41d4-a716-446655440000"
  ],
  "model_aliases": {
    "gpt-4": "openai/gpt-4o"
  },
  "config": {
    "cost_weight": 0.5,
    "latency_weight": 0.3,
    "quality_weight": 0.2
  }
}
```

**Response** (200 OK):
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "strategy": "balanced",
  "fallback_providers": ["550e8400-e29b-41d4-a716-446655440000"],
  "model_aliases": {"gpt-4": "openai/gpt-4o"},
  "config": {...},
  "message": "Routing rules updated successfully"
}
```

#### 3.1.4 User BYOK Management

##### Add/Update User API Key
```http
POST /api/v1/llm/users/{user_id}/byok
```

**Request Body**:
```json
{
  "provider_type": "openai",
  "api_key": "sk-abc123...",
  "enabled": true,
  "preferences": {
    "preferred_models": ["gpt-4o", "gpt-3.5-turbo"],
    "max_cost_per_request": 0.10
  }
}
```

**Response** (201 Created):
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "provider_type": "openai",
  "enabled": true,
  "power_level": "balanced",
  "credit_balance": 10.50,
  "message": "BYOK configuration updated successfully"
}
```

##### Get User BYOK Keys (Masked)
```http
GET /api/v1/llm/users/{user_id}/byok
```

**Response** (200 OK):
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "byok_providers": {
    "openai": {
      "enabled": true,
      "api_key": "sk-...****",
      "preferences": {
        "preferred_models": ["gpt-4o"]
      },
      "updated_at": "2025-10-23T10:30:00Z"
    },
    "anthropic": {
      "enabled": true,
      "api_key": "sk-ant-...****",
      "preferences": {},
      "updated_at": "2025-10-22T15:20:00Z"
    }
  },
  "power_level": "balanced",
  "credit_balance": 10.50,
  "preferences": {
    "monthly_cap": 100.00
  }
}
```

##### Delete User API Key
```http
DELETE /api/v1/llm/users/{user_id}/byok/{provider}
```

**Response** (200 OK):
```json
{
  "message": "API key deleted successfully",
  "provider": "openai"
}
```

#### 3.1.5 LLM Chat Completions (User-Facing)

##### Chat Completions (OpenAI-Compatible)
```http
POST /api/v1/llm/chat/completions
```

**Request Headers**:
- `Authorization: Bearer <user-api-key>`
- `X-Power-Level: eco | balanced | precision` (optional, overrides user default)

**Request Body** (OpenAI-compatible):
```json
{
  "model": "gpt-4o",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"}
  ],
  "max_tokens": 100,
  "temperature": 0.7,
  "stream": false,
  "power_level": "balanced"
}
```

**Response** (200 OK):
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1698152400,
  "model": "openai/gpt-4o",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The capital of France is Paris."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 8,
    "total_tokens": 33
  },
  "_metadata": {
    "provider_used": "openrouter",
    "cost_incurred": 0.0016,
    "credits_remaining": 10.4984,
    "transaction_id": "880e8400-e29b-41d4-a716-446655440000",
    "power_level": "balanced",
    "user_tier": "professional"
  }
}
```

**Error Response** (402 Payment Required - Insufficient Credits):
```json
{
  "error": {
    "message": "Insufficient credits. Balance: 0.005, Estimated cost: 0.010",
    "type": "insufficient_credits",
    "code": "payment_required"
  }
}
```

#### 3.1.6 Usage Analytics

##### Get User Usage Statistics
```http
GET /api/v1/llm/usage?user_id=<uuid>&days=7&provider_id=<uuid>
```

**Query Parameters**:
- `user_id` (UUID, optional): Filter by user (admin only without user_id)
- `days` (integer, optional): Number of days to analyze (default 7)
- `provider_id` (UUID, optional): Filter by provider

**Response** (200 OK):
```json
{
  "total_requests": 150,
  "total_tokens": 45000,
  "total_cost": 2.35,
  "avg_cost_per_request": 0.0157,
  "providers": [
    {
      "provider_id": "550e8400-e29b-41d4-a716-446655440000",
      "provider_name": "OpenRouter",
      "requests": 120,
      "tokens": 36000,
      "cost": 1.80,
      "avg_latency_ms": 850,
      "unique_users": 1
    },
    {
      "provider_id": "660e8400-e29b-41d4-a716-446655440000",
      "provider_name": "Platform OpenAI",
      "requests": 30,
      "tokens": 9000,
      "cost": 0.55,
      "avg_latency_ms": 1200,
      "unique_users": 1
    }
  ],
  "period_days": 7
}
```

##### Get Credit Status
```http
GET /api/v1/llm/credits?user_id=<uuid>
```

**Response** (200 OK):
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "credits_remaining": 10.50,
  "power_level": "balanced",
  "monthly_cap": 100.00,
  "usage_this_month": 15.25,
  "percentage_used": 15.25
}
```

### 3.2 API Error Responses

**Standard Error Format**:
```json
{
  "error": {
    "message": "Detailed error message",
    "type": "error_type",
    "code": "http_status_code"
  }
}
```

**Common Error Codes**:
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid API key
- `402 Payment Required` - Insufficient credits
- `403 Forbidden` - User lacks required permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded or monthly cap reached
- `500 Internal Server Error` - Server-side error
- `503 Service Unavailable` - All providers unavailable

---

## 4. Security Architecture

### 4.1 API Key Encryption Strategy

**Encryption Method**: Fernet (AES-128-CBC with HMAC authentication)

**Implementation**:
```python
from cryptography.fernet import Fernet

# Generate encryption key (one-time, store in environment)
encryption_key = Fernet.generate_key()
# Example: b'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='

# Store in .env.auth
BYOK_ENCRYPTION_KEY=ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=

# Encrypt API key before storage
cipher = Fernet(BYOK_ENCRYPTION_KEY.encode())
encrypted_key = cipher.encrypt("sk-abc123...".encode())

# Decrypt API key before use
decrypted_key = cipher.decrypt(encrypted_key).decode()
```

**Security Properties**:
- **Symmetric encryption**: Same key encrypts and decrypts
- **HMAC authentication**: Prevents tampering
- **Key rotation**: Support for re-encrypting all keys with new master key
- **Environment storage**: Master key never stored in database
- **Transport security**: Always use HTTPS for API requests

### 4.2 Key Access Control

**Access Control Rules**:

1. **Platform API Keys** (Admin-managed):
   - **Write**: System admins only
   - **Read**: System admins + backend services (encrypted)
   - **Use**: All users (via routing logic)

2. **User BYOK Keys**:
   - **Write**: Key owner only
   - **Read**: Key owner only (masked display)
   - **Decrypt**: Backend services for routing only
   - **Use**: Key owner only

**Database Security**:
```sql
-- Row-level security (RLS) for user_provider_keys
CREATE POLICY user_provider_keys_policy ON user_provider_keys
  FOR ALL
  USING (user_id = current_setting('app.current_user_id')::VARCHAR);

-- Enable RLS
ALTER TABLE user_provider_keys ENABLE ROW LEVEL SECURITY;
```

**API Security**:
```python
# Verify user can only access their own keys
async def verify_key_ownership(user_id: str, key_user_id: str):
    if user_id != key_user_id and not is_admin(user_id):
        raise HTTPException(status_code=403, detail="Access denied")
```

### 4.3 Audit Logging

**Log All Key Operations**:
```python
# Log to audit_logs table
await audit_logger.log(
    user_id=user_id,
    action="byok_key_added",
    resource_type="user_provider_key",
    resource_id=key_id,
    details={
        "provider": provider,
        "key_masked": "sk-...****"
    },
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)
```

**Audit Events**:
- `byok_key_added` - User adds API key
- `byok_key_updated` - User updates API key
- `byok_key_deleted` - User deletes API key
- `byok_key_toggled` - User enables/disables key
- `byok_key_accessed` - System decrypts key for use (high-frequency, sample logging)

### 4.4 Rate Limiting Per User/Tier

**Rate Limit Configuration** (per user, per subscription tier):

```python
RATE_LIMITS = {
    "trial": {
        "requests_per_minute": 10,
        "requests_per_hour": 100,
        "requests_per_day": 500
    },
    "starter": {
        "requests_per_minute": 30,
        "requests_per_hour": 1000,
        "requests_per_day": 10000
    },
    "professional": {
        "requests_per_minute": 100,
        "requests_per_hour": 5000,
        "requests_per_day": 50000
    },
    "enterprise": {
        "requests_per_minute": 500,
        "requests_per_hour": 20000,
        "requests_per_day": -1  # Unlimited
    }
}
```

**Implementation** (Redis-based sliding window):
```python
import redis.asyncio as aioredis

async def check_rate_limit(user_id: str, tier: str) -> bool:
    """Check if user is within rate limits"""
    redis_client = aioredis.from_url("redis://unicorn-redis:6379")

    # Check minute window
    minute_key = f"rate_limit:{user_id}:minute:{int(time.time() / 60)}"
    minute_count = await redis_client.incr(minute_key)
    await redis_client.expire(minute_key, 60)

    if minute_count > RATE_LIMITS[tier]["requests_per_minute"]:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Check hour and day windows similarly...
    return True
```

### 4.5 Key Rotation Support

**Rotation Procedure**:

1. **Generate new master key**:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

2. **Run rotation script**:
```python
async def rotate_encryption_keys(old_key: str, new_key: str):
    """Re-encrypt all API keys with new master key"""
    old_cipher = Fernet(old_key.encode())
    new_cipher = Fernet(new_key.encode())

    # Fetch all encrypted keys
    keys = await db.fetch("SELECT id, api_key_encrypted FROM user_provider_keys")

    for key in keys:
        # Decrypt with old key
        decrypted = old_cipher.decrypt(key['api_key_encrypted'].encode()).decode()

        # Re-encrypt with new key
        re_encrypted = new_cipher.encrypt(decrypted.encode()).decode()

        # Update database
        await db.execute(
            "UPDATE user_provider_keys SET api_key_encrypted = $1 WHERE id = $2",
            re_encrypted, key['id']
        )

    logger.info(f"Rotated {len(keys)} API keys")
```

3. **Update environment variable**:
```bash
# Update .env.auth
BYOK_ENCRYPTION_KEY=<new_key>

# Restart services
docker restart ops-center-direct
```

---

## 5. Routing Logic Architecture

### 5.1 Power Level to Model Mapping

**Power Level Definitions**:

```python
POWER_LEVEL_CONFIG = {
    "eco": {
        "description": "Cost-optimized (free or low-cost providers)",
        "max_cost_per_1k_tokens": 0.001,
        "preferred_providers": ["local", "groq", "huggingface"],
        "fallback_providers": ["openrouter:free"],
        "scoring_weights": {
            "cost": 0.7,
            "latency": 0.2,
            "quality": 0.1
        }
    },
    "balanced": {
        "description": "Balance cost and quality",
        "max_cost_per_1k_tokens": 0.01,
        "preferred_providers": ["openrouter", "together", "fireworks"],
        "fallback_providers": ["groq", "local"],
        "scoring_weights": {
            "cost": 0.4,
            "latency": 0.4,
            "quality": 0.2
        }
    },
    "precision": {
        "description": "Quality-optimized (best models)",
        "max_cost_per_1k_tokens": 0.1,
        "preferred_providers": ["openai", "anthropic", "openrouter:premium"],
        "fallback_providers": ["openrouter", "together"],
        "scoring_weights": {
            "cost": 0.1,
            "latency": 0.3,
            "quality": 0.6
        }
    }
}
```

### 5.2 Cost Optimization Algorithm (WilmerAI-style)

**Scoring Function**:

```python
def calculate_provider_score(
    model: Dict,
    power_level: str,
    routing_config: Dict,
    historical_data: Dict
) -> float:
    """
    Calculate provider score based on cost, latency, and quality

    Args:
        model: Model metadata (cost, latency, quality_score)
        power_level: User power level (eco, balanced, precision)
        routing_config: Routing configuration from database
        historical_data: Recent performance metrics

    Returns:
        Score between 0.0 (worst) and 1.0 (best)
    """
    weights = POWER_LEVEL_CONFIG[power_level]["scoring_weights"]

    # 1. Cost score (lower is better)
    max_cost = max(m['cost'] for m in all_models)
    cost_score = 1.0 - (model['cost_per_1m_input_tokens'] / max_cost)

    # 2. Latency score (lower is better)
    max_latency = max(m['avg_latency_ms'] for m in all_models)
    latency_score = 1.0 - (model['avg_latency_ms'] / max_latency)

    # 3. Quality score (from model metadata)
    quality_score = model['quality_score']  # 0.0-1.0

    # 4. Weighted composite score
    composite_score = (
        weights['cost'] * cost_score +
        weights['latency'] * latency_score +
        weights['quality'] * quality_score
    )

    # 5. Apply penalties
    # Penalize if provider has recent errors
    error_rate = historical_data.get('error_rate', 0.0)
    composite_score *= (1.0 - error_rate * 0.5)

    # Penalize if provider is near rate limits
    rate_limit_usage = historical_data.get('rate_limit_usage', 0.0)
    if rate_limit_usage > 0.8:
        composite_score *= 0.5

    return composite_score
```

**Example Calculation**:

```python
# User selects "balanced" power level
power_level = "balanced"
weights = {"cost": 0.4, "latency": 0.4, "quality": 0.2}

# Available models
models = [
    {
        "name": "groq/llama3-70b",
        "cost_per_1m_input_tokens": 0.0,
        "avg_latency_ms": 600,
        "quality_score": 0.80
    },
    {
        "name": "openrouter/mixtral-8x22b",
        "cost_per_1m_input_tokens": 1.2,
        "avg_latency_ms": 1500,
        "quality_score": 0.85
    },
    {
        "name": "openai/gpt-4o",
        "cost_per_1m_input_tokens": 5.0,
        "avg_latency_ms": 2000,
        "quality_score": 0.95
    }
]

# Calculate scores
# Groq: cost=1.0, latency=1.0, quality=0.80 → 0.4*1.0 + 0.4*1.0 + 0.2*0.80 = 0.96
# OpenRouter: cost=0.76, latency=0.73, quality=0.85 → 0.4*0.76 + 0.4*0.73 + 0.2*0.85 = 0.766
# OpenAI: cost=0.0, latency=0.0, quality=0.95 → 0.4*0.0 + 0.4*0.0 + 0.2*0.95 = 0.19

# Winner: groq/llama3-70b (score: 0.96)
```

### 5.3 Fallback Strategies

**Fallback Decision Tree**:

```
┌─────────────────────────────────────┐
│ 1. Try Primary Provider             │
│    (highest score from routing)     │
└─────────────┬───────────────────────┘
              │
              ▼
         ┌─────────┐
         │ Success?│
         └─────────┘
              │
         Yes──┴──No
          │        │
          │        ▼
          │   ┌─────────────────────────┐
          │   │ Error Type?             │
          │   └─────────────────────────┘
          │             │
          │        ┌────┼────┐
          │        ▼    ▼    ▼
          │      Rate Auth  Timeout
          │      Limit
          │        │    │    │
          │        └────┼────┘
          │             │
          │             ▼
          │   ┌─────────────────────────┐
          │   │ 2. Try Fallback Provider│
          │   │    (next highest score) │
          │   └─────────────────────────┘
          │             │
          │             ▼
          │        ┌─────────┐
          │        │ Success?│
          │        └─────────┘
          │             │
          │        Yes──┴──No
          │         │        │
          │         │        ▼
          │         │   ┌─────────────────────────┐
          │         │   │ 3. Try Secondary        │
          │         │   │    Fallback (if exists) │
          │         │   └─────────────────────────┘
          │         │        │
          │         │        ▼
          │         │   ┌─────────┐
          │         │   │ Success?│
          │         │   └─────────┘
          │         │        │
          │         │   Yes──┴──No
          │         │    │        │
          │         │    │        ▼
          │         │    │   ┌────────────────┐
          │         │    │   │ 4. Return Error│
          │         │    │   │ "All providers │
          │         │    │   │  unavailable"  │
          │         │    │   └────────────────┘
          │         │    │
          └─────────┴────┘
                   │
                   ▼
            ┌──────────────────┐
            │ Return Response  │
            │ + Metadata       │
            │ (provider used,  │
            │  cost, credits)  │
            └──────────────────┘
```

**Implementation**:

```python
async def route_request_with_fallback(
    request: ChatCompletionRequest,
    user_id: str,
    power_level: str,
    max_retries: int = 3
) -> Dict:
    """Route request with automatic fallback"""

    # 1. Get available providers
    providers = await get_available_providers(user_id, power_level)

    # 2. Score and sort providers
    scored_providers = []
    for provider in providers:
        score = calculate_provider_score(provider, power_level, routing_config, historical_data)
        scored_providers.append((score, provider))

    scored_providers.sort(reverse=True, key=lambda x: x[0])

    # 3. Try providers in order
    for attempt, (score, provider) in enumerate(scored_providers):
        if attempt >= max_retries:
            break

        try:
            # Try request with this provider
            response = await make_llm_request(provider, request, user_id)

            # Success! Return response
            return {
                "success": True,
                "response": response,
                "provider_used": provider['name'],
                "attempts": attempt + 1
            }

        except RateLimitError:
            logger.warning(f"Rate limit hit for {provider['name']}, trying fallback")
            # Mark provider as temporarily unavailable
            await redis_client.setex(
                f"provider:{provider['id']}:rate_limited",
                300,  # 5 minutes
                "1"
            )
            continue

        except AuthenticationError:
            logger.error(f"Auth failed for {provider['name']}, trying fallback")
            # Mark provider as unhealthy
            await db.execute(
                "UPDATE llm_providers SET health_status = 'unhealthy' WHERE id = $1",
                provider['id']
            )
            continue

        except TimeoutError:
            logger.warning(f"Timeout for {provider['name']}, trying fallback")
            continue

        except Exception as e:
            logger.error(f"Unknown error for {provider['name']}: {e}")
            continue

    # All providers failed
    raise HTTPException(
        status_code=503,
        detail="All LLM providers are currently unavailable"
    )
```

### 5.4 Load Balancing Across Providers

**Round-Robin with Health Checks**:

```python
async def select_provider_with_load_balancing(
    providers: List[Dict],
    power_level: str
) -> Dict:
    """
    Select provider using weighted round-robin

    Weights are based on:
    - Provider priority
    - Current health status
    - Recent latency
    """

    # 1. Filter to healthy providers
    healthy_providers = [
        p for p in providers
        if p['health_status'] == 'healthy'
    ]

    if not healthy_providers:
        # Fall back to any provider
        healthy_providers = providers

    # 2. Calculate weights
    total_priority = sum(p['priority'] for p in healthy_providers)
    weights = [p['priority'] / total_priority for p in healthy_providers]

    # 3. Select provider using weighted random choice
    import random
    selected = random.choices(healthy_providers, weights=weights, k=1)[0]

    return selected
```

**Sticky Sessions** (for multi-turn conversations):

```python
async def get_provider_for_conversation(
    conversation_id: str,
    user_id: str,
    power_level: str
) -> Dict:
    """
    Ensure same provider is used for entire conversation
    """

    # Check if conversation has existing provider
    cache_key = f"conversation:{conversation_id}:provider"
    cached_provider_id = await redis_client.get(cache_key)

    if cached_provider_id:
        # Use existing provider
        provider = await db.fetchrow(
            "SELECT * FROM llm_providers WHERE id = $1 AND enabled = true",
            cached_provider_id
        )
        if provider:
            return provider

    # Select new provider and cache
    provider = await select_provider(user_id, power_level)
    await redis_client.setex(cache_key, 3600, str(provider['id']))  # 1 hour

    return provider
```

---

## 6. Frontend Architecture

### 6.1 Component Hierarchy

```
App.jsx
├── Layout.jsx
│   ├── Sidebar.jsx
│   └── Header.jsx
└── Routes
    ├── /admin/llm/providers → ProviderManagement.jsx
    │   ├── ProviderList.jsx
    │   ├── ProviderCard.jsx
    │   ├── CreateProviderModal.jsx
    │   ├── EditProviderModal.jsx
    │   └── TestProviderDialog.jsx
    │
    ├── /admin/llm/models → ModelManagement.jsx
    │   ├── ModelList.jsx
    │   ├── ModelCard.jsx
    │   ├── CreateModelModal.jsx
    │   └── EditModelModal.jsx
    │
    ├── /admin/llm/routing → RoutingConfig.jsx
    │   ├── RoutingStrategySelector.jsx
    │   ├── PowerLevelSettings.jsx
    │   ├── FallbackProviderList.jsx
    │   └── ModelAliasEditor.jsx
    │
    ├── /account/llm/byok → BYOKManager.jsx (User-facing)
    │   ├── ProviderKeyList.jsx
    │   ├── AddKeyModal.jsx
    │   ├── EditKeyModal.jsx
    │   └── KeyValidationDialog.jsx
    │
    ├── /account/llm/settings → LLMSettings.jsx (User-facing)
    │   ├── PowerLevelSelector.jsx
    │   ├── PreferencesEditor.jsx
    │   └── UsageDashboard.jsx
    │
    └── /account/subscription/usage → UsageAnalytics.jsx
        ├── UsageChart.jsx (react-chartjs-2)
        ├── CostBreakdown.jsx
        ├── ProviderDistribution.jsx
        └── ExportButton.jsx
```

### 6.2 Provider Management UI (Admin)

**Page**: `/admin/llm/providers`

**Components**:

1. **ProviderList.jsx** - Grid of provider cards
2. **ProviderCard.jsx** - Individual provider with stats
3. **CreateProviderModal.jsx** - Add new provider
4. **TestProviderDialog.jsx** - Test provider connection

**Mockup**:

```
┌──────────────────────────────────────────────────────────────────┐
│                    LLM Provider Management                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  [+ Add Provider]  [⚙️ Routing Rules]  [📊 Analytics]           │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ OpenRouter      │  │ Platform OpenAI │  │ Together AI     │ │
│  │ ────────────────│  │ ────────────────│  │ ────────────────│ │
│  │ Status: Healthy │  │ Status: Healthy │  │ Status: Healthy │ │
│  │ Models: 15      │  │ Models: 6       │  │ Models: 8       │ │
│  │ Priority: 90    │  │ Priority: 80    │  │ Priority: 70    │ │
│  │ Avg Cost: $1.25 │  │ Avg Cost: $8.50 │  │ Avg Cost: $2.10 │ │
│  │                 │  │                 │  │                 │ │
│  │ [Edit] [Test]   │  │ [Edit] [Test]   │  │ [Edit] [Test]   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Groq (Free)     │  │ Local vLLM      │  │ Anthropic       │ │
│  │ ────────────────│  │ ────────────────│  │ ────────────────│ │
│  │ Status: Healthy │  │ Status: Healthy │  │ Status: Unknown │ │
│  │ Models: 4       │  │ Models: 1       │  │ Models: 3       │ │
│  │ Priority: 60    │  │ Priority: 100   │  │ Priority: 80    │ │
│  │ Avg Cost: $0.00 │  │ Avg Cost: $0.00 │  │ Avg Cost: $12.0 │ │
│  │                 │  │                 │  │                 │ │
│  │ [Edit] [Test]   │  │ [Edit] [Test]   │  │ [Edit] [Test]   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

**CreateProviderModal.jsx**:

```
┌──────────────────────────────────────────────┐
│          Add LLM Provider                    │
├──────────────────────────────────────────────┤
│                                              │
│  Provider Name: [OpenRouter____________]    │
│                                              │
│  Provider Type: [openrouter ▼]              │
│                 Options:                     │
│                 - openrouter                 │
│                 - openai                     │
│                 - anthropic                  │
│                 - together                   │
│                 - groq                       │
│                 - huggingface                │
│                 - custom                     │
│                                              │
│  API Key: [sk-or-v1-abc123********____]     │
│           [👁️ Show]                         │
│                                              │
│  API Base URL: [https://openrouter.ai/api]  │
│                (auto-filled)                 │
│                                              │
│  Priority: [90] (higher = more preferred)   │
│                                              │
│  Enabled: [✓] Enable this provider          │
│                                              │
│  Advanced Config (JSON): [▼]                │
│  ┌────────────────────────────────────────┐ │
│  │ {                                      │ │
│  │   "timeout": 30000,                    │ │
│  │   "max_retries": 3                     │ │
│  │ }                                      │ │
│  └────────────────────────────────────────┘ │
│                                              │
│           [Test Connection] [Cancel] [Add]   │
└──────────────────────────────────────────────┘
```

### 6.3 BYOK Configuration Wizard (User)

**Page**: `/account/llm/byok`

**Components**:

1. **ProviderKeyList.jsx** - List of configured keys
2. **AddKeyModal.jsx** - Add new API key
3. **KeyValidationDialog.jsx** - Validate key

**Mockup**:

```
┌──────────────────────────────────────────────────────────────────┐
│              Your API Keys (BYOK)                                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Bring Your Own Key (BYOK) allows you to use your own API keys   │
│  for LLM providers. Your keys are encrypted and secure.          │
│                                                                   │
│  [+ Add API Key]                                                  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ OpenAI                                    [Enabled ▼]       │ │
│  │ ─────────────────────────────────────────────────────────  │ │
│  │ API Key: sk-...****                                        │ │
│  │ Added: Oct 20, 2025                                        │ │
│  │ Last Used: Oct 23, 2025 (2 hours ago)                      │ │
│  │ Usage: 150 requests, $2.35 this month                      │ │
│  │                                                             │ │
│  │ Preferred Models:                                           │ │
│  │ • gpt-4o                                                    │ │
│  │ • gpt-3.5-turbo                                             │ │
│  │                                                             │ │
│  │ [Edit] [Delete] [View Usage]                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Anthropic                                 [Enabled ▼]       │ │
│  │ ─────────────────────────────────────────────────────────  │ │
│  │ API Key: sk-ant-...****                                    │ │
│  │ Added: Oct 22, 2025                                        │ │
│  │ Last Used: Never                                            │ │
│  │ Usage: 0 requests                                           │ │
│  │                                                             │ │
│  │ [Edit] [Delete]                                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  💡 Tip: When using your own keys, you'll only be charged for    │
│     the platform fee (10%), not the full model cost.             │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

**AddKeyModal.jsx**:

```
┌──────────────────────────────────────────────┐
│          Add API Key                         │
├──────────────────────────────────────────────┤
│                                              │
│  Provider: [OpenAI ▼]                        │
│            Options:                          │
│            - OpenAI                          │
│            - Anthropic (Claude)              │
│            - Together AI                     │
│            - Groq                            │
│            - HuggingFace                     │
│            - OpenRouter                      │
│                                              │
│  API Key: [sk-abc123******************___]   │
│           [👁️ Show]                         │
│                                              │
│  ⚠️  Security Note:                          │
│  Your API key is encrypted with AES-256      │
│  and stored securely. We never log your      │
│  keys in plaintext.                          │
│                                              │
│  Validation: [Validate Key]                  │
│  Status: ⏳ Not validated                    │
│                                              │
│  Preferences (Optional):                     │
│  ┌────────────────────────────────────────┐ │
│  │ Preferred Models:                      │ │
│  │ [✓] gpt-4o                             │ │
│  │ [✓] gpt-3.5-turbo                      │ │
│  │ [ ] gpt-4-turbo                        │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  Max Cost Per Request: [$0.10_______]       │
│                                              │
│           [Cancel] [Add Key]                 │
└──────────────────────────────────────────────┘
```

### 6.4 Power Level Selector UI (User)

**Page**: `/account/llm/settings`

**Component**: **PowerLevelSelector.jsx**

**Mockup**:

```
┌──────────────────────────────────────────────────────────────────┐
│              LLM Settings                                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Power Level                                                      │
│  ────────────────────────────────────────────────────────────   │
│  Select how the system routes your LLM requests                   │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ ⚡ Eco                                   [ ]                │ │
│  │ ─────────────────────────────────────────────────────────  │ │
│  │ Use free or low-cost providers (Groq, HuggingFace, Local)  │ │
│  │ Best for: Prototyping, experimentation                      │ │
│  │ Avg Cost: $0.00 - $0.001 per 1K tokens                      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ ⚖️ Balanced                             [●]                │ │
│  │ ─────────────────────────────────────────────────────────  │ │
│  │ Balance cost and quality (OpenRouter, Together, Fireworks) │ │
│  │ Best for: Production workloads, daily use                   │ │
│  │ Avg Cost: $0.002 - $0.01 per 1K tokens                      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 🎯 Precision                            [ ]                │ │
│  │ ─────────────────────────────────────────────────────────  │ │
│  │ Use best models (OpenAI GPT-4, Anthropic Claude 3.5)       │ │
│  │ Best for: Complex reasoning, critical tasks                 │ │
│  │ Avg Cost: $0.01 - $0.10 per 1K tokens                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Additional Preferences                                           │
│  ────────────────────────────────────────────────────────────   │
│  [✓] Automatic fallback if primary provider fails                │
│  [✓] Use BYOK providers when available                           │
│  [ ] Require local models for privacy-sensitive requests         │
│                                                                   │
│  Monthly Spending Cap: [$100.00_______]                          │
│                                                                   │
│  [Save Settings]                                                  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 6.5 Usage Dashboard

**Page**: `/account/subscription/usage`

**Components**:

1. **UsageChart.jsx** - Time-series chart (react-chartjs-2)
2. **CostBreakdown.jsx** - Cost by provider
3. **ProviderDistribution.jsx** - Pie chart

**Mockup**:

```
┌──────────────────────────────────────────────────────────────────┐
│              LLM Usage Analytics                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Time Period: [Last 7 Days ▼]  [Export CSV]                      │
│                                                                   │
│  Summary                                                          │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐   │
│  │ Requests  │  │ Tokens    │  │ Cost      │  │ Avg Cost  │   │
│  │   150     │  │   45,000  │  │  $2.35    │  │  $0.016   │   │
│  │           │  │           │  │           │  │ per req   │   │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘   │
│                                                                   │
│  Usage Over Time                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                                                             │ │
│  │  [Chart: Line graph showing requests/day]                  │ │
│  │  Mon  Tue  Wed  Thu  Fri  Sat  Sun                         │ │
│  │   20   25   18   22   30   20   15                         │ │
│  │                                                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Cost Breakdown by Provider                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ OpenRouter          ████████████  $1.80 (77%)               │ │
│  │ Platform OpenAI     ███           $0.55 (23%)               │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Provider Performance                                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Provider     Requests  Tokens  Cost    Avg Latency         │ │
│  │ ──────────────────────────────────────────────────────────│ │
│  │ OpenRouter      120    36,000  $1.80    850ms              │ │
│  │ Platform OpenAI  30     9,000  $0.55   1200ms              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 7. Integration Architecture

### 7.1 Integration with Existing Systems

**Keycloak SSO**:
- All API endpoints require Keycloak authentication
- User ID extracted from JWT token
- BYOK keys tied to Keycloak user ID

**Lago Billing**:
- LLM usage events sent to Lago for billing
- Credit balance synced from Lago subscriptions
- Monthly spending caps enforced via Lago

**PostgreSQL (unicorn_db)**:
- All LLM routing tables in shared database
- Reuse existing connection pooling
- Foreign key constraints to maintain data integrity

**Redis Cache**:
- Cache routing rules (60s TTL)
- Cache provider health status (5min TTL)
- Rate limiting with sliding windows

### 7.2 LiteLLM Proxy Configuration

**LiteLLM Config** (`litellm_config.yaml`):

```yaml
model_list:
  # OpenRouter
  - model_name: openrouter/*
    litellm_params:
      model: openrouter/*
      api_base: https://openrouter.ai/api/v1
      api_key: os.environ/OPENROUTER_API_KEY

  # OpenAI (Platform)
  - model_name: openai/*
    litellm_params:
      model: gpt-*
      api_base: https://api.openai.com/v1
      api_key: os.environ/OPENAI_API_KEY

  # Anthropic (Platform)
  - model_name: anthropic/*
    litellm_params:
      model: claude-*
      api_base: https://api.anthropic.com/v1
      api_key: os.environ/ANTHROPIC_API_KEY

router_settings:
  routing_strategy: usage-based-routing
  model_group_alias:
    gpt-4: openai/gpt-4o
    claude: anthropic/claude-3-5-sonnet-20241022
  fallbacks:
    - openrouter/*
    - together/*
    - groq/*
  allowed_fails: 3
  cooldown_time: 300  # 5 minutes
  num_retries: 2
  timeout: 30
```

**Dynamic Provider Injection**:

```python
async def inject_user_byok_key(
    user_id: str,
    provider_type: str,
    request: Dict
) -> Dict:
    """Inject user's BYOK API key into LiteLLM request"""

    # Get user's API key
    byok_manager = get_byok_manager()
    api_key = await byok_manager.get_user_api_key(user_id, provider_type)

    if api_key:
        # Override with user's key
        request['api_key'] = api_key
        request['metadata'] = request.get('metadata', {})
        request['metadata']['using_byok'] = True
        logger.info(f"Using BYOK for {user_id}/{provider_type}")

    return request
```

### 7.3 Event-Driven Architecture

**Events to Emit**:

1. **provider.created** - New provider added
2. **provider.updated** - Provider config changed
3. **provider.deleted** - Provider removed
4. **provider.health_changed** - Provider health status changed
5. **user.byok_added** - User adds API key
6. **user.byok_deleted** - User removes API key
7. **usage.request_completed** - LLM request completed
8. **usage.request_failed** - LLM request failed
9. **routing.fallback_triggered** - Fallback provider used
10. **billing.credit_deducted** - Credits deducted for request

**Event Bus** (Redis Pub/Sub):

```python
import redis.asyncio as aioredis

async def publish_event(event_type: str, data: Dict):
    """Publish event to Redis pub/sub"""
    redis_client = aioredis.from_url("redis://unicorn-redis:6379")

    event = {
        "type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data
    }

    await redis_client.publish("ops-center:events", json.dumps(event))
```

**Event Subscribers**:

```python
# Billing service subscribes to usage events
async def handle_usage_event(event: Dict):
    if event['type'] == 'usage.request_completed':
        # Send to Lago for billing
        await lago_client.create_usage_event(
            customer_id=event['data']['user_id'],
            event_code='llm_request',
            properties={
                'tokens': event['data']['tokens_used'],
                'cost': event['data']['cost']
            }
        )
```

---

## 8. Deployment Architecture

### 8.1 Docker Services

**New Services**:

None - All functionality runs within existing `ops-center-direct` container.

**Updated Services**:

```yaml
# services/ops-center/docker-compose.direct.yml

services:
  ops-center-direct:
    # ... existing config ...
    environment:
      # Existing vars
      KEYCLOAK_URL: http://uchub-keycloak:8080
      POSTGRES_HOST: unicorn-postgresql
      REDIS_HOST: unicorn-redis

      # New vars for LiteLLM routing
      LITELLM_PROXY_URL: http://unicorn-litellm-wilmer:4000
      LITELLM_MASTER_KEY: ${LITELLM_MASTER_KEY}
      BYOK_ENCRYPTION_KEY: ${BYOK_ENCRYPTION_KEY}

      # Feature flags
      FEATURE_BYOK_ENABLED: "true"
      FEATURE_POWER_LEVELS_ENABLED: "true"
      FEATURE_AUTO_FALLBACK_ENABLED: "true"
```

### 8.2 Environment Variables

**Required New Variables** (`.env.auth`):

```bash
# LiteLLM Routing
LITELLM_PROXY_URL=http://unicorn-litellm-wilmer:4000
LITELLM_MASTER_KEY=<generated-secret>

# BYOK Encryption
BYOK_ENCRYPTION_KEY=<generated-fernet-key>

# Platform API Keys (Admin-managed providers)
OPENROUTER_API_KEY=<platform-key>
OPENAI_API_KEY=<platform-key>
ANTHROPIC_API_KEY=<platform-key>
TOGETHER_API_KEY=<platform-key>

# Feature Flags
FEATURE_BYOK_ENABLED=true
FEATURE_POWER_LEVELS_ENABLED=true
FEATURE_AUTO_FALLBACK_ENABLED=true

# Rate Limiting
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_MAX_REQUESTS_PER_WINDOW=100
```

### 8.3 Database Migrations

**Migration Script** (`backend/migrations/003_llm_routing.sql`):

```sql
-- Run this migration to add LLM routing tables

BEGIN;

-- 1. Providers table
CREATE TABLE IF NOT EXISTS llm_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT,
    api_base_url TEXT NOT NULL,
    enabled BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0,
    config JSONB DEFAULT '{}',
    health_status VARCHAR(20) DEFAULT 'unknown',
    last_health_check TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(name, type)
);

CREATE INDEX idx_llm_providers_enabled ON llm_providers(enabled);
CREATE INDEX idx_llm_providers_priority ON llm_providers(priority DESC);
CREATE INDEX idx_llm_providers_health ON llm_providers(health_status);

-- 2. Models table
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
    quality_score DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(provider_id, name)
);

CREATE INDEX idx_llm_models_enabled ON llm_models(enabled);
CREATE INDEX idx_llm_models_provider ON llm_models(provider_id);
CREATE INDEX idx_llm_models_cost ON llm_models(cost_per_1m_input_tokens);
CREATE INDEX idx_llm_models_quality ON llm_models(quality_score DESC);

-- 3. User provider keys table (if not exists)
CREATE TABLE IF NOT EXISTS user_provider_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(user_id, provider)
);

CREATE INDEX idx_user_provider_keys_user ON user_provider_keys(user_id);
CREATE INDEX idx_user_provider_keys_enabled ON user_provider_keys(user_id, enabled);

-- 4. Routing rules table
CREATE TABLE IF NOT EXISTS llm_routing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy VARCHAR(50) NOT NULL DEFAULT 'balanced',
    fallback_providers UUID[] DEFAULT '{}',
    model_aliases JSONB DEFAULT '{}',
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert default routing rule
INSERT INTO llm_routing_rules (strategy, config) VALUES
('balanced', '{"cost_weight": 0.4, "latency_weight": 0.4, "quality_weight": 0.2, "max_retries": 3, "retry_delay_ms": 500, "timeout_ms": 30000}');

-- 5. User LLM settings table
CREATE TABLE IF NOT EXISTS user_llm_settings (
    user_id VARCHAR(100) PRIMARY KEY,
    power_level VARCHAR(20) DEFAULT 'balanced',
    credit_balance DECIMAL(10, 2) DEFAULT 0,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_llm_settings_power ON user_llm_settings(power_level);

-- 6. Usage logs table
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
    status VARCHAR(20),
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_llm_usage_user ON llm_usage_logs(user_id);
CREATE INDEX idx_llm_usage_created ON llm_usage_logs(created_at DESC);
CREATE INDEX idx_llm_usage_provider ON llm_usage_logs(provider_id);
CREATE INDEX idx_llm_usage_status ON llm_usage_logs(status);

COMMIT;
```

**Run Migration**:

```bash
# Connect to PostgreSQL
docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db < backend/migrations/003_llm_routing.sql

# Verify tables created
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt llm_*"
```

### 8.4 Monitoring & Alerting

**Metrics to Track** (Prometheus):

```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['provider', 'model', 'power_level', 'status']
)

llm_request_duration = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration',
    ['provider', 'model']
)

llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total tokens processed',
    ['provider', 'model', 'type']  # type = input/output
)

llm_cost_total = Counter(
    'llm_cost_total',
    'Total cost incurred',
    ['provider', 'model', 'power_level']
)

# Provider health
llm_provider_health = Gauge(
    'llm_provider_health',
    'Provider health status (1=healthy, 0=unhealthy)',
    ['provider']
)

# Fallback metrics
llm_fallbacks_total = Counter(
    'llm_fallbacks_total',
    'Total fallback triggers',
    ['primary_provider', 'fallback_provider', 'reason']
)
```

**Grafana Dashboard**:

```json
{
  "dashboard": {
    "title": "LLM Routing & BYOK",
    "panels": [
      {
        "title": "Requests per Provider",
        "targets": [
          "rate(llm_requests_total[5m])"
        ]
      },
      {
        "title": "Average Latency",
        "targets": [
          "histogram_quantile(0.95, llm_request_duration_seconds)"
        ]
      },
      {
        "title": "Cost per Provider",
        "targets": [
          "increase(llm_cost_total[1h])"
        ]
      },
      {
        "title": "Provider Health",
        "targets": [
          "llm_provider_health"
        ]
      },
      {
        "title": "Fallback Rate",
        "targets": [
          "rate(llm_fallbacks_total[5m])"
        ]
      }
    ]
  }
}
```

**Alerting Rules** (Prometheus):

```yaml
groups:
  - name: llm_routing
    rules:
      - alert: ProviderUnhealthy
        expr: llm_provider_health == 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "LLM provider {{ $labels.provider }} is unhealthy"

      - alert: HighFallbackRate
        expr: rate(llm_fallbacks_total[5m]) > 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High fallback rate for LLM requests"

      - alert: HighCost
        expr: increase(llm_cost_total[1h]) > 10
        labels:
          severity: info
        annotations:
          summary: "LLM costs exceeded $10/hour"
```

---

## Conclusion

This architecture document provides a comprehensive technical design for Epic 3.1: LiteLLM Multi-Provider Routing. The system is designed to be:

1. **Secure**: Fernet encryption, audit logging, rate limiting
2. **Scalable**: PostgreSQL + Redis caching, load balancing
3. **Intelligent**: WilmerAI-style cost/latency/quality optimization
4. **User-Friendly**: Intuitive UI for BYOK and power levels
5. **Resilient**: Automatic fallback mechanisms
6. **Observable**: Comprehensive metrics and alerting

**Next Steps**:

1. **Phase 1**: Backend implementation (database + API endpoints)
2. **Phase 2**: Frontend implementation (UI components)
3. **Phase 3**: LiteLLM integration and routing logic
4. **Phase 4**: Testing, monitoring, and documentation
5. **Phase 5**: Production deployment

**Estimated Implementation Timeline**: 3-4 weeks (4-5 developer-days)

**Dependencies**:
- Existing `litellm_routing_api.py` (extends functionality)
- Existing `byok_manager.py` (uses as-is)
- Existing `secret_manager.py` (uses for encryption)
- React frontend (Material-UI components)
- PostgreSQL, Redis, Keycloak (already configured)

**Success Criteria**:
- ✅ Users can add BYOK API keys securely
- ✅ Users can select power levels (Eco, Balanced, Precision)
- ✅ Automatic routing based on cost/latency/quality scoring
- ✅ Automatic fallback when providers fail
- ✅ Usage tracking and analytics
- ✅ Admin can manage providers and models
- ✅ All security requirements met (encryption, audit logging, rate limiting)

---

**Document End**
