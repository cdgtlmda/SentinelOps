import React from 'react'
import { format } from 'date-fns'
import type { AgentActivity } from '@/types/activity'
import type { Agent } from '@/store'

interface AgentStatusProps {
  agents: Agent[]
  agentActivities: AgentActivity[]
}

export function AgentStatus({ agents, agentActivities }: AgentStatusProps) {
  const getStatusColor = (status: AgentActivity['status']) => {
    switch (status) {
      case 'idle':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
      case 'processing':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
      case 'waiting':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
      case 'error':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
    }
  }

  const getStatusIcon = (status: AgentActivity['status']) => {
    switch (status) {
      case 'idle':
        return (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        )
      case 'processing':
        return (
          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )
      case 'waiting':
        return (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'error':
        return (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'completed':
        return (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {agents.map((agent) => {
          const activity = agentActivities.find(a => a.agentId === agent.id)
          if (!activity) return null

          return (
            <div
              key={agent.id}
              className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow"
            >
              {/* Agent Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    {agent.name}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                    {agent.type} Agent
                  </p>
                </div>
                <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${getStatusColor(activity.status)}`}>
                  {getStatusIcon(activity.status)}
                  <span className="capitalize">{activity.status}</span>
                </div>
              </div>

              {/* Current Task */}
              {activity.currentTask && (
                <div className="mb-3 p-2 bg-gray-50 dark:bg-gray-900 rounded">
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Current Task</p>
                  <p className="text-sm text-gray-900 dark:text-gray-100 font-medium">
                    {activity.currentTask}
                  </p>
                </div>
              )}

              {/* Stats */}
              <div className="grid grid-cols-3 gap-2 mb-3">
                <div className="text-center">
                  <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {activity.tasksCompleted}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Completed</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-semibold text-blue-600 dark:text-blue-400">
                    {activity.tasksInProgress}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">In Progress</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-semibold text-red-600 dark:text-red-400">
                    {activity.errorCount}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Errors</p>
                </div>
              </div>

              {/* Last Action */}
              <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Last action: {format(activity.lastActionTimestamp, 'HH:mm:ss')}
                </p>
              </div>

              {/* Capabilities */}
              {agent.capabilities.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1">
                  {agent.capabilities.slice(0, 3).map((capability, index) => (
                    <span
                      key={index}
                      className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded"
                    >
                      {capability}
                    </span>
                  ))}
                  {agent.capabilities.length > 3 && (
                    <span className="px-2 py-0.5 text-xs text-gray-500 dark:text-gray-400">
                      +{agent.capabilities.length - 3} more
                    </span>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Summary Stats */}
      <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Total Agents</p>
            <p className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              {agents.length}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Active</p>
            <p className="text-xl font-semibold text-green-600 dark:text-green-400">
              {agentActivities.filter(a => a.status === 'processing').length}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Idle</p>
            <p className="text-xl font-semibold text-gray-600 dark:text-gray-400">
              {agentActivities.filter(a => a.status === 'idle').length}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Errors</p>
            <p className="text-xl font-semibold text-red-600 dark:text-red-400">
              {agentActivities.filter(a => a.status === 'error').length}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}