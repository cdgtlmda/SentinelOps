"use client"

import { useState } from 'react'
import { useUserPreferencesStore } from '@/store'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Bell, 
  Mail, 
  MessageSquare, 
  Volume2, 
  Webhook,
  Plus,
  Trash2,
  TestTube,
  Settings
} from 'lucide-react'

interface EmailDigestSettings {
  enabled: boolean
  frequency: 'daily' | 'weekly' | 'monthly'
  time: string
  includeResolved: boolean
}

interface IntegrationSettings {
  slack: {
    enabled: boolean
    webhookUrl: string
    channel: string
    mentionUsers: boolean
  }
  teams: {
    enabled: boolean
    webhookUrl: string
    mentionUsers: boolean
  }
}

interface WebhookConfig {
  id: string
  name: string
  url: string
  events: string[]
  headers: Record<string, string>
  active: boolean
}

export default function NotificationSettings() {
  const { notifications, updateNotificationPreferences } = useUserPreferencesStore()
  
  const [emailDigest, setEmailDigest] = useState<EmailDigestSettings>({
    enabled: true,
    frequency: 'daily',
    time: '09:00',
    includeResolved: false
  })

  const [integrations, setIntegrations] = useState<IntegrationSettings>({
    slack: {
      enabled: false,
      webhookUrl: '',
      channel: '#incidents',
      mentionUsers: true
    },
    teams: {
      enabled: false,
      webhookUrl: '',
      mentionUsers: true
    }
  })

  const [webhooks, setWebhooks] = useState<WebhookConfig[]>([])
  const [soundEnabled, setSoundEnabled] = useState(true)
  const [selectedSound, setSelectedSound] = useState('default')

  const notificationSounds = [
    { value: 'default', label: 'Default' },
    { value: 'chime', label: 'Chime' },
    { value: 'ping', label: 'Ping' },
    { value: 'bell', label: 'Bell' },
    { value: 'alert', label: 'Alert' },
    { value: 'none', label: 'None' },
  ]

  const eventTypes = [
    'incident.created',
    'incident.updated',
    'incident.resolved',
    'agent.offline',
    'workflow.failed',
  ]

  const addWebhook = () => {
    const newWebhook: WebhookConfig = {
      id: crypto.randomUUID(),
      name: 'New Webhook',
      url: '',
      events: [],
      headers: {},
      active: true
    }
    setWebhooks([...webhooks, newWebhook])
  }

  const removeWebhook = (id: string) => {
    setWebhooks(webhooks.filter(w => w.id !== id))
  }

  const updateWebhook = (id: string, updates: Partial<WebhookConfig>) => {
    setWebhooks(webhooks.map(w => 
      w.id === id ? { ...w, ...updates } : w
    ))
  }

  const testNotification = (channel: string) => {
    // Implement test notification logic
    console.log(`Testing ${channel} notification`)
  }

  return (
    <div className="space-y-6">
      {/* Notification Channels */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Notification Channels
          </CardTitle>
          <CardDescription>
            Choose how you want to receive notifications
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="email-notifications" className="flex items-center gap-2">
                <Mail className="w-4 h-4" />
                Email Notifications
              </Label>
              <p className="text-sm text-muted-foreground">
                Receive incident alerts via email
              </p>
            </div>
            <Switch
              id="email-notifications"
              checked={notifications.email}
              onCheckedChange={(checked) => updateNotificationPreferences({ email: checked })}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="slack-notifications" className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4" />
                Slack Notifications
              </Label>
              <p className="text-sm text-muted-foreground">
                Get real-time alerts in your Slack workspace
              </p>
            </div>
            <Switch
              id="slack-notifications"
              checked={notifications.slack}
              onCheckedChange={(checked) => updateNotificationPreferences({ slack: checked })}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="in-app-notifications" className="flex items-center gap-2">
                <Bell className="w-4 h-4" />
                In-App Notifications
              </Label>
              <p className="text-sm text-muted-foreground">
                Show notifications within SentinelOps
              </p>
            </div>
            <Switch
              id="in-app-notifications"
              checked={notifications.inApp}
              onCheckedChange={(checked) => updateNotificationPreferences({ inApp: checked })}
            />
          </div>

          {/* Severity Threshold */}
          <div className="space-y-2 pt-4 border-t">
            <Label>Severity Threshold</Label>
            <Select 
              value={notifications.severityThreshold} 
              onValueChange={(value) => updateNotificationPreferences({ severityThreshold: value as any })}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select severity threshold" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low and above</SelectItem>
                <SelectItem value="medium">Medium and above</SelectItem>
                <SelectItem value="high">High and above</SelectItem>
                <SelectItem value="critical">Critical only</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">
              Only receive notifications for incidents at or above this severity level
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Email Digest Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="w-5 h-5" />
            Email Digest
          </CardTitle>
          <CardDescription>
            Configure email summary settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="email-digest">Enable Email Digest</Label>
            <Switch
              id="email-digest"
              checked={emailDigest.enabled}
              onCheckedChange={(checked) => setEmailDigest({ ...emailDigest, enabled: checked })}
            />
          </div>

          {emailDigest.enabled && (
            <>
              <div className="space-y-2">
                <Label>Frequency</Label>
                <Select 
                  value={emailDigest.frequency} 
                  onValueChange={(value: any) => setEmailDigest({ ...emailDigest, frequency: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                    <SelectItem value="monthly">Monthly</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="digest-time">Delivery Time</Label>
                <Input
                  id="digest-time"
                  type="time"
                  value={emailDigest.time}
                  onChange={(e) => setEmailDigest({ ...emailDigest, time: e.target.value })}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="include-resolved">Include Resolved Incidents</Label>
                <Switch
                  id="include-resolved"
                  checked={emailDigest.includeResolved}
                  onCheckedChange={(checked) => setEmailDigest({ ...emailDigest, includeResolved: checked })}
                />
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Integrations */}
      <Card>
        <CardHeader>
          <CardTitle>Integrations</CardTitle>
          <CardDescription>
            Connect SentinelOps with your favorite tools
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="slack" className="space-y-4">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="slack">Slack</TabsTrigger>
              <TabsTrigger value="teams">Microsoft Teams</TabsTrigger>
            </TabsList>

            <TabsContent value="slack" className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="slack-enabled">Enable Slack Integration</Label>
                <Switch
                  id="slack-enabled"
                  checked={integrations.slack.enabled}
                  onCheckedChange={(checked) => 
                    setIntegrations({ ...integrations, slack: { ...integrations.slack, enabled: checked }})
                  }
                />
              </div>

              {integrations.slack.enabled && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="slack-webhook">Webhook URL</Label>
                    <Input
                      id="slack-webhook"
                      type="url"
                      placeholder="https://hooks.slack.com/services/..."
                      value={integrations.slack.webhookUrl}
                      onChange={(e) => 
                        setIntegrations({ 
                          ...integrations, 
                          slack: { ...integrations.slack, webhookUrl: e.target.value }
                        })
                      }
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="slack-channel">Default Channel</Label>
                    <Input
                      id="slack-channel"
                      placeholder="#incidents"
                      value={integrations.slack.channel}
                      onChange={(e) => 
                        setIntegrations({ 
                          ...integrations, 
                          slack: { ...integrations.slack, channel: e.target.value }
                        })
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="slack-mentions">Mention Users</Label>
                    <Switch
                      id="slack-mentions"
                      checked={integrations.slack.mentionUsers}
                      onCheckedChange={(checked) => 
                        setIntegrations({ 
                          ...integrations, 
                          slack: { ...integrations.slack, mentionUsers: checked }
                        })
                      }
                    />
                  </div>

                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => testNotification('slack')}
                  >
                    <TestTube className="w-4 h-4 mr-2" />
                    Test Slack Notification
                  </Button>
                </>
              )}
            </TabsContent>

            <TabsContent value="teams" className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="teams-enabled">Enable Teams Integration</Label>
                <Switch
                  id="teams-enabled"
                  checked={integrations.teams.enabled}
                  onCheckedChange={(checked) => 
                    setIntegrations({ ...integrations, teams: { ...integrations.teams, enabled: checked }})
                  }
                />
              </div>

              {integrations.teams.enabled && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="teams-webhook">Webhook URL</Label>
                    <Input
                      id="teams-webhook"
                      type="url"
                      placeholder="https://outlook.office.com/webhook/..."
                      value={integrations.teams.webhookUrl}
                      onChange={(e) => 
                        setIntegrations({ 
                          ...integrations, 
                          teams: { ...integrations.teams, webhookUrl: e.target.value }
                        })
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="teams-mentions">Mention Users</Label>
                    <Switch
                      id="teams-mentions"
                      checked={integrations.teams.mentionUsers}
                      onCheckedChange={(checked) => 
                        setIntegrations({ 
                          ...integrations, 
                          teams: { ...integrations.teams, mentionUsers: checked }
                        })
                      }
                    />
                  </div>

                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => testNotification('teams')}
                  >
                    <TestTube className="w-4 h-4 mr-2" />
                    Test Teams Notification
                  </Button>
                </>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Webhook Configurations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Webhook className="w-5 h-5" />
            Webhooks
          </CardTitle>
          <CardDescription>
            Configure custom webhooks for advanced integrations
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {webhooks.map(webhook => (
            <div key={webhook.id} className="p-4 border rounded-lg space-y-3">
              <div className="flex items-center justify-between">
                <Input
                  value={webhook.name}
                  onChange={(e) => updateWebhook(webhook.id, { name: e.target.value })}
                  placeholder="Webhook name"
                  className="max-w-xs"
                />
                <div className="flex items-center gap-2">
                  <Switch
                    checked={webhook.active}
                    onCheckedChange={(checked) => updateWebhook(webhook.id, { active: checked })}
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeWebhook(webhook.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              <Input
                value={webhook.url}
                onChange={(e) => updateWebhook(webhook.id, { url: e.target.value })}
                placeholder="https://your-webhook-endpoint.com"
                type="url"
              />

              <div className="space-y-2">
                <Label>Events</Label>
                <div className="flex flex-wrap gap-2">
                  {eventTypes.map(event => (
                    <Badge
                      key={event}
                      variant={webhook.events.includes(event) ? 'default' : 'outline'}
                      className="cursor-pointer"
                      onClick={() => {
                        const events = webhook.events.includes(event)
                          ? webhook.events.filter(e => e !== event)
                          : [...webhook.events, event]
                        updateWebhook(webhook.id, { events })
                      }}
                    >
                      {event}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          ))}

          <Button onClick={addWebhook} variant="outline" className="w-full">
            <Plus className="w-4 h-4 mr-2" />
            Add Webhook
          </Button>
        </CardContent>
      </Card>

      {/* Sound Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Volume2 className="w-5 h-5" />
            Notification Sounds
          </CardTitle>
          <CardDescription>
            Customize notification audio alerts
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="sound-enabled">Enable Notification Sounds</Label>
            <Switch
              id="sound-enabled"
              checked={soundEnabled}
              onCheckedChange={setSoundEnabled}
            />
          </div>

          {soundEnabled && (
            <div className="space-y-2">
              <Label>Notification Sound</Label>
              <Select value={selectedSound} onValueChange={setSelectedSound}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {notificationSounds.map(sound => (
                    <SelectItem key={sound.value} value={sound.value}>
                      {sound.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => console.log('Playing sound:', selectedSound)}
              >
                <Volume2 className="w-4 h-4 mr-2" />
                Preview Sound
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}