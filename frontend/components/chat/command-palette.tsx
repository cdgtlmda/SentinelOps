import React, { useState, useEffect, useCallback } from 'react'
import { cn } from '@/lib/utils'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Command, 
  Search, 
  Sparkles,
  ArrowRight,
  Info,
  History,
  Keyboard,
  Hash,
  AtSign,
  Calendar,
  Filter
} from 'lucide-react'
import { COMMAND_REGISTRY, parseCommand, getCommandSuggestions } from '@/lib/ai-commands'

interface CommandPaletteProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCommandExecute: (command: string) => void
  commandHistory?: string[]
}

interface CommandParameter {
  name: string
  value: string
  type: 'text' | 'select' | 'number' | 'date'
  options?: string[]
  required?: boolean
  description?: string
}

export function CommandPalette({
  open,
  onOpenChange,
  onCommandExecute,
  commandHistory = [],
}: CommandPaletteProps) {
  const [search, setSearch] = useState('')
  const [selectedCommand, setSelectedCommand] = useState<string | null>(null)
  const [selectedSubcommand, setSelectedSubcommand] = useState<string | null>(null)
  const [parameters, setParameters] = useState<Record<string, string>>({})
  const [naturalLanguageInput, setNaturalLanguageInput] = useState('')
  const [activeTab, setActiveTab] = useState<'commands' | 'natural'>('commands')

  // Reset state when dialog closes
  useEffect(() => {
    if (!open) {
      setSearch('')
      setSelectedCommand(null)
      setSelectedSubcommand(null)
      setParameters({})
      setNaturalLanguageInput('')
      setActiveTab('commands')
    }
  }, [open])

  // Get filtered commands based on search
  const filteredCommands = Object.entries(COMMAND_REGISTRY).filter(([cmd]) =>
    cmd.toLowerCase().includes(search.toLowerCase())
  )

  // Handle command selection
  const handleCommandSelect = (command: string) => {
    setSelectedCommand(command)
    setSelectedSubcommand(null)
    setParameters({})
  }

  // Handle subcommand selection
  const handleSubcommandSelect = (subcommand: string) => {
    setSelectedSubcommand(subcommand)
    
    // Initialize parameters for the subcommand
    const commandInfo = COMMAND_REGISTRY[selectedCommand!]
    const params = commandInfo.parameters[subcommand] || []
    const initialParams: Record<string, string> = {}
    params.forEach(param => {
      initialParams[param] = ''
    })
    setParameters(initialParams)
  }

  // Build and execute command
  const executeCommand = () => {
    let command = selectedCommand
    if (selectedSubcommand) {
      command += ` ${selectedSubcommand}`
    }
    
    // Add parameters
    Object.entries(parameters).forEach(([key, value]) => {
      if (value) {
        command += ` ${key}="${value}"`
      }
    })
    
    onCommandExecute(command)
    onOpenChange(false)
  }

  // Parse and execute natural language command
  const executeNaturalLanguage = () => {
    // Simple natural language to command conversion
    const lower = naturalLanguageInput.toLowerCase()
    let command = naturalLanguageInput
    
    // Pattern matching for common phrases
    if (lower.includes('create') && lower.includes('incident')) {
      command = '/incident new'
      if (lower.includes('high') || lower.includes('critical')) {
        command += ' priority="high"'
      }
    } else if (lower.includes('check') && lower.includes('status')) {
      command = '/incident status'
      const incMatch = lower.match(/inc-\d+/i)
      if (incMatch) {
        command += ` id="${incMatch[0]}"`
      }
    } else if (lower.includes('assign') && lower.includes('agent')) {
      command = '/agent assign'
    }
    
    onCommandExecute(command)
    onOpenChange(false)
  }

  // Get parameter input fields
  const renderParameterInputs = () => {
    if (!selectedCommand || !selectedSubcommand) return null
    
    const commandInfo = COMMAND_REGISTRY[selectedCommand]
    const params = commandInfo.parameters[selectedSubcommand] || []
    
    return params.map(param => {
      // Determine parameter type and metadata
      const paramInfo = getParameterInfo(param, selectedCommand, selectedSubcommand)
      
      return (
        <div key={param} className="space-y-2">
          <Label htmlFor={param} className="text-sm">
            {paramInfo.label}
            {paramInfo.required && <span className="text-destructive ml-1">*</span>}
          </Label>
          
          {paramInfo.type === 'select' ? (
            <select
              id={param}
              value={parameters[param] || ''}
              onChange={(e) => setParameters(prev => ({ ...prev, [param]: e.target.value }))}
              className="w-full px-3 py-2 border rounded-md bg-background"
            >
              <option value="">Select {paramInfo.label}</option>
              {paramInfo.options?.map(option => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          ) : (
            <Input
              id={param}
              type={paramInfo.type}
              value={parameters[param] || ''}
              onChange={(e) => setParameters(prev => ({ ...prev, [param]: e.target.value }))}
              placeholder={paramInfo.placeholder}
              className="w-full"
            />
          )}
          
          {paramInfo.description && (
            <p className="text-xs text-muted-foreground">{paramInfo.description}</p>
          )}
        </div>
      )
    })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Command className="h-5 w-5" />
            Command Palette
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'commands' | 'natural')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="commands" className="gap-2">
              <Command className="h-4 w-4" />
              Commands
            </TabsTrigger>
            <TabsTrigger value="natural" className="gap-2">
              <Sparkles className="h-4 w-4" />
              Natural Language
            </TabsTrigger>
          </TabsList>

          <TabsContent value="commands" className="space-y-4">
            {!selectedCommand ? (
              <>
                {/* Command Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search commands..."
                    className="pl-9"
                  />
                </div>

                {/* Command List */}
                <ScrollArea className="h-[300px] border rounded-lg p-4">
                  <div className="space-y-2">
                    {filteredCommands.map(([cmd, info]) => (
                      <button
                        key={cmd}
                        onClick={() => handleCommandSelect(cmd)}
                        className="w-full p-3 text-left hover:bg-accent rounded-lg transition-colors group"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium text-sm">{cmd}</p>
                            <p className="text-xs text-muted-foreground mt-1">
                              {info.description}
                            </p>
                          </div>
                          <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                      </button>
                    ))}
                  </div>
                </ScrollArea>

                {/* Recent Commands */}
                {commandHistory.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <History className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm text-muted-foreground">Recent Commands</span>
                    </div>
                    <div className="space-y-1">
                      {commandHistory.slice(0, 3).map((cmd, index) => (
                        <button
                          key={index}
                          onClick={() => {
                            onCommandExecute(cmd)
                            onOpenChange(false)
                          }}
                          className="w-full p-2 text-left text-sm hover:bg-accent rounded transition-colors"
                        >
                          <code className="text-xs">{cmd}</code>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : !selectedSubcommand ? (
              <>
                {/* Subcommand Selection */}
                <div className="space-y-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedCommand(null)}
                    className="gap-2"
                  >
                    ← Back
                  </Button>
                  
                  <h3 className="font-medium text-lg">{selectedCommand}</h3>
                  
                  <div className="space-y-2">
                    {Object.entries(COMMAND_REGISTRY[selectedCommand].subcommands).map(([sub, desc]) => (
                      <button
                        key={sub}
                        onClick={() => handleSubcommandSelect(sub)}
                        className="w-full p-3 text-left hover:bg-accent rounded-lg transition-colors"
                      >
                        <p className="font-medium text-sm">{selectedCommand} {sub}</p>
                        <p className="text-xs text-muted-foreground mt-1">{desc}</p>
                      </button>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <>
                {/* Parameter Input */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedSubcommand(null)}
                      className="gap-2"
                    >
                      ← Back
                    </Button>
                    
                    <Badge variant="secondary">
                      {selectedCommand} {selectedSubcommand}
                    </Badge>
                  </div>
                  
                  <div className="space-y-4">
                    {renderParameterInputs()}
                  </div>
                  
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                      Cancel
                    </Button>
                    <Button onClick={executeCommand}>
                      Execute Command
                    </Button>
                  </div>
                </div>
              </>
            )}
          </TabsContent>

          <TabsContent value="natural" className="space-y-4">
            <div className="space-y-4">
              <div>
                <Label htmlFor="natural-input">Describe what you want to do</Label>
                <div className="mt-2">
                  <textarea
                    id="natural-input"
                    value={naturalLanguageInput}
                    onChange={(e) => setNaturalLanguageInput(e.target.value)}
                    placeholder="e.g., Create a high priority incident for the API authentication issue"
                    className="w-full min-h-[100px] p-3 border rounded-lg bg-background resize-none"
                  />
                </div>
              </div>

              {/* Examples */}
              <div>
                <p className="text-sm text-muted-foreground mb-2">Examples:</p>
                <div className="space-y-2">
                  {[
                    'Create a critical incident for database connection timeout',
                    'Check status of incident INC-12345',
                    'Show all high priority incidents',
                    'Assign this to an available agent',
                  ].map((example, index) => (
                    <button
                      key={index}
                      onClick={() => setNaturalLanguageInput(example)}
                      className="w-full p-2 text-left text-sm hover:bg-accent rounded transition-colors"
                    >
                      <span className="text-muted-foreground">"</span>
                      {example}
                      <span className="text-muted-foreground">"</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => onOpenChange(false)}>
                  Cancel
                </Button>
                <Button 
                  onClick={executeNaturalLanguage}
                  disabled={!naturalLanguageInput.trim()}
                >
                  Execute
                </Button>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* Keyboard Shortcuts */}
        <div className="mt-4 pt-4 border-t">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Keyboard className="h-3 w-3" />
            <span>Press</span>
            <kbd className="px-1.5 py-0.5 bg-muted rounded">⌘K</kbd>
            <span>to open • </span>
            <kbd className="px-1.5 py-0.5 bg-muted rounded">Esc</kbd>
            <span>to close</span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

// Helper function to get parameter information
function getParameterInfo(
  param: string,
  command: string,
  subcommand: string
): {
  label: string
  type: 'text' | 'select' | 'number' | 'date'
  options?: string[]
  placeholder?: string
  description?: string
  required?: boolean
} {
  // Define parameter metadata
  const parameterMetadata: Record<string, any> = {
    priority: {
      label: 'Priority',
      type: 'select',
      options: ['critical', 'high', 'medium', 'low'],
      required: true,
    },
    title: {
      label: 'Title',
      type: 'text',
      placeholder: 'Brief description of the issue',
      required: true,
    },
    description: {
      label: 'Description',
      type: 'text',
      placeholder: 'Detailed description',
    },
    id: {
      label: 'Incident ID',
      type: 'text',
      placeholder: 'e.g., INC-12345',
      required: true,
    },
    agent: {
      label: 'Agent',
      type: 'text',
      placeholder: 'Agent name or @mention',
      required: true,
    },
    filter: {
      label: 'Filter',
      type: 'text',
      placeholder: 'e.g., status:open priority:high',
    },
    limit: {
      label: 'Limit',
      type: 'number',
      placeholder: 'Number of results',
    },
    resolution: {
      label: 'Resolution',
      type: 'text',
      placeholder: 'How was this resolved?',
      required: true,
    },
  }

  return parameterMetadata[param] || {
    label: param.charAt(0).toUpperCase() + param.slice(1),
    type: 'text',
    placeholder: `Enter ${param}`,
  }
}

// Export hook for keyboard shortcut
export function useCommandPalette() {
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setIsOpen(true)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return {
    isOpen,
    setIsOpen,
  }
}