"use client"

import * as React from "react"
import { Table } from "@tanstack/react-table"
import { 
  Trash2, 
  Archive, 
  UserPlus, 
  MoreHorizontal,
  CheckSquare,
  Square,
  MinusSquare
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"

export interface BulkAction<TData> {
  label: string
  icon?: React.ReactNode
  onClick: (rows: TData[]) => void
  variant?: "default" | "destructive"
  confirmMessage?: string
}

interface DataTableBulkActionsProps<TData> {
  table: Table<TData>
  actions?: BulkAction<TData>[]
  customActions?: React.ReactNode
  className?: string
  position?: "top" | "bottom" | "sticky"
}

export function DataTableBulkActions<TData>({
  table,
  actions = defaultActions,
  customActions,
  className,
  position = "top",
}: DataTableBulkActionsProps<TData>) {
  const selectedRows = table.getFilteredSelectedRowModel().rows
  const totalRows = table.getFilteredRowModel().rows
  const isAllSelected = selectedRows.length === totalRows.length && totalRows.length > 0
  const isSomeSelected = selectedRows.length > 0 && selectedRows.length < totalRows.length

  if (selectedRows.length === 0) {
    return null
  }

  const handleAction = (action: BulkAction<TData>) => {
    const selectedData = selectedRows.map((row) => row.original)
    
    if (action.confirmMessage) {
      if (confirm(action.confirmMessage)) {
        action.onClick(selectedData)
        table.toggleAllRowsSelected(false)
      }
    } else {
      action.onClick(selectedData)
      table.toggleAllRowsSelected(false)
    }
  }

  const handleSelectAll = () => {
    table.toggleAllPageRowsSelected(!isAllSelected)
  }

  const handleSelectFiltered = () => {
    table.toggleAllRowsSelected(!isAllSelected)
  }

  return (
    <div
      className={cn(
        "flex items-center justify-between px-4 py-3 bg-muted/50 border rounded-lg",
        position === "sticky" && "sticky top-0 z-20",
        className
      )}
    >
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2"
            onClick={handleSelectAll}
          >
            {isAllSelected ? (
              <CheckSquare className="h-4 w-4" />
            ) : isSomeSelected ? (
              <MinusSquare className="h-4 w-4" />
            ) : (
              <Square className="h-4 w-4" />
            )}
          </Button>
          <span className="text-sm font-medium">
            {selectedRows.length} of {totalRows.length} row(s) selected
          </span>
        </div>

        <div className="h-4 w-px bg-border" />

        <div className="flex items-center gap-2">
          {actions.slice(0, 3).map((action, index) => (
            <Button
              key={index}
              variant={action.variant || "outline"}
              size="sm"
              onClick={() => handleAction(action)}
              className="h-8"
            >
              {action.icon}
              <span className="ml-2">{action.label}</span>
            </Button>
          ))}

          {actions.length > 3 && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="h-8">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>More Actions</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {actions.slice(3).map((action, index) => (
                  <DropdownMenuItem
                    key={index}
                    onClick={() => handleAction(action)}
                    className={action.variant === "destructive" ? "text-destructive" : ""}
                  >
                    {action.icon}
                    <span className="ml-2">{action.label}</span>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}

          {customActions}
        </div>
      </div>

      <div className="flex items-center gap-2">
        {totalRows.length !== table.getCoreRowModel().rows.length && (
          <Button
            variant="link"
            size="sm"
            onClick={handleSelectFiltered}
            className="h-auto p-0 text-xs"
          >
            Select all {totalRows.length} filtered rows
          </Button>
        )}
        
        <Button
          variant="ghost"
          size="sm"
          onClick={() => table.toggleAllRowsSelected(false)}
          className="h-8"
        >
          Clear selection
        </Button>
      </div>
    </div>
  )
}

// Default actions that can be overridden
const defaultActions: BulkAction<any>[] = [
  {
    label: "Delete",
    icon: <Trash2 className="h-4 w-4" />,
    variant: "destructive",
    confirmMessage: "Are you sure you want to delete the selected items?",
    onClick: (rows) => {
      console.log("Delete", rows)
    },
  },
  {
    label: "Archive",
    icon: <Archive className="h-4 w-4" />,
    onClick: (rows) => {
      console.log("Archive", rows)
    },
  },
  {
    label: "Assign",
    icon: <UserPlus className="h-4 w-4" />,
    onClick: (rows) => {
      console.log("Assign", rows)
    },
  },
]