'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { DndContext, DragEndEvent, DragMoveEvent, DragStartEvent, useSensor, useSensors, PointerSensor, KeyboardSensor } from '@dnd-kit/core'
import { snapCenterToCursor } from '@dnd-kit/modifiers'
import { 
  DashboardWidget, 
  Widget,
  WidgetTemplate 
} from '@/types/personalization'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Grid3x3,
  Move,
  Maximize2,
  Minimize2,
  Lock,
  Unlock,
  Layers,
  Layout,
  Save,
  Undo,
  Redo,
  Copy,
  Trash2,
  Settings,
  Eye,
  EyeOff,
  ChevronRight
} from 'lucide-react'

interface WidgetArrangementProps {
  widgets: DashboardWidget[]
  gridCols?: number
  gridRows?: number
  onUpdate: (widgets: DashboardWidget[]) => void
  isEditing?: boolean
  availableWidgets?: Widget[]
  templates?: WidgetTemplate[]
}

interface GridPosition {
  x: number
  y: number
  w: number
  h: number
}

interface LayoutPreset {
  id: string
  name: string
  description: string
  icon: string
  layout: GridPosition[]
}

const LAYOUT_PRESETS: LayoutPreset[] = [
  {
    id: 'single-focus',
    name: 'Single Focus',
    description: 'One large widget with smaller supporting widgets',
    icon: '⬜',
    layout: [
      { x: 0, y: 0, w: 8, h: 6 },
      { x: 8, y: 0, w: 4, h: 3 },
      { x: 8, y: 3, w: 4, h: 3 },
      { x: 0, y: 6, w: 12, h: 2 }
    ]
  },
  {
    id: 'equal-grid',
    name: 'Equal Grid',
    description: 'Four equal-sized widgets',
    icon: '⚏',
    layout: [
      { x: 0, y: 0, w: 6, h: 4 },
      { x: 6, y: 0, w: 6, h: 4 },
      { x: 0, y: 4, w: 6, h: 4 },
      { x: 6, y: 4, w: 6, h: 4 }
    ]
  },
  {
    id: 'dashboard-classic',
    name: 'Dashboard Classic',
    description: 'Top metrics row with main content below',
    icon: '⬛',
    layout: [
      { x: 0, y: 0, w: 3, h: 2 },
      { x: 3, y: 0, w: 3, h: 2 },
      { x: 6, y: 0, w: 3, h: 2 },
      { x: 9, y: 0, w: 3, h: 2 },
      { x: 0, y: 2, w: 8, h: 4 },
      { x: 8, y: 2, w: 4, h: 4 },
      { x: 0, y: 6, w: 12, h: 2 }
    ]
  },
  {
    id: 'two-column',
    name: 'Two Column',
    description: 'Split view with two main areas',
    icon: '⚎',
    layout: [
      { x: 0, y: 0, w: 6, h: 8 },
      { x: 6, y: 0, w: 6, h: 8 }
    ]
  }
]

interface DraggableWidgetProps {
  widget: DashboardWidget
  isLocked?: boolean
  isSelected?: boolean
  onSelect?: () => void
  onConfigure?: () => void
}

function DraggableWidget({ widget, isLocked, isSelected, onSelect, onConfigure }: DraggableWidgetProps) {
  return (
    <div 
      className={`
        relative h-full bg-white dark:bg-gray-800 border rounded-lg p-4 
        transition-all cursor-move hover:shadow-lg
        ${isSelected ? 'ring-2 ring-blue-500' : ''}
        ${isLocked ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      onClick={onSelect}
    >
      <div className="absolute top-2 right-2 flex gap-1">
        {isLocked ? (
          <Lock className="h-4 w-4 text-gray-400" />
        ) : (
          <Unlock className="h-4 w-4 text-gray-400" />
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation()
            onConfigure?.()
          }}
        >
          <Settings className="h-3 w-3" />
        </Button>
      </div>
      
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="font-medium">{widget.widgetId}</p>
          <p className="text-sm text-gray-500">
            {widget.w}x{widget.h}
          </p>
        </div>
      </div>
    </div>
  )
}

export function WidgetArrangement({
  widgets: initialWidgets,
  gridCols = 12,
  gridRows = 8,
  onUpdate,
  isEditing = false,
  availableWidgets = [],
  templates = []
}: WidgetArrangementProps) {
  const [widgets, setWidgets] = useState<DashboardWidget[]>(initialWidgets)
  const [selectedWidgetId, setSelectedWidgetId] = useState<string | null>(null)
  const [showGridLines, setShowGridLines] = useState(true)
  const [snapToGrid, setSnapToGrid] = useState(true)
  const [lockedWidgets, setLockedWidgets] = useState<Set<string>>(new Set())
  const [hiddenWidgets, setHiddenWidgets] = useState<Set<string>>(new Set())
  const [showLayoutPresets, setShowLayoutPresets] = useState(false)
  const [showWidgetConfig, setShowWidgetConfig] = useState(false)
  const [history, setHistory] = useState<DashboardWidget[][]>([initialWidgets])
  const [historyIndex, setHistoryIndex] = useState(0)
  const gridRef = useRef<HTMLDivElement>(null)

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor)
  )

  useEffect(() => {
    setWidgets(initialWidgets)
  }, [initialWidgets])

  const addToHistory = useCallback((newWidgets: DashboardWidget[]) => {
    const newHistory = history.slice(0, historyIndex + 1)
    newHistory.push(newWidgets)
    setHistory(newHistory)
    setHistoryIndex(newHistory.length - 1)
  }, [history, historyIndex])

  const undo = useCallback(() => {
    if (historyIndex > 0) {
      const newIndex = historyIndex - 1
      setHistoryIndex(newIndex)
      setWidgets(history[newIndex])
      onUpdate(history[newIndex])
    }
  }, [history, historyIndex, onUpdate])

  const redo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      const newIndex = historyIndex + 1
      setHistoryIndex(newIndex)
      setWidgets(history[newIndex])
      onUpdate(history[newIndex])
    }
  }, [history, historyIndex, onUpdate])

  const getGridPosition = useCallback((clientX: number, clientY: number): GridPosition | null => {
    if (!gridRef.current) return null

    const rect = gridRef.current.getBoundingClientRect()
    const cellWidth = rect.width / gridCols
    const cellHeight = rect.height / gridRows

    const x = Math.floor((clientX - rect.left) / cellWidth)
    const y = Math.floor((clientY - rect.top) / cellHeight)

    return {
      x: Math.max(0, Math.min(gridCols - 1, x)),
      y: Math.max(0, Math.min(gridRows - 1, y)),
      w: 1,
      h: 1
    }
  }, [gridCols, gridRows])

  const checkCollision = useCallback((widget: DashboardWidget, otherWidgets: DashboardWidget[]) => {
    return otherWidgets.some(other => {
      if (other.id === widget.id || hiddenWidgets.has(other.id)) return false
      
      const horizontalOverlap = widget.x < other.x + other.w && widget.x + widget.w > other.x
      const verticalOverlap = widget.y < other.y + other.h && widget.y + widget.h > other.y
      
      return horizontalOverlap && verticalOverlap
    })
  }, [hiddenWidgets])

  const findFreePosition = useCallback((widget: DashboardWidget): GridPosition => {
    for (let y = 0; y <= gridRows - widget.h; y++) {
      for (let x = 0; x <= gridCols - widget.w; x++) {
        const testWidget = { ...widget, x, y }
        if (!checkCollision(testWidget, widgets)) {
          return { x, y, w: widget.w, h: widget.h }
        }
      }
    }
    return { x: 0, y: 0, w: widget.w, h: widget.h }
  }, [gridCols, gridRows, widgets, checkCollision])

  const handleDragMove = useCallback((event: DragMoveEvent) => {
    if (!snapToGrid || !gridRef.current) return

    const { active, delta } = event
    const widget = widgets.find(w => w.id === active.id)
    if (!widget || lockedWidgets.has(widget.id)) return

    const position = getGridPosition(
      event.activatorEvent.clientX + delta.x,
      event.activatorEvent.clientY + delta.y
    )

    if (position) {
      const updatedWidget = {
        ...widget,
        x: Math.max(0, Math.min(gridCols - widget.w, position.x)),
        y: Math.max(0, Math.min(gridRows - widget.h, position.y))
      }

      const newWidgets = widgets.map(w => 
        w.id === widget.id ? updatedWidget : w
      )

      setWidgets(newWidgets)
    }
  }, [widgets, gridCols, gridRows, snapToGrid, lockedWidgets, getGridPosition])

  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active } = event
    const widget = widgets.find(w => w.id === active.id)
    if (!widget || lockedWidgets.has(widget.id)) return

    // Check for collisions and find free position if needed
    const otherWidgets = widgets.filter(w => w.id !== widget.id)
    if (checkCollision(widget, otherWidgets)) {
      const freePosition = findFreePosition(widget)
      const updatedWidget = { ...widget, ...freePosition }
      const newWidgets = widgets.map(w => 
        w.id === widget.id ? updatedWidget : w
      )
      setWidgets(newWidgets)
      addToHistory(newWidgets)
      onUpdate(newWidgets)
    } else {
      addToHistory(widgets)
      onUpdate(widgets)
    }
  }, [widgets, lockedWidgets, checkCollision, findFreePosition, addToHistory, onUpdate])

  const applyLayoutPreset = useCallback((preset: LayoutPreset) => {
    const newWidgets = widgets.slice(0, preset.layout.length).map((widget, index) => ({
      ...widget,
      ...preset.layout[index]
    }))

    setWidgets(newWidgets)
    addToHistory(newWidgets)
    onUpdate(newWidgets)
    setShowLayoutPresets(false)
  }, [widgets, addToHistory, onUpdate])

  const toggleWidgetLock = useCallback((widgetId: string) => {
    const newLocked = new Set(lockedWidgets)
    if (newLocked.has(widgetId)) {
      newLocked.delete(widgetId)
    } else {
      newLocked.add(widgetId)
    }
    setLockedWidgets(newLocked)
  }, [lockedWidgets])

  const toggleWidgetVisibility = useCallback((widgetId: string) => {
    const newHidden = new Set(hiddenWidgets)
    if (newHidden.has(widgetId)) {
      newHidden.delete(widgetId)
    } else {
      newHidden.add(widgetId)
    }
    setHiddenWidgets(newHidden)
  }, [hiddenWidgets])

  const duplicateWidget = useCallback((widgetId: string) => {
    const widget = widgets.find(w => w.id === widgetId)
    if (!widget) return

    const freePosition = findFreePosition(widget)
    const newWidget: DashboardWidget = {
      ...widget,
      id: `widget_${Date.now()}`,
      ...freePosition
    }

    const newWidgets = [...widgets, newWidget]
    setWidgets(newWidgets)
    addToHistory(newWidgets)
    onUpdate(newWidgets)
  }, [widgets, findFreePosition, addToHistory, onUpdate])

  const removeWidget = useCallback((widgetId: string) => {
    const newWidgets = widgets.filter(w => w.id !== widgetId)
    setWidgets(newWidgets)
    addToHistory(newWidgets)
    onUpdate(newWidgets)
    setSelectedWidgetId(null)
  }, [widgets, addToHistory, onUpdate])

  const resizeWidget = useCallback((widgetId: string, dw: number, dh: number) => {
    const widget = widgets.find(w => w.id === widgetId)
    if (!widget || lockedWidgets.has(widgetId)) return

    const newW = Math.max(1, Math.min(gridCols - widget.x, widget.w + dw))
    const newH = Math.max(1, Math.min(gridRows - widget.y, widget.h + dh))

    const updatedWidget = { ...widget, w: newW, h: newH }
    const newWidgets = widgets.map(w => 
      w.id === widgetId ? updatedWidget : w
    )

    setWidgets(newWidgets)
    addToHistory(newWidgets)
    onUpdate(newWidgets)
  }, [widgets, gridCols, gridRows, lockedWidgets, addToHistory, onUpdate])

  const selectedWidget = widgets.find(w => w.id === selectedWidgetId)

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      {isEditing && (
        <div className="flex items-center justify-between p-2 border-b bg-gray-50 dark:bg-gray-900">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={undo}
              disabled={historyIndex === 0}
            >
              <Undo className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={redo}
              disabled={historyIndex === history.length - 1}
            >
              <Redo className="h-4 w-4" />
            </Button>
            
            <div className="h-6 w-px bg-gray-300 dark:bg-gray-700" />
            
            <Button
              variant={showGridLines ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setShowGridLines(!showGridLines)}
            >
              <Grid3x3 className="h-4 w-4 mr-1" />
              Grid
            </Button>
            
            <Button
              variant={snapToGrid ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setSnapToGrid(!snapToGrid)}
            >
              <Move className="h-4 w-4 mr-1" />
              Snap
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowLayoutPresets(true)}
            >
              <Layout className="h-4 w-4 mr-1" />
              Presets
            </Button>
          </div>

          {selectedWidget && (
            <div className="flex items-center gap-2">
              <Badge variant="outline">
                {selectedWidget.widgetId} ({selectedWidget.w}x{selectedWidget.h})
              </Badge>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => toggleWidgetLock(selectedWidget.id)}
              >
                {lockedWidgets.has(selectedWidget.id) ? (
                  <Lock className="h-4 w-4" />
                ) : (
                  <Unlock className="h-4 w-4" />
                )}
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => toggleWidgetVisibility(selectedWidget.id)}
              >
                {hiddenWidgets.has(selectedWidget.id) ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => duplicateWidget(selectedWidget.id)}
              >
                <Copy className="h-4 w-4" />
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => removeWidget(selectedWidget.id)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
              
              <div className="h-6 w-px bg-gray-300 dark:bg-gray-700" />
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => resizeWidget(selectedWidget.id, -1, 0)}
                disabled={selectedWidget.w <= 1}
              >
                W-
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => resizeWidget(selectedWidget.id, 1, 0)}
                disabled={selectedWidget.x + selectedWidget.w >= gridCols}
              >
                W+
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => resizeWidget(selectedWidget.id, 0, -1)}
                disabled={selectedWidget.h <= 1}
              >
                H-
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => resizeWidget(selectedWidget.id, 0, 1)}
                disabled={selectedWidget.y + selectedWidget.h >= gridRows}
              >
                H+
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Grid Container */}
      <div className="flex-1 p-4 overflow-auto">
        <DndContext
          sensors={sensors}
          onDragMove={handleDragMove}
          onDragEnd={handleDragEnd}
          modifiers={[snapCenterToCursor]}
        >
          <div
            ref={gridRef}
            className="relative w-full h-full min-h-[400px] border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg"
            style={{
              backgroundImage: showGridLines
                ? `repeating-linear-gradient(
                    0deg,
                    transparent,
                    transparent ${100 / gridRows - 0.1}%,
                    rgba(0,0,0,0.1) ${100 / gridRows - 0.1}%,
                    rgba(0,0,0,0.1) ${100 / gridRows}%
                  ),
                  repeating-linear-gradient(
                    90deg,
                    transparent,
                    transparent ${100 / gridCols - 0.1}%,
                    rgba(0,0,0,0.1) ${100 / gridCols - 0.1}%,
                    rgba(0,0,0,0.1) ${100 / gridCols}%
                  )`
                : undefined
            }}
          >
            {widgets.map((widget) => {
              if (hiddenWidgets.has(widget.id)) return null

              return (
                <div
                  key={widget.id}
                  className="absolute transition-all duration-200"
                  style={{
                    left: `${(widget.x / gridCols) * 100}%`,
                    top: `${(widget.y / gridRows) * 100}%`,
                    width: `${(widget.w / gridCols) * 100}%`,
                    height: `${(widget.h / gridRows) * 100}%`,
                    padding: '4px'
                  }}
                >
                  <DraggableWidget
                    widget={widget}
                    isLocked={lockedWidgets.has(widget.id)}
                    isSelected={selectedWidgetId === widget.id}
                    onSelect={() => setSelectedWidgetId(widget.id)}
                    onConfigure={() => {
                      setSelectedWidgetId(widget.id)
                      setShowWidgetConfig(true)
                    }}
                  />
                </div>
              )
            })}
          </div>
        </DndContext>
      </div>

      {/* Layout Presets Dialog */}
      <Dialog open={showLayoutPresets} onOpenChange={setShowLayoutPresets}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Layout Presets</DialogTitle>
          </DialogHeader>
          <ScrollArea className="h-[400px]">
            <div className="grid grid-cols-2 gap-4 p-4">
              {LAYOUT_PRESETS.map((preset) => (
                <Card
                  key={preset.id}
                  className="p-4 cursor-pointer hover:border-blue-500 transition-colors"
                  onClick={() => applyLayoutPreset(preset)}
                >
                  <div className="flex items-start gap-3">
                    <div className="text-4xl">{preset.icon}</div>
                    <div className="flex-1">
                      <h3 className="font-semibold">{preset.name}</h3>
                      <p className="text-sm text-gray-500 mt-1">
                        {preset.description}
                      </p>
                      <p className="text-xs text-gray-400 mt-2">
                        {preset.layout.length} widgets
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* Widget Configuration Dialog */}
      <Dialog open={showWidgetConfig} onOpenChange={setShowWidgetConfig}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Widget Configuration</DialogTitle>
          </DialogHeader>
          {selectedWidget && (
            <div className="space-y-4">
              <div>
                <Label>Widget Type</Label>
                <p className="text-sm text-gray-500">{selectedWidget.widgetId}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Position X</Label>
                  <Input
                    type="number"
                    value={selectedWidget.x}
                    onChange={(e) => {
                      const newX = parseInt(e.target.value) || 0
                      const updatedWidget = { ...selectedWidget, x: newX }
                      const newWidgets = widgets.map(w => 
                        w.id === selectedWidget.id ? updatedWidget : w
                      )
                      setWidgets(newWidgets)
                      onUpdate(newWidgets)
                    }}
                    min={0}
                    max={gridCols - selectedWidget.w}
                  />
                </div>
                <div>
                  <Label>Position Y</Label>
                  <Input
                    type="number"
                    value={selectedWidget.y}
                    onChange={(e) => {
                      const newY = parseInt(e.target.value) || 0
                      const updatedWidget = { ...selectedWidget, y: newY }
                      const newWidgets = widgets.map(w => 
                        w.id === selectedWidget.id ? updatedWidget : w
                      )
                      setWidgets(newWidgets)
                      onUpdate(newWidgets)
                    }}
                    min={0}
                    max={gridRows - selectedWidget.h}
                  />
                </div>
                <div>
                  <Label>Width</Label>
                  <Input
                    type="number"
                    value={selectedWidget.w}
                    onChange={(e) => {
                      const newW = parseInt(e.target.value) || 1
                      const updatedWidget = { ...selectedWidget, w: newW }
                      const newWidgets = widgets.map(w => 
                        w.id === selectedWidget.id ? updatedWidget : w
                      )
                      setWidgets(newWidgets)
                      onUpdate(newWidgets)
                    }}
                    min={1}
                    max={gridCols - selectedWidget.x}
                  />
                </div>
                <div>
                  <Label>Height</Label>
                  <Input
                    type="number"
                    value={selectedWidget.h}
                    onChange={(e) => {
                      const newH = parseInt(e.target.value) || 1
                      const updatedWidget = { ...selectedWidget, h: newH }
                      const newWidgets = widgets.map(w => 
                        w.id === selectedWidget.id ? updatedWidget : w
                      )
                      setWidgets(newWidgets)
                      onUpdate(newWidgets)
                    }}
                    min={1}
                    max={gridRows - selectedWidget.y}
                  />
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setShowWidgetConfig(false)}>
              Done
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}