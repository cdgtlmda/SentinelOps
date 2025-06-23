'use client'

import React, { useState, useMemo, useCallback } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea
} from 'recharts'
import { format } from 'date-fns'
import { ChartContainer } from './chart-container'
import { IncidentTrendData, ChartFilter } from '@/types/charts'
import { IncidentSeverity } from '@/types/incident'
import { useTheme } from 'next-themes'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Calendar } from 'lucide-react'

interface IncidentTrendsProps {
  data: IncidentTrendData[]
  filter?: ChartFilter
  onFilterChange?: (filter: ChartFilter) => void
  onRefresh?: () => void
  loading?: boolean
  error?: string
}

const SEVERITY_COLORS = {
  critical: '#DC2626',
  high: '#EA580C',
  medium: '#F59E0B',
  low: '#3B82F6',
  total: '#6B7280',
  movingAverage: '#10B981'
}

const TIME_RANGES = [
  { label: 'Last 24 Hours', value: '24h' },
  { label: 'Last 7 Days', value: '7d' },
  { label: 'Last 30 Days', value: '30d' },
  { label: 'Last 90 Days', value: '90d' },
  { label: 'Last Year', value: '1y' }
]

function IncidentTrendsComponent({
  data,
  filter,
  onFilterChange,
  onRefresh,
  loading,
  error
}: IncidentTrendsProps) {
  const { theme } = useTheme()
  const [selectedSeverities, setSelectedSeverities] = useState<IncidentSeverity[]>(['critical', 'high', 'medium', 'low'])
  const [showMovingAverage, setShowMovingAverage] = useState(true)
  const [highlightAnomalies, setHighlightAnomalies] = useState(true)
  const [timeRange, setTimeRange] = useState('7d')

  const anomalyData = useMemo(() => {
    return data.filter(d => d.anomaly).map(d => ({
      x1: d.date,
      x2: d.date,
      y1: 0,
      y2: Math.max(d.total, d.critical + d.high + d.medium + d.low)
    }))
  }, [data])

  const handleSeverityToggle = useCallback((severity: IncidentSeverity) => {
    setSelectedSeverities(prev => 
      prev.includes(severity) 
        ? prev.filter(s => s !== severity)
        : [...prev, severity]
    )
  }, [])

  const handleTimeRangeChange = useCallback((value: string) => {
    setTimeRange(value)
    if (onFilterChange) {
      // Convert time range to actual dates
      const end = new Date()
      let start = new Date()
      
      switch (value) {
        case '24h':
          start.setHours(start.getHours() - 24)
          break
        case '7d':
          start.setDate(start.getDate() - 7)
          break
        case '30d':
          start.setDate(start.getDate() - 30)
          break
        case '90d':
          start.setDate(start.getDate() - 90)
          break
        case '1y':
          start.setFullYear(start.getFullYear() - 1)
          break
      }
      
      onFilterChange({
        ...filter,
        dateRange: {
          start,
          end,
          granularity: value === '24h' ? 'hour' : value === '7d' ? 'day' : 'week'
        }
      })
    }
  }, [onFilterChange, filter])

  const renderDataTable = useCallback(() => (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b">
          <th className="text-left p-2">Date</th>
          <th className="text-right p-2">Total</th>
          <th className="text-right p-2">Critical</th>
          <th className="text-right p-2">High</th>
          <th className="text-right p-2">Medium</th>
          <th className="text-right p-2">Low</th>
          {showMovingAverage && <th className="text-right p-2">Moving Avg</th>}
        </tr>
      </thead>
      <tbody>
        {data.map((row, index) => (
          <tr key={index} className="border-b hover:bg-muted/50">
            <td className="p-2">{row.date}</td>
            <td className="text-right p-2">{row.total}</td>
            <td className="text-right p-2 text-red-600">{row.critical}</td>
            <td className="text-right p-2 text-orange-600">{row.high}</td>
            <td className="text-right p-2 text-yellow-600">{row.medium}</td>
            <td className="text-right p-2 text-blue-600">{row.low}</td>
            {showMovingAverage && (
              <td className="text-right p-2 text-green-600">
                {row.movingAverage?.toFixed(1) || '-'}
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  ), [data, showMovingAverage])

  const handleExport = useCallback((options: any) => {
    // Implementation would export the chart/data
    console.log('Exporting with options:', options)
  }, [])

  return (
    <ChartContainer
      title="Incident Trends"
      description="Track incident patterns and anomalies over time"
      onRefresh={onRefresh}
      onExport={handleExport}
      renderDataTable={renderDataTable}
      loading={loading}
      error={error}
    >
      <div className="space-y-4">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="space-y-2">
            <Label>Time Range</Label>
            <Select value={timeRange} onValueChange={handleTimeRangeChange}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TIME_RANGES.map(range => (
                  <SelectItem key={range.value} value={range.value}>
                    {range.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Severity Levels</Label>
            <div className="flex gap-2">
              {(['critical', 'high', 'medium', 'low'] as IncidentSeverity[]).map(severity => (
                <Button
                  key={severity}
                  variant={selectedSeverities.includes(severity) ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleSeverityToggle(severity)}
                  className="capitalize"
                  style={{
                    backgroundColor: selectedSeverities.includes(severity) 
                      ? SEVERITY_COLORS[severity] 
                      : undefined,
                    borderColor: SEVERITY_COLORS[severity],
                    color: selectedSeverities.includes(severity) ? 'white' : SEVERITY_COLORS[severity]
                  }}
                >
                  {severity}
                </Button>
              ))}
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              variant={showMovingAverage ? 'default' : 'outline'}
              size="sm"
              onClick={() => setShowMovingAverage(!showMovingAverage)}
            >
              Moving Average
            </Button>
            <Button
              variant={highlightAnomalies ? 'default' : 'outline'}
              size="sm"
              onClick={() => setHighlightAnomalies(!highlightAnomalies)}
            >
              Anomalies
            </Button>
          </div>
        </div>

        <div className="h-[300px] sm:h-[350px] md:h-[400px]">
          <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke={theme === 'dark' ? '#374151' : '#E5E7EB'}
            />
            <XAxis 
              dataKey="date" 
              stroke={theme === 'dark' ? '#9CA3AF' : '#6B7280'}
              tick={{ fontSize: 12 }}
            />
            <YAxis 
              stroke={theme === 'dark' ? '#9CA3AF' : '#6B7280'}
              tick={{ fontSize: 12 }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: theme === 'dark' ? '#1F2937' : '#FFFFFF',
                border: `1px solid ${theme === 'dark' ? '#374151' : '#E5E7EB'}`,
                borderRadius: '6px'
              }}
              labelStyle={{ color: theme === 'dark' ? '#F3F4F6' : '#111827' }}
            />
            <Legend 
              wrapperStyle={{ fontSize: '12px' }}
              iconType="line"
            />
            
            {highlightAnomalies && anomalyData.map((anomaly, index) => (
              <ReferenceArea
                key={index}
                x1={anomaly.x1}
                x2={anomaly.x2}
                fill="#DC2626"
                fillOpacity={0.1}
                stroke="#DC2626"
                strokeDasharray="3 3"
              />
            ))}

            {selectedSeverities.includes('critical') && (
              <Line
                type="monotone"
                dataKey="critical"
                stroke={SEVERITY_COLORS.critical}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            )}
            {selectedSeverities.includes('high') && (
              <Line
                type="monotone"
                dataKey="high"
                stroke={SEVERITY_COLORS.high}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            )}
            {selectedSeverities.includes('medium') && (
              <Line
                type="monotone"
                dataKey="medium"
                stroke={SEVERITY_COLORS.medium}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            )}
            {selectedSeverities.includes('low') && (
              <Line
                type="monotone"
                dataKey="low"
                stroke={SEVERITY_COLORS.low}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            )}
            
            <Line
              type="monotone"
              dataKey="total"
              stroke={SEVERITY_COLORS.total}
              strokeWidth={3}
              strokeDasharray="5 5"
              dot={false}
            />
            
            {showMovingAverage && (
              <Line
                type="monotone"
                dataKey="movingAverage"
                stroke={SEVERITY_COLORS.movingAverage}
                strokeWidth={2}
                strokeDasharray="3 3"
                dot={false}
              />
            )}
          </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </ChartContainer>
  )
}

// Export memoized component with custom comparison
export const IncidentTrends = React.memo(IncidentTrendsComponent, (prevProps, nextProps) => {
  return (
    prevProps.data === nextProps.data &&
    prevProps.filter === nextProps.filter &&
    prevProps.loading === nextProps.loading &&
    prevProps.error === nextProps.error &&
    prevProps.onFilterChange === nextProps.onFilterChange &&
    prevProps.onRefresh === nextProps.onRefresh
  )
})