"""
Billing Provider Config API

Ops-Center is the single pane of glass. Billing / metering / analytics are
PLUGGABLE and configured per-deployment via env. This endpoint tells the
frontend which billing provider backs THIS server so the UI can adapt:
  - "local"     -> this node charges (its own Stripe + credits tables): full UI
  - "federated" -> a central hub charges (e.g. billing.unicorncommander.ai):
                   show balance/usage + a deep-link to the hub; one card vault
                   shared across all apps
  - "disabled"  -> hide billing surfaces entirely
...and shows provenance ("served by X") so it's transparent where data lives.

Same console code on every deployment; only env changes.

Endpoint:
- GET /api/v1/billing/provider-config   (returns only non-secret config)

Env:
- BILLING_PROVIDER         local | federated | disabled            (default: local)
- BILLING_PROVIDER_NAME    display name of the billing provider     (default: BRANDING_COMPANY_NAME or "This deployment")
- BILLING_MANAGE_URL       federated: hub base URL (https://billing.unicorncommander.ai)
- BILLING_BUY_CREDITS_URL  optional explicit buy-credits deep link  (default: BILLING_MANAGE_URL)
- BILLING_CURRENCY         ISO currency                             (default: usd)
- STRIPE_PUBLISHABLE_KEY   pk_... key; surfaced to the browser in LOCAL mode so card
                           entry works without a frontend rebuild (publishable keys are
                           public by design and already ship in the client bundle).

Federated provenance (only meaningful when BILLING_PROVIDER=federated) — lets the UI
render WHICH hub operates billing/metering, with its name, logo, and a link home:
- FEDERATION_PROVIDER_NAME  provider display name   (default: "Unicorn Commander")
- FEDERATION_PROVIDER_URL   provider home URL        (default: "https://unicorncommander.ai")
- FEDERATION_PROVIDER_LOGO  provider logo path/URL   (default: "/logos/uc-logo-512.png")
"""

import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1/billing", tags=["billing-config"])


@router.get("/provider-config")
async def get_billing_provider_config():
    provider = (os.getenv("BILLING_PROVIDER") or "local").strip().lower()
    if provider not in ("local", "federated", "disabled"):
        provider = "local"

    name = (
        os.getenv("BILLING_PROVIDER_NAME")
        or os.getenv("BRANDING_COMPANY_NAME")
        or "This deployment"
    )
    manage_url = (os.getenv("BILLING_MANAGE_URL") or "").rstrip("/")
    buy_credits_url = (os.getenv("BILLING_BUY_CREDITS_URL") or manage_url or "").rstrip("/")

    pk = os.getenv("STRIPE_PUBLISHABLE_KEY") or ""
    has_stripe = pk.startswith("pk_")

    if provider == "disabled":
        caps = {"saved_cards": False, "buy_credits": False, "invoices": False, "subscriptions": False}
    elif provider == "federated":
        caps = {"saved_cards": False, "buy_credits": bool(buy_credits_url), "invoices": False, "subscriptions": False}
    else:  # local
        caps = {"saved_cards": has_stripe, "buy_credits": True, "invoices": True, "subscriptions": True}

    if provider == "federated":
        source = {
            "kind": "remote",
            "label": (manage_url.replace("https://", "").replace("http://", "") or name),
        }
    elif provider == "disabled":
        source = {"kind": "none", "label": "Billing disabled"}
    else:
        source = {"kind": "local", "label": name}

    # Federated provenance: when a central hub operates billing/metering, surface its
    # brand so the console can show "Billing & metering operated by <hub>" with a logo
    # and a link home. Only populated in federated mode; blank otherwise so the UI can
    # cleanly skip the treatment. All env-overridable for non-UC federations.
    if provider == "federated":
        provider_display_name = (
            os.getenv("FEDERATION_PROVIDER_NAME") or "Unicorn Commander"
        )
        provider_url = (
            os.getenv("FEDERATION_PROVIDER_URL") or "https://unicorncommander.ai"
        )
        provider_logo_url = (
            os.getenv("FEDERATION_PROVIDER_LOGO") or "/logos/uc-logo-512.png"
        )
    else:
        provider_display_name = ""
        provider_url = ""
        provider_logo_url = ""

    body = {
        "provider": provider,
        "display_name": name,
        "manage_url": manage_url,
        "buy_credits_url": buy_credits_url,
        "currency": (os.getenv("BILLING_CURRENCY") or "usd").lower(),
        "capabilities": caps,
        "source": source,
        # Federated provenance (branding only; blank unless provider == "federated")
        "provider_display_name": provider_display_name,
        "provider_url": provider_url,
        "provider_logo_url": provider_logo_url,
        # public by design; only in local mode where THIS node does the charging
        "stripe_publishable_key": pk if (provider == "local" and has_stripe) else "",
    }
    return JSONResponse(body)
