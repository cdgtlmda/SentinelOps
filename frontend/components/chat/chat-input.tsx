import React, { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { cn } from '@/lib/utils'
import { ChatCommand } from '@/types/chat'

interface ChatInputProps {
  value?: string
  onChange?: (value: string) => void
  onSendMessage: (message: string) => void
  isTyping?: boolean
  typingAgent?: string
  commandSuggestions?: ChatCommand[]
  getCommandSuggestions?: (input: string) => ChatCommand[]
  placeholder?: string
  className?: string
}

export function ChatInput({
  value: controlledValue,
  onChange: controlledOnChange,
  onSendMessage,
  isTyping,
  typingAgent,
  commandSuggestions = [],
  getCommandSuggestions,
  placeholder = 'Type a message...',
  className,
}: ChatInputProps) {
  const [internalMessage, setInternalMessage] = useState('')
  const message = controlledValue !== undefined ? controlledValue : internalMessage
  const setMessage = controlledOnChange || setInternalMessage
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(0)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  
  // Get suggestions based on input
  const suggestions = getCommandSuggestions ? getCommandSuggestions(message) : []
  
  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`
    }
  }, [message])
  
  // Handle keyboard events
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    } else if (e.key === 'Escape' && showSuggestions) {
      setShowSuggestions(false)
    } else if (showSuggestions && suggestions.length > 0) {
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedSuggestionIndex(prev => 
          prev > 0 ? prev - 1 : suggestions.length - 1
        )
      } else if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedSuggestionIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : 0
        )
      } else if (e.key === 'Tab' || (e.key === 'Enter' && showSuggestions)) {
        e.preventDefault()
        const selectedCommand = suggestions[selectedSuggestionIndex]
        if (selectedCommand) {
          setMessage(selectedCommand.command + ' ')
          setShowSuggestions(false)
        }
      }
    }
  }
  
  // Handle message send
  const handleSend = () => {
    if (message.trim()) {
      onSendMessage(message)
      setMessage('')
      setShowSuggestions(false)
      setSelectedSuggestionIndex(0)
    }
  }
  
  // Handle input change
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setMessage(value)
    
    // Show suggestions for commands
    if (value.startsWith('/') && getCommandSuggestions) {
      setShowSuggestions(true)
      setSelectedSuggestionIndex(0)
    } else {
      setShowSuggestions(false)
    }
  }
  
  // Handle file attachment (placeholder)
  const handleAttachment = () => {
    // Placeholder for file attachment functionality
    console.log('File attachment clicked')
  }
  
  return (
    <div className={cn('relative', className)}>
      {/* Typing indicator */}
      {isTyping && typingAgent && (
        <div className="absolute -top-8 left-0 flex items-center gap-2 text-sm text-muted-foreground">
          <span>{typingAgent} is typing</span>
          <span className="flex gap-1">
            <span className="animate-bounce" style={{ animationDelay: '0ms' }}>.</span>
            <span className="animate-bounce" style={{ animationDelay: '150ms' }}>.</span>
            <span className="animate-bounce" style={{ animationDelay: '300ms' }}>.</span>
          </span>
        </div>
      )}
      
      {/* Command suggestions */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute bottom-full mb-2 left-0 right-0 bg-popover border rounded-lg shadow-lg max-h-48 overflow-y-auto">
          {suggestions.map((suggestion, index) => (
            <button
              key={suggestion.command}
              onClick={() => {
                setMessage(suggestion.command + ' ')
                setShowSuggestions(false)
                textareaRef.current?.focus()
              }}
              className={cn(
                'w-full text-left px-4 py-2 hover:bg-accent transition-colors flex items-center gap-3',
                index === selectedSuggestionIndex && 'bg-accent'
              )}
            >
              <span className="text-lg">{suggestion.icon}</span>
              <div>
                <p className="font-medium text-sm">{suggestion.command}</p>
                <p className="text-xs text-muted-foreground">{suggestion.description}</p>
              </div>
            </button>
          ))}
        </div>
      )}
      
      {/* Input container */}
      <div className="flex items-end gap-2 bg-background border rounded-lg p-2">
        {/* Attachment button */}
        <button
          onClick={handleAttachment}
          className="p-2 hover:bg-accent rounded-md transition-colors text-muted-foreground hover:text-foreground"
          aria-label="Attach file"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
          </svg>
        </button>
        
        {/* Textarea */}
        <label htmlFor="chat-input" className="sr-only">
          Message input
        </label>
        <textarea
          id="chat-input"
          ref={textareaRef}
          value={message}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="flex-1 resize-none bg-transparent focus:outline-none min-h-[40px] max-h-[120px] py-2"
          rows={1}
          aria-label="Type your message"
        />
        
        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={!message.trim()}
          className={cn(
            'p-2 rounded-md transition-colors',
            message.trim()
              ? 'bg-primary text-primary-foreground hover:bg-primary/90'
              : 'bg-muted text-muted-foreground cursor-not-allowed'
          )}
          aria-label="Send message"
          aria-disabled={!message.trim()}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
      
      {/* Keyboard shortcuts hint */}
      <div className="mt-1 text-xs text-muted-foreground flex justify-between">
        <span>Press Enter to send, Shift+Enter for new line</span>
        <span>Type / for commands</span>
      </div>
    </div>
  )
}