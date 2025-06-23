'use client'

import { useState } from 'react'
import { AlertTriangle, ShieldAlert, Info, AlertCircle, Lock, Check } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { 
  RiskLevel, 
  ConfirmationMethod,
  ConfirmationDialogConfig,
  RiskAssessment 
} from '@/types/approvals'

interface ConfirmationDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  config: ConfirmationDialogConfig
  riskAssessment?: RiskAssessment
  onConfirm: (confirmationData?: any) => void
  onCancel: () => void
  loading?: boolean
}

const riskLevelConfig = {
  low: {
    icon: Info,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    badgeVariant: 'secondary' as const,
    title: 'Low Risk Action'
  },
  medium: {
    icon: AlertCircle,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    badgeVariant: 'default' as const,
    title: 'Medium Risk Action'
  },
  high: {
    icon: AlertTriangle,
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    badgeVariant: 'default' as const,
    title: 'High Risk Action'
  },
  critical: {
    icon: ShieldAlert,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    badgeVariant: 'destructive' as const,
    title: 'Critical Risk Action'
  }
}

export function ConfirmationDialog({
  open,
  onOpenChange,
  config,
  riskAssessment,
  onConfirm,
  onCancel,
  loading = false
}: ConfirmationDialogProps) {
  const [confirmationData, setConfirmationData] = useState<any>({})
  const [isValid, setIsValid] = useState(false)

  const riskConfig = riskLevelConfig[config.riskLevel]
  const Icon = riskConfig.icon

  const handleConfirmationMethodChange = (value: any) => {
    setConfirmationData(value)
    
    // Validate based on confirmation method
    switch (config.confirmationMethod) {
      case 'checkbox':
        setIsValid(value.acknowledged === true)
        break
      case 'text_input':
        setIsValid(
          config.confirmationPattern
            ? new RegExp(config.confirmationPattern).test(value.confirmationText || '')
            : (value.confirmationText || '').length > 0
        )
        break
      case 'mfa':
        setIsValid((value.mfaCode || '').length === 6)
        break
      default:
        setIsValid(true)
    }
  }

  const renderConfirmationMethod = () => {
    switch (config.confirmationMethod) {
      case 'checkbox':
        return (
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <Checkbox
                id="acknowledge"
                checked={confirmationData.acknowledged || false}
                onCheckedChange={(checked) => 
                  handleConfirmationMethodChange({ ...confirmationData, acknowledged: checked })
                }
              />
              <Label 
                htmlFor="acknowledge" 
                className="text-sm font-normal cursor-pointer"
              >
                I understand the risks and want to proceed with this action
              </Label>
            </div>
          </div>
        )

      case 'text_input':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="confirmation-text">
                {config.confirmationPrompt || 'Type the action name to confirm'}
              </Label>
              <Input
                id="confirmation-text"
                type="text"
                placeholder={config.confirmationPattern?.toString() || 'Enter confirmation'}
                value={confirmationData.confirmationText || ''}
                onChange={(e) => 
                  handleConfirmationMethodChange({ ...confirmationData, confirmationText: e.target.value })
                }
                className="mt-2"
              />
            </div>
          </div>
        )

      case 'mfa':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="mfa-code" className="flex items-center gap-2">
                <Lock className="w-4 h-4" />
                Enter your 6-digit MFA code
              </Label>
              <Input
                id="mfa-code"
                type="text"
                placeholder="000000"
                maxLength={6}
                value={confirmationData.mfaCode || ''}
                onChange={(e) => 
                  handleConfirmationMethodChange({ ...confirmationData, mfaCode: e.target.value })
                }
                className="mt-2 font-mono text-center text-lg"
              />
            </div>
          </div>
        )

      case 'manager_approval':
        return (
          <Alert className="border-blue-200 bg-blue-50">
            <Info className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800">
              This action requires manager approval. A request has been sent to your manager.
              You will be notified once approved.
            </AlertDescription>
          </Alert>
        )

      default:
        return null
    }
  }

  const renderImpactSummary = () => {
    if (!config.showImpactSummary || !riskAssessment) return null

    return (
      <div className="space-y-3">
        <h4 className="text-sm font-medium">Potential Impact</h4>
        <div className="grid grid-cols-2 gap-3 text-sm">
          {riskAssessment.potentialImpact.users > 0 && (
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-yellow-500 rounded-full" />
              <span className="text-muted-foreground">
                {riskAssessment.potentialImpact.users.toLocaleString()} users affected
              </span>
            </div>
          )}
          {riskAssessment.potentialImpact.services.length > 0 && (
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-orange-500 rounded-full" />
              <span className="text-muted-foreground">
                {riskAssessment.potentialImpact.services.length} services impacted
              </span>
            </div>
          )}
          {riskAssessment.potentialImpact.downtime && (
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-red-500 rounded-full" />
              <span className="text-muted-foreground">
                ~{riskAssessment.potentialImpact.downtime} min downtime
              </span>
            </div>
          )}
          {riskAssessment.potentialImpact.revenue && (
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full" />
              <span className="text-muted-foreground">
                ${riskAssessment.potentialImpact.revenue.toLocaleString()} at risk
              </span>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className={cn(
              "p-2 rounded-lg",
              riskConfig.bgColor
            )}>
              <Icon className={cn("w-5 h-5", riskConfig.color)} />
            </div>
            <div className="flex-1">
              <DialogTitle className="flex items-center gap-2">
                {config.title}
                <Badge variant={riskConfig.badgeVariant}>
                  {config.riskLevel.toUpperCase()} RISK
                </Badge>
              </DialogTitle>
            </div>
          </div>
          <DialogDescription className="mt-3">
            {config.message}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {config.showRiskAssessment && riskAssessment && (
            <Alert className={cn(
              "border",
              riskConfig.borderColor,
              riskConfig.bgColor
            )}>
              <Icon className={cn("h-4 w-4", riskConfig.color)} />
              <AlertDescription className={riskConfig.color}>
                <strong>Risk Score: {riskAssessment.riskScore}/100</strong>
                <br />
                {riskAssessment.factors.length} risk factors identified
              </AlertDescription>
            </Alert>
          )}

          {renderImpactSummary()}

          <div className="border-t pt-4">
            {renderConfirmationMethod()}
          </div>

          {config.requireExplicitConsent && config.confirmationMethod !== 'checkbox' && (
            <div className="flex items-start space-x-3">
              <Checkbox
                id="explicit-consent"
                checked={confirmationData.explicitConsent || false}
                onCheckedChange={(checked) => 
                  handleConfirmationMethodChange({ ...confirmationData, explicitConsent: checked })
                }
              />
              <Label 
                htmlFor="explicit-consent" 
                className="text-sm font-normal cursor-pointer"
              >
                I acknowledge the risks and take full responsibility for this action
              </Label>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            variant={config.riskLevel === 'critical' ? 'destructive' : 'default'}
            onClick={() => onConfirm(confirmationData)}
            disabled={!isValid || loading}
            className="min-w-[100px]"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Processing...
              </>
            ) : (
              <>
                <Check className="w-4 h-4 mr-2" />
                Confirm Action
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}