'use client'

import { cn } from '@/lib/utils'
import { IncidentStatus } from '@/types/incident'
import { 
  Circle, 
  CircleDot, 
  Search, 
  CheckCircle, 
  CheckCircle2, 
  XCircle,
  Clock,
  Loader2
} from 'lucide-react'
import { useVisualAccessibility } from '@/hooks/use-visual-accessibility'

interface StatusBadgeProps {
  status: IncidentStatus
  size?: 'sm' | 'md' | 'lg'
  showIcon?: boolean
  showPattern?: boolean
  animate?: boolean
  className?: string
}

const statusConfig: Record<IncidentStatus, {
  label: string
  color: string
  bgColor: string
  borderColor: string
  icon: typeof Circle
  pattern: string
  animated?: boolean
  description: string
}> = {
  new: {
    label: 'New',
    color: 'text-purple-700 dark:text-purple-400',
    bgColor: 'bg-purple-50 dark:bg-purple-950/50',
    borderColor: 'border-purple-200 dark:border-purple-800',
    icon: Circle,
    pattern: 'pattern-dots',
    animated: true,
    description: 'Newly created incident awaiting triage'
  },
  acknowledged: {
    label: 'Acknowledged',
    color: 'text-blue-700 dark:text-blue-400',
    bgColor: 'bg-blue-50 dark:bg-blue-950/50',
    borderColor: 'border-blue-200 dark:border-blue-800',
    icon: CircleDot,
    pattern: 'pattern-vertical-stripes',
    description: 'Incident has been acknowledged by team'
  },
  investigating: {
    label: 'Investigating',
    color: 'text-yellow-700 dark:text-yellow-400',
    bgColor: 'bg-yellow-50 dark:bg-yellow-950/50',
    borderColor: 'border-yellow-200 dark:border-yellow-800',
    icon: Search,
    pattern: 'pattern-diagonal-stripes',
    animated: true,
    description: 'Team is actively investigating the issue'
  },
  remediated: {
    label: 'Remediated',
    color: 'text-cyan-700 dark:text-cyan-400',
    bgColor: 'bg-cyan-50 dark:bg-cyan-950/50',
    borderColor: 'border-cyan-200 dark:border-cyan-800',
    icon: CheckCircle,
    pattern: 'pattern-horizontal-stripes',
    description: 'Issue has been fixed, monitoring for stability'
  },
  resolved: {
    label: 'Resolved',
    color: 'text-green-700 dark:text-green-400',
    bgColor: 'bg-green-50 dark:bg-green-950/50',
    borderColor: 'border-green-200 dark:border-green-800',
    icon: CheckCircle2,
    pattern: '',
    description: 'Incident has been fully resolved'
  },
  closed: {
    label: 'Closed',
    color: 'text-gray-700 dark:text-gray-400',
    bgColor: 'bg-gray-50 dark:bg-gray-950/50',
    borderColor: 'border-gray-200 dark:border-gray-800',
    icon: XCircle,
    pattern: '',
    description: 'Incident is closed and archived'
  }
}

const sizeClasses = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-1',
  lg: 'text-base px-3 py-1.5'
}

const iconSizes = {
  sm: 'h-3 w-3',
  md: 'h-4 w-4',
  lg: 'h-5 w-5'
}

export function StatusBadge({ 
  status, 
  size = 'md', 
  showIcon = true,
  showPattern,
  animate = true,
  className 
}: StatusBadgeProps) {
  const { shouldShowPatterns } = useVisualAccessibility()
  const config = statusConfig[status]
  const Icon = config.icon
  const displayPattern = showPattern ?? shouldShowPatterns()
  const shouldAnimate = animate && config.animated

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 font-medium rounded-md border',
        sizeClasses[size],
        config.color,
        config.bgColor,
        config.borderColor,
        displayPattern && config.pattern,
        shouldAnimate && 'animate-pulse',
        className
      )}
      title={config.description}
      role="status"
      aria-label={`Status: ${config.label} - ${config.description}`}
      aria-live={shouldAnimate ? 'polite' : 'off'}
      data-status={status}
    >
      {showIcon && (
        <Icon 
          className={cn(
            iconSizes[size], 
            'flex-shrink-0',
            shouldAnimate && status === 'investigating' && 'animate-spin'
          )} 
          aria-hidden="true" 
        />
      )}
      <span>{config.label}</span>
    </span>
  )
}