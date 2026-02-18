from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Depends, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse, HTMLResponse, Response, RedirectResponse
import psutil
import docker
import asyncio
import json
import os
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import GPUtil
import aiofiles
from pydantic import BaseModel
from fastapi import UploadFile, File
import httpx
import yaml
from pathlib import Path
import hashlib
import shutil
from collections import defaultdict
import re
import logging
from server_docker_manager import DockerServiceManager
from quick_docker_fix import get_running_services
from network_manager import network_manager
from ai_model_manager import ai_model_manager, ModelSettingsUpdate, ModelDownloadRequest
from storage_manager import storage_backup_manager, StorageInfo, BackupConfig, BackupInfo, BackupStatus
from extension_manager import extension_manager, ExtensionInstallRequest, ExtensionActionRequest, ExtensionConfigUpdate
from log_manager import log_manager, LogFilter, LogExportRequest
from auth_manager import auth_manager, UserCreate, UserUpdate, PasswordChange, LoginCredentials, APIKeyCreate
from hardware_info import hardware_detector
from update_manager import github_update_manager
from fastapi.responses import RedirectResponse
import secrets
import base64
from landing_config import landing_config
from system_manager import (
    system_manager,
    NetworkConfig,
    NetworkStatus,
    SystemPasswordChange,
    PackageList
)
from system_detector import system_detector, get_system_capabilities
from role_mapper import add_role_to_user_info, map_keycloak_role
from csrf_protection import create_csrf_protection, get_csrf_token
from rate_limiter import rate_limiter, rate_limit, check_rate_limit_manual
from audit_logger import audit_logger
from request_id_middleware import RequestIDMiddleware
from audit_endpoints import router as audit_router
from audit_helpers import (
    log_auth_success, log_auth_failure, log_logout,
    log_service_operation, log_permission_denied,
    get_client_ip, get_user_agent
)
from password_policy import validate_password, check_password_strength, get_password_requirements
from service_discovery import service_discovery
from lago_webhooks import router as lago_webhook_router
from webhooks import router as stripe_webhooks_router
from byok_api import router as byok_router
from tier_enforcement_middleware import TierEnforcementMiddleware
from credit_deduction_middleware import CreditDeductionMiddleware
from usage_api import router as usage_router
from admin_subscriptions_api import router as admin_subscriptions_router
from tier_check_middleware import router as tier_check_router
from subscription_api import router as subscription_router
from subscription_management_api import router as subscription_management_router
from stripe_api import router as stripe_router
from billing_api import router as billing_router
from payment_methods_api import router as payment_methods_router
from credit_api import router as credit_router
from credit_purchase_api import router as credit_purchase_router
from local_user_api import router as local_user_router
from org_api import router as org_router
from org_access_api import router as org_access_router
from org_manager import org_manager
from org_billing_api import router as org_billing_router
from org_features_api import router as org_features_router
from firewall_api import router as firewall_router
from cloudflare_api import router as cloudflare_router
from migration_api import router as migration_router
from credential_api import router as credential_router
from keycloak_status_api import router as keycloak_status_router
from litellm_routing_api import router as litellm_routing_router
from litellm_api import router as litellm_api_router  # Chat completions, credits, BYOK
from model_catalog_api import router as model_catalog_router  # Model catalog API
from model_access_api import router as model_access_router  # Model access control (Epic 3.3)
from litellm_credit_system import CreditSystem
from byok_manager import BYOKManager
import asyncpg
import redis.asyncio as aioredis
from local_users_api import router as admin_local_users_router
from platform_settings_api import router as platform_settings_router
from user_management_api import router as user_management_router
# TODO: Install Pillow dependency before enabling avatar storage
# from avatar_storage import router as avatar_storage_router  # Avatar storage & caching
from redis_session import redis_session_manager
from account_management_api import router as account_management_router
from subscription_tiers_api import router as subscription_tiers_router
from tier_features_api import router as tier_features_router
from app_definitions_api import router as app_definitions_router
from routers.forgejo import router as forgejo_router

# Local Inference Module (GPU/Model Management)
from routers.local_inference import router as local_inference_router

# RAG Services (Infinity Embedding/Reranker Proxy)
from routers.rag_services import router as rag_services_router

# GPU Services (Unified Infinity + Granite Management)
from routers.gpu_services import router as gpu_services_router

# Granite API Keys Management
from routers.granite_keys import router as granite_keys_router

# Billing Analytics API
from billing_analytics_api import router as billing_analytics_router

# Model List Management API
from model_list_api import admin_router as model_list_admin_router
from model_list_api import user_router as model_list_user_router
from model_list_api import public_router as model_list_public_router

# Invite Code System (VIP Founder)
from invite_codes_api import admin_router as invite_codes_admin_router
from invite_codes_api import user_router as invite_codes_user_router

# Email Notification System (Epic 2.3)
from email_scheduler import EmailScheduler
from email_notification_api import router as notification_router
from email_provider_api import router as email_provider_router

# Email Alert System (Epic 2.5 - Agent 2)
from email_alerts_api import router as email_alerts_router

# Alert Trigger System (Epic 2.5 - Agent 3)
from alert_triggers_api import router as alert_triggers_router

# Extensions Marketplace API - Phase 1 MVP (NEW)
from extensions_catalog_api import router as extensions_catalog_router
from my_apps_api import router as my_apps_router
from extensions_cart_api import router as extensions_cart_router
from extensions_purchase_api import router as extensions_purchase_router
from extensions_admin_api import router as extensions_admin_api_router

# Advanced Log Search API (Epic 2.5)
from logs_search_api import router as logs_search_router

# System Metrics & Health Monitoring (Epic 2.5)
from system_metrics_api import router as system_metrics_router
from metrics_collector import MetricsCollector
from alert_manager import AlertManager
# Grafana Integration (Monitoring Team)
from grafana_api import router as grafana_router

# Umami Analytics Integration (Epic 2.5 - Monitoring)
from umami_api import router as umami_router

# Umami Dashboard API (January 2026)
from routers.umami import router as umami_dashboard_router

# Website Uptime Monitor (January 2026)
from routers.website_monitor import router as website_monitor_router

# Alerts Management API (January 2026)
from routers.alerts_api import router as alerts_router

# Webhooks Management API (January 2026)
from routers.webhooks_api import router as webhooks_router

# System Audit Log API (January 2026)
from routers.audit_api import admin_router as audit_admin_router, internal_router as audit_internal_router

# Prometheus Monitoring API (Epic 3.1)
from prometheus_api import router as prometheus_router

# Revenue Analytics (Epic 2.6)
from revenue_analytics import router as revenue_analytics_router

# User Analytics (Epic 2.6)
from user_analytics import router as user_analytics_router

# Usage Analytics (Epic 2.6)
from usage_analytics import router as usage_analytics_router

# Supplementary Analytics & Metering (November 2025)
from routers.analytics import (
    revenue_router as analytics_revenue_router,
    users_router as analytics_users_router,
    services_router as analytics_services_router,
    metrics_router as analytics_metrics_router,
    performance_router as analytics_performance_router,
    main_router as analytics_main_router
)
from routers.metering import router as metering_router

# Model Management API (Sprint 6-7)
from model_management_api import router as model_management_router

# Permissions Management API (Sprint 6-7)
from permissions_management_api import router as permissions_management_router

# LLM Usage API (Sprint 6-7)
from llm_usage_api import router as llm_usage_router

# LLM Provider Settings API (Sprint 6-7)
from llm_provider_settings_api import router as llm_provider_settings_router

# LLM Provider Keys API (Epic 3.2 - Unified LLM Management)
from provider_keys_api import router as provider_keys_router

# UC API Keys & Platform Keys Management (November 2025)
from uc_api_keys import router as uc_api_keys_router
from platform_keys_api import router as platform_keys_router

# Service API Keys Management (January 2026) - GUI-configurable service-to-service auth
from service_keys_api import router as service_keys_router

# LLM Testing Lab API (Epic 3.2 - Unified LLM Management)
from testing_lab_api import router as testing_lab_router

# Traefik Services Detail API (Sprint 6-7)
from traefik_services_detail_api import router as traefik_services_detail_router

# API Documentation (Epic 2.8)
from api_docs import router as api_docs_router

# Performance Optimization (Epic 3.1)
from cache_middleware import CacheHeaderMiddleware, CompressionMiddleware
# Note: redis_cache_manager provides decorators for API endpoint caching (future use)

# Input Validation Middleware (P1 Security Fix)
from middleware.validation import InputValidationMiddleware

# Storage & Backup Management
from storage_backup_api import router as storage_backup_router
from restic_api_endpoints import router as restic_backup_router
# from backup_scheduler import backup_scheduler  # TODO: Install apscheduler in container first

# Traefik management APIs
from traefik_api import router as traefik_router
from traefik_routes_api import router as traefik_routes_router
from traefik_services_api import router as traefik_services_router
from traefik_ssl_manager import router as traefik_ssl_router
from traefik_metrics_api import router as traefik_metrics_router
from traefik_middlewares_api import router as traefik_middlewares_router
from traefik_live_api import router as traefik_live_router  # NEW: Live data from Docker labels

# Brigade Integration API (H23)
from brigade_api import router as brigade_router

# System Metrics & Analytics (Epic 2.5)
from system_metrics_api import router as system_metrics_router
from metrics_collector import MetricsCollector

# The Colonel AI Command System (Phase 1)
from routers.colonel import router as colonel_router
from colonel.websocket_gateway import colonel_gateway
from colonel.a2a_server import router as colonel_a2a_router

# White-Label Configuration API
from white_label_api import router as white_label_router

# Landing Page Settings API
from landing_page_settings_api import router as landing_settings_router

# Keycloak SSO integration
try:
    from keycloak_integration import (
        create_user as keycloak_create_user,
        set_user_password as keycloak_set_password,
        get_user_by_email as keycloak_get_user_by_email,
        get_user_by_username as keycloak_get_user_by_username,
        set_subscription_tier as keycloak_set_subscription_tier
    )
    KEYCLOAK_ENABLED = True
except ImportError:
    print("Keycloak integration not available")
    KEYCLOAK_ENABLED = False

# Two-Factor Authentication Management API (Priority 1 Polish)
from two_factor_api import router as two_factor_router

# OAuth settings from environment
EXTERNAL_HOST = os.environ.get("EXTERNAL_HOST", "192.168.1.135")
EXTERNAL_PROTOCOL = os.environ.get("EXTERNAL_PROTOCOL", "http")
OAUTH_CLIENT_ID = "ops-center"
OAUTH_CLIENT_SECRET = os.environ.get("OPS_CENTER_OAUTH_CLIENT_SECRET", "a1b2c3d4e5f6789012345678901234567890abcd")
# When using HTTPS (via Traefik), don't include port since Traefik handles the mapping
# When using HTTP (local dev), include port :8084
if EXTERNAL_PROTOCOL == "https":
    OAUTH_REDIRECT_URI = f"{EXTERNAL_PROTOCOL}://{EXTERNAL_HOST}/auth/callback"
else:
    OAUTH_REDIRECT_URI = f"{EXTERNAL_PROTOCOL}://{EXTERNAL_HOST}:8084/auth/callback"

# Session storage - Redis-backed with 2-hour TTL
# Configuration: REDIS_HOST=unicorn-redis, REDIS_PORT=6379, SESSION_TTL=7200
sessions = redis_session_manager

# Security Feature Toggles
CSRF_ENABLED = os.environ.get("CSRF_ENABLED", "true").lower() == "true"
CSRF_SECRET_KEY = os.environ.get("CSRF_SECRET_KEY", secrets.token_hex(32))
RATE_LIMIT_ENABLED = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
AUDIT_ENABLED = os.environ.get("AUDIT_ENABLED", "true").lower() == "true"
PASSWORD_POLICY_ENABLED = os.environ.get("PASSWORD_POLICY_ENABLED", "true").lower() == "true"
TIER_ENFORCEMENT_ENABLED = os.environ.get("TIER_ENFORCEMENT_ENABLED", "true").lower() == "true"
COOKIE_SECURE = EXTERNAL_PROTOCOL == "https"

# Enhanced monitoring imports
try:
    from resource_monitor import ResourceMonitor
    resource_monitor = ResourceMonitor()
    ENHANCED_MONITORING = True
except ImportError:
    print("Enhanced monitoring not available, using basic monitoring")
    ENHANCED_MONITORING = False

try:
    from deployment_config import DeploymentService
    deployment_service = DeploymentService()
    DEPLOYMENT_CONFIG = True
except ImportError:
    print("Deployment config not available, using defaults")
    DEPLOYMENT_CONFIG = False

app = FastAPI(title="UC-1 Pro Admin Dashboard API")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["1000/hour"])
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Add input validation middleware (P1 Security Fix)
app.add_middleware(InputValidationMiddleware)
logger.info("Input validation middleware enabled (P1 Security Fix)")

# Add rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please wait before making more requests."}
    )

# Initialize Docker service manager
docker_manager = DockerServiceManager()


# Helper function to get user organization context
async def get_user_org_context(user_id: str, email: str = None) -> dict:
    """
    Get organization context for a user from Keycloak attributes or database.

    Args:
        user_id: Keycloak user ID (sub claim)
        email: User's email (optional, for lookup if needed)

    Returns:
        Dictionary with org_id, org_name, org_role
        Returns default values if user has no organization
    """
    # Helper function to check database for organization membership
    async def check_database_membership(uid: str) -> dict:
        """Check PostgreSQL for organization membership.

        uid can be either:
        - Keycloak sub (zitadel_id) - needs to be looked up first
        - Internal user ID - can be used directly
        """
        try:
            # Use the app's database pool if available
            if hasattr(app.state, 'db_pool') and app.state.db_pool:
                async with app.state.db_pool.acquire() as conn:
                    # First, try to find org membership by joining through users table
                    # This handles Keycloak sub (zitadel_id) -> internal user ID -> org membership
                    result = await conn.fetchrow("""
                        SELECT om.org_id, om.role, o.name as org_name
                        FROM users u
                        JOIN organization_members om ON u.id::text = om.user_id
                        JOIN organizations o ON om.org_id = o.id
                        WHERE u.zitadel_id = $1
                        LIMIT 1
                    """, uid)

                    if result:
                        logger.info(f"Found org membership in database for Keycloak user {uid}: {result['org_id']}")
                        return {
                            "org_id": str(result["org_id"]),
                            "org_name": result["org_name"],
                            "org_role": result["role"].lower() if result["role"] else "member"
                        }

                    # Fallback: try direct user_id lookup (for internal IDs)
                    result = await conn.fetchrow("""
                        SELECT om.org_id, om.role, o.name as org_name
                        FROM organization_members om
                        JOIN organizations o ON om.org_id = o.id
                        WHERE om.user_id = $1
                        LIMIT 1
                    """, uid)

                    if result:
                        logger.info(f"Found org membership in database for user {uid}: {result['org_id']}")
                        return {
                            "org_id": str(result["org_id"]),
                            "org_name": result["org_name"],
                            "org_role": result["role"].lower() if result["role"] else "member"
                        }
            else:
                logger.warning("Database pool not available for org membership lookup")
        except Exception as db_err:
            logger.error(f"Database lookup for org membership failed: {db_err}")

        return {"org_id": None, "org_name": None, "org_role": None}

    try:
        # Import here to avoid circular dependency
        from keycloak_integration import get_user_by_email, _get_attr_value

        # First, try Keycloak lookup
        org_id = None
        org_name = None
        org_role = "member"

        if email:
            user = await get_user_by_email(email)
            if user:
                # Extract organization attributes from Keycloak user
                attrs = user.get("attributes", {})
                org_id = _get_attr_value(attrs, "org_id")
                org_name = _get_attr_value(attrs, "org_name")
                org_role = _get_attr_value(attrs, "org_role", "member")
            else:
                logger.warning(f"User not found in Keycloak: {email}")
        else:
            logger.warning(f"Cannot fetch org context from Keycloak for user_id {user_id} without email")

        # If Keycloak doesn't have org info, check the database
        if not org_id and user_id:
            logger.info(f"Keycloak has no org info for user {user_id}, checking database...")
            db_result = await check_database_membership(user_id)
            if db_result.get("org_id"):
                return db_result

        # Fallback to file-backed org manager if database doesn't have membership
        if not org_id and user_id:
            try:
                from org_manager import org_manager
                user_orgs = org_manager.get_user_orgs(user_id)
                if user_orgs:
                    org = user_orgs[0]
                    org_role = org_manager.get_user_role_in_org(org.id, user_id) or "member"
                    logger.info(f"Found org membership in file store for user {user_id}: {org.id}")
                    return {
                        "org_id": org.id,
                        "org_name": org.name,
                        "org_role": org_role
                    }
            except Exception as org_err:
                logger.error(f"File store lookup for org membership failed: {org_err}")

        return {
            "org_id": org_id,
            "org_name": org_name,
            "org_role": org_role
        }
    except Exception as e:
        logger.error(f"Error getting user org context: {e}")
        return {
            "org_id": None,
            "org_name": None,
            "org_role": "member"
        }


async def auto_provision_user_org(user_id: str, email: Optional[str], display_name: str) -> dict:
    """
    Create a default organization and assign the user as owner when no org is found.
    Mirrors signup provisioning for Keycloak-only users.
    """
    from org_manager import org_manager

    # Build a unique org name
    base_name = f"{display_name}'s Organization" if display_name else "My Organization"
    org_name = base_name
    attempt = 1
    while True:
        try:
            org_id = org_manager.create_organization(
                name=org_name,
                plan_tier="founders_friend"
            )
            break
        except ValueError as e:
            if "already exists" not in str(e).lower() or attempt >= 5:
                raise
            attempt += 1
            org_name = f"{base_name} ({attempt})"

    # Add user as owner
    org_manager.add_user_to_org(
        org_id=org_id,
        user_id=user_id,
        role="owner"
    )

    # Write to Postgres for org-centric APIs (best-effort)
    try:
        if hasattr(app.state, 'db_pool') and app.state.db_pool:
            async with app.state.db_pool.acquire() as conn:
                # Detect available columns to support multiple schema variants
                org_columns = await conn.fetch(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'organizations'
                    """
                )
                org_column_names = {row["column_name"] for row in org_columns}

                def slugify(value: str) -> str:
                    return re.sub(r"[^a-z0-9-]", "", value.lower().replace(" ", "-"))

                org_values = {
                    "id": org_id,
                    "name": org_name,
                    "display_name": org_name,
                    "slug": slugify(org_name) if "slug" in org_column_names else None,
                    "plan_tier": "founders_friend",
                    "status": "active",
                    "is_active": True,
                    "max_seats": 1,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }

                insert_org_cols = [c for c in org_values if c in org_column_names]
                if "id" in insert_org_cols and "name" in insert_org_cols:
                    placeholders = ", ".join(f"${i}" for i in range(1, len(insert_org_cols) + 1))
                    cols_sql = ", ".join(insert_org_cols)
                    values = [org_values[c] for c in insert_org_cols]
                    await conn.execute(
                        f"""
                        INSERT INTO organizations ({cols_sql})
                        VALUES ({placeholders})
                        ON CONFLICT (id) DO NOTHING
                        """,
                        *values
                    )

                member_columns = await conn.fetch(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'organization_members'
                    """
                )
                member_column_names = {row["column_name"] for row in member_columns}

                org_id_column = "org_id" if "org_id" in member_column_names else (
                    "organization_id" if "organization_id" in member_column_names else None
                )

                if org_id_column and "user_id" in member_column_names and "role" in member_column_names:
                    member_values = {
                        org_id_column: org_id,
                        "user_id": user_id,
                        "role": "owner",
                        "joined_at": datetime.utcnow(),
                        "is_active": True
                    }
                    insert_member_cols = [c for c in member_values if c in member_column_names]
                    member_placeholders = ", ".join(f"${i}" for i in range(1, len(insert_member_cols) + 1))
                    member_cols_sql = ", ".join(insert_member_cols)
                    member_values_list = [member_values[c] for c in insert_member_cols]
                    await conn.execute(
                        f"""
                        INSERT INTO organization_members ({member_cols_sql})
                        VALUES ({member_placeholders})
                        ON CONFLICT DO NOTHING
                        """,
                        *member_values_list
                    )
    except Exception as db_error:
        logger.error(f"Failed to write org provisioning data to Postgres: {db_error}")

    # Update Keycloak attributes if available
    if KEYCLOAK_ENABLED and email:
        try:
            from keycloak_integration import update_user_attributes
            await update_user_attributes(email, {
                "subscription_tier": ["trial"],
                "subscription_status": ["active"],
                "org_id": [org_id],
                "org_name": [org_name],
                "org_role": ["owner"]
            })
        except Exception as keycloak_error:
            logger.error(f"Failed to update Keycloak attributes for {email}: {keycloak_error}")

    # Create Lago subscription for the organization (best-effort)
    try:
        from lago_integration import subscribe_org_to_plan, LagoIntegrationError
        subscription = await subscribe_org_to_plan(
            org_id=org_id,
            plan_code="founders_friend",
            org_name=org_name,
            email=email or "",
            user_id=user_id
        )
        if subscription and subscription.get("lago_id"):
            org_manager.update_org_billing_ids(
                org_id=org_id,
                lago_id=subscription.get("lago_id")
            )
    except LagoIntegrationError as lago_error:
        logger.error(f"Failed to create Lago subscription for org {org_id}: {lago_error}")
    except Exception as lago_error:
        logger.error(f"Unexpected error creating Lago subscription for org {org_id}: {lago_error}")

    # Create credit account (best-effort)
    try:
        from credit_system import credit_manager
        await credit_manager.initialize()
        await credit_manager.create_user_credits(
            user_id=email or user_id,
            tier="trial"
        )
    except Exception as credit_error:
        logger.error(f"Failed to create credit account during auto-provision for {email}: {credit_error}")

    logger.info(f"Auto-provisioned org {org_id} for user {user_id}")
    return {
        "org_id": org_id,
        "org_name": org_name,
        "org_role": "owner"
    }


# CORS configuration (Security Team - Nov 12, 2025)
# Restrict origins to known domains for security
allowed_origins = [
    "https://unicorncommander.ai",
    "https://api.unicorncommander.ai",
    "https://auth.unicorncommander.ai",
    "http://localhost:8084",
    "http://localhost:3000",
    "http://localhost:5173",  # Vite dev server
]

# Allow additional origins from environment variable
additional_origins = os.environ.get("ADDITIONAL_CORS_ORIGINS", "").split(",")
if additional_origins and additional_origins[0]:  # Check if not empty
    allowed_origins.extend([origin.strip() for origin in additional_origins if origin.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*", "X-CSRF-Token", "Authorization", "Content-Type"],
    expose_headers=["X-CSRF-Token", "X-Request-ID"],
)

# Enable GZip compression for faster response times
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request ID tracking middleware (Security Team - Nov 12, 2025)
app.add_middleware(RequestIDMiddleware)
logger.info("Request ID tracking middleware enabled")

# Cache middleware for performance optimization (Epic 3.1)
app.add_middleware(CacheHeaderMiddleware)
app.add_middleware(CompressionMiddleware)
logger.info("Cache middleware registered (Epic 3.1)")

# Rate limiting setup (Security Team - Nov 12, 2025)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, default_limits=["1000/hour"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
logger.info("Rate limiting enabled (1000 requests/hour default)")

# Session Management Middleware
from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET_KEY", secrets.token_urlsafe(32)),
    max_age=3600,  # 1 hour
    same_site="lax",
    https_only=COOKIE_SECURE
)

# CSRF Protection Middleware
csrf_protect, csrf_middleware_factory = create_csrf_protection(
    enabled=CSRF_ENABLED,
    secret_key=CSRF_SECRET_KEY,
    exempt_urls={
        "/auth/callback",
        "/auth/login",
        "/auth/logout",
        "/auth/register",  # Public signup endpoint
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/logout",
        "/api/v1/auth/callback",
        "/api/v1/auth/csrf-token",  # CSRF token endpoint must be accessible
        "/api/v1/webhooks/lago",  # Lago webhooks
        "/api/v1/billing/webhooks/stripe",  # Stripe webhooks
        "/api/v1/tier-check/health",  # Health checks
        "/api/v1/traefik",  # Traefik API (Epic 1.3) - REST API, not form submissions
        "/api/v1/analytics/web-vitals",  # Web Vitals tracking (Epic 3.1) - high-frequency analytics
        "/api/v1/llm/",  # LLM API endpoints - used by Brigade, Open-WebUI (API calls, not forms)
        "/api/llmcall",  # Bolt.DIY LLM proxy endpoint - external integration
        "/api/github-template",  # Bolt.DIY GitHub template proxy - external integration
        "/api/v1/email-provider/",  # Email provider API - testing and management
        "/api/v1/platform/",  # Platform settings API - credential management
        "/api/v1/pricing/",  # Dynamic pricing API - calculation endpoints (Nov 12, 2025)
        "/api/v1/monitoring/grafana/",  # Grafana integration API - monitoring endpoints
        "/api/v1/admin/users/",  # User management and API key endpoints - REST API operations
        "/api/v1/org/",  # Organization management API - CRUD operations
        "/api/v1/org",    # Organization management API (without trailing slash)
        "/api/v1/alerts/",  # Email alert system - REST API operations
        "/api/v1/logs/",  # Log search system - REST API operations
        "/api/v1/website-monitor/",  # Website uptime monitoring - REST API operations
        "/api/v1/umami/",  # Umami analytics dashboard - REST API operations
        "/api/v1/my-apps/",  # Apps marketplace - REST API operations
        "/api/v1/credits/",  # Credit system - REST API operations
        "/api/v1/subscriptions/",  # Subscription management - REST API operations
        "/api/v1/system/",  # System status - REST API operations
        "/api/v1/billing/",  # Billing analytics - REST API operations
    },
    sessions_store=sessions,
    cookie_secure=COOKIE_SECURE
)
app.add_middleware(csrf_middleware_factory)

# Tier Enforcement Middleware (after CSRF, before routes)
if TIER_ENFORCEMENT_ENABLED:
    app.add_middleware(TierEnforcementMiddleware)
    # Store sessions reference in app state for middleware access
    app.state.sessions = sessions
    logger.info("Tier Enforcement Middleware enabled")

# Credit Deduction Middleware (after Tier Enforcement, before routes)
# Automatically deducts credits for LLM API calls
app.add_middleware(CreditDeductionMiddleware)
logger.info("Credit Deduction Middleware enabled (automatic credit tracking)")

logger.info(f"CSRF Protection: {'Enabled' if CSRF_ENABLED else 'Disabled'}")
logger.info(f"Rate Limiting: {'Enabled' if RATE_LIMIT_ENABLED else 'Disabled'}")
logger.info(f"Audit Logging: {'Enabled' if AUDIT_ENABLED else 'Disabled'}")
logger.info(f"Password Policy: {'Enabled' if PASSWORD_POLICY_ENABLED else 'Disabled'}")
logger.info(f"Tier Enforcement: {'Enabled' if TIER_ENFORCEMENT_ENABLED else 'Disabled'}")

# Startup event handler
@app.on_event("startup")
async def startup_event():
    """Initialize security services on startup"""
    if AUDIT_ENABLED:
        try:
            await audit_logger.initialize()
            logger.info("Audit logging system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize audit logging: {e}")
            if not os.environ.get("AUDIT_FAIL_OPEN", "true").lower() == "true":
                raise

    if RATE_LIMIT_ENABLED:
        try:
            await rate_limiter.initialize()
            logger.info("Rate limiting system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize rate limiting: {e}")
            if not os.environ.get("RATE_LIMIT_FAIL_OPEN", "true").lower() == "true":
                raise

    # Initialize LiteLLM credit system (CRITICAL for Brigade integration)
    try:
        # Create PostgreSQL connection pool
        db_pool = await asyncpg.create_pool(
            host=os.getenv('POSTGRES_HOST', 'unicorn-postgresql'),
            port=int(os.getenv('POSTGRES_PORT', '5432')),
            user=os.getenv('POSTGRES_USER', 'unicorn'),
            password=os.getenv('POSTGRES_PASSWORD', 'unicorn'),
            database=os.getenv('POSTGRES_DB', 'unicorn_db'),
            min_size=2,
            max_size=10
        )
        logger.info("PostgreSQL connection pool created")

        # Create Redis client
        redis_url = os.getenv('REDIS_URL', f"redis://{os.getenv('REDIS_HOST', 'unicorn-redis')}:{os.getenv('REDIS_PORT', '6379')}")
        redis_client = aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info(f"Connecting to Redis at: {redis_url}")
        await redis_client.ping()  # Test connection
        logger.info("Redis client connected")

        # Initialize credit system
        credit_system = CreditSystem(db_pool, redis_client)
        app.state.credit_system = credit_system
        app.state.db_pool = db_pool  # Store for cleanup
        app.state.redis_client = redis_client  # Store for cleanup
        logger.info("LiteLLM credit system initialized successfully")

        # Initialize BYOK manager (uses same db_pool)
        byok_manager = BYOKManager(db_pool)
        app.state.byok_manager = byok_manager
        logger.info("BYOK manager initialized successfully")

        # Initialize Model Access API dependencies (Epic 3.3)
        from model_access_api import init_dependencies as init_model_access_deps
        init_model_access_deps(db_pool, credit_system, byok_manager)
        logger.info("Model Access API dependencies initialized successfully")

        # Initialize API Key Manager (Epic: External App Authentication)
        from api_key_manager import initialize_api_key_manager
        await initialize_api_key_manager(db_pool)
        logger.info("API Key Manager initialized successfully")

        # Initialize Landing Page Settings API (Phase 2)
        # TODO: Re-enable when landing_page_settings_api module is implemented
        # from landing_page_settings_api import init_landing_settings
        # init_landing_settings(db_pool, redis_client)
        # logger.info("Landing Page Settings API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize credit system / BYOK / API keys: {e}")
        # Don't block startup, but credit-based features will fail
        app.state.credit_system = None
        app.state.byok_manager = None

    # Start email scheduler (Epic 2.3)
    try:
        email_scheduler = EmailScheduler()
        await email_scheduler.start()
        logger.info("Email scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start email scheduler: {e}")
        # Don't block startup if email fails

    # Start backup scheduler (TODO: Install apscheduler in container first)
    # try:
    #     backup_scheduler.start()
    #     logger.info("Backup scheduler started successfully")
    # except Exception as e:
    #     logger.error(f"Failed to start backup scheduler: {e}")

    # Start metrics collector (Epic 2.5)
    try:
        metrics_collector = MetricsCollector()
        asyncio.create_task(metrics_collector.start())
        logger.info("Metrics collector started successfully")
    except Exception as e:
        logger.error(f"Failed to start metrics collector: {e}")
        # Don't block startup if metrics collection fails

    # Start alert checker (Epic 2.5)
    try:
        from alert_manager import AlertManager
        alert_manager = AlertManager()
        asyncio.create_task(check_alerts_periodically())
        logger.info("Alert checker started successfully")
    except Exception as e:
        logger.error(f"Failed to start alert checker: {e}")
        # Don't block startup if alert checking fails


async def check_alerts_periodically():
    """
    Background task that checks for system alerts every 60 seconds.
    Epic 2.5: Admin Dashboard Polish - Analytics Lead
    """
    from alert_manager import AlertManager
    alert_manager = AlertManager()

    while True:
        try:
            await alert_manager.check_alerts()
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            logger.info("Alert checker stopped")
            break
        except Exception as e:
            logger.error(f"Alert check error: {e}")
            await asyncio.sleep(60)

# Shutdown event handler
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if RATE_LIMIT_ENABLED:
        try:
            await rate_limiter.close()
            logger.info("Rate limiter closed")
        except Exception as e:
            logger.error(f"Error closing rate limiter: {e}")

    # Close credit system connections
    if hasattr(app.state, 'db_pool') and app.state.db_pool:
        try:
            await app.state.db_pool.close()
            logger.info("PostgreSQL connection pool closed")
        except Exception as e:
            logger.error(f"Error closing database pool: {e}")

    if hasattr(app.state, 'redis_client') and app.state.redis_client:
        try:
            await app.state.redis_client.close()
            logger.info("Redis client closed")
        except Exception as e:
            logger.error(f"Error closing Redis client: {e}")

    # Stop backup scheduler (TODO: Install apscheduler in container first)
    # try:
    #     backup_scheduler.stop()
    #     logger.info("Backup scheduler stopped")
    # except Exception as e:
    #     logger.error(f"Error stopping backup scheduler: {e}")

# Register Model Access Control FIRST - Epic 3.3 (HIGH PRIORITY)
app.include_router(model_access_router)
logger.info("⭐ Model Access Control API registered at /api/v1/models (PRIORITY ROUTE)")

# Register audit logs router
if AUDIT_ENABLED:
    app.include_router(audit_router)
    logger.info("Audit logs API endpoints registered at /api/v1/audit")

# Register BYOK router
app.include_router(byok_router)

# Pass sessions store to BYOK router for authentication
from byok_api import set_sessions_store
set_sessions_store(sessions)
logger.info("BYOK API endpoints registered at /api/v1/keys")

# Register Lago webhooks router
app.include_router(lago_webhook_router)
logger.info("Lago webhooks registered at /api/v1/webhooks/lago")

# Register Stripe webhooks router (Epic 2.4)
app.include_router(stripe_webhooks_router)
logger.info("Stripe webhooks registered at /api/v1/webhooks/stripe/*")

# Register usage tracking API (always enabled for tier info)
app.include_router(usage_router)
logger.info("Usage tracking API endpoints registered at /api/v1/usage")

# Register admin subscription management router
app.include_router(admin_subscriptions_router)
logger.info("Admin subscription management registered at /api/v1/admin/subscriptions")

# Register tier check ForwardAuth router (for Traefik middleware)
app.include_router(tier_check_router)
logger.info("Tier check ForwardAuth endpoints registered at /api/v1/tier-check")

# Register user-facing subscription management router
app.include_router(subscription_router)
logger.info("Subscription management API endpoints registered at /api/v1/subscriptions")

# Register subscription change management (upgrade/downgrade/cancel)
app.include_router(subscription_management_router)
logger.info("Subscription change management endpoints registered at /api/v1/subscriptions (upgrade/downgrade/cancel)")

# Register Stripe payment integration router
app.include_router(stripe_router)
logger.info("Stripe payment API endpoints registered at /api/v1/billing")

# Register Lago billing/invoice endpoints
app.include_router(billing_router)
logger.info("Lago billing/invoice API endpoints registered at /api/v1/billing")

# Register payment methods management
app.include_router(payment_methods_router)
logger.info("Payment methods API endpoints registered at /api/v1/payment-methods")

# Extensions Marketplace API - Phase 1 MVP (NEW)
# NOTE: Purchase & Admin routers registered BEFORE catalog to avoid /{addon_id} catching specific routes
app.include_router(extensions_purchase_router)
logger.info("Extensions Purchase API endpoints registered at /api/v1/extensions/checkout, /api/v1/extensions/purchases")
app.include_router(extensions_admin_api_router)
logger.info("Extensions Admin API endpoints registered at /api/v1/admin/extensions")
app.include_router(extensions_cart_router)
logger.info("Extensions Cart API endpoints registered at /api/v1/cart")
app.include_router(extensions_catalog_router)
logger.info("Extensions Catalog API endpoints registered at /api/v1/extensions (includes /{addon_id})")

# My Apps API - Tier-filtered apps for authenticated users
app.include_router(my_apps_router)
logger.info("My Apps API endpoints registered at /api/v1/my-apps (RBAC-filtered)")

# Advanced Log Search API (Epic 2.5)
app.include_router(logs_search_router)
logger.info("Advanced Log Search API endpoints registered at /api/v1/logs/search/advanced, /api/v1/logs/services, /api/v1/logs/stats")

# Epic 1.8: Credit & Usage Metering System
app.include_router(credit_router)
logger.info("Credit & Usage Metering API endpoints registered at /api/v1/credits")

# Credit Purchase System (One-time purchases via Stripe)
app.include_router(credit_purchase_router)
logger.info("Credit Purchase API endpoints registered at /api/v1/billing/credits")

# Register Local User Management endpoints
app.include_router(local_user_router)
logger.info("Local User Management API endpoints registered at /api/v1/local-users")

# Register Organization Management endpoints
app.include_router(org_router)
logger.info("Organization Management API endpoints registered at /api/v1/org")

# Register Org-Centric Access endpoints (multi-tenancy)
app.include_router(org_access_router)
logger.info("Org-Centric Access API endpoints registered at /api/v1/users/me")

# Register Organization Billing endpoints
app.include_router(org_billing_router)
logger.info("Organization Billing API endpoints registered at /api/v1/org-billing")

# Register Organization Features Admin endpoints
app.include_router(org_features_router)
logger.info("Organization Features Admin API endpoints registered at /api/v1/admin/orgs/{org_id}/features")

# Register Firewall Management endpoints
app.include_router(firewall_router)
logger.info("Firewall Management API endpoints registered at /api/v1/network/firewall")

# Register Cloudflare DNS API endpoints
app.include_router(cloudflare_router)
logger.info("Cloudflare DNS API endpoints registered at /api/v1/cloudflare")

# Epic 1.7: NameCheap Migration Wizard
app.include_router(migration_router)
logger.info("Migration API endpoints registered at /api/v1/migration")

# Epic 1.6/1.7: Service Credential Management
app.include_router(credential_router)
logger.info("Credential management API endpoints registered at /api/v1/credentials")

# Invite Code System (Admin & User)
app.include_router(invite_codes_admin_router)
logger.info("Invite Codes Admin API endpoints registered at /api/v1/admin/invite-codes")
app.include_router(invite_codes_user_router)
logger.info("Invite Codes User API endpoints registered at /api/v1/invite-codes")

# Alerts Management (January 2026)
app.include_router(alerts_router)
logger.info("Alerts Management API endpoints registered at /api/v1/monitoring/alerts")

# Webhooks Management (January 2026)
app.include_router(webhooks_router)
logger.info("Webhooks Management API endpoints registered at /api/v1/admin/webhooks")

# System Audit Log (January 2026)
app.include_router(audit_admin_router)
app.include_router(audit_internal_router)
logger.info("System Audit Log API endpoints registered at /api/v1/admin/audit-log, /api/v1/audit/log")

# Keycloak Status API
app.include_router(keycloak_status_router)
logger.info("Keycloak status API endpoints registered at /api/v1/system/keycloak")

# User Management API (Keycloak users)
app.include_router(user_management_router)
logger.info("User Management API endpoints registered at /api/v1/admin/users")

# Account & System Management API (Missing endpoints fix - November 2025)
app.include_router(account_management_router)
logger.info("Account & System Management API endpoints registered")

# Avatar Storage API (November 2025 - CORS fix for bolt.diy)
# TODO: Uncomment when Pillow dependency is installed
# app.include_router(avatar_storage_router)
logger.info("Avatar storage API endpoints registered at /api/v1/users/{user_id}/avatar")

# Subscription Tier Management API (Epic 4.4)
app.include_router(subscription_tiers_router)
logger.info("Subscription Tier Management API endpoints registered at /api/v1/admin/tiers")

# Tier Features Association API
app.include_router(tier_features_router)
logger.info("Tier Features API endpoints registered at /api/v1/tiers/features")

# App Definitions Management API
app.include_router(app_definitions_router)
logger.info("App Definitions API endpoints registered at /api/v1/admin/apps")

# LiteLLM Routing and Provider Management API
app.include_router(admin_local_users_router)
logger.info("Admin Local User Management API endpoints registered at /api/v1/admin/system/local-users")
app.include_router(litellm_routing_router)
logger.info("LiteLLM routing API endpoints registered at /api/v1/llm")

# Forgejo integration
app.include_router(forgejo_router)
logger.info("Forgejo API endpoints registered at /api/v1/forgejo")

# Local Inference Module (GPU/Model Management) - January 2026
app.include_router(local_inference_router)
logger.info("Local Inference API endpoints registered at /api/v1/local-inference")

# RAG Services (Infinity Embedding/Reranker Proxy) - January 2026
app.include_router(rag_services_router)
logger.info("RAG Services API endpoints registered at /api/v1/rag-services")

# GPU Services (Unified Infinity + Granite Management) - January 2026
app.include_router(gpu_services_router)
logger.info("GPU Services API endpoints registered at /api/v1/gpu-services")

# Granite API Keys Management - February 2026
app.include_router(granite_keys_router)
logger.info("Granite API Keys endpoints registered at /api/v1/granite-keys")

# Billing Analytics API
app.include_router(billing_analytics_router)
logger.info("Billing Analytics API endpoints registered at /api/v1/billing/analytics")

# Model List Management API
app.include_router(model_list_admin_router)
app.include_router(model_list_user_router)
app.include_router(model_list_public_router)
logger.info("Model List Management API endpoints registered")

# Register LiteLLM API router
app.include_router(litellm_api_router)

# Pass sessions store to LiteLLM router for session-based authentication
from litellm_api import set_sessions_store as litellm_set_sessions_store
litellm_set_sessions_store(sessions)
logger.info("LiteLLM chat completions API endpoints registered at /api/v1/llm (chat/completions, credits, BYOK)")
app.include_router(model_catalog_router)
logger.info("Model Catalog API endpoints registered at /api/v1/llm (models, providers)")
# model_access_router already registered earlier (line ~547) - REMOVED DUPLICATE
app.include_router(provider_keys_router)
logger.info("Provider Keys API endpoints registered at /api/v1/llm/providers (keys management)")
app.include_router(testing_lab_router)
logger.info("Testing Lab API endpoints registered at /api/v1/llm/test (interactive testing)")

# UC API Keys & Platform Keys Management (November 2025)
app.include_router(uc_api_keys_router)
logger.info("UC API Keys endpoints registered at /api/v1/account/uc-api-keys")
app.include_router(platform_keys_router)
logger.info("Platform Keys Management endpoints registered at /api/v1/admin/platform-keys (Admin only)")

# Service API Keys Management (January 2026)
app.include_router(service_keys_router)
logger.info("Service Keys Management endpoints registered at /api/v1/admin/service-keys (Admin only)")

# Platform Settings API
app.include_router(platform_settings_router)
logger.info("Platform Settings API endpoints registered at /api/v1/platform")

# Traefik Configuration Management APIs (Epic 1.3)
app.include_router(traefik_router)
logger.info("Traefik Comprehensive API endpoints registered at /api/v1/traefik (Epic 1.3)")

# Traefik Live Data API (NEW - reads real Docker labels)
app.include_router(traefik_live_router)
logger.info("Traefik Live Data API endpoints registered at /api/v1/traefik/live")

# Legacy Traefik APIs (keep for backward compatibility)
app.include_router(traefik_routes_router)
logger.info("Traefik Routes API endpoints registered at /api/v1/traefik/routes")
app.include_router(traefik_services_router)
logger.info("Traefik Services API endpoints registered at /api/v1/traefik/services")
app.include_router(traefik_ssl_router)
logger.info("Traefik SSL Management API endpoints registered at /api/v1/traefik/ssl")
app.include_router(traefik_metrics_router)
logger.info("Traefik Metrics API endpoints registered at /api/v1/traefik/metrics")
app.include_router(traefik_middlewares_router)
logger.info("Traefik Middlewares API endpoints registered at /api/v1/traefik/middlewares")

# Brigade Integration API (H23)
app.include_router(brigade_router)
logger.info("Brigade Proxy API endpoints registered at /api/v1/brigade (H23)")

# Storage & Backup Management
app.include_router(storage_backup_router)
logger.info("Storage & Backup API endpoints registered at /api/v1/storage and /api/v1/backups")
app.include_router(restic_backup_router)
logger.info("Restic Backup API endpoints registered at /api/v1/backups/restic")

# Email Notification API (Epic 2.3)
app.include_router(notification_router)
logger.info("Email Notification API endpoints registered at /api/v1/notifications")

# Two-Factor Authentication Management API (Priority 1 Polish)
app.include_router(two_factor_router)
logger.info("Two-Factor Authentication API endpoints registered at /api/v1/admin/2fa")

# Email Provider Management API
app.include_router(email_provider_router)
logger.info("Email Provider API endpoints registered at /api/v1/email-provider")

# Email Alert System (Epic 2.5 - Agent 2)
app.include_router(email_alerts_router)
logger.info("Email Alert System API endpoints registered at /api/v1/alerts")

# Alert Trigger System (Epic 2.5 - Agent 3)
app.include_router(alert_triggers_router)
logger.info("Alert Trigger System API endpoints registered at /api/v1/alert-triggers")

# System Metrics API (Epic 2.5 - Admin Dashboard Polish)
app.include_router(system_metrics_router)
# Grafana API
app.include_router(grafana_router)
logger.info("Grafana API endpoints registered at /api/v1/monitoring/grafana")
logger.info("System Metrics API endpoints registered at /api/v1/system")

# Umami Analytics API (Epic 2.5 - Monitoring)
app.include_router(umami_router)
logger.info("Umami Analytics API endpoints registered at /api/v1/monitoring/umami")

# Umami Dashboard API (January 2026)
app.include_router(umami_dashboard_router)
logger.info("Umami Dashboard API endpoints registered at /api/v1/umami")

# Website Uptime Monitor (January 2026)
app.include_router(website_monitor_router)
logger.info("Website Monitor API endpoints registered at /api/v1/website-monitor")

# Prometheus Monitoring API (Epic 3.1)
app.include_router(prometheus_router)
logger.info("Prometheus Monitoring API endpoints registered at /api/v1/monitoring/prometheus")

# Supplementary Analytics & Metering (November 2025) - REGISTERED FIRST for priority
# Priority registration ensures mock data endpoints override old database-dependent endpoints
app.include_router(analytics_revenue_router)
app.include_router(analytics_users_router)  # PRIORITY: Mock endpoints (cohorts, growth) override old DB endpoints
app.include_router(analytics_services_router)
app.include_router(analytics_metrics_router)
app.include_router(analytics_performance_router)
app.include_router(analytics_main_router)
app.include_router(metering_router)
logger.info("Supplementary Analytics endpoints registered (PRIORITY - mock data):")
logger.info("  - Revenue: /api/v1/analytics/revenue/* (mrr, arr, growth, churn, forecast, by-tier)")
logger.info("  - Users: /api/v1/analytics/users/* (ltv, churn, acquisition, cohorts, growth)")
logger.info("  - Services: /api/v1/analytics/services/* (popularity, cost-per-user, adoption, performance, uptime, latency, errors)")
logger.info("  - Metrics: /api/v1/analytics/metrics/* (summary, kpis, alerts)")
logger.info("  - Performance: /api/v1/analytics/performance/* (metrics)")
logger.info("  - Main: /api/v1/analytics/summary")
logger.info("Metering endpoints registered (/api/v1/llm/usage/summary, /api/v1/llm/costs, /api/v1/metering/*)")

# Revenue Analytics API (Epic 2.6)
app.include_router(revenue_analytics_router)
logger.info("Revenue Analytics API endpoints registered at /api/v1/analytics/revenue")

# User Analytics API (Epic 2.6) - AFTER new router (non-conflicting endpoints only)
app.include_router(user_analytics_router)
logger.info("User Analytics API endpoints registered at /api/v1/analytics/users (non-conflicting only)")

# Usage Analytics API (Epic 2.6)
app.include_router(usage_analytics_router)
logger.info("Usage Analytics API endpoints registered at /api/v1/analytics/usage")

# Model Management API (Sprint 6-7) - TEMPORARILY DISABLED for Epic 3.3 testing
# CONFLICT: Both model_management_router and model_access_router use /api/v1/models prefix
# model_management_router has root route "/" which may interfere with model_access_router
# TODO: After Epic 3.3 works, either change prefix or merge routers
# app.include_router(model_management_router)
# logger.info("Model Management API endpoints registered at /api/v1/models")

# Permissions Management API (Sprint 6-7)
app.include_router(permissions_management_router)
logger.info("Permissions Management API endpoints registered at /api/v1/permissions")

# LLM Usage API (Sprint 6-7)
app.include_router(llm_usage_router)
logger.info("LLM Usage API endpoints registered at /api/v1/llm/usage")

# LLM Provider Settings API (Sprint 6-7)
app.include_router(llm_provider_settings_router)
logger.info("LLM Provider Settings API endpoints registered at /api/v1/llm/providers")

# Traefik Services Detail API (Sprint 6-7)
app.include_router(traefik_services_detail_router)
logger.info("Traefik Services Detail API endpoints registered at /api/v1/traefik/services")

# API Documentation (Epic 2.8)
app.include_router(api_docs_router)
logger.info("API Documentation endpoints registered at /api/v1/docs (Epic 2.8)")
logger.info("API Documentation endpoints registered at /api/v1/docs (Epic 2.8)")

# API Documentation (Epic 2.8)
app.include_router(api_docs_router)
logger.info("API Documentation endpoints registered at /api/v1/docs (Epic 2.8)")
logger.info("API Documentation endpoints registered at /api/v1/docs")

# White-Label Configuration API
app.include_router(white_label_router)
logger.info("White-Label Configuration API endpoints registered at /api/v1/admin/white-label")

# Landing Page Settings API
app.include_router(landing_settings_router)
logger.info("Landing Page Settings API endpoints registered at /api/v1/system/settings (public) and /api/v1/admin/settings (admin)")

# Dynamic Pricing Management API
from dynamic_pricing_api import router as dynamic_pricing_router
app.include_router(dynamic_pricing_router)

# Pricing Packages API (public pricing information)
from pricing_packages_api import router as pricing_packages_router
app.include_router(pricing_packages_router)
logger.info("Dynamic Pricing Management API endpoints registered at /api/v1/pricing")

# The Colonel AI Command System
app.include_router(colonel_router)
app.include_router(colonel_a2a_router)
logger.info("🎖️ Colonel AI Command System registered at /api/v1/colonel + A2A at /.well-known/agent.json")

# CSRF Token Endpoint removed - see line 2897 for the full implementation that handles unauthenticated users

# ============================================================================
# Bolt.DIY LLM Proxy Endpoint
# ============================================================================
# Provides a simple /api/llmcall endpoint that forwards to LiteLLM API
# This allows Bolt.DIY to make LLM calls without changing its configuration

@app.post("/api/llmcall", include_in_schema=False)
async def bolt_llm_proxy(request: Request):
    """
    Proxy endpoint for Bolt.DIY LLM calls
    Forwards POST /api/llmcall to /api/v1/llm/chat/completions
    """
    try:
        # Get request body
        body = await request.json()

        # Get Authorization header if present
        auth_header = request.headers.get("Authorization", "")

        # Import the chat completions handler from litellm_api
        from litellm_api import router as litellm_router

        # Forward to the LiteLLM chat completions endpoint
        # Create a new request with the same body and headers
        from fastapi import HTTPException
        import httpx

        # Call the internal LiteLLM API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:8084/api/v1/llm/chat/completions",
                json=body,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json"
                },
                timeout=300.0  # 5 minute timeout for long generations
            )

            # Return the response from LiteLLM
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )

    except Exception as e:
        logger.error(f"Bolt LLM proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Bolt.DIY GitHub Template Proxy Endpoint
# ============================================================================
# Fetches GitHub repository contents for Bolt starter templates

@app.get("/api/github-template", include_in_schema=False)
async def bolt_github_template_proxy(repo: str):
    """
    Proxy endpoint for Bolt.DIY GitHub template fetching
    Fetches repository contents from GitHub API and returns files
    """
    import httpx
    import base64

    try:
        logger.info(f"Fetching GitHub template: {repo}")

        # Parse repo (format: owner/repo)
        if "/" not in repo:
            raise HTTPException(status_code=400, detail="Invalid repo format. Expected: owner/repo")

        owner, repo_name = repo.split("/", 1)

        # GitHub API endpoint
        github_api_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents"

        async def fetch_repo_contents(path=""):
            """Recursively fetch all files from repo"""
            url = f"{github_api_url}/{path}" if path else github_api_url

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        "Accept": "application/vnd.github.v3+json",
                        "User-Agent": "Unicorn-Commander-Bolt"
                    },
                    timeout=30.0
                )

                if response.status_code != 200:
                    logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"GitHub API error: {response.text}"
                    )

                items = response.json()
                files = []

                for item in items:
                    if item["type"] == "file":
                        # Fetch file content
                        file_response = await client.get(
                            item["url"],
                            headers={
                                "Accept": "application/vnd.github.v3+json",
                                "User-Agent": "Unicorn-Commander-Bolt"
                            },
                            timeout=30.0
                        )

                        if file_response.status_code == 200:
                            file_data = file_response.json()
                            # Decode base64 content
                            content = base64.b64decode(file_data.get("content", "")).decode("utf-8", errors="ignore")
                            files.append({
                                "name": item["name"],
                                "path": item["path"],
                                "content": content
                            })

                    elif item["type"] == "dir":
                        # Recursively fetch directory contents
                        subfiles = await fetch_repo_contents(item["path"])
                        files.extend(subfiles)

                return files

        # Fetch all files
        files = await fetch_repo_contents()

        logger.info(f"Successfully fetched {len(files)} files from {repo}")
        return files

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub template proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Root redirect must be defined early to take precedence
@app.get("/", include_in_schema=False)
async def root_redirect(request: Request):
    """Show registration page or serve dashboard for authenticated users"""
    print("Root redirect handler called!")
    session_token = request.cookies.get("session_token")
    print(f"Session token from cookie: {session_token[:20] if session_token else 'None'}...")
    print(f"Session token exists in Redis: {session_token in sessions if session_token else False}")
    if session_token and session_token in sessions:
        print("User authenticated, serving React app")
        # Serve the React app for authenticated users
        if os.path.exists("public/index.html"):
            response = FileResponse("public/index.html")
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        elif os.path.exists("dist/index.html"):
            response = FileResponse("dist/index.html")
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        elif os.path.exists("../public/index.html"):
            response = FileResponse("../public/index.html")
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        else:
            # Fallback: redirect to signup if frontend not found
            print("ERROR: React app not found at public/index.html or dist/index.html")
            return RedirectResponse(url="/auth/login", status_code=302)
    else:
        print("User not authenticated, serving React app (will show landing page based on mode)")
        # Serve the React app for unauthenticated users
        # React RootRedirect component will handle landing page mode logic
        if os.path.exists("public/index.html"):
            response = FileResponse("public/index.html")
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        elif os.path.exists("dist/index.html"):
            response = FileResponse("dist/index.html")
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        else:
            # Fallback: redirect to login if frontend not found
            print("ERROR: React app not found at public/index.html or dist/index.html")
            return RedirectResponse(url="/auth/login", status_code=302)

# Initialize Docker client
try:
    docker_client = docker.from_env()
except Exception as e:
    print(f"Warning: Docker client initialization failed: {e}")
    docker_client = None

# Model registry storage
MODEL_REGISTRY_PATH = "/home/ucadmin/UC-1-Pro/volumes/model_registry.json"
MODELS_DIR = os.environ.get("MODELS_DIR", "/home/ucadmin/UC-1-Pro/volumes/vllm_models")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# Active downloads tracking
active_downloads = {}
download_progress = defaultdict(lambda: {"status": "pending", "progress": 0, "speed": 0, "eta": None})

# Initialize model registry
def load_model_registry():
    if os.path.exists(MODEL_REGISTRY_PATH):
        try:
            with open(MODEL_REGISTRY_PATH, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "models": {},
        "active_model": None,
        "global_settings": {
            "default_retention": "keep",
            "default_context_size": 16384
        }
    }

def save_model_registry(registry):
    try:
        with open(MODEL_REGISTRY_PATH, 'w') as f:
            json.dump(registry, f, indent=2)
    except Exception as e:
        print(f"Error saving model registry: {e}")

model_registry = load_model_registry()

# Helper function to get directory size
def get_directory_size(path):
    """Get total size of a directory"""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_directory_size(entry.path)
    except:
        pass
    
    # Format size
    if total > 1024**3:
        return f"{total / (1024**3):.1f} GB"
    elif total > 1024**2:
        return f"{total / (1024**2):.1f} MB"
    else:
        return f"{total / 1024:.1f} KB"

# Function to scan and discover existing models
def scan_existing_models():
    """Scan the models directory and update registry with found models"""
    if not os.path.exists(MODELS_DIR):
        print(f"Models directory not found: {MODELS_DIR}")
        return
    
    print(f"Scanning for models in {MODELS_DIR}")
    
    # Recursively look for model directories
    def scan_directory(base_path, parent_path=""):
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                # Check if it's a model directory (contains config.json or similar)
                config_files = ['config.json', 'model.safetensors', 'model-00001-of-00005.safetensors', 'model.bin', 'pytorch_model.bin']
                has_config = any(os.path.exists(os.path.join(item_path, cf)) for cf in config_files)
                
                if has_config:
                    # Build full model ID from path
                    if parent_path:
                        model_id = f"{parent_path}/{item}"
                    else:
                        model_id = item
                    
                    # Check if it's already in registry
                    if model_id not in model_registry["models"]:
                        print(f"Found model: {model_id}")
                        
                        # Get model size
                        size = get_directory_size(item_path)
                        
                        # Determine quantization from name
                        quantization = "Unknown"
                        if "AWQ" in item:
                            quantization = "AWQ"
                        elif "GPTQ" in item:
                            quantization = "GPTQ"
                        elif "GGUF" in item:
                            quantization = "GGUF"
                        
                        # Determine if it's the active model based on env var
                        default_model = os.environ.get("DEFAULT_LLM_MODEL", "")
                        # Clean up the model ID for comparison
                        clean_model_id = model_id.replace("models--", "").replace("--", "/")
                        is_active = (model_id == default_model or 
                                   clean_model_id == default_model or 
                                   default_model.endswith(f"/{item}"))
                        
                        model_registry["models"][model_id] = {
                            "id": model_id,
                            "path": item_path,
                            "quantization": quantization,
                            "discovered_at": datetime.now().isoformat(),
                            "size": size,
                            "active": is_active
                        }
                else:
                    # Recursively scan subdirectories
                    scan_directory(item_path, f"{parent_path}/{item}" if parent_path else item)
    
    scan_directory(MODELS_DIR)
    save_model_registry(model_registry)
    print(f"Found {len(model_registry['models'])} models")

# Scan for existing models on startup
scan_existing_models()

# Service definitions
SERVICES = {
    "open-webui": {
        "container": "unicorn-open-webui",
        "name": "Chat UI",
        "port": 8080,
        "healthcheck": "/health",
        "description": "Web interface for AI chat interactions"
    },
    "vllm": {
        "container": "unicorn-vllm",
        "name": "vLLM API (Qwen 32B)",
        "port": 8000,
        "healthcheck": "/health",
        "description": "High-performance LLM inference server - Qwen 32B model"
    },
    "vllm-gemma3": {
        "container": "unicorn-vllm-gemma3",
        "name": "vLLM API (Gemma 3 27B)",
        "port": 8005,
        "healthcheck": "/health",
        "description": "High-performance LLM inference server - Gemma 3 27B AWQ model"
    },
    "vllm-gemma3-1b": {
        "container": "unicorn-vllm-gemma3-1b",
        "name": "vLLM API (Gemma 3 1B)",
        "port": 8006,
        "healthcheck": "/health",
        "description": "Ultra-fast LLM inference - Gemma 3 1B AWQ model"
    },
    "vllm-gemma3-4b": {
        "container": "unicorn-vllm-gemma3-4b",
        "name": "vLLM API (Gemma 3 4B)",
        "port": 8007,
        "healthcheck": "/health",
        "description": "Fast LLM inference - Gemma 3 4B AWQ model"
    },
    "vllm-gemma3-12b": {
        "container": "unicorn-vllm-gemma3-12b",
        "name": "vLLM API (Gemma 3 12B)",
        "port": 8008,
        "healthcheck": "/health",
        "description": "Balanced LLM inference - Gemma 3 12B AWQ model"
    },
    "whisperx": {
        "container": "unicorn-whisperx",
        "name": "WhisperX",
        "port": 9000,
        "healthcheck": "/health",
        "description": "Advanced speech-to-text with speaker diarization"
    },
    "kokoro": {
        "container": "unicorn-kokoro",
        "name": "Kokoro TTS",
        "port": 8880,
        "healthcheck": "/health",
        "description": "High-quality text-to-speech synthesis"
    },
    "embeddings": {
        "container": "unicorn-embeddings",
        "name": "Embeddings",
        "port": 8082,
        "healthcheck": "/health",
        "description": "Text embedding service for RAG"
    },
    "reranker": {
        "container": "unicorn-reranker",
        "name": "Reranker",
        "port": 8083,
        "healthcheck": "/health",
        "description": "Document reranking for improved search"
    },
    "searxng": {
        "container": "unicorn-searxng",
        "name": "SearXNG",
        "port": 8888,
        "healthcheck": "/",
        "description": "Private search engine"
    },
    "qdrant": {
        "container": "unicorn-qdrant",
        "name": "Qdrant",
        "port": 6333,
        "healthcheck": "/health",
        "description": "Vector database for embeddings"
    },
    "tika-ocr": {
        "container": "unicorn-tika-ocr",
        "name": "Tika OCR",
        "port": 9998,
        "healthcheck": "/",
        "description": "Document parsing and OCR"
    },
    "postgres": {
        "container": "unicorn-postgres",
        "name": "PostgreSQL",
        "port": 5432,
        "healthcheck": None,
        "description": "Main database"
    },
    "redis": {
        "container": "unicorn-redis",
        "name": "Redis",
        "port": 6379,
        "healthcheck": None,
        "description": "Cache and message queue"
    },
    "prometheus": {
        "container": "unicorn-prometheus",
        "name": "Prometheus",
        "port": 9090,
        "healthcheck": "/-/healthy",
        "description": "Metrics collection"
    }
}

# WebSocket connections
websocket_connections = set()

# Pydantic models
class ServiceAction(BaseModel):
    action: str  # start, stop, restart

class NetworkConfig(BaseModel):
    interface: str
    method: str  # dhcp, static
    address: Optional[str] = None
    netmask: Optional[str] = None
    gateway: Optional[str] = None
    dns: Optional[List[str]] = None

class SystemSettings(BaseModel):
    idle_timeout_minutes: int = 5
    idle_policy: str = "swap"  # swap, unload, none
    idle_model: str = "microsoft/DialoGPT-small"
    enable_monitoring: bool = True
    enable_backups: bool = True
    backup_schedule: str = "0 2 * * *"

class ModelDownload(BaseModel):
    model_id: str
    quantization: Optional[str] = None

class ModelEstimate(BaseModel):
    model_id: str
    model_size: str
    quantization: str
    context_size: int = 16384

class ActiveModel(BaseModel):
    model_id: str

class ModelConfig(BaseModel):
    retention: Optional[str] = None
    context_size: Optional[int] = None

class GlobalModelSettings(BaseModel):
    default_retention: str = "keep"
    default_context_size: int = 16384

# Colonel WebSocket endpoint for streaming AI chat
@app.websocket("/ws/colonel")
async def colonel_websocket(websocket: WebSocket):
    """WebSocket endpoint for Colonel AI chat with streaming LLM responses."""
    await colonel_gateway.handle_websocket(websocket)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_connections.add(websocket)
    try:
        while True:
            # Keep connection alive and handle messages
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)

async def broadcast_progress(model_id: str, progress_data: dict):
    """Broadcast download progress to all connected WebSocket clients"""
    message = json.dumps({
        "type": "download_progress",
        "model_id": model_id,
        "data": progress_data
    })
    
    disconnected = set()
    for websocket in websocket_connections:
        try:
            await websocket.send_text(message)
        except:
            disconnected.add(websocket)
    
    # Clean up disconnected websockets
    for ws in disconnected:
        websocket_connections.discard(ws)

# Hugging Face API functions
async def search_huggingface_models(query: str, limit: int = 20):
    """Search Hugging Face for models"""
    async with httpx.AsyncClient() as client:
        headers = {}
        if HF_TOKEN:
            headers["Authorization"] = f"Bearer {HF_TOKEN}"
        
        # Search for text-generation models that are likely vLLM compatible
        params = {
            "search": query,
            "filter": "text-generation",
            "limit": limit,
            "sort": "downloads"
        }
        
        try:
            response = await client.get(
                "https://huggingface.co/api/models",
                params=params,
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                models = response.json()
                
                # Process and enhance model data
                processed_models = []
                for model in models:
                    # Fetch model card to get more details
                    try:
                        card_response = await client.get(
                            f"https://huggingface.co/api/models/{model['id']}",
                            headers=headers,
                            timeout=5.0
                        )
                        if card_response.status_code == 200:
                            model_details = card_response.json()
                            
                            # Determine available quantizations
                            files = model_details.get("siblings", [])
                            quantizations = detect_quantizations(files)
                            
                            # Estimate model size
                            model_size = estimate_model_size_from_files(files)
                            
                            processed_models.append({
                                "id": model["id"],
                                "name": model.get("id", "").split("/")[-1],
                                "description": model.get("pipeline_tag", "Text generation model"),
                                "downloads": model_details.get("downloads", 0),
                                "likes": model_details.get("likes", 0),
                                "size": model_size,
                                "task": "text-generation",
                                "quantizations": quantizations,
                                "vllm_compatible": check_vllm_compatibility(model_details),
                                "trending": model_details.get("downloads", 0) > 100000
                            })
                    except:
                        # Fallback for models where detailed info fails
                        processed_models.append({
                            "id": model["id"],
                            "name": model.get("id", "").split("/")[-1],
                            "description": "Model from Hugging Face",
                            "downloads": model.get("downloads", 0),
                            "likes": model.get("likes", 0),
                            "size": "Unknown",
                            "task": "text-generation",
                            "quantizations": ["Q4_K_M", "Q5_K_M"],
                            "vllm_compatible": True
                        })
                
                return processed_models[:limit]
            
        except Exception as e:
            print(f"Error searching HuggingFace: {e}")
    
    # Return fallback trending models on error
    return get_trending_models()[:limit]

def get_trending_models():
    """Get trending models as fallback"""
    return [
        {
            "id": "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "name": "Llama 3.1 8B Instruct",
            "description": "Latest Llama model optimized for instruction following",
            "downloads": 2500000,
            "likes": 15000,
            "size": "16GB",
            "task": "text-generation",
            "quantizations": ["Q4_K_M", "Q5_K_M", "Q8_0", "F16"],
            "vllm_compatible": True,
            "trending": True
        },
        {
            "id": "Qwen/Qwen2.5-32B-Instruct-AWQ",
            "name": "Qwen 2.5 32B Instruct AWQ",
            "description": "State-of-the-art model with 32K context length",
            "downloads": 1800000,
            "likes": 12000,
            "size": "18GB",
            "task": "text-generation",
            "quantizations": ["AWQ"],
            "vllm_compatible": True,
            "trending": True
        },
        {
            "id": "mistralai/Mistral-7B-Instruct-v0.2",
            "name": "Mistral 7B Instruct v0.2",
            "description": "Efficient 7B model with sliding window attention",
            "downloads": 3200000,
            "likes": 18000,
            "size": "14GB",
            "task": "text-generation",
            "quantizations": ["Q4_K_M", "Q5_K_M", "Q8_0"],
            "vllm_compatible": True,
            "trending": True
        }
    ]

def detect_quantizations(files):
    """Detect available quantizations from model files"""
    quantizations = set()
    
    for file in files:
        filename = file.get("rfilename", "")
        
        # Check for common quantization patterns
        if "awq" in filename.lower():
            quantizations.add("AWQ")
        if "gptq" in filename.lower():
            quantizations.add("GPTQ")
        if "q4_k_m" in filename.lower():
            quantizations.add("Q4_K_M")
        if "q5_k_m" in filename.lower():
            quantizations.add("Q5_K_M")
        if "q8_0" in filename.lower():
            quantizations.add("Q8_0")
        if "fp16" in filename.lower() or "f16" in filename.lower():
            quantizations.add("F16")
        if ".gguf" in filename:
            # GGUF files often have multiple quants
            quantizations.update(["Q4_K_M", "Q5_K_M", "Q8_0"])
    
    # Default quantizations if none detected
    if not quantizations:
        quantizations = {"Q4_K_M", "Q5_K_M"}
    
    return sorted(list(quantizations))

def estimate_model_size_from_files(files):
    """Estimate total model size from file listing"""
    total_size = 0
    
    for file in files:
        size = file.get("size", 0)
        total_size += size
    
    # Convert to human readable
    if total_size == 0:
        return "Unknown"
    
    gb = total_size / (1024 ** 3)
    if gb > 1:
        return f"{gb:.1f}GB"
    
    mb = total_size / (1024 ** 2)
    return f"{mb:.0f}MB"

def check_vllm_compatibility(model_details):
    """Check if model is likely vLLM compatible"""
    # Check model architecture
    config = model_details.get("config", {})
    arch = config.get("model_type", "").lower()
    
    # Known vLLM compatible architectures
    vllm_architectures = [
        "llama", "mistral", "qwen", "phi", "gemma", "gpt2", "gptj", 
        "gpt_neox", "opt", "bloom", "falcon", "mpt", "starcoder",
        "baichuan", "aquila", "chatglm", "internlm", "yi"
    ]
    
    for va in vllm_architectures:
        if va in arch:
            return True
    
    # Check tags
    tags = model_details.get("tags", [])
    if "text-generation" in tags:
        return True
    
    # Default to true for text-generation models
    return True

# Memory estimation
def calculate_model_memory(model_size_str: str, quantization: str, context_size: int = 16384):
    """Calculate memory requirements for a model"""
    # Parse model size
    size_gb = 0
    if "GB" in model_size_str.upper():
        size_gb = float(re.findall(r'[\d.]+', model_size_str)[0])
    elif "MB" in model_size_str.upper():
        size_gb = float(re.findall(r'[\d.]+', model_size_str)[0]) / 1024
    elif "B" in model_size_str:
        # Assume it's parameter count in billions
        param_b = float(re.findall(r'[\d.]+', model_size_str)[0])
        # Rough estimate: 2 bytes per parameter for fp16
        size_gb = (param_b * 2)
    
    # Quantization multipliers
    quant_multipliers = {
        'F16': 1.0,        # Full precision
        'FP16': 1.0,
        'Q8_0': 0.5,       # 8-bit quantization  
        'Q5_K_M': 0.375,   # 5-bit quantization
        'Q4_K_M': 0.25,    # 4-bit quantization
        'AWQ': 0.25,       # AWQ 4-bit
        'GPTQ': 0.25,      # GPTQ 4-bit
        'Q3_K_M': 0.1875   # 3-bit quantization
    }
    
    multiplier = quant_multipliers.get(quantization, 0.25)
    model_memory_gb = size_gb * multiplier
    
    # Context memory calculation
    # Rough estimate: 4 bytes per token for KV cache
    context_memory_gb = (context_size * 4 * 2) / (1024 ** 3)  # *2 for K and V
    
    # Add overhead (20% for safety)
    total_memory_gb = (model_memory_gb + context_memory_gb) * 1.2
    
    # Get available GPU memory using nvidia-smi instead of GPUtil
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.free,memory.total', '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            parts = result.stdout.strip().split(', ')
            if len(parts) >= 2:
                available_memory_gb = float(parts[0]) / 1024
                total_gpu_memory_gb = float(parts[1]) / 1024
                usage_percentage = (total_memory_gb / total_gpu_memory_gb) * 100
            else:
                available_memory_gb = 32  # Default for RTX 5090
                total_gpu_memory_gb = 32
                usage_percentage = (total_memory_gb / total_gpu_memory_gb) * 100
        else:
            available_memory_gb = 32  # Default for RTX 5090
            total_gpu_memory_gb = 32
            usage_percentage = (total_memory_gb / total_gpu_memory_gb) * 100
    except:
        available_memory_gb = 32
        total_gpu_memory_gb = 32
        usage_percentage = (total_memory_gb / total_gpu_memory_gb) * 100
    
    return {
        "model": round(model_memory_gb, 2),
        "context": round(context_memory_gb, 2),
        "total": round(total_memory_gb, 2),
        "available": round(available_memory_gb, 2),
        "percentage": round(usage_percentage, 1),
        "fits": total_memory_gb <= available_memory_gb
    }

# Model download functionality
async def download_model_with_progress(model_id: str, quantization: Optional[str], background_tasks: BackgroundTasks):
    """Download a model using huggingface-cli with progress tracking"""
    download_id = hashlib.md5(f"{model_id}:{quantization}".encode()).hexdigest()
    
    # Initialize progress
    download_progress[download_id] = {
        "status": "initializing",
        "progress": 0,
        "speed": 0,
        "eta": None,
        "model_id": model_id,
        "quantization": quantization
    }
    
    try:
        # Create model directory
        model_path = os.path.join(MODELS_DIR, model_id.replace("/", "_"))
        os.makedirs(model_path, exist_ok=True)
        
        # Build huggingface-cli command
        cmd = ["huggingface-cli", "download", model_id, "--local-dir", model_path]
        
        if HF_TOKEN:
            cmd.extend(["--token", HF_TOKEN])
        
        if quantization:
            # Add pattern to download only specific quantization files
            if quantization == "AWQ":
                cmd.extend(["--include", "*awq*", "*.json", "*.txt"])
            elif quantization == "GPTQ":
                cmd.extend(["--include", "*gptq*", "*.json", "*.txt"])
            elif quantization in ["Q4_K_M", "Q5_K_M", "Q8_0"]:
                cmd.extend(["--include", f"*{quantization.lower()}*", "*.json", "*.txt"])
        
        # Start download process
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        download_progress[download_id]["status"] = "downloading"
        active_downloads[download_id] = process
        
        # Parse output for progress
        start_time = time.time()
        last_update = 0
        
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            
            line = line.decode('utf-8').strip()
            
            # Parse progress from huggingface-cli output
            if "Downloading" in line or "%" in line:
                # Extract progress percentage
                match = re.search(r'(\d+)%', line)
                if match:
                    progress = int(match.group(1))
                    current_time = time.time()
                    
                    # Calculate speed
                    if current_time - last_update > 1:  # Update every second
                        elapsed = current_time - start_time
                        speed = progress / elapsed if elapsed > 0 else 0
                        eta = (100 - progress) / speed if speed > 0 else None
                        
                        download_progress[download_id].update({
                            "status": "downloading",
                            "progress": progress,
                            "speed": round(speed, 2),
                            "eta": round(eta) if eta else None
                        })
                        
                        # Broadcast progress
                        await broadcast_progress(model_id, download_progress[download_id])
                        last_update = current_time
        
        # Wait for completion
        await process.wait()
        
        if process.returncode == 0:
            # Success - register the model
            download_progress[download_id]["status"] = "completed"
            download_progress[download_id]["progress"] = 100
            
            # Add to model registry
            model_registry["models"][model_id] = {
                "id": model_id,
                "path": model_path,
                "quantization": quantization,
                "downloaded_at": datetime.now().isoformat(),
                "size": get_directory_size(model_path),
                "active": False
            }
            save_model_registry(model_registry)
            
            await broadcast_progress(model_id, download_progress[download_id])
        else:
            # Failed
            download_progress[download_id]["status"] = "failed"
            download_progress[download_id]["error"] = "Download failed"
            await broadcast_progress(model_id, download_progress[download_id])
    
    except Exception as e:
        download_progress[download_id]["status"] = "failed"
        download_progress[download_id]["error"] = str(e)
        await broadcast_progress(model_id, download_progress[download_id])
    
    finally:
        # Cleanup
        if download_id in active_downloads:
            del active_downloads[download_id]


# ===========================
# Authentication Functions
# ===========================

# Keycloak session-based authentication (current system)
async def get_current_user(request: Request):
    """Get current user from Keycloak session cookie"""
    session_token = request.cookies.get("session_token")

    if not session_token or session_token not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")


async def get_current_user_optional(request: Request) -> Optional[dict]:
    """Get current user if authenticated, otherwise return None (doesn't fail)"""
    session_token = request.cookies.get("session_token")

    if not session_token or session_token not in sessions:
        return None

    session = sessions[session_token]
    user_data = session.get("user", {})

    # Map Keycloak/Authentik roles to ops-center roles
    if "role" not in user_data:
        # Extract role from Keycloak groups/roles
        mapped_role = map_keycloak_role(user_data)
        user_data["role"] = mapped_role

        # Update session with role for future requests
        session["user"] = user_data
        sessions[session_token] = session  # Save back to Redis

        logger.info(f"Mapped role '{mapped_role}' for user '{user_data.get('preferred_username', user_data.get('username', 'unknown'))}'")

    return user_data

async def require_admin(current_user: dict = Depends(get_current_user)):
    """Require admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

async def require_power_user(current_user: dict = Depends(get_current_user)):
    """Require power_user or admin role"""
    role = current_user.get("role", "viewer")
    if role not in ["admin", "power_user"]:
        raise HTTPException(
            status_code=403,
            detail="Power user or admin access required"
        )
    return current_user

async def require_user(current_user: dict = Depends(get_current_user)):
    """Require user, power_user, or admin role (excludes viewers)"""
    role = current_user.get("role", "viewer")
    if role not in ["admin", "power_user", "user"]:
        raise HTTPException(
            status_code=403,
            detail="User access required"
        )
    return current_user

# API Routes

@app.get("/api/v1/system/status")
async def get_system_status(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get current system resource usage with enhanced monitoring (works with or without auth)"""
    try:
        # Try enhanced monitoring first
        if ENHANCED_MONITORING:
            try:
                metrics = {
                    "cpu": resource_monitor.get_cpu_metrics(),
                    "memory": resource_monitor.get_memory_metrics(),
                    "gpu": resource_monitor.get_gpu_metrics(),
                    "disk": resource_monitor.get_disk_metrics(),
                    "network": resource_monitor.get_network_metrics(),
                    "processes": resource_monitor.get_top_processes()
                }
                
                # Format for API compatibility
                gpu_info = []
                if metrics["gpu"].get("nvidia_gpus"):
                    for gpu in metrics["gpu"]["nvidia_gpus"]:
                        gpu_info.append({
                            "name": gpu.get("name", "Unknown GPU"),
                            "utilization": gpu.get("utilization_percent", 0),
                            "memory_used": gpu.get("memory_used_mb", 0) * 1024 * 1024,
                            "memory_total": gpu.get("memory_total_mb", 0) * 1024 * 1024,
                            "temperature": gpu.get("temperature", 0),
                            "power_draw": gpu.get("power_w", 0),
                            "power_limit": gpu.get("power_limit_w", 0)
                        })
                
                return {
                    "cpu": {
                        "percent": metrics["cpu"].get("usage_percent", 0),
                        "per_cpu": metrics["cpu"].get("per_core_usage", []),
                        "cores": metrics["cpu"].get("cores", 0),
                        "freq_current": metrics["cpu"].get("frequency", {}).get("current", 0)
                    },
                    "memory": {
                        "used": int(metrics["memory"].get("ram", {}).get("used_gb", 0) * 1024 * 1024 * 1024),
                        "total": int(metrics["memory"].get("ram", {}).get("total_gb", 0) * 1024 * 1024 * 1024),
                        "available": int(metrics["memory"].get("ram", {}).get("available_gb", 0) * 1024 * 1024 * 1024),
                        "percent": metrics["memory"].get("ram", {}).get("percent", 0)
                    },
                    "disk": {
                        "used": int(metrics["disk"].get("partitions", [{}])[0].get("used_gb", 0) * 1024 * 1024 * 1024),
                        "total": int(metrics["disk"].get("partitions", [{}])[0].get("total_gb", 0) * 1024 * 1024 * 1024),
                        "percent": metrics["disk"].get("partitions", [{}])[0].get("percent", 0)
                    },
                    "gpu": gpu_info,
                    "uptime": int(time.time() - psutil.boot_time()),
                    "load_average": metrics["cpu"].get("load_average", [0, 0, 0]),
                    "processes": metrics.get("processes", []),
                    "enhanced_monitoring": True
                }
            except Exception as e:
                print(f"Enhanced monitoring failed, falling back to basic: {e}")
        
        # Fallback to basic monitoring
        # CPU info - use non-blocking calls
        cpu_percent = psutil.cpu_percent(interval=0)  # Non-blocking
        cpu_percent_per_core = psutil.cpu_percent(interval=0, percpu=True)  # Non-blocking
        cpu_count = psutil.cpu_count()
        
        # Memory info
        memory = psutil.virtual_memory()
        
        # Disk info
        disk = psutil.disk_usage('/')
        
        # GPU info (if available) - skip GPUtil for now as it might be blocking
        gpu_info = []
        # Temporarily disable GPUtil calls to fix performance
        # try:
        #     gpus = GPUtil.getGPUs()
        #     for gpu in gpus:
        #         gpu_info.append({
        #             "name": gpu.name,
        #             "utilization": round(gpu.load * 100, 1),
        #             "memory_used": int(gpu.memoryUsed * 1024 * 1024),  # Convert to bytes
        #             "memory_total": int(gpu.memoryTotal * 1024 * 1024),  # Convert to bytes
        #             "temperature": gpu.temperature,
        #             "power_draw": getattr(gpu, 'powerDraw', 0),
        #             "power_limit": getattr(gpu, 'powerLimit', 0)
        #         })
        # except Exception as e:
        #     print(f"GPU info error: {e}")
        
        # Use nvidia-smi for GPU info instead
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw,power.limit', 
                                   '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    parts = line.split(', ')
                    if len(parts) >= 7:
                        gpu_info.append({
                            "name": parts[0],
                            "utilization": float(parts[1]) if parts[1] != '[N/A]' else 0,
                            "memory_used": int(float(parts[2]) * 1024 * 1024) if parts[2] != '[N/A]' else 0,
                            "memory_total": int(float(parts[3]) * 1024 * 1024) if parts[3] != '[N/A]' else 0,
                            "temperature": float(parts[4]) if parts[4] != '[N/A]' else 0,
                            "power_draw": float(parts[5]) if parts[5] != '[N/A]' else 0,
                            "power_limit": float(parts[6]) if parts[6] != '[N/A]' else 0
                        })
        except Exception as e:
            print(f"GPU info error: {e}")
        
        # Get CPU frequency
        cpu_freq = psutil.cpu_freq()
        
        # Get load average
        load_avg = os.getloadavg()
        
        # Get uptime
        boot_time = psutil.boot_time()
        uptime = int(time.time() - boot_time)
        
        # Get top processes - skip for performance
        processes = []
        # Skip process enumeration for now to improve performance
        # This was causing significant delays in the API response
        # try:
        #     for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
        #         try:
        #             pinfo = proc.info
        #             processes.append({
        #                 'pid': pinfo['pid'],
        #                 'name': pinfo['name'],
        #                 'cpu_percent': pinfo['cpu_percent'] or 0,
        #                 'memory_mb': pinfo['memory_info'].rss / (1024 * 1024) if pinfo['memory_info'] else 0,
        #                 'status': pinfo['status']
        #             })
        #         except (psutil.NoSuchProcess, psutil.AccessDenied):
        #             pass
        #     
        #     # Sort by CPU usage and take top 10
        #     processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        #     processes = processes[:10]
        # except Exception as e:
        #     print(f"Error getting processes: {e}")
        
        return {
            "cpu": {
                "percent": round(cpu_percent, 1),
                "per_cpu": [round(p, 1) for p in cpu_percent_per_core],
                "cores": cpu_count,
                "freq_current": int(cpu_freq.current) if cpu_freq else 0
            },
            "memory": {
                "used": memory.used,
                "total": memory.total,
                "available": memory.available,
                "percent": round(memory.percent, 1)
            },
            "disk": {
                "used": disk.used,
                "total": disk.total,
                "percent": round(disk.percent, 1)
            },
            "gpu": gpu_info,
            "uptime": uptime,
            "load_average": list(load_avg),
            "processes": processes,
            "enhanced_monitoring": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/system/hardware")
async def get_hardware_info():
    """Get detailed hardware information"""
    try:
        return hardware_detector.get_all_hardware_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/system/disk-io")
async def get_disk_io_stats(current_user: dict = Depends(get_current_user)):
    """Get current disk I/O statistics (authenticated users only)"""
    try:
        import psutil
        import time
        
        # Get disk I/O counters
        disk_io = psutil.disk_io_counters()
        
        if disk_io:
            return {
                "read_bytes": disk_io.read_bytes,
                "write_bytes": disk_io.write_bytes,
                "read_count": disk_io.read_count,
                "write_count": disk_io.write_count,
                "read_time": disk_io.read_time,
                "write_time": disk_io.write_time,
                "timestamp": time.time()
            }
        else:
            return {
                "read_bytes": 0,
                "write_bytes": 0,
                "read_count": 0,
                "write_count": 0,
                "read_time": 0,
                "write_time": 0,
                "timestamp": time.time()
            }
    except Exception as e:
        logger.error(f"Disk I/O stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get disk I/O stats: {str(e)}")

@app.get("/api/v1/system/capabilities")
async def get_system_capabilities_endpoint(current_user: dict = Depends(get_current_user)):
    """
    Get complete system capabilities including hardware detection and deployment type.
    This endpoint dynamically detects GPUs, NPUs, CPU, memory, and provides deployment recommendations.
    """
    try:
        capabilities = get_system_capabilities()
        return capabilities
    except Exception as e:
        logger.error(f"System capabilities detection error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to detect system capabilities: {str(e)}")

@app.get("/api/v1/system/settings")
async def get_system_settings():
    """Get system-wide settings (public endpoint for landing page mode)"""
    return {
        "landing_page_mode": "direct_sso",  # direct_sso | public_marketplace | custom
        "branding": {
            "company_name": "Unicorn Commander",
            "logo_url": "/logos/magic_unicorn_logo.webp",
            "primary_color": "#7c3aed"
        },
        "sso_enabled": True,
        "allow_registration": False
    }

@app.get("/api/v1/deployment/config")
async def get_deployment_config():
    """Get deployment configuration"""
    try:
        if DEPLOYMENT_CONFIG:
            # Use the enhanced deployment service
            config = {
                "deployment_type": deployment_service.detect_deployment_type(),
                "primary_app_url": deployment_service.get_primary_app_url(),
                "admin_only_mode": deployment_service.is_admin_only_mode(),
                "registered_applications": deployment_service.get_registered_applications(),
                "enabled_features": deployment_service.get_enabled_features(),
                "branding": deployment_service.get_branding_config()
            }
        else:
            # Fallback configuration for UC-1 Pro
            config = {
                "deployment_type": "enterprise",
                "primary_app_url": "http://localhost:8080",
                "admin_only_mode": False,
                "registered_applications": ["open-webui", "center-deep", "vllm"],
                "enabled_features": ["vllm", "gpu_monitoring", "enterprise_auth", "model_management"],
                "branding": {
                    "name": "UC-1 Pro Operations Center",
                    "theme": "unicorn"
                }
            }
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===========================
# Landing Page Customization
# ===========================

@app.get("/api/v1/landing/config")
async def get_landing_config(current_user: dict = Depends(get_current_user)):
    """Get landing page configuration (authenticated users only)"""
    try:
        return landing_config.get_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/landing/config")
async def update_landing_config(
    updates: dict,
    current_user: dict = Depends(require_admin)
):
    """Update landing page configuration (admin only)"""
    try:
        success = landing_config.update_config(updates)
        if success:
            return {"status": "success", "config": landing_config.get_config()}
        else:
            raise HTTPException(status_code=500, detail="Failed to update configuration")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/landing/theme/{preset}")
async def apply_theme_preset(
    preset: str,
    current_user: dict = Depends(require_admin)
):
    """Apply a theme preset (admin only)"""
    try:
        if preset not in landing_config.THEME_PRESETS:
            raise HTTPException(status_code=400, detail=f"Invalid preset: {preset}")
        
        success = landing_config.apply_theme_preset(preset)
        if success:
            return {"status": "success", "config": landing_config.get_config()}
        else:
            raise HTTPException(status_code=500, detail="Failed to apply theme")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/landing/themes")
async def get_available_themes():
    """Get available theme presets"""
    return landing_config.THEME_PRESETS

@app.get("/api/v1/services/discovery")
async def get_service_discovery():
    """
    Dynamic service discovery endpoint.

    Returns all service endpoints with both internal and external URLs.
    Automatically adapts to different deployment configurations.

    Returns:
        dict: Service discovery information including:
            - services: All available services with internal/external URLs
            - external_urls: Public-facing URLs
            - internal_urls: Docker network URLs
            - deployment: Current deployment configuration
    """
    try:
        return {
            "services": service_discovery.get_service_info(),
            "external_urls": service_discovery.get_external_urls(),
            "internal_urls": service_discovery.get_all_services(),
            "deployment": {
                "external_host": service_discovery.external_host,
                "external_protocol": service_discovery.external_protocol,
                "docker_available": service_discovery.docker_client is not None
            }
        }
    except Exception as e:
        logger.error(f"Service discovery failed: {e}")
        raise HTTPException(status_code=500, detail=f"Service discovery failed: {str(e)}")

@app.get("/api/v1/service-urls")
async def get_service_urls():
    """Get service URLs with proper domain configuration"""
    external_host = os.getenv("EXTERNAL_HOST", "localhost")
    external_protocol = os.getenv("EXTERNAL_PROTOCOL", "http")
    
    # Build base URL
    if external_host != "localhost":
        base_url = f"{external_protocol}://{external_host}"
    else:
        base_url = ""  # Empty for relative URLs when using localhost
    
    # Define service URLs with subdomain support
    service_urls = {
        'vllm': f"{base_url}:8000/docs" if base_url else "http://localhost:8000/docs",
        'open-webui': f"{external_protocol}://chat.{external_host}" if external_host != "localhost" else "http://localhost:8080",
        'searxng': f"{external_protocol}://search.{external_host}" if external_host != "localhost" else "http://localhost:8888",
        'unicorn-orator': f"{external_protocol}://tts.{external_host}" if external_host != "localhost" else "http://localhost:8885",
        'unicorn-amanuensis': f"{external_protocol}://stt.{external_host}/web" if external_host != "localhost" else "http://localhost:8887/web",
        'prometheus': f"{base_url}:9090" if base_url else "http://localhost:9090",
        'grafana': f"{base_url}:3000" if base_url else "http://localhost:3000",
        'portainer': f"{base_url}:9443" if base_url else "http://localhost:9443",
        'comfyui': f"{base_url}:8188" if base_url else "http://localhost:8188",
        'n8n': f"{base_url}:5678" if base_url else "http://localhost:5678",
        'qdrant': f"{base_url}:6333/dashboard" if base_url else "http://localhost:6333/dashboard",
        'admin-dashboard': f"{base_url}:8084" if base_url else "http://localhost:8084",
        'ollama': f"{base_url}:11434" if base_url else "http://localhost:11434",
        'ollama-webui': f"{base_url}:11435" if base_url else "http://localhost:11435"
    }
    
    return {
        "base_url": base_url,
        "external_host": external_host,
        "external_protocol": external_protocol,
        "service_urls": service_urls
    }

@app.post("/api/v1/landing/service/{service_id}")
async def update_landing_service(
    service_id: str,
    updates: dict,
    current_user: dict = Depends(require_admin)
):
    """Update a specific service configuration (admin only)"""
    try:
        success = landing_config.update_service(service_id, updates)
        if success:
            return {"status": "success", "config": landing_config.get_config()}
        else:
            raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/landing/custom-link")
async def add_custom_link(
    link_data: dict,
    current_user: dict = Depends(require_admin)
):
    """Add a custom service link (admin only)"""
    try:
        success = landing_config.add_custom_link(link_data)
        if success:
            return {"status": "success", "config": landing_config.get_config()}
        else:
            raise HTTPException(status_code=500, detail="Failed to add custom link")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/landing/custom-link/{link_id}")
async def remove_custom_link(
    link_id: str,
    current_user: dict = Depends(require_admin)
):
    """Remove a custom service link (admin only)"""
    try:
        success = landing_config.remove_custom_link(link_id)
        if success:
            return {"status": "success", "config": landing_config.get_config()}
        else:
            raise HTTPException(status_code=404, detail=f"Link {link_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/landing/reorder")
async def reorder_services(
    service_order: list,
    current_user: dict = Depends(require_admin)
):
    """Reorder services on landing page (admin only)"""
    try:
        success = landing_config.reorder_services(service_order)
        if success:
            return {"status": "success", "config": landing_config.get_config()}
        else:
            raise HTTPException(status_code=500, detail="Failed to reorder services")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/landing/reset")
async def reset_landing_config(current_user: dict = Depends(require_admin)):
    """Reset landing page to default configuration (admin only)"""
    try:
        success = landing_config.reset_to_default()
        if success:
            return {"status": "success", "config": landing_config.get_config()}
        else:
            raise HTTPException(status_code=500, detail="Failed to reset configuration")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/landing/export")
async def export_landing_config(current_user: dict = Depends(require_admin)):
    """Export landing page configuration (admin only)"""
    try:
        config_json = landing_config.export_config()
        return JSONResponse(
            content={"config": config_json},
            headers={"Content-Disposition": "attachment; filename=landing_config.json"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/landing/import")
async def import_landing_config(
    config_data: dict,
    current_user: dict = Depends(require_admin)
):
    """Import landing page configuration (admin only)"""
    try:
        config_json = json.dumps(config_data)
        success = landing_config.import_config(config_json)
        if success:
            return {"status": "success", "config": landing_config.get_config()}
        else:
            raise HTTPException(status_code=400, detail="Invalid configuration format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===========================
# Service Management
# ===========================

@app.get("/api/v1/services")
async def list_services(current_user: dict = Depends(get_current_user)):
    """List all services with their status (authenticated users only)"""
    try:
        # Use Quick Docker Fix for reliable container detection
        services = get_running_services()
        print(f"DEBUG: Quick Docker Fix returned {len(services)} services")
        
        # Format the services for the expected API response
        formatted_services = []
        for service in services:
            # Determine hardware type based on GPU usage
            hardware_type = 'gpu' if service.get('gpu_enabled', False) else 'cpu'

            # Determine usage level based on service category
            category = service.get('category', 'general')
            if category in ['inference', 'processing']:
                usage_level = 'high'
            elif category in ['database', 'interface']:
                usage_level = 'medium'
            else:
                usage_level = 'normal'

            formatted_services.append({
                "name": service['name'],
                "service_name": service['name'],  # Add for frontend compatibility
                "display_name": service['display_name'],
                "status": service['status'],
                "port": service['port'],
                "description": service['description'],
                "cpu_percent": service['cpu_percent'],
                "resource_usage": service['cpu_percent'],  # Add for frontend compatibility
                "memory_mb": service['memory_mb'],
                "uptime": service['uptime'],
                "type": service.get('type', 'core'),
                "category": service.get('category', 'general'),
                "container_name": service['container_name'],
                "gpu_enabled": service['gpu_enabled'],
                "hardware_type": hardware_type,  # Add hardware_type field
                "usage_level": usage_level,  # Add usage_level field
                "image": service['image']
            })

        return formatted_services
    
    except Exception as e:
        print(f"Error listing services with Quick Docker Fix: {e}")
        # Fall back to development mode mock data
        if os.environ.get('DEVELOPMENT', 'false').lower() == 'true':
            services = []
            for service_id, service_info in SERVICES.items():
                gpu_enabled = service_id in ["vllm"]
                cpu_pct = 12.5 if service_id == "vllm" else 2.1
                services.append({
                    "name": service_id,
                    "service_name": service_id,
                    "display_name": service_info["name"],
                    "status": "healthy" if service_id in ["vllm", "open-webui"] else "stopped",
                    "port": service_info["port"],
                    "description": service_info.get("description", ""),
                    "cpu_percent": cpu_pct,
                    "resource_usage": cpu_pct,
                    "memory_mb": 8192 if service_id == "vllm" else 512,
                    "uptime": "2h 15m" if service_id in ["vllm", "open-webui"] else None,
                    "category": "core",
                    "container_name": service_info["container"],
                    "gpu_enabled": gpu_enabled,
                    "hardware_type": 'gpu' if gpu_enabled else 'cpu',
                    "usage_level": 'high' if service_id == "vllm" else 'normal',
                    "image": "unknown"
                })
            return services
        
        # Return empty list as fallback
        return []

@app.post("/api/v1/services/{container_name}/action")
async def service_action(
    request: Request,
    container_name: str,
    action: ServiceAction,
    current_user: dict = Depends(require_admin)
):
    """Perform action on a service (admin only)"""
    # Rate limiting for admin operations
    if RATE_LIMIT_ENABLED:
        user_id = current_user.get("user_id", "unknown")
        is_admin = current_user.get("role") == "admin"
        await check_rate_limit_manual(request, category="admin", user_id=user_id, is_admin=is_admin)

    try:
        # Use direct Docker CLI commands for reliable service control
        result = subprocess.run(
            ['docker', action.action, container_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Audit log successful service operation
            if AUDIT_ENABLED:
                await log_service_operation(
                    request,
                    user_id=current_user.get("user_id", "unknown"),
                    username=current_user.get("username", "unknown"),
                    operation=action.action,
                    service_name=container_name,
                    success=True
                )

            return {
                "status": "success",
                "action": action.action,
                "service": container_name,
                "message": f"Successfully {action.action}ed {container_name}"
            }
        else:
            # Audit log failed service operation
            if AUDIT_ENABLED:
                await log_service_operation(
                    request,
                    user_id=current_user.get("user_id", "unknown"),
                    username=current_user.get("username", "unknown"),
                    operation=action.action,
                    service_name=container_name,
                    success=False,
                    error_message=result.stderr
                )

            raise HTTPException(
                status_code=500,
                detail=f"Failed to {action.action} {container_name}: {result.stderr}"
            )
    except subprocess.TimeoutExpired:
        # Audit log timeout
        if AUDIT_ENABLED:
            await log_service_operation(
                request,
                user_id=current_user.get("user_id", "unknown"),
                username=current_user.get("username", "unknown"),
                operation=action.action,
                service_name=container_name,
                success=False,
                error_message=f"Timeout while trying to {action.action}"
            )

        raise HTTPException(
            status_code=500,
            detail=f"Timeout while trying to {action.action} {container_name}"
        )
    except Exception as e:
        # Audit log error
        if AUDIT_ENABLED:
            await log_service_operation(
                request,
                user_id=current_user.get("user_id", "unknown"),
                username=current_user.get("username", "unknown"),
                operation=action.action,
                service_name=container_name,
                success=False,
                error_message=str(e)
            )

        raise HTTPException(
            status_code=500,
            detail=f"Error controlling service: {str(e)}"
        )

@app.get("/api/v1/services/{container_name}/logs")
async def get_service_logs(container_name: str, lines: int = 100):
    """Get logs from a service container"""
    logs = docker_manager.get_service_logs(container_name, lines)
    return {"container": container_name, "logs": logs}

@app.get("/api/v1/services/{container_name}/stats")
async def get_service_stats(container_name: str):
    """Get detailed stats for a service container"""
    stats = docker_manager._get_container_stats(container_name)
    if stats:
        return {"container": container_name, "stats": stats}
    else:
        # Return basic stats when Docker API is not available
        # Look for the service in our current services list
        services = docker_manager.discover_all_services()
        all_services = services.get("core", [])
        
        # Flatten extension services (it's a dict of lists)
        extensions = services.get("extensions", {})
        if isinstance(extensions, dict):
            for ext_name, ext_services in extensions.items():
                all_services.extend(ext_services)
        else:
            all_services.extend(extensions)
        
        for service in all_services:
            if service.get("container_name") == container_name:
                # Return basic info we have
                return {
                    "container": container_name,
                    "stats": {
                        "name": service.get("name"),
                        "display_name": service.get("display_name"),
                        "status": service.get("status"),
                        "cpu_percent": service.get("cpu_percent", 0),
                        "memory_mb": service.get("memory_mb", 0),
                        "uptime": service.get("uptime"),
                        "created": None,
                        "ports": [service.get("port")] if service.get("port") else [],
                        "networks": [],
                        "volumes": [],
                        "environment": {},
                        "labels": {},
                        "image": service.get("image", "unknown")
                    }
                }
        
        # If container not found at all
        raise HTTPException(status_code=404, detail="Container not found")

# Model Management Routes

@app.get("/api/v1/models/search")
async def search_models(q: Optional[str] = None):
    """Search for models on Hugging Face"""
    if not q:
        # Return trending models
        trending = await search_huggingface_models("", limit=10)
        return trending
    
    # Search with query
    results = await search_huggingface_models(q, limit=20)
    return results

@app.post("/api/v1/models/estimate-memory")
async def estimate_memory(request: ModelEstimate):
    """Estimate memory requirements for a model"""
    return calculate_model_memory(
        request.model_size,
        request.quantization,
        request.context_size
    )

@app.post("/api/v1/models/download")
async def download_model(
    request: ModelDownload,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_admin)
):
    """Start downloading a model (admin only)"""
    # Check if already downloading
    for download_id, progress in download_progress.items():
        if progress.get("model_id") == request.model_id and progress.get("status") in ["initializing", "downloading"]:
            return {"status": "already_downloading", "model_id": request.model_id}
    
    # Start download in background
    background_tasks.add_task(
        download_model_with_progress,
        request.model_id,
        request.quantization
    )
    
    return {"status": "started", "model_id": request.model_id}

@app.get("/api/v1/models/download-progress/{model_id:path}")
async def get_download_progress(model_id: str):
    """Get download progress for a model"""
    # Find progress for this model
    for download_id, progress in download_progress.items():
        if progress.get("model_id") == model_id:
            return progress
    
    return {"status": "not_found"}

@app.get("/api/v1/models")
async def get_models(current_user: dict = Depends(get_current_user)):
    """Get list of downloaded models (authenticated users only)"""
    models = []
    
    for model_id, model_info in model_registry["models"].items():
        models.append({
            "id": model_id,
            "name": model_id.split("/")[-1],
            "type": "Local",
            "size": model_info.get("size", "Unknown"),
            "last_used": model_info.get("last_used", "Never"),
            "active": model_info.get("active", False),
            "quantization": model_info.get("quantization", "Unknown"),
            "path": model_info.get("path", "")
        })
    
    return models

@app.delete("/api/v1/models/{model_id:path}")
async def delete_model(
    model_id: str,
    current_user: dict = Depends(require_admin)
):
    """Delete a model (admin only)"""
    if model_id in model_registry["models"]:
        model_info = model_registry["models"][model_id]
        model_path = model_info.get("path", "")
        
        # Delete files
        if os.path.exists(model_path):
            shutil.rmtree(model_path)
        
        # Remove from registry
        del model_registry["models"][model_id]
        save_model_registry(model_registry)
        
        return {"status": "deleted", "model_id": model_id}
    
    raise HTTPException(status_code=404, detail="Model not found")

@app.post("/api/v1/models/active")
async def set_active_model(
    request: ActiveModel,
    current_user: dict = Depends(require_admin)
):
    """Set the active model and restart vLLM (admin only)"""
    model_id = request.model_id
    
    if model_id not in model_registry["models"]:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Update registry
    for mid in model_registry["models"]:
        model_registry["models"][mid]["active"] = (mid == model_id)
    
    model_registry["active_model"] = model_id
    save_model_registry(model_registry)
    
    # Update vLLM configuration
    if docker_client:
        try:
            # Get vLLM container
            vllm_container = docker_client.containers.get("unicorn-vllm")
            
            # Update environment variable
            env_vars = vllm_container.attrs['Config']['Env']
            new_env = []
            
            for env in env_vars:
                if not env.startswith("MODEL="):
                    new_env.append(env)
            
            new_env.append(f"MODEL={model_id}")
            
            # Restart container with new model
            vllm_container.stop()
            vllm_container.remove()
            
            # Get original run config
            config = vllm_container.attrs
            
            # Start new container with updated model
            docker_client.containers.run(
                image=config['Config']['Image'],
                name="unicorn-vllm",
                environment=new_env,
                ports={"8000/tcp": 8000},
                volumes=config['Mounts'],
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            return {"status": "activated", "model_id": model_id}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to switch model: {str(e)}")
    
    return {"status": "activated", "model_id": model_id, "note": "Docker not available, model marked as active"}

@app.put("/api/v1/models/{model_id:path}/config")
async def update_model_config(model_id: str, config: ModelConfig):
    """Update model-specific configuration"""
    if model_id not in model_registry["models"]:
        raise HTTPException(status_code=404, detail="Model not found")
    
    if config.retention is not None:
        model_registry["models"][model_id]["retention"] = config.retention
    
    if config.context_size is not None:
        model_registry["models"][model_id]["context_size"] = config.context_size
    
    save_model_registry(model_registry)
    
    return {"status": "updated", "model_id": model_id}

@app.get("/api/v1/models/settings")
async def get_model_settings():
    """Get global model settings"""
    return model_registry["global_settings"]

@app.put("/api/v1/models/settings")
async def update_model_settings(settings: GlobalModelSettings):
    """Update global model settings"""
    model_registry["global_settings"].update(settings.dict())
    save_model_registry(model_registry)
    
    return {"status": "updated"}

@app.post("/api/v1/models/upload")
async def upload_model(model: UploadFile = File(...)):
    """Upload a model file"""
    try:
        # Save to models directory
        if not os.path.exists(MODELS_DIR):
            os.makedirs(MODELS_DIR)
        
        file_path = os.path.join(MODELS_DIR, model.filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await model.read()
            await f.write(content)
        
        # Add to registry
        model_id = f"local/{model.filename}"
        model_registry["models"][model_id] = {
            "id": model_id,
            "path": file_path,
            "uploaded_at": datetime.now().isoformat(),
            "size": get_directory_size(file_path),
            "active": False
        }
        save_model_registry(model_registry)
        
        return {"status": "uploaded", "model_id": model_id, "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# New AI Model Management endpoints
@app.get("/api/v1/models/settings/{backend}")
async def get_backend_settings(backend: str):
    """Get global settings for vLLM or Ollama"""
    if backend not in ["vllm", "ollama"]:
        raise HTTPException(status_code=400, detail="Invalid backend. Use 'vllm' or 'ollama'")
    
    return ai_model_manager.get_global_settings(backend)

@app.put("/api/v1/models/settings/{backend}")
async def update_backend_settings(backend: str, settings: Dict[str, Any]):
    """Update global settings for vLLM or Ollama"""
    if backend not in ["vllm", "ollama"]:
        raise HTTPException(status_code=400, detail="Invalid backend. Use 'vllm' or 'ollama'")
    
    updated = ai_model_manager.update_global_settings(backend, settings)
    return {"status": "updated", "settings": updated}

@app.get("/api/v1/models/{backend}/{model_id:path}/settings")
async def get_model_settings(backend: str, model_id: str):
    """Get effective settings for a specific model"""
    if backend not in ["vllm", "ollama"]:
        raise HTTPException(status_code=400, detail="Invalid backend")
    
    return ai_model_manager.get_model_settings(model_id, backend)

@app.post("/api/v1/models/settings")
async def update_model_settings(update: ModelSettingsUpdate):
    """Update model-specific settings overrides"""
    result = ai_model_manager.update_model_settings(
        update.model_id, 
        update.backend, 
        update.settings
    )
    return {"status": "updated", "settings": result}

@app.get("/api/v1/models/installed")
async def get_installed_models():
    """Get all installed models for both vLLM and Ollama"""
    models = await ai_model_manager.scan_local_models()
    return models

@app.post("/api/v1/models/download")
async def download_model(request: ModelDownloadRequest):
    """Download a model from Hugging Face or Ollama Hub"""
    try:
        if request.backend == "vllm":
            task_id = await ai_model_manager.download_vllm_model(
                request.model_id, 
                request.settings
            )
        elif request.backend == "ollama":
            task_id = await ai_model_manager.download_ollama_model(request.model_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid backend")
        
        return {"status": "started", "task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/models/downloads")
async def get_download_status():
    """Get status of all download tasks"""
    return ai_model_manager.get_all_downloads()

@app.get("/api/v1/models/downloads/{task_id}")
async def get_download_task_status(task_id: str):
    """Get status of a specific download task"""
    status = ai_model_manager.get_download_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Download task not found")
    return status

@app.post("/api/v1/models/{backend}/{model_id:path}/activate")
async def activate_model(backend: str, model_id: str):
    """Activate a model for use"""
    if backend == "vllm":
        result = await ai_model_manager.activate_vllm_model(model_id)
        return result
    elif backend == "ollama":
        # Ollama models are activated on demand
        return {"status": "ready", "model_id": model_id, "message": "Ollama models are activated on demand"}
    else:
        raise HTTPException(status_code=400, detail="Invalid backend")

@app.delete("/api/v1/models/{backend}/{model_id:path}")
async def delete_model_by_backend(backend: str, model_id: str):
    """Delete a model"""
    try:
        result = await ai_model_manager.delete_model(model_id, backend)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Unified vLLM Manager Routes
@app.get("/api/v1/vllm/endpoint")
async def get_vllm_endpoint():
    """Get the unified vLLM endpoint information for OpenWebUI integration"""
    try:
        # Check if unified manager is running (now on port 8000)
        unified_manager_url = "http://unicorn-vllm:8000"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                # Get endpoint info from unified manager
                response = await client.get(f"{unified_manager_url}/v1/endpoint")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Add convenience fields for OpenWebUI
                    if data.get("status") == "active":
                        data["openwebui_config"] = {
                            "name": f"vLLM ({data['model_id']})",
                            "url": data["docker_endpoint"],
                            "api_key": data.get("api_key", ""),
                            "model": data["model_id"]
                        }
                    
                    return data
                    
            except (httpx.ConnectError, httpx.TimeoutException):
                pass
        
        # Fallback to traditional vLLM endpoint
        return {
            "status": "traditional",
            "endpoint": "http://unicorn-vllm:8000",
            "docker_endpoint": "http://unicorn-vllm:8000",
            "external_endpoint": f"http://{os.environ.get('EXTERNAL_HOST', 'localhost')}:8000",
            "openai_compatible": True,
            "api_key": os.environ.get("VLLM_API_KEY", ""),
            "openwebui_config": {
                "name": "vLLM (Traditional)",
                "url": "http://unicorn-vllm:8000",
                "api_key": os.environ.get("VLLM_API_KEY", ""),
                "model": os.environ.get("DEFAULT_LLM_MODEL", "")
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting vLLM endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/vllm/switch-model")
async def switch_vllm_model(request: Dict[str, Any]):
    """Switch vLLM model using unified manager"""
    try:
        unified_manager_url = "http://unicorn-vllm:8000"
        model_id = request.get("model_id")
        
        if not model_id:
            raise ValueError("model_id is required")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{unified_manager_url}/v1/models/switch",
                json={"model_id": model_id}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.text
                )
                
    except httpx.ConnectError:
        # Fallback to traditional activation
        result = await ai_model_manager.activate_vllm_model(request.get("model_id"))
        return result
    except Exception as e:
        logger.error(f"Error switching vLLM model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/vllm/models")
async def get_vllm_models_unified():
    """Get all vLLM models from unified manager"""
    try:
        unified_manager_url = "http://unicorn-vllm:8000"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{unified_manager_url}/v1/models")
                
                if response.status_code == 200:
                    return response.json()
                    
            except (httpx.ConnectError, httpx.TimeoutException):
                pass
        
        # Fallback to scanning local models
        models = await ai_model_manager.scan_local_models()
        return {"object": "list", "data": models.get("vllm", [])}
        
    except Exception as e:
        logger.error(f"Error getting vLLM models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Network management routes
@app.get("/api/v1/network/status")
async def get_network_status(current_user: dict = Depends(get_current_user)):
    """Get network status and interfaces (authenticated users only)"""
    try:
        network_status = {
            "ethernet": {"connected": False, "ip": None, "interface": None},
            "wifi": {"connected": False, "ssid": None, "signal": 0, "interface": None},
            "bluetooth": {"enabled": False, "devices": 0}
        }
        
        # Get network interfaces using Ubuntu Server native tools
        try:
            interfaces = network_manager.get_network_interfaces()
            
            # Process interfaces
            for ifname, info in interfaces.items():
                if info['type'] == 'ethernet' and info['state'] == 'UP':
                    ip_addr = None
                    if info['ip_addresses']:
                        ip_addr = info['ip_addresses'][0]['address']
                    
                    network_status["ethernet"] = {
                        "connected": True,
                        "ip": ip_addr,
                        "interface": ifname,
                        "ip_address": ip_addr,  # For compatibility
                        "speed": "1000"  # Default, could be detected
                    }
                elif info['type'] == 'wifi':
                    # Check for WiFi connection
                    wifi_conn = network_manager.get_current_wifi_connection()
                    if wifi_conn:
                        network_status["wifi"] = {
                            "connected": True,
                            "ssid": wifi_conn.get('ssid', ''),
                            "signal": wifi_conn.get('signal', 0),
                            "interface": wifi_conn['interface'],
                            "ip": wifi_conn['ip_addresses'][0]['address'] if wifi_conn['ip_addresses'] else None
                        }
        except Exception as e:
            print(f"Error getting network status: {e}")
        
        # Check Bluetooth status
        try:
            bt_result = subprocess.run(
                ["systemctl", "is-active", "bluetooth"],
                capture_output=True, text=True, timeout=5
            )
            network_status["bluetooth"]["enabled"] = (bt_result.returncode == 0 and bt_result.stdout.strip() == "active")
            
            if network_status["bluetooth"]["enabled"]:
                # Count paired devices
                bt_devices = subprocess.run(
                    ["bluetoothctl", "devices"],
                    capture_output=True, text=True, timeout=5
                )
                if bt_devices.returncode == 0:
                    network_status["bluetooth"]["devices"] = len(bt_devices.stdout.strip().split('\n'))
        except:
            pass
        
        return network_status
    except Exception as e:
        print(f"Network status error: {e}")
        # Return simulated data as fallback
        return {
            "ethernet": {"connected": True, "ip": "192.168.1.100", "interface": "eth0"},
            "wifi": {"connected": False, "ssid": None, "signal": 0},
            "bluetooth": {"enabled": True, "devices": 0}
        }

@app.get("/api/v1/network/wifi/scan")
async def scan_wifi():
    """Scan for WiFi networks"""
    try:
        networks = network_manager.get_wifi_networks()
        
        # Sort by signal strength
        networks.sort(key=lambda x: x.get('signal', 0), reverse=True)
        
        # Format for frontend compatibility
        formatted_networks = []
        for network in networks:
            formatted_networks.append({
                "ssid": network.get('ssid', 'Hidden Network'),
                "signal": network.get('signal', 0),
                "signal_strength": network.get('signal', 0),  # For compatibility
                "security": network.get('security', 'Open'),
                "bssid": network.get('bssid', ''),
                "frequency": network.get('frequency', 0)
            })
        
        return formatted_networks
    
    except Exception as e:
        print(f"WiFi scan error: {e}")
        # Return mock data as fallback
        return [
            {"ssid": "Network scan failed", "signal": 0, "security": "Unknown"},
        ]

@app.post("/api/v1/network/wifi/connect")
async def connect_wifi(
    request: dict,
    current_user: dict = Depends(require_admin)
):
    """Connect to a WiFi network (admin only)"""
    ssid = request.get("ssid")
    password = request.get("password", "")
    
    if not ssid:
        raise HTTPException(status_code=400, detail="SSID is required")
    
    try:
        success = network_manager.connect_to_wifi(ssid, password)
        
        if success:
            return {"status": "connected", "message": f"Connected to {ssid}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to connect to WiFi")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/network/wifi/disconnect")
async def disconnect_wifi():
    """Disconnect from current WiFi network"""
    try:
        success = network_manager.disconnect_wifi()
        
        if success:
            return {"status": "disconnected", "message": "WiFi disconnected"}
        else:
            raise HTTPException(status_code=400, detail="No active WiFi connection")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/network/configure")
async def configure_network(
    config: NetworkConfig,
    current_user: dict = Depends(require_admin)
):
    """Configure network interface (static IP, DHCP, etc.) (admin only)"""
    try:
        interface = config.interface
        
        # Convert netmask to prefix length if needed
        prefix = 24  # Default
        if config.netmask:
            # Simple conversion for common netmasks
            netmask_to_prefix = {
                "255.255.255.0": 24,
                "255.255.0.0": 16,
                "255.0.0.0": 8,
                "255.255.255.128": 25,
                "255.255.255.192": 26,
                "255.255.255.224": 27,
                "255.255.255.240": 28,
                "255.255.255.248": 29,
                "255.255.255.252": 30
            }
            prefix = netmask_to_prefix.get(config.netmask, 24)
        
        # Prepare configuration
        net_config = {
            "method": config.method,
            "address": config.address,
            "prefix": prefix,
            "gateway": config.gateway,
            "dns": config.dns
        }
        
        success = network_manager.update_interface_config(interface, net_config)
        
        if success:
            return {"status": "configured", "message": f"Interface {interface} configured successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to configure network interface")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/network/wifi/forget/{ssid}")
async def forget_wifi_network(ssid: str):
    """Forget a saved WiFi network"""
    try:
        result = subprocess.run(
            ["nmcli", "connection", "delete", ssid],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            return {"status": "forgotten", "message": f"Network {ssid} forgotten"}
        else:
            raise HTTPException(status_code=404, detail="Network not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Settings routes
@app.get("/api/v1/settings")
async def get_settings():
    """Get system settings"""
    return {
        "system": {
            "idle_timeout": 300,
            "auto_swap_enabled": True,
            "max_memory_percent": 95,
            "log_level": "info"
        },
        "notifications": {
            "email_enabled": False,
            "email_address": "",
            "webhook_enabled": False,
            "webhook_url": "",
            "alert_on_errors": True,
            "alert_on_updates": False
        },
        "security": {
            "auth_enabled": True,
            "session_timeout": 3600,
            "api_keys": []
        },
        "backup": {
            "auto_backup_enabled": True,
            "backup_schedule": "0 2 * * *",
            "retention_days": 7,
            "backup_location": "/backups"
        }
    }

@app.put("/api/v1/settings")
async def update_settings(settings: SystemSettings):
    """Update system settings"""
    # Save settings (mock for now)
    return {"status": "updated"}

# Extension management
EXTENSIONS_DIR = "/home/ucadmin/UC-1-Pro/extensions"

@app.get("/api/v1/extensions")
async def get_extensions(current_user: dict = Depends(get_current_user)):
    """Get list of installed extensions with full metadata (authenticated users only)"""
    extensions = []
    ext_dir = Path('/home/ucadmin/UC-1-Pro/extensions')
    
    if ext_dir.exists():
        for item in ext_dir.iterdir():
            if item.is_dir() and (item / 'docker-compose.yml').exists():
                # Read description from README
                description = ''
                readme = item / 'README.md'
                if readme.exists():
                    try:
                        with open(readme, 'r') as f:
                            lines = f.readlines()
                            if len(lines) > 2:
                                description = lines[2].strip() if lines[2].strip() else lines[0].strip().replace('#', '').strip()
                    except:
                        pass
                
                # Check if running
                status = 'stopped'
                try:
                    result = subprocess.run(
                        ['docker', 'ps', '--filter', f'name={item.name}', '--format', '{{.Names}}'],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        status = 'running'
                except:
                    pass
                
                # Get friendly name
                name_map = {
                    'bolt.diy': 'Bolt.DIY',
                    'comfyui': 'ComfyUI',
                    'dev-tools': 'Development Tools',
                    'monitoring': 'Grafana Monitoring',
                    'n8n': 'n8n Workflows',
                    'ollama': 'Ollama',
                    'portainer': 'Portainer CE',
                    'traefik': 'Traefik Proxy'
                }
                
                extensions.append({
                    'id': item.name,
                    'name': name_map.get(item.name, item.name.replace('-', ' ').title()),
                    'description': description or f'{item.name} extension',
                    'status': status,
                    'category': _determine_extension_category(item.name)
                })
    
    return {"extensions": extensions}

def _determine_extension_category(name: str) -> str:
    """Determine category based on extension name"""
    categories = {
        'monitoring': 'Monitoring',
        'grafana': 'Monitoring',
        'prometheus': 'Monitoring',
        'comfyui': 'AI Tools',
        'ollama': 'AI Tools',
        'stable-diffusion': 'AI Tools',
        'portainer': 'Management',
        'traefik': 'Networking',
        'n8n': 'Automation',
        'dev-tools': 'Development',
        'code-server': 'Development',
        'bolt': 'Development'
    }
    
    name_lower = name.lower()
    for key, category in categories.items():
        if key in name_lower:
            return category
    return 'Other'

@app.post("/api/v1/extensions/{extension_id}/start")
async def start_extension(extension_id: str):
    """Start an extension"""
    ext_path = os.path.join(EXTENSIONS_DIR, extension_id)
    if not os.path.exists(ext_path):
        raise HTTPException(status_code=404, detail="Extension not found")
    
    try:
        # Run docker-compose up for the extension
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            cwd=ext_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return {"status": "started", "extension": extension_id}
        else:
            raise HTTPException(status_code=500, detail=result.stderr)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/extensions/{extension_id}/stop")
async def stop_extension(extension_id: str):
    """Stop an extension"""
    ext_path = os.path.join(EXTENSIONS_DIR, extension_id)
    if not os.path.exists(ext_path):
        raise HTTPException(status_code=404, detail="Extension not found")
    
    try:
        # Run docker-compose down for the extension
        result = subprocess.run(
            ["docker", "compose", "down"],
            cwd=ext_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return {"status": "stopped", "extension": extension_id}
        else:
            raise HTTPException(status_code=500, detail=result.stderr)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Storage & Backup Management Routes

@app.get("/api/v1/storage", response_model=StorageInfo)
async def get_storage_info(current_user: dict = Depends(get_current_user)):
    """Get comprehensive storage information (authenticated users only)"""
    try:
        return storage_backup_manager.get_storage_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/storage/volumes/{volume_name}")
async def get_volume_details(
    volume_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed information about a specific volume (authenticated users only)"""
    try:
        details = storage_backup_manager.get_volume_details(volume_name)
        if not details:
            raise HTTPException(status_code=404, detail="Volume not found")
        return details
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/backup/status", response_model=BackupStatus)
async def get_backup_status():
    """Get backup status and history"""
    try:
        return storage_backup_manager.get_backup_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/backup/create")
async def create_backup(
    background_tasks: BackgroundTasks,
    backup_type: str = "manual",
    current_user: dict = Depends(require_admin)
):
    """Create a new backup (admin only)"""
    try:
        backup_id = await storage_backup_manager.create_backup(backup_type)
        return {"status": "created", "backup_id": backup_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/backup/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    restore_path: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """Restore from a backup (admin only)"""
    try:
        success = await storage_backup_manager.restore_backup(backup_id, restore_path)
        if success:
            return {"status": "restored", "backup_id": backup_id, "restore_path": restore_path}
        else:
            raise HTTPException(status_code=500, detail="Restore failed")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/backup/{backup_id}")
async def delete_backup(
    backup_id: str,
    current_user: dict = Depends(require_admin)
):
    """Delete a backup (admin only)"""
    try:
        success = storage_backup_manager.delete_backup(backup_id)
        if success:
            return {"status": "deleted", "backup_id": backup_id}
        else:
            raise HTTPException(status_code=500, detail="Delete failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/backup/config", response_model=BackupConfig)
async def update_backup_config(config: Dict[str, Any]):
    """Update backup configuration"""
    try:
        updated_config = storage_backup_manager.update_backup_config(config)
        return updated_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/backup/config", response_model=BackupConfig)
async def get_backup_config():
    """Get current backup configuration"""
    try:
        return storage_backup_manager.backup_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Extension Management endpoints
# Commented out - using direct implementation above
# @app.get("/api/v1/extensions")
# async def get_extensions():
#     """Get list of installed extensions"""
#     try:
#         extensions = extension_manager.get_installed_extensions()
#         return {"extensions": [ext.dict() for ext in extensions]}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/extensions/install")
async def install_extension(
    request: ExtensionInstallRequest,
    current_user: dict = Depends(require_admin)
):
    """Install a new extension (admin only)"""
    try:
        result = await extension_manager.install_extension(request)
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/extensions/{extension_id}")
async def uninstall_extension(
    extension_id: str,
    current_user: dict = Depends(require_admin)
):
    """Uninstall an extension (admin only)"""
    try:
        result = await extension_manager.uninstall_extension(extension_id)
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/extensions/{extension_id}/control")
async def control_extension(
    extension_id: str,
    request: ExtensionActionRequest,
    current_user: dict = Depends(require_admin)
):
    """Control an extension (start, stop, restart) (admin only)"""
    try:
        result = await extension_manager.control_extension(extension_id, request.action)
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/extensions/{extension_id}/config")
async def update_extension_config(
    extension_id: str,
    config_update: ExtensionConfigUpdate,
    current_user: dict = Depends(require_admin)
):
    """Update extension configuration (admin only)"""
    try:
        result = extension_manager.update_extension_config(extension_id, config_update)
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/extensions/{extension_id}/logs")
async def get_extension_logs(
    extension_id: str,
    lines: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get extension logs (authenticated users only)"""
    try:
        result = extension_manager.get_extension_logs(extension_id, lines)
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Log Management endpoints
@app.get("/api/v1/logs/sources")
async def get_log_sources(current_user: dict = Depends(get_current_user)):
    """Get available log sources (authenticated users only)"""
    try:
        sources = await log_manager.get_log_sources()
        return {"sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/logs/stats")
async def get_log_stats(current_user: dict = Depends(get_current_user)):
    """Get log statistics (authenticated users only)"""
    try:
        stats = await log_manager.get_log_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/logs/search")
async def search_logs(
    filters: LogFilter,
    current_user: dict = Depends(get_current_user)
):
    """Search logs based on filters (authenticated users only)"""
    try:
        logs = await log_manager.search_logs(filters)
        return {"logs": [log.dict() for log in logs], "count": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/logs/export")
async def export_logs(
    request: LogExportRequest,
    current_user: dict = Depends(require_admin)
):
    """Export logs to file (admin only)"""
    try:
        result = await log_manager.export_logs(request)
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for log streaming
@app.websocket("/ws/logs/{source_id}")
async def websocket_log_stream(websocket: WebSocket, source_id: str):
    """Stream logs via WebSocket"""
    await websocket.accept()
    
    try:
        # Parse filters from query params
        filters = None
        if websocket.query_params:
            filter_dict = {}
            if "levels" in websocket.query_params:
                filter_dict["levels"] = websocket.query_params["levels"].split(",")
            if "search" in websocket.query_params:
                filter_dict["search"] = websocket.query_params["search"]
            if filter_dict:
                filters = LogFilter(**filter_dict)
        
        # Stream logs
        async for log_line in log_manager.stream_logs(source_id, filters):
            await websocket.send_text(log_line)
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for log source: {source_id}")
    except Exception as e:
        print(f"Error in log streaming: {e}")
        await websocket.close()

# Authentication endpoints
security = HTTPBearer()

# Legacy JWT-based authentication (kept for backward compatibility if needed)
async def get_current_user_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token (legacy)"""
    token = credentials.credentials
    user_info = auth_manager.verify_token(token)

    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user_info

async def require_admin_jwt(current_user: dict = Depends(get_current_user_jwt)):
    """Require admin role (legacy JWT)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@app.post("/api/v1/auth/login")
async def login(credentials: LoginCredentials, request: Request):
    """Login and get access token"""
    # Rate limiting check
    if RATE_LIMIT_ENABLED:
        await check_rate_limit_manual(request, category="auth", user_id=credentials.username)

    try:
        # Get request info
        request_info = {
            "ip_address": get_client_ip(request),
            "user_agent": get_user_agent(request)
        }

        token = await auth_manager.login(credentials, request_info)

        # Audit log successful login
        if AUDIT_ENABLED:
            await log_auth_success(
                request,
                user_id=credentials.username,
                username=credentials.username,
                metadata={"method": "legacy_api_login"}
            )

        return token
    except ValueError as e:
        # Audit log failed login
        if AUDIT_ENABLED:
            await log_auth_failure(
                request,
                username=credentials.username,
                reason=str(e),
                metadata={"method": "legacy_api_login"}
            )
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        # Audit log error
        if AUDIT_ENABLED:
            await log_auth_failure(
                request,
                username=credentials.username,
                reason=f"Internal error: {str(e)}",
                metadata={"method": "legacy_api_login"}
            )
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/auth/logout")
async def logout(request: Request, current_user: dict = Depends(get_current_user)):
    """Logout and invalidate session"""
    try:
        # Get session token from cookie
        session_token = request.cookies.get("session_token")

        # Audit log logout (wrapped in try/except to prevent logout failure if audit fails)
        if AUDIT_ENABLED:
            try:
                await log_logout(
                    request,
                    user_id=current_user.get("user_id", "unknown"),
                    username=current_user.get("username", "unknown"),
                    metadata={"method": "api_logout"}
                )
            except Exception as audit_error:
                # Log the error but don't fail the logout
                print(f"Warning: Audit logging failed during logout: {audit_error}")

        # Get id_token from session (needed for proper logout without confirmation page)
        id_token = None
        if session_token:
            try:
                session_data = sessions.get(session_token)
                if session_data and isinstance(session_data, dict):
                    id_token = session_data.get("id_token")
            except Exception as e:
                print(f"Warning: Could not retrieve id_token from session: {e}")

        # Delete session from Redis
        if session_token and session_token in sessions:
            del sessions[session_token]

        # Build Keycloak logout URL with id_token_hint (required for auto-logout)
        keycloak_external_url = os.getenv("KEYCLOAK_EXTERNAL_URL", "https://auth.unicorncommander.ai")
        keycloak_realm = os.getenv("KEYCLOAK_REALM", "uchub")
        external_host = os.getenv("EXTERNAL_HOST", "unicorncommander.ai")
        external_protocol = os.getenv("EXTERNAL_PROTOCOL", "https")

        # Our logout confirmation page URL (where Keycloak will redirect after clearing session)
        logout_confirmation_url = f"{external_protocol}://{external_host}/auth/logged-out"

        # Keycloak logout URL - using simple redirect_uri (not post_logout_redirect_uri)
        # This avoids the strict validation that comes with id_token_hint
        keycloak_logout_url = (
            f"{keycloak_external_url}/realms/{keycloak_realm}/protocol/openid-connect/logout"
            f"?client_id={os.getenv('KEYCLOAK_CLIENT_ID', 'ops-center')}"
            f"&redirect_uri={logout_confirmation_url}"
        )

        print(f"Logout URL: {keycloak_logout_url}")

        return {
            "message": "Logged out successfully",
            "logout_url": keycloak_logout_url
        }
    except Exception as e:
        # Log the full exception details
        import traceback
        print(f"ERROR in logout endpoint: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    try:
        user = auth_manager.get_user(current_user["user_id"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/auth/profile")
async def update_profile(
    request: Request,
    name: str = None,
    email: str = None,
    avatar: UploadFile = File(None)
):
    """
    Update user profile including avatar/profile picture.
    Accepts multipart/form-data with optional avatar image file.
    """
    session_token = request.cookies.get("session_token")
    if not session_token or session_token not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = sessions.get(session_token)
    user = session_data.get("user", {})
    user_email = user.get("email")

    if not user_email:
        raise HTTPException(status_code=400, detail="User email not found in session")

    logger.info(f"Updating profile for user: {user_email}")

    try:
        updates = {}

        # Handle avatar upload if provided
        if avatar and avatar.filename:
            # Validate file type
            allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
            file_ext = os.path.splitext(avatar.filename)[1].lower()

            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
                )

            # Validate file size (max 2MB)
            content = await avatar.read()
            if len(content) > 2 * 1024 * 1024:  # 2MB
                raise HTTPException(status_code=400, detail="File size must be less than 2MB")

            # Create avatars directory if it doesn't exist
            avatar_dir = "/app/public/avatars"
            os.makedirs(avatar_dir, exist_ok=True)

            # Generate unique filename
            file_hash = hashlib.md5(content).hexdigest()[:12]
            avatar_filename = f"{user_email.split('@')[0]}_{file_hash}{file_ext}"
            avatar_path = os.path.join(avatar_dir, avatar_filename)

            # Save avatar file
            with open(avatar_path, "wb") as f:
                f.write(content)

            # Store avatar URL (relative path)
            avatar_url = f"/avatars/{avatar_filename}"
            updates["avatar"] = avatar_url
            logger.info(f"Saved avatar to {avatar_path}")

        # Handle name update
        if name:
            updates["name"] = name
            logger.info(f"Updating name to: {name}")

        # Handle email update (requires Keycloak update)
        if email and email != user_email:
            # TODO: Update email in Keycloak
            logger.warning(f"Email update requested but not implemented: {email}")
            # For now, don't allow email changes
            raise HTTPException(status_code=400, detail="Email changes not supported yet")

        # Update session with new data
        if updates:
            user.update(updates)
            session_data["user"] = user
            sessions[session_token] = session_data

            logger.info(f"Profile updated successfully for {user_email}: {updates}")

        return {
            "success": True,
            "message": "Profile updated successfully",
            "user": user
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@app.get("/api/v1/auth/csrf-token")
async def get_csrf_token_endpoint(request: Request):
    """
    Get CSRF token for the current session
    Returns the CSRF token that should be included in state-changing requests
    Creates a session with CSRF token if one doesn't exist (for unauthenticated users)
    """
    csrf_token = get_csrf_token(request, sessions)
    new_session_token = None

    if not csrf_token:
        # Create a temporary session for unauthenticated users to get CSRF token
        # This is needed for signup/payment flows before authentication
        session_token = request.cookies.get("session_token")
        if not session_token:
            session_token = secrets.token_urlsafe(32)
            new_session_token = session_token  # Mark that we need to set the cookie

        # Generate new CSRF token
        csrf_token = csrf_protect.generate_token()

        # Create or update session with CSRF token
        sessions[session_token] = {
            "csrf_token": csrf_token,
            "created": time.time(),
            "user": None  # No user yet (unauthenticated)
        }

    # Create response with CSRF token
    response = JSONResponse(content={
        "csrf_token": csrf_token,
        "header_name": "X-CSRF-Token",
        "cookie_name": "csrf_token"
    })

    # Set session_token cookie if this is a new session
    if new_session_token:
        cookie_kwargs = {
            "key": "session_token",
            "value": new_session_token,
            "httponly": True,
            "secure": (EXTERNAL_PROTOCOL == "https"),
            "samesite": "none",
            "max_age": 7200,  # 2 hours, matching Redis TTL
            "path": "/"
        }
        # Set domain for cross-subdomain cookie sharing
        if "." in EXTERNAL_HOST and not EXTERNAL_HOST.startswith("localhost"):
            cookie_kwargs["domain"] = f".{EXTERNAL_HOST}"
        response.set_cookie(**cookie_kwargs)

    return response

# User Management endpoints (admin only)
@app.get("/api/v1/users")
async def get_users(current_user: dict = Depends(require_admin)):
    """Get all users (admin only)"""
    try:
        users = auth_manager.get_users()
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/users")
async def create_user(user_create: UserCreate, current_user: dict = Depends(require_admin)):
    """Create a new user (admin only)"""
    try:
        user = auth_manager.create_user(user_create)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/users/{user_id}")
async def get_user(user_id: str, current_user: dict = Depends(require_admin)):
    """Get user by ID (admin only)"""
    try:
        user = auth_manager.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/users/{user_id}")
async def update_user(user_id: str, user_update: UserUpdate, current_user: dict = Depends(require_admin)):
    """Update user (admin only)"""
    try:
        user = auth_manager.update_user(user_id, user_update)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(require_admin)):
    """Delete user (admin only)"""
    try:
        # Prevent self-deletion
        if user_id == current_user["user_id"]:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        success = auth_manager.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Password Management
@app.post("/api/v1/auth/change-password")
async def change_password(request: Request, password_change: PasswordChange, current_user: dict = Depends(get_current_user)):
    """
    Change current user's password

    Returns detailed feedback including password strength and warnings
    """
    try:
        result = auth_manager.change_password(current_user["user_id"], password_change)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to change password"))

        # Audit log password change
        if AUDIT_ENABLED:
            await audit_logger.log(
                action="auth.password_change",
                result="success",
                user_id=current_user["user_id"],
                username=current_user.get("username", "unknown"),
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                metadata={"method": "api"}
            )

        return result
    except ValueError as e:
        # Pydantic validation errors (password policy violations)
        if AUDIT_ENABLED:
            await audit_logger.log(
                action="auth.password_change",
                result="failure",
                user_id=current_user["user_id"],
                username=current_user.get("username", "unknown"),
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                error_message=str(e)
            )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if AUDIT_ENABLED:
            await audit_logger.log(
                action="auth.password_change",
                result="error",
                user_id=current_user["user_id"],
                username=current_user.get("username", "unknown"),
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                error_message=str(e)
            )
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/auth/password-policy")
async def get_password_policy():
    """
    Get password policy requirements and examples

    Returns policy details to help users create compliant passwords
    """
    from password_policy import get_password_requirements
    return get_password_requirements()

# API Key Management
@app.get("/api/v1/api-keys")
async def get_api_keys(current_user: dict = Depends(get_current_user)):
    """Get current user's API keys"""
    try:
        keys = auth_manager.get_user_api_keys(current_user["user_id"])
        return {"api_keys": keys}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/api-keys")
async def create_api_key(key_create: APIKeyCreate, current_user: dict = Depends(get_current_user)):
    """Create a new API key"""
    try:
        api_key = auth_manager.create_api_key(current_user["user_id"], key_create)
        return api_key
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/api-keys/{key_id}")
async def delete_api_key(key_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an API key"""
    try:
        success = auth_manager.delete_api_key(key_id, current_user["user_id"])
        if not success:
            raise HTTPException(status_code=404, detail="API key not found")
        return {"message": "API key deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Session Management
@app.get("/api/v1/sessions")
async def get_sessions(current_user: dict = Depends(get_current_user)):
    """Get current user's sessions"""
    try:
        sessions = auth_manager.get_user_sessions(current_user["user_id"])
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/sessions/{session_id}")
async def revoke_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Revoke a session"""
    try:
        success = auth_manager.revoke_session(session_id, current_user["user_id"])
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session revoked successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update Management endpoints
@app.get("/api/v1/updates/status")
async def get_update_status(current_user: dict = Depends(get_current_user)):
    """Get current update status (authenticated users only)"""
    try:
        return github_update_manager.get_update_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/updates/check")
async def check_for_updates(current_user: dict = Depends(get_current_user)):
    """Check for available updates (authenticated users only)"""
    try:
        result = await github_update_manager.check_for_updates()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/updates/apply")
async def apply_update(
    backup_first: bool = True,
    current_user: dict = Depends(require_admin)
):
    """Apply available updates (admin only)"""
    try:
        result = await github_update_manager.apply_update(backup_first)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/updates/changelog")
async def get_changelog(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Get recent changelog entries (authenticated users only)"""
    try:
        changelog = await github_update_manager.get_changelog(limit)
        return {"changelog": changelog}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# System Management Endpoints (Headless Server Management)
@app.get("/api/v1/system/network", response_model=NetworkStatus)
async def get_network_configuration(current_user: dict = Depends(require_admin)):
    """
    Get current network configuration.

    Reads network configuration from netplan/interfaces files.
    Returns IP, netmask, gateway, DNS servers, and hostname.

    Requires: Admin role
    """
    try:
        network_status = system_manager.get_network_config()

        # Log access for security audit
        logger.info(f"Network configuration read by admin user: {current_user.get('username', 'unknown')}")

        return network_status
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error reading network configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read network configuration: {str(e)}")


@app.put("/api/v1/system/network")
async def update_network_configuration(
    config: NetworkConfig,
    current_user: dict = Depends(require_admin)
):
    """
    Update network configuration.

    Updates netplan configuration and applies changes.
    Supports both DHCP and static IP configuration.

    Requires: Admin role

    Args:
        config: NetworkConfig with new settings

    Returns:
        Success message with updated configuration

    Security:
        - Requires admin role
        - Validates all inputs
        - Logs all changes
        - Creates backup before applying
    """
    try:
        # Validate configuration
        if not config.dhcp and not (config.ip and config.netmask):
            raise HTTPException(
                status_code=400,
                detail="Static IP configuration requires both IP address and netmask"
            )

        # Log the change attempt
        logger.info(f"Network configuration update initiated by admin user: {current_user.get('username', 'unknown')}")
        logger.info(f"Configuration: DHCP={config.dhcp}, IP={config.ip}, Gateway={config.gateway}")

        # Apply configuration
        success = system_manager.update_network_config(config)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to apply network configuration")

        # Get updated configuration
        updated_config = system_manager.get_network_config()

        # Log successful change
        logger.info(f"Network configuration updated successfully by user: {current_user.get('username', 'unknown')}")

        return {
            "message": "Network configuration updated successfully",
            "configuration": updated_config.dict(),
            "warning": "Network changes may cause temporary connection interruption"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating network configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update network configuration: {str(e)}")


@app.post("/api/v1/system/user/password")
async def change_user_password(
    password_change: SystemPasswordChange,
    current_user: dict = Depends(require_admin)
):
    """
    Change Linux user password.

    Changes the password for a Linux system user with verification.
    Requires current password for security.

    Requires: Admin role

    Args:
        password_change: PasswordChange with username, current and new passwords

    Returns:
        Success message

    Security:
        - Requires admin role
        - Verifies current password before change
        - Validates password strength (min 8 chars, uppercase, lowercase, digit)
        - Logs all password change attempts
        - Does not return sensitive information
    """
    try:
        # Additional security check - prevent changing root password via API
        if password_change.username == 'root':
            logger.warning(f"Attempt to change root password via API by user: {current_user.get('username', 'unknown')}")
            raise HTTPException(
                status_code=403,
                detail="Changing root password via API is not allowed for security reasons"
            )

        # Log password change attempt (without actual passwords)
        logger.info(f"Password change requested for user '{password_change.username}' by admin: {current_user.get('username', 'unknown')}")

        # Change password
        success = system_manager.change_user_password(
            username=password_change.username,
            current_password=password_change.current_password,
            new_password=password_change.new_password
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to change password")

        # Log successful change (without passwords)
        logger.info(f"Password changed successfully for user '{password_change.username}'")

        return {
            "message": f"Password changed successfully for user '{password_change.username}'",
            "username": password_change.username
        }

    except ValueError as e:
        # Log failed attempts
        logger.warning(f"Password change failed for user '{password_change.username}': {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        logger.error(f"Insufficient permissions for password change: {e}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to change password: {str(e)}")


@app.get("/api/v1/system/packages", response_model=PackageList)
async def get_available_packages(current_user: dict = Depends(require_admin)):
    """
    Get list of available system package updates.

    Checks for available updates using apt package manager.
    Updates package cache before checking.

    Requires: Admin role

    Returns:
        PackageList with available updates including:
        - Package name
        - Current version
        - Available version
        - Size (if available)
        - Description (if available)

    Security:
        - Requires admin role
        - Logs all access
        - Read-only operation
    """
    try:
        # Log access
        logger.info(f"Package list requested by admin user: {current_user.get('username', 'unknown')}")

        # Get available updates
        package_list = system_manager.get_available_updates()

        logger.info(f"Found {package_list.total_count} available package updates")

        return package_list

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving package updates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve package updates: {str(e)}")


# ==================== Analytics Endpoints ====================

@app.post("/api/v1/analytics/web-vitals")
async def track_web_vitals(request: Request):
    """
    Track Web Vitals metrics from the frontend.

    Accepts Core Web Vitals data (LCP, FID, CLS, FCP, TTFB, INP) and logs them
    for monitoring and performance analysis.

    Request Body:
        {
            "metric_name": "LCP",
            "value": 2500,
            "rating": "good",
            "metric_id": "v3-1234567890",
            "url": "/admin/dashboard",
            "user_agent": "Mozilla/5.0...",
            "timestamp": "2025-10-25T07:30:00.000Z"
        }

    Returns:
        {"status": "success", "message": "Web vitals tracked"}

    Note:
        Currently logs metrics only. Future enhancement: store in database
        for analytics and performance monitoring dashboards.
    """
    try:
        data = await request.json()

        # Extract required fields
        metric_name = data.get("metric_name", "unknown")
        value = data.get("value", 0)
        rating = data.get("rating", "unknown")
        metric_id = data.get("metric_id", "unknown")
        url = data.get("url", "unknown")
        user_agent = data.get("user_agent", "unknown")
        timestamp = data.get("timestamp", datetime.utcnow().isoformat())

        # Log the web vitals metric
        logger.info(
            f"Web Vitals: {metric_name}={value}ms (rating: {rating}) | "
            f"URL: {url} | ID: {metric_id} | UA: {user_agent[:50]}... | "
            f"Time: {timestamp}"
        )

        # TODO: Store in database for analytics dashboard
        # Future enhancement: INSERT INTO web_vitals_metrics (metric_name, value, rating, url, timestamp)

        return {
            "status": "success",
            "message": "Web vitals tracked",
            "metric": metric_name,
            "value": value
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Error tracking web vitals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to track web vitals: {str(e)}")


@app.get("/api/v1/org/my-orgs")
async def get_my_organizations(current_user: dict = Depends(get_current_user)):
    """
    Get all organizations the current user belongs to.

    Returns an array of organizations with the user's role in each organization.
    Used by the frontend OrganizationContext to populate the org switcher.

    Returns:
        [
            {
                "id": "org_abc123",
                "name": "Organization Name",
                "role": "owner",
                "created_at": "2025-01-01T00:00:00Z",
                "plan_tier": "professional",
                "status": "active"
            }
        ]

    Returns:
        Empty array if user has no organizations

    Authentication:
        Requires valid session (any authenticated user)
    """
    try:
        # Get user ID from session
        user_id = current_user.get("id") or current_user.get("email")

        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in session")

        # Get organizations for this user using org_manager
        organizations = org_manager.get_user_orgs(user_id)

        if not organizations:
            logger.info(f"No organizations found for user: {user_id}")
            return []

        # Get user's role in each organization
        org_users_map = org_manager._load_org_users()

        result = []
        for org in organizations:
            # Find user's role in this org
            user_role = "member"  # default
            org_users = org_users_map.get(org.id, [])
            for org_user in org_users:
                if org_user.user_id == user_id:
                    user_role = org_user.role
                    break

            result.append({
                "id": org.id,
                "name": org.name,
                "role": user_role,
                "created_at": org.created_at.isoformat() if isinstance(org.created_at, datetime) else org.created_at,
                "plan_tier": org.plan_tier,
                "status": org.status
            })

        logger.info(f"Found {len(result)} organizations for user: {user_id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user organizations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve organizations: {str(e)}")


# User Registration endpoint
@app.post("/auth/register")
async def register_user(request: Request):
    """
    Public user registration endpoint for UC-Cloud signup form.
    Creates user locally, in Keycloak, creates organization, and subscribes to Lago.

    Flow:
    1. Validate input
    2. Create organization
    3. Create user locally
    4. Create user in Keycloak with org_id attribute
    5. Add user as organization owner
    6. Create Lago customer for organization
    7. Subscribe organization to "founders_friend" plan
    8. Create session with org context
    """
    org_id = None
    local_user_created = False
    keycloak_user_created = False
    lago_customer_created = False

    try:
        data = await request.json()

        # Validate required fields
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")

        if not name or not email or not password:
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: name, email, and password are required"
            )

        # Validate email format
        if "@" not in email or "." not in email.split("@")[1]:
            raise HTTPException(status_code=400, detail="Invalid email format")

        # Validate password strength
        password_validation = validate_password(password)
        if not password_validation.get("valid"):
            raise HTTPException(
                status_code=400,
                detail=password_validation.get("feedback", "Password does not meet requirements")
            )

        # Split name into first and last name
        name_parts = name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        # Generate username from email (before @ symbol)
        username = email.split("@")[0].lower().replace(".", "_").replace("-", "_")

        # Check if user already exists locally
        existing_users = auth_manager.get_users()
        if any(u.get("email") == email for u in existing_users):
            raise HTTPException(status_code=400, detail="Email already registered")
        if any(u.get("username") == username for u in existing_users):
            # Add random suffix to username if it already exists
            import random
            username = f"{username}_{random.randint(1000, 9999)}"

        # Step 1: Create organization for the new user
        from org_manager import org_manager
        org_name = f"{name}'s Organization"
        logger.info(f"Creating organization: {org_name}")

        try:
            org_id = org_manager.create_organization(
                name=org_name,
                plan_tier="founders_friend"
            )
            logger.info(f"Created organization: {org_id} - {org_name}")
        except Exception as org_error:
            logger.error(f"Failed to create organization: {org_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create organization: {str(org_error)}"
            )

        # Step 2: Create user locally
        user_create = UserCreate(
            username=username,
            email=email,
            password=password,
            full_name=name,
            role="user"
        )

        local_user = auth_manager.create_user(user_create)
        local_user_created = True
        logger.info(f"Created local user: {username} (ID: {local_user['id']})")

        # Step 3: Create user in Keycloak if enabled
        keycloak_user_id = None
        if KEYCLOAK_ENABLED:
            try:
                # Check if user exists in Keycloak
                existing_keycloak_user = await keycloak_get_user_by_email(email)
                if existing_keycloak_user:
                    raise HTTPException(
                        status_code=400,
                        detail="Email already registered in authentication system"
                    )

                # Create user in Keycloak with org_id in attributes
                keycloak_user_id = await keycloak_create_user(
                    email=email,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    attributes={
                        "subscription_tier": ["trial"],
                        "subscription_status": ["active"],
                        "org_id": [org_id],
                        "org_name": [org_name],
                        "org_role": ["owner"]
                    }
                )

                if not keycloak_user_id:
                    logger.error(f"Failed to create Keycloak user for {email}")
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to create user in authentication system"
                    )

                keycloak_user_created = True

                # Set password for the user
                password_set = await keycloak_set_password(
                    user_id=keycloak_user_id,
                    password=password,
                    temporary=False
                )

                if not password_set:
                    logger.error(f"Failed to set password for Keycloak user {keycloak_user_id}")
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to set password in authentication system"
                    )

                logger.info(f"Successfully created Keycloak user {keycloak_user_id} for {email}")

            except HTTPException:
                # Clean up on Keycloak error
                raise
            except Exception as e:
                logger.error(f"Error creating Keycloak user: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create user in authentication system: {str(e)}"
                )

        # Step 4: Add user to organization as owner
        try:
            org_manager.add_user_to_org(
                org_id=org_id,
                user_id=keycloak_user_id or local_user["id"],
                role="owner"
            )
            logger.info(f"Added user {username} as owner of org {org_id}")
        except Exception as org_error:
            logger.error(f"Failed to add user to organization: {org_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to add user to organization: {str(org_error)}"
            )

        # Step 5: Create Lago customer for the organization
        from lago_integration import subscribe_org_to_plan, LagoIntegrationError

        try:
            logger.info(f"Creating Lago customer for org {org_id}")
            subscription = await subscribe_org_to_plan(
                org_id=org_id,
                plan_code="founders_friend",
                org_name=org_name,
                email=email,
                user_id=keycloak_user_id or local_user["id"]
            )
            lago_customer_created = True

            # Update organization with Lago customer ID if available
            if subscription and subscription.get("lago_id"):
                org_manager.update_org_billing_ids(
                    org_id=org_id,
                    lago_id=subscription.get("lago_id")
                )

            logger.info(f"Successfully subscribed org {org_id} to founders_friend plan")

        except LagoIntegrationError as lago_error:
            # Log error but don't fail registration - billing can be fixed later
            logger.error(f"Failed to create Lago subscription for org {org_id}: {lago_error}")
            logger.warning(f"Continuing registration without Lago subscription - can be added later")
        except Exception as lago_error:
            # Log error but don't fail registration
            logger.error(f"Unexpected error creating Lago subscription: {lago_error}")
            logger.warning(f"Continuing registration without Lago subscription")

        # Step 5.5: Create credit account for new user (CRITICAL - enables API access)
        credit_account_created = False
        try:
            from credit_system import credit_manager

            # Initialize credit manager if needed
            await credit_manager.initialize()

            # Create credit account with trial tier allocation
            credit_balance = await credit_manager.create_user_credits(
                user_id=email,  # Use email as user_id for credit system
                tier="trial"
            )
            credit_account_created = True
            logger.info(f"Created credit account for {email}: {credit_balance['credits_remaining']} credits")

        except Exception as credit_error:
            # Log error but don't fail registration - credits will auto-provision on first API call
            logger.error(f"Failed to create credit account during registration for {email}: {credit_error}")
            logger.warning(f"User will have credits auto-provisioned on first API call")

        # Step 6: Audit log successful registration
        if AUDIT_ENABLED:
            await log_auth_success(
                request,
                user_id=local_user["id"],
                username=username,
                metadata={
                    "method": "signup",
                    "email": email,
                    "keycloak_user_id": keycloak_user_id,
                    "org_id": org_id,
                    "org_name": org_name,
                    "lago_customer_created": lago_customer_created,
                    "credit_account_created": credit_account_created
                }
            )

        # Step 7: Auto-login: Create authenticated session for the new user
        session_token = request.cookies.get("session_token")
        if not session_token:
            session_token = secrets.token_urlsafe(32)

        # Get existing session data to preserve CSRF token if exists
        existing_session = sessions.get(session_token)
        existing_csrf = existing_session.get("csrf_token") if existing_session else None

        # Update session with authenticated user info and org data
        sessions[session_token] = {
            "user_id": local_user["id"],
            "username": username,
            "email": email,
            "csrf_token": existing_csrf or csrf_protect.generate_token(),
            "created": time.time(),
            "authenticated": True,
            "keycloak_user_id": keycloak_user_id,
            "org_id": org_id,
            "org_name": org_name,
            "org_role": "owner"
        }

        logger.info(f"New user {username} registered with org: {org_name} (ID: {org_id})")

        # Return response with session cookie
        response = JSONResponse(content={
            "success": True,
            "message": "Account created successfully",
            "user_id": local_user["id"],
            "username": username,
            "email": email,
            "org_id": org_id,
            "org_name": org_name,
            "org_role": "owner"
        })

        # Build cookie kwargs for cross-subdomain support
        session_cookie_kwargs = {
            "key": "session_token",
            "value": session_token,
            "httponly": True,
            "secure": (EXTERNAL_PROTOCOL == "https"),
            "samesite": "none",
            "max_age": 7200,  # 2 hours
            "path": "/"
        }
        if "." in EXTERNAL_HOST and not EXTERNAL_HOST.startswith("localhost"):
            session_cookie_kwargs["domain"] = f".{EXTERNAL_HOST}"
        response.set_cookie(**session_cookie_kwargs)

        # Also set CSRF token cookie for double-submit pattern
        csrf_token = sessions[session_token]["csrf_token"]
        csrf_cookie_kwargs = {
            "key": "csrf_token",
            "value": csrf_token,
            "httponly": False,  # Must be accessible to JavaScript
            "secure": (EXTERNAL_PROTOCOL == "https"),
            "samesite": "none",
            "max_age": 86400,  # 24 hours
            "path": "/"
        }
        if "." in EXTERNAL_HOST and not EXTERNAL_HOST.startswith("localhost"):
            csrf_cookie_kwargs["domain"] = f".{EXTERNAL_HOST}"
        response.set_cookie(**csrf_cookie_kwargs)

        return response

    except HTTPException as http_exc:
        # Rollback on HTTP exceptions (validation errors, etc.)
        logger.error(f"Registration failed with HTTP error: {http_exc.detail}")

        # Rollback in reverse order
        if lago_customer_created and org_id:
            logger.info(f"Rolling back: Lago customer/subscription for org {org_id}")
            # Note: Lago customer deletion would require additional API calls
            # For now, we log it for manual cleanup if needed

        if keycloak_user_created and KEYCLOAK_ENABLED:
            logger.info(f"Rolling back: Keycloak user {email}")
            try:
                from keycloak_integration import delete_user as keycloak_delete_user
                await keycloak_delete_user(email)
                logger.info(f"Rolled back Keycloak user {email}")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback Keycloak user: {rollback_error}")

        if local_user_created:
            logger.info(f"Rolling back: Local user {username}")
            try:
                auth_manager.delete_user(local_user["id"])
                logger.info(f"Rolled back local user {username}")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback local user: {rollback_error}")

        if org_id:
            logger.info(f"Rolling back: Organization {org_id}")
            try:
                from org_manager import org_manager
                org_manager.delete_organization(org_id)
                logger.info(f"Rolled back organization {org_id}")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback organization: {rollback_error}")

        raise http_exc

    except ValueError as e:
        # Handle validation errors from auth_manager
        logger.error(f"Validation error during registration: {e}")

        # Rollback
        if org_id:
            try:
                from org_manager import org_manager
                org_manager.delete_organization(org_id)
                logger.info(f"Rolled back organization {org_id} after validation error")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback organization: {rollback_error}")

        if AUDIT_ENABLED:
            try:
                email_for_log = data.get("email", "unknown") if 'data' in locals() else "unknown"
            except:
                email_for_log = "unknown"
            await log_auth_failure(
                request,
                username=email_for_log,
                reason=str(e),
                metadata={"method": "signup", "rollback_performed": True}
            )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error in user registration: {e}", exc_info=True)

        # Comprehensive rollback
        if lago_customer_created and org_id:
            logger.info(f"Rolling back: Lago customer for org {org_id}")

        if keycloak_user_created and KEYCLOAK_ENABLED and 'email' in locals():
            logger.info(f"Rolling back: Keycloak user {email}")
            try:
                from keycloak_integration import delete_user as keycloak_delete_user
                await keycloak_delete_user(email)
            except Exception as rollback_error:
                logger.error(f"Failed to rollback Keycloak user: {rollback_error}")

        if local_user_created and 'local_user' in locals():
            logger.info(f"Rolling back: Local user")
            try:
                auth_manager.delete_user(local_user["id"])
            except Exception as rollback_error:
                logger.error(f"Failed to rollback local user: {rollback_error}")

        if org_id:
            logger.info(f"Rolling back: Organization {org_id}")
            try:
                from org_manager import org_manager
                org_manager.delete_organization(org_id)
            except Exception as rollback_error:
                logger.error(f"Failed to rollback organization: {rollback_error}")

        if AUDIT_ENABLED:
            try:
                email_for_log = data.get("email", "unknown") if 'data' in locals() else "unknown"
            except:
                email_for_log = "unknown"
            await log_auth_failure(
                request,
                username=email_for_log,
                reason=f"Internal error: {str(e)}",
                metadata={"method": "signup", "rollback_performed": True}
            )
        raise HTTPException(status_code=500, detail="Registration failed. Please try again later.")

# Direct login endpoint
@app.post("/auth/direct-login")
async def direct_login(request: Request, credentials: dict):
    """Direct authentication with Authentik"""
    username = credentials.get("username")
    password = credentials.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")

    # Rate limiting check
    if RATE_LIMIT_ENABLED:
        try:
            identifier = rate_limiter.get_identifier(request, username)
            allowed, metadata = await rate_limiter.check_rate_limit(identifier, "auth")

            if not allowed:
                retry_after = metadata.get("retry_after", 60)
                if AUDIT_ENABLED:
                    await audit_logger.log(
                        action="auth.rate_limit_exceeded",
                        result="denied",
                        username=username,
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request),
                        error_message=f"Too many login attempts. Try again in {retry_after} seconds"
                    )

                raise HTTPException(
                    status_code=429,
                    detail=f"Too many login attempts. Try again in {retry_after} seconds",
                    headers={"Retry-After": str(retry_after)}
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
    
    # Authenticate against Keycloak
    async with httpx.AsyncClient() as client:
        # Keycloak realm (default to "master" if not specified)
        keycloak_realm = os.getenv("KEYCLOAK_REALM", "master")

        # Try to authenticate using Keycloak's password flow
        auth_url = "https://auth.yoda.unicorncommander.ai" if "yoda.unicorncommander.ai" in str(request.url) else f"https://auth.{EXTERNAL_HOST}"

        # Use OAuth password grant with Keycloak endpoints
        token_url = f"{auth_url}/realms/{keycloak_realm}/protocol/openid-connect/token"
        data = {
            "grant_type": "password",
            "username": username,
            "password": password,
            "client_id": OAUTH_CLIENT_ID,
            "client_secret": OAUTH_CLIENT_SECRET,
            "scope": "openid profile email"
        }

        try:
            response = await client.post(token_url, data=data)

            if response.status_code == 200:
                tokens = response.json()
                access_token = tokens.get("access_token")

                # Get user info
                userinfo_url = f"{auth_url}/realms/{keycloak_realm}/protocol/openid-connect/userinfo"
                headers = {"Authorization": f"Bearer {access_token}"}
                user_response = await client.get(userinfo_url, headers=headers)
                
                if user_response.status_code == 200:
                    user_info = user_response.json()

                    # Map Keycloak/Authentik role to ops-center role
                    user_info = add_role_to_user_info(user_info)
                    username = user_info.get('preferred_username') or user_info.get('username', 'unknown')
                    user_id = user_info.get('sub') or user_info.get('id', 'unknown')
                    role = user_info.get('role', 'viewer')
                    logger.info(f"Login: User '{username}' authenticated with role '{role}'")

                    # Audit log successful authentication
                    if AUDIT_ENABLED:
                        await log_auth_success(
                            request,
                            user_id=user_id,
                            username=username,
                            metadata={"role": role, "method": "direct_login"}
                        )

                    # Get organization context for the user
                    email = user_info.get('email')
                    org_context = await get_user_org_context(user_id, email)
                    auto_provisioned = False

                    # Auto-provision org for Keycloak-only users with no org context
                    if not org_context.get("org_id") and role != "admin":
                        display_name = (
                            user_info.get("name")
                            or user_info.get("preferred_username")
                            or username
                        )
                        try:
                            org_context = await auto_provision_user_org(
                                user_id=user_id,
                                email=email,
                                display_name=display_name
                            )
                            auto_provisioned = True
                        except Exception as provision_error:
                            logger.error(f"Auto-provisioning org failed for {email}: {provision_error}")

                    # Create session with org data
                    session_token = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
                    sessions[session_token] = {
                        "user": user_info,
                        "access_token": access_token,
                        "created": time.time(),
                        "org_id": org_context.get("org_id"),
                        "org_name": org_context.get("org_name"),
                        "org_role": org_context.get("org_role")
                    }

                    if org_context.get("org_id"):
                        logger.info(f"User {username} logged in with org: {org_context.get('org_name')}")
                    else:
                        logger.info(f"User {username} logged in without organization")

                    # Create response with session cookie
                    response = JSONResponse({"success": True, "user": user_info})
                    # Build cookie kwargs for cross-subdomain support
                    login_cookie_kwargs = {
                        "key": "session_token",
                        "value": session_token,
                        "httponly": True,
                        "secure": (EXTERNAL_PROTOCOL == "https"),
                        "samesite": "none",
                        "max_age": 86400,  # 24 hours
                        "path": "/"
                    }
                    if "." in EXTERNAL_HOST and not EXTERNAL_HOST.startswith("localhost"):
                        login_cookie_kwargs["domain"] = f".{EXTERNAL_HOST}"
                    response.set_cookie(**login_cookie_kwargs)
                    return response
            else:
                # Authentication failed
                if AUDIT_ENABLED:
                    await log_auth_failure(
                        request,
                        username=username,
                        reason="Invalid credentials",
                        metadata={"status_code": response.status_code, "method": "direct_login"}
                    )

                return JSONResponse(
                    {"success": False, "detail": "Invalid username or password"},
                    status_code=401
                )
                
        except Exception as e:
            print(f"Direct login error: {e}")
            if AUDIT_ENABLED:
                await log_auth_failure(
                    request,
                    username=username,
                    reason=f"Authentication service error: {str(e)}",
                    metadata={"method": "direct_login"}
                )

            return JSONResponse(
                {"success": False, "detail": "Authentication service unavailable"},
                status_code=503
            )

# OAuth endpoints
@app.get("/auth/login")
async def oauth_login(request: Request):
    """Redirect to Authentik OAuth authorization"""
    state = secrets.token_urlsafe(32)
    # Capture return_url for post-login redirect
    return_url = request.query_params.get("return_url")
    sessions[state] = {"created": time.time(), "return_url": return_url}
    
    # Build redirect URI based on the request host
    if "yoda.unicorncommander.ai" in str(request.url):
        redirect_uri = "https://yoda.unicorncommander.ai/auth/callback"
        auth_base = "https://auth.yoda.unicorncommander.ai"
    else:
        # Use the external host from environment
        redirect_uri = f"https://{EXTERNAL_HOST}/auth/callback"
        auth_base = f"https://auth.{EXTERNAL_HOST}"

    # Keycloak realm (default to "master" if not specified)
    keycloak_realm = os.getenv("KEYCLOAK_REALM", "master")

    # Use Keycloak OAuth endpoints (not Authentik)
    auth_url = (
        f"{auth_base}/realms/{keycloak_realm}/protocol/openid-connect/auth"
        f"?client_id={OAUTH_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid%20profile%20email"
        f"&state={state}"
    )
    return RedirectResponse(url=auth_url)

# SSO Login Initiation Endpoints
@app.get("/auth/login/google")
async def login_google(request: Request):
    """Initiate Google OAuth via Keycloak"""
    keycloak_realm = os.getenv("KEYCLOAK_REALM", "master")
    auth_url = f"https://auth.{EXTERNAL_HOST}"
    redirect_uri = f"https://{EXTERNAL_HOST}/auth/callback"

    authorize_url = (
        f"{auth_url}/realms/{keycloak_realm}/protocol/openid-connect/auth"
        f"?client_id={OAUTH_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid email profile"
        f"&kc_idp_hint=google"
    )

    return RedirectResponse(url=authorize_url)


@app.get("/auth/login/github")
async def login_github(request: Request):
    """Initiate GitHub OAuth via Keycloak"""
    keycloak_realm = os.getenv("KEYCLOAK_REALM", "master")
    auth_url = f"https://auth.{EXTERNAL_HOST}"
    redirect_uri = f"https://{EXTERNAL_HOST}/auth/callback"

    authorize_url = (
        f"{auth_url}/realms/{keycloak_realm}/protocol/openid-connect/auth"
        f"?client_id={OAUTH_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid email profile"
        f"&kc_idp_hint=github"
    )

    return RedirectResponse(url=authorize_url)


@app.get("/auth/login/microsoft")
async def login_microsoft(request: Request):
    """Initiate Microsoft OAuth via Keycloak"""
    keycloak_realm = os.getenv("KEYCLOAK_REALM", "master")
    auth_url = f"https://auth.{EXTERNAL_HOST}"
    redirect_uri = f"https://{EXTERNAL_HOST}/auth/callback"

    authorize_url = (
        f"{auth_url}/realms/{keycloak_realm}/protocol/openid-connect/auth"
        f"?client_id={OAUTH_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid email profile"
        f"&kc_idp_hint=microsoft"
    )

    return RedirectResponse(url=authorize_url)


@app.get("/auth/callback")
async def oauth_callback(request: Request, code: str, state: str = None):
    """Handle OAuth callback from Keycloak"""
    # Log immediately to file to debug
    with open("/tmp/oauth_debug.log", "a") as f:
        f.write(f"=== OAuth callback at {datetime.now()} ===\n")
        f.write(f"Code: {code[:10] if code else 'None'}...\n")
        f.write(f"State: {state}\n")
        f.write(f"URL: {request.url}\n")
        f.write(f"Client ID: {OAUTH_CLIENT_ID}\n")
        f.write(f"Client Secret exists: {bool(OAUTH_CLIENT_SECRET)}\n")

    # Build correct redirect URI based on the request
    redirect_uri = f"https://{EXTERNAL_HOST}/auth/callback"

    # Keycloak realm (default to "uchub" for ops-center)
    keycloak_realm = os.getenv("KEYCLOAK_REALM", "uchub")

    # Use Keycloak token endpoint (INTERNAL URL for server-to-server communication)
    # Token exchange happens backend-to-backend, not via browser
    keycloak_url = os.getenv("KEYCLOAK_URL", "http://centerdeep-keycloak:8080")
    token_url = f"{keycloak_url}/realms/{keycloak_realm}/protocol/openid-connect/token"

    # Exchange code for token
    async with httpx.AsyncClient() as client:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": OAUTH_CLIENT_ID,
            "client_secret": OAUTH_CLIENT_SECRET
        }
        
        try:
            print(f"Starting token exchange to: {token_url}")
            print(f"With data: client_id={OAUTH_CLIENT_ID}, code={code[:10]}...")
            response = await client.post(token_url, data=data)
            print(f"Token exchange response: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    tokens = response.json()
                    access_token = tokens.get("access_token")
                    print(f"Got access token: {access_token[:20] if access_token else 'None'}...")
                    
                    if not access_token:
                        print(f"No access token in response: {tokens}")
                        return RedirectResponse(url="/?error=no_access_token")
                except Exception as e:
                    print(f"Failed to parse token response: {e}")
                    print(f"Response text: {response.text}")
                    return RedirectResponse(url="/?error=token_parse_error")
                
                # Get user info using external Keycloak URL
                # Use external URL to ensure JWT validation succeeds
                userinfo_url = f"https://auth.{EXTERNAL_HOST}/realms/{keycloak_realm}/protocol/openid-connect/userinfo"

                print(f"Getting user info from: {userinfo_url}")
                headers = {"Authorization": f"Bearer {access_token}"}
                user_response = await client.get(userinfo_url, headers=headers)
                print(f"User info response: {user_response.status_code}")
                
                if user_response.status_code == 200:
                    user_info = user_response.json()
                    print(f"User info retrieved: {user_info.get('username', 'unknown')}")

                    # Map Keycloak/Authentik role to ops-center role
                    user_info = add_role_to_user_info(user_info)
                    username = user_info.get('preferred_username') or user_info.get('username', 'unknown')
                    user_id = user_info.get('sub') or user_info.get('id', 'unknown')
                    role = user_info.get('role', 'viewer')
                    print(f"User '{username}' assigned role: {role}")
                    logger.info(f"OAuth callback: User '{username}' logged in with role '{role}'")

                    # Audit log successful OAuth authentication
                    if AUDIT_ENABLED:
                        await log_auth_success(
                            request,
                            user_id=user_id,
                            username=username,
                            metadata={"role": role, "method": "oauth_callback"}
                        )

                    # Get organization context for the user
                    email = user_info.get('email')
                    org_context = await get_user_org_context(user_id, email)
                    auto_provisioned = False  # Initialize for subscription check logic

                    # Create session with org data (store id_token for logout!)
                    session_token = secrets.token_urlsafe(32)
                    sessions[session_token] = {
                        "user": user_info,
                        "access_token": access_token,
                        "id_token": tokens.get("id_token"),  # Store id_token for proper logout
                        "created": time.time(),
                        "org_id": org_context.get("org_id"),
                        "org_name": org_context.get("org_name"),
                        "org_role": org_context.get("org_role")
                    }
                    print(f"Session created with token: {session_token[:10]}...")
                    # Note: sessions is RedisSessionManager, not a dict
                    if org_context.get("org_id"):
                        print(f"User belongs to org: {org_context.get('org_name')} (ID: {org_context.get('org_id')})")
                    else:
                        print(f"User has no organization assigned")

                    # Check if user has active subscription (UNLESS they're an admin)
                    user_role = user_info.get("role", "viewer")
                    org_id = org_context.get("org_id")

                    # Check for return_url from login flow (stored with state)
                    stored_return_url = None
                    if state:
                        try:
                            state_data = sessions.get(state)
                            if state_data and isinstance(state_data, dict):
                                stored_return_url = state_data.get("return_url")
                                print(f"Found stored return_url: {stored_return_url}")
                        except Exception as e:
                            print(f"Could not retrieve state data: {e}")

                    redirect_url = "/"  # Default to landing page

                    # Admins bypass payment gate entirely
                    if user_role == "admin":
                        print(f"User is admin, bypassing subscription check - direct access to landing page")
                        redirect_url = "/"
                    elif auto_provisioned:
                        print("Auto-provisioned user org, skipping subscription check")
                        redirect_url = "/"
                    elif org_id:
                        try:
                            # First check the database for subscription status
                            db_subscription = None
                            if hasattr(app.state, 'db_pool') and app.state.db_pool:
                                async with app.state.db_pool.acquire() as conn:
                                    db_sub_result = await conn.fetchrow("""
                                        SELECT subscription_plan, status
                                        FROM organization_subscriptions
                                        WHERE org_id = $1 AND status IN ('active', 'trialing')
                                        LIMIT 1
                                    """, org_id)
                                    if db_sub_result:
                                        db_subscription = {
                                            "plan_code": db_sub_result["subscription_plan"],
                                            "status": db_sub_result["status"]
                                        }
                                        print(f"Found active subscription in database: {db_subscription}")

                            # If database has active or trial subscription, allow access
                            if db_subscription and db_subscription.get("status") in ("active", "trialing"):
                                print(f"User has valid subscription (from database): {db_subscription.get('plan_code', 'unknown')} - status: {db_subscription.get('status')}")
                                redirect_url = "/"
                            else:
                                # Fall back to Lago check
                                from lago_integration import get_subscription
                                subscription = await get_subscription(org_id)

                                if not subscription or subscription.get("status") not in ("active", "trialing"):
                                    # No active or trial subscription - redirect to signup flow
                                    print(f"No active subscription for org {org_id}, redirecting to signup flow")
                                    redirect_url = "/signup-flow.html"
                                else:
                                    print(f"User has active subscription (from Lago): {subscription.get('plan_code', 'unknown')}")
                                    redirect_url = "/"
                        except Exception as e:
                            # If subscription check fails, log error but allow access
                            # This prevents blocking users if Lago is temporarily unavailable
                            logger.error(f"Error checking subscription: {e}")
                            print(f"Subscription check failed, allowing access: {e}")
                            redirect_url = "/"
                    else:
                        # No org_id - new user, redirect to signup flow
                        print(f"User has no organization, redirecting to signup flow")
                        redirect_url = "/signup-flow.html"

                    # Override with stored return_url if valid (external subdomain)
                    if stored_return_url and redirect_url != "/signup-flow.html":
                        # Validate return_url is a safe subdomain
                        if stored_return_url.startswith(f"https://") and EXTERNAL_HOST in stored_return_url:
                            print(f"Redirecting to return_url: {stored_return_url}")
                            redirect_url = stored_return_url
                        else:
                            print(f"Ignoring invalid return_url: {stored_return_url}")

                    # Redirect with session token
                    response = RedirectResponse(url=redirect_url)
                    
                    # Set cookie with domain for subdomain access
                    cookie_kwargs = {
                        "key": "session_token",
                        "value": session_token,
                        "path": "/",  # Ensure cookie is available for all paths
                        "httponly": True,
                        "secure": (EXTERNAL_PROTOCOL == "https"),
                        "samesite": "none",
                        "max_age": 86400  # 24 hours
                    }

                    # Set domain for cookie sharing across subdomains
                    # unicorncommander.ai -> .unicorncommander.ai
                    if "." in EXTERNAL_HOST and not EXTERNAL_HOST.startswith("localhost"):
                        cookie_kwargs["domain"] = f".{EXTERNAL_HOST}"
                        print(f"Setting cookie domain to: .{EXTERNAL_HOST}")

                    response.set_cookie(**cookie_kwargs)
                    print(f"Redirecting to {redirect_url} with session cookie")
                    print(f"Cookie config: httponly={cookie_kwargs['httponly']}, secure={cookie_kwargs['secure']}, domain={cookie_kwargs.get('domain', 'not set')}")
                    return response
                else:
                    print(f"Failed to get user info: {user_response.status_code}")
                    print(f"User info error: {user_response.text}")
            else:
                print(f"Token exchange failed: {response.status_code}")
                print(f"Token error: {response.text}")
        except Exception as e:
            print(f"OAuth error: {e}")
            import traceback
            traceback.print_exc()
    
    # On error, redirect back to root which will restart auth flow
    return RedirectResponse(url="/?error=authentication_failed")

@app.get("/auth/logout")
async def logout(request: Request):
    """Logout and clear session"""
    session_token = request.cookies.get("session_token")

    if session_token and session_token in sessions:
        # Get user info before deleting session
        session = sessions[session_token]
        user_info = session.get("user", {})
        username = user_info.get('preferred_username') or user_info.get('username', 'unknown')
        user_id = user_info.get('sub') or user_info.get('id', 'unknown')

        # Audit log logout
        if AUDIT_ENABLED:
            await log_logout(
                request,
                user_id=user_id,
                username=username,
                metadata={"method": "oauth_logout"}
            )

        # Delete session
        del sessions[session_token]

    # Redirect to root, which will trigger auth flow again
    response = RedirectResponse(url="/")
    response.delete_cookie("session_token")
    return response

@app.get("/auth/logged-out")
async def logged_out(request: Request):
    """Logout confirmation page that auto-redirects to login"""
    # Delete any remaining session from Redis
    session_token = request.cookies.get("session_token")
    if session_token and session_token in sessions:
        del sessions[session_token]

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Logged Out - Unicorn Commander</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 60px 80px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                text-align: center;
                max-width: 500px;
            }
            .icon {
                font-size: 64px;
                margin-bottom: 20px;
            }
            h1 {
                color: #667eea;
                font-size: 32px;
                margin-bottom: 10px;
            }
            p {
                color: #666;
                font-size: 18px;
                margin-bottom: 30px;
            }
            .spinner {
                display: inline-block;
                width: 40px;
                height: 40px;
                border: 4px solid rgba(102, 126, 234, 0.2);
                border-top-color: #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            .redirect-info {
                color: #999;
                font-size: 14px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon">👋</div>
            <h1>Logged Out Successfully</h1>
            <p>You have been signed out of your account.</p>
            <div class="spinner"></div>
            <div class="redirect-info">Redirecting to home page...</div>
        </div>
        <script>
            // Clear Keycloak session via hidden iframe
            const iframe = document.createElement('iframe');
            iframe.style.display = 'none';
            iframe.src = 'https://auth.unicorncommander.ai/realms/uchub/protocol/openid-connect/logout';
            document.body.appendChild(iframe);

            // Redirect to home page after 2 seconds (not /auth/login to avoid auto-login)
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        </script>
    </body>
    </html>
    """
    # Create response and delete the session cookie
    response = HTMLResponse(content=html_content)
    response.delete_cookie("session_token")
    return response

@app.get("/auth/user")
async def get_auth_user(request: Request):
    """Get current authenticated user info (endpoint for compatibility)"""
    user_data = await get_current_user(request)
    return {"user": user_data}

@app.get("/auth/check")
async def check_auth(request: Request):
    """Check authentication for Traefik ForwardAuth"""
    session_token = request.cookies.get("session_token")
    if not session_token or session_token not in sessions:
        # Return 401 to trigger redirect to login
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Return 200 to allow access
    return {"authenticated": True}

@app.get("/api/v1/auth/session")
async def get_session_info(request: Request):
    """Bridge OAuth session to React app"""
    print(f"Session endpoint called. Cookies: {request.cookies}")
    session_token = request.cookies.get("session_token")
    print(f"Session token from cookie: {session_token[:10] if session_token else 'None'}...")
    # Note: sessions is RedisSessionManager, not a dict

    if session_token and session_token in sessions:
        session = sessions[session_token]
        user_info = session.get("user", {})

        # Get the actual role from user_info (mapped during OAuth callback)
        user_role = user_info.get("role", "viewer")
        print(f"DEBUG: User role from session: {user_role}")

        # Generate a token for the React app to use
        import json
        import base64
        token_data = {
            "username": user_info.get("username", user_info.get("preferred_username", "user")),
            "role": user_role,
            "auth_method": "oauth"
        }
        # Simple token for React app (not secure, just for session bridging)
        token = base64.b64encode(json.dumps(token_data).encode()).decode()

        return {
            "authenticated": True,
            "token": token,
            "user": {
                "username": user_info.get("username", user_info.get("preferred_username", "user")),
                "email": user_info.get("email", ""),
                "name": user_info.get("name", ""),
                "role": user_role
            }
        }
    
    # No valid session found
    print(f"No valid session found. Token exists: {bool(session_token)}, In sessions: {session_token in sessions if session_token else False}")
    return JSONResponse(
        status_code=401,
        content={"authenticated": False, "detail": "No valid session"}
    )


@app.get("/api/v1/auth/sso-token")
async def get_sso_token(request: Request):
    """
    Return the session_token for trusted subdomain SSO.

    This endpoint allows trusted subdomains (*.your-domain.com) to obtain
    the session_token for use as a Bearer token in cross-origin API requests.

    The browser sends cookies to this endpoint (same origin), and we return
    the session_token in the response body for the subdomain to use.
    """
    origin = request.headers.get("origin", "")

    # Only allow requests from trusted subdomains
    trusted_origins = [
        f"https://{EXTERNAL_HOST}",
        f"https://leads.{EXTERNAL_HOST}",
        f"https://leads-api.{EXTERNAL_HOST}",
    ]

    if origin not in trusted_origins:
        print(f"[SSO-TOKEN] Rejected origin: {origin}")
        return JSONResponse(
            status_code=403,
            content={"detail": f"Origin not allowed: {origin}"},
            headers={
                "Access-Control-Allow-Origin": origin if origin else "*",
                "Access-Control-Allow-Credentials": "true",
            }
        )

    session_token = request.cookies.get("session_token")
    print(f"[SSO-TOKEN] Origin: {origin}, session_token exists: {bool(session_token)}")

    if session_token and session_token in sessions:
        session = sessions[session_token]
        user_info = session.get("user", {})

        if user_info:
            # Return the session_token for use as Bearer token
            response_data = {
                "authenticated": True,
                "session_token": session_token,
                "user": {
                    "id": user_info.get("sub", "unknown"),
                    "email": user_info.get("email", ""),
                    "name": user_info.get("preferred_username") or user_info.get("name", ""),
                    "is_admin": user_info.get("role") in ["admin", "power_user"]
                }
            }
            print(f"[SSO-TOKEN] Returning token for user: {user_info.get('email')}")
            response = JSONResponse(content=response_data)
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            return response

    print(f"[SSO-TOKEN] No valid session")
    response = JSONResponse(
        status_code=401,
        content={"authenticated": False, "detail": "No valid session"}
    )
    response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


# Login route handler - checks for existing session and handles return_url
@app.get("/login")
async def login_page(request: Request):
    """Handle login requests with return_url support for SSO.

    If user already has a valid session (e.g., logged into ops-center),
    redirect directly to return_url for seamless SSO experience.
    If not authenticated, initiate OAuth flow with Keycloak.
    """
    session_token = request.cookies.get("session_token")
    return_url = request.query_params.get("return_url")

    print(f"[LOGIN] return_url={return_url}, session_token exists={bool(session_token)}")

    # If already authenticated, redirect to return_url or home
    if session_token and session_token in sessions:
        session_data = sessions.get(session_token)
        if session_data and session_data.get("user"):
            print(f"[LOGIN] User already authenticated, redirecting to return_url")
            if return_url:
                # Validate return_url is a safe subdomain
                if return_url.startswith("https://") and EXTERNAL_HOST in return_url:
                    # Set cookie again with proper domain before redirect
                    response = RedirectResponse(url=return_url)
                    cookie_kwargs = {
                        "key": "session_token",
                        "value": session_token,
                        "httponly": True,
                        "secure": (EXTERNAL_PROTOCOL == "https"),
                        "samesite": "none",
                        "max_age": 86400,
                        "path": "/"
                    }
                    if "." in EXTERNAL_HOST and not EXTERNAL_HOST.startswith("localhost"):
                        cookie_kwargs["domain"] = f".{EXTERNAL_HOST}"
                    response.set_cookie(**cookie_kwargs)
                    return response
            return RedirectResponse(url="/")

    # Not authenticated, start OAuth flow with return_url preserved
    print(f"[LOGIN] No valid session, redirecting to OAuth")
    oauth_url = "/auth/login"
    if return_url:
        oauth_url += f"?return_url={return_url}"
    return RedirectResponse(url=oauth_url)

# Login page endpoint - now just redirects to OAuth
@app.get("/login.html")
async def serve_login():
    """Redirect to OAuth login flow"""
    return RedirectResponse(url="/auth/login")

# Serve the React app for dashboard route (handles refresh)
@app.get("/dashboard")
async def serve_dashboard(request: Request):
    """Serve the React app for /dashboard route with auth check"""
    session_token = request.cookies.get("session_token")

    if session_token and session_token in sessions:
        # User is authenticated, serve the React app
        for index_path in ["public/index.html", "dist/index.html", "../public/index.html"]:
            if os.path.exists(index_path):
                response = FileResponse(index_path)
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
        raise HTTPException(status_code=404, detail="Frontend not found")
    else:
        # Not authenticated, redirect to OAuth login
        return RedirectResponse(url="/auth/login", status_code=302)

# Serve the React app for admin routes
@app.get("/admin")
@app.get("/admin/{path:path}")
async def serve_admin(request: Request, path: str = ""):
    """Serve the React admin app for all /admin routes"""
    # Check if user is authenticated via session cookie
    session_token = request.cookies.get("session_token")

    # If authenticated via OAuth, create a bridge to the React app
    if session_token and session_token in sessions:
        # User is authenticated, serve the admin page
        # The React app will need to call /api/v1/auth/me to get user info
        if os.path.exists("public/index.html"):
            response = FileResponse("public/index.html")
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        elif os.path.exists("dist/index.html"):
            response = FileResponse("dist/index.html")
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        elif os.path.exists("../public/index.html"):
            response = FileResponse("../public/index.html")
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
    else:
        # Not authenticated, redirect to OAuth login
        return RedirectResponse(url="/auth/login", status_code=302)

    raise HTTPException(status_code=404, detail="Admin interface not found")

# Serve the React app for all non-API routes
@app.get("/{full_path:path}")
async def serve_spa(full_path: str, request: Request):
    """Serve the React app for all routes (excluding API paths)"""
    # CRITICAL FIX: Skip API routes BEFORE processing anything else
    # This allows FastAPI routers to handle API requests naturally
    if full_path.startswith("api/"):
        # Don't handle API routes here - let them fall through to 404
        # which will be caught by the registered routers
        from fastapi import status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found"
        )

    # Skip empty path as it's handled by the root redirect
    if full_path == "":
        print("Catch-all got empty path, this shouldn't happen")
        return RedirectResponse(url="/login.html", status_code=302)

    # Check if requesting a static file
    if full_path.startswith(("assets/", "logos/")) or full_path.endswith((".html", ".js", ".css", ".png", ".jpg", ".svg", ".ico", ".json", ".webmanifest", ".woff", ".woff2", ".ttf", ".webp", ".jpeg", ".gif")):
        # First check public directory
        public_path = os.path.join("public", full_path)
        if os.path.exists(public_path):
            return FileResponse(public_path)
        # Then check dist directory
        file_path = os.path.join("dist", full_path)
        if os.path.exists(file_path):
            return FileResponse(file_path)

    # For all other routes, return the index.html (for React Router)
    # Check public directory first (deployed build), then dist
    for index_path in ["public/index.html", "dist/index.html"]:
        if os.path.exists(index_path):
            # Add cache-control headers to prevent browser caching of index.html
            response = FileResponse(index_path)
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
    raise HTTPException(status_code=404, detail="Frontend not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)
