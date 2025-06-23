'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { ColorContrastChecker } from '@/components/accessibility/color-contrast-checker'
import { AccessibilityToolbar } from '@/components/accessibility/accessibility-toolbar'
import { LandmarkNavigator } from '@/components/accessibility/landmark-navigator'
import { validateAccessibility, ValidationResult } from '@/lib/accessibility/wcag-validator'
import { 
  AccessibleFormField, 
  FormFieldset, 
  FormErrorSummary,
  RequiredFieldIndicator,
  AccessibleRadioGroup,
  AccessibleTable,
  ScreenReaderOnly,
  StatusAnnouncer
} from '@/components/accessibility'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  FileText, 
  RefreshCw,
  Download,
  Search,
  Filter
} from 'lucide-react'

export default function AccessibilityAuditPage() {
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null)
  const [isValidating, setIsValidating] = useState(false)
  const [filterType, setFilterType] = useState<'all' | 'violations' | 'warnings'>('all')
  const [searchTerm, setSearchTerm] = useState('')

  const runValidation = async () => {
    setIsValidating(true)
    
    // Small delay to show loading state
    await new Promise(resolve => setTimeout(resolve, 500))
    
    const result = validateAccessibility()
    setValidationResult(result)
    setIsValidating(false)
  }

  useEffect(() => {
    // Run initial validation
    runValidation()
  }, [])

  const exportReport = () => {
    if (!validationResult) return

    const report = {
      timestamp: new Date().toISOString(),
      summary: validationResult.summary,
      violations: validationResult.violations,
      warnings: validationResult.warnings,
    }

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `accessibility-audit-${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const filteredItems = validationResult ? [
    ...(filterType === 'all' || filterType === 'violations' 
      ? validationResult.violations.map(v => ({ ...v, itemType: 'violation' as const }))
      : []),
    ...(filterType === 'all' || filterType === 'warnings'
      ? validationResult.warnings.map(w => ({ ...w, itemType: 'warning' as const }))
      : [])
  ].filter(item => 
    searchTerm === '' || 
    item.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.type.toLowerCase().includes(searchTerm.toLowerCase())
  ) : []

  return (
    <main className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Accessibility Audit</h1>
          <p className="text-muted-foreground mt-2">
            Comprehensive WCAG 2.1 compliance testing and validation
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={runValidation}
            disabled={isValidating}
            variant="outline"
          >
            {isValidating ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Validating...
              </>
            ) : (
              <>
                <RefreshCw className="mr-2 h-4 w-4" />
                Re-run Audit
              </>
            )}
          </Button>
          <Button
            onClick={exportReport}
            disabled={!validationResult}
            variant="outline"
          >
            <Download className="mr-2 h-4 w-4" />
            Export Report
          </Button>
        </div>
      </header>

      {/* Summary Cards */}
      {validationResult && (
        <section aria-labelledby="summary-heading" className="grid gap-4 md:grid-cols-4">
          <ScreenReaderOnly>
            <h2 id="summary-heading">Audit Summary</h2>
          </ScreenReaderOnly>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Overall Status</CardTitle>
              {validationResult.passed ? (
                <CheckCircle2 className="h-4 w-4 text-green-600" />
              ) : (
                <XCircle className="h-4 w-4 text-red-600" />
              )}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {validationResult.passed ? 'Passed' : 'Failed'}
              </div>
              <p className="text-xs text-muted-foreground">
                WCAG 2.1 Compliance
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Issues</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{validationResult.summary.total}</div>
              <p className="text-xs text-muted-foreground">
                Found in audit
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Violations</CardTitle>
              <XCircle className="h-4 w-4 text-red-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {validationResult.summary.failed}
              </div>
              <p className="text-xs text-muted-foreground">
                Must be fixed
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Warnings</CardTitle>
              <AlertTriangle className="h-4 w-4 text-amber-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-amber-600">
                {validationResult.summary.warnings}
              </div>
              <p className="text-xs text-muted-foreground">
                Should be reviewed
              </p>
            </CardContent>
          </Card>
        </section>
      )}

      {/* Main Content */}
      <Tabs defaultValue="audit" className="space-y-4">
        <TabsList>
          <TabsTrigger value="audit">Audit Results</TabsTrigger>
          <TabsTrigger value="contrast">Color Contrast</TabsTrigger>
          <TabsTrigger value="forms">Form Examples</TabsTrigger>
          <TabsTrigger value="tables">Table Examples</TabsTrigger>
          <TabsTrigger value="toolbar">Accessibility Settings</TabsTrigger>
          <TabsTrigger value="guidelines">WCAG Guidelines</TabsTrigger>
        </TabsList>

        <TabsContent value="audit" className="space-y-4">
          {validationResult && (
            <>
              {/* Filters */}
              <div className="flex gap-4 items-center">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="Search issues..."
                    className="w-full pl-10 pr-4 py-2 border rounded-md"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <div className="flex gap-2">
                  <Button
                    variant={filterType === 'all' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFilterType('all')}
                  >
                    All ({validationResult.summary.total})
                  </Button>
                  <Button
                    variant={filterType === 'violations' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFilterType('violations')}
                  >
                    Violations ({validationResult.summary.failed})
                  </Button>
                  <Button
                    variant={filterType === 'warnings' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFilterType('warnings')}
                  >
                    Warnings ({validationResult.summary.warnings})
                  </Button>
                </div>
              </div>

              {/* Results List */}
              <ScrollArea className="h-[600px] rounded-md border">
                <div className="p-4 space-y-4">
                  {filteredItems.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      {searchTerm ? 'No issues match your search' : 'No issues found'}
                    </div>
                  ) : (
                    filteredItems.map((item, index) => (
                      <Card key={index} className={
                        item.itemType === 'violation' 
                          ? 'border-red-200 dark:border-red-900'
                          : 'border-amber-200 dark:border-amber-900'
                      }>
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <div className="space-y-1">
                              <CardTitle className="text-base flex items-center gap-2">
                                {item.itemType === 'violation' ? (
                                  <XCircle className="h-4 w-4 text-red-600" />
                                ) : (
                                  <AlertTriangle className="h-4 w-4 text-amber-600" />
                                )}
                                {item.type.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                              </CardTitle>
                              {item.selector && (
                                <code className="text-xs bg-muted px-2 py-1 rounded">
                                  {item.selector}
                                </code>
                              )}
                            </div>
                            {item.itemType === 'violation' && (
                              <Badge variant="destructive">
                                {(item as any).severity}
                              </Badge>
                            )}
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-2">
                          <p className="text-sm">{item.message}</p>
                          {item.itemType === 'violation' && (
                            <>
                              <div className="text-sm">
                                <span className="font-medium">WCAG Criteria:</span>{' '}
                                <span className="text-muted-foreground">
                                  {(item as any).wcagCriteria}
                                </span>
                              </div>
                              <Alert>
                                <AlertTitle className="text-sm">How to Fix</AlertTitle>
                                <AlertDescription className="text-sm">
                                  {(item as any).howToFix}
                                </AlertDescription>
                              </Alert>
                            </>
                          )}
                          {item.itemType === 'warning' && (
                            <Alert className="border-amber-200 dark:border-amber-900">
                              <AlertTriangle className="h-4 w-4" />
                              <AlertTitle className="text-sm">Recommendation</AlertTitle>
                              <AlertDescription className="text-sm">
                                {(item as any).recommendation}
                              </AlertDescription>
                            </Alert>
                          )}
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              </ScrollArea>
            </>
          )}
        </TabsContent>

        <TabsContent value="contrast">
          <ColorContrastChecker />
        </TabsContent>

        <TabsContent value="forms" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Accessible Form Components</CardTitle>
              <CardDescription>
                Examples of our accessible form components with proper labeling, error handling, and screen reader support.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <RequiredFieldIndicator />
              
              <FormFieldset legend="Contact Information">
                <AccessibleFormField
                  label="Full Name"
                  description="Enter your first and last name"
                  required
                >
                  <Input type="text" placeholder="John Doe" />
                </AccessibleFormField>
                
                <AccessibleFormField
                  label="Email Address"
                  description="We'll use this to contact you"
                  required
                  error="Please enter a valid email address"
                >
                  <Input type="email" placeholder="john@example.com" />
                </AccessibleFormField>
                
                <AccessibleFormField
                  label="Message"
                  description="Tell us how we can help"
                  srInstructions="Maximum 500 characters. Be specific about your issue."
                >
                  <Textarea placeholder="Describe your issue..." rows={4} />
                </AccessibleFormField>
              </FormFieldset>
              
              <AccessibleRadioGroup
                legend="Incident Severity"
                name="severity"
                options={[
                  { value: 'critical', label: 'Critical', description: 'System is completely down' },
                  { value: 'high', label: 'High', description: 'Major functionality affected' },
                  { value: 'medium', label: 'Medium', description: 'Some features impacted' },
                  { value: 'low', label: 'Low', description: 'Minor inconvenience' }
                ]}
                required
              />
              
              <FormErrorSummary
                errors={[
                  { field: 'Email', message: 'Please enter a valid email address', fieldId: 'email-field' },
                  { field: 'Severity', message: 'Please select incident severity', fieldId: 'severity-field' }
                ]}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tables" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Accessible Table Components</CardTitle>
              <CardDescription>
                Examples of accessible tables with proper captions, headers, and navigation announcements.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AccessibleTable
                caption="Recent Security Incidents"
                summary="Table showing the 5 most recent security incidents with their status and severity"
                columns={[
                  { key: 'id', header: 'ID', sortable: true },
                  { key: 'title', header: 'Title', sortable: true },
                  { key: 'severity', header: 'Severity', sortable: true },
                  { key: 'status', header: 'Status' },
                  { key: 'date', header: 'Date', sortable: true, align: 'right' }
                ]}
                data={[
                  { id: 'INC-001', title: 'Unauthorized access attempt', severity: 'High', status: 'Resolved', date: '2024-01-15' },
                  { id: 'INC-002', title: 'DDoS attack detected', severity: 'Critical', status: 'Investigating', date: '2024-01-14' },
                  { id: 'INC-003', title: 'Suspicious login activity', severity: 'Medium', status: 'Acknowledged', date: '2024-01-13' },
                  { id: 'INC-004', title: 'Malware detected on endpoint', severity: 'High', status: 'Remediated', date: '2024-01-12' },
                  { id: 'INC-005', title: 'Policy violation', severity: 'Low', status: 'Closed', date: '2024-01-11' }
                ]}
                showRowNumbers
                rowHeaderField="id"
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="toolbar">
          <Card>
            <CardHeader>
              <CardTitle>Accessibility Toolbar Demo</CardTitle>
              <CardDescription>
                The accessibility toolbar is available on all pages. Click the settings icon in the 
                bottom-right corner to access accessibility options.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Alert>
                  <AlertTitle>Features Available</AlertTitle>
                  <AlertDescription>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>Adjustable font size (50% - 200%)</li>
                      <li>High contrast mode toggle</li>
                      <li>Reduced motion for animations</li>
                      <li>Enhanced focus indicators</li>
                      <li>Screen reader announcement controls</li>
                      <li>Keyboard navigation shortcuts</li>
                    </ul>
                  </AlertDescription>
                </Alert>
                <p className="text-sm text-muted-foreground">
                  Settings are automatically saved and persist across sessions.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="guidelines">
          <div className="grid gap-4">
            <Card>
              <CardHeader>
                <CardTitle>WCAG 2.1 Guidelines Overview</CardTitle>
                <CardDescription>
                  Web Content Accessibility Guidelines (WCAG) 2.1 covers a wide range of 
                  recommendations for making Web content more accessible.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-2">1. Perceivable</h3>
                    <p className="text-sm text-muted-foreground">
                      Information and user interface components must be presentable to users 
                      in ways they can perceive.
                    </p>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">2. Operable</h3>
                    <p className="text-sm text-muted-foreground">
                      User interface components and navigation must be operable.
                    </p>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">3. Understandable</h3>
                    <p className="text-sm text-muted-foreground">
                      Information and the operation of user interface must be understandable.
                    </p>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">4. Robust</h3>
                    <p className="text-sm text-muted-foreground">
                      Content must be robust enough that it can be interpreted reliably by a 
                      wide variety of user agents, including assistive technologies.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Conformance Levels</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-start gap-3">
                  <Badge className="mt-0.5">A</Badge>
                  <div>
                    <p className="font-medium">Level A (Minimum)</p>
                    <p className="text-sm text-muted-foreground">
                      The most basic web accessibility features
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Badge className="mt-0.5">AA</Badge>
                  <div>
                    <p className="font-medium">Level AA (Recommended)</p>
                    <p className="text-sm text-muted-foreground">
                      Deals with the biggest and most common barriers for disabled users
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Badge className="mt-0.5">AAA</Badge>
                  <div>
                    <p className="font-medium">Level AAA (Enhanced)</p>
                    <p className="text-sm text-muted-foreground">
                      The highest and most complex level of web accessibility
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Accessibility Toolbar */}
      <AccessibilityToolbar />
      
      {/* Landmark Navigator (Dev Mode) */}
      <LandmarkNavigator showVisualIndicator={true} />
    </main>
  )
}