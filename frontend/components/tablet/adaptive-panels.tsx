"use client"

import React, { useState, useRef, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { ChevronLeft, ChevronRight, ChevronUp, ChevronDown, GripVertical, GripHorizontal } from 'lucide-react'

interface AdaptivePanelsProps {
  primaryPanel?: React.ReactNode
  secondaryPanel?: React.ReactNode
  orientation: 'portrait' | 'landscape'
  className?: string
  defaultSecondaryWidth?: number
  defaultSecondaryHeight?: number
  minSecondaryWidth?: number
  maxSecondaryWidth?: number
  minSecondaryHeight?: number
  maxSecondaryHeight?: number
  stacked?: boolean
  priority?: 'primary' | 'secondary'
  onResize?: (size: number) => void
}

export function AdaptivePanels({
  primaryPanel,
  secondaryPanel,
  orientation,
  className,
  defaultSecondaryWidth = 350,
  defaultSecondaryHeight = 300,
  minSecondaryWidth = 250,
  maxSecondaryWidth = 600,
  minSecondaryHeight = 200,
  maxSecondaryHeight = 500,
  stacked = false,
  priority = 'primary',
  onResize
}: AdaptivePanelsProps) {
  const [secondarySize, setSecondarySize] = useState(
    orientation === 'landscape' ? defaultSecondaryWidth : defaultSecondaryHeight
  )
  const [isSecondaryCollapsed, setIsSecondaryCollapsed] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const startPosRef = useRef<number>(0)
  const startSizeRef = useRef<number>(0)

  const isHorizontal = orientation === 'landscape' && !stacked

  useEffect(() => {
    if (onResize) {
      onResize(secondarySize)
    }
  }, [secondarySize, onResize])

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault()
    setIsDragging(true)
    startPosRef.current = isHorizontal ? e.clientX : e.clientY
    startSizeRef.current = secondarySize
  }

  useEffect(() => {
    if (!isDragging) return

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return

      const delta = isHorizontal 
        ? startPosRef.current - e.clientX
        : startPosRef.current - e.clientY

      const newSize = startSizeRef.current + delta
      const minSize = isHorizontal ? minSecondaryWidth : minSecondaryHeight
      const maxSize = isHorizontal ? maxSecondaryWidth : maxSecondaryHeight

      setSecondarySize(Math.max(minSize, Math.min(maxSize, newSize)))
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
  }, [isDragging, isHorizontal, minSecondaryWidth, maxSecondaryWidth, minSecondaryHeight, maxSecondaryHeight])

  const toggleCollapse = () => {
    setIsSecondaryCollapsed(!isSecondaryCollapsed)
  }

  if (!secondaryPanel) {
    return <div className={cn("flex-1 overflow-hidden", className)}>{primaryPanel}</div>
  }

  const renderResizeHandle = () => (
    <div
      className={cn(
        "group flex items-center justify-center bg-gray-100 hover:bg-gray-200 transition-colors cursor-col-resize select-none",
        isHorizontal ? "w-2 h-full" : "h-2 w-full cursor-row-resize",
        isDragging && "bg-blue-200"
      )}
      onMouseDown={handleMouseDown}
    >
      {isHorizontal ? (
        <GripVertical className="w-4 h-4 text-gray-400 group-hover:text-gray-600" />
      ) : (
        <GripHorizontal className="w-4 h-4 text-gray-400 group-hover:text-gray-600" />
      )}
    </div>
  )

  const renderCollapseButton = () => (
    <button
      onClick={toggleCollapse}
      className={cn(
        "absolute z-10 p-1 bg-white border rounded-md shadow-sm hover:bg-gray-50 transition-colors",
        isHorizontal 
          ? "left-0 top-1/2 -translate-y-1/2 -translate-x-1/2"
          : "left-1/2 top-0 -translate-x-1/2 -translate-y-1/2"
      )}
    >
      {isHorizontal ? (
        isSecondaryCollapsed ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />
      ) : (
        isSecondaryCollapsed ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
      )}
    </button>
  )

  return (
    <div 
      ref={containerRef}
      className={cn(
        "flex overflow-hidden relative",
        isHorizontal ? "flex-row" : "flex-col",
        className
      )}
    >
      {/* Primary Panel */}
      <div className={cn(
        "overflow-hidden",
        priority === 'primary' ? "flex-1" : isHorizontal ? "w-auto" : "h-auto"
      )}>
        {primaryPanel}
      </div>

      {/* Resize Handle and Secondary Panel */}
      {!isSecondaryCollapsed && (
        <>
          {renderResizeHandle()}
          <div 
            className={cn(
              "overflow-hidden bg-white border-gray-200 relative",
              isHorizontal 
                ? `border-l` 
                : `border-t`,
              priority === 'secondary' ? "flex-1" : ""
            )}
            style={{
              [isHorizontal ? 'width' : 'height']: 
                priority === 'secondary' ? 'auto' : `${secondarySize}px`
            }}
          >
            {renderCollapseButton()}
            {secondaryPanel}
          </div>
        </>
      )}

      {/* Collapsed State */}
      {isSecondaryCollapsed && (
        <div 
          className={cn(
            "relative bg-gray-100",
            isHorizontal ? "w-12 border-l" : "h-12 border-t"
          )}
        >
          {renderCollapseButton()}
        </div>
      )}
    </div>
  )
}

// Dynamic Panel Stack for Multiple Panels
interface PanelStackProps {
  panels: Array<{
    id: string
    title: string
    content: React.ReactNode
    priority?: number
    minSize?: number
    collapsible?: boolean
  }>
  orientation: 'portrait' | 'landscape'
  className?: string
}

export function PanelStack({ panels, orientation, className }: PanelStackProps) {
  const [collapsedPanels, setCollapsedPanels] = useState<Set<string>>(new Set())
  
  const sortedPanels = [...panels].sort((a, b) => 
    (b.priority || 0) - (a.priority || 0)
  )

  const togglePanel = (id: string) => {
    setCollapsedPanels(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  return (
    <div className={cn(
      "flex",
      orientation === 'landscape' ? "flex-row" : "flex-col",
      className
    )}>
      {sortedPanels.map((panel, index) => (
        <React.Fragment key={panel.id}>
          {index > 0 && (
            <div className={cn(
              "bg-gray-200",
              orientation === 'landscape' ? "w-px" : "h-px"
            )} />
          )}
          <div 
            className={cn(
              "relative",
              collapsedPanels.has(panel.id) 
                ? orientation === 'landscape' ? "w-12" : "h-12"
                : "flex-1"
            )}
          >
            {panel.collapsible !== false && (
              <button
                onClick={() => togglePanel(panel.id)}
                className="absolute top-2 right-2 z-10 p-1 bg-white border rounded shadow-sm hover:bg-gray-50"
              >
                {collapsedPanels.has(panel.id) ? (
                  orientation === 'landscape' ? <ChevronLeft className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />
                ) : (
                  orientation === 'landscape' ? <ChevronRight className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
                )}
              </button>
            )}
            {!collapsedPanels.has(panel.id) && (
              <div className="h-full overflow-auto p-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">{panel.title}</h3>
                {panel.content}
              </div>
            )}
          </div>
        </React.Fragment>
      ))}
    </div>
  )
}