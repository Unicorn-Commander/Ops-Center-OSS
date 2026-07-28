#!/bin/bash
# Show Alembic Migration Status
# Usage: ./migration_status.sh [--verbose]

set -e

# Configuration
CONTAINER_NAME="ops-center-direct"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Alembic Migration Status${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}ERROR: Container '$CONTAINER_NAME' is not running${NC}"
    exit 1
fi

# Get current migration version
echo -e "\n${CYAN}Current Migration Version:${NC}"
CURRENT_VERSION=$(docker exec "$CONTAINER_NAME" bash -c "cd /app && alembic current 2>&1" || echo "none")
if [ -z "$CURRENT_VERSION" ] || [ "$CURRENT_VERSION" == "none" ]; then
    echo -e "${YELLOW}  No migrations applied yet (clean database)${NC}"
    CURRENT_VERSION="none"
else
    echo -e "${GREEN}  $CURRENT_VERSION${NC}"
fi

# Get latest migration (head)
echo -e "\n${CYAN}Latest Migration (Head):${NC}"
HEAD_VERSION=$(docker exec "$CONTAINER_NAME" bash -c "cd /app && alembic heads 2>&1" || echo "unknown")
if [ -z "$HEAD_VERSION" ] || [ "$HEAD_VERSION" == "unknown" ]; then
    echo -e "${RED}  No migrations found${NC}"
else
    echo -e "${GREEN}  $HEAD_VERSION${NC}"
fi

# Check if up to date
echo -e "\n${CYAN}Status:${NC}"
if [ "$CURRENT_VERSION" == "$HEAD_VERSION" ] || [ "$HEAD_VERSION" == "unknown" ]; then
    echo -e "${GREEN}  ✓ Database is up to date${NC}"
    UP_TO_DATE=true
else
    echo -e "${YELLOW}  ⚠ Pending migrations available${NC}"
    UP_TO_DATE=false
fi

# Show migration history
echo -e "\n${CYAN}Migration History:${NC}"
if [ "$1" == "--verbose" ]; then
    docker exec "$CONTAINER_NAME" bash -c "cd /app && alembic history --verbose 2>&1" || echo "  No migration history"
else
    docker exec "$CONTAINER_NAME" bash -c "cd /app && alembic history 2>&1" | head -10 || echo "  No migration history"
    echo -e "${YELLOW}  (Use --verbose for full history)${NC}"
fi

# Database information
echo -e "\n${CYAN}Database Information:${NC}"
DB_NAME=$(docker exec unicorn-postgresql psql -U unicorn -t -c "SELECT current_database();" 2>/dev/null | xargs || echo "unknown")
echo -e "${YELLOW}  Database:${NC} $DB_NAME"

TABLE_COUNT=$(docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | xargs || echo "0")
echo -e "${YELLOW}  Tables:${NC} $TABLE_COUNT"

DB_SIZE=$(docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -t -c "SELECT pg_size_pretty(pg_database_size('unicorn_db'));" 2>/dev/null | xargs || echo "unknown")
echo -e "${YELLOW}  Size:${NC} $DB_SIZE"

# Alembic version table
echo -e "\n${CYAN}Alembic Version Table:${NC}"
ALEMBIC_TABLE=$(docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -t -c "SELECT version_num FROM alembic_version;" 2>/dev/null | xargs || echo "none")
if [ "$ALEMBIC_TABLE" == "none" ] || [ -z "$ALEMBIC_TABLE" ]; then
    echo -e "${YELLOW}  Not initialized (run initial migration)${NC}"
else
    echo -e "${GREEN}  $ALEMBIC_TABLE${NC}"
fi

# Summary
echo -e "\n${GREEN}========================================${NC}"
if [ "$UP_TO_DATE" == true ]; then
    echo -e "${GREEN}✓ Database is up to date${NC}"
else
    echo -e "${YELLOW}⚠ Pending migrations available${NC}"
    echo -e "${YELLOW}Run: ./scripts/run_migrations.sh${NC}"
fi
echo -e "${GREEN}========================================${NC}"

exit 0
