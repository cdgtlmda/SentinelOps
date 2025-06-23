'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useActivityFeed } from '@/hooks/use-websocket';
import { ActivityEvent } from '@/types/websocket';
import { cn } from '@/lib/utils';
import { useThrottle } from '@/hooks/use-throttle';
import { 
  Activity, 
  AlertCircle, 
  CheckCircle, 
  Info, 
  UserPlus,
  FileText,
  Settings,
  Shield,
  Zap,
  Clock
} from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface ActivityFeedItem extends ActivityEvent {
  icon?: React.ReactNode;
  color?: string;
}

interface RealtimeActivityFeedProps {
  initialActivities?: ActivityFeedItem[];
  maxItems?: number;
  autoScroll?: boolean;
  showTimestamps?: boolean;
  filterTypes?: string[];
  className?: string;
}

export function RealtimeActivityFeed({
  initialActivities = [],
  maxItems = 50,
  autoScroll = true,
  showTimestamps = true,
  filterTypes,
  className
}: RealtimeActivityFeedProps) {
  const [activities, setActivities] = useState<ActivityFeedItem[]>(initialActivities);
  const [isPaused, setIsPaused] = useState(false);
  const [newItemsCount, setNewItemsCount] = useState(0);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  
  // Batch updates for throttling
  const pendingEventsRef = useRef<ActivityFeedItem[]>([]);

  // Flush pending events to state (throttled to 100ms)
  const flushPendingEvents = useCallback(() => {
    if (pendingEventsRef.current.length === 0) return;

    const eventsToAdd = [...pendingEventsRef.current];
    pendingEventsRef.current = [];

    setActivities(prev => {
      const newActivities = [...eventsToAdd.reverse(), ...prev];
      // Keep only the most recent items
      return newActivities.slice(0, maxItems);
    });

    if (isPaused) {
      setNewItemsCount(prev => prev + eventsToAdd.length);
    }
  }, [isPaused, maxItems]);

  // Create throttled version of flush function
  const throttledFlush = useThrottle(flushPendingEvents, 100);

  // Handle real-time activity updates
  const { isConnected } = useActivityFeed((event: ActivityEvent) => {
    const activityItem = enrichActivityEvent(event);
    
    if (filterTypes && !filterTypes.includes(event.type)) {
      return;
    }

    // Add to pending events and trigger throttled flush
    pendingEventsRef.current.push(activityItem);
    throttledFlush();
  });

  // Auto-scroll to top when new items arrive (if not paused)
  useEffect(() => {
    if (autoScroll && !isPaused && activities.length > 0) {
      scrollAreaRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [activities, autoScroll, isPaused]);

  // Enrich activity event with icon and color based on type
  function enrichActivityEvent(event: ActivityEvent): ActivityFeedItem {
    let icon: React.ReactNode;
    let color: string;

    switch (event.type) {
      case 'incident.created':
        icon = <AlertCircle className="h-4 w-4" />;
        color = 'text-red-500';
        break;
      case 'incident.resolved':
        icon = <CheckCircle className="h-4 w-4" />;
        color = 'text-green-500';
        break;
      case 'agent.joined':
        icon = <UserPlus className="h-4 w-4" />;
        color = 'text-blue-500';
        break;
      case 'config.updated':
        icon = <Settings className="h-4 w-4" />;
        color = 'text-purple-500';
        break;
      case 'security.alert':
        icon = <Shield className="h-4 w-4" />;
        color = 'text-orange-500';
        break;
      case 'performance.spike':
        icon = <Zap className="h-4 w-4" />;
        color = 'text-yellow-500';
        break;
      case 'report.generated':
        icon = <FileText className="h-4 w-4" />;
        color = 'text-gray-500';
        break;
      default:
        icon = <Info className="h-4 w-4" />;
        color = 'text-gray-500';
    }

    return {
      ...event,
      icon,
      color
    };
  }

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);

    if (diffSecs < 60) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    
    return date.toLocaleString();
  };

  const getActionDescription = (activity: ActivityFeedItem) => {
    // Custom formatting based on activity type
    switch (activity.type) {
      case 'incident.created':
        return `created incident "${activity.target}"`;
      case 'incident.resolved':
        return `resolved incident "${activity.target}"`;
      case 'agent.joined':
        return `joined the team`;
      case 'config.updated':
        return `updated ${activity.target} configuration`;
      case 'security.alert':
        return `triggered security alert: ${activity.action}`;
      case 'performance.spike':
        return `detected performance spike in ${activity.target}`;
      case 'report.generated':
        return `generated ${activity.target} report`;
      default:
        return activity.action;
    }
  };

  const handleResume = () => {
    setIsPaused(false);
    setNewItemsCount(0);
  };

  return (
    <div className={cn('flex flex-col h-full bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800', className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          <h3 className="font-semibold">Activity Feed</h3>
          {isConnected && (
            <Badge variant="default" className="bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">
              Live
            </Badge>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsPaused(!isPaused)}
        >
          {isPaused ? 'Resume' : 'Pause'}
        </Button>
      </div>

      {/* New items notification */}
      {isPaused && newItemsCount > 0 && (
        <div className="px-4 py-2 bg-blue-50 dark:bg-blue-950 border-b border-blue-200 dark:border-blue-800">
          <button
            onClick={handleResume}
            className="text-sm text-blue-700 dark:text-blue-300 hover:underline"
          >
            {newItemsCount} new {newItemsCount === 1 ? 'activity' : 'activities'} - Click to view
          </button>
        </div>
      )}

      {/* Activity list */}
      <ScrollArea className="flex-1" ref={scrollAreaRef}>
        <div className="p-4 space-y-3">
          {activities.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No activities yet</p>
            </div>
          ) : (
            activities.map((activity, index) => (
              <div
                key={activity.id}
                className={cn(
                  'flex gap-3 p-3 rounded-lg transition-all',
                  'hover:bg-gray-50 dark:hover:bg-gray-800',
                  index === 0 && !isPaused && 'animate-slide-in-top'
                )}
              >
                <div className={cn('mt-0.5', activity.color)}>
                  {activity.icon}
                </div>
                
                <div className="flex-1 min-w-0">
                  <p className="text-sm">
                    <span className="font-medium">{activity.actor}</span>
                    {' '}
                    <span className="text-muted-foreground">
                      {getActionDescription(activity)}
                    </span>
                  </p>
                  
                  {activity.metadata && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {Object.entries(activity.metadata).map(([key, value]) => (
                        <Badge key={key} variant="secondary" className="text-xs">
                          {key}: {String(value)}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>

                {showTimestamps && (
                  <div className="text-xs text-muted-foreground whitespace-nowrap">
                    {formatTimestamp(activity.timestamp)}
                  </div>
                )}
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      {!isConnected && (
        <div className="p-2 text-center text-xs text-muted-foreground border-t border-gray-200 dark:border-gray-800">
          Real-time updates unavailable
        </div>
      )}
    </div>
  );
}