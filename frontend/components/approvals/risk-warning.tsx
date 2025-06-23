'use client'

import { AlertTriangle, TrendingUp, Shield, Clock, Users, Server, DollarSign, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { RiskAssessment, RiskLevel, RiskFactor } from '@/types/approvals'

interface RiskWarningProps {
  assessment: RiskAssessment
  showDetails?: boolean
  showMitigations?: boolean
  className?: string
}

const riskLevelConfig = {
  low: {
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    progressColor: 'bg-blue-600',
    badgeVariant: 'secondary' as const
  },
  medium: {
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    progressColor: 'bg-yellow-600',
    badgeVariant: 'default' as const
  },
  high: {
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    progressColor: 'bg-orange-600',
    badgeVariant: 'default' as const
  },
  critical: {
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    progressColor: 'bg-red-600',
    badgeVariant: 'destructive' as const
  }
}

const factorIcons = {
  'User Impact': Users,
  'Service Criticality': Server,
  'Historical Performance': TrendingUp,
  'Incident History': AlertCircle,
  'Financial': DollarSign,
  'Security': Shield,
  'Time Sensitive': Clock
}

export function RiskWarning({ 
  assessment, 
  showDetails = true, 
  showMitigations = true,
  className 
}: RiskWarningProps) {
  const config = riskLevelConfig[assessment.overallRisk]

  const renderRiskFactors = () => {
    return assessment.factors.map((factor) => {
      const Icon = factorIcons[factor.category as keyof typeof factorIcons] || AlertTriangle
      const factorConfig = riskLevelConfig[factor.severity]
      
      return (
        <div key={factor.id} className="space-y-3">
          <div className="flex items-start gap-3">
            <div className={cn(
              "p-2 rounded-lg shrink-0",
              factorConfig.bgColor
            )}>
              <Icon className={cn("w-4 h-4", factorConfig.color)} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="text-sm font-medium">{factor.category}</h4>
                <Badge variant={factorConfig.badgeVariant} className="text-xs">
                  {factor.severity}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">{factor.description}</p>
              
              {factor.probability > 0 && (
                <div className="mt-2 space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Probability</span>
                    <span className={factorConfig.color}>
                      {Math.round(factor.probability * 100)}%
                    </span>
                  </div>
                  <Progress 
                    value={factor.probability * 100} 
                    className="h-1.5"
                  />
                </div>
              )}

              {factor.impact.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-medium text-muted-foreground mb-1">
                    Potential Impact:
                  </p>
                  <ul className="text-xs space-y-0.5">
                    {factor.impact.map((impact, idx) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <div className="w-1 h-1 bg-muted-foreground rounded-full mt-1.5 shrink-0" />
                        <span className="text-muted-foreground">{impact}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {showMitigations && factor.mitigations && factor.mitigations.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-medium text-green-600 mb-1">
                    Mitigation Strategies:
                  </p>
                  <ul className="text-xs space-y-0.5">
                    {factor.mitigations.map((mitigation, idx) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <Shield className="w-3 h-3 text-green-600 mt-0.5 shrink-0" />
                        <span className="text-muted-foreground">{mitigation}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )
    })
  }

  const renderImpactSummary = () => {
    const { potentialImpact } = assessment
    const impacts = []

    if (potentialImpact.users > 0) {
      impacts.push({
        icon: Users,
        label: 'Users Affected',
        value: potentialImpact.users.toLocaleString(),
        severity: potentialImpact.users > 10000 ? 'high' : 'medium'
      })
    }

    if (potentialImpact.services.length > 0) {
      impacts.push({
        icon: Server,
        label: 'Services Impacted',
        value: potentialImpact.services.length.toString(),
        severity: potentialImpact.services.length > 3 ? 'high' : 'medium'
      })
    }

    if (potentialImpact.downtime) {
      impacts.push({
        icon: Clock,
        label: 'Est. Downtime',
        value: `${potentialImpact.downtime} min`,
        severity: potentialImpact.downtime > 30 ? 'high' : 'medium'
      })
    }

    if (potentialImpact.revenue) {
      impacts.push({
        icon: DollarSign,
        label: 'Revenue at Risk',
        value: `$${potentialImpact.revenue.toLocaleString()}`,
        severity: potentialImpact.revenue > 50000 ? 'critical' : 'high'
      })
    }

    return (
      <div className="grid grid-cols-2 gap-3">
        {impacts.map((impact, idx) => {
          const Icon = impact.icon
          const impactConfig = riskLevelConfig[impact.severity as RiskLevel]
          
          return (
            <div 
              key={idx}
              className={cn(
                "p-3 rounded-lg border",
                impactConfig.borderColor,
                impactConfig.bgColor
              )}
            >
              <div className="flex items-center gap-2 mb-1">
                <Icon className={cn("w-4 h-4", impactConfig.color)} />
                <span className="text-xs font-medium text-muted-foreground">
                  {impact.label}
                </span>
              </div>
              <p className={cn("text-lg font-semibold", impactConfig.color)}>
                {impact.value}
              </p>
            </div>
          )
        })}
      </div>
    )
  }

  const renderHistoricalData = () => {
    if (!assessment.historicalData) return null

    return (
      <div className="space-y-3">
        <h4 className="text-sm font-medium">Historical Performance</h4>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Similar Actions</p>
            <p className="font-medium">{assessment.historicalData.similarActionsCount}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Success Rate</p>
            <div className="flex items-center gap-2">
              <p className="font-medium">{assessment.historicalData.successRate}%</p>
              <Progress 
                value={assessment.historicalData.successRate} 
                className="w-16 h-2"
              />
            </div>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Avg Recovery Time</p>
            <p className="font-medium">{assessment.historicalData.averageRecoveryTime} min</p>
          </div>
          {assessment.historicalData.lastIncident && (
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Last Incident</p>
              <p className="font-medium">
                {Math.floor(
                  (Date.now() - assessment.historicalData.lastIncident.getTime()) / 
                  (1000 * 60 * 60 * 24)
                )} days ago
              </p>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className={cn(
        "pb-4",
        config.bgColor,
        config.borderColor,
        "border-b"
      )}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white rounded-lg shadow-sm">
              <AlertTriangle className={cn("w-5 h-5", config.color)} />
            </div>
            <div>
              <CardTitle className="text-lg">Risk Assessment</CardTitle>
              <CardDescription>
                Overall risk score: {assessment.riskScore}/100
              </CardDescription>
            </div>
          </div>
          <Badge variant={config.badgeVariant} className="text-sm">
            {assessment.overallRisk.toUpperCase()} RISK
          </Badge>
        </div>
        <Progress 
          value={assessment.riskScore} 
          className="h-2 mt-3"
        />
      </CardHeader>
      
      <CardContent className="pt-6">
        <div className="space-y-6">
          {showDetails && (
            <>
              <div className="space-y-4">
                <h3 className="text-sm font-medium">Risk Factors</h3>
                <div className="space-y-4">
                  {renderRiskFactors()}
                </div>
              </div>

              <div className="border-t pt-6">
                <h3 className="text-sm font-medium mb-4">Impact Summary</h3>
                {renderImpactSummary()}
              </div>

              {assessment.historicalData && (
                <div className="border-t pt-6">
                  {renderHistoricalData()}
                </div>
              )}
            </>
          )}

          {!showDetails && (
            <Alert className={cn(
              "border",
              config.borderColor,
              config.bgColor
            )}>
              <AlertTriangle className={cn("h-4 w-4", config.color)} />
              <AlertTitle>Risk Level: {assessment.overallRisk.toUpperCase()}</AlertTitle>
              <AlertDescription>
                {assessment.factors.length} risk factors identified. 
                Risk score: {assessment.riskScore}/100
              </AlertDescription>
            </Alert>
          )}
        </div>
      </CardContent>
    </Card>
  )
}