'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { Incident, TimelineEvent, RemediationStep, IncidentNote } from '@/types/incident'
import { SeverityBadge } from './severity-badge'
import { StatusBadge } from './status-badge'
import { 
  Clock, 
  User, 
  Calendar,
  AlertTriangle,
  MessageSquare,
  Activity,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Server,
  Database,
  Globe,
  Cloud,
  Cpu,
  HelpCircle,
  ExternalLink,
  Copy,
  Share2,
  Edit,
  MoreVertical,
  PlayCircle,
  RotateCcw,
  Flag
} from 'lucide-react'
import { format, formatDistanceToNow } from 'date-fns'

interface IncidentDetailsProps {
  incident: Incident
  onStatusChange?: (status: Incident['status']) => void
  onAssign?: (userId: string) => void
  onAddNote?: (note: Omit<IncidentNote, 'id' | 'timestamp'>) => void
  onExecuteRemediation?: (stepId: string) => void
  className?: string
}

export function IncidentDetails({
  incident,
  onStatusChange,
  onAssign,
  onAddNote,
  onExecuteRemediation,
  className
}: IncidentDetailsProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'timeline' | 'remediation' | 'notes'>('overview')
  const [noteContent, setNoteContent] = useState('')
  const [isInternalNote, setIsInternalNote] = useState(true)

  const resourceIcons = {
    server: Server,
    database: Database,
    service: Globe,
    network: Cloud,
    application: Cpu,
    other: HelpCircle
  }

  const timelineIcons = {
    status_change: Flag,
    action_taken: Activity,
    comment: MessageSquare,
    alert: AlertTriangle,
    automated_action: PlayCircle
  }

  const metricsData = [
    {
      label: 'Time to Acknowledge',
      value: incident.metrics.timeToAcknowledge 
        ? `${Math.round(incident.metrics.timeToAcknowledge / 60)}m`
        : 'N/A',
      icon: Clock
    },
    {
      label: 'Time to Resolve',
      value: incident.metrics.timeToResolve
        ? `${Math.round(incident.metrics.timeToResolve / 60)}m`
        : 'In Progress',
      icon: CheckCircle2
    },
    {
      label: 'Impacted Users',
      value: incident.metrics.impactedUsers?.toLocaleString() || 'Unknown',
      icon: User
    },
    {
      label: 'SLA Status',
      value: incident.metrics.slaStatus.toUpperCase(),
      icon: incident.metrics.slaStatus === 'breached' ? XCircle : CheckCircle2,
      className: incident.metrics.slaStatus === 'breached' ? 'text-red-600' : 'text-green-600'
    }
  ]

  const handleAddNote = () => {
    if (noteContent.trim() && onAddNote) {
      onAddNote({
        author: 'Current User', // In real app, this would come from auth context
        content: noteContent.trim(),
        isInternal: isInternalNote
      })
      setNoteContent('')
    }
  }

  const TabButton = ({ 
    tab, 
    label, 
    count 
  }: { 
    tab: typeof activeTab
    label: string
    count?: number 
  }) => (
    <button
      onClick={() => setActiveTab(tab)}
      className={cn(
        'px-4 py-2 text-sm font-medium transition-colors relative',
        activeTab === tab
          ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
          : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
      )}
    >
      {label}
      {count !== undefined && count > 0 && (
        <span className="ml-2 px-1.5 py-0.5 text-xs bg-gray-100 dark:bg-gray-800 rounded-full">
          {count}
        </span>
      )}
    </button>
  )

  return (
    <div className={cn('bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800', className)}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              {incident.title}
            </h1>
            <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
              <span className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                Created {format(incident.createdAt, 'MMM d, yyyy h:mm a')}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                Updated {formatDistanceToNow(incident.updatedAt, { addSuffix: true })}
              </span>
            </div>
          </div>
          <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-colors">
            <MoreVertical className="h-5 w-5" />
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <SeverityBadge severity={incident.severity} />
          <StatusBadge status={incident.status} />
          {incident.assignedTo && (
            <span className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
              <User className="h-4 w-4" />
              Assigned to {incident.assignedTo}
            </span>
          )}
          <div className="flex items-center gap-2 ml-auto">
            <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-colors" title="Copy incident ID">
              <Copy className="h-4 w-4" />
            </button>
            <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-colors" title="Share incident">
              <Share2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Bar */}
      <div className="px-6 py-4 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-800">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {metricsData.map(({ label, value, icon: Icon, className: metricClass }) => (
            <div key={label} className="flex items-center gap-3">
              <Icon className={cn('h-5 w-5 text-gray-400', metricClass)} />
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
                <p className={cn('text-sm font-medium', metricClass || 'text-gray-900 dark:text-gray-100')}>
                  {value}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-800 px-6">
        <div className="flex gap-6">
          <TabButton tab="overview" label="Overview" />
          <TabButton tab="timeline" label="Timeline" count={incident.timeline.length} />
          <TabButton tab="remediation" label="Remediation" count={incident.remediationSteps.length} />
          <TabButton tab="notes" label="Notes" count={incident.notes.length} />
        </div>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Description */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Description</h3>
              <p className="text-gray-600 dark:text-gray-400">{incident.description}</p>
            </div>

            {/* Affected Resources */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Affected Resources ({incident.affectedResources.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {incident.affectedResources.map((resource) => {
                  const Icon = resourceIcons[resource.type]
                  return (
                    <div
                      key={resource.id}
                      className="flex items-start gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700"
                    >
                      <Icon className="h-5 w-5 text-gray-400 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 dark:text-gray-100">{resource.name}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">{resource.impact}</p>
                        <span className={cn(
                          'inline-block mt-1 text-xs px-2 py-0.5 rounded-full',
                          resource.status === 'healthy' && 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
                          resource.status === 'degraded' && 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
                          resource.status === 'down' && 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
                          resource.status === 'unknown' && 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
                        )}>
                          {resource.status}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Related Alerts */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Related Alerts ({incident.alerts.length})
              </h3>
              <div className="space-y-2">
                {incident.alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800"
                  >
                    <AlertTriangle className="h-4 w-4 text-yellow-500 mt-0.5" />
                    <div className="flex-1">
                      <div className="flex items-start justify-between">
                        <p className="font-medium text-gray-900 dark:text-gray-100">{alert.name}</p>
                        <span className="text-xs text-gray-500">{format(alert.timestamp, 'h:mm a')}</span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{alert.message}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Source: {alert.source}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Tags */}
            {incident.tags.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {incident.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-md"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'timeline' && (
          <div className="space-y-4">
            {incident.timeline.map((event, index) => {
              const Icon = timelineIcons[event.type] || Activity
              return (
                <div key={event.id} className="flex gap-3">
                  <div className="relative">
                    <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-full">
                      <Icon className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                    </div>
                    {index < incident.timeline.length - 1 && (
                      <div className="absolute top-10 left-1/2 transform -translate-x-1/2 w-0.5 h-16 bg-gray-200 dark:bg-gray-700" />
                    )}
                  </div>
                  <div className="flex-1 pb-8">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-gray-900 dark:text-gray-100">{event.title}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{event.description}</p>
                        {event.actor && (
                          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">By {event.actor}</p>
                        )}
                      </div>
                      <span className="text-xs text-gray-500 whitespace-nowrap">
                        {formatDistanceToNow(event.timestamp, { addSuffix: true })}
                      </span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {activeTab === 'remediation' && (
          <div className="space-y-4">
            {incident.remediationSteps.map((step) => (
              <div
                key={step.id}
                className={cn(
                  'p-4 rounded-lg border',
                  step.status === 'completed' && 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800',
                  step.status === 'in_progress' && 'bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800',
                  step.status === 'failed' && 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800',
                  step.status === 'pending' && 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700',
                  step.status === 'skipped' && 'bg-gray-100 dark:bg-gray-800 border-gray-300 dark:border-gray-600'
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500">Step {step.order}</span>
                      {step.automatable && (
                        <span className="px-2 py-0.5 text-xs bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded-full">
                          Automatable
                        </span>
                      )}
                    </div>
                    <h4 className="font-medium text-gray-900 dark:text-gray-100 mt-1">{step.title}</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{step.description}</p>
                    
                    {step.result && (
                      <div className="mt-2 p-2 bg-white dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700">
                        <p className="text-xs text-gray-600 dark:text-gray-400">{step.result}</p>
                      </div>
                    )}

                    <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                      {step.estimatedDuration && (
                        <span>Est. {step.estimatedDuration}m</span>
                      )}
                      {step.actualDuration && (
                        <span>Actual: {step.actualDuration}m</span>
                      )}
                      {step.completedBy && (
                        <span>Completed by {step.completedBy}</span>
                      )}
                    </div>
                  </div>

                  {step.status === 'pending' && step.automatable && onExecuteRemediation && (
                    <button
                      onClick={() => onExecuteRemediation(step.id)}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                      <PlayCircle className="h-4 w-4" />
                      Execute
                    </button>
                  )}

                  {step.status === 'in_progress' && (
                    <div className="animate-spin">
                      <RotateCcw className="h-5 w-5 text-blue-600" />
                    </div>
                  )}

                  {step.status === 'completed' && (
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                  )}

                  {step.status === 'failed' && (
                    <XCircle className="h-5 w-5 text-red-600" />
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'notes' && (
          <div className="space-y-4">
            {/* Add Note Form */}
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <textarea
                value={noteContent}
                onChange={(e) => setNoteContent(e.target.value)}
                placeholder="Add a note..."
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                rows={3}
              />
              <div className="flex items-center justify-between mt-3">
                <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                  <input
                    type="checkbox"
                    checked={isInternalNote}
                    onChange={(e) => setIsInternalNote(e.target.checked)}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  Internal note
                </label>
                <button
                  onClick={handleAddNote}
                  disabled={!noteContent.trim()}
                  className={cn(
                    'px-4 py-2 text-sm rounded-md transition-colors',
                    noteContent.trim()
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  )}
                >
                  Add Note
                </button>
              </div>
            </div>

            {/* Notes List */}
            <div className="space-y-3">
              {incident.notes.map((note) => (
                <div
                  key={note.id}
                  className={cn(
                    'p-4 rounded-lg',
                    note.isInternal
                      ? 'bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-800'
                      : 'bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-sm text-gray-900 dark:text-gray-100">
                          {note.author}
                        </span>
                        {note.isInternal && (
                          <span className="px-2 py-0.5 text-xs bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300 rounded">
                            Internal
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{note.content}</p>
                    </div>
                    <span className="text-xs text-gray-500 whitespace-nowrap">
                      {formatDistanceToNow(note.timestamp, { addSuffix: true })}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}