"use client"

import { useState, Suspense } from 'react'
import dynamic from 'next/dynamic'
import { useIncidentStore, useAgentStore } from '@/store'
import { loadDemoData } from '@/lib/demo-data'
import { SplitScreen } from '@/components/layout/split-screen'
import { QuickActionBar } from '@/components/actions/quick-action-bar'
import { Loader2 } from 'lucide-react'

// Loading skeleton for chat interface
const ChatSkeleton = () => (
  <div className="flex items-center justify-center h-full">
    <div className="text-center space-y-3">
      <Loader2 className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
      <p className="text-sm text-muted-foreground">Loading chat interface...</p>
    </div>
  </div>
)

// Loading skeleton for activity viewer
const ActivitySkeleton = () => (
  <div className="flex items-center justify-center h-full">
    <div className="text-center space-y-3">
      <Loader2 className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
      <p className="text-sm text-muted-foreground">Loading activity viewer...</p>
    </div>
  </div>
)

// Dynamic imports with loading states
const ChatInterface = dynamic(() => import('@/components/chat').then(mod => mod.ChatInterface), {
  loading: () => <ChatSkeleton />,
  ssr: false
})

const ActivityViewer = dynamic(() => import('@/components/activity').then(mod => mod.ActivityViewer), {
  loading: () => <ActivitySkeleton />,
  ssr: false
})

export default function DashboardPage() {
  const [selectedIncidentIds, setSelectedIncidentIds] = useState<Set<string>>(new Set())
  const incidents = useIncidentStore((state) => state.incidents)
  const agents = useAgentStore((state) => state.agents)
  const updateIncident = useIncidentStore((state) => state.updateIncident)

  const handleActionComplete = (action: any, result: any) => {
    // Handle bulk actions
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

  return (
    <div className="h-[calc(100vh-4rem)] relative">
      <SplitScreen
        leftPanel={{
          id: 'chat',
          title: 'Chat',
          content: <ChatInterface />,
          minWidth: 30,
          maxWidth: 70
        }}
        rightPanel={{
          id: 'activity',
          title: 'Activity',
          content: <ActivityViewer />,
          actions: loadDemoButton,
          minWidth: 30,
          maxWidth: 70
        }}
        defaultLeftWidth={50}
        className="h-full"
      />
      
      {/* Quick Action Bar for active incidents */}
      {incidents.filter(i => i.status !== 'resolved' && i.status !== 'closed').length > 0 && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-50">
          <QuickActionBar
            incidentIds={incidents.filter(i => i.status !== 'resolved' && i.status !== 'closed').map(i => i.id)}
            variant="fixed"
            onActionComplete={handleActionComplete}
          />
        </div>
      )}
    </div>
  )
}