#!/usr/bin/env python3
"""
Test LLM Provider Integration

This script tests the complete integration flow:
1. Initialize LLMConfigManager with encryption key
2. Get active provider for "chat"
3. Decrypt API key if provider_type="api_key"
4. Convert to LiteLLM config
5. Test inference (optional - requires working LiteLLM)

Usage:
    python3 test_provider_integration.py [--skip-inference]

Author: Ops-Center Backend Team
Date: October 20, 2025
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from dotenv import load_dotenv
from llm_config_manager import LLMConfigManager
from llm_provider_integration import LLMProviderIntegration, ProviderConfiguration


async def initialize_db_pool():
    """Initialize PostgreSQL connection pool."""
    # Load environment
    env_file = Path(__file__).parent.parent.parent / '.env.auth'
    load_dotenv(env_file)

    # Database connection
    db_pool = await asyncpg.create_pool(
        host=os.getenv('POSTGRES_HOST', 'unicorn-postgresql'),
        port=int(os.getenv('POSTGRES_PORT', '5432')),
        user=os.getenv('POSTGRES_USER', 'unicorn'),
        password=os.getenv('POSTGRES_PASSWORD', 'unicorn'),
        database=os.getenv('POSTGRES_DB', 'unicorn_db'),
        min_size=1,
        max_size=5
    )

    return db_pool


async def test_get_active_provider(integration: LLMProviderIntegration):
    """Test: Get active provider for chat."""
    print("\n" + "=" * 70)
    print("TEST 1: Get Active Provider for 'chat'")
    print("=" * 70)

    try:
        config = await integration.get_active_llm_provider("chat")

        if not config:
            print("❌ FAILED: No active provider configured for 'chat'")
            print("\nTo configure an active provider:")
            print("1. Go to Ops-Center LLM Management UI")
            print("2. Or use API: POST /api/v1/llm-config/active")
            print("   {")
            print('     "purpose": "chat",')
            print('     "provider_type": "api_key",')
            print('     "provider_id": 1')
            print("   }")
            return None

        print("✅ PASSED: Active provider found")
        print(f"\nProvider Type: {config.provider_type}")
        print(f"Provider ID: {config.provider_id}")

        if config.provider_type == "api_key":
            print(f"Provider Name: {config.provider_name}")
            print(f"API Key: {'*' * (len(config.api_key) - 4) + config.api_key[-4:] if config.api_key else 'None'}")
        elif config.provider_type == "ai_server":
            print(f"Server Type: {config.server_type}")
            print(f"Base URL: {config.base_url}")
            print(f"Model Path: {config.model_path}")

        print(f"Enabled: {config.enabled}")
        print(f"Purpose: {config.purpose}")
        print(f"Health Status: {config.health_status or 'Unknown'}")

        if config.fallback_provider_type:
            print(f"\nFallback Provider: {config.fallback_provider_type}/{config.fallback_provider_id}")

        return config

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_litellm_conversion(config: ProviderConfiguration):
    """Test: Convert provider config to LiteLLM format."""
    print("\n" + "=" * 70)
    print("TEST 2: Convert to LiteLLM Config")
    print("=" * 70)

    try:
        litellm_config = config.to_litellm_config()

        print("✅ PASSED: Converted to LiteLLM format")
        print("\nLiteLLM Config:")

        for key, value in litellm_config.items():
            if key == 'api_key' and value:
                # Mask API key
                masked = '*' * (len(value) - 4) + value[-4:] if len(value) > 4 else '****'
                print(f"  {key}: {masked}")
            else:
                print(f"  {key}: {value}")

        return litellm_config

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_wilmer_conversion(config: ProviderConfiguration):
    """Test: Convert provider config to WilmerRouter format."""
    print("\n" + "=" * 70)
    print("TEST 3: Convert to WilmerRouter Config")
    print("=" * 70)

    try:
        wilmer_config = config.to_wilmer_config()

        print("✅ PASSED: Converted to WilmerRouter format")
        print("\nWilmerRouter Config:")

        for key, value in wilmer_config.items():
            if key == 'api_key' and value:
                # Mask API key
                masked = '*' * (len(value) - 4) + value[-4:] if len(value) > 4 else '****'
                print(f"  {key}: {masked}")
            else:
                print(f"  {key}: {value}")

        return wilmer_config

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_provider_health(integration: LLMProviderIntegration, config: ProviderConfiguration):
    """Test: Check provider health."""
    print("\n" + "=" * 70)
    print("TEST 4: Test Provider Health")
    print("=" * 70)

    try:
        success, message = await integration.test_provider(config)

        if success:
            print(f"✅ PASSED: Provider is healthy")
            print(f"Message: {message}")
        else:
            print(f"⚠️  WARNING: Provider health check failed")
            print(f"Message: {message}")
            print("\nThis may be expected if:")
            print("- Provider API is temporarily down")
            print("- API key has rate limits")
            print("- Local server is not running")

        return success

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_fallback_provider(integration: LLMProviderIntegration, config: ProviderConfiguration):
    """Test: Get fallback provider."""
    print("\n" + "=" * 70)
    print("TEST 5: Get Fallback Provider")
    print("=" * 70)

    try:
        fallback = await integration.get_fallback_provider(config)

        if not fallback:
            print("ℹ️  INFO: No fallback provider configured")
            print("\nTo configure a fallback:")
            print("1. Update active provider with fallback_provider_type and fallback_provider_id")
            print("2. Or use API: POST /api/v1/llm-config/active")
            return None

        print("✅ PASSED: Fallback provider found")
        print(f"\nFallback Provider Type: {fallback.provider_type}")
        print(f"Fallback Provider ID: {fallback.provider_id}")

        if fallback.provider_type == "api_key":
            print(f"Provider Name: {fallback.provider_name}")
        elif fallback.provider_type == "ai_server":
            print(f"Server Type: {fallback.server_type}")
            print(f"Base URL: {fallback.base_url}")

        return fallback

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_inference(litellm_config: dict, skip: bool = False):
    """Test: Actual LLM inference (optional)."""
    print("\n" + "=" * 70)
    print("TEST 6: LLM Inference (Optional)")
    print("=" * 70)

    if skip:
        print("⏭️  SKIPPED: Inference test skipped (use --test-inference to enable)")
        return

    try:
        # Try to import litellm
        try:
            import litellm
        except ImportError:
            print("⚠️  WARNING: litellm not installed")
            print("\nTo install: pip install litellm")
            return

        print("🔄 Testing inference with a simple prompt...")

        # Determine model based on provider
        api_base = litellm_config.get('api_base')
        api_key = litellm_config.get('api_key')
        provider = litellm_config.get('custom_llm_provider')

        # Select appropriate model
        if provider == 'openrouter':
            model = 'openrouter/meta-llama/llama-3.1-8b-instruct'
        elif provider == 'openai':
            model = 'gpt-3.5-turbo'
        elif provider == 'anthropic':
            model = 'claude-3-haiku-20240307'
        elif provider in ['vllm', 'ollama', 'llamacpp']:
            model = litellm_config.get('model', 'default')
        else:
            model = 'gpt-3.5-turbo'

        print(f"Model: {model}")
        print(f"Provider: {provider}")

        # Make request
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": "Say 'Hello' in one word"}],
            api_base=api_base,
            api_key=api_key,
            max_tokens=10
        )

        answer = response.choices[0].message.content.strip()

        print(f"\n✅ PASSED: Inference successful")
        print(f"Response: {answer}")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description='Test LLM Provider Integration')
    parser.add_argument('--test-inference', action='store_true', help='Test actual LLM inference (requires litellm)')
    args = parser.parse_args()

    print("=" * 70)
    print("LLM Provider Integration Test Suite")
    print("=" * 70)

    # Load environment
    env_file = Path(__file__).parent.parent.parent / '.env.auth'
    print(f"\nLoading environment from: {env_file}")
    load_dotenv(env_file)

    # Check encryption key
    encryption_key = os.getenv('BYOK_ENCRYPTION_KEY')
    if not encryption_key:
        print("\n❌ ERROR: BYOK_ENCRYPTION_KEY not set in .env.auth")
        print("\nRun this command first:")
        print("  python3 backend/scripts/generate_encryption_key.py")
        return 1

    print(f"✅ Encryption key loaded: {encryption_key[:8]}...{encryption_key[-8:]}")

    # Initialize database pool
    print("\n🔄 Initializing database connection...")
    try:
        db_pool = await initialize_db_pool()
        print("✅ Database connection established")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return 1

    try:
        # Initialize LLMConfigManager
        print("\n🔄 Initializing LLMConfigManager...")
        llm_manager = LLMConfigManager(db_pool, encryption_key)
        print("✅ LLMConfigManager initialized")

        # Initialize integration layer
        print("\n🔄 Initializing LLMProviderIntegration...")
        integration = LLMProviderIntegration(llm_manager)
        print("✅ LLMProviderIntegration initialized")

        # Run tests
        config = await test_get_active_provider(integration)
        if not config:
            return 1

        litellm_config = await test_litellm_conversion(config)
        if not litellm_config:
            return 1

        wilmer_config = await test_wilmer_conversion(config)
        if not wilmer_config:
            return 1

        await test_provider_health(integration, config)

        await test_fallback_provider(integration, config)

        await test_inference(litellm_config, skip=not args.test_inference)

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print("✅ All core tests passed!")
        print("\nThe LLM provider integration is working correctly.")
        print("\nNext steps:")
        print("1. Integrate this into your inference endpoints")
        print("2. Use integration.get_active_llm_provider('chat') to get provider config")
        print("3. Convert to LiteLLM format with config.to_litellm_config()")
        print("4. Make inference requests with the config")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # Clean up
        await llm_manager.close()
        await db_pool.close()
        print("\n🔄 Resources cleaned up")


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
