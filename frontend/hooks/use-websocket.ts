'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { useWebSocket as useWebSocketContext } from '@/context/websocket-context';
import { 
  ChannelType, 
  MessageHandler, 
  WebSocketMessage,
  ConnectionState,
  OutgoingMessage
} from '@/types/websocket';

interface UseWebSocketOptions {
  channel?: ChannelType;
  onMessage?: MessageHandler;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
}

interface UseWebSocketReturn {
  connectionState: ConnectionState;
  send: (message: OutgoingMessage) => string | null;
  latency: number;
  isConnected: boolean;
  isReconnecting: boolean;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const { 
    client, 
    connectionState, 
    metrics, 
    send: sendMessage, 
    subscribe, 
    onError 
  } = useWebSocketContext();
  
  const [latency, setLatency] = useState(0);
  const optionsRef = useRef(options);
  optionsRef.current = options;

  // Subscribe to channel if provided
  useEffect(() => {
    if (!options.channel || !options.onMessage) {
      return;
    }

    const unsubscribe = subscribe(options.channel, options.onMessage);
    return unsubscribe;
  }, [options.channel, options.onMessage, subscribe]);

  // Handle connection state changes
  useEffect(() => {
    if (connectionState === ConnectionState.CONNECTED && optionsRef.current.onConnect) {
      optionsRef.current.onConnect();
    } else if (connectionState === ConnectionState.DISCONNECTED && optionsRef.current.onDisconnect) {
      optionsRef.current.onDisconnect();
    }
  }, [connectionState]);

  // Handle errors
  useEffect(() => {
    if (!options.onError) {
      return;
    }

    const unsubscribe = onError(options.onError);
    return unsubscribe;
  }, [options.onError, onError]);

  // Update latency
  useEffect(() => {
    const interval = setInterval(() => {
      setLatency(metrics.latency);
    }, 1000);

    return () => clearInterval(interval);
  }, [metrics.latency]);

  const send = useCallback((message: OutgoingMessage): string | null => {
    return sendMessage(message);
  }, [sendMessage]);

  return {
    connectionState,
    send,
    latency,
    isConnected: connectionState === ConnectionState.CONNECTED,
    isReconnecting: connectionState === ConnectionState.RECONNECTING
  };
}

// Specialized hooks for specific channels
export function useIncidentUpdates(handler: (update: any) => void) {
  return useWebSocket({
    channel: ChannelType.INCIDENTS,
    onMessage: (message) => {
      if (message.channel === ChannelType.INCIDENTS) {
        handler(message.payload);
      }
    }
  });
}

export function useAgentStatus(handler: (status: any) => void) {
  return useWebSocket({
    channel: ChannelType.AGENTS,
    onMessage: (message) => {
      if (message.channel === ChannelType.AGENTS) {
        handler(message.payload);
      }
    }
  });
}

export function useChatMessages(conversationId: string, handler: (message: any) => void) {
  const { send, ...rest } = useWebSocket({
    channel: ChannelType.CHAT,
    onMessage: (message) => {
      if (message.channel === ChannelType.CHAT && 
          message.payload.conversationId === conversationId) {
        handler(message.payload);
      }
    }
  });

  const sendChatMessage = useCallback((content: string) => {
    return send({
      type: 'chat.message',
      channel: ChannelType.CHAT,
      payload: {
        conversationId,
        content
      }
    });
  }, [send, conversationId]);

  return {
    ...rest,
    sendMessage: sendChatMessage
  };
}

export function useAlerts(handler: (alert: any) => void) {
  return useWebSocket({
    channel: ChannelType.ALERTS,
    onMessage: (message) => {
      if (message.channel === ChannelType.ALERTS) {
        handler(message.payload);
      }
    }
  });
}

export function useActivityFeed(handler: (activity: any) => void) {
  return useWebSocket({
    channel: ChannelType.ACTIVITY,
    onMessage: (message) => {
      if (message.channel === ChannelType.ACTIVITY) {
        handler(message.payload);
      }
    }
  });
}