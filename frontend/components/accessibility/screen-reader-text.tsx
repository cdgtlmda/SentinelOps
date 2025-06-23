'use client'

import React, { useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'

interface ScreenReaderOnlyProps {
  children: React.ReactNode
  as?: keyof JSX.IntrinsicElements
  className?: string
}

/**
 * Component that renders content only visible to screen readers
 * Uses CSS to hide content visually while keeping it accessible
 */
export const ScreenReaderOnly: React.FC<ScreenReaderOnlyProps> = ({
  children,
  as: Component = 'span',
  className
}) => {
  return (
    <Component
      className={cn(
        'sr-only',
        className
      )}
    >
      {children}
    </Component>
  )
}

interface LiveRegionProps {
  children: React.ReactNode
  /**
   * How aggressively assistive technology should notify the user of updates
   * - polite: User will be notified of changes when idle
   * - assertive: User will be notified immediately
   */
  politeness?: 'polite' | 'assertive'
  /**
   * What types of changes should be announced
   * - additions: New content added
   * - removals: Content removed
   * - text: Text content changed
   * - all: All changes
   */
  relevant?: 'additions' | 'removals' | 'text' | 'all'
  /**
   * Whether the entire region should be announced when any part changes
   */
  atomic?: boolean
  className?: string
}

/**
 * Component for creating ARIA live regions that announce dynamic content changes
 * to screen reader users
 */
export const LiveRegion: React.FC<LiveRegionProps> = ({
  children,
  politeness = 'polite',
  relevant = 'additions',
  atomic = false,
  className
}) => {
  return (
    <div
      role={politeness === 'assertive' ? 'alert' : 'status'}
      aria-live={politeness}
      aria-relevant={relevant}
      aria-atomic={atomic}
      className={cn(
        'sr-only',
        className
      )}
    >
      {children}
    </div>
  )
}

interface StatusAnnouncerProps {
  message: string
  /**
   * Clear the message after this many milliseconds
   * Set to 0 to keep the message indefinitely
   */
  clearAfter?: number
  politeness?: 'polite' | 'assertive'
}

/**
 * Component for announcing status messages to screen reader users
 * Automatically clears messages after a specified duration
 */
export const StatusAnnouncer: React.FC<StatusAnnouncerProps> = ({
  message,
  clearAfter = 5000,
  politeness = 'polite'
}) => {
  const [currentMessage, setCurrentMessage] = React.useState(message)
  const timeoutRef = useRef<NodeJS.Timeout>()

  useEffect(() => {
    setCurrentMessage(message)

    if (clearAfter > 0 && message) {
      // Clear any existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }

      // Set new timeout
      timeoutRef.current = setTimeout(() => {
        setCurrentMessage('')
      }, clearAfter)
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [message, clearAfter])

  return (
    <LiveRegion politeness={politeness}>
      {currentMessage}
    </LiveRegion>
  )
}

interface ContextDescriptionProps {
  children: React.ReactNode
  id: string
  className?: string
}

/**
 * Component for providing additional context descriptions
 * that can be referenced by aria-describedby
 */
export const ContextDescription: React.FC<ContextDescriptionProps> = ({
  children,
  id,
  className
}) => {
  return (
    <div
      id={id}
      className={cn(
        'sr-only',
        className
      )}
    >
      {children}
    </div>
  )
}

interface VisuallyHiddenProps {
  children: React.ReactNode
  /**
   * Whether the content should become visible when focused
   * Useful for skip links and other keyboard navigation aids
   */
  showOnFocus?: boolean
  as?: keyof JSX.IntrinsicElements
  className?: string
}

/**
 * Component that hides content visually but keeps it accessible
 * Can optionally show content when focused for keyboard navigation
 */
export const VisuallyHidden: React.FC<VisuallyHiddenProps> = ({
  children,
  showOnFocus = false,
  as: Component = 'span',
  className
}) => {
  return (
    <Component
      className={cn(
        showOnFocus ? 'sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md' : 'sr-only',
        className
      )}
    >
      {children}
    </Component>
  )
}

// Hook for programmatically announcing messages
export const useAnnouncement = () => {
  const [announcement, setAnnouncement] = React.useState('')

  const announce = React.useCallback((message: string, politeness: 'polite' | 'assertive' = 'polite') => {
    // Clear existing announcement to ensure re-announcement of same message
    setAnnouncement('')
    
    // Use setTimeout to ensure the clear happens before the new announcement
    setTimeout(() => {
      setAnnouncement(message)
    }, 100)
  }, [])

  const clear = React.useCallback(() => {
    setAnnouncement('')
  }, [])

  return {
    announcement,
    announce,
    clear,
    Announcer: () => announcement ? <StatusAnnouncer message={announcement} /> : null
  }
}