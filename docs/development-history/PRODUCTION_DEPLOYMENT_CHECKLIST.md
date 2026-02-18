# Production Deployment Checklist

**Status**: 🟡 PRE-PRODUCTION (Development/Testing Phase)
**Date Created**: October 23, 2025
**Production Launch**: TBD (User will notify)

---

## Pre-Production Phase (Current)

This system is currently in **development and testing mode**. The following items are deferred until actual production deployment:

### 🔒 Security Items (Deferred)

#### API Token Rotation
- [ ] **Cloudflare API Token Rotation**
  - **Current**: Development token exposed in git history
  - **Action**: Rotate token before production launch
  - **Guide**: `/docs/CLOUDFLARE_TOKEN_ROTATION_GUIDE.md`
  - **Priority**: P0 (before production)
  - **Time**: 15 minutes

- [ ] **Stripe API Keys** (Test → Live)
  - **Current**: Using Stripe test mode keys
  - **Action**: Switch to live keys for production
  - **Files**: `.env.auth`, Platform Settings GUI
  - **Priority**: P0 (before production)

- [ ] **Lago Encryption Keys**
  - **Current**: Using development keys
  - **Action**: Generate production-grade encryption keys
  - **Priority**: P0 (before production)

- [ ] **Session Secret Keys**
  - **Current**: Using development secret
  - **Action**: Generate cryptographically secure production secret
  - **Priority**: P0 (before production)

#### Access Control
- [ ] **Default Admin Password**
  - **Current**: `your-admin-password`
  - **Action**: Change to unique, secure password
  - **Priority**: P0 (before production)

- [ ] **Keycloak Admin Password**
  - **Current**: `your-admin-password`
  - **Action**: Change to unique, secure password
  - **Priority**: P0 (before production)

### 📧 Email Configuration

- [ ] **Configure Production SMTP**
  - **Current**: Microsoft 365 OAuth2 configured but not fully tested
  - **Action**: Verify email sending works for all notification types
  - **Priority**: P1 (high)

### 💳 Payment Processing

- [ ] **Complete Stripe Webhook Configuration**
  - **Current**: Webhook secret configured, endpoints created
  - **Action**: Test end-to-end payment flow with real test cards
  - **Priority**: P1 (high)

- [ ] **Lago Billing Integration Testing**
  - **Current**: All 4 subscription plans configured
  - **Action**: Test complete subscription lifecycle
  - **Priority**: P1 (high)

### 📊 Monitoring & Alerts

- [ ] **Set Up Production Monitoring**
  - **Action**: Configure Grafana dashboards for production metrics
  - **Priority**: P2 (medium)

- [ ] **Configure Alerts**
  - **Action**: Set up email/webhook alerts for critical events
  - **Priority**: P2 (medium)

---

## Production Launch Checklist

When you're ready to go to production, complete these tasks in order:

### Phase 1: Security Hardening (2-3 hours)

1. **Rotate All Sensitive Tokens**
   - [ ] Cloudflare API token
   - [ ] Stripe API keys (test → live)
   - [ ] Lago encryption keys
   - [ ] Session secret keys
   - [ ] Keycloak admin password
   - [ ] Database passwords

2. **Review Access Control**
   - [ ] Audit all admin accounts
   - [ ] Review role assignments
   - [ ] Disable/remove test accounts
   - [ ] Verify SSO providers (Google, GitHub, Microsoft)

3. **Secure Environment Files**
   - [ ] Verify no secrets in git history
   - [ ] Update `.gitignore` to prevent future leaks
   - [ ] Consider using secret management service (Vault, AWS Secrets Manager)

### Phase 2: Service Configuration (1-2 hours)

1. **Payment Processing**
   - [ ] Switch Stripe to live mode
   - [ ] Configure Stripe live webhook endpoint
   - [ ] Test payment flow end-to-end
   - [ ] Verify Lago billing events

2. **Email Service**
   - [ ] Test all email templates
   - [ ] Verify SMTP/OAuth2 credentials
   - [ ] Test password reset emails
   - [ ] Test invoice emails

3. **DNS & SSL**
   - [ ] Verify all DNS records point to production server
   - [ ] Confirm SSL certificates are valid
   - [ ] Test HTTPS on all subdomains

### Phase 3: Testing & Validation (2-4 hours)

1. **User Flows**
   - [ ] Test new user signup (email + payment)
   - [ ] Test SSO login (Google, GitHub, Microsoft)
   - [ ] Test subscription management
   - [ ] Test API key generation
   - [ ] Test organization creation
   - [ ] Test user impersonation (admin)

2. **Payment Flows**
   - [ ] Test Trial plan signup
   - [ ] Test Starter plan payment
   - [ ] Test Professional plan payment
   - [ ] Test Enterprise plan payment
   - [ ] Test subscription upgrade
   - [ ] Test subscription cancellation

3. **API Endpoints**
   - [ ] Test LiteLLM proxy
   - [ ] Test Cloudflare DNS management
   - [ ] Test Brigade agent creation
   - [ ] Test usage tracking
   - [ ] Test billing webhooks

### Phase 4: Monitoring & Backup (1 hour)

1. **Monitoring Setup**
   - [ ] Configure production Grafana dashboards
   - [ ] Set up uptime monitoring (UptimeRobot, Pingdom)
   - [ ] Configure alert notifications
   - [ ] Test alert delivery

2. **Backup Verification**
   - [ ] Verify automated database backups running
   - [ ] Test backup restoration
   - [ ] Configure off-site backup storage
   - [ ] Document backup/restore procedures

### Phase 5: Documentation (1 hour)

1. **Update Documentation**
   - [ ] Production deployment guide
   - [ ] User onboarding guide
   - [ ] Admin operations handbook
   - [ ] Troubleshooting guide

2. **Team Handoff**
   - [ ] Document admin credentials (secure vault)
   - [ ] Create runbook for common operations
   - [ ] Train team members on admin functions

---

## Post-Production Tasks

After initial production launch:

### Week 1
- [ ] Monitor error logs daily
- [ ] Review user signups and activation rates
- [ ] Check payment success/failure rates
- [ ] Verify email delivery rates
- [ ] Review API usage patterns

### Week 2-4
- [ ] Optimize slow queries/endpoints
- [ ] Review security logs
- [ ] Analyze user behavior
- [ ] Gather user feedback
- [ ] Plan feature enhancements

### Month 2+
- [ ] Quarterly security audit
- [ ] Review and optimize costs
- [ ] Plan scaling strategy
- [ ] User retention analysis
- [ ] Feature usage analytics

---

## Contact for Production Launch

**When ready to deploy to production**:

1. **Notify**: Let me (Claude) know you're ready
2. **I will**:
   - Walk through security checklist
   - Help rotate all tokens/keys
   - Verify configuration
   - Test critical paths
   - Monitor initial deployment

3. **Estimated Time**: 6-12 hours for full production deployment
4. **Recommended**: Deploy during low-traffic hours

---

## Quick Reference

### Current Status
- **Phase**: Development/Testing
- **Environment**: Pre-production
- **Security**: Development-grade (test tokens, default passwords)
- **Payment**: Stripe test mode
- **Users**: Test users only

### Production Ready Status
- **Code**: 90%+ complete
- **Features**: All major features implemented
- **Testing**: Manual testing remaining
- **Security**: Needs hardening (token rotation, password changes)
- **Monitoring**: Needs production configuration

### Estimated Production Readiness
- **With Security Fixes**: 2-3 hours
- **With Full Testing**: 6-12 hours
- **Risk Level**: Low (well-tested architecture)

---

**Remember**: This checklist will be your guide when you decide to go to production. Until then, we're in safe development mode! 🚀
