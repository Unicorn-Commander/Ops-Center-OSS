"""
LLM Routing Engine

Business logic for routing LLM requests to optimal models based on:
- Power level (eco, balanced, precision)
- User tier (free, starter, professional, enterprise)
- Task type (code, chat, rag, creative)
- Cost optimization
- Fallback strategies

Author: Backend API Developer
Epic: 3.1 - LiteLLM Multi-Provider Routing
Date: October 23, 2025
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import random

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models.llm_models import (
    LLMProvider, LLMModel, LLMRoutingRule,
    UserAPIKey, LLMUsageLog
)

logger = logging.getLogger(__name__)


# ============================================================================
# Power Level Definitions
# ============================================================================

POWER_LEVELS = {
    'eco': {
        'max_cost_per_1m_tokens': 0.50,  # $0.50 per 1M tokens max
        'max_latency_ms': 10000,  # 10 seconds max
        'prefer_cached': True,
        'allow_fallback': True,
        'description': 'Budget-friendly models, longer wait times'
    },
    'balanced': {
        'max_cost_per_1m_tokens': 5.00,  # $5.00 per 1M tokens max
        'max_latency_ms': 5000,  # 5 seconds max
        'prefer_cached': True,
        'allow_fallback': True,
        'description': 'Balance of cost and performance'
    },
    'precision': {
        'max_cost_per_1m_tokens': 100.00,  # $100.00 per 1M tokens max
        'max_latency_ms': 2000,  # 2 seconds max
        'prefer_cached': False,  # Fresh results
        'allow_fallback': False,  # No fallback, fail fast
        'description': 'Best available models, fastest response'
    }
}


# ============================================================================
# Routing Engine
# ============================================================================

class LLMRoutingEngine:
    """
    LLM Routing Engine

    Selects optimal LLM model based on:
    - User tier and permissions
    - Power level (eco/balanced/precision)
    - Task type
    - User's own API keys (BYOK)
    - Cost optimization
    - Fallback strategies
    """

    def __init__(self, db: Session):
        """
        Initialize routing engine

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def select_model(
        self,
        user_id: str,
        user_tier: str,
        power_level: str = 'balanced',
        task_type: Optional[str] = None,
        estimated_tokens: Optional[int] = None,
        require_streaming: bool = False,
        require_function_calling: bool = False,
        require_vision: bool = False
    ) -> Tuple[Optional[LLMModel], Optional[str], Optional[str]]:
        """
        Select optimal model for request

        Args:
            user_id: Keycloak user ID
            user_tier: User's subscription tier (free, starter, professional, enterprise)
            power_level: Power level (eco, balanced, precision)
            task_type: Task type (code, chat, rag, creative, general)
            estimated_tokens: Estimated token count for request
            require_streaming: Model must support streaming
            require_function_calling: Model must support function calling
            require_vision: Model must support vision

        Returns:
            Tuple of (model, api_key, key_source)
            - model: Selected LLMModel object
            - api_key: API key to use (system or user's)
            - key_source: 'system' or 'byok'
        """
        try:
            # Validate power level
            if power_level not in POWER_LEVELS:
                logger.warning(f"Invalid power level '{power_level}', defaulting to 'balanced'")
                power_level = 'balanced'

            # Get power level config
            power_config = POWER_LEVELS[power_level]

            # Step 1: Check if user has BYOK for any provider
            user_keys = self.db.query(UserAPIKey).filter(
                and_(
                    UserAPIKey.user_id == user_id,
                    UserAPIKey.is_active == True,
                    UserAPIKey.is_validated == True
                )
            ).all()

            user_provider_ids = [key.provider_id for key in user_keys]

            # Step 2: Find routing rules that match criteria
            query = self.db.query(LLMRoutingRule).join(LLMModel).join(LLMProvider).filter(
                and_(
                    LLMRoutingRule.is_active == True,
                    LLMRoutingRule.power_level == power_level,
                    or_(
                        LLMRoutingRule.user_tier == user_tier,
                        LLMRoutingRule.user_tier == 'all'
                    ),
                    LLMModel.is_active == True,
                    LLMModel.is_deprecated == False,
                    LLMProvider.is_active == True
                )
            )

            # Filter by task type if specified
            if task_type:
                query = query.filter(
                    or_(
                        LLMRoutingRule.task_type == task_type,
                        LLMRoutingRule.task_type == 'general',
                        LLMRoutingRule.task_type == None
                    )
                )

            # Apply capability filters
            if require_streaming:
                query = query.filter(LLMModel.supports_streaming == True)

            if require_function_calling:
                query = query.filter(LLMModel.supports_function_calling == True)

            if require_vision:
                query = query.filter(LLMModel.supports_vision == True)

            # Apply token constraints
            if estimated_tokens:
                query = query.filter(
                    or_(
                        LLMRoutingRule.max_tokens == None,
                        LLMRoutingRule.max_tokens >= estimated_tokens
                    )
                )

            # Get candidates and sort by priority
            routing_rules = query.order_by(
                LLMRoutingRule.priority.asc(),
                LLMRoutingRule.weight.desc()
            ).all()

            if not routing_rules:
                logger.warning(f"No routing rules found for power={power_level}, tier={user_tier}, task={task_type}")
                return None, None, None

            # Step 3: Select model using weighted random selection
            # Prefer models where user has BYOK
            byok_candidates = []
            system_candidates = []

            for rule in routing_rules:
                model = rule.model

                # Check cost constraints from power level
                avg_cost = (model.cost_per_1m_input_tokens or 0 + model.cost_per_1m_output_tokens or 0) / 2
                if avg_cost > power_config['max_cost_per_1m_tokens']:
                    continue

                # Check latency constraints
                if model.avg_latency_ms and model.avg_latency_ms > power_config['max_latency_ms']:
                    continue

                # Check if model requires BYOK
                if rule.requires_byok:
                    if model.provider_id in user_provider_ids:
                        byok_candidates.append((rule, model))
                else:
                    # Provider has system key or user has BYOK
                    if model.provider_id in user_provider_ids:
                        byok_candidates.append((rule, model))
                    elif model.provider.is_system_provider:
                        system_candidates.append((rule, model))

            # Prefer BYOK (saves platform costs)
            if byok_candidates:
                rule, model = self._weighted_random_select(byok_candidates)
                user_key = self.db.query(UserAPIKey).filter(
                    and_(
                        UserAPIKey.user_id == user_id,
                        UserAPIKey.provider_id == model.provider_id,
                        UserAPIKey.is_active == True
                    )
                ).first()

                logger.info(f"Selected BYOK model: {model.model_name} (provider: {model.provider.provider_name})")
                return model, user_key.encrypted_api_key if user_key else None, 'byok'

            elif system_candidates:
                rule, model = self._weighted_random_select(system_candidates)
                logger.info(f"Selected system model: {model.model_name} (provider: {model.provider.provider_name})")
                return model, None, 'system'  # System key will be retrieved by provider

            else:
                logger.warning(f"No eligible models found for user {user_id}")
                return None, None, None

        except Exception as e:
            logger.error(f"Error in select_model: {e}", exc_info=True)
            return None, None, None

    def _weighted_random_select(
        self,
        candidates: List[Tuple[LLMRoutingRule, LLMModel]]
    ) -> Tuple[LLMRoutingRule, LLMModel]:
        """
        Select model using weighted random selection

        Args:
            candidates: List of (routing_rule, model) tuples

        Returns:
            Selected (routing_rule, model) tuple
        """
        if not candidates:
            return None, None

        # If only one candidate, return it
        if len(candidates) == 1:
            return candidates[0]

        # Calculate total weight
        total_weight = sum(rule.weight for rule, _ in candidates)

        # Random selection weighted by priority
        rand = random.randint(1, total_weight)
        cumulative = 0

        for rule, model in candidates:
            cumulative += rule.weight
            if rand <= cumulative:
                return rule, model

        # Fallback to first candidate
        return candidates[0]

    def get_fallback_model(
        self,
        user_id: str,
        user_tier: str,
        power_level: str,
        task_type: Optional[str] = None,
        exclude_model_ids: Optional[List[int]] = None
    ) -> Tuple[Optional[LLMModel], Optional[str], Optional[str]]:
        """
        Get fallback model when primary model fails

        Args:
            user_id: Keycloak user ID
            user_tier: User's subscription tier
            power_level: Power level
            task_type: Task type
            exclude_model_ids: Model IDs to exclude (already failed)

        Returns:
            Tuple of (model, api_key, key_source)
        """
        try:
            # Check if fallback is allowed for this power level
            power_config = POWER_LEVELS.get(power_level, POWER_LEVELS['balanced'])
            if not power_config.get('allow_fallback', True):
                logger.info(f"Fallback disabled for power level '{power_level}'")
                return None, None, None

            # Query fallback routing rules
            query = self.db.query(LLMRoutingRule).join(LLMModel).join(LLMProvider).filter(
                and_(
                    LLMRoutingRule.is_active == True,
                    LLMRoutingRule.is_fallback == True,
                    LLMRoutingRule.power_level == power_level,
                    or_(
                        LLMRoutingRule.user_tier == user_tier,
                        LLMRoutingRule.user_tier == 'all'
                    ),
                    LLMModel.is_active == True,
                    LLMProvider.is_active == True
                )
            )

            # Filter by task type
            if task_type:
                query = query.filter(
                    or_(
                        LLMRoutingRule.task_type == task_type,
                        LLMRoutingRule.task_type == 'general',
                        LLMRoutingRule.task_type == None
                    )
                )

            # Exclude already-failed models
            if exclude_model_ids:
                query = query.filter(LLMModel.id.notin_(exclude_model_ids))

            # Get fallback candidates sorted by fallback_order
            fallback_rules = query.order_by(
                LLMRoutingRule.fallback_order.asc()
            ).all()

            if not fallback_rules:
                logger.warning(f"No fallback models available")
                return None, None, None

            # Select first available fallback
            for rule in fallback_rules:
                model = rule.model

                # Check if user has BYOK for this provider
                user_key = self.db.query(UserAPIKey).filter(
                    and_(
                        UserAPIKey.user_id == user_id,
                        UserAPIKey.provider_id == model.provider_id,
                        UserAPIKey.is_active == True,
                        UserAPIKey.is_validated == True
                    )
                ).first()

                if user_key:
                    logger.info(f"Fallback to BYOK model: {model.model_name}")
                    return model, user_key.encrypted_api_key, 'byok'
                elif model.provider.is_system_provider:
                    logger.info(f"Fallback to system model: {model.model_name}")
                    return model, None, 'system'

            logger.warning(f"No eligible fallback models found")
            return None, None, None

        except Exception as e:
            logger.error(f"Error in get_fallback_model: {e}", exc_info=True)
            return None, None, None

    def calculate_cost(
        self,
        model: LLMModel,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0
    ) -> Dict[str, float]:
        """
        Calculate cost for LLM request

        Args:
            model: LLMModel object
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            cached_tokens: Number of cached tokens

        Returns:
            Dictionary with cost breakdown
        """
        try:
            # Get pricing
            cost_per_1m_input = model.cost_per_1m_input_tokens or 0.0
            cost_per_1m_output = model.cost_per_1m_output_tokens or 0.0
            cost_per_1m_cached = model.cost_per_1m_tokens_cached or (cost_per_1m_input * 0.5)  # 50% discount for cached

            # Calculate costs (divide by 1M to get actual cost)
            cost_input = (prompt_tokens * cost_per_1m_input) / 1_000_000
            cost_output = (completion_tokens * cost_per_1m_output) / 1_000_000
            cost_cached = (cached_tokens * cost_per_1m_cached) / 1_000_000

            total_cost = cost_input + cost_output - cost_cached  # Subtract cached savings

            return {
                'cost_input_usd': round(cost_input, 6),
                'cost_output_usd': round(cost_output, 6),
                'cost_cached_usd': round(cost_cached, 6),
                'cost_total_usd': round(max(total_cost, 0.0), 6),  # Never negative
                'total_tokens': prompt_tokens + completion_tokens,
                'model_id': model.id,
                'model_name': model.model_name
            }

        except Exception as e:
            logger.error(f"Error calculating cost: {e}", exc_info=True)
            return {
                'cost_input_usd': 0.0,
                'cost_output_usd': 0.0,
                'cost_cached_usd': 0.0,
                'cost_total_usd': 0.0,
                'total_tokens': prompt_tokens + completion_tokens,
                'error': str(e)
            }

    def log_usage(
        self,
        user_id: str,
        model: LLMModel,
        request_id: str,
        power_level: str,
        task_type: Optional[str],
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int,
        cost_breakdown: Dict[str, float],
        used_byok: bool,
        user_key_id: Optional[int],
        latency_ms: int,
        status_code: int,
        error_message: Optional[str] = None,
        was_fallback: bool = False,
        fallback_reason: Optional[str] = None,
        request_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Optional[int]:
        """
        Log LLM usage for billing and analytics

        Args:
            user_id: Keycloak user ID
            model: LLMModel object
            request_id: Unique request ID
            power_level: Power level used
            task_type: Task type
            prompt_tokens: Prompt token count
            completion_tokens: Completion token count
            cached_tokens: Cached token count
            cost_breakdown: Cost calculation from calculate_cost()
            used_byok: Whether user's own API key was used
            user_key_id: UserAPIKey ID if BYOK
            latency_ms: Request latency
            status_code: HTTP status code
            error_message: Error message if failed
            was_fallback: Whether fallback model was used
            fallback_reason: Reason for fallback
            request_ip: Client IP address
            user_agent: Client user agent
            session_id: Session ID

        Returns:
            Usage log ID or None if failed
        """
        try:
            # Calculate tokens per second
            tokens_per_second = None
            if latency_ms > 0:
                total_tokens = prompt_tokens + completion_tokens
                tokens_per_second = round((total_tokens / latency_ms) * 1000, 2)

            # Create usage log entry
            usage_log = LLMUsageLog(
                user_id=user_id,
                provider_id=model.provider_id,
                model_id=model.id,
                user_key_id=user_key_id,
                request_id=request_id,
                power_level=power_level,
                task_type=task_type,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                cached_tokens=cached_tokens,
                cost_input_usd=cost_breakdown.get('cost_input_usd', 0.0),
                cost_output_usd=cost_breakdown.get('cost_output_usd', 0.0),
                cost_total_usd=cost_breakdown.get('cost_total_usd', 0.0),
                used_byok=used_byok,
                latency_ms=latency_ms,
                tokens_per_second=tokens_per_second,
                status_code=status_code,
                error_message=error_message,
                was_fallback=was_fallback,
                fallback_reason=fallback_reason,
                request_ip=request_ip,
                user_agent=user_agent,
                session_id=session_id,
                created_at=datetime.utcnow()
            )

            self.db.add(usage_log)
            self.db.commit()

            # Update user API key stats if BYOK
            if used_byok and user_key_id:
                user_key = self.db.query(UserAPIKey).filter(
                    UserAPIKey.id == user_key_id
                ).first()

                if user_key:
                    user_key.total_requests += 1
                    user_key.total_tokens += (prompt_tokens + completion_tokens)
                    user_key.total_cost_usd += cost_breakdown.get('cost_total_usd', 0.0)
                    user_key.last_used_at = datetime.utcnow()
                    self.db.commit()

            logger.info(f"Logged usage: request_id={request_id}, tokens={prompt_tokens + completion_tokens}, cost=${cost_breakdown.get('cost_total_usd', 0.0):.6f}")
            return usage_log.id

        except Exception as e:
            logger.error(f"Error logging usage: {e}", exc_info=True)
            self.db.rollback()
            return None

    def get_user_usage_stats(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage statistics for user

        Args:
            user_id: Keycloak user ID
            days: Number of days to look back

        Returns:
            Dictionary with usage stats
        """
        try:
            from datetime import timedelta

            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Query usage logs
            logs = self.db.query(LLMUsageLog).filter(
                and_(
                    LLMUsageLog.user_id == user_id,
                    LLMUsageLog.created_at >= start_date
                )
            ).all()

            # Calculate stats
            total_requests = len(logs)
            total_tokens = sum(log.total_tokens for log in logs)
            total_cost = sum(log.cost_total_usd for log in logs)
            byok_requests = sum(1 for log in logs if log.used_byok)

            # Group by provider
            provider_stats = {}
            for log in logs:
                provider_name = log.provider.provider_name if log.provider else 'Unknown'
                if provider_name not in provider_stats:
                    provider_stats[provider_name] = {
                        'requests': 0,
                        'tokens': 0,
                        'cost': 0.0
                    }
                provider_stats[provider_name]['requests'] += 1
                provider_stats[provider_name]['tokens'] += log.total_tokens
                provider_stats[provider_name]['cost'] += log.cost_total_usd

            # Group by power level
            power_level_stats = {}
            for log in logs:
                pl = log.power_level or 'balanced'
                if pl not in power_level_stats:
                    power_level_stats[pl] = {
                        'requests': 0,
                        'tokens': 0,
                        'cost': 0.0
                    }
                power_level_stats[pl]['requests'] += 1
                power_level_stats[pl]['tokens'] += log.total_tokens
                power_level_stats[pl]['cost'] += log.cost_total_usd

            return {
                'user_id': user_id,
                'period_days': days,
                'total_requests': total_requests,
                'total_tokens': total_tokens,
                'total_cost_usd': round(total_cost, 6),
                'avg_cost_per_request': round(total_cost / total_requests, 6) if total_requests > 0 else 0.0,
                'byok_requests': byok_requests,
                'byok_percentage': round((byok_requests / total_requests) * 100, 2) if total_requests > 0 else 0.0,
                'provider_breakdown': provider_stats,
                'power_level_breakdown': power_level_stats,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting usage stats: {e}", exc_info=True)
            return {
                'user_id': user_id,
                'error': str(e)
            }


# ============================================================================
# Helper Functions
# ============================================================================

def get_routing_engine(db: Session) -> LLMRoutingEngine:
    """
    Get LLM routing engine instance

    Args:
        db: SQLAlchemy database session

    Returns:
        LLMRoutingEngine instance
    """
    return LLMRoutingEngine(db)
