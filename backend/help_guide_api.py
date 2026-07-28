"""
The Guide — an end-user-facing help agent for Ops-Center.

DISTINCT from Colonel: Colonel is the root-level admin/ops agent (bash, docker,
filesystem — full system access). The Guide is for END USERS: it has ZERO
system access — it cannot run any skill, command, or action. It only explains
how to use the platform and points to the right page, grounded in the help
knowledge base. Safe by construction (no skill-execution path exists here).

Ops-center-native: it calls the local inference gateway directly (no Brigade
dependency) with an INTERNAL key and a local model, so end users are never
billed for asking for help and a malicious prompt can't run anything.
"""

import json
import logging
import os
import re
import time
import uuid
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

logger = logging.getLogger("help_guide")

router = APIRouter(prefix="/api/v1/help", tags=["help"])

# Authenticate via the platform's Redis-backed session dependency (same one the
# rest of the user-facing app and the AuthMiddleware use). NB: litellm_api's
# get_user_id reads an in-memory session dict that is wiped on every backend
# restart — using it here makes the Guide 401 until the user re-logs in. The
# Redis-backed dependency survives restarts and matches the cookie the account
# tools forward to their self-calls.
from auth_dependencies import require_authenticated_user  # noqa: E402

GUIDE_NAME = os.getenv("HELP_GUIDE_NAME", "Guide")
# Model is configurable; if unset or unavailable we auto-pick an available local
# model from the gateway so this works on any node without per-node config.
_CONFIGURED_MODEL = os.getenv("HELP_GUIDE_MODEL", "")

_model_cache: Dict[str, Any] = {"ts": 0.0, "model": None}
_MODEL_TTL = 300.0

# --- The Guide's knowledge (kept compact; mirrors src/data/helpContent.js) ----
GUIDE_KNOWLEDGE = """
Unicorn Commander Ops-Center is the management hub for the UC-Cloud suite. Key areas and pages:

BILLING & PLANS:
- /admin/billing/tiers — subscription tiers (price, included apps, limits, markup).
- /admin/billing/rates — the rate book: markup %, credit value (default $0.01), per-model overrides; local models are bundled ($0) or metered.
- /admin/billing/credits — Buy Credits (one wallet spans free local + paid cloud usage).
- /admin/billing/credit-packs — define buyable credit packs.
- /admin/billing/inference-policy — per-(app,model) included-vs-metered; default is metered.
- /admin/billing/agent-pricing — units charged per federated agent invocation.

AI & MODELS:
- /admin/ai/models — model catalog: federation (local GPU, free/bundled) + cloud (cost+markup via gateway).
- /admin/ai/model-lists — curated per-app model lists with tier visibility.

INFRASTRUCTURE & FEDERATION:
- /admin/infra/federation — node identity, branding, peers, advertised services.
- /admin/infra/federation/contracts — ENFORCED trust per peer: trust_mode (full/scoped/consumer/publisher/isolated), publish[]/consume[] ACLs; global default isolated = deny-by-default.
- /admin/infra/services, /resources, /hardware, /network, /storage, /traefik — server management.

PEOPLE & ACCESS:
- /admin/people/users — users (tier controls app access; role controls Ops-Center permissions).
- /admin/people/organizations — orgs are tenants/workspaces sharing billing + a credit pool.
- /admin/people/org-features — grant a specific app to one org regardless of its tier.
- /admin/people/authentication — Keycloak SSO (uchub realm), brokered Google/GitHub/Microsoft.

MONITORING & INTEGRATIONS:
- /admin/monitoring/analytics, /logs, /alerts, /audit — observability.
- /admin/integrations/credentials — Stripe/Lago/Keycloak/Cloudflare/Forgejo keys (with test).
- /admin/integrations/email — email providers.

PLATFORM:
- /admin (Admin Dashboard) — infra health. /admin/my-dashboard — personal credits/usage/subscription.
- /admin/platform/white-label, /landing — branding. /admin/platform/extensions — add-ons marketplace.

KEY CONCEPTS:
- Subscription = app access (+ some included inference). Credits = a metered inference wallet. They are ORTHOGONAL: a solo founder can need more credits than an enterprise.
- Local models (own GPUs) bill $0 (fair-use throttled). Cloud models bill provider cost + markup.
- Colonel is the root-level admin agent (separate from you). You are the Guide — you help end users and never run actions.

COMMON Q&A:
Q: How do credits work? A: One wallet covers free local ($0) and paid cloud (cost+markup) usage; top up on the Buy Credits page or via your plan allocation.
Q: How do I upgrade my plan? A: From My Dashboard or Current Plan, choose a higher tier; it takes effect immediately.
Q: Metered vs included models? A: Included = bundled into a subscription (cost absorbed); metered = drawn from the credit wallet. Set per (app, model) under Inference Policy; default is metered.
Q: Federation Settings vs Contracts? A: Settings = node identity/peers/advertised services; Contracts = the ENFORCED trust (trust_mode + publish/consume ACLs) that gates traffic.
Q: How do I give an org a premium app without changing its tier? A: Use Org Feature Grants (/admin/people/org-features).
Q: Tier vs role? A: Tier controls which apps a user can access; role controls what they can do inside Ops-Center.
"""

GUIDE_SYSTEM_PROMPT = f"""You are {GUIDE_NAME}, the friendly help assistant for Unicorn Commander Ops-Center.

Your job: help end users and admins understand and navigate the platform — what a page does, where to find a setting, how billing/credits/federation/access work. Be warm, concise, and practical. When relevant, name the exact page (e.g. "go to Billing → Rates at /admin/billing/rates").

Hard rules:
- You CANNOT take any action, run any command, change any setting, or access the system. You only explain and guide. If asked to DO something, explain where the user can do it themselves.
- Only answer questions about using Unicorn Commander / Ops-Center. For anything off-topic, briefly say it's outside your scope and suggest the relevant page or contacting support.
- If you are not sure, say so and point to the most relevant page or the Help panel's FAQ tab. Do not invent features.
- Keep answers short (2-5 sentences) unless asked for detail.

Use this knowledge base:
{GUIDE_KNOWLEDGE}
"""


class GuideMessage(BaseModel):
    role: str
    content: str


class GuideAskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    page: Optional[str] = None          # current route, for context
    page_help: Optional[str] = None     # optional: the current page's help text
    history: List[GuideMessage] = Field(default_factory=list)


_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
# gpt-oss "harmony" format: ...<|channel|>final<|message|>ANSWER<|return|>. When
# present, the real answer is the LAST final-channel message; otherwise strip the
# stray control tokens (<|...|>) so they never leak into the UI.
_HARMONY_FINAL = re.compile(r"<\|channel\|>final<\|message\|>(.*?)(?:<\|end\|>|<\|return\|>|$)", re.DOTALL)
_HARMONY_TOKENS = re.compile(r"<\|[^|>]*\|>")


def _strip_thinking(text: str) -> str:
    """Reasoning models emit chain-of-thought we must not show: Qwen/DeepSeek use
    <think>...</think>; gpt-oss uses harmony channels (<|channel|>analysis|final...).
    Return only the user-facing answer."""
    if not text:
        return text
    finals = _HARMONY_FINAL.findall(text)
    if finals:
        text = finals[-1]
    text = _THINK_BLOCK.sub("", text)
    text = re.sub(r"</?think>", "", text, flags=re.IGNORECASE)
    text = _HARMONY_TOKENS.sub("", text)  # drop any leftover harmony control tokens
    return text.strip()


async def _resolve_gateway() -> tuple:
    try:
        from gateway_key_provisioning import _resolve_gateway_creds
        url, key = await _resolve_gateway_creds()
        return (url or "").rstrip("/"), key or ""
    except Exception as exc:
        logger.debug("Guide gateway creds unavailable: %s", exc)
        return "", ""


async def _pick_model(gateway_url: str, master_key: str, client: httpx.AsyncClient) -> Optional[str]:
    """Choose an available model: configured one if present, else a small/local
    model from the gateway, else the first available. Cached."""
    now = time.monotonic()
    if _model_cache["model"] and (now - _model_cache["ts"]) < _MODEL_TTL:
        return _model_cache["model"]
    try:
        resp = await client.get(f"{gateway_url}/v1/models", headers={"Authorization": f"Bearer {master_key}"})
        ids = [m.get("id") for m in (resp.json().get("data") or []) if m.get("id")] if resp.status_code == 200 else []
    except Exception as exc:
        logger.debug("Guide model list fetch failed: %s", exc)
        ids = []
    chosen = None
    if _CONFIGURED_MODEL and (_CONFIGURED_MODEL in ids or not ids):
        chosen = _CONFIGURED_MODEL
    if not chosen and ids:
        # Prefer models that RELIABLY emit OpenAI tool_calls (the Guide's account
        # lookups depend on it) and are still cheap/local. Measured on the home
        # gateway: qwen3.x-35b-a3b + llama-3.3-70b = 3/3; gpt-oss-20b = mostly but
        # prompt-sensitive; qwen3-30b-a3b = 0/3 (emits text, never structured).
        prefer = ("qwen3.6-35b", "qwen3.5-35b", "llama-3.3-70b", "qwen3.6", "qwen3.5",
                  "gpt-oss-20b", "gemma", "llama-3.2", "local")
        for p in prefer:
            match = next((m for m in ids if p in m.lower()), None)
            if match:
                chosen = match
                break
        chosen = chosen or ids[0]
    if chosen:
        _model_cache.update({"model": chosen, "ts": now})
    return chosen


# ============================================================================
# Personal Account Assistant — Phase 1 (READ-ONLY) account tools.
#
# Safety model: every tool is a thin wrapper over an EXISTING user-facing
# endpoint, called via a localhost self-call that forwards ONLY the caller's
# session cookie. The wrapped endpoint's own auth + RLS + RBAC re-run, so the
# Guide can do nothing the user couldn't do themselves in the UI. The LLM call
# stays internal (master key + local model = free); tool EXECUTIONS run strictly
# as the user. Tool paths/params are FIXED here — the model only chooses WHICH
# tool, never a URL or arbitrary query params (no injection surface). Phase 1 is
# read-only; mutations (upgrade/buy-credits/create-key) are Phase 2 and require
# confirmation + audit. See ~/Documents/UC-Personal-Account-Assistant-Design.md.
# ============================================================================

_ACCOUNT_ENABLED = os.getenv("ACCOUNT_ASSISTANT_ENABLED", "true").lower() not in ("0", "false", "no")
_MAX_TOOL_ROUNDS = 2          # tool-executing rounds before forcing a text answer
_MAX_TOOLS_PER_ROUND = 4      # cap distinct tool execs/round (some models repeat a call many times)
_TOOL_RESULT_CAP = 3000       # max chars of a tool result fed back to the model

# Each tool = a fixed (method, path[, params]) over an existing user endpoint.
ACCOUNT_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "get_my_credit_balance",
        "path": "/api/v1/credits/balance",
        "description": "The signed-in user's current credit balance, monthly allocation, and tier. Use for 'what's my balance / how many credits do I have left'.",
    },
    {
        "name": "get_my_usage",
        "path": "/api/v1/usage/current",
        "description": "The user's current billing-period API usage: used, limit, remaining, percentage, and reset date. Use for 'how much usage do I have left / am I near my limit'.",
    },
    {
        "name": "get_my_plan",
        "path": "/api/v1/subscriptions/my-access",
        "description": "The user's current subscription: plan name, monthly price, included features, and call limit. Use for 'what plan am I on / what does my plan include'.",
    },
    {
        "name": "get_my_invoices",
        "path": "/api/v1/billing/invoices",
        "params": {"limit": 10},
        "description": "The user's recent invoices (number, amount, status, dates, PDF link). Use for 'show my invoices / why was I charged / my last payment'.",
    },
    {
        "name": "list_my_api_keys",
        "path": "/api/v1/account/uc-api-keys",
        "description": "The user's API keys — names, prefixes, status, last-used ONLY. Never returns a secret. Use for 'what API keys do I have / when was a key last used'.",
    },
]
_TOOL_BY_NAME = {t["name"]: t for t in ACCOUNT_TOOLS}

# Defensive whitelist: only these fields survive on an API-key listing.
_ALLOWED_KEY_FIELDS = {
    "key_id", "id", "key_name", "name", "key_preview", "permissions",
    "created_at", "last_used", "expires_at", "is_active", "status",
}


def _self_base_url() -> str:
    return os.getenv("OPS_CENTER_SELF_URL", "http://localhost:8084").rstrip("/")


def _account_tools_openai() -> List[Dict[str, Any]]:
    """OpenAI-format tool specs. No params are exposed to the model — paths and
    query params are fixed server-side, so the model only picks a tool name."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": {"type": "object", "properties": {}},
            },
        }
        for t in ACCOUNT_TOOLS
    ]


def _sanitize_api_keys(data: Any) -> Any:
    """Strip everything but safe metadata from an API-key listing — never let a
    secret/hash leave the backend even if an upstream change starts returning it."""
    def clean(item: Any) -> Any:
        if isinstance(item, dict):
            return {k: v for k, v in item.items() if k in _ALLOWED_KEY_FIELDS}
        return item
    if isinstance(data, list):
        return [clean(i) for i in data]
    if isinstance(data, dict) and isinstance(data.get("data"), list):
        return {**{k: v for k, v in data.items() if k != "data"}, "data": [clean(i) for i in data["data"]]}
    return data


async def _execute_account_tool(name: str, session_token: Optional[str], client: httpx.AsyncClient) -> Any:
    """Run one read tool AS the user (forward only the session cookie). Returns the
    endpoint's JSON, or {"error": ...} — never raises into the loop."""
    tool = _TOOL_BY_NAME.get(name)
    if not tool:
        return {"error": f"unknown tool '{name}'"}
    if not session_token:
        return {"error": "I can't see your account right now — you don't appear to be signed in with a session."}
    url = f"{_self_base_url()}{tool['path']}"
    try:
        resp = await client.get(url, params=tool.get("params"), cookies={"session_token": session_token}, timeout=20.0)
    except Exception as exc:
        logger.debug("Account tool %s self-call failed: %s", name, exc)
        return {"error": "the account service is unavailable right now."}
    if resp.status_code in (401, 403):
        return {"error": "your session may have expired, or you don't have access to that — try signing in again."}
    if resp.status_code >= 400:
        return {"error": f"couldn't fetch that (status {resp.status_code})."}
    try:
        data = resp.json()
    except Exception:
        return {"error": "the account service returned an unexpected response."}
    if name == "list_my_api_keys":
        data = _sanitize_api_keys(data)
    return data


# ============================================================================
# Personal Account Assistant — Phase 2 (MUTATIONS, confirm-gated).
#
# A WRITE tool is NEVER auto-executed. When the model calls one, we validate the
# params, stash a single-use "pending action" in Redis (owner-scoped, short-
# lived), and return it to the UI as a Confirm/Cancel card. Only an explicit
# POST /guide/confirm-action (as the same user, forwarding the session+CSRF
# cookies) runs the underlying mutation endpoint — so the model can PROPOSE but
# never DO, and the human approves the exact action. Every proposal + execution
# is audited. Financial actions (upgrade/buy-credits) are intentionally NOT
# tools here — the Guide points the user to the existing checkout UI instead, so
# the agent never moves money. Phase 1 read tools stay above. See
# ~/Documents/UC-Personal-Account-Assistant-Design.md.
# ============================================================================

_PENDING_PREFIX = "guide_pending:"  # stored via redis_session_manager (its own prefix is added)
_ALLOWED_KEY_SCOPES = ("llm:inference", "llm:models")

WRITE_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "create_api_key",
        "confirm_label": "Create key",
        "description": (
            "PROPOSE creating a new API key for the signed-in user. This does NOT execute — the "
            "user must confirm. Provide a short descriptive 'name'; if the user didn't give one, ask "
            "for it instead of guessing."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Short descriptive name, e.g. 'CI bot' or 'staging server'."},
                "expires_in_days": {"type": "integer", "minimum": 1, "maximum": 3650,
                                    "description": "Days until the key expires (1-3650). Default 90."},
                "permissions": {"type": "array", "items": {"type": "string", "enum": list(_ALLOWED_KEY_SCOPES)},
                                "description": "Scopes to grant. Default both."},
            },
            "required": ["name"],
        },
    },
    {
        "name": "revoke_api_key",
        "confirm_label": "Revoke key",
        "description": (
            "PROPOSE revoking (deactivating) one of the user's existing API keys. This does NOT "
            "execute — the user must confirm. You need the key's id: if you don't have it, call "
            "list_my_api_keys FIRST, then pass its key_id (and key_name, for the confirmation display)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "key_id": {"type": "string", "description": "The id of the key to revoke (from list_my_api_keys)."},
                "key_name": {"type": "string", "description": "The key's name, for the confirmation display."},
            },
            "required": ["key_id"],
        },
    },
    {
        "name": "rotate_api_key",
        "confirm_label": "Rotate key",
        "description": (
            "PROPOSE rotating one of the user's API keys: issue a NEW key with the same scopes and "
            "revoke the OLD one. Does NOT execute — the user must confirm. Call list_my_api_keys FIRST "
            "to find the key, then pass key_id, key_name, and (if known) its permissions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "key_id": {"type": "string", "description": "The id of the key to rotate (from list_my_api_keys)."},
                "key_name": {"type": "string", "description": "The key's name — reused for the new key + display."},
                "permissions": {"type": "array", "items": {"type": "string", "enum": list(_ALLOWED_KEY_SCOPES)},
                                "description": "Scopes to carry to the new key. Default both."},
            },
            "required": ["key_id"],
        },
    },
]
_WRITE_BY_NAME = {t["name"]: t for t in WRITE_TOOLS}
_KEY_ID_RE = re.compile(r"^[0-9a-fA-F-]{8,64}$")  # plain id only — blocks path injection into the URL


def _write_tools_openai() -> List[Dict[str, Any]]:
    return [
        {"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}}
        for t in WRITE_TOOLS
    ]


def _prepare_write(tool_name: str, raw: Dict[str, Any]) -> tuple:
    """Validate+normalize the model's proposed params into a concrete action.
    Returns (spec, title, summary) where spec is either
    {"kind":"single","method","path","body"} or a named compound (e.g. rotate).
    Raises ValueError(clarifying question) if the proposal is incomplete — the
    Guide then asks the user instead of proposing."""
    if tool_name == "create_api_key":
        name = (str(raw.get("name") or "")).strip()
        if not name:
            raise ValueError("Sure — what would you like to name the API key?")
        name = name[:255]
        try:
            days = max(1, min(3650, int(raw.get("expires_in_days") or 90)))
        except (TypeError, ValueError):
            days = 90
        perms = [p for p in (raw.get("permissions") or []) if p in _ALLOWED_KEY_SCOPES]
        perms = perms or list(_ALLOWED_KEY_SCOPES)
        spec = {"kind": "single", "method": "POST", "path": "/api/v1/account/uc-api-keys",
                "body": {"name": name, "expires_in_days": days, "permissions": perms}}
        summary = f"Create API key “{name}” — scopes: {', '.join(perms)}; expires in {days} days."
        return spec, "Create API key", summary

    if tool_name == "revoke_api_key":
        key_id = (str(raw.get("key_id") or "")).strip()
        if not _KEY_ID_RE.match(key_id):
            raise ValueError("Which key should I revoke? Tell me its name and I'll look up the right one.")
        label = (str(raw.get("key_name") or "")).strip()
        disp = f"“{label}”" if label else f"id {key_id[:8]}…"
        spec = {"kind": "single", "method": "DELETE", "path": f"/api/v1/account/uc-api-keys/{key_id}", "body": None}
        summary = (f"Revoke API key {disp} — any app or script using it will stop working immediately. "
                   "This can't be undone.")
        return spec, "Revoke API key", summary

    if tool_name == "rotate_api_key":
        key_id = (str(raw.get("key_id") or "")).strip()
        if not _KEY_ID_RE.match(key_id):
            raise ValueError("Which key should I rotate? Tell me its name and I'll look up the right one.")
        name = (str(raw.get("key_name") or "")).strip()[:255] or "rotated key"
        perms = [p for p in (raw.get("permissions") or []) if p in _ALLOWED_KEY_SCOPES]
        perms = perms or list(_ALLOWED_KEY_SCOPES)
        spec = {"kind": "rotate", "old_key_id": key_id,
                "create_body": {"name": name, "permissions": perms}}
        summary = (f"Rotate API key “{name}” — issue a NEW key with the same scopes, then revoke the old "
                   "one. You'll see the new key once; apps must switch to it.")
        return spec, "Rotate API key", summary

    raise ValueError("That action isn't supported yet.")


def _shape_write_result(tool_name: str, data: Any) -> Dict[str, Any]:
    """Shape the underlying endpoint's response for the UI. For api-key creation
    the full secret is passed through ONCE (shown once, never audited/logged)."""
    if tool_name == "create_api_key" and isinstance(data, dict):
        return {
            "api_key": data.get("api_key"),          # full secret — shown once in the UI
            "key_preview": data.get("key_preview"),
            "key_name": data.get("key_name"),
            "expires_at": data.get("expires_at"),
            "warning": data.get("warning") or "Save this key now — you won't be able to see it again.",
        }
    return data if isinstance(data, dict) else {"result": data}


def _pending_set(action_id: str, payload: Dict[str, Any]) -> None:
    from redis_session import redis_session_manager
    redis_session_manager.set(_PENDING_PREFIX + action_id, payload)


def _pending_pop(action_id: str) -> Optional[Dict[str, Any]]:
    """Get-and-delete (single use) so a proposal can't be replayed."""
    from redis_session import redis_session_manager
    data = redis_session_manager.get(_PENDING_PREFIX + action_id)
    if data is not None:
        redis_session_manager.delete(_PENDING_PREFIX + action_id)
    return data


async def _audit(request: Request, user: Dict[str, Any], action: str, result: str, **kw) -> None:
    try:
        from audit_logger import audit_logger
        await audit_logger.log(
            action=action, result=result,
            user_id=user.get("user_id"), username=user.get("email"),
            ip_address=(request.client.host if request.client else None),
            user_agent=request.headers.get("user-agent"),
            **kw,
        )
    except Exception as exc:  # never let auditing break the action
        logger.debug("Guide audit log failed (%s): %s", action, exc)


@router.post("/guide/ask")
async def guide_ask(payload: GuideAskRequest, request: Request,
                    user: Dict[str, Any] = Depends(require_authenticated_user)):
    """Ask the Guide. Returns {answer}. Never bills the user (internal key +
    local model). For account questions it may call READ-ONLY account tools that
    run strictly as the signed-in user (forwarded session cookie → RLS/RBAC
    enforced by the wrapped endpoints). Fail-soft to a helpful message."""
    fallback = (
        "I'm having trouble reaching my knowledge service right now. "
        "Try the FAQ tab in this Help panel, or check the page you're on — most settings have an info banner."
    )
    user_id = user.get("user_id") or "unknown"
    gateway_url, master_key = await _resolve_gateway()
    if not gateway_url or not master_key:
        return {"answer": fallback, "ok": False}

    # Forward ONLY the session cookie to account tools — so they run as the user.
    session_token = request.cookies.get("session_token")
    tools_enabled = bool(_ACCOUNT_ENABLED and session_token)

    system = GUIDE_SYSTEM_PROMPT
    if tools_enabled:
        system += (
            "\n\nACCOUNT LOOKUP: You have READ-ONLY tools for THIS signed-in user's own account "
            "(balance, usage, plan, invoices, API key names, summary). When the user asks about their "
            "own balance/usage/plan/charges/invoices/API keys, call the appropriate tool immediately "
            "and answer from the real returned data — do not narrate your reasoning, and never invent "
            "numbers. Tools are read-only and scoped to this user (you can't change anything or see "
            "anyone else's data); never reveal an API key secret. If a tool errors, say so plainly and "
            "point to the relevant page."
            "\n\nACTIONS (require user confirmation): You can PROPOSE two actions; neither executes "
            "until the user clicks Confirm. (1) create_api_key — when the user wants a new API key, "
            "call it with a sensible 'name' (ask for one if they didn't give it). (2) revoke_api_key — "
            "when the user wants to delete/revoke a key, FIRST call list_my_api_keys to find the right "
            "key, then call revoke_api_key with its key_id and key_name. (3) rotate_api_key — when the "
            "user wants to rotate/replace a key, FIRST call list_my_api_keys, then call rotate_api_key "
            "with its key_id, key_name, and permissions. You CANNOT change plans, buy "
            "credits, or make any payment — for those, point the user to the page: upgrade/downgrade at "
            "/admin/billing/tiers (or My Dashboard), buy credits at /admin/billing/credits. Never claim "
            "you performed an action."
        )
    if payload.page:
        system += f"\n\nThe user is currently on: {payload.page}"
    if payload.page_help:
        system += f"\nHelp shown for this page:\n{payload.page_help[:2000]}"

    messages: List[Dict[str, Any]] = [{"role": "system", "content": system}]
    for m in payload.history[-6:]:
        if m.role in ("user", "assistant") and m.content:
            messages.append({"role": m.role, "content": m.content[:4000]})
    messages.append({"role": "user", "content": payload.question})

    timeout = float(os.getenv("HELP_GUIDE_TIMEOUT", "60"))
    used_tools: List[str] = []
    headers = {"Authorization": f"Bearer {master_key}", "Content-Type": "application/json"}

    async def _chat(client, model, tools, tool_choice):
        # gpt-oss/Qwen reasoning models spend tokens "thinking" before the tool
        # call or answer — too small a budget truncates the tool call mid-emit
        # (LiteLLM then returns it as raw text instead of structured tool_calls).
        body: Dict[str, Any] = {"model": model, "messages": messages, "temperature": 0.3, "max_tokens": 2000}
        if tools:
            body["tools"] = tools
            body["tool_choice"] = tool_choice
        return await client.post(f"{gateway_url}/v1/chat/completions", headers=headers, json=body)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            model = await _pick_model(gateway_url, master_key, client)
            if not model:
                return {"answer": fallback, "ok": False}

            tools = (_account_tools_openai() + _write_tools_openai()) if tools_enabled else None
            rounds = 0
            while True:
                # Final round (rounds exhausted): force a text answer, no more tools.
                tool_choice = "none" if (tools and rounds >= _MAX_TOOL_ROUNDS) else "auto"
                resp = await _chat(client, model, tools, tool_choice)

                # Gateway/model may not support tool-calling — drop tools and retry once.
                if resp.status_code == 400 and tools:
                    logger.info("Guide gateway rejected tools (400); retrying without account tools.")
                    tools = None
                    continue
                if resp.status_code >= 400:
                    logger.warning("Guide gateway %d: %s", resp.status_code, resp.text[:200])
                    _model_cache.update({"model": None, "ts": 0.0})  # stale model? re-pick next time.
                    return {"answer": fallback, "ok": False}

                data = resp.json()
                msg = ((data.get("choices") or [{}])[0].get("message") or {})
                tool_calls = msg.get("tool_calls") or []

                if tool_calls and tools and tool_choice == "auto":
                    read_calls = [tc for tc in tool_calls
                                  if ((tc.get("function") or {}).get("name") in _TOOL_BY_NAME)]
                    write_calls = [tc for tc in tool_calls
                                   if ((tc.get("function") or {}).get("name") in _WRITE_BY_NAME)]

                    # READ tools execute first. A WRITE proposed in the same turn is
                    # dropped and the model re-proposes next round with the real data
                    # (e.g. list_my_api_keys → then revoke_api_key by id).
                    if read_calls:
                        # Some models emit the same call many times — dedup + cap.
                        seen, deduped = set(), []
                        for tc in read_calls:
                            fn = (tc.get("function") or {})
                            sig = (fn.get("name") or "", fn.get("arguments") or "")
                            if sig in seen:
                                continue
                            seen.add(sig)
                            deduped.append(tc)
                            if len(deduped) >= _MAX_TOOLS_PER_ROUND:
                                break
                        messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": deduped})
                        cache: Dict[str, Any] = {}
                        for tc in deduped:
                            tname = (tc.get("function") or {}).get("name") or ""
                            if tname not in cache:
                                cache[tname] = await _execute_account_tool(tname, session_token, client)
                                used_tools.append(tname)
                                logger.info("Guide account tool user=%s tool=%s ok=%s",
                                            user_id, tname, not (isinstance(cache[tname], dict) and "error" in cache[tname]))
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc.get("id") or tname,
                                "name": tname,
                                "content": json.dumps(cache[tname], default=str)[:_TOOL_RESULT_CAP],
                            })
                        rounds += 1
                        continue

                    # WRITE only → never execute here: validate, stash a single-use
                    # pending action, and hand the UI a Confirm/Cancel card.
                    if write_calls:
                        fn = write_calls[0].get("function") or {}
                        wname = fn.get("name")
                        try:
                            raw_args = json.loads(fn.get("arguments") or "{}")
                        except Exception:
                            raw_args = {}
                        try:
                            spec, title, summary = _prepare_write(wname, raw_args)
                        except ValueError as ve:
                            # Incomplete proposal (e.g. missing name/id) — ask, don't propose.
                            return {"answer": str(ve), "ok": True}
                        action_id = uuid.uuid4().hex
                        _pending_set(action_id, {"user_id": user_id, "tool": wname, "spec": spec,
                                                 "title": title, "summary": summary})
                        await _audit(request, user, f"guide.{wname}.proposed", "success",
                                     resource_type="api-key", metadata={"summary": summary})
                        logger.info("Guide proposed write user=%s tool=%s action=%s", user_id, wname, action_id)
                        return {
                            "answer": "Here's what I'll do — review and confirm below.",
                            "pending_action": {"id": action_id, "tool": wname, "title": title,
                                               "summary": summary,
                                               "confirm_label": _WRITE_BY_NAME[wname].get("confirm_label", "Confirm")},
                            "ok": True, "model": model,
                        }
                    # else: only unrecognized tool calls — fall through to a text answer.

                answer = _strip_thinking((msg.get("content") or "").strip())
                return {"answer": answer or fallback, "ok": bool(answer), "model": model,
                        "used_tools": used_tools or None}
    except Exception as exc:
        logger.warning("Guide ask failed for user %s: %s", user_id, exc)
        return {"answer": fallback, "ok": False}


class ConfirmActionRequest(BaseModel):
    action_id: str = Field(..., min_length=8, max_length=64)


@router.post("/guide/confirm-action")
async def guide_confirm_action(payload: ConfirmActionRequest, request: Request,
                               user: Dict[str, Any] = Depends(require_authenticated_user)):
    """Execute a previously-proposed write action — ONLY after the user clicks
    Confirm. Runs the underlying mutation endpoint AS the user (forwards the
    session + CSRF cookies → its own auth/RLS/RBAC re-run). Single-use + audited."""
    user_id = user.get("user_id") or "unknown"
    pending = _pending_pop(payload.action_id)
    if not pending:
        return {"ok": False, "detail": "This action expired or was already used — please ask again."}
    if pending.get("user_id") != user_id:
        await _audit(request, user, "guide.confirm.denied", "denied",
                     metadata={"action_id": payload.action_id})
        return {"ok": False, "detail": "That action isn't available to your account."}

    tool = _WRITE_BY_NAME.get(pending.get("tool", ""))
    spec = pending.get("spec") or {}
    if not tool or not spec:
        return {"ok": False, "detail": "That action is no longer valid — please ask again."}
    tname = tool["name"]

    session_token = request.cookies.get("session_token")
    csrf = request.cookies.get("csrf_token")
    headers = {"Content-Type": "application/json"}
    cookies = {"session_token": session_token or ""}
    if csrf:                                   # satisfy the mutation endpoint's CSRF
        headers["X-CSRF-Token"] = csrf
        cookies["csrf_token"] = csrf

    async def _call(client, method, path, body):
        return await client.request(method, f"{_self_base_url()}{path}", json=body, headers=headers, cookies=cookies)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Compound: rotate = create a new key, then revoke the old one.
            if spec.get("kind") == "rotate":
                cresp = await _call(client, "POST", "/api/v1/account/uc-api-keys", spec.get("create_body") or {})
                if cresp.status_code >= 400:
                    await _audit(request, user, f"guide.{tname}.confirmed", "failure", resource_type="api-key",
                                 error_message=f"create:{cresp.status_code}", metadata={"summary": pending.get("summary")})
                    return {"ok": False, "detail": f"Couldn't create the new key (status {cresp.status_code}) — nothing was changed."}
                new_data = cresp.json() if cresp.headers.get("content-type", "").startswith("application/json") else {}
                old_revoked = False
                try:                                   # best-effort: the new key already exists
                    rresp = await _call(client, "DELETE", f"/api/v1/account/uc-api-keys/{spec.get('old_key_id')}", None)
                    old_revoked = rresp.status_code < 400
                except Exception:
                    old_revoked = False
                result = _shape_write_result("create_api_key", new_data)
                if not old_revoked:
                    result["warning"] = (result.get("warning", "") + " Heads up: the OLD key could not be revoked — revoke it yourself under Account → API Keys.").strip()
                await _audit(request, user, f"guide.{tname}.confirmed", "success", resource_type="api-key",
                             resource_id=str(new_data.get("key_id")) if isinstance(new_data, dict) else None,
                             metadata={"summary": pending.get("summary"),
                                       "key_preview": result.get("key_preview"), "old_revoked": old_revoked})
                logger.info("Guide rotated key user=%s old_revoked=%s", user_id, old_revoked)
                return {"ok": True, "tool": tname, "result": result,
                        "message": "Rotated — new key issued and old key revoked." if old_revoked
                                   else "New key issued, but the old key wasn't revoked."}

            # Single call.
            method, path = spec.get("method"), spec.get("path")
            if not method or not path:
                return {"ok": False, "detail": "That action is no longer valid — please ask again."}
            resp = await _call(client, method, path, spec.get("body"))
    except Exception as exc:
        logger.warning("Guide confirm self-call failed user=%s tool=%s: %s", user_id, tname, exc)
        await _audit(request, user, f"guide.{tname}.confirmed", "error",
                     resource_type="api-key", error_message=str(exc)[:300],
                     metadata={"summary": pending.get("summary")})
        return {"ok": False, "detail": "I couldn't reach the account service to complete that."}

    if resp.status_code >= 400:
        detail = "your session may have expired — try again" if resp.status_code in (401, 403) else f"it didn't go through (status {resp.status_code})"
        await _audit(request, user, f"guide.{tname}.confirmed", "failure",
                     resource_type="api-key", error_message=f"{resp.status_code}",
                     metadata={"summary": pending.get("summary")})
        return {"ok": False, "detail": f"The action failed — {detail}."}

    try:
        data = resp.json()
    except Exception:
        data = {}
    result = _shape_write_result(tname, data)
    # Audit success WITHOUT the secret (only the preview/name).
    await _audit(request, user, f"guide.{tname}.confirmed", "success",
                 resource_type="api-key",
                 resource_id=str(data.get("key_id")) if isinstance(data, dict) else None,
                 metadata={"summary": pending.get("summary"),
                           "key_preview": result.get("key_preview") if isinstance(result, dict) else None})
    logger.info("Guide executed write user=%s tool=%s ok", user_id, tname)
    return {"ok": True, "tool": tname, "result": result, "message": "Done!"}
