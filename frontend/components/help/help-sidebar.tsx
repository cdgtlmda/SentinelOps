'use client'

import { useState, useEffect } from 'react'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import {
  Search,
  BookOpen,
  Video,
  MessageCircle,
  ExternalLink,
  ChevronRight,
  Home,
  Settings,
  Shield,
  Zap,
  Users,
  BarChart3,
  HelpCircle,
  Lightbulb,
  FileText,
  Youtube,
  Book,
  GraduationCap
} from 'lucide-react'

interface HelpArticle {
  id: string
  title: string
  description: string
  category: string
  tags: string[]
  content?: string
  videoUrl?: string
  readTime?: number
  helpful?: number
  notHelpful?: number
}

interface HelpCategory {
  id: string
  name: string
  icon: React.ElementType
  description: string
  articles: HelpArticle[]
}

const HELP_CATEGORIES: HelpCategory[] = [
  {
    id: 'getting-started',
    name: 'Getting Started',
    icon: Home,
    description: 'Learn the basics of SentinelOps',
    articles: [
      {
        id: 'intro-to-sentinelops',
        title: 'Introduction to SentinelOps',
        description: 'Overview of the AI-powered security operations platform',
        category: 'getting-started',
        tags: ['basics', 'overview'],
        readTime: 5
      },
      {
        id: 'first-incident',
        title: 'Handling Your First Incident',
        description: 'Step-by-step guide to incident response',
        category: 'getting-started',
        tags: ['tutorial', 'incidents'],
        readTime: 10
      },
      {
        id: 'dashboard-overview',
        title: 'Dashboard Overview',
        description: 'Understanding the main dashboard and its components',
        category: 'getting-started',
        tags: ['dashboard', 'navigation'],
        readTime: 7
      }
    ]
  },
  {
    id: 'incidents',
    name: 'Incident Management',
    icon: Shield,
    description: 'Manage and respond to security incidents',
    articles: [
      {
        id: 'incident-lifecycle',
        title: 'Incident Lifecycle',
        description: 'Understanding incident states and transitions',
        category: 'incidents',
        tags: ['incidents', 'workflow'],
        readTime: 8
      },
      {
        id: 'severity-levels',
        title: 'Severity Levels Explained',
        description: 'How SentinelOps categorizes incident severity',
        category: 'incidents',
        tags: ['incidents', 'severity'],
        readTime: 5
      },
      {
        id: 'remediation-actions',
        title: 'Remediation Actions',
        description: 'Available automated and manual remediation options',
        category: 'incidents',
        tags: ['remediation', 'automation'],
        readTime: 12
      }
    ]
  },
  {
    id: 'agents',
    name: 'AI Agents',
    icon: Users,
    description: 'Working with AI agents',
    articles: [
      {
        id: 'agent-types',
        title: 'Understanding Agent Types',
        description: 'Detection, Analysis, Remediation, and Communication agents',
        category: 'agents',
        tags: ['agents', 'ai'],
        readTime: 10
      },
      {
        id: 'agent-collaboration',
        title: 'Agent Collaboration',
        description: 'How agents work together to resolve incidents',
        category: 'agents',
        tags: ['agents', 'workflow'],
        readTime: 8
      }
    ]
  },
  {
    id: 'analytics',
    name: 'Analytics & Reports',
    icon: BarChart3,
    description: 'Analyze trends and generate reports',
    articles: [
      {
        id: 'custom-reports',
        title: 'Creating Custom Reports',
        description: 'Build reports tailored to your needs',
        category: 'analytics',
        tags: ['reports', 'analytics'],
        readTime: 15
      },
      {
        id: 'metrics-guide',
        title: 'Key Metrics Guide',
        description: 'Understanding important security metrics',
        category: 'analytics',
        tags: ['metrics', 'kpi'],
        readTime: 10
      }
    ]
  }
]

interface HelpSidebarProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  currentPage?: string
}

export function HelpSidebar({ open, onOpenChange, currentPage }: HelpSidebarProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [selectedArticle, setSelectedArticle] = useState<HelpArticle | null>(null)
  const [helpfulArticles, setHelpfulArticles] = useState<Set<string>>(new Set())

  // Get contextual help based on current page
  const getContextualHelp = () => {
    if (!currentPage) return []
    
    const contextMap: Record<string, string[]> = {
      '/dashboard': ['intro-to-sentinelops', 'dashboard-overview'],
      '/incidents': ['incident-lifecycle', 'severity-levels', 'first-incident'],
      '/agents': ['agent-types', 'agent-collaboration'],
      '/analytics': ['custom-reports', 'metrics-guide']
    }

    const relevantArticleIds = contextMap[currentPage] || []
    return HELP_CATEGORIES.flatMap(cat => cat.articles)
      .filter(article => relevantArticleIds.includes(article.id))
  }

  const contextualHelp = getContextualHelp()

  // Search functionality
  const searchResults = searchQuery
    ? HELP_CATEGORIES.flatMap(cat => cat.articles)
        .filter(article => 
          article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          article.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
          article.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
        )
    : []

  const handleArticleClick = (article: HelpArticle) => {
    setSelectedArticle(article)
    // Track article view
    console.log('Viewing article:', article.id)
  }

  const handleHelpfulClick = (articleId: string, helpful: boolean) => {
    if (helpful) {
      setHelpfulArticles(new Set([...helpfulArticles, articleId]))
    } else {
      const newSet = new Set(helpfulArticles)
      newSet.delete(articleId)
      setHelpfulArticles(newSet)
    }
    // Track feedback
    console.log('Article feedback:', articleId, helpful)
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[400px] sm:w-[540px]">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <HelpCircle className="h-5 w-5" />
            Help & Documentation
          </SheetTitle>
          <SheetDescription>
            Find answers, learn features, and get support
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search help articles..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>

          {/* Content */}
          <div className="mt-6">
            {selectedArticle ? (
              // Article View
              <div className="space-y-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedArticle(null)}
                  className="mb-2"
                >
                  ← Back to articles
                </Button>
                
                <div>
                  <h3 className="text-lg font-semibold">{selectedArticle.title}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="outline">{selectedArticle.category}</Badge>
                    {selectedArticle.readTime && (
                      <span className="text-sm text-gray-500">
                        {selectedArticle.readTime} min read
                      </span>
                    )}
                  </div>
                </div>

                <Separator />

                <div className="prose prose-sm dark:prose-invert">
                  <p>{selectedArticle.description}</p>
                  {selectedArticle.content ? (
                    <div dangerouslySetInnerHTML={{ __html: selectedArticle.content }} />
                  ) : (
                    <div className="space-y-4">
                      <p>
                        This is where the full article content would be displayed. 
                        In a real implementation, this would be fetched from a 
                        content management system or API.
                      </p>
                      
                      {selectedArticle.videoUrl && (
                        <Card className="p-4">
                          <div className="flex items-center gap-3">
                            <Youtube className="h-8 w-8 text-red-500" />
                            <div className="flex-1">
                              <p className="font-medium">Video Tutorial</p>
                              <p className="text-sm text-gray-500">
                                Watch a video walkthrough of this topic
                              </p>
                            </div>
                            <Button variant="outline" size="sm">
                              <ExternalLink className="h-4 w-4 mr-1" />
                              Watch
                            </Button>
                          </div>
                        </Card>
                      )}
                    </div>
                  )}
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-500">
                    Was this article helpful?
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant={helpfulArticles.has(selectedArticle.id) ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => handleHelpfulClick(selectedArticle.id, true)}
                    >
                      Yes
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleHelpfulClick(selectedArticle.id, false)}
                    >
                      No
                    </Button>
                  </div>
                </div>
              </div>
            ) : searchQuery ? (
              // Search Results
              <div className="space-y-4">
                <h3 className="font-semibold">
                  Search results for "{searchQuery}"
                </h3>
                {searchResults.length > 0 ? (
                  <div className="space-y-2">
                    {searchResults.map((article) => (
                      <ArticleCard
                        key={article.id}
                        article={article}
                        onClick={() => handleArticleClick(article)}
                      />
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">
                    No articles found. Try different keywords.
                  </p>
                )}
              </div>
            ) : (
              // Default View with Tabs
              <Tabs defaultValue="contextual" className="space-y-4">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="contextual">For You</TabsTrigger>
                  <TabsTrigger value="categories">Browse</TabsTrigger>
                  <TabsTrigger value="resources">Resources</TabsTrigger>
                </TabsList>

                <TabsContent value="contextual" className="space-y-4">
                  {contextualHelp.length > 0 ? (
                    <>
                      <div>
                        <h3 className="font-semibold mb-2">
                          Recommended for this page
                        </h3>
                        <div className="space-y-2">
                          {contextualHelp.map((article) => (
                            <ArticleCard
                              key={article.id}
                              article={article}
                              onClick={() => handleArticleClick(article)}
                            />
                          ))}
                        </div>
                      </div>
                      <Separator />
                    </>
                  ) : null}

                  <div>
                    <h3 className="font-semibold mb-2">Popular Articles</h3>
                    <div className="space-y-2">
                      {HELP_CATEGORIES[0].articles.slice(0, 3).map((article) => (
                        <ArticleCard
                          key={article.id}
                          article={article}
                          onClick={() => handleArticleClick(article)}
                        />
                      ))}
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="categories" className="space-y-4">
                  <ScrollArea className="h-[400px]">
                    {HELP_CATEGORIES.map((category) => (
                      <div key={category.id} className="mb-6">
                        <button
                          className="w-full text-left"
                          onClick={() => setSelectedCategory(
                            selectedCategory === category.id ? null : category.id
                          )}
                        >
                          <Card className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                            <div className="flex items-center gap-3">
                              <category.icon className="h-5 w-5 text-gray-500" />
                              <div className="flex-1">
                                <h3 className="font-semibold">{category.name}</h3>
                                <p className="text-sm text-gray-500">
                                  {category.description}
                                </p>
                              </div>
                              <ChevronRight 
                                className={`h-4 w-4 transition-transform ${
                                  selectedCategory === category.id ? 'rotate-90' : ''
                                }`} 
                              />
                            </div>
                          </Card>
                        </button>

                        {selectedCategory === category.id && (
                          <div className="mt-2 ml-4 space-y-2">
                            {category.articles.map((article) => (
                              <ArticleCard
                                key={article.id}
                                article={article}
                                onClick={() => handleArticleClick(article)}
                                compact
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </ScrollArea>
                </TabsContent>

                <TabsContent value="resources" className="space-y-4">
                  <div className="grid gap-4">
                    <ResourceCard
                      icon={Book}
                      title="Documentation"
                      description="Comprehensive guides and API references"
                      action="View Docs"
                      onClick={() => window.open('/docs', '_blank')}
                    />
                    <ResourceCard
                      icon={Youtube}
                      title="Video Tutorials"
                      description="Step-by-step video walkthroughs"
                      action="Watch Videos"
                      onClick={() => window.open('/tutorials', '_blank')}
                    />
                    <ResourceCard
                      icon={GraduationCap}
                      title="Training Center"
                      description="Interactive courses and certifications"
                      action="Start Learning"
                      onClick={() => window.open('/training', '_blank')}
                    />
                    <ResourceCard
                      icon={MessageCircle}
                      title="Community Forum"
                      description="Connect with other users and experts"
                      action="Join Community"
                      onClick={() => window.open('/community', '_blank')}
                    />
                  </div>
                </TabsContent>
              </Tabs>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="absolute bottom-6 left-6 right-6">
          <Card className="p-4 bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
            <div className="flex items-center gap-3">
              <Lightbulb className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              <div className="flex-1">
                <p className="font-medium text-sm">Need more help?</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Contact our support team
                </p>
              </div>
              <Button size="sm" variant="outline">
                Contact Support
              </Button>
            </div>
          </Card>
        </div>
      </SheetContent>
    </Sheet>
  )
}

function ArticleCard({ 
  article, 
  onClick, 
  compact = false 
}: { 
  article: HelpArticle
  onClick: () => void
  compact?: boolean 
}) {
  return (
    <Card 
      className="p-3 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className={`font-medium ${compact ? 'text-sm' : ''}`}>
            {article.title}
          </h4>
          {!compact && (
            <p className="text-sm text-gray-500 mt-1">
              {article.description}
            </p>
          )}
          <div className="flex items-center gap-2 mt-2">
            {article.tags.map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
            {article.readTime && (
              <span className="text-xs text-gray-400">
                {article.readTime} min
              </span>
            )}
          </div>
        </div>
        <ChevronRight className="h-4 w-4 text-gray-400 flex-shrink-0" />
      </div>
    </Card>
  )
}

function ResourceCard({
  icon: Icon,
  title,
  description,
  action,
  onClick
}: {
  icon: React.ElementType
  title: string
  description: string
  action: string
  onClick: () => void
}) {
  return (
    <Card className="p-4">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1">
          <h4 className="font-medium">{title}</h4>
          <p className="text-sm text-gray-500">{description}</p>
        </div>
        <Button variant="outline" size="sm" onClick={onClick}>
          {action}
          <ExternalLink className="h-3 w-3 ml-1" />
        </Button>
      </div>
    </Card>
  )
}