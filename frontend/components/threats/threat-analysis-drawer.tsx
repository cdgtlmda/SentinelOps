"use client"

import React, { useState, useEffect } from 'react'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { 
  AlertTriangle, 
  Brain, 
  Clock, 
  Shield, 
  Target, 
  Zap,
  ExternalLink,
  Copy,
  CheckCircle,
  AlertCircle,
  XCircle
} from 'lucide-react'

interface ThreatAnalysis {
  incident_id: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  root_cause: string
  blast_radius: string
  recommended_action: string
  confidence: number
  mitre_tactics: string[]
  mitre_techniques: string[]
  indicators_of_compromise: string[]
  remediation_steps: string[]
  estimated_impact: string
  business_context: string
  gemini_tokens: number
  analysis_timestamp: string
  model_used: string
}

interface ThreatAnalysisDrawerProps {
  incidentId: string
  trigger?: React.ReactNode
  onAnalysisLoad?: (analysis: ThreatAnalysis) => void
}

const SeverityBadge = ({ severity }: { severity: string }) => {
  const severityConfig = {
    LOW: { color: 'bg-blue-100 text-blue-800 border-blue-200', icon: '🔵' },
    MEDIUM: { color: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: '🟡' },
    HIGH: { color: 'bg-orange-100 text-orange-800 border-orange-200', icon: '🟠' },
    CRITICAL: { color: 'bg-red-100 text-red-800 border-red-200', icon: '🔴' }
  }
  
  const config = severityConfig[severity as keyof typeof severityConfig] || severityConfig.MEDIUM
  
  return (
    <Badge className={`${config.color} font-semibold`}>
      <span className="mr-1">{config.icon}</span>
      {severity}
    </Badge>
  )
}

const ConfidenceIndicator = ({ confidence }: { confidence: number }) => {
  const percentage = Math.round(confidence * 100)
  const color = confidence >= 0.8 ? 'bg-green-500' : confidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
  
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span>AI Confidence</span>
        <span className="font-semibold">{percentage}%</span>
      </div>
      <Progress value={percentage} className="h-2" />
      <div className="text-xs text-muted-foreground">
        {confidence >= 0.8 ? 'High confidence' : confidence >= 0.6 ? 'Medium confidence' : 'Low confidence'}
      </div>
    </div>
  )
}

const MitreTechnique = ({ technique }: { technique: string }) => {
  const [id, ...nameParts] = technique.split(' - ')
  const name = nameParts.join(' - ')
  
  return (
    <div className="flex items-center justify-between p-2 bg-slate-50 rounded border">
      <div>
        <div className="font-mono text-sm font-semibold">{id}</div>
        {name && <div className="text-xs text-muted-foreground">{name}</div>}
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => window.open(`https://attack.mitre.org/techniques/${id.replace('T', 'T').replace('.', '/')}/`, '_blank')}
      >
        <ExternalLink className="h-3 w-3" />
      </Button>
    </div>
  )
}

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
  } catch (err) {
    console.error('Failed to copy to clipboard:', err)
  }
}

export function ThreatAnalysisDrawer({ incidentId, trigger, onAnalysisLoad }: ThreatAnalysisDrawerProps) {
  const [analysis, setAnalysis] = useState<ThreatAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copiedStates, setCopiedStates] = useState<Record<string, boolean>>({})

  const loadAnalysis = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`/api/v1/threats/analysis/${incidentId}`)
      const data = await response.json()
      
      if (data.status === 'success') {
        setAnalysis(data.data)
        onAnalysisLoad?.(data.data)
      } else {
        setError(data.message || 'Failed to load analysis')
      }
    } catch (err) {
      setError('Network error loading analysis')
      console.error('Error loading analysis:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = async (text: string, key: string) => {
    await copyToClipboard(text)
    setCopiedStates(prev => ({ ...prev, [key]: true }))
    setTimeout(() => {
      setCopiedStates(prev => ({ ...prev, [key]: false }))
    }, 2000)
  }

  const generateSlackMessage = () => {
    if (!analysis) return ''
    
    return `*Incident ${analysis.incident_id} – ${analysis.severity}*
_Root cause_: ${analysis.root_cause}
_Blast radius_: ${analysis.blast_radius}
_Remediation_: ${analysis.recommended_action}
_Gemini confidence_: ${(analysis.confidence * 100).toFixed(0)}%
_MITRE Tactics_: ${analysis.mitre_tactics.join(', ')}
_Business Impact_: ${analysis.estimated_impact}`
  }

  return (
    <Sheet>
      <SheetTrigger asChild>
        {trigger || (
          <Button variant="outline" onClick={loadAnalysis}>
            <Brain className="mr-2 h-4 w-4" />
            View Analysis
          </Button>
        )}
      </SheetTrigger>
      
      <SheetContent side="right" className="w-full sm:max-w-2xl overflow-hidden">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Threat Analysis
          </SheetTitle>
          <SheetDescription>
            AI-powered security incident analysis for {incidentId}
          </SheetDescription>
        </SheetHeader>

        <ScrollArea className="h-full pb-20">
          <div className="space-y-6 mt-6">
            {loading && (
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-center space-x-2">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                    <span>Loading analysis...</span>
                  </div>
                </CardContent>
              </Card>
            )}

            {error && (
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center space-x-2 text-red-600">
                    <XCircle className="h-5 w-5" />
                    <span>{error}</span>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={loadAnalysis}
                    className="mt-3"
                  >
                    Retry
                  </Button>
                </CardContent>
              </Card>
            )}

            {analysis && (
              <>
                {/* Summary Card */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5" />
                        Incident Summary
                      </CardTitle>
                      <SeverityBadge severity={analysis.severity} />
                    </div>
                    <CardDescription className="flex items-center gap-2 text-xs">
                      <Clock className="h-3 w-3" />
                      {new Date(analysis.analysis_timestamp).toLocaleString()}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <h4 className="font-semibold mb-2">Root Cause</h4>
                      <p className="text-sm text-muted-foreground">{analysis.root_cause}</p>
                    </div>
                    
                    <div>
                      <h4 className="font-semibold mb-2">Blast Radius</h4>
                      <p className="text-sm text-muted-foreground">{analysis.blast_radius}</p>
                    </div>
                    
                    <div>
                      <h4 className="font-semibold mb-2">Business Impact</h4>
                      <p className="text-sm text-muted-foreground">{analysis.estimated_impact}</p>
                    </div>
                    
                    <ConfidenceIndicator confidence={analysis.confidence} />
                  </CardContent>
                </Card>

                {/* Recommended Actions */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Shield className="h-5 w-5" />
                      Recommended Actions
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="p-3 bg-blue-50 border border-blue-200 rounded">
                        <h4 className="font-semibold text-blue-800 mb-1">Immediate Action</h4>
                        <p className="text-sm text-blue-700">{analysis.recommended_action}</p>
                      </div>
                      
                      <div>
                        <h4 className="font-semibold mb-2">Detailed Remediation Steps</h4>
                        <div className="space-y-2">
                          {analysis.remediation_steps.map((step, index) => (
                            <div key={index} className="flex items-start gap-2">
                              <div className="rounded-full bg-blue-100 text-blue-800 text-xs w-6 h-6 flex items-center justify-center font-semibold mt-0.5">
                                {index + 1}
                              </div>
                              <p className="text-sm text-muted-foreground flex-1">{step}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* MITRE ATT&CK Mapping */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5" />
                      MITRE ATT&CK Mapping
                    </CardTitle>
                    <CardDescription>
                      Tactics and techniques identified in this incident
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <h4 className="font-semibold mb-2">Tactics</h4>
                      <div className="flex flex-wrap gap-2">
                        {analysis.mitre_tactics.map((tactic, index) => (
                          <Badge key={index} variant="secondary" className="text-xs">
                            {tactic}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-semibold mb-2">Techniques</h4>
                      <div className="space-y-2">
                        {analysis.mitre_techniques.map((technique, index) => (
                          <MitreTechnique key={index} technique={technique} />
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Indicators of Compromise */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Zap className="h-5 w-5" />
                      Indicators of Compromise
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {analysis.indicators_of_compromise.map((ioc, index) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-yellow-50 border border-yellow-200 rounded">
                          <code className="text-sm font-mono">{ioc}</code>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleCopy(ioc, `ioc-${index}`)}
                          >
                            {copiedStates[`ioc-${index}`] ? (
                              <CheckCircle className="h-3 w-3 text-green-600" />
                            ) : (
                              <Copy className="h-3 w-3" />
                            )}
                          </Button>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Slack Notification Preview */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      💬 Slack Notification
                    </CardTitle>
                    <CardDescription>
                      Copy this formatted message for Slack notifications
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="relative">
                      <pre className="text-sm bg-slate-100 p-3 rounded border whitespace-pre-wrap">
                        {generateSlackMessage()}
                      </pre>
                      <Button
                        variant="outline"
                        size="sm"
                        className="absolute top-2 right-2"
                        onClick={() => handleCopy(generateSlackMessage(), 'slack')}
                      >
                        {copiedStates.slack ? (
                          <CheckCircle className="h-3 w-3 text-green-600" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Analysis Metadata */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Brain className="h-5 w-5" />
                      Analysis Details
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-semibold">Model:</span>
                        <div className="text-muted-foreground">{analysis.model_used}</div>
                      </div>
                      <div>
                        <span className="font-semibold">Tokens:</span>
                        <div className="text-muted-foreground">{analysis.gemini_tokens.toLocaleString()}</div>
                      </div>
                    </div>
                    
                    <Separator />
                    
                    <div>
                      <span className="font-semibold text-sm">Business Context:</span>
                      <p className="text-sm text-muted-foreground mt-1">{analysis.business_context}</p>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  )
}