"""
SQLAlchemy models for federation state in Ops-Center.
"""

from datetime import datetime
import enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from backend.database.models import Base


class FederationNodeStatus(enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


class FederationNodeRole(enum.Enum):
    BILLING = "billing"
    INFERENCE = "inference"
    GATEWAY = "gateway"


class InferenceServiceType(enum.Enum):
    LLM = "llm"
    TTS = "tts"
    STT = "stt"
    EMBEDDINGS = "embeddings"
    IMAGE_GEN = "image_gen"
    MUSIC_GEN = "music_gen"
    RERANKER = "reranker"
    AGENTS = "agents"
    SEARCH = "search"
    EXTRACTION = "extraction"


class FederationNode(Base):
    __tablename__ = "federation_nodes"

    id = Column(String(36), primary_key=True)
    node_id = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    endpoint_url = Column(String(512), nullable=False)
    auth_method = Column(String(50), nullable=False, default="jwt")
    auth_credential = Column(Text, nullable=True)
    hardware_profile = Column(JSON, nullable=True)
    status = Column(
        SQLEnum(FederationNodeStatus),
        nullable=False,
        default=FederationNodeStatus.OFFLINE,
        index=True,
    )
    roles = Column(JSON, nullable=True)
    region = Column(String(100), nullable=True)
    status_message = Column(Text, nullable=True)
    last_heartbeat = Column(DateTime, nullable=True, index=True)
    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    is_self = Column(Boolean, default=False, nullable=False)

    services = relationship(
        "FederationService",
        back_populates="node",
        cascade="all, delete-orphan",
    )


class FederationService(Base):
    __tablename__ = "federation_services"

    id = Column(String(36), primary_key=True)
    node_id = Column(
        String(36),
        ForeignKey("federation_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_type = Column(SQLEnum(InferenceServiceType), nullable=False, index=True)
    models = Column(JSON, nullable=True)
    endpoint_path = Column(String(512), nullable=True)
    status = Column(String(50), nullable=False, default="unknown", index=True)
    capabilities = Column(JSON, nullable=True)
    cold_start_seconds = Column(Integer, nullable=True)
    avg_latency_ms = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    node = relationship("FederationNode", back_populates="services")


class FederationUsage(Base):
    __tablename__ = "federation_usage"

    id = Column(String(36), primary_key=True)
    source_node_id = Column(String(255), nullable=False, index=True)
    target_node_id = Column(String(255), nullable=False, index=True)
    service_type = Column(SQLEnum(InferenceServiceType), nullable=False, index=True)
    model = Column(String(255), nullable=True)
    tokens_in = Column(Integer, nullable=True)
    tokens_out = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class FederationPeer(Base):
    __tablename__ = "federation_peers"

    id = Column(String(36), primary_key=True)
    local_node_id = Column(
        String(36),
        ForeignKey("federation_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    remote_node_id = Column(
        String(36),
        ForeignKey("federation_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trust_level = Column(String(50), nullable=False, default="read_only")
    established_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_verified = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # --- Phase 1: per-peer trust mode + service ACL fields ---
    # See Unicorn-Ecosystem/FEDERATION_TRUST_MODES.md for the full design.
    # Defaults preserve current full-mesh behavior.
    trust_mode = Column(String(50), nullable=False, default="full")
    publish = Column(JSON, nullable=False, default=list)
    consume = Column(JSON, nullable=False, default=list)
    capability_token = Column(Text, nullable=True)
    authority_for = Column(JSON, nullable=False, default=list)
    consumer_of = Column(JSON, nullable=False, default=list)


class FederationAuthority(Base):
    __tablename__ = "federation_authorities"

    id = Column(Integer, primary_key=True)
    resource_type = Column(String(100), nullable=False, index=True)
    node_id = Column(
        String(36),
        ForeignKey("federation_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_primary = Column(Boolean, nullable=False, default=True)
    since = Column(DateTime, default=datetime.utcnow, nullable=False)
    extra_metadata = Column("metadata", JSON, nullable=False, default=dict)


