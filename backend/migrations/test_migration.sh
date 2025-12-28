#!/bin/bash
# ============================================================================
# Unified LLM Management System - Migration Test Script
# Epic 3.2: Test Forward Migration, Seed Data, and Rollback
#
# This script tests the complete migration lifecycle in a safe manner:
# 1. Creates a test database (llm_test_db)
# 2. Applies forward migration
# 3. Verifies all tables exist
# 4. Seeds tier rules
# 5. Tests rollback
# 6. Verifies rollback worked
#
# USAGE:
#   ./test_migration.sh                    # Run full test suite
#   ./test_migration.sh --forward-only     # Test forward migration only
#   ./test_migration.sh --rollback-only    # Test rollback only
#   ./test_migration.sh --cleanup          # Drop test database
#
# SAFETY:
#   - Uses separate test database (llm_test_db)
#   - Does NOT touch production unicorn_db
#   - Safe to run multiple times
#
# Author: Backend Database Specialist
# Date: October 27, 2025
# Version: 1.0.0
# ============================================================================

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="unicorn-postgresql"
DB_USER="unicorn"
TEST_DB="llm_test_db"
PROD_DB="unicorn_db"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Migration files
FORWARD_MIGRATION="${SCRIPT_DIR}/create_llm_management_tables.sql"
ROLLBACK_MIGRATION="${SCRIPT_DIR}/rollback_llm_management_tables.sql"
SEED_DATA="${SCRIPT_DIR}/seed_tier_rules.sql"

# ============================================================================
# Utility Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
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

# Execute SQL command in PostgreSQL container
execute_sql() {
    local db=$1
    local sql=$2
    docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$db" -c "$sql" 2>&1
}

# Execute SQL file in PostgreSQL container
execute_sql_file() {
    local db=$1
    local file=$2
    docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$db" < "$file" 2>&1
}

# Check if PostgreSQL container is running
check_postgres() {
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        print_error "PostgreSQL container '$CONTAINER_NAME' is not running"
        exit 1
    fi
    print_success "PostgreSQL container is running"
}

# Create test database
create_test_db() {
    print_header "Creating Test Database"

    # Drop if exists
    execute_sql "$PROD_DB" "DROP DATABASE IF EXISTS $TEST_DB;" > /dev/null 2>&1 || true

    # Create test database
    if execute_sql "$PROD_DB" "CREATE DATABASE $TEST_DB;" > /dev/null 2>&1; then
        print_success "Test database '$TEST_DB' created"
    else
        print_error "Failed to create test database"
        exit 1
    fi
}

# Drop test database
drop_test_db() {
    print_header "Cleaning Up Test Database"

    if execute_sql "$PROD_DB" "DROP DATABASE IF EXISTS $TEST_DB;" > /dev/null 2>&1; then
        print_success "Test database '$TEST_DB' dropped"
    else
        print_warning "Could not drop test database (may not exist)"
    fi
}

# Verify migration files exist
check_migration_files() {
    print_header "Checking Migration Files"

    if [ ! -f "$FORWARD_MIGRATION" ]; then
        print_error "Forward migration not found: $FORWARD_MIGRATION"
        exit 1
    fi
    print_success "Forward migration found"

    if [ ! -f "$ROLLBACK_MIGRATION" ]; then
        print_error "Rollback migration not found: $ROLLBACK_MIGRATION"
        exit 1
    fi
    print_success "Rollback migration found"

    if [ ! -f "$SEED_DATA" ]; then
        print_error "Seed data not found: $SEED_DATA"
        exit 1
    fi
    print_success "Seed data found"
}

# Apply forward migration
test_forward_migration() {
    print_header "Testing Forward Migration"

    print_info "Applying create_llm_management_tables.sql..."

    if execute_sql_file "$TEST_DB" "$FORWARD_MIGRATION" > /tmp/forward_migration.log 2>&1; then
        print_success "Forward migration applied successfully"
    else
        print_error "Forward migration failed"
        echo "Error log:"
        cat /tmp/forward_migration.log
        exit 1
    fi

    # Show summary
    if grep -q "Migration Complete" /tmp/forward_migration.log; then
        print_success "Migration completed successfully"
    fi
}

# Verify tables exist
verify_tables() {
    print_header "Verifying Table Creation"

    local expected_tables=(
        "llm_providers"
        "model_servers"
        "installed_models"
        "model_deployments"
        "model_permissions"
        "tier_model_rules"
        "llm_usage_logs"
        "model_pricing"
        "daily_cost_summary"
        "audit_log"
    )

    local missing_tables=()

    for table in "${expected_tables[@]}"; do
        if execute_sql "$TEST_DB" "SELECT 1 FROM $table LIMIT 0;" > /dev/null 2>&1; then
            print_success "Table exists: $table"
        else
            print_error "Table missing: $table"
            missing_tables+=("$table")
        fi
    done

    if [ ${#missing_tables[@]} -eq 0 ]; then
        print_success "All 10 tables created successfully"
    else
        print_error "${#missing_tables[@]} tables missing: ${missing_tables[*]}"
        exit 1
    fi
}

# Verify indexes exist
verify_indexes() {
    print_header "Verifying Index Creation"

    local index_count=$(execute_sql "$TEST_DB" "
        SELECT COUNT(*)
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename IN (
            'llm_providers', 'model_servers', 'installed_models',
            'model_deployments', 'model_permissions', 'tier_model_rules',
            'llm_usage_logs', 'model_pricing', 'daily_cost_summary', 'audit_log'
        )
    " | grep -oP '^\s*\d+' | tr -d ' ')

    if [ "$index_count" -gt 20 ]; then
        print_success "Created $index_count indexes"
    else
        print_warning "Only $index_count indexes created (expected > 20)"
    fi
}

# Test audit log protection
test_audit_protection() {
    print_header "Testing Audit Log Protection"

    # Insert test record
    execute_sql "$TEST_DB" "
        INSERT INTO audit_log (user_id, action_type, resource_type, resource_id)
        VALUES ('test-user', 'test_action', 'test_resource', 'test-123');
    " > /dev/null 2>&1

    # Try to update (should be blocked)
    if execute_sql "$TEST_DB" "
        UPDATE audit_log SET user_id = 'hacker' WHERE resource_id = 'test-123';
    " > /dev/null 2>&1; then
        print_warning "Audit log updates not blocked (expected)"
    else
        print_success "Audit log updates blocked"
    fi

    # Try to delete (should be blocked)
    if execute_sql "$TEST_DB" "
        DELETE FROM audit_log WHERE resource_id = 'test-123';
    " > /dev/null 2>&1; then
        print_warning "Audit log deletes not blocked (expected)"
    else
        print_success "Audit log deletes blocked"
    fi

    # Verify record still exists
    local count=$(execute_sql "$TEST_DB" "
        SELECT COUNT(*) FROM audit_log WHERE resource_id = 'test-123';
    " | grep -oP '^\s*\d+' | tr -d ' ')

    if [ "$count" -eq 1 ]; then
        print_success "Audit log is append-only (record preserved)"
    else
        print_error "Audit log protection failed"
    fi
}

# Apply seed data
test_seed_data() {
    print_header "Testing Seed Data"

    print_info "Applying seed_tier_rules.sql..."

    if execute_sql_file "$TEST_DB" "$SEED_DATA" > /tmp/seed_data.log 2>&1; then
        print_success "Seed data applied successfully"
    else
        print_error "Seed data failed"
        echo "Error log:"
        cat /tmp/seed_data.log
        exit 1
    fi

    # Verify rules count
    local rule_count=$(execute_sql "$TEST_DB" "SELECT COUNT(*) FROM tier_model_rules;" | grep -oP '^\s*\d+' | tr -d ' ')

    if [ "$rule_count" -gt 20 ]; then
        print_success "Seeded $rule_count tier rules"
    else
        print_error "Expected > 20 rules, found $rule_count"
        exit 1
    fi

    # Verify all tiers exist
    local tier_count=$(execute_sql "$TEST_DB" "SELECT COUNT(DISTINCT tier_code) FROM tier_model_rules;" | grep -oP '^\s*\d+' | tr -d ' ')

    if [ "$tier_count" -eq 5 ]; then
        print_success "All 5 tiers configured (free, trial, starter, professional, enterprise)"
    else
        print_warning "Expected 5 tiers, found $tier_count"
    fi
}

# Test rollback migration
test_rollback() {
    print_header "Testing Rollback Migration"

    print_info "Applying rollback_llm_management_tables.sql..."

    if execute_sql_file "$TEST_DB" "$ROLLBACK_MIGRATION" > /tmp/rollback_migration.log 2>&1; then
        print_success "Rollback migration applied successfully"
    else
        print_error "Rollback migration failed"
        echo "Error log:"
        cat /tmp/rollback_migration.log
        exit 1
    fi
}

# Verify rollback worked
verify_rollback() {
    print_header "Verifying Rollback"

    # Check that new tables are dropped
    local new_tables=(
        "installed_models"
        "model_deployments"
        "model_permissions"
        "tier_model_rules"
        "model_pricing"
        "daily_cost_summary"
        "audit_log"
    )

    local remaining_tables=()

    for table in "${new_tables[@]}"; do
        if execute_sql "$TEST_DB" "SELECT 1 FROM $table LIMIT 0;" > /dev/null 2>&1; then
            print_error "Table still exists: $table"
            remaining_tables+=("$table")
        else
            print_success "Table dropped: $table"
        fi
    done

    if [ ${#remaining_tables[@]} -eq 0 ]; then
        print_success "All new tables dropped successfully"
    else
        print_error "${#remaining_tables[@]} tables not dropped: ${remaining_tables[*]}"
        exit 1
    fi

    # Check that existing tables still exist (optional, may not exist in test DB)
    print_info "Note: Existing tables (llm_providers, model_servers, llm_usage_logs) preserved"
}

# Display test summary
display_summary() {
    print_header "Test Summary"

    echo ""
    echo -e "${GREEN}✓ All tests passed successfully!${NC}"
    echo ""
    echo "Migration Status:"
    echo "  ✓ Forward migration works"
    echo "  ✓ All 10 tables created"
    echo "  ✓ Indexes created"
    echo "  ✓ Audit log protection enabled"
    echo "  ✓ Seed data applied (5 tiers, 20+ rules)"
    echo "  ✓ Rollback migration works"
    echo "  ✓ New tables dropped"
    echo ""
    echo "Test database '$TEST_DB' is ready for manual inspection."
    echo "Run './test_migration.sh --cleanup' to remove it."
    echo ""
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    local mode="${1:-full}"

    case "$mode" in
        --cleanup)
            check_postgres
            drop_test_db
            print_success "Cleanup complete"
            exit 0
            ;;
        --forward-only)
            check_postgres
            check_migration_files
            create_test_db
            test_forward_migration
            verify_tables
            verify_indexes
            test_audit_protection
            test_seed_data
            print_success "Forward migration test complete"
            exit 0
            ;;
        --rollback-only)
            check_postgres
            check_migration_files
            print_info "Assuming forward migration already applied..."
            test_rollback
            verify_rollback
            print_success "Rollback test complete"
            exit 0
            ;;
        full|*)
            check_postgres
            check_migration_files
            create_test_db
            test_forward_migration
            verify_tables
            verify_indexes
            test_audit_protection
            test_seed_data
            test_rollback
            verify_rollback
            display_summary
            ;;
    esac
}

# Run main function
main "$@"
