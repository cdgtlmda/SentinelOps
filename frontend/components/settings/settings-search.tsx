"use client"

import { useState, useMemo, useEffect } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Search, 
  Clock, 
  Star, 
  ChevronRight,
  Settings,
  Palette,
  Bell,
  Monitor,
  Globe,
  Hash,
  Calendar,
  Volume2,
  Webhook,
  Layout,
  Eye,
  RefreshCw,
  BarChart3
} from 'lucide-react'

interface SettingItem {
  id: string
  title: string
  description: string
  category: string
  keywords: string[]
  icon: React.ComponentType<{ className?: string }>
  path: string
}

interface SearchResult extends SettingItem {
  score: number
  matches: string[]
}

interface SettingsSearchProps {
  onNavigate: (tab: string) => void
}

export default function SettingsSearch({ onNavigate }: SettingsSearchProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearchFocused, setIsSearchFocused] = useState(false)
  const [recentSearches, setRecentSearches] = useState<string[]>([])
  const [selectedIndex, setSelectedIndex] = useState(0)

  const allSettings: SettingItem[] = [
    // Appearance Settings
    {
      id: 'theme',
      title: 'Theme',
      description: 'Choose between light, dark, or system theme',
      category: 'appearance',
      keywords: ['theme', 'dark', 'light', 'mode', 'color', 'appearance'],
      icon: Palette,
      path: 'appearance'
    },
    {
      id: 'color-scheme',
      title: 'Color Scheme',
      description: 'Customize the interface color palette',
      category: 'appearance',
      keywords: ['color', 'scheme', 'palette', 'primary', 'custom'],
      icon: Palette,
      path: 'appearance'
    },
    {
      id: 'font-size',
      title: 'Font Size',
      description: 'Adjust text size throughout the interface',
      category: 'appearance',
      keywords: ['font', 'size', 'text', 'typography', 'scale'],
      icon: Settings,
      path: 'appearance'
    },
    {
      id: 'animations',
      title: 'Animations',
      description: 'Enable or disable interface animations',
      category: 'appearance',
      keywords: ['animation', 'motion', 'effects', 'transitions'],
      icon: Settings,
      path: 'appearance'
    },

    // Notification Settings
    {
      id: 'email-notifications',
      title: 'Email Notifications',
      description: 'Configure email alert preferences',
      category: 'notifications',
      keywords: ['email', 'notifications', 'alerts', 'messages'],
      icon: Bell,
      path: 'notifications'
    },
    {
      id: 'slack-integration',
      title: 'Slack Integration',
      description: 'Set up Slack notifications',
      category: 'notifications',
      keywords: ['slack', 'integration', 'webhook', 'chat'],
      icon: Bell,
      path: 'notifications'
    },
    {
      id: 'notification-sounds',
      title: 'Notification Sounds',
      description: 'Customize alert sounds',
      category: 'notifications',
      keywords: ['sound', 'audio', 'alert', 'notification', 'volume'],
      icon: Volume2,
      path: 'notifications'
    },
    {
      id: 'webhooks',
      title: 'Webhooks',
      description: 'Configure custom webhook integrations',
      category: 'notifications',
      keywords: ['webhook', 'api', 'integration', 'custom'],
      icon: Webhook,
      path: 'notifications'
    },

    // Display Settings
    {
      id: 'dashboard-layout',
      title: 'Dashboard Layout',
      description: 'Choose between grid or list view',
      category: 'display',
      keywords: ['dashboard', 'layout', 'grid', 'list', 'view'],
      icon: Layout,
      path: 'display'
    },
    {
      id: 'widget-visibility',
      title: 'Widget Visibility',
      description: 'Show or hide dashboard widgets',
      category: 'display',
      keywords: ['widget', 'visibility', 'show', 'hide', 'dashboard'],
      icon: Eye,
      path: 'display'
    },
    {
      id: 'refresh-interval',
      title: 'Refresh Interval',
      description: 'Set data refresh frequency',
      category: 'display',
      keywords: ['refresh', 'interval', 'update', 'frequency', 'auto'],
      icon: RefreshCw,
      path: 'display'
    },
    {
      id: 'chart-preferences',
      title: 'Chart Preferences',
      description: 'Customize chart appearance',
      category: 'display',
      keywords: ['chart', 'graph', 'visualization', 'data'],
      icon: BarChart3,
      path: 'display'
    },

    // Language Settings
    {
      id: 'language',
      title: 'Language',
      description: 'Select your preferred language',
      category: 'language',
      keywords: ['language', 'locale', 'translation', 'i18n'],
      icon: Globe,
      path: 'language'
    },
    {
      id: 'date-format',
      title: 'Date Format',
      description: 'Choose date display format',
      category: 'language',
      keywords: ['date', 'format', 'calendar', 'time'],
      icon: Calendar,
      path: 'language'
    },
    {
      id: 'number-format',
      title: 'Number Format',
      description: 'Set number and currency format',
      category: 'language',
      keywords: ['number', 'format', 'currency', 'decimal'],
      icon: Hash,
      path: 'language'
    },

    // Timezone Settings
    {
      id: 'timezone',
      title: 'Time Zone',
      description: 'Set your primary time zone',
      category: 'timezone',
      keywords: ['timezone', 'time', 'zone', 'clock', 'region'],
      icon: Clock,
      path: 'timezone'
    },
    {
      id: 'business-hours',
      title: 'Business Hours',
      description: 'Define working hours',
      category: 'timezone',
      keywords: ['business', 'hours', 'working', 'schedule'],
      icon: Clock,
      path: 'timezone'
    },
  ]

  const popularSettings = [
    'theme',
    'email-notifications',
    'dashboard-layout',
    'timezone',
    'language'
  ]

  // Load recent searches from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('settings-recent-searches')
    if (stored) {
      setRecentSearches(JSON.parse(stored))
    }
  }, [])

  // Fuzzy search implementation
  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return []

    const query = searchQuery.toLowerCase()
    const results: SearchResult[] = []

    allSettings.forEach(setting => {
      let score = 0
      const matches: string[] = []

      // Title match (highest priority)
      if (setting.title.toLowerCase().includes(query)) {
        score += 10
        matches.push('title')
      }

      // Description match
      if (setting.description.toLowerCase().includes(query)) {
        score += 5
        matches.push('description')
      }

      // Keywords match
      setting.keywords.forEach(keyword => {
        if (keyword.includes(query)) {
          score += 3
          matches.push(`keyword: ${keyword}`)
        }
      })

      // Category match
      if (setting.category.includes(query)) {
        score += 2
        matches.push('category')
      }

      if (score > 0) {
        results.push({ ...setting, score, matches })
      }
    })

    // Sort by score (highest first)
    return results.sort((a, b) => b.score - a.score)
  }, [searchQuery])

  const handleSearch = (value: string) => {
    setSearchQuery(value)
    if (value.trim()) {
      setSelectedIndex(0)
    }
  }

  const handleSelectSetting = (setting: SettingItem) => {
    // Add to recent searches
    const newRecent = [setting.title, ...recentSearches.filter(s => s !== setting.title)].slice(0, 5)
    setRecentSearches(newRecent)
    localStorage.setItem('settings-recent-searches', JSON.stringify(newRecent))

    // Navigate to setting
    onNavigate(setting.path)
    setSearchQuery('')
    setIsSearchFocused(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!searchResults.length) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => Math.min(prev + 1, searchResults.length - 1))
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => Math.max(prev - 1, 0))
        break
      case 'Enter':
        e.preventDefault()
        if (searchResults[selectedIndex]) {
          handleSelectSetting(searchResults[selectedIndex])
        }
        break
      case 'Escape':
        e.preventDefault()
        setSearchQuery('')
        setIsSearchFocused(false)
        break
    }
  }

  const popularSettingsItems = allSettings.filter(s => popularSettings.includes(s.id))

  return (
    <div className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search settings..."
          value={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
          onFocus={() => setIsSearchFocused(true)}
          onBlur={() => setTimeout(() => setIsSearchFocused(false), 200)}
          onKeyDown={handleKeyDown}
          className="pl-10 pr-4"
        />
      </div>

      {/* Search Results Dropdown */}
      {isSearchFocused && (searchQuery || recentSearches.length > 0 || popularSettings.length > 0) && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-background border rounded-lg shadow-lg z-50">
          <ScrollArea className="max-h-96">
            {searchQuery && searchResults.length > 0 ? (
              <div className="p-2">
                <div className="text-xs font-medium text-muted-foreground px-2 py-1">
                  Search Results
                </div>
                {searchResults.map((result, index) => {
                  const Icon = result.icon
                  return (
                    <button
                      key={result.id}
                      onClick={() => handleSelectSetting(result)}
                      className={`w-full flex items-center gap-3 p-2 rounded-md hover:bg-accent transition-colors text-left ${
                        index === selectedIndex ? 'bg-accent' : ''
                      }`}
                    >
                      <Icon className="w-4 h-4 text-muted-foreground shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm">{result.title}</div>
                        <div className="text-xs text-muted-foreground truncate">
                          {result.description}
                        </div>
                      </div>
                      <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" />
                    </button>
                  )
                })}
              </div>
            ) : searchQuery ? (
              <div className="p-8 text-center text-muted-foreground">
                No settings found for "{searchQuery}"
              </div>
            ) : (
              <>
                {/* Recent Searches */}
                {recentSearches.length > 0 && (
                  <div className="p-2 border-b">
                    <div className="text-xs font-medium text-muted-foreground px-2 py-1 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Recent
                    </div>
                    {recentSearches.map(search => {
                      const setting = allSettings.find(s => s.title === search)
                      if (!setting) return null
                      const Icon = setting.icon
                      return (
                        <button
                          key={search}
                          onClick={() => handleSelectSetting(setting)}
                          className="w-full flex items-center gap-3 p-2 rounded-md hover:bg-accent transition-colors text-left"
                        >
                          <Icon className="w-4 h-4 text-muted-foreground" />
                          <span className="text-sm">{search}</span>
                        </button>
                      )
                    })}
                  </div>
                )}

                {/* Popular Settings */}
                <div className="p-2">
                  <div className="text-xs font-medium text-muted-foreground px-2 py-1 flex items-center gap-1">
                    <Star className="w-3 h-3" />
                    Popular
                  </div>
                  {popularSettingsItems.map(setting => {
                    const Icon = setting.icon
                    return (
                      <button
                        key={setting.id}
                        onClick={() => handleSelectSetting(setting)}
                        className="w-full flex items-center gap-3 p-2 rounded-md hover:bg-accent transition-colors text-left"
                      >
                        <Icon className="w-4 h-4 text-muted-foreground" />
                        <div className="flex-1 text-left">
                          <div className="font-medium text-sm">{setting.title}</div>
                          <div className="text-xs text-muted-foreground">
                            {setting.description}
                          </div>
                        </div>
                        <Badge variant="secondary" className="text-xs">
                          {setting.category}
                        </Badge>
                      </button>
                    )
                  })}
                </div>
              </>
            )}
          </ScrollArea>
        </div>
      )}
    </div>
  )
}