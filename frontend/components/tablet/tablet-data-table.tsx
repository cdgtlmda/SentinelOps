"use client"

import React, { useState, useMemo } from 'react'
import { cn } from '@/lib/utils'
import { useOptimalLayout } from '@/hooks/use-orientation'
import { 
  ChevronUp, 
  ChevronDown, 
  ChevronsUpDown,
  Filter,
  Download,
  Eye,
  EyeOff,
  Settings,
  Check
} from 'lucide-react'
import { Card } from '@/components/ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuCheckboxItem,
} from '@/components/ui/dropdown-menu'

interface Column<T> {
  key: string
  label: string
  width?: string
  minWidth?: string
  sortable?: boolean
  filterable?: boolean
  render?: (item: T) => React.ReactNode
  priority?: 'high' | 'medium' | 'low' // For responsive column hiding
  align?: 'left' | 'center' | 'right'
}

interface TabletDataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  className?: string
  onRowClick?: (item: T) => void
  selectable?: boolean
  stickyHeader?: boolean
  pagination?: {
    page: number
    pageSize: number
    total: number
    onPageChange: (page: number) => void
    onPageSizeChange: (size: number) => void
  }
  actions?: React.ReactNode
}

export function TabletDataTable<T extends { id: string | number }>({
  data,
  columns,
  className,
  onRowClick,
  selectable = false,
  stickyHeader = true,
  pagination,
  actions
}: TabletDataTableProps<T>) {
  const layout = useOptimalLayout()
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null)
  const [selectedRows, setSelectedRows] = useState<Set<string | number>>(new Set())
  const [visibleColumns, setVisibleColumns] = useState<Set<string>>(
    new Set(columns.map(col => col.key))
  )
  
  // Filter columns based on screen size and priority
  const displayColumns = useMemo(() => {
    if (layout.isLandscape) {
      return columns.filter(col => visibleColumns.has(col.key))
    }
    
    // In portrait, hide low priority columns
    return columns.filter(col => 
      visibleColumns.has(col.key) && 
      (col.priority !== 'low' || layout.width >= 900)
    )
  }, [columns, visibleColumns, layout.isLandscape, layout.width])
  
  // Sort data
  const sortedData = useMemo(() => {
    if (!sortConfig) return data
    
    return [...data].sort((a, b) => {
      const aValue = (a as any)[sortConfig.key]
      const bValue = (b as any)[sortConfig.key]
      
      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1
      return 0
    })
  }, [data, sortConfig])
  
  const handleSort = (key: string) => {
    setSortConfig(prev => {
      if (!prev || prev.key !== key) {
        return { key, direction: 'asc' }
      }
      if (prev.direction === 'asc') {
        return { key, direction: 'desc' }
      }
      return null
    })
  }
  
  const toggleRowSelection = (id: string | number) => {
    setSelectedRows(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }
  
  const toggleAllSelection = () => {
    if (selectedRows.size === data.length) {
      setSelectedRows(new Set())
    } else {
      setSelectedRows(new Set(data.map(item => item.id)))
    }
  }
  
  const toggleColumnVisibility = (key: string) => {
    setVisibleColumns(prev => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }
  
  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Table Actions Bar */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50/50">
        <div className="flex items-center gap-2">
          {selectable && selectedRows.size > 0 && (
            <Badge variant="secondary" className="gap-1">
              {selectedRows.size} selected
            </Badge>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {actions}
          
          {/* Column visibility toggle */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <Eye className="w-4 h-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>Toggle Columns</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {columns.map(col => (
                <DropdownMenuCheckboxItem
                  key={col.key}
                  checked={visibleColumns.has(col.key)}
                  onCheckedChange={() => toggleColumnVisibility(col.key)}
                >
                  {col.label}
                  {col.priority && (
                    <span className="ml-auto text-xs text-gray-500">
                      {col.priority}
                    </span>
                  )}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
          
          <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <Filter className="w-4 h-4" />
          </button>
          
          <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Table Container */}
      <div className="flex-1 overflow-auto">
        <table className="w-full">
          <thead className={cn(
            "bg-gray-50 border-b",
            stickyHeader && "sticky top-0 z-10"
          )}>
            <tr>
              {selectable && (
                <th className="w-12 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selectedRows.size === data.length && data.length > 0}
                    onChange={toggleAllSelection}
                    className="rounded"
                  />
                </th>
              )}
              {displayColumns.map(col => (
                <th
                  key={col.key}
                  className={cn(
                    "px-4 py-3 text-left text-sm font-medium text-gray-700",
                    col.align === 'center' && "text-center",
                    col.align === 'right' && "text-right",
                    col.sortable && "cursor-pointer hover:bg-gray-100 select-none"
                  )}
                  style={{
                    width: col.width,
                    minWidth: col.minWidth
                  }}
                  onClick={() => col.sortable && handleSort(col.key)}
                >
                  <div className="flex items-center gap-1">
                    <span>{col.label}</span>
                    {col.sortable && (
                      <span className="ml-1">
                        {sortConfig?.key === col.key ? (
                          sortConfig.direction === 'asc' ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          )
                        ) : (
                          <ChevronsUpDown className="w-4 h-4 text-gray-400" />
                        )}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          
          <tbody className="divide-y divide-gray-200">
            {sortedData.length === 0 ? (
              <tr>
                <td 
                  colSpan={displayColumns.length + (selectable ? 1 : 0)} 
                  className="px-4 py-12 text-center text-gray-500"
                >
                  No data available
                </td>
              </tr>
            ) : (
              sortedData.map((item) => (
                <tr
                  key={item.id}
                  className={cn(
                    "hover:bg-gray-50 transition-colors",
                    selectedRows.has(item.id) && "bg-blue-50",
                    onRowClick && "cursor-pointer"
                  )}
                  onClick={() => onRowClick?.(item)}
                >
                  {selectable && (
                    <td className="w-12 px-4 py-3" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={selectedRows.has(item.id)}
                        onChange={() => toggleRowSelection(item.id)}
                        className="rounded"
                      />
                    </td>
                  )}
                  {displayColumns.map(col => (
                    <td
                      key={col.key}
                      className={cn(
                        "px-4 py-3 text-sm",
                        col.align === 'center' && "text-center",
                        col.align === 'right' && "text-right"
                      )}
                    >
                      {col.render ? col.render(item) : (item as any)[col.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      
      {/* Pagination */}
      {pagination && (
        <div className="flex items-center justify-between px-4 py-3 border-t bg-gray-50/50">
          <div className="flex items-center gap-2 text-sm text-gray-700">
            <span>Rows per page:</span>
            <select
              value={pagination.pageSize}
              onChange={(e) => pagination.onPageSizeChange(Number(e.target.value))}
              className="px-2 py-1 border rounded"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
          
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-700">
              {(pagination.page - 1) * pagination.pageSize + 1}-
              {Math.min(pagination.page * pagination.pageSize, pagination.total)} of {pagination.total}
            </span>
            
            <div className="flex gap-1">
              <button
                onClick={() => pagination.onPageChange(pagination.page - 1)}
                disabled={pagination.page === 1}
                className="p-2 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => pagination.onPageChange(pagination.page + 1)}
                disabled={pagination.page * pagination.pageSize >= pagination.total}
                className="p-2 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Responsive table wrapper for automatic column management
interface ResponsiveTableProps<T> extends TabletDataTableProps<T> {
  mobileColumns?: string[] // Columns to show on mobile
  tabletColumns?: string[] // Columns to show on tablet
}

export function ResponsiveTable<T extends { id: string | number }>({
  mobileColumns,
  tabletColumns,
  columns,
  ...props
}: ResponsiveTableProps<T>) {
  const layout = useOptimalLayout()
  
  const filteredColumns = useMemo(() => {
    if (layout.isMobile && mobileColumns) {
      return columns.filter(col => mobileColumns.includes(col.key))
    }
    if (layout.isTablet && tabletColumns) {
      return columns.filter(col => tabletColumns.includes(col.key))
    }
    return columns
  }, [columns, layout.isMobile, layout.isTablet, mobileColumns, tabletColumns])
  
  return <TabletDataTable {...props} columns={filteredColumns} />
}

// Helper components
function Badge({ children, variant = 'default', className }: { 
  children: React.ReactNode
  variant?: 'default' | 'secondary'
  className?: string 
}) {
  return (
    <span className={cn(
      "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
      variant === 'secondary' && "bg-gray-100 text-gray-800",
      variant === 'default' && "bg-blue-100 text-blue-800",
      className
    )}>
      {children}
    </span>
  )
}

function ChevronLeft({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
    </svg>
  )
}

function ChevronRight({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  )
}