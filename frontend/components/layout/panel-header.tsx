"use client"

import React from 'react'
import { cn } from '@/lib/utils'

interface PanelHeaderProps {
  title: string
  isCollapsed: boolean
  onToggleCollapse: () => void
  actions?: React.ReactNode
  position: 'left' | 'right'
  className?: string
}

export function PanelHeader({
  title,
  isCollapsed,
  onToggleCollapse,
  actions,
  position,
  className
}: PanelHeaderProps) {
  return (
    <div className={cn(
      "flex items-center justify-between h-14 px-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60",
      className
    )}>
      <div className="flex items-center gap-2">
        <h2 className="text-lg font-semibold">{title}</h2>
      </div>
      
      <div className="flex items-center gap-2">
        {actions}
        
        <button
          onClick={onToggleCollapse}
          className="p-2 hover:bg-accent rounded-md transition-colors"
          aria-label={isCollapsed ? `Expand ${title}` : `Collapse ${title}`}
          title={`${isCollapsed ? 'Expand' : 'Collapse'} panel (${position === 'left' ? 'Cmd+[' : 'Cmd+]'})`}
        >
          {position === 'left' ? (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d={isCollapsed ? "M9 5l7 7-7 7" : "M15 19l-7-7 7-7"} 
              />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d={isCollapsed ? "M15 19l-7-7 7-7" : "M9 5l7 7-7 7"} 
              />
            </svg>
          )}
        </button>
      </div>
    </div>
  )
}