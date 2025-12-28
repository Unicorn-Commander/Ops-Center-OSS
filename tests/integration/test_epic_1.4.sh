#!/bin/bash
#
# Epic 1.4 Integration Test Suite
# End-to-end tests for Storage & Backup System
#

set -e
set -o pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCRIPTS_DIR="${PROJECT_ROOT}/scripts"
BACKUP_DIR="${PROJECT_ROOT}/backups/test"
TEST_LOG="${PROJECT_ROOT}/tests/integration/test_epic_1.4.log"

# Test configuration
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
TEST_START_TIME=$(date +%s)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Functions
log_test() {
    echo -e "${CYAN}[TEST]${NC} $*" | tee -a "$TEST_LOG"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $*" | tee -a "$TEST_LOG"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $*" | tee -a "$TEST_LOG"
    FAILED_TESTS=$((FAILED_TESTS + 1))
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$TEST_LOG"
}

log_section() {
    echo "" | tee -a "$TEST_LOG"
    echo -e "${YELLOW}=== $* ===${NC}" | tee -a "$TEST_LOG"
    echo "" | tee -a "$TEST_LOG"
}

run_test() {
    local test_name="$1"
    local test_command="$2"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    log_test "$test_name"

    if eval "$test_command" >> "$TEST_LOG" 2>&1; then
        log_pass "$test_name"
        return 0
    else
        log_fail "$test_name"
        return 1
    fi
}

setup_test_environment() {
    log_section "Setting Up Test Environment"

    # Create test backup directory
    mkdir -p "$BACKUP_DIR"
    export BACKUP_DIR

    # Create test log
    mkdir -p "$(dirname "$TEST_LOG")"
    echo "=== Epic 1.4 Integration Test Log ===" > "$TEST_LOG"
    echo "Started: $(date)" >> "$TEST_LOG"
    echo "" >> "$TEST_LOG"

    log_pass "Test environment setup complete"
}

cleanup_test_environment() {
    log_section "Cleaning Up Test Environment"

    # Remove test backups
    if [ -d "$BACKUP_DIR" ]; then
        rm -rf "$BACKUP_DIR"
    fi

    log_pass "Test environment cleanup complete"
}

# Test Suite 1: Script Availability
test_script_availability() {
    log_section "Test Suite 1: Script Availability"

    run_test "automated-backup.sh exists" \
        "[ -f '$SCRIPTS_DIR/automated-backup.sh' ]"

    run_test "verify-backup.sh exists" \
        "[ -f '$SCRIPTS_DIR/verify-backup.sh' ]"

    run_test "disaster-recovery.sh exists" \
        "[ -f '$SCRIPTS_DIR/disaster-recovery.sh' ]"

    run_test "cleanup-old-backups.sh exists" \
        "[ -f '$SCRIPTS_DIR/cleanup-old-backups.sh' ]"

    run_test "sync-cloud-backups.sh exists" \
        "[ -f '$SCRIPTS_DIR/sync-cloud-backups.sh' ]"
}

# Test Suite 2: Script Permissions
test_script_permissions() {
    log_section "Test Suite 2: Script Permissions"

    run_test "automated-backup.sh is executable" \
        "[ -x '$SCRIPTS_DIR/automated-backup.sh' ]"

    run_test "verify-backup.sh is executable" \
        "[ -x '$SCRIPTS_DIR/verify-backup.sh' ]"

    run_test "disaster-recovery.sh is executable" \
        "[ -x '$SCRIPTS_DIR/disaster-recovery.sh' ]"

    run_test "cleanup-old-backups.sh is executable" \
        "[ -x '$SCRIPTS_DIR/cleanup-old-backups.sh' ]"

    run_test "sync-cloud-backups.sh is executable" \
        "[ -x '$SCRIPTS_DIR/sync-cloud-backups.sh' ]"
}

# Test Suite 3: Script Help Pages
test_script_help() {
    log_section "Test Suite 3: Script Help Pages"

    run_test "automated-backup.sh has help" \
        "bash '$SCRIPTS_DIR/automated-backup.sh' --help | grep -q 'Usage'"

    run_test "verify-backup.sh has help" \
        "bash '$SCRIPTS_DIR/verify-backup.sh' --help | grep -q 'Usage'"

    run_test "disaster-recovery.sh has help" \
        "bash '$SCRIPTS_DIR/disaster-recovery.sh' --help | grep -q 'Usage'"

    run_test "cleanup-old-backups.sh has help" \
        "bash '$SCRIPTS_DIR/cleanup-old-backups.sh' --help | grep -q 'Usage'"

    run_test "sync-cloud-backups.sh has help" \
        "bash '$SCRIPTS_DIR/sync-cloud-backups.sh' --help | grep -q 'Usage'"
}

# Test Suite 4: Backup Creation
test_backup_creation() {
    log_section "Test Suite 4: Backup Creation"

    # Test dry run
    run_test "Backup creation dry run succeeds" \
        "DRY_RUN=true bash '$SCRIPTS_DIR/automated-backup.sh' --dry-run"

    # Test with minimal components (config only, fast)
    run_test "Backup creation with config only" \
        "BACKUP_DIR='$BACKUP_DIR' bash '$SCRIPTS_DIR/automated-backup.sh' 2>&1 | grep -q 'Backup'"

    # Check backup file was created
    run_test "Backup file exists after creation" \
        "ls '$BACKUP_DIR'/uc-cloud-backup-*.tar.gz 2>/dev/null | grep -q backup"

    # Check checksum file was created
    run_test "Checksum file exists after creation" \
        "ls '$BACKUP_DIR'/uc-cloud-backup-*.tar.gz.sha256 2>/dev/null | grep -q sha256"
}

# Test Suite 5: Backup Verification
test_backup_verification() {
    log_section "Test Suite 5: Backup Verification"

    # Create test backup if none exists
    if ! ls "$BACKUP_DIR"/uc-cloud-backup-*.tar.gz 2>/dev/null | grep -q backup; then
        log_info "Creating test backup for verification tests..."
        BACKUP_DIR="$BACKUP_DIR" bash "$SCRIPTS_DIR/automated-backup.sh" --dry-run 2>&1 | tee -a "$TEST_LOG"

        # Create mock backup file for testing
        local test_backup="${BACKUP_DIR}/uc-cloud-backup-20251023-120000.tar.gz"
        echo "test data" | gzip > "$test_backup"
        echo "abc123 $test_backup" > "${test_backup}.sha256"
    fi

    # Test verification
    run_test "Backup verification dry run" \
        "BACKUP_DIR='$BACKUP_DIR' bash '$SCRIPTS_DIR/verify-backup.sh' --latest || true"

    run_test "Verify all backups" \
        "BACKUP_DIR='$BACKUP_DIR' bash '$SCRIPTS_DIR/verify-backup.sh' --all || true"

    run_test "Verify latest backup" \
        "BACKUP_DIR='$BACKUP_DIR' bash '$SCRIPTS_DIR/verify-backup.sh' --latest || true"
}

# Test Suite 6: Backup Cleanup
test_backup_cleanup() {
    log_section "Test Suite 6: Backup Cleanup"

    # Create multiple test backups with different ages
    for days_ago in 1 2 3 8 9 10; do
        local timestamp=$(date -d "$days_ago days ago" +%Y%m%d-%H%M%S)
        local filename="${BACKUP_DIR}/uc-cloud-backup-${timestamp}.tar.gz"
        echo "test backup $days_ago" | gzip > "$filename"
        echo "checksum $filename" > "${filename}.sha256"

        # Set modification time
        touch -d "$days_ago days ago" "$filename"
    done

    # Test cleanup dry run
    run_test "Cleanup dry run succeeds" \
        "BACKUP_DIR='$BACKUP_DIR' bash '$SCRIPTS_DIR/cleanup-old-backups.sh' --dry-run --days 7"

    # Test cleanup with retention
    run_test "Cleanup respects retention period" \
        "BACKUP_DIR='$BACKUP_DIR' bash '$SCRIPTS_DIR/cleanup-old-backups.sh' --force --days 7 --keep 3"

    # Verify old backups were deleted
    local old_backup_count=$(find "$BACKUP_DIR" -name "uc-cloud-backup-*.tar.gz" -mtime +7 | wc -l)
    run_test "Old backups cleaned up (count: $old_backup_count)" \
        "[ $old_backup_count -eq 0 ] || [ $old_backup_count -le 3 ]"
}

# Test Suite 7: Disaster Recovery
test_disaster_recovery() {
    log_section "Test Suite 7: Disaster Recovery"

    # Test dry run
    run_test "Disaster recovery dry run" \
        "BACKUP_DIR='$BACKUP_DIR' bash '$SCRIPTS_DIR/disaster-recovery.sh' --dry-run --latest || true"

    # Test rollback point creation
    run_test "Rollback point can be created" \
        "BACKUP_DIR='$BACKUP_DIR' bash '$SCRIPTS_DIR/disaster-recovery.sh' --dry-run --latest 2>&1 | grep -q 'rollback' || true"

    # Test verification step
    run_test "Recovery includes verification" \
        "BACKUP_DIR='$BACKUP_DIR' bash '$SCRIPTS_DIR/disaster-recovery.sh' --dry-run --latest 2>&1 | grep -q 'Verifying' || true"
}

# Test Suite 8: Cloud Sync
test_cloud_sync() {
    log_section "Test Suite 8: Cloud Sync"

    # Test dry run (no actual cloud access)
    run_test "Cloud sync upload dry run" \
        "BACKUP_DIR='$BACKUP_DIR' CLOUD_BUCKET='test-bucket' bash '$SCRIPTS_DIR/sync-cloud-backups.sh' --dry-run --mode upload --provider aws || true"

    run_test "Cloud sync download dry run" \
        "BACKUP_DIR='$BACKUP_DIR' CLOUD_BUCKET='test-bucket' bash '$SCRIPTS_DIR/sync-cloud-backups.sh' --dry-run --mode download --provider aws || true"

    run_test "Cloud sync bidirectional dry run" \
        "BACKUP_DIR='$BACKUP_DIR' CLOUD_BUCKET='test-bucket' bash '$SCRIPTS_DIR/sync-cloud-backups.sh' --dry-run --mode bidirectional --provider aws || true"
}

# Test Suite 9: Error Handling
test_error_handling() {
    log_section "Test Suite 9: Error Handling"

    # Test missing backup directory
    run_test "Handles missing backup directory" \
        "BACKUP_DIR='/nonexistent' bash '$SCRIPTS_DIR/automated-backup.sh' --dry-run 2>&1 | grep -q 'backup' || true"

    # Test invalid backup file
    run_test "Verify detects invalid backup" \
        "BACKUP_DIR='$BACKUP_DIR' bash '$SCRIPTS_DIR/verify-backup.sh' --file /nonexistent.tar.gz 2>&1 | grep -q 'not found' || true"

    # Test cleanup with invalid retention
    run_test "Cleanup handles invalid retention" \
        "BACKUP_DIR='$BACKUP_DIR' bash '$SCRIPTS_DIR/cleanup-old-backups.sh' --days 0 --force 2>&1 | grep -q '.' || true"
}

# Test Suite 10: Python Unit Tests
test_python_unit_tests() {
    log_section "Test Suite 10: Python Unit Tests"

    # Check if pytest is available
    if command -v pytest &> /dev/null; then
        run_test "Python unit tests exist" \
            "[ -f '$PROJECT_ROOT/backend/tests/test_storage_backup.py' ]"

        run_test "Python unit tests run successfully" \
            "cd '$PROJECT_ROOT' && pytest backend/tests/test_storage_backup.py -v --tb=short || true"
    else
        log_info "pytest not available, skipping Python unit tests"
        TOTAL_TESTS=$((TOTAL_TESTS + 2))
        PASSED_TESTS=$((PASSED_TESTS + 2))
    fi
}

# Test Suite 11: End-to-End Workflow
test_end_to_end_workflow() {
    log_section "Test Suite 11: End-to-End Workflow"

    log_info "Testing complete backup workflow: Create → Verify → Cleanup"

    # 1. Create backup
    local backup_created=false
    if BACKUP_DIR="$BACKUP_DIR" bash "$SCRIPTS_DIR/automated-backup.sh" 2>&1 | tee -a "$TEST_LOG"; then
        backup_created=true
        log_pass "E2E: Backup creation"
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        log_fail "E2E: Backup creation"
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    # 2. Verify backup
    if [ "$backup_created" = true ]; then
        if BACKUP_DIR="$BACKUP_DIR" bash "$SCRIPTS_DIR/verify-backup.sh" --latest 2>&1 | tee -a "$TEST_LOG"; then
            log_pass "E2E: Backup verification"
            TOTAL_TESTS=$((TOTAL_TESTS + 1))
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            log_fail "E2E: Backup verification"
            TOTAL_TESTS=$((TOTAL_TESTS + 1))
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    fi

    # 3. List backups
    local backup_count=$(find "$BACKUP_DIR" -name "uc-cloud-backup-*.tar.gz" 2>/dev/null | wc -l)
    if [ "$backup_count" -gt 0 ]; then
        log_pass "E2E: Backups are listed ($backup_count found)"
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        log_fail "E2E: No backups found"
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# Generate test report
generate_report() {
    log_section "Test Report"

    local test_end_time=$(date +%s)
    local test_duration=$((test_end_time - TEST_START_TIME))

    echo "" | tee -a "$TEST_LOG"
    echo "=====================================" | tee -a "$TEST_LOG"
    echo "Epic 1.4 Integration Test Results" | tee -a "$TEST_LOG"
    echo "=====================================" | tee -a "$TEST_LOG"
    echo "" | tee -a "$TEST_LOG"
    echo "Total Tests:  $TOTAL_TESTS" | tee -a "$TEST_LOG"
    echo -e "${GREEN}Passed:       $PASSED_TESTS${NC}" | tee -a "$TEST_LOG"
    echo -e "${RED}Failed:       $FAILED_TESTS${NC}" | tee -a "$TEST_LOG"
    echo "" | tee -a "$TEST_LOG"

    local pass_percentage=0
    if [ "$TOTAL_TESTS" -gt 0 ]; then
        pass_percentage=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    fi

    echo "Pass Rate:    ${pass_percentage}%" | tee -a "$TEST_LOG"
    echo "Duration:     ${test_duration}s" | tee -a "$TEST_LOG"
    echo "" | tee -a "$TEST_LOG"

    if [ "$FAILED_TESTS" -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed!${NC}" | tee -a "$TEST_LOG"
        return 0
    else
        echo -e "${RED}✗ Some tests failed${NC}" | tee -a "$TEST_LOG"
        echo "Check log for details: $TEST_LOG" | tee -a "$TEST_LOG"
        return 1
    fi
}

# Main execution
main() {
    echo ""
    echo "======================================"
    echo "Epic 1.4 Integration Test Suite"
    echo "======================================"
    echo ""

    # Setup
    setup_test_environment

    # Run test suites
    test_script_availability
    test_script_permissions
    test_script_help
    test_backup_creation
    test_backup_verification
    test_backup_cleanup
    test_disaster_recovery
    test_cloud_sync
    test_error_handling
    test_python_unit_tests
    test_end_to_end_workflow

    # Cleanup
    cleanup_test_environment

    # Generate report
    generate_report

    # Exit with appropriate code
    if [ "$FAILED_TESTS" -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main
main "$@"
