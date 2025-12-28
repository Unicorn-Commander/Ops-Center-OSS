"""Cost Optimization Engine

Analyzes usage patterns and generates actionable cost optimization recommendations.

Features:
- LLM model cost comparison and recommendations
- Caching opportunity identification
- Plan tier optimization for users
- Resource utilization analysis
- Batch processing recommendations
- Off-peak scheduling suggestions
"""

import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)

# Model cost data (per 1M tokens)
MODEL_COSTS = {
    "gpt-4": {"input": 30.0, "output": 60.0, "quality": 95},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0, "quality": 93},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5, "quality": 80},
    "claude-3-opus": {"input": 15.0, "output": 75.0, "quality": 95},
    "claude-3-sonnet": {"input": 3.0, "output": 15.0, "quality": 88},
    "claude-3-haiku": {"input": 0.25, "output": 1.25, "quality": 75},
    "llama-3-70b": {"input": 0.9, "output": 0.9, "quality": 82},
    "qwen2.5-32b": {"input": 0.5, "output": 0.5, "quality": 78},
}

# Plan tier monthly costs
PLAN_COSTS = {
    "trial": 4.0,  # $1/week
    "starter": 19.0,
    "professional": 49.0,
    "enterprise": 99.0
}

# Plan tier limits
PLAN_LIMITS = {
    "trial": {"api_calls": 700, "tokens": 100000},
    "starter": {"api_calls": 30000, "tokens": 5000000},
    "professional": {"api_calls": 300000, "tokens": 50000000},
    "enterprise": {"api_calls": -1, "tokens": -1}
}

class CostOptimizer:
    """Cost optimization engine for generating recommendations"""

    def __init__(self):
        """Initialize cost optimizer"""
        self.recommendations = []

    async def generate_recommendations(self, days: int = 7) -> List[Dict[str, Any]]:
        """Generate all cost optimization recommendations

        Args:
            days: Number of days to analyze

        Returns:
            List of optimization recommendations
        """
        self.recommendations = []

        # Run all analysis methods
        await self.analyze_llm_usage()
        await self.analyze_caching_opportunities()
        await self.analyze_quota_efficiency()
        await self.analyze_resource_utilization()
        await self.analyze_batch_processing()
        await self.analyze_peak_hours()

        # Sort by potential savings (descending)
        self.recommendations.sort(
            key=lambda x: self._parse_savings(x["potential_savings"]),
            reverse=True
        )

        return self.recommendations

    def _parse_savings(self, savings_str: str) -> float:
        """Parse savings string to float for sorting"""
        try:
            return float(savings_str.replace('$', '').replace('/month', '').replace(',', ''))
        except:
            return 0.0

    async def analyze_llm_usage(self):
        """Analyze LLM usage and recommend cheaper models

        Identifies queries that could use cheaper models without
        significant quality degradation.
        """
        # Simulated analysis (would use actual usage data)
        current_model = "gpt-4"
        current_usage_pct = 45  # 45% of queries use GPT-4

        # Check if cheaper model is viable
        for alt_model in ["gpt-4-turbo", "claude-3-sonnet", "gpt-3.5-turbo"]:
            if MODEL_COSTS[alt_model]["quality"] >= 85:  # acceptable quality
                current_cost = MODEL_COSTS[current_model]["input"]
                alt_cost = MODEL_COSTS[alt_model]["input"]

                if alt_cost < current_cost:
                    # Calculate savings
                    cost_reduction_pct = ((current_cost - alt_cost) / current_cost) * 100
                    monthly_savings = (current_cost - alt_cost) * 0.5 * current_usage_pct / 100

                    quality_loss = MODEL_COSTS[current_model]["quality"] - MODEL_COSTS[alt_model]["quality"]

                    self.recommendations.append({
                        "type": "model_switch",
                        "priority": "high" if monthly_savings > 30 else "medium",
                        "current": current_model,
                        "recommended": alt_model,
                        "potential_savings": f"${monthly_savings:.2f}/month",
                        "impact": f"{cost_reduction_pct:.1f}% cost reduction with {quality_loss}% quality trade-off",
                        "implementation_effort": "low"
                    })
                    break  # Only recommend one alternative

        # Recommend model routing based on query complexity
        self.recommendations.append({
            "type": "smart_routing",
            "priority": "high",
            "current": "Single model for all queries",
            "recommended": "Route simple queries to cheaper models",
            "potential_savings": "$85.00/month",
            "impact": "40% of queries can use GPT-3.5-turbo with no quality loss",
            "implementation_effort": "medium"
        })

    async def analyze_caching_opportunities(self):
        """Identify caching opportunities to reduce API calls

        Analyzes request patterns to find repeated queries that
        could benefit from caching.
        """
        # Simulated analysis
        duplicate_rate = 35  # 35% of queries are duplicates

        if duplicate_rate > 20:
            monthly_savings = 12.0 * (duplicate_rate / 35)  # scale with duplicate rate

            self.recommendations.append({
                "type": "caching",
                "priority": "medium",
                "current": "No response caching",
                "recommended": "Enable Redis caching for embeddings and common queries",
                "potential_savings": f"${monthly_savings:.2f}/month",
                "impact": f"Reduce API calls by {duplicate_rate}% through intelligent caching",
                "implementation_effort": "low"
            })

        # Semantic caching for LLM responses
        self.recommendations.append({
            "type": "semantic_caching",
            "priority": "medium",
            "current": "Exact-match caching only",
            "recommended": "Implement semantic similarity caching for LLM responses",
            "potential_savings": "$28.00/month",
            "impact": "Cache semantically similar queries (50% hit rate expected)",
            "implementation_effort": "medium"
        })

    async def analyze_quota_efficiency(self):
        """Analyze plan tier efficiency and recommend changes

        Identifies users who are over/under their plan limits
        and recommends appropriate tier changes.
        """
        # Simulated analysis of user tiers
        over_quota_users = [
            {"user": "user1@example.com", "tier": "starter", "usage_pct": 145},
            {"user": "user2@example.com", "tier": "starter", "usage_pct": 125}
        ]

        under_quota_users = [
            {"user": "user3@example.com", "tier": "professional", "usage_pct": 15},
            {"user": "user4@example.com", "tier": "professional", "usage_pct": 22}
        ]

        if over_quota_users:
            upgrade_count = len(over_quota_users)
            revenue_gain = upgrade_count * (PLAN_COSTS["professional"] - PLAN_COSTS["starter"])

            self.recommendations.append({
                "type": "plan_upgrade",
                "priority": "high",
                "current": f"{upgrade_count} users over quota on Starter plan",
                "recommended": "Upgrade to Professional plan",
                "potential_savings": f"+${revenue_gain:.2f}/month revenue",
                "impact": "Prevent service degradation and increase revenue",
                "implementation_effort": "low"
            })

        if under_quota_users:
            downgrade_count = len(under_quota_users)
            cost_increase = downgrade_count * (PLAN_COSTS["professional"] - PLAN_COSTS["starter"])

            self.recommendations.append({
                "type": "plan_optimization",
                "priority": "low",
                "current": f"{downgrade_count} users significantly under quota",
                "recommended": "Offer appropriate tier downgrade or features",
                "potential_savings": f"User retention (${cost_increase:.2f}/month at risk)",
                "impact": "Improve user satisfaction and retention",
                "implementation_effort": "low"
            })

        # Usage-based billing recommendation
        self.recommendations.append({
            "type": "billing_model",
            "priority": "medium",
            "current": "Fixed tier pricing",
            "recommended": "Add usage-based billing option",
            "potential_savings": "$150.00/month additional revenue",
            "impact": "Better alignment of costs with usage, attract cost-conscious users",
            "implementation_effort": "high"
        })

    async def analyze_resource_utilization(self):
        """Identify underutilized resources

        Analyzes resource usage patterns to find idle or
        underutilized infrastructure.
        """
        # Simulated resource utilization
        avg_gpu_util = 62  # 62% average GPU utilization

        if avg_gpu_util < 70:
            idle_pct = 100 - avg_gpu_util
            potential_savings = 45.0 * (idle_pct / 38)

            self.recommendations.append({
                "type": "resource_optimization",
                "priority": "medium",
                "current": f"GPU utilization at {avg_gpu_util}%",
                "recommended": "Implement request batching and queue management",
                "potential_savings": f"${potential_savings:.2f}/month",
                "impact": f"Increase GPU utilization by {idle_pct}% through better scheduling",
                "implementation_effort": "medium"
            })

        # Model consolidation
        self.recommendations.append({
            "type": "model_consolidation",
            "priority": "low",
            "current": "Multiple models loaded simultaneously",
            "recommended": "Consolidate to fewer, more versatile models",
            "potential_savings": "$32.00/month",
            "impact": "Reduce memory overhead and improve cache efficiency",
            "implementation_effort": "medium"
        })

    async def analyze_batch_processing(self):
        """Recommend batch processing for cost efficiency

        Identifies workloads that could benefit from batch
        processing instead of real-time processing.
        """
        # Simulated analysis
        batch_eligible_pct = 25  # 25% of requests could be batched

        if batch_eligible_pct > 15:
            monthly_savings = 18.0 * (batch_eligible_pct / 25)

            self.recommendations.append({
                "type": "batch_processing",
                "priority": "medium",
                "current": "All requests processed in real-time",
                "recommended": "Implement batch processing for embeddings and non-urgent tasks",
                "potential_savings": f"${monthly_savings:.2f}/month",
                "impact": f"{batch_eligible_pct}% of workload eligible for batching (5x cost reduction)",
                "implementation_effort": "medium"
            })

        # Scheduled background jobs
        self.recommendations.append({
            "type": "job_scheduling",
            "priority": "low",
            "current": "Background tasks run throughout the day",
            "recommended": "Schedule resource-intensive tasks during off-peak hours",
            "potential_savings": "$8.00/month",
            "impact": "Reduce peak load and improve response times",
            "implementation_effort": "low"
        })

    async def analyze_peak_hours(self):
        """Analyze peak usage hours and recommend scheduling

        Identifies peak usage patterns and recommends strategies
        to shift non-urgent workloads to off-peak hours.
        """
        # Simulated peak hour analysis
        peak_hours = [10, 11, 14, 15]  # 10-11 AM, 2-3 PM
        off_peak_discount = 20  # 20% cost reduction during off-peak

        self.recommendations.append({
            "type": "peak_shifting",
            "priority": "low",
            "current": "Uniform request distribution",
            "recommended": "Incentivize off-peak usage with discounts",
            "potential_savings": "$15.00/month",
            "impact": "Reduce peak load congestion by 30%",
            "implementation_effort": "medium"
        })

        # Auto-scaling recommendation
        self.recommendations.append({
            "type": "auto_scaling",
            "priority": "medium",
            "current": "Fixed infrastructure capacity",
            "recommended": "Implement auto-scaling based on demand",
            "potential_savings": "$65.00/month",
            "impact": "Scale down during off-peak hours (50% capacity reduction possible)",
            "implementation_effort": "high"
        })

    def calculate_model_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a specific model and token count

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Total cost in USD
        """
        costs = MODEL_COSTS.get(model, MODEL_COSTS["gpt-3.5-turbo"])
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]
        return input_cost + output_cost

    def compare_models(self, input_tokens: int, output_tokens: int) -> List[Dict[str, Any]]:
        """Compare costs across different models

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            List of models with costs and quality scores
        """
        comparisons = []

        for model, specs in MODEL_COSTS.items():
            cost = self.calculate_model_cost(model, input_tokens, output_tokens)

            comparisons.append({
                "model": model,
                "cost": round(cost, 4),
                "quality": specs["quality"],
                "cost_per_quality": round(cost / specs["quality"], 6)
            })

        # Sort by cost (ascending)
        comparisons.sort(key=lambda x: x["cost"])

        return comparisons

    def estimate_caching_savings(self, total_calls: int, duplicate_rate: float, avg_cost_per_call: float) -> Dict[str, Any]:
        """Estimate savings from caching implementation

        Args:
            total_calls: Total API calls in period
            duplicate_rate: Percentage of duplicate/cacheable calls (0-100)
            avg_cost_per_call: Average cost per API call

        Returns:
            Dictionary with savings estimate
        """
        cacheable_calls = int(total_calls * (duplicate_rate / 100))
        cache_hit_rate = 80  # Expected 80% cache hit rate

        calls_saved = int(cacheable_calls * (cache_hit_rate / 100))
        cost_saved = calls_saved * avg_cost_per_call

        # Redis hosting cost
        redis_cost = 10.0  # $10/month for Redis hosting

        net_savings = cost_saved - redis_cost

        return {
            "cacheable_calls": cacheable_calls,
            "calls_saved": calls_saved,
            "gross_savings": round(cost_saved, 2),
            "infrastructure_cost": redis_cost,
            "net_savings": round(net_savings, 2),
            "roi_percent": round((net_savings / redis_cost) * 100, 1) if redis_cost > 0 else 0
        }

    def recommend_plan_tier(self, monthly_calls: int, monthly_tokens: int) -> Dict[str, Any]:
        """Recommend appropriate plan tier based on usage

        Args:
            monthly_calls: Monthly API calls
            monthly_tokens: Monthly token usage

        Returns:
            Dictionary with tier recommendation
        """
        # Find appropriate tier
        recommended_tier = "trial"

        for tier, limits in PLAN_LIMITS.items():
            call_limit = limits["api_calls"]
            token_limit = limits["tokens"]

            # Check if usage fits within tier (with 20% buffer)
            if call_limit == -1:  # unlimited
                recommended_tier = tier
                break
            elif monthly_calls <= call_limit * 0.8 and monthly_tokens <= token_limit * 0.8:
                recommended_tier = tier
                break

        # Calculate utilization for recommended tier
        tier_limits = PLAN_LIMITS[recommended_tier]
        call_utilization = (monthly_calls / tier_limits["api_calls"] * 100) if tier_limits["api_calls"] > 0 else 0
        token_utilization = (monthly_tokens / tier_limits["tokens"] * 100) if tier_limits["tokens"] > 0 else 0

        return {
            "recommended_tier": recommended_tier,
            "monthly_cost": PLAN_COSTS[recommended_tier],
            "call_utilization_percent": round(call_utilization, 1),
            "token_utilization_percent": round(token_utilization, 1),
            "buffer_remaining_percent": round(100 - max(call_utilization, token_utilization), 1)
        }

    def analyze_query_complexity(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze query complexity to recommend model selection

        Args:
            queries: List of query dictionaries with 'prompt' and 'tokens'

        Returns:
            Dictionary with complexity analysis and recommendations
        """
        if not queries:
            return {
                "simple_queries_pct": 0,
                "medium_queries_pct": 0,
                "complex_queries_pct": 0,
                "recommendation": "No data available"
            }

        # Classify queries by token count
        simple = sum(1 for q in queries if q.get("tokens", 0) < 500)
        medium = sum(1 for q in queries if 500 <= q.get("tokens", 0) < 2000)
        complex = sum(1 for q in queries if q.get("tokens", 0) >= 2000)

        total = len(queries)

        simple_pct = (simple / total) * 100
        medium_pct = (medium / total) * 100
        complex_pct = (complex / total) * 100

        # Generate recommendation
        if simple_pct > 50:
            recommendation = "Use GPT-3.5-turbo or Claude Haiku for majority of queries"
        elif complex_pct > 40:
            recommendation = "Complex workload - GPT-4 or Claude Opus appropriate"
        else:
            recommendation = "Mixed workload - implement smart routing"

        return {
            "simple_queries_pct": round(simple_pct, 1),
            "medium_queries_pct": round(medium_pct, 1),
            "complex_queries_pct": round(complex_pct, 1),
            "recommendation": recommendation,
            "potential_savings": f"${simple * 0.002 + medium * 0.001:.2f}/month with smart routing"
        }


# Example usage
async def main():
    """Example usage of CostOptimizer"""
    optimizer = CostOptimizer()

    # Generate recommendations
    recommendations = await optimizer.generate_recommendations(days=7)

    print(f"Generated {len(recommendations)} cost optimization recommendations:\n")

    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. [{rec['priority'].upper()}] {rec['type']}")
        print(f"   Current: {rec['current']}")
        print(f"   Recommended: {rec['recommended']}")
        print(f"   Savings: {rec['potential_savings']}")
        print(f"   Impact: {rec['impact']}")
        print(f"   Effort: {rec['implementation_effort']}")
        print()

    # Model comparison
    print("\nModel Cost Comparison (1000 input tokens, 500 output tokens):")
    comparisons = optimizer.compare_models(1000, 500)
    for comp in comparisons:
        print(f"  {comp['model']:<20} ${comp['cost']:<8.4f} Quality: {comp['quality']}/100")

    # Caching analysis
    print("\nCaching Savings Estimate:")
    savings = optimizer.estimate_caching_savings(
        total_calls=50000,
        duplicate_rate=35,
        avg_cost_per_call=0.002
    )
    print(f"  Cacheable calls: {savings['cacheable_calls']}")
    print(f"  Calls saved: {savings['calls_saved']}")
    print(f"  Net savings: ${savings['net_savings']}/month")
    print(f"  ROI: {savings['roi_percent']}%")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
