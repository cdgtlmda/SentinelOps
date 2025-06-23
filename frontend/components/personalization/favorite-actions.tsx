'use client'

import { useState, useEffect } from 'react'
import { FavoriteAction, ActionGroup } from '@/types/personalization'
import { usePersonalization } from '@/hooks/use-personalization'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Star, 
  StarOff, 
  Zap, 
  Settings, 
  Plus,
  Trash2,
  Edit,
  GripVertical,
  Keyboard,
  FolderPlus,
  ChevronRight
} from 'lucide-react'
import { DndContext, DragEndEvent, closestCenter } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

interface FavoriteActionsProps {
  availableActions: Array<{
    id: string
    type: string
    label: string
    icon?: string
    description?: string
  }>
  onActionClick?: (action: FavoriteAction) => void
}

interface QuickAccessToolbarProps {
  actions: FavoriteAction[]
  groups: ActionGroup[]
  onActionClick: (action: FavoriteAction) => void
}

interface SortableActionItemProps {
  action: FavoriteAction
  onEdit: () => void
  onRemove: () => void
}

function SortableActionItem({ action, onEdit, onRemove }: SortableActionItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging
  } = useSortable({ id: action.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border"
    >
      <div className="flex items-center gap-3">
        <button
          className="cursor-grab hover:cursor-grabbing"
          {...attributes}
          {...listeners}
        >
          <GripVertical className="h-4 w-4 text-gray-400" />
        </button>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-medium">{action.label}</span>
            {action.shortcut && (
              <Badge variant="outline" className="text-xs">
                {action.shortcut}
              </Badge>
            )}
          </div>
          <p className="text-sm text-gray-500">Type: {action.actionType}</p>
        </div>
      </div>
      <div className="flex gap-1">
        <Button variant="ghost" size="sm" onClick={onEdit}>
          <Edit className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={onRemove}>
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}

function QuickAccessToolbar({ actions, groups, onActionClick }: QuickAccessToolbarProps) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set())

  const toggleGroup = (groupId: string) => {
    const newExpanded = new Set(expandedGroups)
    if (newExpanded.has(groupId)) {
      newExpanded.delete(groupId)
    } else {
      newExpanded.add(groupId)
    }
    setExpandedGroups(newExpanded)
  }

  const ungroupedActions = actions.filter(a => !a.groupId)
  const groupedActions = groups.map(group => ({
    ...group,
    actions: actions.filter(a => a.groupId === group.id)
  }))

  return (
    <div className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-900 rounded-lg">
      <Zap className="h-4 w-4 text-yellow-500" />
      
      {/* Ungrouped actions */}
      <div className="flex gap-1">
        {ungroupedActions.map((action) => (
          <Button
            key={action.id}
            variant="ghost"
            size="sm"
            onClick={() => onActionClick(action)}
            title={action.shortcut ? `Shortcut: ${action.shortcut}` : undefined}
          >
            {action.icon && <span className="mr-1">{action.icon}</span>}
            {action.label}
          </Button>
        ))}
      </div>

      {/* Grouped actions */}
      {groupedActions.map((group) => (
        <div key={group.id} className="relative">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => toggleGroup(group.id)}
            className="flex items-center gap-1"
          >
            {group.icon && <span className="mr-1">{group.icon}</span>}
            {group.name}
            <ChevronRight 
              className={`h-3 w-3 transition-transform ${
                expandedGroups.has(group.id) ? 'rotate-90' : ''
              }`} 
            />
          </Button>
          
          {expandedGroups.has(group.id) && (
            <div className="absolute top-full left-0 mt-1 p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border z-50">
              {group.actions.map((action) => (
                <Button
                  key={action.id}
                  variant="ghost"
                  size="sm"
                  onClick={() => onActionClick(action)}
                  className="w-full justify-start"
                  title={action.shortcut ? `Shortcut: ${action.shortcut}` : undefined}
                >
                  {action.icon && <span className="mr-1">{action.icon}</span>}
                  {action.label}
                  {action.shortcut && (
                    <Badge variant="outline" className="ml-auto text-xs">
                      {action.shortcut}
                    </Badge>
                  )}
                </Button>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export function FavoriteActions({ availableActions, onActionClick }: FavoriteActionsProps) {
  const { 
    settings, 
    addFavoriteAction, 
    removeFavoriteAction, 
    updateFavoriteAction,
    saveActionGroup 
  } = usePersonalization()
  
  const [showManageDialog, setShowManageDialog] = useState(false)
  const [showGroupDialog, setShowGroupDialog] = useState(false)
  const [editingAction, setEditingAction] = useState<FavoriteAction | null>(null)
  const [actionForm, setActionForm] = useState({
    label: '',
    shortcut: '',
    groupId: ''
  })
  const [groupForm, setGroupForm] = useState({
    name: '',
    icon: ''
  })

  // Register keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      const action = settings.favoriteActions.find(
        a => a.shortcut && a.shortcut.toLowerCase() === e.key.toLowerCase() && e.ctrlKey
      )
      
      if (action && onActionClick) {
        e.preventDefault()
        onActionClick(action)
      }
    }

    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [settings.favoriteActions, onActionClick])

  const handleToggleFavorite = async (action: typeof availableActions[0]) => {
    const existing = settings.favoriteActions.find(a => a.actionId === action.id)
    
    if (existing) {
      await removeFavoriteAction(existing.id)
    } else {
      await addFavoriteAction({
        actionId: action.id,
        actionType: action.type,
        label: action.label,
        icon: action.icon,
        order: settings.favoriteActions.length
      })
    }
  }

  const handleUpdateAction = async () => {
    if (!editingAction) return

    await updateFavoriteAction(editingAction.id, {
      label: actionForm.label,
      shortcut: actionForm.shortcut,
      groupId: actionForm.groupId || undefined
    })

    setEditingAction(null)
    setActionForm({ label: '', shortcut: '', groupId: '' })
  }

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event
    
    if (over && active.id !== over.id) {
      const oldIndex = settings.favoriteActions.findIndex(a => a.id === active.id)
      const newIndex = settings.favoriteActions.findIndex(a => a.id === over.id)
      
      const newOrder = [...settings.favoriteActions]
      const [movedItem] = newOrder.splice(oldIndex, 1)
      newOrder.splice(newIndex, 0, movedItem)
      
      // Update order for all affected items
      for (let i = 0; i < newOrder.length; i++) {
        if (newOrder[i].order !== i) {
          await updateFavoriteAction(newOrder[i].id, { order: i })
        }
      }
    }
  }

  const handleCreateGroup = async () => {
    if (!groupForm.name) return

    await saveActionGroup({
      name: groupForm.name,
      icon: groupForm.icon,
      actions: [],
      order: settings.actionGroups.length
    })

    setGroupForm({ name: '', icon: '' })
    setShowGroupDialog(false)
  }

  const isFavorite = (actionId: string) => {
    return settings.favoriteActions.some(a => a.actionId === actionId)
  }

  return (
    <>
      {/* Quick Access Toolbar */}
      {settings.favoriteActions.length > 0 && (
        <QuickAccessToolbar
          actions={settings.favoriteActions}
          groups={settings.actionGroups}
          onActionClick={(action) => onActionClick?.(action)}
        />
      )}

      {/* Manage Button */}
      <Button
        variant="outline"
        size="sm"
        onClick={() => setShowManageDialog(true)}
      >
        <Star className="h-4 w-4 mr-1" />
        Manage Favorites
      </Button>

      {/* Manage Dialog */}
      <Dialog open={showManageDialog} onOpenChange={setShowManageDialog}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Manage Favorite Actions</DialogTitle>
          </DialogHeader>

          <Tabs defaultValue="favorites">
            <TabsList>
              <TabsTrigger value="favorites">My Favorites</TabsTrigger>
              <TabsTrigger value="available">Available Actions</TabsTrigger>
              <TabsTrigger value="shortcuts">Keyboard Shortcuts</TabsTrigger>
            </TabsList>

            <TabsContent value="favorites">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <p className="text-sm text-gray-500">
                    Drag to reorder your favorite actions
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowGroupDialog(true)}
                  >
                    <FolderPlus className="h-4 w-4 mr-1" />
                    Create Group
                  </Button>
                </div>

                <DndContext
                  collisionDetection={closestCenter}
                  onDragEnd={handleDragEnd}
                >
                  <SortableContext
                    items={settings.favoriteActions.map(a => a.id)}
                    strategy={verticalListSortingStrategy}
                  >
                    <ScrollArea className="h-[300px]">
                      <div className="space-y-2 p-1">
                        {settings.favoriteActions
                          .sort((a, b) => a.order - b.order)
                          .map((action) => (
                            <SortableActionItem
                              key={action.id}
                              action={action}
                              onEdit={() => {
                                setEditingAction(action)
                                setActionForm({
                                  label: action.label,
                                  shortcut: action.shortcut || '',
                                  groupId: action.groupId || ''
                                })
                              }}
                              onRemove={() => removeFavoriteAction(action.id)}
                            />
                          ))}
                      </div>
                    </ScrollArea>
                  </SortableContext>
                </DndContext>
              </div>
            </TabsContent>

            <TabsContent value="available">
              <ScrollArea className="h-[400px]">
                <div className="grid gap-2 p-1">
                  {availableActions.map((action) => (
                    <Card key={action.id} className="p-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            {action.icon && <span>{action.icon}</span>}
                            <span className="font-medium">{action.label}</span>
                            <Badge variant="outline" className="text-xs">
                              {action.type}
                            </Badge>
                          </div>
                          {action.description && (
                            <p className="text-sm text-gray-500 mt-1">
                              {action.description}
                            </p>
                          )}
                        </div>
                        <Button
                          variant={isFavorite(action.id) ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => handleToggleFavorite(action)}
                        >
                          {isFavorite(action.id) ? (
                            <>
                              <Star className="h-4 w-4 mr-1 fill-current" />
                              Favorited
                            </>
                          ) : (
                            <>
                              <StarOff className="h-4 w-4 mr-1" />
                              Add to Favorites
                            </>
                          )}
                        </Button>
                      </div>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="shortcuts">
              <div className="space-y-4">
                <p className="text-sm text-gray-500">
                  Assign keyboard shortcuts to your favorite actions for quick access
                </p>
                <ScrollArea className="h-[350px]">
                  <div className="space-y-2">
                    {settings.favoriteActions.map((action) => (
                      <Card key={action.id} className="p-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {action.icon && <span>{action.icon}</span>}
                            <span className="font-medium">{action.label}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="flex items-center gap-1 text-sm text-gray-500">
                              <Keyboard className="h-4 w-4" />
                              <kbd className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-800 rounded">
                                Ctrl
                              </kbd>
                              +
                            </div>
                            <Input
                              value={action.shortcut || ''}
                              onChange={(e) => {
                                const value = e.target.value.slice(-1).toUpperCase()
                                updateFavoriteAction(action.id, { shortcut: value })
                              }}
                              placeholder="Key"
                              className="w-16 text-center"
                              maxLength={1}
                            />
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            </TabsContent>
          </Tabs>

          {/* Edit Action Form */}
          {editingAction && (
            <div className="border-t pt-4 space-y-4">
              <h3 className="font-semibold">Edit Action</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="action-label">Label</Label>
                  <Input
                    id="action-label"
                    value={actionForm.label}
                    onChange={(e) => setActionForm({ ...actionForm, label: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="action-shortcut">Shortcut (Ctrl +)</Label>
                  <Input
                    id="action-shortcut"
                    value={actionForm.shortcut}
                    onChange={(e) => setActionForm({ ...actionForm, shortcut: e.target.value.slice(-1).toUpperCase() })}
                    placeholder="Key"
                    maxLength={1}
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="action-group">Group</Label>
                <select
                  id="action-group"
                  value={actionForm.groupId}
                  onChange={(e) => setActionForm({ ...actionForm, groupId: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="">No Group</option>
                  {settings.actionGroups.map((group) => (
                    <option key={group.id} value={group.id}>
                      {group.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setEditingAction(null)}>
                  Cancel
                </Button>
                <Button onClick={handleUpdateAction}>
                  Update Action
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Create Group Dialog */}
      <Dialog open={showGroupDialog} onOpenChange={setShowGroupDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Action Group</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="group-name">Group Name</Label>
              <Input
                id="group-name"
                value={groupForm.name}
                onChange={(e) => setGroupForm({ ...groupForm, name: e.target.value })}
                placeholder="e.g., Security Actions"
              />
            </div>
            <div>
              <Label htmlFor="group-icon">Icon (Emoji)</Label>
              <Input
                id="group-icon"
                value={groupForm.icon}
                onChange={(e) => setGroupForm({ ...groupForm, icon: e.target.value })}
                placeholder="e.g., 🛡️"
                maxLength={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowGroupDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateGroup}>
              Create Group
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}