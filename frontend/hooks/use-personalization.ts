import { useState, useEffect, useCallback } from 'react'
import { 
  PersonalizationSettings, 
  DashboardLayout, 
  SavedFilter, 
  FavoriteAction, 
  ViewPreference,
  Widget,
  DashboardWidget,
  ActionGroup
} from '@/types/personalization'

const STORAGE_KEY = 'sentinelops_personalization'

const defaultSettings: PersonalizationSettings = {
  dashboards: [],
  savedFilters: [],
  favoriteActions: [],
  actionGroups: [],
  viewPreferences: [],
  widgetLibrary: [],
  preferences: {
    autoSaveInterval: 30000, // 30 seconds
    enableSharing: true,
    enableKeyboardShortcuts: true
  }
}

export function usePersonalization() {
  const [settings, setSettings] = useState<PersonalizationSettings>(defaultSettings)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

  // Load settings from localStorage
  useEffect(() => {
    const loadSettings = () => {
      try {
        const stored = localStorage.getItem(STORAGE_KEY)
        if (stored) {
          const parsed = JSON.parse(stored)
          // Convert date strings back to Date objects
          if (parsed.dashboards) {
            parsed.dashboards = parsed.dashboards.map((d: any) => ({
              ...d,
              createdAt: new Date(d.createdAt),
              updatedAt: new Date(d.updatedAt)
            }))
          }
          if (parsed.savedFilters) {
            parsed.savedFilters = parsed.savedFilters.map((f: any) => ({
              ...f,
              createdAt: new Date(f.createdAt),
              updatedAt: new Date(f.updatedAt)
            }))
          }
          if (parsed.viewPreferences) {
            parsed.viewPreferences = parsed.viewPreferences.map((v: any) => ({
              ...v,
              createdAt: new Date(v.createdAt),
              updatedAt: new Date(v.updatedAt)
            }))
          }
          setSettings({ ...defaultSettings, ...parsed })
        }
      } catch (error) {
        console.error('Failed to load personalization settings:', error)
      } finally {
        setIsLoading(false)
      }
    }

    loadSettings()
  }, [])

  // Save settings to localStorage
  const saveSettings = useCallback(async (newSettings: PersonalizationSettings) => {
    setIsSaving(true)
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newSettings))
      setSettings(newSettings)
    } catch (error) {
      console.error('Failed to save personalization settings:', error)
      throw error
    } finally {
      setIsSaving(false)
    }
  }, [])

  // Dashboard management
  const saveDashboard = useCallback(async (dashboard: Omit<DashboardLayout, 'id' | 'createdAt' | 'updatedAt'>) => {
    const newDashboard: DashboardLayout = {
      ...dashboard,
      id: `dashboard_${Date.now()}`,
      createdAt: new Date(),
      updatedAt: new Date()
    }

    const newSettings = {
      ...settings,
      dashboards: [...settings.dashboards, newDashboard]
    }

    await saveSettings(newSettings)
    return newDashboard
  }, [settings, saveSettings])

  const updateDashboard = useCallback(async (dashboardId: string, updates: Partial<DashboardLayout>) => {
    const newSettings = {
      ...settings,
      dashboards: settings.dashboards.map(d => 
        d.id === dashboardId 
          ? { ...d, ...updates, updatedAt: new Date() }
          : d
      )
    }

    await saveSettings(newSettings)
  }, [settings, saveSettings])

  const deleteDashboard = useCallback(async (dashboardId: string) => {
    const newSettings = {
      ...settings,
      dashboards: settings.dashboards.filter(d => d.id !== dashboardId),
      activeDashboardId: settings.activeDashboardId === dashboardId ? undefined : settings.activeDashboardId
    }

    await saveSettings(newSettings)
  }, [settings, saveSettings])

  const setActiveDashboard = useCallback(async (dashboardId: string | undefined) => {
    const newSettings = {
      ...settings,
      activeDashboardId: dashboardId
    }

    await saveSettings(newSettings)
  }, [settings, saveSettings])

  // Widget management
  const addWidget = useCallback(async (dashboardId: string, widget: DashboardWidget) => {
    const dashboard = settings.dashboards.find(d => d.id === dashboardId)
    if (!dashboard) return

    const updatedDashboard = {
      ...dashboard,
      widgets: [...dashboard.widgets, widget],
      updatedAt: new Date()
    }

    await updateDashboard(dashboardId, updatedDashboard)
  }, [settings.dashboards, updateDashboard])

  const removeWidget = useCallback(async (dashboardId: string, widgetId: string) => {
    const dashboard = settings.dashboards.find(d => d.id === dashboardId)
    if (!dashboard) return

    const updatedDashboard = {
      ...dashboard,
      widgets: dashboard.widgets.filter(w => w.id !== widgetId),
      updatedAt: new Date()
    }

    await updateDashboard(dashboardId, updatedDashboard)
  }, [settings.dashboards, updateDashboard])

  const updateWidget = useCallback(async (dashboardId: string, widgetId: string, updates: Partial<DashboardWidget>) => {
    const dashboard = settings.dashboards.find(d => d.id === dashboardId)
    if (!dashboard) return

    const updatedDashboard = {
      ...dashboard,
      widgets: dashboard.widgets.map(w => 
        w.id === widgetId ? { ...w, ...updates } : w
      ),
      updatedAt: new Date()
    }

    await updateDashboard(dashboardId, updatedDashboard)
  }, [settings.dashboards, updateDashboard])

  // Filter management
  const saveFilter = useCallback(async (filter: Omit<SavedFilter, 'id' | 'createdAt' | 'updatedAt'>) => {
    const newFilter: SavedFilter = {
      ...filter,
      id: `filter_${Date.now()}`,
      createdAt: new Date(),
      updatedAt: new Date()
    }

    const newSettings = {
      ...settings,
      savedFilters: [...settings.savedFilters, newFilter]
    }

    await saveSettings(newSettings)
    return newFilter
  }, [settings, saveSettings])

  const updateFilter = useCallback(async (filterId: string, updates: Partial<SavedFilter>) => {
    const newSettings = {
      ...settings,
      savedFilters: settings.savedFilters.map(f => 
        f.id === filterId 
          ? { ...f, ...updates, updatedAt: new Date() }
          : f
      )
    }

    await saveSettings(newSettings)
  }, [settings, saveSettings])

  const deleteFilter = useCallback(async (filterId: string) => {
    const newSettings = {
      ...settings,
      savedFilters: settings.savedFilters.filter(f => f.id !== filterId)
    }

    await saveSettings(newSettings)
  }, [settings, saveSettings])

  // Favorite actions management
  const addFavoriteAction = useCallback(async (action: Omit<FavoriteAction, 'id'>) => {
    const newAction: FavoriteAction = {
      ...action,
      id: `action_${Date.now()}`
    }

    const newSettings = {
      ...settings,
      favoriteActions: [...settings.favoriteActions, newAction]
    }

    await saveSettings(newSettings)
    return newAction
  }, [settings, saveSettings])

  const removeFavoriteAction = useCallback(async (actionId: string) => {
    const newSettings = {
      ...settings,
      favoriteActions: settings.favoriteActions.filter(a => a.id !== actionId)
    }

    await saveSettings(newSettings)
  }, [settings, saveSettings])

  const updateFavoriteAction = useCallback(async (actionId: string, updates: Partial<FavoriteAction>) => {
    const newSettings = {
      ...settings,
      favoriteActions: settings.favoriteActions.map(a => 
        a.id === actionId ? { ...a, ...updates } : a
      )
    }

    await saveSettings(newSettings)
  }, [settings, saveSettings])

  // Action groups management
  const saveActionGroup = useCallback(async (group: Omit<ActionGroup, 'id'>) => {
    const newGroup: ActionGroup = {
      ...group,
      id: `group_${Date.now()}`
    }

    const newSettings = {
      ...settings,
      actionGroups: [...settings.actionGroups, newGroup]
    }

    await saveSettings(newSettings)
    return newGroup
  }, [settings, saveSettings])

  // View preferences management
  const saveViewPreference = useCallback(async (view: Omit<ViewPreference, 'id' | 'createdAt' | 'updatedAt'>) => {
    const newView: ViewPreference = {
      ...view,
      id: `view_${Date.now()}`,
      createdAt: new Date(),
      updatedAt: new Date()
    }

    const newSettings = {
      ...settings,
      viewPreferences: [...settings.viewPreferences, newView]
    }

    await saveSettings(newSettings)
    return newView
  }, [settings, saveSettings])

  const updateViewPreference = useCallback(async (viewId: string, updates: Partial<ViewPreference>) => {
    const newSettings = {
      ...settings,
      viewPreferences: settings.viewPreferences.map(v => 
        v.id === viewId 
          ? { ...v, ...updates, updatedAt: new Date() }
          : v
      )
    }

    await saveSettings(newSettings)
  }, [settings, saveSettings])

  const deleteViewPreference = useCallback(async (viewId: string) => {
    const newSettings = {
      ...settings,
      viewPreferences: settings.viewPreferences.filter(v => v.id !== viewId)
    }

    await saveSettings(newSettings)
  }, [settings, saveSettings])

  // Export/Import functionality
  const exportSettings = useCallback(() => {
    const dataStr = JSON.stringify(settings, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
    
    const exportFileDefaultName = `sentinelops_personalization_${new Date().toISOString().split('T')[0]}.json`
    
    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
  }, [settings])

  const importSettings = useCallback(async (file: File) => {
    try {
      const text = await file.text()
      const imported = JSON.parse(text)
      
      // Validate and merge with existing settings
      const mergedSettings: PersonalizationSettings = {
        ...settings,
        ...imported,
        // Merge arrays instead of replacing
        dashboards: [...settings.dashboards, ...(imported.dashboards || [])],
        savedFilters: [...settings.savedFilters, ...(imported.savedFilters || [])],
        favoriteActions: [...settings.favoriteActions, ...(imported.favoriteActions || [])],
        actionGroups: [...settings.actionGroups, ...(imported.actionGroups || [])],
        viewPreferences: [...settings.viewPreferences, ...(imported.viewPreferences || [])],
        widgetLibrary: [...settings.widgetLibrary, ...(imported.widgetLibrary || [])]
      }

      await saveSettings(mergedSettings)
    } catch (error) {
      console.error('Failed to import settings:', error)
      throw error
    }
  }, [settings, saveSettings])

  // Reset to defaults
  const resetSettings = useCallback(async () => {
    await saveSettings(defaultSettings)
  }, [saveSettings])

  return {
    settings,
    isLoading,
    isSaving,
    
    // Dashboard operations
    saveDashboard,
    updateDashboard,
    deleteDashboard,
    setActiveDashboard,
    
    // Widget operations
    addWidget,
    removeWidget,
    updateWidget,
    
    // Filter operations
    saveFilter,
    updateFilter,
    deleteFilter,
    
    // Favorite actions operations
    addFavoriteAction,
    removeFavoriteAction,
    updateFavoriteAction,
    
    // Action groups operations
    saveActionGroup,
    
    // View preferences operations
    saveViewPreference,
    updateViewPreference,
    deleteViewPreference,
    
    // Import/Export
    exportSettings,
    importSettings,
    
    // Reset
    resetSettings
  }
}