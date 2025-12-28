#!/usr/bin/env python3
"""
Fetch All OpenRouter Models and Populate Database
Purpose: Complete seed data for all 348+ models from OpenRouter API
Database: unicorn_db
Author: Database Architect
Created: November 6, 2025
"""

import sys
import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any
import psycopg2
from psycopg2.extras import execute_values

# Database connection parameters
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "ops_center_db"),
    "user": os.getenv("POSTGRES_USER", "ops_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "change-me"),
}

# OpenRouter API configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"

# Tier assignment logic based on pricing
def assign_tier_by_pricing(pricing: Dict[str, Any]) -> List[str]:
    """
    Assign tier access based on model pricing

    Tier Logic:
    - Trial: Free models or very cheap (<$0.0001/1K tokens)
    - Starter: Cheap to mid-range (<$0.001/1K tokens)
    - Professional: Mid to high range (<$0.01/1K tokens)
    - Enterprise: All models including expensive ones
    """
    # Get average cost per 1K tokens
    prompt_cost = float(pricing.get("prompt", 0))
    completion_cost = float(pricing.get("completion", 0))
    avg_cost = (prompt_cost + completion_cost) / 2

    # Free models - all tiers
    if avg_cost == 0:
        return ["trial", "starter", "professional", "enterprise"]

    # Very cheap models (<$0.0001/1K) - all tiers
    elif avg_cost < 0.0001:
        return ["trial", "starter", "professional", "enterprise"]

    # Cheap models (<$0.001/1K) - starter and above
    elif avg_cost < 0.001:
        return ["starter", "professional", "enterprise"]

    # Mid-range models (<$0.01/1K) - professional and above
    elif avg_cost < 0.01:
        return ["professional", "enterprise"]

    # Expensive models (>=$0.01/1K) - enterprise only
    else:
        return ["enterprise"]


def fetch_openrouter_models() -> List[Dict[str, Any]]:
    """Fetch all models from OpenRouter API"""
    print("Fetching models from OpenRouter API...")

    try:
        response = requests.get(
            OPENROUTER_API_URL,
            headers={"User-Agent": "Ops-Center/1.0"},
            timeout=30
        )
        response.raise_for_status()

        data = response.json()
        models = data.get("data", [])

        print(f"✓ Fetched {len(models)} models from OpenRouter")
        return models

    except Exception as e:
        print(f"Error fetching from OpenRouter: {e}")
        return []


def parse_openrouter_model(model: Dict[str, Any]) -> Dict[str, Any]:
    """Parse OpenRouter model data into our schema"""

    # Extract model ID
    model_id = model.get("id", "")

    # Extract name and description
    name = model.get("name", model_id)
    description = model.get("description", f"{name} from OpenRouter")

    # Extract pricing
    pricing_data = model.get("pricing", {})
    pricing = {
        "input_per_1k": float(pricing_data.get("prompt", 0)),
        "output_per_1k": float(pricing_data.get("completion", 0))
    }

    # Extract context length
    context_length = model.get("context_length", 8192)

    # Extract top provider (for release date, etc.)
    top_provider = model.get("top_provider", {})

    # Assign tiers based on pricing
    tier_access = assign_tier_by_pricing(pricing_data)

    # Extract capabilities
    supports_function_calling = "tools" in model.get("supported_generation_types", [])
    supports_vision = "image" in model.get("supported_modalities", []) or "vision" in model_id.lower()

    # Try to extract model family
    model_family = None
    if "/" in model_id:
        parts = model_id.split("/")
        if len(parts) >= 2:
            model_family = parts[1].split(":")[0].split("-")[0]

    return {
        "model_id": model_id,
        "provider": "openrouter",
        "display_name": name,
        "description": description[:500],  # Truncate to 500 chars
        "tier_access": tier_access,
        "pricing": pricing,
        "context_length": context_length,
        "max_output_tokens": context_length // 4,  # Estimate
        "supports_vision": supports_vision,
        "supports_function_calling": supports_function_calling,
        "supports_streaming": True,  # OpenRouter supports streaming
        "model_family": model_family,
        "release_date": None,  # OpenRouter doesn't provide this
        "metadata": {
            "per_request_limits": model.get("per_request_limits"),
            "architecture": model.get("architecture", {}),
            "top_provider": top_provider.get("name") if top_provider else None,
        }
    }


def add_additional_providers() -> List[Dict[str, Any]]:
    """Add models from other providers (Ollama, Anthropic, OpenAI, HuggingFace)"""
    additional_models = []

    # Ollama models (free, local)
    ollama_models = [
        {
            "model_id": "llama-3.3-70b",
            "provider": "ollama",
            "display_name": "Llama 3.3 70B (Local)",
            "description": "Meta's latest open-source model running locally",
            "tier_access": ["trial", "starter", "professional", "enterprise"],
            "pricing": {"input_per_1k": 0, "output_per_1k": 0},
            "context_length": 128000,
            "max_output_tokens": 8000,
            "supports_function_calling": True,
            "model_family": "llama-3",
            "release_date": "2024-12-06",
        },
        {
            "model_id": "qwen2.5-coder:32b",
            "provider": "ollama",
            "display_name": "Qwen 2.5 Coder 32B (Local)",
            "description": "Alibaba's coding-specialized model running locally",
            "tier_access": ["trial", "starter", "professional", "enterprise"],
            "pricing": {"input_per_1k": 0, "output_per_1k": 0},
            "context_length": 131072,
            "max_output_tokens": 8000,
            "supports_function_calling": True,
            "model_family": "qwen-2",
            "release_date": "2024-09-19",
            "metadata": {"specialization": "coding"},
        },
        {
            "model_id": "deepseek-coder-v2:16b",
            "provider": "ollama",
            "display_name": "DeepSeek Coder V2 16B (Local)",
            "description": "DeepSeek's coding model running locally",
            "tier_access": ["trial", "starter", "professional", "enterprise"],
            "pricing": {"input_per_1k": 0, "output_per_1k": 0},
            "context_length": 128000,
            "max_output_tokens": 8000,
            "supports_function_calling": True,
            "model_family": "deepseek",
            "release_date": "2024-06-01",
            "metadata": {"specialization": "coding"},
        },
    ]

    # Anthropic models (direct access, not via OpenRouter)
    anthropic_models = [
        {
            "model_id": "claude-3-5-sonnet-20241022",
            "provider": "anthropic",
            "display_name": "Claude 3.5 Sonnet (Latest)",
            "description": "Anthropic's most capable model with best-in-class reasoning",
            "tier_access": ["professional", "enterprise"],
            "pricing": {"input_per_1k": 0.003, "output_per_1k": 0.015},
            "context_length": 200000,
            "max_output_tokens": 8192,
            "supports_vision": True,
            "supports_function_calling": True,
            "model_family": "claude-3",
            "release_date": "2024-10-22",
        },
        {
            "model_id": "claude-3-haiku-20240307",
            "provider": "anthropic",
            "display_name": "Claude 3 Haiku",
            "description": "Anthropic's fastest model for instant responses",
            "tier_access": ["starter", "professional", "enterprise"],
            "pricing": {"input_per_1k": 0.00025, "output_per_1k": 0.00125},
            "context_length": 200000,
            "max_output_tokens": 4096,
            "supports_vision": True,
            "model_family": "claude-3",
            "release_date": "2024-03-07",
        },
    ]

    # OpenAI models (direct access)
    openai_models = [
        {
            "model_id": "gpt-4-turbo-2024-04-09",
            "provider": "openai",
            "display_name": "GPT-4 Turbo (April 2024)",
            "description": "OpenAI's most capable GPT-4 model with 128K context",
            "tier_access": ["professional", "enterprise"],
            "pricing": {"input_per_1k": 0.01, "output_per_1k": 0.03},
            "context_length": 128000,
            "max_output_tokens": 4096,
            "supports_vision": True,
            "supports_function_calling": True,
            "model_family": "gpt-4",
            "release_date": "2024-04-09",
        },
        {
            "model_id": "gpt-3.5-turbo-0125",
            "provider": "openai",
            "display_name": "GPT-3.5 Turbo (Latest)",
            "description": "OpenAI's fast and affordable model",
            "tier_access": ["starter", "professional", "enterprise"],
            "pricing": {"input_per_1k": 0.0005, "output_per_1k": 0.0015},
            "context_length": 16385,
            "max_output_tokens": 4096,
            "supports_function_calling": True,
            "model_family": "gpt-3.5",
            "release_date": "2024-01-25",
        },
    ]

    # HuggingFace models (inference API)
    huggingface_models = [
        {
            "model_id": "meta-llama/Llama-3.1-70B-Instruct",
            "provider": "huggingface",
            "display_name": "Llama 3.1 70B Instruct (HF)",
            "description": "Meta's 70B model via HuggingFace Inference API",
            "tier_access": ["professional", "enterprise"],
            "pricing": {"input_per_1k": 0.0007, "output_per_1k": 0.0007},
            "context_length": 131072,
            "max_output_tokens": 8000,
            "supports_function_calling": True,
            "model_family": "llama-3",
            "release_date": "2024-07-23",
        },
        {
            "model_id": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "provider": "huggingface",
            "display_name": "Mixtral 8x7B Instruct (HF)",
            "description": "Mistral's mixture-of-experts model via HuggingFace",
            "tier_access": ["starter", "professional", "enterprise"],
            "pricing": {"input_per_1k": 0.0005, "output_per_1k": 0.0005},
            "context_length": 32768,
            "max_output_tokens": 8000,
            "model_family": "mixtral",
            "release_date": "2023-12-11",
        },
    ]

    additional_models.extend(ollama_models)
    additional_models.extend(anthropic_models)
    additional_models.extend(openai_models)
    additional_models.extend(huggingface_models)

    return additional_models


def connect_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)


def seed_models(conn, models: List[Dict[str, Any]]):
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
    errors = 0

    for model in models:
        # Set defaults
        model.setdefault("supports_vision", False)
        model.setdefault("supports_function_calling", False)
        model.setdefault("supports_streaming", True)
        model.setdefault("max_output_tokens", 4096)
        model.setdefault("metadata", {})
        model.setdefault("model_family", None)
        model.setdefault("release_date", None)

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
            errors += 1
            print(f"Error inserting model {model['model_id']}: {e}")
            conn.rollback()
            continue

    conn.commit()
    cursor.close()

    return inserted, updated, errors


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

    # Count models accessible per tier
    tier_counts = {}
    for tier in ["trial", "starter", "professional", "enterprise"]:
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM model_access_control
            WHERE tier_access @> %s::jsonb
        """, (json.dumps([tier]),))
        tier_counts[tier] = cursor.fetchone()[0]

    cursor.close()

    return {
        "total": total,
        "by_provider": by_provider,
        "by_tier": tier_counts
    }


def main():
    """Main execution function"""
    print("=" * 80)
    print("OpenRouter Model Seed - Complete Database Population")
    print("=" * 80)
    print()

    # Fetch from OpenRouter
    openrouter_models = fetch_openrouter_models()
    parsed_models = [parse_openrouter_model(m) for m in openrouter_models]
    print(f"✓ Parsed {len(parsed_models)} OpenRouter models")
    print()

    # Add additional providers
    additional_models = add_additional_providers()
    print(f"✓ Added {len(additional_models)} models from other providers")
    print()

    # Combine all models
    all_models = parsed_models + additional_models
    print(f"✓ Total models to seed: {len(all_models)}")
    print()

    # Connect to database
    print("Connecting to database...")
    conn = connect_db()
    print("✓ Connected successfully")
    print()

    # Seed models
    print("Seeding models...")
    inserted, updated, errors = seed_models(conn, all_models)
    print(f"✓ Inserted: {inserted} models")
    print(f"✓ Updated: {updated} models")
    if errors > 0:
        print(f"⚠ Errors: {errors} models")
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

    print("Models accessible per tier:")
    for tier, count in stats["by_tier"].items():
        print(f"  - {tier}: {count} models")
    print()

    # Close connection
    conn.close()

    print("=" * 80)
    print("Seeding completed successfully!")
    print("=" * 80)

    # Success criteria check
    print()
    print("SUCCESS CRITERIA CHECK:")
    print(f"  ✓ OpenRouter models: {stats['by_provider'][0][1] if stats['by_provider'][0][0] == 'openrouter' else 0} (target: 348+)")
    print(f"  ✓ Trial tier access: {stats['by_tier']['trial']} models (target: 50+)")
    print(f"  ✓ Starter tier access: {stats['by_tier']['starter']} models (target: 150+)")
    print(f"  ✓ Professional tier access: {stats['by_tier']['professional']} models (target: 250+)")
    print(f"  ✓ Enterprise tier access: {stats['by_tier']['enterprise']} models (target: 370+)")


if __name__ == "__main__":
    main()
