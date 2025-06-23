'use client';

import React, { useState, useEffect } from 'react';
import { useAgentStatus } from '@/hooks/use-websocket';
import { AgentStatusUpdate } from '@/types/websocket';
import { cn } from '@/lib/utils';
import { User, Circle, Clock } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface Agent {
  id: string;
  name: string;
  avatar?: string;
  status: 'online' | 'offline' | 'busy' | 'away';
  lastSeen?: Date;
  department?: string;
  role?: string;
}

interface RealtimeAgentStatusProps {
  agents: Agent[];
  showOffline?: boolean;
  compact?: boolean;
  className?: string;
}

export function RealtimeAgentStatus({ 
  agents: initialAgents, 
  showOffline = true,
  compact = false,
  className 
}: RealtimeAgentStatusProps) {
  const [agents, setAgents] = useState<Map<string, Agent>>(
    new Map(initialAgents.map(agent => [agent.id, agent]))
  );
  const [recentChanges, setRecentChanges] = useState<Set<string>>(new Set());

  // Handle real-time agent status updates
  const { isConnected } = useAgentStatus((update: AgentStatusUpdate) => {
    setAgents(prev => {
      const newAgents = new Map(prev);
      const agent = newAgents.get(update.agentId);
      
      if (agent) {
        newAgents.set(update.agentId, {
          ...agent,
          status: update.status,
          lastSeen: update.lastSeen ? new Date(update.lastSeen) : agent.lastSeen
        });

        // Mark as recently changed
        setRecentChanges(prev => new Set([...prev, update.agentId]));
        setTimeout(() => {
          setRecentChanges(prev => {
            const newSet = new Set(prev);
            newSet.delete(update.agentId);
            return newSet;
          });
        }, 3000);
      }
      
      return newAgents;
    });
  });

  // Update agents when initialAgents changes
  useEffect(() => {
    setAgents(new Map(initialAgents.map(agent => [agent.id, agent])));
  }, [initialAgents]);

  const getStatusColor = (status: Agent['status']) => {
    switch (status) {
      case 'online':
        return 'text-green-500';
      case 'busy':
        return 'text-red-500';
      case 'away':
        return 'text-yellow-500';
      case 'offline':
        return 'text-gray-400';
    }
  };

  const getStatusBadgeVariant = (status: Agent['status']) => {
    switch (status) {
      case 'online':
        return 'default';
      case 'busy':
        return 'destructive';
      case 'away':
        return 'secondary';
      case 'offline':
        return 'outline';
    }
  };

  const formatLastSeen = (date?: Date) => {
    if (!date) return 'Never';
    
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  const sortedAgents = Array.from(agents.values()).sort((a, b) => {
    // Sort by status priority (online > busy > away > offline)
    const statusPriority = { online: 0, busy: 1, away: 2, offline: 3 };
    const statusDiff = statusPriority[a.status] - statusPriority[b.status];
    if (statusDiff !== 0) return statusDiff;
    
    // Then by name
    return a.name.localeCompare(b.name);
  });

  const filteredAgents = showOffline 
    ? sortedAgents 
    : sortedAgents.filter(agent => agent.status !== 'offline');

  const onlineCount = sortedAgents.filter(a => a.status === 'online').length;
  const totalCount = sortedAgents.length;

  if (compact) {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        <div className="flex -space-x-2">
          {filteredAgents.slice(0, 5).map((agent) => (
            <TooltipProvider key={agent.id}>
              <Tooltip>
                <TooltipTrigger>
                  <div 
                    className={cn(
                      'relative inline-block transition-transform',
                      recentChanges.has(agent.id) && 'scale-110'
                    )}
                  >
                    {agent.avatar ? (
                      <img
                        src={agent.avatar}
                        alt={agent.name}
                        className="w-8 h-8 rounded-full border-2 border-white dark:border-gray-800"
                      />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 border-2 border-white dark:border-gray-800 flex items-center justify-center">
                        <User className="w-4 h-4 text-gray-500" />
                      </div>
                    )}
                    <Circle 
                      className={cn(
                        'absolute bottom-0 right-0 w-3 h-3',
                        getStatusColor(agent.status)
                      )}
                      fill="currentColor"
                    />
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <div className="text-sm">
                    <p className="font-medium">{agent.name}</p>
                    <p className="text-xs text-muted-foreground capitalize">{agent.status}</p>
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          ))}
        </div>
        {filteredAgents.length > 5 && (
          <span className="text-sm text-muted-foreground">
            +{filteredAgents.length - 5}
          </span>
        )}
        <Badge variant="secondary" className="text-xs">
          {onlineCount}/{totalCount} online
        </Badge>
      </div>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Team Status</h3>
        <Badge variant="secondary">
          {onlineCount}/{totalCount} online
        </Badge>
      </div>

      <div className="grid gap-3">
        {filteredAgents.map((agent) => (
          <div
            key={agent.id}
            className={cn(
              'flex items-center gap-3 p-3 rounded-lg bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 transition-all',
              recentChanges.has(agent.id) && 'ring-2 ring-blue-500 ring-opacity-50'
            )}
          >
            <div className="relative">
              {agent.avatar ? (
                <img
                  src={agent.avatar}
                  alt={agent.name}
                  className="w-10 h-10 rounded-full"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                  <User className="w-5 h-5 text-gray-500" />
                </div>
              )}
              <Circle 
                className={cn(
                  'absolute bottom-0 right-0 w-3 h-3',
                  getStatusColor(agent.status)
                )}
                fill="currentColor"
              />
            </div>

            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{agent.name}</p>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                {agent.role && <span>{agent.role}</span>}
                {agent.department && (
                  <>
                    <span>•</span>
                    <span>{agent.department}</span>
                  </>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Badge 
                variant={getStatusBadgeVariant(agent.status) as any}
                className="capitalize"
              >
                {agent.status}
              </Badge>
              {agent.status === 'offline' && agent.lastSeen && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <Clock className="w-4 h-4 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="text-xs">Last seen {formatLastSeen(agent.lastSeen)}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </div>
          </div>
        ))}
      </div>

      {!isConnected && (
        <p className="text-xs text-center text-muted-foreground">
          Real-time updates unavailable
        </p>
      )}
    </div>
  );
}