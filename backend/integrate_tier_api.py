#!/usr/bin/env python3
"""
Integration Script: Add Tier Check API to server.py

This script safely integrates the tier checking API routes into the existing server.py
"""

import os
import sys

def integrate_tier_api():
    """Add tier check API router to server.py"""
    
    server_path = "/home/muut/Production/UC-1-Pro/services/ops-center/backend/server.py"
    
    # Read the existing server.py
    with open(server_path, 'r') as f:
        content = f.read()
    
    # Check if already integrated
    if "tier_check_api" in content:
        print("✓ Tier Check API already integrated!")
        return True
    
    # Find the imports section (after the auth imports)
    import_marker = "from service_access import service_access_manager"
    
    if import_marker not in content:
        print("ERROR: Could not find import marker in server.py")
        return False
    
    # Add our import
    tier_import = "\n# Tier checking API\nfrom tier_check_api import router as tier_check_router\n"
    content = content.replace(import_marker, import_marker + tier_import)
    
    # Find where to add the router (after app = FastAPI(...))
    app_marker = 'app = FastAPI(title="UC-1 Pro Admin Dashboard API")'
    
    if app_marker not in content:
        print("ERROR: Could not find FastAPI app initialization")
        return False
    
    # Add router registration after CORS middleware setup
    # Find the line after CORS is added
    cors_marker = "app.add_middleware(GZipMiddleware"
    
    router_registration = """
# Include tier check API routes
app.include_router(tier_check_router)
"""
    
    # Insert after CORS/GZip setup
    lines = content.split('\n')
    new_lines = []
    added = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Add after GZipMiddleware line
        if cors_marker in line and not added:
            # Find the closing parenthesis
            if i + 5 < len(lines):
                new_lines.append(router_registration)
                added = True
    
    if not added:
        print("ERROR: Could not find place to add router")
        return False
    
    content = '\n'.join(new_lines)
    
    # Write back
    with open(server_path, 'w') as f:
        f.write(content)
    
    print("✓ Tier Check API routes integrated into server.py!")
    print("  - Added import: tier_check_api")
    print("  - Registered router: app.include_router(tier_check_router)")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("UC-1 Pro: Integrating Tier Check API")
    print("=" * 60)
    
    if integrate_tier_api():
        print("\n✅ Integration complete!")
        print("\nNew API endpoints available:")
        print("  - GET  /api/v1/check-tier")
        print("  - GET  /api/v1/user/tier")
        print("  - GET  /api/v1/services/access-matrix")
        print("  - GET  /api/v1/tiers/info")
        print("  - POST /api/v1/usage/track")
        print("  - GET  /api/v1/rate-limit/check")
        print("\nRestart Ops Center to apply changes:")
        print("  docker restart unicorn-ops-center")
    else:
        print("\n❌ Integration failed!")
        sys.exit(1)
