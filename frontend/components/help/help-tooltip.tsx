'use client'

import { ReactNode, useState } from 'react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { Button } from '@/components/ui/button'
import { 
  HelpCircle, 
  Info, 
  Lightbulb,
  Keyboard,
  MousePointer,
  Video,
  ExternalLink,
  BookOpen
} from 'lucide-react'

interface HelpTooltipProps {
  children: ReactNode
  content: string | ReactNode
  title?: string
  shortcut?: string
  learnMoreUrl?: string
  videoUrl?: string
  showIcon?: boolean
  side?: 'top' | 'right' | 'bottom' | 'left'
  align?: 'start' | 'center' | 'end'
  delayDuration?: number
  className?: string
}

interface TooltipSection {
  icon?: ReactNode
  label: string
  value: string | ReactNode
}

export function HelpTooltip({
  children,
  content,
  title,
  shortcut,
  learnMoreUrl,
  videoUrl,
  showIcon = false,
  side = 'top',
  align = 'center',
  delayDuration = 300,
  className
}: HelpTooltipProps) {
  const [open, setOpen] = useState(false)

  const sections: TooltipSection[] = []
  
  if (shortcut) {
    sections.push({
      icon: <Keyboard className="h-3 w-3" />,
      label: 'Shortcut',
      value: shortcut
    })
  }

  const hasExtras = shortcut || learnMoreUrl || videoUrl

  return (
    <TooltipProvider delayDuration={delayDuration}>
      <Tooltip open={open} onOpenChange={setOpen}>
        <TooltipTrigger asChild>
          <span className={`inline-flex items-center gap-1 ${className || ''}`}>
            {children}
            {showIcon && (
              <HelpCircle className="h-3 w-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" />
            )}
          </span>
        </TooltipTrigger>
        <TooltipContent 
          side={side} 
          align={align}
          className="max-w-sm"
        >
          <div className="space-y-2">
            {title && (
              <div className="font-semibold flex items-center gap-1">
                <Info className="h-3 w-3" />
                {title}
              </div>
            )}
            
            <div className="text-sm">
              {content}
            </div>

            {hasExtras && (
              <div className="border-t pt-2 mt-2 space-y-1">
                {sections.map((section, index) => (
                  <div key={index} className="flex items-center gap-2 text-xs">
                    {section.icon}
                    <span className="text-gray-500">{section.label}:</span>
                    <span className="font-mono">{section.value}</span>
                  </div>
                ))}
                
                {(learnMoreUrl || videoUrl) && (
                  <div className="flex gap-2 mt-2">
                    {learnMoreUrl && (
                      <a
                        href={learnMoreUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-blue-500 hover:text-blue-600"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <BookOpen className="h-3 w-3" />
                        Learn more
                        <ExternalLink className="h-2 w-2" />
                      </a>
                    )}
                    {videoUrl && (
                      <a
                        href={videoUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-blue-500 hover:text-blue-600"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Video className="h-3 w-3" />
                        Watch video
                        <ExternalLink className="h-2 w-2" />
                      </a>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

// Specialized tooltip for keyboard shortcuts
export function ShortcutTooltip({
  children,
  keys,
  description,
  className
}: {
  children: ReactNode
  keys: string[]
  description?: string
  className?: string
}) {
  const isMac = typeof window !== 'undefined' && navigator.platform.toUpperCase().indexOf('MAC') >= 0
  
  const formatKey = (key: string) => {
    if (key === 'cmd' || key === 'meta') return isMac ? '⌘' : 'Ctrl'
    if (key === 'alt') return isMac ? '⌥' : 'Alt'
    if (key === 'shift') return isMac ? '⇧' : 'Shift'
    if (key === 'ctrl') return 'Ctrl'
    if (key === 'enter') return '↵'
    if (key === 'tab') return '⇥'
    if (key === 'escape' || key === 'esc') return 'Esc'
    if (key === 'space') return 'Space'
    if (key === 'backspace') return '⌫'
    if (key === 'delete') return 'Del'
    if (key === 'up') return '↑'
    if (key === 'down') return '↓'
    if (key === 'left') return '←'
    if (key === 'right') return '→'
    return key.toUpperCase()
  }

  const shortcut = keys.map(formatKey).join(' + ')

  return (
    <HelpTooltip
      content={
        <div className="space-y-1">
          {description && <div>{description}</div>}
          <div className="flex items-center gap-1">
            <Keyboard className="h-3 w-3" />
            <span className="font-mono text-xs">{shortcut}</span>
          </div>
        </div>
      }
      className={className}
    >
      {children}
    </HelpTooltip>
  )
}

// Interactive tooltip with actions
export function InteractiveTooltip({
  children,
  content,
  actions,
  className
}: {
  children: ReactNode
  content: string | ReactNode
  actions?: Array<{
    label: string
    onClick: () => void
    variant?: 'default' | 'outline' | 'ghost'
  }>
  className?: string
}) {
  const [open, setOpen] = useState(false)

  return (
    <TooltipProvider>
      <Tooltip open={open} onOpenChange={setOpen}>
        <TooltipTrigger asChild>
          <span className={className}>
            {children}
          </span>
        </TooltipTrigger>
        <TooltipContent className="max-w-sm">
          <div className="space-y-2">
            <div className="text-sm">{content}</div>
            {actions && actions.length > 0 && (
              <div className="flex gap-2 pt-2 border-t">
                {actions.map((action, index) => (
                  <Button
                    key={index}
                    variant={action.variant || 'outline'}
                    size="sm"
                    onClick={() => {
                      action.onClick()
                      setOpen(false)
                    }}
                  >
                    {action.label}
                  </Button>
                ))}
              </div>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

// Feature introduction tooltip
export function FeatureTooltip({
  children,
  featureName,
  description,
  isNew = false,
  isBeta = false,
  className
}: {
  children: ReactNode
  featureName: string
  description: string
  isNew?: boolean
  isBeta?: boolean
  className?: string
}) {
  return (
    <HelpTooltip
      title={
        <div className="flex items-center gap-2">
          <Lightbulb className="h-3 w-3" />
          {featureName}
          {isNew && (
            <span className="px-1.5 py-0.5 text-xs bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300 rounded">
              NEW
            </span>
          )}
          {isBeta && (
            <span className="px-1.5 py-0.5 text-xs bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300 rounded">
              BETA
            </span>
          )}
        </div>
      }
      content={description}
      className={className}
    >
      {children}
    </HelpTooltip>
  )
}

// Contextual help provider
export function HelpProvider({ children }: { children: ReactNode }) {
  return (
    <TooltipProvider delayDuration={300}>
      {children}
    </TooltipProvider>
  )
}