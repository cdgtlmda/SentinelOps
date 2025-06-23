"use client"

import * as React from "react"
import { Table } from "@tanstack/react-table"
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"

interface DataTablePaginationProps<TData> {
  table: Table<TData>
  pageSizeOptions?: number[]
  showPageSizeSelector?: boolean
  showPageInfo?: boolean
  showRowCount?: boolean
  showPageJumper?: boolean
  className?: string
}

export function DataTablePagination<TData>({
  table,
  pageSizeOptions = [10, 20, 30, 40, 50, 100],
  showPageSizeSelector = true,
  showPageInfo = true,
  showRowCount = true,
  showPageJumper = true,
  className,
}: DataTablePaginationProps<TData>) {
  const [pageInput, setPageInput] = React.useState("")

  const handlePageJump = (e: React.FormEvent) => {
    e.preventDefault()
    const page = Number(pageInput)
    if (page > 0 && page <= table.getPageCount()) {
      table.setPageIndex(page - 1)
      setPageInput("")
    }
  }

  return (
    <div className={cn("flex items-center justify-between px-2", className)}>
      <div className="flex-1 text-sm text-muted-foreground">
        {showRowCount && (
          <>
            {table.getFilteredSelectedRowModel().rows.length > 0 && (
              <>
                {table.getFilteredSelectedRowModel().rows.length} of{" "}
              </>
            )}
            {table.getFilteredRowModel().rows.length} row(s)
            {table.getRowModel().rows.length !== table.getCoreRowModel().rows.length && (
              <> (filtered from {table.getCoreRowModel().rows.length} total)</>
            )}
          </>
        )}
      </div>

      <div className="flex items-center space-x-6 lg:space-x-8">
        {showPageSizeSelector && (
          <div className="flex items-center space-x-2">
            <p className="text-sm font-medium">Rows per page</p>
            <Select
              value={`${table.getState().pagination.pageSize}`}
              onValueChange={(value) => {
                table.setPageSize(Number(value))
              }}
            >
              <SelectTrigger className="h-8 w-[70px]">
                <SelectValue placeholder={table.getState().pagination.pageSize} />
              </SelectTrigger>
              <SelectContent side="top">
                {pageSizeOptions.map((pageSize) => (
                  <SelectItem key={pageSize} value={`${pageSize}`}>
                    {pageSize}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {showPageInfo && (
          <div className="flex w-[100px] items-center justify-center text-sm font-medium">
            Page {table.getState().pagination.pageIndex + 1} of{" "}
            {table.getPageCount()}
          </div>
        )}

        {showPageJumper && table.getPageCount() > 5 && (
          <form onSubmit={handlePageJump} className="flex items-center space-x-2">
            <p className="text-sm font-medium">Go to</p>
            <Input
              type="number"
              value={pageInput}
              onChange={(e) => setPageInput(e.target.value)}
              className="h-8 w-[60px]"
              min={1}
              max={table.getPageCount()}
              placeholder={`${table.getState().pagination.pageIndex + 1}`}
            />
          </form>
        )}

        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            className="hidden h-8 w-8 p-0 lg:flex"
            onClick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}
          >
            <span className="sr-only">Go to first page</span>
            <ChevronsLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            className="h-8 w-8 p-0"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            <span className="sr-only">Go to previous page</span>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          
          {/* Page numbers for desktop */}
          <div className="hidden items-center gap-1 md:flex">
            {(() => {
              const currentPage = table.getState().pagination.pageIndex
              const pageCount = table.getPageCount()
              const pages: (number | string)[] = []
              
              // Always show first page
              pages.push(0)
              
              if (currentPage > 2) {
                pages.push("...")
              }
              
              // Show pages around current page
              for (let i = Math.max(1, currentPage - 1); i <= Math.min(pageCount - 2, currentPage + 1); i++) {
                if (!pages.includes(i)) {
                  pages.push(i)
                }
              }
              
              if (currentPage < pageCount - 3) {
                pages.push("...")
              }
              
              // Always show last page
              if (pageCount > 1) {
                pages.push(pageCount - 1)
              }
              
              return pages.map((page, index) => {
                if (page === "...") {
                  return (
                    <span key={`ellipsis-${index}`} className="px-2 text-muted-foreground">
                      ...
                    </span>
                  )
                }
                
                const pageNumber = page as number
                return (
                  <Button
                    key={pageNumber}
                    variant={currentPage === pageNumber ? "default" : "outline"}
                    className="h-8 w-8 p-0"
                    onClick={() => table.setPageIndex(pageNumber)}
                  >
                    {pageNumber + 1}
                  </Button>
                )
              })
            })()}
          </div>
          
          <Button
            variant="outline"
            className="h-8 w-8 p-0"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            <span className="sr-only">Go to next page</span>
            <ChevronRight className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            className="hidden h-8 w-8 p-0 lg:flex"
            onClick={() => table.setPageIndex(table.getPageCount() - 1)}
            disabled={!table.getCanNextPage()}
          >
            <span className="sr-only">Go to last page</span>
            <ChevronsRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}