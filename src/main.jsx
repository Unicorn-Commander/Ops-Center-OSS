import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import './styles/landing.css'
import './styles/mobile-responsive.css'

// Import Web Vitals tracking
import { reportWebVitals } from './utils/webVitals'

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