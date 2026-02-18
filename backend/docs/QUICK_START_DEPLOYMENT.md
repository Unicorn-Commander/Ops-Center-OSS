# Quick Start: Deploy UC-Cloud Services Catalog

> **Time Required**: 10-15 minutes
> **Difficulty**: Easy
> **Prerequisites**: Docker, PostgreSQL access

---

## 🚀 5-Minute Deployment

### Step 1: Backup Database (1 minute)

```bash
cd /opt/ops-center/backend

# Backup current database
docker exec ops-center-postgres pg_dump -U unicorn_ops unicorn_ops_db > \
  backups/backup_before_catalog_$(date +%Y%m%d_%H%M%S).sql

echo "✅ Backup created"
```

### Step 2: Apply Services Catalog (2 minutes)

```bash
# Apply the new services catalog
docker exec -i ops-center-postgres psql -U unicorn_ops -d unicorn_ops_db < \
  sql/uc_cloud_services_catalog.sql

echo "✅ Services catalog deployed"
```

### Step 3: Verify Services (1 minute)

```bash
# Count services
docker exec ops-center-postgres psql -U unicorn_ops -d unicorn_ops_db -c \
  "SELECT COUNT(*) as service_count FROM add_ons;"

# List all services
docker exec ops-center-postgres psql -U unicorn_ops -d unicorn_ops_db -c \
  "SELECT name, category,
   CASE WHEN base_price = 0 THEN 'FREE' ELSE '$' || base_price || '/mo' END as price,
   CASE WHEN is_active THEN '✅' ELSE '🚧' END as status,
   CASE WHEN is_featured THEN '⭐' ELSE '' END as featured
   FROM add_ons ORDER BY sort_order;"

echo "✅ Services verified"
```

**Expected Output:**
```
 service_count
---------------
             8

            name             |    category     |   price   | status | featured
-----------------------------+-----------------+-----------+--------+----------
 Open-WebUI                  | AI & Chat       | FREE      | ✅     | ⭐
 Presenton                   | Productivity    | $19.99/mo | ✅     | ⭐
 Bolt.DIY                    | Development     | $29.99/mo | ✅     | ⭐
 Center-Deep Pro             | Search & Res... | FREE      | ✅     | ⭐
 Unicorn Brigade             | AI Agents       | $39.99/mo | ✅     | ⭐
 Unicorn Amanuensis          | Voice Services  | $14.99/mo | ✅     |
 Unicorn Orator              | Voice Services  | $14.99/mo | ✅     |
 MagicDeck                   | Productivity    | $24.99/mo | 🚧     |
```

### Step 4: Test Marketplace UI (3 minutes)

```bash
# Restart ops-center to pick up changes
docker restart ops-center-direct

# Wait 10 seconds
sleep 10

echo "✅ Ops-center restarted"
```

**Manual Testing:**
1. Navigate to: https://unicorncommander.ai/marketplace
2. Verify 8 services display
3. Check featured services (should show star/badge)
4. Click on a service to see details
5. Verify "Subscribe" buttons work (don't complete payment)

### Step 5: View Documentation (1 minute)

```bash
# View all created documentation
ls -lh /opt/ops-center/backend/docs/

echo "✅ Documentation ready"
```

**Files created:**
- `SERVICE_URLS.md` - Access URLs and authentication details
- `SERVICES_CATALOG_SUMMARY.md` - Complete implementation guide
- `PRICING_STRATEGY.md` - Revenue model and pricing optimization
- `QUICK_START_DEPLOYMENT.md` - This file

---

## ✅ Success Checklist

- [ ] Database backup created
- [ ] SQL file applied successfully
- [ ] 8 services appear in database
- [ ] Featured services marked correctly
- [ ] FREE services have $0.00 price
- [ ] Marketplace page loads
- [ ] Service details show correctly
- [ ] Subscribe buttons appear

---

## 🛠️ Troubleshooting

### Issue: SQL file fails to apply

**Solution:**
```bash
# Check PostgreSQL logs
docker logs ops-center-postgres --tail 50

# Check database connection
docker exec ops-center-postgres psql -U unicorn_ops -d unicorn_ops_db -c "SELECT version();"
```

### Issue: Services don't appear in marketplace

**Solution:**
```bash
# Check if add_ons table exists
docker exec ops-center-postgres psql -U unicorn_ops -d unicorn_ops_db -c "\dt add_ons"

# Check service count
docker exec ops-center-postgres psql -U unicorn_ops -d unicorn_ops_db -c "SELECT COUNT(*) FROM add_ons;"

# Restart backend
docker restart ops-center-direct
```

### Issue: Frontend shows old data

**Solution:**
```bash
# Clear browser cache and hard reload (Ctrl+Shift+R)
# Or restart frontend container
docker restart ops-center-frontend  # if separate container
```

---

## 🔄 Rollback (If Needed)

### Restore from Backup

```bash
# Find your backup file
ls -lt /opt/ops-center/backend/backups/

# Restore from backup (replace with actual filename)
docker exec -i ops-center-postgres psql -U unicorn_ops -d unicorn_ops_db < \
  backups/backup_before_catalog_YYYYMMDD_HHMMSS.sql

echo "✅ Database restored from backup"
```

---

## 📊 Post-Deployment Analytics

### View Service Statistics

```bash
# Service count by category
docker exec ops-center-postgres psql -U unicorn_ops -d unicorn_ops_db -c "
SELECT
    category,
    COUNT(*) as service_count,
    COUNT(*) FILTER (WHERE is_featured = TRUE) as featured_count,
    COUNT(*) FILTER (WHERE base_price = 0) as free_count,
    SUM(base_price) as total_if_all_subscribed
FROM add_ons
WHERE is_active = TRUE
GROUP BY category
ORDER BY category;"
```

### Check Metadata

```bash
# View service metadata
docker exec ops-center-postgres psql -U unicorn_ops -d unicorn_ops_db -c "
SELECT
    name,
    metadata->>'access_url' as url,
    metadata->>'sso_provider' as sso,
    metadata->>'included_in_base' as free
FROM add_ons
ORDER BY sort_order;"
```

---

## 📝 Next Steps

### Immediate (Today)
1. ✅ Deploy SQL file (completed)
2. ✅ Verify services appear (completed)
3. **Test subscription flow**:
   - Click "Subscribe" on a premium service
   - Verify payment modal opens
   - Test Stripe integration (use test card: 4242 4242 4242 4242)
   - Confirm service becomes accessible after payment

### Short-Term (This Week)
1. **Create service icons** (see SERVICES_CATALOG_SUMMARY.md for specifications)
2. **Update frontend** to display new metadata:
   - Trial period badges
   - API key generation for voice services
   - Direct links to service URLs after subscription
3. **Set up email notifications**:
   - Welcome email on subscription
   - Trial ending reminders
   - Service activation confirmation

### Medium-Term (This Month)
1. **Implement bundles**:
   - Voice Suite ($24.99)
   - Developer Kit ($59.99)
   - All-Access ($99.99)
2. **Add annual billing** with 20% discount
3. **Launch referral program**
4. **A/B test pricing page** layouts

### Long-Term (Next Quarter)
1. **Enterprise tiers** for teams (5+ users)
2. **Usage analytics dashboard** for users
3. **Geographic pricing** for international markets
4. **Launch MagicDeck** (Q1 2026)

---

## 📚 Documentation Index

| Document | Purpose | Location |
|----------|---------|----------|
| **Quick Start** | This file - fast deployment | `docs/QUICK_START_DEPLOYMENT.md` |
| **Services Catalog** | Complete implementation guide | `docs/SERVICES_CATALOG_SUMMARY.md` |
| **Service URLs** | Access and authentication details | `docs/SERVICE_URLS.md` |
| **Pricing Strategy** | Revenue model and optimization | `docs/PRICING_STRATEGY.md` |
| **SQL File** | Database schema and data | `sql/uc_cloud_services_catalog.sql` |

---

## 🎉 You're Done!

The UC-Cloud Services Catalog is now deployed and ready for users.

**What users will see:**
- 🆓 **2 FREE services** (Open-WebUI, Center-Deep) included with subscription
- 💎 **5 PREMIUM services** available for $14.99-$39.99/month
- 🚧 **1 COMING SOON** service (MagicDeck) to build anticipation
- ⭐ **Featured services** prominently displayed
- 🎁 **Trial periods** of 7-14 days for premium services

**Revenue potential:**
- Target: 15% conversion to paid services
- Average spend: $45-55/month per paid user
- Year 1 goal: $1M+ ARR

---

**Questions?** See the full documentation in `SERVICES_CATALOG_SUMMARY.md`

**Need help?** Contact: support@unicorncommander.ai

---

**Deployment Date**: _________________
**Deployed By**: _________________
**Status**: ⬜ Not Started | ⬜ In Progress | ⬜ Completed | ⬜ Verified

---

**Version**: 1.0.0
**Last Updated**: November 1, 2025
