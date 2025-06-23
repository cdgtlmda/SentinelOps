"use client"

import React, { useRef, useEffect, useState, useCallback } from 'react'
import { cn } from '@/lib/utils'
import { usePanelState } from '@/hooks/use-panel-state'
import { PanelHeader } from './panel-header'

interface SplitScreenProps {
  leftPanel: {
    id: string
    title: string
    content: React.ReactNode
    actions?: React.ReactNode
    minWidth?: number
    maxWidth?: number
  }
  rightPanel: {
    id: string
    title: string
    content: React.ReactNode
    actions?: React.ReactNode
    minWidth?: number
    maxWidth?: number
  }
  defaultLeftWidth?: number
  className?: string
}

export function SplitScreen({
  leftPanel,
  rightPanel,
  defaultLeftWidth = 50,
  className
}: SplitScreenProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  
  const {
    leftWidth,
    setLeftWidth,
    leftCollapsed,
    rightCollapsed,
    toggleLeftPanel,
    toggleRightPanel,
    activePanel,
    setActivePanel
  } = usePanelState(leftPanel.id, rightPanel.id, defaultLeftWidth)

  // Check if mobile on mount and resize
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Handle drag resize
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  useEffect(() => {
    if (!isDragging) return

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return
      
      const containerRect = containerRef.current.getBoundingClientRect()
      const newLeftWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100
      
      // Apply constraints
      const minLeft = leftPanel.minWidth || 20
      const maxLeft = leftPanel.maxWidth || 80
      const minRight = rightPanel.minWidth || 20
      const maxRight = rightPanel.maxWidth || 80
      
      const rightWidth = 100 - newLeftWidth
      
      if (newLeftWidth >= minLeft && newLeftWidth <= maxLeft && 
          rightWidth >= minRight && rightWidth <= maxRight) {
        setLeftWidth(newLeftWidth)
      }
    }

    const handleMouseUp = () => {
      setIsDragging(false)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDragging, setLeftWidth, leftPanel.minWidth, leftPanel.maxWidth, rightPanel.minWidth, rightPanel.maxWidth])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + [ to toggle left panel
      if ((e.metaKey || e.ctrlKey) && e.key === '[') {
        e.preventDefault()
        toggleLeftPanel()
      }
      // Cmd/Ctrl + ] to toggle right panel
      if ((e.metaKey || e.ctrlKey) && e.key === ']') {
        e.preventDefault()
        toggleRightPanel()
      }
      // Cmd/Ctrl + \ to reset layout
      if ((e.metaKey || e.ctrlKey) && e.key === '\\') {
        e.preventDefault()
        setLeftWidth(defaultLeftWidth)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [toggleLeftPanel, toggleRightPanel, setLeftWidth, defaultLeftWidth])

  // Mobile stacked layout
  if (isMobile) {
    return (
      <div className={cn("flex flex-col h-full", className)}>
        <div className="flex border-b">
          <button
            onClick={() => setActivePanel('left')}
            className={cn(
              "flex-1 px-4 py-3 text-sm font-medium transition-colors",
              activePanel === 'left' 
                ? "bg-background border-b-2 border-primary" 
                : "bg-muted/50 hover:bg-muted"
            )}
          >
            {leftPanel.title}
          </button>
          <button
            onClick={() => setActivePanel('right')}
            className={cn(
              "flex-1 px-4 py-3 text-sm font-medium transition-colors",
              activePanel === 'right' 
                ? "bg-background border-b-2 border-primary" 
                : "bg-muted/50 hover:bg-muted"
            )}
          >
            {rightPanel.title}
          </button>
        </div>
        
        <div className="flex-1 overflow-hidden">
          {activePanel === 'left' ? (
            <div className="h-full overflow-auto p-4">
              {leftPanel.content}
            </div>
          ) : (
            <div className="h-full overflow-auto p-4">
              {rightPanel.content}
            </div>
          )}
        </div>
      </div>
    )
  }

  // Desktop split layout
  const effectiveLeftWidth = leftCollapsed ? 0 : (rightCollapsed ? 100 : leftWidth)
  const effectiveRightWidth = rightCollapsed ? 0 : (leftCollapsed ? 100 : (100 - leftWidth))

  return (
    <div 
      ref={containerRef}
      className={cn("flex h-full relative", className)}
    >
      {/* Left Panel */}
      <div 
        className={cn(
          "relative overflow-hidden transition-all duration-300 ease-in-out",
          leftCollapsed && "opacity-0 pointer-events-none"
        )}
        style={{ width: `${effectiveLeftWidth}%` }}
      >
        <PanelHeader
          title={leftPanel.title}
          isCollapsed={leftCollapsed}
          onToggleCollapse={toggleLeftPanel}
          actions={leftPanel.actions}
          position="left"
        />
        <div className="h-[calc(100%-3.5rem)] overflow-auto p-4">
          {leftPanel.content}
        </div>
      </div>

      {/* Resize Handle */}
      {!leftCollapsed && !rightCollapsed && (
        <div
          className={cn(
            "relative w-1 cursor-col-resize hover:bg-primary/20 transition-colors group",
            isDragging && "bg-primary/20"
          )}
          onMouseDown={handleMouseDown}
        >
          <div className="absolute inset-y-0 -left-1 -right-1 group-hover:bg-primary/10" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1 h-8 bg-border rounded-full opacity-50 group-hover:opacity-100 transition-opacity" />
        </div>
      )}

      {/* Right Panel */}
      <div 
        className={cn(
          "relative overflow-hidden transition-all duration-300 ease-in-out",
          rightCollapsed && "opacity-0 pointer-events-none"
        )}
        style={{ width: `${effectiveRightWidth}%` }}
      >
        <PanelHeader
          title={rightPanel.title}
          isCollapsed={rightCollapsed}
          onToggleCollapse={toggleRightPanel}
          actions={rightPanel.actions}
          position="right"
        />
        <div className="h-[calc(100%-3.5rem)] overflow-auto p-4">
          {rightPanel.content}
        </div>
      </div>

      {/* Collapsed Panel Indicators */}
      {leftCollapsed && (
        <button
          onClick={toggleLeftPanel}
          className="absolute left-0 top-1/2 -translate-y-1/2 w-6 h-24 bg-border hover:bg-primary/20 transition-colors rounded-r-md flex items-center justify-center"
          aria-label="Expand left panel"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      )}
      
      {rightCollapsed && (
        <button
          onClick={toggleRightPanel}
          className="absolute right-0 top-1/2 -translate-y-1/2 w-6 h-24 bg-border hover:bg-primary/20 transition-colors rounded-l-md flex items-center justify-center"
          aria-label="Expand right panel"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      )}
    </div>
  )
}