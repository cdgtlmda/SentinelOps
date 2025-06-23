"use client"

import * as React from "react"
import {
  ColumnDef,
  ColumnFiltersState,
  PaginationState,
  RowSelectionState,
  SortingState,
  VisibilityState,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table"

export interface UseTableOptions<TData> {
  data: TData[]
  columns: ColumnDef<TData>[]
  pageSize?: number
  enableRowSelection?: boolean
  enableMultiSelect?: boolean
  enableSorting?: boolean
  enableFiltering?: boolean
  manualPagination?: boolean
  manualSorting?: boolean
  manualFiltering?: boolean
  pageCount?: number
  onPaginationChange?: (pagination: PaginationState) => void
  onSortingChange?: (sorting: SortingState) => void
  onColumnFiltersChange?: (filters: ColumnFiltersState) => void
  onRowSelectionChange?: (selection: RowSelectionState) => void
  initialState?: {
    sorting?: SortingState
    columnFilters?: ColumnFiltersState
    columnVisibility?: VisibilityState
    rowSelection?: RowSelectionState
    pagination?: PaginationState
  }
}

export function useTable<TData>({
  data,
  columns,
  pageSize = 10,
  enableRowSelection = true,
  enableMultiSelect = true,
  enableSorting = true,
  enableFiltering = true,
  manualPagination = false,
  manualSorting = false,
  manualFiltering = false,
  pageCount,
  onPaginationChange,
  onSortingChange,
  onColumnFiltersChange,
  onRowSelectionChange,
  initialState = {},
}: UseTableOptions<TData>) {
  const [sorting, setSorting] = React.useState<SortingState>(
    initialState.sorting || []
  )
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    initialState.columnFilters || []
  )
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>(
    initialState.columnVisibility || {}
  )
  const [rowSelection, setRowSelection] = React.useState<RowSelectionState>(
    initialState.rowSelection || {}
  )
  const [pagination, setPagination] = React.useState<PaginationState>(
    initialState.pagination || {
      pageIndex: 0,
      pageSize,
    }
  )

  // Handle state changes
  const handleSortingChange = React.useCallback(
    (updater: SortingState | ((old: SortingState) => SortingState)) => {
      const newSorting = typeof updater === "function" ? updater(sorting) : updater
      setSorting(newSorting)
      onSortingChange?.(newSorting)
    },
    [sorting, onSortingChange]
  )

  const handleColumnFiltersChange = React.useCallback(
    (updater: ColumnFiltersState | ((old: ColumnFiltersState) => ColumnFiltersState)) => {
      const newFilters = typeof updater === "function" ? updater(columnFilters) : updater
      setColumnFilters(newFilters)
      onColumnFiltersChange?.(newFilters)
    },
    [columnFilters, onColumnFiltersChange]
  )

  const handleRowSelectionChange = React.useCallback(
    (updater: RowSelectionState | ((old: RowSelectionState) => RowSelectionState)) => {
      const newSelection = typeof updater === "function" ? updater(rowSelection) : updater
      setRowSelection(newSelection)
      onRowSelectionChange?.(newSelection)
    },
    [rowSelection, onRowSelectionChange]
  )

  const handlePaginationChange = React.useCallback(
    (updater: PaginationState | ((old: PaginationState) => PaginationState)) => {
      const newPagination = typeof updater === "function" ? updater(pagination) : updater
      setPagination(newPagination)
      onPaginationChange?.(newPagination)
    },
    [pagination, onPaginationChange]
  )

  const table = useReactTable({
    data,
    columns,
    pageCount,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
      pagination,
    },
    enableRowSelection,
    enableMultiRowSelection: enableMultiSelect,
    enableSorting,
    enableFilters: enableFiltering,
    manualPagination,
    manualSorting,
    manualFiltering,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: manualPagination ? undefined : getPaginationRowModel(),
    getSortedRowModel: manualSorting ? undefined : getSortedRowModel(),
    getFilteredRowModel: manualFiltering ? undefined : getFilteredRowModel(),
    onSortingChange: handleSortingChange,
    onColumnFiltersChange: handleColumnFiltersChange,
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: handleRowSelectionChange,
    onPaginationChange: handlePaginationChange,
  })

  // Helper functions
  const resetFilters = React.useCallback(() => {
    setColumnFilters([])
    onColumnFiltersChange?.([])
  }, [onColumnFiltersChange])

  const resetSorting = React.useCallback(() => {
    setSorting([])
    onSortingChange?.([])
  }, [onSortingChange])

  const resetSelection = React.useCallback(() => {
    setRowSelection({})
    onRowSelectionChange?.({})
  }, [onRowSelectionChange])

  const setGlobalFilter = React.useCallback(
    (value: string) => {
      table.setGlobalFilter(value)
    },
    [table]
  )

  const getSelectedRows = React.useCallback(() => {
    return table.getFilteredSelectedRowModel().rows.map((row) => row.original)
  }, [table])

  const getVisibleColumns = React.useCallback(() => {
    return table.getAllColumns().filter((column) => column.getIsVisible())
  }, [table])

  const toggleAllRowsSelected = React.useCallback(
    (value?: boolean) => {
      table.toggleAllRowsSelected(value)
    },
    [table]
  )

  return {
    table,
    // State
    sorting,
    columnFilters,
    columnVisibility,
    rowSelection,
    pagination,
    // State setters
    setSorting,
    setColumnFilters,
    setColumnVisibility,
    setRowSelection,
    setPagination,
    // Helper functions
    resetFilters,
    resetSorting,
    resetSelection,
    setGlobalFilter,
    getSelectedRows,
    getVisibleColumns,
    toggleAllRowsSelected,
  }
}

// Sorting helpers
export function sortByDate(rowA: any, rowB: any, columnId: string): number {
  const dateA = new Date(rowA.getValue(columnId))
  const dateB = new Date(rowB.getValue(columnId))
  return dateA.getTime() - dateB.getTime()
}

export function sortByNumber(rowA: any, rowB: any, columnId: string): number {
  return rowA.getValue(columnId) - rowB.getValue(columnId)
}

// Filter helpers
export function filterByDateRange(
  row: any,
  columnId: string,
  filterValue: { from?: Date; to?: Date }
): boolean {
  const date = new Date(row.getValue(columnId))
  const { from, to } = filterValue

  if (from && to) {
    return date >= from && date <= to
  } else if (from) {
    return date >= from
  } else if (to) {
    return date <= to
  }

  return true
}

export function filterByMultiSelect(
  row: any,
  columnId: string,
  filterValue: string[]
): boolean {
  const value = row.getValue(columnId)
  return filterValue.includes(value)
}

// Column helpers
export function createColumn<TData>(
  id: string,
  config: Partial<ColumnDef<TData>>
): ColumnDef<TData> {
  return {
    id,
    ...config,
  }
}