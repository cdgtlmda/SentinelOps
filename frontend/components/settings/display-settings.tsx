"use client"

import { useState } from 'react'
import { useUserPreferencesStore, useUIStore } from '@/store'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Button } from '@/components/ui/button'
import { 
  Layout, 
  Grid3x3, 
  List, 
  Eye, 
  EyeOff, 
  RefreshCw,
  BarChart3,
  Palette,
  Settings2
} from 'lucide-react'

interface WidgetVisibility {
  incidentTrends: boolean
  agentStatus: boolean
  responseMetrics: boolean
  threatDistribution: boolean
  realtimeActivity: boolean
  resourceUsage: boolean
}

interface ChartPreferences {
  defaultChartType: 'line' | 'bar' | 'area' | 'pie'
  showDataLabels: boolean
  animateCharts: boolean
  colorPalette: 'default' | 'colorblind' | 'highContrast' | 'custom'
}

export default function DisplaySettings() {
  const { dashboard, updateDashboardPreferences } = useUserPreferencesStore()
  const { dashboardLayout, setDashboardLayout, incidentViewMode, setIncidentViewMode } = useUIStore()
  
  const [widgetVisibility, setWidgetVisibility] = useState<WidgetVisibility>({
    incidentTrends: true,
    agentStatus: true,
    responseMetrics: true,
    threatDistribution: true,
    realtimeActivity: true,
    resourceUsage: true,
  })

  const [chartPreferences, setChartPreferences] = useState<ChartPreferences>({
    defaultChartType: 'line',
    showDataLabels: false,
    animateCharts: true,
    colorPalette: 'default',
  })

  const [autoRefresh, setAutoRefresh] = useState(true)
  const [compactTables, setCompactTables] = useState(false)
  const [showGridLines, setShowGridLines] = useState(true)

  const refreshIntervals = [
    { value: 10, label: '10 seconds' },
    { value: 30, label: '30 seconds' },
    { value: 60, label: '1 minute' },
    { value: 300, label: '5 minutes' },
    { value: 600, label: '10 minutes' },
  ]

  const toggleWidget = (widget: keyof WidgetVisibility) => {
    setWidgetVisibility(prev => ({
      ...prev,
      [widget]: !prev[widget]
    }))
  }

  return (
    <div className="space-y-6">
      {/* Dashboard Layout */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layout className="w-5 h-5" />
            Dashboard Layout
          </CardTitle>
          <CardDescription>
            Configure how information is displayed on your dashboard
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Layout Type */}
          <div className="space-y-3">
            <Label>Layout Type</Label>
            <RadioGroup value={dashboardLayout} onValueChange={(value: any) => setDashboardLayout(value)}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="grid" id="grid-layout" />
                <Label htmlFor="grid-layout" className="flex items-center gap-2 cursor-pointer">
                  <Grid3x3 className="w-4 h-4" />
                  Grid View - Cards arranged in a responsive grid
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="list" id="list-layout" />
                <Label htmlFor="list-layout" className="flex items-center gap-2 cursor-pointer">
                  <List className="w-4 h-4" />
                  List View - Linear arrangement with more details
                </Label>
              </div>
            </RadioGroup>
          </div>

          {/* Default View */}
          <div className="space-y-2">
            <Label>Default View</Label>
            <Select 
              value={dashboard.defaultView} 
              onValueChange={(value) => updateDashboardPreferences({ defaultView: value as any })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="overview">Overview</SelectItem>
                <SelectItem value="incidents">Incidents</SelectItem>
                <SelectItem value="agents">Agents</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Incident View Mode */}
          <div className="space-y-2">
            <Label>Incident View Mode</Label>
            <Select value={incidentViewMode} onValueChange={(value: any) => setIncidentViewMode(value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="timeline">Timeline</SelectItem>
                <SelectItem value="kanban">Kanban Board</SelectItem>
                <SelectItem value="table">Table</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Show Resolved Incidents */}
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="show-resolved">Show Resolved Incidents</Label>
              <p className="text-sm text-muted-foreground">
                Include resolved incidents in dashboard views
              </p>
            </div>
            <Switch
              id="show-resolved"
              checked={dashboard.showResolvedIncidents}
              onCheckedChange={(checked) => updateDashboardPreferences({ showResolvedIncidents: checked })}
            />
          </div>
        </CardContent>
      </Card>

      {/* Widget Visibility */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Eye className="w-5 h-5" />
            Widget Visibility
          </CardTitle>
          <CardDescription>
            Choose which widgets to display on your dashboard
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(widgetVisibility).map(([key, visible]) => (
              <div key={key} className="flex items-center justify-between p-3 border rounded-lg">
                <Label htmlFor={key} className="cursor-pointer capitalize">
                  {key.replace(/([A-Z])/g, ' $1').trim()}
                </Label>
                <Switch
                  id={key}
                  checked={visible}
                  onCheckedChange={() => toggleWidget(key as keyof WidgetVisibility)}
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Data Refresh */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="w-5 h-5" />
            Data Refresh
          </CardTitle>
          <CardDescription>
            Control how often dashboard data is updated
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="auto-refresh">Auto Refresh</Label>
            <Switch
              id="auto-refresh"
              checked={autoRefresh}
              onCheckedChange={setAutoRefresh}
            />
          </div>

          {autoRefresh && (
            <div className="space-y-2">
              <Label>Refresh Interval</Label>
              <Select 
                value={dashboard.refreshInterval.toString()} 
                onValueChange={(value) => updateDashboardPreferences({ refreshInterval: parseInt(value) })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {refreshIntervals.map(interval => (
                    <SelectItem key={interval.value} value={interval.value.toString()}>
                      {interval.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                Lower intervals may impact performance
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Chart Preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Chart Preferences
          </CardTitle>
          <CardDescription>
            Customize how data is visualized in charts
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Default Chart Type</Label>
            <Select 
              value={chartPreferences.defaultChartType} 
              onValueChange={(value: any) => setChartPreferences({ ...chartPreferences, defaultChartType: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="line">Line Chart</SelectItem>
                <SelectItem value="bar">Bar Chart</SelectItem>
                <SelectItem value="area">Area Chart</SelectItem>
                <SelectItem value="pie">Pie Chart</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center justify-between">
            <Label htmlFor="data-labels">Show Data Labels</Label>
            <Switch
              id="data-labels"
              checked={chartPreferences.showDataLabels}
              onCheckedChange={(checked) => 
                setChartPreferences({ ...chartPreferences, showDataLabels: checked })
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <Label htmlFor="animate-charts">Animate Charts</Label>
            <Switch
              id="animate-charts"
              checked={chartPreferences.animateCharts}
              onCheckedChange={(checked) => 
                setChartPreferences({ ...chartPreferences, animateCharts: checked })
              }
            />
          </div>

          <div className="space-y-2">
            <Label>Color Palette</Label>
            <Select 
              value={chartPreferences.colorPalette} 
              onValueChange={(value: any) => setChartPreferences({ ...chartPreferences, colorPalette: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="default">Default</SelectItem>
                <SelectItem value="colorblind">Colorblind Friendly</SelectItem>
                <SelectItem value="highContrast">High Contrast</SelectItem>
                <SelectItem value="custom">Custom</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Table Display */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings2 className="w-5 h-5" />
            Table Display
          </CardTitle>
          <CardDescription>
            Configure table appearance and behavior
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="compact-tables">Compact Tables</Label>
              <p className="text-sm text-muted-foreground">
                Reduce row height to show more data
              </p>
            </div>
            <Switch
              id="compact-tables"
              checked={compactTables}
              onCheckedChange={setCompactTables}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="grid-lines">Show Grid Lines</Label>
              <p className="text-sm text-muted-foreground">
                Display borders between table cells
              </p>
            </div>
            <Switch
              id="grid-lines"
              checked={showGridLines}
              onCheckedChange={setShowGridLines}
            />
          </div>
        </CardContent>
      </Card>

      {/* Preview */}
      <Card>
        <CardHeader>
          <CardTitle>Layout Preview</CardTitle>
          <CardDescription>
            Preview of your current display settings
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="border rounded-lg p-4 space-y-4">
            <div className="text-sm text-muted-foreground mb-2">
              Dashboard Layout: <span className="font-medium">{dashboardLayout}</span>
            </div>
            
            {dashboardLayout === 'grid' ? (
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(widgetVisibility).map(([key, visible]) => 
                  visible && (
                    <div key={key} className="h-20 bg-muted rounded-md p-3">
                      <div className="text-xs font-medium capitalize">
                        {key.replace(/([A-Z])/g, ' $1').trim()}
                      </div>
                    </div>
                  )
                )}
              </div>
            ) : (
              <div className="space-y-2">
                {Object.entries(widgetVisibility).map(([key, visible]) => 
                  visible && (
                    <div key={key} className="h-16 bg-muted rounded-md p-3">
                      <div className="text-xs font-medium capitalize">
                        {key.replace(/([A-Z])/g, ' $1').trim()}
                      </div>
                    </div>
                  )
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}