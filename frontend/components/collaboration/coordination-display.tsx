'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  GitBranch, 
  Lock, 
  Unlock, 
  Users, 
  CheckCircle, 
  XCircle, 
  Clock,
  AlertTriangle,
  Zap,
  Shield,
  Vote,
  Timer
} from 'lucide-react';
import { 
  SynchronizationPoint, 
  ResourceLock, 
  ConsensusDecision,
  CoordinationState,
  Agent
} from '@/types/collaboration';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';

interface CoordinationDisplayProps {
  synchronizationPoints: SynchronizationPoint[];
  resourceLocks: ResourceLock[];
  consensusDecisions: ConsensusDecision[];
  agents: Agent[];
}

export function CoordinationDisplay({
  synchronizationPoints,
  resourceLocks,
  consensusDecisions,
  agents
}: CoordinationDisplayProps) {
  const [activeTab, setActiveTab] = useState('sync');
  const [selectedItem, setSelectedItem] = useState<string | null>(null);

  const getStateColor = (state: CoordinationState): string => {
    switch (state) {
      case 'synchronized':
        return 'text-green-500';
      case 'waiting':
        return 'text-yellow-500';
      case 'conflicted':
        return 'text-red-500';
      case 'active':
        return 'text-blue-500';
      default:
        return 'text-gray-500';
    }
  };

  const getStateIcon = (state: CoordinationState) => {
    switch (state) {
      case 'synchronized':
        return <CheckCircle className="w-4 h-4" />;
      case 'waiting':
        return <Clock className="w-4 h-4" />;
      case 'conflicted':
        return <AlertTriangle className="w-4 h-4" />;
      case 'active':
        return <Zap className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const getAgentName = (agentId: string): string => {
    return agents.find(a => a.id === agentId)?.name || 'Unknown';
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GitBranch className="w-5 h-5" />
            <CardTitle>Coordination Display</CardTitle>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span>Synchronized</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-yellow-500" />
              <span>Waiting</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <span>Conflicted</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="sync" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Synchronization
            </TabsTrigger>
            <TabsTrigger value="locks" className="flex items-center gap-2">
              <Lock className="w-4 h-4" />
              Resource Locks
            </TabsTrigger>
            <TabsTrigger value="consensus" className="flex items-center gap-2">
              <Vote className="w-4 h-4" />
              Consensus
            </TabsTrigger>
          </TabsList>

          <TabsContent value="sync" className="mt-4">
            <ScrollArea className="h-[450px]">
              <div className="space-y-4">
                <AnimatePresence mode="popLayout">
                  {synchronizationPoints.map((point, index) => (
                    <motion.div
                      key={point.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      transition={{ delay: index * 0.05 }}
                      className={cn(
                        "border rounded-lg p-4 cursor-pointer transition-all",
                        selectedItem === point.id && "ring-2 ring-primary"
                      )}
                      onClick={() => setSelectedItem(selectedItem === point.id ? null : point.id)}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <div className={cn("p-2 rounded-lg", 
                            point.state === 'synchronized' && "bg-green-100 dark:bg-green-900/20",
                            point.state === 'waiting' && "bg-yellow-100 dark:bg-yellow-900/20",
                            point.state === 'conflicted' && "bg-red-100 dark:bg-red-900/20"
                          )}>
                            <div className={getStateColor(point.state)}>
                              {getStateIcon(point.state)}
                            </div>
                          </div>
                          <div>
                            <div className="font-medium">Synchronization Point</div>
                            <div className="text-sm text-muted-foreground">
                              {formatDistanceToNow(point.timestamp, { addSuffix: true })}
                            </div>
                          </div>
                        </div>
                        <Badge className={cn(
                          point.state === 'synchronized' && "bg-green-100 text-green-700",
                          point.state === 'waiting' && "bg-yellow-100 text-yellow-700",
                          point.state === 'conflicted' && "bg-red-100 text-red-700"
                        )}>
                          {point.state}
                        </Badge>
                      </div>

                      <div className="space-y-2">
                        <div className="flex flex-wrap gap-2">
                          {point.agentIds.map(agentId => (
                            <Badge key={agentId} variant="secondary">
                              {getAgentName(agentId)}
                            </Badge>
                          ))}
                        </div>

                        {point.duration && (
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Timer className="w-3 h-3" />
                            <span>Duration: {point.duration}ms</span>
                          </div>
                        )}

                        {selectedItem === point.id && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="mt-3 pt-3 border-t"
                          >
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              <div>
                                <span className="text-muted-foreground">Agents:</span>
                                <span className="ml-2 font-medium">{point.agentIds.length}</span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Result:</span>
                                <span className="ml-2 font-medium capitalize">
                                  {point.result || 'In Progress'}
                                </span>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="locks" className="mt-4">
            <ScrollArea className="h-[450px]">
              <div className="space-y-4">
                <AnimatePresence mode="popLayout">
                  {resourceLocks.map((lock, index) => {
                    const owner = agents.find(a => a.id === lock.ownerId);
                    const isExpired = lock.expiresAt && lock.expiresAt < Date.now();

                    return (
                      <motion.div
                        key={lock.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        transition={{ delay: index * 0.05 }}
                        className="border rounded-lg p-4"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <div className={cn(
                              "p-2 rounded-lg",
                              isExpired ? "bg-red-100 dark:bg-red-900/20" : "bg-blue-100 dark:bg-blue-900/20"
                            )}>
                              {isExpired ? (
                                <Unlock className="w-4 h-4 text-red-500" />
                              ) : (
                                <Lock className="w-4 h-4 text-blue-500" />
                              )}
                            </div>
                            <div>
                              <div className="font-medium">{lock.resourceId}</div>
                              <div className="text-sm text-muted-foreground">
                                Acquired {formatDistanceToNow(lock.acquiredAt, { addSuffix: true })}
                              </div>
                            </div>
                          </div>
                          <Badge variant={isExpired ? "destructive" : "default"}>
                            {isExpired ? "Expired" : "Active"}
                          </Badge>
                        </div>

                        <div className="space-y-3">
                          <div className="flex items-center gap-2">
                            <Shield className="w-4 h-4 text-muted-foreground" />
                            <span className="text-sm text-muted-foreground">Owner:</span>
                            <Badge variant="outline">{owner?.name || 'Unknown'}</Badge>
                          </div>

                          {lock.waitingIds.length > 0 && (
                            <div>
                              <div className="flex items-center gap-2 mb-2">
                                <Clock className="w-4 h-4 text-muted-foreground" />
                                <span className="text-sm text-muted-foreground">
                                  Waiting ({lock.waitingIds.length})
                                </span>
                              </div>
                              <div className="flex flex-wrap gap-1">
                                {lock.waitingIds.map(agentId => (
                                  <Badge key={agentId} variant="secondary" className="text-xs">
                                    {getAgentName(agentId)}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}

                          {lock.expiresAt && !isExpired && (
                            <div className="space-y-1">
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">Time remaining</span>
                                <span className="font-medium">
                                  {Math.max(0, Math.floor((lock.expiresAt - Date.now()) / 1000))}s
                                </span>
                              </div>
                              <Progress 
                                value={Math.max(0, ((lock.expiresAt - Date.now()) / (lock.expiresAt - lock.acquiredAt)) * 100)}
                                className="h-2"
                              />
                            </div>
                          )}
                        </div>
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="consensus" className="mt-4">
            <ScrollArea className="h-[450px]">
              <div className="space-y-4">
                <AnimatePresence mode="popLayout">
                  {consensusDecisions.map((decision, index) => {
                    const approvals = Object.values(decision.votes).filter(v => v).length;
                    const rejections = Object.values(decision.votes).filter(v => !v).length;
                    const pending = decision.participants.length - Object.keys(decision.votes).length;
                    const approvalRate = decision.participants.length > 0
                      ? (approvals / decision.participants.length) * 100
                      : 0;

                    return (
                      <motion.div
                        key={decision.id}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        transition={{ delay: index * 0.05 }}
                        className="border rounded-lg p-4"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <div className="font-medium">{decision.topic}</div>
                            <div className="text-sm text-muted-foreground">
                              {formatDistanceToNow(decision.timestamp, { addSuffix: true })}
                            </div>
                          </div>
                          <Badge className={cn(
                            decision.result === 'approved' && "bg-green-100 text-green-700",
                            decision.result === 'rejected' && "bg-red-100 text-red-700",
                            decision.result === 'pending' && "bg-yellow-100 text-yellow-700"
                          )}>
                            {decision.result}
                          </Badge>
                        </div>

                        <div className="space-y-3">
                          {/* Voting progress */}
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="text-muted-foreground">Approval Rate</span>
                              <span className="font-medium">{approvalRate.toFixed(0)}%</span>
                            </div>
                            <Progress value={approvalRate} className="h-2" />
                          </div>

                          {/* Vote breakdown */}
                          <div className="grid grid-cols-3 gap-2 text-sm">
                            <div className="flex items-center gap-1">
                              <CheckCircle className="w-3 h-3 text-green-500" />
                              <span>{approvals} Approved</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <XCircle className="w-3 h-3 text-red-500" />
                              <span>{rejections} Rejected</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Clock className="w-3 h-3 text-yellow-500" />
                              <span>{pending} Pending</span>
                            </div>
                          </div>

                          {/* Participants */}
                          <div>
                            <div className="text-sm text-muted-foreground mb-2">Participants</div>
                            <div className="flex flex-wrap gap-2">
                              {decision.participants.map(agentId => {
                                const vote = decision.votes[agentId];
                                return (
                                  <Badge
                                    key={agentId}
                                    variant="outline"
                                    className={cn(
                                      vote === true && "border-green-500 text-green-700",
                                      vote === false && "border-red-500 text-red-700",
                                      vote === undefined && "border-yellow-500 text-yellow-700"
                                    )}
                                  >
                                    <div className="flex items-center gap-1">
                                      {vote === true && <CheckCircle className="w-3 h-3" />}
                                      {vote === false && <XCircle className="w-3 h-3" />}
                                      {vote === undefined && <Clock className="w-3 h-3" />}
                                      {getAgentName(agentId)}
                                    </div>
                                  </Badge>
                                );
                              })}
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}