"""
Tier-based Access Control Middleware

Provides middleware functions for protecting services based on user subscription tier.
Used by Open-WebUI, Center-Deep, and other protected services.
"""

from functools import wraps
import requests
import os
import logging

# Optional Flask imports (for Flask-based services)
try:
    from flask import request, jsonify, g
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

logger = logging.getLogger(__name__)

# Service access requirements by tier
SERVICE_ACCESS = {
    'ops-center': {
        'min_tier': 'free',
        'description': 'Ops Center Dashboard'
    },
    'chat': {
        'min_tier': 'free',
        'description': 'Open-WebUI Chat Interface'
    },
    'search': {
        'min_tier': 'starter',
        'description': 'Center-Deep Search'
    },
    'search-reranking': {
        'min_tier': 'professional',
        'description': 'Advanced Search Reranking'
    },
    'billing': {
        'min_tier': 'professional',
        'description': 'Lago Billing Dashboard'
    },
    'litellm': {
        'min_tier': 'professional',
        'description': 'LiteLLM Gateway (50+ Models)'
    },
    'tts': {
        'min_tier': 'professional',
        'description': 'Text-to-Speech (Unicorn Orator)'
    },
    'stt': {
        'min_tier': 'professional',
        'description': 'Speech-to-Text (Unicorn Amanuensis)'
    },
    'team-management': {
        'min_tier': 'enterprise',
        'description': 'Team Management'
    },
    'sso': {
        'min_tier': 'enterprise',
        'description': 'SSO Integration'
    },
    'audit-logs': {
        'min_tier': 'enterprise',
        'description': 'Audit Logs'
    }
}

# Tier hierarchy (for comparison)
TIER_LEVELS = {
    'free': 0,
    'starter': 1,
    'professional': 2,
    'enterprise': 3
}

# Rate limits by tier (requests per minute)
RATE_LIMITS = {
    'free': 10,
    'starter': 100,
    'professional': 1000,
    'enterprise': -1  # Unlimited
}

# Concurrent search limits
CONCURRENT_SEARCH_LIMITS = {
    'free': 1,
    'starter': 3,
    'professional': 10,
    'enterprise': -1  # Unlimited
}


def get_user_tier(user_id=None, email=None):
    """
    Get user's subscription tier from Ops Center API.

    Args:
        user_id: User ID
        email: User email (alternative to user_id)

    Returns:
        dict: User info with subscription_tier, or None if not found
    """
    try:
        ops_center_url = os.getenv('OPS_CENTER_URL', 'http://unicorn-ops-center:8084')

        # Try to get user info from Ops Center
        response = requests.get(
            f"{ops_center_url}/api/v1/user/profile",
            params={'user_id': user_id, 'email': email},
            timeout=5
        )

        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"Failed to get user tier: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error getting user tier: {e}")
        return None


def check_service_access(user_tier, service_name):
    """
    Check if user tier has access to service.

    Args:
        user_tier: User's subscription tier (free, starter, professional, enterprise)
        service_name: Service identifier

    Returns:
        tuple: (has_access: bool, required_tier: str, message: str)
    """
    if service_name not in SERVICE_ACCESS:
        # Unknown service - default to requiring professional tier
        return False, 'professional', f'Service {service_name} requires Professional tier or higher'

    service = SERVICE_ACCESS[service_name]
    required_tier = service['min_tier']

    user_level = TIER_LEVELS.get(user_tier.lower(), 0)
    required_level = TIER_LEVELS.get(required_tier.lower(), 0)

    has_access = user_level >= required_level

    if not has_access:
        message = f"{service['description']} requires {required_tier.capitalize()} tier or higher"
    else:
        message = "Access granted"

    return has_access, required_tier, message


def get_rate_limit(user_tier):
    """Get rate limit for user tier."""
    return RATE_LIMITS.get(user_tier.lower(), RATE_LIMITS['free'])


def get_concurrent_search_limit(user_tier):
    """Get concurrent search limit for user tier."""
    return CONCURRENT_SEARCH_LIMITS.get(user_tier.lower(), CONCURRENT_SEARCH_LIMITS['free'])


def require_tier(min_tier, service_name=None):
    """
    Decorator to protect routes with tier requirements.

    Usage:
        @app.route('/api/advanced-search')
        @require_tier('professional', 'search-reranking')
        def advanced_search():
            return {'results': [...]}

    Args:
        min_tier: Minimum subscription tier required
        service_name: Service identifier for access control
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user info from request (various sources)
            user_info = None

            # 1. Try to get from Flask g object (set by auth middleware)
            if hasattr(g, 'user'):
                user_info = g.user

            # 2. Try to get from request headers
            elif request.headers.get('X-User-Email'):
                email = request.headers.get('X-User-Email')
                user_info = get_user_tier(email=email)

            # 3. Try to get from request args
            elif request.args.get('user_id'):
                user_id = request.args.get('user_id')
                user_info = get_user_tier(user_id=user_id)

            # 4. Try to get from session/cookie
            elif request.cookies.get('user_email'):
                email = request.cookies.get('user_email')
                user_info = get_user_tier(email=email)

            if not user_info:
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please log in to access this feature'
                }), 401

            user_tier = user_info.get('subscription_tier', 'free')

            # Check access
            service = service_name or f.__name__
            has_access, required_tier, message = check_service_access(user_tier, service)

            if not has_access:
                return jsonify({
                    'error': 'Upgrade required',
                    'message': message,
                    'current_tier': user_tier,
                    'required_tier': required_tier,
                    'upgrade_url': f'/billing#upgrade-{required_tier}'
                }), 403

            # Add user info to g for use in route
            g.user = user_info
            g.user_tier = user_tier

            return f(*args, **kwargs)

        return decorated_function
    return decorator


def check_rate_limit(user_tier, identifier):
    """
    Check if user has exceeded rate limit.

    Args:
        user_tier: User's subscription tier
        identifier: Unique identifier for rate limiting (user_id, IP, etc.)

    Returns:
        tuple: (allowed: bool, limit: int, remaining: int)
    """
    # TODO: Implement Redis-based rate limiting
    # For now, return simple limit check
    limit = get_rate_limit(user_tier)

    if limit == -1:
        # Unlimited
        return True, -1, -1

    # Placeholder - would check Redis counter here
    return True, limit, limit


def tier_middleware(app):
    """
    Add tier checking middleware to Flask app.

    Usage:
        from tier_middleware import tier_middleware

        app = Flask(__name__)
        tier_middleware(app)
    """
    if not FLASK_AVAILABLE:
        raise ImportError("Flask is required to use tier_middleware. Install Flask or use FastAPI version.")

    @app.before_request
    def check_tier_access():
        """Check tier access before each request."""
        # Skip tier check for certain paths
        skip_paths = [
            '/health',
            '/api/v1/health',
            '/auth/login',
            '/auth/logout',
            '/auth/callback',
            '/static/',
            '/_debug'
        ]

        if any(request.path.startswith(path) for path in skip_paths):
            return None

        # Get user info from session/headers
        # This would be set by your auth middleware
        if hasattr(g, 'user'):
            user_tier = g.user.get('subscription_tier', 'free')

            # Log access for analytics
            logger.info(f"Access: {request.path} by tier: {user_tier}")

            # Check rate limit
            user_id = g.user.get('user_id')
            if user_id:
                allowed, limit, remaining = check_rate_limit(user_tier, user_id)
                if not allowed:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'You have exceeded your rate limit of {limit} requests per minute',
                        'upgrade_url': '/billing#upgrade'
                    }), 429

        return None


# FastAPI version for Python async services
def require_tier_fastapi(min_tier: str, service_name: str = None):
    """
    FastAPI dependency for tier checking.

    Usage:
        from fastapi import Depends
        from tier_middleware import require_tier_fastapi

        @app.get("/api/advanced-search")
        async def advanced_search(
            user_tier: str = Depends(require_tier_fastapi('professional'))
        ):
            return {"results": [...]}
    """
    async def dependency(request):
        # Get user info from request
        user_email = request.headers.get('X-User-Email')

        if not user_email:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )

        user_info = get_user_tier(email=user_email)

        if not user_info:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )

        user_tier = user_info.get('subscription_tier', 'free')
        service = service_name or "unknown"

        has_access, required_tier, message = check_service_access(user_tier, service)

        if not has_access:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=403,
                detail={
                    'error': 'Upgrade required',
                    'message': message,
                    'current_tier': user_tier,
                    'required_tier': required_tier,
                    'upgrade_url': f'/billing#upgrade-{required_tier}'
                }
            )

        return user_tier

    return dependency


# Express.js middleware export (for reference)
EXPRESS_MIDDLEWARE_EXAMPLE = """
// Express.js middleware for Open-WebUI (JavaScript)
// Save as: open-webui/backend/middleware/tierCheck.js

const axios = require('axios');

const OPS_CENTER_URL = process.env.OPS_CENTER_URL || 'http://unicorn-ops-center:8084';

async function getUserTier(userId, email) {
  try {
    const response = await axios.get(`${OPS_CENTER_URL}/api/v1/user/profile`, {
      params: { user_id: userId, email: email },
      timeout: 5000
    });
    return response.data;
  } catch (err) {
    console.error('Failed to get user tier:', err.message);
    return null;
  }
}

function requireTier(minTier, serviceName) {
  return async (req, res, next) => {
    // Get user from request (set by auth middleware)
    const userEmail = req.user?.email || req.headers['x-user-email'];

    if (!userEmail) {
      return res.status(401).json({
        error: 'Authentication required',
        message: 'Please log in to access this feature'
      });
    }

    const userInfo = await getUserTier(null, userEmail);

    if (!userInfo) {
      return res.status(401).json({
        error: 'User not found'
      });
    }

    const userTier = userInfo.subscription_tier || 'free';

    // Check access (implement tier comparison logic)
    const TIER_LEVELS = {
      'free': 0,
      'starter': 1,
      'professional': 2,
      'enterprise': 3
    };

    const userLevel = TIER_LEVELS[userTier.toLowerCase()] || 0;
    const requiredLevel = TIER_LEVELS[minTier.toLowerCase()] || 0;

    if (userLevel < requiredLevel) {
      return res.status(403).json({
        error: 'Upgrade required',
        message: `This feature requires ${minTier} tier or higher`,
        current_tier: userTier,
        required_tier: minTier,
        upgrade_url: `/billing#upgrade-${minTier}`
      });
    }

    // Add tier info to request
    req.userTier = userTier;
    req.userInfo = userInfo;

    next();
  };
}

module.exports = { requireTier, getUserTier };
"""

if __name__ == '__main__':
    # Test the middleware
    print("Tier Middleware Test")
    print("=" * 50)

    # Test service access
    for tier in ['free', 'starter', 'professional', 'enterprise']:
        print(f"\n{tier.upper()} Tier:")
        for service in ['chat', 'search', 'billing', 'litellm', 'team-management']:
            has_access, required, msg = check_service_access(tier, service)
            status = "✓" if has_access else "✗"
            print(f"  {status} {service}: {msg}")

    print("\n" + "=" * 50)
    print("Rate Limits:")
    for tier in ['free', 'starter', 'professional', 'enterprise']:
        limit = get_rate_limit(tier)
        limit_str = "Unlimited" if limit == -1 else f"{limit}/min"
        print(f"  {tier.capitalize()}: {limit_str}")
