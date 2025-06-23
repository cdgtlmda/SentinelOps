"use client"

import * as React from "react"
import { ColumnDef } from "@tanstack/react-table"
import { format } from "date-fns"
import { MoreHorizontal, AlertCircle, Clock, CheckCircle } from "lucide-react"

import { Incident, IncidentSeverity, IncidentStatus } from "@/types/incident"
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

interface IncidentsTableProps {
  incidents: Incident[]
  onIncidentClick?: (incident: Incident) => void
  onIncidentUpdate?: (incident: Incident) => void
  className?: string
}

const severityColors: Record<IncidentSeverity, string> = {
  critical: "bg-red-500/10 text-red-700 border-red-500/20",
  high: "bg-orange-500/10 text-orange-700 border-orange-500/20",
  medium: "bg-yellow-500/10 text-yellow-700 border-yellow-500/20",
  low: "bg-blue-500/10 text-blue-700 border-blue-500/20",
}

const statusIcons: Record<IncidentStatus, React.ReactNode> = {
  new: <AlertCircle className="h-3 w-3" />,
  acknowledged: <Clock className="h-3 w-3" />,
  investigating: <Clock className="h-3 w-3 animate-pulse" />,
  remediated: <CheckCircle className="h-3 w-3" />,
  resolved: <CheckCircle className="h-3 w-3" />,
  closed: <CheckCircle className="h-3 w-3" />,
}

export function IncidentsTable({
  incidents,
  onIncidentClick,
  onIncidentUpdate,
  className,
}: IncidentsTableProps) {
  const columns: ColumnDef<Incident>[] = React.useMemo(
    () => [
      {
        ...createSortableHeader("Title", "title"),
        accessorKey: "title",
        cell: ({ row }) => (
          <div className="flex flex-col">
            <span className="font-medium">{row.getValue("title")}</span>
            <span className="text-xs text-muted-foreground">
              {row.original.id}
            </span>
          </div>
        ),
      },
      {
        ...createSortableHeader("Severity", "severity"),
        accessorKey: "severity",
        cell: ({ row }) => {
          const severity = row.getValue("severity") as IncidentSeverity
          return (
            <Badge
              variant="outline"
              className={cn("capitalize", severityColors[severity])}
            >
              {severity}
            </Badge>
          )
        },
      },
      {
        ...createSortableHeader("Status", "status"),
        accessorKey: "status",
        cell: ({ row }) => {
          const status = row.getValue("status") as IncidentStatus
          return (
            <div className="flex items-center gap-2">
              {statusIcons[status]}
              <span className="capitalize">{status.replace("_", " ")}</span>
            </div>
          )
        },
      },
      {
        ...createSortableHeader("Created", "createdAt"),
        accessorKey: "createdAt",
        cell: ({ row }) => {
          const date = row.getValue("createdAt") as Date
          return (
            <div className="flex flex-col">
              <span>{format(date, "MMM d, yyyy")}</span>
              <span className="text-xs text-muted-foreground">
                {format(date, "h:mm a")}
              </span>
            </div>
          )
        },
      },
      {
        accessorKey: "assignedTo",
        header: "Assigned To",
        cell: ({ row }) => {
          const assignee = row.getValue("assignedTo") as string | undefined
          return assignee ? (
            <div className="flex items-center gap-2">
              <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center">
                <span className="text-xs font-medium">
                  {assignee.charAt(0).toUpperCase()}
                </span>
              </div>
              <span className="text-sm">{assignee}</span>
            </div>
          ) : (
            <span className="text-muted-foreground">Unassigned</span>
          )
        },
      },
      {
        accessorKey: "affectedResources",
        header: "Resources",
        cell: ({ row }) => {
          const resources = row.original.affectedResources
          return (
            <div className="flex items-center gap-1">
              <span className="text-sm">{resources.length}</span>
              <span className="text-xs text-muted-foreground">
                resource{resources.length !== 1 ? "s" : ""}
              </span>
            </div>
          )
        },
      },
      {
        id: "actions",
        cell: ({ row }) => {
          const incident = row.original

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
                  onClick={() => onIncidentClick?.(incident)}
                >
                  View details
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    const updated = { ...incident, status: "acknowledged" as IncidentStatus }
                    onIncidentUpdate?.(updated)
                  }}
                  disabled={incident.status !== "new"}
                >
                  Acknowledge
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    const updated = { ...incident, status: "investigating" as IncidentStatus }
                    onIncidentUpdate?.(updated)
                  }}
                  disabled={["resolved", "closed"].includes(incident.status)}
                >
                  Start investigating
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => {
                    const updated = { ...incident, status: "resolved" as IncidentStatus }
                    onIncidentUpdate?.(updated)
                  }}
                  disabled={["resolved", "closed"].includes(incident.status)}
                >
                  Mark as resolved
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )
        },
      },
    ],
    [onIncidentClick, onIncidentUpdate]
  )

  const filterConfigs: FilterConfig[] = [
    {
      id: "title",
      label: "Title",
      type: "text",
      placeholder: "Search incidents...",
    },
    {
      id: "severity",
      label: "Severity",
      type: "multiselect",
      options: [
        { label: "Critical", value: "critical" },
        { label: "High", value: "high" },
        { label: "Medium", value: "medium" },
        { label: "Low", value: "low" },
      ],
    },
    {
      id: "status",
      label: "Status",
      type: "multiselect",
      options: [
        { label: "New", value: "new" },
        { label: "Acknowledged", value: "acknowledged" },
        { label: "Investigating", value: "investigating" },
        { label: "Remediated", value: "remediated" },
        { label: "Resolved", value: "resolved" },
        { label: "Closed", value: "closed" },
      ],
    },
    {
      id: "createdAt",
      label: "Created Date",
      type: "daterange",
      placeholder: "Select date range",
    },
  ]

  const bulkActions: BulkAction<Incident>[] = [
    {
      label: "Acknowledge",
      icon: <Clock className="h-4 w-4" />,
      onClick: (incidents) => {
        incidents.forEach((incident) => {
          if (incident.status === "new") {
            onIncidentUpdate?.({ ...incident, status: "acknowledged" })
          }
        })
      },
    },
    {
      label: "Assign to me",
      onClick: (incidents) => {
        incidents.forEach((incident) => {
          onIncidentUpdate?.({ ...incident, assignedTo: "current-user" })
        })
      },
    },
    {
      label: "Close",
      icon: <CheckCircle className="h-4 w-4" />,
      onClick: (incidents) => {
        incidents.forEach((incident) => {
          if (incident.status === "resolved") {
            onIncidentUpdate?.({ ...incident, status: "closed" })
          }
        })
      },
    },
  ]

  const {
    table,
    columnFilters,
    setColumnFilters,
  } = useTable({
    data: incidents,
    columns,
    enableRowSelection: true,
    enableMultiSelect: true,
    pageSize: 20,
  })

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Incidents</h2>
        <DataTableExport
          table={table}
          filename="incidents-export"
          exportFormats={["csv", "excel", "json"]}
        />
      </div>

      <DataTableFilters
        table={table}
        filters={filterConfigs}
        onFiltersChange={(filters) => {
          // Apply custom filtering logic for different filter types
          Object.entries(filters).forEach(([key, value]) => {
            if (key === "severity" || key === "status") {
              table.getColumn(key)?.setFilterValue(value)
            } else if (key === "createdAt" && value) {
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
        data={incidents}
        enableRowSelection
        enableMultiSelect
        stickyHeader
        showColumnVisibilityToggle
        showPagination
        onRowClick={onIncidentClick}
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