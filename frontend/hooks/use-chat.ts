import { useState, useCallback, useRef, useEffect } from 'react'
import { Message, MessageType, ChatState, ChatCommand } from '@/types/chat'
import { useAgentStore } from '@/store'

const CHAT_COMMANDS: ChatCommand[] = [
  { command: '/help', description: 'Show available commands', icon: '❓' },
  { command: '/clear', description: 'Clear chat history', icon: '🗑️' },
  { command: '/status', description: 'Show agent status', icon: '📊' },
  { command: '/incident', description: 'Report a new incident', icon: '🚨' },
  { command: '/agents', description: 'List available agents', icon: '🤖' },
]

export function useChat() {
  const [state, setState] = useState<ChatState>({
    messages: [],
    activeAgents: [],
    isTyping: false,
  })
  
  const messageIdCounter = useRef(0)
  const typingTimeoutRef = useRef<NodeJS.Timeout>()
  const agents = useAgentStore((state) => state.agents)
  
  // Generate unique message ID
  const generateMessageId = useCallback(() => {
    messageIdCounter.current += 1
    return `msg-${Date.now()}-${messageIdCounter.current}`
  }, [])
  
  // Add message to chat
  const addMessage = useCallback((
    type: MessageType,
    content: string,
    sender?: string,
    agentId?: string
  ) => {
    const message: Message = {
      id: generateMessageId(),
      type,
      content,
      timestamp: new Date(),
      sender,
      agentId,
      status: type === 'user' ? 'sending' : 'sent',
    }
    
    setState(prev => ({
      ...prev,
      messages: [...prev.messages, message],
    }))
    
    // Update message status after a short delay
    if (type === 'user') {
      setTimeout(() => {
        setState(prev => ({
          ...prev,
          messages: prev.messages.map(msg =>
            msg.id === message.id ? { ...msg, status: 'sent' } : msg
          ),
        }))
      }, 300)
    }
    
    return message
  }, [generateMessageId])
  
  // Send user message
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return
    
    // Handle commands
    if (content.startsWith('/')) {
      const command = content.split(' ')[0].toLowerCase()
      
      switch (command) {
        case '/clear':
          setState(prev => ({ ...prev, messages: [] }))
          addMessage('system', 'Chat history cleared')
          return
          
        case '/help':
          const helpText = CHAT_COMMANDS
            .map(cmd => `${cmd.icon} ${cmd.command} - ${cmd.description}`)
            .join('\n')
          addMessage('system', `Available commands:\n${helpText}`)
          return
          
        case '/status':
          const onlineAgents = agents.filter(a => a.status === 'online')
          const statusText = `Agents online: ${onlineAgents.length}/${agents.length}`
          addMessage('system', statusText)
          return
          
        case '/agents':
          const agentList = agents
            .map(a => `• ${a.name} (${a.type}) - ${a.status}`)
            .join('\n')
          addMessage('system', `Available agents:\n${agentList || 'No agents available'}`)
          return
          
        case '/incident':
          addMessage('system', '🚨 To report an incident, use the Incidents page from the main navigation')
          return
          
        default:
          addMessage('system', `Unknown command: ${command}. Type /help for available commands`)
          return
      }
    }
    
    // Add user message
    const userMessage = addMessage('user', content)
    
    // Simulate agent response with AI enhancements
    setState(prev => ({ ...prev, isTyping: true, typingAgent: 'AI Assistant' }))
    
    // Clear any existing typing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current)
    }
    
    // Simulate typing delay
    typingTimeoutRef.current = setTimeout(() => {
      setState(prev => ({ ...prev, isTyping: false, typingAgent: undefined }))
      
      // Get a random online agent or use default
      const onlineAgents = agents.filter(a => a.status === 'online')
      const respondingAgent = onlineAgents.length > 0
        ? onlineAgents[Math.floor(Math.random() * onlineAgents.length)]
        : null
      
      // Generate response based on content
      let response = ''
      if (content.toLowerCase().includes('hello') || content.toLowerCase().includes('hi')) {
        response = `Hello! I'm ${respondingAgent?.name || 'AI Assistant'}. How can I help you today?`
      } else if (content.toLowerCase().includes('incident')) {
        response = 'I can help you with incident management. Would you like to create a new incident or check the status of existing ones?'
      } else if (content.toLowerCase().includes('help')) {
        response = 'I\'m here to help! You can ask me about incidents, agent status, or use commands like /help to see what I can do.'
      } else {
        response = `I understand you're asking about "${content}". Let me help you with that.`
      }
      
      addMessage(
        'agent',
        response,
        respondingAgent?.name || 'AI Assistant',
        respondingAgent?.id
      )
    }, 1000 + Math.random() * 1000) // 1-2 second delay
  }, [agents, addMessage])
  
  // Get command suggestions
  const getCommandSuggestions = useCallback((input: string) => {
    if (!input.startsWith('/')) return []
    
    const searchTerm = input.toLowerCase()
    return CHAT_COMMANDS.filter(cmd =>
      cmd.command.toLowerCase().startsWith(searchTerm)
    )
  }, [])
  
  // Clear chat
  const clearChat = useCallback(() => {
    setState(prev => ({ ...prev, messages: [] }))
  }, [])
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current)
      }
    }
  }, [])
  
  return {
    messages: state.messages,
    isTyping: state.isTyping,
    typingAgent: state.typingAgent,
    error: state.error,
    sendMessage,
    clearChat,
    getCommandSuggestions,
    commands: CHAT_COMMANDS,
  }
}