#!/bin/bash
#
# Testing Lab API - Quick Installation Script
#
# This script:
# 1. Verifies database schema
# 2. Checks environment variables
# 3. Provides instructions to register API in server.py
#
# Usage: bash TESTING_LAB_INSTALL.sh
#

set -e

echo "======================================"
echo "Testing Lab API - Installation Script"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running from correct directory
if [ ! -f "testing_lab_api.py" ]; then
    echo -e "${RED}Error: testing_lab_api.py not found${NC}"
    echo "Please run this script from: /opt/ops-center/backend/"
    exit 1
fi

echo -e "${GREEN}✓${NC} Found testing_lab_api.py"

# Check database schema
echo ""
echo "Step 1: Checking database schema..."
echo "-----------------------------------"

DB_CHECK=$(docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d llm_usage_logs" 2>&1 || true)

if echo "$DB_CHECK" | grep -q "Table"; then
    echo -e "${GREEN}✓${NC} Table llm_usage_logs exists"
else
    echo -e "${YELLOW}⚠${NC} Table llm_usage_logs not found"
    echo ""
    echo "Creating table..."

    docker exec unicorn-postgresql psql -U unicorn -d unicorn_db << 'EOF'
CREATE TABLE IF NOT EXISTS llm_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    model_name VARCHAR(200),
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    cost DECIMAL(10, 6),
    latency_ms INTEGER,
    success BOOLEAN,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_user_date ON llm_usage_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_source ON llm_usage_logs((metadata->>'source'));
EOF

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Table created successfully"
    else
        echo -e "${RED}✗${NC} Failed to create table"
        exit 1
    fi
fi

# Check environment variables
echo ""
echo "Step 2: Checking environment variables..."
echo "------------------------------------------"

ENV_CHECK=$(docker exec ops-center-direct printenv 2>&1 || true)

check_env_var() {
    local var_name=$1
    if echo "$ENV_CHECK" | grep -q "^${var_name}="; then
        echo -e "${GREEN}✓${NC} ${var_name} is set"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} ${var_name} not set"
        return 1
    fi
}

HAS_PROVIDER=false

if check_env_var "OPENROUTER_API_KEY"; then
    HAS_PROVIDER=true
fi

if check_env_var "OPENAI_API_KEY"; then
    HAS_PROVIDER=true
fi

if check_env_var "ANTHROPIC_API_KEY"; then
    HAS_PROVIDER=true
fi

check_env_var "ENCRYPTION_KEY"
check_env_var "POSTGRES_HOST"
check_env_var "POSTGRES_DB"

if [ "$HAS_PROVIDER" = false ]; then
    echo ""
    echo -e "${RED}✗${NC} No provider API keys found!"
    echo "You need at least one of:"
    echo "  - OPENROUTER_API_KEY"
    echo "  - OPENAI_API_KEY"
    echo "  - ANTHROPIC_API_KEY"
    echo ""
    echo "Add to .env.auth and restart container"
    exit 1
fi

# Check if API is registered
echo ""
echo "Step 3: Checking API registration..."
echo "-------------------------------------"

if grep -q "testing_lab_api" ../backend/server.py 2>/dev/null; then
    echo -e "${GREEN}✓${NC} API already registered in server.py"
else
    echo -e "${YELLOW}⚠${NC} API not registered in server.py"
    echo ""
    echo "To register the API, add these lines to backend/server.py:"
    echo ""
    echo "  # Import Testing Lab API"
    echo "  from testing_lab_api import router as testing_lab_router"
    echo ""
    echo "  # Register router (after other routers)"
    echo "  app.include_router(testing_lab_router)"
    echo ""

    read -p "Would you like me to show you the exact location? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Add the import near the top, after other imports:"
        echo ""
        grep -n "from.*import.*router" ../backend/server.py | head -5
        echo ""
        echo "Add the router registration after other include_router calls:"
        echo ""
        grep -n "include_router" ../backend/server.py | head -5
        echo ""
    fi
fi

# Summary
echo ""
echo "======================================"
echo "Installation Check Complete"
echo "======================================"
echo ""

echo "Next Steps:"
echo "----------"
echo ""
echo "1. Register API in server.py (if not done):"
echo "   vim /opt/ops-center/backend/server.py"
echo ""
echo "2. Restart backend:"
echo "   docker restart ops-center-direct"
echo ""
echo "3. Test the API:"
echo "   export SESSION_TOKEN=\"your-session-token\""
echo "   curl -X POST http://localhost:8084/api/v1/llm/test/templates"
echo ""
echo "4. Read documentation:"
echo "   - TESTING_LAB_README.md (quick start)"
echo "   - TESTING_LAB_INTEGRATION.md (full guide)"
echo "   - TESTING_LAB_TESTING_GUIDE.md (test scenarios)"
echo ""

echo -e "${GREEN}Installation script complete!${NC}"
