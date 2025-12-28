#!/bin/bash
# Run Alembic Migrations with Automatic Backup
# Usage: ./run_migrations.sh [--dry-run]

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
echo -e "${GREEN}Run Alembic Migrations${NC}"
echo -e "${GREEN}========================================${NC}"

# Check for dry-run flag
DRY_RUN=false
if [ "$1" == "--dry-run" ]; then
    DRY_RUN=true
    echo -e "${YELLOW}Mode: DRY RUN (no changes will be made)${NC}"
fi

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

# Get target version (latest)
TARGET_VERSION=$(docker exec "$CONTAINER_NAME" bash -c "cd /app && alembic heads 2>&1" | grep -oP '^\w+' || echo "unknown")
echo -e "${YELLOW}Target version:${NC} $TARGET_VERSION"

if [ "$CURRENT_VERSION" == "$TARGET_VERSION" ]; then
    echo -e "${GREEN}✓ Database is already up to date${NC}"
    exit 0
fi

# Show pending migrations
echo -e "\n${YELLOW}Pending migrations:${NC}"
docker exec "$CONTAINER_NAME" bash -c "cd /app && alembic history --verbose" | grep -A 5 "$CURRENT_VERSION"

if [ "$DRY_RUN" == true ]; then
    echo -e "\n${YELLOW}DRY RUN MODE: Showing SQL that would be executed...${NC}"
    docker exec "$CONTAINER_NAME" bash -c "cd /app && alembic upgrade head --sql"
    echo -e "\n${GREEN}Dry run complete. No changes were made.${NC}"
    exit 0
fi

# Confirmation prompt
echo -e "\n${RED}WARNING: This will modify the database schema!${NC}"
read -p "Continue with migration? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}Migration cancelled.${NC}"
    exit 0
fi

# Create backup before migration
echo -e "\n${YELLOW}Creating database backup before migration...${NC}"
if [ -f "$BACKUP_SCRIPT" ]; then
    bash "$BACKUP_SCRIPT"
    echo -e "${GREEN}✓ Backup complete${NC}"
else
    echo -e "${RED}ERROR: Backup script not found: $BACKUP_SCRIPT${NC}"
    read -p "Continue WITHOUT backup? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${YELLOW}Migration cancelled.${NC}"
        exit 0
    fi
fi

# Run migration
echo -e "\n${YELLOW}Running migrations...${NC}"
docker exec "$CONTAINER_NAME" bash -c "cd /app && alembic upgrade head"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Migrations applied successfully${NC}"
else
    echo -e "${RED}ERROR: Migration failed${NC}"
    echo -e "${YELLOW}Database backup is available in /home/muut/backups/database/${NC}"
    echo -e "${YELLOW}To rollback: ./scripts/rollback_migration.sh${NC}"
    exit 1
fi

# Verify new version
NEW_VERSION=$(docker exec "$CONTAINER_NAME" bash -c "cd /app && alembic current 2>&1" | grep -oP '^\w+' || echo "unknown")
echo -e "${YELLOW}New version:${NC} $NEW_VERSION"

# Get table count
TABLE_COUNT=$(docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | xargs)

# Summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Migration Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}Old version:${NC} $CURRENT_VERSION"
echo -e "${YELLOW}New version:${NC} $NEW_VERSION"
echo -e "${YELLOW}Tables:${NC} $TABLE_COUNT"

exit 0
