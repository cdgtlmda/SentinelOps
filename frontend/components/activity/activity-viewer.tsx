import React, { useState } from 'react'
import { useActivity } from '@/hooks/use-activity'
import { useAgentStore } from '@/store'
import { AgentStatus } from './agent-status'
import { WorkflowVisualizer } from './workflow-visualizer'
import { ActionLog } from './action-log'
import { ResourceMonitor } from './resource-monitor'
import type { ActivityFilter } from '@/types/activity'

type TabView = 'overview' | 'agents' | 'workflows' | 'logs' | 'resources'

export function ActivityViewer() {
  const [activeTab, setActiveTab] = useState<TabView>('overview')
  const [isMobileAccordionOpen, setIsMobileAccordionOpen] = useState<Record<TabView, boolean>>({
    overview: true,
    agents: false,
    workflows: false,
    logs: false,
    resources: false
  })
  
  const agents = useAgentStore((state) => state.agents)
  
  const {
    activities,
    agentActivities,
    workflowVisualizations,
    resourceMetrics,
    filter,
    viewMode,
    isLoading,
    refreshInterval,
    updateFilter,
    updateViewMode,
    clearFilter,
    setAutoRefresh,
    totalCount,
    filteredCount
  } = useActivity()

  const handleFilterChange = (filters: Partial<ActivityFilter>) => {
    updateFilter(filters)
  }

  const toggleAccordion = (tab: TabView) => {
    setIsMobileAccordionOpen(prev => ({
      ...prev,
      [tab]: !prev[tab]
    }))
  }

  const tabs = [
    { id: 'overview' as TabView, label: 'Overview', icon: '📊' },
    { id: 'agents' as TabView, label: 'Agents', icon: '🤖' },
    { id: 'workflows' as TabView, label: 'Workflows', icon: '⚙️' },
    { id: 'logs' as TabView, label: 'Activity Log', icon: '📝' },
    { id: 'resources' as TabView, label: 'Resources', icon: '☁️' }
  ]

  const renderContent = (view: TabView) => {
    switch (view) {
      case 'overview':
        return (
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-500 dark:text-gray-400">Total Activities</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{totalCount}</p>
              </div>
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-500 dark:text-gray-400">Active Agents</p>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {agentActivities.filter(a => a.status === 'processing').length}
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-500 dark:text-gray-400">Running Workflows</p>
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {workflowVisualizations.filter(w => w.status === 'running').length}
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-500 dark:text-gray-400">Est. Cost/Hour</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  ${(resourceMetrics.estimatedCost.total / 100).toFixed(2)}
                </p>
              </div>
            </div>

            {/* Recent Activities */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold mb-4">Recent Activities</h3>
              <div className="space-y-2">
                {activities.slice(0, 5).map((activity) => (
                  <div key={activity.id} className="flex items-center justify-between py-2 border-b last:border-0">
                    <div>
                      <p className="text-sm font-medium">{activity.title}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {activity.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      activity.severity === 'critical' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                      activity.severity === 'error' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                      activity.severity === 'warning' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
                      'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
                    }`}>
                      {activity.severity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )
      
      case 'agents':
        return <AgentStatus agents={agents} agentActivities={agentActivities} />
      
      case 'workflows':
        return <WorkflowVisualizer workflows={workflowVisualizations} />
      
      case 'logs':
        return <ActionLog activities={activities} onFilterChange={handleFilterChange} />
      
      case 'resources':
        return <ResourceMonitor metrics={resourceMetrics} />
      
      default:
        return null
    }
  }

  // Desktop tabs layout
  const desktopView = (
    <div className="hidden md:flex h-full flex-col">
      {/* Tab Headers */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex space-x-1 p-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                activeTab === tab.id
                  ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700/50'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>
      
      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {renderContent(activeTab)}
      </div>
      
      {/* Auto-refresh controls */}
      <div className="bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 px-4 py-2 flex items-center justify-between text-xs">
        <span className="text-gray-600 dark:text-gray-400">
          Auto-refresh: {refreshInterval > 0 ? `${refreshInterval / 1000}s` : 'Off'}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => setAutoRefresh(0)}
            className={`px-2 py-1 rounded ${refreshInterval === 0 ? 'bg-gray-200 dark:bg-gray-700' : 'hover:bg-gray-200 dark:hover:bg-gray-700'}`}
          >
            Off
          </button>
          <button
            onClick={() => setAutoRefresh(5000)}
            className={`px-2 py-1 rounded ${refreshInterval === 5000 ? 'bg-gray-200 dark:bg-gray-700' : 'hover:bg-gray-200 dark:hover:bg-gray-700'}`}
          >
            5s
          </button>
          <button
            onClick={() => setAutoRefresh(10000)}
            className={`px-2 py-1 rounded ${refreshInterval === 10000 ? 'bg-gray-200 dark:bg-gray-700' : 'hover:bg-gray-200 dark:hover:bg-gray-700'}`}
          >
            10s
          </button>
          <button
            onClick={() => setAutoRefresh(30000)}
            className={`px-2 py-1 rounded ${refreshInterval === 30000 ? 'bg-gray-200 dark:bg-gray-700' : 'hover:bg-gray-200 dark:hover:bg-gray-700'}`}
          >
            30s
          </button>
        </div>
      </div>
    </div>
  )

  // Mobile accordion layout
  const mobileView = (
    <div className="md:hidden h-full overflow-y-auto">
      {tabs.map((tab) => (
        <div key={tab.id} className="border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => toggleAccordion(tab.id)}
            className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            <div className="flex items-center gap-2">
              <span>{tab.icon}</span>
              <span className="font-medium">{tab.label}</span>
            </div>
            <svg
              className={`w-5 h-5 text-gray-500 transition-transform ${
                isMobileAccordionOpen[tab.id] ? 'rotate-180' : ''
              }`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {isMobileAccordionOpen[tab.id] && (
            <div className="p-4 bg-gray-50 dark:bg-gray-900">
              {renderContent(tab.id)}
            </div>
          )}
        </div>
      ))}
    </div>
  )

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <svg className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <p className="text-gray-600 dark:text-gray-400">Loading activity data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {desktopView}
      {mobileView}
    </div>
  )
}