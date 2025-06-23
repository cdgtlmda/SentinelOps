"use client"

import { useState } from 'react'
import { useIncidentStore, useUIStore } from '@/store'
import type { IncidentStatus, IncidentSeverity, Incident } from '@/store'
import { MasterDetailView } from '@/components/tablet/master-detail-view'
import { TwoColumnLayout } from '@/components/tablet/tablet-layout'
import { useOptimalLayout } from '@/hooks/use-orientation'
import { Card } from '@/components/ui/card'
import { Shield, AlertTriangle, Clock, CheckCircle, XCircle, ChevronRight } from 'lucide-react'

export default function TabletIncidentsPage() {
  const incidents = useIncidentStore((state) => state.incidents)
  const viewMode = useUIStore((state) => state.incidentViewMode)
  const setViewMode = useUIStore((state) => state.setIncidentViewMode)
  const layout = useOptimalLayout()
  
  const [filterStatus, setFilterStatus] = useState<IncidentStatus | 'all'>('all')
  const [filterSeverity, setFilterSeverity] = useState<IncidentSeverity | 'all'>('all')
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | undefined>()
  
  const filteredIncidents = incidents.filter(incident => {
    if (filterStatus !== 'all' && incident.status !== filterStatus) return false
    if (filterSeverity !== 'all' && incident.severity !== filterSeverity) return false
    return true
  })

  const renderListItem = (incident: Incident, isSelected: boolean) => (
    <div className={`p-4 ${isSelected ? 'bg-blue-50' : ''}`}>
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-semibold text-gray-900 flex-1 pr-2">{incident.title}</h3>
        <div className="flex items-center gap-2">
          {incident.severity === 'critical' && <AlertTriangle className="w-4 h-4 text-red-600" />}
          {incident.status === 'active' && <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />}
        </div>
      </div>
      
      <p className="text-sm text-gray-600 line-clamp-2 mb-3">{incident.description}</p>
      
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <span className={`px-2 py-1 text-xs rounded-full ${
            incident.severity === 'critical' ? 'bg-red-100 text-red-700' :
            incident.severity === 'high' ? 'bg-orange-100 text-orange-700' :
            incident.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
            'bg-gray-100 text-gray-700'
          }`}>
            {incident.severity}
          </span>
          <span className={`px-2 py-1 text-xs rounded-full ${
            incident.status === 'active' ? 'bg-red-100 text-red-700' :
            incident.status === 'investigating' ? 'bg-yellow-100 text-yellow-700' :
            incident.status === 'resolved' ? 'bg-green-100 text-green-700' :
            'bg-gray-100 text-gray-700'
          }`}>
            {incident.status}
          </span>
        </div>
        <span className="text-xs text-gray-500">
          {new Date(incident.createdAt).toLocaleTimeString()}
        </span>
      </div>
    </div>
  )

  const renderDetail = (incident: Incident) => (
    <div className="p-6">
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-4">
          {incident.severity === 'critical' && (
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
          )}
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900">{incident.title}</h2>
            <p className="text-sm text-gray-500 mt-1">ID: {incident.id}</p>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4 mb-6">
          <Card className="p-4">
            <p className="text-sm text-gray-600 mb-1">Status</p>
            <div className="flex items-center gap-2">
              {incident.status === 'active' && <Clock className="w-4 h-4 text-yellow-500" />}
              {incident.status === 'investigating' && <Shield className="w-4 h-4 text-blue-500" />}
              {incident.status === 'resolved' && <CheckCircle className="w-4 h-4 text-green-500" />}
              {incident.status === 'closed' && <XCircle className="w-4 h-4 text-gray-500" />}
              <span className="font-medium capitalize">{incident.status}</span>
            </div>
          </Card>
          
          <Card className="p-4">
            <p className="text-sm text-gray-600 mb-1">Severity</p>
            <div className="flex items-center gap-2">
              <span className={`px-3 py-1 text-sm rounded-full font-medium ${
                incident.severity === 'critical' ? 'bg-red-100 text-red-700' :
                incident.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                incident.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                'bg-gray-100 text-gray-700'
              }`}>
                {incident.severity.toUpperCase()}
              </span>
            </div>
          </Card>
        </div>
        
        <div className="space-y-4">
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Description</h3>
            <p className="text-gray-600">{incident.description}</p>
          </div>
          
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Timeline</h3>
            <div className="space-y-2">
              <div className="flex items-center gap-3 text-sm">
                <span className="text-gray-500">Created:</span>
                <span>{new Date(incident.createdAt).toLocaleString()}</span>
              </div>
              {incident.acknowledgedAt && (
                <div className="flex items-center gap-3 text-sm">
                  <span className="text-gray-500">Acknowledged:</span>
                  <span>{new Date(incident.acknowledgedAt).toLocaleString()}</span>
                </div>
              )}
              {incident.resolvedAt && (
                <div className="flex items-center gap-3 text-sm">
                  <span className="text-gray-500">Resolved:</span>
                  <span>{new Date(incident.resolvedAt).toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>
          
          {incident.tags && incident.tags.length > 0 && (
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Tags</h3>
              <div className="flex flex-wrap gap-2">
                {incident.tags.map(tag => (
                  <span key={tag} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
      
      <div className="border-t pt-4">
        <div className="flex gap-3">
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            Acknowledge
          </button>
          <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
            Assign Agent
          </button>
          <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
            Add Note
          </button>
        </div>
      </div>
    </div>
  )

  // For landscape mode in tablets, use two-column layout
  if (layout.isLandscape && layout.columns >= 2) {
    return (
      <TwoColumnLayout
        leftWidth="w-2/5"
        left={
          <div className="h-full flex flex-col">
            <div className="p-4 border-b">
              <h1 className="text-xl font-bold mb-4">Incidents</h1>
              
              <div className="flex flex-col gap-3">
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value as IncidentStatus | 'all')}
                  className="px-3 py-2 border rounded-lg text-sm"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="investigating">Investigating</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                </select>
                
                <select
                  value={filterSeverity}
                  onChange={(e) => setFilterSeverity(e.target.value as IncidentSeverity | 'all')}
                  className="px-3 py-2 border rounded-lg text-sm"
                >
                  <option value="all">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto">
              {filteredIncidents.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  No incidents found
                </div>
              ) : (
                <div className="divide-y">
                  {filteredIncidents.map(incident => (
                    <div
                      key={incident.id}
                      onClick={() => setSelectedIncidentId(incident.id)}
                      className={`cursor-pointer transition-colors hover:bg-gray-50 ${
                        selectedIncidentId === incident.id ? 'bg-blue-50 border-l-4 border-l-blue-600' : ''
                      }`}
                    >
                      {renderListItem(incident, selectedIncidentId === incident.id)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        }
        right={
          selectedIncidentId ? (
            renderDetail(filteredIncidents.find(i => i.id === selectedIncidentId)!)
          ) : (
            <div className="h-full flex items-center justify-center text-gray-400">
              <div className="text-center">
                <Shield className="w-16 h-16 mx-auto mb-4" />
                <p className="text-lg">Select an incident to view details</p>
              </div>
            </div>
          )
        }
      />
    )
  }

  // For portrait mode, use master-detail view with animations
  return (
    <MasterDetailView
      items={filteredIncidents}
      selectedId={selectedIncidentId}
      onSelectItem={(incident) => setSelectedIncidentId(incident.id)}
      renderListItem={renderListItem}
      renderDetail={renderDetail}
      getItemId={(incident) => incident.id}
      listTitle="Incidents"
      detailTitle={(incident) => incident.title}
      emptyState={
        <div className="text-center">
          <Shield className="w-12 h-12 mx-auto mb-3 text-gray-400" />
          <p>No incidents found</p>
          <p className="text-sm text-gray-500 mt-1">Adjust your filters or create a new incident</p>
        </div>
      }
    />
  )
}