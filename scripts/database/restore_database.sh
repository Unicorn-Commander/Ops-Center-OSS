#!/bin/bash
# Database Restore Script for Ops-Center
# Restores PostgreSQL database from backup

set -e

# Configuration
BACKUP_DIR="/opt/backups/database"
CONTAINER_NAME="unicorn-postgresql"
DB_USER="unicorn"
DB_NAME="unicorn_db"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Ops-Center Database Restore${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if backup file is provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <backup_file>${NC}"
    echo -e "\n${YELLOW}Available backups:${NC}"
    ls -lht "$BACKUP_DIR"/${DB_NAME}_*.sql 2>/dev/null | head -10 | awk '{print "  " $9 " (" $5 ", " $6 " " $7 ")"}'
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}ERROR: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

# Check if PostgreSQL container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}ERROR: PostgreSQL container '$CONTAINER_NAME' is not running${NC}"
    exit 1
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo -e "${YELLOW}Backup file:${NC} $BACKUP_FILE"
echo -e "${YELLOW}Size:${NC} $BACKUP_SIZE"

# Confirmation prompt
echo -e "\n${RED}WARNING: This will OVERWRITE the current database!${NC}"
read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}Restore cancelled.${NC}"
    exit 0
fi

# Create a backup of current database before restoring
echo -e "\n${YELLOW}Creating backup of current database first...${NC}"
SAFETY_BACKUP="$BACKUP_DIR/${DB_NAME}_before_restore_$(date +"%Y%m%d_%H%M%S").sql"
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" \
    --format=plain \
    --no-owner \
    --no-acl \
    > "$SAFETY_BACKUP"
echo -e "${GREEN}✓ Safety backup created: $SAFETY_BACKUP${NC}"

# Restore database
echo -e "\n${YELLOW}Restoring database from backup...${NC}"
cat "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database restored successfully${NC}"
else
    echo -e "${RED}ERROR: Database restore failed${NC}"
    echo -e "${YELLOW}Safety backup available at: $SAFETY_BACKUP${NC}"
    exit 1
fi

# Verify restoration
echo -e "\n${YELLOW}Verifying restoration...${NC}"
TABLE_COUNT=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | xargs)
echo -e "${GREEN}✓ Tables restored: ${TABLE_COUNT}${NC}"

# Summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Restore Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}Restored from:${NC} $BACKUP_FILE"
echo -e "${YELLOW}Safety backup:${NC} $SAFETY_BACKUP"
echo -e "${YELLOW}Tables:${NC} $TABLE_COUNT"

exit 0
