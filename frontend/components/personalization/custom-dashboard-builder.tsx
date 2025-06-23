'use client'

import { useState, useRef, useCallback } from 'react'
import { 
  DashboardLayout, 
  DashboardWidget, 
  Widget 
} from '@/types/personalization'
import { usePersonalization } from '@/hooks/use-personalization'
import { WidgetArrangement } from './widget-arrangement'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { 
  GripVertical, 
  X, 
  Save, 
  Share2, 
  Download, 
  Upload,
  Plus,
  Settings,
  Expand,
  Shrink
} from 'lucide-react'

interface DashboardBuilderProps {
  dashboard?: DashboardLayout
  onSave?: (dashboard: DashboardLayout) => void
  onCancel?: () => void
}

// GridCell component removed - now using WidgetArrangement component instead

export function CustomDashboardBuilder({ 
  dashboard: initialDashboard, 
  onSave, 
  onCancel 
}: DashboardBuilderProps) {
  const { settings, saveDashboard, updateDashboard } = usePersonalization()
  const [dashboard, setDashboard] = useState<DashboardLayout>(
    initialDashboard || {
      id: '',
      name: 'New Dashboard',
      description: '',
      widgets: [],
      gridCols: 12,
      gridRows: 8,
      createdAt: new Date(),
      updatedAt: new Date()
    }
  )
  const [isEditing, setIsEditing] = useState(true)
  const [showWidgetLibrary, setShowWidgetLibrary] = useState(false)
  const [showShareDialog, setShowShareDialog] = useState(false)
  // Drag and drop handled by WidgetArrangement component

  const handleAddWidget = (widget: Widget) => {
    const newWidget: DashboardWidget = {
      id: `widget_${Date.now()}`,
      widgetId: widget.id,
      x: 0,
      y: 0,
      w: widget.defaultSize.w,
      h: widget.defaultSize.h,
      config: {}
    }

    setDashboard({
      ...dashboard,
      widgets: [...dashboard.widgets, newWidget]
    })
    setShowWidgetLibrary(false)
  }

  // Widget operations handled by WidgetArrangement component

  const handleSave = async () => {
    try {
      if (dashboard.id) {
        await updateDashboard(dashboard.id, dashboard)
      } else {
        const saved = await saveDashboard(dashboard)
        setDashboard(saved)
      }
      onSave?.(dashboard)
    } catch (error) {
      console.error('Failed to save dashboard:', error)
    }
  }

  const handleExport = () => {
    const dataStr = JSON.stringify(dashboard, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
    
    const exportFileDefaultName = `dashboard_${dashboard.name.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.json`
    
    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
  }

  // Widget selection now handled by WidgetArrangement component

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-4">
          <Input
            value={dashboard.name}
            onChange={(e) => setDashboard({ ...dashboard, name: e.target.value })}
            className="text-lg font-semibold"
            placeholder="Dashboard Name"
          />
          <Button
            variant={isEditing ? 'default' : 'outline'}
            size="sm"
            onClick={() => setIsEditing(!isEditing)}
          >
            {isEditing ? 'Preview' : 'Edit'}
          </Button>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowWidgetLibrary(true)}
            disabled={!isEditing}
          >
            <Plus className="h-4 w-4 mr-1" />
            Add Widget
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowShareDialog(true)}
          >
            <Share2 className="h-4 w-4 mr-1" />
            Share
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
          >
            <Download className="h-4 w-4 mr-1" />
            Export
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={handleSave}
          >
            <Save className="h-4 w-4 mr-1" />
            Save
          </Button>
          {onCancel && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onCancel}
            >
              Cancel
            </Button>
          )}
        </div>
      </div>

      {/* Widget Arrangement */}
      <div className="flex-1">
        <WidgetArrangement
          widgets={dashboard.widgets}
          gridCols={dashboard.gridCols}
          gridRows={dashboard.gridRows}
          onUpdate={(newWidgets) => {
            setDashboard({ ...dashboard, widgets: newWidgets })
          }}
          isEditing={isEditing}
          availableWidgets={[
            { id: 'incidents-chart', type: 'chart', title: 'Incident Trends', defaultSize: { w: 4, h: 2 } },
            { id: 'agents-status', type: 'data', title: 'Agent Status', defaultSize: { w: 3, h: 2 } },
            { id: 'activity-feed', type: 'activity', title: 'Activity Feed', defaultSize: { w: 3, h: 3 } },
            { id: 'chat-widget', type: 'chat', title: 'Chat Interface', defaultSize: { w: 6, h: 4 } },
          ] as Widget[]}
        />
      </div>

      {/* Widget Library Dialog */}
      <Dialog open={showWidgetLibrary} onOpenChange={setShowWidgetLibrary}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Widget Library</DialogTitle>
          </DialogHeader>
          <Tabs defaultValue="all">
            <TabsList>
              <TabsTrigger value="all">All Widgets</TabsTrigger>
              <TabsTrigger value="charts">Charts</TabsTrigger>
              <TabsTrigger value="data">Data</TabsTrigger>
              <TabsTrigger value="custom">Custom</TabsTrigger>
            </TabsList>
            <TabsContent value="all">
              <ScrollArea className="h-[400px]">
                <div className="grid grid-cols-3 gap-4 p-4">
                  {/* Mock widgets - replace with actual widget library */}
                  {[
                    { id: 'incidents-chart', type: 'chart', title: 'Incident Trends', defaultSize: { w: 4, h: 2 } },
                    { id: 'agents-status', type: 'data', title: 'Agent Status', defaultSize: { w: 3, h: 2 } },
                    { id: 'activity-feed', type: 'activity', title: 'Activity Feed', defaultSize: { w: 3, h: 3 } },
                    { id: 'chat-widget', type: 'chat', title: 'Chat Interface', defaultSize: { w: 6, h: 4 } },
                  ].map((widget) => (
                    <Card
                      key={widget.id}
                      className="p-4 cursor-pointer hover:border-blue-500 transition-colors"
                      onClick={() => handleAddWidget(widget as Widget)}
                    >
                      <h3 className="font-semibold">{widget.title}</h3>
                      <p className="text-sm text-gray-500 mt-1">
                        Size: {widget.defaultSize.w}x{widget.defaultSize.h}
                      </p>
                      <Badge variant="outline" className="mt-2">
                        {widget.type}
                      </Badge>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>

      {/* Share Dialog */}
      <Dialog open={showShareDialog} onOpenChange={setShowShareDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Share Dashboard</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Share Link</Label>
              <div className="flex gap-2 mt-1">
                <Input
                  value={`${window.location.origin}/dashboard/${dashboard.id}`}
                  readOnly
                />
                <Button variant="outline" size="sm">
                  Copy
                </Button>
              </div>
            </div>
            <div>
              <Label>Permissions</Label>
              <div className="space-y-2 mt-1">
                <label className="flex items-center">
                  <input type="checkbox" className="mr-2" />
                  Allow editing
                </label>
                <label className="flex items-center">
                  <input type="checkbox" className="mr-2" />
                  Allow duplication
                </label>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowShareDialog(false)}>
              Cancel
            </Button>
            <Button>Share</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}