'use client';

import React, { useState } from 'react';
import { TimelineView } from '@/components/workflows/timeline-view';
import { FlowchartDisplay } from '@/components/workflows/flowchart-display';
import { AgentHandoffView } from '@/components/workflows/agent-handoff';
import { ProgressTracker } from '@/components/workflows/progress-tracker';
import { DependencyMap } from '@/components/workflows/dependency-map';
import { useWorkflow } from '@/hooks/use-workflow';
import { WorkflowStep, Agent, WorkflowConstraint } from '@/types/workflow';
import { 
  Play, 
  Pause, 
  RefreshCw,
  GitBranch,
  Clock,
  TrendingUp,
  Users,
  Network
} from 'lucide-react';
import { cn } from '@/lib/utils';

type ViewType = 'timeline' | 'flowchart' | 'handoffs' | 'progress' | 'dependencies';

export default function WorkflowsPage() {
  const { workflow, metrics, startSimulation, stopSimulation, simulateProgress } = useWorkflow();
  const [isSimulating, setIsSimulating] = useState(false);
  const [activeView, setActiveView] = useState<ViewType>('timeline');
  const [selectedStep, setSelectedStep] = useState<WorkflowStep | null>(null);

  // Create agents map
  const agents = new Map<string, Agent>();
  workflow.steps.forEach(step => {
    if (step.agent) {
      agents.set(step.agent.id, step.agent);
    }
  });

  // Mock constraints
  const constraints: WorkflowConstraint[] = [
    {
      id: 'constraint-1',
      type: 'resource',
      description: 'Limited processing capacity',
      severity: 'high',
      affectedSteps: ['step-4b', 'step-5']
    },
    {
      id: 'constraint-2',
      type: 'time',
      description: 'Deadline approaching',
      severity: 'medium',
      affectedSteps: ['step-6', 'step-7']
    }
  ];

  const handleToggleSimulation = () => {
    if (isSimulating) {
      stopSimulation();
    } else {
      startSimulation();
    }
    setIsSimulating(!isSimulating);
  };

  const handleStepClick = (step: WorkflowStep) => {
    setSelectedStep(step);
  };

  const viewOptions = [
    { id: 'timeline', label: 'Timeline', icon: Clock },
    { id: 'flowchart', label: 'Flowchart', icon: GitBranch },
    { id: 'progress', label: 'Progress', icon: TrendingUp },
    { id: 'handoffs', label: 'Handoffs', icon: Users },
    { id: 'dependencies', label: 'Dependencies', icon: Network }
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Workflow Visualization
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Monitor and analyze your workflow execution in real-time
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 mb-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={handleToggleSimulation}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors",
                isSimulating
                  ? "bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900 dark:text-red-300"
                  : "bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900 dark:text-green-300"
              )}
            >
              {isSimulating ? (
                <>
                  <Pause className="w-4 h-4" />
                  Pause Simulation
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Start Simulation
                </>
              )}
            </button>
            
            <button
              onClick={simulateProgress}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-300 font-medium transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Step Forward
            </button>
          </div>
          
          <div className="text-sm text-gray-600 dark:text-gray-400">
            <span className="font-medium">Status:</span> {workflow.status} | 
            <span className="font-medium ml-2">Progress:</span> {Math.round(workflow.progress)}%
          </div>
        </div>

        {/* View Selector */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-2 mb-6 flex gap-2">
          {viewOptions.map(option => {
            const Icon = option.icon;
            return (
              <button
                key={option.id}
                onClick={() => setActiveView(option.id as ViewType)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors",
                  activeView === option.id
                    ? "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300"
                    : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
                )}
              >
                <Icon className="w-4 h-4" />
                {option.label}
              </button>
            );
          })}
        </div>

        {/* Main Content */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm">
          {activeView === 'timeline' && (
            <TimelineView workflow={workflow} onStepClick={handleStepClick} />
          )}
          
          {activeView === 'flowchart' && (
            <div className="h-[600px] p-6">
              <FlowchartDisplay workflow={workflow} onNodeClick={handleStepClick} />
            </div>
          )}
          
          {activeView === 'progress' && (
            <div className="p-6">
              <ProgressTracker workflow={workflow} metrics={metrics} />
            </div>
          )}
          
          {activeView === 'handoffs' && (
            <div className="p-6">
              <AgentHandoffView 
                handoffs={workflow.handoffs} 
                agents={agents}
                onHandoffClick={(handoff) => console.log('Handoff clicked:', handoff)}
              />
            </div>
          )}
          
          {activeView === 'dependencies' && (
            <div className="h-[600px] p-6">
              <DependencyMap 
                workflow={workflow} 
                constraints={constraints}
                onNodeClick={handleStepClick}
              />
            </div>
          )}
        </div>

        {/* Selected Step Details */}
        {selectedStep && (
          <div className="mt-6 bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
            <h3 className="text-lg font-semibold mb-4">Step Details</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Name</p>
                <p className="font-medium">{selectedStep.name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Status</p>
                <p className="font-medium capitalize">{selectedStep.status}</p>
              </div>
              {selectedStep.agent && (
                <>
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Assigned Agent</p>
                    <p className="font-medium">{selectedStep.agent.name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Specialization</p>
                    <p className="font-medium">{selectedStep.agent.specialization}</p>
                  </div>
                </>
              )}
              {selectedStep.progress !== undefined && (
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Progress</p>
                  <p className="font-medium">{selectedStep.progress}%</p>
                </div>
              )}
              {selectedStep.duration && (
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Duration</p>
                  <p className="font-medium">{Math.round(selectedStep.duration / 1000)}s</p>
                </div>
              )}
            </div>
            {selectedStep.description && (
              <div className="mt-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">Description</p>
                <p className="mt-1">{selectedStep.description}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}