import React, { useState, useEffect, useCallback } from 'react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { 
  Search, 
  Clock, 
  Hash, 
  AtSign,
  Command,
  ArrowRight,
  Sparkles
} from 'lucide-react'

interface AutoCompleteItem {
  id: string
  type: 'command' | 'entity' | 'recent' | 'suggestion'
  text: string
  displayText?: string
  icon?: React.ReactNode
  description?: string
  metadata?: Record<string, any>
  score?: number
}

interface AutoCompleteProps {
  value: string
  onSelect: (item: AutoCompleteItem) => void
  recentSearches?: string[]
  entities?: {
    incidents?: string[]
    agents?: string[]
    systems?: string[]
  }
  maxSuggestions?: number
  className?: string
}

export function AutoComplete({
  value,
  onSelect,
  recentSearches = [],
  entities = {},
  maxSuggestions = 8,
  className,
}: AutoCompleteProps) {
  const [suggestions, setSuggestions] = useState<AutoCompleteItem[]>([])
  const [selectedIndex, setSelectedIndex] = useState(0)

  // Fuzzy match function
  const fuzzyMatch = useCallback((pattern: string, text: string): number => {
    pattern = pattern.toLowerCase()
    text = text.toLowerCase()
    
    if (text === pattern) return 1.0
    if (text.includes(pattern)) return 0.8
    
    let score = 0
    let patternIndex = 0
    let prevMatchIndex = -1
    
    for (let i = 0; i < text.length && patternIndex < pattern.length; i++) {
      if (text[i] === pattern[patternIndex]) {
        score += 1
        if (prevMatchIndex !== -1 && i === prevMatchIndex + 1) {
          score += 0.5 // Bonus for consecutive matches
        }
        prevMatchIndex = i
        patternIndex++
      }
    }
    
    return patternIndex === pattern.length ? score / pattern.length : 0
  }, [])

  // Generate suggestions based on input
  useEffect(() => {
    if (!value || value.length < 2) {
      setSuggestions([])
      return
    }

    const allSuggestions: AutoCompleteItem[] = []
    const lowerValue = value.toLowerCase()

    // Command suggestions
    if (value.startsWith('/')) {
      const commandPattern = value.substring(1)
      const commands = [
        { command: '/incident new', desc: 'Create a new incident' },
        { command: '/incident status', desc: 'Check incident status' },
        { command: '/agent list', desc: 'List all agents' },
        { command: '/agent assign', desc: 'Assign to agent' },
        { command: '/help', desc: 'Show help' },
        { command: '/clear', desc: 'Clear chat' },
      ]

      commands.forEach(({ command, desc }) => {
        const score = fuzzyMatch(commandPattern, command.substring(1))
        if (score > 0.3) {
          allSuggestions.push({
            id: `cmd-${command}`,
            type: 'command',
            text: command,
            displayText: command,
            description: desc,
            icon: <Command className="h-3 w-3" />,
            score,
          })
        }
      })
    }

    // Entity recognition
    // Check for incident IDs
    if (lowerValue.includes('inc-') || lowerValue.includes('incident')) {
      const pattern = lowerValue.match(/inc-(\d*)/)?.[1] || ''
      const incidentSuggestions = [
        'INC-12345',
        'INC-12344',
        'INC-12343',
        'INC-12342',
        'INC-12341',
      ]
      
      incidentSuggestions.forEach(inc => {
        const score = fuzzyMatch(pattern || lowerValue, inc)
        if (score > 0.3 || lowerValue.includes('incident')) {
          allSuggestions.push({
            id: `incident-${inc}`,
            type: 'entity',
            text: inc,
            displayText: `${inc} - API Authentication Issue`,
            description: 'High Priority • In Progress',
            icon: <Hash className="h-3 w-3" />,
            score,
          })
        }
      })
    }

    // Check for agent mentions
    if (value.includes('@') || lowerValue.includes('agent')) {
      const pattern = value.split('@').pop() || ''
      const agentNames = entities.agents || ['alice', 'bob', 'charlie', 'diana']
      
      agentNames.forEach(agent => {
        const score = fuzzyMatch(pattern || lowerValue, agent)
        if (score > 0.3) {
          allSuggestions.push({
            id: `agent-${agent}`,
            type: 'entity',
            text: `@${agent}`,
            displayText: `@${agent}`,
            description: 'Security Team • Online',
            icon: <AtSign className="h-3 w-3" />,
            score,
          })
        }
      })
    }

    // Recent searches
    recentSearches.forEach(search => {
      const score = fuzzyMatch(value, search)
      if (score > 0.4 && search !== value) {
        allSuggestions.push({
          id: `recent-${search}`,
          type: 'recent',
          text: search,
          displayText: search,
          icon: <Clock className="h-3 w-3" />,
          score: score * 0.9, // Slightly lower priority than exact matches
        })
      }
    })

    // Intelligent suggestions based on partial input
    const intelligentSuggestions = generateIntelligentSuggestions(value)
    intelligentSuggestions.forEach((sugg, index) => {
      allSuggestions.push({
        id: `ai-${index}`,
        type: 'suggestion',
        text: sugg.text,
        displayText: sugg.text,
        description: sugg.description,
        icon: <Sparkles className="h-3 w-3" />,
        score: sugg.score || 0.5,
      })
    })

    // Sort by score and limit
    const sorted = allSuggestions
      .sort((a, b) => (b.score || 0) - (a.score || 0))
      .slice(0, maxSuggestions)

    setSuggestions(sorted)
    setSelectedIndex(0)
  }, [value, recentSearches, entities, fuzzyMatch, maxSuggestions])

  // Generate intelligent suggestions
  const generateIntelligentSuggestions = (input: string): Array<{
    text: string
    description?: string
    score?: number
  }> => {
    const suggestions: Array<{ text: string; description?: string; score?: number }> = []
    const lower = input.toLowerCase()

    // Context-aware completions
    if (lower.includes('create') && !lower.includes('incident')) {
      suggestions.push({
        text: 'create new incident',
        description: 'Start incident creation flow',
        score: 0.8,
      })
    }

    if (lower.includes('check') || lower.includes('status')) {
      suggestions.push({
        text: 'check incident status',
        description: 'View incident details',
        score: 0.8,
      })
    }

    if (lower.includes('assign')) {
      suggestions.push({
        text: 'assign to available agent',
        description: 'Find and assign to agent',
        score: 0.8,
      })
    }

    if (lower.includes('high') || lower.includes('critical')) {
      suggestions.push({
        text: 'show high priority incidents',
        description: 'Filter by priority',
        score: 0.7,
      })
    }

    return suggestions
  }

  if (suggestions.length === 0) {
    return null
  }

  return (
    <div className={cn('absolute bottom-full mb-2 w-full', className)}>
      <div className="bg-popover border rounded-lg shadow-lg max-h-64 overflow-y-auto">
        <div className="p-2 border-b">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Search className="h-3 w-3" />
            <span>Suggestions</span>
            <kbd className="ml-auto px-1.5 py-0.5 text-[10px] bg-muted rounded">Tab</kbd>
            <span className="text-[10px]">to complete</span>
          </div>
        </div>
        
        <div className="py-1">
          {suggestions.map((suggestion, index) => (
            <button
              key={suggestion.id}
              onClick={() => onSelect(suggestion)}
              onMouseEnter={() => setSelectedIndex(index)}
              className={cn(
                'w-full px-3 py-2 flex items-start gap-3 hover:bg-accent transition-colors',
                index === selectedIndex && 'bg-accent'
              )}
            >
              <span className="text-muted-foreground mt-0.5">
                {suggestion.icon}
              </span>
              <div className="flex-1 text-left">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">
                    {suggestion.displayText || suggestion.text}
                  </span>
                  {suggestion.type === 'recent' && (
                    <Badge variant="secondary" className="text-[10px] px-1 py-0">
                      Recent
                    </Badge>
                  )}
                  {suggestion.type === 'suggestion' && suggestion.score && suggestion.score > 0.7 && (
                    <Badge variant="secondary" className="text-[10px] px-1 py-0">
                      AI
                    </Badge>
                  )}
                </div>
                {suggestion.description && (
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {suggestion.description}
                  </p>
                )}
              </div>
              {index === selectedIndex && (
                <ArrowRight className="h-3 w-3 text-muted-foreground mt-0.5" />
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

// Export helper hook for managing autocomplete state
export function useAutoComplete() {
  const [recentSearches, setRecentSearches] = useState<string[]>([])

  const addToRecent = useCallback((search: string) => {
    setRecentSearches(prev => {
      const filtered = prev.filter(s => s !== search)
      return [search, ...filtered].slice(0, 10)
    })
  }, [])

  return {
    recentSearches,
    addToRecent,
  }
}