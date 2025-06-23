'use client'

import React, { useState } from 'react'
import { motion, PanInfo } from 'framer-motion'
import {
  AlertCircle,
  CheckCircle,
  Clock,
  MessageSquare,
  ChevronDown,
  ChevronUp,
  Shield,
  TrendingUp,
  User,
  Calendar
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { SeverityBadge } from '@/components/incidents/severity-badge'
import { StatusBadge } from '@/components/incidents/status-badge'
import type { Incident } from '@/types/incident'

interface MobileIncidentCardProps {
  incident: Incident
  onAcknowledge?: (id: string) => void
  onEscalate?: (id: string) => void
  onResolve?: (id: string) => void
  onChat?: (id: string) => void
}

export function MobileIncidentCard({
  incident,
  onAcknowledge,
  onEscalate,
  onResolve,
  onChat
}: MobileIncidentCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [swipeDirection, setSwipeDirection] = useState<'left' | 'right' | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleDragEnd = (event: any, info: PanInfo) => {
    const threshold = 100
    
    if (info.offset.x > threshold) {
      // Swipe right - Acknowledge
      if (onAcknowledge && incident.status === 'open') {
        onAcknowledge(incident.id)
      }
    } else if (info.offset.x < -threshold) {
      // Swipe left - Escalate
      if (onEscalate) {
        onEscalate(incident.id)
      }
    }
    
    setSwipeDirection(null)
    setIsDragging(false)
  }

  const handleDrag = (event: any, info: PanInfo) => {
    setIsDragging(true)
    if (info.offset.x > 50) {
      setSwipeDirection('right')
    } else if (info.offset.x < -50) {
      setSwipeDirection('left')
    } else {
      setSwipeDirection(null)
    }
  }

  const formatTime = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (days > 0) return `${days}d ago`
    if (hours > 0) return `${hours}h ago`
    return `${minutes}m ago`
  }

  return (
    <motion.div
      drag="x"
      dragConstraints={{ left: -100, right: 100 }}
      dragElastic={0.2}
      onDrag={handleDrag}
      onDragEnd={handleDragEnd}
      animate={{
        x: 0,
        backgroundColor: 
          swipeDirection === 'right' ? 'rgba(34, 197, 94, 0.1)' :
          swipeDirection === 'left' ? 'rgba(239, 68, 68, 0.1)' :
          'transparent'
      }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="relative"
    >
      {/* Swipe Action Indicators */}
      <div className="absolute inset-0 flex items-center justify-between px-4 pointer-events-none">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ 
            opacity: swipeDirection === 'right' ? 1 : 0,
            scale: swipeDirection === 'right' ? 1 : 0.8
          }}
          className="flex items-center gap-2 text-green-600"
        >
          <CheckCircle className="h-5 w-5" />
          <span className="font-medium">Acknowledge</span>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ 
            opacity: swipeDirection === 'left' ? 1 : 0,
            scale: swipeDirection === 'left' ? 1 : 0.8
          }}
          className="flex items-center gap-2 text-red-600"
        >
          <span className="font-medium">Escalate</span>
          <TrendingUp className="h-5 w-5" />
        </motion.div>
      </div>

      <Card className={cn(
        "overflow-hidden transition-shadow duration-200",
        isDragging && "shadow-lg"
      )}>
        <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
          {/* Card Header */}
          <div className="p-4">
            <div className="flex items-start justify-between gap-2 mb-3">
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-sm truncate pr-2">
                  {incident.title}
                </h3>
                <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  <span>{formatTime(incident.createdAt)}</span>
                  <span>•</span>
                  <span>{incident.source}</span>
                </div>
              </div>
              <SeverityBadge severity={incident.severity} />
            </div>

            <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
              {incident.description}
            </p>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <StatusBadge status={incident.status} />
                {incident.assignedTo && (
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <User className="h-3 w-3" />
                    <span>{incident.assignedTo}</span>
                  </div>
                )}
              </div>
              
              <CollapsibleTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="sm"
                  className="h-8 w-8 p-0"
                >
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </Button>
              </CollapsibleTrigger>
            </div>
          </div>

          {/* Collapsible Details */}
          <CollapsibleContent>
            <div className="px-4 pb-4 pt-2 border-t border-border">
              {/* Additional Details */}
              <div className="space-y-3 mb-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Type:</span>
                  <Badge variant="outline">{incident.type}</Badge>
                </div>
                
                {incident.affectedServices && incident.affectedServices.length > 0 && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Affected:</span>
                    <div className="flex gap-1">
                      {incident.affectedServices.slice(0, 2).map(service => (
                        <Badge key={service} variant="secondary" className="text-xs">
                          {service}
                        </Badge>
                      ))}
                      {incident.affectedServices.length > 2 && (
                        <Badge variant="secondary" className="text-xs">
                          +{incident.affectedServices.length - 2}
                        </Badge>
                      )}
                    </div>
                  </div>
                )}

                {incident.metrics && (
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {incident.metrics.responseTime && (
                      <div>
                        <span className="text-muted-foreground">Response:</span>
                        <span className="ml-1 font-medium">{incident.metrics.responseTime}ms</span>
                      </div>
                    )}
                    {incident.metrics.errorRate && (
                      <div>
                        <span className="text-muted-foreground">Error Rate:</span>
                        <span className="ml-1 font-medium">{incident.metrics.errorRate}%</span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-2 gap-2">
                {incident.status === 'open' && onAcknowledge && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onAcknowledge(incident.id)}
                    className="h-10"
                  >
                    <CheckCircle className="h-4 w-4 mr-1" />
                    Acknowledge
                  </Button>
                )}
                
                {onEscalate && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onEscalate(incident.id)}
                    className="h-10"
                  >
                    <TrendingUp className="h-4 w-4 mr-1" />
                    Escalate
                  </Button>
                )}
                
                {incident.status !== 'resolved' && onResolve && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onResolve(incident.id)}
                    className="h-10"
                  >
                    <Shield className="h-4 w-4 mr-1" />
                    Resolve
                  </Button>
                )}
                
                {onChat && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onChat(incident.id)}
                    className="h-10"
                  >
                    <MessageSquare className="h-4 w-4 mr-1" />
                    AI Chat
                  </Button>
                )}
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </Card>
    </motion.div>
  )
}

export default MobileIncidentCard