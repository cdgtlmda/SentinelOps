"use client"

import { useState } from 'react'
import { useIncidentStore, useAgentStore } from '@/store'
import { loadDemoData } from '@/lib/demo-data'
import { TabletLayout, TabletGridLayout } from '@/components/tablet/tablet-layout'
import { AdaptivePanels } from '@/components/tablet/adaptive-panels'
import { ChatInterface } from '@/components/chat'
import { ActivityViewer } from '@/components/activity'
import { QuickActionBar } from '@/components/actions/quick-action-bar'
import { useOptimalLayout } from '@/hooks/use-orientation'
import { Card } from '@/components/ui/card'
import { Shield, AlertTriangle, CheckCircle, Clock, Users, Activity } from 'lucide-react'

export default function TabletDashboardPage() {
  const [selectedIncidentIds, setSelectedIncidentIds] = useState<Set<string>>(new Set())
  const incidents = useIncidentStore((state) => state.incidents)
  const agents = useAgentStore((state) => state.agents)
  const updateIncident = useIncidentStore((state) => state.updateIncident)
  const layout = useOptimalLayout({ sidebar: true, secondaryPanel: true })

  const handleActionComplete = (action: any, result: any) => {
    if (selectedIncidentIds.size > 0) {
      selectedIncidentIds.forEach(id => {
        const incident = incidents.find(i => i.id === id)
        if (!incident) return

        if (action.type === 'acknowledge') {
          updateIncident(id, { 
            status: 'acknowledged',
            acknowledgedAt: new Date(),
            updatedAt: new Date()
          })
        } else if (action.type === 'investigate') {
          updateIncident(id, { 
            status: 'investigating',
            updatedAt: new Date()
          })
        } else if (action.type === 'remediate') {
          updateIncident(id, { 
            status: 'remediated',
            updatedAt: new Date()
          })
        }
      })
      setSelectedIncidentIds(new Set())
    }
  }

  const loadDemoButton = incidents.length === 0 && agents.length === 0 && (
    <button
      onClick={loadDemoData}
      className="px-3 py-1.5 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
    >
      Load Demo Data
    </button>
  )

  // Stats cards for sidebar
  const statsCards = (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Critical</p>
              <p className="text-2xl font-semibold">{incidents.filter(i => i.severity === 'critical').length}</p>
            </div>
          </div>
        </div>
      </Card>
      
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <Clock className="w-5 h-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Pending</p>
              <p className="text-2xl font-semibold">{incidents.filter(i => i.status === 'open').length}</p>
            </div>
          </div>
        </div>
      </Card>
      
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Resolved</p>
              <p className="text-2xl font-semibold">{incidents.filter(i => i.status === 'resolved').length}</p>
            </div>
          </div>
        </div>
      </Card>
      
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Users className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Active Agents</p>
              <p className="text-2xl font-semibold">{agents.filter(a => a.status === 'active').length}</p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )

  // Main content
  const mainContent = (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-4 border-b">
        <h1 className="text-2xl font-bold">Operations Dashboard</h1>
        {loadDemoButton}
      </div>
      
      <div className="flex-1 overflow-hidden">
        {layout.isLandscape ? (
          <AdaptivePanels
            orientation={layout.orientation}
            primaryPanel={<ChatInterface />}
            secondaryPanel={<ActivityViewer />}
            defaultSecondaryWidth={400}
            minSecondaryWidth={350}
            maxSecondaryWidth={600}
          />
        ) : (
          <TabletGridLayout columns={{ portrait: 1, landscape: 2 }}>
            <Card className="h-96">
              <ChatInterface />
            </Card>
            <Card className="h-96">
              <ActivityViewer />
            </Card>
          </TabletGridLayout>
        )}
      </div>
    </div>
  )

  return (
    <TabletLayout
      sidebar={layout.showSidebar && statsCards}
      secondaryPanel={
        layout.showSecondaryPanel && (
          <div className="p-4">
            <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
            <div className="space-y-2">
              {incidents.slice(0, 5).map(incident => (
                <Card key={incident.id} className="p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Shield className="w-4 h-4 text-gray-500" />
                      <span className="text-sm font-medium">{incident.title}</span>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      incident.severity === 'critical' ? 'bg-red-100 text-red-700' :
                      incident.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                      incident.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {incident.severity}
                    </span>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )
      }
    >
      {mainContent}
      
      {/* Quick Action Bar */}
      {incidents.filter(i => i.status !== 'resolved' && i.status !== 'closed').length > 0 && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-50">
          <QuickActionBar
            incidentIds={incidents.filter(i => i.status !== 'resolved' && i.status !== 'closed').map(i => i.id)}
            variant="fixed"
            onActionComplete={handleActionComplete}
          />
        </div>
      )}
    </TabletLayout>
  )
}