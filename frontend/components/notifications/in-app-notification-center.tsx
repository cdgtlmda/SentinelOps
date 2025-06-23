/**
 * In-App Notification Center Component
 * Displays notification feed with grouping, priority, and actions
 */

import React, { useState, useMemo } from 'react'
import { 
  Bell, 
  Check, 
  CheckCheck, 
  AlertCircle, 
  Info, 
  AlertTriangle, 
  X,
  Filter,
  MoreHorizontal,
  ExternalLink,
  Archive,
  Settings
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'

export interface Notification {
  id: string
  title: string
  message: string
  type: 'incident' | 'alert' | 'update' | 'info'
  priority: 'critical' | 'high' | 'medium' | 'low'
  timestamp: Date
  read: boolean
  actionUrl?: string
  actionLabel?: string
  groupId?: string
  metadata?: Record<string, any>
}

interface NotificationGroup {
  id: string
  title: string
  notifications: Notification[]
  timestamp: Date
}

interface InAppNotificationCenterProps {
  notifications: Notification[]
  onMarkAsRead: (id: string) => void
  onMarkAllAsRead: () => void
  onArchive: (id: string) => void
  onActionClick?: (notification: Notification) => void
  onSettingsClick?: () => void
}

export function InAppNotificationCenter({
  notifications,
  onMarkAsRead,
  onMarkAllAsRead,
  onArchive,
  onActionClick,
  onSettingsClick
}: InAppNotificationCenterProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [filter, setFilter] = useState<'all' | 'unread'>('all')

  // Calculate unread count
  const unreadCount = notifications.filter(n => !n.read).length

  // Filter notifications
  const filteredNotifications = useMemo(() => {
    if (filter === 'unread') {
      return notifications.filter(n => !n.read)
    }
    return notifications
  }, [notifications, filter])

  // Group notifications
  const groupedNotifications = useMemo(() => {
    const groups = new Map<string, NotificationGroup>()
    
    filteredNotifications.forEach(notification => {
      const groupId = notification.groupId || notification.id
      
      if (!groups.has(groupId)) {
        groups.set(groupId, {
          id: groupId,
          title: notification.title,
          notifications: [],
          timestamp: notification.timestamp
        })
      }
      
      groups.get(groupId)!.notifications.push(notification)
    })

    return Array.from(groups.values()).sort((a, b) => 
      b.timestamp.getTime() - a.timestamp.getTime()
    )
  }, [filteredNotifications])

  const getPriorityIcon = (priority: Notification['priority']) => {
    switch (priority) {
      case 'critical':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      case 'high':
        return <AlertTriangle className="h-4 w-4 text-orange-500" />
      case 'medium':
        return <Info className="h-4 w-4 text-blue-500" />
      case 'low':
        return <Info className="h-4 w-4 text-gray-500" />
    }
  }

  const getPriorityColor = (priority: Notification['priority']) => {
    switch (priority) {
      case 'critical': return 'destructive'
      case 'high': return 'warning'
      case 'medium': return 'default'
      case 'low': return 'secondary'
    }
  }

  const getTypeIcon = (type: Notification['type']) => {
    switch (type) {
      case 'incident':
        return <AlertCircle className="h-4 w-4" />
      case 'alert':
        return <AlertTriangle className="h-4 w-4" />
      case 'update':
        return <Info className="h-4 w-4" />
      case 'info':
        return <Info className="h-4 w-4" />
    }
  }

  const renderNotification = (notification: Notification) => (
    <div
      key={notification.id}
      className={cn(
        "p-4 border-b last:border-b-0 transition-colors",
        !notification.read && "bg-muted/50"
      )}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          {getPriorityIcon(notification.priority)}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="text-sm font-medium">{notification.title}</h4>
                <Badge variant={getPriorityColor(notification.priority)} className="text-xs">
                  {notification.priority}
                </Badge>
                {!notification.read && (
                  <span className="h-2 w-2 bg-primary rounded-full" />
                )}
              </div>
              
              <p className="text-sm text-muted-foreground">{notification.message}</p>
              
              <div className="flex items-center gap-4 mt-2">
                <span className="text-xs text-muted-foreground">
                  {formatDistanceToNow(notification.timestamp, { addSuffix: true })}
                </span>
                
                {notification.actionUrl && (
                  <Button
                    variant="link"
                    size="sm"
                    className="h-auto p-0 text-xs"
                    onClick={() => onActionClick?.(notification)}
                  >
                    {notification.actionLabel || 'View'}
                    <ExternalLink className="h-3 w-3 ml-1" />
                  </Button>
                )}
              </div>
            </div>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {!notification.read && (
                  <DropdownMenuItem onClick={() => onMarkAsRead(notification.id)}>
                    <Check className="h-4 w-4 mr-2" />
                    Mark as read
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem onClick={() => onArchive(notification.id)}>
                  <Archive className="h-4 w-4 mr-2" />
                  Archive
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </div>
  )

  const renderNotificationGroup = (group: NotificationGroup) => {
    if (group.notifications.length === 1) {
      return renderNotification(group.notifications[0])
    }

    const unreadInGroup = group.notifications.filter(n => !n.read).length

    return (
      <div key={group.id} className="border-b last:border-b-0">
        <div className="p-4 bg-muted/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-medium">{group.title}</h4>
              <Badge variant="secondary" className="text-xs">
                {group.notifications.length} notifications
              </Badge>
              {unreadInGroup > 0 && (
                <Badge variant="default" className="text-xs">
                  {unreadInGroup} unread
                </Badge>
              )}
            </div>
            <span className="text-xs text-muted-foreground">
              {formatDistanceToNow(group.timestamp, { addSuffix: true })}
            </span>
          </div>
        </div>
        <div className="divide-y">
          {group.notifications.map(notification => (
            <div key={notification.id} className="pl-8">
              {renderNotification(notification)}
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-destructive text-destructive-foreground text-xs flex items-center justify-center">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </Button>
      </SheetTrigger>
      
      <SheetContent className="w-full sm:max-w-lg p-0">
        <SheetHeader className="p-6 pb-4">
          <div className="flex items-center justify-between">
            <SheetTitle>Notifications</SheetTitle>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onMarkAllAsRead}
                >
                  <CheckCheck className="h-4 w-4 mr-2" />
                  Mark all read
                </Button>
              )}
              {onSettingsClick && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onSettingsClick}
                >
                  <Settings className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
          <SheetDescription>
            Stay updated with incidents, alerts, and system updates
          </SheetDescription>
        </SheetHeader>
        
        <Tabs value={filter} onValueChange={(v) => setFilter(v as 'all' | 'unread')} className="flex-1">
          <TabsList className="w-full rounded-none border-b">
            <TabsTrigger value="all" className="flex-1">
              All
              {notifications.length > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {notifications.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="unread" className="flex-1">
              Unread
              {unreadCount > 0 && (
                <Badge variant="default" className="ml-2">
                  {unreadCount}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value={filter} className="m-0 flex-1">
            <ScrollArea className="h-[calc(100vh-200px)]">
              {groupedNotifications.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">
                  <Bell className="h-12 w-12 mx-auto mb-4 opacity-20" />
                  <p className="text-sm">
                    {filter === 'unread' ? 'No unread notifications' : 'No notifications yet'}
                  </p>
                </div>
              ) : (
                <div>
                  {groupedNotifications.map(group => renderNotificationGroup(group))}
                </div>
              )}
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  )
}