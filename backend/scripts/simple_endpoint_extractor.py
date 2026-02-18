#!/usr/bin/env python3
"""
Simple API Endpoint Extractor using regex patterns
Extracts all FastAPI routes from backend API files.
"""

import re
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple


class SimpleEndpointExtractor:
    """Extract FastAPI endpoints using regex patterns"""

    def __init__(self, backend_dir: str):
        self.backend_dir = Path(backend_dir)
        self.endpoints = []

    def extract_from_file(self, file_path: Path) -> List[Dict]:
        """Extract endpoints from a single file"""
        endpoints = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract router prefix and tags
            router_prefix = ""
            router_tags = []

            # Pattern: router = APIRouter(prefix="/api/v1/...", tags=["..."])
            router_pattern = r'router\s*=\s*APIRouter\s*\((.*?)\)'
            router_match = re.search(router_pattern, content, re.DOTALL)

            if router_match:
                router_args = router_match.group(1)

                # Extract prefix
                prefix_match = re.search(r'prefix\s*=\s*["\']([^"\']+)["\']', router_args)
                if prefix_match:
                    router_prefix = prefix_match.group(1)

                # Extract tags
                tags_match = re.search(r'tags\s*=\s*\[(.*?)\]', router_args)
                if tags_match:
                    tags_str = tags_match.group(1)
                    router_tags = re.findall(r'["\']([^"\']+)["\']', tags_str)

            # Extract route decorators and functions
            # Pattern: @router.METHOD("path") followed by async def or def
            route_pattern = r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']\s*.*?\)\s*(?:async\s+)?def\s+(\w+)'

            for match in re.finditer(route_pattern, content, re.MULTILINE):
                method = match.group(1).upper()
                path = match.group(2)
                function_name = match.group(3)

                # Build full path
                full_path = router_prefix + path if router_prefix else path

                # Try to extract docstring
                func_start = match.end()
                # Look for docstring after function definition
                docstring_pattern = r'^\s*"""(.*?)"""'
                remaining_content = content[func_start:]
                docstring_match = re.search(docstring_pattern, remaining_content, re.DOTALL | re.MULTILINE)

                summary = ""
                description = ""

                if docstring_match:
                    docstring = docstring_match.group(1).strip()
                    lines = docstring.split('\n')
                    summary = lines[0].strip() if lines else ""
                    description = docstring
                else:
                    # Generate summary from function name
                    summary = function_name.replace('_', ' ').title()

                endpoints.append({
                    "method": method,
                    "path": full_path,
                    "function": function_name,
                    "summary": summary,
                    "description": description,
                    "tags": router_tags if router_tags else [file_path.stem.replace('_api', '')],
                    "file": file_path.name
                })

        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

        return endpoints

    def scan_all_files(self) -> List[Dict]:
        """Scan all API files"""
        api_files = list(self.backend_dir.glob("*_api.py"))
        api_files.append(self.backend_dir / "server.py")

        for api_file in api_files:
            if api_file.exists():
                file_endpoints = self.extract_from_file(api_file)
                if file_endpoints:
                    print(f"✓ {api_file.name}: {len(file_endpoints)} endpoints")
                    self.endpoints.extend(file_endpoints)

        return self.endpoints


def generate_openapi_yaml(endpoints: List[Dict], output_file: str):
    """Generate OpenAPI 3.0 YAML"""

    # Group by tag
    by_tag = defaultdict(list)
    for ep in endpoints:
        tag = ep['tags'][0] if ep['tags'] else 'default'
        by_tag[tag].append(ep)

    yaml_content = """openapi: 3.0.0
info:
  title: UC-Cloud Ops-Center API
  version: 2.1.0
  description: |
    Comprehensive API documentation for UC-Cloud Operations Center.

    ## Features
    - **User Management**: Keycloak SSO integration for user authentication and authorization
    - **Organization Management**: Multi-tenant organization and team management
    - **Billing & Subscriptions**: Lago billing integration with Stripe payments
    - **LLM Infrastructure**: LiteLLM proxy for multi-provider LLM access
    - **Service Management**: Docker service orchestration and monitoring
    - **Analytics & Monitoring**: Real-time metrics, usage tracking, and reporting
    - **Traefik Management**: Dynamic routing, SSL/TLS, and load balancing
    - **Storage & Backup**: Restic-based backup management

    ## Authentication
    All endpoints require JWT Bearer token authentication via Keycloak SSO.

    ## Rate Limiting
    API endpoints are rate-limited based on subscription tier:
    - Trial: 100 requests/day
    - Starter: 1,000 requests/month
    - Professional: 10,000 requests/month
    - Enterprise: Unlimited

  contact:
    name: UC-Cloud Support
    url: https://unicorncommander.com
    email: support@magicunicorn.tech
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://unicorncommander.ai
    description: Production server
  - url: http://localhost:8084
    description: Development server

security:
  - BearerAuth: []

tags:
"""

    # Add tags
    for tag in sorted(by_tag.keys()):
        tag_display = tag.replace('_', ' ').title()
        yaml_content += f"  - name: {tag}\n"
        yaml_content += f"    description: {tag_display} operations\n"

    yaml_content += "\npaths:\n"

    # Group by path
    by_path = defaultdict(list)
    for ep in endpoints:
        by_path[ep['path']].append(ep)

    for path in sorted(by_path.keys()):
        yaml_content += f"  {path}:\n"

        for ep in by_path[path]:
            method = ep['method'].lower()
            yaml_content += f"    {method}:\n"
            yaml_content += f"      summary: {ep['summary']}\n"
            yaml_content += f"      operationId: {ep['function']}\n"

            if ep['tags']:
                yaml_content += f"      tags:\n"
                for tag in ep['tags']:
                    yaml_content += f"        - {tag}\n"

            if ep['description']:
                desc_lines = ep['description'].split('\n')
                yaml_content += f"      description: |\n"
                for line in desc_lines:
                    yaml_content += f"        {line}\n"

            # Extract path parameters
            path_params = re.findall(r'\{(\w+)\}', path)
            if path_params:
                yaml_content += f"      parameters:\n"
                for param in path_params:
                    yaml_content += f"        - name: {param}\n"
                    yaml_content += f"          in: path\n"
                    yaml_content += f"          required: true\n"
                    yaml_content += f"          schema:\n"
                    yaml_content += f"            type: string\n"
                    yaml_content += f"          description: {param.replace('_', ' ').title()}\n"

            yaml_content += f"      responses:\n"
            yaml_content += f"        '200':\n"
            yaml_content += f"          description: Successful response\n"
            yaml_content += f"          content:\n"
            yaml_content += f"            application/json:\n"
            yaml_content += f"              schema:\n"
            yaml_content += f"                type: object\n"
            yaml_content += f"        '400':\n"
            yaml_content += f"          description: Bad request - Invalid input\n"
            yaml_content += f"        '401':\n"
            yaml_content += f"          description: Unauthorized - Authentication required\n"
            yaml_content += f"        '403':\n"
            yaml_content += f"          description: Forbidden - Insufficient permissions\n"
            yaml_content += f"        '404':\n"
            yaml_content += f"          description: Resource not found\n"
            yaml_content += f"        '500':\n"
            yaml_content += f"          description: Internal server error\n"

    yaml_content += """
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |
        JWT token obtained from Keycloak SSO authentication.

        To obtain a token:
        1. Navigate to https://auth.unicorncommander.ai
        2. Login with credentials or OAuth provider (Google, GitHub, Microsoft)
        3. Retrieve access_token from response
        4. Include in Authorization header: `Bearer <token>`

  schemas:
    Error:
      type: object
      required:
        - detail
      properties:
        detail:
          type: string
          description: Error message
        status_code:
          type: integer
          description: HTTP status code

    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
          description: User ID (Keycloak UUID)
        email:
          type: string
          format: email
          description: User email address
        username:
          type: string
          description: Username
        roles:
          type: array
          items:
            type: string
          description: User roles (admin, moderator, developer, analyst, viewer)
        subscription_tier:
          type: string
          enum: [trial, starter, professional, enterprise]
          description: Current subscription tier
        subscription_status:
          type: string
          enum: [active, suspended, cancelled]
          description: Subscription status
        created_at:
          type: string
          format: date-time
          description: Account creation timestamp

    Organization:
      type: object
      properties:
        id:
          type: string
          format: uuid
          description: Organization ID
        name:
          type: string
          description: Organization name
        owner_id:
          type: string
          format: uuid
          description: Owner user ID
        member_count:
          type: integer
          description: Number of members
        subscription_tier:
          type: string
          enum: [trial, starter, professional, enterprise]
          description: Organization subscription tier
        created_at:
          type: string
          format: date-time
          description: Creation timestamp

    Subscription:
      type: object
      properties:
        id:
          type: string
          description: Subscription ID (Lago)
        plan_code:
          type: string
          enum: [trial, starter, professional, enterprise]
          description: Plan code
        status:
          type: string
          enum: [active, pending, suspended, cancelled]
          description: Subscription status
        current_period_start:
          type: string
          format: date-time
          description: Current billing period start
        current_period_end:
          type: string
          format: date-time
          description: Current billing period end
        api_calls_limit:
          type: integer
          description: API call limit per period
        api_calls_used:
          type: integer
          description: API calls used in current period
"""

    with open(output_file, 'w') as f:
        f.write(yaml_content)

    print(f"\n✅ OpenAPI YAML: {output_file}")


def generate_markdown_summary(endpoints: List[Dict], output_file: str):
    """Generate markdown summary of all endpoints"""

    # Group by tag
    by_tag = defaultdict(list)
    for ep in endpoints:
        tag = ep['tags'][0] if ep['tags'] else 'default'
        by_tag[tag].append(ep)

    md_content = f"""# UC-Cloud Ops-Center API Endpoints

**Total Endpoints**: {len(endpoints)}

**Generated**: {Path(__file__).stat().st_mtime}

## Endpoints by Category

"""

    for tag in sorted(by_tag.keys()):
        tag_endpoints = by_tag[tag]
        tag_display = tag.replace('_', ' ').title()

        md_content += f"### {tag_display} ({len(tag_endpoints)} endpoints)\n\n"

        for ep in sorted(tag_endpoints, key=lambda x: (x['path'], x['method'])):
            md_content += f"- **{ep['method']}** `{ep['path']}`\n"
            md_content += f"  - **Function**: `{ep['function']}`\n"
            md_content += f"  - **Summary**: {ep['summary']}\n"

            # Extract path parameters
            path_params = re.findall(r'\{(\w+)\}', ep['path'])
            if path_params:
                md_content += f"  - **Path Parameters**: {', '.join(path_params)}\n"

            md_content += "\n"

        md_content += "\n"

    # Statistics
    md_content += "## Statistics\n\n"

    method_count = defaultdict(int)
    for ep in endpoints:
        method_count[ep['method']] += 1

    md_content += "### Endpoints by HTTP Method\n\n"
    for method, count in sorted(method_count.items()):
        md_content += f"- **{method}**: {count}\n"

    with open(output_file, 'w') as f:
        f.write(md_content)

    print(f"✅ Markdown Summary: {output_file}")


def main():
    """Main execution"""
    print("🔍 UC-Cloud Ops-Center API Endpoint Extractor\n")
    print("=" * 60)

    backend_dir = Path(__file__).parent.parent
    print(f"Scanning: {backend_dir}\n")

    extractor = SimpleEndpointExtractor(str(backend_dir))
    endpoints = extractor.scan_all_files()

    print(f"\n✅ Total endpoints extracted: {len(endpoints)}")

    # Statistics
    by_tag = defaultdict(int)
    by_method = defaultdict(int)

    for ep in endpoints:
        tag = ep['tags'][0] if ep['tags'] else 'default'
        by_tag[tag] += 1
        by_method[ep['method']] += 1

    print(f"\n📊 By Category:")
    for tag, count in sorted(by_tag.items()):
        print(f"  - {tag}: {count}")

    print(f"\n📊 By HTTP Method:")
    for method, count in sorted(by_method.items()):
        print(f"  - {method}: {count}")

    # Generate output files
    print(f"\n📝 Generating documentation...")

    docs_dir = backend_dir.parent / "docs"
    docs_dir.mkdir(exist_ok=True)

    # OpenAPI YAML
    yaml_file = docs_dir / "openapi.yaml"
    generate_openapi_yaml(endpoints, str(yaml_file))

    # OpenAPI JSON
    json_file = docs_dir / "openapi.json"
    with open(json_file, 'w') as f:
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "UC-Cloud Ops-Center API",
                "version": "2.1.0",
                "description": "Comprehensive API documentation"
            },
            "paths": {}
        }
        json.dump(spec, f, indent=2)
    print(f"✅ OpenAPI JSON: {json_file}")

    # Markdown summary
    md_file = docs_dir / "API_ENDPOINTS_SUMMARY.md"
    generate_markdown_summary(endpoints, str(md_file))

    # Save raw endpoint data
    data_file = docs_dir / "endpoints_data.json"
    with open(data_file, 'w') as f:
        json.dump(endpoints, f, indent=2)
    print(f"✅ Endpoint Data: {data_file}")

    print(f"\n🎉 Documentation generation complete!")
    print(f"\nNext steps:")
    print(f"  1. Review {yaml_file}")
    print(f"  2. Add detailed schemas in components section")
    print(f"  3. Add request/response examples")
    print(f"  4. Test with Swagger UI or Redoc")


if __name__ == "__main__":
    main()
