'use client'

import React from 'react'
import { cn } from '@/lib/utils'
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ScreenReaderOnly, StatusAnnouncer } from './screen-reader-text'

interface TableCaptionProps {
  children: React.ReactNode
  /**
   * Additional summary information for complex tables
   */
  summary?: string
  className?: string
}

/**
 * Accessible table caption that provides context for table content
 */
export const TableCaption: React.FC<TableCaptionProps> = ({
  children,
  summary,
  className
}) => {
  return (
    <caption className={cn('text-sm text-muted-foreground mb-2', className)}>
      {children}
      {summary && (
        <ScreenReaderOnly>
          <span>. {summary}</span>
        </ScreenReaderOnly>
      )}
    </caption>
  )
}

interface SortableColumnHeaderProps {
  children: React.ReactNode
  /**
   * Current sort direction
   */
  sortDirection?: 'asc' | 'desc' | null
  /**
   * Callback when sort is triggered
   */
  onSort?: () => void
  /**
   * Column identifier for screen reader announcements
   */
  columnName: string
  className?: string
}

/**
 * Accessible sortable column header with proper announcements
 */
export const SortableColumnHeader: React.FC<SortableColumnHeaderProps> = ({
  children,
  sortDirection,
  onSort,
  columnName,
  className
}) => {
  const getSortIcon = () => {
    if (sortDirection === 'asc') return <ArrowUp className="h-4 w-4" />
    if (sortDirection === 'desc') return <ArrowDown className="h-4 w-4" />
    return <ArrowUpDown className="h-4 w-4" />
  }

  const getSortLabel = () => {
    if (sortDirection === 'asc') return `${columnName}, sorted ascending`
    if (sortDirection === 'desc') return `${columnName}, sorted descending`
    return `${columnName}, sortable`
  }

  return (
    <th scope="col" className={className}>
      {onSort ? (
        <Button
          variant="ghost"
          onClick={onSort}
          className="h-auto p-0 font-medium hover:bg-transparent"
          aria-label={getSortLabel()}
        >
          <span className="flex items-center gap-1">
            {children}
            {getSortIcon()}
          </span>
        </Button>
      ) : (
        children
      )}
    </th>
  )
}

interface RowHeaderProps {
  children: React.ReactNode
  /**
   * ID to reference this header from data cells
   */
  id?: string
  className?: string
}

/**
 * Accessible row header for tables with row headers
 */
export const RowHeader: React.FC<RowHeaderProps> = ({
  children,
  id,
  className
}) => {
  return (
    <th scope="row" id={id} className={className}>
      {children}
    </th>
  )
}

interface DataCellProps {
  children: React.ReactNode
  /**
   * IDs of headers that describe this cell (for complex tables)
   */
  headers?: string[]
  className?: string
}

/**
 * Accessible data cell with header associations
 */
export const DataCell: React.FC<DataCellProps> = ({
  children,
  headers,
  className
}) => {
  return (
    <td headers={headers?.join(' ')} className={className}>
      {children}
    </td>
  )
}

interface AccessibleTableProps {
  /**
   * Table caption
   */
  caption: string
  /**
   * Additional summary for complex tables
   */
  summary?: string
  /**
   * Column definitions
   */
  columns: Array<{
    key: string
    header: string
    sortable?: boolean
    align?: 'left' | 'center' | 'right'
  }>
  /**
   * Table data
   */
  data: Array<Record<string, any>>
  /**
   * Current sort configuration
   */
  sort?: {
    column: string
    direction: 'asc' | 'desc'
  }
  /**
   * Callback when sort changes
   */
  onSort?: (column: string) => void
  /**
   * Whether to show row numbers
   */
  showRowNumbers?: boolean
  /**
   * Custom row header field (makes first column a row header)
   */
  rowHeaderField?: string
  /**
   * Loading state
   */
  isLoading?: boolean
  /**
   * Empty state message
   */
  emptyMessage?: string
  className?: string
}

/**
 * Fully accessible table component with proper structure and announcements
 */
export const AccessibleTable: React.FC<AccessibleTableProps> = ({
  caption,
  summary,
  columns,
  data,
  sort,
  onSort,
  showRowNumbers = false,
  rowHeaderField,
  isLoading = false,
  emptyMessage = 'No data available',
  className
}) => {
  const [sortAnnouncement, setSortAnnouncement] = React.useState('')

  const handleSort = (columnKey: string) => {
    if (!onSort) return

    const column = columns.find(c => c.key === columnKey)
    if (!column) return

    onSort(columnKey)

    // Announce sort change
    const newDirection = sort?.column === columnKey && sort.direction === 'asc' ? 'desc' : 'asc'
    setSortAnnouncement(`Table sorted by ${column.header} in ${newDirection === 'asc' ? 'ascending' : 'descending'} order`)
  }

  const getAlignment = (align?: 'left' | 'center' | 'right') => {
    switch (align) {
      case 'center': return 'text-center'
      case 'right': return 'text-right'
      default: return 'text-left'
    }
  }

  return (
    <>
      <StatusAnnouncer message={sortAnnouncement} />
      
      <div className={cn('relative overflow-x-auto', className)}>
        <table className="w-full">
          <TableCaption summary={summary}>
            {caption}
            {isLoading && <span className="ml-2">(Loading...)</span>}
          </TableCaption>

          <thead>
            <tr>
              {showRowNumbers && (
                <th scope="col" className="text-left">
                  <ScreenReaderOnly>Row number</ScreenReaderOnly>
                  #
                </th>
              )}
              {columns.map((column) => (
                <SortableColumnHeader
                  key={column.key}
                  columnName={column.header}
                  sortDirection={sort?.column === column.key ? sort.direction : null}
                  onSort={column.sortable ? () => handleSort(column.key) : undefined}
                  className={getAlignment(column.align)}
                >
                  {column.header}
                </SortableColumnHeader>
              ))}
            </tr>
          </thead>

          <tbody>
            {isLoading ? (
              <tr>
                <td 
                  colSpan={columns.length + (showRowNumbers ? 1 : 0)} 
                  className="text-center py-8"
                  role="status"
                  aria-live="polite"
                >
                  <span className="text-muted-foreground">Loading table data...</span>
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td 
                  colSpan={columns.length + (showRowNumbers ? 1 : 0)} 
                  className="text-center py-8"
                >
                  <span className="text-muted-foreground">{emptyMessage}</span>
                </td>
              </tr>
            ) : (
              data.map((row, rowIndex) => {
                const rowId = `row-${rowIndex}`
                const isFirstColumnRowHeader = rowHeaderField && columns[0]?.key === rowHeaderField

                return (
                  <tr key={rowIndex}>
                    {showRowNumbers && (
                      <th scope="row" className="text-left">
                        {rowIndex + 1}
                      </th>
                    )}
                    {columns.map((column, colIndex) => {
                      const cellContent = row[column.key]
                      
                      if (isFirstColumnRowHeader && colIndex === 0) {
                        return (
                          <RowHeader 
                            key={column.key} 
                            id={`${rowId}-header`}
                            className={getAlignment(column.align)}
                          >
                            {cellContent}
                          </RowHeader>
                        )
                      }

                      return (
                        <DataCell
                          key={column.key}
                          headers={isFirstColumnRowHeader ? [`${rowId}-header`] : undefined}
                          className={getAlignment(column.align)}
                        >
                          {cellContent}
                        </DataCell>
                      )
                    })}
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </>
  )
}

interface TableNavigationAnnouncerProps {
  currentPage: number
  totalPages: number
  pageSize: number
  totalItems: number
  /**
   * Item name for announcements (e.g., "incidents", "agents")
   */
  itemName: string
}

/**
 * Component that announces table navigation changes to screen readers
 */
export const TableNavigationAnnouncer: React.FC<TableNavigationAnnouncerProps> = ({
  currentPage,
  totalPages,
  pageSize,
  totalItems,
  itemName
}) => {
  const startItem = (currentPage - 1) * pageSize + 1
  const endItem = Math.min(currentPage * pageSize, totalItems)

  const message = `Showing ${startItem} to ${endItem} of ${totalItems} ${itemName}. Page ${currentPage} of ${totalPages}.`

  return <StatusAnnouncer message={message} politeness="polite" />
}

interface TableSummaryProps {
  /**
   * Number of rows in the table
   */
  rowCount: number
  /**
   * Number of columns in the table
   */
  columnCount: number
  /**
   * Additional summary information
   */
  additionalInfo?: string
  className?: string
}

/**
 * Component that provides a summary of table contents for screen readers
 */
export const TableSummary: React.FC<TableSummaryProps> = ({
  rowCount,
  columnCount,
  additionalInfo,
  className
}) => {
  return (
    <ScreenReaderOnly>
      <p className={className}>
        Table with {rowCount} rows and {columnCount} columns.
        {additionalInfo && ` ${additionalInfo}`}
      </p>
    </ScreenReaderOnly>
  )
}