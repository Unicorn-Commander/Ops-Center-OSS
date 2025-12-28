# Subscription Tier Examples

## Visual Service Access by Tier

### Trial Tier (Default)
```
✅ Open-WebUI (Chat)
✅ Center-Deep Search
🔒 User Documentation      → "Upgrade to starter to unlock"
🔒 Bolt.diy                → "Upgrade to professional to unlock"
🔒 Grafana Monitoring      → "Upgrade to professional to unlock"
🔒 Portainer               → "Upgrade to professional to unlock"
🔒 Unicorn Orator          → "Upgrade to enterprise to unlock"
```

### Starter Tier
```
✅ Open-WebUI (Chat)
✅ Center-Deep Search
✅ User Documentation
🔒 Bolt.diy                → "Upgrade to professional to unlock"
🔒 Grafana Monitoring      → "Upgrade to professional to unlock"
🔒 Portainer               → "Upgrade to professional to unlock"
🔒 Unicorn Orator          → "Upgrade to enterprise to unlock"
```

### Professional Tier
```
✅ Open-WebUI (Chat)
✅ Center-Deep Search
✅ User Documentation
✅ Bolt.diy
✅ Grafana Monitoring
✅ Portainer
🔒 Unicorn Orator          → "Upgrade to enterprise to unlock"
```

### Enterprise Tier
```
✅ Open-WebUI (Chat)
✅ Center-Deep Search
✅ User Documentation
✅ Bolt.diy
✅ Grafana Monitoring
✅ Portainer
✅ Unicorn Orator
```

## User Experience Flow

### 1. Page Load (Fast, Non-blocking)
```
1. Page renders immediately with default 'trial' tier
2. Session API call happens in background
3. Services update dynamically when session returns
4. No loading spinners or blank states
```

### 2. Locked Service Interaction
```
User clicks on locked service:
├─ Click is prevented
├─ Alert shows: "Upgrade to [tier] tier or higher to access [service]"
└─ Future: Could show upgrade modal with pricing
```

### 3. Visual Feedback
```
Locked Service Card:
├─ Black overlay (40% opacity)
├─ Backdrop blur effect
├─ Large lock icon (centered)
├─ "Upgrade to unlock" text
├─ "[tier] tier required" badge
└─ 60% opacity (70% on hover)

Unlocked Service Card:
├─ Full color gradient
├─ Hover effects (scale + shadow)
├─ Arrow icon animation
└─ Clickable link to service
```

## Session API Response Examples

### Example 1: Full User Object
```json
{
  "user": {
    "id": "uuid-123",
    "email": "user@example.com",
    "name": "John Doe",
    "subscription_tier": "professional",
    "subscription_expires": "2025-11-09T00:00:00Z"
  },
  "authenticated": true
}
```

### Example 2: Minimal Response
```json
{
  "subscription_tier": "starter"
}
```

### Example 3: No Session (Unauthenticated)
```json
{
  "authenticated": false
}
```
**Result**: Defaults to `trial` tier

### Example 4: API Error
```
HTTP 500 Internal Server Error
```
**Result**: Silent fail, defaults to `trial` tier, logs to console

## Tier Pricing Example (Conceptual)

| Tier | Price/Month | Services | Key Features |
|------|-------------|----------|--------------|
| **Trial** | Free | 2 | Chat + Search |
| **Starter** | $19 | 3 | + Documentation |
| **Professional** | $49 | 6 | + Dev Tools + Monitoring |
| **Enterprise** | $99 | 7 | + Voice Synthesis + Priority Support |

## Implementation Code Examples

### Adding a New Service
```javascript
// 1. Add to services array
{
  title: 'New Service',
  description: 'Description here',
  icon: SomeIcon,
  url: `http://${currentHost}:9999`,
  color: 'from-teal-500 to-teal-700',
  textColor: 'text-teal-100'
}

// 2. Add to tier mapping
const serviceTiers = {
  ...
  'New Service': 'professional', // Set required tier
  ...
};
```

### Adding a New Tier
```javascript
// 1. Update hierarchy
const tierHierarchy = [
  'trial',
  'starter',
  'professional',
  'premium',    // NEW
  'enterprise'
];

// 2. Assign services to new tier
const serviceTiers = {
  ...
  'Advanced Analytics': 'premium', // NEW service
  ...
};
```

### Custom Lock Messages
```javascript
// Future enhancement idea:
const serviceMessages = {
  'Unicorn Orator': 'Unlock 50+ AI voices with Enterprise',
  'Bolt.diy': 'Code faster with Professional tier',
  // ...
};
```

## Browser Console Examples

### Successful Session Fetch
```
Session data received:
{
  user: { subscription_tier: "professional" }
}
```

### Failed Session Fetch
```
Session fetch failed, defaulting to trial tier
```

### Access Check Debug
```javascript
// Add to hasAccess function for debugging:
console.log(`Access check for ${serviceName}:`, {
  userTier,
  requiredTier: serviceTiers[serviceName],
  hasAccess: userTierIndex >= requiredTierIndex
});
```

## Testing Commands

### Mock Different Tiers (Browser Console)
```javascript
// Override session fetch for testing
localStorage.setItem('debug_tier', 'enterprise');

// Then refresh page - modify useEffect to check localStorage first
```

### Verify Lock Overlay
```javascript
// Check if service is locked
document.querySelectorAll('[data-locked="true"]').length

// Get locked service names
[...document.querySelectorAll('[data-locked="true"]')]
  .map(el => el.querySelector('h3').textContent)
```

## Accessibility Considerations

### Current Implementation
- ✅ Title attributes for hover tooltips
- ✅ Cursor changes for locked state
- ✅ Clear visual distinction
- ✅ Keyboard navigation supported

### Future Enhancements
- [ ] ARIA labels for screen readers
- [ ] Focus states for keyboard users
- [ ] Accessible upgrade dialogs
- [ ] High contrast mode support

## Mobile Experience

### Responsive Design
```
Mobile (< 768px):
- Single column grid
- Full-width service cards
- Lock overlay scales appropriately
- Touch-friendly clickable areas

Tablet (768px - 1024px):
- Two column grid
- Optimized card sizes
- Readable tier requirements

Desktop (> 1024px):
- Three column grid
- Hover effects
- Tooltip on hover
```

## Performance Metrics

### Expected Load Times
```
Initial Page Render:        < 100ms  (no blocking)
Session API Call:           < 300ms  (typical)
Service Card Re-render:     < 50ms   (after session)
Lock Overlay Animation:     200ms    (smooth fade)
```

### Bundle Size Impact
```
New Icons (LockClosedIcon): ~2KB
Additional State/Logic:     ~1KB
Total Impact:               ~3KB (negligible)
```

---

**Last Updated**: 2025-10-09
**Component**: PublicLanding.jsx
**Documentation Version**: 1.0
