#!/bin/bash
# Database Backup Script for Ops-Center
# Creates PostgreSQL backup using pg_dump

set -e

# Configuration
BACKUP_DIR="/opt/backups/database"
CONTAINER_NAME="unicorn-postgresql"
DB_USER="unicorn"
DB_NAME="unicorn_db"
RETENTION_DAYS=7
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql"
BACKUP_METADATA="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.metadata.json"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Ops-Center Database Backup${NC}"
echo -e "${GREEN}========================================${NC}"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Check if PostgreSQL container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}ERROR: PostgreSQL container '$CONTAINER_NAME' is not running${NC}"
    exit 1
fi

# Get database size
DB_SIZE=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" | xargs)

echo -e "${YELLOW}Database:${NC} $DB_NAME"
echo -e "${YELLOW}Size:${NC} $DB_SIZE"
echo -e "${YELLOW}Backup file:${NC} $BACKUP_FILE"

# Create backup
echo -e "\n${YELLOW}Creating backup...${NC}"
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" \
    --format=plain \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists \
    > "$BACKUP_FILE"

# Verify backup was created
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}ERROR: Backup file was not created${NC}"
    exit 1
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo -e "${GREEN}✓ Backup created successfully${NC}"
echo -e "${YELLOW}Backup size:${NC} $BACKUP_SIZE"

# Create metadata file
cat > "$BACKUP_METADATA" <<EOF
{
  "database": "$DB_NAME",
  "timestamp": "$TIMESTAMP",
  "date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "db_size": "$DB_SIZE",
  "backup_file": "$BACKUP_FILE",
  "backup_size": "$BACKUP_SIZE",
  "retention_days": $RETENTION_DAYS,
  "expires_on": "$(date -d "+${RETENTION_DAYS} days" +"%Y-%m-%d")",
  "pg_version": "$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -t -c 'SELECT version();' | xargs | cut -d' ' -f2)",
  "tables": $(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | xargs),
  "created_by": "backup_database.sh"
}
EOF

echo -e "${GREEN}✓ Metadata created${NC}"

# Cleanup old backups (keep last N days)
echo -e "\n${YELLOW}Cleaning up old backups (retention: ${RETENTION_DAYS} days)...${NC}"
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql" -type f -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "${DB_NAME}_*.metadata.json" -type f -mtime +$RETENTION_DAYS -delete

REMAINING_BACKUPS=$(ls -1 "$BACKUP_DIR"/${DB_NAME}_*.sql 2>/dev/null | wc -l)
echo -e "${GREEN}✓ Cleanup complete. Remaining backups: ${REMAINING_BACKUPS}${NC}"

# Summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Backup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}Backup location:${NC} $BACKUP_FILE"
echo -e "${YELLOW}Metadata:${NC} $BACKUP_METADATA"
echo -e "${YELLOW}Expires on:${NC} $(date -d "+${RETENTION_DAYS} days" +"%Y-%m-%d")"

# List recent backups
echo -e "\n${YELLOW}Recent backups:${NC}"
ls -lht "$BACKUP_DIR"/${DB_NAME}_*.sql | head -5 | awk '{print "  " $9 " (" $5 ")"}'

exit 0
