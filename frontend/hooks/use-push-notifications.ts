/**
 * Hook for managing push notifications
 */

import { useState, useEffect, useCallback } from 'react'
import { pushManager } from '@/lib/notifications/push-manager'
import { useToast } from '@/hooks/use-toast'

interface UsePushNotificationsReturn {
  isSupported: boolean
  permission: NotificationPermission
  isSubscribed: boolean
  isLoading: boolean
  error: string | null
  requestPermission: () => Promise<void>
  subscribe: () => Promise<void>
  unsubscribe: () => Promise<void>
  showNotification: (title: string, options?: NotificationOptions) => Promise<void>
  updateBadgeCount: (count: number) => Promise<void>
}

export function usePushNotifications(): UsePushNotificationsReturn {
  const [isSupported, setIsSupported] = useState(false)
  const [permission, setPermission] = useState<NotificationPermission>('default')
  const [isSubscribed, setIsSubscribed] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  // Initialize push manager and check status
  useEffect(() => {
    const checkStatus = async () => {
      try {
        setIsLoading(true)
        await pushManager.initialize()
        const status = await pushManager.getSubscriptionStatus()
        
        setIsSupported(status.isSupported)
        setPermission(status.permission)
        setIsSubscribed(status.isSubscribed)
        setError(null)
      } catch (err) {
        console.error('Failed to check push notification status:', err)
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setIsLoading(false)
      }
    }

    checkStatus()
  }, [])

  // Request notification permission
  const requestPermission = useCallback(async () => {
    try {
      setIsLoading(true)
      const newPermission = await pushManager.requestPermission()
      setPermission(newPermission)
      
      if (newPermission === 'granted') {
        toast({
          title: 'Notifications enabled',
          description: 'You will now receive push notifications',
        })
      } else if (newPermission === 'denied') {
        toast({
          title: 'Notifications blocked',
          description: 'Please enable notifications in your browser settings',
          variant: 'destructive',
        })
      }
    } catch (err) {
      console.error('Failed to request permission:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
      toast({
        title: 'Error',
        description: 'Failed to request notification permission',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }, [toast])

  // Subscribe to push notifications
  const subscribe = useCallback(async () => {
    try {
      setIsLoading(true)
      await pushManager.subscribe()
      setIsSubscribed(true)
      
      toast({
        title: 'Subscribed successfully',
        description: 'You are now subscribed to push notifications',
      })
    } catch (err) {
      console.error('Failed to subscribe:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
      toast({
        title: 'Subscription failed',
        description: err instanceof Error ? err.message : 'Failed to subscribe',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }, [toast])

  // Unsubscribe from push notifications
  const unsubscribe = useCallback(async () => {
    try {
      setIsLoading(true)
      await pushManager.unsubscribe()
      setIsSubscribed(false)
      
      toast({
        title: 'Unsubscribed',
        description: 'You will no longer receive push notifications',
      })
    } catch (err) {
      console.error('Failed to unsubscribe:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
      toast({
        title: 'Error',
        description: 'Failed to unsubscribe from notifications',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }, [toast])

  // Show a local notification
  const showNotification = useCallback(async (title: string, options?: NotificationOptions) => {
    try {
      await pushManager.showNotification(title, options)
    } catch (err) {
      console.error('Failed to show notification:', err)
      // Fallback to in-app toast if push notification fails
      toast({
        title,
        description: options?.body,
      })
    }
  }, [toast])

  // Update badge count
  const updateBadgeCount = useCallback(async (count: number) => {
    try {
      await pushManager.updateBadgeCount(count)
    } catch (err) {
      console.error('Failed to update badge count:', err)
    }
  }, [])

  // Listen for permission changes
  useEffect(() => {
    if (!isSupported) return

    const checkPermission = () => {
      if ('Notification' in window) {
        setPermission(Notification.permission)
      }
    }

    // Check permission on focus
    window.addEventListener('focus', checkPermission)
    
    // Some browsers support permission change events
    if ('permissions' in navigator) {
      navigator.permissions.query({ name: 'notifications' as PermissionName })
        .then(permissionStatus => {
          permissionStatus.onchange = () => {
            setPermission(Notification.permission)
          }
        })
        .catch(console.error)
    }

    return () => {
      window.removeEventListener('focus', checkPermission)
    }
  }, [isSupported])

  return {
    isSupported,
    permission,
    isSubscribed,
    isLoading,
    error,
    requestPermission,
    subscribe,
    unsubscribe,
    showNotification,
    updateBadgeCount,
  }
}