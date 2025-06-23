/**
 * Notification Permission Prompt Component
 * User-friendly UI for requesting notification permissions
 */

import React, { useState } from 'react'
import { Bell, BellOff, X, CheckCircle, AlertCircle, Info } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { usePushNotifications } from '@/hooks/use-push-notifications'

interface NotificationPermissionPromptProps {
  onClose?: () => void
  showBenefits?: boolean
}

export function NotificationPermissionPrompt({ 
  onClose, 
  showBenefits = true 
}: NotificationPermissionPromptProps) {
  const {
    isSupported,
    permission,
    isSubscribed,
    isLoading,
    error,
    requestPermission,
    subscribe
  } = usePushNotifications()

  const [showReEnableDialog, setShowReEnableDialog] = useState(false)

  // Don't show if not supported
  if (!isSupported) {
    return null
  }

  // Don't show if already subscribed
  if (isSubscribed && permission === 'granted') {
    return null
  }

  const handleEnable = async () => {
    if (permission === 'default') {
      await requestPermission()
    }
    
    if (permission === 'granted' || Notification.permission === 'granted') {
      await subscribe()
    }
  }

  const benefits = [
    {
      icon: <AlertCircle className="h-5 w-5 text-red-500" />,
      title: 'Critical Incident Alerts',
      description: 'Get instant notifications for high-priority incidents'
    },
    {
      icon: <CheckCircle className="h-5 w-5 text-green-500" />,
      title: 'Status Updates',
      description: 'Stay informed about incident resolutions and system status'
    },
    {
      icon: <Bell className="h-5 w-5 text-blue-500" />,
      title: 'Smart Notifications',
      description: 'Receive only relevant alerts based on your preferences'
    }
  ]

  if (permission === 'denied') {
    return (
      <>
        <Alert variant="destructive" className="mb-4">
          <BellOff className="h-4 w-4" />
          <AlertTitle>Notifications Blocked</AlertTitle>
          <AlertDescription className="mt-2">
            Push notifications are currently blocked for this site. 
            <Button
              variant="link"
              size="sm"
              className="ml-1 h-auto p-0"
              onClick={() => setShowReEnableDialog(true)}
            >
              Learn how to re-enable them
            </Button>
          </AlertDescription>
        </Alert>

        <Dialog open={showReEnableDialog} onOpenChange={setShowReEnableDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>How to Re-enable Notifications</DialogTitle>
              <DialogDescription>
                Follow these steps to allow notifications from SentinelOps:
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <h4 className="font-medium">For Chrome/Edge:</h4>
                <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground">
                  <li>Click the lock icon in the address bar</li>
                  <li>Find "Notifications" in the permissions list</li>
                  <li>Change from "Block" to "Allow"</li>
                  <li>Refresh the page</li>
                </ol>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium">For Firefox:</h4>
                <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground">
                  <li>Click the lock icon in the address bar</li>
                  <li>Click "Connection secure" dropdown</li>
                  <li>Click "More information"</li>
                  <li>Go to "Permissions" tab</li>
                  <li>Find "Receive Notifications" and uncheck "Use Default"</li>
                  <li>Select "Allow"</li>
                </ol>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium">For Safari:</h4>
                <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground">
                  <li>Go to Safari → Preferences</li>
                  <li>Click "Websites" tab</li>
                  <li>Select "Notifications" from the sidebar</li>
                  <li>Find SentinelOps and change to "Allow"</li>
                </ol>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </>
    )
  }

  return (
    <Card className="relative">
      {onClose && (
        <Button
          variant="ghost"
          size="sm"
          className="absolute right-2 top-2"
          onClick={onClose}
        >
          <X className="h-4 w-4" />
        </Button>
      )}
      
      <CardHeader>
        <div className="flex items-center gap-2">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Bell className="h-6 w-6 text-primary" />
          </div>
          <div>
            <CardTitle>Enable Push Notifications</CardTitle>
            <CardDescription>
              Stay updated with real-time alerts and incident notifications
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {showBenefits && (
          <div className="space-y-3">
            {benefits.map((benefit, index) => (
              <div key={index} className="flex gap-3">
                {benefit.icon}
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-medium">{benefit.title}</p>
                  <p className="text-sm text-muted-foreground">{benefit.description}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="flex gap-2">
          <Button
            onClick={handleEnable}
            disabled={isLoading}
            className="flex-1"
          >
            {isLoading ? (
              <>Loading...</>
            ) : (
              <>
                <Bell className="h-4 w-4 mr-2" />
                Enable Notifications
              </>
            )}
          </Button>
          
          {onClose && (
            <Button
              variant="outline"
              onClick={onClose}
              disabled={isLoading}
            >
              Maybe Later
            </Button>
          )}
        </div>

        <p className="text-xs text-muted-foreground text-center">
          <Info className="h-3 w-3 inline mr-1" />
          You can change this setting anytime in your preferences
        </p>
      </CardContent>
    </Card>
  )
}