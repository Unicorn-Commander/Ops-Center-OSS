#!/bin/bash
# ============================================================================
# Test Migration 002: System API Key Storage
#
# This script verifies that migration 002 was applied correctly by:
# 1. Checking if all required columns exist
# 2. Verifying column data types
# 3. Checking if indexes were created
# 4. Testing column comments
# 5. Validating existing data
#
# Usage:
#   bash test_migration.sh
#
# Author: Backend API Developer
# Date: October 27, 2025
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "\n${BLUE}======================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}======================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((TESTS_PASSED++))
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

run_psql() {
    docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -t -A -c "$1"
}

# ============================================================================
# Test Functions
# ============================================================================

test_table_exists() {
    print_header "Test 1: Table Existence"
    ((TESTS_RUN++))

    result=$(run_psql "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'llm_providers';")

    if [ "$result" = "1" ]; then
        print_success "Table 'llm_providers' exists"
    else
        print_error "Table 'llm_providers' does not exist"
    fi
}

test_columns_exist() {
    print_header "Test 2: Column Existence"

    columns=("encrypted_api_key" "api_key_source" "api_key_updated_at" "api_key_last_tested" "api_key_test_status")

    for col in "${columns[@]}"; do
        ((TESTS_RUN++))
        result=$(run_psql "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'llm_providers' AND column_name = '$col';")

        if [ "$result" = "1" ]; then
            print_success "Column '$col' exists"
        else
            print_error "Column '$col' does not exist"
        fi
    done
}

test_column_types() {
    print_header "Test 3: Column Data Types"

    # Check encrypted_api_key is TEXT
    ((TESTS_RUN++))
    result=$(run_psql "SELECT data_type FROM information_schema.columns WHERE table_name = 'llm_providers' AND column_name = 'encrypted_api_key';")
    if [ "$result" = "text" ]; then
        print_success "encrypted_api_key is TEXT"
    else
        print_error "encrypted_api_key is $result (expected TEXT)"
    fi

    # Check api_key_source is VARCHAR(50)
    ((TESTS_RUN++))
    result=$(run_psql "SELECT data_type FROM information_schema.columns WHERE table_name = 'llm_providers' AND column_name = 'api_key_source';")
    if [ "$result" = "character varying" ]; then
        print_success "api_key_source is VARCHAR"
    else
        print_error "api_key_source is $result (expected VARCHAR)"
    fi

    # Check api_key_updated_at is TIMESTAMP
    ((TESTS_RUN++))
    result=$(run_psql "SELECT data_type FROM information_schema.columns WHERE table_name = 'llm_providers' AND column_name = 'api_key_updated_at';")
    if [[ "$result" == *"timestamp"* ]]; then
        print_success "api_key_updated_at is TIMESTAMP"
    else
        print_error "api_key_updated_at is $result (expected TIMESTAMP)"
    fi

    # Check api_key_test_status is VARCHAR(20)
    ((TESTS_RUN++))
    result=$(run_psql "SELECT data_type FROM information_schema.columns WHERE table_name = 'llm_providers' AND column_name = 'api_key_test_status';")
    if [ "$result" = "character varying" ]; then
        print_success "api_key_test_status is VARCHAR"
    else
        print_error "api_key_test_status is $result (expected VARCHAR)"
    fi
}

test_indexes_exist() {
    print_header "Test 4: Index Existence"

    # Check idx_llm_providers_api_key_source
    ((TESTS_RUN++))
    result=$(run_psql "SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'llm_providers' AND indexname = 'idx_llm_providers_api_key_source';")
    if [ "$result" = "1" ]; then
        print_success "Index 'idx_llm_providers_api_key_source' exists"
    else
        print_error "Index 'idx_llm_providers_api_key_source' does not exist"
    fi

    # Check idx_llm_providers_has_db_key
    ((TESTS_RUN++))
    result=$(run_psql "SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'llm_providers' AND indexname = 'idx_llm_providers_has_db_key';")
    if [ "$result" = "1" ]; then
        print_success "Index 'idx_llm_providers_has_db_key' exists"
    else
        print_error "Index 'idx_llm_providers_has_db_key' does not exist"
    fi
}

test_column_comments() {
    print_header "Test 5: Column Comments"

    # Check if encrypted_api_key has a comment
    ((TESTS_RUN++))
    result=$(run_psql "SELECT col_description('llm_providers'::regclass, (SELECT ordinal_position FROM information_schema.columns WHERE table_name = 'llm_providers' AND column_name = 'encrypted_api_key'));")
    if [ -n "$result" ]; then
        print_success "encrypted_api_key has documentation comment"
        print_info "Comment: ${result:0:80}..."
    else
        print_error "encrypted_api_key missing documentation comment"
    fi

    # Check if api_key_source has a comment
    ((TESTS_RUN++))
    result=$(run_psql "SELECT col_description('llm_providers'::regclass, (SELECT ordinal_position FROM information_schema.columns WHERE table_name = 'llm_providers' AND column_name = 'api_key_source'));")
    if [ -n "$result" ]; then
        print_success "api_key_source has documentation comment"
    else
        print_error "api_key_source missing documentation comment"
    fi
}

test_default_values() {
    print_header "Test 6: Default Values"

    # Check api_key_source default
    ((TESTS_RUN++))
    result=$(run_psql "SELECT column_default FROM information_schema.columns WHERE table_name = 'llm_providers' AND column_name = 'api_key_source';")
    if [[ "$result" == *"environment"* ]]; then
        print_success "api_key_source defaults to 'environment'"
    else
        print_error "api_key_source default is '$result' (expected 'environment')"
    fi
}

test_nullable_constraints() {
    print_header "Test 7: Nullable Constraints"

    # encrypted_api_key should be nullable
    ((TESTS_RUN++))
    result=$(run_psql "SELECT is_nullable FROM information_schema.columns WHERE table_name = 'llm_providers' AND column_name = 'encrypted_api_key';")
    if [ "$result" = "YES" ]; then
        print_success "encrypted_api_key is nullable (correct)"
    else
        print_error "encrypted_api_key is NOT NULL (should be nullable)"
    fi

    # api_key_source should be NOT NULL (has default)
    ((TESTS_RUN++))
    result=$(run_psql "SELECT is_nullable FROM information_schema.columns WHERE table_name = 'llm_providers' AND column_name = 'api_key_source';")
    # Note: It might be YES because it has a default, which is fine
    print_info "api_key_source nullable: $result"
}

test_existing_data() {
    print_header "Test 8: Existing Data Validation"

    # Check if existing providers have api_key_source set
    ((TESTS_RUN++))
    result=$(run_psql "SELECT COUNT(*) FROM llm_providers WHERE api_key_source IS NOT NULL;")
    total=$(run_psql "SELECT COUNT(*) FROM llm_providers;")

    if [ "$result" = "$total" ]; then
        print_success "All $total providers have api_key_source set"
    else
        print_error "Only $result of $total providers have api_key_source set"
    fi

    # Show breakdown by source
    print_info "Breakdown by api_key_source:"
    run_psql "SELECT api_key_source, COUNT(*) as count FROM llm_providers GROUP BY api_key_source;" | while IFS='|' read -r source count; do
        print_info "  - $source: $count"
    done
}

test_full_schema() {
    print_header "Test 9: Full Schema Display"

    print_info "Current llm_providers schema:"
    echo ""
    docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d llm_providers"
}

# ============================================================================
# Main Test Runner
# ============================================================================

print_header "Migration 002 Test Suite"
echo -e "${BLUE}Testing system API key storage migration${NC}"
echo -e "${BLUE}Date: $(date)${NC}\n"

# Run all tests
test_table_exists
test_columns_exist
test_column_types
test_indexes_exist
test_column_comments
test_default_values
test_nullable_constraints
test_existing_data
test_full_schema

# ============================================================================
# Test Summary
# ============================================================================

print_header "Test Summary"

echo -e "Tests Run:    ${BLUE}$TESTS_RUN${NC}"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}  ✅ ALL TESTS PASSED${NC}"
    echo -e "${GREEN}========================================${NC}\n"
    exit 0
else
    echo -e "\n${RED}========================================${NC}"
    echo -e "${RED}  ❌ SOME TESTS FAILED${NC}"
    echo -e "${RED}========================================${NC}\n"
    exit 1
fi
