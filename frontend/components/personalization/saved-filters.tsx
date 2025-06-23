'use client'

import { useState } from 'react'
import { SavedFilter } from '@/types/personalization'
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
import { 
  Filter, 
  Save, 
  X, 
  Share2, 
  Star, 
  StarOff,
  Tag,
  Trash2,
  Edit,
  Copy,
  Check
} from 'lucide-react'

interface SavedFiltersProps {
  currentFilter?: Record<string, any>
  entityType?: 'incidents' | 'agents' | 'activities' | 'all'
  onApplyFilter?: (filter: SavedFilter) => void
  onDeleteFilter?: (filterId: string) => void
}

interface FilterQuickAccessProps {
  filters: SavedFilter[]
  activeFilterId?: string
  onSelectFilter: (filter: SavedFilter) => void
}

function FilterQuickAccess({ filters, activeFilterId, onSelectFilter }: FilterQuickAccessProps) {
  return (
    <div className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-900 rounded-lg">
      <Filter className="h-4 w-4 text-gray-500" />
      <div className="flex gap-1 overflow-x-auto">
        {filters.map((filter) => (
          <Button
            key={filter.id}
            variant={activeFilterId === filter.id ? 'default' : 'ghost'}
            size="sm"
            onClick={() => onSelectFilter(filter)}
            className="whitespace-nowrap"
          >
            {filter.isDefault && <Star className="h-3 w-3 mr-1" />}
            {filter.name}
          </Button>
        ))}
      </div>
    </div>
  )
}

export function SavedFilters({ 
  currentFilter, 
  entityType = 'all',
  onApplyFilter,
  onDeleteFilter 
}: SavedFiltersProps) {
  const { 
    settings, 
    saveFilter, 
    updateFilter, 
    deleteFilter: deleteFilterFromStore 
  } = usePersonalization()
  
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [showManageDialog, setShowManageDialog] = useState(false)
  const [editingFilter, setEditingFilter] = useState<SavedFilter | null>(null)
  const [filterForm, setFilterForm] = useState({
    name: '',
    description: '',
    category: '',
    tags: '',
    isDefault: false,
    isShared: false
  })

  const relevantFilters = settings.savedFilters.filter(
    f => f.entityType === entityType || f.entityType === 'all' || entityType === 'all'
  )

  const handleSaveFilter = async () => {
    if (!currentFilter || !filterForm.name) return

    try {
      const newFilter = await saveFilter({
        name: filterForm.name,
        description: filterForm.description,
        filter: currentFilter,
        entityType,
        isDefault: filterForm.isDefault,
        isShared: filterForm.isShared,
        category: filterForm.category,
        tags: filterForm.tags.split(',').map(t => t.trim()).filter(Boolean)
      })

      // If set as default, update other filters
      if (filterForm.isDefault) {
        for (const filter of relevantFilters) {
          if (filter.id !== newFilter.id && filter.isDefault) {
            await updateFilter(filter.id, { isDefault: false })
          }
        }
      }

      setShowSaveDialog(false)
      setFilterForm({
        name: '',
        description: '',
        category: '',
        tags: '',
        isDefault: false,
        isShared: false
      })
    } catch (error) {
      console.error('Failed to save filter:', error)
    }
  }

  const handleUpdateFilter = async () => {
    if (!editingFilter) return

    try {
      await updateFilter(editingFilter.id, {
        name: filterForm.name,
        description: filterForm.description,
        category: filterForm.category,
        tags: filterForm.tags.split(',').map(t => t.trim()).filter(Boolean),
        isDefault: filterForm.isDefault,
        isShared: filterForm.isShared
      })

      // If set as default, update other filters
      if (filterForm.isDefault) {
        for (const filter of relevantFilters) {
          if (filter.id !== editingFilter.id && filter.isDefault) {
            await updateFilter(filter.id, { isDefault: false })
          }
        }
      }

      setEditingFilter(null)
      setShowManageDialog(false)
    } catch (error) {
      console.error('Failed to update filter:', error)
    }
  }

  const handleDeleteFilter = async (filterId: string) => {
    try {
      await deleteFilterFromStore(filterId)
      onDeleteFilter?.(filterId)
    } catch (error) {
      console.error('Failed to delete filter:', error)
    }
  }

  const handleEditFilter = (filter: SavedFilter) => {
    setEditingFilter(filter)
    setFilterForm({
      name: filter.name,
      description: filter.description || '',
      category: filter.category || '',
      tags: filter.tags?.join(', ') || '',
      isDefault: filter.isDefault || false,
      isShared: filter.isShared || false
    })
  }

  const handleDuplicateFilter = async (filter: SavedFilter) => {
    try {
      await saveFilter({
        name: `${filter.name} (Copy)`,
        description: filter.description,
        filter: filter.filter,
        entityType: filter.entityType,
        category: filter.category,
        tags: filter.tags
      })
    } catch (error) {
      console.error('Failed to duplicate filter:', error)
    }
  }

  const groupedFilters = relevantFilters.reduce((acc, filter) => {
    const category = filter.category || 'Uncategorized'
    if (!acc[category]) {
      acc[category] = []
    }
    acc[category].push(filter)
    return acc
  }, {} as Record<string, SavedFilter[]>)

  return (
    <>
      {/* Quick Access Bar */}
      {relevantFilters.length > 0 && (
        <FilterQuickAccess
          filters={relevantFilters.slice(0, 5)}
          onSelectFilter={(filter) => onApplyFilter?.(filter)}
        />
      )}

      {/* Action Buttons */}
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowSaveDialog(true)}
          disabled={!currentFilter}
        >
          <Save className="h-4 w-4 mr-1" />
          Save Filter
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowManageDialog(true)}
        >
          <Filter className="h-4 w-4 mr-1" />
          Manage Filters
        </Button>
      </div>

      {/* Save Filter Dialog */}
      <Dialog open={showSaveDialog} onOpenChange={setShowSaveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save Filter</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="filter-name">Name</Label>
              <Input
                id="filter-name"
                value={filterForm.name}
                onChange={(e) => setFilterForm({ ...filterForm, name: e.target.value })}
                placeholder="e.g., High Priority Incidents"
              />
            </div>
            <div>
              <Label htmlFor="filter-description">Description</Label>
              <Textarea
                id="filter-description"
                value={filterForm.description}
                onChange={(e) => setFilterForm({ ...filterForm, description: e.target.value })}
                placeholder="Optional description"
                rows={2}
              />
            </div>
            <div>
              <Label htmlFor="filter-category">Category</Label>
              <Input
                id="filter-category"
                value={filterForm.category}
                onChange={(e) => setFilterForm({ ...filterForm, category: e.target.value })}
                placeholder="e.g., Security, Performance"
              />
            </div>
            <div>
              <Label htmlFor="filter-tags">Tags</Label>
              <Input
                id="filter-tags"
                value={filterForm.tags}
                onChange={(e) => setFilterForm({ ...filterForm, tags: e.target.value })}
                placeholder="Comma-separated tags"
              />
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={filterForm.isDefault}
                  onChange={(e) => setFilterForm({ ...filterForm, isDefault: e.target.checked })}
                  className="mr-2"
                />
                Set as default
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={filterForm.isShared}
                  onChange={(e) => setFilterForm({ ...filterForm, isShared: e.target.checked })}
                  className="mr-2"
                />
                Share with team
              </label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSaveDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveFilter}>
              Save Filter
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Manage Filters Dialog */}
      <Dialog open={showManageDialog} onOpenChange={setShowManageDialog}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Manage Filters</DialogTitle>
          </DialogHeader>
          
          {editingFilter ? (
            <div className="space-y-4">
              <div>
                <Label htmlFor="edit-filter-name">Name</Label>
                <Input
                  id="edit-filter-name"
                  value={filterForm.name}
                  onChange={(e) => setFilterForm({ ...filterForm, name: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="edit-filter-description">Description</Label>
                <Textarea
                  id="edit-filter-description"
                  value={filterForm.description}
                  onChange={(e) => setFilterForm({ ...filterForm, description: e.target.value })}
                  rows={2}
                />
              </div>
              <div>
                <Label htmlFor="edit-filter-category">Category</Label>
                <Input
                  id="edit-filter-category"
                  value={filterForm.category}
                  onChange={(e) => setFilterForm({ ...filterForm, category: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="edit-filter-tags">Tags</Label>
                <Input
                  id="edit-filter-tags"
                  value={filterForm.tags}
                  onChange={(e) => setFilterForm({ ...filterForm, tags: e.target.value })}
                />
              </div>
              <div className="flex items-center gap-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filterForm.isDefault}
                    onChange={(e) => setFilterForm({ ...filterForm, isDefault: e.target.checked })}
                    className="mr-2"
                  />
                  Set as default
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filterForm.isShared}
                    onChange={(e) => setFilterForm({ ...filterForm, isShared: e.target.checked })}
                    className="mr-2"
                  />
                  Share with team
                </label>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setEditingFilter(null)}>
                  Cancel
                </Button>
                <Button onClick={handleUpdateFilter}>
                  Update Filter
                </Button>
              </div>
            </div>
          ) : (
            <Tabs defaultValue="all">
              <TabsList>
                <TabsTrigger value="all">All Categories</TabsTrigger>
                {Object.keys(groupedFilters).map((category) => (
                  <TabsTrigger key={category} value={category}>
                    {category}
                  </TabsTrigger>
                ))}
              </TabsList>
              
              <TabsContent value="all">
                <ScrollArea className="h-[400px]">
                  <div className="space-y-4 p-4">
                    {Object.entries(groupedFilters).map(([category, filters]) => (
                      <div key={category}>
                        <h3 className="font-semibold mb-2">{category}</h3>
                        <div className="grid gap-2">
                          {filters.map((filter) => (
                            <Card key={filter.id} className="p-3">
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2">
                                    <h4 className="font-medium">{filter.name}</h4>
                                    {filter.isDefault && (
                                      <Badge variant="secondary" className="text-xs">
                                        <Star className="h-3 w-3 mr-1" />
                                        Default
                                      </Badge>
                                    )}
                                    {filter.isShared && (
                                      <Badge variant="outline" className="text-xs">
                                        <Share2 className="h-3 w-3 mr-1" />
                                        Shared
                                      </Badge>
                                    )}
                                  </div>
                                  {filter.description && (
                                    <p className="text-sm text-gray-500 mt-1">
                                      {filter.description}
                                    </p>
                                  )}
                                  {filter.tags && filter.tags.length > 0 && (
                                    <div className="flex gap-1 mt-2">
                                      {filter.tags.map((tag) => (
                                        <Badge key={tag} variant="outline" className="text-xs">
                                          {tag}
                                        </Badge>
                                      ))}
                                    </div>
                                  )}
                                </div>
                                <div className="flex gap-1">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => onApplyFilter?.(filter)}
                                  >
                                    <Check className="h-4 w-4" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleEditFilter(filter)}
                                  >
                                    <Edit className="h-4 w-4" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleDuplicateFilter(filter)}
                                  >
                                    <Copy className="h-4 w-4" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleDeleteFilter(filter.id)}
                                  >
                                    <Trash2 className="h-4 w-4" />
                                  </Button>
                                </div>
                              </div>
                            </Card>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </TabsContent>
              
              {Object.entries(groupedFilters).map(([category, filters]) => (
                <TabsContent key={category} value={category}>
                  <ScrollArea className="h-[400px]">
                    <div className="grid gap-2 p-4">
                      {filters.map((filter) => (
                        <Card key={filter.id} className="p-3">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <h4 className="font-medium">{filter.name}</h4>
                                {filter.isDefault && (
                                  <Badge variant="secondary" className="text-xs">
                                    <Star className="h-3 w-3 mr-1" />
                                    Default
                                  </Badge>
                                )}
                                {filter.isShared && (
                                  <Badge variant="outline" className="text-xs">
                                    <Share2 className="h-3 w-3 mr-1" />
                                    Shared
                                  </Badge>
                                )}
                              </div>
                              {filter.description && (
                                <p className="text-sm text-gray-500 mt-1">
                                  {filter.description}
                                </p>
                              )}
                              {filter.tags && filter.tags.length > 0 && (
                                <div className="flex gap-1 mt-2">
                                  {filter.tags.map((tag) => (
                                    <Badge key={tag} variant="outline" className="text-xs">
                                      {tag}
                                    </Badge>
                                  ))}
                                </div>
                              )}
                            </div>
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => onApplyFilter?.(filter)}
                              >
                                <Check className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEditFilter(filter)}
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDuplicateFilter(filter)}
                              >
                                <Copy className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDeleteFilter(filter.id)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        </Card>
                      ))}
                    </div>
                  </ScrollArea>
                </TabsContent>
              ))}
            </Tabs>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}