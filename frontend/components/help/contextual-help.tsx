'use client'

import { useState, useEffect, ReactNode } from 'react'
import { usePathname } from 'next/navigation'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { 
  HelpCircle, 
  Lightbulb, 
  AlertCircle,
  Info,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  BookOpen,
  Video,
  MessageSquare,
  Sparkles,
  X
} from 'lucide-react'

interface HelpContent {
  id: string
  type: 'tip' | 'warning' | 'info' | 'suggestion'
  title: string
  content: string | ReactNode
  actions?: Array<{
    label: string
    onClick: () => void
    variant?: 'default' | 'outline' | 'ghost'
  }>
  learnMoreUrl?: string
  relatedTopics?: string[]
  priority?: 'high' | 'medium' | 'low'
}

interface PageHelpConfig {
  path: string | RegExp
  content: HelpContent[]
  quickActions?: Array<{
    label: string
    icon: React.ElementType
    onClick: () => void
  }>
}

const PAGE_HELP_CONFIGS: PageHelpConfig[] = [
  {
    path: '/dashboard',
    content: [
      {
        id: 'dashboard-overview',
        type: 'info',
        title: 'Dashboard Overview',
        content: 'This dashboard provides a real-time view of your security posture. Monitor incidents, agent activities, and system health at a glance.',
        relatedTopics: ['incidents', 'agents', 'metrics']
      },
      {
        id: 'dashboard-tip',
        type: 'tip',
        title: 'Pro Tip: Customize Your View',
        content: 'You can rearrange widgets and save custom dashboard layouts. Click the settings icon to get started.',
        actions: [
          {
            label: 'Customize Dashboard',
            onClick: () => console.log('Open dashboard customization'),
            variant: 'outline'
          }
        ]
      }
    ],
    quickActions: [
      {
        label: 'View Tutorial',
        icon: Video,
        onClick: () => console.log('Start dashboard tutorial')
      },
      {
        label: 'Keyboard Shortcuts',
        icon: BookOpen,
        onClick: () => console.log('Show keyboard shortcuts')
      }
    ]
  },
  {
    path: /^\/incidents/,
    content: [
      {
        id: 'incident-severity',
        type: 'info',
        title: 'Understanding Severity Levels',
        content: (
          <div className="space-y-2">
            <p className="text-sm">Incidents are categorized by severity:</p>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Badge variant="destructive">Critical</Badge>
                <span className="text-xs">Immediate action required</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="destructive" className="bg-orange-500">High</Badge>
                <span className="text-xs">Significant impact</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="secondary">Medium</Badge>
                <span className="text-xs">Moderate impact</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline">Low</Badge>
                <span className="text-xs">Minor impact</span>
              </div>
            </div>
          </div>
        ),
        priority: 'high'
      },
      {
        id: 'incident-actions',
        type: 'suggestion',
        title: 'Quick Actions Available',
        content: 'You can acknowledge, escalate, or remediate incidents directly from this view. Use keyboard shortcuts for faster response.',
        actions: [
          {
            label: 'View Shortcuts',
            onClick: () => console.log('Show incident shortcuts')
          }
        ]
      }
    ]
  },
  {
    path: '/agents',
    content: [
      {
        id: 'agent-types',
        type: 'info',
        title: 'AI Agent Types',
        content: (
          <div className="space-y-2 text-sm">
            <p>SentinelOps uses specialized AI agents:</p>
            <ul className="space-y-1 ml-4">
              <li>• <strong>Detection</strong>: Monitors for threats</li>
              <li>• <strong>Analysis</strong>: Investigates incidents</li>
              <li>• <strong>Remediation</strong>: Executes fixes</li>
              <li>• <strong>Communication</strong>: Sends notifications</li>
            </ul>
          </div>
        ),
        learnMoreUrl: '/docs/agents'
      },
      {
        id: 'agent-collaboration',
        type: 'tip',
        title: 'Agent Collaboration',
        content: 'Agents work together automatically. The orchestrator coordinates their activities for efficient incident response.',
        priority: 'medium'
      }
    ]
  }
]

interface ContextualHelpProps {
  className?: string
  position?: 'fixed' | 'relative'
  defaultExpanded?: boolean
  showQuickActions?: boolean
}

export function ContextualHelp({ 
  className = '',
  position = 'fixed',
  defaultExpanded = false,
  showQuickActions = true
}: ContextualHelpProps) {
  const pathname = usePathname()
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)
  const [dismissedHelp, setDismissedHelp] = useState<Set<string>>(
    new Set(JSON.parse(localStorage.getItem('dismissedHelp') || '[]'))
  )
  const [activeHelp, setActiveHelp] = useState<HelpContent[]>([])
  const [quickActions, setQuickActions] = useState<PageHelpConfig['quickActions']>([])

  useEffect(() => {
    // Find matching help config for current page
    const config = PAGE_HELP_CONFIGS.find(cfg => {
      if (typeof cfg.path === 'string') {
        return pathname === cfg.path
      }
      return cfg.path.test(pathname)
    })

    if (config) {
      // Filter out dismissed help items
      const visibleHelp = config.content.filter(
        item => !dismissedHelp.has(item.id)
      )
      
      // Sort by priority
      const sortedHelp = visibleHelp.sort((a, b) => {
        const priorityOrder = { high: 0, medium: 1, low: 2 }
        const aPriority = priorityOrder[a.priority || 'medium']
        const bPriority = priorityOrder[b.priority || 'medium']
        return aPriority - bPriority
      })

      setActiveHelp(sortedHelp)
      setQuickActions(config.quickActions)
    } else {
      setActiveHelp([])
      setQuickActions([])
    }
  }, [pathname, dismissedHelp])

  const handleDismiss = (helpId: string) => {
    const newDismissed = new Set([...dismissedHelp, helpId])
    setDismissedHelp(newDismissed)
    localStorage.setItem('dismissedHelp', JSON.stringify([...newDismissed]))
  }

  const handleResetDismissed = () => {
    setDismissedHelp(new Set())
    localStorage.removeItem('dismissedHelp')
  }

  if (activeHelp.length === 0 && (!quickActions || quickActions.length === 0)) {
    return null
  }

  const getIcon = (type: HelpContent['type']) => {
    switch (type) {
      case 'tip':
        return Lightbulb
      case 'warning':
        return AlertCircle
      case 'info':
        return Info
      case 'suggestion':
        return Sparkles
    }
  }

  const getIconColor = (type: HelpContent['type']) => {
    switch (type) {
      case 'tip':
        return 'text-yellow-600 dark:text-yellow-400'
      case 'warning':
        return 'text-orange-600 dark:text-orange-400'
      case 'info':
        return 'text-blue-600 dark:text-blue-400'
      case 'suggestion':
        return 'text-purple-600 dark:text-purple-400'
    }
  }

  const containerClasses = position === 'fixed' 
    ? 'fixed bottom-4 right-4 z-40 w-80'
    : 'relative w-full'

  return (
    <div className={`${containerClasses} ${className}`}>
      <Card className="shadow-lg">
        {/* Header */}
        <div className="p-3 border-b">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <HelpCircle className="h-4 w-4" />
              <span className="font-medium text-sm">Quick Help</span>
              {activeHelp.length > 0 && (
                <Badge variant="secondary" className="text-xs">
                  {activeHelp.length}
                </Badge>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
            </Button>
          </div>
        </div>

        <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
          <CollapsibleContent>
            {/* Quick Actions */}
            {showQuickActions && quickActions && quickActions.length > 0 && (
              <div className="p-3 border-b">
                <div className="flex gap-2">
                  {quickActions.map((action, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      size="sm"
                      onClick={action.onClick}
                      className="flex-1"
                    >
                      <action.icon className="h-4 w-4 mr-1" />
                      {action.label}
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {/* Help Content */}
            <div className="max-h-96 overflow-y-auto">
              {activeHelp.map((item, index) => {
                const Icon = getIcon(item.type)
                const iconColor = getIconColor(item.type)

                return (
                  <div
                    key={item.id}
                    className={`p-3 ${index !== activeHelp.length - 1 ? 'border-b' : ''}`}
                  >
                    <div className="space-y-2">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-2">
                          <Icon className={`h-4 w-4 mt-0.5 ${iconColor}`} />
                          <div className="flex-1">
                            <h4 className="text-sm font-medium">{item.title}</h4>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDismiss(item.id)}
                          className="h-6 w-6 p-0"
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>

                      <div className="text-sm text-gray-600 dark:text-gray-400 ml-6">
                        {item.content}
                      </div>

                      {/* Actions */}
                      {(item.actions || item.learnMoreUrl || item.relatedTopics) && (
                        <div className="ml-6 space-y-2">
                          {item.actions && (
                            <div className="flex gap-2">
                              {item.actions.map((action, actionIndex) => (
                                <Button
                                  key={actionIndex}
                                  variant={action.variant || 'outline'}
                                  size="sm"
                                  onClick={action.onClick}
                                >
                                  {action.label}
                                </Button>
                              ))}
                            </div>
                          )}

                          {item.learnMoreUrl && (
                            <a
                              href={item.learnMoreUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400"
                            >
                              Learn more
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          )}

                          {item.relatedTopics && item.relatedTopics.length > 0 && (
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-gray-500">Related:</span>
                              <div className="flex gap-1">
                                {item.relatedTopics.map((topic) => (
                                  <Badge key={topic} variant="outline" className="text-xs">
                                    {topic}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Footer */}
            {dismissedHelp.size > 0 && (
              <div className="p-3 border-t bg-gray-50 dark:bg-gray-900">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleResetDismissed}
                  className="w-full text-xs"
                >
                  Show all tips ({dismissedHelp.size} hidden)
                </Button>
              </div>
            )}
          </CollapsibleContent>
        </Collapsible>
      </Card>
    </div>
  )
}

// Smart help button that shows relevant help for current context
export function SmartHelpButton({ className }: { className?: string }) {
  const pathname = usePathname()
  const [showHelp, setShowHelp] = useState(false)
  const [hasRelevantHelp, setHasRelevantHelp] = useState(false)

  useEffect(() => {
    // Check if there's help content for current page
    const hasHelp = PAGE_HELP_CONFIGS.some(cfg => {
      if (typeof cfg.path === 'string') {
        return pathname === cfg.path
      }
      return cfg.path.test(pathname)
    })
    setHasRelevantHelp(hasHelp)
  }, [pathname])

  if (!hasRelevantHelp) return null

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setShowHelp(!showHelp)}
        className={className}
      >
        <HelpCircle className="h-4 w-4" />
        <span className="ml-1">Help</span>
        <Badge variant="secondary" className="ml-1 text-xs">
          <Sparkles className="h-3 w-3" />
        </Badge>
      </Button>

      {showHelp && (
        <ContextualHelp
          position="fixed"
          defaultExpanded={true}
        />
      )}
    </>
  )
}

// Help beacon for drawing attention to help content
export function HelpBeacon({ 
  targetSelector,
  content,
  onDismiss
}: {
  targetSelector: string
  content: HelpContent
  onDismiss?: () => void
}) {
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null)

  useEffect(() => {
    const element = document.querySelector(targetSelector)
    if (element) {
      const rect = element.getBoundingClientRect()
      setPosition({
        top: rect.top + rect.height / 2,
        left: rect.right + 10
      })
    }
  }, [targetSelector])

  if (!position) return null

  return (
    <div
      className="fixed z-50 animate-pulse"
      style={{ top: position.top, left: position.left }}
    >
      <div className="relative">
        <div className="absolute -inset-1 bg-blue-500 rounded-full opacity-75 blur"></div>
        <div className="relative bg-blue-500 rounded-full p-2">
          <HelpCircle className="h-4 w-4 text-white" />
        </div>
      </div>
    </div>
  )
}