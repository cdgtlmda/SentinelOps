export type WorkflowStatus = 'pending' | 'active' | 'completed' | 'failed' | 'paused';
export type StepStatus = 'pending' | 'active' | 'completed' | 'failed' | 'skipped';
export type HandoffStatus = 'pending' | 'in-progress' | 'completed' | 'failed';

export interface Agent {
  id: string;
  name: string;
  avatar?: string;
  specialization: string;
  status: 'available' | 'busy' | 'offline';
}

export interface WorkflowStep {
  id: string;
  name: string;
  description?: string;
  status: StepStatus;
  startTime?: Date;
  endTime?: Date;
  duration?: number; // in milliseconds
  agent?: Agent;
  dependencies: string[]; // IDs of steps this step depends on
  parallelSteps?: string[]; // IDs of steps that can run in parallel
  isDecisionPoint?: boolean;
  decisionOptions?: DecisionOption[];
  progress?: number; // 0-100
  error?: string;
  data?: Record<string, any>;
}

export interface DecisionOption {
  id: string;
  label: string;
  condition?: string;
  nextStepId: string;
}

export interface AgentHandoff {
  id: string;
  fromAgentId: string;
  toAgentId: string;
  fromStepId: string;
  toStepId: string;
  status: HandoffStatus;
  dataPackage: {
    summary: string;
    context: Record<string, any>;
    artifacts?: string[];
  };
  startTime: Date;
  endTime?: Date;
  error?: string;
}

export interface WorkflowConnection {
  id: string;
  fromStepId: string;
  toStepId: string;
  type: 'sequential' | 'conditional' | 'parallel';
  condition?: string;
  label?: string;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  status: WorkflowStatus;
  steps: WorkflowStep[];
  connections: WorkflowConnection[];
  handoffs: AgentHandoff[];
  startTime?: Date;
  endTime?: Date;
  totalDuration?: number;
  progress: number; // 0-100
  criticalPath: string[]; // Step IDs in critical path
  currentStepId?: string;
}

export interface WorkflowNode {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  step: WorkflowStep;
}

export interface WorkflowConstraint {
  id: string;
  type: 'resource' | 'time' | 'dependency';
  description: string;
  severity: 'low' | 'medium' | 'high';
  affectedSteps: string[];
}

export interface WorkflowMetrics {
  totalSteps: number;
  completedSteps: number;
  failedSteps: number;
  averageStepDuration: number;
  estimatedTimeRemaining: number;
  bottlenecks: {
    stepId: string;
    reason: string;
    impact: 'low' | 'medium' | 'high';
  }[];
}