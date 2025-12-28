# Ops-Center API Quick Start Guide

**Last Updated**: October 25, 2025

Get up and running with the Ops-Center API in under 10 minutes.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Authentication Setup](#authentication-setup)
3. [Your First API Call](#your-first-api-call)
4. [Common Use Cases](#common-use-cases)
5. [Next Steps](#next-steps)

---

## Prerequisites

Before you begin, ensure you have:

- ✅ An active Ops-Center account
- ✅ Your account credentials (email + password)
- ✅ A tool for making HTTP requests (cURL, Postman, or code editor)
- ✅ (Optional) Node.js or Python installed for code examples

### Subscription Tiers & API Access

| Tier | API Calls/Month | Best For |
|------|-----------------|----------|
| 🔬 **Trial** | 700 (100/day) | Testing and evaluation |
| 🚀 **Starter** | 1,000 | Small projects |
| 💼 **Professional** | 10,000 | Production applications |
| 🏢 **Enterprise** | Unlimited | Large-scale deployments |

---

## Authentication Setup

The Ops-Center API uses OAuth 2.0 authentication via Keycloak SSO. You'll need to obtain an access token before making API calls.

### Step 1: Get Your Access Token

**Using cURL:**

```bash
curl -X POST https://auth.your-domain.com/realms/uchub/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=ops-center" \
  -d "client_secret=your-keycloak-client-secret" \
  -d "username=YOUR_EMAIL" \
  -d "password=YOUR_PASSWORD"
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cC...",
  "expires_in": 3600,
  "refresh_expires_in": 86400,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cC...",
  "token_type": "Bearer"
}
```

**Save your access token!** You'll need it for all API requests.

### Step 2: Store Your Token

**In your terminal (for cURL users):**

```bash
export OPS_TOKEN="your-access-token-here"
```

**In JavaScript:**

```javascript
// Store in localStorage for web apps
localStorage.setItem('authToken', 'your-access-token-here');
```

**In Python:**

```python
# Store in environment variable or config
import os
os.environ['OPS_TOKEN'] = 'your-access-token-here'
```

### Token Refresh

Access tokens expire after 1 hour. Use your refresh token to get a new access token without re-authenticating:

```bash
curl -X POST https://auth.your-domain.com/realms/uchub/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token" \
  -d "client_id=ops-center" \
  -d "client_secret=your-keycloak-client-secret" \
  -d "refresh_token=YOUR_REFRESH_TOKEN"
```

---

## Your First API Call

Let's start with a simple request to verify your authentication is working.

### Get System Status

**cURL:**

```bash
curl -X GET https://your-domain.com/api/v1/system/status \
  -H "Authorization: Bearer $OPS_TOKEN"
```

**JavaScript:**

```javascript
const token = localStorage.getItem('authToken');

fetch('/api/v1/system/status', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(response => response.json())
.then(data => {
  console.log('System Status:', data);
  console.log(`CPU: ${data.cpu_percent}%`);
  console.log(`Memory: ${data.memory_percent}%`);
})
.catch(error => console.error('Error:', error));
```

**Python:**

```python
import requests
import os

token = os.environ['OPS_TOKEN']

response = requests.get(
    'https://your-domain.com/api/v1/system/status',
    headers={'Authorization': f'Bearer {token}'}
)

data = response.json()
print(f"CPU: {data['cpu_percent']}%")
print(f"Memory: {data['memory_percent']}%")
```

**Expected Response:**

```json
{
  "status": "healthy",
  "cpu_percent": 35.2,
  "memory_percent": 62.5,
  "disk_percent": 45.8,
  "services": {
    "total": 12,
    "running": 12,
    "stopped": 0
  },
  "uptime_seconds": 3600000
}
```

✅ **Success!** If you see system stats, your authentication is working correctly.

---

## Common Use Cases

### Use Case 1: List All Users

**Goal**: Get a list of all users in your organization.

**cURL:**

```bash
curl -X GET https://your-domain.com/api/v1/admin/users \
  -H "Authorization: Bearer $OPS_TOKEN"
```

**JavaScript:**

```javascript
async function getUsers() {
  const token = localStorage.getItem('authToken');

  const response = await fetch('/api/v1/admin/users', {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  const users = await response.json();
  console.log(`Found ${users.length} users`);

  // Display users
  users.forEach(user => {
    console.log(`- ${user.username} (${user.email}) - ${user.subscription_tier}`);
  });
}

getUsers();
```

**Python:**

```python
def get_users(token):
    response = requests.get(
        'https://your-domain.com/api/v1/admin/users',
        headers={'Authorization': f'Bearer {token}'}
    )
    users = response.json()

    print(f"Found {len(users)} users")
    for user in users:
        print(f"- {user['username']} ({user['email']}) - {user.get('subscription_tier', 'none')}")

get_users(token)
```

### Use Case 2: Create a New User

**Goal**: Programmatically create a new user account.

**JavaScript:**

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

  const newUser = await response.json();
  console.log(`Created user: ${newUser.id}`);
  return newUser;
}

// Usage
createUser({
  email: 'john.doe@example.com',
  username: 'johndoe',
  firstName: 'John',
  lastName: 'Doe',
  password: 'SecureP@ssw0rd!',
  role: 'developer',
  tier: 'starter'
});
```

**Python:**

```python
def create_user(token, user_data):
    response = requests.post(
        'https://your-domain.com/api/v1/admin/users/comprehensive',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        json={
            'email': user_data['email'],
            'username': user_data['username'],
            'firstName': user_data['first_name'],
            'lastName': user_data['last_name'],
            'password': user_data['password'],
            'role': user_data.get('role', 'viewer'),
            'subscription_tier': user_data.get('tier', 'trial'),
            'enabled': True
        }
    )

    new_user = response.json()
    print(f"Created user: {new_user['id']}")
    return new_user

# Usage
create_user(token, {
    'email': 'john.doe@example.com',
    'username': 'johndoe',
    'first_name': 'John',
    'last_name': 'Doe',
    'password': 'SecureP@ssw0rd!',
    'role': 'developer',
    'tier': 'starter'
})
```

### Use Case 3: Get Current Subscription

**Goal**: Check your current subscription plan and usage.

**JavaScript:**

```javascript
async function getSubscription() {
  const token = localStorage.getItem('authToken');

  const response = await fetch('/api/v1/billing/subscriptions/current', {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  const subscription = await response.json();

  console.log(`Plan: ${subscription.plan_name}`);
  console.log(`Status: ${subscription.status}`);
  console.log(`API Calls Used: ${subscription.api_calls_used}/${subscription.api_calls_limit}`);
  console.log(`Next Billing: ${subscription.next_billing_date}`);
}

getSubscription();
```

**Python:**

```python
def get_subscription(token):
    response = requests.get(
        'https://your-domain.com/api/v1/billing/subscriptions/current',
        headers={'Authorization': f'Bearer {token}'}
    )

    subscription = response.json()

    print(f"Plan: {subscription['plan_name']}")
    print(f"Status: {subscription['status']}")
    print(f"API Calls: {subscription['api_calls_used']}/{subscription['api_calls_limit']}")
    print(f"Next Billing: {subscription['next_billing_date']}")

get_subscription(token)
```

### Use Case 4: Filter Users by Criteria

**Goal**: Find all professional tier users who are admins.

**JavaScript:**

```javascript
async function filterUsers(filters) {
  const token = localStorage.getItem('authToken');

  const params = new URLSearchParams({
    tier: filters.tier,
    role: filters.role,
    status: filters.status,
    limit: filters.limit || 50
  });

  const response = await fetch(`/api/v1/admin/users?${params}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  const users = await response.json();
  console.log(`Found ${users.length} users matching criteria`);
  return users;
}

// Usage: Find all professional tier admins
filterUsers({
  tier: 'professional',
  role: 'admin',
  status: 'enabled'
});
```

**Python:**

```python
def filter_users(token, **filters):
    params = {
        'tier': filters.get('tier'),
        'role': filters.get('role'),
        'status': filters.get('status'),
        'limit': filters.get('limit', 50)
    }

    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}

    response = requests.get(
        'https://your-domain.com/api/v1/admin/users',
        params=params,
        headers={'Authorization': f'Bearer {token}'}
    )

    users = response.json()
    print(f"Found {len(users)} users matching criteria")
    return users

# Usage
filter_users(token, tier='professional', role='admin', status='enabled')
```

### Use Case 5: Chat with LLM (OpenAI-compatible)

**Goal**: Send a chat message to an AI model via LiteLLM proxy.

**JavaScript:**

```javascript
async function chatWithAI(messages, model = 'openai/gpt-4') {
  const token = localStorage.getItem('authToken');

  const response = await fetch('/api/v1/llm/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: model,
      messages: messages,
      temperature: 0.7,
      max_tokens: 150
    })
  });

  const result = await response.json();
  return result.choices[0].message.content;
}

// Usage
const response = await chatWithAI([
  { role: 'system', content: 'You are a helpful assistant.' },
  { role: 'user', content: 'What is the capital of France?' }
]);

console.log('AI Response:', response);
```

**Python:**

```python
def chat_with_ai(token, messages, model='openai/gpt-4'):
    response = requests.post(
        'https://your-domain.com/api/v1/llm/chat/completions',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        json={
            'model': model,
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 150
        }
    )

    result = response.json()
    return result['choices'][0]['message']['content']

# Usage
response = chat_with_ai(token, [
    {'role': 'system', 'content': 'You are a helpful assistant.'},
    {'role': 'user', 'content': 'What is the capital of France?'}
])

print('AI Response:', response)
```

---

## Error Handling

### Common HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Request completed successfully |
| 401 | Unauthorized | Check your auth token |
| 403 | Forbidden | You don't have permission |
| 404 | Not Found | Resource doesn't exist |
| 422 | Validation Error | Check request body format |
| 429 | Rate Limited | Wait and retry |
| 500 | Server Error | Contact support |

### Handling Errors in Code

**JavaScript:**

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
      throw new Error(error.detail || `HTTP ${response.status} error`);
    }

    return await response.json();
  } catch (error) {
    console.error('API Error:', error.message);
    throw error;
  }
}

// Usage
try {
  const users = await safeApiCall('/api/v1/admin/users');
} catch (error) {
  alert(`Failed to fetch users: ${error.message}`);
}
```

**Python:**

```python
def safe_api_call(url, token, method='GET', data=None):
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
        else:
            raise ValueError(f'Unsupported method: {method}')

        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        error_msg = e.response.json().get('detail', str(e))
        print(f"API Error: {error_msg}")
        raise

# Usage
try:
    users = safe_api_call('https://your-domain.com/api/v1/admin/users', token)
except Exception as e:
    print(f"Failed to fetch users: {e}")
```

---

## Rate Limiting

### Understanding Rate Limits

Every API response includes rate limit headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1698432000
```

### Check Your Current Usage

**JavaScript:**

```javascript
async function checkRateLimit() {
  const token = localStorage.getItem('authToken');

  const response = await fetch('/api/v1/system/status', {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  console.log('Rate Limit:', response.headers.get('X-RateLimit-Limit'));
  console.log('Remaining:', response.headers.get('X-RateLimit-Remaining'));

  const resetTime = parseInt(response.headers.get('X-RateLimit-Reset'));
  const resetDate = new Date(resetTime * 1000);
  console.log('Resets at:', resetDate.toLocaleString());
}
```

### Handling Rate Limits

```javascript
async function apiCallWithRetry(url, options = {}, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    const response = await fetch(url, options);

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

## Next Steps

Now that you've completed the quick start, explore these advanced topics:

### 📚 Documentation

- **Full API Reference**: `/docs/api/API_REFERENCE.md`
- **Code Examples**: `/docs/API_EXAMPLES.md`
- **Security Best Practices**: `/docs/README_SECURITY.md`

### 🛠️ Interactive Tools

- **API Playground**: https://your-domain.com/admin/platform/api-docs
  - Test API endpoints interactively
  - See request/response examples
  - Save and share requests

### 🚀 Advanced Features

1. **Bulk Operations**
   - Import users from CSV
   - Bulk role assignments
   - Bulk tier changes

2. **Organization Management**
   - Create organizations
   - Invite team members
   - Manage roles and permissions

3. **Real-time Updates**
   - WebSocket connections
   - Event subscriptions
   - Live notifications

4. **LLM Integration**
   - 100+ AI models
   - OpenAI-compatible API
   - Usage tracking and cost optimization

### 📊 Monitoring & Analytics

- **User Analytics**: `/api/v1/admin/users/analytics/summary`
- **Billing Analytics**: `/api/v1/billing/analytics`
- **System Metrics**: `/api/v1/system/status`

### 🔐 Security

- **API Key Management**: Create service accounts with API keys
- **Role-Based Access Control**: Assign granular permissions
- **Audit Logging**: Track all API activity

---

## Troubleshooting

### I'm getting 401 Unauthorized errors

**Solution**: Your access token has expired. Refresh it using your refresh token:

```bash
curl -X POST https://auth.your-domain.com/realms/uchub/protocol/openid-connect/token \
  -d "grant_type=refresh_token" \
  -d "client_id=ops-center" \
  -d "client_secret=your-keycloak-client-secret" \
  -d "refresh_token=YOUR_REFRESH_TOKEN"
```

### I'm getting 403 Forbidden errors

**Solution**: You don't have the required permissions. Check your role:

```bash
curl -X GET https://your-domain.com/api/v1/auth/session \
  -H "Authorization: Bearer $OPS_TOKEN"
```

Most admin operations require the `admin` or `moderator` role.

### I'm getting 429 Rate Limit errors

**Solution**: You've exceeded your API quota. Either:
- Wait for the rate limit to reset (check `X-RateLimit-Reset` header)
- Upgrade to a higher tier with more API calls
- Implement exponential backoff in your code

### My requests are timing out

**Solution**: The API has a 30-second timeout for requests. If your operation takes longer:
- Use pagination for large data sets
- Break bulk operations into smaller batches
- Consider using WebSocket connections for real-time updates

---

## Get Help

- 📚 **Documentation**: https://your-domain.com:8086
- 💬 **Support**: support@your-domain.com
- 🐛 **Report Bugs**: https://github.com/Unicorn-Commander/UC-Cloud/issues
- 💡 **Feature Requests**: https://github.com/Unicorn-Commander/UC-Cloud/discussions

---

**Happy coding! 🎉**
