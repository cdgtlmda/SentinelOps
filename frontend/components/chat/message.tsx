import React from 'react'
import { cn } from '@/lib/utils'
import { Message as MessageType } from '@/types/chat'
import { useAgentStore } from '@/store'

interface MessageProps {
  message: MessageType
  isGrouped?: boolean
}

export function Message({ message, isGrouped = false }: MessageProps) {
  const agents = useAgentStore((state) => state.agents)
  const agent = message.agentId ? agents.find(a => a.id === message.agentId) : null
  
  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    }).format(date)
  }
  
  if (message.type === 'system') {
    return (
      <div className="flex justify-center my-4">
        <div className="bg-muted/50 text-muted-foreground text-sm px-3 py-1.5 rounded-full">
          {message.content}
        </div>
      </div>
    )
  }
  
  const isUser = message.type === 'user'
  
  return (
    <div
      className={cn(
        'flex gap-3',
        isUser ? 'justify-end' : 'justify-start',
        isGrouped ? 'mt-1' : 'mt-4'
      )}
    >
      {/* Avatar for agent messages */}
      {!isUser && !isGrouped && (
        <div className="flex-shrink-0">
          <div
            className={cn(
              'w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium',
              agent?.color ? '' : 'bg-primary text-primary-foreground'
            )}
            style={agent?.color ? { backgroundColor: agent.color, color: 'white' } : {}}
          >
            {agent?.avatar || message.sender?.charAt(0).toUpperCase() || '🤖'}
          </div>
        </div>
      )}
      
      {/* Spacer for grouped agent messages */}
      {!isUser && isGrouped && <div className="w-8 flex-shrink-0" />}
      
      <div
        className={cn(
          'flex flex-col',
          isUser ? 'items-end' : 'items-start',
          'max-w-[70%]'
        )}
      >
        {/* Sender name for agent messages */}
        {!isUser && !isGrouped && (
          <span className="text-xs text-muted-foreground mb-1 px-1">
            {message.sender || 'Agent'}
          </span>
        )}
        
        {/* Message bubble */}
        <div
          className={cn(
            'px-4 py-2 rounded-2xl break-words',
            isUser
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted/50 text-foreground',
            message.content.includes('\n') && 'whitespace-pre-wrap'
          )}
        >
          <p className="text-sm">{message.content}</p>
        </div>
        
        {/* Timestamp and status */}
        <div className="flex items-center gap-2 mt-1 px-1">
          <span className="text-xs text-muted-foreground">
            {formatTime(message.timestamp)}
          </span>
          
          {/* Status indicator for user messages */}
          {isUser && message.status && (
            <span className="text-xs text-muted-foreground">
              {message.status === 'sending' && '○'}
              {message.status === 'sent' && '✓'}
              {message.status === 'delivered' && '✓✓'}
              {message.status === 'error' && '⚠️'}
            </span>
          )}
        </div>
        
        {/* Attachments */}
        {message.attachments && message.attachments.length > 0 && (
          <div className="mt-2 space-y-1">
            {message.attachments.map(attachment => (
              <div
                key={attachment.id}
                className="flex items-center gap-2 px-3 py-2 bg-muted/30 rounded-lg text-xs"
              >
                <span>📎</span>
                <span className="truncate">{attachment.name}</span>
                <span className="text-muted-foreground">
                  ({(attachment.size / 1024).toFixed(1)}KB)
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}