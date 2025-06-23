'use client'

import { useState } from 'react'
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  PieChart,
  Pie,
  Cell,
  Sankey
} from 'recharts'
import { ChartContainer } from './chart-container'
import { ResourceUsageData } from '@/types/charts'
import { useTheme } from 'next-themes'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { 
  Cpu, 
  HardDrive, 
  Activity, 
  DollarSign,
  TrendingUp,
  TrendingDown,
  AlertTriangle
} from 'lucide-react'

interface ResourceUsageProps {
  usageData: ResourceUsageData[]
  costBreakdown: { category: string; amount: number; percentage: number }[]
  apiMetrics: { endpoint: string; calls: number; avgLatency: number; errorRate: number }[]
  capacityData: { resource: string; used: number; total: number; projected: number }[]
  serviceUsage?: { service: string; cpu: number; memory: number; cost: number }[]
  onRefresh?: () => void
  loading?: boolean
  error?: string
}

const RESOURCE_COLORS = {
  cpu: '#3B82F6',
  memory: '#10B981',
  storage: '#F59E0B',
  network: '#8B5CF6',
  cost: '#EF4444',
  api: '#EC4899'
}

export function ResourceUsage({
  usageData,
  costBreakdown,
  apiMetrics,
  capacityData,
  serviceUsage,
  onRefresh,
  loading,
  error
}: ResourceUsageProps) {
  const { theme } = useTheme()
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h')
  const [selectedResources, setSelectedResources] = useState(['cpu', 'memory'])

  const latestData = usageData[usageData.length - 1] || {}
  const previousData = usageData[usageData.length - 2] || {}
  
  const calculateChange = (current: number, previous: number) => {
    if (!previous) return 0
    return ((current - previous) / previous) * 100
  }

  const cpuChange = calculateChange(latestData.cpu || 0, previousData.cpu || 0)
  const costChange = calculateChange(latestData.cost || 0, previousData.cost || 0)
  const totalCost = usageData.reduce((sum, d) => sum + (d.cost || 0), 0)

  const renderCustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-background border rounded-lg p-3 shadow-lg">
          <p className="font-semibold">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
              {entry.name === 'Cost' ? ` $${entry.value.toFixed(2)}` : 
               entry.name.includes('CPU') || entry.name.includes('Memory') ? '%' : ''}
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
        <h4 className="font-semibold mb-2">Resource Summary</h4>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left p-2">Resource</th>
              <th className="text-right p-2">Current</th>
              <th className="text-right p-2">Average</th>
              <th className="text-right p-2">Peak</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b hover:bg-muted/50">
              <td className="p-2">CPU</td>
              <td className="text-right p-2">{latestData.cpu?.toFixed(1)}%</td>
              <td className="text-right p-2">
                {(usageData.reduce((sum, d) => sum + d.cpu, 0) / usageData.length).toFixed(1)}%
              </td>
              <td className="text-right p-2">{Math.max(...usageData.map(d => d.cpu)).toFixed(1)}%</td>
            </tr>
            <tr className="border-b hover:bg-muted/50">
              <td className="p-2">Memory</td>
              <td className="text-right p-2">{latestData.memory?.toFixed(1)}%</td>
              <td className="text-right p-2">
                {(usageData.reduce((sum, d) => sum + d.memory, 0) / usageData.length).toFixed(1)}%
              </td>
              <td className="text-right p-2">{Math.max(...usageData.map(d => d.memory)).toFixed(1)}%</td>
            </tr>
            <tr className="border-b hover:bg-muted/50">
              <td className="p-2">Total Cost</td>
              <td className="text-right p-2" colSpan={3}>${totalCost.toFixed(2)}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )

  const handleExport = (options: any) => {
    console.log('Exporting with options:', options)
  }

  const toggleResource = (resource: string) => {
    setSelectedResources(prev =>
      prev.includes(resource)
        ? prev.filter(r => r !== resource)
        : [...prev, resource]
    )
  }

  return (
    <ChartContainer
      title="Resource Usage"
      description="Monitor system resources and cloud costs"
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
                <p className="text-sm text-muted-foreground">CPU Usage</p>
                <p className="text-2xl font-bold">{latestData.cpu?.toFixed(1)}%</p>
                <div className={`flex items-center gap-1 text-sm ${cpuChange > 0 ? 'text-red-500' : 'text-green-500'}`}>
                  {cpuChange > 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                  {Math.abs(cpuChange).toFixed(1)}%
                </div>
              </div>
              <Cpu className="h-8 w-8 text-blue-500" />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Memory Usage</p>
                <p className="text-2xl font-bold">{latestData.memory?.toFixed(1)}%</p>
                <Progress value={latestData.memory} className="h-2 mt-2" />
              </div>
              <HardDrive className="h-8 w-8 text-green-500" />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">API Calls</p>
                <p className="text-2xl font-bold">{latestData.apiCalls?.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground">Last hour</p>
              </div>
              <Activity className="h-8 w-8 text-purple-500" />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Current Cost</p>
                <p className="text-2xl font-bold">${latestData.cost?.toFixed(2)}</p>
                <div className={`flex items-center gap-1 text-sm ${costChange > 10 ? 'text-red-500' : 'text-green-500'}`}>
                  {costChange > 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                  {Math.abs(costChange).toFixed(1)}%
                </div>
              </div>
              <DollarSign className="h-8 w-8 text-red-500" />
            </div>
          </Card>
        </div>

        <Tabs defaultValue="utilization" className="w-full">
          <TabsList className="grid grid-cols-5 w-full max-w-lg">
            <TabsTrigger value="utilization">Utilization</TabsTrigger>
            <TabsTrigger value="costs">Costs</TabsTrigger>
            <TabsTrigger value="api">API</TabsTrigger>
            <TabsTrigger value="capacity">Capacity</TabsTrigger>
            <TabsTrigger value="services">Services</TabsTrigger>
          </TabsList>

          <TabsContent value="utilization" className="space-y-4">
            <Card className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium">Resource Utilization Over Time</h3>
                <div className="flex gap-2">
                  {['cpu', 'memory', 'storage', 'network'].map(resource => (
                    <button
                      key={resource}
                      onClick={() => toggleResource(resource)}
                      className={`px-3 py-1 text-xs rounded-md transition-colors ${
                        selectedResources.includes(resource)
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted text-muted-foreground'
                      }`}
                    >
                      {resource.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={usageData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(time) => new Date(time).toLocaleTimeString()}
                  />
                  <YAxis />
                  <Tooltip content={renderCustomTooltip} />
                  <Legend />
                  {selectedResources.includes('cpu') && (
                    <Area 
                      type="monotone" 
                      dataKey="cpu" 
                      stroke={RESOURCE_COLORS.cpu}
                      fill={RESOURCE_COLORS.cpu}
                      fillOpacity={0.3}
                      name="CPU %"
                    />
                  )}
                  {selectedResources.includes('memory') && (
                    <Area 
                      type="monotone" 
                      dataKey="memory" 
                      stroke={RESOURCE_COLORS.memory}
                      fill={RESOURCE_COLORS.memory}
                      fillOpacity={0.3}
                      name="Memory %"
                    />
                  )}
                  {selectedResources.includes('storage') && (
                    <Area 
                      type="monotone" 
                      dataKey="storage" 
                      stroke={RESOURCE_COLORS.storage}
                      fill={RESOURCE_COLORS.storage}
                      fillOpacity={0.3}
                      name="Storage %"
                    />
                  )}
                  {selectedResources.includes('network') && (
                    <Area 
                      type="monotone" 
                      dataKey="network" 
                      stroke={RESOURCE_COLORS.network}
                      fill={RESOURCE_COLORS.network}
                      fillOpacity={0.3}
                      name="Network Mbps"
                    />
                  )}
                </AreaChart>
              </ResponsiveContainer>
            </Card>
          </TabsContent>

          <TabsContent value="costs" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="p-4">
                <h3 className="text-sm font-medium mb-4">Cost Breakdown</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={costBreakdown}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ category, percentage }) => `${category} (${percentage.toFixed(0)}%)`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="amount"
                    >
                      {costBreakdown.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={Object.values(RESOURCE_COLORS)[index % Object.values(RESOURCE_COLORS).length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      formatter={(value: number) => `$${value.toFixed(2)}`}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </Card>

              <Card className="p-4">
                <h3 className="text-sm font-medium mb-4">Cost Trend</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={usageData}>
                    <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />
                    <XAxis 
                      dataKey="timestamp" 
                      tickFormatter={(time) => new Date(time).toLocaleDateString()}
                    />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip content={renderCustomTooltip} />
                    <Legend />
                    <Bar yAxisId="left" dataKey="cost" fill={RESOURCE_COLORS.cost} name="Cost ($)" />
                    <Line 
                      yAxisId="right" 
                      type="monotone" 
                      dataKey="apiCalls" 
                      stroke={RESOURCE_COLORS.api}
                      strokeWidth={2}
                      name="API Calls"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="api" className="space-y-4">
            <Card className="p-4">
              <h3 className="text-sm font-medium mb-4">API Usage Metrics</h3>
              <div className="space-y-4">
                {apiMetrics.map((metric, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{metric.endpoint}</span>
                      <div className="flex gap-4 text-sm">
                        <span>{metric.calls.toLocaleString()} calls</span>
                        <span className="text-muted-foreground">{metric.avgLatency}ms avg</span>
                        <span className={metric.errorRate > 1 ? 'text-red-500' : 'text-green-500'}>
                          {metric.errorRate.toFixed(2)}% errors
                        </span>
                      </div>
                    </div>
                    <Progress value={Math.min((metric.calls / 10000) * 100, 100)} className="h-2" />
                  </div>
                ))}
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="capacity" className="space-y-4">
            <Card className="p-4">
              <h3 className="text-sm font-medium mb-4">Capacity Planning</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={capacityData} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />
                  <XAxis type="number" domain={[0, 100]} />
                  <YAxis dataKey="resource" type="category" width={80} />
                  <Tooltip content={renderCustomTooltip} />
                  <Legend />
                  <Bar dataKey="used" stackId="a" fill="#3B82F6" name="Used %" />
                  <Bar 
                    dataKey={(entry: any) => entry.projected - entry.used} 
                    stackId="a" 
                    fill="#F59E0B" 
                    name="Projected Growth %"
                  />
                  <Bar 
                    dataKey={(entry: any) => 100 - entry.projected} 
                    stackId="a" 
                    fill="#E5E7EB" 
                    name="Available %"
                  />
                </BarChart>
              </ResponsiveContainer>
              
              <div className="mt-4 space-y-2">
                {capacityData.filter(d => d.projected > 80).map((resource, index) => (
                  <div key={index} className="flex items-center gap-2 p-2 bg-yellow-500/10 rounded-md">
                    <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    <span className="text-sm">
                      {resource.resource} projected to reach {resource.projected}% capacity
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="services" className="space-y-4">
            {serviceUsage && (
              <Card className="p-4">
                <h3 className="text-sm font-medium mb-4">Service Resource Consumption</h3>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={serviceUsage}>
                    <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />
                    <XAxis dataKey="service" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip content={renderCustomTooltip} />
                    <Legend />
                    <Bar yAxisId="left" dataKey="cpu" fill={RESOURCE_COLORS.cpu} name="CPU %" />
                    <Bar yAxisId="left" dataKey="memory" fill={RESOURCE_COLORS.memory} name="Memory %" />
                    <Line 
                      yAxisId="right" 
                      type="monotone" 
                      dataKey="cost" 
                      stroke={RESOURCE_COLORS.cost}
                      strokeWidth={2}
                      name="Cost ($)"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </ChartContainer>
  )
}