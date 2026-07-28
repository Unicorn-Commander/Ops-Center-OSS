"""
Versioned, idempotent core-schema migration runner for ops-center.

WHY THIS EXISTS
---------------
ops-center runs on two live nodes (bigboy=dev, commander=LIVE Stripe customer)
and we deploy CODE via cherry-pick, which copies code but NOT schema. The two
`unicorn_db` databases drifted (133 column diffs across 99 shared tables), so a
feature written against one node's shape can hit a different shape on the other
and 500 silently (this happened with `credit_packages`). This runner makes the
CORE billing/identity/federation tables converge BY CONSTRUCTION: both deploy
branches run the same versioned `migrations/core/*.sql` on startup.

CONTRACT (mirrors the proven `ensure_feature_tables.sql` self-heal in server.py)
--------------------------------------------------------------------------------
* Every migration is IDEMPOTENT: `CREATE ... IF NOT EXISTS`,
  `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, `INSERT ... ON CONFLICT DO NOTHING`,
  `CREATE OR REPLACE`. It must be safe to run on every boot. NEVER DROP/TRUNCATE.
* Applied statement-by-statement (respecting `$$` dollar-quoted bodies) so one
  benign failure does not abort the rest — asyncpg otherwise runs a multi-stmt
  string as a single implicit transaction.
* NON-FATAL: a failure logs loudly but must never block startup.
* A `schema_migrations` tracking table records which versions/checksums ran. A
  file is (re)applied when it is new OR its checksum changed (an edited migration
  re-runs — safe, because every statement is idempotent).
* DANGEROUS migrations (PK / identity-column TYPE changes — e.g. uuid<->int)
  do NOT live here and are NEVER auto-applied. They require explicit sign-off and
  are run out-of-band from `migrations/core/pending_signoff/`.
"""
import hashlib
import logging
import os

logger = logging.getLogger(__name__)

CORE_DIR = os.path.join(os.path.dirname(__file__), "migrations", "core")


def split_sql_statements(sql: str):
    """Split a multi-statement SQL string on top-level `;`, respecting `$$`
    dollar-quoted bodies (functions / DO blocks). Mirrors the splitter used by
    the ensure_feature_tables boot block in server.py."""
    stmts, buf, in_dollar = [], [], False
    for line in sql.splitlines():
        buf.append(line)
        if line.count("$$") % 2 == 1:
            in_dollar = not in_dollar
        if not in_dollar and line.rstrip().endswith(";"):
            stmts.append("\n".join(buf))
            buf = []
    if any(s.strip() for s in buf):
        stmts.append("\n".join(buf))
    return [s for s in stmts if s.strip()]


async def _ensure_tracking_table(conn):
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version    TEXT PRIMARY KEY,
            checksum   TEXT,
            applied_at TIMESTAMPTZ DEFAULT now(),
            ok         INTEGER DEFAULT 0,
            skipped    INTEGER DEFAULT 0
        )
        """
    )


async def run_core_migrations(pool) -> dict:
    """Apply migrations/core/*.sql in lexical order. Idempotent and non-fatal —
    returns a summary dict and NEVER raises (a migration problem must not crash
    the boot of a live node)."""
    summary = {"dir": CORE_DIR, "applied": [], "skipped_already": [], "failed": []}
    try:
        if not os.path.isdir(CORE_DIR):
            logger.info("core_migrations: no core/ dir at %s; nothing to run", CORE_DIR)
            return summary
        files = sorted(f for f in os.listdir(CORE_DIR) if f.endswith(".sql"))
        if not files:
            logger.info("core_migrations: core/ dir is empty; nothing to run")
            return summary
        async with pool.acquire() as conn:
            await _ensure_tracking_table(conn)
            rows = await conn.fetch("SELECT version, checksum FROM schema_migrations")
            applied = {r["version"]: r["checksum"] for r in rows}
            for fname in files:
                version = fname[:-4]  # strip .sql
                with open(os.path.join(CORE_DIR, fname)) as fh:
                    sql = fh.read()
                checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()[:16]
                if applied.get(version) == checksum:
                    summary["skipped_already"].append(version)
                    continue
                ok = fail = 0
                for stmt in split_sql_statements(sql):
                    try:
                        await conn.execute(stmt)
                        ok += 1
                    except Exception as se:  # idempotent stmt failing is benign — log + continue
                        fail += 1
                        logger.warning(
                            "core_migration %s: statement skipped: %s", version, str(se)[:160]
                        )
                await conn.execute(
                    """
                    INSERT INTO schema_migrations (version, checksum, ok, skipped)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (version) DO UPDATE
                      SET checksum = EXCLUDED.checksum, applied_at = now(),
                          ok = EXCLUDED.ok, skipped = EXCLUDED.skipped
                    """,
                    version, checksum, ok, fail,
                )
                summary["applied"].append({"version": version, "ok": ok, "skipped": fail})
                logger.info("core_migration %s applied (%d ok, %d skipped)", version, ok, fail)
    except Exception as e:  # whole-runner failure must not block startup
        logger.error("core_migrations failed (non-fatal, continuing startup): %s", e)
        summary["failed"].append(str(e))
    return summary
