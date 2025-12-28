"""
WilmerAI Intelligent LLM Routing Engine

This module implements intelligent provider selection based on:
- Privacy requirements (local > free tier > paid API)
- Latency SLO (Groq for instant, Together for fast, OpenAI for balanced)
- Budget constraints (free tier > cheap > expensive)
- Model capabilities (code vs chat vs reasoning)
- User power level (Eco vs Balanced vs Precision)

Author: Ops-Center Backend Team
Date: October 20, 2025
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks for model selection"""
    CODE = "code"
    CHAT = "chat"
    RAG = "rag"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    REASONING = "reasoning"


class LatencySLO(Enum):
    """Latency service level objectives"""
    INSTANT = "instant"  # <500ms (Groq)
    FAST = "fast"  # <2s (Together, Fireworks)
    NORMAL = "normal"  # <5s (Most providers)
    SLOW = "slow"  # >5s (Acceptable for long tasks)


class PowerLevel(Enum):
    """User power level preferences"""
    ECO = "eco"  # Minimize cost, use free tier
    BALANCED = "balanced"  # Balance cost/quality
    PRECISION = "precision"  # Maximize quality


class QualityRequirement(Enum):
    """Quality requirements for tasks"""
    BASIC = "basic"  # 60-70% quality
    GOOD = "good"  # 80-85% quality
    BEST = "best"  # 95%+ quality


@dataclass
class RoutingRequest:
    """Request for routing decision"""
    task_type: TaskType
    estimated_tokens: int
    latency_slo: LatencySLO
    privacy_required: bool
    user_tier: str  # "free", "starter", "professional", "enterprise"
    credits_remaining: float
    quality_requirement: QualityRequirement
    power_level: PowerLevel
    max_context_length: Optional[int] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProviderChoice:
    """Selected provider and configuration"""
    provider: str  # e.g., "groq", "openrouter", "together"
    model: str  # e.g., "llama3-70b-8192"
    max_tokens: int
    temperature: float
    estimated_cost: float
    reasoning: str  # Why this provider was chosen
    fallback_chain: List[str]  # Fallback providers in order
    is_byok: bool = False  # Whether using user's BYOK key


# Provider configuration and pricing
PROVIDER_CONFIGS = {
    # Local (Free Tier - Always Available)
    "local/qwen-32b": {
        "provider": "local",
        "model": "vllm/Qwen2.5-32B-Instruct-AWQ",
        "api_base": "http://unicorn-vllm:8000",
        "cost_per_1k": 0.0,
        "max_tokens": 16384,
        "avg_latency_ms": 2000,
        "strengths": ["code", "reasoning"],
        "requires_tier": "free"
    },
    "local/llama3-8b": {
        "provider": "local",
        "model": "ollama/llama3",
        "api_base": "http://unicorn-ollama:11434",
        "cost_per_1k": 0.0,
        "max_tokens": 8192,
        "avg_latency_ms": 1000,
        "strengths": ["chat", "analysis"],
        "requires_tier": "free"
    },

    # Free Tier Providers
    "groq/llama3-70b": {
        "provider": "groq",
        "model": "groq/llama3-70b-8192",
        "cost_per_1k": 0.0,
        "max_tokens": 8192,
        "avg_latency_ms": 300,
        "strengths": ["chat", "instant"],
        "requires_tier": "free"
    },
    "huggingface/mixtral-8x7b": {
        "provider": "huggingface",
        "model": "huggingface/mistralai/Mixtral-8x7B-Instruct-v0.1",
        "cost_per_1k": 0.0,
        "max_tokens": 32768,
        "avg_latency_ms": 5000,
        "strengths": ["rag", "long-context"],
        "requires_tier": "free"
    },

    # Paid Tier (Low Cost)
    "together/mixtral-8x22b": {
        "provider": "together",
        "model": "together_ai/mistralai/Mixtral-8x22B-Instruct-v0.1",
        "cost_per_1k": 0.002,
        "max_tokens": 65536,
        "avg_latency_ms": 1500,
        "strengths": ["rag", "long-context", "balanced"],
        "requires_tier": "starter"
    },
    "fireworks/qwen-72b": {
        "provider": "fireworks",
        "model": "fireworks_ai/accounts/fireworks/models/qwen-72b",
        "cost_per_1k": 0.002,
        "max_tokens": 32768,
        "avg_latency_ms": 1200,
        "strengths": ["code", "function-calling"],
        "requires_tier": "starter"
    },
    "deepinfra/llama3-70b": {
        "provider": "deepinfra",
        "model": "deepinfra/meta-llama/Meta-Llama-3-70B-Instruct",
        "cost_per_1k": 0.003,
        "max_tokens": 8192,
        "avg_latency_ms": 1800,
        "strengths": ["chat", "analysis"],
        "requires_tier": "starter"
    },

    # OpenRouter (Multi-Model Gateway)
    "openrouter/claude-3.5": {
        "provider": "openrouter",
        "model": "openrouter/anthropic/claude-3.5-sonnet",
        "cost_per_1k": 0.008,
        "max_tokens": 8192,
        "avg_latency_ms": 2000,
        "strengths": ["creative", "reasoning", "code", "best"],
        "requires_tier": "professional"
    },
    "openrouter/gpt-4o": {
        "provider": "openrouter",
        "model": "openrouter/openai/gpt-4o",
        "cost_per_1k": 0.010,
        "max_tokens": 4096,
        "avg_latency_ms": 1800,
        "strengths": ["creative", "analysis", "best"],
        "requires_tier": "professional"
    },

    # Premium (Direct Access)
    "anthropic/claude-3.5": {
        "provider": "anthropic",
        "model": "anthropic/claude-3-5-sonnet-20241022",
        "cost_per_1k": 0.015,
        "max_tokens": 8192,
        "avg_latency_ms": 1500,
        "strengths": ["creative", "reasoning", "code", "best"],
        "requires_tier": "enterprise"
    },
    "openai/gpt-4o": {
        "provider": "openai",
        "model": "openai/gpt-4o",
        "cost_per_1k": 0.015,
        "max_tokens": 4096,
        "avg_latency_ms": 1200,
        "strengths": ["creative", "analysis", "best"],
        "requires_tier": "enterprise"
    }
}


# Power level configuration
POWER_LEVEL_CONFIGS = {
    PowerLevel.ECO: {
        "max_cost_per_request": 0.001,
        "preferred_providers": ["local", "groq", "huggingface"],
        "quality_threshold": 0.6,
        "latency_tolerance": LatencySLO.SLOW
    },
    PowerLevel.BALANCED: {
        "max_cost_per_request": 0.01,
        "preferred_providers": ["together", "fireworks", "openrouter", "deepinfra"],
        "quality_threshold": 0.8,
        "latency_tolerance": LatencySLO.FAST
    },
    PowerLevel.PRECISION: {
        "max_cost_per_request": 0.1,
        "preferred_providers": ["anthropic", "openai", "openrouter"],
        "quality_threshold": 0.95,
        "latency_tolerance": LatencySLO.INSTANT
    }
}


class WilmerRouter:
    """
    Intelligent LLM provider router.

    Makes routing decisions based on multiple factors:
    - Privacy requirements
    - Latency SLO
    - Budget constraints
    - Task type
    - Quality requirements
    - User tier
    """

    def __init__(self, byok_service=None, cache_service=None):
        """
        Initialize WilmerRouter.

        Args:
            byok_service: Optional BYOK service for checking user keys
            cache_service: Optional cache service for routing decisions
        """
        self.byok_service = byok_service
        self.cache_service = cache_service
        self.provider_health = {}  # Track provider health
        self.last_health_check = None

    async def select_provider(
        self,
        request: RoutingRequest,
        user_byok_providers: Optional[List[str]] = None
    ) -> ProviderChoice:
        """
        Select best provider based on routing request.

        Args:
            request: RoutingRequest with all selection criteria
            user_byok_providers: List of providers user has BYOK keys for

        Returns:
            ProviderChoice with selected provider and configuration
        """
        logger.info(
            f"Routing decision requested: task={request.task_type.value}, "
            f"latency={request.latency_slo.value}, privacy={request.privacy_required}, "
            f"tier={request.user_tier}, power={request.power_level.value}"
        )

        # Check cache for identical requests (5-minute TTL)
        cache_key = self._get_cache_key(request)
        if self.cache_service:
            cached = await self.cache_service.get(cache_key)
            if cached:
                logger.info(f"Returning cached routing decision: {cached['provider']}")
                return ProviderChoice(**cached)

        # 1. Privacy-first: use local if required
        if request.privacy_required:
            choice = self._select_local_model(request)
            logger.info(f"Privacy mode: Selected {choice.provider}/{choice.model}")
            await self._cache_decision(cache_key, choice)
            return choice

        # 2. BYOK override: if user has key for preferred provider, use it
        if user_byok_providers:
            choice = self._select_byok_provider(request, user_byok_providers)
            if choice:
                logger.info(f"BYOK mode: Selected {choice.provider}/{choice.model}")
                await self._cache_decision(cache_key, choice)
                return choice

        # 3. Ultra-low latency: Groq for instant responses
        if request.latency_slo == LatencySLO.INSTANT:
            if request.estimated_tokens < 8000:
                choice = self._create_choice(
                    "groq/llama3-70b",
                    request,
                    "Ultra-low latency requirement (Groq optimized for <500ms)"
                )
                logger.info(f"Instant latency: Selected {choice.provider}/{choice.model}")
                await self._cache_decision(cache_key, choice)
                return choice

        # 4. Budget-constrained: free tier
        if request.credits_remaining < 0.01 or request.user_tier == "free":
            choice = self._select_free_tier(request)
            logger.info(f"Free tier: Selected {choice.provider}/{choice.model}")
            await self._cache_decision(cache_key, choice)
            return choice

        # 5. Power level routing
        power_config = POWER_LEVEL_CONFIGS[request.power_level]

        # Calculate cost constraint
        max_cost = min(
            power_config["max_cost_per_request"],
            request.credits_remaining * 0.1  # Don't spend >10% of remaining credits
        )

        # 6. Task-specific routing
        choice = await self._select_by_task_type(request, max_cost, power_config)

        logger.info(
            f"Task routing: Selected {choice.provider}/{choice.model} "
            f"(cost: ${choice.estimated_cost:.4f}, quality: {request.quality_requirement.value})"
        )

        await self._cache_decision(cache_key, choice)
        return choice

    def _select_local_model(self, request: RoutingRequest) -> ProviderChoice:
        """Select best local model for privacy-first routing."""
        if request.task_type in [TaskType.CODE, TaskType.REASONING]:
            model_key = "local/qwen-32b"
        else:
            model_key = "local/llama3-8b"

        return self._create_choice(
            model_key,
            request,
            "Privacy-first: local model (no external API calls)"
        )

    def _select_byok_provider(
        self,
        request: RoutingRequest,
        user_byok_providers: List[str]
    ) -> Optional[ProviderChoice]:
        """
        Select provider from user's BYOK keys.

        Prioritize based on quality requirement.
        """
        # Map BYOK providers to quality scores
        provider_quality = {
            "anthropic": 0.95,
            "openai": 0.93,
            "openrouter": 0.90,
            "together": 0.85,
            "fireworks": 0.83,
            "deepinfra": 0.80,
            "groq": 0.78,
            "huggingface": 0.70
        }

        # Find best BYOK provider for quality requirement
        target_quality = {
            QualityRequirement.BASIC: 0.6,
            QualityRequirement.GOOD: 0.8,
            QualityRequirement.BEST: 0.95
        }[request.quality_requirement]

        best_provider = None
        best_quality = 0

        for provider in user_byok_providers:
            provider_base = provider.split("/")[0]
            quality = provider_quality.get(provider_base, 0.5)

            if quality >= target_quality and quality > best_quality:
                # Find model for this provider
                for model_key, config in PROVIDER_CONFIGS.items():
                    if model_key.startswith(provider_base + "/"):
                        # Check if model is good for task
                        if request.task_type.value in config["strengths"]:
                            best_provider = model_key
                            best_quality = quality

        if best_provider:
            choice = self._create_choice(
                best_provider,
                request,
                f"BYOK: Using user's {best_provider.split('/')[0]} API key (free credits)"
            )
            choice.is_byok = True
            choice.estimated_cost = 0.0  # User's own key
            return choice

        return None

    def _select_free_tier(self, request: RoutingRequest) -> ProviderChoice:
        """Select best free tier provider."""
        # Code tasks: use local Qwen
        if request.task_type == TaskType.CODE:
            return self._create_choice(
                "local/qwen-32b",
                request,
                "Free tier: Local Qwen for code tasks"
            )

        # Instant response needed: Groq
        if request.latency_slo == LatencySLO.INSTANT and request.estimated_tokens < 8000:
            return self._create_choice(
                "groq/llama3-70b",
                request,
                "Free tier: Groq for instant responses"
            )

        # Long context: HuggingFace Mixtral
        if request.estimated_tokens > 16000:
            return self._create_choice(
                "huggingface/mixtral-8x7b",
                request,
                "Free tier: HuggingFace Mixtral for long context"
            )

        # Default: local Llama3
        return self._create_choice(
            "local/llama3-8b",
            request,
            "Free tier: Local Llama3 for general tasks"
        )

    async def _select_by_task_type(
        self,
        request: RoutingRequest,
        max_cost: float,
        power_config: Dict[str, Any]
    ) -> ProviderChoice:
        """Select provider based on task type and constraints."""
        task_type = request.task_type
        quality = request.quality_requirement

        # Code tasks
        if task_type == TaskType.CODE:
            if quality == QualityRequirement.BEST:
                if max_cost >= 0.008:
                    return self._create_choice(
                        "openrouter/claude-3.5",
                        request,
                        "Code task (best quality): Claude 3.5 via OpenRouter"
                    )
                else:
                    return self._create_choice(
                        "fireworks/qwen-72b",
                        request,
                        "Code task (budget-friendly): Qwen 72B via Fireworks"
                    )
            else:
                return self._create_choice(
                    "fireworks/qwen-72b",
                    request,
                    "Code task (balanced): Qwen 72B via Fireworks"
                )

        # Creative tasks
        if task_type == TaskType.CREATIVE:
            if quality == QualityRequirement.BEST:
                if request.user_tier in ["enterprise", "professional"] and max_cost >= 0.015:
                    return self._create_choice(
                        "anthropic/claude-3.5",
                        request,
                        "Creative task (best quality): Claude 3.5 direct API"
                    )
                elif max_cost >= 0.008:
                    return self._create_choice(
                        "openrouter/claude-3.5",
                        request,
                        "Creative task (best quality): Claude 3.5 via OpenRouter"
                    )
            return self._create_choice(
                "openrouter/gpt-4o",
                request,
                "Creative task (good quality): GPT-4o via OpenRouter"
            )

        # RAG / Long context
        if task_type == TaskType.RAG and request.estimated_tokens > 30000:
            return self._create_choice(
                "together/mixtral-8x22b",
                request,
                "RAG task (long context): Mixtral 8x22B via Together"
            )

        # Reasoning tasks
        if task_type == TaskType.REASONING:
            if quality == QualityRequirement.BEST and max_cost >= 0.008:
                return self._create_choice(
                    "openrouter/claude-3.5",
                    request,
                    "Reasoning task (best quality): Claude 3.5 via OpenRouter"
                )
            else:
                return self._create_choice(
                    "local/qwen-32b",
                    request,
                    "Reasoning task (balanced): Local Qwen 32B"
                )

        # Default: balanced cost/quality
        if request.user_tier in ["enterprise", "professional"] and max_cost >= 0.010:
            return self._create_choice(
                "openrouter/gpt-4o",
                request,
                "General task (premium tier): GPT-4o via OpenRouter"
            )
        else:
            return self._create_choice(
                "together/mixtral-8x22b",
                request,
                "General task (balanced): Mixtral 8x22B via Together"
            )

    def _create_choice(
        self,
        model_key: str,
        request: RoutingRequest,
        reasoning: str
    ) -> ProviderChoice:
        """Create a ProviderChoice from model key and request."""
        config = PROVIDER_CONFIGS[model_key]

        # Calculate estimated cost
        estimated_cost = (request.estimated_tokens / 1000) * config["cost_per_1k"]

        # Determine temperature based on task type
        temperature = {
            TaskType.CODE: 0.2,
            TaskType.CHAT: 0.7,
            TaskType.CREATIVE: 0.9,
            TaskType.ANALYSIS: 0.3,
            TaskType.RAG: 0.1,
            TaskType.REASONING: 0.2,
            TaskType.TRANSLATION: 0.3,
            TaskType.SUMMARIZATION: 0.3
        }.get(request.task_type, 0.7)

        # Get fallback chain
        fallback_chain = self.get_fallback_chain(model_key, request)

        return ProviderChoice(
            provider=config["provider"],
            model=config["model"],
            max_tokens=min(config["max_tokens"], request.estimated_tokens * 2),
            temperature=temperature,
            estimated_cost=estimated_cost,
            reasoning=reasoning,
            fallback_chain=fallback_chain,
            is_byok=False
        )

    def get_fallback_chain(
        self,
        primary_model: str,
        request: RoutingRequest
    ) -> List[str]:
        """
        Get fallback providers if primary fails.

        Returns list of fallback model keys in priority order.
        """
        primary_config = PROVIDER_CONFIGS[primary_model]
        fallbacks = []

        # Find similar models (same strengths, different providers)
        for model_key, config in PROVIDER_CONFIGS.items():
            if model_key == primary_model:
                continue

            # Check if model has similar strengths
            common_strengths = set(config["strengths"]) & set(primary_config["strengths"])
            if common_strengths:
                # Check if user tier allows
                if self._tier_allows_provider(request.user_tier, config["requires_tier"]):
                    # Add with priority based on cost similarity
                    cost_diff = abs(config["cost_per_1k"] - primary_config["cost_per_1k"])
                    fallbacks.append((cost_diff, model_key))

        # Sort by cost similarity and return top 3
        fallbacks.sort()
        return [model_key for _, model_key in fallbacks[:3]]

    def _tier_allows_provider(self, user_tier: str, required_tier: str) -> bool:
        """Check if user tier allows provider."""
        tier_hierarchy = ["free", "starter", "professional", "enterprise"]
        user_level = tier_hierarchy.index(user_tier) if user_tier in tier_hierarchy else 0
        required_level = tier_hierarchy.index(required_tier) if required_tier in tier_hierarchy else 0
        return user_level >= required_level

    async def estimate_cost(
        self,
        request: RoutingRequest,
        provider_key: str
    ) -> float:
        """
        Calculate expected cost before execution.

        Args:
            request: RoutingRequest
            provider_key: Provider key (e.g., "groq/llama3-70b")

        Returns:
            Estimated cost in credits
        """
        config = PROVIDER_CONFIGS.get(provider_key)
        if not config:
            logger.warning(f"Unknown provider: {provider_key}")
            return 0.01  # Default estimate

        # Base cost calculation
        cost = (request.estimated_tokens / 1000) * config["cost_per_1k"]

        # Add output token estimate (assume 1:1 ratio for safety)
        cost *= 2

        return cost

    def _get_cache_key(self, request: RoutingRequest) -> str:
        """Generate cache key for routing decision."""
        return (
            f"wilmer:routing:{request.task_type.value}:"
            f"{request.latency_slo.value}:{request.privacy_required}:"
            f"{request.user_tier}:{request.power_level.value}:"
            f"{request.quality_requirement.value}:{request.estimated_tokens}"
        )

    async def _cache_decision(self, key: str, choice: ProviderChoice):
        """Cache routing decision for 5 minutes."""
        if self.cache_service:
            await self.cache_service.set(
                key,
                {
                    "provider": choice.provider,
                    "model": choice.model,
                    "max_tokens": choice.max_tokens,
                    "temperature": choice.temperature,
                    "estimated_cost": choice.estimated_cost,
                    "reasoning": choice.reasoning,
                    "fallback_chain": choice.fallback_chain,
                    "is_byok": choice.is_byok
                },
                ttl=300  # 5 minutes
            )

    async def check_provider_health(self) -> Dict[str, bool]:
        """
        Check health of all configured providers.

        Returns:
            Dict mapping provider names to health status (True/False)
        """
        if self.last_health_check:
            # Only check every 60 seconds
            if (datetime.now() - self.last_health_check).total_seconds() < 60:
                return self.provider_health

        logger.info("Performing provider health checks...")

        health_results = {}

        # Check each unique provider
        unique_providers = set(
            config["provider"] for config in PROVIDER_CONFIGS.values()
        )

        for provider in unique_providers:
            try:
                # TODO: Implement actual health check
                # For now, assume all healthy except "local" which requires service check
                if provider == "local":
                    # Check if vLLM/Ollama are accessible
                    health_results[provider] = True  # Placeholder
                else:
                    health_results[provider] = True
            except Exception as e:
                logger.error(f"Health check failed for {provider}: {e}")
                health_results[provider] = False

        self.provider_health = health_results
        self.last_health_check = datetime.now()

        return health_results

    def get_available_models_for_tier(self, user_tier: str) -> List[Dict[str, Any]]:
        """
        Get list of available models for user tier.

        Args:
            user_tier: User's subscription tier

        Returns:
            List of model configs available to tier
        """
        available = []

        for model_key, config in PROVIDER_CONFIGS.items():
            if self._tier_allows_provider(user_tier, config["requires_tier"]):
                available.append({
                    "key": model_key,
                    "provider": config["provider"],
                    "model": config["model"],
                    "max_tokens": config["max_tokens"],
                    "cost_per_1k": config["cost_per_1k"],
                    "strengths": config["strengths"],
                    "avg_latency_ms": config["avg_latency_ms"]
                })

        return available


# Singleton instance
_wilmer_router: Optional[WilmerRouter] = None


def get_wilmer_router(byok_service=None, cache_service=None) -> WilmerRouter:
    """Get or create singleton WilmerRouter instance."""
    global _wilmer_router
    if _wilmer_router is None:
        _wilmer_router = WilmerRouter(byok_service, cache_service)
    return _wilmer_router
