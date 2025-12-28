#!/bin/bash
#
# UC-Cloud Automated Backup Script
# Creates comprehensive backups of volumes, config, and databases
# Supports cloud upload and email notifications
#

set -e
set -o pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-${PROJECT_ROOT}/backups}"
LOG_FILE="${LOG_FILE:-/var/log/uc-cloud-backup.log}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="uc-cloud-backup-${TIMESTAMP}"
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
CHECKSUM_FILE="${BACKUP_FILE}.sha256"

# Cloud configuration
CLOUD_BACKUP_ENABLED="${CLOUD_BACKUP_ENABLED:-false}"
CLOUD_PROVIDER="${CLOUD_PROVIDER:-aws}"  # aws, gcp, azure
CLOUD_BUCKET="${CLOUD_BUCKET:-}"
CLOUD_REGION="${CLOUD_REGION:-us-east-1}"

# Email configuration
EMAIL_NOTIFICATIONS="${EMAIL_NOTIFICATIONS:-false}"
EMAIL_TO="${EMAIL_TO:-}"
EMAIL_FROM="${EMAIL_FROM:-backup@your-domain.com}"
SMTP_HOST="${SMTP_HOST:-localhost}"
SMTP_PORT="${SMTP_PORT:-25}"

# Backup options
DRY_RUN="${DRY_RUN:-false}"
VERBOSE="${VERBOSE:-false}"
COMPRESSION_LEVEL="${COMPRESSION_LEVEL:-6}"

# Exit codes
EXIT_SUCCESS=0
EXIT_BACKUP_FAILED=1
EXIT_CLOUD_UPLOAD_FAILED=2
EXIT_EMAIL_FAILED=3

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
UC-Cloud Automated Backup Script

Usage: $0 [OPTIONS]

Options:
    -d, --dry-run           Simulate backup without creating files
    -v, --verbose           Enable verbose output
    -c, --cloud             Enable cloud upload
    -e, --email            Enable email notifications
    --compression LEVEL     Compression level (1-9, default: 6)
    --backup-dir PATH       Backup directory (default: ./backups)
    -h, --help             Show this help message

Environment Variables:
    BACKUP_DIR              Backup directory path
    LOG_FILE                Log file path
    CLOUD_BACKUP_ENABLED    Enable cloud backups (true/false)
    CLOUD_PROVIDER          Cloud provider (aws/gcp/azure)
    CLOUD_BUCKET            Cloud storage bucket name
    EMAIL_NOTIFICATIONS     Enable email notifications (true/false)
    EMAIL_TO                Recipient email address
    SMTP_HOST               SMTP server hostname
    SMTP_PORT               SMTP server port

Exit Codes:
    0   Success
    1   Backup creation failed
    2   Cloud upload failed
    3   Email notification failed

Examples:
    # Basic backup
    $0

    # Dry run with verbose output
    $0 --dry-run --verbose

    # Backup with cloud upload
    $0 --cloud

    # Custom backup directory
    BACKUP_DIR=/mnt/backups $0

EOF
}

check_dependencies() {
    log_info "Checking dependencies..."

    local deps=("tar" "gzip" "sha256sum")
    local missing=()

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done

    if [ "$CLOUD_BACKUP_ENABLED" = "true" ]; then
        case "$CLOUD_PROVIDER" in
            aws)
                if ! command -v aws &> /dev/null; then
                    missing+=("aws-cli")
                fi
                ;;
            gcp)
                if ! command -v gsutil &> /dev/null; then
                    missing+=("gsutil")
                fi
                ;;
            azure)
                if ! command -v az &> /dev/null; then
                    missing+=("azure-cli")
                fi
                ;;
        esac
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing dependencies: ${missing[*]}"
        return 1
    fi

    log_success "All dependencies satisfied"
    return 0
}

create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        log_info "Creating backup directory: $BACKUP_DIR"
        if [ "$DRY_RUN" = "false" ]; then
            mkdir -p "$BACKUP_DIR"
        fi
    fi
}

backup_volumes() {
    log_info "Backing up volumes..."

    local volumes_dir="${PROJECT_ROOT}/volumes"
    if [ ! -d "$volumes_dir" ]; then
        log_warning "Volumes directory not found: $volumes_dir"
        return 0
    fi

    if [ "$DRY_RUN" = "false" ]; then
        tar -czf "${BACKUP_DIR}/${BACKUP_NAME}-volumes.tar.gz" \
            -C "$(dirname "$volumes_dir")" \
            "$(basename "$volumes_dir")" 2>&1 | tee -a "$LOG_FILE"

        log_success "Volumes backed up successfully"
    else
        log_info "[DRY RUN] Would backup: $volumes_dir"
    fi
}

backup_config() {
    log_info "Backing up configuration files..."

    local config_files=(
        "${PROJECT_ROOT}/docker-compose.yml"
        "${PROJECT_ROOT}/.env"
        "${PROJECT_ROOT}/services/ops-center/.env.auth"
        "${PROJECT_ROOT}/services/ops-center/backend/.env"
        "${PROJECT_ROOT}/traefik/traefik.yml"
        "${PROJECT_ROOT}/traefik/dynamic/*.yml"
    )

    if [ "$DRY_RUN" = "false" ]; then
        local temp_config_dir="${BACKUP_DIR}/config-temp"
        mkdir -p "$temp_config_dir"

        for file in "${config_files[@]}"; do
            if [ -e "$file" ]; then
                cp -r "$file" "$temp_config_dir/" 2>&1 | tee -a "$LOG_FILE" || true
            fi
        done

        tar -czf "${BACKUP_DIR}/${BACKUP_NAME}-config.tar.gz" \
            -C "$BACKUP_DIR" config-temp 2>&1 | tee -a "$LOG_FILE"

        rm -rf "$temp_config_dir"
        log_success "Configuration backed up successfully"
    else
        log_info "[DRY RUN] Would backup: ${#config_files[@]} configuration files"
    fi
}

backup_database() {
    log_info "Backing up PostgreSQL database..."

    if [ "$DRY_RUN" = "false" ]; then
        # Check if PostgreSQL container is running
        if ! docker ps --format '{{.Names}}' | grep -q "unicorn-postgresql"; then
            log_warning "PostgreSQL container not running, skipping database backup"
            return 0
        fi

        # Backup PostgreSQL
        docker exec unicorn-postgresql pg_dumpall -U unicorn > \
            "${BACKUP_DIR}/${BACKUP_NAME}-postgres.sql" 2>&1 | tee -a "$LOG_FILE"

        gzip "${BACKUP_DIR}/${BACKUP_NAME}-postgres.sql"
        log_success "PostgreSQL database backed up successfully"

        # Backup Redis (if needed)
        if docker ps --format '{{.Names}}' | grep -q "unicorn-redis"; then
            docker exec unicorn-redis redis-cli SAVE 2>&1 | tee -a "$LOG_FILE" || true
            docker cp unicorn-redis:/data/dump.rdb \
                "${BACKUP_DIR}/${BACKUP_NAME}-redis.rdb" 2>&1 | tee -a "$LOG_FILE" || true
            log_success "Redis data backed up successfully"
        fi
    else
        log_info "[DRY RUN] Would backup PostgreSQL and Redis databases"
    fi
}

create_archive() {
    log_info "Creating unified backup archive..."

    if [ "$DRY_RUN" = "false" ]; then
        # Combine all backup components
        tar -czf "$BACKUP_FILE" \
            --exclude="${BACKUP_NAME}.tar.gz" \
            -C "$BACKUP_DIR" \
            "${BACKUP_NAME}"-* 2>&1 | tee -a "$LOG_FILE"

        # Create checksum
        sha256sum "$BACKUP_FILE" > "$CHECKSUM_FILE"

        # Clean up individual archives
        rm -f "${BACKUP_DIR}/${BACKUP_NAME}"-*.tar.gz \
              "${BACKUP_DIR}/${BACKUP_NAME}"-*.sql.gz \
              "${BACKUP_DIR}/${BACKUP_NAME}"-*.rdb

        local size=$(du -h "$BACKUP_FILE" | cut -f1)
        log_success "Backup archive created: $BACKUP_FILE ($size)"
    else
        log_info "[DRY RUN] Would create backup archive: $BACKUP_FILE"
    fi
}

upload_to_cloud() {
    if [ "$CLOUD_BACKUP_ENABLED" != "true" ]; then
        return 0
    fi

    log_info "Uploading backup to cloud ($CLOUD_PROVIDER)..."

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would upload to: ${CLOUD_PROVIDER}://${CLOUD_BUCKET}/"
        return 0
    fi

    case "$CLOUD_PROVIDER" in
        aws)
            aws s3 cp "$BACKUP_FILE" "s3://${CLOUD_BUCKET}/" \
                --region "$CLOUD_REGION" 2>&1 | tee -a "$LOG_FILE"
            aws s3 cp "$CHECKSUM_FILE" "s3://${CLOUD_BUCKET}/" \
                --region "$CLOUD_REGION" 2>&1 | tee -a "$LOG_FILE"
            ;;
        gcp)
            gsutil cp "$BACKUP_FILE" "gs://${CLOUD_BUCKET}/" 2>&1 | tee -a "$LOG_FILE"
            gsutil cp "$CHECKSUM_FILE" "gs://${CLOUD_BUCKET}/" 2>&1 | tee -a "$LOG_FILE"
            ;;
        azure)
            az storage blob upload --file "$BACKUP_FILE" \
                --container-name "$CLOUD_BUCKET" \
                --name "$(basename "$BACKUP_FILE")" 2>&1 | tee -a "$LOG_FILE"
            az storage blob upload --file "$CHECKSUM_FILE" \
                --container-name "$CLOUD_BUCKET" \
                --name "$(basename "$CHECKSUM_FILE")" 2>&1 | tee -a "$LOG_FILE"
            ;;
        *)
            log_error "Unsupported cloud provider: $CLOUD_PROVIDER"
            return 1
            ;;
    esac

    log_success "Backup uploaded to cloud successfully"
}

send_notification() {
    local status="$1"
    local message="$2"

    if [ "$EMAIL_NOTIFICATIONS" != "true" ] || [ -z "$EMAIL_TO" ]; then
        return 0
    fi

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would send email to: $EMAIL_TO"
        return 0
    fi

    log_info "Sending email notification..."

    local subject="[UC-Cloud] Backup $status - $TIMESTAMP"
    local body="UC-Cloud Backup Report

Status: $status
Timestamp: $TIMESTAMP
Backup File: $BACKUP_FILE
Message: $message

Log: $LOG_FILE
"

    # Try to send email using mail command
    if command -v mail &> /dev/null; then
        echo "$body" | mail -s "$subject" \
            -r "$EMAIL_FROM" \
            -S smtp="$SMTP_HOST:$SMTP_PORT" \
            "$EMAIL_TO" 2>&1 | tee -a "$LOG_FILE" || true
        log_success "Email notification sent"
    else
        log_warning "mail command not available, skipping email notification"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--cloud)
            CLOUD_BACKUP_ENABLED=true
            shift
            ;;
        -e|--email)
            EMAIL_NOTIFICATIONS=true
            shift
            ;;
        --compression)
            COMPRESSION_LEVEL="$2"
            shift 2
            ;;
        --backup-dir)
            BACKUP_DIR="$2"
            shift 2
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
    log_info "=== UC-Cloud Backup Started ==="
    log_info "Timestamp: $TIMESTAMP"
    log_info "Backup directory: $BACKUP_DIR"
    log_info "Dry run: $DRY_RUN"

    # Check dependencies
    if ! check_dependencies; then
        send_notification "FAILED" "Missing dependencies"
        exit $EXIT_BACKUP_FAILED
    fi

    # Create backup directory
    create_backup_dir

    # Perform backups
    if ! backup_volumes; then
        send_notification "FAILED" "Volume backup failed"
        exit $EXIT_BACKUP_FAILED
    fi

    if ! backup_config; then
        send_notification "FAILED" "Configuration backup failed"
        exit $EXIT_BACKUP_FAILED
    fi

    if ! backup_database; then
        send_notification "FAILED" "Database backup failed"
        exit $EXIT_BACKUP_FAILED
    fi

    # Create unified archive
    if ! create_archive; then
        send_notification "FAILED" "Archive creation failed"
        exit $EXIT_BACKUP_FAILED
    fi

    # Upload to cloud
    if ! upload_to_cloud; then
        send_notification "WARNING" "Cloud upload failed, local backup available"
        exit $EXIT_CLOUD_UPLOAD_FAILED
    fi

    # Send success notification
    send_notification "SUCCESS" "Backup completed successfully"

    log_success "=== UC-Cloud Backup Completed Successfully ==="
    exit $EXIT_SUCCESS
}

# Run main function
main
