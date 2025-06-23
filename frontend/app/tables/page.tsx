"use client"

import * as React from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { IncidentsTable } from "@/components/tables/incidents-table"
import { AgentsTable } from "@/components/tables/agents-table"
import { AlertsTable } from "@/components/tables/alerts-table"
import { AuditLogTable, AuditLogEntry } from "@/components/tables/audit-log-table"
import { generateMockIncidents } from "@/lib/demo-incidents"
import { generateMockAgents } from "@/lib/demo-data"
import { Alert } from "@/types/alerts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

// Generate mock data for demonstration
const mockIncidents = generateMockIncidents(100)
const mockAgents = generateMockAgents(50)

// Generate mock alerts
const mockAlerts: Alert[] = Array.from({ length: 75 }, (_, i) => ({
  id: `alert-${i + 1}`,
  type: ["success", "error", "warning", "info"][Math.floor(Math.random() * 4)] as Alert["type"],
  title: [
    "System update completed",
    "Failed authentication attempt",
    "High CPU usage detected",
    "New security patch available",
    "Backup completed successfully",
    "Database connection error",
    "SSL certificate expiring soon",
    "Unusual network activity detected",
  ][Math.floor(Math.random() * 8)],
  message: i % 3 === 0 ? "Additional details about this alert would appear here. This could include more context about what triggered the alert and any relevant metrics." : undefined,
  timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000),
  read: Math.random() > 0.3,
  sound: Math.random() > 0.5,
  persist: Math.random() > 0.7,
  priority: ["low", "normal", "high", "critical"][Math.floor(Math.random() * 4)] as Alert["priority"],
  dismissible: Math.random() > 0.1,
  actions: i % 4 === 0 ? [
    { label: "View", onClick: () => console.log("View clicked"), variant: "primary" },
    { label: "Dismiss", onClick: () => console.log("Dismiss clicked") },
  ] : undefined,
}))

// Generate mock audit log entries
const mockAuditLogs: AuditLogEntry[] = Array.from({ length: 200 }, (_, i) => {
  const categories = ["auth", "config", "security", "data", "system"] as const
  const category = categories[Math.floor(Math.random() * categories.length)]
  
  const actionsByCategory = {
    auth: ["user.login", "user.logout", "user.password_reset", "user.2fa_enabled"],
    config: ["config.update", "config.backup", "config.restore", "settings.change"],
    security: ["security.alert", "security.scan", "firewall.update", "access.denied"],
    data: ["data.export", "data.import", "data.delete", "backup.create"],
    system: ["system.restart", "service.start", "service.stop", "update.install"],
  }
  
  const actions = actionsByCategory[category]
  const action = actions[Math.floor(Math.random() * actions.length)]
  
  const users = ["admin", "john.doe", "jane.smith", "system", "api-service"]
  const user = users[Math.floor(Math.random() * users.length)]
  
  return {
    id: `log-${i + 1}`,
    timestamp: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000),
    user,
    userEmail: user !== "system" && user !== "api-service" ? `${user}@example.com` : undefined,
    action,
    category,
    resource: Math.random() > 0.3 ? `resource-${Math.floor(Math.random() * 100)}` : undefined,
    resourceType: Math.random() > 0.3 ? ["server", "database", "file", "user", "config"][Math.floor(Math.random() * 5)] : undefined,
    ipAddress: Math.random() > 0.2 ? `192.168.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}` : undefined,
    userAgent: Math.random() > 0.5 ? "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" : undefined,
    status: Math.random() > 0.85 ? "failure" : Math.random() > 0.7 ? "warning" : "success",
    details: Math.random() > 0.5 ? {
      reason: "User action completed",
      affectedItems: Math.floor(Math.random() * 10) + 1,
    } : undefined,
    metadata: Math.random() > 0.3 ? {
      duration: Math.floor(Math.random() * 1000) + 50,
      changes: Math.random() > 0.5 ? [
        {
          field: "status",
          oldValue: "active",
          newValue: "inactive",
        },
      ] : undefined,
    } : undefined,
  }
})

export default function TablesPage() {
  const [selectedTab, setSelectedTab] = React.useState("incidents")

  const handleIncidentClick = (incident: any) => {
    console.log("Incident clicked:", incident)
  }

  const handleIncidentUpdate = (incident: any) => {
    console.log("Incident updated:", incident)
  }

  const handleAgentClick = (agent: any) => {
    console.log("Agent clicked:", agent)
  }

  const handleAgentAction = (agentId: string, action: string) => {
    console.log("Agent action:", agentId, action)
  }

  const handleAlertClick = (alert: Alert) => {
    console.log("Alert clicked:", alert)
  }

  const handleAlertAction = (alertId: string, action: string) => {
    console.log("Alert action:", alertId, action)
  }

  const handleAuditLogClick = (entry: AuditLogEntry) => {
    console.log("Audit log entry clicked:", entry)
  }

  return (
    <div className="container mx-auto py-8 space-y-8">
      <div>
        <h1 className="text-4xl font-bold mb-2">Data Tables</h1>
        <p className="text-muted-foreground">
          Comprehensive data table components with advanced features including sorting, filtering,
          pagination, row selection, bulk actions, and data export.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Table Features</CardTitle>
          <CardDescription>
            All tables include the following features:
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-2">
              <h4 className="font-medium">Data Management</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Sortable columns (click headers)</li>
                <li>• Advanced filtering with multiple types</li>
                <li>• Column visibility toggle</li>
                <li>• Sticky table headers</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="font-medium">Selection & Actions</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Row selection (single/multi)</li>
                <li>• Bulk actions toolbar</li>
                <li>• Row click handlers</li>
                <li>• Context menu actions</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="font-medium">Export & Navigation</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Export to CSV, Excel, JSON</li>
                <li>• Advanced pagination controls</li>
                <li>• Page size selection</li>
                <li>• Keyboard navigation support</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="incidents">Incidents</TabsTrigger>
          <TabsTrigger value="agents">Agents</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="audit">Audit Log</TabsTrigger>
        </TabsList>

        <TabsContent value="incidents" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Incidents Table</CardTitle>
              <CardDescription>
                Manage and track security incidents with severity levels, status tracking, and resource impact.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <IncidentsTable
                incidents={mockIncidents}
                onIncidentClick={handleIncidentClick}
                onIncidentUpdate={handleIncidentUpdate}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="agents" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Agents Table</CardTitle>
              <CardDescription>
                Monitor and control AI agents with real-time status, performance metrics, and task management.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AgentsTable
                agents={mockAgents}
                onAgentClick={handleAgentClick}
                onAgentAction={handleAgentAction}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Alerts Table</CardTitle>
              <CardDescription>
                View and manage system alerts with priority levels, read status, and quick actions.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AlertsTable
                alerts={mockAlerts}
                onAlertClick={handleAlertClick}
                onAlertAction={handleAlertAction}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="audit" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Audit Log Table</CardTitle>
              <CardDescription>
                Track all system activities and changes with detailed logging, user attribution, and status tracking.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AuditLogTable
                entries={mockAuditLogs}
                onEntryClick={handleAuditLogClick}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Card>
        <CardHeader>
          <CardTitle>Usage Tips</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-medium mb-2">Filtering</h4>
            <p className="text-sm text-muted-foreground">
              Use the filter bar to search and filter data. Multiple filters can be applied simultaneously.
              Clear individual filters with the × button or use "Clear all" to reset.
            </p>
          </div>
          <div>
            <h4 className="font-medium mb-2">Bulk Operations</h4>
            <p className="text-sm text-muted-foreground">
              Select multiple rows using the checkboxes to enable bulk actions. The bulk actions toolbar
              will appear with context-specific actions for the selected items.
            </p>
          </div>
          <div>
            <h4 className="font-medium mb-2">Data Export</h4>
            <p className="text-sm text-muted-foreground">
              Export data in various formats using the Export button. You can export all data or only
              selected rows, and choose which columns to include in the export.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}