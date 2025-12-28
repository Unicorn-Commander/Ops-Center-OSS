# Epic 2.5 - Integration Guide for UI Lead

**Purpose**: Quick reference for integrating responsive design and dark mode into dashboard components
**Audience**: UI Lead working on DashboardPro widgets
**Prerequisites**: Basic React hooks knowledge, familiarity with Material-UI

---

## Quick Start (5 Minutes)

### 1. Import the Hooks

```javascript
// At the top of your component file
import { useResponsive } from '../hooks/useResponsive';
import { useTheme } from '../contexts/ThemeContext';
```

### 2. Use in Your Component

```javascript
const MyWidget = () => {
  const { theme } = useTheme();
  const { isMobile, getChartHeight } = useResponsive();

  return (
    <div
      style={{
        backgroundColor: theme.palette.background.paper, // Dark mode aware
        padding: isMobile ? '16px' : '24px',            // Responsive
        height: getChartHeight(),                        // Responsive
      }}
    >
      {/* Your content */}
    </div>
  );
};
```

### 3. Test It

- Open Chrome DevTools → Device Toolbar (Ctrl+Shift+M)
- Test at 375px (mobile), 768px (tablet), 1920px (desktop)
- Switch themes: Settings → Theme Switcher

---

## Responsive Design Patterns

### Pattern 1: Grid Columns

**Before** (hardcoded):
```javascript
<Grid container spacing={3}>
  <Grid item xs={12} md={6} lg={4}>
    <Widget />
  </Grid>
</Grid>
```

**After** (responsive hook):
```javascript
import { useResponsive } from '../hooks/useResponsive';

const MyComponent = () => {
  const { getGridColumns } = useResponsive();
  const columns = getGridColumns(); // 1 mobile, 2 tablet, 3+ desktop

  return (
    <Grid container spacing={3}>
      {widgets.map(widget => (
        <Grid item xs={12} sm={12/2} md={12/columns} key={widget.id}>
          <Widget {...widget} />
        </Grid>
      ))}
    </Grid>
  );
};
```

### Pattern 2: Conditional Rendering

**Before**:
```javascript
const MyComponent = () => {
  const isMobile = useMediaQuery('(max-width: 600px)'); // Duplicate code

  return (
    <div>
      {isMobile ? <MobileView /> : <DesktopView />}
    </div>
  );
};
```

**After**:
```javascript
const MyComponent = () => {
  const { isMobile, isTablet, isDesktop } = useResponsive();

  return (
    <div>
      {isMobile && <MobileView />}
      {isTablet && <TabletView />}
      {isDesktop && <DesktopView />}
    </div>
  );
};
```

### Pattern 3: Dynamic Heights

**Before**:
```javascript
<Chart height={300} /> // Fixed height
```

**After**:
```javascript
const { getChartHeight } = useResponsive();

<Chart height={getChartHeight()} /> // 200px mobile, 250px tablet, 300px desktop
```

### Pattern 4: Touch Target Sizes

**Before**:
```javascript
<Button style={{ width: 32, height: 32 }}>X</Button> // Too small for mobile!
```

**After**:
```javascript
const { getTouchTargetSize } = useResponsive();
const size = getTouchTargetSize(); // 44px mobile, 40px desktop

<Button style={{ width: size, height: size }}>X</Button>
```

---

## Dark Mode Patterns

### Pattern 1: Background Colors

**Before** (hardcoded):
```javascript
<div className="bg-gray-800">Content</div>
```

**After** (theme-aware):
```javascript
const { theme } = useTheme();

<div style={{ backgroundColor: theme.palette.background.paper }}>
  Content
</div>
```

**Available Theme Colors**:
```javascript
theme.palette.background.default  // Page background
theme.palette.background.paper    // Card background
theme.palette.text.primary        // Main text
theme.palette.text.secondary      // Muted text
theme.palette.divider             // Border colors
theme.palette.primary.main        // Primary color
theme.palette.error.main          // Error color
theme.palette.success.main        // Success color
theme.palette.warning.main        // Warning color
```

### Pattern 2: Text Colors

**Before**:
```javascript
<h1 className="text-white">Title</h1>
<p className="text-gray-400">Subtitle</p>
```

**After**:
```javascript
const { theme } = useTheme();

<h1 style={{ color: theme.palette.text.primary }}>Title</h1>
<p style={{ color: theme.palette.text.secondary }}>Subtitle</p>
```

### Pattern 3: Glassmorphism Effects

**Before**:
```javascript
<div className="backdrop-blur-lg bg-white/10">
  Glass card
</div>
```

**After** (theme-aware):
```javascript
const { theme } = useTheme();

<div
  style={{
    backdropFilter: theme.palette.mode === 'dark' ? 'blur(20px)' : 'blur(10px)',
    background: theme.palette.mode === 'dark'
      ? 'rgba(31, 41, 55, 0.8)'
      : 'rgba(255, 255, 255, 0.1)',
  }}
>
  Glass card
</div>
```

### Pattern 4: Chart Colors (Chart.js)

**Before**:
```javascript
const chartOptions = {
  plugins: {
    legend: {
      labels: { color: '#FFFFFF' } // Hardcoded white
    }
  }
};
```

**After**:
```javascript
const { theme } = useTheme();

const chartOptions = useMemo(() => ({
  plugins: {
    legend: {
      labels: {
        color: theme.palette.text.primary
      }
    }
  },
  scales: {
    x: {
      ticks: { color: theme.palette.text.secondary },
      grid: { color: theme.palette.divider }
    },
    y: {
      ticks: { color: theme.palette.text.secondary },
      grid: { color: theme.palette.divider }
    }
  }
}), [theme]);

<Chart options={chartOptions} />
```

---

## Accessibility Patterns

### Pattern 1: Color Contrast Validation

**Before**:
```javascript
const accentColor = '#9CA3AF'; // Hope it works!
```

**After**:
```javascript
import { checkColorContrast } from '../utils/a11y';

const accentColor = '#9CA3AF';
const backgroundColor = '#1F2937';

const check = checkColorContrast(accentColor, backgroundColor, false);
if (!check.passes) {
  console.warn(`Color contrast too low: ${check.ratio} (need ${check.required})`);
  // Use getAccessibleColor() to fix it
}
```

### Pattern 2: Screen Reader Announcements

**Before**:
```javascript
const handleSave = () => {
  saveData();
  alert('Data saved'); // Bad UX!
};
```

**After**:
```javascript
import { announceToScreenReader } from '../utils/a11y';

const handleSave = () => {
  saveData();
  announceToScreenReader('Data saved successfully', 'polite');
  // Screen readers will announce, no visual alert
};
```

### Pattern 3: ARIA Labels

**Before**:
```javascript
<Button onClick={handleDelete}>
  <TrashIcon />
</Button>
```

**After**:
```javascript
<Button
  onClick={handleDelete}
  aria-label="Delete this item permanently"
>
  <TrashIcon aria-hidden="true" />
</Button>
```

### Pattern 4: Focus Management (Modals)

**Before**:
```javascript
const Modal = ({ children }) => {
  return <div className="modal">{children}</div>;
};
```

**After**:
```javascript
import { trapFocus } from '../utils/a11y';
import { useRef, useEffect } from 'react';

const Modal = ({ children, isOpen }) => {
  const modalRef = useRef(null);

  useEffect(() => {
    if (isOpen && modalRef.current) {
      const cleanup = trapFocus(modalRef.current);
      return cleanup;
    }
  }, [isOpen]);

  return (
    <div ref={modalRef} className="modal" role="dialog" aria-modal="true">
      {children}
    </div>
  );
};
```

---

## Touch Gesture Patterns

### Pattern 1: Swipe to Dismiss

**Use Case**: Alert cards, notifications

```javascript
import { useTouchGestures } from '../hooks/useTouchGestures';

const AlertCard = ({ message, onDismiss }) => {
  const gestures = useTouchGestures({
    onSwipeLeft: () => onDismiss(),
  });

  return (
    <div {...gestures} className="alert-card">
      {message}
      <button onClick={onDismiss}>×</button>
    </div>
  );
};
```

### Pattern 2: Tap for Selection

**Use Case**: Card grids, image galleries

```javascript
const ServiceCard = ({ service, onSelect }) => {
  const gestures = useTouchGestures({
    onTap: () => onSelect(service),
    onLongPress: () => showContextMenu(service),
  });

  return (
    <div {...gestures} className="service-card">
      <Icon />
      <span>{service.name}</span>
    </div>
  );
};
```

### Pattern 3: Pull to Refresh

**Use Case**: Activity feeds, data lists

```javascript
const ActivityFeed = ({ onRefresh }) => {
  const [isPulling, setIsPulling] = useState(false);

  const gestures = useTouchGestures({
    onSwipeDown: (e, { distance }) => {
      if (distance > 100) {
        setIsPulling(true);
        onRefresh().finally(() => setIsPulling(false));
      }
    },
  });

  return (
    <div {...gestures}>
      {isPulling && <RefreshIndicator />}
      <ActivityList />
    </div>
  );
};
```

---

## Loading Skeleton Pattern

### Pattern 1: Lazy Load with Skeleton

**Before**:
```javascript
import DashboardPro from './DashboardPro';

<DashboardPro /> // Blank screen while loading
```

**After**:
```javascript
import { lazy, Suspense } from 'react';
import DashboardSkeleton from '../components/DashboardSkeleton';

const DashboardPro = lazy(() => import('./DashboardPro'));

<Suspense fallback={<DashboardSkeleton />}>
  <DashboardPro />
</Suspense>
```

### Pattern 2: Custom Widget Skeleton

**Create your own skeleton**:
```javascript
const WidgetSkeleton = () => {
  const { theme } = useTheme();

  return (
    <div
      style={{
        backgroundColor: theme.palette.background.paper,
        padding: '16px',
        borderRadius: '12px',
      }}
    >
      {/* Title skeleton */}
      <div
        className="animate-pulse"
        style={{
          backgroundColor: theme.palette.divider,
          height: '20px',
          width: '60%',
          borderRadius: '4px',
          marginBottom: '12px',
        }}
      />

      {/* Content skeleton */}
      <div
        className="animate-pulse"
        style={{
          backgroundColor: theme.palette.divider,
          height: '100px',
          width: '100%',
          borderRadius: '8px',
        }}
      />
    </div>
  );
};
```

---

## Performance Optimization Patterns

### Pattern 1: Debounced Resize

**Before**:
```javascript
useEffect(() => {
  const handleResize = () => {
    // Runs on every resize event (hundreds of times!)
    updateLayout();
  };

  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, []);
```

**After**:
```javascript
import { debounce } from '../utils/a11y';

useEffect(() => {
  const handleResize = debounce(() => {
    // Runs once after resize stops (250ms delay)
    updateLayout();
  }, 250);

  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, []);
```

### Pattern 2: Memoized Calculations

**Before**:
```javascript
const MyComponent = ({ data }) => {
  const processed = processData(data); // Runs on every render!

  return <Chart data={processed} />;
};
```

**After**:
```javascript
import { useMemo } from 'react';

const MyComponent = ({ data }) => {
  const processed = useMemo(() => processData(data), [data]);

  return <Chart data={processed} />;
};
```

### Pattern 3: Memoized Theme Options

**Before**:
```javascript
const MyComponent = () => {
  const { theme } = useTheme();

  const chartOptions = {
    // Recreated on every render!
    plugins: { legend: { labels: { color: theme.palette.text.primary } } }
  };

  return <Chart options={chartOptions} />;
};
```

**After**:
```javascript
import { useMemo } from 'react';

const MyComponent = () => {
  const { theme } = useTheme();

  const chartOptions = useMemo(() => ({
    plugins: { legend: { labels: { color: theme.palette.text.primary } } }
  }), [theme]);

  return <Chart options={chartOptions} />;
};
```

---

## Common Widget Templates

### Template 1: Metric Card

```javascript
import { useResponsive } from '../hooks/useResponsive';
import { useTheme } from '../contexts/ThemeContext';

const MetricCard = ({ title, value, subtitle, icon: Icon, color = 'blue' }) => {
  const { theme } = useTheme();
  const { isMobile } = useResponsive();

  return (
    <div
      style={{
        backgroundColor: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: '16px',
        padding: isMobile ? '16px' : '24px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div
          style={{
            backgroundColor: `${color}20`,
            padding: '12px',
            borderRadius: '12px',
          }}
        >
          <Icon style={{ width: '24px', height: '24px', color }} />
        </div>
      </div>

      <p style={{ color: theme.palette.text.secondary, fontSize: '14px', marginBottom: '4px' }}>
        {title}
      </p>
      <p style={{ color: theme.palette.text.primary, fontSize: isMobile ? '24px' : '32px', fontWeight: 'bold' }}>
        {value}
      </p>
      {subtitle && (
        <p style={{ color: theme.palette.text.secondary, fontSize: '12px', opacity: 0.8 }}>
          {subtitle}
        </p>
      )}
    </div>
  );
};
```

### Template 2: Chart Widget

```javascript
import { useMemo } from 'react';
import { useResponsive } from '../hooks/useResponsive';
import { useTheme } from '../contexts/ThemeContext';
import { Line } from 'react-chartjs-2';

const ChartWidget = ({ title, data }) => {
  const { theme } = useTheme();
  const { getChartHeight } = useResponsive();

  const chartOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: theme.palette.text.primary }
      }
    },
    scales: {
      x: {
        ticks: { color: theme.palette.text.secondary },
        grid: { color: theme.palette.divider }
      },
      y: {
        ticks: { color: theme.palette.text.secondary },
        grid: { color: theme.palette.divider }
      }
    }
  }), [theme]);

  return (
    <div
      style={{
        backgroundColor: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: '16px',
        padding: '24px',
      }}
    >
      <h3 style={{ color: theme.palette.text.primary, marginBottom: '16px' }}>
        {title}
      </h3>
      <div style={{ height: getChartHeight() }}>
        <Line data={data} options={chartOptions} />
      </div>
    </div>
  );
};
```

### Template 3: Service Status Card

```javascript
import { useTouchGestures } from '../hooks/useTouchGestures';
import { useTheme } from '../contexts/ThemeContext';

const ServiceStatusCard = ({ service, onSelect }) => {
  const { theme } = useTheme();

  const gestures = useTouchGestures({
    onTap: () => onSelect(service),
  });

  const statusColor = service.status === 'running'
    ? theme.palette.success.main
    : theme.palette.error.main;

  return (
    <div
      {...gestures}
      style={{
        backgroundColor: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: '12px',
        padding: '16px',
        cursor: 'pointer',
        transition: 'all 0.3s',
      }}
    >
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '32px', marginBottom: '8px' }}>
          {service.icon}
        </div>
        <p style={{ color: theme.palette.text.primary, fontSize: '14px', marginBottom: '8px' }}>
          {service.name}
        </p>
        <div
          style={{
            width: '8px',
            height: '8px',
            backgroundColor: statusColor,
            borderRadius: '50%',
            margin: '0 auto',
            animation: 'pulse 2s infinite',
          }}
        />
      </div>
    </div>
  );
};
```

---

## Testing Your Components

### 1. Responsive Testing

**Chrome DevTools**:
```
1. Open DevTools (F12)
2. Toggle Device Toolbar (Ctrl+Shift+M)
3. Test these widths:
   - 375px (iPhone SE)
   - 768px (iPad)
   - 1920px (Desktop)
4. Verify:
   - No horizontal scrolling
   - Text readable
   - Touch targets ≥ 44px
```

### 2. Dark Mode Testing

**Theme Switcher**:
```
1. Go to Settings → Theme
2. Test all 3 themes:
   - Unicorn (purple/gold)
   - Dark (dark bg, light text)
   - Light (light bg, dark text)
3. Verify:
   - Text readable in all themes
   - Colors don't clash
   - Borders visible
```

### 3. Accessibility Testing

**Lighthouse Audit**:
```
1. Open DevTools → Lighthouse
2. Select "Accessibility"
3. Run audit
4. Fix any issues (aim for 95+)
```

**Color Contrast**:
```javascript
// Test in browser console
import { checkColorContrast } from '../utils/a11y';
checkColorContrast('#E5E7EB', '#1F2937', false);
// → { ratio: '7.12', passes: true, level: 'AAA' }
```

---

## Troubleshooting

### Issue: Hook Errors

**Error**: `useResponsive must be used within a component`

**Fix**: Import from correct path
```javascript
// ❌ Wrong
import { useResponsive } from 'hooks/useResponsive';

// ✅ Correct
import { useResponsive } from '../hooks/useResponsive';
```

### Issue: Theme Not Updating

**Error**: Component doesn't re-render on theme change

**Fix**: Ensure you're using the hook correctly
```javascript
// ❌ Wrong (theme won't update)
const theme = useContext(ThemeContext);

// ✅ Correct
import { useTheme } from '../contexts/ThemeContext';
const { theme } = useTheme();
```

### Issue: Touch Gestures Not Working

**Error**: Swipe gestures not triggering

**Fix**: Apply gestures to correct element
```javascript
// ❌ Wrong
<div>
  <button {...gestures}>Swipe</button>
</div>

// ✅ Correct
<div {...gestures}>
  <button>Swipe</button>
</div>
```

### Issue: Color Contrast Failures

**Error**: Lighthouse reports low contrast

**Fix**: Use getAccessibleColor utility
```javascript
import { getAccessibleColor } from '../utils/a11y';

const textColor = getAccessibleColor('#9CA3AF', backgroundColor, false);
// Returns WCAG AA compliant color
```

---

## Quick Reference Card

### Hooks
```javascript
// Responsive
import { useResponsive } from '../hooks/useResponsive';
const { isMobile, isTablet, isDesktop, getGridColumns, getChartHeight } = useResponsive();

// Theme
import { useTheme } from '../contexts/ThemeContext';
const { theme } = useTheme();

// Touch Gestures
import { useTouchGestures } from '../hooks/useTouchGestures';
const gestures = useTouchGestures({ onSwipeLeft, onTap });
```

### Theme Colors
```javascript
theme.palette.background.default   // Page bg
theme.palette.background.paper     // Card bg
theme.palette.text.primary         // Main text
theme.palette.text.secondary       // Muted text
theme.palette.divider              // Borders
```

### Accessibility
```javascript
import { checkColorContrast, announceToScreenReader } from '../utils/a11y';
```

### Breakpoints
```
xs: 0-599px     (Mobile portrait)
sm: 600-959px   (Mobile landscape / Small tablet)
md: 960-1279px  (Tablet)
lg: 1280-1919px (Desktop)
xl: 1920px+     (Large desktop)
```

---

## Need Help?

- **Full Documentation**: `/docs/UX_LEAD_DELIVERY_REPORT.md` (18 pages)
- **Test Plan**: `/docs/EPIC_2.5_UX_TEST_PLAN.md` (28 pages)
- **Code Examples**: All functions have JSDoc comments
- **Live Examples**: See `DashboardPro.jsx` for real-world usage

---

**Happy Building!** 🚀
