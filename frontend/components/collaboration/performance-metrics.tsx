'use client';

import React, { useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Gauge, 
  BarChart3,
  AlertTriangle,
  Zap,
  Clock,
  ArrowUp,
  ArrowDown,
  Minus
} from 'lucide-react';
import { CollaborationMetrics, Agent, Message, Bottleneck, CommunicationEdge } from '@/types/collaboration';
import { cn } from '@/lib/utils';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';

interface PerformanceMetricsProps {
  metrics: CollaborationMetrics;
  agents: Agent[];
  messages: Message[];
  communicationGraph: CommunicationEdge[];
}

export function PerformanceMetrics({
  metrics,
  agents,
  messages,
  communicationGraph
}: PerformanceMetricsProps) {
  const [timeWindow, setTimeWindow] = useState<'1m' | '5m' | '15m'>('5m');

  // Calculate time-series data
  const timeSeriesData = useMemo(() => {
    const now = Date.now();
    const windowMs = {
      '1m': 60 * 1000,
      '5m': 5 * 60 * 1000,
      '15m': 15 * 60 * 1000
    }[timeWindow];
    
    const bucketSize = windowMs / 20; // 20 data points
    const buckets: Record<number, { time: number; messages: number; avgResponseTime: number; errors: number }> = {};

    messages
      .filter(m => now - m.timestamp <= windowMs)
      .forEach(message => {
        const bucketIndex = Math.floor((now - message.timestamp) / bucketSize);
        if (!buckets[bucketIndex]) {
          buckets[bucketIndex] = { 
            time: now - (bucketIndex * bucketSize), 
            messages: 0, 
            avgResponseTime: 0,
            errors: 0
          };
        }
        buckets[bucketIndex].messages++;
        if (message.responseTime) {
          buckets[bucketIndex].avgResponseTime = 
            (buckets[bucketIndex].avgResponseTime * (buckets[bucketIndex].messages - 1) + message.responseTime) / 
            buckets[bucketIndex].messages;
        }
        if (message.status === 'failed') {
          buckets[bucketIndex].errors++;
        }
      });

    return Object.values(buckets)
      .sort((a, b) => a.time - b.time)
      .map(bucket => ({
        time: new Date(bucket.time).toLocaleTimeString(),
        messages: bucket.messages,
        avgResponseTime: Math.round(bucket.avgResponseTime),
        errorRate: bucket.messages > 0 ? (bucket.errors / bucket.messages) * 100 : 0
      }));
  }, [messages, timeWindow]);

  // Calculate agent performance data
  const agentPerformance = useMemo(() => {
    return agents.map(agent => {
      const agentMessages = messages.filter(
        m => m.fromAgentId === agent.id || 
             m.toAgentId === agent.id ||
             (Array.isArray(m.toAgentId) && m.toAgentId.includes(agent.id))
      );

      const sentMessages = messages.filter(m => m.fromAgentId === agent.id);
      const receivedMessages = agentMessages.filter(m => m.fromAgentId !== agent.id);
      const responseTimes = sentMessages
        .filter(m => m.responseTime)
        .map(m => m.responseTime!);

      const avgResponseTime = responseTimes.length > 0
        ? responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length
        : 0;

      const errorRate = sentMessages.length > 0
        ? sentMessages.filter(m => m.status === 'failed').length / sentMessages.length * 100
        : 0;

      return {
        name: agent.name,
        sent: sentMessages.length,
        received: receivedMessages.length,
        avgResponseTime: Math.round(avgResponseTime),
        errorRate: Math.round(errorRate),
        efficiency: Math.round(100 - errorRate - (avgResponseTime / 100))
      };
    });
  }, [agents, messages]);

  // Calculate communication heat map data
  const heatMapData = useMemo(() => {
    const matrix: Record<string, Record<string, number>> = {};
    
    agents.forEach(agent => {
      matrix[agent.id] = {};
      agents.forEach(other => {
        if (agent.id !== other.id) {
          const edge = communicationGraph.find(
            e => (e.source === agent.id && e.target === other.id) ||
                 (e.source === other.id && e.target === agent.id)
          );
          matrix[agent.id][other.id] = edge ? edge.weight : 0;
        }
      });
    });

    return agents.map(fromAgent => ({
      from: fromAgent.name,
      ...agents.reduce((acc, toAgent) => ({
        ...acc,
        [toAgent.name]: matrix[fromAgent.id]?.[toAgent.id] || 0
      }), {})
    }));
  }, [agents, communicationGraph]);

  // Radar chart data for agent capabilities
  const radarData = useMemo(() => {
    const metrics = ['Throughput', 'Response Time', 'Reliability', 'Efficiency', 'Load Balance'];
    
    return metrics.map(metric => {
      const dataPoint: any = { metric };
      
      agents.forEach(agent => {
        const perf = agentPerformance.find(p => p.name === agent.name);
        if (perf) {
          switch (metric) {
            case 'Throughput':
              dataPoint[agent.name] = Math.min(100, (perf.sent + perf.received) / 2);
              break;
            case 'Response Time':
              dataPoint[agent.name] = Math.max(0, 100 - (perf.avgResponseTime / 10));
              break;
            case 'Reliability':
              dataPoint[agent.name] = 100 - perf.errorRate;
              break;
            case 'Efficiency':
              dataPoint[agent.name] = perf.efficiency;
              break;
            case 'Load Balance':
              const avgLoad = agentPerformance.reduce((sum, p) => sum + p.sent + p.received, 0) / agentPerformance.length;
              const agentLoad = perf.sent + perf.received;
              dataPoint[agent.name] = Math.max(0, 100 - Math.abs(agentLoad - avgLoad) * 10);
              break;
          }
        }
      });
      
      return dataPoint;
    });
  }, [agents, agentPerformance]);

  const getTrendIcon = (current: number, previous: number) => {
    const change = ((current - previous) / previous) * 100;
    if (Math.abs(change) < 5) return <Minus className="w-4 h-4 text-gray-500" />;
    if (change > 0) return <ArrowUp className="w-4 h-4 text-green-500" />;
    return <ArrowDown className="w-4 h-4 text-red-500" />;
  };

  const getBottleneckSeverityColor = (severity: Bottleneck['severity']) => {
    switch (severity) {
      case 'high': return 'text-red-500 bg-red-100 dark:bg-red-900/20';
      case 'medium': return 'text-yellow-500 bg-yellow-100 dark:bg-yellow-900/20';
      case 'low': return 'text-blue-500 bg-blue-100 dark:bg-blue-900/20';
    }
  };

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#14b8a6'];

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            <CardTitle>Performance Metrics</CardTitle>
          </div>
          <Tabs value={timeWindow} onValueChange={(v) => setTimeWindow(v as any)}>
            <TabsList>
              <TabsTrigger value="1m">1 min</TabsTrigger>
              <TabsTrigger value="5m">5 min</TabsTrigger>
              <TabsTrigger value="15m">15 min</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </CardHeader>
      <CardContent>
        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">Efficiency</span>
                <Gauge className="w-4 h-4 text-muted-foreground" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold">{metrics.efficiency.toFixed(1)}%</span>
                {getTrendIcon(metrics.efficiency, 85)}
              </div>
              <Progress value={metrics.efficiency} className="mt-2 h-1" />
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">Throughput</span>
                <Zap className="w-4 h-4 text-muted-foreground" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold">{metrics.throughput.toFixed(1)}</span>
                <span className="text-xs text-muted-foreground">msg/s</span>
              </div>
              <div className="mt-2 text-xs text-muted-foreground">
                {metrics.totalMessages} total messages
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">Avg Response</span>
                <Clock className="w-4 h-4 text-muted-foreground" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold">{metrics.averageResponseTime.toFixed(0)}</span>
                <span className="text-xs text-muted-foreground">ms</span>
              </div>
              <Progress 
                value={Math.min(100, (300 - metrics.averageResponseTime) / 3)} 
                className="mt-2 h-1"
              />
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">Error Rate</span>
                <AlertTriangle className="w-4 h-4 text-muted-foreground" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold">{metrics.errorRate.toFixed(1)}%</span>
                {getTrendIcon(5, metrics.errorRate)}
              </div>
              <Progress 
                value={metrics.errorRate} 
                className="mt-2 h-1"
                // @ts-ignore - custom color
                indicatorClassName="bg-red-500"
              />
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="timeline" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
            <TabsTrigger value="agents">Agent Performance</TabsTrigger>
            <TabsTrigger value="heatmap">Heat Map</TabsTrigger>
            <TabsTrigger value="bottlenecks">Bottlenecks</TabsTrigger>
          </TabsList>

          <TabsContent value="timeline" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Message Flow & Response Times</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={timeSeriesData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Legend />
                    <Line 
                      yAxisId="left"
                      type="monotone" 
                      dataKey="messages" 
                      stroke="#3b82f6" 
                      name="Messages"
                      strokeWidth={2}
                    />
                    <Line 
                      yAxisId="right"
                      type="monotone" 
                      dataKey="avgResponseTime" 
                      stroke="#10b981" 
                      name="Avg Response (ms)"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="agents" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Agent Performance Comparison</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={agentPerformance}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="sent" fill="#3b82f6" name="Sent" />
                    <Bar dataKey="received" fill="#10b981" name="Received" />
                    <Bar dataKey="efficiency" fill="#8b5cf6" name="Efficiency %" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Agent Capabilities Radar</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={radarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="metric" />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} />
                    {agents.map((agent, index) => (
                      <Radar
                        key={agent.id}
                        name={agent.name}
                        dataKey={agent.name}
                        stroke={COLORS[index % COLORS.length]}
                        fill={COLORS[index % COLORS.length]}
                        fillOpacity={0.3}
                      />
                    ))}
                    <Legend />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="heatmap" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Communication Heat Map</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr>
                        <th className="p-2 text-left">From \ To</th>
                        {agents.map(agent => (
                          <th key={agent.id} className="p-2 text-center text-sm">
                            {agent.name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {agents.map(fromAgent => (
                        <tr key={fromAgent.id}>
                          <td className="p-2 font-medium text-sm">{fromAgent.name}</td>
                          {agents.map(toAgent => {
                            const value = heatMapData.find(d => d.from === fromAgent.name)?.[toAgent.name] || 0;
                            const intensity = Math.min(value / 20, 1);
                            
                            return (
                              <td 
                                key={toAgent.id} 
                                className="p-2 text-center"
                                style={{
                                  backgroundColor: fromAgent.id === toAgent.id 
                                    ? 'transparent' 
                                    : `rgba(59, 130, 246, ${intensity * 0.5})`,
                                  color: intensity > 0.5 ? 'white' : 'inherit'
                                }}
                              >
                                {fromAgent.id === toAgent.id ? '-' : value}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="bottlenecks" className="space-y-4">
            {metrics.bottlenecks.length === 0 ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
                  <p className="text-lg font-medium">No bottlenecks detected</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    All agents are performing within acceptable parameters
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {metrics.bottlenecks.map((bottleneck, index) => {
                  const agent = agents.find(a => a.id === bottleneck.agentId);
                  
                  return (
                    <motion.div
                      key={`${bottleneck.agentId}-${index}`}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <Card>
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className={cn(
                                "p-2 rounded-lg",
                                getBottleneckSeverityColor(bottleneck.severity)
                              )}>
                                <AlertTriangle className="w-4 h-4" />
                              </div>
                              <div>
                                <div className="font-medium">{agent?.name || 'Unknown Agent'}</div>
                                <div className="text-sm text-muted-foreground">
                                  {bottleneck.description}
                                </div>
                              </div>
                            </div>
                            <Badge 
                              variant="outline"
                              className={cn(
                                bottleneck.severity === 'high' && "border-red-500 text-red-700",
                                bottleneck.severity === 'medium' && "border-yellow-500 text-yellow-700",
                                bottleneck.severity === 'low' && "border-blue-500 text-blue-700"
                              )}
                            >
                              {bottleneck.severity}
                            </Badge>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}