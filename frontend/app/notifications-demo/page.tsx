'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Bell, Send, Settings, TestTube, Info } from 'lucide-react'
import {
  NotificationPermissionPrompt,
  InAppNotificationCenter,
  NotificationToastContainer,
  useNotificationToast,
  NotificationPreferences,
  type Notification
} from '@/components/notifications'
import { usePushNotifications } from '@/hooks/use-push-notifications'

export default function NotificationsDemoPage() {
  const { showToast, notifications: toastNotifications, dismissToast } = useNotificationToast()
  const { showNotification, updateBadgeCount } = usePushNotifications()
  const [showPermissionPrompt, setShowPermissionPrompt] = useState(true)
  const [showPreferences, setShowPreferences] = useState(false)
  
  // Demo notification state
  const [notifications, setNotifications] = useState<Notification[]>([
    {
      id: '1',
      title: 'Critical Incident Detected',
      message: 'Database connection failure on production server',
      type: 'incident',
      priority: 'critical',
      timestamp: new Date(Date.now() - 5 * 60 * 1000),
      read: false,
      actionUrl: '/incidents/123',
      actionLabel: 'View Incident',
      groupId: 'incident-123'
    },
    {
      id: '2',
      title: 'Security Alert',
      message: 'Unusual login activity detected from new location',
      type: 'alert',
      priority: 'high',
      timestamp: new Date(Date.now() - 30 * 60 * 1000),
      read: false,
      actionUrl: '/alerts/456',
      groupId: 'alert-456'
    },
    {
      id: '3',
      title: 'System Update',
      message: 'Scheduled maintenance completed successfully',
      type: 'update',
      priority: 'low',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
      read: true,
      groupId: 'update-789'
    }
  ])

  // Demo preferences state
  const [channels] = useState([
    {
      id: 'incidents',
      name: 'Incident Notifications',
      description: 'Critical incidents and system failures',
      icon: <Bell className="h-5 w-5" />,
      enabled: true,
      settings: {
        critical: true,
        high: true,
        medium: false,
        low: false
      }
    },
    {
      id: 'alerts',
      name: 'Security Alerts',
      description: 'Security threats and anomalies',
      icon: <Bell className="h-5 w-5" />,
      enabled: true,
      settings: {
        critical: true,
        high: true,
        medium: true,
        low: false
      }
    }
  ])

  const [quietHours, setQuietHours] = useState({
    enabled: false,
    startTime: '22:00',
    endTime: '08:00',
    timezone: 'America/New_York',
    overrideCritical: true
  })

  const [soundEnabled, setSoundEnabled] = useState(true)
  const [vibrationEnabled, setVibrationEnabled] = useState(true)
  const [doNotDisturb, setDoNotDisturb] = useState(false)

  // Handlers
  const handleMarkAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    )
    updateBadgeCount(notifications.filter(n => !n.read && n.id !== id).length)
  }

  const handleMarkAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
    updateBadgeCount(0)
  }

  const handleArchive = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  const sendTestToast = (type: 'success' | 'error' | 'warning' | 'info') => {
    const messages = {
      success: { title: 'Operation Successful', description: 'Your changes have been saved' },
      error: { title: 'Error Occurred', description: 'Failed to complete the operation' },
      warning: { title: 'Warning', description: 'This action may have consequences' },
      info: { title: 'Information', description: 'Here\'s something you should know' }
    }

    showToast({
      ...messages[type],
      type,
      duration: 5000,
      action: type === 'error' ? {
        label: 'Retry',
        onClick: () => console.log('Retry clicked')
      } : undefined
    })
  }

  const sendTestPushNotification = async () => {
    try {
      await showNotification('Test Push Notification', {
        body: 'This is a test push notification from SentinelOps',
        tag: 'test-notification',
        requireInteraction: false,
        actions: [
          { action: 'view', title: 'View' },
          { action: 'dismiss', title: 'Dismiss' }
        ]
      })
    } catch (error) {
      showToast({
        title: 'Failed to send notification',
        description: error instanceof Error ? error.message : 'Unknown error',
        type: 'error'
      })
    }
  }

  const addNewNotification = () => {
    const newNotification: Notification = {
      id: Date.now().toString(),
      title: 'New Test Notification',
      message: `This is a test notification created at ${new Date().toLocaleTimeString()}`,
      type: 'info',
      priority: 'medium',
      timestamp: new Date(),
      read: false,
      actionUrl: '#',
      actionLabel: 'View Details'
    }
    
    setNotifications(prev => [newNotification, ...prev])
    updateBadgeCount(notifications.filter(n => !n.read).length + 1)
    
    showToast({
      title: 'New Notification',
      description: newNotification.message,
      type: 'info',
      duration: 5000
    })
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Notification System Demo</h1>
        <p className="text-muted-foreground">
          Test the comprehensive push notification system with permissions, in-app notifications, and preferences
        </p>
      </div>

      {!showPreferences ? (
        <div className="space-y-6">
          {/* Permission Prompt */}
          {showPermissionPrompt && (
            <div className="mb-6">
              <NotificationPermissionPrompt onClose={() => setShowPermissionPrompt(false)} />
            </div>
          )}

          {/* Test Controls */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TestTube className="h-5 w-5" />
                Test Notifications
              </CardTitle>
              <CardDescription>
                Send test notifications to see how they appear
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="text-sm font-medium mb-3">Toast Notifications</h4>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => sendTestToast('success')}
                    className="text-green-600"
                  >
                    Success Toast
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => sendTestToast('error')}
                    className="text-red-600"
                  >
                    Error Toast
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => sendTestToast('warning')}
                    className="text-yellow-600"
                  >
                    Warning Toast
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => sendTestToast('info')}
                    className="text-blue-600"
                  >
                    Info Toast
                  </Button>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium mb-3">Push Notifications</h4>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={sendTestPushNotification}
                  >
                    <Send className="h-4 w-4 mr-2" />
                    Send Push Notification
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={addNewNotification}
                  >
                    <Bell className="h-4 w-4 mr-2" />
                    Add In-App Notification
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Notification Center Demo */}
          <Card>
            <CardHeader>
              <CardTitle>Notification Center</CardTitle>
              <CardDescription>
                Click the bell icon to view and manage notifications
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <InAppNotificationCenter
                    notifications={notifications}
                    onMarkAsRead={handleMarkAsRead}
                    onMarkAllAsRead={handleMarkAllAsRead}
                    onArchive={handleArchive}
                    onSettingsClick={() => setShowPreferences(true)}
                  />
                  <span className="text-sm text-muted-foreground">
                    {notifications.filter(n => !n.read).length} unread notifications
                  </span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowPreferences(true)}
                >
                  <Settings className="h-4 w-4 mr-2" />
                  Preferences
                </Button>
              </div>
            </CardContent>
          </Card>

          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              This demo shows how the notification system works. In a real application, 
              notifications would be triggered by actual system events and synced with a backend server.
            </AlertDescription>
          </Alert>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">Notification Preferences</h2>
            <Button onClick={() => setShowPreferences(false)}>
              Back to Demo
            </Button>
          </div>
          
          <NotificationPreferences
            channels={channels}
            quietHours={quietHours}
            soundEnabled={soundEnabled}
            vibrationEnabled={vibrationEnabled}
            doNotDisturb={doNotDisturb}
            onChannelToggle={(channelId, enabled) => console.log('Channel toggle:', channelId, enabled)}
            onChannelSettingChange={(channelId, priority, enabled) => 
              console.log('Channel setting:', channelId, priority, enabled)
            }
            onQuietHoursChange={setQuietHours}
            onSoundToggle={setSoundEnabled}
            onVibrationToggle={setVibrationEnabled}
            onDoNotDisturbToggle={setDoNotDisturb}
          />
        </div>
      )}

      {/* Toast Container */}
      <NotificationToastContainer
        notifications={toastNotifications}
        onDismiss={dismissToast}
        position="top-right"
        maxNotifications={5}
      />
    </div>
  )
}