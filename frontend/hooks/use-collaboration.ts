import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Agent,
  Message,
  CollaborationSession,
  CollaborationMetrics,
  MessageType,
  NetworkTopology,
  SynchronizationPoint,
  ResourceLock,
  ConsensusDecision,
  CommunicationEdge,
  CollaborationState,
  CoordinationState,
  MessageStatus,
  Bottleneck
} from '@/types/collaboration';

const AGENT_NAMES = ['Orchestrator', 'DataProcessor', 'Analyzer', 'Reporter', 'Monitor', 'Validator'];
const MESSAGE_TYPES: MessageType[] = ['request', 'response', 'broadcast', 'error', 'sync', 'ack'];

export function useCollaboration(topology: NetworkTopology = 'mesh') {
  const [state, setState] = useState<CollaborationState>(() => ({
    session: createInitialSession(topology),
    synchronizationPoints: [],
    resourceLocks: [],
    consensusDecisions: [],
    communicationGraph: []
  }));

  const simulationRef = useRef<NodeJS.Timeout | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);

  // Create initial session
  function createInitialSession(topology: NetworkTopology): CollaborationSession {
    const agents = AGENT_NAMES.map((name, index) => ({
      id: `agent-${index}`,
      name,
      type: name.toLowerCase(),
      status: 'idle' as const,
      capabilities: generateCapabilities(name),
      position: calculateAgentPosition(index, AGENT_NAMES.length, topology),
      metrics: {
        messagesProcessed: 0,
        averageResponseTime: 0,
        errorRate: 0,
        throughput: 0
      }
    }));

    return {
      id: `session-${Date.now()}`,
      agents,
      messages: [],
      topology,
      startTime: Date.now(),
      metrics: {
        totalMessages: 0,
        averageResponseTime: 0,
        communicationOverhead: 0,
        efficiency: 100,
        throughput: 0,
        errorRate: 0,
        bottlenecks: []
      }
    };
  }

  // Generate agent capabilities
  function generateCapabilities(agentName: string): string[] {
    const capabilityMap: Record<string, string[]> = {
      Orchestrator: ['coordinate', 'distribute', 'monitor'],
      DataProcessor: ['transform', 'validate', 'aggregate'],
      Analyzer: ['analyze', 'predict', 'classify'],
      Reporter: ['visualize', 'export', 'notify'],
      Monitor: ['track', 'alert', 'diagnose'],
      Validator: ['verify', 'audit', 'certify']
    };
    return capabilityMap[agentName] || ['process'];
  }

  // Calculate agent positions based on topology
  function calculateAgentPosition(
    index: number,
    total: number,
    topology: NetworkTopology
  ): { x: number; y: number } {
    switch (topology) {
      case 'hub':
        if (index === 0) return { x: 50, y: 50 }; // Center
        const hubAngle = (index - 1) * (2 * Math.PI / (total - 1));
        return {
          x: 50 + 35 * Math.cos(hubAngle),
          y: 50 + 35 * Math.sin(hubAngle)
        };
      
      case 'hierarchical':
        const level = Math.floor(Math.log2(index + 1));
        const posInLevel = index - (Math.pow(2, level) - 1);
        const nodesInLevel = Math.pow(2, level);
        return {
          x: 10 + (posInLevel + 0.5) * (80 / nodesInLevel),
          y: 10 + level * 25
        };
      
      case 'mesh':
      default:
        const angle = index * (2 * Math.PI / total);
        return {
          x: 50 + 35 * Math.cos(angle),
          y: 50 + 35 * Math.sin(angle)
        };
    }
  }

  // Send message between agents
  const sendMessage = useCallback((
    fromAgentId: string,
    toAgentId: string | string[],
    type: MessageType,
    content?: any
  ) => {
    const message: Message = {
      id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      fromAgentId,
      toAgentId,
      type,
      status: 'pending',
      content: content || { action: 'process', payload: { data: 'sample' } },
      timestamp: Date.now(),
      size: Math.floor(Math.random() * 1000) + 100,
      priority: Math.random() > 0.8 ? 'high' : Math.random() > 0.5 ? 'medium' : 'low'
    };

    setState(prev => ({
      ...prev,
      session: {
        ...prev.session,
        messages: [...prev.session.messages, message]
      }
    }));

    // Simulate message delivery
    setTimeout(() => {
      setState(prev => ({
        ...prev,
        session: {
          ...prev.session,
          messages: prev.session.messages.map(msg =>
            msg.id === message.id
              ? { ...msg, status: 'in-transit' as MessageStatus }
              : msg
          )
        }
      }));
    }, 300);

    setTimeout(() => {
      const success = Math.random() > 0.1;
      setState(prev => ({
        ...prev,
        session: {
          ...prev.session,
          messages: prev.session.messages.map(msg =>
            msg.id === message.id
              ? {
                  ...msg,
                  status: success ? 'delivered' : 'failed' as MessageStatus,
                  responseTime: Date.now() - message.timestamp
                }
              : msg
          ),
          agents: prev.session.agents.map(agent => {
            if (agent.id === fromAgentId || agent.id === toAgentId || 
                (Array.isArray(toAgentId) && toAgentId.includes(agent.id))) {
              return {
                ...agent,
                metrics: {
                  ...agent.metrics,
                  messagesProcessed: agent.metrics.messagesProcessed + 1
                }
              };
            }
            return agent;
          })
        }
      }));
    }, 800 + Math.random() * 500);
  }, []);

  // Create synchronization point
  const createSyncPoint = useCallback((agentIds: string[]) => {
    const syncPoint: SynchronizationPoint = {
      id: `sync-${Date.now()}`,
      agentIds,
      state: 'waiting',
      timestamp: Date.now()
    };

    setState(prev => ({
      ...prev,
      synchronizationPoints: [...prev.synchronizationPoints, syncPoint]
    }));

    // Simulate synchronization
    setTimeout(() => {
      setState(prev => ({
        ...prev,
        synchronizationPoints: prev.synchronizationPoints.map(sp =>
          sp.id === syncPoint.id
            ? { ...sp, state: 'synchronized' as CoordinationState, duration: 1500 }
            : sp
        )
      }));
    }, 1500);
  }, []);

  // Create resource lock
  const createResourceLock = useCallback((resourceId: string, ownerId: string, waitingIds: string[]) => {
    const lock: ResourceLock = {
      id: `lock-${Date.now()}`,
      resourceId,
      ownerId,
      waitingIds,
      acquiredAt: Date.now(),
      expiresAt: Date.now() + 5000
    };

    setState(prev => ({
      ...prev,
      resourceLocks: [...prev.resourceLocks, lock]
    }));
  }, []);

  // Create consensus decision
  const createConsensusDecision = useCallback((topic: string, participants: string[]) => {
    const decision: ConsensusDecision = {
      id: `consensus-${Date.now()}`,
      topic,
      participants,
      votes: {},
      result: 'pending',
      timestamp: Date.now()
    };

    setState(prev => ({
      ...prev,
      consensusDecisions: [...prev.consensusDecisions, decision]
    }));

    // Simulate voting
    participants.forEach((agentId, index) => {
      setTimeout(() => {
        setState(prev => ({
          ...prev,
          consensusDecisions: prev.consensusDecisions.map(cd =>
            cd.id === decision.id
              ? {
                  ...cd,
                  votes: { ...cd.votes, [agentId]: Math.random() > 0.3 }
                }
              : cd
          )
        }));
      }, 500 + index * 200);
    });

    // Finalize decision
    setTimeout(() => {
      setState(prev => ({
        ...prev,
        consensusDecisions: prev.consensusDecisions.map(cd => {
          if (cd.id === decision.id) {
            const approvals = Object.values(cd.votes).filter(v => v).length;
            const result = approvals > participants.length / 2 ? 'approved' : 'rejected';
            return { ...cd, result };
          }
          return cd;
        })
      }));
    }, 500 + participants.length * 200 + 500);
  }, []);

  // Calculate metrics
  const calculateMetrics = useCallback((): CollaborationMetrics => {
    const messages = state.session.messages;
    const deliveredMessages = messages.filter(m => m.status === 'delivered');
    const failedMessages = messages.filter(m => m.status === 'failed');
    
    const totalMessages = messages.length;
    const averageResponseTime = deliveredMessages.length > 0
      ? deliveredMessages.reduce((sum, m) => sum + (m.responseTime || 0), 0) / deliveredMessages.length
      : 0;
    
    const errorRate = totalMessages > 0 ? (failedMessages.length / totalMessages) * 100 : 0;
    const throughput = totalMessages > 0
      ? (deliveredMessages.length / ((Date.now() - state.session.startTime) / 1000))
      : 0;

    // Calculate communication overhead
    const directMessages = messages.filter(m => !Array.isArray(m.toAgentId)).length;
    const broadcastMessages = messages.filter(m => Array.isArray(m.toAgentId)).length;
    const communicationOverhead = broadcastMessages * 0.5 + directMessages * 0.1;

    // Detect bottlenecks
    const bottlenecks: Bottleneck[] = [];
    state.session.agents.forEach(agent => {
      const agentMessages = messages.filter(
        m => m.fromAgentId === agent.id || m.toAgentId === agent.id
      );
      const avgResponseTime = agentMessages
        .filter(m => m.responseTime)
        .reduce((sum, m) => sum + (m.responseTime || 0), 0) / agentMessages.length;
      
      if (avgResponseTime > averageResponseTime * 1.5) {
        bottlenecks.push({
          agentId: agent.id,
          severity: avgResponseTime > averageResponseTime * 2 ? 'high' : 'medium',
          type: 'processing',
          description: `High response time: ${avgResponseTime.toFixed(0)}ms`,
          timestamp: Date.now()
        });
      }
    });

    const efficiency = 100 - (errorRate + communicationOverhead / 10);

    return {
      totalMessages,
      averageResponseTime,
      communicationOverhead,
      efficiency: Math.max(0, Math.min(100, efficiency)),
      throughput,
      errorRate,
      bottlenecks
    };
  }, [state.session]);

  // Update metrics periodically
  useEffect(() => {
    const interval = setInterval(() => {
      setState(prev => ({
        ...prev,
        session: {
          ...prev.session,
          metrics: calculateMetrics()
        }
      }));
    }, 1000);

    return () => clearInterval(interval);
  }, [calculateMetrics]);

  // Start simulation
  const startSimulation = useCallback(() => {
    setIsSimulating(true);
    
    const simulate = () => {
      // Random message between agents
      const agents = state.session.agents;
      const fromAgent = agents[Math.floor(Math.random() * agents.length)];
      const otherAgents = agents.filter(a => a.id !== fromAgent.id);
      
      if (Math.random() > 0.7) {
        // Broadcast
        sendMessage(
          fromAgent.id,
          otherAgents.map(a => a.id),
          'broadcast',
          { announcement: 'Status update' }
        );
      } else {
        // Direct message
        const toAgent = otherAgents[Math.floor(Math.random() * otherAgents.length)];
        const messageType = MESSAGE_TYPES[Math.floor(Math.random() * MESSAGE_TYPES.length)];
        sendMessage(fromAgent.id, toAgent.id, messageType);
      }

      // Occasionally create sync points
      if (Math.random() > 0.9) {
        const numAgents = 2 + Math.floor(Math.random() * 3);
        const selectedAgents = agents
          .slice()
          .sort(() => Math.random() - 0.5)
          .slice(0, numAgents)
          .map(a => a.id);
        createSyncPoint(selectedAgents);
      }

      // Occasionally create resource locks
      if (Math.random() > 0.95) {
        const owner = agents[Math.floor(Math.random() * agents.length)];
        const waitingCount = Math.floor(Math.random() * 3);
        const waiting = agents
          .filter(a => a.id !== owner.id)
          .slice(0, waitingCount)
          .map(a => a.id);
        createResourceLock(`resource-${Date.now()}`, owner.id, waiting);
      }

      // Occasionally create consensus decisions
      if (Math.random() > 0.97) {
        const participants = agents
          .slice()
          .sort(() => Math.random() - 0.5)
          .slice(0, 3 + Math.floor(Math.random() * 3))
          .map(a => a.id);
        createConsensusDecision('Deployment approval', participants);
      }
    };

    simulationRef.current = setInterval(simulate, 1000 + Math.random() * 2000);
  }, [state.session.agents, sendMessage, createSyncPoint, createResourceLock, createConsensusDecision]);

  // Stop simulation
  const stopSimulation = useCallback(() => {
    setIsSimulating(false);
    if (simulationRef.current) {
      clearInterval(simulationRef.current);
      simulationRef.current = null;
    }
  }, []);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (simulationRef.current) {
        clearInterval(simulationRef.current);
      }
    };
  }, []);

  // Update communication graph
  useEffect(() => {
    const edges: CommunicationEdge[] = [];
    const edgeMap = new Map<string, CommunicationEdge>();

    state.session.messages.forEach(message => {
      if (!Array.isArray(message.toAgentId)) {
        const key = `${message.fromAgentId}-${message.toAgentId}`;
        const existing = edgeMap.get(key);
        
        if (existing) {
          existing.weight += 1;
          existing.latency = (existing.latency + (message.responseTime || 0)) / 2;
          existing.reliability = message.status === 'delivered' 
            ? (existing.reliability + 1) / 2 
            : existing.reliability / 2;
        } else {
          edgeMap.set(key, {
            source: message.fromAgentId,
            target: message.toAgentId,
            weight: 1,
            latency: message.responseTime || 0,
            reliability: message.status === 'delivered' ? 1 : 0
          });
        }
      }
    });

    setState(prev => ({
      ...prev,
      communicationGraph: Array.from(edgeMap.values())
    }));
  }, [state.session.messages]);

  return {
    state,
    sendMessage,
    createSyncPoint,
    createResourceLock,
    createConsensusDecision,
    startSimulation,
    stopSimulation,
    isSimulating,
    metrics: state.session.metrics
  };
}