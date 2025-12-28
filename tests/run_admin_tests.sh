#!/bin/bash
# Test runner for Keycloak Admin Subscription Management

set -e

echo "========================================"
echo "Keycloak Admin API Test Suite"
echo "========================================"
echo

# Check if .env exists
if [ ! -f "../.env" ]; then
    echo "Error: .env file not found in parent directory"
    echo "Please create .env with Keycloak credentials"
    exit 1
fi

# Load environment variables
echo "Loading environment variables..."
set -a
source ../.env
set +a

# Set defaults if not in .env
export KEYCLOAK_URL="${KEYCLOAK_URL:-https://auth.your-domain.com}"
export KEYCLOAK_REALM="${KEYCLOAK_REALM:-uchub}"
export KEYCLOAK_CLIENT_ID="${KEYCLOAK_CLIENT_ID:-admin-cli}"
export KEYCLOAK_ADMIN_USERNAME="${KEYCLOAK_ADMIN_USERNAME:-admin}"

# Check for admin password
if [ -z "$KEYCLOAK_ADMIN_PASSWORD" ]; then
    echo "Error: KEYCLOAK_ADMIN_PASSWORD not set in .env"
    exit 1
fi

echo "Environment configured:"
echo "  KEYCLOAK_URL: $KEYCLOAK_URL"
echo "  KEYCLOAK_REALM: $KEYCLOAK_REALM"
echo "  KEYCLOAK_ADMIN_USERNAME: $KEYCLOAK_ADMIN_USERNAME"
echo

# Run Python tests
echo "Running Python test suite..."
python3 test_keycloak_admin.py

echo
echo "========================================"
echo "Tests complete!"
echo "========================================"
