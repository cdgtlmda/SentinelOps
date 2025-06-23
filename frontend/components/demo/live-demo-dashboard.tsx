"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { 
  Play, 
  Pause, 
  Square, 
  Activity,
  Shield,
  Zap,
  Target,
  AlertTriangle,
  TrendingUp,
  Clock,
  Brain,
  Database
} from 'lucide-react'

interface DemoMetrics {
  timestamp: string
  demo_elapsed_seconds: number
  scenarios_per_minute: number
  severity_distribution: Record<string, number>
  analysis_performance: {
    total_analyzed: number
    average_confidence: number
    analysis_rate: number
  }
  threat_intel_stats: {
    threats_detected: number
    detection_rate: number
  }
  demo_stats: {
    scenarios_generated: number
    incidents_analyzed: number
    threats_detected: number
    false_positives: number
    critical_incidents: number
  }
}

interface DemoSession {
  demo_id: string
  start_time: string
  status: 'running' | 'completed' | 'error'
  config: {
    demo_duration_minutes: number
    demo_intensity: string
    threat_intel_enabled: boolean
    real_time_analysis: boolean
  }
}

interface LiveIncident {
  simulation_id: string
  event_type: string
  severity: 'LOW' | 'MEDIUM' | 'CRITICAL'
  finding: string
  timestamp: string
  demo_phase: string
  threat_intel_enrichment?: boolean
  risk_score?: number
}

const SeverityBadge = ({ severity }: { severity: string }) => {
  const configs = {
    LOW: 'bg-blue-100 text-blue-800 border-blue-200',
    MEDIUM: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    CRITICAL: 'bg-red-100 text-red-800 border-red-200'
  }
  return (
    <Badge className={configs[severity as keyof typeof configs] || configs.MEDIUM}>
      {severity}
    </Badge>
  )
}

const IntensityIndicator = ({ intensity }: { intensity: string }) => {
  const configs = {
    low: { color: 'bg-green-500', label: 'Low', percentage: 25 },
    medium: { color: 'bg-yellow-500', label: 'Medium', percentage: 50 },
    high: { color: 'bg-orange-500', label: 'High', percentage: 75 },
    extreme: { color: 'bg-red-500', label: 'Extreme', percentage: 100 }
  }
  
  const config = configs[intensity as keyof typeof configs] || configs.medium
  
  return (
    <div className="flex items-center space-x-2">
      <div className="flex-1">
        <Progress value={config.percentage} className="h-2" />
      </div>
      <span className="text-sm font-medium">{config.label}</span>
    </div>
  )
}

export function LiveDemoDashboard() {
  const [demoSession, setDemoSession] = useState<DemoSession | null>(null)
  const [metrics, setMetrics] = useState<DemoMetrics | null>(null)
  const [recentIncidents, setRecentIncidents] = useState<LiveIncident[]>([])
  const [isRunning, setIsRunning] = useState(false)
  const [loading, setLoading] = useState(false)

  // Auto-refresh data when demo is running
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null
    
    if (isRunning) {
      interval = setInterval(async () => {
        await fetchLiveMetrics()
        await fetchRecentIncidents()
      }, 2000) // Update every 2 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isRunning])

  const startDemo = async (intensity: string = 'medium', duration: number = 20) => {
    setLoading(true)
    try {
      const response = await fetch('/api/v1/demo/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          intensity,
          duration_minutes: duration,
          threat_intel_enabled: true,
          real_time_analysis: true
        })
      })
      
      const data = await response.json()
      if (data.status === 'success') {
        setDemoSession(data.session)
        setIsRunning(true)
      }
    } catch (error) {
      console.error('Failed to start demo:', error)
    } finally {
      setLoading(false)
    }
  }

  const stopDemo = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/v1/demo/stop', {
        method: 'POST'
      })
      
      if (response.ok) {
        setIsRunning(false)
        setDemoSession(null)
      }
    } catch (error) {
      console.error('Failed to stop demo:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchLiveMetrics = async () => {
    try {
      const response = await fetch('/api/v1/demo/metrics')
      const data = await response.json()
      if (data.status === 'success') {
        setMetrics(data.metrics)
      }
    } catch (error) {
      console.error('Failed to fetch metrics:', error)
    }
  }

  const fetchRecentIncidents = async () => {
    try {
      const response = await fetch('/api/v1/demo/incidents?limit=10')
      const data = await response.json()
      if (data.status === 'success') {
        setRecentIncidents(data.incidents)
      }
    } catch (error) {
      console.error('Failed to fetch incidents:', error)
    }
  }

  const formatElapsedTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  const getDemoProgress = () => {
    if (!demoSession || !metrics) return 0
    const totalDuration = demoSession.config.demo_duration_minutes * 60
    return Math.min(100, (metrics.demo_elapsed_seconds / totalDuration) * 100)
  }

  return (
    <div className="space-y-6">
      {/* Demo Control Panel */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                SentinelOps Live Demo
              </CardTitle>
              <CardDescription>
                Real-time threat simulation with AI-powered analysis
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              {!isRunning ? (
                <>
                  <Button
                    onClick={() => startDemo('medium', 20)}
                    disabled={loading}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <Play className="mr-2 h-4 w-4" />
                    Start Demo
                  </Button>
                  <Button
                    onClick={() => startDemo('high', 15)}
                    disabled={loading}
                    variant="outline"
                  >
                    <Zap className="mr-2 h-4 w-4" />
                    High Intensity
                  </Button>
                </>
              ) : (
                <Button
                  onClick={stopDemo}
                  disabled={loading}
                  variant="destructive"
                >
                  <Square className="mr-2 h-4 w-4" />
                  Stop Demo
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        
        {demoSession && (
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium">Demo Duration</label>
                <div className="text-2xl font-bold">
                  {metrics ? formatElapsedTime(metrics.demo_elapsed_seconds) : '0:00'}
                  <span className="text-sm text-muted-foreground ml-1">
                    / {demoSession.config.demo_duration_minutes}:00
                  </span>
                </div>
                <Progress value={getDemoProgress()} className="mt-2" />
              </div>
              
              <div>
                <label className="text-sm font-medium">Intensity Level</label>
                <div className="mt-1">
                  <IntensityIndicator intensity={demoSession.config.demo_intensity} />
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium">Status</label>
                <div className="flex items-center space-x-2 mt-1">
                  <div className={`w-2 h-2 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                  <span className="font-medium">
                    {isRunning ? 'Running' : 'Stopped'}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Live Metrics */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Target className="h-4 w-4" />
                Scenarios Generated
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.demo_stats.scenarios_generated}</div>
              <p className="text-xs text-muted-foreground">
                {metrics.scenarios_per_minute.toFixed(1)}/min
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Brain className="h-4 w-4" />
                AI Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.analysis_performance.total_analyzed}</div>
              <p className="text-xs text-muted-foreground">
                {(metrics.analysis_performance.average_confidence * 100).toFixed(0)}% avg confidence
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Shield className="h-4 w-4" />
                Threats Detected
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.threat_intel_stats.threats_detected}</div>
              <p className="text-xs text-muted-foreground">
                {metrics.threat_intel_stats.detection_rate.toFixed(1)}/min
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Critical Incidents
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {metrics.demo_stats.critical_incidents}
              </div>
              <p className="text-xs text-muted-foreground">
                {metrics.demo_stats.false_positives} false positives
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Severity Distribution */}
      {metrics && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Threat Severity Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              {Object.entries(metrics.severity_distribution).map(([severity, count]) => (
                <div key={severity} className="text-center">
                  <div className="text-2xl font-bold">{count}</div>
                  <SeverityBadge severity={severity} />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Incidents */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Live Incident Stream
          </CardTitle>
          <CardDescription>
            Real-time security events and threat detections
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {recentIncidents.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                {isRunning ? 'Waiting for incidents...' : 'Start demo to see live incidents'}
              </div>
            ) : (
              recentIncidents.map((incident) => (
                <div key={incident.simulation_id} className="border rounded-lg p-3 hover:bg-muted/50 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <SeverityBadge severity={incident.severity} />
                      <span className="font-medium">{incident.event_type}</span>
                      {incident.threat_intel_enrichment && (
                        <Badge variant="outline" className="text-xs">
                          <Database className="mr-1 h-3 w-3" />
                          Threat Intel
                        </Badge>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {new Date(incident.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">{incident.finding}</p>
                  <div className="flex items-center justify-between mt-2 text-xs">
                    <span className="text-blue-600">Phase: {incident.demo_phase}</span>
                    {incident.risk_score && (
                      <span className="text-orange-600">Risk: {incident.risk_score}/100</span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Demo Features */}
      <Card>
        <CardHeader>
          <CardTitle>Demo Features Active</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full" />
              <span className="text-sm">Threat Simulation</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full" />
              <span className="text-sm">Threat Intelligence</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full" />
              <span className="text-sm">AI Analysis</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full" />
              <span className="text-sm">Real-time Detection</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}