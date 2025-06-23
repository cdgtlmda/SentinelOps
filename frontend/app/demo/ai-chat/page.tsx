'use client'

import { ChatInterface } from '@/components/chat/chat-interface'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Sparkles, Brain, MessageSquare, Command, Zap, Globe } from 'lucide-react'

export default function AIChatDemo() {
  return (
    <div className="container mx-auto py-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-4 flex items-center gap-3">
          <Sparkles className="h-8 w-8 text-primary" />
          AI-Powered Conversational Chat Demo
        </h1>
        <p className="text-lg text-muted-foreground">
          Experience natural language understanding, intelligent suggestions, and context-aware conversations
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Feature Cards */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Brain className="h-5 w-5 text-primary" />
              Natural Language Understanding
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-3">
              AI understands your intent and extracts key information from natural conversations.
            </p>
            <div className="space-y-2">
              <Badge variant="secondary" className="text-xs">Intent Recognition</Badge>
              <Badge variant="secondary" className="text-xs">Entity Extraction</Badge>
              <Badge variant="secondary" className="text-xs">Confidence Scoring</Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <MessageSquare className="h-5 w-5 text-primary" />
              Context-Aware Conversations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-3">
              Maintains conversation context and links related incidents and agents automatically.
            </p>
            <div className="space-y-2">
              <Badge variant="secondary" className="text-xs">Context Tracking</Badge>
              <Badge variant="secondary" className="text-xs">Related Linking</Badge>
              <Badge variant="secondary" className="text-xs">Smart Summaries</Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Zap className="h-5 w-5 text-primary" />
              Intelligent Assistance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-3">
              Get AI-powered suggestions, auto-complete, and command recommendations.
            </p>
            <div className="space-y-2">
              <Badge variant="secondary" className="text-xs">Action Suggestions</Badge>
              <Badge variant="secondary" className="text-xs">Auto-Complete</Badge>
              <Badge variant="secondary" className="text-xs">Command Palette</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Try It Out Section */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Try These Examples</CardTitle>
          <CardDescription>Click any example to see the AI features in action</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h4 className="text-sm font-medium mb-2">Natural Language Commands</h4>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground italic">"Create a high priority incident for API authentication failures"</p>
                <p className="text-sm text-muted-foreground italic">"Check the status of incident INC-12345"</p>
                <p className="text-sm text-muted-foreground italic">"Who's available to help with database issues?"</p>
              </div>
            </div>
            <div className="space-y-2">
              <h4 className="text-sm font-medium mb-2">Structured Commands</h4>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground font-mono">/incident new priority=high</p>
                <p className="text-sm text-muted-foreground font-mono">/agent assign @alice</p>
                <p className="text-sm text-muted-foreground font-mono">/help</p>
              </div>
            </div>
          </div>
          
          <div className="mt-4 pt-4 border-t">
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Command className="h-3 w-3" />
                Press ⌘K for command palette
              </span>
              <span className="flex items-center gap-1">
                <Globe className="h-3 w-3" />
                Supports multiple languages
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Chat Interface */}
      <Card className="h-[600px]">
        <CardHeader>
          <CardTitle>AI-Powered Chat Interface</CardTitle>
          <CardDescription>
            Start typing to experience natural language understanding and intelligent suggestions
          </CardDescription>
        </CardHeader>
        <CardContent className="h-[calc(100%-5rem)] p-0">
          <ChatInterface className="h-full" />
        </CardContent>
      </Card>

      {/* Feature Details */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">How It Works</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <h4 className="font-medium text-sm mb-1">1. Type Naturally</h4>
              <p className="text-sm text-muted-foreground">
                Just describe what you want in plain English. The AI understands context and intent.
              </p>
            </div>
            <div>
              <h4 className="font-medium text-sm mb-1">2. Get Smart Suggestions</h4>
              <p className="text-sm text-muted-foreground">
                As you type, see intelligent auto-complete and action suggestions based on context.
              </p>
            </div>
            <div>
              <h4 className="font-medium text-sm mb-1">3. Track Context</h4>
              <p className="text-sm text-muted-foreground">
                The AI maintains conversation context and links related incidents and agents.
              </p>
            </div>
            <div>
              <h4 className="font-medium text-sm mb-1">4. Learn & Improve</h4>
              <p className="text-sm text-muted-foreground">
                The system learns from your interactions to provide better suggestions over time.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Key Features</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-start gap-2">
              <span className="text-primary mt-0.5">✓</span>
              <div>
                <p className="text-sm font-medium">Intent Recognition</p>
                <p className="text-xs text-muted-foreground">Understands what you're trying to do</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-primary mt-0.5">✓</span>
              <div>
                <p className="text-sm font-medium">Entity Extraction</p>
                <p className="text-xs text-muted-foreground">Identifies incident IDs, agent names, priorities</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-primary mt-0.5">✓</span>
              <div>
                <p className="text-sm font-medium">Fuzzy Matching</p>
                <p className="text-xs text-muted-foreground">Finds what you mean even with typos</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-primary mt-0.5">✓</span>
              <div>
                <p className="text-sm font-medium">Multi-Language Ready</p>
                <p className="text-xs text-muted-foreground">Structured for internationalization</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-primary mt-0.5">✓</span>
              <div>
                <p className="text-sm font-medium">Learning System</p>
                <p className="text-xs text-muted-foreground">Improves suggestions based on usage</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}