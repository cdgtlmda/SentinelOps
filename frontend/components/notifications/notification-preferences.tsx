/**
 * Notification Preferences Component
 * Manage notification channels, quiet hours, and device settings
 */

import React, { useState } from 'react'
import { 
  Bell, 
  BellOff, 
  Moon, 
  Sun, 
  Volume2, 
  VolumeX,
  Smartphone,
  Monitor,
  Mail,
  MessageSquare,
  Calendar,
  Shield,
  AlertCircle,
  CheckCircle,
  Info,
  AlertTriangle
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { usePushNotifications } from '@/hooks/use-push-notifications'
import { cn } from '@/lib/utils'

interface NotificationChannel {
  id: string
  name: string
  description: string
  icon: React.ReactNode
  enabled: boolean
  settings?: {
    critical: boolean
    high: boolean
    medium: boolean
    low: boolean
  }
}

interface QuietHours {
  enabled: boolean
  startTime: string
  endTime: string
  timezone: string
  overrideCritical: boolean
}

interface NotificationPreferencesProps {
  channels: NotificationChannel[]
  quietHours: QuietHours
  soundEnabled: boolean
  vibrationEnabled: boolean
  doNotDisturb: boolean
  onChannelToggle: (channelId: string, enabled: boolean) => void
  onChannelSettingChange: (channelId: string, priority: string, enabled: boolean) => void
  onQuietHoursChange: (quietHours: QuietHours) => void
  onSoundToggle: (enabled: boolean) => void
  onVibrationToggle: (enabled: boolean) => void
  onDoNotDisturbToggle: (enabled: boolean) => void
}

export function NotificationPreferences({
  channels,
  quietHours,
  soundEnabled,
  vibrationEnabled,
  doNotDisturb,
  onChannelToggle,
  onChannelSettingChange,
  onQuietHoursChange,
  onSoundToggle,
  onVibrationToggle,
  onDoNotDisturbToggle
}: NotificationPreferencesProps) {
  const { isSupported, permission, isSubscribed, subscribe, unsubscribe } = usePushNotifications()
  const [expandedChannels, setExpandedChannels] = useState<Set<string>>(new Set())

  const toggleChannelExpanded = (channelId: string) => {
    setExpandedChannels(prev => {
      const next = new Set(prev)
      if (next.has(channelId)) {
        next.delete(channelId)
      } else {
        next.add(channelId)
      }
      return next
    })
  }

  const priorityIcons = {
    critical: <AlertCircle className="h-4 w-4 text-red-500" />,
    high: <AlertTriangle className="h-4 w-4 text-orange-500" />,
    medium: <Info className="h-4 w-4 text-blue-500" />,
    low: <Info className="h-4 w-4 text-gray-500" />
  }

  return (
    <div className="space-y-6">
      {/* Push Notification Status */}
      {isSupported && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Push Notifications
            </CardTitle>
            <CardDescription>
              Receive real-time notifications even when the app is closed
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">Browser Notifications</span>
                    {permission === 'granted' && (
                      <Badge variant="outline" className="text-green-600">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Enabled
                      </Badge>
                    )}
                    {permission === 'denied' && (
                      <Badge variant="outline" className="text-red-600">
                        <BellOff className="h-3 w-3 mr-1" />
                        Blocked
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {isSubscribed 
                      ? 'You are subscribed to push notifications'
                      : 'Enable to receive notifications when the app is closed'
                    }
                  </p>
                </div>
                <Switch
                  checked={isSubscribed}
                  onCheckedChange={isSubscribed ? unsubscribe : subscribe}
                  disabled={permission === 'denied'}
                />
              </div>

              {permission === 'denied' && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Notifications are blocked in your browser. Please check your browser settings to re-enable them.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Do Not Disturb */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Do Not Disturb
          </CardTitle>
          <CardDescription>
            Temporarily pause all notifications
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="font-medium">Enable Do Not Disturb</p>
              <p className="text-sm text-muted-foreground">
                {doNotDisturb 
                  ? 'All notifications are currently paused'
                  : 'Receive notifications normally'
                }
              </p>
            </div>
            <Switch
              checked={doNotDisturb}
              onCheckedChange={onDoNotDisturbToggle}
            />
          </div>
        </CardContent>
      </Card>

      {/* Notification Channels */}
      <Card>
        <CardHeader>
          <CardTitle>Notification Channels</CardTitle>
          <CardDescription>
            Choose which types of notifications you want to receive
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {channels.map((channel, index) => (
            <div key={channel.id}>
              {index > 0 && <Separator className="my-4" />}
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div 
                    className="flex items-center gap-3 flex-1 cursor-pointer"
                    onClick={() => toggleChannelExpanded(channel.id)}
                  >
                    {channel.icon}
                    <div className="space-y-1">
                      <p className="font-medium">{channel.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {channel.description}
                      </p>
                    </div>
                  </div>
                  <Switch
                    checked={channel.enabled}
                    onCheckedChange={(enabled) => onChannelToggle(channel.id, enabled)}
                  />
                </div>

                {expandedChannels.has(channel.id) && channel.settings && (
                  <div className="ml-10 space-y-3 pt-2">
                    <p className="text-sm font-medium text-muted-foreground">
                      Priority Settings
                    </p>
                    {Object.entries(channel.settings).map(([priority, enabled]) => (
                      <div key={priority} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {priorityIcons[priority as keyof typeof priorityIcons]}
                          <Label className="text-sm capitalize">{priority}</Label>
                        </div>
                        <Switch
                          checked={enabled}
                          onCheckedChange={(checked) => 
                            onChannelSettingChange(channel.id, priority, checked)
                          }
                          disabled={!channel.enabled}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Quiet Hours */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Moon className="h-5 w-5" />
            Quiet Hours
          </CardTitle>
          <CardDescription>
            Schedule times when you don't want to receive notifications
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="quiet-hours">Enable Quiet Hours</Label>
            <Switch
              id="quiet-hours"
              checked={quietHours.enabled}
              onCheckedChange={(enabled) => 
                onQuietHoursChange({ ...quietHours, enabled })
              }
            />
          </div>

          {quietHours.enabled && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="start-time">Start Time</Label>
                  <input
                    id="start-time"
                    type="time"
                    value={quietHours.startTime}
                    onChange={(e) => 
                      onQuietHoursChange({ ...quietHours, startTime: e.target.value })
                    }
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="end-time">End Time</Label>
                  <input
                    id="end-time"
                    type="time"
                    value={quietHours.endTime}
                    onChange={(e) => 
                      onQuietHoursChange({ ...quietHours, endTime: e.target.value })
                    }
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="override-critical">Allow Critical Alerts</Label>
                  <p className="text-sm text-muted-foreground">
                    Override quiet hours for critical notifications
                  </p>
                </div>
                <Switch
                  id="override-critical"
                  checked={quietHours.overrideCritical}
                  onCheckedChange={(checked) => 
                    onQuietHoursChange({ ...quietHours, overrideCritical: checked })
                  }
                />
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Sound & Vibration */}
      <Card>
        <CardHeader>
          <CardTitle>Sound & Vibration</CardTitle>
          <CardDescription>
            Control notification sounds and vibrations
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Volume2 className="h-5 w-5 text-muted-foreground" />
              <div className="space-y-1">
                <Label htmlFor="sound">Notification Sound</Label>
                <p className="text-sm text-muted-foreground">
                  Play sound for notifications
                </p>
              </div>
            </div>
            <Switch
              id="sound"
              checked={soundEnabled}
              onCheckedChange={onSoundToggle}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Smartphone className="h-5 w-5 text-muted-foreground" />
              <div className="space-y-1">
                <Label htmlFor="vibration">Vibration</Label>
                <p className="text-sm text-muted-foreground">
                  Vibrate device for notifications (mobile only)
                </p>
              </div>
            </div>
            <Switch
              id="vibration"
              checked={vibrationEnabled}
              onCheckedChange={onVibrationToggle}
            />
          </div>
        </CardContent>
      </Card>

      {/* Device Management */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="h-5 w-5" />
            Device Management
          </CardTitle>
          <CardDescription>
            Manage devices receiving notifications
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-3">
                <Monitor className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="font-medium">Current Device</p>
                  <p className="text-sm text-muted-foreground">
                    {navigator.userAgent.includes('Mobile') ? 'Mobile' : 'Desktop'} • Active now
                  </p>
                </div>
              </div>
              <Badge variant="outline" className="text-green-600">
                <CheckCircle className="h-3 w-3 mr-1" />
                Active
              </Badge>
            </div>
            
            <p className="text-sm text-muted-foreground text-center py-2">
              To manage notifications on other devices, sign in on those devices
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}