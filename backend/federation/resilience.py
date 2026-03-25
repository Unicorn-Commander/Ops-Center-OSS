"""
Federation Resilience — Circuit Breakers, Distributed Locks, Audit Trail

1. CircuitBreaker: Prevents cascading failures when peer nodes go down.
   After N consecutive failures to a peer, stop trying for a cooldown period.

2. DistributedLock: Redis-based lock for cloud GPU provisioning.
   Prevents multiple concurrent provisioning requests from spinning up
   duplicate instances.

3. RoutingAuditLog: Records every routing decision for debugging and compliance.
   Stored in PostgreSQL for queryability.
"""

import json
import time
import uuid
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger("federation.resilience")


class CircuitState(Enum):
    CLOSED = "closed"      # normal — requests flow through
    OPEN = "open"          # tripped — requests blocked
    HALF_OPEN = "half_open"  # testing — one request allowed through


class CircuitBreaker:
    """Per-peer circuit breaker.

    Tracks consecutive failures to each peer node. After `failure_threshold`
    failures, the circuit opens and all requests to that peer are blocked
    for `cooldown_seconds`. After cooldown, one request is allowed through
    (half-open). If it succeeds, circuit closes. If it fails, circuit reopens.
    """

    def __init__(self, failure_threshold: int = 3, cooldown_seconds: int = 30):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        # Per-peer state: {node_id: {state, failures, last_failure, last_success}}
        self._peers: Dict[str, Dict[str, Any]] = {}

    def can_request(self, node_id: str) -> bool:
        """Check if requests to this peer are allowed."""
        peer = self._peers.get(node_id)
        if peer is None:
            return True

        state = peer["state"]
        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.OPEN:
            # Check if cooldown has passed
            if time.time() - peer["last_failure"] >= self.cooldown_seconds:
                peer["state"] = CircuitState.HALF_OPEN
                logger.info(f"Circuit half-open for {node_id}")
                return True
            return False
        elif state == CircuitState.HALF_OPEN:
            return True  # allow one test request
        return False

    def record_success(self, node_id: str):
        """Record a successful request to a peer."""
        self._peers[node_id] = {
            "state": CircuitState.CLOSED,
            "failures": 0,
            "last_failure": 0,
            "last_success": time.time(),
        }

    def record_failure(self, node_id: str):
        """Record a failed request to a peer."""
        peer = self._peers.setdefault(node_id, {
            "state": CircuitState.CLOSED,
            "failures": 0,
            "last_failure": 0,
            "last_success": 0,
        })

        peer["failures"] += 1
        peer["last_failure"] = time.time()

        if peer["state"] == CircuitState.HALF_OPEN:
            # Test request failed — reopen circuit
            peer["state"] = CircuitState.OPEN
            logger.warning(f"Circuit reopened for {node_id} (half-open test failed)")
        elif peer["failures"] >= self.failure_threshold:
            peer["state"] = CircuitState.OPEN
            logger.warning(f"Circuit opened for {node_id} after {peer['failures']} consecutive failures")

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """Get circuit breaker status for all peers."""
        return {
            node_id: {
                "state": peer["state"].value,
                "failures": peer["failures"],
                "last_failure": peer["last_failure"],
                "last_success": peer["last_success"],
            }
            for node_id, peer in self._peers.items()
        }


class DistributedLock:
    """Redis-based distributed lock for preventing double-provisioning."""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.lock_ttl = 300  # 5 minutes max lock hold

    async def acquire(self, lock_name: str, holder_id: str = None) -> bool:
        """Try to acquire a lock. Returns True if acquired."""
        holder_id = holder_id or uuid.uuid4().hex[:8]
        key = f"federation:lock:{lock_name}"

        # SET NX with TTL — atomic acquire
        acquired = await self.redis.set(key, holder_id, nx=True, ex=self.lock_ttl)
        if acquired:
            logger.debug(f"Lock acquired: {lock_name} by {holder_id}")
        return bool(acquired)

    async def release(self, lock_name: str, holder_id: str = None):
        """Release a lock. Only releases if held by the same holder."""
        key = f"federation:lock:{lock_name}"
        if holder_id:
            # Only release if we hold it
            current = await self.redis.get(key)
            if current and current.decode() == holder_id:
                await self.redis.delete(key)
                logger.debug(f"Lock released: {lock_name} by {holder_id}")
        else:
            await self.redis.delete(key)

    async def is_locked(self, lock_name: str) -> bool:
        """Check if a lock is currently held."""
        key = f"federation:lock:{lock_name}"
        return bool(await self.redis.exists(key))


class RoutingAuditLog:
    """Records federation routing decisions for debugging and compliance.

    Every time the inference router makes a decision, it logs:
    - What was requested (service type, model, user tier)
    - What candidates were considered
    - What constraints filtered out candidates
    - What was selected and why (scoring details)
    - The outcome (success, failure, latency)
    """

    def __init__(self, db_pool=None):
        self.db_pool = db_pool
        self._buffer = []  # buffer for batch inserts
        self._buffer_limit = 50

    async def log_decision(
        self,
        request_id: str,
        service_type: str,
        model: Optional[str],
        user_id: Optional[str],
        user_tier: Optional[str],
        candidates_found: int,
        candidates_after_constraints: int,
        constraints_applied: Optional[Dict] = None,
        selected_target: Optional[str] = None,
        selected_node_id: Optional[str] = None,
        selected_reason: Optional[str] = None,
        routing_score: Optional[float] = None,
        latency_ms: Optional[int] = None,
        outcome: str = "routed",  # routed, no_capacity, error, provisioning
        error_message: Optional[str] = None,
    ):
        """Log a routing decision."""
        entry = {
            "id": uuid.uuid4().hex,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "service_type": service_type,
            "model": model,
            "user_id": user_id,
            "user_tier": user_tier,
            "candidates_found": candidates_found,
            "candidates_after_constraints": candidates_after_constraints,
            "constraints": constraints_applied,
            "selected_target": selected_target,
            "selected_node_id": selected_node_id,
            "selected_reason": selected_reason,
            "routing_score": routing_score,
            "latency_ms": latency_ms,
            "outcome": outcome,
            "error": error_message,
        }

        self._buffer.append(entry)

        # Log important decisions
        if outcome in ("no_capacity", "error", "provisioning"):
            logger.warning(f"Routing [{outcome}] {service_type}/{model} for {user_tier}: {selected_reason or error_message}")
        else:
            logger.info(f"Routing [{outcome}] {service_type}/{model} -> {selected_target}:{selected_node_id} (score={routing_score})")

        # Flush if buffer is full
        if len(self._buffer) >= self._buffer_limit:
            await self.flush()

    async def flush(self):
        """Flush buffered entries to PostgreSQL."""
        if not self._buffer or not self.db_pool:
            self._buffer.clear()
            return

        entries = self._buffer.copy()
        self._buffer.clear()

        try:
            async with self.db_pool.acquire() as conn:
                await conn.executemany("""
                    INSERT INTO federation_routing_audit (
                        id, request_id, timestamp, service_type, model,
                        user_id, user_tier, candidates_found, candidates_after_constraints,
                        constraints, selected_target, selected_node_id, selected_reason,
                        routing_score, latency_ms, outcome, error
                    ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)
                """, [
                    (
                        e["id"], e["request_id"], e["timestamp"], e["service_type"], e["model"],
                        e["user_id"], e["user_tier"], e["candidates_found"], e["candidates_after_constraints"],
                        json.dumps(e["constraints"]) if e["constraints"] else None,
                        e["selected_target"], e["selected_node_id"], e["selected_reason"],
                        e["routing_score"], e["latency_ms"], e["outcome"], e["error"],
                    )
                    for e in entries
                ])
        except Exception as ex:
            logger.error(f"Failed to flush routing audit log: {ex}")

    async def query(
        self,
        service_type: Optional[str] = None,
        outcome: Optional[str] = None,
        user_tier: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        """Query routing audit log."""
        if not self.db_pool:
            return []

        conditions = []
        params = []
        idx = 1

        if service_type:
            conditions.append(f"service_type = ${idx}")
            params.append(service_type)
            idx += 1
        if outcome:
            conditions.append(f"outcome = ${idx}")
            params.append(outcome)
            idx += 1
        if user_tier:
            conditions.append(f"user_tier = ${idx}")
            params.append(user_tier)
            idx += 1

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    f"SELECT * FROM federation_routing_audit {where} ORDER BY timestamp DESC LIMIT ${idx}",
                    *params, limit
                )
                return [dict(r) for r in rows]
        except Exception as ex:
            logger.error(f"Audit query failed: {ex}")
            return []


# Module singletons
_circuit_breaker: Optional[CircuitBreaker] = None
_audit_log: Optional[RoutingAuditLog] = None


def get_circuit_breaker() -> CircuitBreaker:
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = CircuitBreaker()
    return _circuit_breaker


def get_routing_audit_log(db_pool=None) -> RoutingAuditLog:
    global _audit_log
    if _audit_log is None:
        _audit_log = RoutingAuditLog(db_pool)
    elif db_pool and not _audit_log.db_pool:
        _audit_log.db_pool = db_pool
    return _audit_log
