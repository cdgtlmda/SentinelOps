'use client'

import { useState } from 'react'
import {
  RadialBarChart,
  RadialBar,
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
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  Cell
} from 'recharts'
import { ChartContainer } from './chart-container'
import { SuccessRateData } from '@/types/charts'
import { useTheme } from 'next-themes'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { CheckCircle2, XCircle, TrendingUp, TrendingDown } from 'lucide-react'

interface SuccessRatesProps {
  overallData: SuccessRateData[]
  trendData: SuccessRateData[]
  byTypeData: SuccessRateData[]
  agentEffectivenessData: SuccessRateData[]
  remediationData: { type: string; success: number; failed: number; total: number }[]
  onRefresh?: () => void
  loading?: boolean
  error?: string
}

const SUCCESS_COLORS = {
  excellent: '#10B981',
  good: '#3B82F6',
  fair: '#F59E0B',
  poor: '#EF4444'
}

export function SuccessRates({
  overallData,
  trendData,
  byTypeData,
  agentEffectivenessData,
  remediationData,
  onRefresh,
  loading,
  error
}: SuccessRatesProps) {
  const { theme } = useTheme()
  const [selectedPeriod, setSelectedPeriod] = useState('7d')

  const getSuccessColor = (rate: number) => {
    if (rate >= 95) return SUCCESS_COLORS.excellent
    if (rate >= 85) return SUCCESS_COLORS.good
    if (rate >= 70) return SUCCESS_COLORS.fair
    return SUCCESS_COLORS.poor
  }

  const getSuccessLabel = (rate: number) => {
    if (rate >= 95) return 'Excellent'
    if (rate >= 85) return 'Good'
    if (rate >= 70) return 'Fair'
    return 'Poor'
  }

  const currentSuccessRate = overallData[overallData.length - 1]?.successRate || 0
  const previousSuccessRate = overallData[overallData.length - 2]?.successRate || 0
  const rateChange = currentSuccessRate - previousSuccessRate

  const renderCustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-background border rounded-lg p-3 shadow-lg">
          <p className="font-semibold">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
              {entry.name.includes('Rate') ? '%' : ''}
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
        <h4 className="font-semibold mb-2">Success Rate Summary</h4>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left p-2">Metric</th>
              <th className="text-right p-2">Value</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b hover:bg-muted/50">
              <td className="p-2">Current Success Rate</td>
              <td className="text-right p-2">{currentSuccessRate.toFixed(1)}%</td>
            </tr>
            <tr className="border-b hover:bg-muted/50">
              <td className="p-2">Change</td>
              <td className="text-right p-2 flex items-center justify-end gap-1">
                {rateChange > 0 ? (
                  <TrendingUp className="h-4 w-4 text-green-500" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-500" />
                )}
                {Math.abs(rateChange).toFixed(1)}%
              </td>
            </tr>
            <tr className="border-b hover:bg-muted/50">
              <td className="p-2">Total Incidents</td>
              <td className="text-right p-2">
                {overallData.reduce((sum, d) => sum + d.totalIncidents, 0)}
              </td>
            </tr>
            <tr className="border-b hover:bg-muted/50">
              <td className="p-2">Successful Remediations</td>
              <td className="text-right p-2">
                {overallData.reduce((sum, d) => sum + d.successfulRemediations, 0)}
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

  // Prepare gauge data
  const gaugeData = [
    {
      name: 'Success Rate',
      value: currentSuccessRate,
      fill: getSuccessColor(currentSuccessRate)
    }
  ]

  return (
    <ChartContainer
      title="Success Rates"
      description="Track remediation effectiveness and agent performance"
      onRefresh={onRefresh}
      onExport={handleExport}
      renderDataTable={renderDataTable}
      loading={loading}
      error={error}
    >
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="p-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium">Overall Success Rate</h3>
                <div className={`flex items-center gap-1 text-sm ${rateChange > 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {rateChange > 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                  {Math.abs(rateChange).toFixed(1)}%
                </div>
              </div>
              
              <div className="relative h-32">
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart 
                    cx="50%" 
                    cy="50%" 
                    innerRadius="60%" 
                    outerRadius="90%" 
                    data={gaugeData}
                    startAngle={180} 
                    endAngle={0}
                  >
                    <RadialBar dataKey="value" cornerRadius={10} fill={gaugeData[0].fill} />
                  </RadialBarChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <p className="text-3xl font-bold">{currentSuccessRate.toFixed(1)}%</p>
                    <p className="text-sm text-muted-foreground">{getSuccessLabel(currentSuccessRate)}</p>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <h3 className="text-sm font-medium mb-4">Remediation Breakdown</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  <span className="text-sm">Successful</span>
                </div>
                <span className="text-sm font-medium">
                  {overallData.reduce((sum, d) => sum + d.successfulRemediations, 0)}
                </span>
              </div>
              <Progress 
                value={currentSuccessRate} 
                className="h-2"
                style={{ '--progress-color': SUCCESS_COLORS.excellent } as any}
              />
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <XCircle className="h-4 w-4 text-red-500" />
                  <span className="text-sm">Failed</span>
                </div>
                <span className="text-sm font-medium">
                  {overallData.reduce((sum, d) => sum + d.failedRemediations, 0)}
                </span>
              </div>
              <Progress 
                value={100 - currentSuccessRate} 
                className="h-2"
                style={{ '--progress-color': SUCCESS_COLORS.poor } as any}
              />
            </div>
          </Card>

          <Card className="p-4">
            <h3 className="text-sm font-medium mb-4">Top Performing Agents</h3>
            <div className="space-y-2">
              {agentEffectivenessData.slice(0, 3).map((agent, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm">{agent.agentId}</span>
                  <div className="flex items-center gap-2">
                    <Progress 
                      value={agent.successRate} 
                      className="w-20 h-2"
                      style={{ '--progress-color': getSuccessColor(agent.successRate) } as any}
                    />
                    <span className="text-sm font-medium w-12 text-right">
                      {agent.successRate.toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <Tabs defaultValue="trends" className="w-full">
          <TabsList className="grid grid-cols-4 w-full max-w-md">
            <TabsTrigger value="trends">Trends</TabsTrigger>
            <TabsTrigger value="by-type">By Type</TabsTrigger>
            <TabsTrigger value="agents">Agents</TabsTrigger>
            <TabsTrigger value="remediation">Remediation</TabsTrigger>
          </TabsList>

          <TabsContent value="trends" className="space-y-4">
            <Card className="p-4">
              <h3 className="text-sm font-medium mb-4">Success Rate Trends</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />
                  <XAxis dataKey="period" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip content={renderCustomTooltip} />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="successRate" 
                    stroke="#10B981" 
                    strokeWidth={2}
                    name="Success Rate %"
                    dot={{ r: 4 }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="totalIncidents" 
                    stroke="#3B82F6" 
                    strokeWidth={2}
                    name="Total Incidents"
                    yAxisId="right"
                    dot={{ r: 4 }}
                  />
                  <YAxis yAxisId="right" orientation="right" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </TabsContent>

          <TabsContent value="by-type" className="space-y-4">
            <Card className="p-4">
              <h3 className="text-sm font-medium mb-4">Success Rate by Incident Type</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={byTypeData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />
                  <XAxis dataKey="incidentType" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip content={renderCustomTooltip} />
                  <Bar dataKey="successRate" name="Success Rate %">
                    {byTypeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getSuccessColor(entry.successRate)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </TabsContent>

          <TabsContent value="agents" className="space-y-4">
            <Card className="p-4">
              <h3 className="text-sm font-medium mb-4">Agent Effectiveness Scores</h3>
              <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={agentEffectivenessData.slice(0, 6)}>
                  <PolarGrid stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />
                  <PolarAngleAxis dataKey="agentId" />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} />
                  <Radar 
                    name="Success Rate" 
                    dataKey="successRate" 
                    stroke="#10B981" 
                    fill="#10B981" 
                    fillOpacity={0.6}
                  />
                  <Tooltip content={renderCustomTooltip} />
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </Card>
          </TabsContent>

          <TabsContent value="remediation" className="space-y-4">
            <Card className="p-4">
              <h3 className="text-sm font-medium mb-4">Remediation Success by Type</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={remediationData} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />
                  <XAxis type="number" />
                  <YAxis dataKey="type" type="category" width={120} />
                  <Tooltip content={renderCustomTooltip} />
                  <Legend />
                  <Bar dataKey="success" stackId="a" fill="#10B981" name="Successful" />
                  <Bar dataKey="failed" stackId="a" fill="#EF4444" name="Failed" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </ChartContainer>
  )
}