#!/bin/bash
#
# UC-Cloud Backup Cleanup Script
# Removes old backups while maintaining retention policy
#

set -e
set -o pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-${PROJECT_ROOT}/backups}"
LOG_FILE="${LOG_FILE:-/var/log/uc-cloud-backup-cleanup.log}"

# Retention settings
RETENTION_DAYS="${RETENTION_DAYS:-7}"
MIN_BACKUPS_KEEP="${MIN_BACKUPS_KEEP:-3}"

# Flags
DRY_RUN=false
FORCE=false
VERBOSE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
    [ "$VERBOSE" = "true" ] && echo -e "${BLUE}[INFO]${NC} $*"
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
UC-Cloud Backup Cleanup Script

Usage: $0 [OPTIONS]

Options:
    -d, --days N           Retention period in days (default: 7)
    -k, --keep N           Minimum backups to keep (default: 3)
    -n, --dry-run          Show what would be deleted
    -f, --force            Skip confirmation
    -v, --verbose          Enable verbose output
    -h, --help             Show this help message

Environment Variables:
    BACKUP_DIR             Backup directory path
    RETENTION_DAYS         Retention period in days
    MIN_BACKUPS_KEEP       Minimum backups to keep
    LOG_FILE               Log file path

Examples:
    # Dry run to see what would be deleted
    $0 --dry-run

    # Delete backups older than 30 days, keep at least 5
    $0 --days 30 --keep 5

    # Force cleanup without confirmation
    $0 --force

EOF
}

format_size() {
    local size=$1
    if [ "$size" -lt 1024 ]; then
        echo "${size}B"
    elif [ "$size" -lt 1048576 ]; then
        echo "$(( size / 1024 ))KB"
    elif [ "$size" -lt 1073741824 ]; then
        echo "$(( size / 1048576 ))MB"
    else
        echo "$(( size / 1073741824 ))GB"
    fi
}

find_old_backups() {
    find "$BACKUP_DIR" -name "uc-cloud-backup-*.tar.gz" -type f -mtime +"$RETENTION_DAYS" -printf '%T@ %p %s\n' | sort -rn
}

find_all_backups() {
    find "$BACKUP_DIR" -name "uc-cloud-backup-*.tar.gz" -type f -printf '%T@ %p %s\n' | sort -rn
}

count_backups() {
    find "$BACKUP_DIR" -name "uc-cloud-backup-*.tar.gz" -type f | wc -l
}

delete_backup() {
    local backup_file="$1"
    local checksum_file="${backup_file}.sha256"

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would delete: $(basename "$backup_file")"
    else
        log_info "Deleting: $(basename "$backup_file")"
        rm -f "$backup_file"

        if [ -f "$checksum_file" ]; then
            rm -f "$checksum_file"
        fi

        log_success "Deleted: $(basename "$backup_file")"
    fi
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--days)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        -k|--keep)
            MIN_BACKUPS_KEEP="$2"
            shift 2
            ;;
        -n|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -f|--force)
            FORCE=true
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
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main
main() {
    log_info "=== UC-Cloud Backup Cleanup Started ==="
    log_info "Backup directory: $BACKUP_DIR"
    log_info "Retention period: $RETENTION_DAYS days"
    log_info "Minimum backups to keep: $MIN_BACKUPS_KEEP"

    if [ ! -d "$BACKUP_DIR" ]; then
        log_error "Backup directory not found: $BACKUP_DIR"
        exit 1
    fi

    # Count total backups
    local total_backups=$(count_backups)
    log_info "Total backups found: $total_backups"

    if [ "$total_backups" -eq 0 ]; then
        log_info "No backups to clean up"
        exit 0
    fi

    # Find old backups
    local old_backups=$(find_old_backups)
    local old_count=$(echo "$old_backups" | grep -c . || echo 0)

    if [ "$old_count" -eq 0 ]; then
        log_info "No backups older than $RETENTION_DAYS days"
        exit 0
    fi

    log_info "Found $old_count backups older than $RETENTION_DAYS days"

    # Check minimum retention
    local remaining=$((total_backups - old_count))

    if [ "$remaining" -lt "$MIN_BACKUPS_KEEP" ]; then
        local can_delete=$((total_backups - MIN_BACKUPS_KEEP))

        if [ "$can_delete" -le 0 ]; then
            log_warning "Cannot delete any backups (would violate minimum retention of $MIN_BACKUPS_KEEP)"
            exit 0
        fi

        log_warning "Only $can_delete backups can be deleted (minimum retention: $MIN_BACKUPS_KEEP)"

        # Trim list to only delete allowed amount
        old_backups=$(echo "$old_backups" | head -n "$can_delete")
        old_count=$can_delete
    fi

    # Calculate space to be freed
    local total_size=0
    while IFS= read -r line; do
        local size=$(echo "$line" | awk '{print $3}')
        total_size=$((total_size + size))
    done <<< "$old_backups"

    local size_formatted=$(format_size "$total_size")

    log_info "Space to be freed: $size_formatted"

    # Show backups to be deleted
    echo ""
    log_info "Backups to be deleted:"
    while IFS= read -r line; do
        local timestamp=$(echo "$line" | awk '{print $1}')
        local filepath=$(echo "$line" | awk '{print $2}')
        local size=$(echo "$line" | awk '{print $3}')
        local filename=$(basename "$filepath")
        local date=$(date -d @"${timestamp%.*}" '+%Y-%m-%d %H:%M:%S')
        local size_fmt=$(format_size "$size")

        echo "  - $filename ($date, $size_fmt)"
    done <<< "$old_backups"
    echo ""

    # Confirm deletion
    if [ "$FORCE" != "true" ] && [ "$DRY_RUN" != "true" ]; then
        read -p "Delete $old_count backup(s) and free $size_formatted? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
            log_warning "Cleanup cancelled by user"
            exit 0
        fi
    fi

    # Delete backups
    local deleted=0
    local failed=0

    while IFS= read -r line; do
        local filepath=$(echo "$line" | awk '{print $2}')

        if delete_backup "$filepath"; then
            deleted=$((deleted + 1))
        else
            failed=$((failed + 1))
        fi
    done <<< "$old_backups"

    # Summary
    echo ""
    log_success "=== Cleanup Summary ==="
    log_info "Backups deleted: $deleted"
    log_info "Failed deletions: $failed"
    log_info "Space freed: $size_formatted"

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] No files were actually deleted"
    fi

    exit 0
}

main
