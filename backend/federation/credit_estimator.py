"""
Credit estimation for federation-routed inference requests.

Maps service types and cloud GPU costs to credit amounts,
so users can see the cost before confirming a request.

Cost basis (1 credit ~ $0.001):
  Pricing is derived from actual cloud GPU compute costs with a 25% markup.
  Reference GPU: Lambda GH200 at $1.99/hr ($0.000553/sec).

  Service          | Compute time | Raw cost | +25% markup | Credits
  -----------------|-------------|----------|-------------|--------
  music_gen (60s)  | ~120s       | $0.066   | $0.083      | 83
  image_gen        | ~30s        | $0.017   | $0.021      | 21
  stt (per min)    | ~10s        | $0.006   | $0.007      | 7
  tts              | ~5s         | $0.003   | $0.004      | 4
  embeddings       | ~1s         | $0.0006  | $0.0007     | 1
  reranker         | ~2s         | $0.001   | $0.001      | 1
  llm              | varies      | per-token pricing       | varies
"""


from typing import Any, Dict

# Cloud GPU hourly rates (USD) for dynamic cost calculation.
# Used by estimate_credits() when route_target == "cloud_gpu".
GPU_HOURLY_RATES: Dict[str, float] = {
    "gpu_1x_gh200": 1.99,
    "gpu_1x_a10": 0.86,
    "gpu_1x_a100_sxm4": 1.48,
    "gpu_1x_h100_pcie": 2.86,
    "self_hosted": 0.0,  # free — no cloud cost
}

# Base credit costs per service type (1 credit ~ $0.001).
# Derived from Lambda GH200 compute cost ($0.000553/sec) + 25% markup.
# LLM keeps per-token pricing because duration varies widely by prompt.
SERVICE_CREDIT_COSTS: Dict[str, Dict[str, float]] = {
    "llm": {
        "base_per_request": 5,        # minimum
        "per_1k_input_tokens": 2,
        "per_1k_output_tokens": 4,
    },
    "tts": {
        "base_per_request": 4,        # ~5s compute → $0.003 → +25% → 4 credits
        "per_minute_audio": 5,
    },
    "stt": {
        "base_per_request": 2,
        "per_minute_audio": 7,        # ~10s compute per min → $0.006 → +25% → 7 credits
    },
    "embeddings": {
        "base_per_request": 1,        # ~1s compute → $0.0006 → +25% → 1 credit
        "per_1k_tokens": 0.5,
    },
    "reranker": {
        "base_per_request": 1,        # ~2s compute → $0.001 → +25% → 1 credit
        "per_document": 0.2,
    },
    "image_gen": {
        "base_per_request": 21,       # FLUX ~30s → $0.017 → +25% → 21 credits
        "per_megapixel": 10,
    },
    "music_gen": {
        "base_per_request": 83,       # ACE-Step ~120s for 60s song → $0.066 → +25% → 83 credits
        "per_minute_audio": 30,
    },
}


def estimate_credits(
    service_type: str,
    route_target: str,  # "local", "peer", "cloud", "cloud_gpu"
    cloud_cost_per_hour: float = 0.0,
    estimated_duration_seconds: float = 30.0,
    tier_markup_percentage: float = 0.0,
    gpu_type: str | None = None,
    **kwargs: Any,  # tokens, duration, documents, etc.
) -> Dict[str, Any]:
    """Estimate credit cost for a federation-routed request.

    Args:
        service_type: The type of inference service (e.g. "llm", "tts").
        route_target: Where the request will be routed ("local", "peer",
            "cloud", or "cloud_gpu").
        cloud_cost_per_hour: Hourly cost of the cloud GPU in USD.
            If *gpu_type* is provided this is looked up automatically.
        estimated_duration_seconds: Expected request duration in seconds.
        tier_markup_percentage: Percentage markup to apply based on user tier.
        gpu_type: Optional key into ``GPU_HOURLY_RATES`` (e.g.
            ``"gpu_1x_gh200"``).  When set, overrides *cloud_cost_per_hour*.
        **kwargs: Additional parameters like token counts, audio duration, etc.

    Returns:
        Dict with keys:
            - credits (int): Total estimated credits.
            - cost_usd (float): Equivalent USD cost.
            - breakdown (dict): Itemised credit components.
            - free (bool): True if routed to self-hosted infrastructure.
    """
    if route_target in ("local", "peer"):
        # Self-hosted = free (or internal cost accounting)
        return {"credits": 0, "cost_usd": 0.0, "breakdown": {}, "free": True}

    base = SERVICE_CREDIT_COSTS.get(service_type, {})
    base_credits = int(base.get("base_per_request", 5))

    # Resolve hourly rate from gpu_type if provided
    if gpu_type and gpu_type in GPU_HOURLY_RATES:
        cloud_cost_per_hour = GPU_HOURLY_RATES[gpu_type]

    # Add compute cost for cloud GPU
    compute_credits = 0
    if route_target == "cloud_gpu" and cloud_cost_per_hour > 0:
        compute_cost_usd = (estimated_duration_seconds / 3600) * cloud_cost_per_hour
        compute_credits = int(compute_cost_usd * 1000)  # $0.001 per credit

    # Apply tier markup
    subtotal = base_credits + compute_credits
    markup_credits = int(subtotal * tier_markup_percentage / 100)

    total = subtotal + markup_credits

    return {
        "credits": total,
        "cost_usd": total / 1000,
        "breakdown": {
            "base_credits": base_credits,
            "compute_credits": compute_credits,
            "markup_credits": markup_credits,
        },
        "free": False,
    }
