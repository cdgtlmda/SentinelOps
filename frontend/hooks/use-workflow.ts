import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  Workflow, 
  WorkflowStep, 
  StepStatus, 
  WorkflowStatus,
  AgentHandoff,
  HandoffStatus,
  WorkflowMetrics
} from '@/types/workflow';

// Mock data generator
const generateMockWorkflow = (): Workflow => {
  const steps: WorkflowStep[] = [
    {
      id: 'step-1',
      name: 'Initialize Environment',
      description: 'Set up the base environment and dependencies',
      status: 'completed',
      startTime: new Date(Date.now() - 3600000),
      endTime: new Date(Date.now() - 3300000),
      duration: 300000,
      agent: {
        id: 'agent-1',
        name: 'Setup Agent',
        specialization: 'Infrastructure',
        status: 'available'
      },
      dependencies: [],
      progress: 100
    },
    {
      id: 'step-2',
      name: 'Data Collection',
      description: 'Gather required data from various sources',
      status: 'completed',
      startTime: new Date(Date.now() - 3300000),
      endTime: new Date(Date.now() - 2700000),
      duration: 600000,
      agent: {
        id: 'agent-2',
        name: 'Data Agent',
        specialization: 'Data Processing',
        status: 'busy'
      },
      dependencies: ['step-1'],
      progress: 100
    },
    {
      id: 'step-3',
      name: 'Analysis Decision',
      description: 'Determine analysis approach based on data',
      status: 'active',
      startTime: new Date(Date.now() - 2700000),
      agent: {
        id: 'agent-3',
        name: 'Analysis Agent',
        specialization: 'Decision Making',
        status: 'busy'
      },
      dependencies: ['step-2'],
      isDecisionPoint: true,
      decisionOptions: [
        { id: 'opt-1', label: 'Standard Analysis', nextStepId: 'step-4a' },
        { id: 'opt-2', label: 'Deep Analysis', nextStepId: 'step-4b' }
      ],
      progress: 65
    },
    {
      id: 'step-4a',
      name: 'Standard Processing',
      description: 'Execute standard analysis workflow',
      status: 'pending',
      agent: {
        id: 'agent-4',
        name: 'Process Agent A',
        specialization: 'Standard Processing',
        status: 'available'
      },
      dependencies: ['step-3'],
      progress: 0
    },
    {
      id: 'step-4b',
      name: 'Deep Processing',
      description: 'Execute comprehensive analysis workflow',
      status: 'pending',
      agent: {
        id: 'agent-5',
        name: 'Process Agent B',
        specialization: 'Deep Analysis',
        status: 'available'
      },
      dependencies: ['step-3'],
      progress: 0
    },
    {
      id: 'step-5',
      name: 'Quality Check',
      description: 'Validate results and ensure quality standards',
      status: 'pending',
      dependencies: ['step-4a', 'step-4b'],
      parallelSteps: ['step-6'],
      progress: 0
    },
    {
      id: 'step-6',
      name: 'Report Generation',
      description: 'Create comprehensive report',
      status: 'pending',
      dependencies: ['step-4a', 'step-4b'],
      parallelSteps: ['step-5'],
      progress: 0
    },
    {
      id: 'step-7',
      name: 'Final Review',
      description: 'Review and approve final outputs',
      status: 'pending',
      dependencies: ['step-5', 'step-6'],
      progress: 0
    }
  ];

  const handoffs: AgentHandoff[] = [
    {
      id: 'handoff-1',
      fromAgentId: 'agent-1',
      toAgentId: 'agent-2',
      fromStepId: 'step-1',
      toStepId: 'step-2',
      status: 'completed',
      dataPackage: {
        summary: 'Environment configuration and credentials',
        context: { envReady: true, configPath: '/config/env.json' }
      },
      startTime: new Date(Date.now() - 3300000),
      endTime: new Date(Date.now() - 3250000)
    },
    {
      id: 'handoff-2',
      fromAgentId: 'agent-2',
      toAgentId: 'agent-3',
      fromStepId: 'step-2',
      toStepId: 'step-3',
      status: 'in-progress',
      dataPackage: {
        summary: 'Collected data sets and metadata',
        context: { dataSize: '2.5GB', recordCount: 150000 },
        artifacts: ['dataset_v1.csv', 'metadata.json']
      },
      startTime: new Date(Date.now() - 2700000)
    }
  ];

  return {
    id: 'workflow-1',
    name: 'Data Analysis Pipeline',
    description: 'Automated data processing and analysis workflow',
    status: 'active',
    steps,
    connections: [
      { id: 'conn-1', fromStepId: 'step-1', toStepId: 'step-2', type: 'sequential' },
      { id: 'conn-2', fromStepId: 'step-2', toStepId: 'step-3', type: 'sequential' },
      { id: 'conn-3', fromStepId: 'step-3', toStepId: 'step-4a', type: 'conditional', condition: 'Standard' },
      { id: 'conn-4', fromStepId: 'step-3', toStepId: 'step-4b', type: 'conditional', condition: 'Deep' },
      { id: 'conn-5', fromStepId: 'step-4a', toStepId: 'step-5', type: 'sequential' },
      { id: 'conn-6', fromStepId: 'step-4a', toStepId: 'step-6', type: 'parallel' },
      { id: 'conn-7', fromStepId: 'step-4b', toStepId: 'step-5', type: 'sequential' },
      { id: 'conn-8', fromStepId: 'step-4b', toStepId: 'step-6', type: 'parallel' },
      { id: 'conn-9', fromStepId: 'step-5', toStepId: 'step-7', type: 'sequential' },
      { id: 'conn-10', fromStepId: 'step-6', toStepId: 'step-7', type: 'sequential' }
    ],
    handoffs,
    startTime: new Date(Date.now() - 3600000),
    progress: 35,
    criticalPath: ['step-1', 'step-2', 'step-3', 'step-4b', 'step-5', 'step-7']
  };
};

export const useWorkflow = (workflowId?: string) => {
  const [workflow, setWorkflow] = useState<Workflow>(generateMockWorkflow());
  const [metrics, setMetrics] = useState<WorkflowMetrics | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Calculate metrics
  const calculateMetrics = useCallback((wf: Workflow): WorkflowMetrics => {
    const completedSteps = wf.steps.filter(s => s.status === 'completed').length;
    const failedSteps = wf.steps.filter(s => s.status === 'failed').length;
    
    const durations = wf.steps
      .filter(s => s.duration)
      .map(s => s.duration!);
    
    const averageStepDuration = durations.length > 0
      ? durations.reduce((a, b) => a + b, 0) / durations.length
      : 0;

    const remainingSteps = wf.steps.filter(s => 
      s.status === 'pending' || s.status === 'active'
    ).length;
    
    const estimatedTimeRemaining = remainingSteps * averageStepDuration;

    // Identify bottlenecks (simplified)
    const bottlenecks = wf.steps
      .filter(s => s.status === 'active' && s.progress && s.progress < 50)
      .map(s => ({
        stepId: s.id,
        reason: 'Slow progress detected',
        impact: s.progress! < 25 ? 'high' as const : 'medium' as const
      }));

    return {
      totalSteps: wf.steps.length,
      completedSteps,
      failedSteps,
      averageStepDuration,
      estimatedTimeRemaining,
      bottlenecks
    };
  }, []);

  // Simulate workflow progress
  const simulateProgress = useCallback(() => {
    setWorkflow(prev => {
      const updated = { ...prev };
      let changed = false;

      // Update active step progress
      updated.steps = updated.steps.map(step => {
        if (step.status === 'active' && step.progress !== undefined) {
          const newProgress = Math.min(100, step.progress + Math.random() * 10);
          
          if (newProgress >= 100) {
            // Complete the step
            return {
              ...step,
              status: 'completed' as StepStatus,
              progress: 100,
              endTime: new Date()
            };
          }
          
          changed = true;
          return { ...step, progress: newProgress };
        }
        return step;
      });

      // Activate next steps if dependencies are met
      updated.steps = updated.steps.map(step => {
        if (step.status === 'pending') {
          const dependenciesMet = step.dependencies.every(depId =>
            updated.steps.find(s => s.id === depId)?.status === 'completed'
          );
          
          if (dependenciesMet) {
            changed = true;
            return {
              ...step,
              status: 'active' as StepStatus,
              startTime: new Date(),
              progress: 0
            };
          }
        }
        return step;
      });

      // Update handoffs
      updated.handoffs = updated.handoffs.map(handoff => {
        if (handoff.status === 'in-progress' && Math.random() > 0.7) {
          return {
            ...handoff,
            status: 'completed' as HandoffStatus,
            endTime: new Date()
          };
        }
        return handoff;
      });

      // Calculate overall progress
      const completedSteps = updated.steps.filter(s => s.status === 'completed').length;
      updated.progress = (completedSteps / updated.steps.length) * 100;

      // Update workflow status
      if (updated.progress >= 100) {
        updated.status = 'completed';
        updated.endTime = new Date();
      }

      return changed ? updated : prev;
    });
  }, []);

  // Update step status
  const updateStepStatus = useCallback((stepId: string, status: StepStatus) => {
    setWorkflow(prev => ({
      ...prev,
      steps: prev.steps.map(step =>
        step.id === stepId ? { ...step, status } : step
      )
    }));
  }, []);

  // Start/stop simulation
  const startSimulation = useCallback(() => {
    if (!intervalRef.current) {
      intervalRef.current = setInterval(simulateProgress, 1000);
    }
  }, [simulateProgress]);

  const stopSimulation = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Update metrics when workflow changes
  useEffect(() => {
    setMetrics(calculateMetrics(workflow));
  }, [workflow, calculateMetrics]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    workflow,
    metrics,
    updateStepStatus,
    startSimulation,
    stopSimulation,
    simulateProgress
  };
};