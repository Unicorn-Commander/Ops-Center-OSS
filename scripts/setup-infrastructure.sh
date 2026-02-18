#!/bin/bash
# ==============================================================================
# Ops-Center Infrastructure Setup & Deployment Script
# ==============================================================================
#
# Complete setup for Ops-Center on a Docker-based UC-Cloud deployment.
# Handles: prerequisites, database migrations, frontend builds, container
# restart, health checks, and seed data.
#
# Usage:
#   ./scripts/setup-infrastructure.sh              # Full setup
#   ./scripts/setup-infrastructure.sh --migrate    # Database migrations only
#   ./scripts/setup-infrastructure.sh --build      # Frontend build only
#   ./scripts/setup-infrastructure.sh --restart    # Restart container only
#   ./scripts/setup-infrastructure.sh --health     # Health check only
#   ./scripts/setup-infrastructure.sh --seed       # Seed initial data only
#   ./scripts/setup-infrastructure.sh --quick      # Skip npm install, fast rebuild
#
# Options:
#   --skip-backup     Skip database backup before migrations
#   --skip-health     Skip post-deployment health checks
#   --skip-seed       Skip seed data step
#   --force           Force rebuild even if no changes detected
#   --verbose         Show detailed output
#
# ==============================================================================

set -euo pipefail

# ==============================================================================
# Configuration
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPS_CENTER_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="${OPS_CENTER_DIR}/backend"
MIGRATIONS_DIR="${BACKEND_DIR}/migrations"
PUBLIC_DIR="${OPS_CENTER_DIR}/public"
BACKUP_DIR="${OPS_CENTER_DIR}/backups"

CONTAINER_NAME="ops-center-direct"
DB_CONTAINER="unicorn-postgresql"
REDIS_CONTAINER="unicorn-redis"
KEYCLOAK_CONTAINER="uchub-keycloak"

DB_USER="${POSTGRES_USER:-unicorn}"
DB_NAME="${POSTGRES_DB:-unicorn_db}"

HEALTH_CHECK_URL="${HEALTH_CHECK_URL:-http://localhost:8084}"
HEALTH_CHECK_TIMEOUT=60
HEALTH_CHECK_INTERVAL=5

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Flags
MODE="full"
SKIP_BACKUP=false
SKIP_HEALTH=false
SKIP_SEED=false
FORCE=false
VERBOSE=false
QUICK=false

# Counters
STEPS_TOTAL=0
STEPS_PASSED=0
STEPS_FAILED=0
STEPS_SKIPPED=0
START_TIME=$(date +%s)

# ==============================================================================
# Parse Arguments
# ==============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --migrate)     MODE="migrate";  shift ;;
        --build)       MODE="build";    shift ;;
        --restart)     MODE="restart";  shift ;;
        --health)      MODE="health";   shift ;;
        --seed)        MODE="seed";     shift ;;
        --quick)       QUICK=true;      shift ;;
        --skip-backup) SKIP_BACKUP=true; shift ;;
        --skip-health) SKIP_HEALTH=true; shift ;;
        --skip-seed)   SKIP_SEED=true;  shift ;;
        --force)       FORCE=true;      shift ;;
        --verbose)     VERBOSE=true;    shift ;;
        --help|-h)
            head -30 "$0" | grep "^#" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run with --help for usage"
            exit 1
            ;;
    esac
done

# ==============================================================================
# Logging
# ==============================================================================

log_header() {
    echo ""
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}${BOLD}  $1${NC}"
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

log_step() {
    STEPS_TOTAL=$((STEPS_TOTAL + 1))
    echo -e "\n${CYAN}[$STEPS_TOTAL]${NC} ${BOLD}$1${NC}"
}

log_ok() {
    STEPS_PASSED=$((STEPS_PASSED + 1))
    echo -e "  ${GREEN}[OK]${NC} $1"
}

log_fail() {
    STEPS_FAILED=$((STEPS_FAILED + 1))
    echo -e "  ${RED}[FAIL]${NC} $1"
}

log_warn() {
    echo -e "  ${YELLOW}[WARN]${NC} $1"
}

log_skip() {
    STEPS_SKIPPED=$((STEPS_SKIPPED + 1))
    echo -e "  ${YELLOW}[SKIP]${NC} $1"
}

log_info() {
    echo -e "  ${BLUE}[INFO]${NC} $1"
}

log_detail() {
    if [ "$VERBOSE" = true ]; then
        echo -e "        $1"
    fi
}

# ==============================================================================
# Utility Functions
# ==============================================================================

container_running() {
    docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${1}$"
}

run_sql() {
    docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "$1" 2>&1
}

run_sql_file() {
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" < "$1" 2>&1
}

table_exists() {
    local result
    result=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema='public' AND table_name='$1');" 2>/dev/null)
    [ "$result" = "t" ]
}

# ==============================================================================
# Step 1: Prerequisites Check
# ==============================================================================

check_prerequisites() {
    log_step "Checking prerequisites"

    # Docker
    if command -v docker &>/dev/null && docker info &>/dev/null; then
        log_ok "Docker: $(docker --version | grep -oP '\d+\.\d+\.\d+')"
    else
        log_fail "Docker is not running"
        return 1
    fi

    # Docker Compose
    if docker compose version &>/dev/null; then
        log_ok "Docker Compose: $(docker compose version --short)"
    else
        log_fail "Docker Compose not available"
        return 1
    fi

    # PostgreSQL container
    if container_running "$DB_CONTAINER"; then
        local db_version
        db_version=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -tAc "SELECT version();" 2>/dev/null | grep -oP 'PostgreSQL \d+\.\d+' || echo "unknown")
        log_ok "PostgreSQL: $db_version"
    else
        log_fail "PostgreSQL container ($DB_CONTAINER) not running"
        return 1
    fi

    # Redis container
    if container_running "$REDIS_CONTAINER"; then
        log_ok "Redis: running"
    else
        log_warn "Redis container ($REDIS_CONTAINER) not running (non-fatal)"
    fi

    # Keycloak container
    if container_running "$KEYCLOAK_CONTAINER"; then
        log_ok "Keycloak: running"
    else
        log_warn "Keycloak container ($KEYCLOAK_CONTAINER) not running (non-fatal)"
    fi

    # Node.js (for frontend builds)
    if command -v node &>/dev/null; then
        log_ok "Node.js: $(node --version)"
    else
        log_warn "Node.js not found (needed for frontend builds)"
    fi

    # npm
    if command -v npm &>/dev/null; then
        log_ok "npm: $(npm --version)"
    else
        log_warn "npm not found (needed for frontend builds)"
    fi

    # Disk space (need at least 2GB free)
    local avail_gb
    avail_gb=$(df -BG "$OPS_CENTER_DIR" | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$avail_gb" -ge 2 ]; then
        log_ok "Disk space: ${avail_gb}GB available"
    else
        log_fail "Insufficient disk space: ${avail_gb}GB (need 2GB+)"
        return 1
    fi

    return 0
}

# ==============================================================================
# Step 2: Database Backup
# ==============================================================================

backup_database() {
    if [ "$SKIP_BACKUP" = true ]; then
        log_skip "Database backup (--skip-backup)"
        return 0
    fi

    log_step "Backing up database"

    mkdir -p "$BACKUP_DIR"
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/db_backup_${timestamp}.sql.gz"

    if container_running "$DB_CONTAINER"; then
        docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" 2>/dev/null | gzip > "$backup_file"
        if [ -s "$backup_file" ]; then
            local size
            size=$(du -h "$backup_file" | cut -f1)
            log_ok "Backup created: $backup_file ($size)"

            # Keep only last 5 backups
            local count
            count=$(ls -1 "$BACKUP_DIR"/db_backup_*.sql.gz 2>/dev/null | wc -l)
            if [ "$count" -gt 5 ]; then
                ls -1t "$BACKUP_DIR"/db_backup_*.sql.gz | tail -n +6 | xargs rm -f
                log_info "Cleaned old backups (kept last 5)"
            fi
        else
            rm -f "$backup_file"
            log_warn "Backup file was empty, skipped"
        fi
    else
        log_fail "PostgreSQL not running, cannot backup"
        return 1
    fi

    return 0
}

# ==============================================================================
# Step 3: Database Migrations
# ==============================================================================

run_migrations() {
    log_step "Running database migrations"

    if [ ! -d "$MIGRATIONS_DIR" ]; then
        log_fail "Migrations directory not found: $MIGRATIONS_DIR"
        return 1
    fi

    # Create migrations tracking table if it doesn't exist
    run_sql "CREATE TABLE IF NOT EXISTS _migration_history (
        id SERIAL PRIMARY KEY,
        filename VARCHAR(255) NOT NULL UNIQUE,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        checksum VARCHAR(64)
    );" >/dev/null 2>&1

    # Ensure uuid-ossp extension exists (needed by many migrations)
    run_sql 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";' >/dev/null 2>&1

    # Define migration order - foundational schemas first, then features
    # All migrations use IF NOT EXISTS / IF EXISTS so they're safe to re-run
    local -a MIGRATION_ORDER=(
        # Core infrastructure
        "001_organization_tables.sql"
        "001_create_permissions.sql"
        "001_model_servers.sql"
        "001_create_tier_model_access.sql"

        # Phase 2 schemas
        "002_add_system_api_keys.sql"
        "002_two_factor_policies.sql"
        "002_migrate_jsonb_to_tier_model_access.sql"

        # Phase 3 schemas
        "003_add_service_organizations.sql"
        "003_add_service_organizations_fixed.sql"
        "003_service_orgs_final.sql"
        "003_fix_schema_mismatches.sql"
        "003_notification_preferences.sql"
        "003_populate_tier_model_access.sql"

        # Phase 4+
        "004_notification_history.sql"
        "005_email_providers.sql"
        "006_add_white_label_config.sql"
        "006_permission_audit_log.sql"
        "007_user_execution_servers.sql"
        "008_system_settings_schema.sql"

        # Feature schemas (alphabetical)
        "add_credit_purchases.sql"
        "add_email_notifications_column.sql"
        "add_llm_markup_percentage.sql"
        "add_models_table.sql"
        "add_org_tier_id.sql"
        "add_subscription_changes_table.sql"
        "add_subscription_tiers.sql"
        "add_vip_founder_tier.sql"
        "alert_triggers_schema.sql"
        "alerts_schema.sql"
        "assign_vip_founder_to_aaron.sql"
        "audit_log_schema.sql"
        "create_byok_keys_table.sql"
        "create_credit_system_tables.sql"
        "create_dynamic_pricing.sql"
        "create_email_logs_table.sql"
        "create_invite_codes.sql"
        "create_llm_management_tables.sql"
        "create_llm_management_tables_v2.sql"
        "create_llm_tables.sql"
        "create_org_billing.sql"
        "model_lists_schema.sql"
        "org_features_schema.sql"
        "performance_indexes.sql"
        "rename_features_to_apps.sql"
        "seed_tier_rules.sql"
        "service_api_keys_schema.sql"
        "subscription_history_schema.sql"
        "usage_tracking_schema.sql"
        "webhooks_schema.sql"

        # Infrastructure schemas
        "local_inference_schema.sql"
        "colonel_schema.sql"
        "granite_api_keys_schema.sql"
        "crisis_ops_registration.sql"
    )

    local applied=0
    local skipped=0
    local failed=0

    for migration in "${MIGRATION_ORDER[@]}"; do
        local filepath="${MIGRATIONS_DIR}/${migration}"

        # Skip if file doesn't exist
        if [ ! -f "$filepath" ]; then
            log_detail "Not found: $migration"
            continue
        fi

        # Check if already applied
        local already_applied
        already_applied=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
            "SELECT COUNT(*) FROM _migration_history WHERE filename='$migration';" 2>/dev/null || echo "0")

        if [ "$already_applied" = "1" ] && [ "$FORCE" != true ]; then
            skipped=$((skipped + 1))
            log_detail "Already applied: $migration"
            continue
        fi

        # Run migration
        log_info "Applying: $migration"
        local output
        if output=$(run_sql_file "$filepath" 2>&1); then
            # Record in history
            local checksum
            checksum=$(md5sum "$filepath" | cut -d' ' -f1)
            run_sql "INSERT INTO _migration_history (filename, checksum) VALUES ('$migration', '$checksum') ON CONFLICT (filename) DO UPDATE SET applied_at=CURRENT_TIMESTAMP, checksum='$checksum';" >/dev/null 2>&1
            applied=$((applied + 1))
        else
            # Many migrations use IF NOT EXISTS, so errors about existing objects are fine
            if echo "$output" | grep -qiE "already exists|duplicate key|relation.*already"; then
                # Record as applied anyway since the schema already exists
                local checksum
                checksum=$(md5sum "$filepath" | cut -d' ' -f1)
                run_sql "INSERT INTO _migration_history (filename, checksum) VALUES ('$migration', '$checksum') ON CONFLICT (filename) DO UPDATE SET applied_at=CURRENT_TIMESTAMP, checksum='$checksum';" >/dev/null 2>&1
                skipped=$((skipped + 1))
                log_detail "Schema already exists: $migration"
            else
                failed=$((failed + 1))
                log_warn "Failed: $migration"
                if [ "$VERBOSE" = true ]; then
                    echo "$output" | head -5
                fi
            fi
        fi
    done

    # Also run any migrations not in the ordered list (new files)
    for filepath in "$MIGRATIONS_DIR"/*.sql; do
        local migration
        migration=$(basename "$filepath")

        # Skip rollback files
        if echo "$migration" | grep -qi "rollback"; then
            continue
        fi

        # Skip if already in our ordered list
        local in_list=false
        for ordered in "${MIGRATION_ORDER[@]}"; do
            if [ "$migration" = "$ordered" ]; then
                in_list=true
                break
            fi
        done
        if [ "$in_list" = true ]; then
            continue
        fi

        # Check if already applied
        local already_applied
        already_applied=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
            "SELECT COUNT(*) FROM _migration_history WHERE filename='$migration';" 2>/dev/null || echo "0")

        if [ "$already_applied" = "1" ] && [ "$FORCE" != true ]; then
            skipped=$((skipped + 1))
            continue
        fi

        log_info "Applying (unordered): $migration"
        if output=$(run_sql_file "$filepath" 2>&1); then
            local checksum
            checksum=$(md5sum "$filepath" | cut -d' ' -f1)
            run_sql "INSERT INTO _migration_history (filename, checksum) VALUES ('$migration', '$checksum') ON CONFLICT (filename) DO UPDATE SET applied_at=CURRENT_TIMESTAMP, checksum='$checksum';" >/dev/null 2>&1
            applied=$((applied + 1))
        else
            if echo "$output" | grep -qiE "already exists|duplicate key|relation.*already"; then
                local checksum
                checksum=$(md5sum "$filepath" | cut -d' ' -f1)
                run_sql "INSERT INTO _migration_history (filename, checksum) VALUES ('$migration', '$checksum') ON CONFLICT (filename) DO UPDATE SET applied_at=CURRENT_TIMESTAMP, checksum='$checksum';" >/dev/null 2>&1
                skipped=$((skipped + 1))
            else
                failed=$((failed + 1))
                log_warn "Failed: $migration"
            fi
        fi
    done

    # Get table count
    local table_count
    table_count=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null || echo "?")

    if [ "$failed" -eq 0 ]; then
        log_ok "Migrations complete: $applied applied, $skipped already up-to-date ($table_count tables)"
    else
        log_warn "Migrations: $applied applied, $skipped skipped, $failed failed ($table_count tables)"
    fi

    return 0
}

# ==============================================================================
# Step 4: Frontend Build
# ==============================================================================

build_frontend() {
    log_step "Building frontend"

    cd "$OPS_CENTER_DIR"

    # Check if package.json exists
    if [ ! -f "package.json" ]; then
        log_fail "package.json not found in $OPS_CENTER_DIR"
        return 1
    fi

    # Install dependencies (skip if --quick and node_modules exists)
    if [ "$QUICK" = true ] && [ -d "node_modules" ]; then
        log_info "Quick mode: skipping npm install"
    else
        log_info "Installing npm dependencies..."
        if npm install --no-audit --no-fund 2>&1 | tail -3; then
            log_ok "Dependencies installed"
        else
            log_fail "npm install failed"
            return 1
        fi
    fi

    # Clear Vite cache
    rm -rf node_modules/.vite dist 2>/dev/null || true

    # Build
    log_info "Building production bundle..."
    if npm run build:skip-verify 2>&1 | tail -5; then
        log_ok "Frontend built successfully"
    else
        log_fail "Frontend build failed"
        return 1
    fi

    # Deploy to public/
    if [ -d "dist" ]; then
        log_info "Deploying to public/..."
        # Preserve logos and other static assets that aren't part of the build
        cp -r dist/* "$PUBLIC_DIR/" 2>/dev/null || true

        local bundle_size
        bundle_size=$(du -sh dist/ | cut -f1)
        local asset_count
        asset_count=$(find dist/assets -name '*.js' 2>/dev/null | wc -l)
        log_ok "Deployed: $bundle_size ($asset_count JS bundles)"
    else
        log_fail "dist/ directory not created"
        return 1
    fi

    return 0
}

# ==============================================================================
# Step 5: Restart Container
# ==============================================================================

restart_container() {
    log_step "Restarting Ops-Center container"

    if container_running "$CONTAINER_NAME"; then
        log_info "Restarting $CONTAINER_NAME..."
        docker restart "$CONTAINER_NAME" 2>&1
        log_ok "Container restarted"
    else
        log_info "Container not running, starting..."
        cd "$OPS_CENTER_DIR"
        if [ -f "docker-compose.direct.yml" ]; then
            docker compose -f docker-compose.direct.yml up -d 2>&1
            log_ok "Container started"
        else
            log_fail "docker-compose.direct.yml not found"
            return 1
        fi
    fi

    # Wait for container to be ready
    log_info "Waiting for container startup..."
    local elapsed=0
    while [ $elapsed -lt 15 ]; do
        if container_running "$CONTAINER_NAME"; then
            sleep 2
            log_ok "Container is running"
            return 0
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done

    log_fail "Container failed to start within 15 seconds"
    return 1
}

# ==============================================================================
# Step 6: Health Checks
# ==============================================================================

run_health_checks() {
    if [ "$SKIP_HEALTH" = true ]; then
        log_skip "Health checks (--skip-health)"
        return 0
    fi

    log_step "Running health checks"

    local checks_passed=0
    local checks_failed=0

    # Wait for the API to respond
    log_info "Waiting for API to respond..."
    local elapsed=0
    local api_ready=false
    while [ $elapsed -lt $HEALTH_CHECK_TIMEOUT ]; do
        if curl -sf "${HEALTH_CHECK_URL}/api/v1/health" >/dev/null 2>&1; then
            api_ready=true
            break
        fi
        sleep $HEALTH_CHECK_INTERVAL
        elapsed=$((elapsed + HEALTH_CHECK_INTERVAL))
        if [ $((elapsed % 15)) -eq 0 ]; then
            log_detail "Still waiting... (${elapsed}s)"
        fi
    done

    if [ "$api_ready" = true ]; then
        log_ok "API health endpoint responding (${elapsed}s)"
        checks_passed=$((checks_passed + 1))
    else
        log_fail "API health endpoint not responding after ${HEALTH_CHECK_TIMEOUT}s"
        checks_failed=$((checks_failed + 1))
    fi

    # Check system status endpoint
    local status_code
    status_code=$(curl -so /dev/null -w "%{http_code}" --max-time 10 "${HEALTH_CHECK_URL}/api/v1/system/status" 2>/dev/null || echo "000")
    if [ "$status_code" = "200" ]; then
        log_ok "System status endpoint: 200 OK"
        checks_passed=$((checks_passed + 1))
    else
        log_warn "System status endpoint: $status_code"
        checks_failed=$((checks_failed + 1))
    fi

    # Check frontend serving
    status_code=$(curl -so /dev/null -w "%{http_code}" --max-time 10 "${HEALTH_CHECK_URL}/" 2>/dev/null || echo "000")
    if [ "$status_code" = "200" ]; then
        log_ok "Frontend serving: 200 OK"
        checks_passed=$((checks_passed + 1))
    else
        log_warn "Frontend serving: $status_code"
        checks_failed=$((checks_failed + 1))
    fi

    # Database connectivity
    if run_sql "SELECT 1;" >/dev/null 2>&1; then
        log_ok "Database connectivity: OK"
        checks_passed=$((checks_passed + 1))
    else
        log_fail "Database connectivity: FAILED"
        checks_failed=$((checks_failed + 1))
    fi

    # Redis connectivity
    if container_running "$REDIS_CONTAINER"; then
        if docker exec "$REDIS_CONTAINER" redis-cli ping 2>/dev/null | grep -q "PONG"; then
            log_ok "Redis connectivity: OK"
            checks_passed=$((checks_passed + 1))
        else
            log_warn "Redis connectivity: FAILED"
            checks_failed=$((checks_failed + 1))
        fi
    fi

    # Check container logs for recent errors
    local error_count
    error_count=$(docker logs "$CONTAINER_NAME" --since 2m 2>&1 | grep -ciE "error|exception|traceback" || true)
    if [ "$error_count" -le 2 ]; then
        log_ok "Container logs: clean ($error_count issues)"
    else
        log_warn "Container logs: $error_count errors in last 2 minutes"
    fi

    log_info "Health: $checks_passed passed, $checks_failed failed"

    if [ "$checks_failed" -gt 1 ]; then
        return 1
    fi
    return 0
}

# ==============================================================================
# Step 7: Seed Initial Data
# ==============================================================================

seed_data() {
    if [ "$SKIP_SEED" = true ]; then
        log_skip "Seed data (--skip-seed)"
        return 0
    fi

    log_step "Checking seed data"

    local seeded=0

    # Check if subscription tiers exist
    local tier_count
    tier_count=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
        "SELECT COUNT(*) FROM subscription_tiers;" 2>/dev/null || echo "0")
    if [ "$tier_count" -gt 0 ]; then
        log_ok "Subscription tiers: $tier_count tiers configured"
    else
        log_info "No subscription tiers found - run tier migrations first"
    fi

    # Check if add_ons/apps exist
    local apps_count
    apps_count=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
        "SELECT COUNT(*) FROM add_ons;" 2>/dev/null || echo "0")
    if [ "$apps_count" -gt 0 ]; then
        log_ok "Apps/Add-ons: $apps_count configured"
    else
        log_info "No apps configured yet"
    fi

    # Check if model lists are seeded
    local model_list_count
    model_list_count=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
        "SELECT COUNT(*) FROM app_model_lists;" 2>/dev/null || echo "0")
    if [ "$model_list_count" -gt 0 ]; then
        log_ok "Model lists: $model_list_count lists configured"
    else
        # Try to run seed script if it exists
        if [ -f "${BACKEND_DIR}/scripts/seed_model_lists.py" ]; then
            log_info "Seeding model lists..."
            docker exec "$CONTAINER_NAME" python3 /app/scripts/seed_model_lists.py 2>&1 | tail -3 || true
            seeded=$((seeded + 1))
        fi
    fi

    # Check organizations
    local org_count
    org_count=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
        "SELECT COUNT(*) FROM organizations;" 2>/dev/null || echo "0")
    log_ok "Organizations: $org_count configured"

    # Overall table statistics
    local table_count
    table_count=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null || echo "?")
    log_ok "Database: $table_count tables total"

    return 0
}

# ==============================================================================
# Summary
# ==============================================================================

print_summary() {
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - START_TIME))

    echo ""
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}${BOLD}  Summary${NC}"
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    echo -e "  Mode:     ${CYAN}$MODE${NC}"
    echo -e "  Duration: ${CYAN}${duration}s${NC}"
    echo -e "  Steps:    ${GREEN}$STEPS_PASSED passed${NC}, ${RED}$STEPS_FAILED failed${NC}, ${YELLOW}$STEPS_SKIPPED skipped${NC}"

    if [ "$STEPS_FAILED" -eq 0 ]; then
        echo ""
        echo -e "  ${GREEN}${BOLD}Infrastructure setup completed successfully!${NC}"
        echo ""
        echo -e "  ${BOLD}Access:${NC}"
        echo -e "    Dashboard:  ${CYAN}https://unicorncommander.ai/admin${NC}"
        echo -e "    API:        ${CYAN}https://unicorncommander.ai/api/v1/health${NC}"
        echo -e "    Local:      ${CYAN}http://localhost:8084${NC}"
    else
        echo ""
        echo -e "  ${RED}${BOLD}Setup completed with $STEPS_FAILED failures. Check output above.${NC}"
        echo ""
        echo -e "  ${BOLD}Troubleshooting:${NC}"
        echo -e "    Logs:       docker logs $CONTAINER_NAME --tail 50"
        echo -e "    DB:         docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME"
        echo -e "    Health:     $0 --health --verbose"
    fi

    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# ==============================================================================
# Main
# ==============================================================================

main() {
    log_header "Ops-Center Infrastructure Setup"
    echo -e "  Mode: ${CYAN}${BOLD}$MODE${NC}  |  Quick: $QUICK  |  Force: $FORCE"
    echo -e "  Directory: $OPS_CENTER_DIR"

    case "$MODE" in
        full)
            check_prerequisites || exit 1
            backup_database || true
            run_migrations
            build_frontend
            restart_container
            run_health_checks || true
            seed_data || true
            ;;
        migrate)
            check_prerequisites || exit 1
            backup_database || true
            run_migrations
            ;;
        build)
            build_frontend
            ;;
        restart)
            restart_container
            run_health_checks || true
            ;;
        health)
            check_prerequisites || true
            run_health_checks
            ;;
        seed)
            check_prerequisites || exit 1
            seed_data
            ;;
        *)
            echo "Unknown mode: $MODE"
            exit 1
            ;;
    esac

    print_summary

    if [ "$STEPS_FAILED" -gt 0 ]; then
        exit 1
    fi
}

main
