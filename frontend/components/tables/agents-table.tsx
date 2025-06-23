"use client"

import * as React from "react"
import { ColumnDef } from "@tanstack/react-table"
import { format } from "date-fns"
import { 
  MoreHorizontal, 
  Play, 
  Pause, 
  RefreshCw, 
  AlertCircle,
  Activity,
  Cpu,
  MemoryStick
} from "lucide-react"

import { Agent, AgentType, AgentStatus } from "@/types/agent"
import { DataTable, createSortableHeader } from "./data-table"
import { DataTableFilters, FilterConfig } from "./data-table-filters"
import { DataTablePagination } from "./data-table-pagination"
import { DataTableExport } from "./data-table-export"
import { DataTableBulkActions, BulkAction } from "./data-table-bulk-actions"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
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

interface AgentsTableProps {
  agents: Agent[]
  onAgentClick?: (agent: Agent) => void
  onAgentAction?: (agentId: string, action: string) => void
  className?: string
}

const typeColors: Record<AgentType, string> = {
  security: "bg-purple-500/10 text-purple-700 border-purple-500/20",
  monitoring: "bg-blue-500/10 text-blue-700 border-blue-500/20",
  remediation: "bg-green-500/10 text-green-700 border-green-500/20",
  analysis: "bg-orange-500/10 text-orange-700 border-orange-500/20",
  network: "bg-cyan-500/10 text-cyan-700 border-cyan-500/20",
}

const statusColors: Record<AgentStatus, string> = {
  idle: "bg-gray-500/10 text-gray-700 border-gray-500/20",
  processing: "bg-blue-500/10 text-blue-700 border-blue-500/20",
  waiting: "bg-yellow-500/10 text-yellow-700 border-yellow-500/20",
  error: "bg-red-500/10 text-red-700 border-red-500/20",
  completed: "bg-green-500/10 text-green-700 border-green-500/20",
}

export function AgentsTable({
  agents,
  onAgentClick,
  onAgentAction,
  className,
}: AgentsTableProps) {
  const columns: ColumnDef<Agent>[] = React.useMemo(
    () => [
      {
        ...createSortableHeader("Name", "name"),
        accessorKey: "name",
        cell: ({ row }) => (
          <div className="flex items-center gap-2">
            <div className={cn(
              "h-2 w-2 rounded-full",
              row.original.isActive ? "bg-green-500" : "bg-gray-400"
            )} />
            <div className="flex flex-col">
              <span className="font-medium">{row.getValue("name")}</span>
              <span className="text-xs text-muted-foreground">
                {row.original.id}
              </span>
            </div>
          </div>
        ),
      },
      {
        accessorKey: "type",
        header: "Type",
        cell: ({ row }) => {
          const type = row.getValue("type") as AgentType
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
        ...createSortableHeader("Status", "status"),
        accessorKey: "status",
        cell: ({ row }) => {
          const status = row.getValue("status") as AgentStatus
          const task = row.original.currentTask
          return (
            <div className="flex flex-col gap-1">
              <Badge
                variant="outline"
                className={cn("capitalize w-fit", statusColors[status])}
              >
                {status}
              </Badge>
              {task && status === "processing" && (
                <div className="flex items-center gap-2">
                  <Progress value={task.progress} className="w-20 h-2" />
                  <span className="text-xs text-muted-foreground">
                    {task.progress}%
                  </span>
                </div>
              )}
            </div>
          )
        },
      },
      {
        accessorKey: "currentTask",
        header: "Current Task",
        cell: ({ row }) => {
          const task = row.original.currentTask
          if (!task) return <span className="text-muted-foreground">-</span>
          
          return (
            <div className="flex flex-col">
              <span className="text-sm">{task.name}</span>
              <span className="text-xs text-muted-foreground">
                Started {format(task.startTime, "h:mm a")}
              </span>
            </div>
          )
        },
      },
      {
        accessorKey: "metrics",
        header: "Performance",
        cell: ({ row }) => {
          const metrics = row.original.metrics
          return (
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1">
                <Cpu className="h-3 w-3 text-muted-foreground" />
                <span>{metrics.cpuUsage}%</span>
              </div>
              <div className="flex items-center gap-1">
                <MemoryStick className="h-3 w-3 text-muted-foreground" />
                <span>{metrics.memoryUsage}%</span>
              </div>
              <div className="flex items-center gap-1">
                <Activity className="h-3 w-3 text-muted-foreground" />
                <span>{metrics.averageResponseTime}ms</span>
              </div>
            </div>
          )
        },
      },
      {
        ...createSortableHeader("Last Action", "lastActionTimestamp"),
        accessorKey: "lastActionTimestamp",
        cell: ({ row }) => {
          const timestamp = row.getValue("lastActionTimestamp") as Date
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
        accessorKey: "metrics.tasksCompleted",
        header: "Tasks",
        cell: ({ row }) => {
          const metrics = row.original.metrics
          const total = metrics.tasksCompleted + metrics.tasksFailed
          const successRate = total > 0 
            ? Math.round((metrics.tasksCompleted / total) * 100) 
            : 0
            
          return (
            <div className="flex flex-col">
              <span className="text-sm">{metrics.tasksCompleted} completed</span>
              <span className="text-xs text-muted-foreground">
                {successRate}% success rate
              </span>
            </div>
          )
        },
      },
      {
        id: "actions",
        cell: ({ row }) => {
          const agent = row.original

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
                  onClick={() => onAgentClick?.(agent)}
                >
                  View details
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                {agent.isActive ? (
                  <DropdownMenuItem
                    onClick={() => onAgentAction?.(agent.id, "stop")}
                  >
                    <Pause className="mr-2 h-4 w-4" />
                    Stop agent
                  </DropdownMenuItem>
                ) : (
                  <DropdownMenuItem
                    onClick={() => onAgentAction?.(agent.id, "start")}
                  >
                    <Play className="mr-2 h-4 w-4" />
                    Start agent
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem
                  onClick={() => onAgentAction?.(agent.id, "restart")}
                >
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Restart agent
                </DropdownMenuItem>
                {agent.error && (
                  <DropdownMenuItem
                    onClick={() => onAgentAction?.(agent.id, "clearError")}
                  >
                    <AlertCircle className="mr-2 h-4 w-4" />
                    Clear error
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          )
        },
      },
    ],
    [onAgentClick, onAgentAction]
  )

  const filterConfigs: FilterConfig[] = [
    {
      id: "name",
      label: "Name",
      type: "text",
      placeholder: "Search agents...",
    },
    {
      id: "type",
      label: "Type",
      type: "multiselect",
      options: [
        { label: "Security", value: "security" },
        { label: "Monitoring", value: "monitoring" },
        { label: "Remediation", value: "remediation" },
        { label: "Analysis", value: "analysis" },
        { label: "Network", value: "network" },
      ],
    },
    {
      id: "status",
      label: "Status",
      type: "multiselect",
      options: [
        { label: "Idle", value: "idle" },
        { label: "Processing", value: "processing" },
        { label: "Waiting", value: "waiting" },
        { label: "Error", value: "error" },
        { label: "Completed", value: "completed" },
      ],
    },
    {
      id: "isActive",
      label: "Active State",
      type: "select",
      options: [
        { label: "Active", value: "true" },
        { label: "Inactive", value: "false" },
      ],
    },
  ]

  const bulkActions: BulkAction<Agent>[] = [
    {
      label: "Start",
      icon: <Play className="h-4 w-4" />,
      onClick: (agents) => {
        agents.forEach((agent) => {
          if (!agent.isActive) {
            onAgentAction?.(agent.id, "start")
          }
        })
      },
    },
    {
      label: "Stop",
      icon: <Pause className="h-4 w-4" />,
      onClick: (agents) => {
        agents.forEach((agent) => {
          if (agent.isActive) {
            onAgentAction?.(agent.id, "stop")
          }
        })
      },
    },
    {
      label: "Restart",
      icon: <RefreshCw className="h-4 w-4" />,
      onClick: (agents) => {
        agents.forEach((agent) => {
          onAgentAction?.(agent.id, "restart")
        })
      },
    },
    {
      label: "Clear Errors",
      icon: <AlertCircle className="h-4 w-4" />,
      onClick: (agents) => {
        agents.forEach((agent) => {
          if (agent.error) {
            onAgentAction?.(agent.id, "clearError")
          }
        })
      },
    },
  ]

  const { table } = useTable({
    data: agents,
    columns,
    enableRowSelection: true,
    enableMultiSelect: true,
    pageSize: 20,
  })

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Agents</h2>
        <DataTableExport
          table={table}
          filename="agents-export"
          exportFormats={["csv", "excel", "json"]}
        />
      </div>

      <DataTableFilters
        table={table}
        filters={filterConfigs}
        onFiltersChange={(filters) => {
          Object.entries(filters).forEach(([key, value]) => {
            if (key === "isActive") {
              table.getColumn(key)?.setFilterValue(value === "true")
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
        data={agents}
        enableRowSelection
        enableMultiSelect
        stickyHeader
        showColumnVisibilityToggle
        showPagination
        onRowClick={onAgentClick}
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