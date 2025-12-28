#!/bin/bash

################################################################################
# Epic 1.8 - Credit System Database Migration Script
#
# This script safely applies the credit system database schema with:
# - Automatic backup before migration
# - Rollback capability on failure
# - Verification of migration success
# - Seed data for development environment
#
# Author: Testing & DevOps Team Lead
# Date: October 23, 2025
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="unicorn-postgresql"
DB_USER="unicorn"
DB_NAME="unicorn_db"
BACKUP_DIR="/tmp/ops-center-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/credit_system_backup_${TIMESTAMP}.sql"
MIGRATION_SQL="/app/backend/migrations/create_credit_system_tables.sql"

# Environment detection
ENVIRONMENT=${ENVIRONMENT:-"production"}

################################################################################
# Helper Functions
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if PostgreSQL container is running
    if ! docker ps | grep -q ${CONTAINER_NAME}; then
        log_error "PostgreSQL container '${CONTAINER_NAME}' is not running"
        exit 1
    fi

    # Check if migration SQL exists
    if [ ! -f "${MIGRATION_SQL}" ]; then
        log_error "Migration SQL file not found: ${MIGRATION_SQL}"
        exit 1
    fi

    # Create backup directory
    mkdir -p ${BACKUP_DIR}

    log_success "Prerequisites check passed"
}

create_backup() {
    log_info "Creating database backup..."

    docker exec ${CONTAINER_NAME} pg_dump \
        -U ${DB_USER} \
        -d ${DB_NAME} \
        --clean \
        --if-exists \
        > ${BACKUP_FILE}

    if [ $? -eq 0 ]; then
        BACKUP_SIZE=$(du -h ${BACKUP_FILE} | cut -f1)
        log_success "Backup created: ${BACKUP_FILE} (${BACKUP_SIZE})"
    else
        log_error "Backup failed"
        exit 1
    fi
}

apply_migration() {
    log_info "Applying credit system migration..."

    # Copy migration SQL to container
    docker cp ${MIGRATION_SQL} ${CONTAINER_NAME}:/tmp/migration.sql

    # Apply migration
    docker exec -i ${CONTAINER_NAME} psql \
        -U ${DB_USER} \
        -d ${DB_NAME} \
        -f /tmp/migration.sql

    if [ $? -eq 0 ]; then
        log_success "Migration applied successfully"
    else
        log_error "Migration failed"
        return 1
    fi
}

verify_tables() {
    log_info "Verifying tables..."

    EXPECTED_TABLES=(
        "user_credits"
        "credit_transactions"
        "openrouter_accounts"
        "coupon_codes"
        "usage_events"
    )

    for table in "${EXPECTED_TABLES[@]}"; do
        TABLE_EXISTS=$(docker exec ${CONTAINER_NAME} psql \
            -U ${DB_USER} \
            -d ${DB_NAME} \
            -t \
            -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='${table}';")

        if [ "${TABLE_EXISTS}" -eq 1 ]; then
            log_success "✓ Table '${table}' exists"
        else
            log_error "✗ Table '${table}' not found"
            return 1
        fi
    done

    log_success "All tables verified"
}

verify_indexes() {
    log_info "Verifying indexes..."

    EXPECTED_INDEXES=(
        "idx_user_credits_user_id"
        "idx_credit_transactions_user_id"
        "idx_credit_transactions_created_at"
        "idx_openrouter_accounts_user_id"
        "idx_coupon_codes_code"
        "idx_usage_events_user_id"
    )

    for index in "${EXPECTED_INDEXES[@]}"; do
        INDEX_EXISTS=$(docker exec ${CONTAINER_NAME} psql \
            -U ${DB_USER} \
            -d ${DB_NAME} \
            -t \
            -c "SELECT COUNT(*) FROM pg_indexes WHERE indexname='${index}';")

        if [ "${INDEX_EXISTS}" -eq 1 ]; then
            log_success "✓ Index '${index}' exists"
        else
            log_warning "⚠ Index '${index}' not found (may be optional)"
        fi
    done
}

seed_development_data() {
    if [ "${ENVIRONMENT}" != "production" ]; then
        log_info "Seeding development test data..."

        # Seed test coupons
        docker exec -i ${CONTAINER_NAME} psql \
            -U ${DB_USER} \
            -d ${DB_NAME} \
            -c "INSERT INTO coupon_codes (code, discount_type, discount_value, max_uses, expires_at) VALUES
                ('WELCOME100', 'fixed', 100.00, 1000, NOW() + INTERVAL '30 days'),
                ('SAVE50', 'percentage', 50, 500, NOW() + INTERVAL '60 days'),
                ('TEST10', 'fixed', 10.00, 100, NOW() + INTERVAL '7 days')
                ON CONFLICT (code) DO NOTHING;"

        # Seed test user credits
        docker exec -i ${CONTAINER_NAME} psql \
            -U ${DB_USER} \
            -d ${DB_NAME} \
            -c "INSERT INTO user_credits (user_id, credits_remaining, tier) VALUES
                ('test@example.com', 100.00, 'professional'),
                ('admin@example.com', 1000.00, 'enterprise')
                ON CONFLICT (user_id) DO NOTHING;"

        log_success "Development data seeded"
    fi
}

rollback_migration() {
    log_warning "Rolling back migration..."

    if [ -f "${BACKUP_FILE}" ]; then
        docker exec -i ${CONTAINER_NAME} psql \
            -U ${DB_USER} \
            -d ${DB_NAME} \
            < ${BACKUP_FILE}

        if [ $? -eq 0 ]; then
            log_success "Rollback completed successfully"
        else
            log_error "Rollback failed - manual intervention required"
            log_error "Backup file: ${BACKUP_FILE}"
        fi
    else
        log_error "Backup file not found - cannot rollback"
    fi
}

cleanup() {
    # Remove temporary migration file from container
    docker exec ${CONTAINER_NAME} rm -f /tmp/migration.sql 2>/dev/null || true

    log_info "Backup retained at: ${BACKUP_FILE}"
}

print_summary() {
    echo ""
    echo "=========================================="
    echo "    MIGRATION SUMMARY"
    echo "=========================================="
    echo "Environment:    ${ENVIRONMENT}"
    echo "Database:       ${DB_NAME}"
    echo "Backup:         ${BACKUP_FILE}"
    echo "Timestamp:      $(date)"
    echo "=========================================="
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    echo ""
    echo "=========================================="
    echo "  Epic 1.8 Credit System Migration"
    echo "=========================================="
    echo ""

    # Step 1: Prerequisites
    check_prerequisites

    # Step 2: Create backup
    create_backup

    # Step 3: Apply migration
    if apply_migration; then
        # Step 4: Verify migration
        if verify_tables && verify_indexes; then
            # Step 5: Seed development data
            seed_development_data

            # Success
            log_success "Migration completed successfully!"
            print_summary
            cleanup
            exit 0
        else
            # Verification failed
            log_error "Migration verification failed"
            rollback_migration
            cleanup
            exit 1
        fi
    else
        # Migration failed
        log_error "Migration application failed"
        rollback_migration
        cleanup
        exit 1
    fi
}

# Trap errors and perform cleanup
trap 'log_error "Script failed on line $LINENO"; cleanup; exit 1' ERR

# Run main function
main "$@"
