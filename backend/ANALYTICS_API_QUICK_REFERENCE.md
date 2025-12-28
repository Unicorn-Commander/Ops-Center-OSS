# Analytics & Metering API - Quick Reference

**Date**: November 26, 2025
**Base URL**: `http://localhost:8084` or `https://your-domain.com`

---

## LLM Usage & Costs (3 endpoints)

```bash
# 1. LLM Usage Summary
GET /api/v1/llm/usage/summary?range=month
# range: day, week, month, year

# 2. LLM Costs
GET /api/v1/llm/costs?period=30d
# period: 7d, 30d, 90d, etc.

# 3. LLM Cache Stats
GET /api/v1/llm/cache-stats
```

---

## Revenue Analytics (5 endpoints)

```bash
# 4. Monthly Recurring Revenue
GET /api/v1/analytics/revenue/mrr?months=12
# months: 1-24

# 5. Annual Recurring Revenue
GET /api/v1/analytics/revenue/arr

# 6. Revenue Growth
GET /api/v1/analytics/revenue/growth

# 7. Revenue Forecast
GET /api/v1/analytics/revenue/forecast?months_ahead=6
# months_ahead: 1-12

# 8. Revenue by Tier
GET /api/v1/analytics/revenue/by-tier
```

---

## User Analytics (3 endpoints)

```bash
# 9. Customer Lifetime Value
GET /api/v1/analytics/users/ltv

# 10. User Churn Rate
GET /api/v1/analytics/users/churn

# 11. User Acquisition
GET /api/v1/analytics/users/acquisition
```

---

## Service Analytics (4 endpoints)

```bash
# 12. Service Popularity
GET /api/v1/analytics/services/popularity

# 13. Cost per User
GET /api/v1/analytics/services/cost-per-user

# 14. Service Adoption
GET /api/v1/analytics/services/adoption

# 15. Service Performance
GET /api/v1/analytics/services/performance
```

---

## Metrics & KPIs (3 endpoints)

```bash
# 16. Metrics Summary
GET /api/v1/analytics/metrics/summary

# 17. KPIs
GET /api/v1/analytics/metrics/kpis

# 18. Metric Alerts
GET /api/v1/analytics/metrics/alerts
```

---

## Metering (3 endpoints)

```bash
# 19. Service Metering
GET /api/v1/metering/service/{service_name}?period=this_month
# service_name: llm_inference, storage, bandwidth
# period: this_month, last_month, this_quarter, last_quarter

# 20. Metering Summary
GET /api/v1/metering/summary?period=this_month
# period: this_month, last_month, this_quarter

# 21. Billing Analytics
GET /api/v1/billing/analytics/summary
```

---

## Example Usage

### Curl

```bash
# Get MRR for last 6 months
curl http://localhost:8084/api/v1/analytics/revenue/mrr?months=6

# Get user churn rate
curl http://localhost:8084/api/v1/analytics/users/churn

# Get LLM usage summary
curl http://localhost:8084/api/v1/llm/usage/summary?range=month
```

### JavaScript

```javascript
// Fetch MRR data
const response = await fetch('/api/v1/analytics/revenue/mrr?months=12');
const data = await response.json();
console.log('Current MRR:', data.current_mrr);

// Fetch user LTV
const ltv = await fetch('/api/v1/analytics/users/ltv').then(r => r.json());
console.log('Average LTV:', ltv.average_ltv);
```

### Python

```python
import requests

# Get revenue ARR
response = requests.get('http://localhost:8084/api/v1/analytics/revenue/arr')
data = response.json()
print(f"ARR: ${data['arr']}")

# Get service performance
perf = requests.get('http://localhost:8084/api/v1/analytics/services/performance').json()
for service in perf['services']:
    print(f"{service['service']}: {service['uptime']}% uptime")
```

---

## Response Format

All endpoints return JSON with this structure:

```json
{
  "data_field_1": "value",
  "data_field_2": {...},
  "calculated_at": "2025-11-26T12:34:56.789012"
}
```

**Status Codes**:
- `200` - Success
- `400` - Bad request (invalid parameters)
- `401` - Unauthorized (when auth is added)
- `500` - Server error

---

## Common Fields

- `calculated_at` - ISO 8601 timestamp of when data was generated
- `total_*` - Sum/count of items
- `*_by_tier` - Breakdown by subscription tier (trial, starter, professional, enterprise)
- `*_growth` - Percentage change (positive = growth, negative = decline)

---

## Testing

Run all tests:

```bash
bash /tmp/test_analytics_endpoints.sh
```

Test specific endpoint:

```bash
curl -s http://localhost:8084/api/v1/analytics/revenue/mrr | jq '.'
```

---

## Documentation

- **Swagger UI**: http://localhost:8084/docs
- **Full Implementation**: `ANALYTICS_METERING_IMPLEMENTATION.md`
- **Source Code**:
  - `backend/routers/analytics.py` (606 lines)
  - `backend/routers/metering.py` (345 lines)

---

## Notes

- All endpoints currently return **mock data**
- No authentication required (for now)
- Average response time: < 50ms
- All timestamps in UTC ISO 8601 format
