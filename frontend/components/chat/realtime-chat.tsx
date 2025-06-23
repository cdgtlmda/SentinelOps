'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useChatMessages } from '@/hooks/use-websocket';
import { ChatMessage as ChatMessageType } from '@/types/websocket';
import { cn } from '@/lib/utils';
import { Send, Paperclip, MoreVertical, Check, CheckCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface User {
  id: string;
  name: string;
  avatar?: string;
  role?: string;
}

interface Message extends ChatMessageType {
  sender: User;
  delivered?: boolean;
  readBy?: string[];
}

interface RealtimeChatProps {
  conversationId: string;
  currentUser: User;
  participants: User[];
  initialMessages?: Message[];
  onSendMessage?: (message: Message) => void;
  className?: string;
}

export function RealtimeChat({
  conversationId,
  currentUser,
  participants,
  initialMessages = [],
  onSendMessage,
  className
}: RealtimeChatProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState<Set<string>>(new Set());
  const [unreadCount, setUnreadCount] = useState(0);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const lastMessageRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Handle real-time chat messages
  const { sendMessage: sendWebSocketMessage, isConnected, latency } = useChatMessages(
    conversationId,
    (message: ChatMessageType) => {
      // Find sender from participants
      const sender = participants.find(p => p.id === message.senderId) || {
        id: message.senderId,
        name: 'Unknown User'
      };

      const newMessage: Message = {
        ...message,
        sender,
        delivered: true,
        readBy: [message.senderId]
      };

      setMessages(prev => [...prev, newMessage]);
      
      // Increment unread count if message is from another user
      if (message.senderId !== currentUser.id) {
        setUnreadCount(prev => prev + 1);
      }

      // Scroll to bottom on new message
      setTimeout(() => {
        lastMessageRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  );

  // Mark messages as read when viewing
  useEffect(() => {
    const markAsRead = () => {
      if (document.visibilityState === 'visible') {
        setUnreadCount(0);
        // Send read receipts for unread messages
        const unreadMessages = messages.filter(
          m => m.senderId !== currentUser.id && !m.readBy?.includes(currentUser.id)
        );
        unreadMessages.forEach(message => {
          // Send read receipt via WebSocket
          sendWebSocketMessage(JSON.stringify({
            type: 'read_receipt',
            messageId: message.id,
            readBy: currentUser.id
          }));
        });
      }
    };

    document.addEventListener('visibilitychange', markAsRead);
    markAsRead(); // Mark as read on mount

    return () => {
      document.removeEventListener('visibilitychange', markAsRead);
    };
  }, [messages, currentUser.id, sendWebSocketMessage]);

  const handleSendMessage = useCallback(() => {
    if (!inputValue.trim()) return;

    const newMessage: Message = {
      id: `temp-${Date.now()}`,
      conversationId,
      senderId: currentUser.id,
      content: inputValue,
      timestamp: Date.now(),
      sender: currentUser,
      delivered: false,
      readBy: [currentUser.id]
    };

    // Optimistically add message
    setMessages(prev => [...prev, newMessage]);
    
    // Send via WebSocket
    const messageId = sendWebSocketMessage(inputValue);
    
    // Update message ID when sent
    setMessages(prev => prev.map(m => 
      m.id === newMessage.id 
        ? { ...m, id: messageId || m.id, delivered: true }
        : m
    ));

    // Call parent handler
    onSendMessage?.(newMessage);

    // Clear input
    setInputValue('');
    inputRef.current?.focus();

    // Scroll to bottom
    setTimeout(() => {
      lastMessageRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  }, [inputValue, conversationId, currentUser, sendWebSocketMessage, onSendMessage]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
  };

  const groupMessagesByDate = (messages: Message[]) => {
    const groups: { [key: string]: Message[] } = {};
    
    messages.forEach(message => {
      const date = new Date(message.timestamp);
      const dateKey = date.toDateString();
      
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(message);
    });

    return groups;
  };

  const messageGroups = groupMessagesByDate(messages);

  return (
    <div className={cn('flex flex-col h-full bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800', className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-center gap-3">
          <h3 className="font-semibold">Chat</h3>
          {participants.length > 2 && (
            <Badge variant="secondary">{participants.length} participants</Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          {isConnected ? (
            <Badge variant="default" className="bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">
              Connected • {latency}ms
            </Badge>
          ) : (
            <Badge variant="secondary">Offline</Badge>
          )}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>Clear chat</DropdownMenuItem>
              <DropdownMenuItem>Export chat</DropdownMenuItem>
              <DropdownMenuItem>Leave conversation</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
        <div className="space-y-4">
          {Object.entries(messageGroups).map(([dateKey, dateMessages]) => (
            <div key={dateKey}>
              <div className="flex items-center justify-center my-4">
                <div className="bg-gray-100 dark:bg-gray-800 px-3 py-1 rounded-full text-xs text-muted-foreground">
                  {dateKey === new Date().toDateString() ? 'Today' : dateKey}
                </div>
              </div>
              
              {dateMessages.map((message, index) => {
                const isCurrentUser = message.senderId === currentUser.id;
                const showAvatar = index === 0 || 
                  dateMessages[index - 1]?.senderId !== message.senderId;

                return (
                  <div
                    key={message.id}
                    ref={index === dateMessages.length - 1 ? lastMessageRef : null}
                    className={cn(
                      'flex gap-3',
                      isCurrentUser && 'flex-row-reverse'
                    )}
                  >
                    {showAvatar ? (
                      <Avatar className="w-8 h-8">
                        {message.sender.avatar ? (
                          <img src={message.sender.avatar} alt={message.sender.name} />
                        ) : (
                          <div className="w-full h-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-sm">
                            {message.sender.name[0]}
                          </div>
                        )}
                      </Avatar>
                    ) : (
                      <div className="w-8" />
                    )}

                    <div className={cn(
                      'flex flex-col gap-1 max-w-[70%]',
                      isCurrentUser && 'items-end'
                    )}>
                      {showAvatar && !isCurrentUser && (
                        <span className="text-xs text-muted-foreground">
                          {message.sender.name}
                        </span>
                      )}
                      
                      <div className={cn(
                        'px-4 py-2 rounded-lg',
                        isCurrentUser
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 dark:bg-gray-800'
                      )}>
                        <p className="text-sm whitespace-pre-wrap break-words">
                          {message.content}
                        </p>
                      </div>

                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <span>{formatTimestamp(message.timestamp)}</span>
                        {isCurrentUser && (
                          <>
                            {message.delivered ? (
                              message.readBy && message.readBy.length > 1 ? (
                                <CheckCheck className="w-3 h-3 text-blue-500" />
                              ) : (
                                <Check className="w-3 h-3" />
                              )
                            ) : (
                              <div className="w-3 h-3 rounded-full border-2 border-current animate-spin" />
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Typing indicator */}
      {isTyping.size > 0 && (
        <div className="px-4 py-2 text-xs text-muted-foreground">
          {Array.from(isTyping).join(', ')} {isTyping.size === 1 ? 'is' : 'are'} typing...
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-800">
        <div className="flex items-end gap-2">
          <Button variant="ghost" size="icon" className="shrink-0">
            <Paperclip className="h-4 w-4" />
          </Button>
          <Input
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type a message..."
            className="flex-1"
            disabled={!isConnected}
          />
          <Button 
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || !isConnected}
            size="icon"
            className="shrink-0"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Unread count badge */}
      {unreadCount > 0 && (
        <div className="absolute top-2 right-2">
          <Badge variant="destructive" className="rounded-full">
            {unreadCount}
          </Badge>
        </div>
      )}
    </div>
  );
}