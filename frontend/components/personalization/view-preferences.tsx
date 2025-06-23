'use client'

import { useState, useEffect, useCallback } from 'react'
import { ViewPreference } from '@/types/personalization'
import { usePersonalization } from '@/hooks/use-personalization'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { 
  Eye, 
  Save, 
  X, 
  Share2, 
  Star, 
  StarOff,
  Settings,
  Layout,
  Copy,
  Trash2,
  Edit,
  Check,
  Camera,
  Download,
  Upload,
  RotateCcw,
  Grid3x3,
  List,
  BarChart3,
  Users,
  MessageSquare
} from 'lucide-react'

interface ViewPreferencesProps {
  viewType?: 'dashboard' | 'incidents' | 'agents' | 'analytics' | 'custom'
  currentState?: Record<string, any>
  onApply?: (preference: ViewPreference) => void
  onSave?: (preference: ViewPreference) => void
}

interface ViewState {
  // Common view state properties
  layout?: 'grid' | 'list' | 'cards' | 'table'
  density?: 'compact' | 'comfortable' | 'spacious'
  theme?: 'light' | 'dark' | 'auto'
  
  // Panel visibility
  showSidebar?: boolean
  showFilters?: boolean
  showActivityPanel?: boolean
  
  // Column preferences for tables
  visibleColumns?: string[]
  columnOrder?: string[]
  columnWidths?: Record<string, number>
  
  // Sort and filter preferences
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  filters?: Record<string, any>
  
  // Chart preferences
  chartType?: string
  chartTimeRange?: string
  chartMetrics?: string[]
  
  // Other preferences
  autoRefresh?: boolean
  refreshInterval?: number
  itemsPerPage?: number
  expandedSections?: string[]
}

const VIEW_TYPE_ICONS = {
  dashboard: Grid3x3,
  incidents: List,
  agents: Users,
  analytics: BarChart3,
  custom: Settings
}

const DEFAULT_VIEW_STATES: Record<string, ViewState> = {
  dashboard: {
    layout: 'grid',
    density: 'comfortable',
    showSidebar: true,
    showActivityPanel: true,
    autoRefresh: true,
    refreshInterval: 30000
  },
  incidents: {
    layout: 'table',
    density: 'compact',
    showFilters: true,
    itemsPerPage: 20,
    sortBy: 'createdAt',
    sortOrder: 'desc'
  },
  agents: {
    layout: 'cards',
    density: 'comfortable',
    showFilters: false,
    autoRefresh: true,
    refreshInterval: 10000
  },
  analytics: {
    layout: 'grid',
    density: 'comfortable',
    chartTimeRange: '7d',
    showSidebar: true
  }
}

function ViewPreferenceCard({ 
  preference, 
  isActive,
  onApply, 
  onEdit, 
  onDelete, 
  onDuplicate,
  onSetDefault 
}: {
  preference: ViewPreference
  isActive?: boolean
  onApply: () => void
  onEdit: () => void
  onDelete: () => void
  onDuplicate: () => void
  onSetDefault: () => void
}) {
  const Icon = VIEW_TYPE_ICONS[preference.viewType] || Settings
  
  return (
    <Card className={`p-4 ${isActive ? 'ring-2 ring-blue-500' : ''}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
            <Icon className="h-5 w-5" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold">{preference.name}</h3>
              {preference.isDefault && (
                <Badge variant="secondary" className="text-xs">
                  <Star className="h-3 w-3 mr-1" />
                  Default
                </Badge>
              )}
              {preference.isShared && (
                <Badge variant="outline" className="text-xs">
                  <Share2 className="h-3 w-3 mr-1" />
                  Shared
                </Badge>
              )}
            </div>
            {preference.description && (
              <p className="text-sm text-gray-500 mt-1">
                {preference.description}
              </p>
            )}
            <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
              <span>Type: {preference.viewType}</span>
              <span>•</span>
              <span>Updated: {new Date(preference.updatedAt).toLocaleDateString()}</span>
            </div>
          </div>
        </div>
        
        <div className="flex gap-1">
          <Button
            variant={isActive ? 'default' : 'ghost'}
            size="sm"
            onClick={onApply}
          >
            <Check className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onEdit}
          >
            <Edit className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onDuplicate}
          >
            <Copy className="h-4 w-4" />
          </Button>
          {!preference.isDefault && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onSetDefault}
            >
              <Star className="h-4 w-4" />
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={onDelete}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </Card>
  )
}

export function ViewPreferences({ 
  viewType = 'custom',
  currentState = {},
  onApply,
  onSave 
}: ViewPreferencesProps) {
  const { 
    settings, 
    saveViewPreference, 
    updateViewPreference, 
    deleteViewPreference 
  } = usePersonalization()
  
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [showManageDialog, setShowManageDialog] = useState(false)
  const [showPreviewDialog, setShowPreviewDialog] = useState(false)
  const [editingPreference, setEditingPreference] = useState<ViewPreference | null>(null)
  const [activePreferenceId, setActivePreferenceId] = useState<string | null>(null)
  const [previewState, setPreviewState] = useState<ViewState>({})
  
  const [preferenceForm, setPreferenceForm] = useState({
    name: '',
    description: '',
    isShared: false
  })
  
  const [viewState, setViewState] = useState<ViewState>({
    ...DEFAULT_VIEW_STATES[viewType] || {},
    ...currentState
  })

  // Find relevant preferences for current view type
  const relevantPreferences = settings.viewPreferences.filter(
    p => p.viewType === viewType || viewType === 'custom'
  )

  // Find default preference for current view type
  const defaultPreference = relevantPreferences.find(p => p.isDefault)

  useEffect(() => {
    if (defaultPreference && !activePreferenceId) {
      setViewState(defaultPreference.state as ViewState)
      setActivePreferenceId(defaultPreference.id)
    }
  }, [defaultPreference, activePreferenceId])

  const handleSavePreference = async () => {
    if (!preferenceForm.name) return

    try {
      const newPreference = await saveViewPreference({
        name: preferenceForm.name,
        description: preferenceForm.description,
        viewType,
        state: viewState,
        isShared: preferenceForm.isShared
      })

      onSave?.(newPreference)
      setShowSaveDialog(false)
      setPreferenceForm({ name: '', description: '', isShared: false })
    } catch (error) {
      console.error('Failed to save view preference:', error)
    }
  }

  const handleUpdatePreference = async () => {
    if (!editingPreference) return

    try {
      await updateViewPreference(editingPreference.id, {
        name: preferenceForm.name,
        description: preferenceForm.description,
        state: viewState,
        isShared: preferenceForm.isShared
      })

      setEditingPreference(null)
      setShowManageDialog(false)
    } catch (error) {
      console.error('Failed to update view preference:', error)
    }
  }

  const handleApplyPreference = (preference: ViewPreference) => {
    setViewState(preference.state as ViewState)
    setActivePreferenceId(preference.id)
    onApply?.(preference)
  }

  const handleDeletePreference = async (preferenceId: string) => {
    try {
      await deleteViewPreference(preferenceId)
      if (activePreferenceId === preferenceId) {
        setActivePreferenceId(null)
        setViewState(DEFAULT_VIEW_STATES[viewType] || {})
      }
    } catch (error) {
      console.error('Failed to delete view preference:', error)
    }
  }

  const handleDuplicatePreference = async (preference: ViewPreference) => {
    try {
      await saveViewPreference({
        name: `${preference.name} (Copy)`,
        description: preference.description,
        viewType: preference.viewType,
        state: preference.state
      })
    } catch (error) {
      console.error('Failed to duplicate view preference:', error)
    }
  }

  const handleSetDefault = async (preferenceId: string) => {
    // Update all preferences to remove default status
    for (const pref of relevantPreferences) {
      if (pref.isDefault && pref.id !== preferenceId) {
        await updateViewPreference(pref.id, { isDefault: false })
      }
    }
    
    // Set new default
    await updateViewPreference(preferenceId, { isDefault: true })
  }

  const handleResetToDefaults = () => {
    setViewState(DEFAULT_VIEW_STATES[viewType] || {})
  }

  const captureCurrentView = () => {
    // In a real implementation, this would capture the current view state
    // from the active components
    const capturedState: ViewState = {
      ...viewState,
      // Add timestamp or other metadata
      capturedAt: new Date().toISOString()
    }
    setViewState(capturedState)
  }

  const exportPreferences = () => {
    const dataStr = JSON.stringify(relevantPreferences, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
    
    const exportFileDefaultName = `view_preferences_${viewType}_${new Date().toISOString().split('T')[0]}.json`
    
    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
  }

  const importPreferences = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      const text = await file.text()
      const imported = JSON.parse(text)
      
      // Validate and save imported preferences
      for (const pref of imported) {
        if (pref.viewType === viewType || viewType === 'custom') {
          await saveViewPreference({
            name: pref.name,
            description: pref.description,
            viewType: pref.viewType,
            state: pref.state,
            isShared: pref.isShared
          })
        }
      }
    } catch (error) {
      console.error('Failed to import preferences:', error)
    }
  }

  return (
    <>
      {/* Quick Actions Bar */}
      <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-900 rounded-lg">
        <div className="flex items-center gap-2">
          <Eye className="h-4 w-4 text-gray-500" />
          <span className="text-sm font-medium">View Preferences</span>
          {activePreferenceId && (
            <Badge variant="outline" className="text-xs">
              {relevantPreferences.find(p => p.id === activePreferenceId)?.name}
            </Badge>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={captureCurrentView}
          >
            <Camera className="h-4 w-4 mr-1" />
            Capture
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowSaveDialog(true)}
          >
            <Save className="h-4 w-4 mr-1" />
            Save
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowManageDialog(true)}
          >
            <Settings className="h-4 w-4 mr-1" />
            Manage
          </Button>
        </div>
      </div>

      {/* Save Dialog */}
      <Dialog open={showSaveDialog} onOpenChange={setShowSaveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save View Preference</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="preference-name">Name</Label>
              <Input
                id="preference-name"
                value={preferenceForm.name}
                onChange={(e) => setPreferenceForm({ ...preferenceForm, name: e.target.value })}
                placeholder="e.g., Compact Incident View"
              />
            </div>
            <div>
              <Label htmlFor="preference-description">Description</Label>
              <Textarea
                id="preference-description"
                value={preferenceForm.description}
                onChange={(e) => setPreferenceForm({ ...preferenceForm, description: e.target.value })}
                placeholder="Optional description"
                rows={2}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="preference-shared">Share with team</Label>
              <Switch
                id="preference-shared"
                checked={preferenceForm.isShared}
                onCheckedChange={(checked) => setPreferenceForm({ ...preferenceForm, isShared: checked })}
              />
            </div>
            
            {/* Preview of current state */}
            <div className="border rounded-lg p-3 bg-gray-50 dark:bg-gray-900">
              <h4 className="text-sm font-medium mb-2">Current View Settings</h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {Object.entries(viewState).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-500">{key}:</span>
                    <span className="font-mono">{JSON.stringify(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSaveDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSavePreference}>
              Save Preference
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Manage Dialog */}
      <Dialog open={showManageDialog} onOpenChange={setShowManageDialog}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Manage View Preferences</DialogTitle>
          </DialogHeader>
          
          {editingPreference ? (
            <div className="space-y-4">
              <div>
                <Label htmlFor="edit-preference-name">Name</Label>
                <Input
                  id="edit-preference-name"
                  value={preferenceForm.name}
                  onChange={(e) => setPreferenceForm({ ...preferenceForm, name: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="edit-preference-description">Description</Label>
                <Textarea
                  id="edit-preference-description"
                  value={preferenceForm.description}
                  onChange={(e) => setPreferenceForm({ ...preferenceForm, description: e.target.value })}
                  rows={2}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="edit-preference-shared">Share with team</Label>
                <Switch
                  id="edit-preference-shared"
                  checked={preferenceForm.isShared}
                  onCheckedChange={(checked) => setPreferenceForm({ ...preferenceForm, isShared: checked })}
                />
              </div>
              
              {/* State Editor */}
              <div>
                <Label>View State Configuration</Label>
                <Tabs defaultValue="layout" className="mt-2">
                  <TabsList>
                    <TabsTrigger value="layout">Layout</TabsTrigger>
                    <TabsTrigger value="display">Display</TabsTrigger>
                    <TabsTrigger value="data">Data</TabsTrigger>
                    <TabsTrigger value="advanced">Advanced</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="layout" className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Layout Type</Label>
                        <Select
                          value={viewState.layout || 'grid'}
                          onValueChange={(value) => setViewState({ ...viewState, layout: value as any })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="grid">Grid</SelectItem>
                            <SelectItem value="list">List</SelectItem>
                            <SelectItem value="cards">Cards</SelectItem>
                            <SelectItem value="table">Table</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Density</Label>
                        <Select
                          value={viewState.density || 'comfortable'}
                          onValueChange={(value) => setViewState({ ...viewState, density: value as any })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="compact">Compact</SelectItem>
                            <SelectItem value="comfortable">Comfortable</SelectItem>
                            <SelectItem value="spacious">Spacious</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label>Show Sidebar</Label>
                        <Switch
                          checked={viewState.showSidebar || false}
                          onCheckedChange={(checked) => setViewState({ ...viewState, showSidebar: checked })}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Show Filters</Label>
                        <Switch
                          checked={viewState.showFilters || false}
                          onCheckedChange={(checked) => setViewState({ ...viewState, showFilters: checked })}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Show Activity Panel</Label>
                        <Switch
                          checked={viewState.showActivityPanel || false}
                          onCheckedChange={(checked) => setViewState({ ...viewState, showActivityPanel: checked })}
                        />
                      </div>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="display" className="space-y-4">
                    <div>
                      <Label>Items Per Page</Label>
                      <Input
                        type="number"
                        value={viewState.itemsPerPage || 20}
                        onChange={(e) => setViewState({ ...viewState, itemsPerPage: parseInt(e.target.value) || 20 })}
                        min={10}
                        max={100}
                        step={10}
                      />
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="data" className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Sort By</Label>
                        <Input
                          value={viewState.sortBy || ''}
                          onChange={(e) => setViewState({ ...viewState, sortBy: e.target.value })}
                          placeholder="Field name"
                        />
                      </div>
                      <div>
                        <Label>Sort Order</Label>
                        <Select
                          value={viewState.sortOrder || 'desc'}
                          onValueChange={(value) => setViewState({ ...viewState, sortOrder: value as any })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="asc">Ascending</SelectItem>
                            <SelectItem value="desc">Descending</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="advanced" className="space-y-4">
                    <div className="flex items-center justify-between">
                      <Label>Auto Refresh</Label>
                      <Switch
                        checked={viewState.autoRefresh || false}
                        onCheckedChange={(checked) => setViewState({ ...viewState, autoRefresh: checked })}
                      />
                    </div>
                    {viewState.autoRefresh && (
                      <div>
                        <Label>Refresh Interval (seconds)</Label>
                        <Input
                          type="number"
                          value={(viewState.refreshInterval || 30000) / 1000}
                          onChange={(e) => setViewState({ 
                            ...viewState, 
                            refreshInterval: parseInt(e.target.value) * 1000 || 30000 
                          })}
                          min={5}
                          max={300}
                        />
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </div>
              
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setEditingPreference(null)}>
                  Cancel
                </Button>
                <Button onClick={handleUpdatePreference}>
                  Update Preference
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-500">
                  Manage your saved view preferences
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleResetToDefaults}
                  >
                    <RotateCcw className="h-4 w-4 mr-1" />
                    Reset to Defaults
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={exportPreferences}
                  >
                    <Download className="h-4 w-4 mr-1" />
                    Export
                  </Button>
                  <Label htmlFor="import-preferences" className="cursor-pointer">
                    <Button
                      variant="outline"
                      size="sm"
                      as="span"
                    >
                      <Upload className="h-4 w-4 mr-1" />
                      Import
                    </Button>
                  </Label>
                  <input
                    id="import-preferences"
                    type="file"
                    accept=".json"
                    onChange={importPreferences}
                    className="hidden"
                  />
                </div>
              </div>
              
              <Tabs defaultValue={viewType}>
                <TabsList>
                  <TabsTrigger value="all">All Types</TabsTrigger>
                  <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
                  <TabsTrigger value="incidents">Incidents</TabsTrigger>
                  <TabsTrigger value="agents">Agents</TabsTrigger>
                  <TabsTrigger value="analytics">Analytics</TabsTrigger>
                  <TabsTrigger value="custom">Custom</TabsTrigger>
                </TabsList>
                
                <TabsContent value="all">
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-2 p-1">
                      {settings.viewPreferences.map((preference) => (
                        <ViewPreferenceCard
                          key={preference.id}
                          preference={preference}
                          isActive={activePreferenceId === preference.id}
                          onApply={() => handleApplyPreference(preference)}
                          onEdit={() => {
                            setEditingPreference(preference)
                            setPreferenceForm({
                              name: preference.name,
                              description: preference.description || '',
                              isShared: preference.isShared || false
                            })
                            setViewState(preference.state as ViewState)
                          }}
                          onDelete={() => handleDeletePreference(preference.id)}
                          onDuplicate={() => handleDuplicatePreference(preference)}
                          onSetDefault={() => handleSetDefault(preference.id)}
                        />
                      ))}
                    </div>
                  </ScrollArea>
                </TabsContent>
                
                {['dashboard', 'incidents', 'agents', 'analytics', 'custom'].map((type) => (
                  <TabsContent key={type} value={type}>
                    <ScrollArea className="h-[400px]">
                      <div className="space-y-2 p-1">
                        {settings.viewPreferences
                          .filter(p => p.viewType === type)
                          .map((preference) => (
                            <ViewPreferenceCard
                              key={preference.id}
                              preference={preference}
                              isActive={activePreferenceId === preference.id}
                              onApply={() => handleApplyPreference(preference)}
                              onEdit={() => {
                                setEditingPreference(preference)
                                setPreferenceForm({
                                  name: preference.name,
                                  description: preference.description || '',
                                  isShared: preference.isShared || false
                                })
                                setViewState(preference.state as ViewState)
                              }}
                              onDelete={() => handleDeletePreference(preference.id)}
                              onDuplicate={() => handleDuplicatePreference(preference)}
                              onSetDefault={() => handleSetDefault(preference.id)}
                            />
                          ))}
                      </div>
                    </ScrollArea>
                  </TabsContent>
                ))}
              </Tabs>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Preview Dialog */}
      <Dialog open={showPreviewDialog} onOpenChange={setShowPreviewDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Preview View State</DialogTitle>
          </DialogHeader>
          <ScrollArea className="h-[400px]">
            <pre className="text-sm">
              {JSON.stringify(previewState, null, 2)}
            </pre>
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </>
  )
}