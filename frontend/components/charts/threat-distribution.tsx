'use client'

import { useState } from 'react'
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadialBarChart,
  RadialBar,
  Treemap
} from 'recharts'
import { ChartContainer } from './chart-container'
import { ThreatDistributionData, GeographicData } from '@/types/charts'
import { useTheme } from 'next-themes'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card } from '@/components/ui/card'

interface ThreatDistributionProps {
  threatTypeData: ThreatDistributionData[]
  severityData: ThreatDistributionData[]
  geographicData?: GeographicData[]
  attackVectorData?: { vector: string; count: number; trend: 'up' | 'down' | 'stable' }[]
  timeDistributionData?: { hour: number; count: number }[]
  onRefresh?: () => void
  loading?: boolean
  error?: string
}

const COLORS = {
  critical: '#DC2626',
  high: '#EA580C',
  medium: '#F59E0B',
  low: '#3B82F6',
  info: '#6B7280'
}

const THREAT_COLORS = [
  '#8B5CF6', '#EC4899', '#EF4444', '#F59E0B', '#10B981',
  '#3B82F6', '#06B6D4', '#6366F1', '#F472B6', '#A78BFA'
]

export function ThreatDistribution({
  threatTypeData,
  severityData,
  geographicData,
  attackVectorData,
  timeDistributionData,
  onRefresh,
  loading,
  error
}: ThreatDistributionProps) {
  const { theme } = useTheme()
  const [activeIndex, setActiveIndex] = useState<number | undefined>()

  const renderCustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-background border rounded-lg p-3 shadow-lg">
          <p className="font-semibold">{payload[0].name || payload[0].payload.type}</p>
          <p className="text-sm">Count: {payload[0].value}</p>
          <p className="text-sm text-muted-foreground">
            {payload[0].payload.percentage?.toFixed(1)}% of total
          </p>
        </div>
      )
    }
    return null
  }

  const renderDataTable = () => (
    <div className="space-y-6">
      <div>
        <h4 className="font-semibold mb-2">Threat Types</h4>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left p-2">Type</th>
              <th className="text-right p-2">Count</th>
              <th className="text-right p-2">Percentage</th>
            </tr>
          </thead>
          <tbody>
            {threatTypeData.map((item, index) => (
              <tr key={index} className="border-b hover:bg-muted/50">
                <td className="p-2">{item.type}</td>
                <td className="text-right p-2">{item.count}</td>
                <td className="text-right p-2">{item.percentage.toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div>
        <h4 className="font-semibold mb-2">Severity Distribution</h4>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left p-2">Severity</th>
              <th className="text-right p-2">Count</th>
              <th className="text-right p-2">Percentage</th>
            </tr>
          </thead>
          <tbody>
            {severityData.map((item, index) => (
              <tr key={index} className="border-b hover:bg-muted/50">
                <td className="p-2 capitalize">{item.severity}</td>
                <td className="text-right p-2">{item.count}</td>
                <td className="text-right p-2">{item.percentage.toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )

  const handleExport = (options: any) => {
    console.log('Exporting with options:', options)
  }

  const onPieEnter = (_: any, index: number) => {
    setActiveIndex(index)
  }

  const onPieLeave = () => {
    setActiveIndex(undefined)
  }

  return (
    <ChartContainer
      title="Threat Distribution"
      description="Analyze threat patterns and attack vectors"
      onRefresh={onRefresh}
      onExport={handleExport}
      renderDataTable={renderDataTable}
      loading={loading}
      error={error}
    >
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid grid-cols-5 w-full max-w-lg">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="severity">Severity</TabsTrigger>
          <TabsTrigger value="vectors">Vectors</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="geographic">Geographic</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="p-4">
              <h3 className="text-sm font-medium mb-4">Threat Types</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={threatTypeData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ type, percentage }) => `${type} (${percentage.toFixed(0)}%)`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                    activeIndex={activeIndex}
                    activeShape={(props: any) => {
                      const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill } = props
                      return (
                        <g>
                          <Sector
                            cx={cx}
                            cy={cy}
                            innerRadius={innerRadius}
                            outerRadius={outerRadius + 10}
                            startAngle={startAngle}
                            endAngle={endAngle}
                            fill={fill}
                          />
                        </g>
                      )
                    }}
                    onMouseEnter={onPieEnter}
                    onMouseLeave={onPieLeave}
                  >
                    {threatTypeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={THREAT_COLORS[index % THREAT_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={renderCustomTooltip} />
                </PieChart>
              </ResponsiveContainer>
            </Card>

            <Card className="p-4">
              <h3 className="text-sm font-medium mb-4">Top Threats</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={threatTypeData.slice(0, 5)} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />
                  <XAxis type="number" />
                  <YAxis dataKey="type" type="category" width={100} />
                  <Tooltip content={renderCustomTooltip} />
                  <Bar dataKey="count" fill="#8B5CF6" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="severity" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="p-4">
              <h3 className="text-sm font-medium mb-4">Severity Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <RadialBarChart cx="50%" cy="50%" innerRadius="10%" outerRadius="90%" data={severityData}>
                  <RadialBar dataKey="count" cornerRadius={10} fill="#82ca9d">
                    {severityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[entry.severity as keyof typeof COLORS]} />
                    ))}
                  </RadialBar>
                  <Tooltip content={renderCustomTooltip} />
                  <Legend />
                </RadialBarChart>
              </ResponsiveContainer>
            </Card>

            <Card className="p-4">
              <h3 className="text-sm font-medium mb-4">Severity Breakdown</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={severityData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />
                  <XAxis dataKey="severity" />
                  <YAxis />
                  <Tooltip content={renderCustomTooltip} />
                  <Bar dataKey="count">
                    {severityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[entry.severity as keyof typeof COLORS]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="vectors" className="space-y-4">
          {attackVectorData && (
            <Card className="p-4">
              <h3 className="text-sm font-medium mb-4">Attack Vectors</h3>
              <ResponsiveContainer width="100%" height={400}>
                <Treemap
                  data={attackVectorData.map(v => ({ name: v.vector, size: v.count, trend: v.trend }))}
                  dataKey="size"
                  aspectRatio={4 / 3}
                  fill="#8884d8"
                  content={({ x, y, width, height, name, value, trend }: any) => (
                    <g>
                      <rect
                        x={x}
                        y={y}
                        width={width}
                        height={height}
                        fill={trend === 'up' ? '#EF4444' : trend === 'down' ? '#10B981' : '#6B7280'}
                        fillOpacity={0.8}
                        stroke="#fff"
                        strokeWidth={2}
                      />
                      <text
                        x={x + width / 2}
                        y={y + height / 2}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill="white"
                        fontSize={12}
                      >
                        {name}
                      </text>
                      <text
                        x={x + width / 2}
                        y={y + height / 2 + 15}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill="white"
                        fontSize={10}
                      >
                        {value}
                      </text>
                    </g>
                  )}
                />
              </ResponsiveContainer>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="timeline" className="space-y-4">
          {timeDistributionData && (
            <Card className="p-4">
              <h3 className="text-sm font-medium mb-4">24-Hour Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={timeDistributionData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />
                  <XAxis 
                    dataKey="hour" 
                    tickFormatter={(hour) => `${hour}:00`}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(hour) => `${hour}:00`}
                    content={renderCustomTooltip}
                  />
                  <Bar dataKey="count" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="geographic" className="space-y-4">
          {geographicData && (
            <Card className="p-4">
              <h3 className="text-sm font-medium mb-4">Geographic Distribution</h3>
              <div className="h-96 flex items-center justify-center text-muted-foreground">
                Geographic heat map would be rendered here using a mapping library
              </div>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </ChartContainer>
  )
}

// Fix for missing Sector import
const Sector = ({ cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill }: any) => {
  const polarToCartesian = (centerX: number, centerY: number, radius: number, angleInDegrees: number) => {
    const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0
    return {
      x: centerX + (radius * Math.cos(angleInRadians)),
      y: centerY + (radius * Math.sin(angleInRadians))
    }
  }

  const arc = (x: number, y: number, radius: number, startAngle: number, endAngle: number) => {
    const start = polarToCartesian(x, y, radius, endAngle)
    const end = polarToCartesian(x, y, radius, startAngle)
    const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1"
    return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`
  }

  const outerArc = arc(cx, cy, outerRadius, startAngle, endAngle)
  const innerArc = arc(cx, cy, innerRadius, endAngle, startAngle)

  return (
    <path d={`${outerArc} L ${cx + innerRadius * Math.cos((endAngle - 90) * Math.PI / 180)} ${cy + innerRadius * Math.sin((endAngle - 90) * Math.PI / 180)} ${innerArc} Z`} fill={fill} />
  )
}