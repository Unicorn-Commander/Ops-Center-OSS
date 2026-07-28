#!/bin/bash
# Email Alert System Deployment Script
# Version: 1.0.0
# Date: November 29, 2025

set -e  # Exit on error

echo "=================================================="
echo "Email Alert System Deployment"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running from correct directory
if [ ! -f "backend/email_alerts.py" ]; then
    echo -e "${RED}Error: Must run from ops-center directory${NC}"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo -e "${YELLOW}Step 1/6: Checking environment variables...${NC}"
if [ -z "$MS365_CLIENT_ID" ] || [ -z "$MS365_TENANT_ID" ] || [ -z "$MS365_CLIENT_SECRET" ]; then
    echo -e "${YELLOW}Warning: Microsoft 365 credentials not found in environment${NC}"
    echo "Will load from database instead (if configured)"
else
    echo -e "${GREEN}✓ Microsoft 365 credentials found${NC}"
fi

echo ""
echo -e "${YELLOW}Step 2/6: Installing Python dependencies...${NC}"
docker exec ops-center-direct pip install --quiet msal==1.30.0 jinja2==3.1.4 httpx==0.27.0 psycopg2-binary==2.9.9
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}✗ Failed to install dependencies${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 3/6: Applying database migration...${NC}"
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /tmp/create_email_logs_table.sql > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database migration applied${NC}"
else
    echo -e "${YELLOW}⚠ Migration may have already been applied${NC}"
fi

echo ""
echo -e "${YELLOW}Step 4/6: Checking if API router is registered...${NC}"
if grep -q "email_alerts_api" backend/server.py; then
    echo -e "${GREEN}✓ API router already registered${NC}"
else
    echo -e "${RED}✗ API router NOT registered${NC}"
    echo ""
    echo "Add these lines to backend/server.py:"
    echo ""
    echo "  from email_alerts_api import router as alerts_router"
    echo "  app.include_router(alerts_router)"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to cancel..."
fi

echo ""
echo -e "${YELLOW}Step 5/6: Restarting ops-center container...${NC}"
docker restart ops-center-direct
echo "Waiting for container to start..."
sleep 5
echo -e "${GREEN}✓ Container restarted${NC}"

echo ""
echo -e "${YELLOW}Step 6/6: Running health check...${NC}"
sleep 2
HEALTH_RESPONSE=$(curl -s http://localhost:8084/api/v1/alerts/health 2>/dev/null)

if echo "$HEALTH_RESPONSE" | grep -q "\"healthy\":true"; then
    echo -e "${GREEN}✓ Email system is healthy!${NC}"
    echo ""
    echo "Response:"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool
else
    echo -e "${RED}✗ Health check failed or endpoint not available${NC}"
    echo "Response: $HEALTH_RESPONSE"
    echo ""
    echo "This might mean:"
    echo "1. API router not registered in server.py"
    echo "2. Container still starting (wait 30 seconds and retry)"
    echo "3. Microsoft 365 credentials not configured"
fi

echo ""
echo "=================================================="
echo "Deployment Complete!"
echo "=================================================="
echo ""
echo "Next Steps:"
echo "1. Send test email:"
echo "   curl -X POST http://localhost:8084/api/v1/alerts/test \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"recipient\": \"admin@example.com\"}'"
echo ""
echo "2. View email history:"
echo "   curl http://localhost:8084/api/v1/alerts/history"
echo ""
echo "3. Check container logs:"
echo "   docker logs ops-center-direct --tail 50 -f"
echo ""
echo "Documentation: docs/EMAIL_ALERTS_IMPLEMENTATION_REPORT.md"
echo ""
