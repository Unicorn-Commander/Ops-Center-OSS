import React, { useState } from 'react';
import {
  DocumentDuplicateIcon,
  CheckCircleIcon,
  ChevronRightIcon,
  CodeBracketIcon,
  UserIcon,
  BuildingOfficeIcon,
  CreditCardIcon,
  ServerIcon,
  CubeIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

const ApiExampleGallery = () => {
  const { currentTheme } = useTheme();
  const [copiedId, setCopiedId] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState('curl');
  const [selectedCategory, setSelectedCategory] = useState('users');

  const isDark = currentTheme === 'dark' || currentTheme === 'unicorn';

  // Example categories
  const categories = [
    { id: 'users', name: 'User Management', icon: UserIcon, color: 'blue' },
    { id: 'organizations', name: 'Organizations', icon: BuildingOfficeIcon, color: 'purple' },
    { id: 'billing', name: 'Billing & Subscriptions', icon: CreditCardIcon, color: 'green' },
    { id: 'llm', name: 'LLM Integration', icon: CubeIcon, color: 'pink' },
    { id: 'system', name: 'System Admin', icon: ServerIcon, color: 'orange' }
  ];

  // Code examples organized by category
  const examples = {
    users: [
      {
        id: 'get-users',
        title: 'List All Users',
        description: 'Retrieve a list of all users in your organization',
        code: {
          curl: `curl -X GET https://unicorncommander.ai/api/v1/admin/users \\
  -H "Authorization: Bearer YOUR_TOKEN"`,
          javascript: `const response = await fetch('/api/v1/admin/users', {
  headers: {
    'Authorization': \`Bearer \${token}\`
  }
});
const users = await response.json();
console.log(\`Found \${users.length} users\`);`,
          python: `import requests

response = requests.get(
    'https://unicorncommander.ai/api/v1/admin/users',
    headers={'Authorization': f'Bearer {token}'}
)
users = response.json()
print(f"Found {len(users)} users")`
        }
      },
      {
        id: 'create-user',
        title: 'Create New User',
        description: 'Create a new user account with full provisioning',
        code: {
          curl: `curl -X POST https://unicorncommander.ai/api/v1/admin/users/comprehensive \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "john.doe@example.com",
    "username": "johndoe",
    "firstName": "John",
    "lastName": "Doe",
    "password": "SecureP@ssw0rd!",
    "role": "developer",
    "subscription_tier": "starter"
  }'`,
          javascript: `const newUser = await fetch('/api/v1/admin/users/comprehensive', {
  method: 'POST',
  headers: {
    'Authorization': \`Bearer \${token}\`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'john.doe@example.com',
    username: 'johndoe',
    firstName: 'John',
    lastName: 'Doe',
    password: 'SecureP@ssw0rd!',
    role: 'developer',
    subscription_tier: 'starter'
  })
});
const user = await newUser.json();`,
          python: `response = requests.post(
    'https://unicorncommander.ai/api/v1/admin/users/comprehensive',
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    },
    json={
        'email': 'john.doe@example.com',
        'username': 'johndoe',
        'firstName': 'John',
        'lastName': 'Doe',
        'password': 'SecureP@ssw0rd!',
        'role': 'developer',
        'subscription_tier': 'starter'
    }
)
user = response.json()`
        }
      },
      {
        id: 'filter-users',
        title: 'Filter Users',
        description: 'Advanced filtering by tier, role, status, and more',
        code: {
          curl: `curl -X GET "https://unicorncommander.ai/api/v1/admin/users?tier=professional&role=admin&status=enabled&limit=50" \\
  -H "Authorization: Bearer YOUR_TOKEN"`,
          javascript: `const params = new URLSearchParams({
  tier: 'professional',
  role: 'admin',
  status: 'enabled',
  limit: 50
});

const response = await fetch(\`/api/v1/admin/users?\${params}\`, {
  headers: { 'Authorization': \`Bearer \${token}\` }
});
const users = await response.json();`,
          python: `params = {
    'tier': 'professional',
    'role': 'admin',
    'status': 'enabled',
    'limit': 50
}

response = requests.get(
    'https://unicorncommander.ai/api/v1/admin/users',
    params=params,
    headers={'Authorization': f'Bearer {token}'}
)
users = response.json()`
        }
      }
    ],
    organizations: [
      {
        id: 'list-orgs',
        title: 'List Organizations',
        description: 'Get all organizations accessible to your account',
        code: {
          curl: `curl -X GET https://unicorncommander.ai/api/v1/organizations \\
  -H "Authorization: Bearer YOUR_TOKEN"`,
          javascript: `const response = await fetch('/api/v1/organizations', {
  headers: { 'Authorization': \`Bearer \${token}\` }
});
const orgs = await response.json();`,
          python: `response = requests.get(
    'https://unicorncommander.ai/api/v1/organizations',
    headers={'Authorization': f'Bearer {token}'}
)
orgs = response.json()`
        }
      },
      {
        id: 'create-org',
        title: 'Create Organization',
        description: 'Create a new organization',
        code: {
          curl: `curl -X POST https://unicorncommander.ai/api/v1/organizations \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Acme Corporation",
    "slug": "acme-corp",
    "description": "Enterprise customer"
  }'`,
          javascript: `const org = await fetch('/api/v1/organizations', {
  method: 'POST',
  headers: {
    'Authorization': \`Bearer \${token}\`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'Acme Corporation',
    slug: 'acme-corp',
    description: 'Enterprise customer'
  })
});`,
          python: `response = requests.post(
    'https://unicorncommander.ai/api/v1/organizations',
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    },
    json={
        'name': 'Acme Corporation',
        'slug': 'acme-corp',
        'description': 'Enterprise customer'
    }
)`
        }
      }
    ],
    billing: [
      {
        id: 'get-plans',
        title: 'Get Subscription Plans',
        description: 'List all available subscription plans',
        code: {
          curl: `curl -X GET https://unicorncommander.ai/api/v1/billing/plans \\
  -H "Authorization: Bearer YOUR_TOKEN"`,
          javascript: `const response = await fetch('/api/v1/billing/plans', {
  headers: { 'Authorization': \`Bearer \${token}\` }
});
const plans = await response.json();
plans.forEach(plan => {
  console.log(\`\${plan.name}: $\${plan.amount_cents / 100}/\${plan.interval}\`);
});`,
          python: `response = requests.get(
    'https://unicorncommander.ai/api/v1/billing/plans',
    headers={'Authorization': f'Bearer {token}'}
)
plans = response.json()
for plan in plans:
    print(f"{plan['name']}: ${plan['amount_cents'] / 100}/{plan['interval']}")`
        }
      },
      {
        id: 'current-subscription',
        title: 'Get Current Subscription',
        description: 'View your current subscription details',
        code: {
          curl: `curl -X GET https://unicorncommander.ai/api/v1/billing/subscriptions/current \\
  -H "Authorization: Bearer YOUR_TOKEN"`,
          javascript: `const response = await fetch('/api/v1/billing/subscriptions/current', {
  headers: { 'Authorization': \`Bearer \${token}\` }
});
const subscription = await response.json();
console.log(\`Plan: \${subscription.plan_name}\`);
console.log(\`Status: \${subscription.status}\`);`,
          python: `response = requests.get(
    'https://unicorncommander.ai/api/v1/billing/subscriptions/current',
    headers={'Authorization': f'Bearer {token}'}
)
subscription = response.json()
print(f"Plan: {subscription['plan_name']}")
print(f"Status: {subscription['status']}")`
        }
      }
    ],
    llm: [
      {
        id: 'chat-completion',
        title: 'Chat Completion',
        description: 'Send a chat message to an AI model (OpenAI-compatible)',
        code: {
          curl: `curl -X POST https://unicorncommander.ai/api/v1/llm/chat/completions \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "openai/gpt-4",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0.7
  }'`,
          javascript: `const result = await fetch('/api/v1/llm/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': \`Bearer \${token}\`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'openai/gpt-4',
    messages: [
      { role: 'system', content: 'You are a helpful assistant.' },
      { role: 'user', content: 'Hello!' }
    ],
    temperature: 0.7
  })
});
const data = await result.json();
console.log(data.choices[0].message.content);`,
          python: `response = requests.post(
    'https://unicorncommander.ai/api/v1/llm/chat/completions',
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    },
    json={
        'model': 'openai/gpt-4',
        'messages': [
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': 'Hello!'}
        ],
        'temperature': 0.7
    }
)
result = response.json()
print(result['choices'][0]['message']['content'])`
        }
      },
      {
        id: 'list-models',
        title: 'List Available Models',
        description: 'Get all available AI models via LiteLLM',
        code: {
          curl: `curl -X GET https://unicorncommander.ai/api/v1/llm/models \\
  -H "Authorization: Bearer YOUR_TOKEN"`,
          javascript: `const response = await fetch('/api/v1/llm/models', {
  headers: { 'Authorization': \`Bearer \${token}\` }
});
const models = await response.json();
models.data.forEach(model => {
  console.log(\`\${model.id}: \${model.owned_by}\`);
});`,
          python: `response = requests.get(
    'https://unicorncommander.ai/api/v1/llm/models',
    headers={'Authorization': f'Bearer {token}'}
)
models = response.json()
for model in models['data']:
    print(f"{model['id']}: {model['owned_by']}")`
        }
      }
    ],
    system: [
      {
        id: 'system-status',
        title: 'Get System Status',
        description: 'Check overall system health and resource usage',
        code: {
          curl: `curl -X GET https://unicorncommander.ai/api/v1/system/status \\
  -H "Authorization: Bearer YOUR_TOKEN"`,
          javascript: `const response = await fetch('/api/v1/system/status', {
  headers: { 'Authorization': \`Bearer \${token}\` }
});
const status = await response.json();
console.log(\`CPU: \${status.cpu_percent}%\`);
console.log(\`Memory: \${status.memory_percent}%\`);`,
          python: `response = requests.get(
    'https://unicorncommander.ai/api/v1/system/status',
    headers={'Authorization': f'Bearer {token}'}
)
status = response.json()
print(f"CPU: {status['cpu_percent']}%")
print(f"Memory: {status['memory_percent']}%")`
        }
      },
      {
        id: 'user-analytics',
        title: 'User Analytics',
        description: 'Get user statistics and metrics',
        code: {
          curl: `curl -X GET https://unicorncommander.ai/api/v1/admin/users/analytics/summary \\
  -H "Authorization: Bearer YOUR_TOKEN"`,
          javascript: `const response = await fetch('/api/v1/admin/users/analytics/summary', {
  headers: { 'Authorization': \`Bearer \${token}\` }
});
const analytics = await response.json();
console.log(\`Total Users: \${analytics.total_users}\`);
console.log(\`Active Users: \${analytics.active_users}\`);`,
          python: `response = requests.get(
    'https://unicorncommander.ai/api/v1/admin/users/analytics/summary',
    headers={'Authorization': f'Bearer {token}'}
)
analytics = response.json()
print(f"Total Users: {analytics['total_users']}")
print(f"Active Users: {analytics['active_users']}")`
        }
      }
    ]
  };

  const handleCopy = (code, exampleId) => {
    navigator.clipboard.writeText(code);
    setCopiedId(exampleId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const currentExamples = examples[selectedCategory] || [];
  const currentCategory = categories.find(c => c.id === selectedCategory);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'} mb-2`}>
          <CodeBracketIcon className="inline-block w-6 h-6 mr-2 mb-1" />
          API Code Examples
        </h2>
        <p className={isDark ? 'text-gray-300' : 'text-gray-600'}>
          Real-world examples for common API operations. Click to copy.
        </p>
      </div>

      {/* Category Selection */}
      <div className="flex flex-wrap gap-2">
        {categories.map((category) => {
          const Icon = category.icon;
          const isActive = selectedCategory === category.id;

          return (
            <button
              key={category.id}
              onClick={() => setSelectedCategory(category.id)}
              className={`
                px-4 py-2 rounded-lg font-medium transition-all duration-200
                flex items-center gap-2
                ${isActive
                  ? isDark
                    ? 'bg-purple-600 text-white shadow-lg'
                    : 'bg-blue-600 text-white shadow-lg'
                  : isDark
                    ? 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }
              `}
            >
              <Icon className="w-5 h-5" />
              {category.name}
            </button>
          );
        })}
      </div>

      {/* Language Selection */}
      <div className="flex gap-2 border-b border-gray-700">
        {['curl', 'javascript', 'python'].map((lang) => (
          <button
            key={lang}
            onClick={() => setSelectedLanguage(lang)}
            className={`
              px-4 py-2 font-medium transition-colors
              ${selectedLanguage === lang
                ? isDark
                  ? 'border-b-2 border-purple-500 text-purple-400'
                  : 'border-b-2 border-blue-500 text-blue-600'
                : isDark
                  ? 'text-gray-400 hover:text-gray-300'
                  : 'text-gray-600 hover:text-gray-800'
              }
            `}
          >
            {lang === 'curl' ? 'cURL' : lang === 'javascript' ? 'JavaScript' : 'Python'}
          </button>
        ))}
      </div>

      {/* Examples List */}
      <div className="space-y-4">
        {currentExamples.map((example) => (
          <div
            key={example.id}
            className={`
              rounded-lg overflow-hidden border
              ${isDark
                ? 'bg-gray-800 border-gray-700'
                : 'bg-white border-gray-200'
              }
            `}
          >
            {/* Example Header */}
            <div className={`px-6 py-4 border-b ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
              <h3 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'} mb-1`}>
                {example.title}
              </h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                {example.description}
              </p>
            </div>

            {/* Code Block */}
            <div className="relative">
              <pre className={`
                px-6 py-4 overflow-x-auto text-sm
                ${isDark ? 'bg-gray-900 text-gray-300' : 'bg-gray-50 text-gray-800'}
              `}>
                <code>{example.code[selectedLanguage]}</code>
              </pre>

              {/* Copy Button */}
              <button
                onClick={() => handleCopy(example.code[selectedLanguage], example.id)}
                className={`
                  absolute top-2 right-2 px-3 py-1.5 rounded-md
                  font-medium text-sm transition-all duration-200
                  flex items-center gap-2
                  ${isDark
                    ? copiedId === example.id
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    : copiedId === example.id
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }
                `}
              >
                {copiedId === example.id ? (
                  <>
                    <CheckCircleIcon className="w-4 h-4" />
                    Copied!
                  </>
                ) : (
                  <>
                    <DocumentDuplicateIcon className="w-4 h-4" />
                    Copy
                  </>
                )}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Footer Links */}
      <div className={`mt-8 p-4 rounded-lg border ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-blue-50 border-blue-200'}`}>
        <h4 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'} mb-2`}>
          Need More Examples?
        </h4>
        <div className="flex flex-wrap gap-4">
          <a
            href="/docs/API_EXAMPLES.md"
            className={`flex items-center gap-2 ${isDark ? 'text-purple-400 hover:text-purple-300' : 'text-blue-600 hover:text-blue-700'}`}
          >
            Complete API Examples Guide
            <ChevronRightIcon className="w-4 h-4" />
          </a>
          <a
            href="/docs/API_QUICK_START.md"
            className={`flex items-center gap-2 ${isDark ? 'text-purple-400 hover:text-purple-300' : 'text-blue-600 hover:text-blue-700'}`}
          >
            Quick Start Tutorial
            <ChevronRightIcon className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  );
};

export default ApiExampleGallery;
