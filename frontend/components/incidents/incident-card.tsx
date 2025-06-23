'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { Incident } from '@/types/incident'
import { SeverityBadge } from './severity-badge'
import { StatusBadge } from './status-badge'
import { QuickActionBar } from '@/components/actions/quick-action-bar'
import { 
  ChevronDown, 
  ChevronUp, 
  Clock, 
  User, 
  AlertTriangle,
  CheckCircle,
  Search,
  MoreVertical,
  ExternalLink,
  MessageSquare,
  Activity,
  CheckSquare
} from 'lucide-react'
import { formatDistanceToNow, format } from 'date-fns'

interface IncidentCardProps {
  incident: Incident
  view?: 'grid' | 'list'
  onAcknowledge?: (id: string) => void
  onInvestigate?: (id: string) => void
  onRemediate?: (id: string) => void
  onViewDetails?: (id: string) => void
  onActionComplete?: (action: any, result: any) => void
  isSelected?: boolean
  onToggleSelect?: (id: string) => void
  className?: string
}

export function IncidentCard({
  incident,
  view = 'grid',
  onAcknowledge,
  onInvestigate,
  onRemediate,
  onViewDetails,
  onActionComplete,
  isSelected = false,
  onToggleSelect,
  className
}: IncidentCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [isHovered, setIsHovered] = useState(false)

  const timeToResolve = incident.resolvedAt 
    ? Math.round((incident.resolvedAt.getTime() - incident.createdAt.getTime()) / 1000 / 60)
    : null

  const handleQuickAction = (e: React.MouseEvent, action: () => void) => {
    e.stopPropagation()
    action()
  }

  const cardContent = (
    <>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 truncate pr-2">
            {incident.title}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
            {incident.description}
          </p>
        </div>
        <button
          className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          aria-label="More options"
        >
          <MoreVertical className="h-4 w-4 text-gray-500" />
        </button>
      </div>

      {/* Badges */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <SeverityBadge severity={incident.severity} size="sm" />
        <StatusBadge status={incident.status} size="sm" />
        {incident.assignedTo && (
          <span className="inline-flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400">
            <User className="h-3 w-3" />
            {incident.assignedTo}
          </span>
        )}
      </div>

      {/* Timestamps */}
      <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-500 mb-3">
        <span className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {formatDistanceToNow(incident.createdAt, { addSuffix: true })}
        </span>
        {timeToResolve && (
          <span className="flex items-center gap-1">
            <Activity className="h-3 w-3" />
            Resolved in {timeToResolve}m
          </span>
        )}
      </div>

      {/* Quick Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-200 dark:border-gray-800">
        <div className="flex items-center gap-2">
          {onToggleSelect && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onToggleSelect(incident.id)
              }}
              className={cn(
                'p-2 rounded-md transition-colors',
                'hover:bg-gray-100 dark:hover:bg-gray-800',
                isSelected && 'bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400'
              )}
              aria-label={isSelected ? 'Deselect incident' : 'Select incident'}
            >
              <CheckSquare className="h-4 w-4" />
            </button>
          )}
          <QuickActionBar
            incidentIds={[incident.id]}
            variant="inline"
            onActionComplete={(action, result) => {
              // Handle action completion based on action type
              if (action.type === 'acknowledge' && onAcknowledge) {
                onAcknowledge(incident.id)
              } else if (action.type === 'investigate' && onInvestigate) {
                onInvestigate(incident.id)
              } else if (action.type === 'remediate' && onRemediate) {
                onRemediate(incident.id)
              }
              onActionComplete?.(action, result)
            }}
          />
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
          aria-expanded={isExpanded}
          aria-label={isExpanded ? 'Collapse details' : 'Expand details'}
        >
          {isExpanded ? (
            <>
              Less <ChevronUp className="h-3 w-3" />
            </>
          ) : (
            <>
              More <ChevronDown className="h-3 w-3" />
            </>
          )}
        </button>
      </div>

      {/* Expandable Details */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-800 space-y-3">
          {/* Affected Resources */}
          {incident.affectedResources.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Affected Resources ({incident.affectedResources.length})
              </h4>
              <div className="flex flex-wrap gap-1">
                {incident.affectedResources.slice(0, 3).map((resource) => (
                  <span
                    key={resource.id}
                    className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300"
                  >
                    {resource.name}
                  </span>
                ))}
                {incident.affectedResources.length > 3 && (
                  <span className="text-xs text-gray-500">
                    +{incident.affectedResources.length - 3} more
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Recent Timeline */}
          {incident.timeline.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Recent Activity
              </h4>
              <div className="space-y-1">
                {incident.timeline.slice(-2).map((event) => (
                  <div key={event.id} className="text-xs text-gray-600 dark:text-gray-400">
                    <span className="font-medium">{event.title}</span> •{' '}
                    {formatDistanceToNow(event.timestamp, { addSuffix: true })}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* View Details Link */}
          {onViewDetails && (
            <button
              onClick={(e) => handleQuickAction(e, () => onViewDetails(incident.id))}
              className="flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
            >
              View full details
              <ExternalLink className="h-3 w-3" />
            </button>
          )}
        </div>
      )}
    </>
  )

  if (view === 'list') {
    return (
      <div
        className={cn(
          'bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800',
          'p-4 transition-all duration-200',
          isHovered && 'shadow-md border-gray-300 dark:border-gray-700',
          isSelected && 'ring-2 ring-blue-500 border-blue-500',
          'cursor-pointer',
          className
        )}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={() => onViewDetails?.(incident.id)}
        role="article"
        aria-label={`Incident: ${incident.title}`}
      >
        <div className="flex items-start gap-4">
          <div className="flex-1">
            {cardContent}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div
      className={cn(
        'bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800',
        'p-4 transition-all duration-200',
        isHovered && 'shadow-md border-gray-300 dark:border-gray-700 transform -translate-y-0.5',
        isSelected && 'ring-2 ring-blue-500 border-blue-500',
        'cursor-pointer',
        className
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onViewDetails?.(incident.id)}
      role="article"
      aria-label={`Incident: ${incident.title}`}
    >
      {cardContent}
    </div>
  )
}