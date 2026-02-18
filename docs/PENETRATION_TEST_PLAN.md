# Credential Management System - Penetration Test Plan

**Project**: UC-Cloud Ops-Center
**Date**: October 23, 2025
**Test Environment**: https://unicorncommander.ai (Production) OR http://localhost:8084 (Local)
**Tester**: Security Team
**Duration**: 2 hours

---

## Overview

This document provides step-by-step penetration testing procedures for the credential management system. All tests should be run after security fixes are implemented.

**Test Categories**:
1. Authentication & Authorization
2. Input Validation (SQL Injection, XSS)
3. Credential Security (Encryption, Masking)
4. Rate Limiting & DoS Protection
5. Error Handling & Information Disclosure
6. Audit Logging

---

## Prerequisites

**Tools Required**:
- `curl` (command-line HTTP client)
- `jq` (JSON processor)
- Browser with Developer Tools
- PostgreSQL client
- Admin session cookie

**Get Admin Session Cookie**:
```bash
# 1. Login to Ops-Center via browser
open https://unicorncommander.ai

# 2. Open DevTools → Application → Cookies
# 3. Copy session cookie value

# 4. Set environment variable
export SESSION_COOKIE="session=your_cookie_value_here"
```

**Set Test Variables**:
```bash
# For production testing
export API_BASE="https://unicorncommander.ai/api/v1/credentials"

# For local testing
export API_BASE="http://localhost:8084/api/v1/credentials"
```

---

## Test Suite 1: Authentication & Authorization

### Test 1.1: Unauthenticated Access (SHOULD FAIL)

**Objective**: Verify all endpoints require authentication

**Test**:
```bash
# Attempt to list credentials without authentication
curl -X GET "$API_BASE" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n"

# Expected: 401 Unauthorized
# Actual:
```

**Pass Criteria**: ✅ 401 Unauthorized response

**Result**: [ ] PASS [ ] FAIL

---

### Test 1.2: Invalid Session Cookie (SHOULD FAIL)

**Objective**: Verify invalid sessions are rejected

**Test**:
```bash
# Attempt with fake session cookie
curl -X GET "$API_BASE" \
  -H "Cookie: session=fake_invalid_session_12345" \
  -w "\nHTTP Status: %{http_code}\n"

# Expected: 401 Unauthorized
# Actual:
```

**Pass Criteria**: ✅ 401 Unauthorized response

**Result**: [ ] PASS [ ] FAIL

---

### Test 1.3: Authenticated Access (SHOULD SUCCEED)

**Objective**: Verify valid sessions are accepted

**Test**:
```bash
# List credentials with valid session
curl -X GET "$API_BASE" \
  -H "Cookie: $SESSION_COOKIE" \
  -w "\nHTTP Status: %{http_code}\n" | jq

# Expected: 200 OK with credential list
# Actual:
```

**Pass Criteria**: ✅ 200 OK response with JSON array

**Result**: [ ] PASS [ ] FAIL

---

## Test Suite 2: Input Validation

### Test 2.1: SQL Injection in Service Name (SHOULD FAIL)

**Objective**: Verify parameterized queries prevent SQL injection

**Test**:
```bash
# Attempt SQL injection
curl -X POST "$API_BASE" \
  -H "Content-Type: application/json" \
  -H "Cookie: $SESSION_COOKIE" \
  -d '{
    "service": "cloudflare; DROP TABLE service_credentials; --",
    "credential_type": "api_token",
    "value": "test_value_12345"
  }' \
  -w "\nHTTP Status: %{http_code}\n" | jq

# Expected: 400 Bad Request (Pydantic validation error)
# Should NOT execute SQL DROP command
# Actual:
```

**Pass Criteria**: ✅ 400 Bad Request with validation error

**Verification**:
```bash
# Verify table still exists
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "\dt service_credentials"

# Expected: Table exists
```

**Result**: [ ] PASS [ ] FAIL

---

### Test 2.2: XSS in Metadata Description (SHOULD BE SANITIZED)

**Objective**: Verify metadata fields are sanitized to prevent XSS

**Test**:
```bash
# Attempt XSS injection
curl -X POST "$API_BASE" \
  -H "Content-Type: application/json" \
  -H "Cookie: $SESSION_COOKIE" \
  -d '{
    "service": "cloudflare",
    "credential_type": "api_token",
    "value": "cf_test_token_xss_prevention_12345",
    "metadata": {
      "description": "<script>alert(\"XSS Attack\")</script>Production Token"
    }
  }' \
  -w "\nHTTP Status: %{http_code}\n" | jq

# Expected: 201 Created
# Description should be: "Production Token" (script tags stripped)
# Actual:
```

**Pass Criteria**: ✅ Script tags stripped from description

**Verification**:
```bash
# Retrieve credential
curl -X GET "$API_BASE/cloudflare/api_token" \
  -H "Cookie: $SESSION_COOKIE" | jq '.metadata.description'

# Expected: "Production Token" (NO <script> tags)
```

**Result**: [ ] PASS [ ] FAIL

**Cleanup**:
```bash
# Delete test credential
curl -X DELETE "$API_BASE/cloudflare/api_token" \
  -H "Cookie: $SESSION_COOKIE"
```

---

### Test 2.3: Invalid Service Name (SHOULD FAIL)

**Objective**: Verify only whitelisted services are accepted

**Test**:
```bash
# Attempt unsupported service
curl -X POST "$API_BASE" \
  -H "Content-Type: application/json" \
  -H "Cookie: $SESSION_COOKIE" \
  -d '{
    "service": "fake_service_not_supported",
    "credential_type": "api_token",
    "value": "test_value"
  }' \
  -w "\nHTTP Status: %{http_code}\n" | jq

# Expected: 400 Bad Request with "Unsupported service" error
# Actual:
```

**Pass Criteria**: ✅ 400 Bad Request with service validation error

**Result**: [ ] PASS [ ] FAIL

---

### Test 2.4: Invalid Credential Type (SHOULD FAIL)

**Objective**: Verify credential types validated per service

**Test**:
```bash
# Attempt invalid credential type for Cloudflare
curl -X POST "$API_BASE" \
  -H "Content-Type: application/json" \
  -H "Cookie: $SESSION_COOKIE" \
  -d '{
    "service": "cloudflare",
    "credential_type": "fake_invalid_type",
    "value": "test_value"
  }' \
  -w "\nHTTP Status: %{http_code}\n" | jq

# Expected: 400 Bad Request with "Invalid credential type" error
# Actual:
```

**Pass Criteria**: ✅ 400 Bad Request with type validation error

**Result**: [ ] PASS [ ] FAIL

---

## Test Suite 3: Credential Security

### Test 3.1: Credential Encryption in Database

**Objective**: Verify credentials are encrypted at rest

**Test**:
```bash
# Create test credential
curl -X POST "$API_BASE" \
  -H "Content-Type: application/json" \
  -H "Cookie: $SESSION_COOKIE" \
  -d '{
    "service": "cloudflare",
    "credential_type": "api_token",
    "value": "cf_PLAINTEXT_SECRET_VALUE_12345",
    "metadata": {"description": "Test encryption"}
  }' | jq

# Check database for encrypted value
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT encrypted_value FROM service_credentials WHERE service = 'cloudflare' ORDER BY created_at DESC LIMIT 1;"

# Expected: Encrypted Fernet string (starts with "gAAAAA...")
# NOT: "cf_PLAINTEXT_SECRET_VALUE_12345"
# Actual:
```

**Pass Criteria**: ✅ Database contains encrypted value, NOT plaintext

**Result**: [ ] PASS [ ] FAIL

**Cleanup**:
```bash
curl -X DELETE "$API_BASE/cloudflare/api_token" -H "Cookie: $SESSION_COOKIE"
```

---

### Test 3.2: Credential Masking in API Responses

**Objective**: Verify credentials NEVER returned as plaintext

**Test**:
```bash
# Create credential with known value
KNOWN_SECRET="cf_KNOWN_SECRET_VALUE_abcdefghijklmnopqrstuvwxyz"

RESPONSE=$(curl -s -X POST "$API_BASE" \
  -H "Content-Type: application/json" \
  -H "Cookie: $SESSION_COOKIE" \
  -d "{
    \"service\": \"cloudflare\",
    \"credential_type\": \"api_token\",
    \"value\": \"$KNOWN_SECRET\",
    \"metadata\": {\"description\": \"Masking test\"}
  }")

echo "$RESPONSE" | jq

# Check if response contains plaintext secret
if echo "$RESPONSE" | grep -q "$KNOWN_SECRET"; then
  echo "❌ FAILED: Plaintext secret found in response!"
  exit 1
else
  echo "✅ PASSED: Plaintext secret not in response"
fi

# Verify masked value present
echo "$RESPONSE" | jq '.masked_value'

# Expected: "cf_KN***xyz" or similar masked format
# NOT: "cf_KNOWN_SECRET_VALUE_abcdefghijklmnopqrstuvwxyz"
# Actual:
```

**Pass Criteria**: ✅ Response contains masked_value only, NOT plaintext

**Result**: [ ] PASS [ ] FAIL

**Cleanup**:
```bash
curl -X DELETE "$API_BASE/cloudflare/api_token" -H "Cookie: $SESSION_COOKIE"
```

---

### Test 3.3: List Credentials Masking

**Objective**: Verify list endpoint also returns masked values

**Test**:
```bash
# Create multiple credentials
curl -s -X POST "$API_BASE" \
  -H "Content-Type: application/json" \
  -H "Cookie: $SESSION_COOKIE" \
  -d '{
    "service": "cloudflare",
    "credential_type": "api_token",
    "value": "cf_SECRET_CLOUDFLARE_TOKEN_12345"
  }' > /dev/null

curl -s -X POST "$API_BASE" \
  -H "Content-Type: application/json" \
  -H "Cookie: $SESSION_COOKIE" \
  -d '{
    "service": "github",
    "credential_type": "api_token",
    "value": "ghp_SECRET_GITHUB_TOKEN_67890"
  }' > /dev/null

# List all credentials
LIST_RESPONSE=$(curl -s -X GET "$API_BASE" -H "Cookie: $SESSION_COOKIE")

echo "$LIST_RESPONSE" | jq

# Verify NO plaintext secrets in list
if echo "$LIST_RESPONSE" | grep -E "(cf_SECRET|ghp_SECRET)"; then
  echo "❌ FAILED: Plaintext secrets found in list!"
  exit 1
else
  echo "✅ PASSED: No plaintext secrets in list"
fi

# Verify all have masked_value
echo "$LIST_RESPONSE" | jq '.[].masked_value'

# Expected: All entries have masked values like "cf_SE***345"
# Actual:
```

**Pass Criteria**: ✅ All credentials masked, no plaintext

**Result**: [ ] PASS [ ] FAIL

**Cleanup**:
```bash
curl -X DELETE "$API_BASE/cloudflare/api_token" -H "Cookie: $SESSION_COOKIE"
curl -X DELETE "$API_BASE/github/api_token" -H "Cookie: $SESSION_COOKIE"
```

---

## Test Suite 4: Rate Limiting & DoS Protection

### Test 4.1: Rate Limiting on Test Endpoint

**Objective**: Verify test endpoint has rate limiting to prevent API abuse

**Test**:
```bash
# Spam test endpoint
echo "Sending 10 requests..."

for i in {1..10}; do
  RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    -X POST "$API_BASE/cloudflare/test" \
    -H "Content-Type: application/json" \
    -H "Cookie: $SESSION_COOKIE" \
    -d '{"value": "fake_token_'$i'"}')

  HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
  echo "Request $i: HTTP $HTTP_CODE"

  # Check if rate limited
  if [ "$HTTP_CODE" = "429" ]; then
    echo "✅ Rate limit triggered after $i requests"
    break
  fi

  sleep 0.1
done

# Expected: 429 Too Many Requests after ~5 requests
# Actual:
```

**Pass Criteria**: ✅ Rate limit error (429) after 5-10 requests

**Result**: [ ] PASS [ ] FAIL

**Notes**: If FAIL, rate limiting is NOT implemented (critical security issue)

---

### Test 4.2: Rate Limit Headers Present

**Objective**: Verify rate limit headers are returned

**Test**:
```bash
# Check rate limit headers
curl -i -X POST "$API_BASE/cloudflare/test" \
  -H "Content-Type: application/json" \
  -H "Cookie: $SESSION_COOKIE" \
  -d '{"value": "test"}' 2>&1 | grep -i "rate-limit"

# Expected headers:
# X-RateLimit-Limit: 5
# X-RateLimit-Remaining: 4
# X-RateLimit-Reset: <timestamp>
# Actual:
```

**Pass Criteria**: ✅ Rate limit headers present

**Result**: [ ] PASS [ ] FAIL

---

## Test Suite 5: Error Handling & Information Disclosure

### Test 5.1: Generic Error Messages (No Stack Traces)

**Objective**: Verify errors don't leak sensitive information

**Test**:
```bash
# Trigger internal error by sending invalid JSON
ERROR_RESPONSE=$(curl -s -X POST "$API_BASE" \
  -H "Content-Type: application/json" \
  -H "Cookie: $SESSION_COOKIE" \
  -d '{"invalid_json_structure": true}')

echo "$ERROR_RESPONSE" | jq

# Check for sensitive information leakage
if echo "$ERROR_RESPONSE" | grep -Ei "(Traceback|File \"|line [0-9]+|/home/|postgres|Exception in)"; then
  echo "❌ FAILED: Stack trace or file paths leaked!"
else
  echo "✅ PASSED: Generic error message only"
fi

# Expected: Generic error like "Failed to create credential"
# NOT: Stack traces, file paths, database errors
# Actual:
```

**Pass Criteria**: ✅ Generic error message only, no sensitive details

**Result**: [ ] PASS [ ] FAIL

---

### Test 5.2: Database Errors Don't Leak Schema

**Objective**: Verify database errors are not exposed to users

**Test**:
```bash
# Attempt to create duplicate credential (violates unique constraint)
curl -s -X POST "$API_BASE" \
  -H "Content-Type: application/json" \
  -H "Cookie: $SESSION_COOKIE" \
  -d '{
    "service": "cloudflare",
    "credential_type": "api_token",
    "value": "cf_test_duplicate_123"
  }' > /dev/null

# Try to create again (should fail)
DUPLICATE_RESPONSE=$(curl -s -X POST "$API_BASE" \
  -H "Content-Type: application/json" \
  -H "Cookie: $SESSION_COOKIE" \
  -d '{
    "service": "cloudflare",
    "credential_type": "api_token",
    "value": "cf_test_duplicate_456"
  }')

echo "$DUPLICATE_RESPONSE" | jq

# Check for database schema leakage
if echo "$DUPLICATE_RESPONSE" | grep -Ei "(UNIQUE constraint|uq_user_service_credential|service_credentials table)"; then
  echo "❌ WARNING: Database schema details exposed"
else
  echo "✅ PASSED: No database details in error"
fi

# Expected: Generic error or user-friendly message
# NOT: "UNIQUE constraint uq_user_service_credential violated"
# Actual:
```

**Pass Criteria**: ✅ No database schema details in error

**Result**: [ ] PASS [ ] FAIL

**Cleanup**:
```bash
curl -X DELETE "$API_BASE/cloudflare/api_token" -H "Cookie: $SESSION_COOKIE"
```

---

## Test Suite 6: Audit Logging

### Test 6.1: Credential Creation Logged

**Objective**: Verify all credential operations are audited

**Test**:
```bash
# Create credential
curl -s -X POST "$API_BASE" \
  -H "Content-Type: application/json" \
  -H "Cookie: $SESSION_COOKIE" \
  -d '{
    "service": "cloudflare",
    "credential_type": "api_token",
    "value": "cf_audit_test_12345",
    "metadata": {"description": "Audit test"}
  }' > /dev/null

# Check audit logs
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT action, user_id, resource_type, details, status FROM audit_logs WHERE action LIKE 'credential.%' ORDER BY timestamp DESC LIMIT 5;"

# Expected: Recent log entry with:
# - action: "credential.create"
# - resource_type: "credential"
# - status: "success"
# - details: {"service": "cloudflare", "credential_type": "api_token"}
# NOT: Plaintext credential value in details
# Actual:
```

**Pass Criteria**: ✅ Audit log entry exists without plaintext credential

**Result**: [ ] PASS [ ] FAIL

**Cleanup**:
```bash
curl -X DELETE "$API_BASE/cloudflare/api_token" -H "Cookie: $SESSION_COOKIE"
```

---

### Test 6.2: Credential Deletion Logged

**Objective**: Verify deletions are audited

**Test**:
```bash
# Create and delete credential
curl -s -X POST "$API_BASE" \
  -H "Content-Type: application/json" \
  -H "Cookie: $SESSION_COOKIE" \
  -d '{
    "service": "cloudflare",
    "credential_type": "api_token",
    "value": "cf_delete_test_12345"
  }' > /dev/null

curl -s -X DELETE "$API_BASE/cloudflare/api_token" \
  -H "Cookie: $SESSION_COOKIE" > /dev/null

# Check audit logs for deletion
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT action, status FROM audit_logs WHERE action = 'credential.delete' ORDER BY timestamp DESC LIMIT 1;"

# Expected: Log entry with action="credential.delete", status="success"
# Actual:
```

**Pass Criteria**: ✅ Delete operation logged

**Result**: [ ] PASS [ ] FAIL

---

### Test 6.3: Failed Operations Logged

**Objective**: Verify failed operations are also audited

**Test**:
```bash
# Attempt invalid credential creation
curl -s -X POST "$API_BASE" \
  -H "Content-Type: application/json" \
  -H "Cookie: $SESSION_COOKIE" \
  -d '{
    "service": "invalid_service",
    "credential_type": "api_token",
    "value": "test"
  }' > /dev/null

# Check for failure audit log
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT action, status FROM audit_logs WHERE status = 'failure' ORDER BY timestamp DESC LIMIT 1;"

# Expected: Log entry with status="failure"
# Actual:
```

**Pass Criteria**: ✅ Failed operation logged

**Result**: [ ] PASS [ ] FAIL

---

## Test Suite 7: Integration Tests

### Test 7.1: Full Credential Lifecycle

**Objective**: Test complete CRUD operations

**Test**:
```bash
echo "=== 1. CREATE credential ==="
CREATE_RESP=$(curl -s -X POST "$API_BASE" \
  -H "Content-Type: application/json" \
  -H "Cookie: $SESSION_COOKIE" \
  -d '{
    "service": "cloudflare",
    "credential_type": "api_token",
    "value": "cf_lifecycle_test_abcdefghijklmnop",
    "metadata": {"description": "Full lifecycle test"}
  }')
echo "$CREATE_RESP" | jq
echo ""

echo "=== 2. READ credential ==="
READ_RESP=$(curl -s -X GET "$API_BASE/cloudflare/api_token" \
  -H "Cookie: $SESSION_COOKIE")
echo "$READ_RESP" | jq
echo ""

echo "=== 3. UPDATE credential ==="
UPDATE_RESP=$(curl -s -X PUT "$API_BASE/cloudflare/api_token" \
  -H "Content-Type: application/json" \
  -H "Cookie: $SESSION_COOKIE" \
  -d '{
    "value": "cf_lifecycle_updated_qrstuvwxyz12345",
    "metadata": {"description": "Updated test"}
  }')
echo "$UPDATE_RESP" | jq
echo ""

echo "=== 4. TEST credential ==="
TEST_RESP=$(curl -s -X POST "$API_BASE/cloudflare/test" \
  -H "Content-Type: application/json" \
  -H "Cookie: $SESSION_COOKIE" \
  -d '{}')
echo "$TEST_RESP" | jq
echo ""

echo "=== 5. DELETE credential ==="
DELETE_RESP=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  -X DELETE "$API_BASE/cloudflare/api_token" \
  -H "Cookie: $SESSION_COOKIE")
echo "$DELETE_RESP"
echo ""

# Verify deleted
echo "=== 6. VERIFY deletion ==="
VERIFY_RESP=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  -X GET "$API_BASE/cloudflare/api_token" \
  -H "Cookie: $SESSION_COOKIE")
echo "$VERIFY_RESP"

# Expected: 404 Not Found
# Actual:
```

**Pass Criteria**: ✅ All operations succeed, deletion confirmed

**Result**: [ ] PASS [ ] FAIL

---

## Test Results Summary

**Test Date**: __________________
**Tester**: __________________
**Environment**: [ ] Production [ ] Local

### Results Table

| Test ID | Category | Test Name | Result | Notes |
|---------|----------|-----------|--------|-------|
| 1.1 | Auth | Unauthenticated Access | [ ] PASS [ ] FAIL | |
| 1.2 | Auth | Invalid Session | [ ] PASS [ ] FAIL | |
| 1.3 | Auth | Valid Session | [ ] PASS [ ] FAIL | |
| 2.1 | Input | SQL Injection | [ ] PASS [ ] FAIL | |
| 2.2 | Input | XSS in Metadata | [ ] PASS [ ] FAIL | |
| 2.3 | Input | Invalid Service | [ ] PASS [ ] FAIL | |
| 2.4 | Input | Invalid Type | [ ] PASS [ ] FAIL | |
| 3.1 | Security | DB Encryption | [ ] PASS [ ] FAIL | |
| 3.2 | Security | Credential Masking | [ ] PASS [ ] FAIL | |
| 3.3 | Security | List Masking | [ ] PASS [ ] FAIL | |
| 4.1 | DoS | Rate Limiting | [ ] PASS [ ] FAIL | **CRITICAL** |
| 4.2 | DoS | Rate Limit Headers | [ ] PASS [ ] FAIL | |
| 5.1 | Errors | Generic Messages | [ ] PASS [ ] FAIL | |
| 5.2 | Errors | No Schema Leak | [ ] PASS [ ] FAIL | |
| 6.1 | Audit | Create Logged | [ ] PASS [ ] FAIL | |
| 6.2 | Audit | Delete Logged | [ ] PASS [ ] FAIL | |
| 6.3 | Audit | Failures Logged | [ ] PASS [ ] FAIL | |
| 7.1 | Integration | Full Lifecycle | [ ] PASS [ ] FAIL | |

**Total Tests**: 18
**Passed**: _____
**Failed**: _____
**Success Rate**: _____%

---

## Critical Failures

**If any of these tests FAIL, DO NOT deploy to production**:

- [ ] Test 1.1 - Unauthenticated Access (auth bypass)
- [ ] Test 2.1 - SQL Injection (database compromise)
- [ ] Test 3.1 - DB Encryption (plaintext credentials)
- [ ] Test 3.2 - Credential Masking (plaintext leak)
- [ ] Test 4.1 - Rate Limiting (DoS vulnerability)

---

## Sign-Off

**Tester Signature**: ______________________
**Date**: ______________________

**Security Approval**: ______________________
**Date**: ______________________

---

*This test plan is confidential and for internal use only.*
