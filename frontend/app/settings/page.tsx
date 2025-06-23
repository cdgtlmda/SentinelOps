"use client"

import { useState, useMemo } from 'react'
import { useUserPreferencesStore, useUIStore } from '@/store'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Palette, 
  Bell, 
  Monitor, 
  Globe, 
  Clock, 
  Search,
  Download,
  Upload,
  RotateCcw,
  Settings,
  Check,
  Loader2
} from 'lucide-react'

import AppearanceSettings from '@/components/settings/appearance-settings'
import NotificationSettings from '@/components/settings/notification-settings'
import DisplaySettings from '@/components/settings/display-settings'
import LanguageSettings from '@/components/settings/language-settings'
import TimezoneSettings from '@/components/settings/timezone-settings'
import SettingsSearch from '@/components/settings/settings-search'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('appearance')
  const [searchQuery, setSearchQuery] = useState('')
  const [isSyncing, setIsSyncing] = useState(false)
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null)
  
  const { theme } = useUIStore()

  const handleExportSettings = async () => {
    // Export logic will be implemented in use-settings hook
    const settings = {
      theme,
      // Add other settings here
    }
    
    const blob = new Blob([JSON.stringify(settings, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `sentinelops-settings-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleImportSettings = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      const text = await file.text()
      const settings = JSON.parse(text)
      // Import logic will be implemented in use-settings hook
      console.log('Importing settings:', settings)
    } catch (error) {
      console.error('Failed to import settings:', error)
    }
  }

  const handleResetToDefaults = () => {
    if (confirm('Are you sure you want to reset all settings to defaults? This action cannot be undone.')) {
      // Reset logic will be implemented in use-settings hook
      console.log('Resetting to defaults')
    }
  }

  const handleSyncSettings = async () => {
    setIsSyncing(true)
    try {
      // Sync logic will be implemented in use-settings hook
      await new Promise(resolve => setTimeout(resolve, 1000))
      setLastSyncTime(new Date())
    } finally {
      setIsSyncing(false)
    }
  }

  const settingsTabs = [
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'display', label: 'Display', icon: Monitor },
    { id: 'language', label: 'Language & Region', icon: Globe },
    { id: 'timezone', label: 'Time Zone', icon: Clock },
  ]

  return (
    <main className="container mx-auto py-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col gap-6 mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Settings className="w-8 h-8" />
              Settings
            </h1>
            <p className="text-muted-foreground mt-2">
              Manage your SentinelOps preferences and configuration
            </p>
          </div>
          
          {/* Settings Actions */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSyncSettings}
              disabled={isSyncing}
            >
              {isSyncing ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Check className="w-4 h-4 mr-2" />
              )}
              {isSyncing ? 'Syncing...' : 'Sync'}
            </Button>
            
            <Button variant="outline" size="sm" onClick={handleExportSettings}>
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
            
            <label htmlFor="import-settings">
              <Button variant="outline" size="sm" asChild>
                <span>
                  <Upload className="w-4 h-4 mr-2" />
                  Import
                </span>
              </Button>
            </label>
            <input
              id="import-settings"
              type="file"
              accept=".json"
              className="hidden"
              onChange={handleImportSettings}
            />
            
            <Button variant="outline" size="sm" onClick={handleResetToDefaults}>
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset
            </Button>
          </div>
        </div>

        {/* Sync Status */}
        {lastSyncTime && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Badge variant="secondary" className="gap-1">
              <Check className="w-3 h-3" />
              Synced
            </Badge>
            Last synced: {lastSyncTime.toLocaleString()}
          </div>
        )}

        {/* Search Bar */}
        <SettingsSearch onNavigate={setActiveTab} />
      </div>

      {/* Settings Content */}
      <div className="flex gap-6">
        {/* Sidebar Navigation */}
        <aside className="w-64 space-y-2">
          <Card>
            <CardContent className="p-2">
              {settingsTabs.map(tab => {
                const Icon = tab.icon
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'bg-primary text-primary-foreground'
                        : 'hover:bg-accent hover:text-accent-foreground'
                    }`}
                    aria-current={activeTab === tab.id ? 'page' : undefined}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                )
              })}
            </CardContent>
          </Card>
        </aside>

        {/* Main Content */}
        <div className="flex-1">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
            <TabsContent value="appearance" className="space-y-4 mt-0">
              <AppearanceSettings />
            </TabsContent>
            
            <TabsContent value="notifications" className="space-y-4 mt-0">
              <NotificationSettings />
            </TabsContent>
            
            <TabsContent value="display" className="space-y-4 mt-0">
              <DisplaySettings />
            </TabsContent>
            
            <TabsContent value="language" className="space-y-4 mt-0">
              <LanguageSettings />
            </TabsContent>
            
            <TabsContent value="timezone" className="space-y-4 mt-0">
              <TimezoneSettings />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </main>
  )
}