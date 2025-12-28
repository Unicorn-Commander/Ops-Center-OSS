"""
API Documentation Endpoints
Provides OpenAPI spec and documentation UI endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/docs", tags=["documentation"])


@router.get("/openapi.json", response_class=JSONResponse)
async def get_openapi_spec():
    """
    Get the complete OpenAPI specification for the Ops-Center API

    Returns:
        JSON OpenAPI 3.0 specification
    """
    try:
        from server import app  # Import the main FastAPI app

        # Get the OpenAPI schema from FastAPI
        openapi_schema = app.openapi()

        # Enhance the schema with additional metadata
        openapi_schema["info"]["description"] = """
        # UC-Cloud Ops-Center API

        The Ops-Center API provides comprehensive management and monitoring capabilities for the UC-Cloud ecosystem.

        ## Features

        - **User Management**: Create, read, update, and delete users with role-based access control
        - **Organization Management**: Multi-tenant organization support with team management
        - **Billing & Subscriptions**: Integration with Lago billing system and Stripe payments
        - **LLM Management**: Manage LiteLLM proxy, models, and providers
        - **Service Management**: Monitor and control UC-Cloud services
        - **Analytics**: Usage metrics, billing analytics, and system monitoring
        - **Security**: Authentication via Keycloak SSO, API key management

        ## Authentication

        All API endpoints require authentication via:

        1. **OAuth 2.0 Bearer Token** (preferred for web applications)
           - Obtain from Keycloak SSO: `https://auth.your-domain.com`
           - Add to requests: `Authorization: Bearer <token>`

        2. **API Key** (for programmatic access)
           - Generate via `/admin/account/api-keys` page
           - Add to requests: `X-API-Key: <key>`

        ## Rate Limiting

        API calls are limited based on subscription tier:
        - **Trial**: 100 calls/day (700/week)
        - **Starter**: 1,000 calls/month
        - **Professional**: 10,000 calls/month
        - **Enterprise**: Unlimited

        ## Base URL

        - **Production**: `https://your-domain.com`
        - **Development**: `http://localhost:8084`
        """

        openapi_schema["info"]["contact"] = {
            "name": "UC-Cloud Support",
            "url": "https://your-domain.com",
            "email": "support@example.com"
        }

        openapi_schema["info"]["license"] = {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }

        # Add security schemes
        openapi_schema["components"] = openapi_schema.get("components", {})
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "OAuth 2.0 JWT token from Keycloak SSO"
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key for programmatic access"
            }
        }

        # Add global security requirement
        openapi_schema["security"] = [
            {"BearerAuth": []},
            {"ApiKeyAuth": []}
        ]

        # Add servers
        openapi_schema["servers"] = [
            {
                "url": "https://your-domain.com",
                "description": "Production server"
            },
            {
                "url": "http://localhost:8084",
                "description": "Development server"
            }
        ]

        # Add tags with descriptions
        openapi_schema["tags"] = [
            {
                "name": "authentication",
                "description": "Authentication and authorization endpoints"
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
                "name": "billing",
                "description": "Subscription and billing management"
            },
            {
                "name": "llm",
                "description": "LLM proxy and model management"
            },
            {
                "name": "services",
                "description": "Service status and management"
            },
            {
                "name": "system",
                "description": "System monitoring and configuration"
            },
            {
                "name": "analytics",
                "description": "Usage analytics and metrics"
            },
            {
                "name": "documentation",
                "description": "API documentation endpoints"
            }
        ]

        return JSONResponse(content=openapi_schema)

    except Exception as e:
        logger.error(f"Failed to generate OpenAPI spec: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate API documentation")


@router.get("/swagger", response_class=HTMLResponse)
async def get_swagger_ui():
    """
    Get Swagger UI HTML page for interactive API documentation
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ops-Center API Documentation - Swagger UI</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.17.14/swagger-ui.css" />
        <style>
            body {
                margin: 0;
                padding: 0;
            }
            .swagger-ui .topbar {
                background-color: #7c3aed;
            }
            .swagger-ui .topbar .download-url-wrapper input[type=text] {
                border-color: #7c3aed;
            }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.17.14/swagger-ui-bundle.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.17.14/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {
                const ui = SwaggerUIBundle({
                    url: "/api/v1/docs/openapi.json",
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout",
                    requestInterceptor: (request) => {
                        // Add auth token from localStorage if available
                        const token = localStorage.getItem('authToken');
                        if (token) {
                            request.headers['Authorization'] = 'Bearer ' + token;
                        }
                        return request;
                    }
                });
                window.ui = ui;
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/redoc", response_class=HTMLResponse)
async def get_redoc_ui():
    """
    Get ReDoc HTML page for alternative API documentation view
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ops-Center API Documentation - ReDoc</title>
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body {
                margin: 0;
                padding: 0;
            }
        </style>
    </head>
    <body>
        <redoc spec-url="/api/v1/docs/openapi.json"></redoc>
        <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/endpoints", response_class=JSONResponse)
async def get_endpoints_list():
    """
    Get a simplified list of all API endpoints grouped by tags

    Returns:
        Grouped list of endpoints with methods, paths, and descriptions
    """
    try:
        from server import app

        openapi_schema = app.openapi()
        endpoints_by_tag = {}

        for path, path_item in openapi_schema.get("paths", {}).items():
            for method, operation in path_item.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    tags = operation.get("tags", ["untagged"])
                    tag = tags[0] if tags else "untagged"

                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []

                    endpoints_by_tag[tag].append({
                        "method": method.upper(),
                        "path": path,
                        "summary": operation.get("summary", ""),
                        "description": operation.get("description", ""),
                        "operationId": operation.get("operationId", ""),
                        "deprecated": operation.get("deprecated", False)
                    })

        return JSONResponse(content=endpoints_by_tag)

    except Exception as e:
        logger.error(f"Failed to get endpoints list: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get endpoints list")


@router.get("/search")
async def search_endpoints(query: str):
    """
    Search API endpoints by keyword

    Args:
        query: Search keyword

    Returns:
        List of matching endpoints
    """
    try:
        from server import app

        openapi_schema = app.openapi()
        results = []
        query_lower = query.lower()

        for path, path_item in openapi_schema.get("paths", {}).items():
            for method, operation in path_item.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    # Search in path, summary, description, tags
                    searchable_text = " ".join([
                        path,
                        operation.get("summary", ""),
                        operation.get("description", ""),
                        " ".join(operation.get("tags", []))
                    ]).lower()

                    if query_lower in searchable_text:
                        results.append({
                            "method": method.upper(),
                            "path": path,
                            "summary": operation.get("summary", ""),
                            "tags": operation.get("tags", [])
                        })

        return JSONResponse(content={"query": query, "results": results, "count": len(results)})

    except Exception as e:
        logger.error(f"Failed to search endpoints: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search endpoints")
