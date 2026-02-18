#!/bin/bash
#
# Setup Test Database for LLM Hub Development
#
# This script creates a clean test database with all required schemas and seed data.
# Safe to run multiple times - will drop and recreate database.
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DB_CONTAINER="unicorn-postgresql"
DB_USER="unicorn"
DB_NAME="unicorn_test"
DB_PASSWORD="unicorn"
MIGRATIONS_DIR="/opt/ops-center/backend/migrations"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}LLM Hub Test Database Setup${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if PostgreSQL container is running
echo -e "${YELLOW}Checking PostgreSQL container...${NC}"
if ! docker ps | grep -q ${DB_CONTAINER}; then
    echo -e "${RED}Error: PostgreSQL container '${DB_CONTAINER}' is not running${NC}"
    echo -e "${YELLOW}Start it with: docker compose up -d unicorn-postgresql${NC}"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL container is running${NC}"
echo ""

# Drop existing test database if exists
echo -e "${YELLOW}Dropping existing test database (if exists)...${NC}"
docker exec ${DB_CONTAINER} psql -U ${DB_USER} -c "DROP DATABASE IF EXISTS ${DB_NAME};" 2>/dev/null || true
echo -e "${GREEN}✓ Old database dropped${NC}"
echo ""

# Create new test database
echo -e "${YELLOW}Creating test database '${DB_NAME}'...${NC}"
docker exec ${DB_CONTAINER} psql -U ${DB_USER} -c "CREATE DATABASE ${DB_NAME};"
echo -e "${GREEN}✓ Database created${NC}"
echo ""

# Run baseline schema migration (if exists)
echo -e "${YELLOW}Running baseline schema migrations...${NC}"
if [ -f "${MIGRATIONS_DIR}/001_baseline_schema.sql" ]; then
    docker exec -i ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} < "${MIGRATIONS_DIR}/001_baseline_schema.sql"
    echo -e "${GREEN}✓ Baseline schema applied${NC}"
else
    echo -e "${YELLOW}⚠ No baseline schema found at ${MIGRATIONS_DIR}/001_baseline_schema.sql${NC}"
fi
echo ""

# Run LLM Hub schema migration
echo -e "${YELLOW}Running LLM Hub schema migrations...${NC}"
if [ -f "${MIGRATIONS_DIR}/002_llm_management_tables.sql" ]; then
    docker exec -i ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} < "${MIGRATIONS_DIR}/002_llm_management_tables.sql"
    echo -e "${GREEN}✓ LLM Hub schema applied${NC}"
else
    echo -e "${YELLOW}⚠ No LLM Hub schema found at ${MIGRATIONS_DIR}/002_llm_management_tables.sql${NC}"
fi
echo ""

# Seed tier rules
echo -e "${YELLOW}Seeding tier rules...${NC}"
if [ -f "${MIGRATIONS_DIR}/seed_tier_rules.sql" ]; then
    docker exec -i ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} < "${MIGRATIONS_DIR}/seed_tier_rules.sql"
    echo -e "${GREEN}✓ Tier rules seeded${NC}"
else
    echo -e "${YELLOW}⚠ No tier rules seed file found${NC}"
fi
echo ""

# Seed test data
echo -e "${YELLOW}Seeding test data...${NC}"
docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} <<EOF
-- Create test users
INSERT INTO users (id, keycloak_id, username, email, tier, created_at)
VALUES
    (gen_random_uuid(), 'test-admin-001', 'admin', 'admin@unicorncommander.ai', 'enterprise', NOW()),
    (gen_random_uuid(), 'test-user-001', 'testuser', 'test@example.com', 'professional', NOW()),
    (gen_random_uuid(), 'test-dev-001', 'devuser', 'admin@example.com', 'enterprise', NOW())
ON CONFLICT (email) DO NOTHING;

-- Create test provider keys (if table exists)
DO \$\$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'llm_provider_keys') THEN
        INSERT INTO llm_provider_keys (provider, api_key, user_id, is_system_key, created_at)
        SELECT
            'openai',
            'sk-test-1234567890',
            u.id,
            false,
            NOW()
        FROM users u
        WHERE u.email = 'admin@unicorncommander.ai'
        ON CONFLICT DO NOTHING;
    END IF;
END \$\$;

-- Create test models (if table exists)
DO \$\$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'llm_models') THEN
        INSERT INTO llm_models (model_id, provider, display_name, context_window, enabled, created_at)
        VALUES
            ('gpt-4', 'openai', 'GPT-4', 8192, true, NOW()),
            ('gpt-3.5-turbo', 'openai', 'GPT-3.5 Turbo', 16384, true, NOW()),
            ('claude-3-opus', 'anthropic', 'Claude 3 Opus', 200000, true, NOW())
        ON CONFLICT (model_id) DO NOTHING;
    END IF;
END \$\$;
EOF
echo -e "${GREEN}✓ Test data seeded${NC}"
echo ""

# Verify database setup
echo -e "${YELLOW}Verifying database setup...${NC}"
echo ""

echo -e "${BLUE}Tables created:${NC}"
docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c "\dt" | grep -E "table|List of relations" || echo "No tables found"
echo ""

echo -e "${BLUE}Test users created:${NC}"
docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c "SELECT username, email, tier FROM users;" 2>/dev/null || echo "Users table not found"
echo ""

echo -e "${BLUE}LLM Hub tables (if exists):${NC}"
docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c "SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'llm_%';" 2>/dev/null || echo "No LLM Hub tables found"
echo ""

# Display connection string
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✓ Test database setup complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${BLUE}Connection String:${NC}"
echo -e "postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}"
echo ""
echo -e "${BLUE}Quick Commands:${NC}"
echo -e "  Connect: ${YELLOW}docker exec -it ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME}${NC}"
echo -e "  List tables: ${YELLOW}docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c '\\dt'${NC}"
echo -e "  Drop database: ${YELLOW}docker exec ${DB_CONTAINER} psql -U ${DB_USER} -c 'DROP DATABASE ${DB_NAME};'${NC}"
echo ""
echo -e "${BLUE}Environment Variable:${NC}"
echo -e "  export DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}"
echo ""

exit 0
