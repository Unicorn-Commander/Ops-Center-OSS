import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import './styles/landing.css'
import './styles/mobile-responsive.css'
import './styles/design-system.css'  // world-class design layer (loaded last)

// Import Web Vitals tracking
import { reportWebVitals } from './utils/webVitals'

// Import suite analytics (Umami pageviews + PostHog product analytics).
// Self-gates on PROD + key presence — a no-op in dev and when keys are unset.
import { initAnalytics } from './utils/analytics'

// Hide loading splash screen
const splash = document.getElementById('loading-splash');
if (splash) {
  splash.style.display = 'none';
}

// Render app
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

// Initialize performance tracking
reportWebVitals();

// Initialize analytics (Umami + PostHog). No-op in dev / when keys unset.
initAnalytics();