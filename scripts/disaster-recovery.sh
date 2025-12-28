#!/bin/bash
#
# UC-Cloud Disaster Recovery Script
# Restores UC-Cloud from backup with rollback capability
#

set -e
set -o pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-${PROJECT_ROOT}/backups}"
RESTORE_DIR="${RESTORE_DIR:-${PROJECT_ROOT}}"
LOG_FILE="${LOG_FILE:-/var/log/uc-cloud-recovery.log}"
ROLLBACK_DIR="${ROLLBACK_DIR:-${BACKUP_DIR}/rollback}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Exit codes
EXIT_SUCCESS=0
EXIT_RESTORE_FAILED=1
EXIT_VERIFICATION_FAILED=2
EXIT_ROLLBACK_FAILED=3
EXIT_USER_CANCELLED=4

# Flags
DRY_RUN=false
FORCE=false
SKIP_VERIFICATION=false
AUTO_CONFIRM=false
CREATE_ROLLBACK=true

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
UC-Cloud Disaster Recovery Script

Usage: $0 [OPTIONS]

Options:
    -f, --file PATH        Restore from specific backup file
    -l, --latest           Restore from latest backup (default)
    -d, --dry-run          Simulate restore without making changes
    --force                Skip confirmation prompts
    --skip-verify          Skip backup verification
    --no-rollback          Don't create rollback point
    --auto-confirm         Automatically confirm all prompts
    -v, --verbose          Enable verbose output
    -h, --help             Show this help message

Environment Variables:
    BACKUP_DIR             Backup directory path
    RESTORE_DIR            Restore target directory
    LOG_FILE               Log file path
    ROLLBACK_DIR           Rollback storage directory

Exit Codes:
    0   Restore completed successfully
    1   Restore failed
    2   Verification failed
    3   Rollback failed
    4   User cancelled operation

Safety Features:
    - Creates rollback point before restore
    - Verifies backup integrity before restore
    - Stops services before restore
    - Verifies services after restore
    - Automatic rollback on failure

Examples:
    # Restore from latest backup (safe mode)
    $0 --latest

    # Restore from specific backup
    $0 --file /path/to/backup.tar.gz

    # Dry run to see what would be restored
    $0 --dry-run

    # Quick restore (skip verification, auto-confirm)
    $0 --latest --skip-verify --auto-confirm --force

EOF
}

confirm() {
    if [ "$AUTO_CONFIRM" = "true" ] || [ "$FORCE" = "true" ]; then
        return 0
    fi

    local prompt="$1"
    read -p "$prompt (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
        return 1
    fi
    return 0
}

find_latest_backup() {
    find "$BACKUP_DIR" -name "uc-cloud-backup-*.tar.gz" -type f -printf '%T@ %p\n' | \
        sort -rn | head -1 | cut -d' ' -f2
}

verify_backup() {
    local backup_file="$1"

    if [ "$SKIP_VERIFICATION" = "true" ]; then
        log_warning "Skipping backup verification (--skip-verify)"
        return 0
    fi

    log_info "Verifying backup integrity..."

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would verify: $backup_file"
        return 0
    fi

    if ! bash "$SCRIPT_DIR/verify-backup.sh" --file "$backup_file"; then
        log_error "Backup verification failed"
        return 1
    fi

    log_success "Backup verification passed"
    return 0
}

stop_services() {
    log_info "Stopping UC-Cloud services..."

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would stop all services"
        return 0
    fi

    cd "$PROJECT_ROOT"

    # Stop all services gracefully
    if docker-compose ps -q 2>/dev/null | grep -q .; then
        docker-compose stop 2>&1 | tee -a "$LOG_FILE"
        log_success "Services stopped"
    else
        log_info "No running services found"
    fi
}

start_services() {
    log_info "Starting UC-Cloud services..."

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would start all services"
        return 0
    fi

    cd "$PROJECT_ROOT"

    # Start services
    docker-compose up -d 2>&1 | tee -a "$LOG_FILE"

    log_success "Services started"
}

create_rollback_point() {
    if [ "$CREATE_ROLLBACK" != "true" ]; then
        log_info "Skipping rollback point creation (--no-rollback)"
        return 0
    fi

    log_info "Creating rollback point..."

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would create rollback point"
        return 0
    fi

    # Create rollback directory
    mkdir -p "$ROLLBACK_DIR"

    local timestamp=$(date +%Y%m%d-%H%M%S)
    local rollback_file="${ROLLBACK_DIR}/pre-restore-${timestamp}.tar.gz"

    # Backup current state
    log_info "Backing up current state to: $rollback_file"

    tar -czf "$rollback_file" \
        -C "$(dirname "$RESTORE_DIR")" \
        --exclude='backups' \
        --exclude='*.tar.gz' \
        "$(basename "$RESTORE_DIR")" 2>&1 | tee -a "$LOG_FILE"

    log_success "Rollback point created: $rollback_file"
    echo "$rollback_file" > "${ROLLBACK_DIR}/latest-rollback.txt"
}

restore_volumes() {
    local backup_file="$1"

    log_info "Restoring volumes..."

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would restore volumes from: $backup_file"
        return 0
    fi

    local temp_dir=$(mktemp -d)
    trap "rm -rf $temp_dir" EXIT

    # Extract backup
    tar -xzf "$backup_file" -C "$temp_dir" 2>&1 | tee -a "$LOG_FILE"

    # Restore volumes
    if [ -d "${temp_dir}/volumes" ]; then
        log_info "Restoring volumes directory..."
        rm -rf "${RESTORE_DIR}/volumes"
        cp -r "${temp_dir}/volumes" "${RESTORE_DIR}/" 2>&1 | tee -a "$LOG_FILE"
        log_success "Volumes restored"
    else
        log_warning "No volumes directory found in backup"
    fi

    rm -rf "$temp_dir"
}

restore_config() {
    local backup_file="$1"

    log_info "Restoring configuration files..."

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would restore configuration from: $backup_file"
        return 0
    fi

    local temp_dir=$(mktemp -d)
    trap "rm -rf $temp_dir" EXIT

    # Extract backup
    tar -xzf "$backup_file" -C "$temp_dir" 2>&1 | tee -a "$LOG_FILE"

    # Restore config files
    if [ -d "${temp_dir}/config-temp" ]; then
        log_info "Restoring configuration files..."

        # Copy files carefully to preserve structure
        find "${temp_dir}/config-temp" -type f -o -type l | while read -r file; do
            local rel_path="${file#${temp_dir}/config-temp/}"
            local dest_path="${RESTORE_DIR}/${rel_path}"

            mkdir -p "$(dirname "$dest_path")"
            cp -f "$file" "$dest_path" 2>&1 | tee -a "$LOG_FILE" || true
        done

        log_success "Configuration restored"
    else
        log_warning "No configuration files found in backup"
    fi

    rm -rf "$temp_dir"
}

restore_database() {
    local backup_file="$1"

    log_info "Restoring database..."

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would restore database from: $backup_file"
        return 0
    fi

    local temp_dir=$(mktemp -d)
    trap "rm -rf $temp_dir" EXIT

    # Extract backup
    tar -xzf "$backup_file" -C "$temp_dir" 2>&1 | tee -a "$LOG_FILE"

    # Check if PostgreSQL container is running
    if ! docker ps --format '{{.Names}}' | grep -q "unicorn-postgresql"; then
        log_warning "PostgreSQL container not running, starting it..."
        docker-compose up -d unicorn-postgresql 2>&1 | tee -a "$LOG_FILE"
        sleep 10
    fi

    # Restore PostgreSQL
    if [ -f "${temp_dir}"/*-postgres.sql.gz ]; then
        log_info "Restoring PostgreSQL database..."
        gunzip -c "${temp_dir}"/*-postgres.sql.gz | \
            docker exec -i unicorn-postgresql psql -U unicorn 2>&1 | tee -a "$LOG_FILE"
        log_success "PostgreSQL database restored"
    else
        log_warning "No PostgreSQL backup found"
    fi

    # Restore Redis
    if [ -f "${temp_dir}"/*-redis.rdb ]; then
        log_info "Restoring Redis data..."
        docker cp "${temp_dir}"/*-redis.rdb unicorn-redis:/data/dump.rdb 2>&1 | tee -a "$LOG_FILE" || true
        docker restart unicorn-redis 2>&1 | tee -a "$LOG_FILE" || true
        log_success "Redis data restored"
    else
        log_warning "No Redis backup found"
    fi

    rm -rf "$temp_dir"
}

verify_services() {
    log_info "Verifying services..."

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would verify services"
        return 0
    fi

    # Wait for services to start
    log_info "Waiting for services to initialize..."
    sleep 15

    # Check critical services
    local critical_services=(
        "unicorn-postgresql"
        "unicorn-redis"
        "ops-center-direct"
    )

    local all_healthy=true

    for service in "${critical_services[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "$service"; then
            local status=$(docker inspect --format='{{.State.Status}}' "$service" 2>/dev/null || echo "not found")
            if [ "$status" = "running" ]; then
                log_success "  ✓ $service is running"
            else
                log_error "  ✗ $service is not running (status: $status)"
                all_healthy=false
            fi
        else
            log_error "  ✗ $service not found"
            all_healthy=false
        fi
    done

    if [ "$all_healthy" = "false" ]; then
        log_error "Service verification failed"
        return 1
    fi

    log_success "All services verified successfully"
    return 0
}

perform_rollback() {
    log_warning "Performing rollback to pre-restore state..."

    if [ ! -f "${ROLLBACK_DIR}/latest-rollback.txt" ]; then
        log_error "No rollback point found"
        return 1
    fi

    local rollback_file=$(cat "${ROLLBACK_DIR}/latest-rollback.txt")

    if [ ! -f "$rollback_file" ]; then
        log_error "Rollback file not found: $rollback_file"
        return 1
    fi

    log_info "Rolling back from: $rollback_file"

    # Stop services
    stop_services

    # Restore from rollback
    tar -xzf "$rollback_file" -C "$(dirname "$RESTORE_DIR")" 2>&1 | tee -a "$LOG_FILE"

    # Start services
    start_services

    log_success "Rollback completed"
}

# Parse command line arguments
BACKUP_FILE=""
MODE="latest"

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--file)
            MODE="file"
            BACKUP_FILE="$2"
            shift 2
            ;;
        -l|--latest)
            MODE="latest"
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --skip-verify)
            SKIP_VERIFICATION=true
            shift
            ;;
        --no-rollback)
            CREATE_ROLLBACK=false
            shift
            ;;
        --auto-confirm)
            AUTO_CONFIRM=true
            shift
            ;;
        -v|--verbose)
            set -x
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

# Main execution
main() {
    log_info "=== UC-Cloud Disaster Recovery Started ==="

    # Find backup file
    if [ "$MODE" = "latest" ]; then
        log_info "Finding latest backup..."
        BACKUP_FILE=$(find_latest_backup)

        if [ -z "$BACKUP_FILE" ]; then
            log_error "No backups found in: $BACKUP_DIR"
            exit $EXIT_RESTORE_FAILED
        fi
    fi

    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "Backup file not found: $BACKUP_FILE"
        exit $EXIT_RESTORE_FAILED
    fi

    log_info "Backup file: $BACKUP_FILE"
    log_info "Restore directory: $RESTORE_DIR"

    # Verify backup
    if ! verify_backup "$BACKUP_FILE"; then
        log_error "Backup verification failed, aborting restore"
        exit $EXIT_VERIFICATION_FAILED
    fi

    # Confirm restore
    if ! confirm "This will restore UC-Cloud from backup. All current data will be replaced. Continue?"; then
        log_warning "Restore cancelled by user"
        exit $EXIT_USER_CANCELLED
    fi

    # Create rollback point
    if ! create_rollback_point; then
        log_warning "Failed to create rollback point"
        if ! confirm "Continue without rollback point?"; then
            exit $EXIT_USER_CANCELLED
        fi
    fi

    # Stop services
    if ! stop_services; then
        log_error "Failed to stop services"
        exit $EXIT_RESTORE_FAILED
    fi

    # Perform restore
    log_info "Starting restore process..."

    if ! restore_volumes "$BACKUP_FILE"; then
        log_error "Volume restore failed"
        perform_rollback
        exit $EXIT_RESTORE_FAILED
    fi

    if ! restore_config "$BACKUP_FILE"; then
        log_error "Configuration restore failed"
        perform_rollback
        exit $EXIT_RESTORE_FAILED
    fi

    if ! restore_database "$BACKUP_FILE"; then
        log_error "Database restore failed"
        perform_rollback
        exit $EXIT_RESTORE_FAILED
    fi

    # Start services
    if ! start_services; then
        log_error "Failed to start services"
        perform_rollback
        exit $EXIT_RESTORE_FAILED
    fi

    # Verify services
    if ! verify_services; then
        log_error "Service verification failed"
        if confirm "Services are not healthy. Perform rollback?"; then
            perform_rollback
        fi
        exit $EXIT_VERIFICATION_FAILED
    fi

    log_success "=== Disaster Recovery Completed Successfully ==="
    log_info "UC-Cloud has been restored from: $BACKUP_FILE"

    exit $EXIT_SUCCESS
}

# Run main function
main
