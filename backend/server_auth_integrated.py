"""
UC-1 Pro Ops Center Backend - WITH CUSTOM AUTH INTEGRATION

This is the updated server.py with custom OAuth authentication replacing Authentik.
Integrates the auth module for direct OAuth with Google, GitHub, Microsoft.
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Depends, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse, HTMLResponse, RedirectResponse
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
import secrets
import base64

# Import existing managers
from server_docker_manager import DockerServiceManager
from quick_docker_fix import get_running_services
from network_manager import network_manager
from ai_model_manager import ai_model_manager, ModelSettingsUpdate, ModelDownloadRequest
from storage_manager import storage_backup_manager, StorageInfo, BackupConfig, BackupInfo, BackupStatus
from extension_manager import extension_manager, ExtensionInstallRequest, ExtensionActionRequest, ExtensionConfigUpdate
from log_manager import log_manager, LogFilter, LogExportRequest
from landing_config import landing_config
from service_access import service_access_manager

# ===== NEW: CUSTOM AUTH MODULE IMPORTS =====
from auth import (
    OAuthManager,
    SessionManager,
    SubscriptionManager,
    SubscriptionTier,
    AccessControl,
    ServiceManager,
    UsageTracker,
    deployment_config
)

# Database imports (we'll need these for user storage)
import sqlite3
from contextlib import contextmanager

# ===== CONFIGURATION =====

# OAuth Configuration from environment
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET")
MICROSOFT_CLIENT_ID = os.environ.get("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.environ.get("MICROSOFT_CLIENT_SECRET")

# External URL configuration
EXTERNAL_HOST = os.environ.get("EXTERNAL_HOST", "your-domain.com")
EXTERNAL_PROTOCOL = os.environ.get("EXTERNAL_PROTOCOL", "https")

# Build OAuth redirect URI
if EXTERNAL_PROTOCOL == "https" and "your-domain.com" in EXTERNAL_HOST:
    OAUTH_REDIRECT_URI = f"{EXTERNAL_PROTOCOL}://{EXTERNAL_HOST}/auth/callback"
elif EXTERNAL_PROTOCOL == "http" and EXTERNAL_HOST == "localhost":
    OAUTH_REDIRECT_URI = f"{EXTERNAL_PROTOCOL}://{EXTERNAL_HOST}:8084/auth/callback"
else:
    OAUTH_REDIRECT_URI = f"{EXTERNAL_PROTOCOL}://{EXTERNAL_HOST}:8084/auth/callback"

# Redis configuration
REDIS_URL = os.environ.get("REDIS_URL", "redis://unicorn-redis:6379/0")

# Stripe configuration
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

# Lago configuration
LAGO_API_URL = os.environ.get("LAGO_API_URL", "http://unicorn-lago-api:3000")
LAGO_API_KEY = os.environ.get("LAGO_API_KEY")

# Encryption key for BYOK
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    print("WARNING: ENCRYPTION_KEY not set, generating temporary key")
    from cryptography.fernet import Fernet
    ENCRYPTION_KEY = Fernet.generate_key().decode()

# ===== INITIALIZE AUTH COMPONENTS =====

# Initialize OAuth Manager
oauth_manager = OAuthManager(
    google_client_id=GOOGLE_CLIENT_ID,
    google_client_secret=GOOGLE_CLIENT_SECRET,
    github_client_id=GITHUB_CLIENT_ID,
    github_client_secret=GITHUB_CLIENT_SECRET,
    microsoft_client_id=MICROSOFT_CLIENT_ID,
    microsoft_client_secret=MICROSOFT_CLIENT_SECRET,
    redirect_uri=OAUTH_REDIRECT_URI
)

# Initialize Session Manager
session_manager = SessionManager(
    redis_url=REDIS_URL,
    session_ttl=86400  # 24 hours
)

# Initialize Subscription Manager
subscription_manager = SubscriptionManager(
    stripe_api_key=STRIPE_SECRET_KEY
)

# Initialize Access Control
access_control = AccessControl(subscription_manager)

# Initialize Service Manager (BYOK)
service_manager = ServiceManager(
    redis_url=REDIS_URL,
    encryption_key=ENCRYPTION_KEY
)

# Initialize Usage Tracker
usage_tracker = UsageTracker(
    lago_api_url=LAGO_API_URL,
    lago_api_key=LAGO_API_KEY,
    redis_url=REDIS_URL
)

# ===== DATABASE SETUP =====

DB_PATH = "/home/muut/Production/UC-1-Pro/volumes/ops_center.db"

@contextmanager
def get_db():
    """Database connection context manager"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """Initialize database schema"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            oauth_provider TEXT NOT NULL,
            oauth_id TEXT NOT NULL,
            subscription_tier TEXT DEFAULT 'trial',
            stripe_customer_id TEXT,
            lago_customer_id TEXT,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_stripe ON users(stripe_customer_id)")

        print("✓ Database initialized")

def get_or_create_user(oauth_provider: str, oauth_id: str, email: str, name: str) -> Dict:
    """Get existing user or create new one"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Try to find existing user by email or OAuth ID
        cursor.execute(
            "SELECT * FROM users WHERE email = ? OR (oauth_provider = ? AND oauth_id = ?)",
            (email, oauth_provider, oauth_id)
        )
        row = cursor.fetchone()

        if row:
            # Update user info
            user_id = row["id"]
            cursor.execute(
                "UPDATE users SET name = ?, oauth_provider = ?, oauth_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (name, oauth_provider, oauth_id, user_id)
            )
            user = dict(row)
        else:
            # Create new user
            user_id = secrets.token_urlsafe(16)
            cursor.execute(
                """INSERT INTO users (id, email, name, oauth_provider, oauth_id, subscription_tier)
                   VALUES (?, ?, ?, ?, ?, 'trial')""",
                (user_id, email, name, oauth_provider, oauth_id)
            )

            # Create Lago customer for Professional/Enterprise tiers later
            # For now, new users start on trial

            user = {
                "id": user_id,
                "email": email,
                "name": name,
                "oauth_provider": oauth_provider,
                "oauth_id": oauth_id,
                "subscription_tier": "trial",
                "is_admin": False
            }

        return user

def update_user_tier(user_id: str, tier: str, stripe_customer_id: str = None):
    """Update user's subscription tier"""
    with get_db() as conn:
        cursor = conn.cursor()
        if stripe_customer_id:
            cursor.execute(
                "UPDATE users SET subscription_tier = ?, stripe_customer_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (tier, stripe_customer_id, user_id)
            )
        else:
            cursor.execute(
                "UPDATE users SET subscription_tier = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (tier, user_id)
            )

# ===== FASTAPI APP SETUP =====

app = FastAPI(title="UC-1 Pro Admin Dashboard API")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    init_database()
    print("✓ Auth system initialized")

# Initialize Docker service manager
docker_manager = DockerServiceManager()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enable GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Initialize Docker client
try:
    docker_client = docker.from_env()
except Exception as e:
    print(f"Warning: Docker client initialization failed: {e}")
    docker_client = None

# ===== AUTHENTICATION ENDPOINTS =====

@app.get("/", include_in_schema=False)
async def root_redirect(request: Request):
    """Redirect to dashboard if authenticated, or login if not"""
    session_token = request.cookies.get("session_token")
    session = session_manager.get(session_token) if session_token else None

    if session:
        # Authenticated - redirect to dashboard
        return RedirectResponse(url="/dashboard", status_code=302)
    else:
        # Not authenticated - show login page
        return RedirectResponse(url="/login.html", status_code=302)

@app.get("/auth/login/{provider}")
async def oauth_login(provider: str):
    """
    Initiate OAuth login with a provider (google, github, microsoft)

    Returns redirect to provider's authorization page
    """
    try:
        auth_url, state = oauth_manager.get_auth_url(provider)
        return RedirectResponse(url=auth_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/auth/callback")
async def oauth_callback(code: str, state: str, request: Request):
    """
    OAuth callback handler - receives authorization code and exchanges for user info

    Creates user account and session, then redirects to dashboard
    """
    try:
        # Exchange code for user information
        user_info = await oauth_manager.handle_callback(code, state)

        # Get or create user in database
        user = get_or_create_user(
            oauth_provider=user_info.get("provider"),
            oauth_id=user_info.get("id"),
            email=user_info.get("email"),
            name=user_info.get("name", user_info.get("email"))
        )

        # Create Lago customer if on Professional/Enterprise tier
        if user["subscription_tier"] in ["professional", "enterprise"]:
            await usage_tracker.create_lago_customer(
                user_id=user["id"],
                email=user["email"],
                name=user["name"],
                tier=user["subscription_tier"]
            )

        # Create session
        session_token = session_manager.create_session({
            "user_id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "subscription_tier": user["subscription_tier"],
            "is_admin": bool(user.get("is_admin"))
        })

        # Set session cookie and redirect to dashboard
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=(EXTERNAL_PROTOCOL == "https"),
            samesite="lax",
            max_age=86400  # 24 hours
        )

        return response

    except Exception as e:
        print(f"OAuth callback error: {e}")
        # Redirect to login with error
        return RedirectResponse(url="/login.html?error=auth_failed", status_code=302)

@app.get("/auth/logout")
async def logout(request: Request):
    """Logout user by deleting session"""
    session_token = request.cookies.get("session_token")
    if session_token:
        session_manager.delete_session(session_token)

    response = RedirectResponse(url="/login.html", status_code=302)
    response.delete_cookie("session_token")
    return response

@app.get("/auth/user")
async def get_current_user(request: Request):
    """Get current authenticated user info"""
    session_token = request.cookies.get("session_token")
    session = session_manager.get(session_token) if session_token else None

    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get fresh user data from database
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        user = dict(row)

    # Get usage statistics
    usage = await usage_tracker.get_user_usage(user["id"])
    credits = await usage_tracker.get_remaining_credits(
        user["id"],
        user["subscription_tier"]
    )

    return {
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "subscription_tier": user["subscription_tier"],
            "is_admin": bool(user.get("is_admin"))
        },
        "usage": usage,
        "credits": credits,
        "tier_features": subscription_manager.get_tier_features(user["subscription_tier"])
    }

# ===== SUBSCRIPTION ENDPOINTS =====

@app.post("/api/v1/subscription/checkout")
async def create_checkout_session(request: Request, tier: str):
    """Create Stripe checkout session for subscription"""
    session_token = request.cookies.get("session_token")
    session = session_manager.get(session_token) if session_token else None

    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get user
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],))
        user = dict(cursor.fetchone())

    # Create checkout session
    success_url = f"{EXTERNAL_PROTOCOL}://{EXTERNAL_HOST}/payment-success?tier={tier}"
    cancel_url = f"{EXTERNAL_PROTOCOL}://{EXTERNAL_HOST}/pricing"

    checkout_url = await subscription_manager.create_checkout_session(
        tier=tier,
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=user["email"],
        metadata={
            "user_id": user["id"],
            "tier": tier
        }
    )

    return {"checkout_url": checkout_url}

@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    import stripe

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Handle event
    action = await subscription_manager.handle_webhook(
        event_type=event["type"],
        event_data=event["data"]
    )

    if action["action"] == "activate_subscription":
        # Update user tier in database
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM users WHERE email = ?",
                (action["email"],)
            )
            row = cursor.fetchone()
            if row:
                user_id = row["id"]
                update_user_tier(
                    user_id=user_id,
                    tier=action["tier"],
                    stripe_customer_id=action.get("subscription_id")
                )

                # Create Lago customer if needed
                if action["tier"] in ["professional", "enterprise"]:
                    await usage_tracker.create_lago_customer(
                        user_id=user_id,
                        email=action["email"],
                        name=action["email"].split("@")[0],
                        tier=action["tier"]
                    )

    return {"status": "success"}

# ===== USAGE TRACKING ENDPOINTS =====

@app.get("/api/v1/user/usage")
async def get_user_usage(request: Request):
    """Get user's API usage statistics"""
    session_token = request.cookies.get("session_token")
    session = session_manager.get(session_token) if session_token else None

    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    usage = await usage_tracker.get_user_usage(session["user_id"])
    credits = await usage_tracker.get_remaining_credits(
        session["user_id"],
        session["subscription_tier"]
    )

    return {
        "usage": usage,
        "credits": credits
    }

# ===== EXAMPLE PROTECTED ENDPOINT =====

@app.post("/api/v1/inference")
async def inference_endpoint(request: Request, prompt: str):
    """
    Example protected endpoint with usage tracking

    Checks:
    1. User is authenticated
    2. User's tier can access managed inference
    3. User hasn't exceeded usage limits
    4. Tracks usage for billing
    """
    session_token = request.cookies.get("session_token")
    session = session_manager.get(session_token) if session_token else None

    # Require authentication
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Check if user can access managed inference
    access_control.require_service(session, "managed_inference")

    # Check usage limit
    can_use = await usage_tracker.check_usage_limit(
        user_id=session["user_id"],
        tier=session["subscription_tier"],
        event_type="inference"
    )

    if not can_use:
        credits = await usage_tracker.get_remaining_credits(
            session["user_id"],
            session["subscription_tier"]
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "usage_limit_exceeded",
                "message": f"You've used all {credits['included_credits']} included credits.",
                "upgrade_url": "/pricing"
            }
        )

    # TODO: Call actual LLM service here
    # For now, return mock response
    response = {
        "response": f"Mock LLM response to: {prompt}",
        "model": "gpt-4",
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }

    # Track usage
    await usage_tracker.track_usage(
        user_id=session["user_id"],
        event_type="inference",
        quantity=1,
        metadata={
            "model": response["model"],
            "tokens": response["usage"]["total_tokens"]
        }
    )

    return response

# ===== KEEP ALL EXISTING ENDPOINTS FROM ORIGINAL server.py =====
# (The rest of the file would include all other endpoints like /api/v1/system/status, etc.)
# For brevity, this is the key auth integration section

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
