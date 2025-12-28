#!/usr/bin/env python3
"""
Seed LLM Providers and Models

This script populates the LiteLLM routing database with common providers and models.
Use this to quickly set up a working multi-provider configuration.

Usage:
    python3 seed_llm_providers.py [--reset]

Options:
    --reset    Drop and recreate all tables (WARNING: destroys existing data)

Author: Backend Developer
Date: October 23, 2025
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from litellm_routing_api import get_db_connection, init_database, cipher_suite
from psycopg2.extras import Json

# Sample providers with realistic pricing
PROVIDERS = [
    {
        "name": "OpenRouter",
        "type": "openrouter",
        "api_base_url": "https://openrouter.ai/api",
        "priority": 1,
        "models": [
            {"name": "openai/gpt-4-turbo", "display_name": "GPT-4 Turbo (OpenRouter)", "cost_in": 10.00, "cost_out": 30.00, "context": 128000},
            {"name": "openai/gpt-3.5-turbo", "display_name": "GPT-3.5 Turbo (OpenRouter)", "cost_in": 0.50, "cost_out": 1.50, "context": 16385},
            {"name": "anthropic/claude-3-opus", "display_name": "Claude 3 Opus (OpenRouter)", "cost_in": 15.00, "cost_out": 75.00, "context": 200000},
            {"name": "anthropic/claude-3-sonnet", "display_name": "Claude 3 Sonnet (OpenRouter)", "cost_in": 3.00, "cost_out": 15.00, "context": 200000},
            {"name": "anthropic/claude-3-haiku", "display_name": "Claude 3 Haiku (OpenRouter)", "cost_in": 0.25, "cost_out": 1.25, "context": 200000},
            {"name": "meta-llama/llama-3-70b-instruct", "display_name": "Llama 3 70B (OpenRouter)", "cost_in": 0.59, "cost_out": 0.79, "context": 8192},
            {"name": "mistralai/mixtral-8x7b-instruct", "display_name": "Mixtral 8x7B (OpenRouter)", "cost_in": 0.24, "cost_out": 0.24, "context": 32768},
            {"name": "google/gemini-pro", "display_name": "Gemini Pro (OpenRouter)", "cost_in": 0.50, "cost_out": 1.50, "context": 30720},
        ]
    },
    {
        "name": "OpenAI Direct",
        "type": "openai",
        "api_base_url": "https://api.openai.com",
        "priority": 2,
        "models": [
            {"name": "gpt-4-turbo", "display_name": "GPT-4 Turbo", "cost_in": 10.00, "cost_out": 30.00, "context": 128000},
            {"name": "gpt-4", "display_name": "GPT-4", "cost_in": 30.00, "cost_out": 60.00, "context": 8192},
            {"name": "gpt-3.5-turbo", "display_name": "GPT-3.5 Turbo", "cost_in": 0.50, "cost_out": 1.50, "context": 16385},
            {"name": "gpt-3.5-turbo-16k", "display_name": "GPT-3.5 Turbo 16K", "cost_in": 3.00, "cost_out": 4.00, "context": 16385},
        ]
    },
    {
        "name": "Anthropic",
        "type": "anthropic",
        "api_base_url": "https://api.anthropic.com",
        "priority": 3,
        "models": [
            {"name": "claude-3-opus-20240229", "display_name": "Claude 3 Opus", "cost_in": 15.00, "cost_out": 75.00, "context": 200000},
            {"name": "claude-3-sonnet-20240229", "display_name": "Claude 3 Sonnet", "cost_in": 3.00, "cost_out": 15.00, "context": 200000},
            {"name": "claude-3-haiku-20240307", "display_name": "Claude 3 Haiku", "cost_in": 0.25, "cost_out": 1.25, "context": 200000},
        ]
    },
    {
        "name": "Together AI",
        "type": "together",
        "api_base_url": "https://api.together.xyz",
        "priority": 4,
        "models": [
            {"name": "meta-llama/Llama-3-70b-chat-hf", "display_name": "Llama 3 70B", "cost_in": 0.70, "cost_out": 0.70, "context": 8192},
            {"name": "mistralai/Mixtral-8x7B-Instruct-v0.1", "display_name": "Mixtral 8x7B", "cost_in": 0.60, "cost_out": 0.60, "context": 32768},
            {"name": "codellama/CodeLlama-70b-Instruct-hf", "display_name": "CodeLlama 70B", "cost_in": 0.70, "cost_out": 0.70, "context": 16384},
        ]
    },
    {
        "name": "Google AI",
        "type": "google",
        "api_base_url": "https://generativelanguage.googleapis.com",
        "priority": 5,
        "models": [
            {"name": "gemini-pro", "display_name": "Gemini Pro", "cost_in": 0.50, "cost_out": 1.50, "context": 30720},
            {"name": "gemini-pro-vision", "display_name": "Gemini Pro Vision", "cost_in": 0.50, "cost_out": 1.50, "context": 30720},
        ]
    }
]

# Default API keys (placeholders - users must provide real keys)
DEFAULT_API_KEYS = {
    "openrouter": "sk-or-v1-REPLACE-WITH-YOUR-KEY",
    "openai": "sk-REPLACE-WITH-YOUR-KEY",
    "anthropic": "sk-ant-REPLACE-WITH-YOUR-KEY",
    "together": "REPLACE-WITH-YOUR-KEY",
    "google": "REPLACE-WITH-YOUR-KEY"
}


def seed_providers(reset=False):
    """Seed providers and models into database"""

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if reset:
            print("⚠️  Resetting database (dropping all tables)...")
            cursor.execute("DROP TABLE IF EXISTS llm_usage_logs CASCADE")
            cursor.execute("DROP TABLE IF EXISTS user_llm_settings CASCADE")
            cursor.execute("DROP TABLE IF EXISTS llm_routing_rules CASCADE")
            cursor.execute("DROP TABLE IF EXISTS llm_models CASCADE")
            cursor.execute("DROP TABLE IF EXISTS llm_providers CASCADE")
            conn.commit()
            print("✅ Tables dropped")

            print("📊 Initializing database schema...")
            init_database()
            print("✅ Schema created")

        print(f"\n🚀 Seeding {len(PROVIDERS)} providers...")

        for provider_data in PROVIDERS:
            provider_name = provider_data["name"]
            provider_type = provider_data["type"]

            # Get or create API key
            api_key = os.getenv(f"{provider_type.upper()}_API_KEY", DEFAULT_API_KEYS.get(provider_type))

            # Encrypt API key
            encrypted_key = cipher_suite.encrypt(api_key.encode()).decode()

            # Check if provider exists
            cursor.execute(
                "SELECT id FROM llm_providers WHERE name = %s AND type = %s",
                (provider_name, provider_type)
            )
            existing = cursor.fetchone()

            if existing:
                provider_id = existing[0]
                print(f"  ↻ Provider '{provider_name}' already exists (updating)")

                cursor.execute("""
                    UPDATE llm_providers
                    SET api_base_url = %s,
                        priority = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (provider_data["api_base_url"], provider_data["priority"], provider_id))
            else:
                print(f"  + Creating provider '{provider_name}'")

                cursor.execute("""
                    INSERT INTO llm_providers (name, type, api_key_encrypted, api_base_url, enabled, priority)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    provider_name,
                    provider_type,
                    encrypted_key,
                    provider_data["api_base_url"],
                    True,
                    provider_data["priority"]
                ))
                provider_id = cursor.fetchone()[0]

            # Seed models
            print(f"    Adding {len(provider_data['models'])} models...")
            for model_data in provider_data["models"]:
                cursor.execute("""
                    INSERT INTO llm_models (
                        provider_id, name, display_name,
                        cost_per_1m_input_tokens, cost_per_1m_output_tokens,
                        context_length, enabled
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (provider_id, name) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        cost_per_1m_input_tokens = EXCLUDED.cost_per_1m_input_tokens,
                        cost_per_1m_output_tokens = EXCLUDED.cost_per_1m_output_tokens,
                        context_length = EXCLUDED.context_length,
                        updated_at = NOW()
                """, (
                    provider_id,
                    model_data["name"],
                    model_data["display_name"],
                    model_data["cost_in"],
                    model_data["cost_out"],
                    model_data["context"],
                    True
                ))

        conn.commit()

        # Print summary
        cursor.execute("SELECT COUNT(*) FROM llm_providers")
        provider_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM llm_models")
        model_count = cursor.fetchone()[0]

        print(f"\n✅ Seeding complete!")
        print(f"   Providers: {provider_count}")
        print(f"   Models: {model_count}")

        print(f"\n⚠️  IMPORTANT: Update API keys in environment or database")
        print(f"   Current keys are placeholders and won't work!")
        print(f"\n   Set environment variables:")
        for ptype in ["openrouter", "openai", "anthropic", "together", "google"]:
            print(f"     {ptype.upper()}_API_KEY=sk-your-actual-key")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error seeding database: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Seed LLM providers and models")
    parser.add_argument("--reset", action="store_true", help="Reset database (drop all tables)")
    args = parser.parse_args()

    if args.reset:
        confirm = input("⚠️  This will delete all existing provider/model data. Continue? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return

    seed_providers(reset=args.reset)


if __name__ == "__main__":
    main()
