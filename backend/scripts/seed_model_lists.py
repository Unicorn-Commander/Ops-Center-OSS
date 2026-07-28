#!/usr/bin/env python3
"""
Seed Model Lists

This script populates the database with initial curated model lists for different apps.
Use this to set up the default model selections for Bolt.diy, Presenton, Open-WebUI, etc.

Usage:
    python3 seed_model_lists.py [--reset]

Options:
    --reset    Delete existing lists before seeding (WARNING: destroys existing data)

Author: Backend Developer
Date: November 19, 2025
"""

import asyncio
import asyncpg
import os
import sys
import argparse
from datetime import datetime


# Database connection settings
DB_CONFIG = {
    'host': os.environ.get('POSTGRES_HOST', 'unicorn-postgresql'),
    'port': 5432,
    'user': os.environ.get('POSTGRES_USER', 'unicorn'),
    'password': os.environ.get('POSTGRES_PASSWORD', 'unicorn'),
    'database': os.environ.get('POSTGRES_DB', 'unicorn_db')
}


# Model context lengths
MODEL_CONTEXT_LENGTHS = {
    'qwen/qwen3-coder:free': 262144,
    'deepseek/deepseek-r1:free': 163840,
    'google/gemini-2.0-flash-exp:free': 1048576,
    'google/gemini-2.5-flash-preview-05-20:free': 1048576,
    'mistralai/mistral-small-3.1-24b-instruct:free': 32768,
    'meta-llama/llama-3.3-70b-instruct:free': 131072,
    'deepseek/deepseek-chat-v3-0324:free': 65536,
}


# Curated model lists
MODEL_LISTS = [
    {
        'name': 'Global Default',
        'slug': 'global',
        'description': 'Best FREE models for all apps - used as fallback when no app-specific list exists',
        'app_identifier': None,  # Global list
        'is_default': True,
        'models': [
            {
                'model_id': 'qwen/qwen3-coder:free',
                'display_name': 'Qwen3 Coder (Free)',
                'description': 'Best FREE coding model - excellent for code generation and debugging',
                'category': 'coding',
                'is_free': True,
            },
            {
                'model_id': 'deepseek/deepseek-r1:free',
                'display_name': 'DeepSeek R1 (Free)',
                'description': 'Excellent for complex reasoning and problem solving',
                'category': 'reasoning',
                'is_free': True,
            },
            {
                'model_id': 'google/gemini-2.0-flash-exp:free',
                'display_name': 'Gemini 2.0 Flash (Free)',
                'description': 'Fast, versatile model for general tasks with large context',
                'category': 'general',
                'is_free': True,
            },
            {
                'model_id': 'google/gemini-2.5-flash-preview-05-20:free',
                'display_name': 'Gemini 2.5 Flash Preview (Free)',
                'description': 'Latest Gemini preview with improved capabilities',
                'category': 'fast',
                'is_free': True,
            },
            {
                'model_id': 'mistralai/mistral-small-3.1-24b-instruct:free',
                'display_name': 'Mistral Small 3.1 (Free)',
                'description': 'Efficient small model for quick responses',
                'category': 'general',
                'is_free': True,
            },
            {
                'model_id': 'meta-llama/llama-3.3-70b-instruct:free',
                'display_name': 'Llama 3.3 70B (Free)',
                'description': 'Large open-source model with great general performance',
                'category': 'general',
                'is_free': True,
            },
        ]
    },
    {
        'name': 'Bolt.diy Coding',
        'slug': 'bolt-diy',
        'description': 'Coding-focused models optimized for AI development environment',
        'app_identifier': 'bolt-diy',
        'is_default': True,
        'models': [
            {
                'model_id': 'qwen/qwen3-coder:free',
                'display_name': 'Qwen3 Coder (Free)',
                'description': 'Best FREE coding model - ideal for code generation, debugging, and refactoring',
                'category': 'coding',
                'is_free': True,
            },
            {
                'model_id': 'deepseek/deepseek-r1:free',
                'display_name': 'DeepSeek R1 (Free)',
                'description': 'Great for complex problems requiring step-by-step reasoning',
                'category': 'reasoning',
                'is_free': True,
            },
            {
                'model_id': 'google/gemini-2.0-flash-exp:free',
                'display_name': 'Gemini 2.0 Flash (Free)',
                'description': 'Fast iterations with massive 1M context window',
                'category': 'fast',
                'is_free': True,
            },
            {
                'model_id': 'meta-llama/llama-3.3-70b-instruct:free',
                'display_name': 'Llama 3.3 70B (Free)',
                'description': 'Strong general performance for various coding tasks',
                'category': 'general',
                'is_free': True,
            },
            {
                'model_id': 'mistralai/mistral-small-3.1-24b-instruct:free',
                'display_name': 'Mistral Small 3.1 (Free)',
                'description': 'Efficient model for quick code completions',
                'category': 'general',
                'is_free': True,
            },
            {
                'model_id': 'deepseek/deepseek-chat-v3-0324:free',
                'display_name': 'DeepSeek Chat V3 (Free)',
                'description': 'Good all-around model for code discussion',
                'category': 'general',
                'is_free': True,
            },
        ]
    },
    {
        'name': 'Presenton Content',
        'slug': 'presenton',
        'description': 'Content generation models optimized for AI presentation creation',
        'app_identifier': 'presenton',
        'is_default': True,
        'models': [
            {
                'model_id': 'google/gemini-2.0-flash-exp:free',
                'display_name': 'Gemini 2.0 Flash (Free)',
                'description': 'Excellent for presentations - fast, creative, and handles long content well',
                'category': 'general',
                'is_free': True,
            },
            {
                'model_id': 'deepseek/deepseek-chat-v3-0324:free',
                'display_name': 'DeepSeek Chat V3 (Free)',
                'description': 'Good for generating well-structured presentation content',
                'category': 'general',
                'is_free': True,
            },
            {
                'model_id': 'mistralai/mistral-small-3.1-24b-instruct:free',
                'display_name': 'Mistral Small 3.1 (Free)',
                'description': 'Creative writing and engaging slide narratives',
                'category': 'creative',
                'is_free': True,
            },
            {
                'model_id': 'meta-llama/llama-3.3-70b-instruct:free',
                'display_name': 'Llama 3.3 70B (Free)',
                'description': 'Strong general performance for diverse presentation topics',
                'category': 'general',
                'is_free': True,
            },
            {
                'model_id': 'google/gemini-2.5-flash-preview-05-20:free',
                'display_name': 'Gemini 2.5 Flash Preview (Free)',
                'description': 'Latest preview with improved content generation',
                'category': 'fast',
                'is_free': True,
            },
        ]
    },
    {
        'name': 'Open-WebUI General',
        'slug': 'open-webui',
        'description': 'General purpose models for the main chat interface',
        'app_identifier': 'open-webui',
        'is_default': True,
        'models': [
            {
                'model_id': 'google/gemini-2.0-flash-exp:free',
                'display_name': 'Gemini 2.0 Flash (Free)',
                'description': 'Best all-around model - fast, capable, and free',
                'category': 'general',
                'is_free': True,
            },
            {
                'model_id': 'meta-llama/llama-3.3-70b-instruct:free',
                'display_name': 'Llama 3.3 70B (Free)',
                'description': 'Large open-source model for comprehensive responses',
                'category': 'general',
                'is_free': True,
            },
            {
                'model_id': 'deepseek/deepseek-r1:free',
                'display_name': 'DeepSeek R1 (Free)',
                'description': 'Advanced reasoning for complex questions',
                'category': 'reasoning',
                'is_free': True,
            },
            {
                'model_id': 'mistralai/mistral-small-3.1-24b-instruct:free',
                'display_name': 'Mistral Small 3.1 (Free)',
                'description': 'Quick and efficient for everyday queries',
                'category': 'general',
                'is_free': True,
            },
            {
                'model_id': 'qwen/qwen3-coder:free',
                'display_name': 'Qwen3 Coder (Free)',
                'description': 'Specialized for coding-related questions',
                'category': 'coding',
                'is_free': True,
            },
        ]
    },
]


async def seed_model_lists(pool: asyncpg.Pool, reset: bool = False):
    """Seed the database with curated model lists"""

    async with pool.acquire() as conn:
        if reset:
            print("Deleting existing model lists...")
            await conn.execute("DELETE FROM app_model_list_items")
            await conn.execute("DELETE FROM app_model_lists")
            print("Existing lists deleted")

        total_lists = 0
        total_items = 0

        for list_data in MODEL_LISTS:
            # Check if list already exists
            existing = await conn.fetchval(
                "SELECT id FROM app_model_lists WHERE slug = $1",
                list_data['slug']
            )

            if existing:
                # Update existing list
                print(f"  Updating list: {list_data['name']} (slug: {list_data['slug']})")

                list_id = existing
                await conn.execute("""
                    UPDATE app_model_lists
                    SET name = $1,
                        description = $2,
                        app_identifier = $3,
                        is_default = $4,
                        updated_at = $5
                    WHERE id = $6
                """,
                    list_data['name'],
                    list_data['description'],
                    list_data['app_identifier'],
                    list_data['is_default'],
                    datetime.utcnow(),
                    list_id
                )

                # Delete existing items to re-seed
                await conn.execute(
                    "DELETE FROM app_model_list_items WHERE list_id = $1",
                    list_id
                )
            else:
                # Create new list
                print(f"  Creating list: {list_data['name']} (slug: {list_data['slug']})")

                list_id = await conn.fetchval("""
                    INSERT INTO app_model_lists (name, slug, description, app_identifier, is_default, created_by)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                """,
                    list_data['name'],
                    list_data['slug'],
                    list_data['description'],
                    list_data['app_identifier'],
                    list_data['is_default'],
                    'system'
                )
                total_lists += 1

            # Insert models
            for sort_order, model_data in enumerate(list_data['models'], start=1):
                model_id = model_data['model_id']
                context_length = MODEL_CONTEXT_LENGTHS.get(model_id)

                await conn.execute("""
                    INSERT INTO app_model_list_items (
                        list_id, model_id, display_name, description, category, sort_order, is_free,
                        context_length, tier_trial, tier_starter, tier_professional, tier_enterprise,
                        tier_vip_founder, tier_byok
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    ON CONFLICT (list_id, model_id) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        description = EXCLUDED.description,
                        category = EXCLUDED.category,
                        sort_order = EXCLUDED.sort_order,
                        is_free = EXCLUDED.is_free,
                        context_length = EXCLUDED.context_length,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    list_id,
                    model_id,
                    model_data['display_name'],
                    model_data['description'],
                    model_data['category'],
                    sort_order,
                    model_data['is_free'],
                    context_length,
                    True,   # tier_trial
                    True,   # tier_starter
                    True,   # tier_professional
                    True,   # tier_enterprise
                    True,   # tier_vip_founder
                    True,   # tier_byok
                )
                total_items += 1

            print(f"    Added {len(list_data['models'])} models")

        # Print summary
        list_count = await conn.fetchval("SELECT COUNT(*) FROM app_model_lists")
        item_count = await conn.fetchval("SELECT COUNT(*) FROM app_model_list_items")

        print("\nSeeding complete!")
        print(f"   Total lists: {list_count}")
        print(f"   Total models: {item_count}")
        print(f"   New lists created: {total_lists}")
        print(f"   Items inserted/updated: {total_items}")


async def main():
    parser = argparse.ArgumentParser(description="Seed curated model lists")
    parser.add_argument("--reset", action="store_true", help="Delete existing lists before seeding")
    args = parser.parse_args()

    if args.reset:
        confirm = input("This will delete all existing model lists. Continue? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return

    print(f"\nConnecting to database at {DB_CONFIG['host']}:{DB_CONFIG['port']}...")

    try:
        pool = await asyncpg.create_pool(**DB_CONFIG)

        print(f"Seeding {len(MODEL_LISTS)} model lists...\n")
        await seed_model_lists(pool, reset=args.reset)

        await pool.close()

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
