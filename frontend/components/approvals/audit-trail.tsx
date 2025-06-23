'use client'

import { useState } from 'react'
import { 
  FileText, 
  User, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Filter,
  Download,
  Search
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { cn } from '@/lib/utils'
import { AuditLogEntry, ChangeRecord } from '@/types/approvals'
import { ActionType } from '@/types/actions'
import { format, formatDistanceToNow, isWithinInterval, startOfDay, endOfDay } from 'date-fns'

interface AuditTrailProps {
  entries: AuditLogEntry[]
  onFilterChange?: (filter: any) => void
  maxHeight?: number
  showExport?: boolean
  className?: string
}

const actionTypeColors: Record<ActionType, { color: string; bgColor: string }> = {
  acknowledge: { color: 'text-blue-600', bgColor: 'bg-blue-50' },
  remediate: { color: 'text-green-600', bgColor: 'bg-green-50' },
  escalate: { color: 'text-orange-600', bgColor: 'bg-orange-50' },
  resolve: { color: 'text-purple-600', bgColor: 'bg-purple-50' },
  close: { color: 'text-gray-600', bgColor: 'bg-gray-50' },
  assign: { color: 'text-cyan-600', bgColor: 'bg-cyan-50' },
  comment: { color: 'text-indigo-600', bgColor: 'bg-indigo-50' },
  custom: { color: 'text-pink-600', bgColor: 'bg-pink-50' }
}

const resultConfig = {
  success: {
    icon: CheckCircle,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    label: 'Success'
  },
  failure: {
    icon: XCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    label: 'Failed'
  },
  partial: {
    icon: AlertCircle,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    label: 'Partial'
  }
}

function AuditLogItem({ entry }: { entry: AuditLogEntry }) {
  const [expanded, setExpanded] = useState(false)
  const actionColors = actionTypeColors[entry.actionType]
  const result = resultConfig[entry.result]
  const ResultIcon = result.icon

  const renderChanges = () => {
    if (!entry.changes || entry.changes.length === 0) return null

    return (
      <div className="mt-3 space-y-2 text-sm">
        <p className="font-medium text-muted-foreground">Changes:</p>
        {entry.changes.map((change, idx) => (
          <div key={idx} className="pl-4 space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                {change.changeType}
              </Badge>
              <span className="font-mono text-xs">{change.field}</span>
            </div>
            {change.changeType === 'update' && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span className="line-through">{JSON.stringify(change.oldValue)}</span>
                <span>→</span>
                <span className="text-foreground">{JSON.stringify(change.newValue)}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    )
  }

  return (
    <div 
      className={cn(
        "p-4 rounded-lg border transition-all cursor-pointer hover:shadow-sm",
        expanded && "shadow-sm"
      )}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start gap-3">
        <div className={cn(
          "p-2 rounded-lg shrink-0",
          actionColors.bgColor
        )}>
          <FileText className={cn("w-4 h-4", actionColors.color)} />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h4 className="text-sm font-medium">{entry.description}</h4>
                <Badge 
                  variant="secondary" 
                  className={cn("text-xs", actionColors.color, actionColors.bgColor)}
                >
                  {entry.actionType}
                </Badge>
              </div>
              <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <User className="w-3 h-3" />
                  {entry.userName}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatDistanceToNow(entry.timestamp, { addSuffix: true })}
                </span>
                {entry.duration && (
                  <span className="font-mono">
                    {entry.duration}ms
                  </span>
                )}
              </div>
            </div>
            
            <div className={cn(
              "p-1.5 rounded shrink-0",
              result.bgColor
            )}>
              <ResultIcon className={cn("w-4 h-4", result.color)} />
            </div>
          </div>

          {expanded && (
            <div className="mt-4 space-y-3 border-t pt-3">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-xs text-muted-foreground">Timestamp</p>
                  <p className="font-mono text-xs">
                    {format(entry.timestamp, 'yyyy-MM-dd HH:mm:ss')}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Action ID</p>
                  <p className="font-mono text-xs">{entry.actionId}</p>
                </div>
                {entry.ipAddress && (
                  <div>
                    <p className="text-xs text-muted-foreground">IP Address</p>
                    <p className="font-mono text-xs">{entry.ipAddress}</p>
                  </div>
                )}
                {entry.resourceId && (
                  <div>
                    <p className="text-xs text-muted-foreground">Resource</p>
                    <p className="font-mono text-xs">
                      {entry.resourceType}: {entry.resourceId}
                    </p>
                  </div>
                )}
              </div>

              {entry.errorMessage && (
                <div className="p-3 rounded-lg bg-red-50 border border-red-200">
                  <p className="text-xs font-medium text-red-800 mb-1">Error</p>
                  <p className="text-xs text-red-700">{entry.errorMessage}</p>
                </div>
              )}

              {renderChanges()}

              {entry.metadata && Object.keys(entry.metadata).length > 0 && (
                <div className="space-y-1">
                  <p className="text-xs font-medium text-muted-foreground">Metadata</p>
                  <pre className="text-xs bg-muted p-2 rounded overflow-x-auto">
                    {JSON.stringify(entry.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export function AuditTrail({
  entries,
  onFilterChange,
  maxHeight = 600,
  showExport = true,
  className
}: AuditTrailProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [actionTypeFilter, setActionTypeFilter] = useState<ActionType | 'all'>('all')
  const [resultFilter, setResultFilter] = useState<'all' | 'success' | 'failure' | 'partial'>('all')
  const [dateFilter, setDateFilter] = useState<'all' | 'today' | 'week' | 'month'>('all')

  const filteredEntries = entries.filter(entry => {
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      if (!entry.description.toLowerCase().includes(query) &&
          !entry.userName.toLowerCase().includes(query) &&
          !entry.actionId.toLowerCase().includes(query)) {
        return false
      }
    }

    // Action type filter
    if (actionTypeFilter !== 'all' && entry.actionType !== actionTypeFilter) {
      return false
    }

    // Result filter
    if (resultFilter !== 'all' && entry.result !== resultFilter) {
      return false
    }

    // Date filter
    if (dateFilter !== 'all') {
      const now = new Date()
      let interval: { start: Date; end: Date }
      
      switch (dateFilter) {
        case 'today':
          interval = { start: startOfDay(now), end: endOfDay(now) }
          break
        case 'week':
          interval = { 
            start: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000), 
            end: now 
          }
          break
        case 'month':
          interval = { 
            start: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000), 
            end: now 
          }
          break
        default:
          return true
      }
      
      if (!isWithinInterval(entry.timestamp, interval)) {
        return false
      }
    }

    return true
  })

  const handleExport = () => {
    const csv = [
      ['Timestamp', 'User', 'Action', 'Description', 'Result', 'Duration (ms)'],
      ...filteredEntries.map(entry => [
        format(entry.timestamp, 'yyyy-MM-dd HH:mm:ss'),
        entry.userName,
        entry.actionType,
        entry.description,
        entry.result,
        entry.duration || ''
      ])
    ].map(row => row.join(',')).join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit-log-${format(new Date(), 'yyyy-MM-dd')}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <Card className={cn("", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">Audit Trail</CardTitle>
            <CardDescription>
              {filteredEntries.length} of {entries.length} entries
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {showExport && (
              <Button
                size="sm"
                variant="outline"
                onClick={handleExport}
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            )}
            <Popover>
              <PopoverTrigger asChild>
                <Button size="sm" variant="outline">
                  <Filter className="w-4 h-4 mr-2" />
                  Filters
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80">
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="action-type">Action Type</Label>
                    <Select 
                      value={actionTypeFilter} 
                      onValueChange={(value) => setActionTypeFilter(value as any)}
                    >
                      <SelectTrigger id="action-type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Actions</SelectItem>
                        <SelectItem value="acknowledge">Acknowledge</SelectItem>
                        <SelectItem value="remediate">Remediate</SelectItem>
                        <SelectItem value="escalate">Escalate</SelectItem>
                        <SelectItem value="resolve">Resolve</SelectItem>
                        <SelectItem value="close">Close</SelectItem>
                        <SelectItem value="assign">Assign</SelectItem>
                        <SelectItem value="comment">Comment</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="result">Result</Label>
                    <Select 
                      value={resultFilter} 
                      onValueChange={(value) => setResultFilter(value as any)}
                    >
                      <SelectTrigger id="result">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Results</SelectItem>
                        <SelectItem value="success">Success</SelectItem>
                        <SelectItem value="failure">Failed</SelectItem>
                        <SelectItem value="partial">Partial</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="date-range">Date Range</Label>
                    <Select 
                      value={dateFilter} 
                      onValueChange={(value) => setDateFilter(value as any)}
                    >
                      <SelectTrigger id="date-range">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Time</SelectItem>
                        <SelectItem value="today">Today</SelectItem>
                        <SelectItem value="week">Last 7 Days</SelectItem>
                        <SelectItem value="month">Last 30 Days</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          </div>
        </div>
        
        <div className="mt-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search by description, user, or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="px-3 pb-3">
        <ScrollArea style={{ height: maxHeight }}>
          <div className="space-y-2 pr-3">
            {filteredEntries.map((entry) => (
              <AuditLogItem key={entry.id} entry={entry} />
            ))}
            
            {filteredEntries.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                <FileText className="w-8 h-8 mx-auto mb-2 opacity-20" />
                <p className="text-sm">No audit entries found</p>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}