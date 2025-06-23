import React from 'react'
import { format } from 'date-fns'
import type { WorkflowVisualization, WorkflowStep } from '@/types/activity'

interface WorkflowVisualizerProps {
  workflows: WorkflowVisualization[]
}

export function WorkflowVisualizer({ workflows }: WorkflowVisualizerProps) {
  const getStepStatusColor = (status: WorkflowStep['status']) => {
    switch (status) {
      case 'pending':
        return 'bg-gray-200 dark:bg-gray-700'
      case 'running':
        return 'bg-blue-500 animate-pulse'
      case 'completed':
        return 'bg-green-500'
      case 'failed':
        return 'bg-red-500'
      case 'skipped':
        return 'bg-gray-400 dark:bg-gray-600'
      default:
        return 'bg-gray-200 dark:bg-gray-700'
    }
  }

  const getWorkflowStatusColor = (status: WorkflowVisualization['status']) => {
    switch (status) {
      case 'pending':
        return 'text-gray-600 dark:text-gray-400'
      case 'running':
        return 'text-blue-600 dark:text-blue-400'
      case 'completed':
        return 'text-green-600 dark:text-green-400'
      case 'failed':
        return 'text-red-600 dark:text-red-400'
      default:
        return 'text-gray-600 dark:text-gray-400'
    }
  }

  const renderWorkflowTimeline = (workflow: WorkflowVisualization) => {
    const steps = workflow.steps
    
    return (
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-4 top-8 bottom-0 w-0.5 bg-gray-300 dark:bg-gray-600" />
        
        {/* Steps */}
        <div className="space-y-6">
          {steps.map((step, index) => (
            <div key={step.id} className="relative flex items-start">
              {/* Step indicator */}
              <div className={`relative z-10 flex items-center justify-center w-8 h-8 rounded-full ${getStepStatusColor(step.status)}`}>
                {step.status === 'running' ? (
                  <svg className="w-4 h-4 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                ) : step.status === 'completed' ? (
                  <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : step.status === 'failed' ? (
                  <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                ) : (
                  <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
                    {index + 1}
                  </span>
                )}
              </div>
              
              {/* Step content */}
              <div className="ml-4 flex-1">
                <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-gray-100">
                        {step.name}
                      </h4>
                      {step.startTime && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                          Started: {format(step.startTime, 'HH:mm:ss')}
                          {step.endTime && (
                            <span className="ml-2">
                              Duration: {Math.round((step.endTime.getTime() - step.startTime.getTime()) / 1000)}s
                            </span>
                          )}
                        </p>
                      )}
                    </div>
                    <span className={`text-xs font-medium capitalize ${getWorkflowStatusColor(step.status as any)}`}>
                      {step.status}
                    </span>
                  </div>
                  
                  {step.error && (
                    <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded text-sm text-red-600 dark:text-red-400">
                      {step.error}
                    </div>
                  )}
                  
                  {/* Dependencies */}
                  {step.dependencies.length > 0 && (
                    <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                      Depends on: {step.dependencies.length} step{step.dependencies.length > 1 ? 's' : ''}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (workflows.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        No active workflows
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {workflows.map((workflow) => (
        <div
          key={workflow.workflowId}
          className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6"
        >
          {/* Workflow Header */}
          <div className="mb-4">
            <div className="flex items-start justify-between mb-2">
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                  {workflow.name}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  ID: {workflow.workflowId}
                </p>
              </div>
              <span className={`text-sm font-medium capitalize ${getWorkflowStatusColor(workflow.status)}`}>
                {workflow.status}
              </span>
            </div>
            
            {/* Progress Bar */}
            <div className="mt-3">
              <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
                <span>Progress</span>
                <span>{Math.round(workflow.progress)}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${
                    workflow.status === 'failed' ? 'bg-red-500' :
                    workflow.status === 'completed' ? 'bg-green-500' :
                    'bg-blue-500'
                  }`}
                  style={{ width: `${workflow.progress}%` }}
                />
              </div>
            </div>
            
            {/* Timing Info */}
            <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500 dark:text-gray-400">Started:</span>
                <span className="ml-2 text-gray-900 dark:text-gray-100">
                  {format(workflow.startTime, 'HH:mm:ss')}
                </span>
              </div>
              {workflow.endTime && (
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Completed:</span>
                  <span className="ml-2 text-gray-900 dark:text-gray-100">
                    {format(workflow.endTime, 'HH:mm:ss')}
                  </span>
                </div>
              )}
              {workflow.estimatedDuration && !workflow.endTime && (
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Est. Duration:</span>
                  <span className="ml-2 text-gray-900 dark:text-gray-100">
                    {Math.round(workflow.estimatedDuration / 1000)}s
                  </span>
                </div>
              )}
            </div>
          </div>
          
          {/* Timeline */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
              Workflow Steps
            </h4>
            {renderWorkflowTimeline(workflow)}
          </div>
        </div>
      ))}
    </div>
  )
}