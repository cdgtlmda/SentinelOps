"use client"

import { useState, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Clock, 
  Globe, 
  MapPin, 
  Plus, 
  Trash2, 
  Calendar,
  Sun,
  Moon
} from 'lucide-react'

interface TimezoneSettings {
  primaryTimezone: string
  autoDetect: boolean
  showMultipleTimezones: boolean
  additionalTimezones: string[]
  businessHours: {
    start: string
    end: string
    workDays: number[]
  }
  handleDST: boolean
}

interface TimezoneInfo {
  name: string
  offset: string
  region: string
  cities: string[]
}

export default function TimezoneSettings() {
  const [settings, setSettings] = useState<TimezoneSettings>({
    primaryTimezone: 'America/New_York',
    autoDetect: true,
    showMultipleTimezones: false,
    additionalTimezones: ['Europe/London', 'Asia/Tokyo'],
    businessHours: {
      start: '09:00',
      end: '17:00',
      workDays: [1, 2, 3, 4, 5] // Monday to Friday
    },
    handleDST: true
  })

  const [searchQuery, setSearchQuery] = useState('')

  const timezones: TimezoneInfo[] = [
    { name: 'America/New_York', offset: 'UTC-5', region: 'Americas', cities: ['New York', 'Toronto', 'Montreal'] },
    { name: 'America/Chicago', offset: 'UTC-6', region: 'Americas', cities: ['Chicago', 'Houston', 'Mexico City'] },
    { name: 'America/Denver', offset: 'UTC-7', region: 'Americas', cities: ['Denver', 'Phoenix', 'Calgary'] },
    { name: 'America/Los_Angeles', offset: 'UTC-8', region: 'Americas', cities: ['Los Angeles', 'Seattle', 'Vancouver'] },
    { name: 'America/Sao_Paulo', offset: 'UTC-3', region: 'Americas', cities: ['São Paulo', 'Rio de Janeiro', 'Buenos Aires'] },
    { name: 'Europe/London', offset: 'UTC+0', region: 'Europe', cities: ['London', 'Dublin', 'Lisbon'] },
    { name: 'Europe/Paris', offset: 'UTC+1', region: 'Europe', cities: ['Paris', 'Berlin', 'Rome'] },
    { name: 'Europe/Moscow', offset: 'UTC+3', region: 'Europe', cities: ['Moscow', 'Istanbul', 'Athens'] },
    { name: 'Asia/Dubai', offset: 'UTC+4', region: 'Asia', cities: ['Dubai', 'Abu Dhabi', 'Muscat'] },
    { name: 'Asia/Kolkata', offset: 'UTC+5:30', region: 'Asia', cities: ['Mumbai', 'Delhi', 'Bangalore'] },
    { name: 'Asia/Shanghai', offset: 'UTC+8', region: 'Asia', cities: ['Shanghai', 'Beijing', 'Hong Kong'] },
    { name: 'Asia/Tokyo', offset: 'UTC+9', region: 'Asia', cities: ['Tokyo', 'Seoul', 'Osaka'] },
    { name: 'Australia/Sydney', offset: 'UTC+11', region: 'Oceania', cities: ['Sydney', 'Melbourne', 'Brisbane'] },
    { name: 'Pacific/Auckland', offset: 'UTC+13', region: 'Oceania', cities: ['Auckland', 'Wellington', 'Christchurch'] },
  ]

  const filteredTimezones = useMemo(() => {
    if (!searchQuery) return timezones

    const query = searchQuery.toLowerCase()
    return timezones.filter(tz => 
      tz.name.toLowerCase().includes(query) ||
      tz.cities.some(city => city.toLowerCase().includes(query)) ||
      tz.region.toLowerCase().includes(query)
    )
  }, [searchQuery])

  const getCurrentTime = (timezone: string) => {
    try {
      return new Date().toLocaleTimeString('en-US', {
        timeZone: timezone,
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      })
    } catch {
      return 'Invalid timezone'
    }
  }

  const addTimezone = (timezone: string) => {
    if (!settings.additionalTimezones.includes(timezone)) {
      setSettings(prev => ({
        ...prev,
        additionalTimezones: [...prev.additionalTimezones, timezone]
      }))
    }
  }

  const removeTimezone = (timezone: string) => {
    setSettings(prev => ({
      ...prev,
      additionalTimezones: prev.additionalTimezones.filter(tz => tz !== timezone)
    }))
  }

  const toggleWorkDay = (day: number) => {
    setSettings(prev => ({
      ...prev,
      businessHours: {
        ...prev.businessHours,
        workDays: prev.businessHours.workDays.includes(day)
          ? prev.businessHours.workDays.filter(d => d !== day)
          : [...prev.businessHours.workDays, day].sort()
      }
    }))
  }

  const weekDays = [
    { value: 0, label: 'Sun' },
    { value: 1, label: 'Mon' },
    { value: 2, label: 'Tue' },
    { value: 3, label: 'Wed' },
    { value: 4, label: 'Thu' },
    { value: 5, label: 'Fri' },
    { value: 6, label: 'Sat' },
  ]

  return (
    <div className="space-y-6">
      {/* Primary Timezone */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Time Zone
          </CardTitle>
          <CardDescription>
            Set your primary time zone and display preferences
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="auto-detect">Auto-detect time zone</Label>
              <p className="text-sm text-muted-foreground">
                Automatically use your device's time zone
              </p>
            </div>
            <Switch
              id="auto-detect"
              checked={settings.autoDetect}
              onCheckedChange={(checked) => setSettings({ ...settings, autoDetect: checked })}
            />
          </div>

          {!settings.autoDetect && (
            <div className="space-y-3">
              <Label>Select Time Zone</Label>
              <div className="relative">
                <MapPin className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search cities or time zones..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              
              <ScrollArea className="h-64 border rounded-md">
                <div className="p-2 space-y-1">
                  {filteredTimezones.map(tz => (
                    <button
                      key={tz.name}
                      onClick={() => setSettings({ ...settings, primaryTimezone: tz.name })}
                      className={`w-full text-left p-3 rounded-md hover:bg-accent transition-colors ${
                        settings.primaryTimezone === tz.name ? 'bg-accent' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">{tz.name.split('/').pop()?.replace('_', ' ')}</div>
                          <div className="text-sm text-muted-foreground">
                            {tz.cities.join(', ')} • {tz.offset}
                          </div>
                        </div>
                        <div className="text-sm font-mono">
                          {getCurrentTime(tz.name)}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </ScrollArea>
            </div>
          )}

          <div className="p-4 bg-muted rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Current Time Zone</div>
                <div className="text-sm text-muted-foreground">
                  {settings.primaryTimezone} • {timezones.find(tz => tz.name === settings.primaryTimezone)?.offset}
                </div>
              </div>
              <div className="text-2xl font-mono">
                {getCurrentTime(settings.primaryTimezone)}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Multiple Time Zones */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="w-5 h-5" />
            Multiple Time Zones
          </CardTitle>
          <CardDescription>
            Display multiple time zones for global teams
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="show-multiple">Show multiple time zones</Label>
            <Switch
              id="show-multiple"
              checked={settings.showMultipleTimezones}
              onCheckedChange={(checked) => setSettings({ ...settings, showMultipleTimezones: checked })}
            />
          </div>

          {settings.showMultipleTimezones && (
            <>
              <div className="space-y-2">
                {settings.additionalTimezones.map(tz => (
                  <div key={tz} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <div className="font-medium">{tz.split('/').pop()?.replace('_', ' ')}</div>
                      <div className="text-sm text-muted-foreground">
                        {timezones.find(t => t.name === tz)?.offset} • {getCurrentTime(tz)}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeTimezone(tz)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-2">
                <Input
                  placeholder="Add time zone..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1"
                />
                <Button
                  size="sm"
                  disabled={!filteredTimezones.length}
                  onClick={() => {
                    if (filteredTimezones.length > 0) {
                      addTimezone(filteredTimezones[0].name)
                      setSearchQuery('')
                    }
                  }}
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Business Hours */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Business Hours
          </CardTitle>
          <CardDescription>
            Define your working hours for better scheduling
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="start-time" className="flex items-center gap-2">
                <Sun className="w-4 h-4" />
                Start Time
              </Label>
              <Input
                id="start-time"
                type="time"
                value={settings.businessHours.start}
                onChange={(e) => setSettings({
                  ...settings,
                  businessHours: { ...settings.businessHours, start: e.target.value }
                })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="end-time" className="flex items-center gap-2">
                <Moon className="w-4 h-4" />
                End Time
              </Label>
              <Input
                id="end-time"
                type="time"
                value={settings.businessHours.end}
                onChange={(e) => setSettings({
                  ...settings,
                  businessHours: { ...settings.businessHours, end: e.target.value }
                })}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Working Days</Label>
            <div className="flex gap-2">
              {weekDays.map(day => (
                <Button
                  key={day.value}
                  variant={settings.businessHours.workDays.includes(day.value) ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => toggleWorkDay(day.value)}
                  className="w-12"
                >
                  {day.label}
                </Button>
              ))}
            </div>
          </div>

          <div className="p-4 bg-muted rounded-lg">
            <div className="text-sm">
              <div className="font-medium mb-1">Your Business Hours</div>
              <div className="text-muted-foreground">
                {weekDays
                  .filter(d => settings.businessHours.workDays.includes(d.value))
                  .map(d => d.label)
                  .join(', ')}
                {' • '}
                {settings.businessHours.start} - {settings.businessHours.end}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* DST Handling */}
      <Card>
        <CardHeader>
          <CardTitle>Daylight Saving Time</CardTitle>
          <CardDescription>
            Configure how to handle DST transitions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="handle-dst">Automatic DST adjustment</Label>
              <p className="text-sm text-muted-foreground">
                Automatically adjust for daylight saving time changes
              </p>
            </div>
            <Switch
              id="handle-dst"
              checked={settings.handleDST}
              onCheckedChange={(checked) => setSettings({ ...settings, handleDST: checked })}
            />
          </div>

          {settings.handleDST && (
            <div className="mt-4 p-4 bg-amber-50 dark:bg-amber-950/20 rounded-lg">
              <p className="text-sm text-amber-600 dark:text-amber-400">
                <strong>Note:</strong> Scheduled tasks and notifications will automatically 
                adjust when daylight saving time begins or ends.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}