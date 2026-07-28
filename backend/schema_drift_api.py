"""
Admin endpoint for the core-table schema-drift check.

  GET /api/v1/admin/schema-drift              full drift report (canonical vs live)
  GET /api/v1/admin/schema-drift/fingerprint  raw live {table: {column: udt}}
  GET /api/v1/admin/schema-drift/health        200 ok / 200-or-503 on drift

The /health route normally returns 200 with the status in the body so it is
informational and never takes a node down for KNOWN drift. Set the environment
variable SCHEMA_DRIFT_FAIL_HEALTH=1 to make it return 503 on drift instead — that
lets CI or an external health probe FAIL on a new core-table divergence.
"""
import logging
import os

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

import schema_drift
from federation_settings_api import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/schema-drift", tags=["admin", "schema-drift"])


def _pool(request: Request):
    return getattr(request.app.state, "db_pool", None)


@router.get("")
async def get_schema_drift(request: Request, admin=Depends(require_admin)):
    """Full drift report: canonical contract vs live schema for the CORE tables."""
    pool = _pool(request)
    if pool is None:
        return JSONResponse(status_code=503, content={"status": "error", "error": "db pool not ready"})
    report = await schema_drift.check_drift(pool)
    return report


@router.get("/fingerprint")
async def get_fingerprint(request: Request, admin=Depends(require_admin)):
    """Raw live fingerprint for the CORE tables — useful when diffing two nodes."""
    pool = _pool(request)
    if pool is None:
        return JSONResponse(status_code=503, content={"status": "error", "error": "db pool not ready"})
    contract = schema_drift.load_contract()
    live = await schema_drift.introspect(pool, schema_drift.core_tables(contract))
    return {"tables": {t: {c: {"udt": u, "class": schema_drift.type_class(u)}
                           for c, u in cols.items()} for t, cols in live.items()}}


@router.get("/health")
async def schema_drift_health(request: Request, admin=Depends(require_admin)):
    """Lightweight pass/fail. Returns 503 on drift only when SCHEMA_DRIFT_FAIL_HEALTH
    is set, so the fail-loud behavior is opt-in and can't surprise a live node."""
    pool = _pool(request)
    if pool is None:
        return JSONResponse(status_code=503, content={"status": "error", "error": "db pool not ready"})
    report = await schema_drift.check_drift(pool)
    body = {"status": report.get("status"), "summary": report.get("summary"),
            "signoff_pending": report.get("signoff_pending", [])}
    fail = os.getenv("SCHEMA_DRIFT_FAIL_HEALTH", "").lower() in ("1", "true", "yes", "on")
    if fail and report.get("status") != "ok":
        return JSONResponse(status_code=503, content=body)
    return body
