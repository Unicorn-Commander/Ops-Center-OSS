"""
Federation Module for UC-Cloud Ops-Center
==========================================
Peer-to-peer federation system enabling multiple Unicorn Commander instances
to discover each other, share services, and route inference requests across nodes.

Components:
    NodeRegistry       - Redis + PostgreSQL backed node registration and discovery
    NodeAgent          - Background agent for registration, heartbeat, and service advertisement
    InferenceRouter    - Routes inference requests to the best available backend
    HardwareDetector   - Detects local hardware capabilities for service determination
    FederationMeter    - Cross-node usage tracking and billing
"""

import logging

logger = logging.getLogger(__name__)

# Import with graceful degradation so a broken submodule does not take down
# the entire federation package.

try:
    from .node_registry import NodeRegistry
except Exception as exc:
    logger.warning("Failed to import NodeRegistry: %s", exc)
    NodeRegistry = None  # type: ignore[assignment,misc]

try:
    from .inference_router import InferenceRouter
except Exception as exc:
    logger.warning("Failed to import InferenceRouter: %s", exc)
    InferenceRouter = None  # type: ignore[assignment,misc]

try:
    from .hardware_detector import HardwareDetector
except Exception as exc:
    logger.warning("Failed to import HardwareDetector: %s", exc)
    HardwareDetector = None  # type: ignore[assignment,misc]

try:
    from .metering import FederationMeter
except Exception as exc:
    logger.warning("Failed to import FederationMeter: %s", exc)
    FederationMeter = None  # type: ignore[assignment,misc]

try:
    from .node_agent import NodeAgent, get_node_agent
except Exception as exc:
    logger.warning("Failed to import NodeAgent: %s", exc)
    NodeAgent = None  # type: ignore[assignment,misc]
    get_node_agent = None  # type: ignore[assignment]

try:
    from .startup import start_federation_agent, stop_federation_agent
except Exception as exc:
    logger.warning("Failed to import federation startup hooks: %s", exc)
    start_federation_agent = None  # type: ignore[assignment]
    stop_federation_agent = None  # type: ignore[assignment]

try:
    from .credit_estimator import estimate_credits, SERVICE_CREDIT_COSTS
except ImportError:
    estimate_credits = None  # type: ignore[assignment]
    SERVICE_CREDIT_COSTS = None  # type: ignore[assignment]

try:
    from .auth import FederationAuth, get_federation_auth, verify_federation_request
except Exception as exc:
    logger.warning("Failed to import FederationAuth: %s", exc)
    FederationAuth = None  # type: ignore[assignment,misc]
    get_federation_auth = None  # type: ignore[assignment]
    verify_federation_request = None  # type: ignore[assignment]

try:
    from .cloud_provisioner import CloudProvisioner, get_cloud_provisioner
except Exception as exc:
    logger.warning("Failed to import CloudProvisioner: %s", exc)
    CloudProvisioner = None  # type: ignore[assignment,misc]
    get_cloud_provisioner = None  # type: ignore[assignment]

try:
    from .resilience import (
        CircuitBreaker,
        DistributedLock,
        RoutingAuditLog,
        get_circuit_breaker,
        get_routing_audit_log,
    )
except Exception as exc:
    logger.warning("Failed to import resilience module: %s", exc)
    CircuitBreaker = None  # type: ignore[assignment,misc]
    DistributedLock = None  # type: ignore[assignment,misc]
    RoutingAuditLog = None  # type: ignore[assignment,misc]
    get_circuit_breaker = None  # type: ignore[assignment]
    get_routing_audit_log = None  # type: ignore[assignment]

try:
    from .pipelines import (
        Pipeline,
        PipelineExecution,
        PipelineRegistry,
        PipelineStep,
        get_pipeline_registry,
    )
except Exception as exc:
    logger.warning("Failed to import Pipeline system: %s", exc)
    Pipeline = None  # type: ignore[assignment,misc]
    PipelineExecution = None  # type: ignore[assignment,misc]
    PipelineRegistry = None  # type: ignore[assignment,misc]
    PipelineStep = None  # type: ignore[assignment,misc]
    get_pipeline_registry = None  # type: ignore[assignment]

try:
    from .access_control import ServiceAccessControl, get_service_access_control
except Exception as exc:
    logger.warning("Failed to import ServiceAccessControl: %s", exc)
    ServiceAccessControl = None  # type: ignore[assignment,misc]
    get_service_access_control = None  # type: ignore[assignment]

__all__ = [
    "FederationAuth",
    "get_federation_auth",
    "verify_federation_request",
    "NodeRegistry",
    "NodeAgent",
    "InferenceRouter",
    "HardwareDetector",
    "FederationMeter",
    "CloudProvisioner",
    "estimate_credits",
    "SERVICE_CREDIT_COSTS",
    "get_node_agent",
    "get_cloud_provisioner",
    "start_federation_agent",
    "stop_federation_agent",
    "Pipeline",
    "PipelineExecution",
    "PipelineRegistry",
    "PipelineStep",
    "get_pipeline_registry",
    "ServiceAccessControl",
    "get_service_access_control",
    "CircuitBreaker",
    "DistributedLock",
    "RoutingAuditLog",
    "get_circuit_breaker",
    "get_routing_audit_log",
]
