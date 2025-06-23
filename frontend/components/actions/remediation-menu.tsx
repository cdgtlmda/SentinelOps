'use client'

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  RefreshCw,
  Scale,
  RotateCcw,
  Trash2,
  Key,
  FileCode,
  Server,
  Zap,
  AlertTriangle,
  Clock,
  CheckCircle
} from 'lucide-react'
import { RemediationOption, RemediationType } from '@/types/actions'
import { cn } from '@/lib/utils'

interface RemediationMenuProps {
  open: boolean
  onClose: () => void
  incidentIds: string[]
  onRemediate: (option: RemediationOption) => Promise<void>
}

const remediationIcons: Record<RemediationType, any> = {
  restart_service: RefreshCw,
  scale_resources: Scale,
  rollback_deployment: RotateCcw,
  clear_cache: Trash2,
  rotate_credentials: Key,
  apply_patch: FileCode,
  failover: Server,
  custom_script: Zap
}

const mockRemediations: RemediationOption[] = [
  {
    id: '1',
    type: 'restart_service',
    name: 'Restart Service',
    description: 'Restart the affected service to clear any stuck processes',
    riskLevel: 'low',
    estimatedDuration: 30,
    requiresApproval: false,
    automatable: true,
    impacts: ['Service will be briefly unavailable'],
    rollbackable: false,
    successRate: 95
  },
  {
    id: '2',
    type: 'scale_resources',
    name: 'Scale Up Resources',
    description: 'Increase compute resources to handle load',
    riskLevel: 'low',
    estimatedDuration: 120,
    requiresApproval: false,
    automatable: true,
    impacts: ['Increased costs'],
    rollbackable: true,
    successRate: 98
  },
  {
    id: '3',
    type: 'rollback_deployment',
    name: 'Rollback Deployment',
    description: 'Revert to the previous stable version',
    riskLevel: 'medium',
    estimatedDuration: 300,
    requiresApproval: true,
    automatable: true,
    impacts: ['Recent features will be unavailable'],
    rollbackable: false,
    successRate: 92
  },
  {
    id: '4',
    type: 'rotate_credentials',
    name: 'Rotate Credentials',
    description: 'Generate new API keys and update all services',
    riskLevel: 'high',
    estimatedDuration: 600,
    requiresApproval: true,
    automatable: false,
    impacts: ['All clients must update their credentials'],
    rollbackable: false,
    successRate: 88
  }
]

export function RemediationMenu({
  open,
  onClose,
  incidentIds,
  onRemediate
}: RemediationMenuProps) {
  const [selectedOption, setSelectedOption] = useState<RemediationOption | null>(null)
  const [autoExecute, setAutoExecute] = useState(true)
  const [isLoading, setIsLoading] = useState(false)

  const handleRemediate = async () => {
    if (!selectedOption) return

    setIsLoading(true)
    try {
      await onRemediate(selectedOption)
      onClose()
    } finally {
      setIsLoading(false)
    }
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 dark:text-green-400'
      case 'medium': return 'text-yellow-600 dark:text-yellow-400'
      case 'high': return 'text-red-600 dark:text-red-400'
      case 'critical': return 'text-red-800 dark:text-red-300'
      default: return 'text-gray-600 dark:text-gray-400'
    }
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Select Remediation Action</DialogTitle>
          <DialogDescription>
            Choose a remediation action for {incidentIds.length} selected incident{incidentIds.length > 1 ? 's' : ''}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <Select
            value={selectedOption?.id}
            onValueChange={(id) => setSelectedOption(mockRemediations.find(r => r.id === id) || null)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select a remediation action" />
            </SelectTrigger>
            <SelectContent>
              {mockRemediations.map((option) => {
                const Icon = remediationIcons[option.type]
                return (
                  <SelectItem key={option.id} value={option.id}>
                    <div className="flex items-center gap-2">
                      <Icon className="h-4 w-4" />
                      <span>{option.name}</span>
                      <span className={cn('text-xs', getRiskColor(option.riskLevel))}>
                        ({option.riskLevel} risk)
                      </span>
                    </div>
                  </SelectItem>
                )
              })}
            </SelectContent>
          </Select>

          {selectedOption && (
            <div className="space-y-4 p-4 bg-secondary/50 rounded-lg">
              <div>
                <h4 className="font-medium mb-1">{selectedOption.name}</h4>
                <p className="text-sm text-muted-foreground">{selectedOption.description}</p>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <AlertTriangle className={cn('h-4 w-4', getRiskColor(selectedOption.riskLevel))} />
                  <span>Risk Level: <strong className={getRiskColor(selectedOption.riskLevel)}>
                    {selectedOption.riskLevel}
                  </strong></span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span>Duration: <strong>{selectedOption.estimatedDuration}s</strong></span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
                  <span>Success Rate: <strong>{selectedOption.successRate}%</strong></span>
                </div>
                <div className="flex items-center gap-2">
                  <RotateCcw className="h-4 w-4 text-muted-foreground" />
                  <span>Rollbackable: <strong>{selectedOption.rollbackable ? 'Yes' : 'No'}</strong></span>
                </div>
              </div>

              {selectedOption.impacts && selectedOption.impacts.length > 0 && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Impacts:</strong>
                    <ul className="mt-1 ml-4 list-disc">
                      {selectedOption.impacts.map((impact, i) => (
                        <li key={i}>{impact}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </Alert>
              )}

              {selectedOption.automatable && (
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="auto-execute"
                    checked={autoExecute}
                    onCheckedChange={(checked) => setAutoExecute(checked as boolean)}
                  />
                  <label
                    htmlFor="auto-execute"
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    Execute automatically
                  </label>
                </div>
              )}

              {selectedOption.requiresApproval && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    This action requires approval from a team lead or manager
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleRemediate}
            disabled={!selectedOption || isLoading}
            variant={selectedOption?.riskLevel === 'high' ? 'destructive' : 'default'}
          >
            {isLoading ? 'Executing...' : 'Execute Remediation'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}