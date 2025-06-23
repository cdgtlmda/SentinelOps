'use client'

import { cn } from '@/lib/utils'
import { IncidentSeverity } from '@/types/incident'
import { AlertTriangle, AlertCircle, Info, AlertOctagon } from 'lucide-react'
import { useVisualAccessibility } from '@/hooks/use-visual-accessibility'

interface SeverityBadgeProps {
  severity: IncidentSeverity
  size?: 'sm' | 'md' | 'lg'
  showIcon?: boolean
  showPattern?: boolean
  className?: string
}

const severityConfig: Record<IncidentSeverity, {
  label: string
  color: string
  bgColor: string
  borderColor: string
  icon: typeof AlertTriangle
  pattern: string
  description: string
}> = {
  critical: {
    label: 'Critical',
    color: 'text-red-700 dark:text-red-400',
    bgColor: 'bg-red-50 dark:bg-red-950/50',
    borderColor: 'border-red-200 dark:border-red-800',
    icon: AlertOctagon,
    pattern: 'pattern-cross',
    description: 'Immediate action required - severe impact on operations'
  },
  high: {
    label: 'High',
    color: 'text-orange-700 dark:text-orange-400',
    bgColor: 'bg-orange-50 dark:bg-orange-950/50',
    borderColor: 'border-orange-200 dark:border-orange-800',
    icon: AlertTriangle,
    pattern: 'pattern-diagonal-stripes',
    description: 'Urgent attention needed - significant impact'
  },
  medium: {
    label: 'Medium',
    color: 'text-yellow-700 dark:text-yellow-400',
    bgColor: 'bg-yellow-50 dark:bg-yellow-950/50',
    borderColor: 'border-yellow-200 dark:border-yellow-800',
    icon: AlertCircle,
    pattern: 'pattern-dots',
    description: 'Moderate impact - should be addressed soon'
  },
  low: {
    label: 'Low',
    color: 'text-blue-700 dark:text-blue-400',
    bgColor: 'bg-blue-50 dark:bg-blue-950/50',
    borderColor: 'border-blue-200 dark:border-blue-800',
    icon: Info,
    pattern: 'pattern-horizontal-stripes',
    description: 'Minor impact - can be scheduled for resolution'
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

export function SeverityBadge({ 
  severity, 
  size = 'md', 
  showIcon = true,
  showPattern,
  className 
}: SeverityBadgeProps) {
  const { shouldShowPatterns } = useVisualAccessibility()
  const config = severityConfig[severity]
  const Icon = config.icon
  const displayPattern = showPattern ?? shouldShowPatterns()

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 font-medium rounded-md border',
        sizeClasses[size],
        config.color,
        config.bgColor,
        config.borderColor,
        displayPattern && config.pattern,
        className
      )}
      title={config.description}
      role="status"
      aria-label={`Severity: ${config.label} - ${config.description}`}
      data-severity={severity}
    >
      {showIcon && (
        <Icon className={cn(iconSizes[size], 'flex-shrink-0')} aria-hidden="true" />
      )}
      <span>{config.label}</span>
    </span>
  )
}