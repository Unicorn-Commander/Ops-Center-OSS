#!/usr/bin/env python3
"""CI gate: static backend sanity checks — parses, never executes, the server.

What it asserts (all via `ast`, so no backend deps/DB/Redis are needed):

  1. backend/server.py parses, creates a FastAPI app, and wires the
     default-deny auth middleware (create_auth_middleware via add_middleware).
  2. Import-sanity for the most critical routers: server.py imports them,
     app.include_router()s them, the module file exists, parses, and actually
     defines the imported router symbol at module scope.
  3. backend/auth_middleware.py's PUBLIC_EXACT / PUBLIC_PREFIXES allowlists
     don't accidentally open admin/mutation surfaces: every entry is checked
     against a denylist of admin-ish / destructive / credential-ish patterns,
     and over-broad prefixes (e.g. "/api/v1/") are rejected outright.

Run from anywhere:  python3 scripts/ci/backend_smoke.py
Exits non-zero with a list of failures.
"""

import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend"

# Critical routers: security / money / user-management surfaces. Keys are the
# module names exactly as server.py imports them; values are the router
# symbols server.py pulls out of each module.
CRITICAL_ROUTERS = {
    "user_management_api": ["router"],
    "account_management_api": ["router"],
    "billing_api": ["router"],
    "stripe_api": ["router"],
    "credit_api": ["router"],
    "org_api": ["router"],
    "subscription_api": ["router"],
    "admin_subscriptions_api": ["router"],
    "litellm_api": ["router"],
    "system_settings_api": ["router"],
    "local_user_api": ["router"],
    "invite_codes_api": ["admin_router", "user_router"],
    "webhooks": ["router"],  # Stripe webhooks
    "routers.audit_api": ["admin_router", "internal_router"],
    "routers.website_monitor": ["router"],
    "routers.federation": ["router"],
}

# Patterns that must NEVER appear in the auth middleware's public allowlists.
# These are admin/mutation surfaces; allowlisting one to "fix" a 401 would
# silently reopen the 2026-06-08 unauthenticated-endpoint hole.
DENY_PATTERNS = [
    (r"/admin\b", "admin-scoped path"),
    (r"/users?\b", "user-management surface"),
    (r"/organizations?\b", "organization-management surface"),
    (r"/delete\b|/remove\b|/purge\b|/terminate\b|/revoke\b|/wipe\b", "destructive verb in path"),
    (r"/credentials?\b|/secrets?\b|/api-keys?\b|/service-keys?\b", "credential surface"),
    (r"/impersonat", "impersonation surface"),
    (r"/permissions?\b|/roles?\b", "authorization surface"),
    (r"/settings\b", "settings mutation surface"),
    (r"/sessions\b", "session administration surface"),
    (r"/keycloak\b", "identity-provider administration"),
    (r"/backups?\b|/restore\b", "backup/restore surface"),
]

# Prefixes this broad would disable the default-deny middleware wholesale.
OVERBROAD = {"/", "/api", "/api/", "/api/v1", "/api/v1/"}

failures = []


def fail(msg: str) -> None:
    failures.append(msg)


def parse(path: Path):
    """ast.parse a file; record a failure and return None on error."""
    if not path.exists():
        fail(f"{path.relative_to(REPO)} does not exist")
        return None
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as e:
        fail(f"{path.relative_to(REPO)}:{e.lineno}: SyntaxError: {e.msg}")
        return None


def iter_module_scope(tree: ast.Module):
    """Yield statements at module scope, descending into if/try/with/loop
    blocks but NOT into function/class bodies (a router imported or defined
    only inside a function is not part of the module surface)."""

    def visit(body):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            yield node
            for field in ("body", "orelse", "finalbody"):
                sub = getattr(node, field, None)
                if isinstance(sub, list):
                    yield from visit(sub)
            for handler in getattr(node, "handlers", []) or []:
                yield from visit(handler.body)

    yield from visit(tree.body)


def module_scope_assignments(tree: ast.Module) -> set:
    """Names assigned at module scope."""
    names = set()
    for node in iter_module_scope(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def check_server() -> ast.Module:
    """Check 1+2: server.py parses, builds a FastAPI app, wires auth
    middleware, and imports + includes every critical router."""
    tree = parse(BACKEND / "server.py")
    if tree is None:
        return None

    # module -> {imported_name: local_alias} — module scope ONLY, so a
    # function-local `from x import router as r` can't mask the real wiring.
    imports = {}
    for node in iter_module_scope(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            bucket = imports.setdefault(node.module, {})
            for alias in node.names:
                bucket[alias.name] = alias.asname or alias.name

    included = set()          # names passed to app.include_router(...)
    fastapi_app = False
    auth_mw_wired = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            # app = FastAPI(...)
            if (
                isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "FastAPI"
                and any(isinstance(t, ast.Name) and t.id == "app" for t in node.targets)
            ):
                fastapi_app = True
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "include_router":
                for arg in node.args:
                    if isinstance(arg, ast.Name):
                        included.add(arg.id)
            elif node.func.attr == "add_middleware":
                # app.add_middleware(create_auth_middleware(enabled=...))
                for arg in node.args:
                    if (
                        isinstance(arg, ast.Call)
                        and isinstance(arg.func, ast.Name)
                        and arg.func.id == "create_auth_middleware"
                    ):
                        auth_mw_wired = True

    if not fastapi_app:
        fail("server.py: no `app = FastAPI(...)` assignment found")
    if "create_auth_middleware" not in imports.get("auth_middleware", {}):
        fail("server.py: no longer imports create_auth_middleware from auth_middleware")
    if not auth_mw_wired:
        fail("server.py: app.add_middleware(create_auth_middleware(...)) not found — default-deny auth gate unwired")

    for module, symbols in CRITICAL_ROUTERS.items():
        mod_path = BACKEND / (module.replace(".", "/") + ".py")
        mod_tree = parse(mod_path)
        defined = module_scope_assignments(mod_tree) if mod_tree else set()
        imported_here = imports.get(module, {})
        for symbol in symbols:
            if mod_tree is not None and symbol not in defined:
                fail(f"{mod_path.relative_to(REPO)}: does not define `{symbol}` at module scope")
            local = imported_here.get(symbol)
            if local is None:
                fail(f"server.py: no longer imports `{symbol}` from `{module}`")
            elif local not in included:
                fail(f"server.py: imports `{module}.{symbol}` as `{local}` but never app.include_router()s it")

    print(
        f"server.py OK: FastAPI app + auth middleware wired, "
        f"{len(CRITICAL_ROUTERS)} critical router modules verified "
        f"({sum(len(s) for s in CRITICAL_ROUTERS.values())} router symbols)."
    )
    return tree


def check_auth_allowlists() -> None:
    """Check 3: the public allowlists in auth_middleware.py stay tight."""
    tree = parse(BACKEND / "auth_middleware.py")
    if tree is None:
        return

    exact = prefixes = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ("PUBLIC_EXACT", "PUBLIC_PREFIXES"):
                    try:
                        value = ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        fail(f"auth_middleware.py: {target.id} is no longer a literal — cannot audit it statically")
                        continue
                    if target.id == "PUBLIC_EXACT":
                        exact = value
                    else:
                        prefixes = value

    if exact is None:
        fail("auth_middleware.py: PUBLIC_EXACT not found (renamed? middleware gutted?)")
    if prefixes is None:
        fail("auth_middleware.py: PUBLIC_PREFIXES not found (renamed? middleware gutted?)")
    if exact is None or prefixes is None:
        return

    entries = [("PUBLIC_EXACT", e) for e in exact] + [("PUBLIC_PREFIXES", p) for p in prefixes]
    if not entries:
        fail("auth_middleware.py: both allowlists are empty — parsing bug or middleware rewrite; audit manually")

    compiled = [(re.compile(pat, re.IGNORECASE), reason) for pat, reason in DENY_PATTERNS]
    for source, entry in entries:
        if not isinstance(entry, str):
            fail(f"auth_middleware.py: non-string entry {entry!r} in {source}")
            continue
        if not entry.startswith("/api"):
            fail(f"auth_middleware.py: {source} entry {entry!r} is outside /api — middleware only gates /api/*")
        if source == "PUBLIC_PREFIXES" and entry.rstrip() in OVERBROAD:
            fail(f"auth_middleware.py: prefix {entry!r} would make the ENTIRE API public")
        for regex, reason in compiled:
            if regex.search(entry):
                fail(
                    f"auth_middleware.py: {source} entry {entry!r} matches denylist "
                    f"pattern `{regex.pattern}` ({reason}) — public allowlist must not expose this"
                )

    if not failures:
        print(f"auth allowlists OK: {len(exact)} exact + {len(prefixes)} prefix entries, none admin/mutation-shaped.")


def main() -> int:
    check_server()
    check_auth_allowlists()

    if failures:
        print("\nBackend smoke FAILED:", file=sys.stderr)
        for f in failures:
            print(f"  FAIL: {f}", file=sys.stderr)
        print(f"\n{len(failures)} failure(s).", file=sys.stderr)
        return 1

    print("\nBackend smoke OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
