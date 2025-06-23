'use client';

import React, { useState, useEffect } from 'react';
import { useWebSocket } from '@/context/websocket-context';
import { ConnectionState } from '@/types/websocket';
import { cn } from '@/lib/utils';
import { Wifi, WifiOff, RefreshCw, AlertTriangle, Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';

interface ConnectionStatusProps {
  className?: string;
  showDetails?: boolean;
  compact?: boolean;
}

export function ConnectionStatus({ 
  className, 
  showDetails = false, 
  compact = false 
}: ConnectionStatusProps) {
  const { connectionState, metrics, connect, disconnect } = useWebSocket();
  const [showTooltip, setShowTooltip] = useState(false);

  const getStatusIcon = () => {
    switch (connectionState) {
      case ConnectionState.CONNECTED:
        return <Wifi className="h-4 w-4" />;
      case ConnectionState.CONNECTING:
      case ConnectionState.RECONNECTING:
        return <RefreshCw className="h-4 w-4 animate-spin" />;
      case ConnectionState.DISCONNECTED:
        return <WifiOff className="h-4 w-4" />;
      case ConnectionState.ERROR:
        return <AlertTriangle className="h-4 w-4" />;
      default:
        return null;
    }
  };

  const getStatusColor = () => {
    switch (connectionState) {
      case ConnectionState.CONNECTED:
        return 'text-green-600 dark:text-green-400';
      case ConnectionState.CONNECTING:
      case ConnectionState.RECONNECTING:
        return 'text-yellow-600 dark:text-yellow-400';
      case ConnectionState.DISCONNECTED:
        return 'text-gray-600 dark:text-gray-400';
      case ConnectionState.ERROR:
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getConnectionQuality = () => {
    if (connectionState !== ConnectionState.CONNECTED) {
      return { quality: 'offline', percentage: 0 };
    }

    if (metrics.latency < 50) {
      return { quality: 'excellent', percentage: 100 };
    } else if (metrics.latency < 150) {
      return { quality: 'good', percentage: 75 };
    } else if (metrics.latency < 300) {
      return { quality: 'fair', percentage: 50 };
    } else {
      return { quality: 'poor', percentage: 25 };
    }
  };

  const { quality, percentage } = getConnectionQuality();

  if (compact) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className={cn('flex items-center gap-1', className)}>
              <div className={cn('transition-colors', getStatusColor())}>
                {getStatusIcon()}
              </div>
              {connectionState === ConnectionState.CONNECTED && metrics.latency > 0 && (
                <span className="text-xs text-muted-foreground">
                  {metrics.latency}ms
                </span>
              )}
            </div>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="max-w-xs">
            <ConnectionStatusDetails metrics={metrics} connectionState={connectionState} />
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={cn('transition-colors', getStatusColor())}>
            {getStatusIcon()}
          </div>
          <span className="text-sm font-medium capitalize">
            {connectionState.toLowerCase()}
          </span>
        </div>
        
        {connectionState === ConnectionState.DISCONNECTED ? (
          <Button
            size="sm"
            variant="outline"
            onClick={() => connect()}
          >
            Connect
          </Button>
        ) : connectionState === ConnectionState.CONNECTED ? (
          <Button
            size="sm"
            variant="outline"
            onClick={() => disconnect()}
          >
            Disconnect
          </Button>
        ) : null}
      </div>

      {showDetails && connectionState === ConnectionState.CONNECTED && (
        <ConnectionStatusDetails metrics={metrics} connectionState={connectionState} />
      )}

      {connectionState === ConnectionState.RECONNECTING && (
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">
            Reconnecting... Attempt #{metrics.reconnects + 1}
          </p>
          <Progress value={33} className="h-1" />
        </div>
      )}
    </div>
  );
}

function ConnectionStatusDetails({ 
  metrics, 
  connectionState 
}: { 
  metrics: any; 
  connectionState: ConnectionState;
}) {
  const getQualityBadge = () => {
    if (connectionState !== ConnectionState.CONNECTED) {
      return <Badge variant="secondary">Offline</Badge>;
    }

    if (metrics.latency < 50) {
      return <Badge variant="default" className="bg-green-600">Excellent</Badge>;
    } else if (metrics.latency < 150) {
      return <Badge variant="default" className="bg-blue-600">Good</Badge>;
    } else if (metrics.latency < 300) {
      return <Badge variant="default" className="bg-yellow-600">Fair</Badge>;
    } else {
      return <Badge variant="destructive">Poor</Badge>;
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">Connection Quality</span>
        {getQualityBadge()}
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-muted-foreground">Latency:</span>
          <span className="ml-1 font-mono">{metrics.latency}ms</span>
        </div>
        <div>
          <span className="text-muted-foreground">Messages:</span>
          <span className="ml-1 font-mono">
            ↑{metrics.messagesSent} ↓{metrics.messagesReceived}
          </span>
        </div>
        <div>
          <span className="text-muted-foreground">Data:</span>
          <span className="ml-1 font-mono">
            ↑{formatBytes(metrics.bytesSent)} ↓{formatBytes(metrics.bytesReceived)}
          </span>
        </div>
        <div>
          <span className="text-muted-foreground">Errors:</span>
          <span className="ml-1 font-mono">{metrics.errors}</span>
        </div>
      </div>

      {metrics.reconnects > 0 && (
        <div className="text-xs text-muted-foreground">
          Reconnected {metrics.reconnects} time{metrics.reconnects > 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))}${sizes[i]}`;
}