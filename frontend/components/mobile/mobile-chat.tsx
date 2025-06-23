'use client'

import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send,
  Mic,
  MicOff,
  Paperclip,
  ArrowLeft,
  MoreVertical,
  Sparkles,
  CheckCheck,
  Clock
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { ScrollArea } from '@/components/ui/scroll-area'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import type { ChatMessage } from '@/types/chat'

interface QuickReply {
  id: string
  text: string
  action?: string
}

interface MobileChatProps {
  messages: ChatMessage[]
  onSendMessage: (message: string) => void
  onBack?: () => void
  onVoiceInput?: (isRecording: boolean) => void
  onFileAttach?: () => void
  quickReplies?: QuickReply[]
  isTyping?: boolean
  chatTitle?: string
  chatContext?: string
}

export function MobileChat({
  messages,
  onSendMessage,
  onBack,
  onVoiceInput,
  onFileAttach,
  quickReplies = [],
  isTyping = false,
  chatTitle = 'AI Assistant',
  chatContext
}: MobileChatProps) {
  const [input, setInput] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [touchStart, setTouchStart] = useState<number | null>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input.trim())
      setInput('')
      inputRef.current?.focus()
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleVoiceToggle = () => {
    setIsRecording(!isRecording)
    if (onVoiceInput) {
      onVoiceInput(!isRecording)
    }
  }

  const handleQuickReply = (reply: QuickReply) => {
    onSendMessage(reply.text)
  }

  // Handle swipe gestures for navigation
  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchStart(e.targetTouches[0].clientX)
  }

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (!touchStart) return
    
    const touchEnd = e.changedTouches[0].clientX
    const distance = touchEnd - touchStart
    
    // Swipe right to go back
    if (distance > 100 && onBack) {
      onBack()
    }
    
    setTouchStart(null)
  }

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(date)
  }

  return (
    <div 
      className="flex flex-col h-screen bg-background safe-top safe-bottom"
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {/* Header */}
      <motion.header 
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex items-center justify-between p-4 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
      >
        <div className="flex items-center gap-3">
          {onBack && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onBack}
              className="h-10 w-10"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
          )}
          
          <div>
            <h1 className="font-semibold text-lg flex items-center gap-2">
              {chatTitle}
              <Sparkles className="h-4 w-4 text-primary" />
            </h1>
            {chatContext && (
              <p className="text-xs text-muted-foreground">{chatContext}</p>
            )}
          </div>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-10 w-10">
              <MoreVertical className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>Clear Chat</DropdownMenuItem>
            <DropdownMenuItem>Export Conversation</DropdownMenuItem>
            <DropdownMenuItem>Settings</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </motion.header>

      {/* Messages */}
      <ScrollArea ref={scrollAreaRef} className="flex-1 px-4 py-4">
        <AnimatePresence initial={false}>
          {messages.map((message, index) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className={cn(
                "flex gap-3 mb-4",
                message.role === 'user' ? "flex-row-reverse" : "flex-row"
              )}
            >
              <Avatar className="h-8 w-8 flex-shrink-0">
                <AvatarImage src={message.role === 'user' ? '/user-avatar.png' : '/ai-avatar.png'} />
                <AvatarFallback>
                  {message.role === 'user' ? 'U' : 'AI'}
                </AvatarFallback>
              </Avatar>

              <div className={cn(
                "flex flex-col gap-1 max-w-[80%]",
                message.role === 'user' ? "items-end" : "items-start"
              )}>
                <div className={cn(
                  "rounded-2xl px-4 py-2",
                  message.role === 'user' 
                    ? "bg-primary text-primary-foreground" 
                    : "bg-muted"
                )}>
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                </div>
                
                <div className="flex items-center gap-2 text-xs text-muted-foreground px-1">
                  <span>{formatTime(message.timestamp)}</span>
                  {message.role === 'user' && (
                    <CheckCheck className="h-3 w-3" />
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing Indicator */}
        <AnimatePresence>
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex items-center gap-3 mb-4"
            >
              <Avatar className="h-8 w-8">
                <AvatarFallback>AI</AvatarFallback>
              </Avatar>
              <div className="bg-muted rounded-2xl px-4 py-2">
                <div className="flex gap-1">
                  <motion.div
                    animate={{ y: [0, -5, 0] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
                    className="w-2 h-2 bg-muted-foreground rounded-full"
                  />
                  <motion.div
                    animate={{ y: [0, -5, 0] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
                    className="w-2 h-2 bg-muted-foreground rounded-full"
                  />
                  <motion.div
                    animate={{ y: [0, -5, 0] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
                    className="w-2 h-2 bg-muted-foreground rounded-full"
                  />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </ScrollArea>

      {/* Quick Replies */}
      {quickReplies.length > 0 && (
        <motion.div 
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="px-4 py-2 border-t border-border"
        >
          <ScrollArea className="w-full" orientation="horizontal">
            <div className="flex gap-2 pb-2">
              {quickReplies.map((reply) => (
                <Button
                  key={reply.id}
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickReply(reply)}
                  className="whitespace-nowrap"
                >
                  {reply.text}
                </Button>
              ))}
            </div>
          </ScrollArea>
        </motion.div>
      )}

      {/* Input Area */}
      <motion.div 
        initial={{ y: 50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="p-4 border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
      >
        <div className="flex items-end gap-2">
          {onFileAttach && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onFileAttach}
              className="h-10 w-10 flex-shrink-0"
            >
              <Paperclip className="h-5 w-5" />
            </Button>
          )}

          <div className="flex-1 relative">
            <Textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type a message..."
              className="min-h-[44px] max-h-[120px] resize-none pr-12"
              rows={1}
            />
            
            {onVoiceInput && (
              <Button
                variant="ghost"
                size="icon"
                onClick={handleVoiceToggle}
                className={cn(
                  "absolute right-1 bottom-1 h-8 w-8",
                  isRecording && "text-destructive"
                )}
              >
                {isRecording ? (
                  <MicOff className="h-4 w-4" />
                ) : (
                  <Mic className="h-4 w-4" />
                )}
              </Button>
            )}
          </div>

          <Button
            onClick={handleSend}
            disabled={!input.trim()}
            size="icon"
            className="h-10 w-10 flex-shrink-0"
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </motion.div>
    </div>
  )
}

export default MobileChat