'use client'

import { useState } from 'react'
import { 
  IncidentTrends, 
  ThreatDistribution, 
  ResponseTimes, 
  SuccessRates, 
  ResourceUsage 
} from '@/components/charts'
import {
  useIncidentTrends,
  useThreatDistribution,
  useResponseTimes,
  useSuccessRates,
  useResourceUsage
} from '@/hooks/use-chart-data'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { ChartFilter } from '@/types/charts'
import { 
  BarChart3, 
  TrendingUp, 
  Shield, 
  Clock, 
  CheckCircle, 
  Cpu,
  RefreshCw,
  Download,
  Calendar
} from 'lucide-react'
import { format } from 'date-fns'

export default function AnalyticsPage() {
  const [globalFilter, setGlobalFilter] = useState<ChartFilter>({})
  const [refreshing, setRefreshing] = useState(false)

  // Use chart data hooks
  const incidentTrends = useIncidentTrends({ filter: globalFilter })
  const threatDistribution = useThreatDistribution({ filter: globalFilter })
  const responseTimes = useResponseTimes({ filter: globalFilter })
  const successRates = useSuccessRates({ filter: globalFilter })
  const resourceUsage = useResourceUsage({ filter: globalFilter, enableRealtime: true })

  const handleGlobalRefresh = async () => {
    setRefreshing(true)
    await Promise.all([
      incidentTrends.refresh(),
      threatDistribution.refresh(),
      responseTimes.refresh(),
      successRates.refresh(),
      resourceUsage.refresh()
    ])
    setTimeout(() => setRefreshing(false), 500)
  }

  const handleTimeRangeChange = (value: string) => {
    const end = new Date()
    let start = new Date()
    let granularity: 'hour' | 'day' | 'week' | 'month' = 'day'
    
    switch (value) {
      case '24h':
        start.setHours(start.getHours() - 24)
        granularity = 'hour'
        break
      case '7d':
        start.setDate(start.getDate() - 7)
        granularity = 'day'
        break
      case '30d':
        start.setDate(start.getDate() - 30)
        granularity = 'week'
        break
      case '90d':
        start.setDate(start.getDate() - 90)
        granularity = 'week'
        break
    }
    
    setGlobalFilter({
      ...globalFilter,
      dateRange: { start, end, granularity }
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Comprehensive insights into your security operations
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <Select defaultValue="7d" onValueChange={handleTimeRangeChange}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="24h">Last 24 Hours</SelectItem>
                <SelectItem value="7d">Last 7 Days</SelectItem>
                <SelectItem value="30d">Last 30 Days</SelectItem>
                <SelectItem value="90d">Last 90 Days</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleGlobalRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh All
          </Button>
          
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Key Metrics Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Incidents</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {incidentTrends.data?.reduce((sum: number, d: any) => sum + d.total, 0) || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-500">↑ 12.5%</span> from last period
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {responseTimes.data?.responseData?.[0]?.mttr.toFixed(1) || '0'} min
            </div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-500">↓ 8.3%</span> improvement
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {successRates.data?.overallData?.[0]?.successRate.toFixed(1) || '0'}%
            </div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-500">↑ 3.2%</span> from baseline
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resource Usage</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {resourceUsage.data?.usageData?.[0]?.cpu.toFixed(1) || '0'}%
            </div>
            <p className="text-xs text-muted-foreground">
              CPU utilization (current)
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Charts */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-6 max-w-2xl">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="incidents" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Incidents
          </TabsTrigger>
          <TabsTrigger value="threats" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Threats
          </TabsTrigger>
          <TabsTrigger value="response" className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Response
          </TabsTrigger>
          <TabsTrigger value="success" className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4" />
            Success
          </TabsTrigger>
          <TabsTrigger value="resources" className="flex items-center gap-2">
            <Cpu className="h-4 w-4" />
            Resources
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <IncidentTrends
              data={incidentTrends.data || []}
              onRefresh={incidentTrends.refresh}
              loading={incidentTrends.loading}
              error={incidentTrends.error || undefined}
            />
            <ThreatDistribution
              threatTypeData={threatDistribution.data?.threatTypes || []}
              severityData={threatDistribution.data?.severityData || []}
              geographicData={threatDistribution.data?.geographic}
              onRefresh={threatDistribution.refresh}
              loading={threatDistribution.loading}
              error={threatDistribution.error || undefined}
            />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <ResponseTimes
              responseData={responseTimes.data?.responseData || []}
              histogramData={responseTimes.data?.histogramData || []}
              mttrTrendData={responseTimes.data?.mttrTrendData || []}
              agentPerformanceData={responseTimes.data?.agentPerformanceData || []}
              onRefresh={responseTimes.refresh}
              loading={responseTimes.loading}
              error={responseTimes.error || undefined}
            />
            <SuccessRates
              overallData={successRates.data?.overallData || []}
              trendData={successRates.data?.trendData || []}
              byTypeData={successRates.data?.byTypeData || []}
              agentEffectivenessData={successRates.data?.agentEffectivenessData || []}
              remediationData={successRates.data?.remediationData || []}
              onRefresh={successRates.refresh}
              loading={successRates.loading}
              error={successRates.error || undefined}
            />
          </div>
        </TabsContent>

        <TabsContent value="incidents" className="space-y-4">
          <IncidentTrends
            data={incidentTrends.data || []}
            filter={globalFilter}
            onFilterChange={setGlobalFilter}
            onRefresh={incidentTrends.refresh}
            loading={incidentTrends.loading}
            error={incidentTrends.error || undefined}
          />
        </TabsContent>

        <TabsContent value="threats" className="space-y-4">
          <ThreatDistribution
            threatTypeData={threatDistribution.data?.threatTypes || []}
            severityData={threatDistribution.data?.severityData || []}
            geographicData={threatDistribution.data?.geographic}
            attackVectorData={[
              { vector: 'Web Application', count: 450, trend: 'up' },
              { vector: 'Email', count: 320, trend: 'down' },
              { vector: 'Network', count: 280, trend: 'stable' },
              { vector: 'Endpoint', count: 210, trend: 'up' },
              { vector: 'Cloud', count: 180, trend: 'up' }
            ]}
            timeDistributionData={Array.from({ length: 24 }, (_, i) => ({
              hour: i,
              count: Math.floor(Math.random() * 100) + 20
            }))}
            onRefresh={threatDistribution.refresh}
            loading={threatDistribution.loading}
            error={threatDistribution.error || undefined}
          />
        </TabsContent>

        <TabsContent value="response" className="space-y-4">
          <ResponseTimes
            responseData={responseTimes.data?.responseData || []}
            histogramData={responseTimes.data?.histogramData || []}
            mttrTrendData={responseTimes.data?.mttrTrendData || []}
            agentPerformanceData={responseTimes.data?.agentPerformanceData || []}
            onRefresh={responseTimes.refresh}
            loading={responseTimes.loading}
            error={responseTimes.error || undefined}
          />
        </TabsContent>

        <TabsContent value="success" className="space-y-4">
          <SuccessRates
            overallData={successRates.data?.overallData || []}
            trendData={successRates.data?.trendData || []}
            byTypeData={successRates.data?.byTypeData || []}
            agentEffectivenessData={successRates.data?.agentEffectivenessData || []}
            remediationData={successRates.data?.remediationData || []}
            onRefresh={successRates.refresh}
            loading={successRates.loading}
            error={successRates.error || undefined}
          />
        </TabsContent>

        <TabsContent value="resources" className="space-y-4">
          <ResourceUsage
            usageData={resourceUsage.data?.usageData || []}
            costBreakdown={resourceUsage.data?.costBreakdown || []}
            apiMetrics={resourceUsage.data?.apiMetrics || []}
            capacityData={resourceUsage.data?.capacityData || []}
            serviceUsage={resourceUsage.data?.serviceUsage}
            onRefresh={resourceUsage.refresh}
            loading={resourceUsage.loading}
            error={resourceUsage.error || undefined}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}