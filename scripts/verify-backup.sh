#!/bin/bash
#
# UC-Cloud Backup Verification Script
# Verifies integrity and completeness of backup archives
#

set -e
set -o pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-${PROJECT_ROOT}/backups}"
LOG_FILE="${LOG_FILE:-/var/log/uc-cloud-backup-verify.log}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Exit codes
EXIT_SUCCESS=0
EXIT_VERIFY_FAILED=1
EXIT_CHECKSUM_FAILED=2
EXIT_EXTRACT_FAILED=3
EXIT_CORRUPTED=4

# Functions
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO" "$@"
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    log "SUCCESS" "$@"
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    log "WARNING" "$@"
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    log "ERROR" "$@"
    echo -e "${RED}[ERROR]${NC} $*"
}

show_help() {
    cat <<EOF
UC-Cloud Backup Verification Script

Usage: $0 [OPTIONS] [BACKUP_FILE]

Options:
    -a, --all              Verify all backups in backup directory
    -l, --latest           Verify latest backup only
    -f, --file PATH        Verify specific backup file
    -e, --extract          Test extraction (dry run)
    -c, --checksum         Verify checksum only
    -v, --verbose          Enable verbose output
    -h, --help             Show this help message

Environment Variables:
    BACKUP_DIR             Backup directory path
    LOG_FILE               Log file path

Exit Codes:
    0   All verifications passed
    1   Verification failed
    2   Checksum verification failed
    3   Extraction test failed
    4   Backup is corrupted

Examples:
    # Verify latest backup
    $0 --latest

    # Verify all backups
    $0 --all

    # Verify specific backup
    $0 --file /path/to/backup.tar.gz

    # Verify with extraction test
    $0 --latest --extract

EOF
}

find_latest_backup() {
    find "$BACKUP_DIR" -name "uc-cloud-backup-*.tar.gz" -type f -printf '%T@ %p\n' | \
        sort -rn | head -1 | cut -d' ' -f2
}

find_all_backups() {
    find "$BACKUP_DIR" -name "uc-cloud-backup-*.tar.gz" -type f | sort
}

verify_checksum() {
    local backup_file="$1"
    local checksum_file="${backup_file}.sha256"

    log_info "Verifying checksum for: $(basename "$backup_file")"

    if [ ! -f "$checksum_file" ]; then
        log_warning "Checksum file not found: $checksum_file"
        return 1
    fi

    local expected_checksum=$(cut -d' ' -f1 "$checksum_file")
    local actual_checksum=$(sha256sum "$backup_file" | cut -d' ' -f1)

    if [ "$expected_checksum" = "$actual_checksum" ]; then
        log_success "Checksum verification passed"
        return 0
    else
        log_error "Checksum mismatch!"
        log_error "Expected: $expected_checksum"
        log_error "Actual:   $actual_checksum"
        return 1
    fi
}

verify_archive_integrity() {
    local backup_file="$1"

    log_info "Verifying archive integrity: $(basename "$backup_file")"

    if ! tar -tzf "$backup_file" > /dev/null 2>&1; then
        log_error "Archive integrity check failed - file may be corrupted"
        return 1
    fi

    log_success "Archive integrity verified"
    return 0
}

verify_archive_contents() {
    local backup_file="$1"

    log_info "Verifying archive contents..."

    local contents=$(tar -tzf "$backup_file" 2>/dev/null)
    local file_count=$(echo "$contents" | wc -l)

    if [ "$file_count" -eq 0 ]; then
        log_error "Archive is empty"
        return 1
    fi

    log_success "Archive contains $file_count files/directories"

    # Check for expected components
    local has_volumes=false
    local has_config=false
    local has_database=false

    if echo "$contents" | grep -q "volumes"; then
        has_volumes=true
        log_info "  ✓ Volumes backup present"
    fi

    if echo "$contents" | grep -q "config"; then
        has_config=true
        log_info "  ✓ Configuration backup present"
    fi

    if echo "$contents" | grep -q "postgres\|redis"; then
        has_database=true
        log_info "  ✓ Database backup present"
    fi

    if [ "$has_volumes" = false ] && [ "$has_config" = false ] && [ "$has_database" = false ]; then
        log_warning "No recognized backup components found"
    fi

    return 0
}

test_extraction() {
    local backup_file="$1"

    log_info "Testing extraction (dry run)..."

    local temp_dir=$(mktemp -d)
    trap "rm -rf $temp_dir" EXIT

    if tar -xzf "$backup_file" -C "$temp_dir" 2>&1 | tee -a "$LOG_FILE"; then
        local extracted_size=$(du -sh "$temp_dir" | cut -f1)
        log_success "Extraction test passed (extracted size: $extracted_size)"
        rm -rf "$temp_dir"
        return 0
    else
        log_error "Extraction test failed"
        rm -rf "$temp_dir"
        return 1
    fi
}

get_backup_info() {
    local backup_file="$1"

    log_info "Backup Information:"
    log_info "  File: $(basename "$backup_file")"
    log_info "  Size: $(du -h "$backup_file" | cut -f1)"
    log_info "  Date: $(stat -c %y "$backup_file" | cut -d'.' -f1)"

    if [ -f "${backup_file}.sha256" ]; then
        log_info "  Checksum: $(cut -d' ' -f1 "${backup_file}.sha256")"
    fi
}

verify_single_backup() {
    local backup_file="$1"
    local do_checksum="${2:-true}"
    local do_extract="${3:-false}"
    local failed=false

    log_info "=== Verifying Backup ==="

    # Get backup info
    get_backup_info "$backup_file"

    # Verify checksum
    if [ "$do_checksum" = "true" ]; then
        if ! verify_checksum "$backup_file"; then
            failed=true
        fi
    fi

    # Verify archive integrity
    if ! verify_archive_integrity "$backup_file"; then
        log_error "Backup is corrupted: $backup_file"
        return $EXIT_CORRUPTED
    fi

    # Verify contents
    if ! verify_archive_contents "$backup_file"; then
        failed=true
    fi

    # Test extraction
    if [ "$do_extract" = "true" ]; then
        if ! test_extraction "$backup_file"; then
            failed=true
        fi
    fi

    # Summary
    if [ "$failed" = "true" ]; then
        log_error "=== Verification FAILED ==="
        return $EXIT_VERIFY_FAILED
    else
        log_success "=== Verification PASSED ==="
        return $EXIT_SUCCESS
    fi
}

# Parse command line arguments
VERIFY_MODE="latest"
DO_EXTRACT=false
DO_CHECKSUM=true
BACKUP_FILE=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--all)
            VERIFY_MODE="all"
            shift
            ;;
        -l|--latest)
            VERIFY_MODE="latest"
            shift
            ;;
        -f|--file)
            VERIFY_MODE="file"
            BACKUP_FILE="$2"
            shift 2
            ;;
        -e|--extract)
            DO_EXTRACT=true
            shift
            ;;
        -c|--checksum)
            DO_CHECKSUM=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            # Assume it's a backup file path
            VERIFY_MODE="file"
            BACKUP_FILE="$1"
            shift
            ;;
    esac
done

# Main execution
main() {
    log_info "=== UC-Cloud Backup Verification Started ==="

    case "$VERIFY_MODE" in
        latest)
            log_info "Verifying latest backup..."
            BACKUP_FILE=$(find_latest_backup)

            if [ -z "$BACKUP_FILE" ]; then
                log_error "No backups found in: $BACKUP_DIR"
                exit $EXIT_VERIFY_FAILED
            fi

            verify_single_backup "$BACKUP_FILE" "$DO_CHECKSUM" "$DO_EXTRACT"
            exit $?
            ;;

        all)
            log_info "Verifying all backups..."
            local backups=$(find_all_backups)

            if [ -z "$backups" ]; then
                log_error "No backups found in: $BACKUP_DIR"
                exit $EXIT_VERIFY_FAILED
            fi

            local total=0
            local passed=0
            local failed=0

            while IFS= read -r backup_file; do
                total=$((total + 1))
                echo ""
                log_info "Verifying backup $total: $(basename "$backup_file")"

                if verify_single_backup "$backup_file" "$DO_CHECKSUM" "$DO_EXTRACT"; then
                    passed=$((passed + 1))
                else
                    failed=$((failed + 1))
                fi
            done <<< "$backups"

            echo ""
            log_info "=== Verification Summary ==="
            log_info "Total backups: $total"
            log_success "Passed: $passed"
            if [ $failed -gt 0 ]; then
                log_error "Failed: $failed"
                exit $EXIT_VERIFY_FAILED
            fi

            log_success "=== All Verifications Passed ==="
            exit $EXIT_SUCCESS
            ;;

        file)
            if [ -z "$BACKUP_FILE" ]; then
                log_error "No backup file specified"
                show_help
                exit $EXIT_VERIFY_FAILED
            fi

            if [ ! -f "$BACKUP_FILE" ]; then
                log_error "Backup file not found: $BACKUP_FILE"
                exit $EXIT_VERIFY_FAILED
            fi

            verify_single_backup "$BACKUP_FILE" "$DO_CHECKSUM" "$DO_EXTRACT"
            exit $?
            ;;

        *)
            log_error "Invalid verification mode: $VERIFY_MODE"
            show_help
            exit $EXIT_VERIFY_FAILED
            ;;
    esac
}

# Run main function
main
