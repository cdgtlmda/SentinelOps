"use client"

import React, { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { useOrientation } from '@/hooks/use-orientation'
import { ChevronLeft, ChevronRight, Inbox } from 'lucide-react'

interface MasterDetailViewProps<T> {
  items: T[]
  selectedId?: string | number
  onSelectItem: (item: T) => void
  renderListItem: (item: T, isSelected: boolean) => React.ReactNode
  renderDetail: (item: T) => React.ReactNode
  getItemId: (item: T) => string | number
  className?: string
  emptyState?: React.ReactNode
  listClassName?: string
  detailClassName?: string
  showBackButton?: boolean
  listTitle?: string
  detailTitle?: string | ((item: T) => string)
}

export function MasterDetailView<T>({
  items,
  selectedId,
  onSelectItem,
  renderListItem,
  renderDetail,
  getItemId,
  className,
  emptyState,
  listClassName,
  detailClassName,
  showBackButton = true,
  listTitle,
  detailTitle
}: MasterDetailViewProps<T>) {
  const { isLandscape } = useOrientation()
  const [showDetail, setShowDetail] = useState(false)
  const [animating, setAnimating] = useState(false)
  
  const selectedItem = items.find(item => getItemId(item) === selectedId)

  useEffect(() => {
    if (selectedId && !isLandscape) {
      setAnimating(true)
      setShowDetail(true)
      setTimeout(() => setAnimating(false), 300)
    }
  }, [selectedId, isLandscape])

  const handleSelectItem = (item: T) => {
    onSelectItem(item)
    if (!isLandscape) {
      setAnimating(true)
      setShowDetail(true)
      setTimeout(() => setAnimating(false), 300)
    }
  }

  const handleBack = () => {
    setAnimating(true)
    setTimeout(() => {
      setShowDetail(false)
      setAnimating(false)
    }, 300)
  }

  // Landscape layout - side by side
  if (isLandscape) {
    return (
      <div className={cn("flex h-full", className)}>
        {/* Master List */}
        <div className={cn(
          "w-96 border-r bg-gray-50/50 flex flex-col overflow-hidden",
          listClassName
        )}>
          {listTitle && (
            <div className="px-4 py-3 border-b bg-white">
              <h2 className="text-lg font-semibold text-gray-900">{listTitle}</h2>
            </div>
          )}
          <div className="flex-1 overflow-y-auto">
            {items.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full p-8 text-gray-500">
                {emptyState || (
                  <>
                    <Inbox className="w-12 h-12 mb-3" />
                    <p className="text-center">No items to display</p>
                  </>
                )}
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {items.map((item) => {
                  const isSelected = getItemId(item) === selectedId
                  return (
                    <div
                      key={getItemId(item)}
                      onClick={() => handleSelectItem(item)}
                      className={cn(
                        "cursor-pointer transition-colors relative",
                        isSelected 
                          ? "bg-blue-50 border-l-4 border-l-blue-600" 
                          : "hover:bg-gray-100 border-l-4 border-l-transparent"
                      )}
                    >
                      {renderListItem(item, isSelected)}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* Detail View */}
        <div className={cn(
          "flex-1 bg-white flex flex-col overflow-hidden",
          detailClassName
        )}>
          {selectedItem ? (
            <>
              {detailTitle && (
                <div className="px-6 py-4 border-b">
                  <h2 className="text-xl font-semibold text-gray-900">
                    {typeof detailTitle === 'function' ? detailTitle(selectedItem) : detailTitle}
                  </h2>
                </div>
              )}
              <div className="flex-1 overflow-y-auto">
                {renderDetail(selectedItem)}
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-full p-8 text-gray-400">
              <ChevronLeft className="w-16 h-16 mb-4" />
              <p className="text-lg">Select an item to view details</p>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Portrait layout - animated transitions
  return (
    <div className={cn("relative h-full overflow-hidden", className)}>
      {/* Master List */}
      <div 
        className={cn(
          "absolute inset-0 bg-gray-50/50 transition-transform duration-300 ease-in-out",
          showDetail && "-translate-x-full",
          listClassName
        )}
      >
        {listTitle && (
          <div className="px-4 py-3 border-b bg-white">
            <h2 className="text-lg font-semibold text-gray-900">{listTitle}</h2>
          </div>
        )}
        <div className="h-full overflow-y-auto">
          {items.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full p-8 text-gray-500">
              {emptyState || (
                <>
                  <Inbox className="w-12 h-12 mb-3" />
                  <p className="text-center">No items to display</p>
                </>
              )}
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {items.map((item) => {
                const isSelected = getItemId(item) === selectedId
                return (
                  <div
                    key={getItemId(item)}
                    onClick={() => handleSelectItem(item)}
                    className={cn(
                      "cursor-pointer transition-colors relative",
                      isSelected 
                        ? "bg-blue-50" 
                        : "hover:bg-gray-100"
                    )}
                  >
                    <div className="pr-4">
                      {renderListItem(item, isSelected)}
                    </div>
                    <ChevronRight className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Detail View */}
      <div 
        className={cn(
          "absolute inset-0 bg-white transition-transform duration-300 ease-in-out",
          !showDetail && "translate-x-full",
          detailClassName
        )}
      >
        {selectedItem && (
          <>
            <div className="sticky top-0 z-10 bg-white border-b">
              <div className="flex items-center px-4 py-3">
                {showBackButton && (
                  <button
                    onClick={handleBack}
                    className="mr-3 p-2 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                )}
                {detailTitle && (
                  <h2 className="text-lg font-semibold text-gray-900 flex-1">
                    {typeof detailTitle === 'function' ? detailTitle(selectedItem) : detailTitle}
                  </h2>
                )}
              </div>
            </div>
            <div className="overflow-y-auto">
              {renderDetail(selectedItem)}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// Responsive Breakpoint Wrapper
interface ResponsiveMasterDetailProps<T> extends MasterDetailViewProps<T> {
  breakpoint?: number
  forceLayout?: 'stacked' | 'side-by-side'
}

export function ResponsiveMasterDetail<T>({
  breakpoint = 768,
  forceLayout,
  ...props
}: ResponsiveMasterDetailProps<T>) {
  const [width, setWidth] = useState(
    typeof window !== 'undefined' ? window.innerWidth : breakpoint + 1
  )

  useEffect(() => {
    const handleResize = () => setWidth(window.innerWidth)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const useSideBySide = forceLayout 
    ? forceLayout === 'side-by-side'
    : width >= breakpoint

  // Override orientation for layout
  const orientation = useSideBySide ? 'landscape' : 'portrait'

  return (
    <div className="h-full" data-orientation={orientation}>
      <MasterDetailView {...props} />
    </div>
  )
}