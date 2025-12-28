"""
LLM Model Access Control

SQLAlchemy model for managing LLM model access control and ID translation.
This model provides:
- Model ID translation (Bolt ID → LiteLLM ID)
- Tier-based access control
- Pricing information
- Provider routing

Database Architect Team Lead
Date: November 8, 2025
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, Text, DECIMAL, TIMESTAMP,
    CheckConstraint, text
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Optional, List, Dict, Any

Base = declarative_base()


class LLMModel(Base):
    """
    LLM Model Access Control & Translation

    Maps frontend model IDs (e.g., "kimi/kimi-dev-72b") to backend LiteLLM
    model IDs (e.g., "openrouter/moonshot/kimi-v1-128k") with tier-based
    access control.

    Example Usage:
        # Check if model is accessible for a tier
        model = session.query(LLMModel).filter_by(model_id="gpt-4o").first()
        if model.is_accessible_for_tier("professional"):
            # Use model.litellm_model_id to call LiteLLM
            pass

        # Get all models for a tier
        models = LLMModel.get_accessible_models(session, "starter")
    """

    __tablename__ = 'models'

    # ========================================================================
    # Primary Key
    # ========================================================================
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ========================================================================
    # Model Identifiers
    # ========================================================================
    model_id = Column(
        String(200),
        unique=True,
        nullable=False,
        index=True,
        comment="Frontend model ID (e.g., 'kimi/kimi-dev-72b')"
    )

    litellm_model_id = Column(
        String(300),
        nullable=False,
        comment="Backend LiteLLM model ID (e.g., 'openrouter/moonshot/kimi-v1-128k')"
    )

    display_name = Column(
        String(300),
        nullable=False,
        comment="Human-readable model name (e.g., 'Kimi Dev 72B')"
    )

    # ========================================================================
    # Provider Information
    # ========================================================================
    provider = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Provider: openai, anthropic, openrouter, etc."
    )

    description = Column(
        Text,
        nullable=True,
        comment="Detailed model description"
    )

    # ========================================================================
    # Access Control
    # ========================================================================
    tier_access = Column(
        JSONB,
        nullable=False,
        default=text("'[\"trial\", \"starter\", \"professional\", \"enterprise\"]'::jsonb"),
        comment="JSONB array of accessible tiers"
    )

    # ========================================================================
    # Pricing (per 1K tokens)
    # ========================================================================
    pricing_input = Column(
        DECIMAL(10, 6),
        nullable=True,
        comment="Cost per 1K input tokens in USD"
    )

    pricing_output = Column(
        DECIMAL(10, 6),
        nullable=True,
        comment="Cost per 1K output tokens in USD"
    )

    # ========================================================================
    # Model Capabilities
    # ========================================================================
    context_length = Column(
        Integer,
        default=8192,
        comment="Maximum context window in tokens"
    )

    max_output_tokens = Column(
        Integer,
        nullable=True,
        comment="Maximum output tokens (if different from context)"
    )

    supports_streaming = Column(
        Boolean,
        default=True,
        comment="Supports streaming responses"
    )

    supports_function_calling = Column(
        Boolean,
        default=False,
        comment="Supports function/tool calling"
    )

    supports_vision = Column(
        Boolean,
        default=False,
        comment="Supports vision/multimodal input"
    )

    # ========================================================================
    # Status
    # ========================================================================
    enabled = Column(
        Boolean,
        default=True,
        index=True,
        comment="Is this model currently available?"
    )

    # ========================================================================
    # Additional Metadata
    # ========================================================================
    tags = Column(
        JSONB,
        default=text("'[]'::jsonb"),
        comment="Tags for categorization (e.g., ['coding', 'reasoning'])"
    )

    metadata = Column(
        JSONB,
        default=text("'{}'::jsonb"),
        comment="Flexible metadata field for future expansion"
    )

    # ========================================================================
    # Timestamps
    # ========================================================================
    created_at = Column(
        TIMESTAMP,
        default=datetime.utcnow,
        nullable=False,
        comment="When this model was added"
    )

    updated_at = Column(
        TIMESTAMP,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp"
    )

    # ========================================================================
    # Table Constraints
    # ========================================================================
    __table_args__ = (
        CheckConstraint(
            "jsonb_typeof(tier_access) = 'array'",
            name='valid_tier_access'
        ),
        CheckConstraint(
            "jsonb_typeof(tags) = 'array'",
            name='valid_tags'
        ),
        CheckConstraint(
            "jsonb_typeof(metadata) = 'object'",
            name='valid_metadata'
        ),
    )

    # ========================================================================
    # Instance Methods
    # ========================================================================

    def is_accessible_for_tier(self, user_tier: str) -> bool:
        """
        Check if this model is accessible for a given subscription tier.

        Args:
            user_tier: User's subscription tier (trial, starter, professional, enterprise)

        Returns:
            True if user has access to this model, False otherwise

        Example:
            >>> model = LLMModel(tier_access=["professional", "enterprise"])
            >>> model.is_accessible_for_tier("professional")
            True
            >>> model.is_accessible_for_tier("trial")
            False
        """
        if not self.enabled:
            return False

        # tier_access is a list in Python after JSONB deserialization
        return user_tier in self.tier_access

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate total cost for a request.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Total cost in USD

        Example:
            >>> model = LLMModel(pricing_input=5.00, pricing_output=15.00)
            >>> model.calculate_cost(input_tokens=1000, output_tokens=500)
            12.5  # (1000/1000 * 5.00) + (500/1000 * 15.00)
        """
        input_cost = (input_tokens / 1000) * float(self.pricing_input or 0)
        output_cost = (output_tokens / 1000) * float(self.pricing_output or 0)
        return input_cost + output_cost

    def has_tag(self, tag: str) -> bool:
        """
        Check if model has a specific tag.

        Args:
            tag: Tag to check (e.g., "coding", "vision")

        Returns:
            True if tag is present, False otherwise

        Example:
            >>> model = LLMModel(tags=["coding", "reasoning"])
            >>> model.has_tag("coding")
            True
            >>> model.has_tag("vision")
            False
        """
        return tag in (self.tags or [])

    def to_dict(self, include_pricing: bool = True) -> Dict[str, Any]:
        """
        Convert to dictionary for API responses.

        Args:
            include_pricing: Whether to include pricing information

        Returns:
            Dictionary representation of the model

        Example:
            >>> model.to_dict(include_pricing=False)
            {
                'id': 1,
                'model_id': 'gpt-4o',
                'display_name': 'GPT-4o',
                ...
            }
        """
        result = {
            'id': self.id,
            'model_id': self.model_id,
            'litellm_model_id': self.litellm_model_id,
            'display_name': self.display_name,
            'provider': self.provider,
            'description': self.description,
            'tier_access': self.tier_access,
            'context_length': self.context_length,
            'max_output_tokens': self.max_output_tokens,
            'supports_streaming': self.supports_streaming,
            'supports_function_calling': self.supports_function_calling,
            'supports_vision': self.supports_vision,
            'enabled': self.enabled,
            'tags': self.tags or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_pricing:
            result.update({
                'pricing_input': float(self.pricing_input) if self.pricing_input else None,
                'pricing_output': float(self.pricing_output) if self.pricing_output else None,
            })

        return result

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<LLMModel("
            f"id={self.id}, "
            f"model_id='{self.model_id}', "
            f"provider='{self.provider}', "
            f"enabled={self.enabled}"
            f")>"
        )

    # ========================================================================
    # Class Methods (Query Helpers)
    # ========================================================================

    @classmethod
    def get_accessible_models(
        cls,
        session,
        user_tier: str,
        provider: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List['LLMModel']:
        """
        Get all models accessible for a given tier with optional filtering.

        Args:
            session: SQLAlchemy session
            user_tier: User's subscription tier
            provider: Optional provider filter (e.g., "openai")
            tags: Optional list of required tags

        Returns:
            List of accessible LLMModel instances

        Example:
            >>> models = LLMModel.get_accessible_models(
            ...     session,
            ...     user_tier="professional",
            ...     provider="openai"
            ... )
            >>> print([m.display_name for m in models])
            ['GPT-4o', 'GPT-4 Turbo']
        """
        query = session.query(cls).filter(
            cls.enabled == True,
            cls.tier_access.contains([user_tier])
        )

        if provider:
            query = query.filter(cls.provider == provider)

        if tags:
            for tag in tags:
                query = query.filter(cls.tags.contains([tag]))

        return query.order_by(cls.provider, cls.display_name).all()

    @classmethod
    def get_by_model_id(cls, session, model_id: str) -> Optional['LLMModel']:
        """
        Get model by frontend model_id.

        Args:
            session: SQLAlchemy session
            model_id: Frontend model ID (e.g., "gpt-4o")

        Returns:
            LLMModel instance or None if not found

        Example:
            >>> model = LLMModel.get_by_model_id(session, "gpt-4o")
            >>> print(model.litellm_model_id)
            'openai/gpt-4o'
        """
        return session.query(cls).filter_by(
            model_id=model_id,
            enabled=True
        ).first()

    @classmethod
    def translate_model_id(cls, session, model_id: str, user_tier: str) -> Optional[str]:
        """
        Translate frontend model ID to LiteLLM model ID with tier validation.

        Args:
            session: SQLAlchemy session
            model_id: Frontend model ID
            user_tier: User's subscription tier

        Returns:
            LiteLLM model ID if accessible, None otherwise

        Example:
            >>> litellm_id = LLMModel.translate_model_id(
            ...     session,
            ...     model_id="kimi/kimi-dev-72b",
            ...     user_tier="professional"
            ... )
            >>> print(litellm_id)
            'openrouter/moonshot/kimi-v1-128k'
        """
        model = cls.get_by_model_id(session, model_id)
        if model and model.is_accessible_for_tier(user_tier):
            return model.litellm_model_id
        return None

    @classmethod
    def get_providers(cls, session, user_tier: Optional[str] = None) -> List[str]:
        """
        Get list of unique providers, optionally filtered by tier access.

        Args:
            session: SQLAlchemy session
            user_tier: Optional tier filter

        Returns:
            List of provider names

        Example:
            >>> providers = LLMModel.get_providers(session, user_tier="trial")
            >>> print(providers)
            ['openai', 'openrouter']
        """
        query = session.query(cls.provider.distinct()).filter(cls.enabled == True)

        if user_tier:
            query = query.filter(cls.tier_access.contains([user_tier]))

        return [p[0] for p in query.order_by(cls.provider).all()]

    # ========================================================================
    # Validation Methods
    # ========================================================================

    @classmethod
    def validate_tier_access(cls, tier_access: List[str]) -> bool:
        """
        Validate tier_access list contains only valid tiers.

        Args:
            tier_access: List of tier strings

        Returns:
            True if all tiers are valid, False otherwise

        Example:
            >>> LLMModel.validate_tier_access(["trial", "starter"])
            True
            >>> LLMModel.validate_tier_access(["invalid_tier"])
            False
        """
        valid_tiers = {"trial", "starter", "professional", "enterprise"}
        return all(tier in valid_tiers for tier in tier_access)
