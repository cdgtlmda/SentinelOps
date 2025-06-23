"use client"

import * as React from "react"
import { ColumnDef } from "@tanstack/react-table"
import { format } from "date-fns"
import { 
  User, 
  Settings, 
  Shield, 
  AlertCircle,
  Activity,
  FileEdit,
  UserPlus,
  LogOut,
  Key
} from "lucide-react"

import { DataTableVirtual, createSortableHeader } from "./data-table-virtual"
import { DataTableFilters, FilterConfig } from "./data-table-filters"
import { DataTableExport } from "./data-table-export"
import { Badge } from "@/components/ui/badge"
import { useTable } from "@/hooks/use-table"
import { cn } from "@/lib/utils"

export interface AuditLogEntry {
  id: string
  timestamp: Date
  user: string
  userEmail?: string
  action: string
  category: "auth" | "config" | "security" | "data" | "system"
  resource?: string
  resourceType?: string
  ipAddress?: string
  userAgent?: string
  status: "success" | "failure" | "warning"
  details?: Record<string, any>
  metadata?: {
    duration?: number
    changes?: Array<{
      field: string
      oldValue: any
      newValue: any
    }>
  }
}

interface AuditLogTableVirtualProps {
  entries: AuditLogEntry[]
  onEntryClick?: (entry: AuditLogEntry) => void
  className?: string
  containerHeight?: string | number
}

const categoryIcons: Record<AuditLogEntry["category"], React.ReactNode> = {
  auth: <Key className="h-4 w-4" />,
  config: <Settings className="h-4 w-4" />,
  security: <Shield className="h-4 w-4" />,
  data: <FileEdit className="h-4 w-4" />,
  system: <Activity className="h-4 w-4" />,
}

const categoryColors: Record<AuditLogEntry["category"], string> = {
  auth: "bg-purple-500/10 text-purple-700 border-purple-500/20",
  config: "bg-blue-500/10 text-blue-700 border-blue-500/20",
  security: "bg-red-500/10 text-red-700 border-red-500/20",
  data: "bg-green-500/10 text-green-700 border-green-500/20",
  system: "bg-gray-500/10 text-gray-700 border-gray-500/20",
}

const statusColors: Record<AuditLogEntry["status"], string> = {
  success: "bg-green-500/10 text-green-700 border-green-500/20",
  failure: "bg-red-500/10 text-red-700 border-red-500/20",
  warning: "bg-yellow-500/10 text-yellow-700 border-yellow-500/20",
}

const actionIcons: Record<string, React.ReactNode> = {
  "user.login": <LogOut className="h-3 w-3" />,
  "user.logout": <LogOut className="h-3 w-3" />,
  "user.create": <UserPlus className="h-3 w-3" />,
  "user.update": <User className="h-3 w-3" />,
  "config.update": <Settings className="h-3 w-3" />,
  "security.alert": <AlertCircle className="h-3 w-3" />,
}

export function AuditLogTableVirtual({
  entries,
  onEntryClick,
  className,
  containerHeight = "calc(100vh - 300px)",
}: AuditLogTableVirtualProps) {
  const [filteredEntries, setFilteredEntries] = React.useState(entries)

  const columns: ColumnDef<AuditLogEntry>[] = React.useMemo(
    () => [
      {
        ...createSortableHeader("Timestamp", "timestamp"),
        accessorKey: "timestamp",
        size: 180,
        cell: ({ row }) => {
          const timestamp = row.getValue("timestamp") as Date
          return (
            <div className="flex flex-col">
              <span className="text-sm font-medium">
                {format(timestamp, "MMM d, yyyy")}
              </span>
              <span className="text-xs text-muted-foreground">
                {format(timestamp, "h:mm:ss.SSS a")}
              </span>
            </div>
          )
        },
      },
      {
        accessorKey: "user",
        header: "User",
        size: 200,
        cell: ({ row }) => {
          const user = row.getValue("user") as string
          const email = row.original.userEmail
          return (
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                <span className="text-sm font-medium">
                  {user.charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-medium">{user}</span>
                {email && (
                  <span className="text-xs text-muted-foreground">{email}</span>
                )}
              </div>
            </div>
          )
        },
      },
      {
        accessorKey: "action",
        header: "Action",
        size: 180,
        cell: ({ row }) => {
          const action = row.getValue("action") as string
          const icon = actionIcons[action]
          return (
            <div className="flex items-center gap-2">
              {icon}
              <span className="text-sm">{action}</span>
            </div>
          )
        },
      },
      {
        accessorKey: "category",
        header: "Category",
        size: 120,
        cell: ({ row }) => {
          const category = row.getValue("category") as AuditLogEntry["category"]
          return (
            <Badge
              variant="outline"
              className={cn("capitalize gap-1", categoryColors[category])}
            >
              {categoryIcons[category]}
              {category}
            </Badge>
          )
        },
      },
      {
        accessorKey: "resource",
        header: "Resource",
        size: 200,
        cell: ({ row }) => {
          const resource = row.original.resource
          const resourceType = row.original.resourceType
          
          if (!resource) {
            return <span className="text-muted-foreground">-</span>
          }
          
          return (
            <div className="flex flex-col">
              <span className="text-sm">{resource}</span>
              {resourceType && (
                <span className="text-xs text-muted-foreground">
                  {resourceType}
                </span>
              )}
            </div>
          )
        },
      },
      {
        accessorKey: "status",
        header: "Status",
        size: 100,
        cell: ({ row }) => {
          const status = row.getValue("status") as AuditLogEntry["status"]
          return (
            <Badge
              variant="outline"
              className={cn("capitalize", statusColors[status])}
            >
              {status}
            </Badge>
          )
        },
      },
      {
        accessorKey: "ipAddress",
        header: "IP Address",
        size: 140,
        cell: ({ row }) => {
          const ip = row.getValue("ipAddress") as string | undefined
          return ip ? (
            <code className="text-xs bg-muted px-1 py-0.5 rounded">
              {ip}
            </code>
          ) : (
            <span className="text-muted-foreground">-</span>
          )
        },
      },
      {
        accessorKey: "metadata",
        header: "Details",
        size: 160,
        cell: ({ row }) => {
          const metadata = row.original.metadata
          const details = row.original.details
          const hasChanges = metadata?.changes && metadata.changes.length > 0
          const hasDetails = details && Object.keys(details).length > 0
          
          if (!hasChanges && !hasDetails) {
            return <span className="text-muted-foreground">-</span>
          }
          
          return (
            <div className="flex items-center gap-2 text-xs">
              {hasChanges && (
                <Badge variant="outline" className="text-xs">
                  {metadata.changes!.length} changes
                </Badge>
              )}
              {metadata?.duration && (
                <span className="text-muted-foreground">
                  {metadata.duration}ms
                </span>
              )}
            </div>
          )
        },
      },
    ],
    []
  )

  const filterConfigs: FilterConfig[] = [
    {
      id: "user",
      label: "User",
      type: "text",
      placeholder: "Search by user...",
    },
    {
      id: "action",
      label: "Action",
      type: "text",
      placeholder: "Search by action...",
    },
    {
      id: "category",
      label: "Category",
      type: "multiselect",
      options: [
        { label: "Authentication", value: "auth" },
        { label: "Configuration", value: "config" },
        { label: "Security", value: "security" },
        { label: "Data", value: "data" },
        { label: "System", value: "system" },
      ],
    },
    {
      id: "status",
      label: "Status",
      type: "multiselect",
      options: [
        { label: "Success", value: "success" },
        { label: "Failure", value: "failure" },
        { label: "Warning", value: "warning" },
      ],
    },
    {
      id: "timestamp",
      label: "Date",
      type: "daterange",
      placeholder: "Select date range",
    },
  ]

  const { table } = useTable({
    data: filteredEntries,
    columns,
    enableRowSelection: false,
    initialState: {
      sorting: [{ id: "timestamp", desc: true }],
    },
  })

  const handleFiltersChange = React.useCallback((filters: Record<string, any>) => {
    let filtered = [...entries]

    if (filters.user) {
      filtered = filtered.filter((entry) =>
        entry.user.toLowerCase().includes(filters.user.toLowerCase()) ||
        (entry.userEmail?.toLowerCase().includes(filters.user.toLowerCase()) ?? false)
      )
    }

    if (filters.action) {
      filtered = filtered.filter((entry) =>
        entry.action.toLowerCase().includes(filters.action.toLowerCase())
      )
    }

    if (filters.category && filters.category.length > 0) {
      filtered = filtered.filter((entry) =>
        filters.category.includes(entry.category)
      )
    }

    if (filters.status && filters.status.length > 0) {
      filtered = filtered.filter((entry) =>
        filters.status.includes(entry.status)
      )
    }

    if (filters.timestamp) {
      const { from, to } = filters.timestamp
      if (from) {
        filtered = filtered.filter((entry) => entry.timestamp >= from)
      }
      if (to) {
        filtered = filtered.filter((entry) => entry.timestamp <= to)
      }
    }

    setFilteredEntries(filtered)
  }, [entries])

  React.useEffect(() => {
    setFilteredEntries(entries)
  }, [entries])

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Audit Log (Virtual Scrolling)</h2>
        <DataTableExport
          table={table}
          filename="audit-log-export"
          exportFormats={["csv", "excel", "json"]}
        />
      </div>

      <DataTableFilters
        table={table}
        filters={filterConfigs}
        onFiltersChange={handleFiltersChange}
      />

      <DataTableVirtual
        table={table}
        columns={columns}
        data={filteredEntries}
        enableRowSelection={false}
        stickyHeader
        showColumnVisibilityToggle
        onRowClick={onEntryClick}
        containerHeight={containerHeight}
        rowHeight={72}
        overscan={5}
      />
    </div>
  )
}