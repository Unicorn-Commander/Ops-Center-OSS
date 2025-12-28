/**
 * K6 Load Testing Script for Ops-Center Billing API
 * ===================================================
 *
 * Usage:
 *   k6 run k6_load_test.js
 *   k6 run --vus 100 --duration 30s k6_load_test.js
 *   k6 run --vus 1000 --duration 1m k6_load_test.js  # Stress test
 *
 * Stages:
 *   1. Ramp-up: 0 → 100 users over 30s
 *   2. Sustained: 100 users for 1 minute
 *   3. Peak: 100 → 1000 users over 30s
 *   4. Sustained Peak: 1000 users for 1 minute
 *   5. Ramp-down: 1000 → 0 users over 30s
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const balanceCheckDuration = new Trend('balance_check_duration');
const usageSummaryDuration = new Trend('usage_summary_duration');
const transactionListDuration = new Trend('transaction_list_duration');
const orgBillingDuration = new Trend('org_billing_duration');
const creditPurchaseErrors = new Counter('credit_purchase_errors');
const authErrors = new Counter('auth_errors');

// Configuration
export const options = {
  stages: [
    { duration: '30s', target: 100 },   // Ramp-up to 100 users
    { duration: '1m', target: 100 },    // Stay at 100 users
    { duration: '30s', target: 500 },   // Ramp up to 500 users
    { duration: '1m', target: 500 },    // Stay at 500 users
    { duration: '30s', target: 1000 },  // Peak to 1000 users
    { duration: '1m', target: 1000 },   // Stay at 1000 users
    { duration: '30s', target: 0 },     // Ramp-down to 0 users
  ],

  thresholds: {
    // Performance thresholds
    'http_req_duration': ['p(95)<100', 'p(99)<500'],  // 95% < 100ms, 99% < 500ms
    'http_req_failed': ['rate<0.01'],  // Error rate < 1%
    'errors': ['rate<0.05'],  // Custom error rate < 5%

    // Specific endpoint thresholds
    'balance_check_duration': ['p(95)<50', 'p(99)<100'],  // Very fast
    'usage_summary_duration': ['p(95)<75', 'p(99)<150'],
    'transaction_list_duration': ['p(95)<100', 'p(99)<200'],
    'org_billing_duration': ['p(95)<150', 'p(99)<300'],
  },

  // Additional options
  noConnectionReuse: false,  // Reuse connections
  userAgent: 'K6LoadTest/1.0',
  insecureSkipTLSVerify: true,  // For local testing
};

// Base URL
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8084';

// Test data
const userIds = Array.from({ length: 1000 }, (_, i) => `user_${10000 + i}`);
const orgIds = Array.from({ length: 100 }, (_, i) => `org_${1000 + i}`);

// Helper functions
function getRandomUser() {
  return userIds[Math.floor(Math.random() * userIds.length)];
}

function getRandomOrg() {
  return orgIds[Math.floor(Math.random() * orgIds.length)];
}

function getAuthHeaders(userId, role = 'user', orgId = null) {
  const headers = {
    'Authorization': `Bearer test_token_${userId}`,
    'Cookie': `session_token=test_session_${userId}`,
    'Content-Type': 'application/json',
  };

  if (role === 'admin') {
    headers['X-Admin'] = 'true';
  }

  if (orgId) {
    headers['X-Org-ID'] = orgId;
  }

  return headers;
}

// ============================================================================
// Test Scenarios
// ============================================================================

export default function() {
  const userId = getRandomUser();
  const orgId = getRandomOrg();

  // Weighted scenario selection (simulates realistic traffic)
  const scenario = Math.random();

  if (scenario < 0.70) {
    // 70% - End user checking balance/usage
    endUserScenario(userId);
  } else if (scenario < 0.90) {
    // 20% - Organization admin checking org billing
    orgAdminScenario(userId, orgId);
  } else {
    // 10% - System admin checking platform analytics
    systemAdminScenario(userId);
  }

  sleep(1); // Think time between requests
}

/**
 * End User Scenario (70% of traffic)
 * Most common: check balance, view usage, browse transactions
 */
function endUserScenario(userId) {
  const headers = getAuthHeaders(userId);

  group('End User - Check Balance', function() {
    const start = Date.now();
    const res = http.get(`${BASE_URL}/api/v1/credits/balance`, { headers });
    const duration = Date.now() - start;

    balanceCheckDuration.add(duration);

    const success = check(res, {
      'balance check status is 200': (r) => r.status === 200,
      'balance check has balance field': (r) => JSON.parse(r.body).balance !== undefined,
      'balance check duration < 50ms': () => duration < 50,
    });

    if (!success) {
      errorRate.add(1);
      if (res.status === 401) authErrors.add(1);
    }
  });

  sleep(0.5);

  group('End User - Usage Summary', function() {
    const start = Date.now();
    const res = http.get(`${BASE_URL}/api/v1/credits/usage/summary`, { headers });
    const duration = Date.now() - start;

    usageSummaryDuration.add(duration);

    check(res, {
      'usage summary status is 200': (r) => r.status === 200,
      'usage summary duration < 75ms': () => duration < 75,
    }) || errorRate.add(1);
  });

  // 50% also check transaction history
  if (Math.random() < 0.5) {
    sleep(0.5);

    group('End User - Transaction History', function() {
      const start = Date.now();
      const res = http.get(`${BASE_URL}/api/v1/credits/transactions?limit=20`, { headers });
      const duration = Date.now() - start;

      transactionListDuration.add(duration);

      check(res, {
        'transactions status is 200': (r) => r.status === 200,
        'transactions is array': (r) => Array.isArray(JSON.parse(r.body).transactions),
        'transactions duration < 100ms': () => duration < 100,
      }) || errorRate.add(1);
    });
  }
}

/**
 * Organization Admin Scenario (20% of traffic)
 * Check org subscription, credit pool, member usage
 */
function orgAdminScenario(userId, orgId) {
  const headers = getAuthHeaders(userId, 'org_admin', orgId);

  group('Org Admin - Get Subscription', function() {
    const start = Date.now();
    const res = http.get(
      `${BASE_URL}/api/v1/org-billing/organizations/${orgId}/subscription`,
      { headers }
    );
    const duration = Date.now() - start;

    orgBillingDuration.add(duration);

    check(res, {
      'org subscription status is 200 or 404': (r) => [200, 404].includes(r.status),
      'org subscription duration < 150ms': () => duration < 150,
    }) || errorRate.add(1);
  });

  sleep(0.5);

  group('Org Admin - Credit Pool', function() {
    const res = http.get(
      `${BASE_URL}/api/v1/org-billing/organizations/${orgId}/credit-pool`,
      { headers }
    );

    check(res, {
      'credit pool status is 200 or 404': (r) => [200, 404].includes(r.status),
    }) || errorRate.add(1);
  });

  sleep(0.5);

  group('Org Admin - Member Usage', function() {
    const res = http.get(
      `${BASE_URL}/api/v1/org-billing/organizations/${orgId}/usage/users`,
      { headers }
    );

    check(res, {
      'member usage status is 200 or 404': (r) => [200, 404].includes(r.status),
    }) || errorRate.add(1);
  });
}

/**
 * System Admin Scenario (10% of traffic)
 * Platform analytics, revenue trends, all subscriptions
 */
function systemAdminScenario(userId) {
  const headers = getAuthHeaders(userId, 'admin');

  group('System Admin - Platform Analytics', function() {
    const res = http.get(
      `${BASE_URL}/api/v1/org-billing/analytics/platform`,
      { headers }
    );

    check(res, {
      'platform analytics status is 200': (r) => r.status === 200,
    }) || errorRate.add(1);
  });

  sleep(0.5);

  group('System Admin - Revenue Trends', function() {
    const res = http.get(
      `${BASE_URL}/api/v1/org-billing/analytics/revenue-trends?period=30d`,
      { headers }
    );

    check(res, {
      'revenue trends status is 200': (r) => r.status === 200,
    }) || errorRate.add(1);
  });

  sleep(0.5);

  group('System Admin - All Subscriptions', function() {
    const res = http.get(
      `${BASE_URL}/api/v1/org-billing/subscriptions?limit=100`,
      { headers }
    );

    check(res, {
      'all subscriptions status is 200': (r) => r.status === 200,
    }) || errorRate.add(1);
  });
}

// ============================================================================
// Test Summary
// ============================================================================

export function handleSummary(data) {
  return {
    'summary.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}

function textSummary(data, options) {
  const indent = options.indent || '';
  const enableColors = options.enableColors || false;

  const metrics = data.metrics;

  let summary = '\n\n';
  summary += `${indent}Load Test Summary\n`;
  summary += `${indent}${'='.repeat(60)}\n\n`;

  // HTTP metrics
  summary += `${indent}HTTP Performance:\n`;
  summary += `${indent}  Requests: ${metrics.http_reqs.count}\n`;
  summary += `${indent}  Duration (avg): ${metrics.http_req_duration.values.avg.toFixed(2)}ms\n`;
  summary += `${indent}  Duration (p95): ${metrics.http_req_duration.values['p(95)'].toFixed(2)}ms\n`;
  summary += `${indent}  Duration (p99): ${metrics.http_req_duration.values['p(99)'].toFixed(2)}ms\n`;
  summary += `${indent}  Failed: ${(metrics.http_req_failed.values.rate * 100).toFixed(2)}%\n\n`;

  // Custom metrics
  if (metrics.balance_check_duration) {
    summary += `${indent}Balance Check Performance:\n`;
    summary += `${indent}  p95: ${metrics.balance_check_duration.values['p(95)'].toFixed(2)}ms\n`;
    summary += `${indent}  p99: ${metrics.balance_check_duration.values['p(99)'].toFixed(2)}ms\n\n`;
  }

  // Thresholds
  summary += `${indent}Threshold Results:\n`;
  for (const [name, threshold] of Object.entries(data.thresholds || {})) {
    const status = threshold.ok ? '✓ PASS' : '✗ FAIL';
    summary += `${indent}  ${status}: ${name}\n`;
  }

  summary += '\n';

  return summary;
}
