'use client';

import React, { useState } from 'react';
import { WebSocketProvider } from '@/context/websocket-context';
import { ToastProvider } from '@/hooks/use-toast';
import { ConnectionStatus } from '@/components/realtime/connection-status';
import { RealtimeIncidentList } from '@/components/incidents/realtime-incident-list';
import { RealtimeAgentStatus } from '@/components/agents/realtime-agent-status';
import { RealtimeChat } from '@/components/chat/realtime-chat';
import { RealtimeActivityFeed } from '@/components/activity/realtime-activity-feed';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Activity, Users, MessageSquare, AlertCircle, Wifi } from 'lucide-react';

// Mock data for demo
const mockIncidents = [
  {
    id: '1',
    title: 'Database Connection Timeout',
    description: 'Multiple failed connection attempts to primary database',
    severity: 'high' as const,
    status: 'investigating' as const,
    createdAt: new Date(Date.now() - 1000 * 60 * 30),
    updatedAt: new Date(Date.now() - 1000 * 60 * 5),
    assignedTo: 'agent-1',
    tags: ['database', 'critical-path'],
    affectedServices: ['API', 'Dashboard'],
    metrics: {
      responseTime: 2500,
      errorRate: 0.15,
      affectedUsers: 450
    }
  },
  {
    id: '2',
    title: 'Elevated API Response Times',
    description: 'API endpoints showing 3x normal response times',
    severity: 'medium' as const,
    status: 'acknowledged' as const,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2),
    updatedAt: new Date(Date.now() - 1000 * 60 * 15),
    assignedTo: 'agent-2',
    tags: ['performance', 'api'],
    affectedServices: ['API'],
    metrics: {
      responseTime: 800,
      errorRate: 0.02,
      affectedUsers: 150
    }
  }
];

const mockAgents = [
  {
    id: 'agent-1',
    name: 'Sarah Chen',
    status: 'online' as const,
    department: 'Infrastructure',
    role: 'Senior SRE',
    lastSeen: new Date()
  },
  {
    id: 'agent-2',
    name: 'Mike Rodriguez',
    status: 'busy' as const,
    department: 'Platform',
    role: 'DevOps Engineer',
    lastSeen: new Date()
  },
  {
    id: 'agent-3',
    name: 'Emily Thompson',
    status: 'away' as const,
    department: 'Security',
    role: 'Security Engineer',
    lastSeen: new Date(Date.now() - 1000 * 60 * 10)
  },
  {
    id: 'agent-4',
    name: 'James Wilson',
    status: 'offline' as const,
    department: 'Infrastructure',
    role: 'SRE',
    lastSeen: new Date(Date.now() - 1000 * 60 * 60 * 2)
  }
];

const mockMessages = [
  {
    id: '1',
    conversationId: 'conv-1',
    senderId: 'agent-2',
    content: 'Investigating the database timeout issue. Looks like connection pool exhaustion.',
    timestamp: Date.now() - 1000 * 60 * 10,
    sender: mockAgents[1],
    delivered: true,
    readBy: ['agent-1', 'agent-2']
  },
  {
    id: '2',
    conversationId: 'conv-1',
    senderId: 'agent-1',
    content: 'I see the same pattern. Let me check the connection pool metrics.',
    timestamp: Date.now() - 1000 * 60 * 8,
    sender: mockAgents[0],
    delivered: true,
    readBy: ['agent-1', 'agent-2']
  }
];

const mockActivities = [
  {
    id: '1',
    type: 'incident.created',
    actor: 'System',
    target: 'Database Connection Timeout',
    action: 'created',
    timestamp: Date.now() - 1000 * 60 * 30,
    metadata: { severity: 'high', service: 'database' }
  },
  {
    id: '2',
    type: 'agent.joined',
    actor: 'Sarah Chen',
    target: 'incident-1',
    action: 'joined investigation',
    timestamp: Date.now() - 1000 * 60 * 25
  },
  {
    id: '3',
    type: 'incident.resolved',
    actor: 'Mike Rodriguez',
    target: 'Cache Service Degradation',
    action: 'resolved',
    timestamp: Date.now() - 1000 * 60 * 15,
    metadata: { duration: '45m', rootCause: 'memory leak' }
  }
];

export default function RealtimeDemoPage() {
  const [selectedIncidents, setSelectedIncidents] = useState<Set<string>>(new Set());

  const handleToggleSelect = (id: string) => {
    setSelectedIncidents(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  return (
    <ToastProvider>
      <WebSocketProvider 
        url={process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:3001'}
        autoConnect={true}
        debug={true}
      >
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
          {/* Header */}
          <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
            <div className="container mx-auto px-4 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-bold">Real-time Features Demo</h1>
                  <p className="text-sm text-muted-foreground mt-1">
                    Experience live updates across all SentinelOps components
                  </p>
                </div>
                <ConnectionStatus showDetails={true} />
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="container mx-auto px-4 py-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column - Incidents */}
              <div className="lg:col-span-2">
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <AlertCircle className="h-5 w-5" />
                        <CardTitle>Live Incidents</CardTitle>
                      </div>
                      <Badge variant="outline">
                        {mockIncidents.length} active
                      </Badge>
                    </div>
                    <CardDescription>
                      Real-time incident updates with automatic refresh
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <RealtimeIncidentList
                      initialIncidents={mockIncidents}
                      selectedIds={selectedIncidents}
                      onToggleSelect={handleToggleSelect}
                      onViewDetails={(id) => console.log('View details:', id)}
                      onAcknowledge={(id) => console.log('Acknowledge:', id)}
                      onInvestigate={(id) => console.log('Investigate:', id)}
                      onRemediate={(id) => console.log('Remediate:', id)}
                    />
                  </CardContent>
                </Card>
              </div>

              {/* Right Column - Agent Status & Activity */}
              <div className="space-y-6">
                {/* Agent Status */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Users className="h-5 w-5" />
                      <CardTitle>Team Status</CardTitle>
                    </div>
                    <CardDescription>
                      Live agent availability updates
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <RealtimeAgentStatus
                      agents={mockAgents}
                      showOffline={true}
                    />
                  </CardContent>
                </Card>

                {/* Activity Feed */}
                <Card className="h-[400px] flex flex-col">
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Activity className="h-5 w-5" />
                      <CardTitle>Activity Feed</CardTitle>
                    </div>
                    <CardDescription>
                      Real-time system events and updates
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="flex-1 overflow-hidden">
                    <RealtimeActivityFeed
                      initialActivities={mockActivities}
                      maxItems={20}
                      autoScroll={true}
                      className="h-full"
                    />
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* Chat Section */}
            <div className="mt-6">
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5" />
                    <CardTitle>Team Chat</CardTitle>
                  </div>
                  <CardDescription>
                    Real-time messaging with delivery status and read receipts
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-[400px]">
                    <RealtimeChat
                      conversationId="conv-1"
                      currentUser={mockAgents[0]}
                      participants={mockAgents.slice(0, 3)}
                      initialMessages={mockMessages}
                      className="h-full"
                    />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Feature Highlights */}
            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                      <Wifi className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <p className="font-medium">Auto Reconnection</p>
                      <p className="text-sm text-muted-foreground">
                        Exponential backoff strategy
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                      <Activity className="h-5 w-5 text-green-600 dark:text-green-400" />
                    </div>
                    <div>
                      <p className="font-medium">Message Queuing</p>
                      <p className="text-sm text-muted-foreground">
                        Offline message persistence
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                      <AlertCircle className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div>
                      <p className="font-medium">Priority Messaging</p>
                      <p className="text-sm text-muted-foreground">
                        Critical alerts first
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
                      <Users className="h-5 w-5 text-orange-600 dark:text-orange-400" />
                    </div>
                    <div>
                      <p className="font-medium">Presence Detection</p>
                      <p className="text-sm text-muted-foreground">
                        Real-time agent status
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </main>
        </div>
      </WebSocketProvider>
    </ToastProvider>
  );
}