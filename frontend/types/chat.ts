export type MessageType = 'user' | 'agent' | 'system'

export type MessageStatus = 'sending' | 'sent' | 'delivered' | 'error'

export interface Message {
  id: string
  type: MessageType
  content: string
  timestamp: Date
  sender?: string // For agent messages
  agentId?: string // Reference to agent
  status?: MessageStatus
  attachments?: Attachment[]
  metadata?: Record<string, any>
  intent?: {
    name: string
    confidence: number
    entities?: Record<string, any>
  }
  suggestedActions?: string[]
}

export interface Attachment {
  id: string
  name: string
  type: string
  size: number
  url?: string
}

export interface Agent {
  id: string
  name: string
  type: string
  avatar?: string
  color?: string
  status: 'online' | 'offline' | 'busy' | 'error'
}

export interface ChatState {
  messages: Message[]
  activeAgents: string[]
  isTyping: boolean
  typingAgent?: string
  error?: string
}

export interface ChatCommand {
  command: string
  description: string
  icon?: string
}