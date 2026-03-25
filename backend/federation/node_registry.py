"""
Federation node registry backed by Redis and PostgreSQL.
"""


from datetime import datetime, timezone
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

HEARTBEAT_TTL_SECONDS = 90
DEGRADED_AFTER_SECONDS = 90
OFFLINE_AFTER_SECONDS = 300


class NodeRegistry:
    def __init__(self, redis_client: Optional[aioredis.Redis] = None, db_pool=None):
        self.redis = redis_client
        self.db_pool = db_pool

    async def register_node(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        node_id = node_data["node_id"]
        services = node_data.get("services", [])
        now = datetime.now(timezone.utc)
        node_uuid = await self._upsert_node(node_data, now)
        await self.update_services(node_id, services, node_uuid=node_uuid)
        await self._cache_node(
            node_id=node_id,
            payload={
                **node_data,
                "status": node_data.get("status", "online"),
                "registered_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "last_heartbeat": now.isoformat(),
            },
        )
        await self.heartbeat(
            node_id,
            {
                "load": node_data.get("load", {}),
                "hardware_profile": node_data.get("hardware_profile", {}),
                "services": services,
            },
        )
        return {
            "node_id": node_id,
            "status": "online",
            "registered_at": now.isoformat(),
            "services_registered": len(services),
        }

    async def heartbeat(self, node_id: str, heartbeat: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        node = await self.get_node(node_id)
        if not node:
            raise ValueError(f"Unknown federation node: {node_id}")

        services = heartbeat.get("services")
        if services is not None:
            await self.update_services(node_id, services)

        if self.redis:
            await self.redis.set(
                f"federation:heartbeat:{node_id}",
                json.dumps(
                    {
                        "ts": time.time(),
                        "load": heartbeat.get("load", {}),
                        "hardware_profile": heartbeat.get("hardware_profile", {}),
                        "services": services or [],
                    }
                ),
                ex=HEARTBEAT_TTL_SECONDS,
            )
            await self.redis.hset(
                f"federation:node:{node_id}",
                mapping={
                    "status": "online",
                    "last_heartbeat": now.isoformat(),
                    "updated_at": now.isoformat(),
                },
            )

        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE federation_nodes
                    SET status = 'online',
                        last_heartbeat = $2,
                        hardware_profile = COALESCE($3::jsonb, hardware_profile),
                        updated_at = $2
                    WHERE node_id = $1
                    """,
                    node_id,
                    now.replace(tzinfo=None),
                    self._json_or_none(heartbeat.get("hardware_profile")),
                )

        return {"node_id": node_id, "status": "online", "last_heartbeat": now.isoformat()}

    async def deregister_node(self, node_id: str) -> bool:
        if self.redis:
            await self.redis.delete(f"federation:node:{node_id}")
            await self.redis.delete(f"federation:heartbeat:{node_id}")
            await self._remove_cached_services(node_id)

        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE federation_nodes
                    SET status = 'offline', updated_at = NOW()
                    WHERE node_id = $1
                    """,
                    node_id,
                )
        return True

    async def get_nodes(self, include_offline: bool = True) -> List[Dict[str, Any]]:
        nodes: List[Dict[str, Any]] = []
        if self.db_pool:
            query = """
                SELECT node_id, display_name, endpoint_url, auth_method, hardware_profile,
                       status::text AS status, roles, region, status_message, last_heartbeat,
                       registered_at, updated_at, is_self
                FROM federation_nodes
            """
            if not include_offline:
                query += " WHERE status != 'offline'"
            query += " ORDER BY display_name, node_id"
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query)
            nodes = [self._normalize_db_node(dict(row)) for row in rows]
        elif self.redis:
            async for key in self.redis.scan_iter(match="federation:node:*"):
                raw = await self.redis.hgetall(key)
                if raw:
                    nodes.append(self._normalize_cached_node(raw))

        for node in nodes:
            node["status"] = await self._live_status(node["node_id"], node.get("status"))

        if not include_offline:
            nodes = [node for node in nodes if node["status"] != "offline"]
        return nodes

    async def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT node_id, display_name, endpoint_url, auth_method, auth_credential,
                           hardware_profile, status::text AS status, roles, region,
                           status_message, last_heartbeat, registered_at, updated_at, is_self
                    FROM federation_nodes
                    WHERE node_id = $1
                    """,
                    node_id,
                )
            if row:
                node = self._normalize_db_node(dict(row))
                node["status"] = await self._live_status(node_id, node.get("status"))
                node["services"] = await self.get_service_catalog(node_id=node_id)
                return node

        if self.redis:
            raw = await self.redis.hgetall(f"federation:node:{node_id}")
            if raw:
                node = self._normalize_cached_node(raw)
                node["status"] = await self._live_status(node_id, node.get("status"))
                node["services"] = await self.get_service_catalog(node_id=node_id)
                return node
        return None

    async def update_services(
        self,
        node_id: str,
        services: List[Dict[str, Any]],
        *,
        node_uuid: Optional[str] = None,
    ) -> None:
        if self.redis:
            await self._remove_cached_services(node_id)
            now_score = time.time()
            for service in services:
                entry = {
                    "node_id": node_id,
                    "service_type": service["service_type"],
                    "models": service.get("models", []),
                    "endpoint_path": service.get("endpoint_path", ""),
                    "status": service.get("status", "unknown"),
                    "capabilities": service.get("capabilities", {}),
                    "avg_latency_ms": service.get("avg_latency_ms"),
                    "cold_start_seconds": service.get("cold_start_seconds"),
                    "cost_usd": service.get("cost_usd", 0.0),
                }
                await self.redis.zadd(
                    "federation:services",
                    {json.dumps(entry, sort_keys=True): now_score},
                )

        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                if node_uuid is None:
                    node_uuid = await conn.fetchval(
                        "SELECT id FROM federation_nodes WHERE node_id = $1",
                        node_id,
                    )
                if node_uuid is None:
                    raise ValueError(f"Cannot update services for unknown node: {node_id}")

                await conn.execute("DELETE FROM federation_services WHERE node_id = $1", node_uuid)
                for service in services:
                    await conn.execute(
                        """
                        INSERT INTO federation_services (
                            id, node_id, service_type, models, endpoint_path, status,
                            capabilities, cold_start_seconds, avg_latency_ms, cost_usd, updated_at
                        ) VALUES (
                            $1, $2, $3::inference_service_type, $4::jsonb, $5, $6, $7::jsonb, $8, $9, $10, NOW()
                        )
                        """,
                        str(uuid.uuid4()),
                        node_uuid,
                        service["service_type"],
                        json.dumps(service.get("models", [])),
                        service.get("endpoint_path"),
                        service.get("status", "unknown"),
                        json.dumps(service.get("capabilities", {})),
                        service.get("cold_start_seconds"),
                        service.get("avg_latency_ms"),
                        service.get("cost_usd"),
                    )

    async def get_service_catalog(
        self,
        service_type: Optional[str] = None,
        *,
        node_id: Optional[str] = None,
        include_offline: bool = False,
    ) -> List[Dict[str, Any]]:
        if self.db_pool:
            conditions = []
            params: List[Any] = []
            if service_type:
                params.append(service_type)
                conditions.append(f"fs.service_type = ${len(params)}::inference_service_type")
            if node_id:
                params.append(node_id)
                conditions.append(f"fn.node_id = ${len(params)}")

            query = """
                SELECT fn.node_id, fn.display_name, fn.endpoint_url, fn.region,
                       fs.service_type::text AS service_type, fs.models, fs.endpoint_path,
                       fs.status, fs.capabilities, fs.cold_start_seconds, fs.avg_latency_ms,
                       fs.cost_usd, fn.last_heartbeat
                FROM federation_services fs
                JOIN federation_nodes fn ON fn.id = fs.node_id
            """
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY fn.display_name, fs.service_type"
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, *params)

            catalog = []
            for row in rows:
                item = dict(row)
                item["models"] = item.get("models") or []
                item["capabilities"] = item.get("capabilities") or {}
                item["last_heartbeat"] = self._iso(item.get("last_heartbeat"))
                item["node_status"] = await self._live_status(item["node_id"], "offline")
                if include_offline or item["node_status"] != "offline":
                    catalog.append(item)
            return catalog

        if not self.redis:
            return []

        entries = await self.redis.zrange("federation:services", 0, -1)
        catalog = []
        for raw in entries:
            item = json.loads(raw)
            if service_type and item.get("service_type") != service_type:
                continue
            if node_id and item.get("node_id") != node_id:
                continue
            status = await self._live_status(item["node_id"], item.get("status"))
            if not include_offline and status == "offline":
                continue
            item["node_status"] = status
            catalog.append(item)
        return catalog

    async def get_topology(self) -> Dict[str, Any]:
        nodes = await self.get_nodes(include_offline=True)
        services = await self.get_service_catalog()
        return {
            "nodes": nodes,
            "edges": [],
            "service_count": len(services),
            "online_nodes": len([node for node in nodes if node["status"] == "online"]),
        }

    async def mark_stale_nodes(self) -> List[Dict[str, Any]]:
        nodes = await self.get_nodes(include_offline=True)
        changes = []
        for node in nodes:
            new_status = await self._live_status(node["node_id"], node.get("status"))
            if new_status != node.get("status") and self.db_pool:
                async with self.db_pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE federation_nodes SET status = $2::federation_node_status, updated_at = NOW() WHERE node_id = $1",
                        node["node_id"],
                        new_status,
                    )
                changes.append(
                    {
                        "node_id": node["node_id"],
                        "previous_status": node.get("status"),
                        "new_status": new_status,
                    }
                )
        return changes

    async def _upsert_node(self, node_data: Dict[str, Any], now: datetime) -> str:
        node_uuid = str(uuid.uuid4())
        if not self.db_pool:
            return node_uuid

        async with self.db_pool.acquire() as conn:
            existing_id = await conn.fetchval(
                "SELECT id FROM federation_nodes WHERE node_id = $1",
                node_data["node_id"],
            )
            if existing_id:
                node_uuid = existing_id
            await conn.execute(
                """
                INSERT INTO federation_nodes (
                    id, node_id, display_name, endpoint_url, auth_method, auth_credential,
                    hardware_profile, status, roles, region, status_message,
                    last_heartbeat, registered_at, updated_at, is_self
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7::jsonb, $8::federation_node_status,
                    $9::jsonb, $10, $11, $12, $13, $14, $15
                )
                ON CONFLICT (node_id) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    endpoint_url = EXCLUDED.endpoint_url,
                    auth_method = EXCLUDED.auth_method,
                    auth_credential = EXCLUDED.auth_credential,
                    hardware_profile = EXCLUDED.hardware_profile,
                    status = EXCLUDED.status,
                    roles = EXCLUDED.roles,
                    region = EXCLUDED.region,
                    status_message = EXCLUDED.status_message,
                    last_heartbeat = EXCLUDED.last_heartbeat,
                    updated_at = EXCLUDED.updated_at,
                    is_self = EXCLUDED.is_self
                """,
                node_uuid,
                node_data["node_id"],
                node_data.get("display_name", node_data["node_id"]),
                node_data["endpoint_url"],
                node_data.get("auth_method", "jwt"),
                node_data.get("auth_credential"),
                json.dumps(node_data.get("hardware_profile", {})),
                node_data.get("status", "online"),
                json.dumps(node_data.get("roles", ["inference"])),
                node_data.get("region"),
                node_data.get("status_message"),
                now.replace(tzinfo=None),
                now.replace(tzinfo=None),
                now.replace(tzinfo=None),
                node_data.get("is_self", False),
            )
        return node_uuid

    async def _cache_node(self, node_id: str, payload: Dict[str, Any]) -> None:
        if not self.redis:
            return
        cached = {}
        for key, value in payload.items():
            if isinstance(value, (dict, list)):
                cached[key] = json.dumps(value)
            elif value is None:
                cached[key] = ""
            else:
                cached[key] = str(value)
        await self.redis.hset(f"federation:node:{node_id}", mapping=cached)

    async def _remove_cached_services(self, node_id: str) -> None:
        if not self.redis:
            return
        members = await self.redis.zrange("federation:services", 0, -1)
        for raw in members:
            item = json.loads(raw)
            if item.get("node_id") == node_id:
                await self.redis.zrem("federation:services", raw)

    async def _live_status(self, node_id: str, fallback: Optional[str]) -> str:
        if not self.redis:
            return fallback or "offline"
        raw = await self.redis.get(f"federation:heartbeat:{node_id}")
        if not raw:
            return "offline"
        payload = json.loads(raw)
        age = time.time() - payload.get("ts", 0)
        if age > OFFLINE_AFTER_SECONDS:
            return "offline"
        if age > DEGRADED_AFTER_SECONDS:
            return "degraded"
        return "online"

    @staticmethod
    def _normalize_db_node(node: Dict[str, Any]) -> Dict[str, Any]:
        node["hardware_profile"] = node.get("hardware_profile") or {}
        node["roles"] = node.get("roles") or []
        node["last_heartbeat"] = NodeRegistry._iso(node.get("last_heartbeat"))
        node["registered_at"] = NodeRegistry._iso(node.get("registered_at"))
        node["updated_at"] = NodeRegistry._iso(node.get("updated_at"))
        return node

    @staticmethod
    def _normalize_cached_node(node: Dict[str, Any]) -> Dict[str, Any]:
        parsed = dict(node)
        for field in ("hardware_profile", "roles", "services", "load"):
            value = parsed.get(field)
            if isinstance(value, str) and value:
                try:
                    parsed[field] = json.loads(value)
                except json.JSONDecodeError:
                    pass
        return parsed

    @staticmethod
    def _json_or_none(value: Any) -> Optional[str]:
        if value is None:
            return None
        return json.dumps(value)

    @staticmethod
    def _iso(value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.replace(tzinfo=timezone.utc).isoformat()
        return str(value)
