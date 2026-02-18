#!/bin/bash
# Integration script for Local Users API
# Adds the new admin-scoped local user management endpoints to server.py

set -e

BACKEND_DIR="/opt/ops-center/backend"
SERVER_FILE="$BACKEND_DIR/server.py"
BACKUP_FILE="$SERVER_FILE.backup.$(date +%Y%m%d_%H%M%S)"

echo "=========================================="
echo "Local Users API Integration Script"
echo "=========================================="
echo ""

# Backup server.py
echo "[1/4] Creating backup of server.py..."
cp "$SERVER_FILE" "$BACKUP_FILE"
echo "  ✓ Backup created: $BACKUP_FILE"
echo ""

# Check if already integrated
if grep -q "from local_users_api import router as admin_local_users_router" "$SERVER_FILE"; then
    echo "[2/4] ⚠️  Import already exists - skipping import step"
else
    echo "[2/4] Adding import statement..."
    # Find the line with "from local_user_api import router as local_user_router"
    # and add the new import right after it
    sed -i '/from local_user_api import router as local_user_router/a from local_users_api import router as admin_local_users_router' "$SERVER_FILE"
    echo "  ✓ Import added"
fi
echo ""

# Check if router already registered
if grep -q "app.include_router(admin_local_users_router)" "$SERVER_FILE"; then
    echo "[3/4] ⚠️  Router already registered - skipping router step"
else
    echo "[3/4] Registering router..."
    # Find the line with existing local_user_router registration
    # and add the new router right after it
    sed -i '/app.include_router(local_user_router)/a \
app.include_router(admin_local_users_router)\
logger.info("Admin Local User Management API endpoints registered at /api/v1/admin/system/local-users")' "$SERVER_FILE"
    echo "  ✓ Router registered"
fi
echo ""

echo "[4/4] Verifying integration..."
if grep -q "from local_users_api import router as admin_local_users_router" "$SERVER_FILE" && \
   grep -q "app.include_router(admin_local_users_router)" "$SERVER_FILE"; then
    echo "  ✓ Integration successful!"
    echo ""
    echo "=========================================="
    echo "✓ INTEGRATION COMPLETE"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Review changes: diff $BACKUP_FILE $SERVER_FILE"
    echo "2. Restart backend: docker restart ops-center-direct"
    echo "3. Test endpoints: curl http://localhost:8084/api/v1/admin/system/local-users"
    echo ""
    echo "Backup location: $BACKUP_FILE"
    echo ""
else
    echo "  ✗ Integration verification failed"
    echo ""
    echo "Rolling back changes..."
    cp "$BACKUP_FILE" "$SERVER_FILE"
    echo "  ✓ Rollback complete"
    exit 1
fi
