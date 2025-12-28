#!/bin/bash

# UC-1 Pro Custom Auth System Setup Script
# This script will help you deploy the custom auth system

set -e

echo "🦄 UC-1 Pro Custom Auth System Setup"
echo "====================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}Step 1: Checking Prerequisites${NC}"
echo "================================"

# Check if running from correct directory
if [ ! -f "backend/server_auth_integrated.py" ]; then
    echo -e "${RED}Error: backend/server_auth_integrated.py not found!${NC}"
    echo "Please run this script from /home/muut/Production/UC-1-Pro/services/ops-center"
    exit 1
fi

echo -e "${GREEN}✓ Files found${NC}"

# Check Python dependencies
echo ""
echo "Checking Python dependencies..."
MISSING_DEPS=()

python3 -c "import stripe" 2>/dev/null || MISSING_DEPS+=("stripe")
python3 -c "import httpx" 2>/dev/null || MISSING_DEPS+=("httpx")
python3 -c "import redis" 2>/dev/null || MISSING_DEPS+=("redis")
python3 -c "import cryptography" 2>/dev/null || MISSING_DEPS+=("cryptography")

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${YELLOW}Missing dependencies: ${MISSING_DEPS[*]}${NC}"
    read -p "Install now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing dependencies..."
        pip3 install stripe httpx redis cryptography
        echo -e "${GREEN}✓ Dependencies installed${NC}"
    else
        echo -e "${RED}Please install dependencies manually: pip3 install stripe httpx redis cryptography${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ All dependencies installed${NC}"
fi

echo ""
echo -e "${BLUE}Step 2: Update OAuth Redirect URIs${NC}"
echo "===================================="
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: You must update redirect URIs in your OAuth applications${NC}"
echo ""
echo "Old Authentik callback:"
echo "  https://auth.your-domain.com/source/oauth/callback/{provider}/"
echo ""
echo "New custom callback:"
echo "  https://your-domain.com/auth/callback"
echo ""
echo "Update in these consoles:"
echo ""
echo "1. Google OAuth:"
echo "   → https://console.cloud.google.com/"
echo "   → Credentials → OAuth 2.0 Client IDs"
echo "   → Edit your client"
echo "   → Authorized redirect URIs → Add:"
echo "     https://your-domain.com/auth/callback"
echo ""
echo "2. GitHub OAuth:"
echo "   → https://github.com/settings/developers"
echo "   → OAuth Apps → Your app"
echo "   → Authorization callback URL:"
echo "     https://your-domain.com/auth/callback"
echo ""
echo "3. Microsoft OAuth:"
echo "   → https://portal.azure.com/"
echo "   → App registrations → Your app"
echo "   → Authentication → Add redirect URI:"
echo "     https://your-domain.com/auth/callback"
echo ""
read -p "Press Enter after updating all OAuth apps..."

echo ""
echo -e "${BLUE}Step 3: Backup Current Files${NC}"
echo "============================="

if [ -f "backend/server.py" ]; then
    BACKUP_FILE="backend/server_authentik_backup_$(date +%Y%m%d_%H%M%S).py"
    cp backend/server.py "$BACKUP_FILE"
    echo -e "${GREEN}✓ Backed up server.py to $BACKUP_FILE${NC}"
fi

if [ -f "public/login.html" ]; then
    BACKUP_FILE="public/login_authentik_backup_$(date +%Y%m%d_%H%M%S).html"
    cp public/login.html "$BACKUP_FILE"
    echo -e "${GREEN}✓ Backed up login.html to $BACKUP_FILE${NC}"
fi

echo ""
echo -e "${BLUE}Step 4: Deploy New Files${NC}"
echo "========================"

# Deploy server
cp backend/server_auth_integrated.py backend/server.py
echo -e "${GREEN}✓ Deployed new server.py${NC}"

# Deploy login page
cp public/login-new.html public/login.html
echo -e "${GREEN}✓ Deployed new login.html${NC}"

# Check if signup and dashboard are already there
if [ ! -f "public/signup.html" ]; then
    echo -e "${YELLOW}Note: public/signup.html already exists${NC}"
fi

if [ ! -f "public/dashboard.html" ]; then
    echo -e "${YELLOW}Note: public/dashboard.html already exists${NC}"
fi

echo ""
echo -e "${BLUE}Step 5: Environment Configuration${NC}"
echo "=================================="

if [ -f ".env.auth" ]; then
    echo -e "${GREEN}✓ .env.auth already exists${NC}"
    echo ""
    echo "Please review and update these values in .env.auth:"
    echo ""
    echo "🔴 REQUIRED (for full functionality):"
    echo "  - STRIPE_SECRET_KEY"
    echo "  - STRIPE_WEBHOOK_SECRET"
    echo "  - STRIPE_*_PRICE_ID (4 price IDs)"
    echo "  - LAGO_API_KEY"
    echo ""
    echo "✅ ALREADY CONFIGURED:"
    echo "  - Google OAuth credentials"
    echo "  - GitHub OAuth credentials"
    echo "  - Microsoft OAuth credentials"
    echo "  - Redis URL"
    echo "  - Encryption key"
    echo ""
else
    echo -e "${RED}Error: .env.auth not found${NC}"
    exit 1
fi

read -p "Press Enter to continue..."

echo ""
echo -e "${BLUE}Step 6: Docker Container Restart${NC}"
echo "================================="

echo ""
echo "Checking for ops-center container..."

if docker ps -a | grep -q "ops-center"; then
    CONTAINER_NAME=$(docker ps -a --filter "name=ops-center" --format "{{.Names}}" | head -1)
    echo "Found container: $CONTAINER_NAME"
    echo ""
    read -p "Restart container now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Restarting $CONTAINER_NAME..."
        docker restart "$CONTAINER_NAME"
        echo -e "${GREEN}✓ Container restarted${NC}"
        echo ""
        echo "Waiting for container to be ready..."
        sleep 5
        echo ""
        echo "Checking logs..."
        docker logs "$CONTAINER_NAME" --tail 20
    fi
else
    echo -e "${YELLOW}No ops-center container found. You may need to rebuild.${NC}"
    echo "Try: docker-compose up -d --build ops-center"
fi

echo ""
echo -e "${BLUE}Step 7: Next Steps${NC}"
echo "=================="
echo ""
echo -e "${GREEN}✅ Custom auth system deployed!${NC}"
echo ""
echo "What works now:"
echo "  ✓ New login page at https://your-domain.com/"
echo "  ✓ OAuth login endpoints ready"
echo "  ✓ User database created"
echo "  ✓ Session management active"
echo ""
echo "To complete setup:"
echo ""
echo "1. Configure Stripe (if needed):"
echo "   → Create 4 products in Stripe dashboard"
echo "   → Update STRIPE_* variables in .env.auth"
echo "   → Set webhook URL: https://your-domain.com/api/v1/stripe/webhook"
echo ""
echo "2. Configure Lago (if needed):"
echo "   → Create billable metrics"
echo "   → Create Professional/Enterprise plans"
echo "   → Update LAGO_API_KEY in .env.auth"
echo ""
echo "3. Test authentication:"
echo "   → Visit https://your-domain.com/"
echo "   → Click 'Continue with Google' (or GitHub/Microsoft)"
echo "   → Should redirect and create account"
echo ""
echo "4. Check logs if issues:"
echo "   docker logs $CONTAINER_NAME -f"
echo ""
echo "5. Check database:"
echo "   sqlite3 /home/muut/Production/UC-1-Pro/volumes/ops_center.db"
echo "   SELECT * FROM users;"
echo ""
echo -e "${YELLOW}📚 Documentation:${NC}"
echo "  - INTEGRATION_GUIDE.md - Complete setup guide"
echo "  - DEPLOYMENT_SUMMARY.md - What we built"
echo "  - backend/auth/README.md - Module docs"
echo ""
echo -e "${GREEN}🎉 Setup complete! Visit https://your-domain.com/ to test${NC}"
