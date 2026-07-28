"""
Kuzu Graph Database Client for Colonel.

Stores entity relationships: Server → runs → Containers, Services, etc.
Kuzu is embedded (no external server), installs via `pip install kuzu`.

Graph is stored at /app/data/colonel_graph/ and auto-populates from Docker.
"""

import logging
import os
from typing import Optional, List, Dict, Any

logger = logging.getLogger("colonel.memory.kuzu")

KUZU_DB_PATH = os.getenv("COLONEL_GRAPH_PATH", "/app/data/colonel_graph")


class ColonelGraphClient:
    """Embedded Kuzu graph database for Colonel entity relationships."""

    def __init__(self):
        self._db = None
        self._conn = None
        self._available = False
        self._initialize()

    def _initialize(self):
        """Initialize Kuzu database and schema."""
        try:
            import kuzu
        except ImportError:
            logger.info("kuzu not installed — graph memory disabled. Install with: pip install kuzu")
            return

        try:
            # Ensure parent dir exists
            os.makedirs(os.path.dirname(KUZU_DB_PATH), exist_ok=True)
            # Kuzu 0.11+ expects to create the path itself; if an empty dir exists, remove it
            if os.path.isdir(KUZU_DB_PATH) and not os.listdir(KUZU_DB_PATH):
                os.rmdir(KUZU_DB_PATH)
            self._db = kuzu.Database(KUZU_DB_PATH)
            self._conn = kuzu.Connection(self._db)

            # Create schema (idempotent)
            self._conn.execute(
                "CREATE NODE TABLE IF NOT EXISTS Server("
                "  name STRING, hostname STRING, os STRING, cpu_cores INT64, ram_gb DOUBLE,"
                "  PRIMARY KEY (name))"
            )
            self._conn.execute(
                "CREATE NODE TABLE IF NOT EXISTS Container("
                "  name STRING, image STRING, status STRING,"
                "  PRIMARY KEY (name))"
            )
            self._conn.execute(
                "CREATE NODE TABLE IF NOT EXISTS Service("
                "  name STRING, url STRING, port INT64, healthy BOOLEAN,"
                "  PRIMARY KEY (name))"
            )
            self._conn.execute(
                "CREATE NODE TABLE IF NOT EXISTS User("
                "  id STRING, email STRING, role STRING,"
                "  PRIMARY KEY (id))"
            )

            # Relationships
            self._conn.execute(
                "CREATE REL TABLE IF NOT EXISTS RUNS_ON(FROM Container TO Server)"
            )
            self._conn.execute(
                "CREATE REL TABLE IF NOT EXISTS PROVIDES(FROM Container TO Service)"
            )
            self._conn.execute(
                "CREATE REL TABLE IF NOT EXISTS DEPENDS_ON(FROM Service TO Service)"
            )
            self._conn.execute(
                "CREATE REL TABLE IF NOT EXISTS INTERACTS_WITH(FROM User TO Service)"
            )

            self._available = True
            logger.info(f"Kuzu graph initialized at {KUZU_DB_PATH}")
        except Exception as e:
            logger.warning(f"Failed to initialize Kuzu: {e}")

    @property
    def available(self) -> bool:
        return self._available

    def populate_from_docker(self):
        """Auto-populate graph with current Docker containers."""
        if not self._available:
            return

        try:
            import docker
            import platform

            client = docker.from_env()

            # Upsert server node
            hostname = platform.node()
            self._conn.execute(
                "MERGE (s:Server {name: $name}) SET s.hostname = $hostname, s.os = $os",
                {"name": hostname, "hostname": hostname, "os": f"{platform.system()} {platform.release()}"},
            )

            # Upsert container nodes
            for c in client.containers.list():
                image = c.image.tags[0] if c.image.tags else c.image.short_id
                self._conn.execute(
                    "MERGE (c:Container {name: $name}) SET c.image = $image, c.status = $status",
                    {"name": c.name, "image": image, "status": c.status},
                )
                # Create RUNS_ON relationship
                self._conn.execute(
                    "MATCH (c:Container {name: $cname}), (s:Server {name: $sname}) "
                    "MERGE (c)-[:RUNS_ON]->(s)",
                    {"cname": c.name, "sname": hostname},
                )

            logger.info(f"Graph populated with {len(client.containers.list())} containers on {hostname}")
        except Exception as e:
            logger.warning(f"Failed to populate graph from Docker: {e}")

    def query_context(self, query_text: str) -> List[str]:
        """
        Find relevant graph context for a user query.
        Returns a list of context strings to inject into the system prompt.
        """
        if not self._available:
            return []

        context = []
        text_lower = query_text.lower()

        try:
            # If asking about containers
            if any(kw in text_lower for kw in ["container", "docker", "service", "running"]):
                result = self._conn.execute(
                    "MATCH (c:Container)-[:RUNS_ON]->(s:Server) "
                    "RETURN c.name, c.image, c.status, s.name LIMIT 20"
                )
                rows = []
                while result.has_next():
                    rows.append(result.get_next())
                if rows:
                    ctx = "Known containers: " + ", ".join(
                        f"{r[0]} ({r[1]}, {r[2]})" for r in rows
                    )
                    context.append(ctx)

            # If asking about a specific container/service by name
            for word in query_text.split():
                if len(word) > 3:
                    result = self._conn.execute(
                        "MATCH (c:Container) WHERE c.name CONTAINS $term "
                        "RETURN c.name, c.image, c.status LIMIT 5",
                        {"term": word.lower()},
                    )
                    rows = []
                    while result.has_next():
                        rows.append(result.get_next())
                    for r in rows:
                        context.append(f"Container '{r[0]}' runs image {r[1]}, status: {r[2]}")

        except Exception as e:
            logger.debug(f"Graph query error: {e}")

        # Deduplicate
        return list(dict.fromkeys(context))

    def add_entity(self, entity_type: str, properties: Dict[str, Any]):
        """Add or update an entity in the graph."""
        if not self._available:
            return

        try:
            if entity_type == "container":
                self._conn.execute(
                    "MERGE (c:Container {name: $name}) SET c.image = $image, c.status = $status",
                    properties,
                )
            elif entity_type == "service":
                self._conn.execute(
                    "MERGE (s:Service {name: $name}) SET s.url = $url, s.port = $port",
                    properties,
                )
            elif entity_type == "user":
                self._conn.execute(
                    "MERGE (u:User {id: $id}) SET u.email = $email, u.role = $role",
                    properties,
                )
        except Exception as e:
            logger.warning(f"Failed to add entity: {e}")

    def get_stats(self) -> Dict[str, int]:
        """Get counts of nodes and relationships."""
        if not self._available:
            return {"available": False}

        stats = {"available": True}
        for table in ["Server", "Container", "Service", "User"]:
            try:
                result = self._conn.execute(f"MATCH (n:{table}) RETURN count(n)")
                if result.has_next():
                    stats[table.lower() + "_count"] = result.get_next()[0]
            except Exception:
                stats[table.lower() + "_count"] = 0

        return stats
