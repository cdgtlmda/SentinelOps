'use client';

import React, { useState } from 'react';
import { WorkflowStep, Workflow } from '@/types/workflow';
import { 
  CheckCircle2, 
  Circle, 
  XCircle, 
  Clock, 
  ChevronDown, 
  ChevronRight,
  User,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

interface TimelineViewProps {
  workflow: Workflow;
  onStepClick?: (step: WorkflowStep) => void;
}

const getStatusIcon = (status: WorkflowStep['status']) => {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="w-6 h-6 text-green-500" />;
    case 'active':
      return <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />;
    case 'failed':
      return <XCircle className="w-6 h-6 text-red-500" />;
    case 'skipped':
      return <Circle className="w-6 h-6 text-gray-400" />;
    default:
      return <Circle className="w-6 h-6 text-gray-300" />;
  }
};

const formatDuration = (ms: number): string => {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
};

const formatTime = (date: Date): string => {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  }).format(date);
};

export const TimelineView: React.FC<TimelineViewProps> = ({ workflow, onStepClick }) => {
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());

  const toggleStep = (stepId: string) => {
    setExpandedSteps(prev => {
      const next = new Set(prev);
      if (next.has(stepId)) {
        next.delete(stepId);
      } else {
        next.add(stepId);
      }
      return next;
    });
  };

  const isOnCriticalPath = (stepId: string) => {
    return workflow.criticalPath.includes(stepId);
  };

  return (
    <div className="relative p-6">
      <h3 className="text-lg font-semibold mb-6">Workflow Timeline</h3>
      
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700" />
        
        {/* Steps */}
        <div className="space-y-6">
          {workflow.steps.map((step, index) => {
            const isExpanded = expandedSteps.has(step.id);
            const isCritical = isOnCriticalPath(step.id);
            
            return (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="relative flex gap-4"
              >
                {/* Status icon */}
                <div className="relative z-10 flex-shrink-0">
                  <div className={cn(
                    "w-12 h-12 rounded-full flex items-center justify-center",
                    "bg-white dark:bg-gray-800 border-2",
                    isCritical ? "border-orange-400" : "border-gray-200 dark:border-gray-700"
                  )}>
                    {getStatusIcon(step.status)}
                  </div>
                  {isCritical && (
                    <div className="absolute -top-1 -right-1">
                      <AlertCircle className="w-4 h-4 text-orange-500" />
                    </div>
                  )}
                </div>
                
                {/* Step content */}
                <div className="flex-1 pb-6">
                  <div
                    className={cn(
                      "rounded-lg border p-4 cursor-pointer transition-all",
                      "hover:shadow-md dark:hover:shadow-gray-800",
                      step.status === 'active' && "border-blue-400 bg-blue-50 dark:bg-blue-950",
                      step.status === 'failed' && "border-red-400 bg-red-50 dark:bg-red-950",
                      step.status === 'completed' && "border-green-400 bg-green-50 dark:bg-green-950",
                      step.status === 'pending' && "border-gray-300 dark:border-gray-600",
                      step.status === 'skipped' && "opacity-50"
                    )}
                    onClick={() => {
                      toggleStep(step.id);
                      onStepClick?.(step);
                    }}
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium text-gray-900 dark:text-gray-100">
                            {step.name}
                          </h4>
                          {step.isDecisionPoint && (
                            <span className="text-xs px-2 py-1 rounded-full bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300">
                              Decision
                            </span>
                          )}
                        </div>
                        
                        {step.description && (
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {step.description}
                          </p>
                        )}
                        
                        {/* Time info */}
                        <div className="flex items-center gap-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                          {step.startTime && (
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {formatTime(step.startTime)}
                            </span>
                          )}
                          {step.duration && (
                            <span>Duration: {formatDuration(step.duration)}</span>
                          )}
                          {step.status === 'active' && step.progress !== undefined && (
                            <span>Progress: {Math.round(step.progress)}%</span>
                          )}
                        </div>
                        
                        {/* Agent info */}
                        {step.agent && (
                          <div className="flex items-center gap-2 mt-2">
                            <User className="w-4 h-4 text-gray-400" />
                            <span className="text-sm text-gray-600 dark:text-gray-400">
                              {step.agent.name} • {step.agent.specialization}
                            </span>
                          </div>
                        )}
                      </div>
                      
                      <button className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                        {isExpanded ? <ChevronDown /> : <ChevronRight />}
                      </button>
                    </div>
                    
                    {/* Progress bar */}
                    {step.status === 'active' && step.progress !== undefined && (
                      <div className="mt-3">
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <motion.div
                            className="bg-blue-500 h-2 rounded-full"
                            initial={{ width: 0 }}
                            animate={{ width: `${step.progress}%` }}
                            transition={{ duration: 0.5 }}
                          />
                        </div>
                      </div>
                    )}
                    
                    {/* Expanded details */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden"
                        >
                          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                            {/* Dependencies */}
                            {step.dependencies.length > 0 && (
                              <div className="mb-3">
                                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                                  Dependencies:
                                </span>
                                <div className="flex flex-wrap gap-2 mt-1">
                                  {step.dependencies.map(depId => {
                                    const depStep = workflow.steps.find(s => s.id === depId);
                                    return (
                                      <span
                                        key={depId}
                                        className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-800"
                                      >
                                        {depStep?.name || depId}
                                      </span>
                                    );
                                  })}
                                </div>
                              </div>
                            )}
                            
                            {/* Decision options */}
                            {step.isDecisionPoint && step.decisionOptions && (
                              <div className="mb-3">
                                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                                  Decision Options:
                                </span>
                                <div className="space-y-1 mt-1">
                                  {step.decisionOptions.map(option => (
                                    <div
                                      key={option.id}
                                      className="text-xs px-2 py-1 rounded bg-purple-100 dark:bg-purple-900"
                                    >
                                      {option.label}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {/* Error info */}
                            {step.error && (
                              <div className="text-xs text-red-600 dark:text-red-400">
                                Error: {step.error}
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
};