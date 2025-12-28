#!/bin/bash
# BYOK Setup Script
# Sets up the Bring Your Own Key system for UC-1 Pro

set -e

echo "=========================================="
echo "BYOK (Bring Your Own Key) Setup"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running from correct directory
if [ ! -f "backend/byok_api.py" ]; then
    echo -e "${RED}Error: Please run this script from the ops-center directory${NC}"
    exit 1
fi

echo "Step 1: Checking dependencies..."

# Check Python dependencies
python3 -c "from cryptography.fernet import Fernet" 2>/dev/null || {
    echo -e "${YELLOW}Installing cryptography library...${NC}"
    pip3 install cryptography
}

echo -e "${GREEN}✓ Dependencies OK${NC}"
echo ""

echo "Step 2: Generating encryption key..."

# Generate encryption key
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

echo -e "${GREEN}✓ Generated encryption key${NC}"
echo ""

echo "Step 3: Checking environment configuration..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env from template...${NC}"
    cp .env.template .env
fi

# Check if ENCRYPTION_KEY is already set
if grep -q "^ENCRYPTION_KEY=" .env; then
    echo -e "${YELLOW}ENCRYPTION_KEY already exists in .env${NC}"
    read -p "Overwrite? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sed -i "s|^ENCRYPTION_KEY=.*|ENCRYPTION_KEY=$ENCRYPTION_KEY|" .env
        echo -e "${GREEN}✓ Updated ENCRYPTION_KEY in .env${NC}"
    else
        echo -e "${YELLOW}Keeping existing ENCRYPTION_KEY${NC}"
    fi
else
    echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" >> .env
    echo -e "${GREEN}✓ Added ENCRYPTION_KEY to .env${NC}"
fi

echo ""

# Check Authentik token
echo "Step 4: Checking Authentik configuration..."

if ! grep -q "^AUTHENTIK_BOOTSTRAP_TOKEN=" .env || grep -q "^AUTHENTIK_BOOTSTRAP_TOKEN=your-authentik-api-token-here" .env; then
    echo -e "${YELLOW}⚠ AUTHENTIK_BOOTSTRAP_TOKEN not configured${NC}"
    echo ""
    echo "To complete BYOK setup, you need an Authentik API token:"
    echo "1. Login to Authentik at https://auth.your-domain.com"
    echo "2. Go to Admin Interface → Directory → Tokens & App passwords"
    echo "3. Create a new token with 'User write' permissions"
    echo "4. Add it to .env:"
    echo "   AUTHENTIK_BOOTSTRAP_TOKEN=your-token-here"
    echo ""
else
    echo -e "${GREEN}✓ AUTHENTIK_BOOTSTRAP_TOKEN configured${NC}"
fi

echo ""
echo "Step 5: Running tests..."

# Test encryption module
if python3 -c "
import os
os.environ['ENCRYPTION_KEY'] = '$ENCRYPTION_KEY'
from backend.key_encryption import get_encryption
enc = get_encryption()
test_key = 'sk-test-1234567890'
encrypted = enc.encrypt_key(test_key)
decrypted = enc.decrypt_key(encrypted)
assert decrypted == test_key, 'Encryption test failed'
print('✓ Encryption/decryption working')
" 2>&1; then
    echo -e "${GREEN}✓ Encryption module working${NC}"
else
    echo -e "${RED}✗ Encryption test failed${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo "BYOK Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. ${YELLOW}Restart the ops-center service:${NC}"
echo "   docker restart unicorn-ops-center"
echo ""
echo "2. ${YELLOW}Configure Authentik API token${NC} (if not already done)"
echo ""
echo "3. ${YELLOW}Test the API:${NC}"
echo "   cd backend/tests"
echo "   python3 test_byok.py"
echo ""
echo "4. ${YELLOW}Access BYOK UI:${NC}"
echo "   https://your-domain.com/settings/api-keys"
echo ""
echo "Documentation:"
echo "- API Reference: /home/muut/Production/UC-1-Pro/docs/BYOK_API.md"
echo "- Implementation Guide: /home/muut/Production/UC-1-Pro/docs/BYOK_IMPLEMENTATION.md"
echo ""
echo -e "${GREEN}Generated Encryption Key (keep secure):${NC}"
echo "$ENCRYPTION_KEY"
echo ""
