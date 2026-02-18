#!/bin/bash
#
# Ops-Center Health Check Script
# Comprehensive health verification for all services
#
# Usage: ./health_check.sh [--timeout=<seconds>] [--service=<service>] [--environment=<env>]
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TIMEOUT=120
SERVICE="all"
ENVIRONMENT="production"
BASE_URL="${BASE_URL:-https://unicorncommander.ai}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --timeout=*)
            TIMEOUT="${1#*=}"
            shift
            ;;
        --service=*)
            SERVICE="${1#*=}"
            shift
            ;;
        --environment=*)
            ENVIRONMENT="${1#*=}"
            shift
            ;;
        --base-url=*)
            BASE_URL="${1#*=}"
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
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Function to check if container is running
check_container() {
    local container_name=$1

    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        log_success "Container running: $container_name"
        return 0
    else
        log_error "Container not running: $container_name"
        return 1
    fi
}

# Function to check container health status
check_container_health() {
    local container_name=$1

    local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "none")

    case "$health_status" in
        healthy)
            log_success "Container healthy: $container_name"
            return 0
            ;;
        starting)
            log_warning "Container starting: $container_name"
            return 1
            ;;
        unhealthy)
            log_error "Container unhealthy: $container_name"
            return 1
            ;;
        none)
            log_warning "No health check defined: $container_name"
            return 0
            ;;
        *)
            log_warning "Unknown health status: $container_name ($health_status)"
            return 1
            ;;
    esac
}

# Function to check HTTP endpoint
check_http_endpoint() {
    local url=$1
    local expected_status=${2:-200}
    local name=$3

    local response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" || echo "000")

    if [ "$response_code" -eq "$expected_status" ]; then
        log_success "HTTP endpoint responding: $name ($url)"
        return 0
    else
        log_error "HTTP endpoint failed: $name ($url) - Got $response_code, expected $expected_status"
        return 1
    fi
}

# Function to check database connection
check_database() {
    log_info "Checking PostgreSQL database..."

    if ! check_container "unicorn-postgresql"; then
        return 1
    fi

    # Test database connection
    if docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT 1;" &>/dev/null; then
        log_success "PostgreSQL database accessible"

        # Check table count
        local table_count=$(docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
        log_info "Database has $table_count tables"

        return 0
    else
        log_error "PostgreSQL database connection failed"
        return 1
    fi
}

# Function to check Redis connection
check_redis() {
    log_info "Checking Redis cache..."

    if ! check_container "unicorn-redis"; then
        return 1
    fi

    # Test Redis connection
    if docker exec unicorn-redis redis-cli ping | grep -q "PONG"; then
        log_success "Redis cache accessible"

        # Check memory usage
        local mem_used=$(docker exec unicorn-redis redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
        log_info "Redis memory usage: $mem_used"

        return 0
    else
        log_error "Redis connection failed"
        return 1
    fi
}

# Function to check Keycloak
check_keycloak() {
    log_info "Checking Keycloak authentication..."

    if ! check_container "uchub-keycloak"; then
        return 1
    fi

    # Test Keycloak health endpoint
    local keycloak_url="${KEYCLOAK_URL:-https://auth.unicorncommander.ai}"

    if check_http_endpoint "$keycloak_url/health/ready" 200 "Keycloak Health"; then
        return 0
    else
        log_warning "Keycloak health check failed (may not be exposed)"
        # Try realm endpoint instead
        if check_http_endpoint "$keycloak_url/realms/uchub" 200 "Keycloak Realm"; then
            return 0
        fi
        return 1
    fi
}

# Function to check backend service
check_backend() {
    log_info "Checking Ops-Center backend..."

    if ! check_container "ops-center-direct"; then
        return 1
    fi

    check_container_health "ops-center-direct" || true

    # Test backend health endpoint
    if check_http_endpoint "${BASE_URL}/api/v1/health" 200 "Backend Health"; then
        # Test system status endpoint
        check_http_endpoint "${BASE_URL}/api/v1/system/status" 200 "System Status" || true
        return 0
    else
        return 1
    fi
}

# Function to check frontend service
check_frontend() {
    log_info "Checking Ops-Center frontend..."

    # Test frontend accessibility
    if check_http_endpoint "${BASE_URL}/" 200 "Frontend Homepage"; then
        # Test admin page
        check_http_endpoint "${BASE_URL}/admin" 200 "Admin Dashboard" || true
        return 0
    else
        return 1
    fi
}

# Function to check service logs for errors
check_logs() {
    local container_name=$1
    local minutes=${2:-5}

    log_info "Checking logs for errors: $container_name (last ${minutes}m)"

    local error_count=$(docker logs "$container_name" --since "${minutes}m" 2>&1 | grep -iE "error|exception|fatal" | wc -l)

    if [ "$error_count" -gt 0 ]; then
        log_warning "Found $error_count errors in logs"
        docker logs "$container_name" --since "${minutes}m" 2>&1 | grep -iE "error|exception|fatal" | tail -5
        return 1
    else
        log_success "No errors in recent logs"
        return 0
    fi
}

# Function to wait for service with timeout
wait_for_service() {
    local check_function=$1
    local service_name=$2
    local timeout=$TIMEOUT
    local elapsed=0

    log_info "Waiting for $service_name (timeout: ${timeout}s)..."

    while [ $elapsed -lt $timeout ]; do
        if $check_function; then
            return 0
        fi

        sleep 5
        elapsed=$((elapsed + 5))

        if [ $((elapsed % 15)) -eq 0 ]; then
            log_info "Still waiting... (${elapsed}s elapsed)"
        fi
    done

    log_error "Timeout waiting for $service_name after ${timeout}s"
    return 1
}

# Main health check flow
main() {
    log_info "========================================="
    log_info "Ops-Center Health Check"
    log_info "Environment: $ENVIRONMENT"
    log_info "Service: $SERVICE"
    log_info "Timeout: ${TIMEOUT}s"
    log_info "========================================="

    local checks_passed=0
    local checks_failed=0

    # Check dependencies first
    if [ "$SERVICE" = "all" ] || [ "$SERVICE" = "database" ]; then
        if wait_for_service check_database "PostgreSQL"; then
            ((checks_passed++))
        else
            ((checks_failed++))
        fi
    fi

    if [ "$SERVICE" = "all" ] || [ "$SERVICE" = "redis" ]; then
        if wait_for_service check_redis "Redis"; then
            ((checks_passed++))
        else
            ((checks_failed++))
        fi
    fi

    if [ "$SERVICE" = "all" ] || [ "$SERVICE" = "keycloak" ]; then
        if wait_for_service check_keycloak "Keycloak"; then
            ((checks_passed++))
        else
            ((checks_failed++))
        fi
    fi

    # Check application services
    if [ "$SERVICE" = "all" ] || [ "$SERVICE" = "backend" ]; then
        if wait_for_service check_backend "Backend"; then
            ((checks_passed++))
            check_logs "ops-center-direct" 5 || true
        else
            ((checks_failed++))
        fi
    fi

    if [ "$SERVICE" = "all" ] || [ "$SERVICE" = "frontend" ]; then
        if wait_for_service check_frontend "Frontend"; then
            ((checks_passed++))
        else
            ((checks_failed++))
        fi
    fi

    # Summary
    log_info "========================================="
    log_info "Health Check Summary"
    log_success "Checks passed: $checks_passed"

    if [ $checks_failed -gt 0 ]; then
        log_error "Checks failed: $checks_failed"
        log_error "========================================="
        exit 1
    else
        log_success "All checks passed!"
        log_success "========================================="
        exit 0
    fi
}

# Run main function
main
