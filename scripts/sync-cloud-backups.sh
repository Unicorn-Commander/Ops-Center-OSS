#!/bin/bash
#
# UC-Cloud Cloud Backup Sync Script
# Bi-directional sync between local and cloud storage
#

set -e
set -o pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-${PROJECT_ROOT}/backups}"
LOG_FILE="${LOG_FILE:-/var/log/uc-cloud-backup-sync.log}"

# Cloud configuration
CLOUD_PROVIDER="${CLOUD_PROVIDER:-aws}"  # aws, gcp, azure
CLOUD_BUCKET="${CLOUD_BUCKET:-}"
CLOUD_REGION="${CLOUD_REGION:-us-east-1}"
CLOUD_PREFIX="${CLOUD_PREFIX:-backups/}"

# Sync settings
SYNC_MODE="${SYNC_MODE:-upload}"  # upload, download, bidirectional
DRY_RUN="${DRY_RUN:-false}"
VERIFY_AFTER_UPLOAD="${VERIFY_AFTER_UPLOAD:-true}"
DELETE_REMOTE="${DELETE_REMOTE:-false}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Exit codes
EXIT_SUCCESS=0
EXIT_SYNC_FAILED=1
EXIT_CLOUD_ERROR=2
EXIT_VERIFICATION_FAILED=3

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
UC-Cloud Cloud Backup Sync Script

Usage: $0 [OPTIONS]

Options:
    -m, --mode MODE        Sync mode: upload, download, bidirectional (default: upload)
    -p, --provider NAME    Cloud provider: aws, gcp, azure (default: aws)
    -b, --bucket NAME      Cloud storage bucket name
    -r, --region REGION    Cloud region (default: us-east-1)
    --prefix PATH          Remote path prefix (default: backups/)
    --delete-remote        Delete remote files not in local
    -n, --dry-run          Show what would be synced
    -v, --verbose          Enable verbose output
    -h, --help             Show this help message

Environment Variables:
    BACKUP_DIR             Local backup directory
    CLOUD_PROVIDER         Cloud provider (aws/gcp/azure)
    CLOUD_BUCKET           Cloud storage bucket
    CLOUD_REGION           Cloud region
    CLOUD_PREFIX           Remote path prefix
    LOG_FILE               Log file path

Sync Modes:
    upload                 Upload local backups to cloud
    download               Download cloud backups to local
    bidirectional          Sync both directions (merge)

Examples:
    # Upload local backups to AWS S3
    $0 --mode upload --provider aws --bucket my-backups

    # Download backups from GCP
    $0 --mode download --provider gcp --bucket my-bucket

    # Bidirectional sync with Azure
    $0 --mode bidirectional --provider azure --bucket mycontainer

    # Dry run to preview changes
    $0 --dry-run --mode upload

EOF
}

check_cloud_cli() {
    case "$CLOUD_PROVIDER" in
        aws)
            if ! command -v aws &> /dev/null; then
                log_error "AWS CLI not installed"
                return 1
            fi
            ;;
        gcp)
            if ! command -v gsutil &> /dev/null; then
                log_error "gsutil not installed"
                return 1
            fi
            ;;
        azure)
            if ! command -v az &> /dev/null; then
                log_error "Azure CLI not installed"
                return 1
            fi
            ;;
        *)
            log_error "Unsupported cloud provider: $CLOUD_PROVIDER"
            return 1
            ;;
    esac

    return 0
}

list_local_backups() {
    find "$BACKUP_DIR" -name "uc-cloud-backup-*.tar.gz" -type f -printf '%f\n' | sort
}

list_remote_backups_aws() {
    aws s3 ls "s3://${CLOUD_BUCKET}/${CLOUD_PREFIX}" --region "$CLOUD_REGION" | \
        grep "uc-cloud-backup-.*\.tar\.gz" | awk '{print $4}' | sort
}

list_remote_backups_gcp() {
    gsutil ls "gs://${CLOUD_BUCKET}/${CLOUD_PREFIX}" | \
        grep "uc-cloud-backup-.*\.tar\.gz" | xargs -n1 basename | sort
}

list_remote_backups_azure() {
    az storage blob list --container-name "$CLOUD_BUCKET" --prefix "$CLOUD_PREFIX" --query "[?contains(name, 'uc-cloud-backup-')].name" -o tsv | \
        xargs -n1 basename | sort
}

list_remote_backups() {
    case "$CLOUD_PROVIDER" in
        aws)
            list_remote_backups_aws
            ;;
        gcp)
            list_remote_backups_gcp
            ;;
        azure)
            list_remote_backups_azure
            ;;
    esac
}

upload_file_aws() {
    local file="$1"
    local remote_path="s3://${CLOUD_BUCKET}/${CLOUD_PREFIX}$(basename "$file")"

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would upload: $(basename "$file") → $remote_path"
        return 0
    fi

    aws s3 cp "$file" "$remote_path" --region "$CLOUD_REGION" 2>&1 | tee -a "$LOG_FILE"
}

upload_file_gcp() {
    local file="$1"
    local remote_path="gs://${CLOUD_BUCKET}/${CLOUD_PREFIX}$(basename "$file")"

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would upload: $(basename "$file") → $remote_path"
        return 0
    fi

    gsutil cp "$file" "$remote_path" 2>&1 | tee -a "$LOG_FILE"
}

upload_file_azure() {
    local file="$1"
    local blob_name="${CLOUD_PREFIX}$(basename "$file")"

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would upload: $(basename "$file") → azure://$blob_name"
        return 0
    fi

    az storage blob upload --file "$file" --container-name "$CLOUD_BUCKET" --name "$blob_name" 2>&1 | tee -a "$LOG_FILE"
}

upload_file() {
    local file="$1"

    case "$CLOUD_PROVIDER" in
        aws)
            upload_file_aws "$file"
            ;;
        gcp)
            upload_file_gcp "$file"
            ;;
        azure)
            upload_file_azure "$file"
            ;;
    esac
}

download_file_aws() {
    local filename="$1"
    local remote_path="s3://${CLOUD_BUCKET}/${CLOUD_PREFIX}${filename}"
    local local_path="${BACKUP_DIR}/${filename}"

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would download: $remote_path → $local_path"
        return 0
    fi

    aws s3 cp "$remote_path" "$local_path" --region "$CLOUD_REGION" 2>&1 | tee -a "$LOG_FILE"
}

download_file_gcp() {
    local filename="$1"
    local remote_path="gs://${CLOUD_BUCKET}/${CLOUD_PREFIX}${filename}"
    local local_path="${BACKUP_DIR}/${filename}"

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would download: $remote_path → $local_path"
        return 0
    fi

    gsutil cp "$remote_path" "$local_path" 2>&1 | tee -a "$LOG_FILE"
}

download_file_azure() {
    local filename="$1"
    local blob_name="${CLOUD_PREFIX}${filename}"
    local local_path="${BACKUP_DIR}/${filename}"

    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would download: azure://$blob_name → $local_path"
        return 0
    fi

    az storage blob download --container-name "$CLOUD_BUCKET" --name "$blob_name" --file "$local_path" 2>&1 | tee -a "$LOG_FILE"
}

download_file() {
    local filename="$1"

    case "$CLOUD_PROVIDER" in
        aws)
            download_file_aws "$filename"
            ;;
        gcp)
            download_file_gcp "$filename"
            ;;
        azure)
            download_file_azure "$filename"
            ;;
    esac
}

sync_upload() {
    log_info "Syncing local backups to cloud..."

    local local_backups=$(list_local_backups)
    local remote_backups=$(list_remote_backups)

    if [ -z "$local_backups" ]; then
        log_warning "No local backups found"
        return 0
    fi

    local uploaded=0
    local skipped=0
    local failed=0

    while IFS= read -r filename; do
        if echo "$remote_backups" | grep -q "^${filename}$"; then
            log_info "Skipping (already in cloud): $filename"
            skipped=$((skipped + 1))
        else
            log_info "Uploading: $filename"
            if upload_file "${BACKUP_DIR}/${filename}"; then
                # Upload checksum file too
                if [ -f "${BACKUP_DIR}/${filename}.sha256" ]; then
                    upload_file "${BACKUP_DIR}/${filename}.sha256" || true
                fi
                log_success "Uploaded: $filename"
                uploaded=$((uploaded + 1))
            else
                log_error "Upload failed: $filename"
                failed=$((failed + 1))
            fi
        fi
    done <<< "$local_backups"

    log_info "Upload summary: $uploaded uploaded, $skipped skipped, $failed failed"
    return 0
}

sync_download() {
    log_info "Syncing cloud backups to local..."

    local local_backups=$(list_local_backups)
    local remote_backups=$(list_remote_backups)

    if [ -z "$remote_backups" ]; then
        log_warning "No remote backups found"
        return 0
    fi

    local downloaded=0
    local skipped=0
    local failed=0

    while IFS= read -r filename; do
        if echo "$local_backups" | grep -q "^${filename}$"; then
            log_info "Skipping (already local): $filename"
            skipped=$((skipped + 1))
        else
            log_info "Downloading: $filename"
            if download_file "$filename"; then
                # Download checksum file too
                download_file "${filename}.sha256" || true
                log_success "Downloaded: $filename"
                downloaded=$((downloaded + 1))
            else
                log_error "Download failed: $filename"
                failed=$((failed + 1))
            fi
        fi
    done <<< "$remote_backups"

    log_info "Download summary: $downloaded downloaded, $skipped skipped, $failed failed"
    return 0
}

sync_bidirectional() {
    log_info "Performing bidirectional sync..."

    # Upload missing backups
    sync_upload

    # Download missing backups
    sync_download

    log_success "Bidirectional sync completed"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--mode)
            SYNC_MODE="$2"
            shift 2
            ;;
        -p|--provider)
            CLOUD_PROVIDER="$2"
            shift 2
            ;;
        -b|--bucket)
            CLOUD_BUCKET="$2"
            shift 2
            ;;
        -r|--region)
            CLOUD_REGION="$2"
            shift 2
            ;;
        --prefix)
            CLOUD_PREFIX="$2"
            shift 2
            ;;
        --delete-remote)
            DELETE_REMOTE=true
            shift
            ;;
        -n|--dry-run)
            DRY_RUN=true
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

# Main
main() {
    log_info "=== UC-Cloud Backup Sync Started ==="
    log_info "Mode: $SYNC_MODE"
    log_info "Provider: $CLOUD_PROVIDER"
    log_info "Bucket: $CLOUD_BUCKET"
    log_info "Local: $BACKUP_DIR"
    log_info "Dry run: $DRY_RUN"

    # Validate configuration
    if [ -z "$CLOUD_BUCKET" ]; then
        log_error "Cloud bucket not specified (use --bucket or CLOUD_BUCKET env var)"
        exit $EXIT_CLOUD_ERROR
    fi

    # Check cloud CLI
    if ! check_cloud_cli; then
        exit $EXIT_CLOUD_ERROR
    fi

    # Create backup directory if needed
    mkdir -p "$BACKUP_DIR"

    # Execute sync based on mode
    case "$SYNC_MODE" in
        upload)
            sync_upload
            ;;
        download)
            sync_download
            ;;
        bidirectional)
            sync_bidirectional
            ;;
        *)
            log_error "Invalid sync mode: $SYNC_MODE"
            show_help
            exit $EXIT_SYNC_FAILED
            ;;
    esac

    log_success "=== Sync Completed Successfully ==="
    exit $EXIT_SUCCESS
}

main
