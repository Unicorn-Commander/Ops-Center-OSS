/**
 * Web Vitals Performance Tracking
 *
 * Tracks Core Web Vitals metrics and sends them to analytics endpoint
 *
 * Metrics tracked:
 * - CLS (Cumulative Layout Shift) - Visual stability
 * - FID (First Input Delay) - Interactivity
 * - FCP (First Contentful Paint) - Loading
 * - LCP (Largest Contentful Paint) - Loading
 * - TTFB (Time to First Byte) - Server response
 * - INP (Interaction to Next Paint) - Responsiveness (new)
 */

import { onCLS, onFCP, onLCP, onTTFB, onINP } from 'web-vitals';

// Performance thresholds (Google's recommended values)
// Note: FID was replaced by INP in web-vitals v4+
export const THRESHOLDS = {
  CLS: { good: 0.1, needsImprovement: 0.25 },
  FCP: { good: 1800, needsImprovement: 3000 },
  LCP: { good: 2500, needsImprovement: 4000 },
  TTFB: { good: 800, needsImprovement: 1800 },
  INP: { good: 200, needsImprovement: 500 }
};

// Store metrics locally for dashboard display
let metricsCache = {};

/**
 * Determine rating based on metric value
 */
function getRating(name, value) {
  const threshold = THRESHOLDS[name];
  if (!threshold) return 'unknown';

  if (value <= threshold.good) return 'good';
  if (value <= threshold.needsImprovement) return 'needs-improvement';
  return 'poor';
}

/**
 * Send metric to analytics endpoint
 */
async function sendToAnalytics(metric) {
  const { name, value, id, rating } = metric;

  // Store in local cache
  metricsCache[name] = {
    name,
    value,
    id,
    rating: getRating(name, value),
    timestamp: Date.now()
  };

  // Emit custom event for local listeners
  window.dispatchEvent(new CustomEvent('webvitals', {
    detail: metricsCache[name]
  }));

  // Send to backend analytics endpoint
  try {
    const response = await fetch('/api/v1/analytics/web-vitals', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
      },
      body: JSON.stringify({
        metric_name: name,
        value: value,
        rating: getRating(name, value),
        metric_id: id,
        url: window.location.pathname,
        user_agent: navigator.userAgent,
        timestamp: new Date().toISOString()
      })
    });

    if (!response.ok) {
      console.warn('Failed to send web vitals:', response.statusText);
    }
  } catch (error) {
    // Silent fail - don't break app if analytics fails
    console.debug('Analytics endpoint unavailable:', error.message);
  }
}

/**
 * Initialize Web Vitals tracking
 */
export function reportWebVitals() {
  // Core Web Vitals (v5 metrics)
  onCLS(sendToAnalytics);  // Cumulative Layout Shift
  onLCP(sendToAnalytics);  // Largest Contentful Paint
  onINP(sendToAnalytics);  // Interaction to Next Paint (replaces FID)

  // Additional metrics
  onFCP(sendToAnalytics);   // First Contentful Paint
  onTTFB(sendToAnalytics);  // Time to First Byte

  console.log('📊 Web Vitals tracking enabled (v5)');
}

/**
 * Get current metrics (for dashboard display)
 */
export function getMetrics() {
  return metricsCache;
}

/**
 * Get metric summary with ratings
 */
export function getMetricsSummary() {
  const metrics = Object.values(metricsCache);

  const summary = {
    overall: 'good',
    metrics: metrics,
    counts: {
      good: 0,
      needsImprovement: 0,
      poor: 0
    }
  };

  metrics.forEach(metric => {
    const rating = metric.rating;
    summary.counts[rating === 'needs-improvement' ? 'needsImprovement' : rating]++;
  });

  // Overall rating is the worst individual rating
  if (summary.counts.poor > 0) {
    summary.overall = 'poor';
  } else if (summary.counts.needsImprovement > 0) {
    summary.overall = 'needs-improvement';
  }

  return summary;
}

/**
 * Performance observer for resource timing
 */
export function observeResourceTiming(callback) {
  if (!('PerformanceObserver' in window)) {
    console.warn('PerformanceObserver not supported');
    return;
  }

  try {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach(entry => {
        if (entry.initiatorType === 'fetch' || entry.initiatorType === 'xmlhttprequest') {
          callback({
            url: entry.name,
            duration: entry.duration,
            size: entry.transferSize,
            cached: entry.transferSize === 0 && entry.decodedBodySize > 0
          });
        }
      });
    });

    observer.observe({ entryTypes: ['resource'] });
  } catch (error) {
    console.warn('Failed to observe resource timing:', error);
  }
}

/**
 * Get navigation timing metrics
 */
export function getNavigationMetrics() {
  if (!window.performance || !window.performance.timing) {
    return null;
  }

  const timing = window.performance.timing;
  const navigation = {
    // Page load metrics
    domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
    domComplete: timing.domComplete - timing.navigationStart,
    loadComplete: timing.loadEventEnd - timing.navigationStart,

    // Network metrics
    dns: timing.domainLookupEnd - timing.domainLookupStart,
    tcp: timing.connectEnd - timing.connectStart,
    request: timing.responseStart - timing.requestStart,
    response: timing.responseEnd - timing.responseStart,

    // Processing metrics
    domProcessing: timing.domComplete - timing.domLoading,

    // Total time
    total: timing.loadEventEnd - timing.navigationStart
  };

  return navigation;
}

/**
 * Track bundle size and chunk loading
 */
export function trackBundleMetrics() {
  if (!window.performance) return;

  const scripts = performance.getEntriesByType('resource')
    .filter(entry => entry.initiatorType === 'script');

  const totalSize = scripts.reduce((sum, script) => sum + (script.transferSize || 0), 0);
  const totalTime = scripts.reduce((sum, script) => sum + script.duration, 0);

  return {
    scriptCount: scripts.length,
    totalSize: totalSize,
    totalTime: totalTime,
    avgSize: totalSize / scripts.length,
    avgTime: totalTime / scripts.length,
    scripts: scripts.map(s => ({
      name: s.name.split('/').pop(),
      size: s.transferSize,
      duration: s.duration,
      cached: s.transferSize === 0 && s.decodedBodySize > 0
    }))
  };
}

/**
 * Export for use in performance dashboard
 */
export default {
  reportWebVitals,
  getMetrics,
  getMetricsSummary,
  observeResourceTiming,
  getNavigationMetrics,
  trackBundleMetrics,
  THRESHOLDS
};
