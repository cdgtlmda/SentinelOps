import { useState, useEffect, useCallback, useMemo } from 'react'
import { useAgentStore, useIncidentStore } from '@/store'
import type { 
  Activity, 
  ActivityFilter, 
  ActivityViewMode, 
  AgentActivity,
  WorkflowVisualization,
  ResourceMetrics,
  ActivityType,
  ActivitySeverity,
  WorkflowStep
} from '@/types/activity'

// Mock data generator for demo purposes
function generateMockActivities(): Activity[] {
  const activities: Activity[] = []
  const now = new Date()
  
  // Generate some mock activities
  for (let i = 0; i < 20; i++) {
    const types: ActivityType[] = [
      'agent_status_change', 'workflow_started', 'workflow_completed',
      'incident_created', 'alert_triggered', 'api_call', 'info'
    ]
    const severities: ActivitySeverity[] = ['info', 'warning', 'error', 'critical']
    
    activities.push({
      id: `activity-${i}`,
      type: types[Math.floor(Math.random() * types.length)],
      severity: severities[Math.floor(Math.random() * severities.length)],
      timestamp: new Date(now.getTime() - Math.random() * 3600000), // Last hour
      title: `Activity ${i}`,
      description: `This is a mock activity description for demo purposes`,
      metadata: {
        duration: Math.floor(Math.random() * 5000),
        retries: Math.floor(Math.random() * 3)
      }
    })
  }
  
  return activities.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
}

export function useActivity() {
  const [activities, setActivities] = useState<Activity[]>([])
  const [filter, setFilter] = useState<ActivityFilter>({})
  const [viewMode, setViewMode] = useState<ActivityViewMode>({
    view: 'timeline',
    sortBy: 'timestamp',
    sortOrder: 'desc'
  })
  const [isLoading, setIsLoading] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(5000) // 5 seconds

  const agents = useAgentStore((state) => state.agents)
  const workflows = useAgentStore((state) => state.workflows)
  const incidents = useIncidentStore((state) => state.incidents)

  // Initialize with mock data
  useEffect(() => {
    const mockActivities = generateMockActivities()
    setActivities(mockActivities)
    setIsLoading(false)
  }, [])

  // Simulate real-time updates
  useEffect(() => {
    if (refreshInterval <= 0) return

    const interval = setInterval(() => {
      // Add a new random activity
      const newActivity: Activity = {
        id: `activity-${Date.now()}`,
        type: 'info',
        severity: 'info',
        timestamp: new Date(),
        title: 'Real-time update',
        description: 'New activity detected',
        metadata: {
          source: 'real-time-monitor'
        }
      }
      
      setActivities(prev => [newActivity, ...prev].slice(0, 100)) // Keep last 100
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [refreshInterval])

  // Filter activities
  const filteredActivities = useMemo(() => {
    return activities.filter(activity => {
      if (filter.types?.length && !filter.types.includes(activity.type)) {
        return false
      }
      if (filter.severities?.length && !filter.severities.includes(activity.severity)) {
        return false
      }
      if (filter.agentIds?.length && (!activity.agentId || !filter.agentIds.includes(activity.agentId))) {
        return false
      }
      if (filter.workflowIds?.length && (!activity.workflowId || !filter.workflowIds.includes(activity.workflowId))) {
        return false
      }
      if (filter.incidentIds?.length && (!activity.incidentId || !filter.incidentIds.includes(activity.incidentId))) {
        return false
      }
      if (filter.startTime && activity.timestamp < filter.startTime) {
        return false
      }
      if (filter.endTime && activity.timestamp > filter.endTime) {
        return false
      }
      if (filter.searchTerm) {
        const searchLower = filter.searchTerm.toLowerCase()
        return (
          activity.title.toLowerCase().includes(searchLower) ||
          activity.description.toLowerCase().includes(searchLower)
        )
      }
      return true
    })
  }, [activities, filter])

  // Sort activities
  const sortedActivities = useMemo(() => {
    const sorted = [...filteredActivities]
    sorted.sort((a, b) => {
      let comparison = 0
      
      switch (viewMode.sortBy) {
        case 'timestamp':
          comparison = a.timestamp.getTime() - b.timestamp.getTime()
          break
        case 'severity':
          const severityOrder = { critical: 4, error: 3, warning: 2, info: 1 }
          comparison = severityOrder[a.severity] - severityOrder[b.severity]
          break
        case 'type':
          comparison = a.type.localeCompare(b.type)
          break
      }
      
      return viewMode.sortOrder === 'asc' ? comparison : -comparison
    })
    
    return sorted
  }, [filteredActivities, viewMode])

  // Group activities if needed
  const groupedActivities = useMemo(() => {
    if (viewMode.view !== 'grouped' || !viewMode.groupBy) {
      return null
    }

    const groups: Record<string, Activity[]> = {}
    
    sortedActivities.forEach(activity => {
      let key = 'other'
      
      switch (viewMode.groupBy) {
        case 'agent':
          key = activity.agentId || 'no-agent'
          break
        case 'workflow':
          key = activity.workflowId || 'no-workflow'
          break
        case 'incident':
          key = activity.incidentId || 'no-incident'
          break
        case 'type':
          key = activity.type
          break
      }
      
      if (!groups[key]) {
        groups[key] = []
      }
      groups[key].push(activity)
    })
    
    return groups
  }, [sortedActivities, viewMode])

  // Get agent activities
  const agentActivities = useMemo((): AgentActivity[] => {
    return agents.map(agent => {
      const agentWorkflows = workflows.filter(w => w.agentId === agent.id)
      const recentActivities = activities.filter(a => a.agentId === agent.id)
      
      let status: AgentActivity['status'] = 'idle'
      if (agent.status === 'error') status = 'error'
      else if (agent.status === 'busy') status = 'processing'
      else if (agentWorkflows.some(w => w.status === 'running')) status = 'processing'
      else if (agentWorkflows.some(w => w.status === 'completed')) status = 'completed'
      
      return {
        agentId: agent.id,
        status,
        currentTask: agentWorkflows.find(w => w.status === 'running')?.name,
        lastActionTimestamp: agent.lastHeartbeat,
        tasksCompleted: agentWorkflows.filter(w => w.status === 'completed').length,
        tasksInProgress: agentWorkflows.filter(w => w.status === 'running').length,
        errorCount: recentActivities.filter(a => a.severity === 'error').length
      }
    })
  }, [agents, workflows, activities])

  // Get workflow visualizations
  const workflowVisualizations = useMemo((): WorkflowVisualization[] => {
    return workflows.map(workflow => {
      // Generate mock steps for demo
      const steps: WorkflowStep[] = [
        {
          id: `${workflow.id}-step-1`,
          name: 'Initialize',
          status: workflow.status === 'failed' ? 'failed' : 'completed',
          startTime: workflow.startedAt,
          endTime: new Date(workflow.startedAt.getTime() + 2000),
          agentId: workflow.agentId,
          dependencies: []
        },
        {
          id: `${workflow.id}-step-2`,
          name: 'Process',
          status: workflow.status === 'running' ? 'running' : 
                 workflow.status === 'failed' ? 'skipped' : 'completed',
          startTime: new Date(workflow.startedAt.getTime() + 2000),
          agentId: workflow.agentId,
          dependencies: [`${workflow.id}-step-1`]
        },
        {
          id: `${workflow.id}-step-3`,
          name: 'Finalize',
          status: workflow.status === 'completed' ? 'completed' : 'pending',
          agentId: workflow.agentId,
          dependencies: [`${workflow.id}-step-2`]
        }
      ]
      
      const completedSteps = steps.filter(s => s.status === 'completed').length
      const progress = (completedSteps / steps.length) * 100
      
      return {
        workflowId: workflow.id,
        name: workflow.name,
        status: workflow.status,
        progress,
        steps,
        startTime: workflow.startedAt,
        endTime: workflow.completedAt,
        estimatedDuration: 10000 // 10 seconds mock
      }
    })
  }, [workflows])

  // Get resource metrics
  const resourceMetrics = useMemo((): ResourceMetrics => {
    return {
      timestamp: new Date(),
      cloudResources: {
        compute: {
          instances: agents.filter(a => a.status === 'online').length,
          vcpus: agents.filter(a => a.status === 'online').length * 2,
          memoryGB: agents.filter(a => a.status === 'online').length * 4
        },
        storage: {
          usedGB: 125,
          totalGB: 500
        },
        network: {
          ingressMbps: Math.random() * 100,
          egressMbps: Math.random() * 50
        }
      },
      apiUsage: [
        {
          provider: 'OpenAI',
          callCount: activities.filter(a => a.type === 'api_call').length,
          tokensUsed: activities.filter(a => a.type === 'api_call').length * 150,
          rateLimit: {
            limit: 10000,
            remaining: 8500,
            resetAt: new Date(Date.now() + 3600000)
          }
        }
      ],
      estimatedCost: {
        compute: agents.filter(a => a.status === 'online').length * 0.05,
        storage: 0.02,
        network: 0.01,
        api: activities.filter(a => a.type === 'api_call').length * 0.002,
        total: 0
      }
    }
  }, [agents, activities])

  // Calculate total cost
  resourceMetrics.estimatedCost.total = 
    resourceMetrics.estimatedCost.compute +
    resourceMetrics.estimatedCost.storage +
    resourceMetrics.estimatedCost.network +
    resourceMetrics.estimatedCost.api

  // Actions
  const updateFilter = useCallback((newFilter: Partial<ActivityFilter>) => {
    setFilter(prev => ({ ...prev, ...newFilter }))
  }, [])

  const updateViewMode = useCallback((newMode: Partial<ActivityViewMode>) => {
    setViewMode(prev => ({ ...prev, ...newMode }))
  }, [])

  const clearFilter = useCallback(() => {
    setFilter({})
  }, [])

  const setAutoRefresh = useCallback((interval: number) => {
    setRefreshInterval(interval)
  }, [])

  return {
    // Data
    activities: sortedActivities,
    groupedActivities,
    agentActivities,
    workflowVisualizations,
    resourceMetrics,
    
    // State
    filter,
    viewMode,
    isLoading,
    refreshInterval,
    
    // Actions
    updateFilter,
    updateViewMode,
    clearFilter,
    setAutoRefresh,
    
    // Counts
    totalCount: activities.length,
    filteredCount: filteredActivities.length
  }
}