#!/usr/bin/env python3
"""
Stripe Integration Verification Script
Checks that all components are properly installed and configured
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"✓ {description}")
        return True
    else:
        print(f"✗ {description} - NOT FOUND")
        return False

def check_import(module_name, description):
    """Check if a module can be imported"""
    try:
        __import__(module_name)
        print(f"✓ {description}")
        return True
    except ImportError as e:
        print(f"✗ {description} - IMPORT ERROR: {e}")
        return False

def check_env_var(var_name, required=True):
    """Check if environment variable is set"""
    value = os.getenv(var_name)
    if value:
        # Mask sensitive values
        if 'SECRET' in var_name or 'KEY' in var_name or 'PASSWORD' in var_name:
            display_value = value[:10] + '...' if len(value) > 10 else '***'
        else:
            display_value = value
        print(f"✓ {var_name} = {display_value}")
        return True
    else:
        status = "REQUIRED" if required else "OPTIONAL"
        print(f"{'✗' if required else '⚠'} {var_name} - NOT SET ({status})")
        return not required

def main():
    print("\n" + "="*60)
    print("Stripe Integration Verification")
    print("="*60 + "\n")

    all_ok = True

    # Check core files
    print("1. Core Integration Files")
    print("-" * 40)
    all_ok &= check_file_exists(
        "backend/stripe_integration.py",
        "Stripe integration module"
    )
    all_ok &= check_file_exists(
        "backend/stripe_api.py",
        "Stripe API endpoints"
    )
    all_ok &= check_file_exists(
        "backend/setup_stripe_products.py",
        "Product setup script"
    )

    print("\n2. Documentation Files")
    print("-" * 40)
    check_file_exists(
        "backend/STRIPE_INTEGRATION.md",
        "Integration documentation"
    )
    check_file_exists(
        "backend/.env.stripe.example",
        "Environment template"
    )
    check_file_exists(
        "STRIPE_IMPLEMENTATION_REPORT.md",
        "Implementation report"
    )

    print("\n3. Python Dependencies")
    print("-" * 40)
    all_ok &= check_import("stripe", "Stripe library (stripe==10.0.0)")
    all_ok &= check_import("fastapi", "FastAPI framework")
    all_ok &= check_import("pydantic", "Pydantic models")
    all_ok &= check_import("httpx", "HTTP client (httpx)")

    print("\n4. Integration Modules")
    print("-" * 40)
    # Change to backend directory for imports
    sys.path.insert(0, str(Path(__file__).parent))

    all_ok &= check_import(
        "stripe_integration",
        "Stripe integration module"
    )
    all_ok &= check_import(
        "stripe_api",
        "Stripe API module"
    )
    all_ok &= check_import(
        "subscription_manager",
        "Subscription manager module"
    )
    all_ok &= check_import(
        "keycloak_integration",
        "Keycloak integration module"
    )

    print("\n5. Environment Variables")
    print("-" * 40)
    print("Required:")
    all_ok &= check_env_var("STRIPE_API_KEY", required=True)
    all_ok &= check_env_var("STRIPE_WEBHOOK_SECRET", required=True)

    print("\nOptional (with defaults):")
    check_env_var("STRIPE_SUCCESS_URL", required=False)
    check_env_var("STRIPE_CANCEL_URL", required=False)
    check_env_var("LAGO_API_URL", required=False)
    check_env_var("LAGO_API_KEY", required=False)

    print("\n6. Server Configuration")
    print("-" * 40)

    # Check if stripe_api is imported in server.py
    server_path = Path("backend/server.py")
    if server_path.exists():
        with open(server_path) as f:
            server_content = f.read()

        if "from stripe_api import router as stripe_router" in server_content:
            print("✓ Stripe API router imported in server.py")
        else:
            print("✗ Stripe API router NOT imported in server.py")
            all_ok = False

        if "app.include_router(stripe_router)" in server_content:
            print("✓ Stripe API router registered in server.py")
        else:
            print("✗ Stripe API router NOT registered in server.py")
            all_ok = False

        if '"/api/v1/billing/webhooks/stripe"' in server_content:
            print("✓ Stripe webhook exempt from CSRF in server.py")
        else:
            print("✗ Stripe webhook NOT exempt from CSRF in server.py")
            all_ok = False
    else:
        print("✗ server.py not found")
        all_ok = False

    # Check requirements.txt
    req_path = Path("backend/requirements.txt")
    if req_path.exists():
        with open(req_path) as f:
            req_content = f.read()
        if "stripe==10.0.0" in req_content or "stripe==" in req_content:
            print("✓ Stripe dependency in requirements.txt")
        else:
            print("✗ Stripe dependency NOT in requirements.txt")
            all_ok = False
    else:
        print("✗ requirements.txt not found")
        all_ok = False

    print("\n" + "="*60)
    if all_ok:
        print("✓ All required components verified successfully!")
        print("\nNext steps:")
        print("1. Run: python backend/setup_stripe_products.py")
        print("2. Update subscription_manager.py with price IDs")
        print("3. Configure Stripe webhook endpoint")
        print("4. Restart the Ops Center server")
    else:
        print("✗ Some components are missing or not configured")
        print("\nPlease review the errors above and:")
        print("1. Install missing dependencies: pip install -r backend/requirements.txt")
        print("2. Set required environment variables in .env")
        print("3. Ensure all integration files are present")
    print("="*60 + "\n")

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
