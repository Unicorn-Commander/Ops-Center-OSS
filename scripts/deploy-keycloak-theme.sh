#!/bin/bash

#############################################################################
# Keycloak Theme Deployment Script for UC-1 Pro
#############################################################################
# This script deploys a custom Keycloak theme to the uchub-keycloak container
#
# Author: Magic Unicorn Unconventional Technology & Stuff Inc
# License: MIT
# Created: October 2025
#############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="uchub-keycloak"
THEME_SOURCE_DIR="/home/deploy/Production/UC-1-Pro/services/ops-center/keycloak-theme"
THEME_NAME="uc-1-pro"  # Name of the theme folder
KEYCLOAK_THEMES_DIR="/opt/keycloak/themes"
KEYCLOAK_USER="keycloak"

#############################################################################
# Helper Functions
#############################################################################

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

#############################################################################
# Pre-flight Checks
#############################################################################

print_header "Keycloak Theme Deployment - Pre-flight Checks"

# Check if running as proper user
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root. Consider running as the 'muut' user instead."
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi
print_success "Docker is available"

# Check if container exists and is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    print_error "Container '${CONTAINER_NAME}' is not running"
    print_info "Available Keycloak containers:"
    docker ps --filter "ancestor=quay.io/keycloak/keycloak" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    exit 1
fi
print_success "Container '${CONTAINER_NAME}' is running"

# Check if source theme directory exists
if [ ! -d "${THEME_SOURCE_DIR}" ]; then
    print_error "Source theme directory not found: ${THEME_SOURCE_DIR}"
    print_info "Creating theme directory structure..."
    mkdir -p "${THEME_SOURCE_DIR}/${THEME_NAME}"
    mkdir -p "${THEME_SOURCE_DIR}/${THEME_NAME}/login"
    mkdir -p "${THEME_SOURCE_DIR}/${THEME_NAME}/account"
    mkdir -p "${THEME_SOURCE_DIR}/${THEME_NAME}/email"
    mkdir -p "${THEME_SOURCE_DIR}/${THEME_NAME}/common"

    # Create basic theme.properties
    cat > "${THEME_SOURCE_DIR}/${THEME_NAME}/theme.properties" << 'EOF'
parent=keycloak
import=common/keycloak

# Theme Metadata
name=UC-1 Pro Theme
version=1.0.0
author=Magic Unicorn Tech

# Styling
styles=css/login.css css/styles.css

# Locales
locales=en
EOF

    print_success "Created basic theme structure at ${THEME_SOURCE_DIR}/${THEME_NAME}"
    print_warning "Theme template created. Please customize before deploying."
    print_info "Add your custom files to: ${THEME_SOURCE_DIR}/${THEME_NAME}"

    # Ask if user wants to continue with template
    read -p "Deploy template theme now? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Deployment cancelled. Customize your theme and run this script again."
        exit 0
    fi
fi

# Verify theme structure
if [ ! -f "${THEME_SOURCE_DIR}/${THEME_NAME}/theme.properties" ]; then
    print_error "Invalid theme structure: theme.properties not found"
    print_info "Expected: ${THEME_SOURCE_DIR}/${THEME_NAME}/theme.properties"
    exit 1
fi
print_success "Theme structure validated"

#############################################################################
# Backup Existing Theme (if exists)
#############################################################################

print_header "Backing Up Existing Theme"

# Check if theme already exists in container
if docker exec "${CONTAINER_NAME}" test -d "${KEYCLOAK_THEMES_DIR}/${THEME_NAME}" 2>/dev/null; then
    BACKUP_DIR="${THEME_SOURCE_DIR}/backups"
    BACKUP_NAME="${THEME_NAME}_backup_$(date +%Y%m%d_%H%M%S)"

    mkdir -p "${BACKUP_DIR}"

    print_info "Existing theme found. Creating backup..."
    docker cp "${CONTAINER_NAME}:${KEYCLOAK_THEMES_DIR}/${THEME_NAME}" "${BACKUP_DIR}/${BACKUP_NAME}"

    if [ $? -eq 0 ]; then
        print_success "Backup created: ${BACKUP_DIR}/${BACKUP_NAME}"
    else
        print_warning "Backup failed, but continuing with deployment"
    fi
else
    print_info "No existing theme found. Proceeding with fresh installation."
fi

#############################################################################
# Deploy Theme to Container
#############################################################################

print_header "Deploying Theme to Keycloak Container"

# Copy theme to container
print_info "Copying theme files to container..."
docker cp "${THEME_SOURCE_DIR}/${THEME_NAME}" "${CONTAINER_NAME}:${KEYCLOAK_THEMES_DIR}/"

if [ $? -ne 0 ]; then
    print_error "Failed to copy theme to container"
    exit 1
fi
print_success "Theme files copied successfully"

# Set proper ownership and permissions
print_info "Setting ownership and permissions..."
docker exec "${CONTAINER_NAME}" chown -R ${KEYCLOAK_USER}:root "${KEYCLOAK_THEMES_DIR}/${THEME_NAME}"
docker exec "${CONTAINER_NAME}" chmod -R 755 "${KEYCLOAK_THEMES_DIR}/${THEME_NAME}"
print_success "Permissions set correctly"

# Verify theme installation
print_info "Verifying theme installation..."
if docker exec "${CONTAINER_NAME}" test -f "${KEYCLOAK_THEMES_DIR}/${THEME_NAME}/theme.properties"; then
    print_success "Theme installed successfully"
else
    print_error "Theme verification failed"
    exit 1
fi

#############################################################################
# Rebuild Theme Cache
#############################################################################

print_header "Rebuilding Keycloak Theme Cache"

print_info "Clearing theme cache in Keycloak..."
# Note: Keycloak 26.0 uses Quarkus, cache is cleared on restart
print_info "Cache will be cleared on container restart"

#############################################################################
# Restart Keycloak Container
#############################################################################

print_header "Restarting Keycloak Container"

print_warning "Restarting ${CONTAINER_NAME}... This may take 30-60 seconds."
docker restart "${CONTAINER_NAME}"

if [ $? -ne 0 ]; then
    print_error "Failed to restart container"
    exit 1
fi

print_info "Waiting for Keycloak to become healthy..."
sleep 5

# Wait for container to be healthy (up to 60 seconds)
TIMEOUT=60
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "${CONTAINER_NAME}" 2>/dev/null || echo "no-health-check")

    if [ "$HEALTH_STATUS" = "healthy" ]; then
        print_success "Keycloak is healthy and ready"
        break
    elif [ "$HEALTH_STATUS" = "no-health-check" ]; then
        # If no health check, just wait for container to be running
        if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
            print_success "Keycloak container is running"
            break
        fi
    fi

    sleep 5
    ELAPSED=$((ELAPSED + 5))
    echo -n "."
done
echo

if [ $ELAPSED -ge $TIMEOUT ]; then
    print_warning "Keycloak health check timeout. Container may still be starting..."
    print_info "Check status with: docker logs ${CONTAINER_NAME}"
fi

#############################################################################
# Verify Theme in Keycloak
#############################################################################

print_header "Verifying Theme Installation"

# List themes in container
print_info "Themes available in Keycloak:"
docker exec "${CONTAINER_NAME}" ls -la "${KEYCLOAK_THEMES_DIR}/" | grep -E '^d' | awk '{print "  - " $9}' | grep -v '^\s*-\s*\.\s*$' | grep -v '^\s*-\s*\.\.\s*$'

# Check if our theme is listed
if docker exec "${CONTAINER_NAME}" ls "${KEYCLOAK_THEMES_DIR}/" | grep -q "^${THEME_NAME}$"; then
    print_success "Theme '${THEME_NAME}' is installed and available"
else
    print_error "Theme '${THEME_NAME}' not found in themes directory"
    exit 1
fi

#############################################################################
# Success Summary
#############################################################################

print_header "Deployment Complete!"

echo -e "${GREEN}"
cat << EOF
╔════════════════════════════════════════════════════════════════╗
║           🎨 Theme Successfully Deployed! 🎨                   ║
╚════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

print_success "Theme Name: ${THEME_NAME}"
print_success "Container: ${CONTAINER_NAME}"
print_success "Location: ${KEYCLOAK_THEMES_DIR}/${THEME_NAME}"

echo
print_header "Next Steps - Activate Theme in Keycloak Admin UI"

echo -e "${YELLOW}To activate the theme for your realm:${NC}"
echo
echo "1. Access Keycloak Admin Console:"
echo "   ${BLUE}http://localhost:9100/admin${NC}"
echo "   (or your configured external URL)"
echo
echo "2. Login with admin credentials"
echo
echo "3. Select your realm (default: 'uchub')"
echo
echo "4. Navigate to: ${BLUE}Realm Settings → Themes${NC}"
echo
echo "5. Set the following theme selections:"
echo "   ${GREEN}Login Theme:${NC}        ${THEME_NAME}"
echo "   ${GREEN}Account Theme:${NC}      ${THEME_NAME}"
echo "   ${GREEN}Email Theme:${NC}        ${THEME_NAME} (optional)"
echo "   ${GREEN}Admin Console:${NC}      ${THEME_NAME} (optional)"
echo
echo "6. Click ${BLUE}Save${NC}"
echo
echo "7. Test the theme:"
echo "   - Open an incognito/private browser window"
echo "   - Navigate to your application login"
echo "   - You should see the new theme"
echo

print_header "Verification Commands"

echo "Check theme in container:"
echo "  ${BLUE}docker exec ${CONTAINER_NAME} ls -la ${KEYCLOAK_THEMES_DIR}/${THEME_NAME}${NC}"
echo
echo "View Keycloak logs:"
echo "  ${BLUE}docker logs ${CONTAINER_NAME} --tail 100${NC}"
echo
echo "View theme properties:"
echo "  ${BLUE}docker exec ${CONTAINER_NAME} cat ${KEYCLOAK_THEMES_DIR}/${THEME_NAME}/theme.properties${NC}"
echo

print_header "Troubleshooting"

echo "If theme doesn't appear:"
echo "  1. Check Keycloak logs for errors"
echo "  2. Verify theme.properties syntax"
echo "  3. Clear browser cache"
echo "  4. Restart Keycloak: ${BLUE}docker restart ${CONTAINER_NAME}${NC}"
echo
echo "To redeploy theme after changes:"
echo "  ${BLUE}./deploy-keycloak-theme.sh${NC}"
echo

print_success "Deployment script completed successfully!"
echo

exit 0
