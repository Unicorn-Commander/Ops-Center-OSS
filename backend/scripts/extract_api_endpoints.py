#!/usr/bin/env python3
"""
API Endpoint Scanner for OpenAPI Documentation Generation
Extracts all FastAPI routes from backend API files to generate comprehensive OpenAPI spec.
"""

import ast
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class Parameter:
    """API endpoint parameter"""
    name: str
    param_type: str  # path, query, header, body
    data_type: str
    required: bool = True
    description: str = ""
    default: Optional[Any] = None


@dataclass
class ResponseSchema:
    """API response schema"""
    status_code: int
    description: str
    schema_type: Optional[str] = None
    example: Optional[Dict] = None


@dataclass
class Endpoint:
    """API endpoint metadata"""
    method: str  # GET, POST, PUT, DELETE, PATCH
    path: str
    function_name: str
    summary: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    parameters: List[Parameter] = field(default_factory=list)
    request_body: Optional[Dict] = None
    responses: List[ResponseSchema] = field(default_factory=list)
    security: List[str] = field(default_factory=list)
    deprecated: bool = False


class EndpointScanner:
    """Scans FastAPI Python files to extract endpoint metadata"""

    def __init__(self, backend_dir: str):
        self.backend_dir = Path(backend_dir)
        self.endpoints: List[Endpoint] = []
        self.pydantic_models: Dict[str, Dict] = {}

    def scan_all_api_files(self) -> List[Endpoint]:
        """Scan all API files in backend directory"""
        api_files = list(self.backend_dir.glob("*_api.py"))
        api_files.append(self.backend_dir / "server.py")

        for api_file in api_files:
            if api_file.exists():
                print(f"Scanning: {api_file.name}")
                self.scan_file(api_file)

        return self.endpoints

    def scan_file(self, file_path: Path):
        """Scan a single Python file for FastAPI routes"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content)

            # Extract router prefix and tags from APIRouter initialization
            router_prefix = ""
            router_tags = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == 'router':
                            if isinstance(node.value, ast.Call):
                                for keyword in node.value.keywords:
                                    if keyword.arg == 'prefix':
                                        if isinstance(keyword.value, ast.Constant):
                                            router_prefix = keyword.value.value
                                    elif keyword.arg == 'tags':
                                        if isinstance(keyword.value, ast.List):
                                            router_tags = [
                                                elt.value for elt in keyword.value.elts
                                                if isinstance(elt, ast.Constant)
                                            ]

            # Extract endpoints from decorated functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    endpoint = self.extract_endpoint_from_function(node, router_prefix, router_tags)
                    if endpoint:
                        self.endpoints.append(endpoint)

        except Exception as e:
            print(f"Error scanning {file_path}: {e}")

    def extract_endpoint_from_function(
        self,
        func_node: ast.FunctionDef,
        router_prefix: str,
        router_tags: List[str]
    ) -> Optional[Endpoint]:
        """Extract endpoint metadata from a decorated function"""

        # Look for route decorator
        route_decorator = None
        http_method = None
        route_path = ""

        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    method_name = decorator.func.attr
                    if method_name in ['get', 'post', 'put', 'delete', 'patch']:
                        http_method = method_name.upper()
                        # Get path from first argument
                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            route_path = decorator.args[0].value
                        route_decorator = decorator
                        break

        if not http_method or not route_path:
            return None

        # Build full path
        full_path = router_prefix + route_path if router_prefix else route_path

        # Extract docstring
        docstring = ast.get_docstring(func_node) or ""
        summary = docstring.split('\n')[0] if docstring else func_node.name.replace('_', ' ').title()

        # Extract parameters from function signature
        parameters = self.extract_parameters(func_node)

        # Determine security (check for Depends)
        security = []
        for arg in func_node.args.args:
            if arg.annotation and isinstance(arg.annotation, ast.Call):
                if isinstance(arg.annotation.func, ast.Name):
                    if arg.annotation.func.id in ['Depends', 'require_admin', 'get_current_user']:
                        security.append("BearerAuth")

        return Endpoint(
            method=http_method,
            path=full_path,
            function_name=func_node.name,
            summary=summary,
            description=docstring,
            tags=router_tags if router_tags else ["default"],
            parameters=parameters,
            security=security,
        )

    def extract_parameters(self, func_node: ast.FunctionDef) -> List[Parameter]:
        """Extract parameters from function signature"""
        parameters = []

        for arg in func_node.args.args:
            # Skip 'request', 'self', and dependency injection params
            if arg.arg in ['request', 'self']:
                continue

            param_type = "query"  # default
            data_type = "string"  # default
            required = True

            # Determine if it's a path parameter
            # Path params are typically in the function name or have specific annotations
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    data_type = arg.annotation.id.lower()

            # Check if parameter has default value
            defaults_offset = len(func_node.args.args) - len(func_node.args.defaults)
            arg_index = func_node.args.args.index(arg)
            if arg_index >= defaults_offset:
                required = False

            # Path parameters (detected by name pattern or position)
            if '_id' in arg.arg or arg.arg.endswith('id'):
                param_type = "path"

            parameters.append(Parameter(
                name=arg.arg,
                param_type=param_type,
                data_type=data_type,
                required=required,
                description=f"{arg.arg.replace('_', ' ').title()}"
            ))

        return parameters


class OpenAPIGenerator:
    """Generates OpenAPI 3.0 specification from extracted endpoints"""

    def __init__(self, endpoints: List[Endpoint]):
        self.endpoints = endpoints

    def generate_openapi_yaml(self, output_file: str):
        """Generate OpenAPI 3.0 YAML specification"""

        # Group endpoints by tag
        endpoints_by_tag = {}
        for endpoint in self.endpoints:
            tag = endpoint.tags[0] if endpoint.tags else "default"
            if tag not in endpoints_by_tag:
                endpoints_by_tag[tag] = []
            endpoints_by_tag[tag].append(endpoint)

        yaml_content = self.build_openapi_yaml(endpoints_by_tag)

        with open(output_file, 'w') as f:
            f.write(yaml_content)

        print(f"\n✅ OpenAPI YAML generated: {output_file}")

    def generate_openapi_json(self, output_file: str):
        """Generate OpenAPI 3.0 JSON specification"""

        spec = self.build_openapi_dict()

        with open(output_file, 'w') as f:
            json.dump(spec, f, indent=2)

        print(f"✅ OpenAPI JSON generated: {output_file}")

    def build_openapi_dict(self) -> Dict:
        """Build OpenAPI specification dictionary"""

        paths = {}

        for endpoint in self.endpoints:
            if endpoint.path not in paths:
                paths[endpoint.path] = {}

            operation = {
                "summary": endpoint.summary,
                "description": endpoint.description,
                "tags": endpoint.tags,
                "operationId": endpoint.function_name,
            }

            # Add parameters
            if endpoint.parameters:
                operation["parameters"] = [
                    {
                        "name": param.name,
                        "in": param.param_type,
                        "required": param.required,
                        "schema": {"type": param.data_type},
                        "description": param.description
                    }
                    for param in endpoint.parameters
                ]

            # Add security
            if endpoint.security:
                operation["security"] = [{"BearerAuth": []}]

            # Add responses
            operation["responses"] = {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                },
                "401": {
                    "description": "Unauthorized - Authentication required"
                },
                "403": {
                    "description": "Forbidden - Insufficient permissions"
                },
                "404": {
                    "description": "Not found"
                },
                "500": {
                    "description": "Internal server error"
                }
            }

            paths[endpoint.path][endpoint.method.lower()] = operation

        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "UC-Cloud Ops-Center API",
                "version": "2.1.0",
                "description": "Comprehensive API documentation for UC-Cloud Operations Center",
                "contact": {
                    "name": "UC-Cloud Support",
                    "url": "https://your-domain.com",
                    "email": "support@example.com"
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT"
                }
            },
            "servers": [
                {
                    "url": "https://your-domain.com",
                    "description": "Production server"
                },
                {
                    "url": "http://localhost:8084",
                    "description": "Development server"
                }
            ],
            "paths": paths,
            "components": {
                "securitySchemes": {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                        "description": "JWT token from Keycloak SSO authentication"
                    }
                }
            }
        }

        return spec

    def build_openapi_yaml(self, endpoints_by_tag: Dict[str, List[Endpoint]]) -> str:
        """Build OpenAPI YAML content"""

        yaml = """openapi: 3.0.0
info:
  title: UC-Cloud Ops-Center API
  version: 2.1.0
  description: |
    Comprehensive API documentation for UC-Cloud Operations Center.

    The Ops-Center API provides centralized management for:
    - User Management (Keycloak SSO)
    - Organization Management
    - Billing & Subscriptions (Lago + Stripe)
    - LLM Infrastructure (LiteLLM Proxy)
    - Service Management
    - Analytics & Monitoring

  contact:
    name: UC-Cloud Support
    url: https://your-domain.com
    email: support@example.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://your-domain.com
    description: Production server
  - url: http://localhost:8084
    description: Development server

tags:
"""

        # Add tags
        all_tags = set()
        for tag in endpoints_by_tag.keys():
            all_tags.add(tag)

        for tag in sorted(all_tags):
            yaml += f"  - name: {tag}\n"
            yaml += f"    description: {tag.replace('_', ' ').title()} operations\n"

        yaml += "\npaths:\n"

        # Add paths
        paths_dict = {}
        for endpoint in self.endpoints:
            if endpoint.path not in paths_dict:
                paths_dict[endpoint.path] = []
            paths_dict[endpoint.path].append(endpoint)

        for path in sorted(paths_dict.keys()):
            yaml += f"  {path}:\n"

            for endpoint in paths_dict[path]:
                method = endpoint.method.lower()
                yaml += f"    {method}:\n"
                yaml += f"      summary: {endpoint.summary}\n"
                yaml += f"      operationId: {endpoint.function_name}\n"

                if endpoint.tags:
                    yaml += f"      tags:\n"
                    for tag in endpoint.tags:
                        yaml += f"        - {tag}\n"

                if endpoint.description:
                    desc = endpoint.description.replace('\n', '\n        ')
                    yaml += f"      description: |\n        {desc}\n"

                if endpoint.parameters:
                    yaml += f"      parameters:\n"
                    for param in endpoint.parameters:
                        yaml += f"        - name: {param.name}\n"
                        yaml += f"          in: {param.param_type}\n"
                        yaml += f"          required: {str(param.required).lower()}\n"
                        yaml += f"          schema:\n"
                        yaml += f"            type: {param.data_type}\n"
                        if param.description:
                            yaml += f"          description: {param.description}\n"

                if endpoint.security:
                    yaml += f"      security:\n"
                    yaml += f"        - BearerAuth: []\n"

                yaml += f"      responses:\n"
                yaml += f"        '200':\n"
                yaml += f"          description: Successful response\n"
                yaml += f"          content:\n"
                yaml += f"            application/json:\n"
                yaml += f"              schema:\n"
                yaml += f"                type: object\n"
                yaml += f"        '401':\n"
                yaml += f"          description: Unauthorized - Authentication required\n"
                yaml += f"        '403':\n"
                yaml += f"          description: Forbidden - Insufficient permissions\n"
                yaml += f"        '404':\n"
                yaml += f"          description: Resource not found\n"
                yaml += f"        '500':\n"
                yaml += f"          description: Internal server error\n"

        yaml += """
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT token from Keycloak SSO authentication
"""

        return yaml


def main():
    """Main execution"""
    print("🔍 UC-Cloud Ops-Center API Endpoint Scanner\n")
    print("=" * 60)

    backend_dir = Path(__file__).parent.parent
    print(f"Backend directory: {backend_dir}\n")

    # Scan endpoints
    scanner = EndpointScanner(str(backend_dir))
    endpoints = scanner.scan_all_api_files()

    print(f"\n✅ Found {len(endpoints)} API endpoints")

    # Group by tag
    by_tag = {}
    for ep in endpoints:
        tag = ep.tags[0] if ep.tags else "default"
        by_tag[tag] = by_tag.get(tag, 0) + 1

    print(f"\n📊 Endpoints by category:")
    for tag, count in sorted(by_tag.items()):
        print(f"  - {tag}: {count} endpoints")

    # Generate OpenAPI specs
    print(f"\n📝 Generating OpenAPI specifications...")

    generator = OpenAPIGenerator(endpoints)

    docs_dir = backend_dir.parent / "docs"
    docs_dir.mkdir(exist_ok=True)

    yaml_file = docs_dir / "openapi.yaml"
    json_file = docs_dir / "openapi.json"

    generator.generate_openapi_yaml(str(yaml_file))
    generator.generate_openapi_json(str(json_file))

    print(f"\n✅ OpenAPI documentation generated successfully!")
    print(f"\nFiles created:")
    print(f"  - {yaml_file}")
    print(f"  - {json_file}")

    # Generate endpoint summary
    summary_file = docs_dir / "API_ENDPOINTS_SUMMARY.md"
    with open(summary_file, 'w') as f:
        f.write("# API Endpoints Summary\n\n")
        f.write(f"**Total Endpoints**: {len(endpoints)}\n\n")

        for tag in sorted(by_tag.keys()):
            tag_endpoints = [ep for ep in endpoints if tag in ep.tags]
            f.write(f"## {tag.replace('_', ' ').title()} ({len(tag_endpoints)} endpoints)\n\n")

            for ep in sorted(tag_endpoints, key=lambda x: x.path):
                f.write(f"- **{ep.method}** `{ep.path}` - {ep.summary}\n")

            f.write("\n")

    print(f"  - {summary_file}")
    print(f"\n🎉 Done!")


if __name__ == "__main__":
    main()
