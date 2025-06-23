"use client"

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { 
  AlertCircle, 
  CheckCircle, 
  Info, 
  X,
  Eye,
  EyeOff
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface AccessibilityIssue {
  id: string
  type: 'error' | 'warning' | 'info'
  level: 'A' | 'AA' | 'AAA'
  element?: string
  description: string
  recommendation: string
  wcagCriteria?: string
}

export function AccessibilityAudit() {
  const [isAuditing, setIsAuditing] = useState(false)
  const [issues, setIssues] = useState<AccessibilityIssue[]>([])
  const [showAudit, setShowAudit] = useState(false)

  const runAudit = () => {
    setIsAuditing(true)
    const foundIssues: AccessibilityIssue[] = []

    // Check for missing alt text on images
    const images = document.querySelectorAll('img:not([alt])')
    images.forEach((img, index) => {
      foundIssues.push({
        id: `img-alt-${index}`,
        type: 'error',
        level: 'A',
        element: img.outerHTML.substring(0, 100) + '...',
        description: 'Image missing alt attribute',
        recommendation: 'Add descriptive alt text to all images',
        wcagCriteria: '1.1.1 Non-text Content'
      })
    })

    // Check for missing labels on form inputs
    const inputs = document.querySelectorAll('input:not([aria-label]):not([aria-labelledby]):not([id])')
    inputs.forEach((input, index) => {
      const label = input.closest('label')
      if (!label) {
        foundIssues.push({
          id: `input-label-${index}`,
          type: 'error',
          level: 'A',
          element: input.outerHTML.substring(0, 100) + '...',
          description: 'Form input missing label',
          recommendation: 'Add a label element or aria-label attribute',
          wcagCriteria: '3.3.2 Labels or Instructions'
        })
      }
    })

    // Check for missing ARIA labels on icon buttons
    const iconButtons = document.querySelectorAll('button[class*="icon"]:not([aria-label]):not([aria-labelledby])')
    iconButtons.forEach((button, index) => {
      const hasText = button.textContent?.trim()
      if (!hasText) {
        foundIssues.push({
          id: `button-aria-${index}`,
          type: 'error',
          level: 'A',
          element: button.outerHTML.substring(0, 100) + '...',
          description: 'Icon-only button missing accessible label',
          recommendation: 'Add aria-label to describe the button action',
          wcagCriteria: '4.1.2 Name, Role, Value'
        })
      }
    })

    // Check heading hierarchy
    const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'))
    let lastLevel = 0
    headings.forEach((heading, index) => {
      const level = parseInt(heading.tagName[1])
      if (level > lastLevel + 1 && lastLevel !== 0) {
        foundIssues.push({
          id: `heading-${index}`,
          type: 'warning',
          level: 'AA',
          element: heading.outerHTML.substring(0, 100) + '...',
          description: `Heading level skipped (h${lastLevel} to h${level})`,
          recommendation: 'Maintain proper heading hierarchy',
          wcagCriteria: '1.3.1 Info and Relationships'
        })
      }
      lastLevel = level
    })

    // Check for keyboard traps
    const modals = document.querySelectorAll('[role="dialog"]')
    modals.forEach((modal, index) => {
      const focusableElements = modal.querySelectorAll(
        'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select'
      )
      if (focusableElements.length > 0) {
        foundIssues.push({
          id: `focus-trap-${index}`,
          type: 'info',
          level: 'AA',
          description: 'Modal dialog detected - ensure proper focus management',
          recommendation: 'Implement focus trap within modal when open',
          wcagCriteria: '2.1.2 No Keyboard Trap'
        })
      }
    })

    // Check color contrast (simplified check)
    const lowContrastElements = document.querySelectorAll('.text-muted-foreground')
    if (lowContrastElements.length > 0) {
      foundIssues.push({
        id: 'color-contrast',
        type: 'warning',
        level: 'AA',
        description: 'Potential low contrast text detected',
        recommendation: 'Verify text meets 4.5:1 contrast ratio (3:1 for large text)',
        wcagCriteria: '1.4.3 Contrast (Minimum)'
      })
    }

    // Check for live regions
    const liveRegions = document.querySelectorAll('[aria-live]')
    if (liveRegions.length === 0) {
      foundIssues.push({
        id: 'live-regions',
        type: 'info',
        level: 'AA',
        description: 'No ARIA live regions detected',
        recommendation: 'Add aria-live regions for dynamic content updates',
        wcagCriteria: '4.1.3 Status Messages'
      })
    }

    setIssues(foundIssues)
    setIsAuditing(false)
  }

  // Run audit on mount in development
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      setTimeout(runAudit, 1000) // Wait for page to fully load
    }
  }, [])

  if (!showAudit) {
    return (
      <Button
        onClick={() => setShowAudit(true)}
        variant="outline"
        size="sm"
        className="fixed bottom-4 right-4 z-50"
        aria-label="Show accessibility audit"
      >
        <Eye className="h-4 w-4 mr-2" />
        A11y Audit
      </Button>
    )
  }

  return (
    <Card className="fixed bottom-4 right-4 z-50 w-96 max-h-[600px] overflow-hidden flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div>
          <CardTitle className="text-lg">Accessibility Audit</CardTitle>
          <CardDescription>
            Found {issues.length} potential issues
          </CardDescription>
        </div>
        <Button
          onClick={() => setShowAudit(false)}
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          aria-label="Close accessibility audit"
        >
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto">
        <div className="space-y-4">
          <Button
            onClick={runAudit}
            disabled={isAuditing}
            className="w-full"
          >
            {isAuditing ? 'Auditing...' : 'Run Audit'}
          </Button>

          {issues.length === 0 && !isAuditing && (
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertTitle>No issues found</AlertTitle>
              <AlertDescription>
                Great job! No accessibility issues were detected.
              </AlertDescription>
            </Alert>
          )}

          {issues.map((issue) => (
            <Alert
              key={issue.id}
              className={cn(
                issue.type === 'error' && 'border-destructive',
                issue.type === 'warning' && 'border-yellow-500',
                issue.type === 'info' && 'border-blue-500'
              )}
            >
              <div className="flex items-start gap-2">
                {issue.type === 'error' && <AlertCircle className="h-4 w-4 text-destructive" />}
                {issue.type === 'warning' && <AlertCircle className="h-4 w-4 text-yellow-500" />}
                {issue.type === 'info' && <Info className="h-4 w-4 text-blue-500" />}
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <AlertTitle className="text-sm">{issue.description}</AlertTitle>
                    <Badge variant="outline" className="text-xs">
                      WCAG {issue.level}
                    </Badge>
                  </div>
                  <AlertDescription className="text-xs">
                    {issue.recommendation}
                    {issue.wcagCriteria && (
                      <span className="block mt-1 text-muted-foreground">
                        Criteria: {issue.wcagCriteria}
                      </span>
                    )}
                  </AlertDescription>
                  {issue.element && (
                    <pre className="text-xs bg-muted p-2 rounded mt-2 overflow-x-auto">
                      <code>{issue.element}</code>
                    </pre>
                  )}
                </div>
              </div>
            </Alert>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}