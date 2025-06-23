import React, { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Sparkles, 
  ArrowRight, 
  MessageSquare,
  Zap,
  TrendingUp,
  Clock,
  CheckCircle2
} from 'lucide-react'

interface SuggestedAction {
  id: string
  text: string
  icon?: React.ReactNode
  category: 'quick-reply' | 'action' | 'question' | 'command'
  confidence?: number
  metadata?: Record<string, any>
}

interface SuggestedActionsProps {
  actions: string[]
  intent?: string
  onActionSelect: (action: string) => void
  onLearnFromSelection?: (action: string, selected: boolean) => void
  className?: string
  showPredictions?: boolean
}

export function SuggestedActions({
  actions,
  intent,
  onActionSelect,
  onLearnFromSelection,
  className,
  showPredictions = true,
}: SuggestedActionsProps) {
  const [suggestedActions, setSuggestedActions] = useState<SuggestedAction[]>([])
  const [recentlyUsed, setRecentlyUsed] = useState<string[]>([])
  const [isLearning, setIsLearning] = useState(false)

  // Convert string actions to SuggestedAction objects
  useEffect(() => {
    const categorizedActions = actions.map((action, index) => ({
      id: `action-${index}-${Date.now()}`,
      text: action,
      icon: getActionIcon(action, intent),
      category: categorizeAction(action),
      confidence: 0.7 + Math.random() * 0.3, // Simulated confidence
    }))

    setSuggestedActions(categorizedActions)
  }, [actions, intent])

  // Handle action selection
  const handleActionClick = (action: SuggestedAction) => {
    onActionSelect(action.text)
    
    // Track selection for learning
    if (onLearnFromSelection) {
      setIsLearning(true)
      onLearnFromSelection(action.text, true)
      
      // Update recently used
      setRecentlyUsed(prev => {
        const updated = [action.text, ...prev.filter(a => a !== action.text)]
        return updated.slice(0, 5) // Keep only 5 most recent
      })

      // Visual feedback
      setTimeout(() => setIsLearning(false), 1000)
    }
  }

  // Group actions by category
  const groupedActions = suggestedActions.reduce((groups, action) => {
    const category = action.category
    if (!groups[category]) {
      groups[category] = []
    }
    groups[category].push(action)
    return groups
  }, {} as Record<string, SuggestedAction[]>)

  const categoryTitles = {
    'quick-reply': 'Quick Replies',
    'action': 'Suggested Actions',
    'question': 'Follow-up Questions',
    'command': 'Commands',
  }

  const categoryIcons = {
    'quick-reply': <MessageSquare className="h-3 w-3" />,
    'action': <Zap className="h-3 w-3" />,
    'question': <MessageSquare className="h-3 w-3" />,
    'command': <ArrowRight className="h-3 w-3" />,
  }

  if (suggestedActions.length === 0) {
    return null
  }

  return (
    <Card className={cn('mb-4', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <CardTitle className="text-sm font-medium">Suggested Actions</CardTitle>
          </div>
          {isLearning && (
            <Badge variant="secondary" className="text-xs gap-1">
              <TrendingUp className="h-3 w-3" />
              Learning
            </Badge>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        {/* Recently Used Section */}
        {recentlyUsed.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center gap-1 mb-2">
              <Clock className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Recently Used</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {recentlyUsed.slice(0, 3).map((action, index) => (
                <Button
                  key={`recent-${index}`}
                  variant="secondary"
                  size="sm"
                  onClick={() => onActionSelect(action)}
                  className="text-xs h-7 gap-1"
                >
                  <CheckCircle2 className="h-3 w-3" />
                  {action}
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* Categorized Actions */}
        <div className="space-y-3">
          {Object.entries(groupedActions).map(([category, categoryActions]) => (
            <div key={category}>
              <div className="flex items-center gap-1 mb-2">
                {categoryIcons[category as keyof typeof categoryIcons]}
                <span className="text-xs text-muted-foreground">
                  {categoryTitles[category as keyof typeof categoryTitles]}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {categoryActions.map(action => (
                  <Button
                    key={action.id}
                    variant="outline"
                    size="sm"
                    onClick={() => handleActionClick(action)}
                    className="text-xs h-7 gap-1 group hover:border-primary"
                  >
                    {action.icon}
                    {action.text}
                    {showPredictions && action.confidence && action.confidence > 0.8 && (
                      <Badge variant="secondary" className="ml-1 px-1 py-0 text-[10px]">
                        {Math.round(action.confidence * 100)}%
                      </Badge>
                    )}
                  </Button>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* AI Prediction Indicator */}
        {showPredictions && (
          <div className="mt-3 pt-3 border-t">
            <p className="text-[10px] text-muted-foreground flex items-center gap-1">
              <Sparkles className="h-3 w-3" />
              AI-powered suggestions based on context and past interactions
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Helper function to get appropriate icon for action
function getActionIcon(action: string, intent?: string): React.ReactNode {
  const lowerAction = action.toLowerCase()
  
  if (lowerAction.includes('create') || lowerAction.includes('new')) {
    return <span>➕</span>
  }
  if (lowerAction.includes('check') || lowerAction.includes('status')) {
    return <span>📊</span>
  }
  if (lowerAction.includes('help') || lowerAction.includes('guide')) {
    return <span>❓</span>
  }
  if (lowerAction.includes('assign')) {
    return <span>👤</span>
  }
  if (lowerAction.includes('priority')) {
    return <span>🔴</span>
  }
  if (lowerAction.includes('close') || lowerAction.includes('resolve')) {
    return <span>✅</span>
  }
  
  // Intent-based icons
  if (intent?.includes('incident')) {
    return <span>🚨</span>
  }
  if (intent?.includes('agent')) {
    return <span>🤖</span>
  }
  
  return null
}

// Helper function to categorize actions
function categorizeAction(action: string): SuggestedAction['category'] {
  const lowerAction = action.toLowerCase()
  
  // Commands (start with /)
  if (action.startsWith('/')) {
    return 'command'
  }
  
  // Questions
  if (lowerAction.includes('?') || 
      lowerAction.startsWith('what') || 
      lowerAction.startsWith('how') ||
      lowerAction.startsWith('when') ||
      lowerAction.startsWith('where') ||
      lowerAction.startsWith('why')) {
    return 'question'
  }
  
  // Quick replies (short responses)
  if (action.split(' ').length <= 3) {
    return 'quick-reply'
  }
  
  // Default to action
  return 'action'
}