#!/bin/bash
# Create New Alembic Migration Script
# Usage: ./create_migration.sh "description of changes"

set -e

# Configuration
PROJECT_DIR="/home/muut/Production/UC-Cloud/services/ops-center"
CONTAINER_NAME="ops-center-direct"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Create Alembic Migration${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if description is provided
if [ -z "$1" ]; then
    echo -e "${RED}ERROR: Migration description required${NC}"
    echo -e "${YELLOW}Usage: $0 \"description of changes\"${NC}"
    echo -e "\n${YELLOW}Examples:${NC}"
    echo -e "  $0 \"add user preferences table\""
    echo -e "  $0 \"add index to email column\""
    echo -e "  $0 \"add cascade delete to foreign keys\""
    exit 1
fi

DESCRIPTION="$1"

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}ERROR: Container '$CONTAINER_NAME' is not running${NC}"
    echo -e "${YELLOW}Start the container first: docker start $CONTAINER_NAME${NC}"
    exit 1
fi

echo -e "${YELLOW}Description:${NC} $DESCRIPTION"
echo -e "${YELLOW}Auto-generate:${NC} Yes (using SQLAlchemy models)"

# Create migration using autogenerate
echo -e "\n${YELLOW}Generating migration file...${NC}"
docker exec "$CONTAINER_NAME" bash -c "cd /app && alembic revision --autogenerate -m \"$DESCRIPTION\""

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Migration file created${NC}"
else
    echo -e "${RED}ERROR: Failed to create migration${NC}"
    exit 1
fi

# Get the latest migration file
MIGRATION_FILE=$(docker exec "$CONTAINER_NAME" bash -c "ls -t /app/alembic/versions/*.py | head -1")
echo -e "${YELLOW}Migration file:${NC} $MIGRATION_FILE"

# Show migration content
echo -e "\n${YELLOW}Migration preview:${NC}"
docker exec "$CONTAINER_NAME" cat "$MIGRATION_FILE" | head -40

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Migration Created!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Review the migration file: ${MIGRATION_FILE}"
echo -e "  2. Edit if needed (Alembic doesn't detect everything)"
echo -e "  3. Run migration: ./scripts/run_migrations.sh"
echo -e "  4. Or run dry-run first: ./scripts/run_migrations.sh --dry-run"

echo -e "\n${RED}IMPORTANT: Review the migration carefully before running!${NC}"
echo -e "${YELLOW}Alembic cannot detect:${NC}"
echo -e "  - Table or column renames"
echo -e "  - Changes to column types (sometimes)"
echo -e "  - Changes to constraints"
echo -e "  - Data migrations"

exit 0
