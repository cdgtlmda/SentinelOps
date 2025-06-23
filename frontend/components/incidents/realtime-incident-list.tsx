'use client'

import React, { useState, useMemo, useCallback, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { Incident, IncidentFilter, IncidentSort, IncidentSeverity, IncidentStatus } from '@/types/incident'
import { IncidentCard } from './incident-card'
import { SeverityBadge } from './severity-badge'
import { StatusBadge } from './status-badge'
import { useIncidentUpdates } from '@/hooks/use-websocket'
import { IncidentUpdate } from '@/types/websocket'
import { 
  Grid3X3, 
  List, 
  Filter, 
  ArrowUpDown,
  Search,
  X,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  Wifi
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/hooks/use-toast'

interface RealtimeIncidentListProps {
  initialIncidents: Incident[]
  onAcknowledge?: (id: string) => void
  onInvestigate?: (id: string) => void
  onRemediate?: (id: string) => void
  onViewDetails?: (id: string) => void
  selectedIds?: Set<string>
  onToggleSelect?: (id: string) => void
  onActionComplete?: (action: any, result: any) => void
  className?: string
}

export function RealtimeIncidentList({
  initialIncidents,
  onAcknowledge,
  onInvestigate,
  onRemediate,
  onViewDetails,
  selectedIds = new Set(),
  onToggleSelect,
  onActionComplete,
  className
}: RealtimeIncidentListProps) {
  const [incidents, setIncidents] = useState<Incident[]>(initialIncidents)
  const [view, setView] = useState<'grid' | 'list'>('grid')
  const [searchTerm, setSearchTerm] = useState('')
  const [filters, setFilters] = useState<IncidentFilter>({})
  const [sort, setSort] = useState<IncidentSort>({
    field: 'createdAt',
    order: 'desc'
  })
  const [currentPage, setCurrentPage] = useState(1)
  const [showFilters, setShowFilters] = useState(false)
  const [recentUpdates, setRecentUpdates] = useState<Set<string>>(new Set())
  const pageSize = 12
  const { toast } = useToast()

  // Handle real-time incident updates
  const { isConnected } = useIncidentUpdates((update: IncidentUpdate) => {
    setIncidents(prev => {
      switch (update.type) {
        case 'created':
          // Add new incident at the beginning
          toast({
            title: 'New Incident',
            description: `${update.data.title} has been created`,
            variant: 'default'
          })
          return [update.data, ...prev]
        
        case 'updated':
          // Update existing incident
          const updatedIncidents = prev.map(incident => 
            incident.id === update.incidentId ? { ...incident, ...update.data } : incident
          )
          // Mark as recently updated
          setRecentUpdates(prev => new Set([...prev, update.incidentId]))
          setTimeout(() => {
            setRecentUpdates(prev => {
              const newSet = new Set(prev)
              newSet.delete(update.incidentId)
              return newSet
            })
          }, 5000)
          return updatedIncidents
        
        case 'resolved':
          // Update status to resolved
          toast({
            title: 'Incident Resolved',
            description: `Incident ${update.incidentId} has been resolved`,
            variant: 'success'
          })
          return prev.map(incident =>
            incident.id === update.incidentId 
              ? { ...incident, status: 'resolved' as IncidentStatus, ...update.data } 
              : incident
          )
        
        case 'escalated':
          // Update severity or assignee
          toast({
            title: 'Incident Escalated',
            description: `Incident ${update.incidentId} has been escalated`,
            variant: 'destructive'
          })
          return prev.map(incident =>
            incident.id === update.incidentId 
              ? { ...incident, ...update.data } 
              : incident
          )
        
        default:
          return prev
      }
    })
  })

  // Update incidents when initialIncidents changes
  useEffect(() => {
    setIncidents(initialIncidents)
  }, [initialIncidents])

  // Filter and sort incidents
  const filteredAndSortedIncidents = useMemo(() => {
    let filtered = [...incidents]

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(incident =>
        incident.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        incident.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        incident.id.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Apply severity filter
    if (filters.severities?.length) {
      filtered = filtered.filter(incident =>
        filters.severities!.includes(incident.severity)
      )
    }

    // Apply status filter
    if (filters.statuses?.length) {
      filtered = filtered.filter(incident =>
        filters.statuses!.includes(incident.status)
      )
    }

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0
      
      switch (sort.field) {
        case 'createdAt':
          comparison = a.createdAt.getTime() - b.createdAt.getTime()
          break
        case 'updatedAt':
          comparison = a.updatedAt.getTime() - b.updatedAt.getTime()
          break
        case 'severity':
          const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 }
          comparison = severityOrder[a.severity] - severityOrder[b.severity]
          break
        case 'status':
          const statusOrder = { new: 0, acknowledged: 1, investigating: 2, remediated: 3, resolved: 4, closed: 5 }
          comparison = statusOrder[a.status] - statusOrder[b.status]
          break
        case 'title':
          comparison = a.title.localeCompare(b.title)
          break
      }

      return sort.order === 'asc' ? comparison : -comparison
    })

    return filtered
  }, [incidents, searchTerm, filters, sort])

  // Pagination
  const totalPages = Math.ceil(filteredAndSortedIncidents.length / pageSize)
  const paginatedIncidents = filteredAndSortedIncidents.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  )

  const handleFilterChange = useCallback((key: keyof IncidentFilter, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    setCurrentPage(1)
  }, [])

  const handleSortChange = useCallback((field: IncidentSort['field']) => {
    setSort(prev => ({
      field,
      order: prev.field === field && prev.order === 'asc' ? 'desc' : 'asc'
    }))
  }, [])

  const clearFilters = useCallback(() => {
    setFilters({})
    setSearchTerm('')
    setCurrentPage(1)
  }, [])

  const activeFilterCount = Object.values(filters).filter(v => v && (Array.isArray(v) ? v.length > 0 : true)).length

  const EmptyState = () => (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <AlertCircle className="h-12 w-12 text-gray-400 mb-4" />
      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">
        No incidents found
      </h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        {searchTerm || activeFilterCount > 0
          ? 'Try adjusting your filters or search term'
          : 'All clear! No incidents to display.'}
      </p>
      {(searchTerm || activeFilterCount > 0) && (
        <button
          onClick={clearFilters}
          className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
        >
          Clear filters
        </button>
      )}
    </div>
  )

  return (
    <div className={cn('space-y-4', className)}>
      {/* Controls */}
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800 p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" aria-hidden="true" />
              <input
                type="text"
                placeholder="Search incidents..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value)
                  setCurrentPage(1)
                }}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                aria-label="Search incidents"
              />
            </div>
          </div>

          {/* Connection Status */}
          <div className="flex items-center gap-2">
            <Badge 
              variant={isConnected ? 'default' : 'secondary'}
              className={cn(
                'gap-1.5',
                isConnected ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' : ''
              )}
            >
              <Wifi className={cn('h-3 w-3', !isConnected && 'opacity-50')} />
              {isConnected ? 'Live' : 'Offline'}
            </Badge>
          </div>

          {/* View Toggle */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setView('grid')}
              className={cn(
                'p-2 rounded-md transition-colors',
                view === 'grid' 
                  ? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100' 
                  : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              )}
              aria-label="Grid view"
              aria-pressed={view === 'grid'}
            >
              <Grid3X3 className="h-4 w-4" aria-hidden="true" />
            </button>
            <button
              onClick={() => setView('list')}
              className={cn(
                'p-2 rounded-md transition-colors',
                view === 'list' 
                  ? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100' 
                  : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              )}
              aria-label="List view"
              aria-pressed={view === 'list'}
            >
              <List className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-md border transition-colors',
              showFilters || activeFilterCount > 0
                ? 'bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                : 'border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'
            )}
            aria-label="Toggle filters"
            aria-expanded={showFilters}
            aria-controls="incident-filters"
          >
            <Filter className="h-4 w-4" aria-hidden="true" />
            Filters
            {activeFilterCount > 0 && (
              <span className="bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-1.5 py-0.5 rounded-full text-xs" aria-label={`${activeFilterCount} active filters`}>
                {activeFilterCount}
              </span>
            )}
          </button>

          {/* Sort Dropdown */}
          <select
            value={`${sort.field}-${sort.order}`}
            onChange={(e) => {
              const [field, order] = e.target.value.split('-') as [IncidentSort['field'], 'asc' | 'desc']
              setSort({ field, order })
            }}
            className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            aria-label="Sort incidents"
          >
            <option value="createdAt-desc">Newest First</option>
            <option value="createdAt-asc">Oldest First</option>
            <option value="updatedAt-desc">Recently Updated</option>
            <option value="severity-asc">Severity (High to Low)</option>
            <option value="severity-desc">Severity (Low to High)</option>
            <option value="status-asc">Status</option>
            <option value="title-asc">Title (A-Z)</option>
            <option value="title-desc">Title (Z-A)</option>
          </select>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-800 space-y-4" id="incident-filters">
            {/* Severity Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Severity
              </label>
              <div className="flex flex-wrap gap-2">
                {(['critical', 'high', 'medium', 'low'] as IncidentSeverity[]).map((severity) => (
                  <button
                    key={severity}
                    onClick={() => {
                      const current = filters.severities || []
                      const updated = current.includes(severity)
                        ? current.filter(s => s !== severity)
                        : [...current, severity]
                      handleFilterChange('severities', updated.length ? updated : undefined)
                    }}
                    className={cn(
                      'transition-all',
                      filters.severities?.includes(severity) && 'ring-2 ring-offset-2 ring-blue-500'
                    )}
                  >
                    <SeverityBadge severity={severity} size="sm" />
                  </button>
                ))}
              </div>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Status
              </label>
              <div className="flex flex-wrap gap-2">
                {(['new', 'acknowledged', 'investigating', 'remediated', 'resolved', 'closed'] as IncidentStatus[]).map((status) => (
                  <button
                    key={status}
                    onClick={() => {
                      const current = filters.statuses || []
                      const updated = current.includes(status)
                        ? current.filter(s => s !== status)
                        : [...current, status]
                      handleFilterChange('statuses', updated.length ? updated : undefined)
                    }}
                    className={cn(
                      'transition-all',
                      filters.statuses?.includes(status) && 'ring-2 ring-offset-2 ring-blue-500'
                    )}
                  >
                    <StatusBadge status={status} size="sm" />
                  </button>
                ))}
              </div>
            </div>

            {/* Clear Filters */}
            {activeFilterCount > 0 && (
              <button
                onClick={clearFilters}
                className="flex items-center gap-1 text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
              >
                <X className="h-4 w-4" />
                Clear all filters
              </button>
            )}
          </div>
        )}
      </div>

      {/* Results count */}
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Showing {paginatedIncidents.length} of {filteredAndSortedIncidents.length} incidents
      </div>

      {/* Incident Grid/List */}
      {paginatedIncidents.length === 0 ? (
        <EmptyState />
      ) : (
        <div className={cn(
          view === 'grid' 
            ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4' 
            : 'space-y-4'
        )}>
          {paginatedIncidents.map((incident) => (
            <div 
              key={incident.id}
              className={cn(
                'transition-all duration-500',
                recentUpdates.has(incident.id) && 'ring-2 ring-blue-500 ring-opacity-50 animate-pulse'
              )}
            >
              <IncidentCard
                incident={incident}
                view={view}
                onAcknowledge={onAcknowledge}
                onInvestigate={onInvestigate}
                onRemediate={onRemediate}
                onViewDetails={onViewDetails}
                isSelected={selectedIds.has(incident.id)}
                onToggleSelect={onToggleSelect}
                onActionComplete={onActionComplete}
              />
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <button
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
            className={cn(
              'p-2 rounded-md transition-colors',
              currentPage === 1
                ? 'text-gray-400 cursor-not-allowed'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
            )}
            aria-label="Previous page"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>

          <div className="flex items-center gap-1">
            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter(page => {
                // Show first, last, current, and adjacent pages
                return page === 1 || 
                       page === totalPages || 
                       Math.abs(page - currentPage) <= 1
              })
              .map((page, index, array) => (
                <React.Fragment key={page}>
                  {index > 0 && array[index - 1] !== page - 1 && (
                    <span className="px-2 text-gray-400">...</span>
                  )}
                  <button
                    onClick={() => setCurrentPage(page)}
                    className={cn(
                      'px-3 py-1 rounded-md text-sm transition-colors',
                      page === currentPage
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                    )}
                    aria-label={`Go to page ${page}`}
                    aria-current={page === currentPage ? 'page' : undefined}
                  >
                    {page}
                  </button>
                </React.Fragment>
              ))}
          </div>

          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
            className={cn(
              'p-2 rounded-md transition-colors',
              currentPage === totalPages
                ? 'text-gray-400 cursor-not-allowed'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
            )}
            aria-label="Next page"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  )
}