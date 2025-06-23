import React, { useState, useMemo } from 'react'
import { format } from 'date-fns'
import type { Activity, ActivityType, ActivitySeverity } from '@/types/activity'

interface ActionLogProps {
  activities: Activity[]
  onFilterChange?: (filters: { types?: ActivityType[], severities?: ActivitySeverity[] }) => void
}

export function ActionLog({ activities, onFilterChange }: ActionLogProps) {
  const [selectedTypes, setSelectedTypes] = useState<Set<ActivityType>>(new Set())
  const [selectedSeverities, setSelectedSeverities] = useState<Set<ActivitySeverity>>(new Set())
  const [searchTerm, setSearchTerm] = useState('')

  const activityTypes: ActivityType[] = [
    'agent_status_change', 'workflow_started', 'workflow_completed', 'workflow_failed',
    'incident_created', 'incident_updated', 'alert_triggered', 'resource_allocated',
    'api_call', 'error', 'info'
  ]

  const severities: ActivitySeverity[] = ['info', 'warning', 'error', 'critical']

  const getSeverityColor = (severity: ActivitySeverity) => {
    switch (severity) {
      case 'info':
        return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20'
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20'
      case 'error':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20'
      case 'critical':
        return 'text-red-800 dark:text-red-300 bg-red-100 dark:bg-red-900/40'
    }
  }

  const getTypeIcon = (type: ActivityType) => {
    switch (type) {
      case 'agent_status_change':
        return '🤖'
      case 'workflow_started':
      case 'workflow_completed':
      case 'workflow_failed':
        return '⚙️'
      case 'incident_created':
      case 'incident_updated':
        return '🚨'
      case 'alert_triggered':
        return '🔔'
      case 'resource_allocated':
        return '☁️'
      case 'api_call':
        return '🔌'
      case 'error':
        return '❌'
      case 'info':
        return 'ℹ️'
      default:
        return '📝'
    }
  }

  const toggleType = (type: ActivityType) => {
    const newTypes = new Set(selectedTypes)
    if (newTypes.has(type)) {
      newTypes.delete(type)
    } else {
      newTypes.add(type)
    }
    setSelectedTypes(newTypes)
    onFilterChange?.({
      types: newTypes.size > 0 ? Array.from(newTypes) : undefined,
      severities: selectedSeverities.size > 0 ? Array.from(selectedSeverities) : undefined
    })
  }

  const toggleSeverity = (severity: ActivitySeverity) => {
    const newSeverities = new Set(selectedSeverities)
    if (newSeverities.has(severity)) {
      newSeverities.delete(severity)
    } else {
      newSeverities.add(severity)
    }
    setSelectedSeverities(newSeverities)
    onFilterChange?.({
      types: selectedTypes.size > 0 ? Array.from(selectedTypes) : undefined,
      severities: newSeverities.size > 0 ? Array.from(newSeverities) : undefined
    })
  }

  const filteredActivities = useMemo(() => {
    return activities.filter(activity => {
      // Filter by type
      if (selectedTypes.size > 0 && !selectedTypes.has(activity.type)) {
        return false
      }
      
      // Filter by severity
      if (selectedSeverities.size > 0 && !selectedSeverities.has(activity.severity)) {
        return false
      }
      
      // Filter by search term
      if (searchTerm) {
        const search = searchTerm.toLowerCase()
        return (
          activity.title.toLowerCase().includes(search) ||
          activity.description.toLowerCase().includes(search)
        )
      }
      
      return true
    })
  }, [activities, selectedTypes, selectedSeverities, searchTerm])

  return (
    <div className="h-full flex flex-col">
      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 space-y-4">
        {/* Search */}
        <div className="relative">
          <input
            type="text"
            placeholder="Search activities..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
          />
          <svg
            className="absolute left-3 top-2.5 w-4 h-4 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>

        {/* Severity Filters */}
        <div>
          <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">Severity</p>
          <div className="flex flex-wrap gap-2">
            {severities.map((severity) => (
              <button
                key={severity}
                onClick={() => toggleSeverity(severity)}
                className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
                  selectedSeverities.has(severity)
                    ? getSeverityColor(severity)
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {severity}
              </button>
            ))}
          </div>
        </div>

        {/* Type Filters */}
        <div>
          <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">Activity Type</p>
          <div className="flex flex-wrap gap-2">
            {activityTypes.slice(0, 5).map((type) => (
              <button
                key={type}
                onClick={() => toggleType(type)}
                className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
                  selectedTypes.has(type)
                    ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {getTypeIcon(type)} {type.replace(/_/g, ' ')}
              </button>
            ))}
            <details className="relative">
              <summary className="px-3 py-1 text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-full cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-600">
                More...
              </summary>
              <div className="absolute z-10 mt-2 p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
                <div className="flex flex-col gap-1">
                  {activityTypes.slice(5).map((type) => (
                    <button
                      key={type}
                      onClick={() => toggleType(type)}
                      className={`px-3 py-1 text-xs font-medium rounded text-left hover:bg-gray-100 dark:hover:bg-gray-700 ${
                        selectedTypes.has(type)
                          ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                          : 'text-gray-600 dark:text-gray-400'
                      }`}
                    >
                      {getTypeIcon(type)} {type.replace(/_/g, ' ')}
                    </button>
                  ))}
                </div>
              </div>
            </details>
          </div>
        </div>

        {/* Results count */}
        <div className="text-xs text-gray-500 dark:text-gray-400">
          Showing {filteredActivities.length} of {activities.length} activities
        </div>
      </div>

      {/* Activity List */}
      <div className="flex-1 overflow-y-auto">
        {filteredActivities.length === 0 ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">
            No activities match your filters
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {filteredActivities.map((activity) => (
              <div
                key={activity.id}
                className="p-4 hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
              >
                <div className="flex items-start gap-3">
                  {/* Icon */}
                  <div className="flex-shrink-0 text-2xl">
                    {getTypeIcon(activity.type)}
                  </div>
                  
                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {activity.title}
                        </h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {activity.description}
                        </p>
                      </div>
                      <span className={`flex-shrink-0 px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(activity.severity)}`}>
                        {activity.severity}
                      </span>
                    </div>
                    
                    {/* Metadata */}
                    <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                      <span>{format(activity.timestamp, 'HH:mm:ss')}</span>
                      {activity.agentId && (
                        <span>Agent: {activity.agentId.slice(0, 8)}</span>
                      )}
                      {activity.workflowId && (
                        <span>Workflow: {activity.workflowId.slice(0, 8)}</span>
                      )}
                      {activity.metadata?.duration && (
                        <span>Duration: {activity.metadata.duration}ms</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}