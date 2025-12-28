#!/usr/bin/env python3
"""
Import all models from OpenRouter API into llm_models table

This script:
1. Fetches all models from OpenRouter API
2. Extracts model details (name, pricing, context, capabilities)
3. Imports them into the llm_models table
4. Links them to the OpenRouter provider

Usage:
    python3 import_openrouter_models.py

Requirements:
    - OpenRouter provider must exist in llm_providers table
    - Database connection (POSTGRES_* env vars)
"""

import os
import sys
import asyncio
import httpx
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# OpenRouter API endpoint
OPENROUTER_API = "https://openrouter.ai/api/v1/models"

# Get database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'unicorn-postgresql'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        user=os.getenv('POSTGRES_USER', 'unicorn'),
        password=os.getenv('POSTGRES_PASSWORD', 'unicorn'),
        database=os.getenv('POSTGRES_DB', 'unicorn_db')
    )


async def fetch_openrouter_models():
    """Fetch all models from OpenRouter API"""
    print("📡 Fetching models from OpenRouter API...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(OPENROUTER_API)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch models: {response.status_code} {response.text}")

        data = response.json()
        models = data.get('data', [])

        print(f"✅ Fetched {len(models)} models from OpenRouter")
        return models


def get_openrouter_provider(conn):
    """Get OpenRouter provider from database"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT id, name, type, api_key_encrypted
        FROM llm_providers
        WHERE type = 'openrouter' AND enabled = true
        LIMIT 1
    """)

    provider = cursor.fetchone()
    cursor.close()

    if not provider:
        raise Exception("OpenRouter provider not found in database. Please add it first.")

    return provider


def parse_model(model_data):
    """Parse OpenRouter model data into our schema"""
    model_id = model_data.get('id', '')

    # Extract pricing (per 1M tokens)
    pricing = model_data.get('pricing', {})
    input_cost = float(pricing.get('prompt', '0')) * 1_000_000  # Convert to per 1M
    output_cost = float(pricing.get('completion', '0')) * 1_000_000  # Convert to per 1M

    # Extract context length
    context_length = model_data.get('context_length', 0)

    # Extract architecture info
    architecture = model_data.get('architecture', {})
    modality = architecture.get('modality', 'text')  # text, multimodal, image

    # Extract capabilities
    top_provider = model_data.get('top_provider', {})
    is_moderated = top_provider.get('is_moderated', False)

    # Generate display name
    name = model_data.get('name', model_id)
    display_name = f"{name} (OpenRouter)"

    # Determine if model is enabled (enable popular models by default)
    enabled = True  # Enable all models by default

    return {
        'model_id': model_id,
        'name': model_id,
        'display_name': display_name,
        'input_cost': input_cost,
        'output_cost': output_cost,
        'context_length': context_length,
        'modality': modality,
        'is_moderated': is_moderated,
        'enabled': enabled,
        'metadata': {
            'description': model_data.get('description', ''),
            'architecture': architecture,
            'top_provider': top_provider,
            'per_request_limits': model_data.get('per_request_limits')
        }
    }


def import_models(conn, provider_id, models_data):
    """Import models into database - commits per model to avoid rollback"""
    imported = 0
    updated = 0
    skipped = 0

    for model_data in models_data:
        cursor = conn.cursor()
        try:
            parsed = parse_model(model_data)

            # Sanity check for cost values (prevent overflow)
            if parsed['input_cost'] > 999999 or parsed['output_cost'] > 999999:
                print(f"⚠️  Skipping {model_data.get('id', 'unknown')}: cost too high (${parsed['input_cost']:.2f}/${parsed['output_cost']:.2f})")
                skipped += 1
                cursor.close()
                continue

            # Check if model already exists
            cursor.execute("""
                SELECT id FROM llm_models
                WHERE provider_id = %s AND name = %s
            """, (provider_id, parsed['name']))

            existing = cursor.fetchone()

            if existing:
                # Update existing model
                cursor.execute("""
                    UPDATE llm_models
                    SET
                        display_name = %s,
                        cost_per_1m_input_tokens = %s,
                        cost_per_1m_output_tokens = %s,
                        context_length = %s,
                        enabled = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (
                    parsed['display_name'],
                    parsed['input_cost'],
                    parsed['output_cost'],
                    parsed['context_length'],
                    parsed['enabled'],
                    existing[0]
                ))
                updated += 1
            else:
                # Insert new model
                cursor.execute("""
                    INSERT INTO llm_models (
                        provider_id, name, display_name,
                        cost_per_1m_input_tokens, cost_per_1m_output_tokens,
                        context_length, enabled,
                        created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """, (
                    provider_id,
                    parsed['name'],
                    parsed['display_name'],
                    parsed['input_cost'],
                    parsed['output_cost'],
                    parsed['context_length'],
                    parsed['enabled']
                ))
                imported += 1

            # Commit per model to avoid transaction rollback
            conn.commit()

        except Exception as e:
            conn.rollback()  # Rollback this model only
            print(f"⚠️  Error importing {model_data.get('id', 'unknown')}: {e}")
            skipped += 1

        finally:
            cursor.close()

    return imported, updated, skipped


async def main():
    """Main execution"""
    print("🚀 OpenRouter Model Importer")
    print("=" * 60)

    # Connect to database
    print("\n📊 Connecting to database...")
    conn = get_db_connection()
    print("✅ Connected to database")

    # Get OpenRouter provider
    provider = get_openrouter_provider(conn)
    print(f"✅ Found OpenRouter provider: {provider['name']} (ID: {provider['id']})")

    # Fetch models from OpenRouter
    models_data = await fetch_openrouter_models()

    # Import models
    print(f"\n📥 Importing {len(models_data)} models...")
    imported, updated, skipped = import_models(conn, provider['id'], models_data)

    # Summary
    print("\n" + "=" * 60)
    print("✅ Import Complete!")
    print(f"   • Imported: {imported} new models")
    print(f"   • Updated: {updated} existing models")
    print(f"   • Skipped: {skipped} models (errors)")
    print(f"   • Total: {imported + updated} models available")

    # Show sample models
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT name, display_name, cost_per_1m_input_tokens, cost_per_1m_output_tokens, context_length
        FROM llm_models
        WHERE provider_id = %s
        ORDER BY cost_per_1m_input_tokens ASC
        LIMIT 10
    """, (provider['id'],))

    sample_models = cursor.fetchall()

    print("\n📋 Sample Models (10 cheapest):")
    print("-" * 60)
    for model in sample_models:
        print(f"   {model['name']}")
        print(f"      Cost: ${model['cost_per_1m_input_tokens']:.2f} / ${model['cost_per_1m_output_tokens']:.2f} per 1M tokens")
        print(f"      Context: {model['context_length']:,} tokens")

    cursor.close()
    conn.close()

    print("\n🎉 Done! All OpenRouter models are now available.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
