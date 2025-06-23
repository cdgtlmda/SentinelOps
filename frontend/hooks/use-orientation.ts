"use client"

import { useState, useEffect, useCallback } from 'react'

interface OrientationState {
  orientation: 'portrait' | 'landscape'
  isPortrait: boolean
  isLandscape: boolean
  angle: number
  width: number
  height: number
  aspectRatio: number
}

interface UseOrientationOptions {
  onOrientationChange?: (state: OrientationState) => void
  lockOrientation?: 'portrait' | 'landscape' | 'any'
}

export function useOrientation(options: UseOrientationOptions = {}) {
  const [state, setState] = useState<OrientationState>(() => {
    if (typeof window === 'undefined') {
      return {
        orientation: 'portrait',
        isPortrait: true,
        isLandscape: false,
        angle: 0,
        width: 768,
        height: 1024,
        aspectRatio: 0.75
      }
    }

    const width = window.innerWidth
    const height = window.innerHeight
    const isLandscape = width > height

    return {
      orientation: isLandscape ? 'landscape' : 'portrait',
      isPortrait: !isLandscape,
      isLandscape,
      angle: 0,
      width,
      height,
      aspectRatio: width / height
    }
  })

  const updateOrientation = useCallback(() => {
    const width = window.innerWidth
    const height = window.innerHeight
    const isLandscape = width > height
    
    // Get angle if available
    let angle = 0
    if (window.screen?.orientation) {
      angle = window.screen.orientation.angle
    } else if (window.orientation !== undefined) {
      angle = window.orientation as number
    }

    const newState: OrientationState = {
      orientation: isLandscape ? 'landscape' : 'portrait',
      isPortrait: !isLandscape,
      isLandscape,
      angle,
      width,
      height,
      aspectRatio: width / height
    }

    setState(newState)
    options.onOrientationChange?.(newState)
  }, [options])

  // Lock orientation if requested
  useEffect(() => {
    if (!options.lockOrientation || options.lockOrientation === 'any') return

    const lockOrientation = async () => {
      if (!window.screen?.orientation?.lock) return

      try {
        await window.screen.orientation.lock(options.lockOrientation)
      } catch (error) {
        console.warn('Failed to lock orientation:', error)
      }
    }

    lockOrientation()

    return () => {
      if (window.screen?.orientation?.unlock) {
        window.screen.orientation.unlock()
      }
    }
  }, [options.lockOrientation])

  // Listen for orientation changes
  useEffect(() => {
    updateOrientation()

    // Handle resize events
    window.addEventListener('resize', updateOrientation)
    
    // Handle orientation change events
    if (window.screen?.orientation) {
      window.screen.orientation.addEventListener('change', updateOrientation)
    } else {
      window.addEventListener('orientationchange', updateOrientation)
    }

    return () => {
      window.removeEventListener('resize', updateOrientation)
      
      if (window.screen?.orientation) {
        window.screen.orientation.removeEventListener('change', updateOrientation)
      } else {
        window.removeEventListener('orientationchange', updateOrientation)
      }
    }
  }, [updateOrientation])

  return state
}

// Hook for optimal layout calculations
interface LayoutConfig {
  columns?: number
  sidebar?: boolean
  secondaryPanel?: boolean
  navigationPosition?: 'top' | 'side' | 'bottom'
}

export function useOptimalLayout(config: LayoutConfig = {}) {
  const orientation = useOrientation()
  
  const getOptimalColumns = () => {
    if (config.columns) return config.columns
    
    if (orientation.isLandscape) {
      if (orientation.width >= 1200) return 3
      if (orientation.width >= 900) return 2
      return 1
    } else {
      if (orientation.width >= 768) return 2
      return 1
    }
  }

  const getSidebarVisibility = () => {
    if (config.sidebar === undefined) {
      return orientation.isLandscape && orientation.width >= 1024
    }
    return config.sidebar
  }

  const getSecondaryPanelVisibility = () => {
    if (config.secondaryPanel === undefined) {
      return orientation.width >= 1200
    }
    return config.secondaryPanel
  }

  const getNavigationPosition = () => {
    if (config.navigationPosition) return config.navigationPosition
    
    if (orientation.isLandscape && orientation.width >= 1024) {
      return 'side'
    }
    return 'top'
  }

  const getContentPadding = () => {
    if (orientation.width >= 1024) return 24
    if (orientation.width >= 768) return 16
    return 12
  }

  return {
    ...orientation,
    columns: getOptimalColumns(),
    showSidebar: getSidebarVisibility(),
    showSecondaryPanel: getSecondaryPanelVisibility(),
    navigationPosition: getNavigationPosition(),
    contentPadding: getContentPadding(),
    isTablet: orientation.width >= 768 && orientation.width < 1024,
    isDesktop: orientation.width >= 1024,
    isMobile: orientation.width < 768
  }
}

// Hook for tracking viewport dimensions
export function useViewport() {
  const [viewport, setViewport] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
    height: typeof window !== 'undefined' ? window.innerHeight : 0,
    dpr: typeof window !== 'undefined' ? window.devicePixelRatio : 1
  })

  useEffect(() => {
    const handleResize = () => {
      setViewport({
        width: window.innerWidth,
        height: window.innerHeight,
        dpr: window.devicePixelRatio
      })
    }

    window.addEventListener('resize', handleResize)
    
    // Handle DPR changes
    const mediaQuery = window.matchMedia(`(resolution: ${window.devicePixelRatio}dppx)`)
    mediaQuery.addEventListener('change', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      mediaQuery.removeEventListener('change', handleResize)
    }
  }, [])

  return viewport
}