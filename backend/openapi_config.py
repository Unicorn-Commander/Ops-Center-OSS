"""
OpenAPI Configuration for UC-Cloud Ops-Center API
Enhanced metadata and documentation for auto-generated API docs
"""

from typing import Dict, List

# OpenAPI Metadata
openapi_metadata = {
    "title": "UC-Cloud Ops-Center API",
    "version": "2.1.0",
    "description": """
# UC-Cloud Operations Center API

The Ops-Center API provides centralized management for the entire UC-Cloud ecosystem.

## Features

- 🔐 **User Management**: Keycloak SSO integration with role-based access control
- 🏢 **Organization Management**: Multi-tenant organizations with team management
- 💰 **Billing & Subscriptions**: Lago billing with Stripe payment processing
- 🤖 **LLM Infrastructure**: LiteLLM proxy supporting 100+ AI models
- 🐳 **Service Management**: Docker orchestration and monitoring
- 📊 **Analytics & Monitoring**: Real-time metrics and usage tracking
- 🔧 **Traefik Management**: Dynamic routing, SSL/TLS, load balancing
- 💾 **Storage & Backup**: Restic-based backup management

## Authentication

All endpoints require JWT Bearer token authentication via Keycloak SSO.

**To authenticate:**

1. Navigate to [https://auth.unicorncommander.ai](https://auth.unicorncommander.ai)
2. Login with credentials or OAuth provider (Google, GitHub, Microsoft)
3. Extract the `access_token` from the response
4. Include in API requests: `Authorization: Bearer <token>`

## Rate Limiting

API endpoints are rate-limited based on subscription tier:

| Tier | Monthly Limit | Burst Limit |
|------|--------------|-------------|
| Trial | 700 requests | 10/min |
| Starter | 1,000 requests | 50/min |
| Professional | 10,000 requests | 200/min |
| Enterprise | Unlimited | 1000/min |

## Subscription Tiers

### Trial - $1/week
- 100 API calls per day
- Open-WebUI access
- Basic AI models
- Community support

### Starter - $19/month ⭐
- 1,000 API calls per month
- Open-WebUI + Center-Deep access
- All AI models
- BYOK support
- Email support

### Professional - $49/month 🚀
- 10,000 API calls per month
- All services (Chat, Search, TTS, STT)
- Billing dashboard access
- Priority support
- BYOK support

### Enterprise - $99/month 💼
- Unlimited API calls
- Team management (5 seats)
- Custom integrations
- 24/7 dedicated support
- White-label options

## Support

- **Documentation**: [https://unicorncommander.com](https://unicorncommander.com)
- **Email**: support@magicunicorn.tech
- **GitHub**: [UC-Cloud Repository](https://github.com/Unicorn-Commander/UC-Cloud)

## Version History

- **v2.1.0** (October 2025): Added analytics endpoints, BYOK, bulk operations
- **v2.0.0** (September 2025): Lago billing integration, organization management
- **v1.0.0** (August 2025): Initial release with user management and LLM proxy
""",
    "contact": {
        "name": "UC-Cloud Support",
        "url": "https://unicorncommander.com",
        "email": "support@magicunicorn.tech"
    },
    "license_info": {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    "terms_of_service": "https://unicorncommander.com/terms",
    "openapi_tags": [
        {
            "name": "authentication",
            "description": "User authentication and session management via Keycloak SSO"
        },
        {
            "name": "users",
            "description": "User management operations (admin only)"
        },
        {
            "name": "organizations",
            "description": "Organization and team management"
        },
        {
            "name": "subscriptions",
            "description": "Subscription plan management and billing"
        },
        {
            "name": "billing",
            "description": "Billing operations, invoices, and payment methods"
        },
        {
            "name": "LLM",
            "description": "LLM inference endpoints (OpenAI-compatible)"
        },
        {
            "name": "LLM Configuration",
            "description": "LLM model configuration and management"
        },
        {
            "name": "LLM Management",
            "description": "LiteLLM proxy routing and provider management"
        },
        {
            "name": "credits",
            "description": "Credit system for API usage tracking"
        },
        {
            "name": "byok",
            "description": "Bring Your Own Key (BYOK) provider key management"
        },
        {
            "name": "services",
            "description": "Docker service management and monitoring"
        },
        {
            "name": "traefik",
            "description": "Traefik reverse proxy management"
        },
        {
            "name": "Traefik Routes",
            "description": "HTTP/HTTPS route configuration"
        },
        {
            "name": "Traefik Services",
            "description": "Backend service definitions"
        },
        {
            "name": "Traefik Middlewares",
            "description": "Request/response middleware configuration"
        },
        {
            "name": "Traefik Metrics",
            "description": "Traefik performance metrics"
        },
        {
            "name": "system-metrics",
            "description": "System resource monitoring (CPU, memory, GPU, disk)"
        },
        {
            "name": "analytics",
            "description": "Usage analytics and reporting"
        },
        {
            "name": "Storage & Backup",
            "description": "Restic backup management and storage operations"
        },
        {
            "name": "Email Notifications",
            "description": "Email notification preferences and scheduling"
        },
        {
            "name": "cloudflare",
            "description": "Cloudflare DNS and security management"
        },
        {
            "name": "network",
            "description": "Network firewall and security rules"
        },
        {
            "name": "migration",
            "description": "Data migration and import/export operations"
        },
        {
            "name": "credentials",
            "description": "API credential management"
        },
        {
            "name": "Local Users",
            "description": "Linux system user management"
        },
        {
            "name": "Platform Settings",
            "description": "Platform-wide configuration"
        },
        {
            "name": "System Settings",
            "description": "System configuration and preferences"
        }
    ],
    "servers": [
        {
            "url": "https://unicorncommander.ai",
            "description": "Production server"
        },
        {
            "url": "http://localhost:8084",
            "description": "Development server"
        }
    ]
}

# Security Schemes
security_schemes = {
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": """
JWT token obtained from Keycloak SSO authentication.

**To obtain a token:**

1. Navigate to https://auth.unicorncommander.ai
2. Login with credentials or OAuth provider (Google, GitHub, Microsoft)
3. Retrieve `access_token` from response
4. Include in Authorization header: `Bearer <token>`

**Token Expiration:**
- Access Token: 15 minutes
- Refresh Token: 30 days
- Session Token: 24 hours (for impersonation)
"""
    }
}

# Common response examples
response_examples = {
    "error_400": {
        "description": "Bad Request - Invalid input",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Validation error: Invalid email format",
                    "status_code": 400,
                    "error_code": "VALIDATION_ERROR"
                }
            }
        }
    },
    "error_401": {
        "description": "Unauthorized - Authentication required",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Authentication required. Please log in.",
                    "status_code": 401,
                    "error_code": "UNAUTHORIZED"
                }
            }
        }
    },
    "error_403": {
        "description": "Forbidden - Insufficient permissions",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Admin role required. Contact your system administrator.",
                    "status_code": 403,
                    "error_code": "FORBIDDEN"
                }
            }
        }
    },
    "error_404": {
        "description": "Not Found - Resource does not exist",
        "content": {
            "application/json": {
                "example": {
                    "detail": "User not found",
                    "status_code": 404,
                    "error_code": "NOT_FOUND"
                }
            }
        }
    },
    "error_429": {
        "description": "Rate Limit Exceeded",
        "content": {
            "application/json": {
                "example": {
                    "detail": "API call limit exceeded. Upgrade to Professional plan.",
                    "status_code": 429,
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": 3600,
                    "current_usage": 1000,
                    "limit": 1000,
                    "reset_at": "2025-11-01T00:00:00Z"
                }
            }
        }
    },
    "error_500": {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "example": {
                    "detail": "An internal server error occurred",
                    "status_code": 500,
                    "error_code": "INTERNAL_ERROR"
                }
            }
        }
    }
}

# Common request/response schemas
common_schemas = {
    "Error": {
        "type": "object",
        "required": ["detail", "status_code"],
        "properties": {
            "detail": {
                "type": "string",
                "description": "Human-readable error message"
            },
            "status_code": {
                "type": "integer",
                "description": "HTTP status code"
            },
            "error_code": {
                "type": "string",
                "description": "Machine-readable error code"
            },
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "description": "Error timestamp"
            }
        }
    },
    "PaginatedResponse": {
        "type": "object",
        "required": ["items", "total", "page", "page_size"],
        "properties": {
            "items": {
                "type": "array",
                "items": {},
                "description": "Page of results"
            },
            "total": {
                "type": "integer",
                "description": "Total items across all pages"
            },
            "page": {
                "type": "integer",
                "description": "Current page number (1-indexed)"
            },
            "page_size": {
                "type": "integer",
                "description": "Items per page"
            },
            "total_pages": {
                "type": "integer",
                "description": "Total number of pages"
            }
        }
    },
    "User": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "format": "uuid",
                "description": "User ID (Keycloak UUID)"
            },
            "email": {
                "type": "string",
                "format": "email",
                "description": "User email address"
            },
            "username": {
                "type": "string",
                "description": "Username"
            },
            "roles": {
                "type": "array",
                "items": {"type": "string"},
                "description": "User roles (admin, moderator, developer, analyst, viewer)"
            },
            "subscription_tier": {
                "type": "string",
                "enum": ["trial", "starter", "professional", "enterprise"],
                "description": "Current subscription tier"
            },
            "subscription_status": {
                "type": "string",
                "enum": ["active", "suspended", "cancelled"],
                "description": "Subscription status"
            }
        }
    }
}


def get_custom_openapi_schema(app):
    """
    Generate custom OpenAPI schema with enhanced metadata

    Args:
        app: FastAPI application instance

    Returns:
        dict: Enhanced OpenAPI schema
    """
    from fastapi.openapi.utils import get_openapi

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=openapi_metadata["title"],
        version=openapi_metadata["version"],
        description=openapi_metadata["description"],
        routes=app.routes,
        tags=openapi_metadata["openapi_tags"],
        servers=openapi_metadata["servers"],
        terms_of_service=openapi_metadata.get("terms_of_service"),
        contact=openapi_metadata.get("contact"),
        license_info=openapi_metadata.get("license_info"),
    )

    # Add security schemes
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["securitySchemes"] = security_schemes

    # Add common schemas
    openapi_schema["components"]["schemas"] = {
        **openapi_schema["components"].get("schemas", {}),
        **common_schemas
    }

    # Add global security requirement
    openapi_schema["security"] = [{"BearerAuth": []}]

    # Add rate limit headers to all responses
    for path_item in openapi_schema["paths"].values():
        for operation in path_item.values():
            if isinstance(operation, dict) and "responses" in operation:
                for response in operation["responses"].values():
                    if isinstance(response, dict):
                        response["headers"] = response.get("headers", {})
                        response["headers"].update({
                            "X-RateLimit-Limit": {
                                "schema": {"type": "integer"},
                                "description": "Total requests allowed per period"
                            },
                            "X-RateLimit-Remaining": {
                                "schema": {"type": "integer"},
                                "description": "Requests remaining in current period"
                            },
                            "X-RateLimit-Reset": {
                                "schema": {"type": "integer"},
                                "description": "Unix timestamp when limit resets"
                            }
                        })

    app.openapi_schema = openapi_schema
    return app.openapi_schema
