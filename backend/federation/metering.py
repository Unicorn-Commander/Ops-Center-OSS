"""
Federation cross-node usage tracking and billing.

Records usage events to PostgreSQL (federation_usage_log table), optionally
reports to Lago billing system, and supports batch reporting to a designated
billing node. Provides aggregated usage summaries by period.
"""


import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class FederationMeter:
    """Cross-node usage tracking with PostgreSQL persistence,
    optional Lago billing integration, and batch reporting to a
    designated billing node.

    Usage:
        meter = FederationMeter(db_pool)
        await meter.record_usage({
            "source_node_id": "uc-yoda",
            "target_node_id": "uc-peer1",
            "service_type": "llm",
            "model": "qwen3.5-27b",
            "tokens_input": 500,
            "tokens_output": 200,
            "latency_ms": 1200,
        })
    """

    def __init__(
        self,
        db_pool=None,
        *,
        lago_url: Optional[str] = None,
        lago_api_key: Optional[str] = None,
        billing_node_url: Optional[str] = None,
        billing_node_key: Optional[str] = None,
    ):
        self.db_pool = db_pool
        self.lago_url = lago_url
        self.lago_api_key = lago_api_key
        self.billing_node_url = billing_node_url
        self.billing_node_key = billing_node_key
        self._pending_batch: List[Dict[str, Any]] = []
        self._batch_max_size = 100

    # ------------------------------------------------------------------
    # Record usage
    # ------------------------------------------------------------------

    async def record_usage(self, usage_event: Dict[str, Any]) -> Dict[str, Any]:
        """Record a single usage event.

        Args:
            usage_event: Dict with keys:
                - source_node_id (str): Node that initiated the request
                - target_node_id (str): Node that served the request
                - service_type (str): e.g. "llm", "tts", "stt", "embeddings"
                - model (str, optional): Model identifier
                - event_type (str, optional): e.g. "inference", "proxy_request"
                - tokens_input (int, optional): Input tokens consumed
                - tokens_output (int, optional): Output tokens generated
                - latency_ms (float, optional): Request latency in milliseconds
                - cost_usd (float, optional): Estimated cost in USD
                - status (str, optional): "success" | "error" | "timeout"
                - metadata (dict, optional): Additional event metadata

        Returns:
            Dict with event_id and status.
        """
        event_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Normalize event
        event = {
            "event_id": event_id,
            "source_node_id": usage_event.get("source_node_id", "unknown"),
            "target_node_id": usage_event.get("target_node_id", "unknown"),
            "service_type": usage_event.get("service_type", "unknown"),
            "model": usage_event.get("model"),
            "event_type": usage_event.get("event_type", "inference"),
            "tokens_input": usage_event.get("tokens_input", 0),
            "tokens_output": usage_event.get("tokens_output", 0),
            "latency_ms": usage_event.get("latency_ms"),
            "cost_usd": usage_event.get("cost_usd", 0.0),
            "status": usage_event.get("status", "success"),
            "metadata": usage_event.get("metadata", {}),
            "timestamp": usage_event.get("timestamp", now.isoformat()),
            "created_at": now.isoformat(),
        }

        # Persist to PostgreSQL
        if self.db_pool:
            try:
                await self._insert_usage_event(event)
            except Exception as exc:
                logger.error("Failed to insert usage event: %s", exc)

        # Report to Lago (non-blocking)
        if self.lago_url and self.lago_api_key:
            try:
                await self._report_to_lago(event)
            except Exception as exc:
                logger.warning("Failed to report to Lago: %s", exc)

        # Buffer for batch reporting to billing node
        if self.billing_node_url:
            self._pending_batch.append(event)
            if len(self._pending_batch) >= self._batch_max_size:
                try:
                    await self.flush_batch()
                except Exception as exc:
                    logger.warning("Failed to flush batch to billing node: %s", exc)

        return {"event_id": event_id, "status": "recorded"}

    # ------------------------------------------------------------------
    # Database operations
    # ------------------------------------------------------------------

    async def _insert_usage_event(self, event: Dict[str, Any]) -> None:
        """Insert a usage event into the federation_usage_log table."""
        if not self.db_pool:
            return

        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO federation_usage_log (
                    id, source_node_id, target_node_id, service_type, model,
                    event_type, tokens_input, tokens_output, latency_ms,
                    cost_usd, status, metadata, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb, $13
                )
                """,
                event["event_id"],
                event["source_node_id"],
                event["target_node_id"],
                event["service_type"],
                event["model"],
                event["event_type"],
                event["tokens_input"],
                event["tokens_output"],
                event["latency_ms"],
                event["cost_usd"],
                event["status"],
                json.dumps(event.get("metadata", {})),
                datetime.fromisoformat(event["created_at"]).replace(tzinfo=None),
            )

    # ------------------------------------------------------------------
    # Lago integration
    # ------------------------------------------------------------------

    async def _report_to_lago(self, event: Dict[str, Any]) -> None:
        """Send a metering event to Lago for billing purposes."""
        if not self.lago_url or not self.lago_api_key:
            return

        lago_event = {
            "event": {
                "transaction_id": event["event_id"],
                "external_subscription_id": event["source_node_id"],
                "code": f"federation_{event['service_type']}",
                "timestamp": event["timestamp"],
                "properties": {
                    "model": event.get("model", ""),
                    "tokens_input": event.get("tokens_input", 0),
                    "tokens_output": event.get("tokens_output", 0),
                    "target_node": event.get("target_node_id", ""),
                    "cost_usd": str(event.get("cost_usd", 0.0)),
                },
            }
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.lago_url}/api/v1/events",
                json=lago_event,
                headers={
                    "Authorization": f"Bearer {self.lago_api_key}",
                    "Content-Type": "application/json",
                },
            )
            if response.status_code >= 400:
                logger.warning(
                    "Lago event submission failed: HTTP %d - %s",
                    response.status_code,
                    response.text[:200],
                )
            else:
                logger.debug(
                    "Lago metering event sent: %s (%s)",
                    event["event_id"],
                    event["service_type"],
                )

    # ------------------------------------------------------------------
    # Batch reporting to billing node
    # ------------------------------------------------------------------

    async def flush_batch(self) -> Dict[str, Any]:
        """Flush pending usage events to the designated billing node."""
        if not self._pending_batch:
            return {"sent": 0, "status": "empty"}

        batch = self._pending_batch.copy()
        self._pending_batch.clear()

        return await self.report_to_billing_node(batch)

    async def report_to_billing_node(
        self, batch: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """POST a batch of usage events to the billing node's report endpoint.

        Args:
            batch: List of usage event dicts.

        Returns:
            Dict with send count and status.
        """
        if not self.billing_node_url:
            logger.debug("No billing node configured, skipping batch report")
            return {"sent": 0, "status": "no_billing_node"}

        url = f"{self.billing_node_url.rstrip('/')}/api/v1/federation/usage/report"
        headers = {"Content-Type": "application/json"}
        if self.billing_node_key:
            headers["Authorization"] = f"Bearer {self.billing_node_key}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json={"events": batch, "count": len(batch)},
                    headers=headers,
                )
                response.raise_for_status()
                logger.info(
                    "Reported %d usage events to billing node %s",
                    len(batch),
                    self.billing_node_url,
                )
                return {"sent": len(batch), "status": "ok", "response": response.json()}
        except Exception as exc:
            logger.error(
                "Failed to report %d events to billing node: %s",
                len(batch),
                exc,
            )
            # Re-add failed batch for retry
            self._pending_batch.extend(batch)
            return {"sent": 0, "status": "error", "error": str(exc)}

    # ------------------------------------------------------------------
    # Usage summaries
    # ------------------------------------------------------------------

    async def get_usage_summary(
        self,
        *,
        node_id: Optional[str] = None,
        period: str = "day",
        service_type: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get aggregated usage summary grouped by service_type, model, and target_node.

        Args:
            node_id: Filter by source node ID (None for all nodes).
            period: Aggregation period - "hour", "day", "week", "month".
            service_type: Optional filter by service type.
            limit: Maximum number of result rows.

        Returns:
            Dict with summary data and aggregated totals.
        """
        if not self.db_pool:
            return {"summary": [], "totals": {}, "period": period, "error": "No database configured"}

        trunc_map = {
            "hour": "hour",
            "day": "day",
            "week": "week",
            "month": "month",
        }
        trunc = trunc_map.get(period, "day")

        conditions = []
        params: List[Any] = []

        if node_id:
            params.append(node_id)
            conditions.append(f"source_node_id = ${len(params)}")

        if service_type:
            params.append(service_type)
            conditions.append(f"service_type = ${len(params)}")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        params.append(limit)
        limit_param = f"${len(params)}"

        query = f"""
            SELECT
                date_trunc('{trunc}', created_at) AS period_start,
                service_type,
                model,
                target_node_id,
                COUNT(*) AS request_count,
                SUM(tokens_input) AS total_tokens_input,
                SUM(tokens_output) AS total_tokens_output,
                ROUND(AVG(latency_ms)::numeric, 2) AS avg_latency_ms,
                ROUND(SUM(COALESCE(cost_usd, 0))::numeric, 6) AS total_cost_usd,
                COUNT(*) FILTER (WHERE status = 'success') AS success_count,
                COUNT(*) FILTER (WHERE status = 'error') AS error_count
            FROM federation_usage_log
            {where_clause}
            GROUP BY period_start, service_type, model, target_node_id
            ORDER BY period_start DESC, request_count DESC
            LIMIT {limit_param}
        """

        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, *params)

            summary = []
            for row in rows:
                item = dict(row)
                # Convert datetime to ISO string
                if item.get("period_start"):
                    item["period_start"] = item["period_start"].isoformat()
                # Convert Decimal to float
                for key in ("avg_latency_ms", "total_cost_usd"):
                    if item.get(key) is not None:
                        item[key] = float(item[key])
                summary.append(item)

            # Compute totals
            totals_query = f"""
                SELECT
                    COUNT(*) AS total_requests,
                    SUM(tokens_input) AS total_tokens_input,
                    SUM(tokens_output) AS total_tokens_output,
                    ROUND(AVG(latency_ms)::numeric, 2) AS avg_latency_ms,
                    ROUND(SUM(COALESCE(cost_usd, 0))::numeric, 6) AS total_cost_usd,
                    COUNT(DISTINCT source_node_id) AS unique_source_nodes,
                    COUNT(DISTINCT target_node_id) AS unique_target_nodes,
                    COUNT(DISTINCT service_type) AS unique_service_types
                FROM federation_usage_log
                {where_clause}
            """
            # Remove the limit param for totals
            totals_params = params[:-1]

            async with self.db_pool.acquire() as conn:
                totals_row = await conn.fetchrow(totals_query, *totals_params)

            totals = {}
            if totals_row:
                totals = dict(totals_row)
                for key in ("avg_latency_ms", "total_cost_usd"):
                    if totals.get(key) is not None:
                        totals[key] = float(totals[key])

            return {
                "summary": summary,
                "totals": totals,
                "period": period,
                "node_id": node_id,
                "service_type": service_type,
            }

        except Exception as exc:
            logger.error("Failed to get usage summary: %s", exc)
            return {
                "summary": [],
                "totals": {},
                "period": period,
                "error": str(exc),
            }

    async def get_node_usage(
        self, node_id: str, *, days: int = 30
    ) -> Dict[str, Any]:
        """Get usage breakdown for a specific node over the last N days."""
        if not self.db_pool:
            return {"node_id": node_id, "usage": [], "error": "No database configured"}

        query = """
            SELECT
                service_type,
                COUNT(*) AS request_count,
                SUM(tokens_input) AS total_tokens_input,
                SUM(tokens_output) AS total_tokens_output,
                ROUND(AVG(latency_ms)::numeric, 2) AS avg_latency_ms,
                ROUND(SUM(COALESCE(cost_usd, 0))::numeric, 6) AS total_cost_usd,
                COUNT(*) FILTER (WHERE status = 'success') AS success_count,
                COUNT(*) FILTER (WHERE status = 'error') AS error_count
            FROM federation_usage_log
            WHERE (source_node_id = $1 OR target_node_id = $1)
              AND created_at >= NOW() - INTERVAL '%s days'
            GROUP BY service_type
            ORDER BY request_count DESC
        """ % days

        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, node_id)

            usage = []
            for row in rows:
                item = dict(row)
                for key in ("avg_latency_ms", "total_cost_usd"):
                    if item.get(key) is not None:
                        item[key] = float(item[key])
                usage.append(item)

            return {"node_id": node_id, "days": days, "usage": usage}

        except Exception as exc:
            logger.error("Failed to get node usage: %s", exc)
            return {"node_id": node_id, "usage": [], "error": str(exc)}
