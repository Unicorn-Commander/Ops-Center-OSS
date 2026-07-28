#!/bin/bash
# Simple test for Keycloak SSO logout endpoint

echo "========================================================"
echo "Keycloak SSO Logout Implementation Test"
echo "========================================================"

# Configuration
API_URL="${API_URL:-http://localhost:8084}"
KEYCLOAK_URL="${KEYCLOAK_URL:-https://auth.unicorncommander.ai}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-master}"
FRONTEND_URL="${FRONTEND_URL:-https://unicorncommander.ai}"

echo ""
echo "Configuration:"
echo "  API URL: $API_URL"
echo "  Keycloak URL: $KEYCLOAK_URL"
echo "  Keycloak Realm: $KEYCLOAK_REALM"
echo "  Frontend URL: $FRONTEND_URL"
echo ""

# Test 1: Check endpoint exists
echo "Test 1: Check logout endpoint"
echo "----------------------------------------"
response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/auth/logout" -H "Content-Type: application/json")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

echo "HTTP Status: $http_code"

if [ "$http_code" == "401" ]; then
    echo "✓ Endpoint exists (requires authentication)"
elif [ "$http_code" == "200" ]; then
    echo "✓ Endpoint accessible"
    echo ""
    echo "Response:"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"

    # Check if response has required fields
    if echo "$body" | grep -q "sso_logout_url"; then
        echo ""
        echo "✓ Response contains sso_logout_url field"

        # Extract and validate logout URL
        logout_url=$(echo "$body" | python3 -c "import json,sys; print(json.load(sys.stdin).get('sso_logout_url', ''))" 2>/dev/null)

        if [ -n "$logout_url" ]; then
            echo "  SSO Logout URL: $logout_url"

            # Check URL format
            expected_base="$KEYCLOAK_URL/realms/$KEYCLOAK_REALM/protocol/openid-connect/logout"
            if echo "$logout_url" | grep -q "$expected_base"; then
                echo "  ✓ URL has correct format"
            else
                echo "  ✗ URL format incorrect"
                echo "    Expected to contain: $expected_base"
            fi

            # Check redirect URI
            if echo "$logout_url" | grep -q "redirect_uri=$FRONTEND_URL"; then
                echo "  ✓ Redirect URI is correct"
            else
                echo "  ✗ Redirect URI incorrect or missing"
                echo "    Expected: redirect_uri=$FRONTEND_URL"
            fi
        fi
    else
        echo "✗ Response missing sso_logout_url field"
    fi
else
    echo "⚠ Unexpected HTTP status: $http_code"
    echo "Response: $body"
fi

echo ""
echo "========================================================"
echo "Test 2: Verify Keycloak endpoint accessibility"
echo "========================================================"

logout_endpoint="$KEYCLOAK_URL/realms/$KEYCLOAK_REALM/protocol/openid-connect/logout"
echo "Testing: $logout_endpoint"
echo ""

# Test with curl (will redirect without session)
response=$(curl -s -w "\n%{http_code}" -L "$logout_endpoint?redirect_uri=$FRONTEND_URL" 2>&1)
http_code=$(echo "$response" | tail -n1)

echo "HTTP Status: $http_code"

if [ "$http_code" == "200" ] || [ "$http_code" == "302" ] || [ "$http_code" == "303" ]; then
    echo "✓ Keycloak logout endpoint is accessible"
elif [ "$http_code" == "000" ]; then
    echo "⚠ Cannot connect to Keycloak (connection error)"
    echo "  Verify Keycloak is running at: $KEYCLOAK_URL"
else
    echo "⚠ Unexpected status: $http_code"
fi

echo ""
echo "========================================================"
echo "Expected Complete Logout Flow"
echo "========================================================"
cat <<EOF

1. Frontend calls: POST $API_URL/api/v1/auth/logout

2. Backend responds:
   {
     "message": "Logged out successfully",
     "sso_logout_url": "$KEYCLOAK_URL/realms/$KEYCLOAK_REALM/protocol/openid-connect/logout?redirect_uri=$FRONTEND_URL"
   }

3. Frontend redirects: window.location.href = response.sso_logout_url

4. Keycloak:
   - Ends SSO session
   - Clears cookies
   - Redirects to: $FRONTEND_URL

5. User is completely logged out

EOF

echo "========================================================"
echo "Frontend Integration Code"
echo "========================================================"
cat <<'EOF'

async function logout() {
  try {
    const response = await fetch('/api/v1/auth/logout', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const data = await response.json();
      // Redirect to Keycloak SSO logout
      window.location.href = data.sso_logout_url;
    } else {
      console.error('Logout failed');
      window.location.href = '/';
    }
  } catch (error) {
    console.error('Logout error:', error);
    window.location.href = '/';
  }
}

EOF

echo "========================================================"
echo "Test Complete"
echo "========================================================"
