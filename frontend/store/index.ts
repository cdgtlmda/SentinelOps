import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

// UI State Types
export interface UIState {
  // Panel visibility
  isSidebarOpen: boolean
  isNotificationPanelOpen: boolean
  isCommandPaletteOpen: boolean
  
  // Theme
  theme: 'light' | 'dark' | 'system'
  
  // View preferences
  dashboardLayout: 'grid' | 'list'
  incidentViewMode: 'timeline' | 'kanban' | 'table'
  
  // Actions
  toggleSidebar: () => void
  toggleNotificationPanel: () => void
  toggleCommandPalette: () => void
  setTheme: (theme: UIState['theme']) => void
  setDashboardLayout: (layout: UIState['dashboardLayout']) => void
  setIncidentViewMode: (mode: UIState['incidentViewMode']) => void
}

// Incident Types
export type IncidentSeverity = 'critical' | 'high' | 'medium' | 'low'
export type IncidentStatus = 'active' | 'investigating' | 'resolved' | 'closed'

export interface Incident {
  id: string
  title: string
  description: string
  severity: IncidentSeverity
  status: IncidentStatus
  createdAt: Date
  updatedAt: Date
  assignedTo?: string[]
  tags: string[]
  affectedServices: string[]
  timeline: IncidentTimelineEntry[]
}

export interface IncidentTimelineEntry {
  id: string
  timestamp: Date
  action: string
  userId: string
  details?: string
}

export interface Alert {
  id: string
  source: string
  message: string
  severity: IncidentSeverity
  timestamp: Date
  acknowledged: boolean
  incidentId?: string
}

export interface IncidentState {
  incidents: Incident[]
  alerts: Alert[]
  activeIncidentId: string | null
  
  // Actions
  addIncident: (incident: Omit<Incident, 'id' | 'createdAt' | 'updatedAt' | 'timeline'>) => void
  updateIncident: (id: string, updates: Partial<Incident>) => void
  setActiveIncident: (id: string | null) => void
  addAlert: (alert: Omit<Alert, 'id' | 'timestamp'>) => void
  acknowledgeAlert: (id: string) => void
  linkAlertToIncident: (alertId: string, incidentId: string) => void
}

// Agent Types
export type AgentStatus = 'online' | 'offline' | 'busy' | 'error'
export type WorkflowStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface Agent {
  id: string
  name: string
  type: 'remediation' | 'investigation' | 'notification' | 'custom'
  status: AgentStatus
  capabilities: string[]
  lastHeartbeat: Date
  configuration: Record<string, any>
}

export interface Workflow {
  id: string
  name: string
  agentId: string
  status: WorkflowStatus
  incidentId?: string
  startedAt: Date
  completedAt?: Date
  logs: WorkflowLog[]
}

export interface WorkflowLog {
  timestamp: Date
  level: 'info' | 'warning' | 'error'
  message: string
  metadata?: Record<string, any>
}

export interface AgentState {
  agents: Agent[]
  workflows: Workflow[]
  
  // Actions
  updateAgentStatus: (id: string, status: AgentStatus) => void
  addWorkflow: (workflow: Omit<Workflow, 'id' | 'startedAt' | 'logs'>) => void
  updateWorkflow: (id: string, updates: Partial<Workflow>) => void
  addWorkflowLog: (workflowId: string, log: Omit<WorkflowLog, 'timestamp'>) => void
}

// User Preferences
export interface UserPreferences {
  notifications: {
    email: boolean
    slack: boolean
    inApp: boolean
    severityThreshold: IncidentSeverity
  }
  dashboard: {
    defaultView: 'overview' | 'incidents' | 'agents'
    refreshInterval: number // in seconds
    showResolvedIncidents: boolean
  }
  
  // Actions
  updateNotificationPreferences: (prefs: Partial<UserPreferences['notifications']>) => void
  updateDashboardPreferences: (prefs: Partial<UserPreferences['dashboard']>) => void
}

// Store implementation
export const useUIStore = create<UIState>()(
  devtools(
    persist(
      (set) => ({
        isSidebarOpen: true,
        isNotificationPanelOpen: false,
        isCommandPaletteOpen: false,
        theme: 'system',
        dashboardLayout: 'grid',
        incidentViewMode: 'timeline',
        
        toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
        toggleNotificationPanel: () => set((state) => ({ isNotificationPanelOpen: !state.isNotificationPanelOpen })),
        toggleCommandPalette: () => set((state) => ({ isCommandPaletteOpen: !state.isCommandPaletteOpen })),
        setTheme: (theme) => set({ theme }),
        setDashboardLayout: (layout) => set({ dashboardLayout: layout }),
        setIncidentViewMode: (mode) => set({ incidentViewMode: mode }),
      }),
      {
        name: 'ui-storage',
      }
    )
  )
)

export const useIncidentStore = create<IncidentState>()(
  devtools(
    (set) => ({
      incidents: [],
      alerts: [],
      activeIncidentId: null,
      
      addIncident: (incident) => set((state) => ({
        incidents: [
          ...state.incidents,
          {
            ...incident,
            id: crypto.randomUUID(),
            createdAt: new Date(),
            updatedAt: new Date(),
            timeline: []
          }
        ]
      })),
      
      updateIncident: (id, updates) => set((state) => ({
        incidents: state.incidents.map(inc => 
          inc.id === id 
            ? { ...inc, ...updates, updatedAt: new Date() }
            : inc
        )
      })),
      
      setActiveIncident: (id) => set({ activeIncidentId: id }),
      
      addAlert: (alert) => set((state) => ({
        alerts: [
          ...state.alerts,
          {
            ...alert,
            id: crypto.randomUUID(),
            timestamp: new Date()
          }
        ]
      })),
      
      acknowledgeAlert: (id) => set((state) => ({
        alerts: state.alerts.map(alert =>
          alert.id === id ? { ...alert, acknowledged: true } : alert
        )
      })),
      
      linkAlertToIncident: (alertId, incidentId) => set((state) => ({
        alerts: state.alerts.map(alert =>
          alert.id === alertId ? { ...alert, incidentId } : alert
        )
      }))
    })
  )
)

export const useAgentStore = create<AgentState>()(
  devtools(
    (set) => ({
      agents: [],
      workflows: [],
      
      updateAgentStatus: (id, status) => set((state) => ({
        agents: state.agents.map(agent =>
          agent.id === id ? { ...agent, status, lastHeartbeat: new Date() } : agent
        )
      })),
      
      addWorkflow: (workflow) => set((state) => ({
        workflows: [
          ...state.workflows,
          {
            ...workflow,
            id: crypto.randomUUID(),
            startedAt: new Date(),
            logs: []
          }
        ]
      })),
      
      updateWorkflow: (id, updates) => set((state) => ({
        workflows: state.workflows.map(wf =>
          wf.id === id ? { ...wf, ...updates } : wf
        )
      })),
      
      addWorkflowLog: (workflowId, log) => set((state) => ({
        workflows: state.workflows.map(wf =>
          wf.id === workflowId
            ? {
                ...wf,
                logs: [...wf.logs, { ...log, timestamp: new Date() }]
              }
            : wf
        )
      }))
    })
  )
)

export const useUserPreferencesStore = create<UserPreferences>()(
  devtools(
    persist(
      (set) => ({
        notifications: {
          email: true,
          slack: false,
          inApp: true,
          severityThreshold: 'medium'
        },
        dashboard: {
          defaultView: 'overview',
          refreshInterval: 30,
          showResolvedIncidents: false
        },
        
        updateNotificationPreferences: (prefs) => set((state) => ({
          notifications: { ...state.notifications, ...prefs }
        })),
        
        updateDashboardPreferences: (prefs) => set((state) => ({
          dashboard: { ...state.dashboard, ...prefs }
        }))
      }),
      {
        name: 'user-preferences-storage',
      }
    )
  )
)