'use client'

import { useState, useMemo, useEffect } from 'react'
import { IncidentList, IncidentDetails } from '@/components/incidents'
import { QuickActionBar } from '@/components/actions/quick-action-bar'
import { generateDemoIncidents } from '@/lib/demo-incidents'
import { Incident } from '@/types/incident'
import { ArrowLeft } from 'lucide-react'
import { useAccessibility } from '@/hooks/use-accessibility'

export default function IncidentsDashboardPage() {
  const [incidents, setIncidents] = useState<Incident[]>(() => generateDemoIncidents())
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null)
  const [selectedIncidentIds, setSelectedIncidentIds] = useState<Set<string>>(new Set())
  const { aria } = useAccessibility()

  const selectedIncident = useMemo(
    () => incidents.find(inc => inc.id === selectedIncidentId),
    [incidents, selectedIncidentId]
  )

  const handleToggleSelect = (id: string) => {
    setSelectedIncidentIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const handleDeselectAll = () => {
    setSelectedIncidentIds(new Set())
  }

  const handleAcknowledge = (id: string) => {
    const incident = incidents.find(inc => inc.id === id)
    if (incident) {
      aria.announceSuccess(`Incident ${incident.title} acknowledged`)
    }
    
    setIncidents(prev => prev.map(inc => 
      inc.id === id 
        ? { 
            ...inc, 
            status: 'acknowledged' as const,
            acknowledgedAt: new Date(),
            updatedAt: new Date(),
            timeline: [
              ...inc.timeline,
              {
                id: `event-ack-${Date.now()}`,
                timestamp: new Date(),
                type: 'status_change' as const,
                actor: 'Current User',
                title: 'Incident Acknowledged',
                description: 'Incident has been acknowledged and team notified'
              }
            ]
          }
        : inc
    ))
  }

  const handleInvestigate = (id: string) => {
    setIncidents(prev => prev.map(inc => 
      inc.id === id 
        ? { 
            ...inc, 
            status: 'investigating' as const,
            updatedAt: new Date(),
            timeline: [
              ...inc.timeline,
              {
                id: `event-inv-${Date.now()}`,
                timestamp: new Date(),
                type: 'status_change' as const,
                actor: 'Current User',
                title: 'Investigation Started',
                description: 'Team is actively investigating the issue'
              }
            ]
          }
        : inc
    ))
  }

  const handleRemediate = (id: string) => {
    setIncidents(prev => prev.map(inc => 
      inc.id === id 
        ? { 
            ...inc, 
            status: 'remediated' as const,
            updatedAt: new Date(),
            timeline: [
              ...inc.timeline,
              {
                id: `event-rem-${Date.now()}`,
                timestamp: new Date(),
                type: 'status_change' as const,
                actor: 'Current User',
                title: 'Remediation Applied',
                description: 'Fix has been applied, monitoring for stability'
              }
            ]
          }
        : inc
    ))
  }

  const handleStatusChange = (status: Incident['status']) => {
    if (!selectedIncidentId) return
    
    const incident = incidents.find(inc => inc.id === selectedIncidentId)
    if (incident) {
      aria.announce(`Incident status changed to ${status}`, 'polite')
    }
    
    setIncidents(prev => prev.map(inc => 
      inc.id === selectedIncidentId 
        ? { 
            ...inc, 
            status,
            updatedAt: new Date(),
            ...(status === 'resolved' && { resolvedAt: new Date() }),
            ...(status === 'closed' && { closedAt: new Date() }),
            timeline: [
              ...inc.timeline,
              {
                id: `event-status-${Date.now()}`,
                timestamp: new Date(),
                type: 'status_change' as const,
                actor: 'Current User',
                title: `Status Changed to ${status}`,
                description: `Incident status updated to ${status}`
              }
            ]
          }
        : inc
    ))
  }

  const handleAddNote = (note: { author: string; content: string; isInternal: boolean }) => {
    if (!selectedIncidentId) return
    
    setIncidents(prev => prev.map(inc => 
      inc.id === selectedIncidentId 
        ? { 
            ...inc,
            notes: [
              ...inc.notes,
              {
                id: `note-${Date.now()}`,
                timestamp: new Date(),
                ...note
              }
            ],
            timeline: [
              ...inc.timeline,
              {
                id: `event-note-${Date.now()}`,
                timestamp: new Date(),
                type: 'comment' as const,
                actor: note.author,
                title: 'Note Added',
                description: note.isInternal ? 'Internal note added' : 'Note added'
              }
            ]
          }
        : inc
    ))
  }

  const handleActionComplete = (action: any, result: any) => {
    // Handle bulk actions
    if (selectedIncidentIds.size > 0 && action.type === 'acknowledge') {
      selectedIncidentIds.forEach(id => handleAcknowledge(id))
      handleDeselectAll()
    } else if (selectedIncidentIds.size > 0 && action.type === 'investigate') {
      selectedIncidentIds.forEach(id => handleInvestigate(id))
      handleDeselectAll()
    } else if (selectedIncidentIds.size > 0 && action.type === 'remediate') {
      selectedIncidentIds.forEach(id => handleRemediate(id))
      handleDeselectAll()
    }
  }

  const handleExecuteRemediation = (stepId: string) => {
    if (!selectedIncidentId) return
    
    setIncidents(prev => prev.map(inc => 
      inc.id === selectedIncidentId 
        ? { 
            ...inc,
            remediationSteps: inc.remediationSteps.map(step =>
              step.id === stepId
                ? { ...step, status: 'in_progress' as const }
                : step
            )
          }
        : inc
    ))

    // Simulate remediation completion after 3 seconds
    setTimeout(() => {
      setIncidents(prev => prev.map(inc => 
        inc.id === selectedIncidentId 
          ? { 
              ...inc,
              remediationSteps: inc.remediationSteps.map(step =>
                step.id === stepId
                  ? { 
                      ...step, 
                      status: 'completed' as const,
                      completedAt: new Date(),
                      completedBy: 'Automation',
                      actualDuration: step.estimatedDuration,
                      result: 'Successfully executed automated remediation step'
                    }
                  : step
              ),
              timeline: [
                ...inc.timeline,
                {
                  id: `event-auto-${Date.now()}`,
                  timestamp: new Date(),
                  type: 'automated_action' as const,
                  actor: 'System',
                  title: 'Automated Remediation Executed',
                  description: `Completed: ${inc.remediationSteps.find(s => s.id === stepId)?.title}`
                }
              ]
            }
          : inc
      ))
    }, 3000)
  }

  if (selectedIncident) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
        <div className="max-w-7xl mx-auto p-6">
          <button
            onClick={() => setSelectedIncidentId(null)}
            className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-6 transition-colors"
            aria-label="Go back to incidents list"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Back to incidents
          </button>
          
          <IncidentDetails
            incident={selectedIncident}
            onStatusChange={handleStatusChange}
            onAddNote={handleAddNote}
            onExecuteRemediation={handleExecuteRemediation}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="max-w-7xl mx-auto p-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Incident Management
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Monitor and manage all incidents across your infrastructure
          </p>
        </div>

        <IncidentList
          incidents={incidents}
          onAcknowledge={handleAcknowledge}
          onInvestigate={handleInvestigate}
          onRemediate={handleRemediate}
          onViewDetails={(id) => setSelectedIncidentId(id)}
          selectedIds={selectedIncidentIds}
          onToggleSelect={handleToggleSelect}
          onActionComplete={handleActionComplete}
        />

        {/* Floating Quick Action Bar */}
        {selectedIncidentIds.size > 0 && (
          <QuickActionBar
            incidentIds={Array.from(selectedIncidentIds)}
            variant="floating"
            onActionComplete={handleActionComplete}
          />
        )}
      </div>
    </div>
  )
}