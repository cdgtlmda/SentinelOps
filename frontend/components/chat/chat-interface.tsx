import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react'
import { cn } from '@/lib/utils'
import { useChat } from '@/hooks/use-chat'
import { useAIChat } from '@/hooks/use-ai-chat'
import { Message } from './message'
import { ChatInput } from './chat-input'
import { ContextManager } from './context-manager'
import { SuggestedActions } from './suggested-actions'
import { AutoComplete, useAutoComplete } from './auto-complete'
import { CommandPalette, useCommandPalette } from './command-palette'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Brain, Sparkles, AlertCircle } from 'lucide-react'

interface ChatInterfaceProps {
  className?: string
}

// Memoized quick command button component
const QuickCommandButton = React.memo(({ 
  command, 
  icon, 
  onClick 
}: { 
  command: string
  icon: React.ReactNode
  onClick: (command: string) => void 
}) => (
  <button
    onClick={() => onClick(command)}
    className="text-xs px-3 py-1.5 bg-muted hover:bg-muted/80 rounded-full transition-colors flex items-center gap-1"
  >
    <span>{icon}</span>
    <span>{command}</span>
  </button>
))
QuickCommandButton.displayName = 'QuickCommandButton'

export function ChatInterface({ className }: ChatInterfaceProps) {
  const {
    messages,
    isTyping,
    typingAgent,
    sendMessage: baseSendMessage,
    getCommandSuggestions,
    commands,
  } = useChat()
  
  const {
    currentIntent,
    context,
    isProcessing,
    processMessage,
    generateAIResponse,
    updateContext,
    resetContext,
    getContextSummary,
  } = useAIChat()
  
  const { recentSearches, addToRecent } = useAutoComplete()
  const { isOpen: isCommandPaletteOpen, setIsOpen: setCommandPaletteOpen } = useCommandPalette()
  
  const [showAutoComplete, setShowAutoComplete] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [commandHistory, setCommandHistory] = useState<string[]>([])
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  
  // Enhanced send message with AI processing
  const sendMessage = useCallback(async (message: string) => {
    // Add to recent searches
    addToRecent(message)
    
    // Add to command history if it's a command
    if (message.startsWith('/')) {
      setCommandHistory(prev => [message, ...prev.slice(0, 9)])
    }
    
    // Process message with AI
    const intent = await processMessage(message)
    
    // Send the message
    baseSendMessage(message)
    
    // Create a temporary message object for context update
    const tempMessage = {
      id: `temp-${Date.now()}`,
      type: 'user' as const,
      content: message,
      timestamp: new Date(),
    }
    updateContext(tempMessage, intent)
    
    // Clear input
    setInputValue('')
    setShowAutoComplete(false)
  }, [baseSendMessage, processMessage, updateContext, messages, addToRecent])
  
  // Handle suggested action selection
  const handleActionSelect = useCallback((action: string) => {
    sendMessage(action)
  }, [sendMessage])
  
  // Handle autocomplete selection
  const handleAutoCompleteSelect = useCallback((item: any) => {
    setInputValue(item.text)
    setShowAutoComplete(false)
  }, [])
  
  // Handle command palette execution
  const handleCommandExecute = useCallback((command: string) => {
    sendMessage(command)
  }, [sendMessage])
  
  // Auto-scroll to bottom on new messages
  useEffect(() => {
    const scrollToBottom = () => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
    
    // Small delay to ensure DOM updates
    const timeoutId = setTimeout(scrollToBottom, 100)
    return () => clearTimeout(timeoutId)
  }, [messages])
  
  // Group messages by sender for better visual organization
  const groupedMessages = useMemo(() => {
    return messages.reduce((groups, message, index) => {
      const prevMessage = index > 0 ? messages[index - 1] : null
      const isGrouped = prevMessage &&
        prevMessage.type === message.type &&
        prevMessage.sender === message.sender &&
        prevMessage.type !== 'system' &&
        // Group if messages are within 2 minutes
        (message.timestamp.getTime() - prevMessage.timestamp.getTime()) < 120000
      
      groups.push({ message, isGrouped })
      return groups
    }, [] as Array<{ message: typeof messages[0]; isGrouped: boolean }>)
  }, [messages])
  
  const isEmpty = messages.length === 0
  
  // Memoize quick command click handlers
  const handleQuickCommandClick = useCallback((command: string) => {
    sendMessage(command)
  }, [sendMessage])
  
  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* AI Processing Indicator */}
      {isProcessing && (
        <div className="absolute top-4 right-4 z-10">
          <Badge variant="secondary" className="gap-1">
            <Brain className="h-3 w-3 animate-pulse" />
            Processing...
          </Badge>
        </div>
      )}
      
      {/* Command Palette */}
      <CommandPalette
        open={isCommandPaletteOpen}
        onOpenChange={setCommandPaletteOpen}
        onCommandExecute={handleCommandExecute}
        commandHistory={commandHistory}
      />
      {/* Messages area */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto px-4 py-4"
      >
        {isEmpty ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center space-y-4 max-w-sm">
              <div className="text-6xl">💬</div>
              <h3 className="text-lg font-semibold">Welcome to SentinelOps Chat</h3>
              <p className="text-sm text-muted-foreground">
                Start a conversation with your AI agents. Type a message below or use /help to see available commands.
              </p>
              
              {/* Quick actions */}
              <div className="pt-4 space-y-2">
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Quick Commands</p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {commands.slice(0, 4).map(cmd => (
                    <QuickCommandButton
                      key={cmd.command}
                      command={cmd.command}
                      icon={cmd.icon}
                      onClick={handleQuickCommandClick}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Context Manager */}
            {context && (
              <div className="sticky top-0 z-10 bg-background/95 backdrop-blur-sm pb-2">
                <ContextManager
                  context={context}
                  onReset={resetContext}
                />
              </div>
            )}
            
            {/* Intent Recognition Display */}
            {currentIntent && currentIntent.needsClarification && (
              <Alert className="mx-4 mb-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  {currentIntent.clarificationPrompt}
                  <div className="flex items-center gap-2 mt-2">
                    <Badge variant="outline" className="text-xs">
                      Confidence: {Math.round(currentIntent.confidence * 100)}%
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      Intent: {currentIntent.intent}
                    </Badge>
                  </div>
                </AlertDescription>
              </Alert>
            )}
            
            {/* Suggested Actions */}
            {currentIntent?.suggestedActions && currentIntent.suggestedActions.length > 0 && (
              <div className="px-4 mb-4">
                <SuggestedActions
                  actions={currentIntent.suggestedActions}
                  intent={currentIntent.intent}
                  onActionSelect={handleActionSelect}
                  onLearnFromSelection={async (action, selected) => {
                    // Implement learning logic
                    try {
                      // Send learning data to backend
                      const response = await fetch('/api/learning/user-action', {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                          intent: currentIntent.intent,
                          action: action,
                          selected: selected,
                          context: {
                            messageHistory: messages.slice(-5).map(m => ({
                              role: m.role,
                              content: m.content,
                              agent: m.agent
                            })),
                            timestamp: new Date().toISOString()
                          }
                        })
                      })

                      if (!response.ok) {
                        console.error('Failed to send learning data:', response.statusText)
                      }
                    } catch (error) {
                      console.error('Error sending learning data:', error)
                    }
                  }}
                />
              </div>
            )}
            
            {/* Messages list */}
            <div className="space-y-1">
              {groupedMessages.map(({ message, isGrouped }) => (
                <Message
                  key={message.id}
                  message={message}
                  isGrouped={isGrouped}
                />
              ))}
              
              {/* Typing indicator as a message */}
              {isTyping && typingAgent && (
                <div className="flex gap-3 mt-4">
                  <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-medium">
                    {typingAgent.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex items-center">
                    <div className="bg-muted/50 px-4 py-2 rounded-2xl">
                      <div className="flex gap-1">
                        <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                        <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                        <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {/* Scroll anchor */}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
      
      {/* Input area */}
      <div className="border-t p-4 relative">
        {/* Auto-complete overlay */}
        {showAutoComplete && inputValue.length > 1 && (
          <AutoComplete
            value={inputValue}
            onSelect={handleAutoCompleteSelect}
            recentSearches={recentSearches}
            entities={{
              incidents: ['INC-12345', 'INC-12344', 'INC-12343'],
              agents: ['alice', 'bob', 'charlie'],
              systems: ['api', 'database', 'frontend'],
            }}
          />
        )}
        
        <ChatInput
          value={inputValue}
          onChange={(value) => {
            setInputValue(value)
            setShowAutoComplete(value.length > 1)
          }}
          onSendMessage={sendMessage}
          isTyping={isTyping}
          typingAgent={typingAgent}
          getCommandSuggestions={getCommandSuggestions}
          placeholder="Type a message or / for commands..."
        />
        
        {/* AI Features Indicator */}
        <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <Sparkles className="h-3 w-3" />
              AI-powered chat
            </span>
            {currentIntent && (
              <span className="flex items-center gap-1">
                Intent: {currentIntent.intent}
              </span>
            )}
          </div>
          <span>Press ⌘K for command palette</span>
        </div>
      </div>
    </div>
  )
}