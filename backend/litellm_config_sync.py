#!/usr/bin/env python3
"""
Federation-aware LiteLLM config sync sidecar.

Polls commander Ops-Center federation API every 30s to discover live LLM
services across the federation mesh. Generates a LiteLLM model_list config
that maps logical model names to live peer endpoints.

Uses stdlib urllib + requests (no async dependencies) for portability.

Usage:
  python3 litellm_config_sync.py [--interval 30] [--config-out /path/to/output.yaml]

Env vars:
  FEDERATION_API_BASE   - Ops-Center API base URL (default: http://localhost:8084)
  AUTH_TOKEN            - Bearer token for federation API
  LITELLM_MASTER_KEY    - LiteLLM master key for config reload
  LITELLM_ENDPOINT      - LiteLLM admin endpoint (default: http://uchub-litellm:4000)
"""

import argparse
import copy
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("litellm-sync")

DEFAULT_INTERVAL = 30
DEFAULT_CONFIG_OUT = "/tmp/litellm_federation.yaml"
FEDERATION_API_BASE = os.environ.get("FEDERATION_API_BASE", "http://localhost:8084")
DEFAULT_LITELLM_ENDPOINT = os.environ.get("LITELLM_ENDPOINT", "http://uchub-litellm:4000")

SERVICE_TYPE_MAP = {"llm": "openai", "embeddings": "openai", "image_gen": "openai"}

DEFAULT_EXTERNAL_MODELS = [
    {
        "model_name": "deepseek-chat-openrouter",
        "litellm_params": {
            "model": "openrouter/deepseek/deepseek-chat-v3-0324",
            "api_key": "os.environ/OPENROUTER_API_KEY",
            "rpm": 500, "tpm": 500000,
        },
        "model_info": {"mode": "cloud", "tier": "paid", "cost_per_1k_tokens": 0.0014,
                       "max_tokens": 65536, "node": "openrouter",
                       "description": "DeepSeek Chat V3 (OpenRouter)"},
    },
    {
        "model_name": "claude-sonnet-openrouter",
        "litellm_params": {
            "model": "openrouter/anthropic/claude-sonnet-4-20250514",
            "api_key": "os.environ/OPENROUTER_API_KEY",
            "rpm": 500, "tpm": 400000,
        },
        "model_info": {"mode": "cloud", "tier": "paid", "cost_per_1k_tokens": 0.003,
                       "max_tokens": 8192, "node": "openrouter",
                       "description": "Claude Sonnet 4 (OpenRouter)"},
    },
    {
        "model_name": "gpt-4o-openrouter",
        "litellm_params": {
            "model": "openrouter/openai/gpt-4o",
            "api_key": "os.environ/OPENROUTER_API_KEY",
            "rpm": 500, "tpm": 300000,
        },
        "model_info": {"mode": "cloud", "tier": "paid", "cost_per_1k_tokens": 0.005,
                       "max_tokens": 16384, "node": "openrouter",
                       "description": "GPT-4o (OpenRouter)"},
    },
    {
        "model_name": "deepseek-r1-openrouter",
        "litellm_params": {
            "model": "openrouter/deepseek/deepseek-r1",
            "api_key": "os.environ/OPENROUTER_API_KEY",
            "rpm": 200, "tpm": 200000,
        },
        "model_info": {"mode": "cloud", "tier": "paid", "cost_per_1k_tokens": 0.008,
                       "max_tokens": 65536, "node": "openrouter",
                       "description": "DeepSeek R1 (OpenRouter)"},
    },
    {
        "model_name": "claude-sonnet-direct",
        "litellm_params": {"model": "claude-3-5-sonnet-20241022",
                           "api_key": "os.environ/ANTHROPIC_API_KEY", "rpm": 50, "tpm": 50000},
        "model_info": {"mode": "cloud", "tier": "paid", "cost_per_1k_tokens": 0.003,
                       "max_tokens": 8192, "node": "anthropic", "description": "Claude Sonnet (direct)"},
    },
    {
        "model_name": "gpt-4o-direct",
        "litellm_params": {"model": "gpt-4o", "api_key": "os.environ/OPENAI_API_KEY", "rpm": 50, "tpm": 50000},
        "model_info": {"mode": "cloud", "tier": "paid", "cost_per_1k_tokens": 0.005,
                       "max_tokens": 16384, "node": "openai", "description": "GPT-4o (direct)"},
    },
]



def _parse_json_field(value, default=None):
    """Parse a field that might be a JSON string or already a dict/list."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default if default is not None else value
    return value


def _safe_model_name(model):
    return model.replace("/", "-").replace(" ", "_").replace(":", "-").lower()


def _normalize_api_base(endpoint_url, endpoint_path):
    base = endpoint_url.rstrip("/") if endpoint_url else ""
    path = (endpoint_path or "").lstrip("/")
    return f"{base}/{path}" if path else base


def fetch_federation_services(service_types=None, auth_token=None):
    """Synchronous federation service discovery. Returns list of service dicts."""
    if service_types is None:
        service_types = list(SERVICE_TYPE_MAP.keys())

    headers = {"accept": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    all_services = []
    session = requests.Session()

    for st in service_types:
        url = f"{FEDERATION_API_BASE}/api/v1/federation/services?service_type={st}"
        try:
            resp = session.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            services = data.get("services", data if isinstance(data, list) else [])
            all_services.extend(services)
        except requests.exceptions.HTTPError as exc:
            logger.warning("Federation API returned %s for %s: %s",
                         exc.response.status_code if exc.response else "?", st, exc)
        except Exception as exc:
            logger.warning("Failed to reach federation API for %s: %s", st, exc)

    return all_services


def build_model_list(federation_services, external_providers):
    model_list = []
    seen = set()

    for svc in federation_services:
        node_id = svc.get("node_id", "unknown")
        display_name = svc.get("display_name", node_id)
        endpoint_url = svc.get("endpoint_url", "")
        endpoint_path = svc.get("endpoint_path", "")
        service_type = svc.get("service_type", "llm")
        node_status = svc.get("node_status", "offline")

        # Parse models (may be JSON string)
        raw_models = svc.get("models", [])
        models = _parse_json_field(raw_models, [])
        if not isinstance(models, list):
            models = []

        # Parse capabilities (may be JSON string)
        caps = _parse_json_field(svc.get("capabilities", {}), {})
        if not isinstance(caps, dict):
            caps = {}

        if node_status == "offline":
            continue
        if not models:
            continue

        api_base = _normalize_api_base(endpoint_url, endpoint_path)
        if not api_base:
            logger.warning("Node %s has no resolvable endpoint", node_id)
            continue

        litellm_prefix = SERVICE_TYPE_MAP.get(service_type, "openai")

        for model in models:
            logical_name = _safe_model_name(model)
            litellm_model = f"{litellm_prefix}/{model}"
            if logical_name in seen:
                continue
            seen.add(logical_name)

            model_list.append({
                "model_name": logical_name,
                "litellm_params": {
                    "model": litellm_model,
                    "api_base": api_base,
                    "api_key": "not-needed",
                    "rpm": caps.get("max_rpm", 200),
                    "tpm": caps.get("max_tpm", 100000),
                },
                "model_info": {
                    "mode": "federation",
                    "tier": "free",
                    "cost_per_1k_tokens": svc.get("cost_usd", 0.0),
                    "max_tokens": caps.get("max_context", 8192),
                    "node": node_id,
                    "node_display": display_name,
                    "description": f"{model} @ {display_name} ({node_id})",
                },
            })

    for ext in external_providers:
        name = ext.get("model_name", "")
        if name in seen:
            continue
        seen.add(name)
        model_list.append(ext)

    logger.info("Model list: %d federation + %d external = %d total",
                len(model_list) - len(external_providers), len(external_providers), len(model_list))
    return model_list


def merge_with_static_config(federation_model_list, static_config_path):
    """Read the static config, prepend federation models, preserve everything else.
    
    Federation models are prepended so they match before wildcard entries.
    Static model_list entries are kept as-is (no dedup, so wildcards stay).
    Federation models that share a model_name with a static entry replace it.
    """
    with open(static_config_path) as fh:
        static_config = yaml.safe_load(fh) or {}

    if not isinstance(static_config, dict):
        logger.warning("Static config is not a dict, treating as empty")
        static_config = {}

    static_models = static_config.get("model_list", [])
    if not isinstance(static_models, list):
        static_models = []

    # Build lookup of static model names for dedup (federation wins)
    static_names = set()
    for m in static_models:
        name = m.get("model_name", "") if isinstance(m, dict) else ""
        if name:
            static_names.add(name)

    # Prepend federation models, replacing same-named static entries
    merged_models = list(federation_model_list)
    fed_names = {m.get("model_name", "") for m in merged_models if isinstance(m, dict)}

    for sm in static_models:
        name = sm.get("model_name", "") if isinstance(sm, dict) else ""
        if name and name not in fed_names:
            merged_models.append(sm)
            fed_names.add(name)

    # Build merged config — preserve everything from static, replace model_list
    merged_config = copy.deepcopy(static_config)
    merged_config["model_list"] = merged_models

    logger.info("Merged config: %d federation, %d static (total %d models)",
                len(federation_model_list), len(static_models), len(merged_models))
    return merged_config


def generate_config_yaml(model_list, static_config_path=None):
    if static_config_path:
        config = merge_with_static_config(model_list, static_config_path)
    else:
        config = {
            "model_list": model_list,
            "general_settings": {"master_key": "os.environ/LITELLM_MASTER_KEY"},
            "litellm_settings": {
                "num_retries": 2, "timeout": 120, "retry_after": 5,
                "fallbacks": True, "drop_params": True, "set_verbose": False,
            },
        }
    return yaml.dump(config, default_flow_style=False, sort_keys=False, width=120)


def _auth_headers(master_key):
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    if master_key:
        headers["Authorization"] = f"Bearer {master_key}"
    return headers


def load_state(state_file):
    """Load the JSON state file mapping model_name -> model_id."""
    if os.path.exists(state_file):
        try:
            with open(state_file) as fh:
                return json.load(fh)
        except (json.JSONDecodeError, IOError):
            logger.warning("Failed to read state file %s, starting fresh", state_file)
    return {}


def save_state(state_file, data):
    """Save the JSON state file."""
    tmp = state_file + ".tmp"
    try:
        with open(tmp, "w") as fh:
            json.dump(data, fh)
        os.rename(tmp, state_file)
    except IOError as exc:
        logger.warning("Failed to write state file %s: %s", state_file, exc)


def register_model(litellm_endpoint, master_key, model_entry):
    """Register a single model via POST /model/new. Returns model_id or None."""
    try:
        resp = requests.post(
            f"{litellm_endpoint}/model/new",
            headers=_auth_headers(master_key),
            json=model_entry,
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            model_id = data.get("model_id") or data.get("model_info", {}).get("id", "")
            logger.debug("Registered %s -> %s", model_entry.get("model_name"), model_id)
            return model_id
        logger.warning("/model/new returned %d for %s: %s",
                       resp.status_code, model_entry.get("model_name"), resp.text[:200])
    except Exception as exc:
        logger.warning("Failed to register model %s: %s", model_entry.get("model_name"), exc)
    return None


def deregister_model(litellm_endpoint, master_key, model_id):
    """Remove a model via POST /model/delete. Returns True on success."""
    try:
        resp = requests.post(
            f"{litellm_endpoint}/model/delete",
            headers=_auth_headers(master_key),
            json={"id": model_id},
            timeout=10,
        )
        if resp.status_code == 200:
            logger.debug("Deregistered model_id=%s", model_id)
            return True
        logger.warning("/model/delete returned %d for %s: %s",
                       resp.status_code, model_id, resp.text[:200])
    except Exception as exc:
        logger.warning("Failed to deregister model %s: %s", model_id, exc)
    return False


def sync_models_via_api(litellm_endpoint, master_key, desired_models, state):
    """Sync federation models via /model/new and /model/delete.
    
    Returns updated state dict.
    """
    desired_names = {m["model_name"] for m in desired_models}
    current_names = set(state.keys())

    # Remove stale models
    stale = current_names - desired_names
    for name in sorted(stale):
        model_id = state.pop(name, None)
        if model_id:
            if deregister_model(litellm_endpoint, master_key, model_id):
                logger.info("Removed stale model: %s", name)
            else:
                # Don't lose the ID on failure — retry next cycle
                state[name] = model_id

    # Add new models
    new_names = desired_names - set(state.keys())
    added = 0
    for model_entry in desired_models:
        name = model_entry["model_name"]
        if name not in new_names:
            continue
        model_id = register_model(litellm_endpoint, master_key, model_entry)
        if model_id:
            state[name] = model_id
            added += 1

    if added > 0:
        logger.info("Registered %d new federation models", added)
    return state


_shutting_down = False


def _handle_signal(signum, frame):
    global _shutting_down
    logger.info("Signal %s received, shutting down...", signum)
    _shutting_down = True


def run_sync_loop(config_out, interval, auth_token, litellm_endpoint, litellm_master_key,
                  static_config_path=None, state_file=None):
    if not state_file:
        state_file = os.path.join(os.path.dirname(config_out), "litellm_sync_state.json")

    state = load_state(state_file)
    logger.info("Loaded state: %d models tracked", len(state))

    while not _shutting_down:
        try:
            services = fetch_federation_services(auth_token=auth_token)
            desired_models = build_model_list(services, DEFAULT_EXTERNAL_MODELS)
            state = sync_models_via_api(litellm_endpoint, litellm_master_key, desired_models, state)
            save_state(state_file, state)

            # Also write the federation config file for reference/debugging
            yaml_str = generate_config_yaml(desired_models, static_config_path)
            header = (
                f"# Auto-generated by litellm_config_sync.py\n"
                f"# Generated: {datetime.now(timezone.utc).isoformat()}\n"
                f"# Federation peers: {len(services)}\n"
                f"# Total federation models: {len(desired_models)}\n"
                f"# Models synced via API: {len(state)}\n\n"
            )
            with open(config_out, "w") as fh:
                fh.write(header)
                fh.write(yaml_str)

            logger.info("Sync complete: %d models active via API", len(state))
        except Exception as exc:
            logger.error("Error in sync loop: %s", exc, exc_info=True)

        for _ in range(interval):
            if _shutting_down:
                break
            time.sleep(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    parser = argparse.ArgumentParser(description="Federation-aware LiteLLM config sync")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL)
    parser.add_argument("--config-out", default=DEFAULT_CONFIG_OUT)
    parser.add_argument("--static-config", default=os.environ.get("STATIC_CONFIG"),
                        help="Path to static LiteLLM config for merging (optional)")
    parser.add_argument("--state-file", default=os.environ.get("STATE_FILE"),
                        help="Path to state file tracking registered model IDs")
    parser.add_argument("--auth-token", default=os.environ.get("AUTH_TOKEN"))
    parser.add_argument("--litellm-master-key", default=os.environ.get("LITELLM_MASTER_KEY"))
    parser.add_argument("--litellm-endpoint", default=DEFAULT_LITELLM_ENDPOINT)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--once-reset", action="store_true",
                        help="With --once: deregister all tracked models first, then re-register")
    args = parser.parse_args()

    if args.once:
        services = fetch_federation_services(auth_token=args.auth_token)
        model_list = build_model_list(services, DEFAULT_EXTERNAL_MODELS)
        yaml_str = generate_config_yaml(model_list, args.static_config)
        header = f"# Generated: {datetime.now(timezone.utc).isoformat()}\n"
        with open(args.config_out, "w") as fh:
            fh.write(header)
            fh.write(yaml_str)
        print(f"Built {len(model_list)} federation models -> {args.config_out}")
        print(f"  Federation services discovered: {len(services)}")
        print(f"  Static config: {'merged' if args.static_config else 'not used'}")

        state_file = args.state_file or os.path.join(os.path.dirname(args.config_out),
                                                     "litellm_sync_state.json")
        if args.once_reset:
            state = load_state(state_file)
            print(f"  Resetting: deregistering {len(state)} tracked models...")
            for name, model_id in list(state.items()):
                deregister_model(args.litellm_endpoint, args.litellm_master_key, model_id)
            state = {}
            save_state(state_file, state)
            print("  All models deregistered.")

        state = load_state(state_file)
        state = sync_models_via_api(args.litellm_endpoint, args.litellm_master_key,
                                    model_list, state)
        save_state(state_file, state)
        print(f"  Models now registered via API: {len(state)}")
    else:
        state_file = args.state_file or os.path.join(os.path.dirname(args.config_out),
                                                     "litellm_sync_state.json")
        logger.info("Starting litellm_config_sync (interval=%ds, output=%s, static=%s)",
                     args.interval, args.config_out,
                     args.static_config or "none")
        run_sync_loop(
            config_out=args.config_out,
            interval=args.interval,
            auth_token=args.auth_token,
            litellm_endpoint=args.litellm_endpoint,
            litellm_master_key=args.litellm_master_key,
            static_config_path=args.static_config,
            state_file=state_file,
        )
