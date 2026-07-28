#!/bin/bash

#############################################################################
# Keycloak Theme Verification Script
#############################################################################
# This script verifies that the UC-1 Pro theme is properly installed
#############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CONTAINER_NAME="uchub-keycloak"
THEME_NAME="uc-1-pro"
KEYCLOAK_THEMES_DIR="/opt/keycloak/themes"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Keycloak Theme Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Check if container is running
echo -n "Checking if Keycloak container is running... "
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo -e "${RED}Error: Container '${CONTAINER_NAME}' is not running${NC}"
    exit 1
fi

# Check if theme directory exists
echo -n "Checking if theme directory exists... "
if docker exec "${CONTAINER_NAME}" test -d "${KEYCLOAK_THEMES_DIR}/${THEME_NAME}"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo -e "${RED}Error: Theme directory not found${NC}"
    exit 1
fi

# Check theme.properties
echo -n "Checking theme.properties... "
if docker exec "${CONTAINER_NAME}" test -f "${KEYCLOAK_THEMES_DIR}/${THEME_NAME}/theme.properties"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo -e "${RED}Error: theme.properties not found${NC}"
    exit 1
fi

# Check login theme
echo -n "Checking login theme structure... "
if docker exec "${CONTAINER_NAME}" test -d "${KEYCLOAK_THEMES_DIR}/${THEME_NAME}/login"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠${NC} Login theme not found (optional)"
fi

# Check CSS file
echo -n "Checking login.css... "
if docker exec "${CONTAINER_NAME}" test -f "${KEYCLOAK_THEMES_DIR}/${THEME_NAME}/login/resources/css/login.css"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠${NC} login.css not found (optional)"
fi

# Check file permissions
echo -n "Checking file permissions... "
PERMS=$(docker exec "${CONTAINER_NAME}" stat -c "%a" "${KEYCLOAK_THEMES_DIR}/${THEME_NAME}")
if [ "$PERMS" = "755" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠${NC} Permissions: $PERMS (expected 755)"
fi

# Check file ownership
echo -n "Checking file ownership... "
OWNER=$(docker exec "${CONTAINER_NAME}" stat -c "%U" "${KEYCLOAK_THEMES_DIR}/${THEME_NAME}")
if [ "$OWNER" = "keycloak" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠${NC} Owner: $OWNER (expected keycloak)"
fi

# List theme contents
echo
echo -e "${BLUE}Theme Contents:${NC}"
docker exec "${CONTAINER_NAME}" find "${KEYCLOAK_THEMES_DIR}/${THEME_NAME}" -type f | sed 's|.*/||' | sort | sed 's/^/  - /'

# Check container health
echo
echo -n "Checking Keycloak health status... "
HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "${CONTAINER_NAME}" 2>/dev/null || echo "no-health-check")
if [ "$HEALTH" = "healthy" ]; then
    echo -e "${GREEN}✓ Healthy${NC}"
elif [ "$HEALTH" = "no-health-check" ]; then
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${GREEN}✓ Running${NC}"
    else
        echo -e "${RED}✗ Not running${NC}"
    fi
else
    echo -e "${YELLOW}⚠ ${HEALTH}${NC}"
fi

# Summary
echo
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Theme Verification Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Access Keycloak Admin Console: ${BLUE}http://localhost:9100/admin${NC}"
echo "2. Select your realm (e.g., 'uchub')"
echo "3. Go to: ${BLUE}Realm Settings → Themes${NC}"
echo "4. Set Login Theme to: ${GREEN}${THEME_NAME}${NC}"
echo "5. Click ${GREEN}Save${NC}"
echo
echo "Test the theme:"
echo "  ${BLUE}http://localhost:9100/realms/uchub/account${NC}"
echo

exit 0
