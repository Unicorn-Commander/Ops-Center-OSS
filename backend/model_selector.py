"""
Model Selection Utilities

Helper functions for selecting optimal models based on task requirements.

Author: Ops-Center Backend Team
Date: October 20, 2025
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

from wilmer_router import (
    TaskType, PowerLevel, QualityRequirement,
    LatencySLO, PROVIDER_CONFIGS
)

logger = logging.getLogger(__name__)


class ModelCapability(Enum):
    """Model capability categories"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    FUNCTION_CALLING = "function_calling"
    LONG_CONTEXT = "long_context"
    INSTANT_RESPONSE = "instant_response"
    CREATIVE_WRITING = "creative_writing"
    REASONING = "reasoning"
    MULTILINGUAL = "multilingual"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"


# Model capability matrix
MODEL_CAPABILITIES = {
    # Local Models
    "local/qwen-32b": {
        "capabilities": [
            ModelCapability.CODE_GENERATION,
            ModelCapability.REASONING,
            ModelCapability.FUNCTION_CALLING
        ],
        "quality_score": 0.85,
        "speed_score": 0.7,
        "cost_score": 1.0  # Free
    },
    "local/llama3-8b": {
        "capabilities": [
            ModelCapability.CODE_REVIEW,
            ModelCapability.SUMMARIZATION
        ],
        "quality_score": 0.70,
        "speed_score": 0.9,
        "cost_score": 1.0  # Free
    },

    # Free Tier
    "groq/llama3-70b": {
        "capabilities": [
            ModelCapability.INSTANT_RESPONSE,
            ModelCapability.CODE_REVIEW,
        ],
        "quality_score": 0.80,
        "speed_score": 1.0,  # Fastest
        "cost_score": 1.0  # Free
    },
    "huggingface/mixtral-8x7b": {
        "capabilities": [
            ModelCapability.LONG_CONTEXT,
            ModelCapability.MULTILINGUAL
        ],
        "quality_score": 0.75,
        "speed_score": 0.4,
        "cost_score": 1.0  # Free
    },

    # Paid Low Cost
    "together/mixtral-8x22b": {
        "capabilities": [
            ModelCapability.LONG_CONTEXT,
            ModelCapability.REASONING,
            ModelCapability.MULTILINGUAL
        ],
        "quality_score": 0.85,
        "speed_score": 0.8,
        "cost_score": 0.9
    },
    "fireworks/qwen-72b": {
        "capabilities": [
            ModelCapability.CODE_GENERATION,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.REASONING
        ],
        "quality_score": 0.87,
        "speed_score": 0.85,
        "cost_score": 0.9
    },
    "deepinfra/llama3-70b": {
        "capabilities": [
            ModelCapability.CODE_REVIEW,
            ModelCapability.SUMMARIZATION
        ],
        "quality_score": 0.80,
        "speed_score": 0.75,
        "cost_score": 0.85
    },

    # Premium
    "openrouter/claude-3.5": {
        "capabilities": [
            ModelCapability.CODE_GENERATION,
            ModelCapability.CODE_REVIEW,
            ModelCapability.CREATIVE_WRITING,
            ModelCapability.REASONING,
            ModelCapability.FUNCTION_CALLING
        ],
        "quality_score": 0.95,
        "speed_score": 0.75,
        "cost_score": 0.6
    },
    "openrouter/gpt-4o": {
        "capabilities": [
            ModelCapability.CREATIVE_WRITING,
            ModelCapability.REASONING,
            ModelCapability.MULTILINGUAL,
            ModelCapability.FUNCTION_CALLING
        ],
        "quality_score": 0.93,
        "speed_score": 0.8,
        "cost_score": 0.5
    },
    "anthropic/claude-3.5": {
        "capabilities": [
            ModelCapability.CODE_GENERATION,
            ModelCapability.CODE_REVIEW,
            ModelCapability.CREATIVE_WRITING,
            ModelCapability.REASONING,
            ModelCapability.FUNCTION_CALLING
        ],
        "quality_score": 0.97,
        "speed_score": 0.85,
        "cost_score": 0.4
    },
    "openai/gpt-4o": {
        "capabilities": [
            ModelCapability.CREATIVE_WRITING,
            ModelCapability.REASONING,
            ModelCapability.MULTILINGUAL,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.INSTANT_RESPONSE
        ],
        "quality_score": 0.95,
        "speed_score": 0.9,
        "cost_score": 0.4
    }
}


def select_model_for_task(
    task_type: str,
    power_level: str = "balanced",
    max_cost: float = 0.01,
    required_capabilities: Optional[List[str]] = None,
    min_quality: float = 0.7
) -> Dict[str, Any]:
    """
    Select optimal model for task.

    Args:
        task_type: Type of task (code, chat, reasoning, creative, etc.)
        power_level: User power level (eco, balanced, precision)
        max_cost: Maximum cost per 1K tokens
        required_capabilities: List of required capabilities
        min_quality: Minimum quality score (0-1)

    Returns:
        Dict with selected model key and configuration
    """
    # Convert string to enums
    try:
        task_enum = TaskType(task_type)
    except ValueError:
        task_enum = TaskType.CHAT

    try:
        power_enum = PowerLevel(power_level)
    except ValueError:
        power_enum = PowerLevel.BALANCED

    # Filter models by cost constraint
    affordable_models = {
        key: config for key, config in PROVIDER_CONFIGS.items()
        if config["cost_per_1k"] <= max_cost
    }

    if not affordable_models:
        logger.warning(f"No models within budget ${max_cost}, using cheapest")
        # Find cheapest model
        cheapest = min(
            PROVIDER_CONFIGS.items(),
            key=lambda x: x[1]["cost_per_1k"]
        )
        affordable_models = {cheapest[0]: cheapest[1]}

    # Filter by quality
    quality_models = {}
    for key, config in affordable_models.items():
        capability_info = MODEL_CAPABILITIES.get(key, {})
        if capability_info.get("quality_score", 0) >= min_quality:
            quality_models[key] = config

    if not quality_models:
        logger.warning(f"No models meeting quality threshold {min_quality}")
        quality_models = affordable_models

    # Filter by required capabilities
    if required_capabilities:
        capability_models = {}
        for key, config in quality_models.items():
            capability_info = MODEL_CAPABILITIES.get(key, {})
            model_caps = [cap.value for cap in capability_info.get("capabilities", [])]
            if all(cap in model_caps for cap in required_capabilities):
                capability_models[key] = config

        if capability_models:
            quality_models = capability_models

    # Score models based on power level
    scored_models = []
    for key, config in quality_models.items():
        capability_info = MODEL_CAPABILITIES.get(key, {})

        # Calculate composite score based on power level
        if power_enum == PowerLevel.ECO:
            # Prioritize cost
            score = (
                capability_info.get("cost_score", 0.5) * 0.7 +
                capability_info.get("quality_score", 0.5) * 0.2 +
                capability_info.get("speed_score", 0.5) * 0.1
            )
        elif power_enum == PowerLevel.PRECISION:
            # Prioritize quality
            score = (
                capability_info.get("quality_score", 0.5) * 0.7 +
                capability_info.get("speed_score", 0.5) * 0.2 +
                capability_info.get("cost_score", 0.5) * 0.1
            )
        else:  # BALANCED
            # Equal weight
            score = (
                capability_info.get("quality_score", 0.5) * 0.4 +
                capability_info.get("speed_score", 0.5) * 0.3 +
                capability_info.get("cost_score", 0.5) * 0.3
            )

        # Bonus for task-specific strengths
        if task_type in config.get("strengths", []):
            score += 0.1

        scored_models.append((score, key, config))

    # Select best model
    if not scored_models:
        logger.error("No models found after filtering")
        # Return local fallback
        return {
            "key": "local/llama3-8b",
            "provider": "local",
            "model": "ollama/llama3",
            "config": PROVIDER_CONFIGS["local/llama3-8b"],
            "score": 0.5
        }

    scored_models.sort(reverse=True)
    best_score, best_key, best_config = scored_models[0]

    logger.info(
        f"Selected model: {best_key} (score: {best_score:.2f}) for "
        f"task={task_type}, power={power_level}"
    )

    return {
        "key": best_key,
        "provider": best_config["provider"],
        "model": best_config["model"],
        "config": best_config,
        "score": best_score,
        "alternatives": [
            {"key": key, "score": score}
            for score, key, _ in scored_models[1:4]
        ]
    }


def get_models_by_capability(
    capability: str,
    max_cost: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Get all models with specific capability.

    Args:
        capability: Capability to filter by
        max_cost: Optional maximum cost per 1K tokens

    Returns:
        List of models with that capability
    """
    try:
        capability_enum = ModelCapability(capability)
    except ValueError:
        logger.warning(f"Unknown capability: {capability}")
        return []

    matching_models = []

    for key, capability_info in MODEL_CAPABILITIES.items():
        if capability_enum in capability_info.get("capabilities", []):
            config = PROVIDER_CONFIGS.get(key)
            if config:
                # Check cost constraint
                if max_cost is None or config["cost_per_1k"] <= max_cost:
                    matching_models.append({
                        "key": key,
                        "provider": config["provider"],
                        "model": config["model"],
                        "cost_per_1k": config["cost_per_1k"],
                        "quality_score": capability_info.get("quality_score", 0),
                        "speed_score": capability_info.get("speed_score", 0)
                    })

    # Sort by quality score
    matching_models.sort(key=lambda x: x["quality_score"], reverse=True)

    return matching_models


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.

    Uses rough approximation: 1 token ≈ 4 characters.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    # Rough approximation
    return len(text) // 4


def recommend_context_window(
    estimated_input_tokens: int,
    estimated_output_tokens: int,
    safety_margin: float = 0.2
) -> int:
    """
    Recommend context window size.

    Args:
        estimated_input_tokens: Estimated input size
        estimated_output_tokens: Estimated output size
        safety_margin: Safety margin percentage (default 20%)

    Returns:
        Recommended context window size
    """
    total_tokens = estimated_input_tokens + estimated_output_tokens
    with_margin = int(total_tokens * (1 + safety_margin))

    # Round up to common context sizes
    common_sizes = [2048, 4096, 8192, 16384, 32768, 65536, 131072]
    for size in common_sizes:
        if with_margin <= size:
            return size

    # If larger than all common sizes
    return common_sizes[-1]


def get_optimal_temperature(task_type: str) -> float:
    """
    Get optimal temperature for task type.

    Args:
        task_type: Type of task

    Returns:
        Recommended temperature value
    """
    temperature_map = {
        "code": 0.2,
        "chat": 0.7,
        "creative": 0.9,
        "analysis": 0.3,
        "rag": 0.1,
        "reasoning": 0.2,
        "translation": 0.3,
        "summarization": 0.3
    }

    return temperature_map.get(task_type, 0.7)


def compare_models(
    model_keys: List[str]
) -> List[Dict[str, Any]]:
    """
    Compare multiple models across capabilities.

    Args:
        model_keys: List of model keys to compare

    Returns:
        List of comparison data
    """
    comparisons = []

    for key in model_keys:
        config = PROVIDER_CONFIGS.get(key)
        capabilities = MODEL_CAPABILITIES.get(key, {})

        if not config:
            logger.warning(f"Unknown model: {key}")
            continue

        comparisons.append({
            "key": key,
            "provider": config["provider"],
            "model": config["model"],
            "cost_per_1k": config["cost_per_1k"],
            "max_tokens": config["max_tokens"],
            "avg_latency_ms": config["avg_latency_ms"],
            "quality_score": capabilities.get("quality_score", 0),
            "speed_score": capabilities.get("speed_score", 0),
            "cost_score": capabilities.get("cost_score", 0),
            "capabilities": [
                cap.value for cap in capabilities.get("capabilities", [])
            ],
            "strengths": config.get("strengths", [])
        })

    return comparisons


def get_tier_recommendations(user_tier: str) -> Dict[str, List[str]]:
    """
    Get recommended models for user tier.

    Args:
        user_tier: User's subscription tier

    Returns:
        Dict mapping use cases to recommended models
    """
    tier_hierarchy = ["free", "starter", "professional", "enterprise"]
    tier_level = tier_hierarchy.index(user_tier) if user_tier in tier_hierarchy else 0

    recommendations = {
        "code_tasks": [],
        "creative_tasks": [],
        "chat_tasks": [],
        "reasoning_tasks": [],
        "instant_responses": []
    }

    for key, config in PROVIDER_CONFIGS.items():
        required_tier = config.get("requires_tier", "free")
        required_level = tier_hierarchy.index(required_tier) if required_tier in tier_hierarchy else 0

        if tier_level >= required_level:
            # Add to appropriate categories based on strengths
            if "code" in config.get("strengths", []):
                recommendations["code_tasks"].append(key)
            if "creative" in config.get("strengths", []):
                recommendations["creative_tasks"].append(key)
            if "chat" in config.get("strengths", []):
                recommendations["chat_tasks"].append(key)
            if "reasoning" in config.get("strengths", []):
                recommendations["reasoning_tasks"].append(key)
            if "instant" in config.get("strengths", []):
                recommendations["instant_responses"].append(key)

    return recommendations
