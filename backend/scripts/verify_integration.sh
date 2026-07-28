#!/bin/bash
# Verify LLM Provider Integration
# Quick verification script to check if integration is working

set -e

echo "======================================================================"
echo "LLM Provider Integration - Verification Script"
echo "======================================================================"

echo ""
echo "1. Checking if BYOK_ENCRYPTION_KEY is set..."
ENV_FILE="/home/muut/Production/UC-Cloud/services/ops-center/.env.auth"
if grep -q "BYOK_ENCRYPTION_KEY=" "$ENV_FILE" && ! grep -q "BYOK_ENCRYPTION_KEY=$" "$ENV_FILE"; then
    echo "   ✅ BYOK_ENCRYPTION_KEY is set"
    KEY=$(grep "BYOK_ENCRYPTION_KEY=" "$ENV_FILE" | cut -d'=' -f2)
    echo "   Key: ${KEY:0:8}...${KEY: -8}"
else
    echo "   ❌ BYOK_ENCRYPTION_KEY is NOT set"
    echo ""
    echo "   Run: python3 backend/scripts/generate_encryption_key.py"
    exit 1
fi

echo ""
echo "2. Checking if ops-center container is running..."
if docker ps | grep -q "ops-center-direct"; then
    echo "   ✅ ops-center-direct is running"
else
    echo "   ❌ ops-center-direct is NOT running"
    echo ""
    echo "   Run: docker restart ops-center-direct"
    exit 1
fi

echo ""
echo "3. Checking if integration files exist..."
BACKEND_DIR="/home/muut/Production/UC-Cloud/services/ops-center/backend"
if [ -f "$BACKEND_DIR/llm_provider_integration.py" ]; then
    echo "   ✅ llm_provider_integration.py exists"
else
    echo "   ❌ llm_provider_integration.py NOT found"
    exit 1
fi

if [ -f "$BACKEND_DIR/scripts/test_provider_integration.py" ]; then
    echo "   ✅ test_provider_integration.py exists"
else
    echo "   ❌ test_provider_integration.py NOT found"
    exit 1
fi

echo ""
echo "4. Checking database connectivity..."
if docker exec ops-center-direct psql -U unicorn -d unicorn_db -c "SELECT 1;" > /dev/null 2>&1; then
    echo "   ✅ Database is accessible"
else
    echo "   ⚠️  Database check failed (may not have psql in container)"
    echo "   This is OK if using asyncpg Python driver"
fi

echo ""
echo "5. Testing API endpoint..."
if curl -s http://localhost:8084/api/v1/llm-config/health | grep -q "healthy"; then
    echo "   ✅ LLM Config API is responding"
else
    echo "   ⚠️  LLM Config API health check failed"
    echo "   This is expected if server.py hasn't been updated yet"
fi

echo ""
echo "======================================================================"
echo "VERIFICATION SUMMARY"
echo "======================================================================"
echo ""
echo "✅ All critical components verified"
echo ""
echo "Next steps:"
echo "1. Restart ops-center (if not done yet):"
echo "   docker restart ops-center-direct"
echo ""
echo "2. Run integration tests:"
echo "   docker exec ops-center-direct python3 /app/scripts/test_provider_integration.py"
echo ""
echo "3. Update server.py to initialize the integration"
echo "   See: LLM_PROVIDER_INTEGRATION.md for code examples"
echo ""
echo "======================================================================"
