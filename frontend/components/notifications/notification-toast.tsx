/**
 * Notification Toast Component
 * In-app toast notifications with queue management and actions
 */

import React, { useEffect, useState } from 'react'
import { X, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

export interface ToastNotification {
  id: string
  title: string
  description?: string
  type?: 'success' | 'error' | 'warning' | 'info'
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
  onDismiss?: () => void
}

interface NotificationToastProps {
  notification: ToastNotification
  onDismiss: (id: string) => void
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left'
}

export function NotificationToast({ 
  notification, 
  onDismiss,
  position = 'top-right' 
}: NotificationToastProps) {
  const [isVisible, setIsVisible] = useState(true)
  const [timeLeft, setTimeLeft] = useState(notification.duration || 5000)
  const [isPaused, setIsPaused] = useState(false)

  useEffect(() => {
    if (!isPaused && notification.duration && notification.duration > 0) {
      const interval = setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 100) {
            handleDismiss()
            return 0
          }
          return prev - 100
        })
      }, 100)

      return () => clearInterval(interval)
    }
  }, [isPaused, notification.duration])

  const handleDismiss = () => {
    setIsVisible(false)
    setTimeout(() => {
      onDismiss(notification.id)
      notification.onDismiss?.()
    }, 200)
  }

  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />
      case 'info':
      default:
        return <Info className="h-5 w-5 text-blue-500" />
    }
  }

  const getProgressColor = () => {
    switch (notification.type) {
      case 'success': return 'bg-green-500'
      case 'error': return 'bg-red-500'
      case 'warning': return 'bg-yellow-500'
      case 'info':
      default: return 'bg-blue-500'
    }
  }

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: position.includes('top') ? -20 : 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.2 }}
          onMouseEnter={() => setIsPaused(true)}
          onMouseLeave={() => setIsPaused(false)}
          className={cn(
            "relative w-full max-w-sm bg-background border rounded-lg shadow-lg overflow-hidden",
            "pointer-events-auto"
          )}
        >
          <div className="p-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0">
                {getIcon()}
              </div>
              
              <div className="flex-1 pt-0.5">
                <h3 className="text-sm font-medium">{notification.title}</h3>
                {notification.description && (
                  <p className="mt-1 text-sm text-muted-foreground">
                    {notification.description}
                  </p>
                )}
                
                {notification.action && (
                  <Button
                    variant="link"
                    size="sm"
                    className="mt-2 h-auto p-0"
                    onClick={() => {
                      notification.action!.onClick()
                      handleDismiss()
                    }}
                  >
                    {notification.action.label}
                  </Button>
                )}
              </div>
              
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 flex-shrink-0"
                onClick={handleDismiss}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
          
          {notification.duration && notification.duration > 0 && (
            <div className="h-1 bg-muted">
              <div
                className={cn(
                  "h-full transition-all duration-100",
                  getProgressColor()
                )}
                style={{
                  width: `${(timeLeft / notification.duration) * 100}%`
                }}
              />
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

interface NotificationToastContainerProps {
  notifications: ToastNotification[]
  onDismiss: (id: string) => void
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left'
  maxNotifications?: number
}

export function NotificationToastContainer({
  notifications,
  onDismiss,
  position = 'top-right',
  maxNotifications = 5
}: NotificationToastContainerProps) {
  const positionClasses = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4'
  }

  const isTop = position.includes('top')
  const visibleNotifications = notifications.slice(0, maxNotifications)

  return (
    <div
      className={cn(
        "fixed z-50 pointer-events-none",
        positionClasses[position]
      )}
    >
      <div
        className={cn(
          "flex flex-col gap-2",
          isTop ? '' : 'flex-col-reverse'
        )}
      >
        {visibleNotifications.map((notification) => (
          <NotificationToast
            key={notification.id}
            notification={notification}
            onDismiss={onDismiss}
            position={position}
          />
        ))}
      </div>
    </div>
  )
}

// Hook for managing toast notifications
export function useNotificationToast() {
  const [notifications, setNotifications] = useState<ToastNotification[]>([])

  const showToast = (notification: Omit<ToastNotification, 'id'>) => {
    const id = Date.now().toString()
    const newNotification: ToastNotification = {
      ...notification,
      id,
      duration: notification.duration ?? 5000
    }
    
    setNotifications((prev) => [newNotification, ...prev])
    return id
  }

  const dismissToast = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }

  const dismissAll = () => {
    setNotifications([])
  }

  return {
    notifications,
    showToast,
    dismissToast,
    dismissAll
  }
}