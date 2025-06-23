"use client"

import * as React from "react"
import {
  ColumnDef,
  ColumnFiltersState,
  SortingState,
  VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
  RowSelectionState,
  Row,
  Table as TableType,
} from "@tanstack/react-table"
import { useVirtualizer } from "@tanstack/react-virtual"
import { ArrowUpDown, ChevronDown, Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"

export interface DataTableVirtualProps<TData, TValue> {
  columns?: ColumnDef<TData, TValue>[]
  data: TData[]
  table?: TableType<TData>
  onRowSelectionChange?: (selectedRows: TData[]) => void
  enableRowSelection?: boolean
  enableMultiSelect?: boolean
  stickyHeader?: boolean
  isLoading?: boolean
  emptyMessage?: string
  className?: string
  onSortingChange?: (sorting: SortingState) => void
  onColumnFiltersChange?: (filters: ColumnFiltersState) => void
  showColumnVisibilityToggle?: boolean
  getRowId?: (row: TData) => string
  initialSorting?: SortingState
  initialColumnVisibility?: VisibilityState
  onRowClick?: (row: TData) => void
  rowHeight?: number
  overscan?: number
  containerHeight?: string | number
}

function DataTableVirtualComponent<TData, TValue>({
  columns,
  data,
  table: externalTable,
  onRowSelectionChange,
  enableRowSelection = false,
  enableMultiSelect = true,
  stickyHeader = true,
  isLoading = false,
  emptyMessage = "No results found.",
  className,
  onSortingChange,
  onColumnFiltersChange,
  showColumnVisibilityToggle = true,
  getRowId,
  initialSorting = [],
  initialColumnVisibility = {},
  onRowClick,
  rowHeight = 60,
  overscan = 10,
  containerHeight = "600px",
}: DataTableVirtualProps<TData, TValue>) {
  const [sorting, setSorting] = React.useState<SortingState>(initialSorting)
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>(initialColumnVisibility)
  const [rowSelection, setRowSelection] = React.useState<RowSelectionState>({})

  const tableContainerRef = React.useRef<HTMLDivElement>(null)

  const tableColumns = React.useMemo(() => {
    if (!columns || !enableRowSelection) return columns || []

    const selectColumn: ColumnDef<TData, TValue> = {
      id: "select",
      size: 40,
      header: ({ table }) =>
        enableMultiSelect ? (
          <Checkbox
            checked={
              table.getIsAllPageRowsSelected() ||
              (table.getIsSomePageRowsSelected() && "indeterminate")
            }
            onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
            aria-label="Select all"
          />
        ) : null,
      cell: ({ row }) => (
        <Checkbox
          checked={row.getIsSelected()}
          onCheckedChange={(value) => {
            if (!enableMultiSelect) {
              table.toggleAllRowsSelected(false)
            }
            row.toggleSelected(!!value)
          }}
          aria-label="Select row"
          onClick={(e) => e.stopPropagation()}
        />
      ),
      enableSorting: false,
      enableHiding: false,
    }

    return [selectColumn, ...columns]
  }, [columns, enableRowSelection, enableMultiSelect])

  const table = externalTable || useReactTable({
    data,
    columns: tableColumns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: (updater) => {
      setSorting(updater)
      if (onSortingChange) {
        const newSorting = typeof updater === "function" ? updater(sorting) : updater
        onSortingChange(newSorting)
      }
    },
    onColumnFiltersChange: (updater) => {
      setColumnFilters(updater)
      if (onColumnFiltersChange) {
        const newFilters = typeof updater === "function" ? updater(columnFilters) : updater
        onColumnFiltersChange(newFilters)
      }
    },
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
    },
    getRowId,
  })

  const { rows } = table.getRowModel()

  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => tableContainerRef.current,
    estimateSize: () => rowHeight,
    overscan,
  })

  const virtualRows = rowVirtualizer.getVirtualItems()
  const totalSize = rowVirtualizer.getTotalSize()
  const paddingTop = virtualRows.length > 0 ? virtualRows?.[0]?.start || 0 : 0
  const paddingBottom =
    virtualRows.length > 0
      ? totalSize - (virtualRows?.[virtualRows.length - 1]?.end || 0)
      : 0

  // Memoize grid template columns calculation
  const gridTemplateColumns = React.useMemo(() => {
    const visibleColumns = table.getAllColumns().filter((col) => col.getIsVisible())
    return `repeat(${visibleColumns.length}, minmax(0, 1fr))`
  }, [table, columnVisibility])

  // Memoize row click handler
  const handleRowClick = React.useCallback(
    (rowData: TData) => {
      onRowClick?.(rowData)
    },
    [onRowClick]
  )

  React.useEffect(() => {
    if (onRowSelectionChange) {
      const selectedRows = table.getFilteredSelectedRowModel().rows.map((row) => row.original)
      onRowSelectionChange(selectedRows)
    }
  }, [rowSelection, onRowSelectionChange, table])

  return (
    <div className={cn("space-y-4", className)}>
      {showColumnVisibilityToggle && (
        <div className="flex items-center justify-end">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="ml-auto">
                Columns <ChevronDown className="ml-2 h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {table
                .getAllColumns()
                .filter((column) => column.getCanHide())
                .map((column) => {
                  return (
                    <DropdownMenuCheckboxItem
                      key={column.id}
                      className="capitalize"
                      checked={column.getIsVisible()}
                      onCheckedChange={(value) => column.toggleVisibility(!!value)}
                    >
                      {column.id}
                    </DropdownMenuCheckboxItem>
                  )
                })}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      )}

      <div 
        ref={tableContainerRef}
        className="rounded-md border overflow-auto"
        style={{ height: containerHeight }}
      >
        <div className="relative">
          <div 
            className={cn(
              "grid min-w-full",
              stickyHeader && "sticky top-0 z-10 bg-background border-b"
            )}
            style={{
              gridTemplateColumns,
            }}
          >
            {table.getHeaderGroups().map((headerGroup) =>
              headerGroup.headers.map((header) => (
                <div
                  key={header.id}
                  className={cn(
                    "px-3 py-3 text-left align-middle font-medium text-muted-foreground",
                    header.column.getCanSort() && "cursor-pointer select-none"
                  )}
                  style={{
                    width: header.getSize() !== 150 ? header.getSize() : undefined,
                  }}
                  onClick={header.column.getToggleSortingHandler()}
                >
                  <div className="flex items-center">
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                    {header.column.getCanSort() && (
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          {isLoading ? (
            <div className="flex h-24 items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span className="ml-2">Loading...</span>
            </div>
          ) : rows.length === 0 ? (
            <div className="flex h-24 items-center justify-center text-center">
              {emptyMessage}
            </div>
          ) : (
            <div style={{ minHeight: `${totalSize}px` }}>
              {paddingTop > 0 && <div style={{ height: paddingTop }} />}
              {virtualRows.map((virtualRow) => {
                const row = rows[virtualRow.index]
                return (
                  <div
                    key={row.id}
                    data-index={virtualRow.index}
                    ref={rowVirtualizer.measureElement}
                    className={cn(
                      "grid min-w-full border-b transition-colors hover:bg-muted/50",
                      onRowClick && "cursor-pointer",
                      row.getIsSelected() && "bg-muted"
                    )}
                    style={{
                      gridTemplateColumns,
                    }}
                    onClick={() => handleRowClick(row.original)}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <div
                        key={cell.id}
                        className="px-3 py-2 align-middle"
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </div>
                    ))}
                  </div>
                )
              })}
              {paddingBottom > 0 && <div style={{ height: paddingBottom }} />}
            </div>
          )}
        </div>
      </div>

      {rows.length > 0 && (
        <div className="flex items-center justify-between px-2 text-sm text-muted-foreground">
          <div className="flex-1">
            {enableRowSelection && (
              <>
                {table.getFilteredSelectedRowModel().rows.length} of{" "}
                {table.getFilteredRowModel().rows.length} row(s) selected.
              </>
            )}
          </div>
          <div>
            Showing {virtualRows.length} of {rows.length} rows
          </div>
        </div>
      )}
    </div>
  )
}

// Export memoized component
export const DataTableVirtual = React.memo(DataTableVirtualComponent) as typeof DataTableVirtualComponent

export function createSortableHeader<TData>(
  title: string,
  accessorKey: keyof TData
): Partial<ColumnDef<TData>> {
  return {
    accessorKey: accessorKey as string,
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="-ml-2"
        >
          {title}
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
  }
}