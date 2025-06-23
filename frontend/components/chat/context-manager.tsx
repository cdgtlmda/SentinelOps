import React from 'react'
import { cn } from '@/lib/utils'
import { ConversationContext } from '@/hooks/use-ai-chat'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  RotateCcw, 
  MessageSquare, 
  Clock, 
  AlertCircle, 
  Users,
  Link,
  ChevronDown,
  ChevronUp
} from 'lucide-react'

interface ContextManagerProps {
  context: ConversationContext | null
  onReset: () => void
  className?: string
}

export function ContextManager({ context, onReset, className }: ContextManagerProps) {
  const [isExpanded, setIsExpanded] = React.useState(false)

  if (!context) {
    return null
  }

  const duration = Math.floor((new Date().getTime() - context.startTime.getTime()) / 1000 / 60)
  const messageCount = context.messages.length

  return (
    <Card className={cn('mb-4', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-sm font-medium">Conversation Context</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="h-8 w-8 p-0"
            >
              {isExpanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onReset}
              className="h-8 gap-1"
            >
              <RotateCcw className="h-3 w-3" />
              Reset
            </Button>
          </div>
        </div>
        <CardDescription className="text-xs mt-1">
          Tracking: {context.intent.replace('.', ' ').replace(/_/g, ' ')}
        </CardDescription>
      </CardHeader>
      
      <CardContent className="pt-0">
        {/* Summary Stats */}
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>{duration} min</span>
          </div>
          <div className="flex items-center gap-1">
            <MessageSquare className="h-3 w-3" />
            <span>{messageCount} messages</span>
          </div>
        </div>

        {/* Expanded Context Details */}
        {isExpanded && (
          <div className="mt-4 space-y-3">
            {/* Entities */}
            {Object.keys(context.entities).length > 0 && (
              <div>
                <h4 className="text-xs font-medium mb-2">Detected Information</h4>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(context.entities).map(([key, value]) => (
                    <Badge key={key} variant="secondary" className="text-xs">
                      {formatEntityName(key)}: {formatEntityValue(value)}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Related Incidents */}
            {context.relatedIncidents.length > 0 && (
              <div>
                <h4 className="text-xs font-medium mb-2 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  Related Incidents
                </h4>
                <div className="space-y-1">
                  {context.relatedIncidents.map(incidentId => (
                    <a
                      key={incidentId}
                      href={`/incidents/${incidentId}`}
                      className="flex items-center gap-1 text-xs text-primary hover:underline"
                    >
                      <Link className="h-3 w-3" />
                      {incidentId}
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Related Agents */}
            {context.relatedAgents.length > 0 && (
              <div>
                <h4 className="text-xs font-medium mb-2 flex items-center gap-1">
                  <Users className="h-3 w-3" />
                  Mentioned Agents
                </h4>
                <div className="flex flex-wrap gap-1">
                  {context.relatedAgents.map(agent => (
                    <Badge key={agent} variant="outline" className="text-xs">
                      @{agent}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Context Summary */}
            <div className="pt-2 border-t">
              <p className="text-xs text-muted-foreground">
                This conversation started {duration} minutes ago about {formatIntent(context.intent)}.
                {context.relatedIncidents.length > 0 && 
                  ` It references ${context.relatedIncidents.length} incident${context.relatedIncidents.length > 1 ? 's' : ''}.`
                }
                {context.relatedAgents.length > 0 && 
                  ` ${context.relatedAgents.length} agent${context.relatedAgents.length > 1 ? 's have' : ' has'} been mentioned.`
                }
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Helper functions to format entity names and values
function formatEntityName(name: string): string {
  return name
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, str => str.toUpperCase())
    .trim()
}

function formatEntityValue(value: any): string {
  if (Array.isArray(value)) {
    return value.join(', ')
  }
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}

function formatIntent(intent: string): string {
  return intent
    .split('.')
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
    .replace(/_/g, ' ')
}