"use client"

import { useEffect } from 'react'

export function PerformanceMonitor() {
  useEffect(() => {
    // Only run in production and if Performance API is available
    if (typeof window === 'undefined' || !window.performance || process.env.NODE_ENV !== 'production') {
      return
    }

    const measurePerformance = () => {
      try {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
        
        if (navigation) {
          // Calculate key metrics
          const metrics = {
            // Time to first byte
            ttfb: navigation.responseStart - navigation.requestStart,
            // DOM Content Loaded
            dcl: navigation.domContentLoadedEventEnd - navigation.fetchStart,
            // Load Complete
            loadComplete: navigation.loadEventEnd - navigation.fetchStart,
            // First Contentful Paint
            fcp: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
            // Largest Contentful Paint
            lcp: 0
          }

          // Get LCP from PerformanceObserver
          const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries()
            const lastEntry = entries[entries.length - 1]
            metrics.lcp = lastEntry.startTime
            
            // Log performance metrics
            console.log('🚀 Performance Metrics:', {
              'Time to First Byte': `${metrics.ttfb.toFixed(0)}ms`,
              'First Contentful Paint': `${metrics.fcp.toFixed(0)}ms`,
              'DOM Content Loaded': `${metrics.dcl.toFixed(0)}ms`,
              'Largest Contentful Paint': `${metrics.lcp.toFixed(0)}ms`,
              'Total Load Time': `${metrics.loadComplete.toFixed(0)}ms`,
              'Load Time Target': metrics.loadComplete < 3000 ? '✅ PASS' : '❌ FAIL'
            })

            // Send to analytics if needed
            if (window.gtag) {
              window.gtag('event', 'page_load_time', {
                value: Math.round(metrics.loadComplete),
                metric_ttfb: Math.round(metrics.ttfb),
                metric_fcp: Math.round(metrics.fcp),
                metric_lcp: Math.round(metrics.lcp),
                metric_dcl: Math.round(metrics.dcl)
              })
            }

            observer.disconnect()
          })

          observer.observe({ type: 'largest-contentful-paint', buffered: true })

          // Fallback if LCP observer doesn't fire
          setTimeout(() => {
            if (metrics.lcp === 0) {
              console.log('🚀 Performance Metrics (without LCP):', {
                'Time to First Byte': `${metrics.ttfb.toFixed(0)}ms`,
                'First Contentful Paint': `${metrics.fcp.toFixed(0)}ms`,
                'DOM Content Loaded': `${metrics.dcl.toFixed(0)}ms`,
                'Total Load Time': `${metrics.loadComplete.toFixed(0)}ms`,
                'Load Time Target': metrics.loadComplete < 3000 ? '✅ PASS' : '❌ FAIL'
              })
            }
          }, 5000)
        }
      } catch (error) {
        console.error('Performance monitoring error:', error)
      }
    }

    // Wait for page load to complete
    if (document.readyState === 'complete') {
      measurePerformance()
    } else {
      window.addEventListener('load', measurePerformance)
      return () => window.removeEventListener('load', measurePerformance)
    }
  }, [])

  return null
}

// Type declaration for gtag
declare global {
  interface Window {
    gtag?: (...args: any[]) => void
  }
}