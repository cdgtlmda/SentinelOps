'use client';

import React, { useMemo, useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { motion, AnimatePresence } from 'framer-motion';
import { Network, Radio, AlertCircle, CheckCircle, Loader2, Share2 } from 'lucide-react';
import { Agent, Message, NetworkTopology, MessageType } from '@/types/collaboration';
import { cn } from '@/lib/utils';

interface AgentCommunicationFlowProps {
  agents: Agent[];
  messages: Message[];
  topology: NetworkTopology;
  onTopologyChange?: (topology: NetworkTopology) => void;
}

interface AnimatedMessage {
  message: Message;
  fromPos: { x: number; y: number };
  toPos: { x: number; y: number };
  id: string;
}

export function AgentCommunicationFlow({
  agents,
  messages,
  topology,
  onTopologyChange
}: AgentCommunicationFlowProps) {
  const [animatedMessages, setAnimatedMessages] = useState<AnimatedMessage[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  // Track messages for animation
  useEffect(() => {
    const recentMessages = messages.slice(-20).filter(m => m.status === 'in-transit');
    
    recentMessages.forEach(message => {
      const fromAgent = agents.find(a => a.id === message.fromAgentId);
      const toAgents = Array.isArray(message.toAgentId)
        ? agents.filter(a => message.toAgentId.includes(a.id))
        : agents.filter(a => a.id === message.toAgentId);

      if (fromAgent && toAgents.length > 0) {
        toAgents.forEach(toAgent => {
          const animId = `${message.id}-${toAgent.id}`;
          setAnimatedMessages(prev => {
            if (prev.some(am => am.id === animId)) return prev;
            
            return [...prev, {
              message,
              fromPos: fromAgent.position || { x: 50, y: 50 },
              toPos: toAgent.position || { x: 50, y: 50 },
              id: animId
            }];
          });

          // Remove after animation
          setTimeout(() => {
            setAnimatedMessages(prev => prev.filter(am => am.id !== animId));
          }, 2000);
        });
      }
    });
  }, [messages, agents]);

  const messageTypeConfig: Record<MessageType, { color: string; icon: React.ReactNode }> = {
    request: { color: 'text-blue-500', icon: <Radio className="w-3 h-3" /> },
    response: { color: 'text-green-500', icon: <CheckCircle className="w-3 h-3" /> },
    broadcast: { color: 'text-purple-500', icon: <Share2 className="w-3 h-3" /> },
    error: { color: 'text-red-500', icon: <AlertCircle className="w-3 h-3" /> },
    sync: { color: 'text-yellow-500', icon: <Loader2 className="w-3 h-3 animate-spin" /> },
    ack: { color: 'text-gray-500', icon: <CheckCircle className="w-3 h-3" /> }
  };

  const getAgentConnections = (agentId: string) => {
    const connections = new Set<string>();
    messages.forEach(msg => {
      if (msg.fromAgentId === agentId) {
        if (Array.isArray(msg.toAgentId)) {
          msg.toAgentId.forEach(id => connections.add(id));
        } else {
          connections.add(msg.toAgentId);
        }
      } else if (msg.toAgentId === agentId || (Array.isArray(msg.toAgentId) && msg.toAgentId.includes(agentId))) {
        connections.add(msg.fromAgentId);
      }
    });
    return Array.from(connections);
  };

  const renderConnection = (from: Agent, to: Agent) => {
    const key = `${from.id}-${to.id}`;
    const messageCount = messages.filter(
      m => (m.fromAgentId === from.id && m.toAgentId === to.id) ||
           (m.fromAgentId === to.id && m.toAgentId === from.id)
    ).length;

    if (messageCount === 0) return null;

    const fromPos = from.position || { x: 50, y: 50 };
    const toPos = to.position || { x: 50, y: 50 };

    return (
      <line
        key={key}
        x1={`${fromPos.x}%`}
        y1={`${fromPos.y}%`}
        x2={`${toPos.x}%`}
        y2={`${toPos.y}%`}
        stroke="currentColor"
        strokeWidth={Math.min(messageCount / 5, 3)}
        strokeOpacity={0.3}
        className="text-gray-400 dark:text-gray-600"
        strokeDasharray={topology === 'hierarchical' ? '5,5' : undefined}
      />
    );
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Network className="w-5 h-5" />
            <CardTitle>Agent Communication Flow</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Select value={topology} onValueChange={(value) => onTopologyChange?.(value as NetworkTopology)}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="hub">Hub</SelectItem>
                <SelectItem value="mesh">Mesh</SelectItem>
                <SelectItem value="hierarchical">Hierarchical</SelectItem>
              </SelectContent>
            </Select>
            <div className="flex gap-1">
              {Object.entries(messageTypeConfig).map(([type, config]) => (
                <div key={type} className="flex items-center gap-1">
                  <div className={cn("w-2 h-2 rounded-full", config.color.replace('text-', 'bg-'))} />
                  <span className="text-xs text-muted-foreground">{type}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="relative w-full h-[500px] bg-gradient-to-br from-background to-muted/20 rounded-lg overflow-hidden">
          <svg className="absolute inset-0 w-full h-full">
            {/* Render connections */}
            {topology === 'mesh' && agents.map((agent, i) => 
              agents.slice(i + 1).map(otherAgent => 
                renderConnection(agent, otherAgent)
              )
            )}
            
            {topology === 'hub' && agents.slice(1).map(agent => 
              renderConnection(agents[0], agent)
            )}
            
            {topology === 'hierarchical' && agents.map((agent, i) => {
              const parentIndex = Math.floor((i - 1) / 2);
              if (parentIndex >= 0 && parentIndex < agents.length) {
                return renderConnection(agents[parentIndex], agent);
              }
              return null;
            })}
          </svg>

          {/* Render agents */}
          {agents.map(agent => {
            const position = agent.position || { x: 50, y: 50 };
            const connections = getAgentConnections(agent.id);
            const isSelected = selectedAgent === agent.id;
            const isConnected = selectedAgent && connections.includes(selectedAgent);

            return (
              <motion.div
                key={agent.id}
                className={cn(
                  "absolute w-24 h-24 -ml-12 -mt-12 cursor-pointer transition-all",
                  isSelected && "z-10",
                  selectedAgent && !isSelected && !isConnected && "opacity-30"
                )}
                style={{
                  left: `${position.x}%`,
                  top: `${position.y}%`
                }}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setSelectedAgent(isSelected ? null : agent.id)}
              >
                <div className={cn(
                  "relative w-full h-full rounded-full flex items-center justify-center transition-all",
                  "bg-gradient-to-br shadow-lg",
                  agent.status === 'active' && "from-green-500/20 to-green-600/20 border-2 border-green-500",
                  agent.status === 'busy' && "from-yellow-500/20 to-yellow-600/20 border-2 border-yellow-500",
                  agent.status === 'idle' && "from-gray-500/20 to-gray-600/20 border-2 border-gray-500",
                  agent.status === 'error' && "from-red-500/20 to-red-600/20 border-2 border-red-500",
                  isSelected && "ring-4 ring-primary/50"
                )}>
                  <div className="text-center">
                    <div className="font-semibold text-sm">{agent.name}</div>
                    <Badge variant="secondary" className="text-xs mt-1">
                      {agent.metrics.messagesProcessed} msgs
                    </Badge>
                  </div>
                  
                  {/* Status indicator */}
                  <div className={cn(
                    "absolute top-0 right-0 w-3 h-3 rounded-full",
                    agent.status === 'active' && "bg-green-500",
                    agent.status === 'busy' && "bg-yellow-500 animate-pulse",
                    agent.status === 'idle' && "bg-gray-500",
                    agent.status === 'error' && "bg-red-500"
                  )} />
                </div>
              </motion.div>
            );
          })}

          {/* Animated messages */}
          <AnimatePresence>
            {animatedMessages.map(({ message, fromPos, toPos, id }) => {
              const config = messageTypeConfig[message.type];
              const progress = { x: fromPos.x, y: fromPos.y };

              return (
                <motion.div
                  key={id}
                  className={cn(
                    "absolute w-8 h-8 -ml-4 -mt-4 rounded-full flex items-center justify-center",
                    "shadow-lg",
                    config.color.replace('text-', 'bg-').replace('500', '500/80')
                  )}
                  initial={{ left: `${fromPos.x}%`, top: `${fromPos.y}%`, scale: 0 }}
                  animate={{ 
                    left: `${toPos.x}%`, 
                    top: `${toPos.y}%`, 
                    scale: [0, 1.2, 1, 1.2, 0]
                  }}
                  exit={{ scale: 0 }}
                  transition={{ 
                    duration: 2,
                    ease: "easeInOut",
                    scale: { times: [0, 0.1, 0.5, 0.9, 1] }
                  }}
                >
                  {config.icon}
                </motion.div>
              );
            })}
          </AnimatePresence>

          {/* Message queue indicator */}
          {messages.filter(m => m.status === 'pending').length > 0 && (
            <div className="absolute bottom-4 right-4 bg-background/90 backdrop-blur-sm rounded-lg p-3 shadow-lg">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-primary" />
                <span className="text-sm font-medium">
                  {messages.filter(m => m.status === 'pending').length} messages queued
                </span>
              </div>
            </div>
          )}

          {/* Selected agent info */}
          {selectedAgent && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="absolute bottom-4 left-4 bg-background/90 backdrop-blur-sm rounded-lg p-4 shadow-lg max-w-xs"
            >
              <div className="font-semibold mb-2">
                {agents.find(a => a.id === selectedAgent)?.name}
              </div>
              <div className="space-y-1 text-sm">
                <div>Status: {agents.find(a => a.id === selectedAgent)?.status}</div>
                <div>Messages: {agents.find(a => a.id === selectedAgent)?.metrics.messagesProcessed}</div>
                <div>Connections: {getAgentConnections(selectedAgent).length}</div>
              </div>
            </motion.div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}