import { useState, useCallback, useRef } from 'react'
import { Message } from '@/types/chat'
import { parseIntent, extractEntities, generateResponse } from '@/lib/ai-commands'

export interface IntentResult {
  intent: string
  confidence: number
  entities: Record<string, any>
  suggestedActions?: string[]
  needsClarification?: boolean
  clarificationPrompt?: string
}

export interface ConversationContext {
  id: string
  messages: Message[]
  intent: string
  entities: Record<string, any>
  relatedIncidents: string[]
  relatedAgents: string[]
  startTime: Date
  lastUpdateTime: Date
}

export function useAIChat() {
  const [currentIntent, setCurrentIntent] = useState<IntentResult | null>(null)
  const [context, setContext] = useState<ConversationContext | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const contextIdRef = useRef(0)

  // Initialize or update conversation context
  const updateContext = useCallback((message: Message, intent: IntentResult) => {
    setContext(prev => {
      if (!prev) {
        // Create new context
        contextIdRef.current += 1
        return {
          id: `ctx-${Date.now()}-${contextIdRef.current}`,
          messages: [message],
          intent: intent.intent,
          entities: intent.entities,
          relatedIncidents: [],
          relatedAgents: [],
          startTime: new Date(),
          lastUpdateTime: new Date(),
        }
      }

      // Update existing context
      const updatedContext = {
        ...prev,
        messages: [...prev.messages, message],
        lastUpdateTime: new Date(),
      }

      // Update entities (merge with existing)
      if (intent.entities) {
        updatedContext.entities = {
          ...prev.entities,
          ...intent.entities,
        }
      }

      // Extract incident IDs from entities
      if (intent.entities.incidentId && !prev.relatedIncidents.includes(intent.entities.incidentId)) {
        updatedContext.relatedIncidents = [...prev.relatedIncidents, intent.entities.incidentId]
      }

      // Extract agent references
      if (intent.entities.agentName && !prev.relatedAgents.includes(intent.entities.agentName)) {
        updatedContext.relatedAgents = [...prev.relatedAgents, intent.entities.agentName]
      }

      return updatedContext
    })
  }, [])

  // Process natural language input
  const processMessage = useCallback(async (message: string): Promise<IntentResult> => {
    setIsProcessing(true)
    
    try {
      // Parse intent from message
      const intent = await parseIntent(message, context)
      
      // Extract entities from message
      const entities = await extractEntities(message, intent.intent)
      
      // Combine results
      const result: IntentResult = {
        ...intent,
        entities,
      }
      
      // Check if clarification is needed
      if (intent.confidence < 0.6) {
        result.needsClarification = true
        result.clarificationPrompt = generateClarificationPrompt(intent, entities)
      }
      
      // Generate suggested actions based on intent
      result.suggestedActions = generateSuggestedActions(intent.intent, entities)
      
      setCurrentIntent(result)
      return result
    } finally {
      setIsProcessing(false)
    }
  }, [context])

  // Generate AI response based on intent and context
  const generateAIResponse = useCallback(async (
    message: string,
    intent: IntentResult
  ): Promise<string> => {
    // If clarification is needed, return clarification prompt
    if (intent.needsClarification) {
      return intent.clarificationPrompt || "I'm not quite sure what you're asking. Could you please clarify?"
    }

    // Generate response based on intent and context
    return await generateResponse(message, intent, context)
  }, [context])

  // Reset conversation context
  const resetContext = useCallback(() => {
    setContext(null)
    setCurrentIntent(null)
  }, [])

  // Get context summary
  const getContextSummary = useCallback((): string => {
    if (!context) return 'No active conversation'

    const duration = Math.floor((new Date().getTime() - context.startTime.getTime()) / 1000 / 60)
    const messageCount = context.messages.length

    let summary = `Conversation about ${context.intent}\n`
    summary += `Duration: ${duration} minutes\n`
    summary += `Messages: ${messageCount}\n`

    if (context.relatedIncidents.length > 0) {
      summary += `Related incidents: ${context.relatedIncidents.join(', ')}\n`
    }

    if (context.relatedAgents.length > 0) {
      summary += `Mentioned agents: ${context.relatedAgents.join(', ')}\n`
    }

    return summary
  }, [context])

  return {
    currentIntent,
    context,
    isProcessing,
    processMessage,
    generateAIResponse,
    updateContext,
    resetContext,
    getContextSummary,
  }
}

// Helper functions
function generateClarificationPrompt(intent: IntentResult, entities: Record<string, any>): string {
  const prompts = {
    'incident.create': 'Would you like to create a new incident? Please provide more details about the issue.',
    'incident.status': 'Which incident would you like to check the status of? Please provide an incident ID or description.',
    'agent.status': 'Which agent\'s status would you like to check?',
    'help': 'What would you like help with? I can assist with incidents, agents, or system status.',
  }

  return prompts[intent.intent] || 'Could you please provide more details about what you\'d like to do?'
}

function generateSuggestedActions(intent: string, entities: Record<string, any>): string[] {
  const actions: Record<string, string[]> = {
    'incident.create': [
      'Describe the issue',
      'Set priority level',
      'Assign to agent',
      'Add affected systems',
    ],
    'incident.status': [
      'View all incidents',
      'Filter by priority',
      'Check specific incident',
      'View recent updates',
    ],
    'agent.status': [
      'View all agents',
      'Check specific agent',
      'View agent workload',
      'Contact agent',
    ],
    'help': [
      'Create incident',
      'Check status',
      'View agents',
      'System overview',
    ],
  }

  return actions[intent] || ['Tell me more', 'Show examples', 'Get help']
}