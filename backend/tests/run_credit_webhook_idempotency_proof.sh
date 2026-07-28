#!/bin/bash
#############################################################################
# Proof: credit-purchase webhook idempotency / exactly-once grant.
#
# Spins a THROWAWAY postgres:16 container (never a real DB), builds the minimal
# schema, and drives the REAL credit_system.allocate_credits_on_conn() through the
# patched webhook transaction body to prove: single-grant, duplicate no-op,
# concurrent-race single-grant, and mid-grant-failure rollback + safe retry.
#
# Exit: 0 = proof passed, 1 = a proof assertion failed, 3 = docker unavailable.
#############################################################################
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
    echo -e "${YELLOW}docker unavailable - cannot run throwaway-postgres proof${NC}"
    exit 3
fi

CONTAINER="oc-credit-webhook-proof-$$"
# Pick a free ephemeral host port (avoid collisions with other services)
PGPORT="$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1]);s.close()')"
PGPW="proofpw"

cleanup() { docker rm -f "$CONTAINER" >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "Starting throwaway postgres:16 ($CONTAINER) on :$PGPORT ..."
docker run -d --rm --name "$CONTAINER" \
    -e POSTGRES_PASSWORD="$PGPW" -e POSTGRES_DB=proofdb \
    -p ${PGPORT}:5432 postgres:16 >/dev/null

# Wait for readiness
for i in $(seq 1 30); do
    if docker exec "$CONTAINER" pg_isready -U postgres >/dev/null 2>&1; then break; fi
    sleep 1
    if [ "$i" = "30" ]; then echo -e "${RED}postgres did not become ready${NC}"; exit 1; fi
done
sleep 1

export DATABASE_URL="postgresql://postgres:${PGPW}@127.0.0.1:${PGPORT}/proofdb"
export OC_BACKEND="$BACKEND_DIR"

# Ensure asyncpg is importable
python3 -c "import asyncpg" 2>/dev/null || { echo "installing asyncpg..."; pip install -q asyncpg; }

echo "Running proof harness ..."
set +e
python3 "$SCRIPT_DIR/credit_webhook_idempotency_proof.py"
RC=$?
set -e

if [ "$RC" = "0" ]; then
    echo -e "${GREEN}PROOF PASSED${NC}"
else
    echo -e "${RED}PROOF FAILED (rc=$RC)${NC}"
fi
exit $RC
