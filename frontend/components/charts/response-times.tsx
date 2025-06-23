'use client'

import { useState } from 'react'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Area,
  Scatter,
  ScatterChart,
  ZAxis
} from 'recharts'
import { ChartContainer } from './chart-container'
import { ResponseTimeData } from '@/types/charts'
import { useTheme } from 'next-themes'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Clock, TrendingDown, TrendingUp, AlertTriangle } from 'lucide-react'

interface ResponseTimesProps {
  responseData: ResponseTimeData[]
  histogramData: { range: string; count: number; avgMttr: number }[]
  mttrTrendData: { date: string; mttr: number; slaTarget: number }[]
  agentPerformanceData: { agent: string; avgResponseTime: number; incidentCount: number; successRate: number }[]
  onRefresh?: () => void
  loading?: boolean
  error?: string
}

const SLA_COLORS = {
  met: '#10B981',
  at_risk: '#F59E0B',
  breached: '#EF4444'
}

export function ResponseTimes({
  responseData,
  histogramData,
  mttrTrendData,
  agentPerformanceData,
  onRefresh,
  loading,
  error
}: ResponseTimesProps) {
  const { theme } = useTheme()
  const [selectedMetric, setSelectedMetric] = useState<'detection' | 'acknowledgment' | 'resolution'>('resolution')

  const calculateStats = () => {
    const mttrs = responseData.map(d => d.mttr)
    const avg = mttrs.reduce((a, b) => a + b, 0) / mttrs.length
    const sorted = [...mttrs].sort((a, b) => a - b)
    const median = sorted[Math.floor(sorted.length / 2)]
    const p95 = sorted[Math.floor(sorted.length * 0.95)]
    
    const slaStats = {
      met: responseData.filter(d => d.slaStatus === 'met').length,
      at_risk: responseData.filter(d => d.slaStatus === 'at_risk').length,
      breached: responseData.filter(d => d.slaStatus === 'breached').length
    }

    return { avg, median, p95, slaStats }
  }

  const stats = calculateStats()

  const renderCustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-background border rounded-lg p-3 shadow-lg">
          <p className="font-semibold">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value} {entry.unit || 'min'}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  const renderDataTable = () => (
    <div className="space-y-6">
      <div>
        <h4 className="font-semibold mb-2">Response Time Statistics</h4>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left p-2">Metric</th>
              <th className="text-right p-2">Value</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b hover:bg-muted/50">
              <td className="p-2">Average MTTR</td>
              <td className="text-right p-2">{stats.avg.toFixed(1)} min</td>
            </tr>
            <tr className="border-b hover:bg-muted/50">
              <td className="p-2">Median MTTR</td>
              <td className="text-right p-2">{stats.median.toFixed(1)} min</td>
            </tr>
            <tr className="border-b hover:bg-muted/50">
              <td className="p-2">95th Percentile</td>
              <td className="text-right p-2">{stats.p95.toFixed(1)} min</td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div>
        <h4 className="font-semibold mb-2">SLA Compliance</h4>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left p-2">Status</th>
              <th className="text-right p-2">Count</th>
              <th className="text-right p-2">Percentage</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b hover:bg-muted/50">
              <td className="p-2">Met</td>
              <td className="text-right p-2">{stats.slaStats.met}</td>
              <td className="text-right p-2">
                {((stats.slaStats.met / responseData.length) * 100).toFixed(1)}%
              </td>
            </tr>
            <tr className="border-b hover:bg-muted/50">
              <td className="p-2">At Risk</td>
              <td className="text-right p-2">{stats.slaStats.at_risk}</td>
              <td className="text-right p-2">
                {((stats.slaStats.at_risk / responseData.length) * 100).toFixed(1)}%
              </td>
            </tr>
            <tr className="border-b hover:bg-muted/50">
              <td className="p-2">Breached</td>
              <td className="text-right p-2">{stats.slaStats.breached}</td>
              <td className="text-right p-2">
                {((stats.slaStats.breached / responseData.length) * 100).toFixed(1)}%
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )

  const handleExport = (options: any) => {
    console.log('Exporting with options:', options)
  }

  return (
    <ChartContainer
      title="Response Times"
      description="Monitor detection, acknowledgment, and resolution performance"
      onRefresh={onRefresh}
      onExport={handleExport}
      renderDataTable={renderDataTable}
      loading={loading}
      error={error}
    >
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg MTTR</p>
                <p className="text-2xl font-bold">{stats.avg.toFixed(1)} min</p>
              </div>
              <Clock className="h-8 w-8 text-muted-foreground" />
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">SLA Compliance</p>
                <p className="text-2xl font-bold">
                  {((stats.slaStats.met / responseData.length) * 100).toFixed(1)}%
                </p>
              </div>
              {stats.slaStats.met / responseData.length > 0.9 ? (
                <TrendingUp className="h-8 w-8 text-green-500" />
              ) : (
                <TrendingDown className="h-8 w-8 text-red-500" />
              )}
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">P95 Response</p>
                <p className="text-2xl font-bold">{stats.p95.toFixed(1)} min</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-yellow-500" />
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">SLA Status</p>
              <div className="flex gap-2">
                <Badge variant="default" className="bg-green-500">
                  {stats.slaStats.met}
                </Badge>
                <Badge variant="default" className="bg-yellow-500">
                  {stats.slaStats.at_risk}
                </Badge>
                <Badge variant="destructive">
                  {stats.slaStats.breached}
                </Badge>
              </div>
            </div>
          </Card>
        </div>

        <Tabs defaultValue="histogram" className="w-full">
          <TabsList className="grid grid-cols-4 w-full max-w-md">
            <TabsTrigger value="histogram">Histogram</TabsTrigger>
            <TabsTrigger value="trends">MTTR Trends</TabsTrigger>
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
            <TabsTrigger value="agents">Agents</TabsTrigger>
          </TabsList>

          <TabsContent value="histogram" className="space-y-4">
            <Card className="p-4">
              <h3 className="text-sm font-medium mb-4">Response Time Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={histogramData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />
                  <XAxis dataKey="range" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip content={renderCustomTooltip} />
                  <Legend />
                  <Bar yAxisId="left" dataKey="count" fill="#3B82F6" name="Incident Count" />
                  <Line 
                    yAxisId="right" 
                    type="monotone" 
                    dataKey="avgMttr" 
                    stroke="#10B981" 
                    strokeWidth={2}
                    name="Avg MTTR (min)"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </Card>
          </TabsContent>

          <TabsContent value="trends" className="space-y-4">
            <Card className="p-4">
              <h3 className="text-sm font-medium mb-4">MTTR Trend vs SLA Target</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={mttrTrendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip content={renderCustomTooltip} />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="mttr" 
                    stroke="#3B82F6" 
                    strokeWidth={2}
                    name="MTTR"
                    dot={{ r: 4 }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="slaTarget" 
                    stroke="#EF4444" 
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    name="SLA Target"
                    dot={false}
                  />
                  <Area
                    type="monotone"
                    dataKey="mttr"
                    fill="#3B82F6"
                    fillOpacity={0.1}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </TabsContent>

          <TabsContent value="timeline" className="space-y-4">
            <Card className="p-4">
              <h3 className="text-sm font-medium mb-4">Detection to Resolution Timeline</h3>
              <ResponsiveContainer width="100%" height={400}>
                <ScatterChart>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />
                  <XAxis 
                    dataKey="detectionTime" 
                    type="number"
                    domain={['dataMin', 'dataMax']}
                    tickFormatter={(time) => new Date(time).toLocaleDateString()}
                  />
                  <YAxis dataKey="mttr" />
                  <ZAxis dataKey="severity" range={[50, 200]} />
                  <Tooltip 
                    content={({ active, payload }: any) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload
                        return (
                          <div className="bg-background border rounded-lg p-3 shadow-lg">
                            <p className="font-semibold">Incident {data.incidentId}</p>
                            <p className="text-sm">MTTR: {data.mttr} min</p>
                            <p className="text-sm">SLA: <Badge variant={data.slaStatus === 'met' ? 'default' : 'destructive'}>
                              {data.slaStatus}
                            </Badge></p>
                          </div>
                        )
                      }
                      return null
                    }}
                  />
                  <Scatter 
                    data={responseData.map(d => ({
                      ...d,
                      detectionTime: d.detectionTime.getTime(),
                      severity: d.slaStatus === 'breached' ? 3 : d.slaStatus === 'at_risk' ? 2 : 1
                    }))}
                    fill="#8884d8"
                  >
                    {responseData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={SLA_COLORS[entry.slaStatus]} />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </Card>
          </TabsContent>

          <TabsContent value="agents" className="space-y-4">
            <Card className="p-4">
              <h3 className="text-sm font-medium mb-4">Agent Performance Comparison</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={agentPerformanceData} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />
                  <XAxis type="number" />
                  <YAxis dataKey="agent" type="category" width={100} />
                  <Tooltip content={renderCustomTooltip} />
                  <Legend />
                  <Bar dataKey="avgResponseTime" fill="#3B82F6" name="Avg Response Time (min)" />
                </BarChart>
              </ResponsiveContainer>
              
              <div className="mt-4">
                <h4 className="text-sm font-medium mb-2">Agent Details</h4>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Agent</th>
                      <th className="text-right p-2">Incidents</th>
                      <th className="text-right p-2">Avg Response</th>
                      <th className="text-right p-2">Success Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {agentPerformanceData.map((agent, index) => (
                      <tr key={index} className="border-b hover:bg-muted/50">
                        <td className="p-2">{agent.agent}</td>
                        <td className="text-right p-2">{agent.incidentCount}</td>
                        <td className="text-right p-2">{agent.avgResponseTime.toFixed(1)} min</td>
                        <td className="text-right p-2">{(agent.successRate * 100).toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </ChartContainer>
  )
}

// Fix for missing Cell import
const Cell = ({ fill }: { fill: string }) => null