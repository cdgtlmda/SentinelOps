import { useCallback, useRef } from 'react'

/**
 * Hook that debounces a callback function.
 * The callback will only be called after the specified delay has passed
 * since the last invocation.
 * 
 * @param callback - The function to debounce
 * @param delay - The delay in milliseconds
 * @returns The debounced function
 */
export function useDebouncedCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const timeout = useRef<NodeJS.Timeout>()

  const debouncedCallback = useCallback(
    ((...args: Parameters<T>) => {
      clearTimeout(timeout.current)
      timeout.current = setTimeout(() => {
        callback(...args)
      }, delay)
    }) as T,
    [callback, delay]
  )

  return debouncedCallback
}

/**
 * Hook that debounces a callback function with immediate execution option.
 * 
 * @param callback - The function to debounce
 * @param delay - The delay in milliseconds
 * @param immediate - Whether to execute on the leading edge instead of trailing
 * @returns The debounced function
 */
export function useDebouncedCallbackWithImmediate<T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  immediate: boolean = false
): T {
  const timeout = useRef<NodeJS.Timeout>()
  const callNow = useRef(immediate)

  const debouncedCallback = useCallback(
    ((...args: Parameters<T>) => {
      const later = () => {
        timeout.current = undefined
        if (!immediate) callback(...args)
      }

      const shouldCallNow = immediate && !timeout.current
      clearTimeout(timeout.current)
      timeout.current = setTimeout(later, delay)

      if (shouldCallNow) {
        callback(...args)
      }
    }) as T,
    [callback, delay, immediate]
  )

  return debouncedCallback
}