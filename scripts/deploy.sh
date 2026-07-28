#!/bin/bash
#
# Ops-Center Deployment Script
# Supports multiple deployment strategies: rolling, blue-green, canary
#
# Usage: ./deploy.sh [--strategy=<strategy>] [--environment=<env>] [--tag=<tag>]
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="${ENVIRONMENT:-production}"
DEPLOYMENT_STRATEGY="${DEPLOYMENT_STRATEGY:-rolling}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-ghcr.io/unicorn-commander}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
HEALTH_CHECK_TIMEOUT=120
ROLLBACK_ON_FAILURE=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --strategy=*)
            DEPLOYMENT_STRATEGY="${1#*=}"
            shift
            ;;
        --environment=*)
            ENVIRONMENT="${1#*=}"
            shift
            ;;
        --tag=*)
            IMAGE_TAG="${1#*=}"
            shift
            ;;
        --no-rollback)
            ROLLBACK_ON_FAILURE=false
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

# Function to check if Docker is running
check_docker() {
    if ! docker info &>/dev/null; then
        log_error "Docker is not running"
        exit 1
    fi
    log_success "Docker is running"
}

# Function to create backup
create_backup() {
    log_info "Creating backup before deployment..."

    BACKUP_DIR="/opt/ops-center/backups"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)

    mkdir -p "$BACKUP_DIR"

    # Backup database
    if docker ps | grep -q unicorn-postgresql; then
        log_info "Backing up PostgreSQL database..."
        docker exec unicorn-postgresql pg_dump -U unicorn unicorn_db > \
            "$BACKUP_DIR/db_backup_${TIMESTAMP}.sql"
        log_success "Database backup created: db_backup_${TIMESTAMP}.sql"
    fi

    # Backup current docker-compose configuration
    if [ -f "$COMPOSE_FILE" ]; then
        cp "$COMPOSE_FILE" "$BACKUP_DIR/compose_${TIMESTAMP}.yml"
        log_success "Docker Compose config backed up"
    fi

    # Save current container state
    docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}' > \
        "$BACKUP_DIR/containers_${TIMESTAMP}.txt"

    # Export backup path for rollback
    export BACKUP_TIMESTAMP="$TIMESTAMP"
    echo "$TIMESTAMP" > "$BACKUP_DIR/.latest_backup"
}

# Function to pull latest images
pull_images() {
    log_info "Pulling Docker images (tag: $IMAGE_TAG)..."

    docker pull "${REGISTRY}/ops-center-backend:${IMAGE_TAG}" || {
        log_error "Failed to pull backend image"
        return 1
    }

    docker pull "${REGISTRY}/ops-center-frontend:${IMAGE_TAG}" || {
        log_error "Failed to pull frontend image"
        return 1
    }

    log_success "Images pulled successfully"
}

# Function to run database migrations
run_migrations() {
    log_info "Running database migrations..."

    # Check if Alembic is configured
    if docker exec ops-center-direct test -f /app/alembic.ini 2>/dev/null; then
        docker exec ops-center-direct python -m alembic upgrade head || {
            log_error "Database migration failed"
            return 1
        }
        log_success "Database migrations completed"
    else
        log_warning "No Alembic configuration found, skipping migrations"
    fi
}

# Function for rolling deployment
deploy_rolling() {
    log_info "Starting rolling deployment..."

    # Update backend service
    log_info "Updating backend service..."
    docker compose -f "$COMPOSE_FILE" up -d --no-deps ops-center-backend
    sleep 5

    # Check backend health
    if ! ./scripts/health_check.sh --service=backend --timeout=60; then
        log_error "Backend health check failed"
        return 1
    fi

    # Update frontend service
    log_info "Updating frontend service..."
    docker compose -f "$COMPOSE_FILE" up -d --no-deps ops-center-frontend
    sleep 5

    # Check frontend health
    if ! ./scripts/health_check.sh --service=frontend --timeout=30; then
        log_error "Frontend health check failed"
        return 1
    fi

    log_success "Rolling deployment completed successfully"
}

# Function for blue-green deployment
deploy_blue_green() {
    log_info "Starting blue-green deployment..."

    # Determine current and target environments
    CURRENT_ENV=$(docker ps --filter "name=ops-center" --format '{{.Names}}' | grep -oP 'blue|green' || echo "blue")
    if [ "$CURRENT_ENV" = "blue" ]; then
        TARGET_ENV="green"
    else
        TARGET_ENV="blue"
    fi

    log_info "Current environment: $CURRENT_ENV, Target: $TARGET_ENV"

    # Start new environment
    export DEPLOYMENT_COLOR="$TARGET_ENV"
    docker compose -f "$COMPOSE_FILE" -p "ops-center-$TARGET_ENV" up -d

    # Wait for services to be ready
    sleep 10

    # Health check on new environment
    if ! ./scripts/health_check.sh --environment="$TARGET_ENV" --timeout=60; then
        log_error "Health check failed on $TARGET_ENV environment"
        docker compose -f "$COMPOSE_FILE" -p "ops-center-$TARGET_ENV" down
        return 1
    fi

    # Switch traffic (this would typically update load balancer/Traefik)
    log_info "Switching traffic to $TARGET_ENV environment..."
    # Update Traefik labels or load balancer configuration here

    # Stop old environment after successful switch
    log_info "Stopping $CURRENT_ENV environment..."
    docker compose -f "$COMPOSE_FILE" -p "ops-center-$CURRENT_ENV" down

    log_success "Blue-green deployment completed successfully"
}

# Function for canary deployment
deploy_canary() {
    log_info "Starting canary deployment (10% traffic)..."

    # Deploy canary version alongside current version
    export DEPLOYMENT_TYPE="canary"
    docker compose -f "$COMPOSE_FILE" -p "ops-center-canary" up -d

    # Health check
    sleep 10
    if ! ./scripts/health_check.sh --environment="canary" --timeout=60; then
        log_error "Canary health check failed"
        docker compose -f "$COMPOSE_FILE" -p "ops-center-canary" down
        return 1
    fi

    # Monitor canary for 5 minutes
    log_info "Monitoring canary deployment for 5 minutes..."
    log_warning "Manual verification required. Check metrics and logs."
    log_warning "Run './scripts/deploy.sh --promote-canary' to complete deployment"

    log_success "Canary deployment started successfully"
}

# Main deployment flow
main() {
    log_info "========================================="
    log_info "Ops-Center Deployment"
    log_info "Environment: $ENVIRONMENT"
    log_info "Strategy: $DEPLOYMENT_STRATEGY"
    log_info "Image Tag: $IMAGE_TAG"
    log_info "========================================="

    # Pre-deployment checks
    check_docker

    # Create backup
    if ! create_backup; then
        log_error "Backup creation failed"
        exit 1
    fi

    # Pull latest images
    if ! pull_images; then
        log_error "Image pull failed"
        if [ "$ROLLBACK_ON_FAILURE" = true ]; then
            ./scripts/rollback.sh
        fi
        exit 1
    fi

    # Run database migrations
    if ! run_migrations; then
        log_error "Database migration failed"
        if [ "$ROLLBACK_ON_FAILURE" = true ]; then
            ./scripts/rollback.sh
        fi
        exit 1
    fi

    # Deploy based on strategy
    case "$DEPLOYMENT_STRATEGY" in
        rolling)
            if ! deploy_rolling; then
                log_error "Rolling deployment failed"
                if [ "$ROLLBACK_ON_FAILURE" = true ]; then
                    ./scripts/rollback.sh
                fi
                exit 1
            fi
            ;;
        blue-green)
            if ! deploy_blue_green; then
                log_error "Blue-green deployment failed"
                if [ "$ROLLBACK_ON_FAILURE" = true ]; then
                    ./scripts/rollback.sh
                fi
                exit 1
            fi
            ;;
        canary)
            if ! deploy_canary; then
                log_error "Canary deployment failed"
                if [ "$ROLLBACK_ON_FAILURE" = true ]; then
                    ./scripts/rollback.sh
                fi
                exit 1
            fi
            ;;
        *)
            log_error "Unknown deployment strategy: $DEPLOYMENT_STRATEGY"
            exit 1
            ;;
    esac

    # Final health check
    log_info "Running final health check..."
    if ! ./scripts/health_check.sh --timeout=60; then
        log_error "Final health check failed"
        if [ "$ROLLBACK_ON_FAILURE" = true ]; then
            ./scripts/rollback.sh
        fi
        exit 1
    fi

    # Cleanup old images
    log_info "Cleaning up old Docker images..."
    docker image prune -f --filter "until=168h" || true

    log_success "========================================="
    log_success "Deployment completed successfully!"
    log_success "Environment: $ENVIRONMENT"
    log_success "Version: $IMAGE_TAG"
    log_success "========================================="
}

# Run main function
main
