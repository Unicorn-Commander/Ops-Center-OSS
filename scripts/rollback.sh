#!/bin/bash
#
# Ops-Center Rollback Script
# Automatically reverts to the previous working version
#
# Usage: ./rollback.sh [--backup-timestamp=<timestamp>]
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BACKUP_DIR="/opt/ops-center/backups"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

# Parse command line arguments
BACKUP_TIMESTAMP=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --backup-timestamp=*)
            BACKUP_TIMESTAMP="${1#*=}"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Logging functions
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

# Function to find latest backup
find_latest_backup() {
    if [ -n "$BACKUP_TIMESTAMP" ]; then
        echo "$BACKUP_TIMESTAMP"
        return
    fi

    if [ -f "$BACKUP_DIR/.latest_backup" ]; then
        cat "$BACKUP_DIR/.latest_backup"
    else
        # Find most recent backup by timestamp
        ls -t "$BACKUP_DIR"/db_backup_*.sql 2>/dev/null | head -1 | grep -oP '\d{8}_\d{6}' || echo ""
    fi
}

# Function to verify backup exists
verify_backup() {
    local timestamp=$1

    if [ -z "$timestamp" ]; then
        log_error "No backup timestamp found"
        return 1
    fi

    local db_backup="${BACKUP_DIR}/db_backup_${timestamp}.sql"
    local compose_backup="${BACKUP_DIR}/compose_${timestamp}.yml"

    if [ ! -f "$db_backup" ]; then
        log_error "Database backup not found: $db_backup"
        return 1
    fi

    log_success "Found backup from $timestamp"
    return 0
}

# Function to stop current containers
stop_current_services() {
    log_info "Stopping current services..."

    docker compose -f "$COMPOSE_FILE" stop ops-center-backend ops-center-frontend || {
        log_warning "Failed to stop services gracefully, forcing stop..."
        docker stop ops-center-backend ops-center-frontend 2>/dev/null || true
    }

    log_success "Services stopped"
}

# Function to restore database
restore_database() {
    local timestamp=$1
    local db_backup="${BACKUP_DIR}/db_backup_${timestamp}.sql"

    log_info "Restoring database from backup..."

    # Create a safety backup of current state before restore
    docker exec unicorn-postgresql pg_dump -U unicorn unicorn_db > \
        "${BACKUP_DIR}/pre_rollback_$(date +%Y%m%d_%H%M%S).sql" 2>/dev/null || true

    # Drop and recreate database
    docker exec unicorn-postgresql psql -U unicorn -c "DROP DATABASE IF EXISTS unicorn_db;" || true
    docker exec unicorn-postgresql psql -U unicorn -c "CREATE DATABASE unicorn_db;" || {
        log_error "Failed to create database"
        return 1
    }

    # Restore from backup
    docker exec -i unicorn-postgresql psql -U unicorn unicorn_db < "$db_backup" || {
        log_error "Database restore failed"
        return 1
    }

    log_success "Database restored successfully"
}

# Function to restore Docker Compose configuration
restore_compose_config() {
    local timestamp=$1
    local compose_backup="${BACKUP_DIR}/compose_${timestamp}.yml"

    if [ -f "$compose_backup" ]; then
        log_info "Restoring Docker Compose configuration..."
        cp "$compose_backup" "$COMPOSE_FILE"
        log_success "Docker Compose configuration restored"
    else
        log_warning "No Docker Compose backup found, using current configuration"
    fi
}

# Function to get previous image tags
get_previous_images() {
    local timestamp=$1
    local containers_file="${BACKUP_DIR}/containers_${timestamp}.txt"

    if [ -f "$containers_file" ]; then
        log_info "Previous container state:"
        cat "$containers_file"

        # Extract image tags
        BACKEND_IMAGE=$(grep ops-center-backend "$containers_file" | awk '{print $2}' || echo "")
        FRONTEND_IMAGE=$(grep ops-center-frontend "$containers_file" | awk '{print $2}' || echo "")

        if [ -n "$BACKEND_IMAGE" ] && [ -n "$FRONTEND_IMAGE" ]; then
            log_success "Found previous images"
            return 0
        fi
    fi

    log_warning "Could not determine previous image versions"
    return 1
}

# Function to pull previous images
pull_previous_images() {
    if [ -n "$BACKEND_IMAGE" ]; then
        log_info "Pulling previous backend image: $BACKEND_IMAGE"
        docker pull "$BACKEND_IMAGE" || {
            log_error "Failed to pull backend image"
            return 1
        }
    fi

    if [ -n "$FRONTEND_IMAGE" ]; then
        log_info "Pulling previous frontend image: $FRONTEND_IMAGE"
        docker pull "$FRONTEND_IMAGE" || {
            log_error "Failed to pull frontend image"
            return 1
        }
    fi

    log_success "Previous images pulled successfully"
}

# Function to restart services
restart_services() {
    log_info "Restarting services with previous configuration..."

    if [ -n "$BACKEND_IMAGE" ] && [ -n "$FRONTEND_IMAGE" ]; then
        # Start with specific image versions
        export BACKEND_IMAGE
        export FRONTEND_IMAGE
        docker compose -f "$COMPOSE_FILE" up -d ops-center-backend ops-center-frontend
    else
        # Start with whatever is configured
        docker compose -f "$COMPOSE_FILE" up -d ops-center-backend ops-center-frontend
    fi

    # Wait for services to start
    sleep 10

    log_success "Services restarted"
}

# Function to verify rollback
verify_rollback() {
    log_info "Verifying rollback..."

    # Run health check
    if ./scripts/health_check.sh --timeout=60; then
        log_success "Health check passed after rollback"
        return 0
    else
        log_error "Health check failed after rollback"
        return 1
    fi
}

# Main rollback flow
main() {
    log_warning "========================================="
    log_warning "Ops-Center Rollback"
    log_warning "This will revert to a previous version"
    log_warning "========================================="

    # Find backup to restore
    BACKUP_TIMESTAMP=$(find_latest_backup)

    if [ -z "$BACKUP_TIMESTAMP" ]; then
        log_error "No backup found to rollback to"
        log_error "Available backups:"
        ls -lh "$BACKUP_DIR"/db_backup_*.sql 2>/dev/null || echo "None"
        exit 1
    fi

    # Verify backup exists
    if ! verify_backup "$BACKUP_TIMESTAMP"; then
        exit 1
    fi

    log_info "Rolling back to backup from: $BACKUP_TIMESTAMP"
    read -p "Continue with rollback? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Rollback cancelled"
        exit 0
    fi

    # Stop current services
    if ! stop_current_services; then
        log_error "Failed to stop services"
        exit 1
    fi

    # Restore database
    if ! restore_database "$BACKUP_TIMESTAMP"; then
        log_error "Database restore failed"
        exit 1
    fi

    # Restore Docker Compose config
    restore_compose_config "$BACKUP_TIMESTAMP"

    # Get previous image versions
    get_previous_images "$BACKUP_TIMESTAMP" || true

    # Pull previous images if found
    if [ -n "$BACKEND_IMAGE" ] && [ -n "$FRONTEND_IMAGE" ]; then
        pull_previous_images || log_warning "Could not pull previous images, using latest available"
    fi

    # Restart services
    if ! restart_services; then
        log_error "Failed to restart services"
        exit 1
    fi

    # Verify rollback
    if ! verify_rollback; then
        log_error "Rollback verification failed"
        log_error "Manual intervention required!"
        exit 1
    fi

    log_success "========================================="
    log_success "Rollback completed successfully!"
    log_success "Restored to backup: $BACKUP_TIMESTAMP"
    log_success "========================================="
}

# Check if running non-interactively (in CI/CD)
if [ -t 0 ]; then
    # Interactive mode
    main
else
    # Non-interactive mode - skip confirmation
    log_warning "Running in non-interactive mode"
    BACKUP_TIMESTAMP=$(find_latest_backup)

    if [ -z "$BACKUP_TIMESTAMP" ]; then
        log_error "No backup found"
        exit 1
    fi

    verify_backup "$BACKUP_TIMESTAMP" || exit 1
    stop_current_services || exit 1
    restore_database "$BACKUP_TIMESTAMP" || exit 1
    restore_compose_config "$BACKUP_TIMESTAMP"
    restart_services || exit 1
    verify_rollback || exit 1

    log_success "Automated rollback completed"
fi
