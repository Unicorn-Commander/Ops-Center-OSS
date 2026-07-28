"""
Federated metering aggregation helpers.
"""


from collections import defaultdict
from datetime import datetime, timedelta, timezone
import uuid
from typing import Any, Dict, Optional


class MeteringAggregator:
    def __init__(self, db_pool=None):
        self.db_pool = db_pool

    async def record_usage(
        self,
        *,
        source_node_id: str,
        target_node_id: str,
        service_type: str,
        model: Optional[str] = None,
        tokens_in: int = 0,
        tokens_out: int = 0,
        duration_ms: Optional[int] = None,
        cost_usd: float = 0.0,
    ) -> Dict[str, Any]:
        payload = {
            "id": str(uuid.uuid4()),
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "service_type": service_type,
            "model": model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "duration_ms": duration_ms,
            "cost_usd": cost_usd,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO federation_usage (
                        id, source_node_id, target_node_id, service_type, model,
                        tokens_in, tokens_out, duration_ms, cost_usd, created_at
                    ) VALUES (
                        $1, $2, $3, $4::inference_service_type, $5, $6, $7, $8, $9, NOW()
                    )
                    """,
                    payload["id"],
                    source_node_id,
                    target_node_id,
                    service_type,
                    model,
                    tokens_in,
                    tokens_out,
                    duration_ms,
                    cost_usd,
                )
        return payload

    async def summarize_usage(self, hours: int = 24) -> Dict[str, Any]:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        if not self.db_pool:
            return {
                "window_hours": hours,
                "total_requests": 0,
                "total_cost_usd": 0.0,
                "by_service": [],
                "by_target_node": [],
            }

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT source_node_id, target_node_id, service_type::text AS service_type,
                       model, tokens_in, tokens_out, duration_ms, cost_usd, created_at
                FROM federation_usage
                WHERE created_at >= $1
                ORDER BY created_at DESC
                """,
                since.replace(tzinfo=None),
            )

        total_cost = 0.0
        by_service = defaultdict(lambda: {"requests": 0, "cost_usd": 0.0, "tokens_in": 0, "tokens_out": 0})
        by_target = defaultdict(lambda: {"requests": 0, "cost_usd": 0.0})

        for row in rows:
            item = dict(row)
            total_cost += float(item.get("cost_usd") or 0.0)
            service = by_service[item["service_type"]]
            service["requests"] += 1
            service["cost_usd"] += float(item.get("cost_usd") or 0.0)
            service["tokens_in"] += int(item.get("tokens_in") or 0)
            service["tokens_out"] += int(item.get("tokens_out") or 0)

            target = by_target[item["target_node_id"]]
            target["requests"] += 1
            target["cost_usd"] += float(item.get("cost_usd") or 0.0)

        return {
            "window_hours": hours,
            "total_requests": len(rows),
            "total_cost_usd": round(total_cost, 6),
            "by_service": [
                {"service_type": key, **value}
                for key, value in sorted(by_service.items())
            ],
            "by_target_node": [
                {"target_node_id": key, **value}
                for key, value in sorted(by_target.items())
            ],
        }
