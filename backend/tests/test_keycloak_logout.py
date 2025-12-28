"""
Test Keycloak SSO Logout Integration
Tests the /api/v1/auth/logout endpoint with Keycloak SSO
"""

import httpx
import asyncio
import os
import json

# Configuration
BASE_URL = os.getenv("API_URL", "http://localhost:8084")
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "https://auth.your-domain.com")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://your-domain.com")


async def test_logout_endpoint():
    """Test the logout endpoint returns correct SSO logout URL"""

    print("Testing Keycloak SSO Logout")
    print("-" * 50)

    async with httpx.AsyncClient() as client:
        try:
            # First, try to login (you'll need valid credentials)
            print("\n1. Testing logout endpoint structure...")

            # For testing, we'll just check the endpoint without auth
            # In production, you need a valid session token
            response = await client.post(
                f"{BASE_URL}/api/v1/auth/logout",
                headers={"Content-Type": "application/json"}
            )

            print(f"   Status Code: {response.status_code}")

            if response.status_code == 401:
                print("   ✓ Endpoint requires authentication (expected)")
                print("\n2. Expected response format when authenticated:")
                expected_response = {
                    "message": "Logged out successfully",
                    "sso_logout_url": f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/logout?redirect_uri={FRONTEND_URL}"
                }
                print(f"   {json.dumps(expected_response, indent=2)}")

            elif response.status_code == 200:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")

                # Verify response structure
                if "message" in data and "sso_logout_url" in data:
                    print("   ✓ Response has correct structure")

                    # Verify logout URL format
                    expected_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/logout"
                    if expected_url in data["sso_logout_url"]:
                        print("   ✓ SSO logout URL has correct format")
                    else:
                        print(f"   ✗ SSO logout URL incorrect")
                        print(f"     Expected: {expected_url}")
                        print(f"     Got: {data['sso_logout_url']}")

                    # Verify redirect URI
                    if f"redirect_uri={FRONTEND_URL}" in data["sso_logout_url"]:
                        print("   ✓ Redirect URI is correct")
                    else:
                        print(f"   ✗ Redirect URI missing or incorrect")
                else:
                    print("   ✗ Response structure incorrect")
            else:
                print(f"   ✗ Unexpected status code: {response.status_code}")
                print(f"   Response: {response.text}")

        except Exception as e:
            print(f"   ✗ Error: {e}")

    print("\n" + "=" * 50)
    print("Frontend Integration Instructions:")
    print("=" * 50)
    print("""
When user clicks logout:

1. Call the logout endpoint:
   POST /api/v1/auth/logout

2. Parse the response:
   {
     "message": "Logged out successfully",
     "sso_logout_url": "https://auth.your-domain.com/realms/master/protocol/openid-connect/logout?redirect_uri=https://your-domain.com"
   }

3. Redirect browser to sso_logout_url:
   window.location.href = response.sso_logout_url;

This will:
- Clear the local session
- Clear the Keycloak SSO session
- Redirect back to the frontend URL

Example JavaScript/TypeScript code:
```javascript
async function logout() {
  try {
    const response = await fetch('/api/v1/auth/logout', {
      method: 'POST',
      credentials: 'include', // Include cookies
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const data = await response.json();
      // Redirect to Keycloak logout
      window.location.href = data.sso_logout_url;
    } else {
      console.error('Logout failed:', response.statusText);
    }
  } catch (error) {
    console.error('Logout error:', error);
  }
}
```
""")


async def verify_keycloak_endpoint():
    """Verify Keycloak logout endpoint is accessible"""

    print("\n" + "=" * 50)
    print("Verifying Keycloak Logout Endpoint")
    print("=" * 50)

    logout_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/logout"

    print(f"\nKeycloak Logout URL: {logout_url}")
    print(f"Redirect URI: {FRONTEND_URL}")

    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            # Test if endpoint exists (will redirect without valid session)
            response = await client.get(
                logout_url,
                params={"redirect_uri": FRONTEND_URL},
                timeout=10.0
            )

            print(f"\nStatus Code: {response.status_code}")

            if response.status_code == 200 or response.status_code == 302:
                print("✓ Keycloak logout endpoint is accessible")
            else:
                print(f"⚠ Unexpected status: {response.status_code}")

        except httpx.ConnectError:
            print(f"✗ Cannot connect to Keycloak at {KEYCLOAK_URL}")
            print("  Make sure Keycloak is running and accessible")
        except Exception as e:
            print(f"⚠ Error checking endpoint: {e}")


def print_environment_check():
    """Print current environment configuration"""

    print("\n" + "=" * 50)
    print("Environment Configuration Check")
    print("=" * 50)

    configs = [
        ("KEYCLOAK_URL", KEYCLOAK_URL),
        ("KEYCLOAK_REALM", KEYCLOAK_REALM),
        ("FRONTEND_URL", FRONTEND_URL),
        ("API_URL", BASE_URL)
    ]

    for key, value in configs:
        status = "✓" if value else "✗"
        print(f"{status} {key}: {value}")

    print("\nExpected Keycloak Logout URL:")
    print(f"  {KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/logout?redirect_uri={FRONTEND_URL}")


async def main():
    """Run all tests"""
    print_environment_check()
    await test_logout_endpoint()
    await verify_keycloak_endpoint()

    print("\n" + "=" * 50)
    print("Test Complete")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
