# End-to-End Test Scenarios for Epic 3.1: LiteLLM Multi-Provider Routing

## Overview

This document outlines comprehensive end-to-end test scenarios for manual testing of the LiteLLM Multi-Provider Routing system. These scenarios cover the complete user journey from BYOK setup to usage analytics.

---

## Scenario 1: BYOK Setup Flow

### Objective
Verify that users can successfully add and manage their own API keys for LLM providers.

### Prerequisites
- User is logged in to Ops Center
- User has valid API keys for at least one provider (OpenAI, Anthropic, or Google)

### Test Steps

1. **Navigate to API Keys Page**
   - Click on user profile dropdown (top right)
   - Select "Account Settings"
   - Click on "API Keys" tab
   - **Expected**: API Keys management page loads successfully

2. **Add New BYOK Key**
   - Click "Add LLM Provider" button
   - **Expected**: Modal dialog opens with provider selection dropdown

3. **Select Provider**
   - Select "OpenAI" from dropdown
   - **Expected**: API key input field and key name field appear

4. **Enter API Key**
   - Paste valid OpenAI API key (format: `sk-...`)
   - Enter key name: "My OpenAI Key"
   - **Expected**: Form validates input format

5. **Test Connection**
   - Click "Test Connection" button
   - **Expected**:
     - Loading spinner appears
     - After 2-3 seconds, success message: "Connection successful"
     - Green checkmark icon appears

6. **Save Key**
   - Click "Save" button
   - **Expected**:
     - Success notification: "API key saved successfully"
     - Modal closes
     - New key appears in keys list with masked value (`sk-...****abcd`)

7. **Verify Key in List**
   - **Expected**: Key card shows:
     - Provider name: "OpenAI"
     - Key name: "My OpenAI Key"
     - Status: "Active" (green badge)
     - Created date
     - Last used: "Never" (initially)
     - Actions: "Test", "Delete" buttons

### Negative Tests

**Test Invalid API Key**
- Enter invalid key: `invalid-key-format`
- Click "Test Connection"
- **Expected**: Error message "Invalid API key format or authentication failed"

**Test Duplicate Provider**
- Try to add another OpenAI key
- **Expected**: Warning message "You already have a key for this provider. This will replace it."

**Test Empty Fields**
- Leave API key field empty
- Click "Save"
- **Expected**: Validation error "API key is required"

### Success Criteria
- [x] User can add BYOK key
- [x] Key is encrypted and masked in UI
- [x] Connection test validates key
- [x] Key appears in user's key list
- [x] Appropriate error messages shown for invalid inputs

---

## Scenario 2: Power Level Usage

### Objective
Verify that LLM requests with different power levels route to appropriate models and use BYOK when available.

### Prerequisites
- User has BYOK key configured for OpenAI
- User is on Ops Center dashboard or chat interface

### Test Steps

#### Part A: Eco Power Level

1. **Open Chat Interface**
   - Navigate to Chat tab
   - **Expected**: Chat interface loads with message input

2. **Enable Eco Mode**
   - Click power level selector (default: "Balanced")
   - Select "Eco" mode
   - **Expected**: Eco mode badge shows "Free/Ultra-Low Cost"

3. **Send Test Message**
   - Type: "What is the capital of France?"
   - Click Send
   - **Expected**:
     - Message sends successfully
     - Response received within 5-10 seconds
     - Model indicator shows: "Qwen 2.5 32B (vLLM)" or "Gemini 1.5 Flash"

4. **Verify Routing Info**
   - Click "Details" on message
   - **Expected**:
     - Power level: "eco"
     - Cost per 1K tokens: $0.00 or <$0.0001
     - Used BYOK: "No" (eco prefers free platform models)

#### Part B: Balanced Power Level

1. **Switch to Balanced Mode**
   - Click power level selector
   - Select "Balanced"
   - **Expected**: Badge shows "Best Value"

2. **Send Complex Query**
   - Type: "Explain quantum entanglement in simple terms with an analogy"
   - Click Send
   - **Expected**:
     - Response is more detailed and coherent
     - Model indicator shows: "GPT-4o Mini", "Claude 3.5 Haiku", or "Gemini Flash"

3. **Verify BYOK Usage**
   - Click "Details" on message
   - **Expected**:
     - Power level: "balanced"
     - Cost per 1K tokens: $0.0002-$0.005
     - **Used BYOK: "Yes"** (should use user's OpenAI key if available)
     - Provider: "OpenAI" (user's key)

#### Part C: Precision Power Level

1. **Switch to Precision Mode**
   - Click power level selector
   - Select "Precision"
   - **Expected**: Badge shows "Premium Models"

2. **Send Creative Task**
   - Type: "Write a creative short story about a time-traveling cat"
   - Click Send
   - **Expected**:
     - Response is highly creative and well-structured
     - Model indicator shows: "GPT-4o" or "Claude 3.5 Sonnet"
     - Response time: 10-20 seconds

3. **Verify Premium Routing**
   - Click "Details" on message
   - **Expected**:
     - Power level: "precision"
     - Cost per 1K tokens: $0.015
     - Used BYOK: "Yes"
     - Provider: "OpenAI"
     - Tokens used: ~500-1000

### Success Criteria
- [x] Eco mode uses free/cheapest models
- [x] Balanced mode uses mid-tier models
- [x] Precision mode uses premium models
- [x] BYOK key used when available and appropriate
- [x] Routing decisions are transparent to user

---

## Scenario 3: Fallback Mechanism

### Objective
Verify that system gracefully handles provider failures and falls back to alternative providers.

### Prerequisites
- Admin access to Ops Center
- Multiple providers configured

### Test Steps

1. **Verify All Providers Healthy**
   - Navigate to Admin → LLM Providers
   - **Expected**: All providers show green "Healthy" status

2. **Disable Primary Provider**
   - Find OpenAI provider (priority 1)
   - Click "Edit" button
   - Toggle "Enabled" switch to OFF
   - Click "Save"
   - **Expected**:
     - OpenAI status changes to "Disabled" (gray)
     - Warning: "Some users may experience fallback to alternative providers"

3. **Make LLM Request as User**
   - Log in as regular user (with OpenAI BYOK key)
   - Send message with balanced power level
   - **Expected**:
     - Request succeeds (no error shown to user)
     - Response received normally
     - Model used is NOT OpenAI (fallback to Anthropic or Google)

4. **Verify Fallback in Details**
   - Click message details
   - **Expected**:
     - Provider: "Anthropic" or "Google" (not OpenAI)
     - Used BYOK: "No" (user's OpenAI key not used due to provider disabled)
     - Message: "Fallback to alternative provider"

5. **Check Health Dashboard**
   - Navigate to Admin → System Health
   - **Expected**:
     - Alert: "OpenAI provider disabled, fallback active"
     - Requests routed to other providers increase

6. **Re-enable Provider**
   - Go back to Admin → LLM Providers
   - Toggle OpenAI back to enabled
   - Click "Test Health" button
   - **Expected**: Status changes to "Healthy" within 10 seconds

7. **Verify Normal Routing Restored**
   - Send another message as user
   - **Expected**: OpenAI used again (with user's BYOK key)

### Negative Test: All Providers Down

1. **Disable All Providers**
   - Admin disables all providers except one
   - **Expected**: System warns "Critical: Only one provider available"

2. **Make Request**
   - User sends message
   - **Expected**:
     - Request routed to last available provider
     - Warning shown: "Limited provider availability"

3. **Disable Last Provider**
   - Admin disables last provider
   - **Expected**: Error page: "LLM service temporarily unavailable"

### Success Criteria
- [x] System detects provider failures
- [x] Automatic fallback to healthy providers
- [x] No errors exposed to end users
- [x] Usage logged correctly with fallback info
- [x] Health dashboard shows provider status

---

## Scenario 4: Usage Analytics

### Objective
Verify that all LLM usage is tracked and displayed accurately in analytics dashboard.

### Prerequisites
- User has made several LLM requests (from Scenarios 2-3)
- At least 24 hours of usage data available

### Test Steps

#### Part A: Dashboard Overview

1. **Navigate to Usage Dashboard**
   - Click on "Usage" in left sidebar
   - Select "LLM Usage" tab
   - **Expected**: Dashboard loads with charts and stats

2. **Verify Stats Cards**
   - **Expected**: Four cards showing:
     - **Total Requests**: Count of all LLM calls
     - **Total Tokens**: Sum of prompt + completion tokens
     - **Total Cost**: Dollar amount (with cents precision)
     - **Avg Response Time**: Milliseconds

3. **Check Accuracy**
   - Stats should match recent activity
   - **Expected**: Non-zero values if user has made requests

#### Part B: Charts Analysis

1. **Requests by Power Level Chart**
   - **Expected**: Pie chart showing:
     - Eco: X%
     - Balanced: Y%
     - Precision: Z%
   - Hover shows exact counts

2. **Requests by Provider Chart**
   - **Expected**: Bar chart showing:
     - OpenAI: X requests
     - Anthropic: Y requests
     - Google: Z requests
     - vLLM: W requests

3. **Cost Over Time Chart**
   - **Expected**: Line graph showing daily cost
   - Date range selector: "Last 7 days" (default)
   - Tooltips show exact cost per day

4. **BYOK vs Platform Usage**
   - **Expected**: Stacked bar chart showing:
     - BYOK requests (blue)
     - Platform requests (gray)
     - Percentage breakdown

#### Part C: Detailed Usage Table

1. **Scroll to Usage Log Table**
   - **Expected**: Table with columns:
     - Timestamp
     - Model Used
     - Provider
     - Power Level
     - Tokens (Prompt/Completion)
     - Cost
     - BYOK (Yes/No)
     - Response Time

2. **Filter by Date Range**
   - Select "Last 30 days"
   - **Expected**: Table updates with last 30 days of data

3. **Filter by Power Level**
   - Select "Precision only"
   - **Expected**: Table shows only precision requests

4. **Filter by Provider**
   - Select "OpenAI only"
   - **Expected**: Table shows only OpenAI requests

5. **Sort Table**
   - Click "Cost" column header
   - **Expected**: Table sorts by cost (highest first)

#### Part D: Export Data

1. **Export as CSV**
   - Click "Export CSV" button
   - **Expected**:
     - Download starts
     - File name: `llm_usage_YYYYMMDD.csv`
     - File opens in Excel/spreadsheet app

2. **Verify CSV Content**
   - **Expected**: CSV contains:
     - All visible table columns
     - Correct date format
     - Cost in dollars (2 decimal places)
     - All filtered data (if filters applied)

3. **Export with Date Range**
   - Select custom date range: "Last 7 days"
   - Click "Export CSV"
   - **Expected**: CSV contains only last 7 days

### Admin Analytics (Admin Only)

1. **Navigate to Admin Analytics**
   - Admin → Analytics → LLM Usage (All Users)
   - **Expected**: Aggregate view of all users

2. **Verify Aggregate Stats**
   - **Expected**: Stats cards show platform-wide totals:
     - Total requests (all users)
     - Total platform cost
     - Avg requests per user
     - Top providers

3. **Cost Breakdown by User**
   - **Expected**: Table showing:
     - Username
     - Total requests
     - Total cost
     - BYOK usage percentage

### Success Criteria
- [x] All requests logged accurately
- [x] Charts update in real-time
- [x] Filters work correctly
- [x] Cost calculations accurate
- [x] BYOK vs platform usage tracked
- [x] CSV export includes all data
- [x] Admin can view platform-wide analytics

---

## Scenario 5: Multi-Provider BYOK

### Objective
Verify that users can configure multiple BYOK keys and system intelligently routes based on power level preferences.

### Prerequisites
- User has accounts with OpenAI, Anthropic, and Google
- User has valid API keys for all three providers

### Test Steps

1. **Add Multiple BYOK Keys**
   - Navigate to Account → API Keys
   - Add OpenAI key: "My OpenAI Key"
   - Add Anthropic key: "My Anthropic Key"
   - Add Google key: "My Google Key"
   - **Expected**: All three keys visible in list

2. **Send Request (System Chooses)**
   - Set power level: Balanced
   - Send message: "Explain machine learning"
   - **Expected**:
     - System routes to cheapest BYOK option for balanced tier
     - Likely Anthropic Haiku or Google Gemini Flash

3. **Force Specific Provider**
   - Advanced settings → Select provider: "OpenAI"
   - Send message: "Another query"
   - **Expected**: Uses OpenAI (user's key) even if not cheapest

4. **Compare Costs**
   - View usage dashboard
   - Filter by provider
   - **Expected**: Can compare costs across providers

### Success Criteria
- [x] Multiple BYOK keys supported
- [x] System intelligently routes to cheapest available
- [x] User can override provider selection
- [x] All providers tracked separately

---

## Scenario 6: Rate Limiting and Quotas

### Objective
Verify that rate limits are enforced per user and appropriate errors are shown.

### Prerequisites
- Rate limits configured in system (e.g., 100 requests/hour)

### Test Steps

1. **Make Normal Requests**
   - Send 50 messages rapidly
   - **Expected**: All succeed

2. **Approach Rate Limit**
   - Send 50 more messages
   - **Expected**:
     - Requests 1-100 succeed
     - Request 101: Error "Rate limit exceeded"

3. **Check Error Message**
   - **Expected**: User-friendly error:
     - "You've reached your request limit"
     - "Try again in X minutes"
     - "Upgrade to Pro for higher limits"

4. **Verify Rate Limit Reset**
   - Wait 1 hour (or configured reset time)
   - Send new message
   - **Expected**: Success (limit reset)

### Success Criteria
- [x] Rate limits enforced per user
- [x] Clear error messages
- [x] Limits reset automatically
- [x] Admins can adjust limits per user

---

## Scenario 7: Streaming Responses

### Objective
Verify that streaming LLM responses work correctly with all providers.

### Prerequisites
- Streaming enabled in frontend

### Test Steps

1. **Enable Streaming**
   - Settings → Streaming: ON
   - **Expected**: Toggle switches to enabled

2. **Send Long Query**
   - Ask: "Write a detailed explanation of neural networks"
   - **Expected**:
     - Response appears word-by-word (streaming)
     - No delay before first word
     - Smooth streaming experience

3. **Test with Different Providers**
   - Repeat with Eco, Balanced, Precision
   - **Expected**: Streaming works for all providers

4. **Cancel Streaming**
   - Send long query
   - Click "Stop" button mid-stream
   - **Expected**:
     - Streaming stops immediately
     - Partial response visible
     - No error shown

### Success Criteria
- [x] Streaming works for all providers
- [x] No initial delay
- [x] Cancellation works correctly
- [x] Usage tracked for partial responses

---

## Scenario 8: Error Recovery

### Objective
Verify that system handles various error conditions gracefully.

### Test Steps

#### Test A: Invalid BYOK Key Mid-Request

1. **User deletes BYOK key**
   - Account → API Keys → Delete OpenAI key
2. **Make request**
   - **Expected**: Falls back to platform key or alternative provider

#### Test B: Provider Rate Limit

1. **User exhausts OpenAI quota**
   - OpenAI returns 429 (rate limit)
2. **System response**
   - **Expected**:
     - Auto-fallback to Anthropic
     - User sees normal response
     - Warning: "Switched to alternative provider"

#### Test C: Network Timeout

1. **Provider times out**
   - Network delay >30 seconds
2. **System response**
   - **Expected**:
     - Timeout message after 30s
     - "Retrying with alternative provider..."
     - Eventually succeeds with fallback

### Success Criteria
- [x] Graceful error handling
- [x] Automatic retries
- [x] Fallback mechanisms
- [x] User-friendly error messages

---

## Test Execution Checklist

### Pre-Test Setup
- [ ] Ops Center running on `localhost:8084`
- [ ] Test user account created
- [ ] Valid API keys available (OpenAI, Anthropic, Google)
- [ ] Database seeded with initial data
- [ ] All providers enabled and healthy

### Scenario Completion
- [ ] Scenario 1: BYOK Setup Flow
- [ ] Scenario 2: Power Level Usage
- [ ] Scenario 3: Fallback Mechanism
- [ ] Scenario 4: Usage Analytics
- [ ] Scenario 5: Multi-Provider BYOK
- [ ] Scenario 6: Rate Limiting
- [ ] Scenario 7: Streaming Responses
- [ ] Scenario 8: Error Recovery

### Post-Test Validation
- [ ] All usage logged correctly
- [ ] No data leaks (API keys not exposed)
- [ ] Performance acceptable (<2s response time)
- [ ] No memory leaks
- [ ] Logs clean (no errors)

---

## Bug Reporting Template

If issues are found during testing, report using this template:

```markdown
**Bug ID**: E3.1-BUG-XXX
**Severity**: Critical / High / Medium / Low
**Scenario**: [Scenario number and name]
**Step**: [Step number where bug occurred]

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happened]

**Steps to Reproduce**:
1. [First step]
2. [Second step]
3. [...]

**Screenshots/Logs**:
[Attach relevant screenshots or log excerpts]

**Environment**:
- Browser: [Chrome/Firefox/Safari]
- OS: [Windows/Mac/Linux]
- Ops Center version: [X.Y.Z]

**Workaround** (if any):
[Temporary solution]
```

---

## Test Sign-Off

**Tester Name**: _______________
**Date**: _______________
**Scenarios Passed**: ____ / 8
**Scenarios Failed**: ____ / 8
**Bugs Filed**: ____

**Overall Status**: ✅ PASS / ❌ FAIL / ⚠️ PASS WITH ISSUES

**Comments**:
_____________________________________________
_____________________________________________
