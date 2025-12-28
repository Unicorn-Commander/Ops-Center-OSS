#!/bin/bash
# Rollback Last Alembic Migration with Automatic Backup
# Usage: ./rollback_migration.sh [number_of_steps]

set -e

# Configuration
PROJECT_DIR="/home/muut/Production/UC-Cloud/services/ops-center"
CONTAINER_NAME="ops-center-direct"
BACKUP_SCRIPT="$PROJECT_DIR/scripts/database/backup_database.sh"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Rollback Alembic Migration${NC}"
echo -e "${GREEN}========================================${NC}"

# Default to rolling back 1 migration
STEPS="${1:-1}"
echo -e "${YELLOW}Rolling back:${NC} $STEPS migration(s)"

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}ERROR: Container '$CONTAINER_NAME' is not running${NC}"
    echo -e "${YELLOW}Start the container first: docker start $CONTAINER_NAME${NC}"
    exit 1
fi

# Get current migration version
echo -e "\n${YELLOW}Checking current migration status...${NC}"
CURRENT_VERSION=$(docker exec "$CONTAINER_NAME" bash -c "cd /app && alembic current 2>&1" | grep -oP '^\w+' || echo "none")
echo -e "${YELLOW}Current version:${NC} $CURRENT_VERSION"

if [ "$CURRENT_VERSION" == "none" ] || [ "$CURRENT_VERSION" == "" ]; then
    echo -e "${YELLOW}No migrations to rollback${NC}"
    exit 0
fi

# Show migration history
echo -e "\n${YELLOW}Migration history:${NC}"
docker exec "$CONTAINER_NAME" bash -c "cd /app && alembic history --verbose" | head -20

# Confirmation prompt
echo -e "\n${RED}WARNING: This will rollback the last $STEPS migration(s)!${NC}"
echo -e "${YELLOW}Changes will be REVERSED in the database schema.${NC}"
read -p "Continue with rollback? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}Rollback cancelled.${NC}"
    exit 0
fi

# Create backup before rollback
echo -e "\n${YELLOW}Creating database backup before rollback...${NC}"
if [ -f "$BACKUP_SCRIPT" ]; then
    bash "$BACKUP_SCRIPT"
    echo -e "${GREEN}✓ Backup complete${NC}"
else
    echo -e "${RED}ERROR: Backup script not found: $BACKUP_SCRIPT${NC}"
    read -p "Continue WITHOUT backup? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${YELLOW}Rollback cancelled.${NC}"
        exit 0
    fi
fi

# Run rollback
echo -e "\n${YELLOW}Rolling back migrations...${NC}"
docker exec "$CONTAINER_NAME" bash -c "cd /app && alembic downgrade -$STEPS"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Rollback successful${NC}"
else
    echo -e "${RED}ERROR: Rollback failed${NC}"
    echo -e "${YELLOW}Database backup is available in /home/muut/backups/database/${NC}"
    exit 1
fi

# Verify new version
NEW_VERSION=$(docker exec "$CONTAINER_NAME" bash -c "cd /app && alembic current 2>&1" | grep -oP '^\w+' || echo "none")
echo -e "${YELLOW}New version:${NC} $NEW_VERSION"

# Get table count
TABLE_COUNT=$(docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | xargs 2>/dev/null || echo "0")

# Summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Rollback Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}Old version:${NC} $CURRENT_VERSION"
echo -e "${YELLOW}New version:${NC} $NEW_VERSION"
echo -e "${YELLOW}Tables:${NC} $TABLE_COUNT"
echo -e "\n${YELLOW}To re-apply migrations: ./scripts/run_migrations.sh${NC}"

exit 0
