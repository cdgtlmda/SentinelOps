'use client';

import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MessageSquare, 
  Clock, 
  AlertCircle, 
  CheckCircle, 
  Filter, 
  Search,
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  FileText,
  Zap
} from 'lucide-react';
import { Message, Agent, MessageType, MessageStatus } from '@/types/collaboration';
import { cn } from '@/lib/utils';
import { format, formatDistanceToNow } from 'date-fns';

interface MessagePassingVisualizationProps {
  messages: Message[];
  agents: Agent[];
}

export function MessagePassingVisualization({
  messages,
  agents
}: MessagePassingVisualizationProps) {
  const [selectedAgent, setSelectedAgent] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<MessageType | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [timeRange, setTimeRange] = useState<'all' | '1h' | '15m' | '5m'>('all');
  const [view, setView] = useState<'timeline' | 'stats'>('timeline');

  // Filter messages
  const filteredMessages = useMemo(() => {
    let filtered = [...messages].reverse(); // Most recent first

    // Agent filter
    if (selectedAgent !== 'all') {
      filtered = filtered.filter(
        m => m.fromAgentId === selectedAgent || 
             m.toAgentId === selectedAgent ||
             (Array.isArray(m.toAgentId) && m.toAgentId.includes(selectedAgent))
      );
    }

    // Type filter
    if (selectedType !== 'all') {
      filtered = filtered.filter(m => m.type === selectedType);
    }

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(m => 
        JSON.stringify(m.content).toLowerCase().includes(searchQuery.toLowerCase()) ||
        m.id.includes(searchQuery)
      );
    }

    // Time range filter
    if (timeRange !== 'all') {
      const now = Date.now();
      const ranges = {
        '5m': 5 * 60 * 1000,
        '15m': 15 * 60 * 1000,
        '1h': 60 * 60 * 1000
      };
      filtered = filtered.filter(m => now - m.timestamp < ranges[timeRange]);
    }

    return filtered;
  }, [messages, selectedAgent, selectedType, searchQuery, timeRange]);

  // Calculate statistics
  const stats = useMemo(() => {
    const statusCounts = filteredMessages.reduce((acc, msg) => {
      acc[msg.status] = (acc[msg.status] || 0) + 1;
      return acc;
    }, {} as Record<MessageStatus, number>);

    const typeCounts = filteredMessages.reduce((acc, msg) => {
      acc[msg.type] = (acc[msg.type] || 0) + 1;
      return acc;
    }, {} as Record<MessageType, number>);

    const responseTimes = filteredMessages
      .filter(m => m.responseTime)
      .map(m => m.responseTime!);

    const avgResponseTime = responseTimes.length > 0
      ? responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length
      : 0;

    const successRate = filteredMessages.length > 0
      ? (statusCounts.delivered || 0) / filteredMessages.length * 100
      : 0;

    return {
      total: filteredMessages.length,
      statusCounts,
      typeCounts,
      avgResponseTime,
      successRate,
      minResponseTime: Math.min(...responseTimes) || 0,
      maxResponseTime: Math.max(...responseTimes) || 0
    };
  }, [filteredMessages]);

  const getStatusIcon = (status: MessageStatus) => {
    switch (status) {
      case 'delivered':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'in-transit':
        return <Activity className="w-4 h-4 text-blue-500 animate-pulse" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      default:
        return <MessageSquare className="w-4 h-4 text-gray-500" />;
    }
  };

  const getTypeColor = (type: MessageType): string => {
    const colors: Record<MessageType, string> = {
      request: 'bg-blue-500',
      response: 'bg-green-500',
      broadcast: 'bg-purple-500',
      error: 'bg-red-500',
      sync: 'bg-yellow-500',
      ack: 'bg-gray-500'
    };
    return colors[type];
  };

  const getPriorityColor = (priority: string): string => {
    const colors: Record<string, string> = {
      critical: 'text-red-600 bg-red-100',
      high: 'text-orange-600 bg-orange-100',
      medium: 'text-yellow-600 bg-yellow-100',
      low: 'text-gray-600 bg-gray-100'
    };
    return colors[priority];
  };

  const formatBytes = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            <CardTitle>Message Passing Visualization</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Tabs value={view} onValueChange={(v) => setView(v as 'timeline' | 'stats')}>
              <TabsList>
                <TabsTrigger value="timeline">Timeline</TabsTrigger>
                <TabsTrigger value="stats">Statistics</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="flex flex-wrap gap-2 mb-4">
          <Select value={selectedAgent} onValueChange={setSelectedAgent}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="All agents" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All agents</SelectItem>
              {agents.map(agent => (
                <SelectItem key={agent.id} value={agent.id}>
                  {agent.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={selectedType} onValueChange={(v) => setSelectedType(v as MessageType | 'all')}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="All types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              {(['request', 'response', 'broadcast', 'error', 'sync', 'ack'] as MessageType[]).map(type => (
                <SelectItem key={type} value={type}>
                  {type}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={timeRange} onValueChange={(v) => setTimeRange(v as any)}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Time range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All time</SelectItem>
              <SelectItem value="5m">Last 5 min</SelectItem>
              <SelectItem value="15m">Last 15 min</SelectItem>
              <SelectItem value="1h">Last hour</SelectItem>
            </SelectContent>
          </Select>

          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search messages..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8"
            />
          </div>
        </div>

        {view === 'timeline' ? (
          <ScrollArea className="h-[500px] pr-4">
            <div className="space-y-2">
              <AnimatePresence mode="popLayout">
                {filteredMessages.map((message, index) => {
                  const fromAgent = agents.find(a => a.id === message.fromAgentId);
                  const toAgents = Array.isArray(message.toAgentId)
                    ? agents.filter(a => message.toAgentId.includes(a.id))
                    : agents.filter(a => a.id === message.toAgentId);

                  return (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ delay: Math.min(index * 0.02, 0.2) }}
                      className="relative"
                    >
                      <div className="flex items-start gap-3">
                        {/* Timeline indicator */}
                        <div className="flex flex-col items-center">
                          <div className={cn(
                            "w-3 h-3 rounded-full",
                            getTypeColor(message.type)
                          )} />
                          {index < filteredMessages.length - 1 && (
                            <div className="w-0.5 h-20 bg-border" />
                          )}
                        </div>

                        {/* Message content */}
                        <div className="flex-1 bg-card border rounded-lg p-4 space-y-2">
                          <div className="flex items-start justify-between">
                            <div className="flex items-center gap-2">
                              {getStatusIcon(message.status)}
                              <span className="font-medium">
                                {fromAgent?.name || 'Unknown'}
                              </span>
                              <span className="text-muted-foreground">→</span>
                              <span className="font-medium">
                                {toAgents.map(a => a.name).join(', ') || 'Unknown'}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge className={getPriorityColor(message.priority)}>
                                {message.priority}
                              </Badge>
                              <Badge variant="outline">{message.type}</Badge>
                              <span className="text-xs text-muted-foreground">
                                {formatDistanceToNow(message.timestamp, { addSuffix: true })}
                              </span>
                            </div>
                          </div>

                          {/* Message details */}
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <span className="text-muted-foreground">Response Time</span>
                              <div className="font-medium flex items-center gap-1">
                                {message.responseTime ? (
                                  <>
                                    {message.responseTime}ms
                                    {message.responseTime > stats.avgResponseTime && (
                                      <TrendingUp className="w-3 h-3 text-red-500" />
                                    )}
                                    {message.responseTime < stats.avgResponseTime && (
                                      <TrendingDown className="w-3 h-3 text-green-500" />
                                    )}
                                  </>
                                ) : (
                                  '-'
                                )}
                              </div>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Size</span>
                              <div className="font-medium">{formatBytes(message.size)}</div>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Action</span>
                              <div className="font-medium">{message.content.action || '-'}</div>
                            </div>
                            <div>
                              <span className="text-muted-foreground">ID</span>
                              <div className="font-mono text-xs truncate">{message.id}</div>
                            </div>
                          </div>

                          {/* Content preview */}
                          {message.content.payload && (
                            <div className="mt-2 p-2 bg-muted/50 rounded text-xs font-mono overflow-hidden">
                              <pre className="truncate">
                                {JSON.stringify(message.content.payload, null, 2).substring(0, 100)}...
                              </pre>
                            </div>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          </ScrollArea>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {/* Summary stats */}
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Total Messages</span>
                  <BarChart3 className="w-4 h-4 text-muted-foreground" />
                </div>
                <div className="text-2xl font-bold">{stats.total}</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Success Rate</span>
                  <CheckCircle className="w-4 h-4 text-green-500" />
                </div>
                <div className="text-2xl font-bold">{stats.successRate.toFixed(1)}%</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Avg Response</span>
                  <Zap className="w-4 h-4 text-yellow-500" />
                </div>
                <div className="text-2xl font-bold">{stats.avgResponseTime.toFixed(0)}ms</div>
              </CardContent>
            </Card>

            {/* Status breakdown */}
            <Card className="md:col-span-3">
              <CardHeader>
                <CardTitle className="text-base">Message Status Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(stats.statusCounts).map(([status, count]) => (
                    <div key={status} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(status as MessageStatus)}
                        <span className="capitalize">{status}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{count}</span>
                        <div className="w-32 bg-muted rounded-full h-2">
                          <div
                            className={cn(
                              "h-full rounded-full",
                              status === 'delivered' && "bg-green-500",
                              status === 'failed' && "bg-red-500",
                              status === 'in-transit' && "bg-blue-500",
                              status === 'pending' && "bg-yellow-500"
                            )}
                            style={{ width: `${(count / stats.total) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Type breakdown */}
            <Card className="md:col-span-3">
              <CardHeader>
                <CardTitle className="text-base">Message Type Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {Object.entries(stats.typeCounts).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between p-2 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-2">
                        <div className={cn("w-3 h-3 rounded-full", getTypeColor(type as MessageType))} />
                        <span className="capitalize">{type}</span>
                      </div>
                      <Badge variant="secondary">{count}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </CardContent>
    </Card>
  );
}