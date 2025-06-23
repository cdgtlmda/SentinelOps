// Chart-related TypeScript interfaces

import { IncidentSeverity, IncidentStatus } from './incident'

export interface ChartDataPoint {
  timestamp: Date
  value: number
  label?: string
  metadata?: Record<string, any>
}

export interface IncidentTrendData {
  date: string
  total: number
  critical: number
  high: number
  medium: number
  low: number
  movingAverage?: number
  anomaly?: boolean
}

export interface ThreatDistributionData {
  type: string
  count: number
  percentage: number
  severity: IncidentSeverity
}

export interface GeographicData {
  country: string
  region?: string
  lat: number
  lng: number
  count: number
  severity: IncidentSeverity
}

export interface ResponseTimeData {
  incidentId: string
  detectionTime: Date
  acknowledgeTime: Date
  resolutionTime: Date
  mttr: number // minutes
  slaStatus: 'met' | 'at_risk' | 'breached'
}

export interface SuccessRateData {
  period: string
  successRate: number
  totalIncidents: number
  successfulRemediations: number
  failedRemediations: number
  incidentType?: string
  agentId?: string
}

export interface ResourceUsageData {
  timestamp: Date
  cpu: number
  memory: number
  storage: number
  network: number
  apiCalls: number
  cost: number
  service?: string
}

export interface ChartTimeRange {
  start: Date
  end: Date
  granularity: 'hour' | 'day' | 'week' | 'month'
}

export interface ChartFilter {
  severities?: IncidentSeverity[]
  statuses?: IncidentStatus[]
  dateRange?: ChartTimeRange
  comparisonPeriod?: ChartTimeRange
  limit?: number
}

export interface ChartExportOptions {
  format: 'png' | 'svg' | 'csv' | 'json'
  filename?: string
  includeData?: boolean
}

export interface ChartTheme {
  colors: {
    primary: string
    secondary: string
    success: string
    warning: string
    error: string
    info: string
    critical: string
    high: string
    medium: string
    low: string
  }
  dark: boolean
}