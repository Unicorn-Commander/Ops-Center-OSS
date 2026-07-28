#!/usr/bin/env python3
"""
Seed Model Access Control Database
Purpose: Populate model_access_control table with popular LLM models
Database: unicorn_db
Author: Database Architect
Created: November 6, 2025
"""

import sys
import os
import json
from datetime import date
import psycopg2
from psycopg2.extras import execute_values

# Database connection parameters
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "unicorn_db"),
    "user": os.getenv("POSTGRES_USER", "unicorn"),
    "password": os.getenv("POSTGRES_PASSWORD", "unicorn"),
}

# Model seed data
MODELS = [
    # ========================================================================
    # FREE TIER MODELS (All tiers can access)
    # ========================================================================
    {
        "model_id": "gpt-4o-mini",
        "provider": "openrouter",
        "display_name": "GPT-4o Mini",
        "description": "Fast, efficient OpenAI model for simple tasks. Perfect for testing and basic applications.",
        "tier_access": ["trial", "starter", "professional", "enterprise"],
        "pricing": {"input_per_1k": 0.00015, "output_per_1k": 0.0006},
        "context_length": 128000,
        "max_output_tokens": 16000,
        "model_family": "gpt-4",
        "release_date": "2024-07-01",
    },
    {
        "model_id": "phi-3.5-mini",
        "provider": "openrouter",
        "display_name": "Phi-3.5 Mini (Free)",
        "description": "Microsoft's compact model - completely free on OpenRouter",
        "tier_access": ["trial", "starter", "professional", "enterprise"],
        "pricing": {"input_per_1k": 0, "output_per_1k": 0},
        "context_length": 128000,
        "max_output_tokens": 4000,
        "model_family": "phi-3",
        "release_date": "2024-08-20",
    },
    {
        "model_id": "llama-3.1-8b-instruct:free",
        "provider": "openrouter",
        "display_name": "Llama 3.1 8B (Free)",
        "description": "Meta's open-source model - free tier available",
        "tier_access": ["trial", "starter", "professional", "enterprise"],
        "pricing": {"input_per_1k": 0, "output_per_1k": 0},
        "context_length": 131072,
        "max_output_tokens": 8000,
        "supports_function_calling": True,
        "model_family": "llama-3",
        "release_date": "2024-07-23",
    },
    {
        "model_id": "mistral-7b-instruct:free",
        "provider": "openrouter",
        "display_name": "Mistral 7B (Free)",
        "description": "Mistral AI's efficient 7B model - free tier",
        "tier_access": ["trial", "starter", "professional", "enterprise"],
        "pricing": {"input_per_1k": 0, "output_per_1k": 0},
        "context_length": 32768,
        "max_output_tokens": 8000,
        "model_family": "mistral",
        "release_date": "2023-09-27",
    },
    {
        "model_id": "gemini-flash-1.5",
        "provider": "openrouter",
        "display_name": "Google Gemini 1.5 Flash",
        "description": "Google's fast multimodal model with vision support",
        "tier_access": ["trial", "starter", "professional", "enterprise"],
        "pricing": {"input_per_1k": 0.00025, "output_per_1k": 0.00075},
        "context_length": 1000000,
        "max_output_tokens": 8192,
        "supports_vision": True,
        "supports_function_calling": True,
        "model_family": "gemini",
        "release_date": "2024-05-14",
    },

    # ========================================================================
    # STARTER TIER MODELS (Starter, Professional, Enterprise)
    # ========================================================================
    {
        "model_id": "llama-3.1-70b-instruct",
        "provider": "openrouter",
        "display_name": "Llama 3.1 70B Instruct",
        "description": "Meta's powerful 70B parameter model with 128K context",
        "tier_access": ["starter", "professional", "enterprise"],
        "pricing": {"input_per_1k": 0.00035, "output_per_1k": 0.0004},
        "context_length": 131072,
        "max_output_tokens": 8000,
        "supports_function_calling": True,
        "model_family": "llama-3",
        "release_date": "2024-07-23",
    },
    {
        "model_id": "mixtral-8x7b-instruct",
        "provider": "openrouter",
        "display_name": "Mixtral 8x7B Instruct",
        "description": "Mistral's mixture-of-experts model with excellent performance",
        "tier_access": ["starter", "professional", "enterprise"],
        "pricing": {"input_per_1k": 0.00024, "output_per_1k": 0.00024},
        "context_length": 32768,
        "max_output_tokens": 8000,
        "model_family": "mixtral",
        "release_date": "2023-12-11",
    },
    {
        "model_id": "qwen-2.5-72b-instruct",
        "provider": "openrouter",
        "display_name": "Qwen 2.5 72B Instruct",
        "description": "Alibaba's powerful multilingual model",
        "tier_access": ["starter", "professional", "enterprise"],
        "pricing": {"input_per_1k": 0.00035, "output_per_1k": 0.00035},
        "context_length": 131072,
        "max_output_tokens": 8000,
        "supports_function_calling": True,
        "model_family": "qwen-2",
        "release_date": "2024-09-19",
    },

    # ========================================================================
    # PROFESSIONAL TIER MODELS (Professional, Enterprise)
    # ========================================================================
    {
        "model_id": "claude-3.5-sonnet",
        "provider": "openrouter",
        "display_name": "Claude 3.5 Sonnet",
        "description": "Anthropic's most capable model with excellent reasoning and coding abilities",
        "tier_access": ["professional", "enterprise"],
        "pricing": {"input_per_1k": 0.003, "output_per_1k": 0.015},
        "context_length": 200000,
        "max_output_tokens": 8000,
        "supports_vision": True,
        "supports_function_calling": True,
        "model_family": "claude-3",
        "release_date": "2024-06-20",
    },
    {
        "model_id": "gpt-4o",
        "provider": "openrouter",
        "display_name": "GPT-4 Optimized",
        "description": "OpenAI's flagship multimodal model with vision and function calling",
        "tier_access": ["professional", "enterprise"],
        "pricing": {"input_per_1k": 0.0025, "output_per_1k": 0.01},
        "context_length": 128000,
        "max_output_tokens": 16000,
        "supports_vision": True,
        "supports_function_calling": True,
        "model_family": "gpt-4",
        "release_date": "2024-05-13",
    },
    {
        "model_id": "claude-3-opus",
        "provider": "openrouter",
        "display_name": "Claude 3 Opus",
        "description": "Anthropic's most powerful model for complex tasks",
        "tier_access": ["professional", "enterprise"],
        "pricing": {"input_per_1k": 0.015, "output_per_1k": 0.075},
        "context_length": 200000,
        "max_output_tokens": 4096,
        "supports_vision": True,
        "supports_function_calling": True,
        "model_family": "claude-3",
        "release_date": "2024-03-04",
    },
    {
        "model_id": "gemini-pro-1.5",
        "provider": "openrouter",
        "display_name": "Google Gemini 1.5 Pro",
        "description": "Google's advanced multimodal model with massive 2M context",
        "tier_access": ["professional", "enterprise"],
        "pricing": {"input_per_1k": 0.00125, "output_per_1k": 0.005},
        "context_length": 2000000,
        "max_output_tokens": 8192,
        "supports_vision": True,
        "supports_function_calling": True,
        "model_family": "gemini",
        "release_date": "2024-02-15",
    },
    {
        "model_id": "llama-3.1-405b-instruct",
        "provider": "openrouter",
        "display_name": "Llama 3.1 405B Instruct",
        "description": "Meta's largest and most capable open-source model",
        "tier_access": ["professional", "enterprise"],
        "pricing": {"input_per_1k": 0.003, "output_per_1k": 0.003},
        "context_length": 131072,
        "max_output_tokens": 8000,
        "supports_function_calling": True,
        "model_family": "llama-3",
        "release_date": "2024-07-23",
    },

    # ========================================================================
    # ENTERPRISE TIER MODELS (Enterprise only)
    # ========================================================================
    {
        "model_id": "gpt-4-turbo",
        "provider": "openrouter",
        "display_name": "GPT-4 Turbo",
        "description": "Extended context GPT-4 with vision, JSON mode, and function calling",
        "tier_access": ["enterprise"],
        "pricing": {"input_per_1k": 0.01, "output_per_1k": 0.03},
        "context_length": 128000,
        "max_output_tokens": 4096,
        "supports_vision": True,
        "supports_function_calling": True,
        "model_family": "gpt-4",
        "release_date": "2023-11-06",
    },
    {
        "model_id": "claude-3-opus-20240229",
        "provider": "openrouter",
        "display_name": "Claude 3 Opus (Latest)",
        "description": "Latest version of Anthropic's most powerful model",
        "tier_access": ["enterprise"],
        "pricing": {"input_per_1k": 0.015, "output_per_1k": 0.075},
        "context_length": 200000,
        "max_output_tokens": 4096,
        "supports_vision": True,
        "supports_function_calling": True,
        "model_family": "claude-3",
        "release_date": "2024-02-29",
    },
    {
        "model_id": "o1-preview",
        "provider": "openrouter",
        "display_name": "OpenAI o1 Preview",
        "description": "OpenAI's reasoning model with enhanced problem-solving capabilities",
        "tier_access": ["enterprise"],
        "pricing": {"input_per_1k": 0.015, "output_per_1k": 0.06},
        "context_length": 128000,
        "max_output_tokens": 32768,
        "supports_function_calling": True,
        "model_family": "o1",
        "release_date": "2024-09-12",
    },

    # ========================================================================
    # LOCAL MODELS (Always available - Ollama)
    # ========================================================================
    {
        "model_id": "llama-3.3-70b",
        "provider": "ollama",
        "display_name": "Llama 3.3 70B (Local)",
        "description": "Meta's open-source model running locally on your hardware",
        "tier_access": ["trial", "starter", "professional", "enterprise"],
        "pricing": {"input_per_1k": 0, "output_per_1k": 0},
        "context_length": 128000,
        "max_output_tokens": 8000,
        "supports_function_calling": True,
        "model_family": "llama-3",
        "release_date": "2024-12-06",
    },
    {
        "model_id": "qwen2.5:32b",
        "provider": "ollama",
        "display_name": "Qwen 2.5 32B (Local)",
        "description": "Alibaba's multilingual model running locally",
        "tier_access": ["trial", "starter", "professional", "enterprise"],
        "pricing": {"input_per_1k": 0, "output_per_1k": 0},
        "context_length": 131072,
        "max_output_tokens": 8000,
        "supports_function_calling": True,
        "model_family": "qwen-2",
        "release_date": "2024-09-19",
    },
    {
        "model_id": "mistral:7b",
        "provider": "ollama",
        "display_name": "Mistral 7B (Local)",
        "description": "Mistral AI's efficient model running locally",
        "tier_access": ["trial", "starter", "professional", "enterprise"],
        "pricing": {"input_per_1k": 0, "output_per_1k": 0},
        "context_length": 32768,
        "max_output_tokens": 8000,
        "model_family": "mistral",
        "release_date": "2023-09-27",
    },
    {
        "model_id": "phi3:mini",
        "provider": "ollama",
        "display_name": "Phi-3 Mini (Local)",
        "description": "Microsoft's compact model running locally",
        "tier_access": ["trial", "starter", "professional", "enterprise"],
        "pricing": {"input_per_1k": 0, "output_per_1k": 0},
        "context_length": 128000,
        "max_output_tokens": 4000,
        "model_family": "phi-3",
        "release_date": "2024-04-23",
    },

    # ========================================================================
    # SPECIALIZED MODELS
    # ========================================================================
    {
        "model_id": "deepseek-coder-v2",
        "provider": "openrouter",
        "display_name": "DeepSeek Coder V2",
        "description": "Specialized coding model with excellent code generation",
        "tier_access": ["professional", "enterprise"],
        "pricing": {"input_per_1k": 0.00014, "output_per_1k": 0.00028},
        "context_length": 128000,
        "max_output_tokens": 8000,
        "supports_function_calling": True,
        "model_family": "deepseek",
        "release_date": "2024-06-01",
        "metadata": {"specialization": "coding"},
    },
    {
        "model_id": "perplexity-llama-3-sonar-large-online",
        "provider": "openrouter",
        "display_name": "Perplexity Sonar Large (Online)",
        "description": "Perplexity's model with real-time web search capabilities",
        "tier_access": ["professional", "enterprise"],
        "pricing": {"input_per_1k": 0.001, "output_per_1k": 0.001},
        "context_length": 127072,
        "max_output_tokens": 8000,
        "supports_function_calling": True,
        "model_family": "perplexity",
        "release_date": "2024-07-01",
        "metadata": {"specialization": "web-search"},
    },
]


def connect_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)


def seed_models(conn):
    """Insert model data into database"""
    cursor = conn.cursor()

    # Prepare insert statement
    insert_query = """
        INSERT INTO model_access_control (
            model_id, provider, display_name, description,
            tier_access, pricing, tier_markup,
            context_length, max_output_tokens,
            supports_vision, supports_function_calling, supports_streaming,
            model_family, release_date, metadata
        ) VALUES (
            %(model_id)s, %(provider)s, %(display_name)s, %(description)s,
            %(tier_access)s::jsonb, %(pricing)s::jsonb, %(tier_markup)s::jsonb,
            %(context_length)s, %(max_output_tokens)s,
            %(supports_vision)s, %(supports_function_calling)s, %(supports_streaming)s,
            %(model_family)s, %(release_date)s, %(metadata)s::jsonb
        )
        ON CONFLICT (model_id) DO UPDATE SET
            provider = EXCLUDED.provider,
            display_name = EXCLUDED.display_name,
            description = EXCLUDED.description,
            tier_access = EXCLUDED.tier_access,
            pricing = EXCLUDED.pricing,
            context_length = EXCLUDED.context_length,
            max_output_tokens = EXCLUDED.max_output_tokens,
            supports_vision = EXCLUDED.supports_vision,
            supports_function_calling = EXCLUDED.supports_function_calling,
            updated_at = NOW()
    """

    inserted = 0
    updated = 0

    for model in MODELS:
        # Set defaults
        model.setdefault("supports_vision", False)
        model.setdefault("supports_function_calling", False)
        model.setdefault("supports_streaming", True)
        model.setdefault("max_output_tokens", 4096)
        model.setdefault("metadata", {})

        # Convert lists/dicts to JSON strings
        model["tier_access"] = json.dumps(model["tier_access"])
        model["pricing"] = json.dumps(model["pricing"])
        model["tier_markup"] = json.dumps({
            "trial": 2.0,
            "starter": 1.5,
            "professional": 1.2,
            "enterprise": 1.0
        })
        model["metadata"] = json.dumps(model.get("metadata", {}))

        try:
            cursor.execute(insert_query, model)
            if cursor.rowcount == 1:
                inserted += 1
            else:
                updated += 1
        except Exception as e:
            print(f"Error inserting model {model['model_id']}: {e}")
            conn.rollback()
            continue

    conn.commit()
    cursor.close()

    return inserted, updated


def verify_data(conn):
    """Verify that data was inserted correctly"""
    cursor = conn.cursor()

    # Count total models
    cursor.execute("SELECT COUNT(*) FROM model_access_control")
    total = cursor.fetchone()[0]

    # Count by provider
    cursor.execute("""
        SELECT provider, COUNT(*)
        FROM model_access_control
        GROUP BY provider
        ORDER BY provider
    """)
    by_provider = cursor.fetchall()

    # Count by tier access
    cursor.execute("""
        SELECT
            CASE
                WHEN tier_access @> '["trial"]' THEN 'trial'
                WHEN tier_access @> '["starter"]' THEN 'starter'
                WHEN tier_access @> '["professional"]' THEN 'professional'
                WHEN tier_access @> '["enterprise"]' THEN 'enterprise'
            END as min_tier,
            COUNT(*)
        FROM model_access_control
        GROUP BY min_tier
        ORDER BY min_tier
    """)
    by_tier = cursor.fetchall()

    # Get sample models
    cursor.execute("""
        SELECT model_id, provider, display_name, tier_access
        FROM model_access_control
        ORDER BY provider, model_id
        LIMIT 10
    """)
    samples = cursor.fetchall()

    cursor.close()

    return {
        "total": total,
        "by_provider": by_provider,
        "by_tier": by_tier,
        "samples": samples
    }


def main():
    """Main execution function"""
    print("=" * 80)
    print("Model Access Control Database Seeding")
    print("=" * 80)
    print()

    # Connect to database
    print("Connecting to database...")
    conn = connect_db()
    print("✓ Connected successfully")
    print()

    # Seed models
    print("Seeding models...")
    inserted, updated = seed_models(conn)
    print(f"✓ Inserted: {inserted} models")
    print(f"✓ Updated: {updated} models")
    print()

    # Verify data
    print("Verifying data...")
    stats = verify_data(conn)
    print(f"✓ Total models: {stats['total']}")
    print()

    print("Models by provider:")
    for provider, count in stats["by_provider"]:
        print(f"  - {provider}: {count} models")
    print()

    print("Models by minimum tier:")
    for tier, count in stats["by_tier"]:
        print(f"  - {tier}: {count} models")
    print()

    print("Sample models:")
    for model_id, provider, display_name, tier_access in stats["samples"]:
        print(f"  - {model_id} ({provider}): {display_name}")
        print(f"    Tiers: {tier_access}")
    print()

    # Close connection
    conn.close()

    print("=" * 80)
    print("Seeding completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
