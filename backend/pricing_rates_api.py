"""
Pricing & Rates API — the editable cost-plus rate book for Unicorn Commander inference resale.

Single source of truth for: provider per-token COSTS, your MARKUP, a safety BUFFER, the CREDIT
value, the local-inference strategy, and per-model overrides. The GUI ("Pricing & Rates") reads the
computed table (provider cost vs your rate vs margin vs credits/1M) and writes edits back here.

Never-lose-money model: metering bills `measured_cost * (1 + markup)`, so margin holds even if a
provider changes prices; `buffer_pct` absorbs cost-map lag; per-model overrides let you bump a rate
instantly if a provider hikes. This module is the config those mechanisms read.

Stored as JSON (no DB schema dependency) at PRICING_CONFIG_PATH so it persists on the bind-mount.

Endpoints (admin):
- GET  /api/v1/admin/pricing/rates  -> computed rate book + settings
- PUT  /api/v1/admin/pricing/rates  -> edit settings and/or per-provider/per-model overrides (GUI)
- POST /api/v1/admin/pricing/seed   -> replace provider COST table (the rate-research job), keep overrides
"""

import os
import json
import copy
import logging
from typing import Dict, Any
from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse

from auth_dependencies import require_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/pricing", tags=["pricing-rates"])

PRICING_CONFIG_PATH = os.getenv("PRICING_CONFIG_PATH", "/app/data/pricing_config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "credit_value_usd": 0.01,     # $ per credit (1 credit = 1 cent)
    "default_markup_pct": 20.0,   # margin on top of provider cost
    "buffer_pct": 10.0,           # safety cushion for cost-map lag (never-lose-money)
    "local": {
        "strategy": "bundled",    # bundled ($0, fair-use throttle) | metered
        "rate_per_million_usd": 0.0,
        "label": "Self-hosted (Unicorn GPUs)",
    },
    "providers": {
        # minimal seed; the rate-research job (POST /seed) fills the full, real table
        "anthropic": {"label": "Anthropic", "markup_pct": None, "source_url": "", "as_of": "", "models": {
            "claude-sonnet-4": {"input_per_million_usd": 3.0, "output_per_million_usd": 15.0, "override_markup_pct": None},
        }},
        "deepseek": {"label": "DeepSeek", "markup_pct": None, "source_url": "", "as_of": "", "models": {
            "deepseek-chat": {"input_per_million_usd": 0.27, "output_per_million_usd": 1.10, "override_markup_pct": None},
        }},
    },
}


def _load() -> Dict[str, Any]:
    try:
        with open(PRICING_CONFIG_PATH) as f:
            cfg = json.load(f)
        merged = copy.deepcopy(DEFAULT_CONFIG)
        merged.update(cfg)
        return merged
    except (FileNotFoundError, json.JSONDecodeError):
        return copy.deepcopy(DEFAULT_CONFIG)


def _nn(value: Any, default: float = 0.0) -> float:
    """Coerce to a non-negative float; fall back to default on bad or negative input."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return default
    return f if f >= 0 else default


def _clamp(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Enforce the never-lose-money invariants in code, not just in the GUI.

    A negative markup/buffer or a zero credit value would silently break margin (or
    divide-by-zero in _compute), so we floor them here at the persistence boundary —
    every write (GUI edit or seed job) passes through this.
    """
    cfg["default_markup_pct"] = _nn(cfg.get("default_markup_pct"), 20.0)
    cfg["buffer_pct"] = _nn(cfg.get("buffer_pct"), 0.0)
    cv = _nn(cfg.get("credit_value_usd"), 0.01)
    cfg["credit_value_usd"] = cv if cv > 0 else 0.01  # used as a divisor — must be > 0
    loc = cfg.get("local")
    if isinstance(loc, dict):
        loc["rate_per_million_usd"] = _nn(loc.get("rate_per_million_usd"), 0.0)
    for prov in cfg.get("providers", {}).values():
        if prov.get("markup_pct") is not None:
            prov["markup_pct"] = _nn(prov.get("markup_pct"), 0.0)
        for m in prov.get("models", {}).values():
            m["input_per_million_usd"] = _nn(m.get("input_per_million_usd"), 0.0)
            m["output_per_million_usd"] = _nn(m.get("output_per_million_usd"), 0.0)
            if m.get("override_markup_pct") is not None:
                m["override_markup_pct"] = _nn(m.get("override_markup_pct"), 0.0)
    return cfg


def _save(cfg: Dict[str, Any]) -> None:
    cfg = _clamp(cfg)
    os.makedirs(os.path.dirname(PRICING_CONFIG_PATH), exist_ok=True)
    tmp = PRICING_CONFIG_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cfg, f, indent=2)
    os.replace(tmp, PRICING_CONFIG_PATH)


def _effective_markup(cfg: Dict[str, Any], provider_key: str, model: Dict[str, Any]) -> float:
    prov = cfg["providers"].get(provider_key, {})
    m = model.get("override_markup_pct")
    if m is None:
        m = prov.get("markup_pct")
    if m is None:
        m = cfg.get("default_markup_pct", 20.0)
    return float(m)


def _compute(cfg: Dict[str, Any]) -> Dict[str, Any]:
    credit = float(cfg.get("credit_value_usd", 0.01)) or 0.01
    buffer = float(cfg.get("buffer_pct", 0.0)) / 100.0
    rows = []
    for pkey, prov in cfg.get("providers", {}).items():
        for mname, m in prov.get("models", {}).items():
            cin = float(m.get("input_per_million_usd", 0.0))
            cout = float(m.get("output_per_million_usd", 0.0))
            mk = _effective_markup(cfg, pkey, m) / 100.0
            rin = cin * (1 + mk) * (1 + buffer)
            rout = cout * (1 + mk) * (1 + buffer)
            rows.append({
                "provider": pkey,
                "provider_label": prov.get("label", pkey),
                "model": mname,
                "cost_input_per_m": round(cin, 4),
                "cost_output_per_m": round(cout, 4),
                "your_input_per_m": round(rin, 4),
                "your_output_per_m": round(rout, 4),
                "markup_pct": round(mk * 100, 1),
                "margin_input_per_m": round(rin - cin, 4),
                "margin_output_per_m": round(rout - cout, 4),
                "credits_per_m_input": round(rin / credit, 1),
                "credits_per_m_output": round(rout / credit, 1),
                "source_url": prov.get("source_url", ""),
                "as_of": prov.get("as_of", ""),
            })
    loc = cfg.get("local", {})
    if loc:
        lr = float(loc.get("rate_per_million_usd", 0.0))
        rows.append({
            "provider": "local", "provider_label": loc.get("label", "Self-hosted"),
            "model": "(all local models)",
            "cost_input_per_m": 0.0, "cost_output_per_m": 0.0,
            "your_input_per_m": lr, "your_output_per_m": lr,
            "markup_pct": None, "margin_input_per_m": lr, "margin_output_per_m": lr,
            "credits_per_m_input": round(lr / credit, 1), "credits_per_m_output": round(lr / credit, 1),
            "source_url": "", "as_of": loc.get("strategy", ""),
        })
    rows.sort(key=lambda r: (r["provider"] != "local", r["provider"], r["model"]))
    return {
        "settings": {k: cfg[k] for k in ("credit_value_usd", "default_markup_pct", "buffer_pct", "local") if k in cfg},
        "rows": rows,
        "provider_count": len(cfg.get("providers", {})),
        "model_count": sum(len(p.get("models", {})) for p in cfg.get("providers", {}).values()),
    }


@router.get("/rates")
async def get_rates(_admin: Dict[str, Any] = Depends(require_admin_user)):
    return JSONResponse(_compute(_load()))


@router.put("/rates")
async def update_rates(
    patch: Dict[str, Any] = Body(...),
    _admin: Dict[str, Any] = Depends(require_admin_user),
):
    cfg = _load()
    for k in ("credit_value_usd", "default_markup_pct", "buffer_pct", "local"):
        if k in patch:
            cfg[k] = patch[k]
    for pkey, pv in (patch.get("providers") or {}).items():
        prov = cfg["providers"].setdefault(pkey, {"label": pkey, "models": {}})
        if "markup_pct" in pv:
            prov["markup_pct"] = pv["markup_pct"]
        if "label" in pv:
            prov["label"] = pv["label"]
        for mname, mv in (pv.get("models") or {}).items():
            prov["models"].setdefault(mname, {}).update(mv)
    _save(cfg)
    return JSONResponse(_compute(cfg))


@router.post("/seed")
async def seed_costs(
    payload: Dict[str, Any] = Body(...),
    _admin: Dict[str, Any] = Depends(require_admin_user),
):
    """Replace/merge the provider COST table (rate-research job). Preserves markup overrides."""
    cfg = _load()
    for pkey, pv in (payload.get("providers") or {}).items():
        prov = cfg["providers"].setdefault(pkey, {"label": pv.get("label", pkey), "models": {}})
        prov["label"] = pv.get("label", prov.get("label", pkey))
        prov["source_url"] = pv.get("source_url", prov.get("source_url", ""))
        prov["as_of"] = pv.get("as_of", prov.get("as_of", ""))
        for mname, mv in (pv.get("models") or {}).items():
            mm = prov["models"].setdefault(mname, {})
            mm["input_per_million_usd"] = mv.get("input_per_million_usd", mm.get("input_per_million_usd", 0.0))
            mm["output_per_million_usd"] = mv.get("output_per_million_usd", mm.get("output_per_million_usd", 0.0))
            mm.setdefault("override_markup_pct", None)
    _save(cfg)
    return JSONResponse(_compute(cfg))


# ============================================================================
# Dynamic refresh — pull live provider pricing from OpenRouter's public catalog
# instead of hand-maintaining costs. Each tracked model carries an `openrouter_id`;
# the refresh job looks up its live $/token and writes input/output per-million,
# preserving your markup/buffer/overrides. New flagships are added by virtue of being
# in the tracked map below (edit here, or persisted per-model in pricing_config.json).
# ============================================================================

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

# Default curated catalog: provider_key -> {model_label: openrouter_id}. Used to seed
# tracking on first refresh; thereafter the per-model `openrouter_id` in the config wins,
# so the tracked set can be edited via the GUI/PUT without code changes.
DEFAULT_TRACKED: Dict[str, Dict[str, str]] = {
    "anthropic": {
        "claude-opus-4-8": "anthropic/claude-opus-4.8",
        "claude-sonnet-4-6": "anthropic/claude-sonnet-4.6",
        "claude-haiku-4-5": "anthropic/claude-haiku-4.5",
    },
    "openai": {
        "gpt-5.5": "openai/gpt-5.5",
        "gpt-5.5-pro": "openai/gpt-5.5-pro",
        "gpt-5-mini": "openai/gpt-5-mini",
        "gpt-4.1": "openai/gpt-4.1",
        "o3": "openai/o3",
        "o4-mini": "openai/o4-mini",
    },
    "google": {
        "gemini-2.5-pro": "google/gemini-2.5-pro",
        "gemini-2.5-flash": "google/gemini-2.5-flash",
        "gemini-2.5-flash-lite": "google/gemini-2.5-flash-lite",
    },
    "deepseek": {
        "deepseek-v4-pro": "deepseek/deepseek-v4-pro",
        "deepseek-v4-flash": "deepseek/deepseek-v4-flash",
    },
    "xai": {"grok-4.3": "x-ai/grok-4.3"},
    "mistral": {
        "mistral-large-latest": "mistralai/mistral-large-2512",
        "codestral-latest": "mistralai/codestral-2508",
    },
}

PROVIDER_LABELS = {
    "anthropic": "Anthropic", "openai": "OpenAI", "google": "Google",
    "deepseek": "DeepSeek", "xai": "xAI", "mistral": "Mistral",
}


async def _fetch_openrouter_prices() -> Dict[str, Dict[str, float]]:
    """Return {openrouter_id: {'input': $/M, 'output': $/M}} from the live catalog."""
    import httpx
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(OPENROUTER_MODELS_URL)
        resp.raise_for_status()
        data = resp.json().get("data", [])
    out: Dict[str, Dict[str, float]] = {}
    for m in data:
        p = m.get("pricing") or {}
        try:
            out[m["id"]] = {
                "input": round(float(p.get("prompt", 0) or 0) * 1_000_000, 4),
                "output": round(float(p.get("completion", 0) or 0) * 1_000_000, 4),
            }
        except (TypeError, ValueError):
            continue
    return out


def _pct_increase(old, new):
    """% increase from old->new for a cost field; None if old is missing/zero."""
    try:
        o, n = float(old), float(new)
    except (TypeError, ValueError):
        return None
    if o <= 0:
        return None
    return round((n - o) / o * 100, 1)


async def perform_refresh(reason: str = "manual") -> Dict[str, Any]:
    """Pull live OpenRouter pricing and update the rate book (preserving markup/overrides).

    Shared by the admin endpoint and the scheduled job. Detects price INCREASES and flags
    any that exceed the safety buffer (the never-lose-money guard: those are the hikes the
    buffer might not fully absorb between refreshes), records refresh metadata for staleness
    detection, and returns a structured report. Never raises — returns ok:false on failure.
    """
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    cfg = _load()
    buffer_pct = float(cfg.get("buffer_pct", 0) or 0)

    try:
        live = await _fetch_openrouter_prices()
    except Exception as e:
        logger.error(f"pricing refresh ({reason}): OpenRouter fetch failed: {e}")
        meta = cfg.setdefault("_refresh_meta", {})
        meta["last_attempt_at"] = now.isoformat()
        meta["last_ok"] = False
        meta["last_error"] = str(e)[:200]
        _save(cfg)
        return {"ok": False, "error": f"Could not reach OpenRouter: {e}", "reason": reason, "changes": []}

    today = now.strftime("%Y-%m-%d")
    changes, missing, hikes = [], [], []
    for pkey, tracked in DEFAULT_TRACKED.items():
        prov = cfg["providers"].setdefault(pkey, {"label": PROVIDER_LABELS.get(pkey, pkey), "models": {}})
        prov.setdefault("label", PROVIDER_LABELS.get(pkey, pkey))
        prov["source_url"] = "https://openrouter.ai/api/v1/models (live)"
        prov["as_of"] = today
        for label, default_or_id in tracked.items():
            mm = prov["models"].setdefault(label, {})
            or_id = mm.get("openrouter_id") or default_or_id  # per-model override wins
            mm["openrouter_id"] = or_id
            mm.setdefault("override_markup_pct", None)
            price = live.get(or_id)
            if not price:
                missing.append(f"{pkey}/{label} ({or_id})")
                continue
            old_in, old_out = mm.get("input_per_million_usd"), mm.get("output_per_million_usd")
            if old_in != price["input"] or old_out != price["output"]:
                inc_in, inc_out = _pct_increase(old_in, price["input"]), _pct_increase(old_out, price["output"])
                changes.append({
                    "model": f"{pkey}/{label}", "openrouter_id": or_id,
                    "old": {"input": old_in, "output": old_out},
                    "new": {"input": price["input"], "output": price["output"]},
                    "pct_increase": {"input": inc_in, "output": inc_out},
                })
                # never-lose-money flag: a cost increase that exceeds the safety buffer
                worst = max([x for x in (inc_in, inc_out) if x is not None], default=None)
                if worst is not None and worst > buffer_pct:
                    hikes.append({
                        "model": f"{pkey}/{label}", "pct": worst,
                        "exceeds_buffer_by": round(worst - buffer_pct, 1),
                        "old": {"input": old_in, "output": old_out},
                        "new": {"input": price["input"], "output": price["output"]},
                    })
            mm["input_per_million_usd"] = price["input"]
            mm["output_per_million_usd"] = price["output"]

    # Refresh metadata (for staleness + hike surfacing on the GUI)
    meta = cfg.setdefault("_refresh_meta", {})
    meta["last_refresh_at"] = now.isoformat()
    meta["last_attempt_at"] = now.isoformat()
    meta["last_ok"] = True
    meta["last_error"] = None
    meta["last_reason"] = reason
    meta["last_changed"] = len(changes)
    if hikes:
        meta["last_hikes"] = hikes  # only keep the most recent refresh's hikes

    _save(cfg)
    result = _compute(cfg)

    if hikes:
        logger.warning(
            f"pricing refresh ({reason}): {len(hikes)} provider price HIKE(S) exceeding the "
            f"{buffer_pct}% buffer — review markups: " +
            "; ".join(f"{h['model']} +{h['pct']}%" for h in hikes)
        )
    logger.info(f"pricing refresh ({reason}): {len(changes)} change(s), {result['model_count']} models, {len(missing)} missing upstream")

    return {
        "ok": True, "reason": reason, "refreshed_at": today,
        "source": "openrouter-live", "models_tracked": result["model_count"],
        "changed": len(changes), "changes": changes,
        "hikes_over_buffer": hikes, "not_found_on_openrouter": missing,
        "rate_book": result,
    }


@router.post("/refresh")
async def refresh_from_openrouter(_admin: Dict[str, Any] = Depends(require_admin_user)):
    """Admin trigger for the live pricing refresh (same job the scheduler runs)."""
    report = await perform_refresh(reason="manual")
    return JSONResponse(report, status_code=200 if report.get("ok") else 503)


@router.get("/status")
async def pricing_status(_admin: Dict[str, Any] = Depends(require_admin_user)):
    """Refresh freshness + any price hikes — drives the GUI staleness/hike banner."""
    from datetime import datetime, timezone
    cfg = _load()
    meta = cfg.get("_refresh_meta", {})
    last = meta.get("last_refresh_at")
    stale_hours = None
    if last:
        try:
            dt = datetime.fromisoformat(last)
            stale_hours = round((datetime.now(timezone.utc) - dt).total_seconds() / 3600, 1)
        except Exception:
            pass
    refresh_hours = float(os.getenv("PRICING_REFRESH_HOURS", "8") or 8)
    return JSONResponse({
        "last_refresh_at": last,
        "last_ok": meta.get("last_ok"),
        "last_error": meta.get("last_error"),
        "last_changed": meta.get("last_changed"),
        "hours_since_refresh": stale_hours,
        # stale if we've missed ~2 scheduled cycles
        "is_stale": (stale_hours is not None and stale_hours > refresh_hours * 2),
        "schedule_hours": refresh_hours,
        "recent_hikes": meta.get("last_hikes", []),
    })
