'use client';

import React, { createContext, useContext, useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { WebSocketClient } from '@/lib/websocket/websocket-client';
import { 
  ConnectionState, 
  WebSocketMessage, 
  OutgoingMessage,
  ChannelType,
  MessageHandler,
  ConnectionStateHandler,
  ErrorHandler,
  ConnectionMetrics
} from '@/types/websocket';

interface WebSocketContextValue {
  client: WebSocketClient | null;
  connectionState: ConnectionState;
  metrics: ConnectionMetrics;
  connect: (authToken?: string) => void;
  disconnect: () => void;
  send: (message: OutgoingMessage) => string | null;
  subscribe: (channel: ChannelType, handler: MessageHandler) => () => void;
  onError: (handler: ErrorHandler) => () => void;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

interface WebSocketProviderProps {
  children: React.ReactNode;
  url?: string;
  autoConnect?: boolean;
  debug?: boolean;
}

export function WebSocketProvider({ 
  children, 
  url = process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:3001',
  autoConnect = true,
  debug = false
}: WebSocketProviderProps) {
  const clientRef = useRef<WebSocketClient | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>(ConnectionState.DISCONNECTED);
  const [metrics, setMetrics] = useState<ConnectionMetrics>({
    latency: 0,
    messagesSent: 0,
    messagesReceived: 0,
    bytesReceived: 0,
    bytesSent: 0,
    errors: 0,
    reconnects: 0
  });

  // Initialize WebSocket client
  useEffect(() => {
    if (!clientRef.current) {
      clientRef.current = new WebSocketClient({
        url,
        debug,
        reconnect: true,
        reconnectInterval: 1000,
        maxReconnectInterval: 30000,
        reconnectDecay: 1.5,
        timeout: 10000
      });

      // Subscribe to state changes
      const unsubscribeState = clientRef.current.onStateChange((state) => {
        setConnectionState(state);
      });

      // Update metrics periodically
      const metricsInterval = setInterval(() => {
        if (clientRef.current) {
          setMetrics(clientRef.current.getMetrics());
        }
      }, 1000);

      // Auto-connect if enabled
      if (autoConnect) {
        const authToken = localStorage.getItem('auth-token');
        clientRef.current.connect(authToken || undefined);
      }

      return () => {
        unsubscribeState();
        clearInterval(metricsInterval);
        clientRef.current?.disconnect();
        clientRef.current = null;
      };
    }
  }, [url, autoConnect, debug]);

  const connect = useCallback((authToken?: string) => {
    clientRef.current?.connect(authToken);
  }, []);

  const disconnect = useCallback(() => {
    clientRef.current?.disconnect();
  }, []);

  const send = useCallback((message: OutgoingMessage): string | null => {
    return clientRef.current?.send(message) || null;
  }, []);

  const subscribe = useCallback((channel: ChannelType, handler: MessageHandler): (() => void) => {
    if (!clientRef.current) {
      return () => {};
    }

    const subscriptionId = clientRef.current.subscribe(channel, handler);
    
    return () => {
      clientRef.current?.unsubscribe(subscriptionId);
    };
  }, []);

  const onError = useCallback((handler: ErrorHandler): (() => void) => {
    if (!clientRef.current) {
      return () => {};
    }

    return clientRef.current.onError(handler);
  }, []);

  const value: WebSocketContextValue = useMemo(() => ({
    client: clientRef.current,
    connectionState,
    metrics,
    connect,
    disconnect,
    send,
    subscribe,
    onError
  }), [connectionState, metrics, connect, disconnect, send, subscribe, onError]);

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  
  return context;
}