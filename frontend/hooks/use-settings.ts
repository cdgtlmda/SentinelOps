import { useState, useCallback, useEffect } from 'react'
import { useUIStore, useUserPreferencesStore } from '@/store'
import { z } from 'zod'

// Settings validation schemas
const appearanceSchema = z.object({
  theme: z.enum(['light', 'dark', 'system']),
  colorScheme: z.string(),
  fontSize: z.number().min(12).max(20),
  uiDensity: z.enum(['compact', 'comfortable', 'spacious']),
  enableAnimations: z.boolean(),
  reduceMotion: z.boolean(),
  highContrast: z.boolean(),
})

const notificationSchema = z.object({
  email: z.boolean(),
  slack: z.boolean(),
  inApp: z.boolean(),
  severityThreshold: z.enum(['low', 'medium', 'high', 'critical']),
  emailDigest: z.object({
    enabled: z.boolean(),
    frequency: z.enum(['daily', 'weekly', 'monthly']),
    time: z.string(),
    includeResolved: z.boolean(),
  }),
  soundEnabled: z.boolean(),
  selectedSound: z.string(),
})

const displaySchema = z.object({
  dashboardLayout: z.enum(['grid', 'list']),
  defaultView: z.enum(['overview', 'incidents', 'agents']),
  incidentViewMode: z.enum(['timeline', 'kanban', 'table']),
  showResolvedIncidents: z.boolean(),
  refreshInterval: z.number().min(10).max(600),
  widgetVisibility: z.record(z.boolean()),
  chartPreferences: z.object({
    defaultChartType: z.enum(['line', 'bar', 'area', 'pie']),
    showDataLabels: z.boolean(),
    animateCharts: z.boolean(),
    colorPalette: z.enum(['default', 'colorblind', 'highContrast', 'custom']),
  }),
})

const languageSchema = z.object({
  language: z.string(),
  region: z.string(),
  dateFormat: z.string(),
  timeFormat: z.enum(['12h', '24h']),
  numberFormat: z.string(),
  currency: z.string(),
  firstDayOfWeek: z.enum(['sunday', 'monday']),
  measurementUnit: z.enum(['metric', 'imperial']),
})

const timezoneSchema = z.object({
  primaryTimezone: z.string(),
  autoDetect: z.boolean(),
  showMultipleTimezones: z.boolean(),
  additionalTimezones: z.array(z.string()),
  businessHours: z.object({
    start: z.string(),
    end: z.string(),
    workDays: z.array(z.number()),
  }),
  handleDST: z.boolean(),
})

// Combined settings schema
const settingsSchema = z.object({
  appearance: appearanceSchema,
  notifications: notificationSchema,
  display: displaySchema,
  language: languageSchema,
  timezone: timezoneSchema,
})

type Settings = z.infer<typeof settingsSchema>

interface SettingsChange {
  category: keyof Settings
  field: string
  oldValue: any
  newValue: any
  timestamp: Date
}

export function useSettings() {
  const uiStore = useUIStore()
  const preferencesStore = useUserPreferencesStore()
  
  const [changes, setChanges] = useState<SettingsChange[]>([])
  const [isSyncing, setIsSyncing] = useState(false)
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  // Get current settings from stores
  const getCurrentSettings = useCallback((): Partial<Settings> => {
    return {
      appearance: {
        theme: uiStore.theme,
        colorScheme: 'default',
        fontSize: 16,
        uiDensity: 'comfortable',
        enableAnimations: true,
        reduceMotion: false,
        highContrast: false,
      },
      notifications: {
        ...preferencesStore.notifications,
        emailDigest: {
          enabled: true,
          frequency: 'daily',
          time: '09:00',
          includeResolved: false,
        },
        soundEnabled: true,
        selectedSound: 'default',
      },
      display: {
        dashboardLayout: uiStore.dashboardLayout,
        defaultView: preferencesStore.dashboard.defaultView,
        incidentViewMode: uiStore.incidentViewMode,
        showResolvedIncidents: preferencesStore.dashboard.showResolvedIncidents,
        refreshInterval: preferencesStore.dashboard.refreshInterval,
        widgetVisibility: {},
        chartPreferences: {
          defaultChartType: 'line',
          showDataLabels: false,
          animateCharts: true,
          colorPalette: 'default',
        },
      },
      language: {
        language: 'en-US',
        region: 'US',
        dateFormat: 'MM/DD/YYYY',
        timeFormat: '12h',
        numberFormat: '1,234.56',
        currency: 'USD',
        firstDayOfWeek: 'sunday',
        measurementUnit: 'imperial',
      },
      timezone: {
        primaryTimezone: 'America/New_York',
        autoDetect: true,
        showMultipleTimezones: false,
        additionalTimezones: [],
        businessHours: {
          start: '09:00',
          end: '17:00',
          workDays: [1, 2, 3, 4, 5],
        },
        handleDST: true,
      },
    }
  }, [uiStore, preferencesStore])

  // Validate a specific setting
  const validateSetting = useCallback((category: keyof Settings, value: any): boolean => {
    try {
      const schema = {
        appearance: appearanceSchema,
        notifications: notificationSchema,
        display: displaySchema,
        language: languageSchema,
        timezone: timezoneSchema,
      }[category]

      schema.parse(value)
      setValidationErrors(prev => {
        const next = { ...prev }
        delete next[category]
        return next
      })
      return true
    } catch (error) {
      if (error instanceof z.ZodError) {
        setValidationErrors(prev => ({
          ...prev,
          [category]: error.errors[0].message
        }))
      }
      return false
    }
  }, [])

  // Track changes for undo/redo functionality
  const trackChange = useCallback((category: keyof Settings, field: string, oldValue: any, newValue: any) => {
    setChanges(prev => [...prev, {
      category,
      field,
      oldValue,
      newValue,
      timestamp: new Date()
    }])
  }, [])

  // Export settings to JSON
  const exportSettings = useCallback(async () => {
    const settings = getCurrentSettings()
    const blob = new Blob([JSON.stringify(settings, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `sentinelops-settings-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, [getCurrentSettings])

  // Import settings from JSON
  const importSettings = useCallback(async (file: File): Promise<boolean> => {
    try {
      const text = await file.text()
      const imported = JSON.parse(text)
      
      // Validate imported settings
      const validated = settingsSchema.partial().parse(imported)
      
      // Apply settings to stores
      if (validated.appearance) {
        if (validated.appearance.theme) {
          uiStore.setTheme(validated.appearance.theme)
        }
      }
      
      if (validated.notifications) {
        preferencesStore.updateNotificationPreferences(validated.notifications)
      }
      
      if (validated.display) {
        if (validated.display.dashboardLayout) {
          uiStore.setDashboardLayout(validated.display.dashboardLayout)
        }
        if (validated.display.incidentViewMode) {
          uiStore.setIncidentViewMode(validated.display.incidentViewMode)
        }
        if (validated.display.defaultView || validated.display.refreshInterval !== undefined) {
          preferencesStore.updateDashboardPreferences({
            defaultView: validated.display.defaultView,
            refreshInterval: validated.display.refreshInterval,
            showResolvedIncidents: validated.display.showResolvedIncidents,
          })
        }
      }
      
      return true
    } catch (error) {
      console.error('Failed to import settings:', error)
      return false
    }
  }, [uiStore, preferencesStore])

  // Reset to default settings
  const resetToDefaults = useCallback(() => {
    // Reset UI store
    uiStore.setTheme('system')
    uiStore.setDashboardLayout('grid')
    uiStore.setIncidentViewMode('timeline')
    
    // Reset preferences
    preferencesStore.updateNotificationPreferences({
      email: true,
      slack: false,
      inApp: true,
      severityThreshold: 'medium'
    })
    
    preferencesStore.updateDashboardPreferences({
      defaultView: 'overview',
      refreshInterval: 30,
      showResolvedIncidents: false
    })
    
    // Clear changes history
    setChanges([])
  }, [uiStore, preferencesStore])

  // Sync settings with backend
  const syncSettings = useCallback(async (): Promise<boolean> => {
    setIsSyncing(true)
    try {
      // Prepare settings data for sync
      const settingsData = {
        general: settings.general,
        notifications: settings.notifications,
        security: settings.security,
        appearance: settings.appearance,
        integrations: settings.integrations,
        advanced: settings.advanced,
        lastModified: new Date().toISOString()
      }

      // Send settings to backend API
      const response = await fetch('/api/settings/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settingsData)
      })

      if (!response.ok) {
        throw new Error(`Settings sync failed: ${response.statusText}`)
      }

      const result = await response.json()
      
      // Update last sync time
      setLastSyncTime(new Date())
      
      // Clear pending changes after successful sync
      setChanges([])
      
      return true
    } catch (error) {
      console.error('Failed to sync settings:', error)
      return false
    } finally {
      setIsSyncing(false)
    }
  }, [settings])

  // Check if settings have unsaved changes
  const hasUnsavedChanges = useCallback(() => {
    return changes.length > 0
  }, [changes])

  // Get settings diff for review
  const getSettingsDiff = useCallback(() => {
    return changes.reduce((acc, change) => {
      const key = `${change.category}.${change.field}`
      if (!acc[key]) {
        acc[key] = {
          category: change.category,
          field: change.field,
          oldValue: change.oldValue,
          newValue: change.newValue,
          changedAt: change.timestamp
        }
      }
      return acc
    }, {} as Record<string, any>)
  }, [changes])

  // Auto-sync settings periodically
  useEffect(() => {
    const interval = setInterval(() => {
      if (hasUnsavedChanges()) {
        syncSettings()
      }
    }, 60000) // Sync every minute if there are changes

    return () => clearInterval(interval)
  }, [hasUnsavedChanges, syncSettings])

  return {
    // State
    getCurrentSettings,
    changes,
    isSyncing,
    lastSyncTime,
    validationErrors,
    
    // Actions
    validateSetting,
    trackChange,
    exportSettings,
    importSettings,
    resetToDefaults,
    syncSettings,
    hasUnsavedChanges,
    getSettingsDiff,
  }
}