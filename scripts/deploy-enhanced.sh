#!/bin/bash
set -euo pipefail

# ==============================================================================
# Enhanced Deployment Script with Zero-Downtime & Automated Rollback
# ==============================================================================
# This script implements blue-green deployment with health checks and automatic
# rollback on failure. It ensures zero-downtime deployments.
# ==============================================================================

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_DIR="/opt/ops-center"
BACKUP_DIR="${DEPLOYMENT_DIR}/backups"
RELEASES_DIR="${DEPLOYMENT_DIR}/releases"
CURRENT_LINK="${DEPLOYMENT_DIR}/current"
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=2
ROLLBACK_ON_FAILURE=${ROLLBACK_ON_FAILURE:-true}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

# Cleanup function for trap
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "Deployment failed with exit code $exit_code"
        if [ "$ROLLBACK_ON_FAILURE" = "true" ]; then
            log_warn "Initiating automatic rollback..."
            rollback_deployment
        fi
    fi
}

trap cleanup EXIT

# ==============================================================================
# PRE-DEPLOYMENT CHECKS
# ==============================================================================
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."

    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi

    # Check disk space (require at least 5GB free)
    local available_space=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$available_space" -lt 5 ]; then
        log_error "Insufficient disk space. Available: ${available_space}GB, Required: 5GB"
        exit 1
    fi

    # Check if required directories exist
    mkdir -p "${BACKUP_DIR}" "${RELEASES_DIR}"

    # Check if docker-compose file exists
    if [ ! -f "docker-compose.direct.yml" ]; then
        log_error "docker-compose.direct.yml not found"
        exit 1
    fi

    log_success "Pre-deployment checks passed"
}

# ==============================================================================
# BACKUP CURRENT STATE
# ==============================================================================
backup_current_state() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/db_backup_${timestamp}.sql"
    local config_backup="${RELEASES_DIR}/compose_${timestamp}.yml"

    log_info "Creating backup of current state..."

    # Backup database
    if docker ps | grep -q unicorn-postgresql; then
        log_info "Backing up PostgreSQL database..."
        docker exec unicorn-postgresql pg_dump -U unicorn unicorn_db > "$backup_file" 2>&1
        if [ $? -eq 0 ]; then
            log_success "Database backed up to $backup_file"
            # Compress backup
            gzip "$backup_file"
            log_success "Backup compressed: ${backup_file}.gz"
        else
            log_error "Database backup failed"
            exit 1
        fi
    fi

    # Backup docker-compose configuration
    if [ -f "docker-compose.direct.yml" ]; then
        cp docker-compose.direct.yml "$config_backup"
        log_success "Configuration backed up to $config_backup"
    fi

    # Save current container image tags
    docker images | grep ops-center > "${RELEASES_DIR}/images_${timestamp}.txt" || true

    # Save last known good state
    echo "$timestamp" > "${RELEASES_DIR}/last_successful_deployment.txt"

    log_success "Backup completed successfully"
}

# ==============================================================================
# DATABASE MIGRATIONS
# ==============================================================================
run_database_migrations() {
    log_info "Running database migrations..."

    # Check if migrations exist
    if [ -d "backend/migrations" ]; then
        # Run Alembic migrations inside container
        docker exec ops-center-direct python -m alembic upgrade head 2>&1
        if [ $? -eq 0 ]; then
            log_success "Database migrations completed successfully"
        else
            log_error "Database migrations failed"
            return 1
        fi
    else
        log_info "No migrations directory found, skipping"
    fi

    return 0
}

# ==============================================================================
# BLUE-GREEN DEPLOYMENT
# ==============================================================================
blue_green_deployment() {
    local deployment_strategy=${DEPLOYMENT_STRATEGY:-blue-green}
    local image_tag=${IMAGE_TAG:-latest}

    log_info "Starting ${deployment_strategy} deployment with image tag: ${image_tag}"

    # Pull new images
    log_info "Pulling latest Docker images..."
    docker compose -f docker-compose.direct.yml pull

    # Build new version
    log_info "Building new version..."
    docker compose -f docker-compose.direct.yml build --no-cache

    # Start new containers with different names (blue-green)
    log_info "Starting new containers (green environment)..."

    # Create temporary compose file with green service names
    sed 's/ops-center-direct/ops-center-green/g' docker-compose.direct.yml > docker-compose.green.yml

    # Start green environment
    docker compose -f docker-compose.green.yml up -d

    # Wait for green environment to be ready
    log_info "Waiting for green environment to be healthy..."
    if ! wait_for_health "ops-center-green"; then
        log_error "Green environment failed health checks"
        docker compose -f docker-compose.green.yml down
        rm -f docker-compose.green.yml
        return 1
    fi

    log_success "Green environment is healthy"

    # Switch traffic (update routing)
    log_info "Switching traffic to green environment..."

    # Stop blue environment (old)
    docker compose -f docker-compose.direct.yml down

    # Rename green to blue
    docker rename ops-center-green ops-center-direct

    # Update compose file
    mv docker-compose.green.yml docker-compose.direct.yml

    log_success "Traffic switched to new deployment"

    return 0
}

# ==============================================================================
# HEALTH CHECKS
# ==============================================================================
wait_for_health() {
    local container_name=$1
    local retries=0

    log_info "Waiting for ${container_name} to be healthy..."

    while [ $retries -lt $HEALTH_CHECK_RETRIES ]; do
        # Check if container is running
        if ! docker ps | grep -q "$container_name"; then
            log_warn "Container ${container_name} is not running (retry $retries/$HEALTH_CHECK_RETRIES)"
            sleep $HEALTH_CHECK_INTERVAL
            retries=$((retries + 1))
            continue
        fi

        # Check HTTP health endpoint
        if curl -f -s http://localhost:8084/api/v1/health >/dev/null 2>&1; then
            log_success "Health check passed for ${container_name}"
            return 0
        fi

        log_info "Health check failed (retry $retries/$HEALTH_CHECK_RETRIES)"
        sleep $HEALTH_CHECK_INTERVAL
        retries=$((retries + 1))
    done

    log_error "Health checks failed after ${HEALTH_CHECK_RETRIES} retries"
    return 1
}

run_smoke_tests() {
    log_info "Running smoke tests..."

    local tests_passed=0
    local tests_failed=0

    # Test 1: System status endpoint
    if curl -f -s http://localhost:8084/api/v1/system/status >/dev/null 2>&1; then
        log_success "✓ System status endpoint responding"
        tests_passed=$((tests_passed + 1))
    else
        log_error "✗ System status endpoint failed"
        tests_failed=$((tests_failed + 1))
    fi

    # Test 2: Health endpoint
    if curl -f -s http://localhost:8084/api/v1/health >/dev/null 2>&1; then
        log_success "✓ Health endpoint responding"
        tests_passed=$((tests_passed + 1))
    else
        log_error "✗ Health endpoint failed"
        tests_failed=$((tests_failed + 1))
    fi

    # Test 3: Frontend serving
    if curl -f -s http://localhost:8084/ >/dev/null 2>&1; then
        log_success "✓ Frontend serving correctly"
        tests_passed=$((tests_passed + 1))
    else
        log_error "✗ Frontend serving failed"
        tests_failed=$((tests_failed + 1))
    fi

    # Test 4: Database connectivity
    # Uses environment variables: POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
    DB_HOST="${POSTGRES_HOST:-localhost}"
    DB_USER="${POSTGRES_USER:-ops_user}"
    DB_PASS="${POSTGRES_PASSWORD:-change-me}"
    DB_NAME="${POSTGRES_DB:-ops_center_db}"
    if docker exec ops-center-direct python -c "import psycopg2; import os; conn = psycopg2.connect(host=os.getenv('POSTGRES_HOST','localhost'), user=os.getenv('POSTGRES_USER','ops_user'), password=os.getenv('POSTGRES_PASSWORD',''), dbname=os.getenv('POSTGRES_DB','ops_center_db')); conn.close()" 2>/dev/null; then
        log_success "Database connectivity OK"
        tests_passed=$((tests_passed + 1))
    else
        log_error "Database connectivity failed"
        tests_failed=$((tests_failed + 1))
    fi

    # Test 5: Redis connectivity
    # Uses environment variable: REDIS_HOST
    if docker exec ops-center-direct python -c "import redis; import os; r = redis.Redis(host=os.getenv('REDIS_HOST','localhost')); r.ping()" 2>/dev/null; then
        log_success "Redis connectivity OK"
        tests_passed=$((tests_passed + 1))
    else
        log_error "Redis connectivity failed"
        tests_failed=$((tests_failed + 1))
    fi

    log_info "Smoke tests completed: ${tests_passed} passed, ${tests_failed} failed"

    if [ $tests_failed -gt 0 ]; then
        return 1
    fi

    return 0
}

# ==============================================================================
# ROLLBACK
# ==============================================================================
rollback_deployment() {
    log_warn "Rolling back deployment..."

    # Get last successful deployment
    if [ -f "${RELEASES_DIR}/last_successful_deployment.txt" ]; then
        local last_good=$(cat "${RELEASES_DIR}/last_successful_deployment.txt")
        log_info "Rolling back to version: $last_good"

        # Restore docker-compose configuration
        local config_backup="${RELEASES_DIR}/compose_${last_good}.yml"
        if [ -f "$config_backup" ]; then
            cp "$config_backup" docker-compose.direct.yml
            log_success "Configuration restored"
        fi

        # Restart services with old configuration
        docker compose -f docker-compose.direct.yml down
        docker compose -f docker-compose.direct.yml up -d

        # Wait for health
        if wait_for_health "ops-center-direct"; then
            log_success "Rollback completed successfully"

            # Restore database if needed
            local db_backup="${BACKUP_DIR}/db_backup_${last_good}.sql.gz"
            if [ -f "$db_backup" ]; then
                log_warn "Database backup available at: $db_backup"
                log_warn "Run manual restore if needed: gunzip < $db_backup | docker exec -i unicorn-postgresql psql -U unicorn unicorn_db"
            fi
        else
            log_error "Rollback failed - manual intervention required"
            exit 1
        fi
    else
        log_error "No previous deployment found for rollback"
        exit 1
    fi
}

# ==============================================================================
# CLEANUP OLD BACKUPS
# ==============================================================================
cleanup_old_backups() {
    local retention_days=${BACKUP_RETENTION_DAYS:-7}

    log_info "Cleaning up backups older than ${retention_days} days..."

    find "${BACKUP_DIR}" -type f -name "*.sql.gz" -mtime +${retention_days} -delete
    find "${RELEASES_DIR}" -type f -mtime +${retention_days} -delete

    log_success "Old backups cleaned up"
}

# ==============================================================================
# POST-DEPLOYMENT NOTIFICATIONS
# ==============================================================================
send_notification() {
    local status=$1
    local message=$2

    # Slack notification (if webhook configured)
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local icon=":white_check_mark:"
        [ "$status" = "failure" ] && icon=":x:"

        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{\"text\": \"${icon} Ops-Center Deployment ${status}: ${message}\"}" \
            2>/dev/null || true
    fi

    # Email notification (if configured)
    if [ -n "${NOTIFICATION_EMAIL:-}" ]; then
        echo "$message" | mail -s "Ops-Center Deployment ${status}" "$NOTIFICATION_EMAIL" 2>/dev/null || true
    fi
}

# ==============================================================================
# MAIN DEPLOYMENT FLOW
# ==============================================================================
main() {
    local start_time=$(date +%s)

    log_info "========================================"
    log_info "Ops-Center Enhanced Deployment Starting"
    log_info "========================================"

    # Step 1: Pre-deployment checks
    pre_deployment_checks

    # Step 2: Backup current state
    backup_current_state

    # Step 3: Run database migrations
    if ! run_database_migrations; then
        log_error "Database migrations failed - aborting deployment"
        exit 1
    fi

    # Step 4: Deploy using blue-green strategy
    if ! blue_green_deployment; then
        log_error "Deployment failed - rollback initiated"
        exit 1
    fi

    # Step 5: Run comprehensive smoke tests
    if ! run_smoke_tests; then
        log_error "Smoke tests failed - rollback initiated"
        exit 1
    fi

    # Step 6: Cleanup old backups
    cleanup_old_backups

    # Step 7: Calculate deployment time
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "========================================"
    log_success "Deployment completed successfully!"
    log_success "Total deployment time: ${duration} seconds"
    log_success "========================================"

    # Send success notification
    send_notification "success" "Deployment completed in ${duration} seconds"
}

# Run main deployment
main "$@"
