#!/usr/bin/env python3
"""
schema_drift_check.py — hot-table schema drift check for ops-center (Phase 0, T3).

Compares the LIVE database's information_schema columns against the columns the
APPLICATION CODE actually reads/writes for the hot admin-console tables. The
expectations below were derived by grepping the managers/routers (sources noted
per table), NOT from the .sql files — a .sql file can claim anything; what 500s
in prod is code touching a column the node lacks.

Complements (does not replace) backend/schema_drift.py, which type-checks the
CORE billing/identity tables against migrations/core/canonical_schema.json on
startup. This script is the standalone ops probe for the FEATURE tables the
console fix-wave leaned on, runnable against any node:

    DATABASE_URL=postgresql://user:pass@host:5432/unicorn_db \
        python3 scripts/ops/schema_drift_check.py

Without DATABASE_URL it falls back to the same POSTGRES_* env vars/defaults the
backend uses (POSTGRES_HOST=unicorn-postgresql, POSTGRES_USER=unicorn, ...).

Exit codes:  0 = no drift
             1 = drift (required column or table missing)
             2 = could not connect/introspect
"""
import asyncio
import os
import sys

# ---------------------------------------------------------------------------
# Code-declared expectations. required = code breaks without it (SELECTed,
# INSERTed or UPDATEd unconditionally). optional = referenced defensively or
# only by the canonical core contract; absence is reported but not fatal.
# ---------------------------------------------------------------------------
EXPECTED = {
    "app_model_lists": {
        "source": "backend/model_list_manager.py (list/create/update queries)",
        "required": [
            "id", "name", "slug", "description", "app_identifier",
            "is_default", "is_active", "created_at", "updated_at",
        ],
        "optional": ["created_by"],
    },
    "app_model_list_items": {
        "source": "backend/model_list_manager.py (get_list_models/add_model/update_model)",
        "required": [
            "id", "list_id", "model_id", "display_name", "category", "sort_order",
            "is_featured", "tier_trial_access", "tier_starter_access",
            "tier_professional_access", "tier_enterprise_access",
            "is_active", "metadata", "created_at", "updated_at",
        ],
        "optional": [],
    },
    "admin_system_settings": {
        "source": "backend/system_settings_manager.py (get/set/delete/list)",
        "required": [
            "key", "encrypted_value", "category", "description", "is_sensitive",
            "value_type", "is_required", "is_editable", "default_value",
            "created_at", "updated_at", "updated_by",
        ],
        "optional": [],
    },
    "monitored_websites": {
        "source": "backend/routers/website_monitor.py (CRUD + alert tracking updates)",
        "required": [
            "id", "name", "url", "server", "check_interval", "timeout",
            "expected_status", "notify_on_down", "is_active",
            "created_at", "updated_at", "last_alert_status", "last_alert_sent_at",
            "alert_email",
        ],
        "optional": [],
    },
    "website_checks": {
        "source": "backend/routers/website_monitor.py (check inserts + history reads)",
        "required": [
            "id", "website_id", "status", "status_code", "response_time_ms",
            "ssl_valid", "ssl_expiry", "error", "checked_at",
        ],
        "optional": [],
    },
    "organization_members": {
        "source": "backend/server.py org lookup/provisioning, org_access_api.py, org_billing_api.py",
        "required": ["org_id", "user_id", "role", "joined_at"],
        # provisioning inserts is_active only when the column exists (defensive);
        # id/is_default come from the core canonical contract, not hot code paths.
        "optional": ["id", "is_active", "is_default"],
    },
    "org_features": {
        "source": "backend/org_features_api.py (grant list/create)",
        "required": [
            "id", "org_id", "feature_key", "enabled",
            "granted_by", "granted_at", "notes",
        ],
        "optional": [],
    },
    "subscription_tiers": {
        "source": "backend/subscription_tiers_api.py, plan_provisioning.py, paid_org_provisioning.py",
        "required": [
            "id", "tier_code", "tier_name", "description", "price_monthly",
            "price_yearly", "is_active", "is_invite_only", "sort_order",
            "api_calls_limit", "team_seats", "byok_enabled", "priority_support",
            "llm_markup_percentage", "lago_plan_code", "stripe_price_monthly",
            "stripe_price_yearly", "created_at", "updated_at", "created_by",
            "updated_by", "max_monthly_llm_budget",
        ],
        "optional": [],
    },
}


def dsn_from_env() -> str:
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


async def fetch_live_columns(conn, tables):
    rows = await conn.fetch(
        """
        SELECT table_name, column_name, udt_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = ANY($1::text[])
        ORDER BY table_name, ordinal_position
        """,
        tables,
    )
    live = {}
    for r in rows:
        live.setdefault(r["table_name"], {})[r["column_name"]] = r["udt_name"]
    return live


def evaluate(live: dict):
    """Pure comparison; returns (lines, drift_count). Separated from DB access
    so it is unit-testable with fixtures."""
    lines = []
    drift = 0
    ok = 0
    for table in sorted(EXPECTED):
        spec = EXPECTED[table]
        live_cols = live.get(table)
        if live_cols is None:
            drift += 1
            lines.append(f"[MISSING TABLE] {table}")
            lines.append(f"    expected by: {spec['source']}")
            lines.append(f"    required columns: {', '.join(spec['required'])}")
            continue
        missing_req = [c for c in spec["required"] if c not in live_cols]
        missing_opt = [c for c in spec["optional"] if c not in live_cols]
        if missing_req:
            drift += 1
            lines.append(f"[DRIFT] {table} — {len(missing_req)} required column(s) missing")
            lines.append(f"    expected by: {spec['source']}")
            for c in missing_req:
                lines.append(f"    MISSING required column: {table}.{c}")
        else:
            ok += 1
            lines.append(
                f"[OK] {table} ({len(spec['required'])} required columns present, "
                f"{len(live_cols)} live)"
            )
        for c in missing_opt:
            lines.append(f"    note: optional column absent (not drift): {table}.{c}")
    lines.append("")
    lines.append(
        f"Summary: {ok}/{len(EXPECTED)} tables OK, {drift} with drift "
        f"({'DRIFT — exit 1' if drift else 'no drift — exit 0'})"
    )
    return lines, drift


async def main() -> int:
    try:
        import asyncpg
    except ImportError:
        print("ERROR: asyncpg not installed (pip install asyncpg)")
        return 2

    dsn = dsn_from_env()
    try:
        conn = await asyncpg.connect(dsn=dsn, timeout=15)
    except Exception as e:
        print(f"ERROR: could not connect to database: {e}")
        print("Set DATABASE_URL (or POSTGRES_HOST/PORT/USER/PASSWORD/DB) and retry.")
        return 2
    try:
        live = await fetch_live_columns(conn, list(EXPECTED.keys()))
    except Exception as e:
        print(f"ERROR: introspection failed: {e}")
        return 2
    finally:
        await conn.close()

    print(f"schema_drift_check: {len(EXPECTED)} hot tables vs code-declared expectations")
    print("")
    lines, drift = evaluate(live)
    for line in lines:
        print(line)
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
