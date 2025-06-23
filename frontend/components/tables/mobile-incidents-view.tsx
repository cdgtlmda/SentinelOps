'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Filter, SortAsc, SortDesc } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { MobileIncidentCard } from '@/components/mobile/mobile-incident-card'
import { PullToRefresh } from '@/components/mobile/pull-to-refresh'
import type { Incident } from '@/types/incident'

interface MobileIncidentsViewProps {
  incidents: Incident[]
  onAcknowledge?: (id: string) => void
  onEscalate?: (id: string) => void
  onResolve?: (id: string) => void
  onChat?: (id: string) => void
  onRefresh?: () => Promise<void>
}

type SortField = 'createdAt' | 'severity' | 'status'
type SortOrder = 'asc' | 'desc'

export function MobileIncidentsView({
  incidents,
  onAcknowledge,
  onEscalate,
  onResolve,
  onChat,
  onRefresh
}: MobileIncidentsViewProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [sortField, setSortField] = useState<SortField>('createdAt')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')

  // Filter and sort incidents
  const filteredIncidents = incidents
    .filter(incident => {
      const matchesSearch = 
        incident.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        incident.description.toLowerCase().includes(searchQuery.toLowerCase())
      
      const matchesSeverity = selectedSeverity === 'all' || incident.severity === selectedSeverity
      const matchesStatus = selectedStatus === 'all' || incident.status === selectedStatus
      
      return matchesSearch && matchesSeverity && matchesStatus
    })
    .sort((a, b) => {
      let comparison = 0
      
      switch (sortField) {
        case 'createdAt':
          comparison = new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
          break
        case 'severity':
          const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 }
          comparison = severityOrder[a.severity] - severityOrder[b.severity]
          break
        case 'status':
          const statusOrder = { open: 0, investigating: 1, acknowledged: 2, resolved: 3 }
          comparison = statusOrder[a.status] - statusOrder[b.status]
          break
      }
      
      return sortOrder === 'asc' ? comparison : -comparison
    })

  const activeFiltersCount = 
    (selectedSeverity !== 'all' ? 1 : 0) + 
    (selectedStatus !== 'all' ? 1 : 0)

  const handleRefresh = async () => {
    if (onRefresh) {
      await onRefresh()
    } else {
      // Default refresh behavior
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Search and Filter Bar */}
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border p-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search incidents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          
          <Button
            variant="outline"
            size="icon"
            onClick={() => setIsFilterOpen(true)}
            className="relative"
          >
            <Filter className="h-4 w-4" />
            {activeFiltersCount > 0 && (
              <Badge 
                variant="destructive" 
                className="absolute -top-1 -right-1 h-5 w-5 p-0 flex items-center justify-center text-[10px]"
              >
                {activeFiltersCount}
              </Badge>
            )}
          </Button>
        </div>

        {/* Quick Stats */}
        <div className="flex gap-2 mt-3 text-xs">
          <Badge variant="secondary">
            Total: {incidents.length}
          </Badge>
          <Badge variant="destructive">
            Critical: {incidents.filter(i => i.severity === 'critical').length}
          </Badge>
          <Badge variant="outline">
            Open: {incidents.filter(i => i.status === 'open').length}
          </Badge>
        </div>
      </div>

      {/* Incidents List */}
      <PullToRefresh onRefresh={handleRefresh} className="flex-1">
        <div className="p-4 space-y-3">
          <AnimatePresence mode="popLayout">
            {filteredIncidents.length > 0 ? (
              filteredIncidents.map((incident) => (
                <motion.div
                  key={incident.id}
                  layout
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  <MobileIncidentCard
                    incident={incident}
                    onAcknowledge={onAcknowledge}
                    onEscalate={onEscalate}
                    onResolve={onResolve}
                    onChat={onChat}
                  />
                </motion.div>
              ))
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-12"
              >
                <p className="text-muted-foreground">No incidents found</p>
                {(searchQuery || activeFiltersCount > 0) && (
                  <Button
                    variant="link"
                    onClick={() => {
                      setSearchQuery('')
                      setSelectedSeverity('all')
                      setSelectedStatus('all')
                    }}
                    className="mt-2"
                  >
                    Clear filters
                  </Button>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </PullToRefresh>

      {/* Filter Sheet */}
      <Sheet open={isFilterOpen} onOpenChange={setIsFilterOpen}>
        <SheetContent side="bottom" className="h-[400px]">
          <SheetHeader>
            <SheetTitle>Filter & Sort</SheetTitle>
          </SheetHeader>
          
          <div className="space-y-4 mt-6">
            {/* Severity Filter */}
            <div>
              <label className="text-sm font-medium mb-2 block">Severity</label>
              <Select value={selectedSeverity} onValueChange={setSelectedSeverity}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Severities</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="text-sm font-medium mb-2 block">Status</label>
              <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="investigating">Investigating</SelectItem>
                  <SelectItem value="acknowledged">Acknowledged</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Sort Options */}
            <div>
              <label className="text-sm font-medium mb-2 block">Sort By</label>
              <div className="flex gap-2">
                <Select value={sortField} onValueChange={(value) => setSortField(value as SortField)}>
                  <SelectTrigger className="flex-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="createdAt">Date</SelectItem>
                    <SelectItem value="severity">Severity</SelectItem>
                    <SelectItem value="status">Status</SelectItem>
                  </SelectContent>
                </Select>
                
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                >
                  {sortOrder === 'asc' ? (
                    <SortAsc className="h-4 w-4" />
                  ) : (
                    <SortDesc className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 pt-4">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => {
                  setSelectedSeverity('all')
                  setSelectedStatus('all')
                  setSortField('createdAt')
                  setSortOrder('desc')
                }}
              >
                Reset
              </Button>
              <Button
                className="flex-1"
                onClick={() => setIsFilterOpen(false)}
              >
                Apply
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  )
}

export default MobileIncidentsView