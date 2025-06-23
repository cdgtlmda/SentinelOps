'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { Agent, AgentAction, AgentStatus, AgentTask, AgentType } from '@/types/agent';

// Mock agent data generator
const generateMockAgent = (id: string, index: number): Agent => {
  const types: AgentType[] = ['security', 'monitoring', 'remediation', 'analysis', 'network'];
  const names = [
    'Sentinel Alpha', 'Guardian Beta', 'Watcher Gamma', 'Defender Delta', 'Scanner Epsilon',
    'Analyzer Zeta', 'Protector Eta', 'Monitor Theta', 'Inspector Iota', 'Validator Kappa'
  ];
  
  const type = types[index % types.length];
  const status: AgentStatus = ['idle', 'processing', 'waiting', 'completed'][Math.floor(Math.random() * 4)] as AgentStatus;
  
  const currentTask: AgentTask | undefined = status === 'processing' || status === 'waiting' ? {
    id: `task-${id}-current`,
    name: 'Security Scan',
    description: 'Performing deep security analysis on network traffic patterns',
    startTime: new Date(Date.now() - Math.random() * 300000),
    progress: Math.floor(Math.random() * 80) + 20,
    status: 'running',
  } : undefined;

  return {
    id,
    name: names[index] || `Agent ${index + 1}`,
    type,
    status,
    currentTask,
    taskHistory: [],
    lastActionTimestamp: new Date(Date.now() - Math.random() * 3600000),
    metrics: {
      tasksCompleted: Math.floor(Math.random() * 100),
      tasksFailed: Math.floor(Math.random() * 10),
      averageResponseTime: Math.floor(Math.random() * 5000) + 1000,
      uptime: Math.floor(Math.random() * 86400),
      cpuUsage: Math.floor(Math.random() * 60) + 10,
      memoryUsage: Math.floor(Math.random() * 70) + 20,
    },
    capabilities: ['scan', 'analyze', 'report', 'remediate'],
    isActive: status !== 'idle',
  };
};

export function useAgents() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const intervalRef = useRef<NodeJS.Timeout>();

  // Initialize agents
  useEffect(() => {
    const mockAgents = Array.from({ length: 10 }, (_, i) => 
      generateMockAgent(`agent-${i + 1}`, i)
    );
    setAgents(mockAgents);
    setIsLoading(false);
  }, []);

  // Simulate real-time updates
  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setAgents(prevAgents => 
        prevAgents.map(agent => {
          // Randomly update agent status and metrics
          if (Math.random() > 0.7) {
            const newAgent = { ...agent };
            
            // Update status
            if (agent.status === 'processing' && agent.currentTask) {
              const newProgress = Math.min(agent.currentTask.progress + Math.random() * 10, 100);
              newAgent.currentTask = {
                ...agent.currentTask,
                progress: newProgress,
              };
              
              if (newProgress >= 100) {
                newAgent.status = 'completed';
                newAgent.currentTask = undefined;
                newAgent.metrics.tasksCompleted += 1;
              }
            } else if (agent.status === 'idle' && Math.random() > 0.8) {
              // Start a new task
              newAgent.status = 'processing';
              newAgent.currentTask = {
                id: `task-${agent.id}-${Date.now()}`,
                name: 'Automated Scan',
                description: 'Running automated security checks',
                startTime: new Date(),
                progress: 0,
                status: 'running',
              };
            }
            
            // Update metrics
            newAgent.metrics.cpuUsage = Math.max(10, Math.min(90, 
              newAgent.metrics.cpuUsage + (Math.random() - 0.5) * 10
            ));
            newAgent.metrics.memoryUsage = Math.max(20, Math.min(80, 
              newAgent.metrics.memoryUsage + (Math.random() - 0.5) * 5
            ));
            newAgent.metrics.uptime += 5;
            
            return newAgent;
          }
          return agent;
        })
      );
    }, 5000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const handleAgentAction = useCallback((agentId: string, action: AgentAction['type']) => {
    setAgents(prevAgents =>
      prevAgents.map(agent => {
        if (agent.id !== agentId) return agent;

        const updatedAgent = { ...agent };
        updatedAgent.lastActionTimestamp = new Date();

        switch (action) {
          case 'start':
            updatedAgent.status = 'processing';
            updatedAgent.isActive = true;
            updatedAgent.currentTask = {
              id: `task-${agent.id}-${Date.now()}`,
              name: 'Manual Task',
              description: 'Manually initiated security scan',
              startTime: new Date(),
              progress: 0,
              status: 'running',
            };
            break;

          case 'stop':
            updatedAgent.status = 'idle';
            updatedAgent.isActive = false;
            if (updatedAgent.currentTask) {
              updatedAgent.currentTask = {
                ...updatedAgent.currentTask,
                status: 'failed',
                endTime: new Date(),
                error: 'Task stopped by user',
              };
              updatedAgent.metrics.tasksFailed += 1;
            }
            updatedAgent.currentTask = undefined;
            break;

          case 'restart':
            updatedAgent.status = 'idle';
            updatedAgent.isActive = false;
            updatedAgent.currentTask = undefined;
            updatedAgent.error = undefined;
            // Simulate restart delay
            setTimeout(() => {
              setAgents(prev =>
                prev.map(a => {
                  if (a.id === agentId) {
                    return {
                      ...a,
                      status: 'processing',
                      isActive: true,
                      currentTask: {
                        id: `task-${a.id}-${Date.now()}`,
                        name: 'System Check',
                        description: 'Running post-restart system checks',
                        startTime: new Date(),
                        progress: 0,
                        status: 'running',
                      },
                    };
                  }
                  return a;
                })
              );
            }, 2000);
            break;

          case 'clearError':
            updatedAgent.error = undefined;
            updatedAgent.status = 'idle';
            break;
        }

        return updatedAgent;
      })
    );
  }, []);

  const simulateError = useCallback((agentId: string) => {
    setAgents(prevAgents =>
      prevAgents.map(agent => {
        if (agent.id === agentId) {
          return {
            ...agent,
            status: 'error' as AgentStatus,
            error: {
              message: 'Connection timeout: Unable to reach target system',
              code: 'CONN_TIMEOUT',
              timestamp: new Date(),
            },
            currentTask: undefined,
          };
        }
        return agent;
      })
    );
  }, []);

  return {
    agents,
    isLoading,
    handleAgentAction,
    simulateError,
  };
}