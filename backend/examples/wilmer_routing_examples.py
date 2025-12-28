"""
WilmerAI Routing Examples

Practical examples of using the WilmerAI routing engine.

Author: Ops-Center Backend Team
Date: October 20, 2025
"""

import asyncio
from typing import Dict, Any

# Import WilmerRouter components
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from wilmer_router import (
    WilmerRouter,
    RoutingRequest,
    TaskType,
    LatencySLO,
    PowerLevel,
    QualityRequirement,
    get_wilmer_router
)
from model_selector import (
    select_model_for_task,
    get_models_by_capability,
    compare_models,
    get_tier_recommendations
)
from provider_health import get_health_checker


# ============================================================================
# Example 1: Basic Code Generation Request
# ============================================================================

async def example_code_generation():
    """Example: Route a code generation request"""
    print("\n" + "="*80)
    print("Example 1: Code Generation Request")
    print("="*80)

    router = get_wilmer_router()

    request = RoutingRequest(
        task_type=TaskType.CODE,
        estimated_tokens=2000,
        latency_slo=LatencySLO.FAST,
        privacy_required=False,
        user_tier="professional",
        credits_remaining=10.0,
        quality_requirement=QualityRequirement.BEST,
        power_level=PowerLevel.BALANCED,
        user_id="dev@example.com"
    )

    choice = await router.select_provider(request)

    print(f"Selected Provider: {choice.provider}")
    print(f"Model: {choice.model}")
    print(f"Max Tokens: {choice.max_tokens}")
    print(f"Temperature: {choice.temperature}")
    print(f"Estimated Cost: ${choice.estimated_cost:.4f}")
    print(f"Reasoning: {choice.reasoning}")
    print(f"Fallback Chain: {choice.fallback_chain}")


# ============================================================================
# Example 2: Privacy-First Request (Sensitive Data)
# ============================================================================

async def example_privacy_first():
    """Example: Route a privacy-sensitive request to local models"""
    print("\n" + "="*80)
    print("Example 2: Privacy-First Request (Medical Data)")
    print("="*80)

    router = get_wilmer_router()

    request = RoutingRequest(
        task_type=TaskType.ANALYSIS,
        estimated_tokens=5000,
        latency_slo=LatencySLO.NORMAL,
        privacy_required=True,  # Force local processing
        user_tier="enterprise",
        credits_remaining=100.0,
        quality_requirement=QualityRequirement.GOOD,
        power_level=PowerLevel.PRECISION,
        user_id="medical@hospital.com"
    )

    choice = await router.select_provider(request)

    print(f"Selected Provider: {choice.provider}")
    print(f"Model: {choice.model}")
    print(f"Privacy Protected: ✓ (No external API calls)")
    print(f"Estimated Cost: ${choice.estimated_cost:.4f}")
    print(f"Reasoning: {choice.reasoning}")


# ============================================================================
# Example 3: BYOK (Bring Your Own Key)
# ============================================================================

async def example_byok_routing():
    """Example: User provides their own OpenAI API key"""
    print("\n" + "="*80)
    print("Example 3: BYOK - User's OpenAI Key")
    print("="*80)

    router = get_wilmer_router()

    request = RoutingRequest(
        task_type=TaskType.CREATIVE,
        estimated_tokens=1500,
        latency_slo=LatencySLO.NORMAL,
        privacy_required=False,
        user_tier="professional",
        credits_remaining=5.0,
        quality_requirement=QualityRequirement.BEST,
        power_level=PowerLevel.PRECISION,
        user_id="writer@example.com"
    )

    # User has their own OpenAI and Anthropic keys
    user_byok_providers = ["openai", "anthropic"]

    choice = await router.select_provider(request, user_byok_providers)

    print(f"Selected Provider: {choice.provider}")
    print(f"Model: {choice.model}")
    print(f"Using BYOK: {choice.is_byok}")
    print(f"Estimated Cost: ${choice.estimated_cost:.4f} (User's credits)")
    print(f"Reasoning: {choice.reasoning}")


# ============================================================================
# Example 4: Budget-Constrained Free Tier
# ============================================================================

async def example_free_tier():
    """Example: User on free tier with no credits"""
    print("\n" + "="*80)
    print("Example 4: Free Tier - No Credits")
    print("="*80)

    router = get_wilmer_router()

    request = RoutingRequest(
        task_type=TaskType.CHAT,
        estimated_tokens=1000,
        latency_slo=LatencySLO.NORMAL,
        privacy_required=False,
        user_tier="free",
        credits_remaining=0.0,
        quality_requirement=QualityRequirement.BASIC,
        power_level=PowerLevel.ECO,
        user_id="freemium@example.com"
    )

    choice = await router.select_provider(request)

    print(f"Selected Provider: {choice.provider}")
    print(f"Model: {choice.model}")
    print(f"Estimated Cost: ${choice.estimated_cost:.4f}")
    print(f"Reasoning: {choice.reasoning}")


# ============================================================================
# Example 5: Ultra-Low Latency (Instant Response)
# ============================================================================

async def example_instant_response():
    """Example: Need <500ms response time"""
    print("\n" + "="*80)
    print("Example 5: Instant Response (<500ms)")
    print("="*80)

    router = get_wilmer_router()

    request = RoutingRequest(
        task_type=TaskType.CHAT,
        estimated_tokens=500,  # Keep small for Groq
        latency_slo=LatencySLO.INSTANT,
        privacy_required=False,
        user_tier="professional",
        credits_remaining=20.0,
        quality_requirement=QualityRequirement.GOOD,
        power_level=PowerLevel.BALANCED,
        user_id="chatbot@example.com"
    )

    choice = await router.select_provider(request)

    print(f"Selected Provider: {choice.provider}")
    print(f"Model: {choice.model}")
    print(f"Expected Latency: <500ms")
    print(f"Estimated Cost: ${choice.estimated_cost:.4f}")
    print(f"Reasoning: {choice.reasoning}")


# ============================================================================
# Example 6: Long Context RAG
# ============================================================================

async def example_long_context_rag():
    """Example: RAG with large document (50K tokens)"""
    print("\n" + "="*80)
    print("Example 6: Long Context RAG (50K tokens)")
    print("="*80)

    router = get_wilmer_router()

    request = RoutingRequest(
        task_type=TaskType.RAG,
        estimated_tokens=50000,  # Very long context
        latency_slo=LatencySLO.SLOW,
        privacy_required=False,
        user_tier="professional",
        credits_remaining=50.0,
        quality_requirement=QualityRequirement.GOOD,
        power_level=PowerLevel.BALANCED,
        user_id="research@example.com"
    )

    choice = await router.select_provider(request)

    print(f"Selected Provider: {choice.provider}")
    print(f"Model: {choice.model}")
    print(f"Max Context: {choice.max_tokens} tokens")
    print(f"Estimated Cost: ${choice.estimated_cost:.4f}")
    print(f"Reasoning: {choice.reasoning}")


# ============================================================================
# Example 7: Power Level Comparison
# ============================================================================

async def example_power_level_comparison():
    """Example: Compare routing across power levels"""
    print("\n" + "="*80)
    print("Example 7: Power Level Comparison")
    print("="*80)

    router = get_wilmer_router()

    base_request_params = {
        "task_type": TaskType.CREATIVE,
        "estimated_tokens": 2000,
        "latency_slo": LatencySLO.NORMAL,
        "privacy_required": False,
        "user_tier": "professional",
        "credits_remaining": 10.0,
        "quality_requirement": QualityRequirement.GOOD,
        "user_id": "user@example.com"
    }

    for power in [PowerLevel.ECO, PowerLevel.BALANCED, PowerLevel.PRECISION]:
        request = RoutingRequest(**base_request_params, power_level=power)
        choice = await router.select_provider(request)

        print(f"\n{power.value.upper()} Mode:")
        print(f"  Provider: {choice.provider}/{choice.model}")
        print(f"  Cost: ${choice.estimated_cost:.4f}")
        print(f"  Reasoning: {choice.reasoning}")


# ============================================================================
# Example 8: Model Selection by Task
# ============================================================================

def example_model_selection():
    """Example: Use model selector for task-specific selection"""
    print("\n" + "="*80)
    print("Example 8: Model Selection by Task")
    print("="*80)

    # Select model for code generation
    code_model = select_model_for_task(
        task_type="code",
        power_level="balanced",
        max_cost=0.01,
        required_capabilities=["code_generation", "function_calling"],
        min_quality=0.8
    )

    print("Code Generation Model:")
    print(f"  Selected: {code_model['key']}")
    print(f"  Provider: {code_model['provider']}")
    print(f"  Score: {code_model['score']:.2f}")
    print(f"  Cost: ${code_model['config']['cost_per_1k']:.4f}/1K")

    # Select model for creative writing
    creative_model = select_model_for_task(
        task_type="creative",
        power_level="precision",
        max_cost=0.02,
        min_quality=0.9
    )

    print("\nCreative Writing Model:")
    print(f"  Selected: {creative_model['key']}")
    print(f"  Provider: {creative_model['provider']}")
    print(f"  Score: {creative_model['score']:.2f}")
    print(f"  Cost: ${creative_model['config']['cost_per_1k']:.4f}/1K")


# ============================================================================
# Example 9: Get Models by Capability
# ============================================================================

def example_models_by_capability():
    """Example: Find all models with specific capability"""
    print("\n" + "="*80)
    print("Example 9: Models by Capability")
    print("="*80)

    # Find all code generation models
    code_models = get_models_by_capability("code_generation", max_cost=0.015)

    print("Code Generation Models (sorted by quality):")
    for model in code_models:
        print(f"  {model['key']}")
        print(f"    Quality: {model['quality_score']:.2f}")
        print(f"    Cost: ${model['cost_per_1k']:.4f}/1K")
        print(f"    Speed: {model['speed_score']:.2f}")


# ============================================================================
# Example 10: Compare Models
# ============================================================================

def example_compare_models():
    """Example: Compare multiple models side-by-side"""
    print("\n" + "="*80)
    print("Example 10: Model Comparison")
    print("="*80)

    models_to_compare = [
        "openrouter/claude-3.5",
        "openrouter/gpt-4o",
        "fireworks/qwen-72b",
        "local/qwen-32b"
    ]

    comparison = compare_models(models_to_compare)

    print("Model Comparison:")
    print(f"{'Model':<30} {'Quality':<10} {'Speed':<10} {'Cost/1K':<10}")
    print("-" * 70)

    for model in comparison:
        print(
            f"{model['key']:<30} "
            f"{model['quality_score']:<10.2f} "
            f"{model['speed_score']:<10.2f} "
            f"${model['cost_per_1k']:<9.4f}"
        )


# ============================================================================
# Example 11: Tier-Based Recommendations
# ============================================================================

def example_tier_recommendations():
    """Example: Get recommended models for user's tier"""
    print("\n" + "="*80)
    print("Example 11: Tier-Based Recommendations")
    print("="*80)

    tiers = ["free", "starter", "professional", "enterprise"]

    for tier in tiers:
        recommendations = get_tier_recommendations(tier)

        print(f"\n{tier.upper()} Tier Recommendations:")
        print(f"  Code Tasks: {recommendations['code_tasks'][:3]}")
        print(f"  Creative Tasks: {recommendations['creative_tasks'][:3]}")
        print(f"  Chat Tasks: {recommendations['chat_tasks'][:3]}")


# ============================================================================
# Example 12: Provider Health Monitoring
# ============================================================================

async def example_health_monitoring():
    """Example: Monitor provider health"""
    print("\n" + "="*80)
    print("Example 12: Provider Health Monitoring")
    print("="*80)

    checker = get_health_checker()

    # Start monitoring
    print("Starting provider health monitoring...")
    await checker.start_monitoring()

    # Wait for first check
    await asyncio.sleep(2)

    # Get health summary
    summary = await checker.get_health_summary()

    print(f"\nProvider Health Summary:")
    print(f"  Total Providers: {summary['total_providers']}")
    print(f"  Healthy: {summary['healthy_providers']}")
    print(f"  Unhealthy: {summary['unhealthy_providers']}")
    print(f"  Overall Health: {summary['overall_health_percentage']:.1f}%")

    if summary['average_response_time_ms']:
        print(f"  Avg Response Time: {summary['average_response_time_ms']:.0f}ms")

    print("\nProvider Details:")
    for provider in summary['providers']:
        status = "✓" if provider['is_healthy'] else "✗"
        print(f"  {status} {provider['provider']}: ", end="")
        if provider['response_time_ms']:
            print(f"{provider['response_time_ms']:.0f}ms")
        else:
            print("N/A")

    # Get healthy providers only
    healthy = await checker.get_healthy_providers()
    print(f"\nHealthy Providers: {healthy}")

    # Stop monitoring
    await checker.stop_monitoring()


# ============================================================================
# Example 13: Cost Estimation
# ============================================================================

async def example_cost_estimation():
    """Example: Estimate costs before making request"""
    print("\n" + "="*80)
    print("Example 13: Cost Estimation")
    print("="*80)

    router = get_wilmer_router()

    request = RoutingRequest(
        task_type=TaskType.CODE,
        estimated_tokens=5000,
        latency_slo=LatencySLO.NORMAL,
        privacy_required=False,
        user_tier="professional",
        credits_remaining=10.0,
        quality_requirement=QualityRequirement.BEST,
        power_level=PowerLevel.BALANCED,
        user_id="dev@example.com"
    )

    # Estimate costs for different providers
    providers_to_check = [
        "openrouter/claude-3.5",
        "openrouter/gpt-4o",
        "fireworks/qwen-72b",
        "together/mixtral-8x22b",
        "local/qwen-32b"
    ]

    print("Cost Estimates (for 5000 tokens):")
    print(f"{'Provider':<30} {'Estimated Cost':<15}")
    print("-" * 50)

    for provider_key in providers_to_check:
        cost = await router.estimate_cost(request, provider_key)
        print(f"{provider_key:<30} ${cost:<14.4f}")


# ============================================================================
# Example 14: Fallback Chain Usage
# ============================================================================

async def example_fallback_chain():
    """Example: Use fallback chain when primary provider fails"""
    print("\n" + "="*80)
    print("Example 14: Fallback Chain")
    print("="*80)

    router = get_wilmer_router()

    request = RoutingRequest(
        task_type=TaskType.CHAT,
        estimated_tokens=2000,
        latency_slo=LatencySLO.FAST,
        privacy_required=False,
        user_tier="professional",
        credits_remaining=10.0,
        quality_requirement=QualityRequirement.GOOD,
        power_level=PowerLevel.BALANCED,
        user_id="user@example.com"
    )

    choice = await router.select_provider(request)

    print(f"Primary Provider: {choice.provider}/{choice.model}")
    print(f"\nFallback Chain (in order):")
    for i, fallback in enumerate(choice.fallback_chain, 1):
        print(f"  {i}. {fallback}")

    print("\nSimulating provider failure...")
    print("Would try fallbacks in order until one succeeds")


# ============================================================================
# Main Function - Run All Examples
# ============================================================================

async def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("WilmerAI Routing Engine - Usage Examples")
    print("="*80)

    # Async examples
    await example_code_generation()
    await example_privacy_first()
    await example_byok_routing()
    await example_free_tier()
    await example_instant_response()
    await example_long_context_rag()
    await example_power_level_comparison()

    # Sync examples
    example_model_selection()
    example_models_by_capability()
    example_compare_models()
    example_tier_recommendations()

    # Async examples
    await example_health_monitoring()
    await example_cost_estimation()
    await example_fallback_chain()

    print("\n" + "="*80)
    print("Examples Complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Run all examples
    asyncio.run(main())
