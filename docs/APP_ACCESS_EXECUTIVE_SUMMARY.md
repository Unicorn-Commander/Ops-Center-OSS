# Role-Based App Access - Executive Summary

**Project**: UC-1 Pro Operations Center
**Date**: October 9, 2025
**Status**: Design Complete - Ready for Implementation

---

## Overview

This document provides a high-level summary of the role-based app access control system design for the UC-1 Pro landing page. The system will filter which applications users can see and access based on their assigned role (admin, power_user, user, viewer) and subscription tier.

---

## Problem Statement

**Current State**:
- Landing page shows all services to all users
- Users can click on any service regardless of permissions
- No visual distinction between accessible and restricted services
- Admin dashboard link visible to all users in dropdown menu

**Issues**:
- Poor user experience (users see services they can't access)
- Security concern (admin tools visible to non-admins)
- No clear upgrade path for locked features
- Hardcoded service list difficult to maintain

---

## Proposed Solution

### Architecture Approach

**Configuration-Driven System with Backend Validation**

```
User Login → Fetch Apps API → Filter by Role/Tier → Display Cards
```

**Key Components**:
1. **Configuration File** (`apps_access.json`): Defines apps and access rules
2. **Backend Manager** (`AppAccessManager`): Enforces access control
3. **API Endpoint** (`/api/v1/apps`): Returns filtered apps
4. **Frontend Integration**: Refactored landing page

### Access Control Rules

**Role-Based Access**:
- **Admin**: Full access to all applications
- **Power User**: Advanced features + configuration tools
- **User**: Standard applications and features
- **Viewer**: Read-only access to basic features

**Subscription Tiers** (works alongside roles):
- **Trial**: Basic services (Open-WebUI, Center Deep, etc.)
- **BYOK** (Bring Your Own Key): Add search and custom keys
- **Professional**: Advanced tools (Bolt.diy, Grafana, Portainer)
- **Enterprise**: Premium features (Unicorn Orator, unlimited access)

**Combined Rules**:
- Some apps require BOTH a role AND a tier (e.g., Bolt.diy needs User role + Professional tier)
- Admin dashboard requires Admin role (tier-independent)
- Basic apps available to all roles

---

## Key Benefits

### User Experience
- **Clarity**: Users only see what they can access
- **Upgrade Paths**: Clear messaging about how to unlock features
- **No Confusion**: Locked apps show helpful prompts
- **Smooth Navigation**: No dead-end clicks

### Security
- **Defense in Depth**: 3 layers (Frontend, Backend API, Service-level)
- **Role Validation**: Backend verifies all access decisions
- **Audit Trail**: All access attempts logged
- **Principle of Least Privilege**: Default to minimal access

### Maintainability
- **Configuration-Driven**: Add apps via JSON, no code changes
- **Extensible**: Easy to add new apps and access rules
- **Version Controlled**: Configuration in Git
- **Testable**: Clear interfaces for unit testing

### Performance
- **Caching**: Multi-level caching (config, results, responses)
- **Fast API**: < 500ms response time target
- **Efficient**: O(n) complexity where n = number of apps
- **Scalable**: Stateless, can scale horizontally

---

## Access Control Matrix

| Application | Admin | Power User | User | Viewer | Tier Required |
|-------------|-------|------------|------|--------|---------------|
| Open-WebUI | ✓ | ✓ | ✓ | ✓ | Trial+ |
| Center Deep | ✓ | ✓ | ✓ | ✓ | Trial+ |
| Presenton | ✓ | ✓ | ✓ | ✓ | Trial+ |
| Bolt.diy | ✓ | ✓ | ✓ | ✗ | Professional+ |
| Grafana | ✓ | ✓ | ✗ | ✗ | Professional+ |
| Portainer | ✓ | ✓ | ✗ | ✗ | Professional+ |
| Unicorn Orator | ✓ | ✓ | ✓ | ✗ | Enterprise+ |
| **Admin Dashboard** | **✓** | **✗** | **✗** | **✗** | Any |

**Legend**: ✓ = Access granted | ✗ = Access denied

---

## Technical Architecture

### Backend Components

**1. Configuration File** (`backend/config/apps_access.json`)
- JSON file defining all applications
- Specifies access rules (roles, tiers, mode)
- Configures visibility settings
- Easy to edit without code changes

**2. Access Manager** (`backend/app_access_manager.py`)
- Python class managing access logic
- Loads and validates configuration
- Checks user access for each app
- Resolves dynamic URLs
- Implements caching (5 min TTL)

**3. API Endpoint** (`backend/server.py`)
- `GET /api/v1/apps`: Returns filtered apps for authenticated user
- Integrates with existing auth middleware
- Returns JSON with apps, user info, statistics
- Supports admin reload: `POST /api/v1/apps/reload`

### Frontend Components

**1. React Hook** (`src/hooks/useUserApps.js`)
- Custom hook to fetch apps from API
- Manages loading and error states
- Filters visible vs available apps
- Caches in component state

**2. Landing Page** (`src/pages/PublicLanding.jsx`)
- Refactored to use API instead of hardcoded services
- Removes client-side access logic
- Renders apps with loading states
- Shows lock overlay for restricted apps

**3. App Card Component** (`src/components/AppCard.jsx`)
- Individual app card rendering
- Lock overlay for unavailable apps
- Upgrade prompt interaction
- Smooth animations

---

## Implementation Timeline

### Phase 1: Backend Foundation (2-3 days)
- Create configuration file
- Implement AppAccessManager class
- Add API endpoint
- Write unit tests

### Phase 2: Frontend Integration (2-3 days)
- Create React hook
- Refactor landing page
- Update app rendering
- Add loading/error states

### Phase 3: Admin Dashboard (1 day)
- Add admin dashboard to config
- Configure admin-only access
- Update dropdown menu
- Test with all roles

### Phase 4: Testing (2-3 days)
- Unit tests (90%+ coverage)
- Integration tests
- End-to-end tests
- Performance testing

### Phase 5: Documentation & Rollout (1-2 days)
- Update documentation
- Create admin guide
- Deploy to staging
- Deploy to production

**Total Estimated Time**: 8-12 days (1.5-2 weeks)

---

## Security Model

### Defense in Depth (3 Layers)

**Layer 1: Frontend Visibility** (User Experience)
- Hide apps from UI
- Show lock overlays
- Prevent clicks on locked apps
- **Security Level**: LOW (can be bypassed)

**Layer 2: Backend API Validation** (Access Control)
- Validate JWT tokens
- Check role and tier
- Filter apps before sending
- Log all access attempts
- **Security Level**: HIGH

**Layer 3: Service-Level Authentication** (Deep Security)
- Services require Authentik SSO
- Traefik enforces auth at reverse proxy
- OAuth token validation
- Session management
- **Security Level**: VERY HIGH

**Result**: Even if user bypasses frontend, backend and services still enforce access control.

---

## Risk Assessment & Mitigation

### Technical Risks

**Risk 1**: Performance degradation with many apps
- **Mitigation**: Multi-level caching, O(n) algorithms
- **Impact**: Low

**Risk 2**: Configuration errors break landing page
- **Mitigation**: JSON schema validation, graceful fallback
- **Impact**: Medium

**Risk 3**: Access control bypass vulnerability
- **Mitigation**: Backend validation, audit logging
- **Impact**: High (but well mitigated)

### Operational Risks

**Risk 1**: Users confused by locked apps
- **Mitigation**: Clear upgrade messages, help documentation
- **Impact**: Low

**Risk 2**: Admins struggle to add new apps
- **Mitigation**: Simple JSON format, admin guide, validation
- **Impact**: Low

**Risk 3**: Rollback needed due to bugs
- **Mitigation**: Git tags, backup files, clear rollback procedure
- **Impact**: Medium (but prepared)

---

## Success Metrics

### Technical KPIs
- API response time: **< 500ms** (p95)
- Page load time: **< 2s** (full page)
- Error rate: **< 0.1%**
- Test coverage: **> 80%**

### User Experience KPIs
- Time to first interaction: **< 3s**
- User satisfaction: **> 4/5**
- Access-related support tickets: **Decrease by 50%**
- Feature discovery: **> 80%**

### Business KPIs
- Upgrade conversion rate: Track locked app interactions
- App engagement: Measure most-used apps
- User retention: Monitor return users

---

## Future Enhancements

### Phase 2 Features (Future)

**1. Admin UI for App Management**
- Web interface to add/edit apps
- No need to edit JSON manually
- Real-time preview
- Access testing tool

**2. Dynamic Service Discovery**
- Auto-detect Docker services via labels
- Health check integration
- Auto-hide unhealthy services

**3. App Usage Analytics**
- Track which apps are most used
- User journey analysis
- Access denial patterns

**4. Time-Based Access**
- Grant temporary access (trials)
- Scheduled maintenance windows
- Expiring permissions

**5. Conditional Access**
- IP/network-based restrictions
- Time-of-day restrictions
- MFA requirements
- Custom conditions

**6. App Categories & Search**
- Group apps by category
- Search functionality
- Favorites/bookmarks

---

## Cost-Benefit Analysis

### Development Cost
- **Time**: 8-12 days (1.5-2 weeks)
- **Resources**: 1 backend developer, 1 frontend developer
- **Testing**: 2-3 days included
- **Total Effort**: ~20 developer-days

### Benefits

**Immediate Benefits**:
- Better security (admin tools hidden from non-admins)
- Improved UX (users see relevant apps only)
- Clear upgrade paths (monetization opportunity)
- Easier maintenance (configuration-driven)

**Long-Term Benefits**:
- Scalable system (easy to add apps)
- Data-driven decisions (usage analytics)
- Reduced support burden (less confusion)
- Foundation for future features (admin UI, etc.)

**ROI**: High - One-time implementation, ongoing benefits

---

## Recommendations

### Priority: HIGH

**Why Implement This?**
1. **Security**: Admin dashboard currently visible to all users (high risk)
2. **User Experience**: Users confused by apps they can't access
3. **Monetization**: Clear upgrade paths increase conversion
4. **Maintainability**: Easier to add new services
5. **Foundation**: Enables future features (admin UI, analytics)

### Implementation Approach

**Recommended**: Incremental rollout
1. Implement backend first (can test via API)
2. Deploy frontend to staging
3. Test with real users
4. Deploy to production with monitoring
5. Iterate based on feedback

**Alternative**: Big bang deployment (not recommended)
- Higher risk
- Harder to debug issues
- No user feedback loop

### Next Steps

**Immediate Actions**:
1. **Review this design** with team
2. **Approve implementation** plan
3. **Assign developers** to project
4. **Create project board** with tasks
5. **Start Phase 1** (backend implementation)

**Timeline**:
- Week 1: Backend + Frontend implementation
- Week 2: Testing + Documentation
- Week 3: Staging deployment + User testing
- Week 4: Production deployment + Monitoring

---

## Related Documents

### Design Documents
- **[ROLE_BASED_APP_ACCESS_DESIGN.md](./ROLE_BASED_APP_ACCESS_DESIGN.md)** - Full architecture design (60 pages)
- **[IMPLEMENTATION_PLAN_APP_ACCESS.md](./IMPLEMENTATION_PLAN_APP_ACCESS.md)** - Detailed implementation plan
- **[APP_ACCESS_ARCHITECTURE_DIAGRAMS.md](./APP_ACCESS_ARCHITECTURE_DIAGRAMS.md)** - Visual diagrams
- **[sample_apps_access.json](./sample_apps_access.json)** - Example configuration

### Existing Documentation
- **[ROLE_MAPPING.md](/home/deploy/Production/UC-1-Pro/services/ops-center/backend/ROLE_MAPPING.md)** - Current role system
- **[AUTHENTIK_SETUP.md](/home/deploy/Production/UC-1-Pro/services/ops-center/backend/AUTHENTIK_SETUP.md)** - Authentication setup
- **[ADMIN_API_QUICK_REFERENCE.md](/home/deploy/Production/UC-1-Pro/services/ops-center/docs/ADMIN_API_QUICK_REFERENCE.md)** - API reference

---

## Questions & Feedback

### Open Questions
1. Should we run role-based and tier-based access in parallel initially?
2. Do we need admin UI for Phase 1 or can it wait?
3. What should happen if API fails (fallback to cached data?)?
4. Should we show upgrade pricing directly in lock overlay?

### Feedback Channels
- **Design Review**: Development team meeting
- **Technical Questions**: GitHub Issues
- **User Feedback**: Post-deployment survey
- **Bug Reports**: Ops-center repository

---

## Approval Checklist

- [ ] Technical architecture reviewed by backend lead
- [ ] Frontend design approved by UI/UX team
- [ ] Security model validated by security team
- [ ] Timeline approved by project manager
- [ ] Resources allocated (developers assigned)
- [ ] Budget approved (if applicable)
- [ ] Stakeholders informed

**Ready to proceed**: ⬜ Yes  ⬜ No  ⬜ Needs revision

---

## Contact Information

**Project Lead**: System Architecture Designer
**Backend Team**: ops-center backend developers
**Frontend Team**: ops-center frontend developers
**Documentation**: /docs folder in ops-center repository

---

**Document Version**: 1.0
**Status**: Final Draft
**Next Review**: After Phase 1 completion
**Approval Required**: Technical Lead, Product Owner
