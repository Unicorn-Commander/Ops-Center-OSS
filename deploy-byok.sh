#!/bin/bash
#
# BYOK Deployment Script
# Deploys BYOK (Bring Your Own Key) system with Keycloak integration
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  BYOK (Bring Your Own Key) - Deployment Script${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Check if encryption key exists
echo -e "${YELLOW}[1/6]${NC} Checking encryption key..."

if [ -f "$BACKEND_DIR/.env" ]; then
    if grep -q "ENCRYPTION_KEY=" "$BACKEND_DIR/.env"; then
        echo -e "${GREEN}✓${NC} Encryption key found in .env"
    else
        echo -e "${YELLOW}!${NC} Encryption key not found in .env"
        echo -e "${BLUE}ℹ${NC} Generating new encryption key..."

        ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
        echo "" >> "$BACKEND_DIR/.env"
        echo "# BYOK Encryption Key (Generated: $(date))" >> "$BACKEND_DIR/.env"
        echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" >> "$BACKEND_DIR/.env"

        echo -e "${GREEN}✓${NC} Encryption key generated and added to .env"
    fi
else
    echo -e "${RED}✗${NC} .env file not found at $BACKEND_DIR/.env"
    echo -e "${BLUE}ℹ${NC} Creating .env from .env.byok template..."

    if [ -f "$BACKEND_DIR/.env.byok" ]; then
        cp "$BACKEND_DIR/.env.byok" "$BACKEND_DIR/.env"
        echo -e "${GREEN}✓${NC} .env file created"
    else
        echo -e "${RED}✗${NC} Template file .env.byok not found"
        exit 1
    fi
fi

# Step 2: Check Keycloak configuration
echo ""
echo -e "${YELLOW}[2/6]${NC} Checking Keycloak configuration..."

if grep -q "KEYCLOAK_URL=" "$BACKEND_DIR/.env"; then
    KEYCLOAK_URL=$(grep "KEYCLOAK_URL=" "$BACKEND_DIR/.env" | cut -d '=' -f2)
    echo -e "${GREEN}✓${NC} Keycloak URL: $KEYCLOAK_URL"
else
    echo -e "${YELLOW}!${NC} KEYCLOAK_URL not configured"
    echo "KEYCLOAK_URL=https://auth.unicorncommander.ai" >> "$BACKEND_DIR/.env"
    echo "KEYCLOAK_REALM=uchub" >> "$BACKEND_DIR/.env"
    echo "KEYCLOAK_CLIENT_ID=ops-center" >> "$BACKEND_DIR/.env"
    echo -e "${GREEN}✓${NC} Default Keycloak config added"
fi

# Step 3: Check dependencies
echo ""
echo -e "${YELLOW}[3/6]${NC} Checking Python dependencies..."

if grep -q "cryptography" "$BACKEND_DIR/requirements.txt" && grep -q "httpx" "$BACKEND_DIR/requirements.txt"; then
    echo -e "${GREEN}✓${NC} Required dependencies in requirements.txt"
else
    echo -e "${YELLOW}!${NC} Adding missing dependencies..."
    echo "cryptography>=41.0.0" >> "$BACKEND_DIR/requirements.txt"
    echo "httpx==0.27.0" >> "$BACKEND_DIR/requirements.txt"
    echo -e "${GREEN}✓${NC} Dependencies added"
fi

# Step 4: Check file integrity
echo ""
echo -e "${YELLOW}[4/6]${NC} Verifying BYOK files..."

REQUIRED_FILES=(
    "$BACKEND_DIR/byok_api.py"
    "$BACKEND_DIR/byok_helpers.py"
    "$BACKEND_DIR/key_encryption.py"
    "$BACKEND_DIR/keycloak_integration.py"
    "$BACKEND_DIR/tests/test_byok.py"
)

ALL_FILES_EXIST=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $(basename $file)"
    else
        echo -e "${RED}✗${NC} Missing: $file"
        ALL_FILES_EXIST=false
    fi
done

if [ "$ALL_FILES_EXIST" = false ]; then
    echo -e "${RED}✗${NC} Some required files are missing"
    exit 1
fi

# Step 5: Build Docker container
echo ""
echo -e "${YELLOW}[5/6]${NC} Building ops-center container..."
echo -e "${BLUE}ℹ${NC} This may take a few minutes..."

cd "$SCRIPT_DIR"

if docker-compose -f docker-compose.ops-center-sso.yml build; then
    echo -e "${GREEN}✓${NC} Container built successfully"
else
    echo -e "${RED}✗${NC} Container build failed"
    exit 1
fi

# Step 6: Restart service
echo ""
echo -e "${YELLOW}[6/6]${NC} Restarting ops-center service..."

docker-compose -f docker-compose.ops-center-sso.yml down
docker-compose -f docker-compose.ops-center-sso.yml up -d

echo ""
echo -e "${GREEN}✓${NC} Service restarted"

# Wait for service to be ready
echo ""
echo -e "${BLUE}ℹ${NC} Waiting for service to be ready..."
sleep 5

# Verify service is running
if docker ps | grep -q "ops-center-direct"; then
    echo -e "${GREEN}✓${NC} Service is running"
else
    echo -e "${RED}✗${NC} Service failed to start"
    echo -e "${BLUE}ℹ${NC} Check logs with: docker logs ops-center-direct"
    exit 1
fi

# Test encryption in container
echo ""
echo -e "${BLUE}ℹ${NC} Testing encryption..."

if docker exec ops-center-direct python3 -c "from key_encryption import get_encryption; enc = get_encryption(); enc.encrypt_key('test')" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Encryption test passed"
else
    echo -e "${YELLOW}!${NC} Encryption test failed (may need to wait for service)"
fi

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ BYOK Deployment Complete${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. Configure Keycloak client secret (if not done):"
echo "   Edit: $BACKEND_DIR/.env"
echo "   Set: KEYCLOAK_CLIENT_SECRET=your_secret_here"
echo ""
echo "2. Test API endpoints:"
echo "   curl https://unicorncommander.ai/api/v1/byok/providers"
echo ""
echo "3. View logs:"
echo "   docker logs -f ops-center-direct"
echo ""
echo "4. Run test suite (after login):"
echo "   export TEST_SESSION_COOKIE=your_cookie"
echo "   cd $BACKEND_DIR"
echo "   python3 tests/test_byok.py"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "   $BACKEND_DIR/BYOK_IMPLEMENTATION_COMPLETE.md"
echo ""
