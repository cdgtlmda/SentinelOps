'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { 
  ChartFilter, 
  IncidentTrendData, 
  ThreatDistributionData,
  ResponseTimeData,
  SuccessRateData,
  ResourceUsageData,
  GeographicData
} from '@/types/charts'
import { subDays, subHours, format, startOfDay, endOfDay } from 'date-fns'

// Mock data generation functions
const generateIncidentTrendData = (days: number): IncidentTrendData[] => {
  const data: IncidentTrendData[] = []
  const now = new Date()
  
  for (let i = days - 1; i >= 0; i--) {
    const date = subDays(now, i)
    const baseCount = Math.floor(Math.random() * 20) + 10
    const critical = Math.floor(Math.random() * 3)
    const high = Math.floor(Math.random() * 5) + 2
    const medium = Math.floor(Math.random() * 8) + 3
    const low = Math.floor(Math.random() * 10) + 5
    
    data.push({
      date: format(date, 'MMM dd'),
      total: critical + high + medium + low,
      critical,
      high,
      medium,
      low,
      movingAverage: baseCount + Math.random() * 5,
      anomaly: Math.random() > 0.9
    })
  }
  
  return data
}

const generateThreatDistributionData = (): {
  threatTypes: ThreatDistributionData[],
  severityData: ThreatDistributionData[],
  geographic: GeographicData[]
} => {
  const threatTypes = [
    'Malware', 'Phishing', 'DDoS', 'SQL Injection', 'XSS', 
    'Brute Force', 'Zero Day', 'Ransomware', 'Data Breach'
  ]
  
  const total = 1000
  const distribution = threatTypes.map(type => {
    const count = Math.floor(Math.random() * 200) + 50
    return {
      type,
      count,
      percentage: (count / total) * 100,
      severity: ['critical', 'high', 'medium', 'low'][Math.floor(Math.random() * 4)] as any
    }
  })
  
  const severityData = ['critical', 'high', 'medium', 'low'].map(severity => {
    const count = distribution.filter(d => d.severity === severity).reduce((sum, d) => sum + d.count, 0)
    return {
      type: severity,
      count,
      percentage: (count / total) * 100,
      severity: severity as any
    }
  })
  
  const geographic: GeographicData[] = [
    { country: 'United States', lat: 37.0902, lng: -95.7129, count: 450, severity: 'high' as any },
    { country: 'China', lat: 35.8617, lng: 104.1954, count: 320, severity: 'critical' as any },
    { country: 'Russia', lat: 61.5240, lng: 105.3188, count: 280, severity: 'high' as any },
    { country: 'Germany', lat: 51.1657, lng: 10.4515, count: 180, severity: 'medium' as any },
    { country: 'Brazil', lat: -14.2350, lng: -51.9253, count: 150, severity: 'low' as any }
  ]
  
  return { threatTypes: distribution, severityData, geographic }
}

const generateResponseTimeData = (): ResponseTimeData[] => {
  const data: ResponseTimeData[] = []
  const now = new Date()
  
  for (let i = 0; i < 100; i++) {
    const detectionTime = subHours(now, Math.random() * 168) // Last week
    const acknowledgeTime = new Date(detectionTime.getTime() + Math.random() * 30 * 60 * 1000) // 0-30 min
    const resolutionTime = new Date(acknowledgeTime.getTime() + Math.random() * 240 * 60 * 1000) // 0-4 hours
    const mttr = (resolutionTime.getTime() - detectionTime.getTime()) / (60 * 1000) // minutes
    
    data.push({
      incidentId: `INC-${1000 + i}`,
      detectionTime,
      acknowledgeTime,
      resolutionTime,
      mttr,
      slaStatus: mttr < 60 ? 'met' : mttr < 120 ? 'at_risk' : 'breached'
    })
  }
  
  return data
}

const generateSuccessRateData = (periods: number): SuccessRateData[] => {
  const data: SuccessRateData[] = []
  
  for (let i = 0; i < periods; i++) {
    const totalIncidents = Math.floor(Math.random() * 50) + 20
    const successRate = 75 + Math.random() * 20 // 75-95%
    const successfulRemediations = Math.floor(totalIncidents * (successRate / 100))
    
    data.push({
      period: `Period ${i + 1}`,
      successRate,
      totalIncidents,
      successfulRemediations,
      failedRemediations: totalIncidents - successfulRemediations
    })
  }
  
  return data
}

const generateResourceUsageData = (hours: number): ResourceUsageData[] => {
  const data: ResourceUsageData[] = []
  const now = new Date()
  
  for (let i = hours - 1; i >= 0; i--) {
    const timestamp = subHours(now, i)
    
    data.push({
      timestamp,
      cpu: 30 + Math.random() * 40 + (i % 6 === 0 ? 20 : 0), // Spike every 6 hours
      memory: 40 + Math.random() * 30,
      storage: 60 + Math.random() * 20,
      network: 20 + Math.random() * 60,
      apiCalls: Math.floor(1000 + Math.random() * 4000),
      cost: 0.5 + Math.random() * 2
    })
  }
  
  return data
}

interface UseChartDataOptions {
  filter?: ChartFilter
  refreshInterval?: number
  enableRealtime?: boolean
}

export function useChartData(
  chartType: 'incidents' | 'threats' | 'response' | 'success' | 'resources',
  options: UseChartDataOptions = {}
) {
  const { filter, refreshInterval = 30000, enableRealtime = false } = options
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<NodeJS.Timeout>()

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500))

      switch (chartType) {
        case 'incidents':
          const days = filter?.dateRange ? 
            Math.ceil((filter.dateRange.end.getTime() - filter.dateRange.start.getTime()) / (1000 * 60 * 60 * 24)) :
            7
          setData(generateIncidentTrendData(days))
          break

        case 'threats':
          const threatData = generateThreatDistributionData()
          setData(threatData)
          break

        case 'response':
          const responseData = generateResponseTimeData()
          const histogramData = [
            { range: '0-30 min', count: 25, avgMttr: 22 },
            { range: '30-60 min', count: 35, avgMttr: 45 },
            { range: '1-2 hrs', count: 20, avgMttr: 90 },
            { range: '2-4 hrs', count: 15, avgMttr: 180 },
            { range: '4+ hrs', count: 5, avgMttr: 360 }
          ]
          const mttrTrendData = generateIncidentTrendData(7).map(d => ({
            date: d.date,
            mttr: 60 + Math.random() * 60,
            slaTarget: 90
          }))
          const agentPerformanceData = [
            { agent: 'Agent-1', avgResponseTime: 45, incidentCount: 120, successRate: 0.92 },
            { agent: 'Agent-2', avgResponseTime: 52, incidentCount: 98, successRate: 0.88 },
            { agent: 'Agent-3', avgResponseTime: 38, incidentCount: 145, successRate: 0.95 },
            { agent: 'Agent-4', avgResponseTime: 61, incidentCount: 87, successRate: 0.85 }
          ]
          setData({ responseData, histogramData, mttrTrendData, agentPerformanceData })
          break

        case 'success':
          const overallData = generateSuccessRateData(1)
          const trendData = generateSuccessRateData(7)
          const byTypeData = [
            { incidentType: 'Malware', successRate: 92, totalIncidents: 45, successfulRemediations: 41, failedRemediations: 4 },
            { incidentType: 'DDoS', successRate: 88, totalIncidents: 32, successfulRemediations: 28, failedRemediations: 4 },
            { incidentType: 'Phishing', successRate: 95, totalIncidents: 58, successfulRemediations: 55, failedRemediations: 3 },
            { incidentType: 'SQL Injection', successRate: 90, totalIncidents: 21, successfulRemediations: 19, failedRemediations: 2 }
          ]
          const agentEffectivenessData = [
            { agentId: 'Agent-1', successRate: 94, totalIncidents: 120, successfulRemediations: 113, failedRemediations: 7 },
            { agentId: 'Agent-2', successRate: 88, totalIncidents: 98, successfulRemediations: 86, failedRemediations: 12 },
            { agentId: 'Agent-3', successRate: 95, totalIncidents: 145, successfulRemediations: 138, failedRemediations: 7 },
            { agentId: 'Agent-4', successRate: 85, totalIncidents: 87, successfulRemediations: 74, failedRemediations: 13 },
            { agentId: 'Agent-5', successRate: 91, totalIncidents: 102, successfulRemediations: 93, failedRemediations: 9 },
            { agentId: 'Agent-6', successRate: 89, totalIncidents: 95, successfulRemediations: 85, failedRemediations: 10 }
          ]
          const remediationData = [
            { type: 'Automated', success: 245, failed: 12, total: 257 },
            { type: 'Semi-Automated', success: 132, failed: 18, total: 150 },
            { type: 'Manual', success: 87, failed: 23, total: 110 },
            { type: 'Escalated', success: 45, failed: 8, total: 53 }
          ]
          setData({ overallData, trendData, byTypeData, agentEffectivenessData, remediationData })
          break

        case 'resources':
          const usageData = generateResourceUsageData(24)
          const costBreakdown = [
            { category: 'Compute', amount: 1250, percentage: 35 },
            { category: 'Storage', amount: 890, percentage: 25 },
            { category: 'Network', amount: 640, percentage: 18 },
            { category: 'API Calls', amount: 430, percentage: 12 },
            { category: 'Other', amount: 360, percentage: 10 }
          ]
          const apiMetrics = [
            { endpoint: '/api/incidents', calls: 8432, avgLatency: 45, errorRate: 0.2 },
            { endpoint: '/api/agents', calls: 6234, avgLatency: 32, errorRate: 0.1 },
            { endpoint: '/api/remediate', calls: 3421, avgLatency: 120, errorRate: 0.5 },
            { endpoint: '/api/alerts', calls: 12543, avgLatency: 28, errorRate: 0.3 }
          ]
          const capacityData = [
            { resource: 'CPU', used: 65, total: 100, projected: 78 },
            { resource: 'Memory', used: 72, total: 100, projected: 85 },
            { resource: 'Storage', used: 58, total: 100, projected: 65 },
            { resource: 'Network', used: 45, total: 100, projected: 52 }
          ]
          const serviceUsage = [
            { service: 'Detection', cpu: 35, memory: 42, cost: 450 },
            { service: 'Analysis', cpu: 45, memory: 58, cost: 680 },
            { service: 'Remediation', cpu: 28, memory: 35, cost: 320 },
            { service: 'Reporting', cpu: 15, memory: 22, cost: 180 }
          ]
          setData({ usageData, costBreakdown, apiMetrics, capacityData, serviceUsage })
          break
      }

      setLoading(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch chart data')
      setLoading(false)
    }
  }, [chartType, filter])

  // Initial fetch
  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Set up refresh interval if enabled
  useEffect(() => {
    if (enableRealtime && refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval)
      
      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
        }
      }
    }
  }, [enableRealtime, refreshInterval, fetchData])

  const refresh = useCallback(() => {
    return fetchData()
  }, [fetchData])

  return {
    data,
    loading,
    error,
    refresh
  }
}

// Export specific hooks for each chart type
export const useIncidentTrends = (options?: UseChartDataOptions) => 
  useChartData('incidents', options)

export const useThreatDistribution = (options?: UseChartDataOptions) => 
  useChartData('threats', options)

export const useResponseTimes = (options?: UseChartDataOptions) => 
  useChartData('response', options)

export const useSuccessRates = (options?: UseChartDataOptions) => 
  useChartData('success', options)

export const useResourceUsage = (options?: UseChartDataOptions) => 
  useChartData('resources', options)