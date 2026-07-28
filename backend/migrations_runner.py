"""
Manifest-driven feature-schema migration runner for ops-center (Phase 0, T3).

WHY THIS EXISTS
---------------
`migrations/` holds ~70 raw .sql files that were historically applied BY HAND
(or never applied at all) — which is how a fresh node ends up with handlers
querying tables/columns that don't exist and 500ing. `ensure_feature_tables.sql`
(server.py boot block) and `core_migrations.py` (versioned migrations/core/)
already self-heal parts of the schema; this runner closes the remaining gap for
FEATURE schemas by applying, on every startup, the small CURATED set of .sql
files listed in `migrations/manifest.json`. Only files whose statements are all
safe to re-run (CREATE ... IF NOT EXISTS / ALTER ... ADD COLUMN IF NOT EXISTS /
INSERT ... ON CONFLICT / CREATE OR REPLACE / DROP-IF-EXISTS-then-CREATE trigger
pairs) are ever listed with `"idempotent": true` — anything else stays out of
the manifest (see its `needs_review` section) and is NEVER auto-applied.

CONTRACT (mirrors the proven ensure_feature_tables / core_migrations self-heal)
-------------------------------------------------------------------------------
* Applies ONLY files listed in manifest.json, in the order listed, and refuses
  any entry not explicitly marked `"idempotent": true`.
* Every statement is executed INDIVIDUALLY with per-statement error tolerance —
  a benign "already exists" (or any other single-statement failure) is logged
  and skipped, never aborts the file, and startup NEVER crashes because of a
  migration (the whole runner is non-fatal by construction).
* Tracking rows live in the SAME `schema_migrations` table core_migrations.py
  owns (version TEXT PRIMARY KEY, checksum, applied_at, ok, skipped) — the
  table already exists on live nodes with that shape, so this runner must NOT
  try to create a differently-shaped tracker. Manifest entries are namespaced
  as `manifest:<file>` in the version column to keep them apart from core
  versions. `applied_at` records when, `ok`/`skipped` record statement counts.
* A file is (re)applied when it is new OR its checksum changed (append another
  convergence ALTER -> it re-runs; safe, everything is idempotent). If a file
  hits a NON-benign statement failure (e.g. a dependency table not created yet
  on a fresh DB), its tracking row is NOT written, so it retries next boot and
  converges once the dependency exists.

Standalone use (manual convergence run, same env as server.py startup):
    python3 backend/migrations_runner.py            # uses POSTGRES_* env vars
    DATABASE_URL=postgres://... python3 backend/migrations_runner.py
"""
import hashlib
import json
import logging
import os

# Reuse the statement splitter and the canonical tracking-table DDL from the
# core runner so the two runners can never disagree about either.
from core_migrations import _ensure_tracking_table, split_sql_statements

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")
MANIFEST_PATH = os.path.join(MIGRATIONS_DIR, "manifest.json")

# Prefix for rows in schema_migrations so manifest entries never collide with
# core_migrations versions (those are bare filenames-sans-.sql like
# "0003_organizations_tenancy_union").
TRACKING_PREFIX = "manifest:"

# SQLSTATEs that mean "the object is already there" — the expected no-op case
# for idempotent DDL that predates IF NOT EXISTS support (e.g. CREATE TRIGGER).
_BENIGN_SQLSTATES = {
    "42P07",  # duplicate_table
    "42710",  # duplicate_object (trigger, policy, ...)
    "42701",  # duplicate_column
    "42723",  # duplicate_function
    "42P06",  # duplicate_schema
    "23505",  # unique_violation (re-seeded data)
}


def _is_benign(exc: Exception) -> bool:
    if getattr(exc, "sqlstate", None) in _BENIGN_SQLSTATES:
        return True
    return "already exists" in str(exc).lower()


def _is_executable(stmt: str) -> bool:
    """True if the statement contains anything besides whitespace and full-line
    `--` comments. The splitter can emit comment-only chunks (e.g. a commented-out
    sample INSERT whose last comment line ends in `;`, or a trailing comment
    footer) and asyncpg raises on comment-only scripts — there is nothing to run,
    so such chunks are skipped instead of counting as failures."""
    for line in stmt.splitlines():
        s = line.strip()
        if s and not s.startswith("--"):
            return True
    return False


def load_manifest(path: str = MANIFEST_PATH) -> dict:
    with open(path) as fh:
        return json.load(fh)


async def run_manifest_migrations(pool, manifest_path: str = MANIFEST_PATH) -> dict:
    """Apply the manifest-listed migrations in order. Idempotent and NON-FATAL —
    returns a summary dict and never raises (a migration problem must not block
    the boot of a live node)."""
    summary = {
        "manifest": manifest_path,
        "applied": [],            # [{name, ok, skipped}] files (re)applied this run
        "skipped_already": [],    # unchanged checksum, nothing to do
        "refused_not_idempotent": [],
        "missing_files": [],
        "failed": [],             # runner-level failures (never raised)
    }
    try:
        if not os.path.exists(manifest_path):
            logger.info("migrations_runner: no manifest at %s; nothing to run", manifest_path)
            return summary
        try:
            manifest = load_manifest(manifest_path)
        except Exception as e:
            logger.error("migrations_runner: manifest.json unreadable (%s); nothing applied", e)
            summary["failed"].append(f"manifest unreadable: {e}")
            return summary

        entries = manifest.get("migrations", [])
        if not entries:
            logger.info("migrations_runner: manifest lists no migrations; nothing to run")
            return summary

        async with pool.acquire() as conn:
            await _ensure_tracking_table(conn)
            rows = await conn.fetch(
                "SELECT version, checksum FROM schema_migrations WHERE version LIKE $1",
                TRACKING_PREFIX + "%",
            )
            applied = {r["version"]: r["checksum"] for r in rows}

            for entry in entries:
                fname = (entry or {}).get("file")
                if not fname:
                    continue
                # Safety rails: manifest may only point at real files directly
                # inside migrations/ and must explicitly vouch for idempotency.
                if entry.get("idempotent") is not True:
                    logger.warning(
                        "migrations_runner: %s not marked idempotent:true — refusing to auto-apply",
                        fname,
                    )
                    summary["refused_not_idempotent"].append(fname)
                    continue
                fpath = os.path.normpath(os.path.join(MIGRATIONS_DIR, fname))
                if os.path.dirname(fpath) != os.path.normpath(MIGRATIONS_DIR):
                    logger.warning("migrations_runner: %s escapes migrations/ — refusing", fname)
                    summary["refused_not_idempotent"].append(fname)
                    continue
                if not os.path.exists(fpath):
                    logger.warning("migrations_runner: %s listed in manifest but missing on disk", fname)
                    summary["missing_files"].append(fname)
                    continue

                with open(fpath) as fh:
                    sql = fh.read()
                checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()[:16]
                version = TRACKING_PREFIX + fname
                if applied.get(version) == checksum:
                    summary["skipped_already"].append(fname)
                    continue

                ok = benign = failed_other = 0
                for stmt in split_sql_statements(sql):
                    if not _is_executable(stmt):
                        continue
                    try:
                        await conn.execute(stmt)
                        ok += 1
                    except Exception as se:
                        if _is_benign(se):
                            benign += 1
                            logger.info(
                                "migrations_runner %s: statement no-op (already exists): %s",
                                fname, str(se)[:120],
                            )
                        else:
                            failed_other += 1
                            logger.warning(
                                "migrations_runner %s: statement skipped: %s",
                                fname, str(se)[:160],
                            )

                if failed_other == 0:
                    # Fully converged -> record checksum so unchanged files are
                    # skipped on future boots.
                    await conn.execute(
                        """
                        INSERT INTO schema_migrations (version, checksum, ok, skipped)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (version) DO UPDATE
                          SET checksum = EXCLUDED.checksum, applied_at = now(),
                              ok = EXCLUDED.ok, skipped = EXCLUDED.skipped
                        """,
                        version, checksum, ok, benign,
                    )
                else:
                    # Do NOT record: a non-benign failure (e.g. dependency table
                    # not there yet) should retry next boot — statements are
                    # idempotent so re-running the file is safe.
                    logger.warning(
                        "migrations_runner %s: %d statement(s) failed non-benignly; "
                        "will retry on next startup", fname, failed_other,
                    )
                summary["applied"].append(
                    {"name": fname, "ok": ok, "skipped": benign + failed_other}
                )
                logger.info(
                    "migrations_runner %s applied (%d ok, %d already-exists, %d skipped)",
                    fname, ok, benign, failed_other,
                )
    except Exception as e:  # whole-runner failure must never block startup
        logger.error("migrations_runner failed (non-fatal, continuing startup): %s", e)
        summary["failed"].append(str(e))
    if summary["skipped_already"]:
        logger.info(
            "migrations_runner: %d file(s) unchanged/skipped: %s",
            len(summary["skipped_already"]), ", ".join(summary["skipped_already"]),
        )
    return summary


def _dsn_from_env() -> str:
    """DATABASE_URL if set, else the same POSTGRES_* envs/defaults server.py uses."""
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return dsn
    return (
        f"postgresql://{os.getenv('POSTGRES_USER', 'unicorn')}"
        f":{os.getenv('POSTGRES_PASSWORD', 'unicorn')}"
        f"@{os.getenv('POSTGRES_HOST', 'unicorn-postgresql')}"
        f":{os.getenv('POSTGRES_PORT', '5432')}"
        f"/{os.getenv('POSTGRES_DB', 'unicorn_db')}"
    )


async def _main() -> int:
    import asyncpg

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    pool = await asyncpg.create_pool(dsn=_dsn_from_env(), min_size=1, max_size=2)
    try:
        summary = await run_manifest_migrations(pool)
    finally:
        await pool.close()
    print(json.dumps(summary, indent=2, default=str))
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    import asyncio
    import sys

    sys.exit(asyncio.run(_main()))
