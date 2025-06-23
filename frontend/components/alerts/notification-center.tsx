'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Alert, AlertType, NotificationGroup } from '@/types/alerts';
import { Bell, X, Check, ChevronDown, ChevronRight, Trash2, CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

interface NotificationCenterProps {
  alerts: Alert[];
  onMarkAsRead: (id: string) => void;
  onMarkAllAsRead: () => void;
  onClearAll: () => void;
  onDismiss: (id: string) => void;
}

const iconMap: Record<AlertType, React.ReactNode> = {
  success: <CheckCircle className="w-4 h-4" />,
  error: <XCircle className="w-4 h-4" />,
  warning: <AlertTriangle className="w-4 h-4" />,
  info: <Info className="w-4 h-4" />,
};

const iconColorMap: Record<AlertType, string> = {
  success: 'text-green-600 dark:text-green-400',
  error: 'text-red-600 dark:text-red-400',
  warning: 'text-yellow-600 dark:text-yellow-400',
  info: 'text-blue-600 dark:text-blue-400',
};

export function NotificationCenter({ 
  alerts, 
  onMarkAsRead, 
  onMarkAllAsRead, 
  onClearAll,
  onDismiss 
}: NotificationCenterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [groups, setGroups] = useState<NotificationGroup[]>([]);
  const panelRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Group alerts by date
  useEffect(() => {
    const grouped = alerts.reduce((acc, alert) => {
      const date = format(alert.timestamp, 'yyyy-MM-dd');
      const existingGroup = acc.find(g => g.id === date);
      
      if (existingGroup) {
        existingGroup.alerts.push(alert);
      } else {
        acc.push({
          id: date,
          title: format(alert.timestamp, 'MMMM d, yyyy'),
          alerts: [alert],
          collapsed: false,
        });
      }
      
      return acc;
    }, [] as NotificationGroup[]);

    // Sort groups by date (newest first)
    grouped.sort((a, b) => b.id.localeCompare(a.id));
    
    // Sort alerts within each group by timestamp (newest first)
    grouped.forEach(group => {
      group.alerts.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
    });

    setGroups(grouped);
  }, [alerts]);

  // Close panel when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        panelRef.current && 
        !panelRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        setIsOpen(false);
        buttonRef.current?.focus();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen]);

  const unreadCount = alerts.filter(a => !a.read).length;

  const toggleGroup = (groupId: string) => {
    setGroups(prev => prev.map(group => 
      group.id === groupId 
        ? { ...group, collapsed: !group.collapsed }
        : group
    ));
  };

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        aria-label={`Notifications ${unreadCount > 0 ? `(${unreadCount} unread)` : ''}`}
        aria-expanded={isOpen}
        aria-controls="notification-panel"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div
          ref={panelRef}
          id="notification-panel"
          className={cn(
            'absolute right-0 mt-2 w-96 max-h-[600px] bg-white dark:bg-gray-900 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden',
            'animate-slide-in-panel'
          )}
          style={{ zIndex: 'var(--z-notification-center)' }}
          role="dialog"
          aria-label="Notifications"
        >
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Notifications</h2>
              <div className="flex items-center gap-2">
                {unreadCount > 0 && (
                  <button
                    onClick={onMarkAllAsRead}
                    className="text-sm text-blue-600 dark:text-blue-400 hover:underline focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 rounded"
                    aria-label="Mark all as read"
                  >
                    <Check className="w-4 h-4" />
                  </button>
                )}
                {alerts.length > 0 && (
                  <button
                    onClick={onClearAll}
                    className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 rounded"
                    aria-label="Clear all notifications"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 rounded"
                  aria-label="Close notifications"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="overflow-y-auto max-h-[500px]">
            {alerts.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                <Bell className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No notifications</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {groups.map(group => (
                  <div key={group.id}>
                    <button
                      onClick={() => toggleGroup(group.id)}
                      className="w-full px-4 py-2 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-sm font-medium text-gray-700 dark:text-gray-300"
                      aria-expanded={!group.collapsed}
                    >
                      <span>{group.title}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {group.alerts.length}
                        </span>
                        {group.collapsed ? (
                          <ChevronRight className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                      </div>
                    </button>
                    
                    {!group.collapsed && (
                      <div className="divide-y divide-gray-100 dark:divide-gray-800">
                        {group.alerts.map(alert => (
                          <div
                            key={alert.id}
                            className={cn(
                              'px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors',
                              !alert.read && 'bg-blue-50/50 dark:bg-blue-900/10'
                            )}
                          >
                            <div className="flex items-start gap-3">
                              <div className={cn('flex-shrink-0 mt-0.5', iconColorMap[alert.type])}>
                                {iconMap[alert.type]}
                              </div>
                              
                              <div className="flex-1 min-w-0">
                                <h3 className={cn(
                                  'text-sm font-medium',
                                  !alert.read && 'text-gray-900 dark:text-gray-100'
                                )}>
                                  {alert.title}
                                </h3>
                                {alert.message && (
                                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                                    {alert.message}
                                  </p>
                                )}
                                <p className="mt-1 text-xs text-gray-500 dark:text-gray-500">
                                  {format(alert.timestamp, 'h:mm a')}
                                </p>
                              </div>
                              
                              <div className="flex items-center gap-1">
                                {!alert.read && (
                                  <button
                                    onClick={() => onMarkAsRead(alert.id)}
                                    className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                    aria-label="Mark as read"
                                  >
                                    <Check className="w-3 h-3" />
                                  </button>
                                )}
                                <button
                                  onClick={() => onDismiss(alert.id)}
                                  className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                  aria-label="Dismiss notification"
                                >
                                  <X className="w-3 h-3" />
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}