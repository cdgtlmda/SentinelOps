"use client"

import React from 'react'
import { cn } from '@/lib/utils'
import { useOrientation } from '@/hooks/use-orientation'
import { AdaptivePanels } from './adaptive-panels'
import { TabletNavigation } from './tablet-navigation'

interface TabletLayoutProps {
  children: React.ReactNode
  className?: string
  navigation?: React.ReactNode
  sidebar?: React.ReactNode
  secondaryPanel?: React.ReactNode
}

export function TabletLayout({
  children,
  className,
  navigation,
  sidebar,
  secondaryPanel
}: TabletLayoutProps) {
  const { orientation, isLandscape } = useOrientation()

  return (
    <div 
      className={cn(
        "flex h-screen w-full overflow-hidden",
        isLandscape ? "flex-row" : "flex-col",
        className
      )}
    >
      {/* Navigation */}
      <TabletNavigation orientation={orientation}>
        {navigation}
      </TabletNavigation>

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {isLandscape ? (
          <AdaptivePanels
            orientation={orientation}
            primaryPanel={
              <div className="flex h-full">
                {sidebar && (
                  <div className="w-80 border-r border-gray-200 bg-gray-50/50 overflow-auto">
                    {sidebar}
                  </div>
                )}
                <div className="flex-1 overflow-auto">
                  {children}
                </div>
              </div>
            }
            secondaryPanel={secondaryPanel}
            defaultSecondaryWidth={400}
            minSecondaryWidth={300}
            maxSecondaryWidth={600}
          />
        ) : (
          // Portrait mode - stack panels
          <div className="flex flex-col h-full">
            <div className="flex-1 overflow-auto">
              {children}
            </div>
            {(sidebar || secondaryPanel) && (
              <AdaptivePanels
                orientation={orientation}
                primaryPanel={sidebar}
                secondaryPanel={secondaryPanel}
                stacked
                defaultSecondaryHeight={300}
                minSecondaryHeight={200}
                maxSecondaryHeight={500}
              />
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// Grid Layout for Dashboard
interface TabletGridLayoutProps {
  children: React.ReactNode
  className?: string
  columns?: {
    portrait: number
    landscape: number
  }
}

export function TabletGridLayout({
  children,
  className,
  columns = { portrait: 2, landscape: 3 }
}: TabletGridLayoutProps) {
  const { isLandscape } = useOrientation()
  const gridCols = isLandscape ? columns.landscape : columns.portrait

  return (
    <div 
      className={cn(
        "grid gap-4 p-4",
        gridCols === 2 && "grid-cols-2",
        gridCols === 3 && "grid-cols-3",
        gridCols === 4 && "grid-cols-4",
        className
      )}
    >
      {children}
    </div>
  )
}

// Two Column Layout
interface TwoColumnLayoutProps {
  left: React.ReactNode
  right: React.ReactNode
  className?: string
  leftWidth?: string
  collapsible?: boolean
}

export function TwoColumnLayout({
  left,
  right,
  className,
  leftWidth = "w-1/3",
  collapsible = false
}: TwoColumnLayoutProps) {
  const [collapsed, setCollapsed] = React.useState(false)
  const { isLandscape } = useOrientation()

  if (!isLandscape && collapsible) {
    return (
      <div className={cn("flex flex-col h-full", className)}>
        <div className="flex-1 overflow-auto">
          {collapsed ? right : left}
        </div>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="px-4 py-2 bg-gray-100 border-t text-sm font-medium"
        >
          {collapsed ? "Show List" : "Show Details"}
        </button>
      </div>
    )
  }

  return (
    <div className={cn("flex h-full", className)}>
      <div className={cn(leftWidth, "border-r overflow-auto")}>
        {left}
      </div>
      <div className="flex-1 overflow-auto">
        {right}
      </div>
    </div>
  )
}