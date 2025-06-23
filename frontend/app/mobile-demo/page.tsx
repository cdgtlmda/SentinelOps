'use client'

import React, { useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { 
  MobileLayout, 
  MobileNavigation, 
  MobileIncidentCard, 
  MobileChat, 
  PullToRefresh 
} from '@/components/mobile'
import { MobileIncidentsView } from '@/components/tables/mobile-incidents-view'
import { useTouchGestures } from '@/hooks/use-touch-gestures'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { 
  Smartphone, 
  Tablet, 
  Monitor, 
  CheckCircle,
  SwipeHorizontal,
  RefreshCw,
  MessageSquare,
  Navigation
} from 'lucide-react'
import { demoIncidents } from '@/lib/demo-incidents'
import type { ChatMessage } from '@/types/chat'

export default function MobileDemoPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState('overview')
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Welcome to the mobile chat demo! I can help you with incident management, security analysis, and more.',
      timestamp: new Date()
    }
  ])
  const [notifications, setNotifications] = useState(3)
  const [showChat, setShowChat] = useState(false)
  const gestureAreaRef = useRef<HTMLDivElement>(null)

  // Use touch gestures hook for demo
  const { isPinching } = useTouchGestures(gestureAreaRef, {
    onSwipe: (direction, velocity) => {
      console.log(`Swiped ${direction} with velocity ${velocity}`)
    },
    onPinch: (scale, center) => {
      console.log(`Pinch scale: ${scale}`, center)
    },
    onLongPress: (position) => {
      console.log('Long press at:', position)
    },
    onDoubleTap: (position) => {
      console.log('Double tap at:', position)
    }
  })

  const handleSendMessage = (message: string) => {
    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date()
    }
    setMessages([...messages, newMessage])

    // Simulate AI response
    setTimeout(() => {
      const response: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I understand you said: "${message}". How can I help you with that?`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, response])
    }, 1000)
  }

  const handleRefresh = async () => {
    console.log('Refreshing data...')
    await new Promise(resolve => setTimeout(resolve, 1500))
    setNotifications(prev => prev + 1)
  }

  const features = [
    {
      icon: SwipeHorizontal,
      title: 'Swipe Gestures',
      description: 'Swipe left to escalate, right to acknowledge incidents'
    },
    {
      icon: RefreshCw,
      title: 'Pull to Refresh',
      description: 'Natural pull-down gesture to refresh data'
    },
    {
      icon: Navigation,
      title: 'Bottom Navigation',
      description: 'Easy thumb-reach navigation with badge indicators'
    },
    {
      icon: MessageSquare,
      title: 'Touch-Optimized Chat',
      description: 'Full-screen chat with voice input and quick replies'
    }
  ]

  if (showChat) {
    return (
      <MobileChat
        messages={messages}
        onSendMessage={handleSendMessage}
        onBack={() => setShowChat(false)}
        onVoiceInput={(isRecording) => console.log('Voice recording:', isRecording)}
        quickReplies={[
          { id: '1', text: 'Show critical incidents' },
          { id: '2', text: 'Check system status' },
          { id: '3', text: 'View recent alerts' }
        ]}
        chatTitle="Security Assistant"
        chatContext="Incident Management"
      />
    )
  }

  return (
    <MobileLayout 
      showNavigation={true} 
      notifications={notifications}
      onRefresh={handleRefresh}
    >
      <div className="p-4">
        <h1 className="text-2xl font-bold mb-6">Mobile Optimization Demo</h1>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="incidents">Incidents</TabsTrigger>
            <TabsTrigger value="gestures">Gestures</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            {/* Device Preview */}
            <Card className="p-4">
              <h2 className="font-semibold mb-3">Responsive Design</h2>
              <div className="flex justify-around">
                <div className="text-center">
                  <Smartphone className="h-8 w-8 mx-auto mb-2 text-primary" />
                  <p className="text-sm">Mobile</p>
                  <CheckCircle className="h-4 w-4 mx-auto mt-1 text-green-600" />
                </div>
                <div className="text-center">
                  <Tablet className="h-8 w-8 mx-auto mb-2 text-primary" />
                  <p className="text-sm">Tablet</p>
                  <CheckCircle className="h-4 w-4 mx-auto mt-1 text-green-600" />
                </div>
                <div className="text-center">
                  <Monitor className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                  <p className="text-sm">Desktop</p>
                  <CheckCircle className="h-4 w-4 mx-auto mt-1 text-green-600" />
                </div>
              </div>
            </Card>

            {/* Features */}
            <div className="space-y-3">
              {features.map((feature) => {
                const Icon = feature.icon
                return (
                  <Card key={feature.title} className="p-4">
                    <div className="flex gap-3">
                      <div className="flex-shrink-0">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                          <Icon className="h-5 w-5 text-primary" />
                        </div>
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium mb-1">{feature.title}</h3>
                        <p className="text-sm text-muted-foreground">
                          {feature.description}
                        </p>
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>

            {/* Try Chat */}
            <Button 
              onClick={() => setShowChat(true)}
              className="w-full"
              size="lg"
            >
              <MessageSquare className="h-4 w-4 mr-2" />
              Try Mobile Chat
            </Button>
          </TabsContent>

          <TabsContent value="incidents">
            <MobileIncidentsView
              incidents={demoIncidents}
              onAcknowledge={(id) => console.log('Acknowledge:', id)}
              onEscalate={(id) => console.log('Escalate:', id)}
              onResolve={(id) => console.log('Resolve:', id)}
              onChat={(id) => {
                console.log('Chat about incident:', id)
                setShowChat(true)
              }}
              onRefresh={handleRefresh}
            />
          </TabsContent>

          <TabsContent value="gestures" className="space-y-4">
            <Card className="p-4">
              <h2 className="font-semibold mb-3">Touch Gestures Demo</h2>
              <p className="text-sm text-muted-foreground mb-4">
                Try different gestures in the area below
              </p>
              
              <div 
                ref={gestureAreaRef}
                className="h-48 bg-muted rounded-lg flex items-center justify-center relative overflow-hidden"
              >
                <p className="text-muted-foreground text-center px-4">
                  {isPinching ? (
                    'Pinching detected!'
                  ) : (
                    'Try: Swipe, Pinch, Long Press, Double Tap'
                  )}
                </p>
              </div>

              <div className="mt-4 space-y-2">
                <Badge variant="outline">Swipe left/right on incident cards</Badge>
                <Badge variant="outline">Pull down to refresh</Badge>
                <Badge variant="outline">Pinch to zoom (where applicable)</Badge>
                <Badge variant="outline">Long press for context menus</Badge>
              </div>
            </Card>

            {/* PWA Info */}
            <Card className="p-4">
              <h3 className="font-semibold mb-2">Progressive Web App</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Installable on home screen</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Works offline with service worker</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Push notifications support</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Native app-like experience</span>
                </li>
              </ul>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </MobileLayout>
  )
}