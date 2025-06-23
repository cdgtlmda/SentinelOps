'use client'

import React, { useState, useRef, useCallback, ReactNode } from 'react'
import { motion, useMotionValue, useTransform, AnimatePresence } from 'framer-motion'
import { RefreshCw, CheckCircle, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface PullToRefreshProps {
  children: ReactNode
  onRefresh: () => Promise<void>
  threshold?: number
  maxPullDistance?: number
  refreshTimeout?: number
  successMessage?: string
  errorMessage?: string
  className?: string
}

type RefreshState = 'idle' | 'pulling' | 'releasing' | 'refreshing' | 'success' | 'error'

export function PullToRefresh({
  children,
  onRefresh,
  threshold = 80,
  maxPullDistance = 150,
  refreshTimeout = 10000,
  successMessage = 'Updated successfully',
  errorMessage = 'Failed to update',
  className
}: PullToRefreshProps) {
  const [state, setState] = useState<RefreshState>('idle')
  const [isEnabled, setIsEnabled] = useState(true)
  const containerRef = useRef<HTMLDivElement>(null)
  const startY = useRef<number>(0)
  const currentY = useRef<number>(0)
  
  const y = useMotionValue(0)
  const rotation = useTransform(y, [0, threshold], [0, 180])
  const scale = useTransform(y, [0, threshold], [0.8, 1])
  const opacity = useTransform(y, [0, threshold * 0.5], [0, 1])

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (!isEnabled || state !== 'idle') return
    
    const touch = e.touches[0]
    startY.current = touch.clientY
    
    // Only enable pull-to-refresh if we're at the top of the scrollable area
    const scrollTop = containerRef.current?.scrollTop || 0
    if (scrollTop === 0) {
      setState('pulling')
    }
  }, [isEnabled, state])

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (state !== 'pulling' && state !== 'releasing') return
    
    const touch = e.touches[0]
    currentY.current = touch.clientY
    const distance = Math.max(0, currentY.current - startY.current)
    const pullDistance = Math.min(distance * 0.5, maxPullDistance)
    
    y.set(pullDistance)
    
    if (pullDistance >= threshold && state === 'pulling') {
      setState('releasing')
      // Haptic feedback on threshold reached (if supported)
      if ('vibrate' in navigator) {
        navigator.vibrate(10)
      }
    } else if (pullDistance < threshold && state === 'releasing') {
      setState('pulling')
    }
  }, [state, threshold, maxPullDistance, y])

  const handleTouchEnd = useCallback(async () => {
    if (state === 'releasing') {
      setState('refreshing')
      y.set(threshold)
      
      try {
        // Set a timeout for the refresh operation
        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => reject(new Error('Refresh timeout')), refreshTimeout)
        })
        
        await Promise.race([onRefresh(), timeoutPromise])
        
        setState('success')
        setTimeout(() => {
          setState('idle')
          y.set(0)
          setIsEnabled(true)
        }, 1500)
      } catch (error) {
        setState('error')
        setTimeout(() => {
          setState('idle')
          y.set(0)
          setIsEnabled(true)
        }, 1500)
      }
    } else {
      setState('idle')
      y.set(0)
    }
  }, [state, threshold, onRefresh, refreshTimeout, y])

  const getIndicatorIcon = () => {
    switch (state) {
      case 'success':
        return <CheckCircle className="h-6 w-6 text-green-600" />
      case 'error':
        return <XCircle className="h-6 w-6 text-red-600" />
      default:
        return (
          <motion.div
            style={{ rotate: rotation }}
            className={cn(
              "transition-colors duration-200",
              state === 'releasing' ? "text-primary" : "text-muted-foreground"
            )}
          >
            <RefreshCw className="h-6 w-6" />
          </motion.div>
        )
    }
  }

  const getMessage = () => {
    switch (state) {
      case 'pulling':
        return 'Pull to refresh'
      case 'releasing':
        return 'Release to refresh'
      case 'refreshing':
        return 'Refreshing...'
      case 'success':
        return successMessage
      case 'error':
        return errorMessage
      default:
        return ''
    }
  }

  return (
    <div className={cn("relative overflow-hidden", className)}>
      {/* Pull Indicator */}
      <motion.div
        style={{ y, opacity }}
        className="absolute top-0 left-0 right-0 flex flex-col items-center justify-center pointer-events-none z-10"
      >
        <motion.div
          style={{ scale }}
          className={cn(
            "flex flex-col items-center justify-center p-4 rounded-full",
            "bg-background shadow-lg border border-border",
            "transition-all duration-200"
          )}
        >
          <AnimatePresence mode="wait">
            <motion.div
              key={state}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              {getIndicatorIcon()}
            </motion.div>
          </AnimatePresence>
          
          <motion.p
            className="text-xs text-muted-foreground mt-2 font-medium"
            initial={{ opacity: 0 }}
            animate={{ opacity: state !== 'idle' ? 1 : 0 }}
          >
            {getMessage()}
          </motion.p>
        </motion.div>
      </motion.div>

      {/* Content */}
      <motion.div
        ref={containerRef}
        style={{ y }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        className={cn(
          "relative",
          state === 'refreshing' && "pointer-events-none"
        )}
      >
        {children}
      </motion.div>

      {/* Loading overlay */}
      <AnimatePresence>
        {state === 'refreshing' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-background/50 backdrop-blur-sm z-20 pointer-events-none"
          />
        )}
      </AnimatePresence>
    </div>
  )
}

export default PullToRefresh