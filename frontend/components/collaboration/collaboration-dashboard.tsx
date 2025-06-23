'use client';

import React, { useState, useMemo, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  Play, 
  Pause, 
  RefreshCw, 
  Settings,
  Maximize2,
  Grid3X3,
  Activity
} from 'lucide-react';
import { NetworkTopology } from '@/types/collaboration';
import { useCollaboration } from '@/hooks/use-collaboration';
import { AgentCommunicationFlow } from './agent-communication-flow';
import { MessagePassingVisualization } from './message-passing-visualization';
import { CoordinationDisplay } from './coordination-display';
import { PerformanceMetrics } from './performance-metrics';
import { cn } from '@/lib/utils';

interface CollaborationDashboardProps {
  initialTopology?: NetworkTopology;
}

export function CollaborationDashboard({ 
  initialTopology = 'mesh' 
}: CollaborationDashboardProps) {
  const [topology, setTopology] = useState<NetworkTopology>(initialTopology);
  const [layout, setLayout] = useState<'grid' | 'tabs'>('tabs');
  const [fullscreenView, setFullscreenView] = useState<string | null>(null);

  const {
    state,
    startSimulation,
    stopSimulation,
    isSimulating,
    metrics,
    resetSimulation
  } = useCollaboration(topology);

  const handleTopologyChange = useCallback((newTopology: NetworkTopology) => {
    setTopology(newTopology);
    // Reset simulation without page reload
    if (resetSimulation) {
      resetSimulation(newTopology);
    }
  }, [resetSimulation]);

  const views = useMemo(() => [
    {
      id: 'flow',
      title: 'Communication Flow',
      icon: <Activity className="w-4 h-4" />,
      component: (
        <AgentCommunicationFlow
          agents={state.session.agents}
          messages={state.session.messages}
          topology={topology}
          onTopologyChange={handleTopologyChange}
        />
      )
    },
    {
      id: 'messages',
      title: 'Message Timeline',
      icon: <Activity className="w-4 h-4" />,
      component: (
        <MessagePassingVisualization
          messages={state.session.messages}
          agents={state.session.agents}
        />
      )
    },
    {
      id: 'coordination',
      title: 'Coordination',
      icon: <Activity className="w-4 h-4" />,
      component: (
        <CoordinationDisplay
          synchronizationPoints={state.synchronizationPoints}
          resourceLocks={state.resourceLocks}
          consensusDecisions={state.consensusDecisions}
          agents={state.session.agents}
        />
      )
    },
    {
      id: 'performance',
      title: 'Performance',
      icon: <Activity className="w-4 h-4" />,
      component: (
        <PerformanceMetrics
          metrics={metrics}
          agents={state.session.agents}
          messages={state.session.messages}
          communicationGraph={state.communicationGraph}
        />
      )
    }
  ], [
    state.session.agents,
    state.session.messages,
    state.synchronizationPoints,
    state.resourceLocks,
    state.consensusDecisions,
    state.communicationGraph,
    topology,
    metrics,
    handleTopologyChange
  ]);

  const renderView = (view: typeof views[0], isFullscreen = false) => {
    return (
      <motion.div
        key={view.id}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className={cn(
          "relative",
          isFullscreen && "fixed inset-0 z-50 bg-background p-4"
        )}
      >
        {isFullscreen && (
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-6 right-6 z-10"
            onClick={() => setFullscreenView(null)}
          >
            <Maximize2 className="w-4 h-4" />
          </Button>
        )}
        <div className={cn("h-full", isFullscreen && "max-w-7xl mx-auto")}>
          {view.component}
        </div>
      </motion.div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Header Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              <CardTitle>Multi-Agent Collaboration Dashboard</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant={isSimulating ? "destructive" : "default"}
                size="sm"
                onClick={isSimulating ? stopSimulation : startSimulation}
              >
                {isSimulating ? (
                  <>
                    <Pause className="w-4 h-4 mr-2" />
                    Stop
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Start
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.location.reload()}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Reset
              </Button>
              <div className="flex items-center border rounded-md">
                <Button
                  variant={layout === 'tabs' ? "secondary" : "ghost"}
                  size="sm"
                  className="rounded-r-none"
                  onClick={() => setLayout('tabs')}
                >
                  Tabs
                </Button>
                <Button
                  variant={layout === 'grid' ? "secondary" : "ghost"}
                  size="sm"
                  className="rounded-l-none"
                  onClick={() => setLayout('grid')}
                >
                  <Grid3X3 className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Active Agents</span>
              <div className="font-medium">{state.session.agents.length}</div>
            </div>
            <div>
              <span className="text-muted-foreground">Total Messages</span>
              <div className="font-medium">{state.session.messages.length}</div>
            </div>
            <div>
              <span className="text-muted-foreground">Efficiency</span>
              <div className="font-medium">{metrics.efficiency.toFixed(1)}%</div>
            </div>
            <div>
              <span className="text-muted-foreground">Avg Response</span>
              <div className="font-medium">{metrics.averageResponseTime.toFixed(0)}ms</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      {fullscreenView ? (
        renderView(views.find(v => v.id === fullscreenView)!, true)
      ) : layout === 'tabs' ? (
        <Tabs defaultValue="flow" className="space-y-4">
          <TabsList className="grid grid-cols-4 w-full">
            {views.map(view => (
              <TabsTrigger key={view.id} value={view.id} className="flex items-center gap-2">
                {view.icon}
                <span className="hidden sm:inline">{view.title}</span>
              </TabsTrigger>
            ))}
          </TabsList>
          {views.map(view => (
            <TabsContent key={view.id} value={view.id} className="mt-4 space-y-4">
              <div className="flex justify-end mb-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setFullscreenView(view.id)}
                >
                  <Maximize2 className="w-4 h-4 mr-2" />
                  Fullscreen
                </Button>
              </div>
              {view.component}
            </TabsContent>
          ))}
        </Tabs>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {views.map(view => (
            <motion.div
              key={view.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="relative group"
            >
              <Button
                variant="ghost"
                size="icon"
                className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => setFullscreenView(view.id)}
              >
                <Maximize2 className="w-4 h-4" />
              </Button>
              <div className="h-[500px]">
                {view.component}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}