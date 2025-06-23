'use client'

import { useState, useEffect } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { 
  Search,
  ChevronDown,
  ChevronUp,
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  Filter,
  X,
  HelpCircle,
  Lightbulb,
  AlertCircle,
  Shield,
  Zap,
  Users,
  BarChart3,
  Settings,
  ExternalLink
} from 'lucide-react'

interface FAQItem {
  id: string
  question: string
  answer: string
  category: string
  tags: string[]
  helpful?: number
  notHelpful?: number
  relatedQuestions?: string[]
  lastUpdated?: Date
  views?: number
}

interface FAQCategory {
  id: string
  name: string
  icon: React.ElementType
  description: string
  itemCount: number
}

const FAQ_CATEGORIES: FAQCategory[] = [
  {
    id: 'general',
    name: 'General',
    icon: HelpCircle,
    description: 'Common questions about SentinelOps',
    itemCount: 15
  },
  {
    id: 'incidents',
    name: 'Incidents',
    icon: AlertCircle,
    description: 'Managing and responding to incidents',
    itemCount: 12
  },
  {
    id: 'agents',
    name: 'AI Agents',
    icon: Users,
    description: 'Understanding AI agent capabilities',
    itemCount: 8
  },
  {
    id: 'security',
    name: 'Security',
    icon: Shield,
    description: 'Security features and best practices',
    itemCount: 10
  },
  {
    id: 'integrations',
    name: 'Integrations',
    icon: Zap,
    description: 'Connecting with other tools',
    itemCount: 6
  },
  {
    id: 'analytics',
    name: 'Analytics',
    icon: BarChart3,
    description: 'Reports and data analysis',
    itemCount: 9
  },
  {
    id: 'settings',
    name: 'Settings',
    icon: Settings,
    description: 'Configuration and customization',
    itemCount: 7
  }
]

const FAQ_ITEMS: FAQItem[] = [
  {
    id: 'faq-1',
    question: 'What is SentinelOps?',
    answer: 'SentinelOps is an AI-powered security operations platform that automatically detects, analyzes, and responds to security incidents. It uses multiple specialized AI agents working together to provide comprehensive security coverage.',
    category: 'general',
    tags: ['overview', 'basics', 'getting-started'],
    helpful: 142,
    notHelpful: 3,
    views: 1523
  },
  {
    id: 'faq-2',
    question: 'How do AI agents work together?',
    answer: 'SentinelOps uses four types of specialized AI agents: Detection agents monitor for threats, Analysis agents investigate incidents, Remediation agents execute fixes, and Communication agents handle notifications. These agents are coordinated by an Orchestration agent that ensures efficient collaboration.',
    category: 'agents',
    tags: ['agents', 'collaboration', 'architecture'],
    helpful: 98,
    notHelpful: 5,
    relatedQuestions: ['faq-3', 'faq-4'],
    views: 876
  },
  {
    id: 'faq-3',
    question: 'What are incident severity levels?',
    answer: 'Incidents are classified into four severity levels: Critical (immediate action required), High (significant impact), Medium (moderate impact), and Low (minor impact). Severity is determined automatically based on factors like potential damage, affected resources, and threat indicators.',
    category: 'incidents',
    tags: ['incidents', 'severity', 'classification'],
    helpful: 76,
    notHelpful: 2,
    views: 654
  },
  {
    id: 'faq-4',
    question: 'Can I customize automated responses?',
    answer: 'Yes, you can customize automated responses through approval workflows and remediation policies. Set conditions for automatic approval, require manual approval for critical actions, and create custom remediation playbooks for specific incident types.',
    category: 'settings',
    tags: ['automation', 'customization', 'remediation'],
    helpful: 65,
    notHelpful: 8,
    views: 432
  },
  {
    id: 'faq-5',
    question: 'How do I integrate with existing security tools?',
    answer: 'SentinelOps provides REST APIs, webhooks, and pre-built integrations for popular security tools. You can connect SIEM systems, ticketing platforms, and communication tools through our integration marketplace or custom API endpoints.',
    category: 'integrations',
    tags: ['api', 'integrations', 'connectivity'],
    helpful: 54,
    notHelpful: 4,
    relatedQuestions: ['faq-6'],
    views: 398
  },
  {
    id: 'faq-6',
    question: 'What data does SentinelOps collect?',
    answer: 'SentinelOps collects security event logs, system metrics, network traffic patterns, and cloud resource configurations. All data is encrypted in transit and at rest, with configurable retention policies and compliance with major security standards.',
    category: 'security',
    tags: ['data', 'privacy', 'compliance'],
    helpful: 89,
    notHelpful: 1,
    views: 765
  }
]

interface FAQIntegrationProps {
  embedded?: boolean
  defaultCategory?: string
  maxItems?: number
  onQuestionClick?: (item: FAQItem) => void
}

export function FAQIntegration({
  embedded = false,
  defaultCategory,
  maxItems,
  onQuestionClick
}: FAQIntegrationProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(defaultCategory || null)
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set())
  const [helpfulItems, setHelpfulItems] = useState<Set<string>>(new Set())
  const [notHelpfulItems, setNotHelpfulItems] = useState<Set<string>>(new Set())
  const [showFilters, setShowFilters] = useState(false)

  // Filter FAQs based on search and category
  const filteredFAQs = FAQ_ITEMS.filter(item => {
    const matchesSearch = searchQuery
      ? item.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.answer.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      : true

    const matchesCategory = selectedCategory
      ? item.category === selectedCategory
      : true

    return matchesSearch && matchesCategory
  }).slice(0, maxItems)

  // Group FAQs by category
  const groupedFAQs = filteredFAQs.reduce((acc, item) => {
    if (!acc[item.category]) {
      acc[item.category] = []
    }
    acc[item.category].push(item)
    return acc
  }, {} as Record<string, FAQItem[]>)

  const toggleExpanded = (itemId: string) => {
    const newExpanded = new Set(expandedItems)
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId)
    } else {
      newExpanded.add(itemId)
    }
    setExpandedItems(newExpanded)
  }

  const handleHelpful = (itemId: string, helpful: boolean) => {
    if (helpful) {
      setHelpfulItems(new Set([...helpfulItems, itemId]))
      const newNotHelpful = new Set(notHelpfulItems)
      newNotHelpful.delete(itemId)
      setNotHelpfulItems(newNotHelpful)
    } else {
      setNotHelpfulItems(new Set([...notHelpfulItems, itemId]))
      const newHelpful = new Set(helpfulItems)
      newHelpful.delete(itemId)
      setHelpfulItems(newHelpful)
    }
    
    // Track feedback
    console.log('FAQ feedback:', itemId, helpful)
  }

  const handleQuestionClick = (item: FAQItem) => {
    toggleExpanded(item.id)
    if (onQuestionClick) {
      onQuestionClick(item)
    }
    
    // Track view
    console.log('FAQ viewed:', item.id)
  }

  const containerClass = embedded 
    ? '' 
    : 'max-w-4xl mx-auto p-6'

  return (
    <div className={containerClass}>
      {/* Header */}
      {!embedded && (
        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-2">Frequently Asked Questions</h1>
          <p className="text-gray-500">
            Find answers to common questions about SentinelOps
          </p>
        </div>
      )}

      {/* Search and Filters */}
      <div className="mb-6 space-y-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search questions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="h-4 w-4 mr-1" />
            Filters
            {selectedCategory && (
              <Badge variant="secondary" className="ml-1">1</Badge>
            )}
          </Button>
        </div>

        {/* Category Filters */}
        {showFilters && (
          <Card className="p-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-medium text-sm">Categories</h3>
                {selectedCategory && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedCategory(null)}
                  >
                    Clear
                  </Button>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {FAQ_CATEGORIES.map((category) => {
                  const Icon = category.icon
                  return (
                    <Button
                      key={category.id}
                      variant={selectedCategory === category.id ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setSelectedCategory(
                        selectedCategory === category.id ? null : category.id
                      )}
                    >
                      <Icon className="h-4 w-4 mr-1" />
                      {category.name}
                      <Badge variant="secondary" className="ml-1">
                        {category.itemCount}
                      </Badge>
                    </Button>
                  )
                })}
              </div>
            </div>
          </Card>
        )}
      </div>

      {/* FAQ List */}
      <div className="space-y-4">
        {searchQuery && filteredFAQs.length === 0 ? (
          <Card className="p-6 text-center">
            <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-3" />
            <h3 className="font-medium mb-1">No results found</h3>
            <p className="text-sm text-gray-500">
              Try different search terms or browse by category
            </p>
          </Card>
        ) : selectedCategory ? (
          // Show filtered items
          <div className="space-y-2">
            {filteredFAQs.map((item) => (
              <FAQItemCard
                key={item.id}
                item={item}
                isExpanded={expandedItems.has(item.id)}
                isHelpful={helpfulItems.has(item.id)}
                isNotHelpful={notHelpfulItems.has(item.id)}
                onToggle={() => handleQuestionClick(item)}
                onHelpful={(helpful) => handleHelpful(item.id, helpful)}
              />
            ))}
          </div>
        ) : (
          // Show grouped by category
          Object.entries(groupedFAQs).map(([categoryId, items]) => {
            const category = FAQ_CATEGORIES.find(c => c.id === categoryId)
            if (!category) return null
            const Icon = category.icon

            return (
              <div key={categoryId} className="space-y-2">
                <div className="flex items-center gap-2 mb-3">
                  <Icon className="h-5 w-5 text-gray-500" />
                  <h2 className="font-semibold">{category.name}</h2>
                  <Badge variant="secondary">{items.length}</Badge>
                </div>
                {items.map((item) => (
                  <FAQItemCard
                    key={item.id}
                    item={item}
                    isExpanded={expandedItems.has(item.id)}
                    isHelpful={helpfulItems.has(item.id)}
                    isNotHelpful={notHelpfulItems.has(item.id)}
                    onToggle={() => handleQuestionClick(item)}
                    onHelpful={(helpful) => handleHelpful(item.id, helpful)}
                  />
                ))}
              </div>
            )
          })
        )}
      </div>

      {/* Contact Support */}
      {!embedded && (
        <Card className="mt-8 p-6 bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Lightbulb className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold mb-1">Can't find what you're looking for?</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                Our support team is here to help you with any questions
              </p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  <MessageSquare className="h-4 w-4 mr-1" />
                  Contact Support
                </Button>
                <Button variant="outline" size="sm">
                  <ExternalLink className="h-4 w-4 mr-1" />
                  View Documentation
                </Button>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}

function FAQItemCard({
  item,
  isExpanded,
  isHelpful,
  isNotHelpful,
  onToggle,
  onHelpful
}: {
  item: FAQItem
  isExpanded: boolean
  isHelpful: boolean
  isNotHelpful: boolean
  onToggle: () => void
  onHelpful: (helpful: boolean) => void
}) {
  return (
    <Card className="overflow-hidden">
      <Collapsible open={isExpanded} onOpenChange={onToggle}>
        <CollapsibleTrigger className="w-full">
          <div className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
            <div className="flex items-start justify-between text-left">
              <div className="flex-1">
                <h3 className="font-medium pr-2">{item.question}</h3>
                <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                  <span>{item.views} views</span>
                  {item.helpful !== undefined && (
                    <>
                      <span>•</span>
                      <span>{item.helpful} found helpful</span>
                    </>
                  )}
                  {item.tags.length > 0 && (
                    <>
                      <span>•</span>
                      <div className="flex gap-1">
                        {item.tags.slice(0, 2).map((tag) => (
                          <Badge key={tag} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                        {item.tags.length > 2 && (
                          <Badge variant="outline" className="text-xs">
                            +{item.tags.length - 2}
                          </Badge>
                        )}
                      </div>
                    </>
                  )}
                </div>
              </div>
              {isExpanded ? (
                <ChevronUp className="h-5 w-5 text-gray-400 flex-shrink-0" />
              ) : (
                <ChevronDown className="h-5 w-5 text-gray-400 flex-shrink-0" />
              )}
            </div>
          </div>
        </CollapsibleTrigger>
        
        <CollapsibleContent>
          <div className="px-4 pb-4 border-t">
            <div className="prose prose-sm dark:prose-invert max-w-none mt-4">
              <p>{item.answer}</p>
            </div>

            {item.relatedQuestions && item.relatedQuestions.length > 0 && (
              <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                <p className="text-sm font-medium mb-2">Related Questions</p>
                <div className="space-y-1">
                  {item.relatedQuestions.map((relatedId) => {
                    const relatedItem = FAQ_ITEMS.find(q => q.id === relatedId)
                    if (!relatedItem) return null
                    return (
                      <button
                        key={relatedId}
                        className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 text-left"
                        onClick={() => onToggle()}
                      >
                        → {relatedItem.question}
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <div className="text-sm text-gray-500">
                Was this helpful?
              </div>
              <div className="flex gap-2">
                <Button
                  variant={isHelpful ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => onHelpful(true)}
                >
                  <ThumbsUp className="h-4 w-4 mr-1" />
                  Yes
                  {item.helpful && (
                    <span className="ml-1">({item.helpful + (isHelpful ? 1 : 0)})</span>
                  )}
                </Button>
                <Button
                  variant={isNotHelpful ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => onHelpful(false)}
                >
                  <ThumbsDown className="h-4 w-4 mr-1" />
                  No
                  {item.notHelpful && (
                    <span className="ml-1">({item.notHelpful + (isNotHelpful ? 1 : 0)})</span>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  )
}