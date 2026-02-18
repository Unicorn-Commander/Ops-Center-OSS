# Ops-Center API Code Examples

**Last Updated**: October 25, 2025

This guide provides comprehensive code examples for all major Ops-Center API endpoints in multiple programming languages.

---

## Table of Contents

1. [Authentication](#authentication)
2. [User Management](#user-management)
3. [Organization Management](#organization-management)
4. [Billing & Subscriptions](#billing--subscriptions)
5. [LLM Management](#llm-management)
6. [System Administration](#system-administration)
7. [Error Handling](#error-handling)

---

## Authentication

All API requests require authentication via Bearer token obtained from Keycloak SSO.

### Get Authentication Token

#### cURL
```bash
# Login and get token
curl -X POST https://auth.unicorncommander.ai/realms/uchub/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=ops-center" \
  -d "client_secret=your-keycloak-client-secret" \
  -d "username=your-email@example.com" \
  -d "password=your-password"
```

#### JavaScript (fetch)
```javascript
async function getAuthToken(username, password) {
  const response = await fetch('https://auth.unicorncommander.ai/realms/uchub/protocol/openid-connect/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: new URLSearchParams({
      grant_type: 'password',
      client_id: 'ops-center',
      client_secret: 'your-keycloak-client-secret',
      username,
      password
    })
  });

  const data = await response.json();
  return data.access_token;
}

// Usage
const token = await getAuthToken('user@example.com', 'password');
localStorage.setItem('authToken', token);
```

#### Python (requests)
```python
import requests

def get_auth_token(username: str, password: str) -> str:
    """Get authentication token from Keycloak"""
    url = 'https://auth.unicorncommander.ai/realms/uchub/protocol/openid-connect/token'

    data = {
        'grant_type': 'password',
        'client_id': 'ops-center',
        'client_secret': 'your-keycloak-client-secret',
        'username': username,
        'password': password
    }

    response = requests.post(url, data=data)
    response.raise_for_status()

    return response.json()['access_token']

# Usage
token = get_auth_token('user@example.com', 'password')
```

---

## User Management

### List All Users

#### cURL
```bash
curl -X GET https://unicorncommander.ai/api/v1/admin/users \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### JavaScript (fetch)
```javascript
async function getAllUsers() {
  const token = localStorage.getItem('authToken');

  const response = await fetch('/api/v1/admin/users', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const users = await response.json();
  return users;
}

// Usage
try {
  const users = await getAllUsers();
  console.log(`Found ${users.length} users`);
} catch (error) {
  console.error('Failed to fetch users:', error);
}
```

#### Python (requests)
```python
import requests

def get_all_users(token: str) -> list:
    """Get all users from Ops-Center"""
    url = 'https://unicorncommander.ai/api/v1/admin/users'

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()

# Usage
users = get_all_users(token)
print(f"Found {len(users)} users")
```

### Advanced Filtering

#### cURL
```bash
# Filter users by tier, role, and status
curl -X GET "https://unicorncommander.ai/api/v1/admin/users?tier=professional&role=admin&status=enabled&limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### JavaScript (axios)
```javascript
import axios from 'axios';

async function filterUsers(filters) {
  const token = localStorage.getItem('authToken');

  const response = await axios.get('/api/v1/admin/users', {
    params: {
      search: filters.search,
      tier: filters.tier,           // trial, starter, professional, enterprise
      role: filters.role,           // admin, moderator, developer, analyst, viewer
      status: filters.status,       // enabled, disabled, suspended
      org_id: filters.orgId,
      created_from: filters.createdFrom,
      created_to: filters.createdTo,
      email_verified: filters.emailVerified,
      byok_enabled: filters.byokEnabled,
      limit: filters.limit || 50,
      offset: filters.offset || 0
    },
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  return response.data;
}

// Usage
const users = await filterUsers({
  tier: 'professional',
  role: 'admin',
  status: 'enabled',
  emailVerified: true,
  limit: 100
});
```

#### Python (httpx - async)
```python
import httpx

async def filter_users(
    token: str,
    tier: str = None,
    role: str = None,
    status: str = None,
    search: str = None,
    limit: int = 50,
    offset: int = 0
) -> dict:
    """Filter users with advanced criteria"""
    url = 'https://unicorncommander.ai/api/v1/admin/users'

    params = {
        'limit': limit,
        'offset': offset
    }

    if search:
        params['search'] = search
    if tier:
        params['tier'] = tier
    if role:
        params['role'] = role
    if status:
        params['status'] = status

    headers = {
        'Authorization': f'Bearer {token}'
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()

# Usage
import asyncio
users = asyncio.run(filter_users(
    token=token,
    tier='professional',
    role='admin',
    status='enabled',
    limit=100
))
```

### Get User Details

#### cURL
```bash
curl -X GET https://unicorncommander.ai/api/v1/admin/users/USER_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### JavaScript
```javascript
async function getUserDetails(userId) {
  const token = localStorage.getItem('authToken');

  const response = await fetch(`/api/v1/admin/users/${userId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  return await response.json();
}

// Usage
const user = await getUserDetails('8a7b6c5d-4e3f-2g1h-0i9j-8k7l6m5n4o3p');
console.log(`User: ${user.username}, Tier: ${user.subscription_tier}`);
```

#### Python
```python
def get_user_details(token: str, user_id: str) -> dict:
    """Get detailed user information"""
    url = f'https://unicorncommander.ai/api/v1/admin/users/{user_id}'

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()

# Usage
user = get_user_details(token, '8a7b6c5d-4e3f-2g1h-0i9j-8k7l6m5n4o3p')
print(f"User: {user['username']}, Tier: {user.get('subscription_tier', 'none')}")
```

### Create User

#### cURL
```bash
curl -X POST https://unicorncommander.ai/api/v1/admin/users/comprehensive \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "username": "newuser",
    "firstName": "John",
    "lastName": "Doe",
    "password": "SecureP@ssw0rd!",
    "role": "developer",
    "subscription_tier": "starter",
    "enabled": true
  }'
```

#### JavaScript
```javascript
async function createUser(userData) {
  const token = localStorage.getItem('authToken');

  const response = await fetch('/api/v1/admin/users/comprehensive', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      email: userData.email,
      username: userData.username,
      firstName: userData.firstName,
      lastName: userData.lastName,
      password: userData.password,
      role: userData.role || 'viewer',
      subscription_tier: userData.tier || 'trial',
      enabled: true
    })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create user');
  }

  return await response.json();
}

// Usage
const newUser = await createUser({
  email: 'john.doe@example.com',
  username: 'johndoe',
  firstName: 'John',
  lastName: 'Doe',
  password: 'SecureP@ssw0rd!',
  role: 'developer',
  tier: 'professional'
});
console.log(`Created user: ${newUser.id}`);
```

#### Python
```python
def create_user(token: str, user_data: dict) -> dict:
    """Create a new user with full provisioning"""
    url = 'https://unicorncommander.ai/api/v1/admin/users/comprehensive'

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'email': user_data['email'],
        'username': user_data['username'],
        'firstName': user_data['first_name'],
        'lastName': user_data['last_name'],
        'password': user_data['password'],
        'role': user_data.get('role', 'viewer'),
        'subscription_tier': user_data.get('tier', 'trial'),
        'enabled': True
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()

# Usage
new_user = create_user(token, {
    'email': 'john.doe@example.com',
    'username': 'johndoe',
    'first_name': 'John',
    'last_name': 'Doe',
    'password': 'SecureP@ssw0rd!',
    'role': 'developer',
    'tier': 'professional'
})
print(f"Created user: {new_user['id']}")
```

### Update User

#### cURL
```bash
curl -X PUT https://unicorncommander.ai/api/v1/admin/users/USER_ID \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "Jane",
    "lastName": "Smith",
    "subscription_tier": "enterprise"
  }'
```

#### JavaScript
```javascript
async function updateUser(userId, updates) {
  const token = localStorage.getItem('authToken');

  const response = await fetch(`/api/v1/admin/users/${userId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updates)
  });

  return await response.json();
}

// Usage
const updated = await updateUser('USER_ID', {
  firstName: 'Jane',
  lastName: 'Smith',
  subscription_tier: 'enterprise'
});
```

#### Python
```python
def update_user(token: str, user_id: str, updates: dict) -> dict:
    """Update user details"""
    url = f'https://unicorncommander.ai/api/v1/admin/users/{user_id}'

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    response = requests.put(url, headers=headers, json=updates)
    response.raise_for_status()

    return response.json()

# Usage
updated = update_user(token, 'USER_ID', {
    'firstName': 'Jane',
    'lastName': 'Smith',
    'subscription_tier': 'enterprise'
})
```

### Bulk Operations

#### Bulk Import Users from CSV

```javascript
async function bulkImportUsers(csvFile) {
  const token = localStorage.getItem('authToken');
  const formData = new FormData();
  formData.append('file', csvFile);

  const response = await fetch('/api/v1/admin/users/bulk/import', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  return await response.json();
}

// Usage
const fileInput = document.getElementById('csvFile');
const result = await bulkImportUsers(fileInput.files[0]);
console.log(`Imported ${result.successful} users, ${result.failed} failed`);
```

#### Bulk Role Assignment

```python
def bulk_assign_roles(token: str, user_ids: list, role: str) -> dict:
    """Assign role to multiple users at once"""
    url = 'https://unicorncommander.ai/api/v1/admin/users/bulk/assign-roles'

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'user_ids': user_ids,
        'role': role
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()

# Usage
result = bulk_assign_roles(token, [
    'user-id-1',
    'user-id-2',
    'user-id-3'
], 'moderator')
print(f"Updated {result['updated_count']} users")
```

---

## Organization Management

### List Organizations

#### cURL
```bash
curl -X GET https://unicorncommander.ai/api/v1/organizations \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### JavaScript
```javascript
async function getOrganizations() {
  const token = localStorage.getItem('authToken');

  const response = await fetch('/api/v1/organizations', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  return await response.json();
}
```

### Create Organization

#### cURL
```bash
curl -X POST https://unicorncommander.ai/api/v1/organizations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "slug": "acme-corp",
    "description": "Enterprise customer"
  }'
```

#### JavaScript
```javascript
async function createOrganization(orgData) {
  const token = localStorage.getItem('authToken');

  const response = await fetch('/api/v1/organizations', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: orgData.name,
      slug: orgData.slug,
      description: orgData.description
    })
  });

  return await response.json();
}

// Usage
const org = await createOrganization({
  name: 'Acme Corporation',
  slug: 'acme-corp',
  description: 'Enterprise customer'
});
```

#### Python
```python
def create_organization(token: str, name: str, slug: str, description: str = '') -> dict:
    """Create a new organization"""
    url = 'https://unicorncommander.ai/api/v1/organizations'

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'name': name,
        'slug': slug,
        'description': description
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()

# Usage
org = create_organization(token, 'Acme Corporation', 'acme-corp', 'Enterprise customer')
```

### Invite Member to Organization

#### cURL
```bash
curl -X POST https://unicorncommander.ai/api/v1/organizations/ORG_ID/invite \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "role": "member"
  }'
```

#### JavaScript
```javascript
async function inviteMember(orgId, email, role = 'member') {
  const token = localStorage.getItem('authToken');

  const response = await fetch(`/api/v1/organizations/${orgId}/invite`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email, role })
  });

  return await response.json();
}
```

---

## Billing & Subscriptions

### Get Subscription Plans

#### cURL
```bash
curl -X GET https://unicorncommander.ai/api/v1/billing/plans \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### JavaScript
```javascript
async function getSubscriptionPlans() {
  const token = localStorage.getItem('authToken');

  const response = await fetch('/api/v1/billing/plans', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  return await response.json();
}

// Usage
const plans = await getSubscriptionPlans();
plans.forEach(plan => {
  console.log(`${plan.name}: $${plan.amount_cents / 100}/${plan.interval}`);
});
```

#### Python
```python
def get_subscription_plans(token: str) -> list:
    """Get all available subscription plans"""
    url = 'https://unicorncommander.ai/api/v1/billing/plans'

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()

# Usage
plans = get_subscription_plans(token)
for plan in plans:
    print(f"{plan['name']}: ${plan['amount_cents'] / 100}/{plan['interval']}")
```

### Get Current Subscription

#### cURL
```bash
curl -X GET https://unicorncommander.ai/api/v1/billing/subscriptions/current \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### JavaScript
```javascript
async function getCurrentSubscription() {
  const token = localStorage.getItem('authToken');

  const response = await fetch('/api/v1/billing/subscriptions/current', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  return await response.json();
}

// Usage
const subscription = await getCurrentSubscription();
console.log(`Current plan: ${subscription.plan_name}`);
console.log(`Status: ${subscription.status}`);
console.log(`Next billing: ${subscription.next_billing_date}`);
```

### Create Subscription

#### cURL
```bash
curl -X POST https://unicorncommander.ai/api/v1/billing/subscriptions/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_code": "professional",
    "payment_method_id": "pm_1234567890"
  }'
```

#### JavaScript
```javascript
async function createSubscription(planCode, paymentMethodId) {
  const token = localStorage.getItem('authToken');

  const response = await fetch('/api/v1/billing/subscriptions/create', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      plan_code: planCode,
      payment_method_id: paymentMethodId
    })
  });

  return await response.json();
}

// Usage
const subscription = await createSubscription('professional', 'pm_1234567890');
```

---

## LLM Management

### Chat Completion (OpenAI-compatible)

#### cURL
```bash
curl -X POST https://unicorncommander.ai/api/v1/llm/chat/completions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "temperature": 0.7,
    "max_tokens": 150
  }'
```

#### JavaScript
```javascript
async function chatCompletion(messages, model = 'openai/gpt-4', options = {}) {
  const token = localStorage.getItem('authToken');

  const response = await fetch('/api/v1/llm/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model,
      messages,
      temperature: options.temperature || 0.7,
      max_tokens: options.maxTokens || 150,
      stream: options.stream || false
    })
  });

  return await response.json();
}

// Usage
const result = await chatCompletion([
  { role: 'system', content: 'You are a helpful assistant.' },
  { role: 'user', content: 'Hello, how are you?' }
]);
console.log(result.choices[0].message.content);
```

#### Python
```python
def chat_completion(
    token: str,
    messages: list,
    model: str = 'openai/gpt-4',
    temperature: float = 0.7,
    max_tokens: int = 150
) -> dict:
    """Send chat completion request to LiteLLM proxy"""
    url = 'https://unicorncommander.ai/api/v1/llm/chat/completions'

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'model': model,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()

# Usage
result = chat_completion(token, [
    {'role': 'system', 'content': 'You are a helpful assistant.'},
    {'role': 'user', 'content': 'Hello, how are you?'}
])
print(result['choices'][0]['message']['content'])
```

### List Available Models

#### cURL
```bash
curl -X GET https://unicorncommander.ai/api/v1/llm/models \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### JavaScript
```javascript
async function getAvailableModels() {
  const token = localStorage.getItem('authToken');

  const response = await fetch('/api/v1/llm/models', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  return await response.json();
}

// Usage
const models = await getAvailableModels();
models.data.forEach(model => {
  console.log(`${model.id}: ${model.owned_by}`);
});
```

---

## System Administration

### Get System Status

#### cURL
```bash
curl -X GET https://unicorncommander.ai/api/v1/system/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### JavaScript
```javascript
async function getSystemStatus() {
  const token = localStorage.getItem('authToken');

  const response = await fetch('/api/v1/system/status', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  return await response.json();
}

// Usage
const status = await getSystemStatus();
console.log(`CPU: ${status.cpu_percent}%`);
console.log(`Memory: ${status.memory_percent}%`);
console.log(`Services: ${status.services.running}/${status.services.total}`);
```

### Get User Analytics Summary

#### cURL
```bash
curl -X GET https://unicorncommander.ai/api/v1/admin/users/analytics/summary \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### JavaScript
```javascript
async function getUserAnalytics() {
  const token = localStorage.getItem('authToken');

  const response = await fetch('/api/v1/admin/users/analytics/summary', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  return await response.json();
}

// Usage
const analytics = await getUserAnalytics();
console.log(`Total Users: ${analytics.total_users}`);
console.log(`Active Users: ${analytics.active_users}`);
console.log(`Enterprise Tier: ${analytics.tiers.enterprise}`);
```

---

## Error Handling

### Standard Error Response Format

All API errors return a consistent JSON format:

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "SPECIFIC_ERROR_CODE",
  "status_code": 400
}
```

### Common Error Codes

- **401 Unauthorized**: Invalid or missing authentication token
- **403 Forbidden**: User doesn't have permission for this operation
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation error (check request body)
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server-side error

### Error Handling Best Practices

#### JavaScript
```javascript
async function safeApiCall(url, options = {}) {
  const token = localStorage.getItem('authToken');

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      const error = await response.json();

      // Handle specific errors
      switch (response.status) {
        case 401:
          // Redirect to login
          window.location.href = '/auth/login';
          break;
        case 403:
          throw new Error('You do not have permission for this operation');
        case 404:
          throw new Error('Resource not found');
        case 422:
          throw new Error(`Validation error: ${error.detail}`);
        case 429:
          throw new Error('Rate limit exceeded. Please try again later');
        default:
          throw new Error(error.detail || 'An error occurred');
      }
    }

    return await response.json();
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
}

// Usage
try {
  const users = await safeApiCall('/api/v1/admin/users');
} catch (error) {
  // Handle error in UI
  alert(error.message);
}
```

#### Python
```python
import requests
from typing import Optional, Dict, Any

class OpsApiError(Exception):
    """Base exception for Ops-Center API errors"""
    def __init__(self, message: str, status_code: int, error_code: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)

def safe_api_call(
    url: str,
    token: str,
    method: str = 'GET',
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make API call with error handling"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f'Unsupported method: {method}')

        # Check for errors
        if not response.ok:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('detail', f'HTTP {response.status_code} error')
            error_code = error_data.get('error_code')

            raise OpsApiError(error_msg, response.status_code, error_code)

        return response.json()

    except requests.exceptions.RequestException as e:
        raise OpsApiError(f'Request failed: {str(e)}', 0)

# Usage
try:
    users = safe_api_call('https://unicorncommander.ai/api/v1/admin/users', token)
except OpsApiError as e:
    if e.status_code == 401:
        print('Authentication required')
    elif e.status_code == 403:
        print('Permission denied')
    else:
        print(f'Error: {e.message}')
```

---

## Rate Limiting

API rate limits are enforced per user and subscription tier:

| Tier | API Calls/Month | API Calls/Minute |
|------|-----------------|------------------|
| Trial | 700 (100/day) | 10 |
| Starter | 1,000 | 30 |
| Professional | 10,000 | 100 |
| Enterprise | Unlimited | 500 |

### Rate Limit Headers

All API responses include rate limit information in headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1698432000
```

### Handling Rate Limits

```javascript
async function apiCallWithRetry(url, options = {}, maxRetries = 3) {
  const token = localStorage.getItem('authToken');

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        ...options.headers
      }
    });

    if (response.status === 429) {
      const resetTime = parseInt(response.headers.get('X-RateLimit-Reset'));
      const waitTime = (resetTime * 1000) - Date.now();

      if (waitTime > 0 && attempt < maxRetries - 1) {
        console.log(`Rate limited. Waiting ${waitTime}ms...`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
        continue;
      }
    }

    return response;
  }

  throw new Error('Max retries exceeded');
}
```

---

## WebSocket Connections (Real-time Updates)

### Connect to Real-time Updates

```javascript
const token = localStorage.getItem('authToken');
const ws = new WebSocket(`wss://unicorncommander.ai/ws?token=${token}`);

ws.onopen = () => {
  console.log('Connected to real-time updates');

  // Subscribe to user updates
  ws.send(JSON.stringify({
    action: 'subscribe',
    channel: 'users'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case 'user_created':
      console.log('New user created:', data.payload);
      break;
    case 'user_updated':
      console.log('User updated:', data.payload);
      break;
    case 'subscription_changed':
      console.log('Subscription changed:', data.payload);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from real-time updates');
};
```

---

## Additional Resources

- **OpenAPI Specification**: `/docs/api/openapi.yaml`
- **Interactive API Explorer**: https://unicorncommander.ai/admin/platform/api-docs
- **Full API Reference**: `/docs/api/API_REFERENCE.md`
- **Quick Start Guide**: `/docs/API_QUICK_START.md`
- **Security Best Practices**: `/docs/README_SECURITY.md`

---

**Need Help?**
- 📚 Documentation: https://unicorncommander.ai:8086
- 💬 Support: support@unicorncommander.com
- 🐛 Report Issues: https://github.com/Unicorn-Commander/UC-Cloud/issues
