"""
Core-table schema-drift detector for ops-center.

Converts "find drift by a prod 500" into "find drift at deploy". On startup (and
on demand via GET /api/v1/admin/schema-drift) we introspect the live schema for a
fixed set of CORE billing / identity / federation tables and compare each
column's coarse TYPE-CLASS to a checked-in canonical contract
(migrations/core/canonical_schema.json). A cross-class divergence on a column the
shared code depends on — e.g. `credit_packages.id` being uuid on one node and
integer on the other — is the exact failure mode that drifted between bigboy and
commander; we surface it loudly instead of waiting for a customer-facing 500.

SEVERITY
--------
  error  : a REQUIRED canonical column is missing, or present with an
           incompatible (cross-class) type. Shared code can 500 on this node.
  danger : a column flagged `signoff` in the contract (a PK / identity-column
           type change) diverges. Same blast radius as error, but it must NOT be
           auto-migrated — it needs explicit sign-off (Phase B).
  info   : benign — a same-class type nuance (varchar/text, timestamp/timestamptz,
           int4/int8), an extra column not in the contract, or a missing OPTIONAL
           column. Not counted as drift.

The check is read-only and never raises; a failure to introspect degrades to an
`error` status with the exception text, never a crash.
"""
import json
import logging
import os

logger = logging.getLogger(__name__)

_CONTRACT_PATH = os.path.join(
    os.path.dirname(__file__), "migrations", "core", "canonical_schema.json"
)

# udt_name -> coarse type-class. Columns whose class matches are compatible;
# a cross-class difference (uuid vs int, uuid vs string, string vs int) is what
# breaks shared code. varchar<->text and timestamp<->timestamptz collapse to one
# class on purpose (benign per the drift audit).
_TYPE_CLASS = {
    "uuid": "uuid",
    "int2": "int", "int4": "int", "int8": "int",
    "integer": "int", "bigint": "int", "smallint": "int",
    "serial": "int", "bigserial": "int",
    "numeric": "numeric", "decimal": "numeric", "float4": "numeric",
    "float8": "numeric", "real": "numeric", "money": "numeric",
    "bool": "bool", "boolean": "bool",
    "json": "json", "jsonb": "json",
    "varchar": "string", "character varying": "string", "text": "string",
    "bpchar": "string", "char": "string", "citext": "string", "name": "string",
    "timestamp": "ts", "timestamptz": "ts", "date": "ts", "time": "ts", "timetz": "ts",
}


def type_class(udt: str) -> str:
    """Map a Postgres udt_name to a coarse class. Unknown types (e.g. enums like
    `federation_node_status`) keep their own name so an enum only matches itself."""
    return _TYPE_CLASS.get((udt or "").lower(), (udt or "").lower())


def load_contract(path: str = _CONTRACT_PATH) -> dict:
    with open(path) as fh:
        return json.load(fh)


def core_tables(contract: dict = None) -> list:
    contract = contract or load_contract()
    return list(contract.get("tables", {}).keys())


async def introspect(pool, tables: list) -> dict:
    """Return {table: {column: udt_name}} for the given tables from the live DB."""
    rows = await _fetch_columns(pool, tables)
    live = {}
    for r in rows:
        live.setdefault(r["table_name"], {})[r["column_name"]] = r["udt_name"]
    return live


async def _fetch_columns(pool, tables: list):
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT table_name, column_name, udt_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = ANY($1::text[])
            ORDER BY table_name, ordinal_position
            """,
            tables,
        )


def evaluate(contract: dict, live: dict) -> dict:
    """Pure comparison of a canonical contract against an introspected live schema.
    Separated from DB access so it is trivially unit-testable with fixtures."""
    tables_report = {}
    counts = {"error": 0, "danger": 0, "info": 0}
    signoff_pending = []

    for table, cols in contract.get("tables", {}).items():
        live_cols = live.get(table)
        issues = []
        if live_cols is None:
            issues.append({
                "column": "*", "severity": "error", "detail": "table missing on this node",
                "live": None, "canonical": "present",
            })
            counts["error"] += 1
            tables_report[table] = {"status": "missing", "issues": issues}
            continue

        canon_names = set(cols.keys())
        for col, spec in cols.items():
            canon_class = spec.get("class")
            optional = spec.get("optional", False)
            signoff = spec.get("signoff")
            if col not in live_cols:
                if optional:
                    issues.append({"column": col, "severity": "info",
                                   "detail": "optional canonical column absent",
                                   "live": None, "canonical": canon_class})
                    counts["info"] += 1
                else:
                    sev = "danger" if signoff else "error"
                    issues.append({"column": col, "severity": sev,
                                   "detail": "required canonical column missing",
                                   "live": None, "canonical": canon_class})
                    counts[sev] += 1
                    if signoff:
                        signoff_pending.append(f"{table}.{col} — {signoff}")
                continue
            live_class = type_class(live_cols[col])
            if live_class != canon_class:
                if signoff:
                    issues.append({"column": col, "severity": "danger",
                                   "detail": f"PK/identity type change needs sign-off: {signoff}",
                                   "live": live_cols[col], "canonical": canon_class})
                    counts["danger"] += 1
                    signoff_pending.append(f"{table}.{col} — {signoff}")
                else:
                    issues.append({"column": col, "severity": "error",
                                   "detail": "incompatible (cross-class) type",
                                   "live": live_cols[col], "canonical": canon_class})
                    counts["error"] += 1

        # extra columns present on the node but not in the contract: benign/info
        for col in live_cols:
            if col not in canon_names:
                issues.append({"column": col, "severity": "info",
                               "detail": "extra column not in canonical contract",
                               "live": live_cols[col], "canonical": None})
                counts["info"] += 1

        actionable = [i for i in issues if i["severity"] in ("error", "danger")]
        tables_report[table] = {
            "status": "drift" if actionable else "ok",
            "issues": issues,
        }

    status = "drift" if (counts["error"] or counts["danger"]) else "ok"
    return {
        "status": status,
        "core_table_count": len(contract.get("tables", {})),
        "summary": counts,
        "signoff_pending": sorted(set(signoff_pending)),
        "tables": tables_report,
    }


async def check_drift(pool, contract: dict = None) -> dict:
    """Introspect the live DB and evaluate it against the canonical contract.
    Read-only; never raises (degrades to status='error' with the message)."""
    try:
        contract = contract or load_contract()
        live = await introspect(pool, core_tables(contract))
        return evaluate(contract, live)
    except Exception as e:
        logger.error("schema_drift check failed: %s", e)
        return {"status": "error", "error": str(e), "summary": {"error": 0, "danger": 0, "info": 0},
                "signoff_pending": [], "tables": {}}


def log_report(report: dict) -> None:
    """Log the drift report LOUDLY when core tables differ — this is the whole
    point: a deploy-time signal instead of a prod 500."""
    status = report.get("status")
    if status == "ok":
        logger.info("schema_drift: core tables OK (%d checked, no actionable drift)",
                    report.get("core_table_count", 0))
        return
    if status == "error":
        logger.error("schema_drift: CHECK FAILED: %s", report.get("error"))
        return
    s = report.get("summary", {})
    logger.error(
        "schema_drift: CORE-TABLE DRIFT DETECTED — %d error, %d danger(sign-off), %d info. "
        "A cherry-picked feature may 500 on this node. See GET /api/v1/admin/schema-drift.",
        s.get("error", 0), s.get("danger", 0), s.get("info", 0),
    )
    for table, rep in report.get("tables", {}).items():
        for issue in rep.get("issues", []):
            if issue["severity"] in ("error", "danger"):
                logger.error(
                    "schema_drift[%s.%s] %s: %s (live=%s canonical=%s)",
                    table, issue["column"], issue["severity"].upper(),
                    issue["detail"], issue["live"], issue["canonical"],
                )
    for p in report.get("signoff_pending", []):
        logger.error("schema_drift: SIGN-OFF REQUIRED before reconcile -> %s", p)
