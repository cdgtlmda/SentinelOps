import { useRef, useCallback, useEffect } from 'react'

export type SwipeDirection = 'left' | 'right' | 'up' | 'down'
export type GestureType = 'swipe' | 'pinch' | 'longPress' | 'tap' | 'doubleTap'

interface TouchPoint {
  x: number
  y: number
  timestamp: number
}

interface GestureHandlers {
  onSwipe?: (direction: SwipeDirection, velocity: number) => void
  onPinch?: (scale: number, center: { x: number; y: number }) => void
  onLongPress?: (position: { x: number; y: number }) => void
  onTap?: (position: { x: number; y: number }) => void
  onDoubleTap?: (position: { x: number; y: number }) => void
}

interface UseTouchGesturesOptions {
  swipeThreshold?: number
  swipeVelocityThreshold?: number
  longPressDelay?: number
  doubleTapDelay?: number
  enablePinch?: boolean
  enableSwipe?: boolean
  enableLongPress?: boolean
  enableTap?: boolean
  preventDefault?: boolean
}

export function useTouchGestures(
  elementRef: React.RefObject<HTMLElement>,
  handlers: GestureHandlers,
  options: UseTouchGesturesOptions = {}
) {
  const {
    swipeThreshold = 50,
    swipeVelocityThreshold = 0.3,
    longPressDelay = 500,
    doubleTapDelay = 300,
    enablePinch = true,
    enableSwipe = true,
    enableLongPress = true,
    enableTap = true,
    preventDefault = true
  } = options

  const touchStartRef = useRef<TouchPoint[]>([])
  const touchEndRef = useRef<TouchPoint | null>(null)
  const longPressTimerRef = useRef<NodeJS.Timeout | null>(null)
  const lastTapRef = useRef<number>(0)
  const initialPinchDistanceRef = useRef<number>(0)
  const isPinchingRef = useRef(false)

  // Calculate distance between two touch points
  const getDistance = (touch1: Touch, touch2: Touch): number => {
    const dx = touch1.clientX - touch2.clientX
    const dy = touch1.clientY - touch2.clientY
    return Math.sqrt(dx * dx + dy * dy)
  }

  // Calculate center point between two touches
  const getCenter = (touch1: Touch, touch2: Touch): { x: number; y: number } => {
    return {
      x: (touch1.clientX + touch2.clientX) / 2,
      y: (touch1.clientY + touch2.clientY) / 2
    }
  }

  // Clear long press timer
  const clearLongPressTimer = () => {
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current)
      longPressTimerRef.current = null
    }
  }

  const handleTouchStart = useCallback((e: TouchEvent) => {
    if (preventDefault) e.preventDefault()

    const touches = Array.from(e.touches)
    touchStartRef.current = touches.map(touch => ({
      x: touch.clientX,
      y: touch.clientY,
      timestamp: Date.now()
    }))

    // Handle pinch gesture start
    if (enablePinch && touches.length === 2) {
      isPinchingRef.current = true
      initialPinchDistanceRef.current = getDistance(touches[0], touches[1])
      clearLongPressTimer()
      return
    }

    // Handle long press
    if (enableLongPress && touches.length === 1) {
      const touch = touches[0]
      longPressTimerRef.current = setTimeout(() => {
        if (handlers.onLongPress) {
          handlers.onLongPress({ x: touch.clientX, y: touch.clientY })
          // Haptic feedback for long press
          if ('vibrate' in navigator) {
            navigator.vibrate(50)
          }
        }
      }, longPressDelay)
    }
  }, [preventDefault, enablePinch, enableLongPress, handlers, longPressDelay])

  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (preventDefault) e.preventDefault()

    const touches = Array.from(e.touches)

    // Handle pinch gesture
    if (enablePinch && isPinchingRef.current && touches.length === 2) {
      const currentDistance = getDistance(touches[0], touches[1])
      const scale = currentDistance / initialPinchDistanceRef.current
      const center = getCenter(touches[0], touches[1])

      if (handlers.onPinch) {
        handlers.onPinch(scale, center)
      }
    }

    // Cancel long press if finger moves
    if (touchStartRef.current.length === 1 && touches.length === 1) {
      const startPoint = touchStartRef.current[0]
      const currentPoint = touches[0]
      const distance = Math.sqrt(
        Math.pow(currentPoint.clientX - startPoint.x, 2) +
        Math.pow(currentPoint.clientY - startPoint.y, 2)
      )

      if (distance > 10) {
        clearLongPressTimer()
      }
    }
  }, [preventDefault, enablePinch, handlers])

  const handleTouchEnd = useCallback((e: TouchEvent) => {
    if (preventDefault) e.preventDefault()

    clearLongPressTimer()

    const changedTouches = Array.from(e.changedTouches)
    const remainingTouches = Array.from(e.touches)

    // Reset pinch state
    if (isPinchingRef.current && remainingTouches.length < 2) {
      isPinchingRef.current = false
      return
    }

    // Handle swipe and tap gestures
    if (touchStartRef.current.length === 1 && changedTouches.length === 1) {
      const startPoint = touchStartRef.current[0]
      const endTouch = changedTouches[0]
      const endPoint = {
        x: endTouch.clientX,
        y: endTouch.clientY,
        timestamp: Date.now()
      }

      const dx = endPoint.x - startPoint.x
      const dy = endPoint.y - startPoint.y
      const distance = Math.sqrt(dx * dx + dy * dy)
      const duration = endPoint.timestamp - startPoint.timestamp
      const velocity = distance / duration

      // Check for swipe
      if (enableSwipe && distance > swipeThreshold && velocity > swipeVelocityThreshold) {
        const absX = Math.abs(dx)
        const absY = Math.abs(dy)

        let direction: SwipeDirection
        if (absX > absY) {
          direction = dx > 0 ? 'right' : 'left'
        } else {
          direction = dy > 0 ? 'down' : 'up'
        }

        if (handlers.onSwipe) {
          handlers.onSwipe(direction, velocity)
        }
      } 
      // Check for tap
      else if (enableTap && distance < 10 && duration < 200) {
        const now = Date.now()
        const timeSinceLastTap = now - lastTapRef.current

        // Check for double tap
        if (timeSinceLastTap < doubleTapDelay) {
          if (handlers.onDoubleTap) {
            handlers.onDoubleTap({ x: endPoint.x, y: endPoint.y })
          }
          lastTapRef.current = 0
        } else {
          // Single tap
          if (handlers.onTap) {
            handlers.onTap({ x: endPoint.x, y: endPoint.y })
          }
          lastTapRef.current = now
        }
      }

      touchEndRef.current = endPoint
    }

    // Clean up if all touches ended
    if (remainingTouches.length === 0) {
      touchStartRef.current = []
      touchEndRef.current = null
    }
  }, [
    preventDefault,
    enableSwipe,
    enableTap,
    swipeThreshold,
    swipeVelocityThreshold,
    doubleTapDelay,
    handlers
  ])

  // Attach event listeners
  useEffect(() => {
    const element = elementRef.current
    if (!element) return

    element.addEventListener('touchstart', handleTouchStart, { passive: !preventDefault })
    element.addEventListener('touchmove', handleTouchMove, { passive: !preventDefault })
    element.addEventListener('touchend', handleTouchEnd, { passive: !preventDefault })

    return () => {
      element.removeEventListener('touchstart', handleTouchStart)
      element.removeEventListener('touchmove', handleTouchMove)
      element.removeEventListener('touchend', handleTouchEnd)
      clearLongPressTimer()
    }
  }, [handleTouchStart, handleTouchMove, handleTouchEnd, preventDefault])

  // Return gesture state for external use
  return {
    isPinching: isPinchingRef.current,
    touchPoints: touchStartRef.current
  }
}