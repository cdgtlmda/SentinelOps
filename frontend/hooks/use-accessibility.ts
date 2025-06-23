'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { ariaLive } from '@/lib/accessibility/aria-live-regions'

interface AccessibilityPreferences {
  fontSize: number
  highContrast: boolean
  reducedMotion: boolean
  focusIndicator: 'default' | 'enhanced' | 'custom'
  screenReaderAnnouncements: boolean
  keyboardShortcuts: boolean
}

interface FocusTrapOptions {
  initialFocus?: string
  returnFocus?: boolean
  allowOutsideClick?: boolean
}

export function useAccessibility() {
  const [preferences, setPreferences] = useState<AccessibilityPreferences>({
    fontSize: 100,
    highContrast: false,
    reducedMotion: false,
    focusIndicator: 'default',
    screenReaderAnnouncements: true,
    keyboardShortcuts: true,
  })

  const [isScreenReaderActive, setIsScreenReaderActive] = useState(false)

  // Load preferences on mount
  useEffect(() => {
    const savedPrefs = localStorage.getItem('accessibilitySettings')
    if (savedPrefs) {
      setPreferences(JSON.parse(savedPrefs))
    }

    // Detect screen reader
    detectScreenReader()
  }, [])

  // Screen reader detection
  const detectScreenReader = () => {
    if (typeof window === 'undefined') return

    // Check for common screen reader indicators
    const indicators = [
      // NVDA
      window.navigator.userAgent.includes('NVDA'),
      // JAWS
      window.navigator.userAgent.includes('JAWS'),
      // VoiceOver (macOS/iOS)
      window.navigator.userAgent.includes('VoiceOver'),
      // Check for aria-live regions being actively used
      document.querySelectorAll('[aria-live]').length > 0,
    ]

    setIsScreenReaderActive(indicators.some(Boolean))
  }

  // Update preferences
  const updatePreference = useCallback(<K extends keyof AccessibilityPreferences>(
    key: K,
    value: AccessibilityPreferences[K]
  ) => {
    setPreferences((prev) => {
      const updated = { ...prev, [key]: value }
      localStorage.setItem('accessibilitySettings', JSON.stringify(updated))
      return updated
    })
  }, [])

  // Keyboard navigation management
  const useKeyboardNavigation = (
    containerRef: React.RefObject<HTMLElement>,
    options: {
      orientation?: 'horizontal' | 'vertical' | 'both'
      loop?: boolean
      onNavigate?: (element: HTMLElement, index: number) => void
    } = {}
  ) => {
    const { orientation = 'both', loop = true, onNavigate } = options

    useEffect(() => {
      const container = containerRef.current
      if (!container || !preferences.keyboardShortcuts) return

      const handleKeyDown = (e: KeyboardEvent) => {
        const focusableElements = container.querySelectorAll<HTMLElement>(
          'a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])'
        )
        const elements = Array.from(focusableElements)
        const currentIndex = elements.indexOf(document.activeElement as HTMLElement)

        let nextIndex = -1

        switch (e.key) {
          case 'ArrowDown':
            if (orientation === 'horizontal') return
            e.preventDefault()
            nextIndex = currentIndex + 1
            break
          case 'ArrowUp':
            if (orientation === 'horizontal') return
            e.preventDefault()
            nextIndex = currentIndex - 1
            break
          case 'ArrowRight':
            if (orientation === 'vertical') return
            e.preventDefault()
            nextIndex = currentIndex + 1
            break
          case 'ArrowLeft':
            if (orientation === 'vertical') return
            e.preventDefault()
            nextIndex = currentIndex - 1
            break
          case 'Home':
            e.preventDefault()
            nextIndex = 0
            break
          case 'End':
            e.preventDefault()
            nextIndex = elements.length - 1
            break
          default:
            return
        }

        if (loop) {
          nextIndex = (nextIndex + elements.length) % elements.length
        } else {
          nextIndex = Math.max(0, Math.min(elements.length - 1, nextIndex))
        }

        if (nextIndex >= 0 && nextIndex < elements.length) {
          elements[nextIndex].focus()
          onNavigate?.(elements[nextIndex], nextIndex)
        }
      }

      container.addEventListener('keydown', handleKeyDown)
      return () => container.removeEventListener('keydown', handleKeyDown)
    }, [containerRef, orientation, loop, onNavigate, preferences.keyboardShortcuts])
  }

  // Focus trap utility
  const useFocusTrap = (
    containerRef: React.RefObject<HTMLElement>,
    isActive: boolean,
    options: FocusTrapOptions = {}
  ) => {
    const { initialFocus, returnFocus = true, allowOutsideClick = false } = options
    const previousFocus = useRef<HTMLElement | null>(null)

    useEffect(() => {
      if (!isActive || !containerRef.current) return

      const container = containerRef.current
      previousFocus.current = document.activeElement as HTMLElement

      // Set initial focus
      if (initialFocus) {
        const initialElement = container.querySelector<HTMLElement>(initialFocus)
        initialElement?.focus()
      } else {
        const firstFocusable = container.querySelector<HTMLElement>(
          'a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])'
        )
        firstFocusable?.focus()
      }

      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key !== 'Tab') return

        const focusableElements = container.querySelectorAll<HTMLElement>(
          'a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])'
        )
        const elements = Array.from(focusableElements)
        if (elements.length === 0) return

        const firstElement = elements[0]
        const lastElement = elements[elements.length - 1]

        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault()
            lastElement.focus()
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault()
            firstElement.focus()
          }
        }
      }

      const handleOutsideClick = (e: MouseEvent) => {
        if (!allowOutsideClick && !container.contains(e.target as Node)) {
          e.preventDefault()
          e.stopPropagation()
        }
      }

      document.addEventListener('keydown', handleKeyDown)
      document.addEventListener('click', handleOutsideClick, true)

      return () => {
        document.removeEventListener('keydown', handleKeyDown)
        document.removeEventListener('click', handleOutsideClick, true)

        if (returnFocus && previousFocus.current) {
          previousFocus.current.focus()
        }
      }
    }, [isActive, containerRef, initialFocus, returnFocus, allowOutsideClick])
  }

  // ARIA attribute helpers
  const ariaHelpers = {
    describedBy: (...ids: (string | undefined)[]) => ({
      'aria-describedby': ids.filter(Boolean).join(' ') || undefined,
    }),

    labelledBy: (...ids: (string | undefined)[]) => ({
      'aria-labelledby': ids.filter(Boolean).join(' ') || undefined,
    }),

    announce: (message: string, priority?: 'polite' | 'assertive') => {
      if (preferences.screenReaderAnnouncements) {
        ariaLive.announce(message, priority)
      }
    },

    announceError: (message: string) => {
      if (preferences.screenReaderAnnouncements) {
        ariaLive.announceError(message)
      }
    },

    announceSuccess: (message: string) => {
      if (preferences.screenReaderAnnouncements) {
        ariaLive.announceSuccess(message)
      }
    },

    live: (
      ariaLive: 'polite' | 'assertive' | 'off' = 'polite',
      ariaRelevant: string = 'additions text'
    ) => ({
      'aria-live': ariaLive,
      'aria-relevant': ariaRelevant,
      'aria-atomic': 'true',
    }),

    expanded: (isExpanded: boolean) => ({
      'aria-expanded': isExpanded,
    }),

    selected: (isSelected: boolean) => ({
      'aria-selected': isSelected,
    }),

    checked: (isChecked: boolean | 'mixed') => ({
      'aria-checked': isChecked,
    }),

    disabled: (isDisabled: boolean) => ({
      'aria-disabled': isDisabled,
      disabled: isDisabled,
    }),

    required: (isRequired: boolean) => ({
      'aria-required': isRequired,
      required: isRequired,
    }),

    invalid: (isInvalid: boolean, errorId?: string) => ({
      'aria-invalid': isInvalid,
      'aria-errormessage': isInvalid ? errorId : undefined,
    }),

    controls: (id: string) => ({
      'aria-controls': id,
    }),

    owns: (...ids: string[]) => ({
      'aria-owns': ids.join(' '),
    }),

    flowTo: (id: string) => ({
      'aria-flowto': id,
    }),

    busy: (isBusy: boolean) => ({
      'aria-busy': isBusy,
    }),

    current: (current: boolean | 'page' | 'step' | 'location' | 'date' | 'time') => ({
      'aria-current': current,
    }),

    orientation: (orientation: 'horizontal' | 'vertical') => ({
      'aria-orientation': orientation,
    }),

    sort: (direction: 'ascending' | 'descending' | 'none' | 'other') => ({
      'aria-sort': direction,
    }),
  }

  // Skip link helper
  const createSkipLink = (targetId: string, text: string = 'Skip to main content') => ({
    href: `#${targetId}`,
    className: 'sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-primary text-primary-foreground px-4 py-2 rounded-md z-50',
    onClick: (e: React.MouseEvent) => {
      e.preventDefault()
      const target = document.getElementById(targetId)
      if (target) {
        target.focus()
        target.scrollIntoView()
      }
    },
    children: text,
  })

  return {
    preferences,
    updatePreference,
    isScreenReaderActive,
    useKeyboardNavigation,
    useFocusTrap,
    aria: ariaHelpers,
    createSkipLink,
  }
}