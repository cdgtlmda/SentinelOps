'use client'

import { useEffect } from 'react'
import { registerServiceWorker } from '@/lib/register-service-worker'
import { loadPolyfills } from '@/lib/polyfills/browser-polyfills'

export function ClientInit() {
  useEffect(() => {
    // Load browser polyfills for cross-browser compatibility
    loadPolyfills()
    
    // Register service worker for PWA functionality
    registerServiceWorker()
  }, [])

  return null
}