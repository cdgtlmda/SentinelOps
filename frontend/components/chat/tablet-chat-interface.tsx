"use client"

import React, { useRef, useEffect, useState, useCallback } from 'react'
import { cn } from '@/lib/utils'
import { useChat } from '@/hooks/use-chat'
import { useAIChat } from '@/hooks/use-ai-chat'
import { useOptimalLayout } from '@/hooks/use-orientation'
import { Message } from './message'
import { ChatInput } from './chat-input'
import { ContextManager } from './context-manager'
import { SuggestedActions } from './suggested-actions'
import { AutoComplete, useAutoComplete } from './auto-complete'
import { CommandPalette, useCommandPalette } from './command-palette'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Card } from '@/components/ui/card'
import { Brain, Sparkles, AlertCircle, Users, History, Pin, Star } from 'lucide-react'
import { AdaptivePanels } from '@/components/tablet/adaptive-panels'

interface TabletChatInterfaceProps {
  className?: string
  showSidebar?: boolean
}

export function TabletChatInterface({ className, showSidebar = true }: TabletChatInterfaceProps) {
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
  const layout = useOptimalLayout()
  
  const [showAutoComplete, setShowAutoComplete] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [commandHistory, setCommandHistory] = useState<string[]>([])
  const [pinnedMessages, setPinnedMessages] = useState<Set<string>>(new Set())
  const [starredMessages, setStarredMessages] = useState<Set<string>>(new Set())
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  
  // Enhanced send message with AI processing
  const sendMessage = useCallback(async (message: string) => {
    addToRecent(message)
    
    if (message.startsWith('/')) {
      setCommandHistory(prev => [message, ...prev.slice(0, 9)])
    }
    
    const intent = await processMessage(message)
    baseSendMessage(message)
    
    const tempMessage = {
      id: `temp-${Date.now()}`,
      type: 'user' as const,
      content: message,
      timestamp: new Date(),
    }
    updateContext(tempMessage, intent)
    
    setInputValue('')
    setShowAutoComplete(false)
  }, [baseSendMessage, processMessage, updateContext, messages, addToRecent])
  
  const handleActionSelect = useCallback((action: string) => {
    sendMessage(action)
  }, [sendMessage])
  
  const handleAutoCompleteSelect = useCallback((item: any) => {
    setInputValue(item.text)
    setShowAutoComplete(false)
  }, [])
  
  const handleCommandExecute = useCallback((command: string) => {
    sendMessage(command)
  }, [sendMessage])
  
  const togglePinMessage = (messageId: string) => {
    setPinnedMessages(prev => {
      const next = new Set(prev)
      if (next.has(messageId)) {
        next.delete(messageId)
      } else {
        next.add(messageId)
      }
      return next
    })
  }
  
  const toggleStarMessage = (messageId: string) => {
    setStarredMessages(prev => {
      const next = new Set(prev)
      if (next.has(messageId)) {
        next.delete(messageId)
      } else {
        next.add(messageId)
      }
      return next
    })
  }
  
  // Auto-scroll to bottom on new messages
  useEffect(() => {
    const scrollToBottom = () => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
    
    const timeoutId = setTimeout(scrollToBottom, 100)
    return () => clearTimeout(timeoutId)
  }, [messages])
  
  // Group messages by sender
  const groupedMessages = messages.reduce((groups, message, index) => {
    const prevMessage = index > 0 ? messages[index - 1] : null
    const isGrouped = prevMessage &&
      prevMessage.type === message.type &&
      prevMessage.sender === message.sender &&
      prevMessage.type !== 'system' &&
      (message.timestamp.getTime() - prevMessage.timestamp.getTime()) < 120000
    
    groups.push({ message, isGrouped })
    return groups
  }, [] as Array<{ message: typeof messages[0]; isGrouped: boolean }>)
  
  const isEmpty = messages.length === 0
  
  // Sidebar content for landscape mode
  const sidebarContent = showSidebar && layout.isLandscape && (
    <div className="h-full flex flex-col bg-gray-50/50">
      <div className="p-4 border-b">
        <h3 className="font-semibold text-gray-900">Chat Information</h3>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Active Users */}
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Users className="w-4 h-4 text-gray-600" />
            <h4 className="font-medium">Active Participants</h4>
          </div>
          <div className="space-y-2">
            {['Alice (Security Agent)', 'Bob (Network Agent)', 'You'].map(user => (
              <div key={user} className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full" />
                <span className="text-sm">{user}</span>
              </div>
            ))}
          </div>
        </Card>
        
        {/* Pinned Messages */}
        {pinnedMessages.size > 0 && (
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Pin className="w-4 h-4 text-gray-600" />
              <h4 className="font-medium">Pinned Messages</h4>
            </div>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {messages
                .filter(msg => pinnedMessages.has(msg.id))
                .map(msg => (
                  <div key={msg.id} className="p-2 bg-gray-100 rounded text-sm">
                    <p className="font-medium text-xs text-gray-600 mb-1">{msg.sender || 'System'}</p>
                    <p className="line-clamp-2">{msg.content}</p>
                  </div>
                ))}
            </div>
          </Card>
        )}
        
        {/* Recent Commands */}
        {commandHistory.length > 0 && (
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <History className="w-4 h-4 text-gray-600" />
              <h4 className="font-medium">Recent Commands</h4>
            </div>
            <div className="space-y-1">
              {commandHistory.slice(0, 5).map((cmd, i) => (
                <button
                  key={i}
                  onClick={() => setInputValue(cmd)}
                  className="w-full text-left px-2 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded"
                >
                  {cmd}
                </button>
              ))}
            </div>
          </Card>
        )}
        
        {/* Context Summary */}
        {context && (
          <Card className="p-4">
            <h4 className="font-medium mb-2">Context Summary</h4>
            <p className="text-sm text-gray-600">{getContextSummary()}</p>
          </Card>
        )}
      </div>
    </div>
  )
  
  const mainChatContent = (
    <div className="flex flex-col h-full">
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
            <div className="text-center space-y-4 max-w-md">
              <div className="text-6xl">💬</div>
              <h3 className="text-xl font-semibold">Welcome to SentinelOps Chat</h3>
              <p className="text-sm text-muted-foreground">
                Start a conversation with your AI agents. Type a message below or use /help to see available commands.
              </p>
              
              {/* Quick actions grid for tablets */}
              <div className="pt-6">
                <p className="text-xs text-muted-foreground uppercase tracking-wide mb-3">Quick Commands</p>
                <div className="grid grid-cols-2 gap-3">
                  {commands.slice(0, 6).map(cmd => (
                    <button
                      key={cmd.command}
                      onClick={() => sendMessage(cmd.command)}
                      className="p-3 bg-muted hover:bg-muted/80 rounded-lg transition-colors text-left"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-lg">{cmd.icon}</span>
                        <span className="font-medium">{cmd.command}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">{cmd.description}</p>
                    </button>
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
              <Alert className="mb-4">
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
              <div className="mb-4">
                <SuggestedActions
                  actions={currentIntent.suggestedActions}
                  intent={currentIntent.intent}
                  onActionSelect={handleActionSelect}
                  onLearnFromSelection={(action, selected) => {
                    console.log('Learning from selection:', action, selected)
                  }}
                />
              </div>
            )}
            
            {/* Messages list */}
            <div className="space-y-1">
              {groupedMessages.map(({ message, isGrouped }) => (
                <div key={message.id} className="group relative">
                  <Message
                    message={message}
                    isGrouped={isGrouped}
                  />
                  
                  {/* Message actions for tablets */}
                  <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                    <button
                      onClick={() => togglePinMessage(message.id)}
                      className={cn(
                        "p-1 rounded hover:bg-gray-100",
                        pinnedMessages.has(message.id) && "text-blue-600"
                      )}
                    >
                      <Pin className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => toggleStarMessage(message.id)}
                      className={cn(
                        "p-1 rounded hover:bg-gray-100",
                        starredMessages.has(message.id) && "text-yellow-600"
                      )}
                    >
                      <Star className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
              
              {/* Typing indicator */}
              {isTyping && typingAgent && (
                <div className="flex gap-3 mt-4">
                  <div className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-medium">
                    {typingAgent.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex items-center">
                    <div className="bg-muted/50 px-4 py-3 rounded-2xl">
                      <div className="flex gap-1.5">
                        <span className="w-2.5 h-2.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                        <span className="w-2.5 h-2.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                        <span className="w-2.5 h-2.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
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
  
  // Return adaptive layout based on orientation
  if (showSidebar && layout.isLandscape) {
    return (
      <AdaptivePanels
        orientation={layout.orientation}
        primaryPanel={mainChatContent}
        secondaryPanel={sidebarContent}
        defaultSecondaryWidth={320}
        minSecondaryWidth={280}
        maxSecondaryWidth={400}
        priority="primary"
        className={className}
      />
    )
  }
  
  return <div className={cn("h-full", className)}>{mainChatContent}</div>
}