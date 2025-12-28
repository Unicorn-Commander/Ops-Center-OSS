# Advanced Log Search - Quick Start Guide

## 🚀 Access the Log Search

**URL**: https://your-domain.com/admin/logs

**Steps**:
1. Login to Ops-Center
2. Navigate to "Logs & Diagnostics" in sidebar
3. Click "Log History" tab
4. Use the filter panel to search logs

---

## 🔍 Quick Search Examples

### Find All Errors
1. Check ☑️ "ERROR" in Severity Levels
2. Click "Search"

### Find Errors from Specific Service
1. Check ☑️ "ERROR"
2. Check ☑️ "ops-center-direct"
3. Click "Search"

### Find Logs from Today
1. Set Start Date: 2025-11-29
2. Set End Date: 2025-11-29
3. Click "Search"

### Search for "failed" in Messages
1. Type "failed" in Text Search
2. Press Enter or click "Search"

### Use Regex Pattern
1. Check ☑️ "Use Regex Pattern"
2. Enter: `user.*failed`
3. Click "Search"

---

## ⚙️ Filter Options

| Filter | What It Does | Example |
|--------|--------------|---------|
| **Text Search** | Search in messages | "error", "timeout" |
| **Severity** | Filter by log level | ERROR, WARN, INFO |
| **Services** | Filter by container | ops-center, litellm |
| **Start/End Date** | Date range | 2025-11-28 to 2025-11-29 |
| **Regex** | Pattern matching | `user_\d+`, `(error\|fail)` |

---

## 🎯 Common Use Cases

### Debug a User Login Issue
```
Filters:
- Text Search: "login" OR "authentication"
- Severity: ERROR, WARN
- Services: ops-center, keycloak
- Date: Today
```

### Find LLM API Errors
```
Filters:
- Severity: ERROR
- Services: litellm, ops-center
- Date: Last 7 days
```

### Audit Admin Actions
```
Filters:
- Text Search: "admin"
- Services: ops-center
- Regex: "admin.*created|admin.*deleted"
```

### Monitor Database Issues
```
Filters:
- Text Search: "database" OR "postgres"
- Severity: ERROR, WARN
- Services: unicorn-postgresql
```

---

## 🎨 Result Display

**Result Stats**:
- "Showing 1-100 of 1,523 results" - Current page range
- "Query time: 145.23ms" - How fast the search ran
- "✓ Cached" - Green checkmark if results were cached (super fast!)

**Result Viewer**:
- Color-coded by severity (red=ERROR, yellow=WARN, blue=INFO, gray=DEBUG)
- Shows timestamp, severity, service name, and message
- Monospace font for easy reading

**Pagination**:
- Results per page: 50/100/200/500 (configurable)
- Previous/Next buttons
- "Page 1 of 16" indicator

---

## ⚡ Performance Tips

### Fast Queries
✅ Use specific date ranges (today, last 7 days)
✅ Filter by severity (ERROR only)
✅ Filter by 1-2 services only
✅ Use smaller page sizes (50-100)

### Slow Queries
❌ No filters (searches all logs)
❌ Very large date ranges (> 1 month)
❌ All services selected
❌ Large page sizes (500+)

**Pro Tip**: Cached queries return in <10ms! Repeat the same search for instant results.

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl + F` | Focus text search input |
| `Enter` | Execute search |
| `Escape` | Clear filters |

---

## 🐛 Troubleshooting

### "No logs found"
1. Check that services are running (Services filter dropdown should show names)
2. Verify date range is correct (not in the future!)
3. Try removing filters one by one
4. Click "Clear Filters" and start over

### "Search is slow"
1. Add a date range filter (narrow the search)
2. Filter by specific services
3. Add severity filter (ERROR or WARN only)
4. Reduce Results per page to 100

### "Cache hit" not showing
- Cache builds after first search
- Repeat the EXACT same search to see green checkmark
- Cache lasts 5 minutes

---

## 📋 Regex Pattern Examples

| Pattern | Matches | Example |
|---------|---------|---------|
| `failed` | Word "failed" | "Login failed" |
| `user.*failed` | "user" then "failed" | "User auth failed" |
| `(?i)error` | "error" (any case) | "Error", "ERROR" |
| `^\[ERROR\]` | Lines starting with "[ERROR]" | "[ERROR] Connection lost" |
| `user_\d+` | "user_" + numbers | "user_123", "user_456" |
| `(error\|fail)` | Either "error" or "fail" | "error occurred" or "failed to connect" |

---

## 📊 Example: Find All LiteLLM Errors Today

**Steps**:
1. Navigate to `/admin/logs` → "Log History"
2. Check ☑️ "ERROR" in Severity
3. Check ☑️ "unicorn-litellm" in Services
4. Set Start Date: 2025-11-29
5. Set End Date: 2025-11-29
6. Click "Search"

**Result**: All ERROR logs from LiteLLM today, sorted newest first

---

## 🔗 API Access (Advanced)

**Endpoint**: `POST /api/v1/logs/search/advanced`

**Example**:
```bash
curl -X POST https://your-domain.com/api/v1/logs/search/advanced \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <token-from-browser>" \
  -d '{
    "severity": ["ERROR"],
    "services": ["ops-center-direct"],
    "start_date": "2025-11-29",
    "limit": 100
  }'
```

**Note**: API requires CSRF token. Easiest to use the frontend UI.

---

## 📚 Full Documentation

See: `/services/ops-center/docs/LOGS_SEARCH_API.md` (20+ pages)

Covers:
- All 4 API endpoints
- Request/response examples
- Filter syntax guide
- Performance optimization
- Troubleshooting
- Integration examples (JavaScript, Python)

---

## ✅ Quick Checklist

Before reporting a bug:
- [ ] Cleared all filters and tried again
- [ ] Verified date range is correct
- [ ] Checked that services are running
- [ ] Tried with just one filter at a time
- [ ] Cleared browser cache (Ctrl+Shift+Delete)

---

**Last Updated**: November 29, 2025
**Version**: 1.0.0
**Status**: ✅ Production Ready
