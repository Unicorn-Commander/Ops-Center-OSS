"""
Runtime Branding Configuration

Provides tenant-specific branding at runtime via environment variables
and landing_config.json. This is the single source of truth for all
brand-related information across all four tenants.

USAGE:
    from branding_config import get_branding_config
    branding = get_branding_config()
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Paths that landing_config.json could live at (per-tenant on disk)
LANDING_CONFIG_PATHS = [
    "/app/config/landing_config.json",
    "/app/backend/config/landing_config.json",
]

# Generic fallback values — no tenant-specific strings here
FALLBACK_BRANDING = {
    "company_name": "Ops-Center",
    "page_title": "Ops-Center",
    "primary_color": "#7c3aed",
    "logo_url": "/logos/ops-center-logo.png",
    "tagline": "Operations Center",
    "subtitle": "System Administration",
    "sso_provider_name": "SSO",
    "sso_enabled": True,
    # Federation upstream IdP — the parent SSO that subordinate tenants
    # delegate auth to (each local Keycloak federates to this one).
    "federation_upstream_name": "Unicorn Commander",
    "federation_upstream_logo": "/logos/The_Colonel.webp",
    "favicon_url": "/favicon.png",
    "og_title": "Ops-Center — Operations Dashboard",
    "og_description": "Centralized operations and management dashboard.",
    "og_image": "/logos/ops-center-logo.png",
}


def _load_landing_config() -> Dict:
    """Load landing_config.json from the first available path."""
    for path_str in LANDING_CONFIG_PATHS:
        config_path = Path(path_str)
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not parse landing config at {config_path}: {e}")
    logger.debug("No landing_config.json found; using fallback branding")
    return {}


def get_branding_config() -> Dict[str, str]:
    """
    Return runtime branding configuration.

    1. BRANDING_* environment variables (set per-tenant container) take TOP priority
    2. landing_config.json values serve as fallback
    3. Generic "Ops-Center" values are the last resort
    """
    branding = dict(FALLBACK_BRANDING)
    landing = _load_landing_config()

    # ---- Layer 2: landing_config.json ----
    lc_branding = landing.get("branding", {})
    lc_config = landing.get("config", {})

    if lc_branding.get("company_name"):
        branding["company_name"] = lc_branding["company_name"]
    if lc_branding.get("logo_url"):
        branding["logo_url"] = lc_branding["logo_url"]

    theme = landing.get("theme", {})
    custom_colors = theme.get("custom_colors", {})
    if custom_colors.get("primary"):
        branding["primary_color"] = custom_colors["primary"]

    if lc_config.get("sso_enabled") is False:
        branding["sso_enabled"] = False
    if lc_config.get("sso_provider_name"):
        branding["sso_provider_name"] = lc_config["sso_provider_name"]

    # ---- Layer 1: BRANDING_* env vars (overrides everything above) ----
    if os.environ.get("BRANDING_COMPANY_NAME"):
        branding["company_name"] = os.environ["BRANDING_COMPANY_NAME"]
    if os.environ.get("BRANDING_PAGE_TITLE"):
        branding["page_title"] = os.environ["BRANDING_PAGE_TITLE"]
    if os.environ.get("BRANDING_PRIMARY_COLOR"):
        branding["primary_color"] = os.environ["BRANDING_PRIMARY_COLOR"]
    if os.environ.get("BRANDING_LOGO_URL"):
        branding["logo_url"] = os.environ["BRANDING_LOGO_URL"]
    if os.environ.get("BRANDING_TAGLINE"):
        branding["tagline"] = os.environ["BRANDING_TAGLINE"]
    if os.environ.get("BRANDING_SUBTITLE"):
        branding["subtitle"] = os.environ["BRANDING_SUBTITLE"]
    if os.environ.get("BRANDING_THEME"):
        branding["theme"] = os.environ["BRANDING_THEME"]

    # SSO can only be disabled via env, not enabled (it's on by default)
    if os.environ.get("BRANDING_SSO_ENABLED", "").lower() in ("false", "0", "no"):
        branding["sso_enabled"] = False
    sso_name = os.environ.get("BRANDING_SSO_PROVIDER_NAME")
    if sso_name:
        branding["sso_provider_name"] = sso_name

    # Federation upstream IdP overrides (constant by default; tenants
    # can override if they federate to a different parent).
    upstream_name = os.environ.get("BRANDING_FEDERATION_UPSTREAM_NAME")
    if upstream_name:
        branding["federation_upstream_name"] = upstream_name
    upstream_logo = os.environ.get("BRANDING_FEDERATION_UPSTREAM_LOGO")
    if upstream_logo:
        branding["federation_upstream_logo"] = upstream_logo

    # Derive og_title and og_description from company_name if not explicitly set
    if not os.environ.get("BRANDING_OG_TITLE"):
        branding["og_title"] = f"{branding['company_name']} — Operations Center"
    else:
        branding["og_title"] = os.environ["BRANDING_OG_TITLE"]

    if not os.environ.get("BRANDING_OG_DESCRIPTION"):
        tagline = branding.get("tagline", "")
        branding["og_description"] = f"{branding['company_name']} — {tagline}" if tagline else f"{branding['company_name']} Operations Dashboard"
    else:
        branding["og_description"] = os.environ["BRANDING_OG_DESCRIPTION"]

    if os.environ.get("BRANDING_OG_IMAGE"):
        branding["og_image"] = os.environ["BRANDING_OG_IMAGE"]

    if os.environ.get("BRANDING_FAVICON_URL"):
        branding["favicon_url"] = os.environ["BRANDING_FAVICON_URL"]

    return branding
