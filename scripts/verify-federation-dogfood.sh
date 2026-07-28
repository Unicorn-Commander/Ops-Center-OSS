#!/bin/bash
# =============================================================================
# Federation dogfood READ-ONLY verifier
# -----------------------------------------------------------------------------
# Checks that the commander(consumer) → bigboy(publisher) federation path is
# correctly configured WITHOUT mutating anything on commander. Run from the
# Mac (SSH aliases: `magicunicorn` = bigboy, `commander` = commander).
# Every remote command is a read (psql SELECT, printenv, curl GET) except the
# optional --with-inference flag, which POSTs ONE ~\$0 inference to BIGBOY
# (the dev node) only.
#
# Node ids (verified live 2026-06-11):
#   bigboy    = uc-magicunicorn
#   commander = uc-unicorncommander   (NOT uc-commander — that row is stale)
#
# Usage:  verify-federation-dogfood.sh [--with-inference]
# =============================================================================
set -u

BIGBOY=magicunicorn
COMMANDER=commander
BIGBOY_ID=uc-magicunicorn
COMMANDER_ID=uc-unicorncommander
ORG="${DOGFOOD_ORG_ID:-org_1921b231-c8a0-4dcc-a3bb-2fb512a2e60d}"   # Magic Unicorn
LAGO_RELAY="http://AUTHORITATIVE_NODE_HOST:13000"
PASS=0; FAIL=0

check() {
  if [ "$2" = "0" ]; then echo "  ✅ $1"; PASS=$((PASS+1));
  else echo "  ❌ $1"; FAIL=$((FAIL+1)); fi
}

psql_bigboy() { ssh "$BIGBOY" "docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -tc \"$1\""; }
psql_cmdr()   { ssh "$COMMANDER" "docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -tc \"$1\""; }

echo "== 1. bigboy (publisher) =="
ssh "$BIGBOY" 'docker ps --format "{{.Names}}" | grep -q "^ops-center-direct$"'; check "ops-center-direct running" $?
ssh "$BIGBOY" 'curl -sf -o /dev/null http://localhost:8084/api/v1/federation/health'; check "federation health 200" $?
ssh "$BIGBOY" 'docker exec ops-center-direct test -f /app/federation/trust.py'; check "trust enforcement code deployed" $?
ssh "$BIGBOY" 'docker exec ops-center-direct grep -q gateway_metered /app/federation/metering.py'; check "metering reconciliation deployed" $?
psql_bigboy "SELECT 1 FROM information_schema.columns WHERE table_name='federation_peers' AND column_name='trust_mode';" | grep -q 1; check "migration 009 applied" $?
psql_bigboy "SELECT fp.trust_mode FROM federation_peers fp JOIN federation_nodes l ON l.id=fp.local_node_id JOIN federation_nodes r ON r.id=fp.remote_node_id WHERE l.node_id='$BIGBOY_ID' AND r.node_id='$COMMANDER_ID';" | grep -qE "publisher|scoped|full"; check "bigboy→commander peer row (publisher/scoped/full)" $?
ssh "$BIGBOY" 'docker exec unicorn-litellm printenv LITELLM_SUCCESS_CALLBACK | grep -q lago'; check "bigboy gateway Lago callback on" $?
ssh "$BIGBOY" 'docker exec unicorn-litellm printenv LAGO_API_CHARGE_BY | grep -q user_id'; check "bigboy gateway charge_by=user_id" $?
ssh "$BIGBOY" "docker exec unicorn-litellm printenv LAGO_API_BASE | grep -q 'AUTHORITATIVE_NODE_HOST:13000'"; check "bigboy gateway → UC-1 Hub relay" $?
psql_bigboy "SELECT 1 FROM platform_settings WHERE key='LITELLM_MASTER_KEY';" | grep -q 1; check "gateway master key in platform_settings" $?

echo "== 2. commander (consumer) — READ-ONLY =="
ssh "$COMMANDER" 'docker ps --format "{{.Names}}" | grep -q "^ops-center-direct$"'; check "ops-center-direct running" $?
ssh "$COMMANDER" 'curl -sf -o /dev/null http://localhost:8084/api/v1/federation/health'; check "federation health 200" $?
ssh "$COMMANDER" 'docker exec ops-center-direct test -f /app/federation/trust.py'; check "trust enforcement code deployed (Aaron step A)" $?
ssh "$COMMANDER" 'docker exec ops-center-direct grep -q gateway_metered /app/federation/metering.py 2>/dev/null'; check "metering reconciliation deployed (Aaron step A)" $?
psql_cmdr "SELECT 1 FROM information_schema.columns WHERE table_name='federation_peers' AND column_name='trust_mode';" | grep -q 1; check "migration 009 applied on commander" $?
psql_cmdr "SELECT status FROM federation_nodes WHERE node_id='$BIGBOY_ID';" | grep -qE "online|degraded"; check "commander registry sees bigboy" $?
psql_cmdr "SELECT fp.trust_mode FROM federation_peers fp JOIN federation_nodes l ON l.id=fp.local_node_id JOIN federation_nodes r ON r.id=fp.remote_node_id WHERE l.node_id='$COMMANDER_ID' AND r.node_id='$BIGBOY_ID';" | grep -qE "consumer|scoped|full"; check "commander→bigboy peer row (consumer/scoped/full) (Aaron step B)" $?

echo "== 3. UC-1 Hub Lago (via Tailscale relay; reads from bigboy) =="
ssh "$BIGBOY" "curl -sf -o /dev/null $LAGO_RELAY/health"; check "Lago relay reachable" $?
ssh "$BIGBOY" "K=\$(docker exec unicorn-litellm printenv LAGO_API_KEY); curl -sf -o /dev/null -H \"Authorization: Bearer \$K\" $LAGO_RELAY/api/v1/billable_metrics"; check "Lago API auth works" $?
ssh "$BIGBOY" "K=\$(docker exec unicorn-litellm printenv LAGO_API_KEY); curl -s -H \"Authorization: Bearer \$K\" \"$LAGO_RELAY/api/v1/events?external_subscription_id=$ORG&per_page=1\" | grep -q ai_api_call"; check "org-keyed ai_api_call events exist for dogfood org" $?

if [ "${1:-}" = "--with-inference" ]; then
  echo "== 4. live federated inference (bigboy publisher endpoint, ~\$0) =="
  ssh "$BIGBOY" "FKEY=\$(docker exec ops-center-direct printenv FEDERATION_KEY); curl -s -m 180 -X POST \
    -H \"Authorization: Bearer \$FKEY\" -H 'X-Federation-Node: $COMMANDER_ID' -H 'X-Federation-Org-Id: $ORG' \
    -H 'Content-Type: application/json' \
    -d '{\"service_type\":\"llm\",\"payload\":{\"model\":\"gpt-4o-mini\",\"messages\":[{\"role\":\"user\",\"content\":\"Say OK\"}],\"max_tokens\":4}}' \
    http://localhost:8084/api/v1/federation/inference | python3 -c 'import sys,json; d=json.load(sys.stdin); assert d.get(\"gateway_metered\") is True and d.get(\"org_id\"), d; print(\"  gateway_metered + org-keyed:\", d[\"org_id\"])'"
  check "federated inference returns gateway_metered under org identity" $?
fi

echo
echo "RESULT: $PASS passed, $FAIL failed"
[ "$FAIL" = "0" ]
