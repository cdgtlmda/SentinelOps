import { useCallback, useRef } from 'react'

/**
 * Hook that limits the rate at which a function can be called.
 * The function will be called at most once per specified delay period.
 * 
 * @param callback - The function to throttle
 * @param delay - The minimum delay between calls in milliseconds
 * @returns The throttled function
 */
export function useThrottle<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const lastRun = useRef(Date.now())
  const timeout = useRef<NodeJS.Timeout>()

  return useCallback(
    ((...args: Parameters<T>) => {
      const now = Date.now()
      const timeSinceLastRun = now - lastRun.current

      if (timeSinceLastRun >= delay) {
        lastRun.current = now
        return callback(...args)
      } else {
        clearTimeout(timeout.current)
        timeout.current = setTimeout(() => {
          lastRun.current = Date.now()
          callback(...args)
        }, delay - timeSinceLastRun)
      }
    }) as T,
    [callback, delay]
  )
}