export interface Widget {
  id: string
  type: 'chart' | 'activity' | 'incidents' | 'agents' | 'chat' | 'custom'
  title: string
  description?: string
  icon?: string
  defaultSize: {
    w: number
    h: number
    minW?: number
    minH?: number
    maxW?: number
    maxH?: number
  }
  config?: Record<string, any>
  category?: string
  tags?: string[]
}

export interface DashboardLayout {
  id: string
  name: string
  description?: string
  widgets: DashboardWidget[]
  gridCols?: number
  gridRows?: number
  isDefault?: boolean
  isShared?: boolean
  createdAt: Date
  updatedAt: Date
  createdBy?: string
  tags?: string[]
}

export interface DashboardWidget {
  id: string
  widgetId: string
  x: number
  y: number
  w: number
  h: number
  config?: Record<string, any>
}

export interface SavedFilter {
  id: string
  name: string
  description?: string
  filter: Record<string, any>
  entityType: 'incidents' | 'agents' | 'activities' | 'all'
  isDefault?: boolean
  isShared?: boolean
  category?: string
  tags?: string[]
  createdAt: Date
  updatedAt: Date
}

export interface FavoriteAction {
  id: string
  actionId: string
  actionType: string
  label: string
  icon?: string
  shortcut?: string
  groupId?: string
  order: number
  config?: Record<string, any>
}

export interface ActionGroup {
  id: string
  name: string
  icon?: string
  actions: string[] // action IDs
  order: number
}

export interface ViewPreference {
  id: string
  name: string
  description?: string
  viewType: 'dashboard' | 'incidents' | 'agents' | 'analytics' | 'custom'
  state: Record<string, any>
  isDefault?: boolean
  isShared?: boolean
  createdAt: Date
  updatedAt: Date
}

export interface PersonalizationSettings {
  dashboards: DashboardLayout[]
  activeDashboardId?: string
  savedFilters: SavedFilter[]
  favoriteActions: FavoriteAction[]
  actionGroups: ActionGroup[]
  viewPreferences: ViewPreference[]
  widgetLibrary: Widget[]
  preferences: {
    defaultDashboardId?: string
    autoSaveInterval?: number
    enableSharing?: boolean
    enableKeyboardShortcuts?: boolean
  }
}

export interface WidgetTemplate {
  id: string
  name: string
  description: string
  thumbnail?: string
  widgets: Widget[]
  layout: Omit<DashboardLayout, 'id' | 'createdAt' | 'updatedAt'>
  category?: string
  tags?: string[]
}

export interface PersonalizationAction {
  type: 
    | 'ADD_WIDGET'
    | 'REMOVE_WIDGET'
    | 'UPDATE_WIDGET'
    | 'MOVE_WIDGET'
    | 'RESIZE_WIDGET'
    | 'SAVE_LAYOUT'
    | 'LOAD_LAYOUT'
    | 'SAVE_FILTER'
    | 'DELETE_FILTER'
    | 'ADD_FAVORITE'
    | 'REMOVE_FAVORITE'
    | 'SAVE_VIEW'
    | 'LOAD_VIEW'
  payload: any
  timestamp: Date
}