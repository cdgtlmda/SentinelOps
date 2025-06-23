'use client'

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Checkbox } from '@/components/ui/checkbox'
import {
  User,
  Users,
  Mail,
  Phone,
  Clock,
  AlertCircle,
  FileText,
  Paperclip
} from 'lucide-react'
import { EscalationRecipient, EscalationRequest } from '@/types/actions'
import { cn } from '@/lib/utils'

interface EscalationDialogProps {
  open: boolean
  onClose: () => void
  incidentIds: string[]
  onEscalate: (request: Partial<EscalationRequest>) => Promise<void>
}

const mockRecipients: EscalationRecipient[] = [
  {
    id: '1',
    type: 'team',
    name: 'Security Operations Team',
    email: 'secops@company.com',
    level: 'team_lead',
    available: true,
    responseTime: 15,
    expertise: ['security', 'incident-response']
  },
  {
    id: '2',
    type: 'individual',
    name: 'John Smith',
    email: 'john.smith@company.com',
    phone: '+1-555-0123',
    level: 'manager',
    available: true,
    responseTime: 30,
    expertise: ['infrastructure', 'cloud'],
    preferredContactMethod: 'email'
  },
  {
    id: '3',
    type: 'team',
    name: 'Infrastructure Team',
    email: 'infra@company.com',
    level: 'on_call',
    available: true,
    responseTime: 10,
    expertise: ['infrastructure', 'networking']
  },
  {
    id: '4',
    type: 'individual',
    name: 'Sarah Johnson',
    email: 'sarah.johnson@company.com',
    level: 'director',
    available: false,
    responseTime: 60,
    expertise: ['management', 'compliance']
  }
]

const templates = [
  { id: 'critical', name: 'Critical Incident', message: 'Critical incident requiring immediate attention. Multiple systems affected.' },
  { id: 'security', name: 'Security Breach', message: 'Potential security breach detected. Immediate investigation required.' },
  { id: 'performance', name: 'Performance Degradation', message: 'Significant performance degradation affecting user experience.' },
  { id: 'custom', name: 'Custom Message', message: '' }
]

export function EscalationDialog({
  open,
  onClose,
  incidentIds,
  onEscalate
}: EscalationDialogProps) {
  const [selectedRecipients, setSelectedRecipients] = useState<string[]>([])
  const [priority, setPriority] = useState<'low' | 'medium' | 'high' | 'urgent'>('high')
  const [selectedTemplate, setSelectedTemplate] = useState('custom')
  const [message, setMessage] = useState('')
  const [includeDetails, setIncludeDetails] = useState(true)
  const [isLoading, setIsLoading] = useState(false)

  const handleTemplateChange = (templateId: string) => {
    setSelectedTemplate(templateId)
    const template = templates.find(t => t.id === templateId)
    if (template && template.message) {
      setMessage(template.message)
    }
  }

  const handleEscalate = async () => {
    if (selectedRecipients.length === 0 || !message.trim()) return

    setIsLoading(true)
    try {
      await onEscalate({
        incidentId: incidentIds[0], // For now, handle first incident
        recipients: selectedRecipients.map(id => mockRecipients.find(r => r.id === id)!),
        priority,
        subject: `Escalation: ${incidentIds.length} incident(s) require attention`,
        message: includeDetails 
          ? `${message}\n\nIncident IDs: ${incidentIds.join(', ')}`
          : message,
        template: selectedTemplate
      })
      onClose()
    } finally {
      setIsLoading(false)
    }
  }

  const toggleRecipient = (recipientId: string) => {
    setSelectedRecipients(prev =>
      prev.includes(recipientId)
        ? prev.filter(id => id !== recipientId)
        : [...prev, recipientId]
    )
  }

  const getPriorityColor = (p: string) => {
    switch (p) {
      case 'low': return 'text-blue-600 dark:text-blue-400'
      case 'medium': return 'text-yellow-600 dark:text-yellow-400'
      case 'high': return 'text-orange-600 dark:text-orange-400'
      case 'urgent': return 'text-red-600 dark:text-red-400'
      default: return 'text-gray-600 dark:text-gray-400'
    }
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Escalate Incident</DialogTitle>
          <DialogDescription>
            Escalate {incidentIds.length} incident{incidentIds.length > 1 ? 's' : ''} to the appropriate team or individual
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Recipients */}
          <div className="space-y-3">
            <Label>Select Recipients</Label>
            <div className="grid gap-2">
              {mockRecipients.map((recipient) => (
                <div
                  key={recipient.id}
                  className={cn(
                    'flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors',
                    selectedRecipients.includes(recipient.id)
                      ? 'bg-primary/10 border-primary'
                      : 'hover:bg-secondary/50',
                    !recipient.available && 'opacity-60'
                  )}
                  onClick={() => toggleRecipient(recipient.id)}
                >
                  <div className="flex items-center gap-3">
                    <Checkbox
                      checked={selectedRecipients.includes(recipient.id)}
                      onCheckedChange={() => toggleRecipient(recipient.id)}
                    />
                    {recipient.type === 'team' ? (
                      <Users className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <User className="h-4 w-4 text-muted-foreground" />
                    )}
                    <div>
                      <p className="font-medium">{recipient.name}</p>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Mail className="h-3 w-3" />
                          {recipient.email}
                        </span>
                        {recipient.phone && (
                          <span className="flex items-center gap-1">
                            <Phone className="h-3 w-3" />
                            {recipient.phone}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="text-right text-sm">
                    <p className={cn(
                      'font-medium',
                      recipient.available ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                    )}>
                      {recipient.available ? 'Available' : 'Unavailable'}
                    </p>
                    <p className="text-xs text-muted-foreground flex items-center gap-1 justify-end">
                      <Clock className="h-3 w-3" />
                      ~{recipient.responseTime}m response
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Priority */}
          <div className="space-y-2">
            <Label htmlFor="priority">Priority</Label>
            <Select value={priority} onValueChange={(v: any) => setPriority(v)}>
              <SelectTrigger id="priority">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">
                  <span className={getPriorityColor('low')}>Low</span>
                </SelectItem>
                <SelectItem value="medium">
                  <span className={getPriorityColor('medium')}>Medium</span>
                </SelectItem>
                <SelectItem value="high">
                  <span className={getPriorityColor('high')}>High</span>
                </SelectItem>
                <SelectItem value="urgent">
                  <span className={getPriorityColor('urgent')}>Urgent</span>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Template */}
          <div className="space-y-2">
            <Label htmlFor="template">Message Template</Label>
            <Select value={selectedTemplate} onValueChange={handleTemplateChange}>
              <SelectTrigger id="template">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {templates.map((template) => (
                  <SelectItem key={template.id} value={template.id}>
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      {template.name}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Message */}
          <div className="space-y-2">
            <Label htmlFor="message">Message</Label>
            <Textarea
              id="message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Describe the incident and why escalation is needed..."
              rows={4}
              className="resize-none"
            />
          </div>

          {/* Options */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="include-details"
                checked={includeDetails}
                onCheckedChange={(checked) => setIncludeDetails(checked as boolean)}
              />
              <label
                htmlFor="include-details"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                Include incident details in message
              </label>
            </div>

            <Button variant="ghost" size="sm" className="w-full justify-start">
              <Paperclip className="h-4 w-4 mr-2" />
              Attach files (coming soon)
            </Button>
          </div>

          {selectedRecipients.length === 0 && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Please select at least one recipient
              </AlertDescription>
            </Alert>
          )}
        </div>

        <div className="flex justify-end gap-2 mt-6">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleEscalate}
            disabled={selectedRecipients.length === 0 || !message.trim() || isLoading}
            variant={priority === 'urgent' ? 'destructive' : 'default'}
          >
            {isLoading ? 'Escalating...' : 'Escalate'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}