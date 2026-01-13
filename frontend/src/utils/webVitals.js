// Web Vitals - Core Web Vitals monitoring for performance optimization
// Tracks: LCP (Largest Contentful Paint), FID (First Input Delay), CLS (Cumulative Layout Shift)
// INP (Interaction to Next Paint), FCP (First Contentful Paint), TTFB (Time to First Byte)

import { onCLS, onFCP, onINP, onLCP, onTTFB } from 'web-vitals';

// Send metrics to Google Analytics 4
const sendToAnalytics = (metric) => {
  // Log to console in development
  if (process.env.NODE_ENV === 'development') {
    console.log(`[Web Vitals] ${metric.name}:`, metric.value.toFixed(2), metric.rating);
  }

  // Send to GA4 if available
  if (typeof window.gtag === 'function') {
    window.gtag('event', metric.name, {
      event_category: 'Web Vitals',
      event_label: metric.id,
      value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
      metric_rating: metric.rating,
      non_interaction: true,
    });
  }
};

// Initialize Web Vitals tracking
export const initWebVitals = () => {
  // Core Web Vitals
  onLCP(sendToAnalytics);  // Largest Contentful Paint - loading performance
  onINP(sendToAnalytics);  // Interaction to Next Paint - interactivity
  onCLS(sendToAnalytics);  // Cumulative Layout Shift - visual stability
  
  // Additional metrics
  onFCP(sendToAnalytics);  // First Contentful Paint - initial render
  onTTFB(sendToAnalytics); // Time to First Byte - server response
};

// Get performance summary for debugging
export const getPerformanceSummary = () => {
  if (typeof window === 'undefined' || !window.performance) return null;
  
  const navigation = performance.getEntriesByType('navigation')[0];
  if (!navigation) return null;
  
  return {
    // Page load metrics
    domContentLoaded: navigation.domContentLoadedEventEnd - navigation.startTime,
    loadComplete: navigation.loadEventEnd - navigation.startTime,
    
    // Network metrics
    dns: navigation.domainLookupEnd - navigation.domainLookupStart,
    tcp: navigation.connectEnd - navigation.connectStart,
    ttfb: navigation.responseStart - navigation.requestStart,
    
    // Resource metrics
    resourceCount: performance.getEntriesByType('resource').length,
    totalTransferSize: performance.getEntriesByType('resource')
      .reduce((total, entry) => total + (entry.transferSize || 0), 0),
  };
};

export default initWebVitals;
