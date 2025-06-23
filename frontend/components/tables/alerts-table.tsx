"use client"

import * as React from "react"
import { ColumnDef } from "@tanstack/react-table"
import { format } from "date-fns"
import { 
  MoreHorizontal, 
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  Bell,
  BellOff,
  Eye
} from "lucide-react"

import { Alert, AlertType } from "@/types/alerts"
import { DataTable, createSortableHeader } from "./data-table"
import { DataTableFilters, FilterConfig } from "./data-table-filters"
import { DataTablePagination } from "./data-table-pagination"
import { DataTableExport } from "./data-table-export"
import { DataTableBulkActions, BulkAction } from "./data-table-bulk-actions"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useTable } from "@/hooks/use-table"
import { cn } from "@/lib/utils"

interface AlertsTableProps {
  alerts: Alert[]
  onAlertClick?: (alert: Alert) => void
  onAlertAction?: (alertId: string, action: string) => void
  className?: string
}

const typeIcons: Record<AlertType, React.ReactNode> = {
  success: <CheckCircle className="h-4 w-4" />,
  error: <XCircle className="h-4 w-4" />,
  warning: <AlertTriangle className="h-4 w-4" />,
  info: <Info className="h-4 w-4" />,
}

const typeColors: Record<AlertType, string> = {
  success: "bg-green-500/10 text-green-700 border-green-500/20",
  error: "bg-red-500/10 text-red-700 border-red-500/20",
  warning: "bg-yellow-500/10 text-yellow-700 border-yellow-500/20",
  info: "bg-blue-500/10 text-blue-700 border-blue-500/20",
}

const priorityColors = {
  low: "bg-gray-500/10 text-gray-700 border-gray-500/20",
  normal: "bg-blue-500/10 text-blue-700 border-blue-500/20",
  high: "bg-orange-500/10 text-orange-700 border-orange-500/20",
  critical: "bg-red-500/10 text-red-700 border-red-500/20",
}

export function AlertsTable({
  alerts,
  onAlertClick,
  onAlertAction,
  className,
}: AlertsTableProps) {
  const columns: ColumnDef<Alert>[] = React.useMemo(
    () => [
      {
        ...createSortableHeader("Title", "title"),
        accessorKey: "title",
        cell: ({ row }) => (
          <div className="flex items-center gap-2">
            {typeIcons[row.original.type]}
            <div className="flex flex-col">
              <span className="font-medium">{row.getValue("title")}</span>
              {row.original.message && (
                <span className="text-xs text-muted-foreground line-clamp-1">
                  {row.original.message}
                </span>
              )}
            </div>
          </div>
        ),
      },
      {
        accessorKey: "type",
        header: "Type",
        cell: ({ row }) => {
          const type = row.getValue("type") as AlertType
          return (
            <Badge
              variant="outline"
              className={cn("capitalize", typeColors[type])}
            >
              {type}
            </Badge>
          )
        },
      },
      {
        accessorKey: "priority",
        header: "Priority",
        cell: ({ row }) => {
          const priority = row.original.priority || "normal"
          return (
            <Badge
              variant="outline"
              className={cn("capitalize", priorityColors[priority])}
            >
              {priority}
            </Badge>
          )
        },
      },
      {
        ...createSortableHeader("Timestamp", "timestamp"),
        accessorKey: "timestamp",
        cell: ({ row }) => {
          const timestamp = row.getValue("timestamp") as Date
          return (
            <div className="flex flex-col">
              <span className="text-sm">{format(timestamp, "MMM d, yyyy")}</span>
              <span className="text-xs text-muted-foreground">
                {format(timestamp, "h:mm:ss a")}
              </span>
            </div>
          )
        },
      },
      {
        accessorKey: "read",
        header: "Status",
        cell: ({ row }) => {
          const isRead = row.getValue("read") as boolean
          const isDismissible = row.original.dismissible !== false
          
          return (
            <div className="flex items-center gap-2">
              {isRead ? (
                <Badge variant="outline" className="bg-muted">
                  Read
                </Badge>
              ) : (
                <Badge variant="outline" className="bg-blue-500/10 text-blue-700">
                  Unread
                </Badge>
              )}
              {row.original.persist && (
                <Badge variant="outline" className="bg-purple-500/10 text-purple-700">
                  Persisted
                </Badge>
              )}
            </div>
          )
        },
      },
      {
        accessorKey: "sound",
        header: "Sound",
        cell: ({ row }) => {
          const hasSound = row.getValue("sound") as boolean
          return (
            <div className="flex items-center">
              {hasSound ? (
                <Bell className="h-4 w-4 text-muted-foreground" />
              ) : (
                <BellOff className="h-4 w-4 text-muted-foreground/50" />
              )}
            </div>
          )
        },
      },
      {
        accessorKey: "actions",
        header: "Quick Actions",
        cell: ({ row }) => {
          const actions = row.original.actions || []
          if (actions.length === 0) {
            return <span className="text-muted-foreground text-sm">-</span>
          }
          
          return (
            <div className="flex items-center gap-1">
              {actions.slice(0, 2).map((action, index) => (
                <Button
                  key={index}
                  variant={action.variant === "primary" ? "default" : "outline"}
                  size="sm"
                  className="h-7 text-xs"
                  onClick={(e) => {
                    e.stopPropagation()
                    action.onClick()
                  }}
                >
                  {action.label}
                </Button>
              ))}
              {actions.length > 2 && (
                <span className="text-xs text-muted-foreground">
                  +{actions.length - 2}
                </span>
              )}
            </div>
          )
        },
      },
      {
        id: "actions",
        cell: ({ row }) => {
          const alert = row.original

          return (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="h-8 w-8 p-0">
                  <span className="sr-only">Open menu</span>
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>Actions</DropdownMenuLabel>
                <DropdownMenuItem
                  onClick={() => onAlertClick?.(alert)}
                >
                  <Eye className="mr-2 h-4 w-4" />
                  View details
                </DropdownMenuItem>
                {!alert.read && (
                  <DropdownMenuItem
                    onClick={() => onAlertAction?.(alert.id, "markRead")}
                  >
                    <CheckCircle className="mr-2 h-4 w-4" />
                    Mark as read
                  </DropdownMenuItem>
                )}
                {alert.read && (
                  <DropdownMenuItem
                    onClick={() => onAlertAction?.(alert.id, "markUnread")}
                  >
                    <Eye className="mr-2 h-4 w-4" />
                    Mark as unread
                  </DropdownMenuItem>
                )}
                <DropdownMenuSeparator />
                {alert.dismissible !== false && (
                  <DropdownMenuItem
                    onClick={() => onAlertAction?.(alert.id, "dismiss")}
                    className="text-destructive"
                  >
                    <XCircle className="mr-2 h-4 w-4" />
                    Dismiss
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          )
        },
      },
    ],
    [onAlertClick, onAlertAction]
  )

  const filterConfigs: FilterConfig[] = [
    {
      id: "title",
      label: "Title",
      type: "text",
      placeholder: "Search alerts...",
    },
    {
      id: "type",
      label: "Type",
      type: "multiselect",
      options: [
        { label: "Success", value: "success" },
        { label: "Error", value: "error" },
        { label: "Warning", value: "warning" },
        { label: "Info", value: "info" },
      ],
    },
    {
      id: "priority",
      label: "Priority",
      type: "multiselect",
      options: [
        { label: "Low", value: "low" },
        { label: "Normal", value: "normal" },
        { label: "High", value: "high" },
        { label: "Critical", value: "critical" },
      ],
    },
    {
      id: "read",
      label: "Read Status",
      type: "select",
      options: [
        { label: "Read", value: "true" },
        { label: "Unread", value: "false" },
      ],
    },
    {
      id: "timestamp",
      label: "Date",
      type: "daterange",
      placeholder: "Select date range",
    },
  ]

  const bulkActions: BulkAction<Alert>[] = [
    {
      label: "Mark as Read",
      icon: <CheckCircle className="h-4 w-4" />,
      onClick: (alerts) => {
        alerts.forEach((alert) => {
          if (!alert.read) {
            onAlertAction?.(alert.id, "markRead")
          }
        })
      },
    },
    {
      label: "Mark as Unread",
      icon: <Eye className="h-4 w-4" />,
      onClick: (alerts) => {
        alerts.forEach((alert) => {
          if (alert.read) {
            onAlertAction?.(alert.id, "markUnread")
          }
        })
      },
    },
    {
      label: "Dismiss",
      icon: <XCircle className="h-4 w-4" />,
      variant: "destructive",
      confirmMessage: "Are you sure you want to dismiss the selected alerts?",
      onClick: (alerts) => {
        alerts.forEach((alert) => {
          if (alert.dismissible !== false) {
            onAlertAction?.(alert.id, "dismiss")
          }
        })
      },
    },
  ]

  const { table } = useTable({
    data: alerts,
    columns,
    enableRowSelection: true,
    enableMultiSelect: true,
    pageSize: 20,
    initialState: {
      sorting: [{ id: "timestamp", desc: true }],
    },
  })

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Alerts</h2>
        <DataTableExport
          table={table}
          filename="alerts-export"
          exportFormats={["csv", "excel", "json"]}
        />
      </div>

      <DataTableFilters
        table={table}
        filters={filterConfigs}
        onFiltersChange={(filters) => {
          Object.entries(filters).forEach(([key, value]) => {
            if (key === "read") {
              table.getColumn(key)?.setFilterValue(value === "true")
            } else if (key === "timestamp" && value) {
              // Handle date range filtering
              table.getColumn(key)?.setFilterValue(value)
            } else {
              table.getColumn(key)?.setFilterValue(value)
            }
          })
        }}
      />

      <DataTableBulkActions
        table={table}
        actions={bulkActions}
        position="sticky"
      />

      <DataTable
        table={table}
        columns={columns}
        data={alerts}
        enableRowSelection
        enableMultiSelect
        stickyHeader
        showColumnVisibilityToggle
        showPagination
        onRowClick={onAlertClick}
        pageSize={20}
        pageSizeOptions={[10, 20, 30, 50, 100]}
      />

      <DataTablePagination
        table={table}
        showPageJumper
        showPageInfo
        showPageSizeSelector
        showRowCount
      />
    </div>
  )
}