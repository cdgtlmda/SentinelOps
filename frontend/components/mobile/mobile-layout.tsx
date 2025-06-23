'use client'

import React, { useState, useEffect, ReactNode } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { WifiOff, RotateCw } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { MobileNavigation } from './mobile-navigation'
import { PullToRefresh } from './pull-to-refresh'
import { useResponsive } from '@/hooks/use-responsive'

interface MobileLayoutProps {
  children: ReactNode
  showNavigation?: boolean
  enablePullToRefresh?: boolean
  onRefresh?: () => Promise<void>
  notifications?: number
  className?: string
}

export function MobileLayout({
  children,
  showNavigation = true,
  enablePullToRefresh = true,
  onRefresh,
  notifications = 0,
  className
}: MobileLayoutProps) {
  const [isOnline, setIsOnline] = useState(true)
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>('portrait')
  const [keyboardHeight, setKeyboardHeight] = useState(0)
  const [safeAreaInsets, setSafeAreaInsets] = useState({
    top: 0,
    bottom: 0,
    left: 0,
    right: 0
  })
  const { isMobile } = useResponsive()

  // Handle online/offline status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // Check initial state
    setIsOnline(navigator.onLine)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  // Handle orientation changes
  useEffect(() => {
    const handleOrientationChange = () => {
      const isLandscape = window.matchMedia('(orientation: landscape)').matches
      setOrientation(isLandscape ? 'landscape' : 'portrait')
    }

    handleOrientationChange()
    window.addEventListener('orientationchange', handleOrientationChange)
    window.addEventListener('resize', handleOrientationChange)

    return () => {
      window.removeEventListener('orientationchange', handleOrientationChange)
      window.removeEventListener('resize', handleOrientationChange)
    }
  }, [])

  // Handle safe area insets (for devices with notches, rounded corners, etc.)
  useEffect(() => {
    const updateSafeAreaInsets = () => {
      const root = document.documentElement
      const computedStyle = getComputedStyle(root)
      
      setSafeAreaInsets({
        top: parseInt(computedStyle.getPropertyValue('--sat') || '0'),
        bottom: parseInt(computedStyle.getPropertyValue('--sab') || '0'),
        left: parseInt(computedStyle.getPropertyValue('--sal') || '0'),
        right: parseInt(computedStyle.getPropertyValue('--sar') || '0')
      })
    }

    updateSafeAreaInsets()
    window.addEventListener('resize', updateSafeAreaInsets)

    return () => {
      window.removeEventListener('resize', updateSafeAreaInsets)
    }
  }, [])

  // Handle virtual keyboard
  useEffect(() => {
    if (!isMobile) return

    const handleViewportChange = () => {
      const visualViewport = window.visualViewport
      if (visualViewport) {
        const keyboardHeight = window.innerHeight - visualViewport.height
        setKeyboardHeight(keyboardHeight)
      }
    }

    window.visualViewport?.addEventListener('resize', handleViewportChange)
    window.visualViewport?.addEventListener('scroll', handleViewportChange)

    return () => {
      window.visualViewport?.removeEventListener('resize', handleViewportChange)
      window.visualViewport?.removeEventListener('scroll', handleViewportChange)
    }
  }, [isMobile])

  const handleRefresh = async () => {
    if (onRefresh) {
      await onRefresh()
    } else {
      // Default refresh behavior
      await new Promise(resolve => setTimeout(resolve, 1000))
      window.location.reload()
    }
  }

  const content = (
    <div
      className={cn(
        "min-h-screen bg-background",
        showNavigation && "pb-16", // Space for bottom navigation
        className
      )}
      style={{
        paddingTop: safeAreaInsets.top,
        paddingBottom: showNavigation ? 64 + safeAreaInsets.bottom : safeAreaInsets.bottom,
        paddingLeft: safeAreaInsets.left,
        paddingRight: safeAreaInsets.right,
        marginBottom: keyboardHeight
      }}
    >
      {children}
    </div>
  )

  return (
    <>
      {/* Offline Indicator */}
      <AnimatePresence>
        {!isOnline && (
          <motion.div
            initial={{ y: -100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -100, opacity: 0 }}
            className="fixed top-0 left-0 right-0 z-50 bg-destructive text-destructive-foreground"
            style={{ paddingTop: safeAreaInsets.top }}
          >
            <div className="flex items-center justify-between px-4 py-2">
              <div className="flex items-center gap-2">
                <WifiOff className="h-4 w-4" />
                <span className="text-sm font-medium">You're offline</span>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => window.location.reload()}
                className="h-7 text-destructive-foreground hover:text-destructive-foreground/80"
              >
                <RotateCw className="h-3 w-3 mr-1" />
                Retry
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content */}
      {enablePullToRefresh && isMobile ? (
        <PullToRefresh onRefresh={handleRefresh}>
          {content}
        </PullToRefresh>
      ) : (
        content
      )}

      {/* Mobile Navigation */}
      {showNavigation && isMobile && (
        <MobileNavigation notifications={notifications} />
      )}

      {/* Orientation Lock Indicator (optional) */}
      {orientation === 'landscape' && isMobile && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 bg-background/95 backdrop-blur z-[100] flex items-center justify-center"
        >
          <div className="text-center px-8">
            <RotateCw className="h-12 w-12 mx-auto mb-4 text-muted-foreground animate-pulse" />
            <h2 className="text-lg font-semibold mb-2">Rotate your device</h2>
            <p className="text-sm text-muted-foreground">
              This app works best in portrait mode
            </p>
          </div>
        </motion.div>
      )}

      <style jsx global>{`
        /* Safe area CSS variables */
        :root {
          --sat: env(safe-area-inset-top);
          --sab: env(safe-area-inset-bottom);
          --sal: env(safe-area-inset-left);
          --sar: env(safe-area-inset-right);
        }

        /* Utility classes for safe areas */
        .safe-top {
          padding-top: env(safe-area-inset-top);
        }
        
        .safe-bottom {
          padding-bottom: env(safe-area-inset-bottom);
        }
        
        .safe-left {
          padding-left: env(safe-area-inset-left);
        }
        
        .safe-right {
          padding-right: env(safe-area-inset-right);
        }

        /* Prevent overscroll on mobile */
        @media (max-width: 768px) {
          body {
            overscroll-behavior: none;
          }
        }

        /* iOS specific fixes */
        @supports (-webkit-touch-callout: none) {
          .min-h-screen {
            min-height: -webkit-fill-available;
          }
        }
      `}</style>
    </>
  )
}

export default MobileLayout