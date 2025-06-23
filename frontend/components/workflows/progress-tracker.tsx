'use client';

import React from 'react';
import { Workflow, WorkflowMetrics } from '@/types/workflow';
import { 
  TrendingUp, 
  Clock, 
  AlertTriangle, 
  CheckCircle2,
  Activity,
  Zap
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

interface ProgressTrackerProps {
  workflow: Workflow;
  metrics: WorkflowMetrics | null;
}

const formatTime = (ms: number): string => {
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

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({ workflow, metrics }) => {
  const criticalPathSteps = workflow.steps.filter(step => 
    workflow.criticalPath.includes(step.id)
  );
  
  const criticalPathProgress = criticalPathSteps.length > 0
    ? criticalPathSteps.filter(s => s.status === 'completed').length / criticalPathSteps.length * 100
    : 0;

  return (
    <div className="space-y-6">
      {/* Overall Progress */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Overall Progress</h3>
          <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {Math.round(workflow.progress)}%
          </span>
        </div>
        
        <div className="relative">
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
            <motion.div
              className="bg-gradient-to-r from-blue-500 to-blue-600 h-4 rounded-full relative overflow-hidden"
              initial={{ width: 0 }}
              animate={{ width: `${workflow.progress}%` }}
              transition={{ duration: 0.5 }}
            >
              {/* Animated shimmer effect */}
              <motion.div
                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                animate={{ x: ['0%', '100%'] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            </motion.div>
          </div>
          
          {/* Milestone markers */}
          <div className="absolute top-0 w-full h-4 flex items-center">
            {[25, 50, 75].map(milestone => (
              <div
                key={milestone}
                className="absolute h-6 w-0.5 bg-gray-400 dark:bg-gray-600 -top-1"
                style={{ left: `${milestone}%` }}
              />
            ))}
          </div>
        </div>
        
        <div className="grid grid-cols-3 gap-4 mt-6">
          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">Completed</p>
            <p className="text-xl font-semibold text-green-600 dark:text-green-400">
              {metrics?.completedSteps || 0}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">In Progress</p>
            <p className="text-xl font-semibold text-blue-600 dark:text-blue-400">
              {workflow.steps.filter(s => s.status === 'active').length}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">Remaining</p>
            <p className="text-xl font-semibold text-gray-600 dark:text-gray-400">
              {workflow.steps.filter(s => s.status === 'pending').length}
            </p>
          </div>
        </div>
      </div>
      
      {/* Critical Path Progress */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Zap className="w-5 h-5 text-orange-500" />
            Critical Path Progress
          </h3>
          <span className="text-xl font-bold text-orange-600 dark:text-orange-400">
            {Math.round(criticalPathProgress)}%
          </span>
        </div>
        
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
          <motion.div
            className="bg-gradient-to-r from-orange-500 to-orange-600 h-3 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${criticalPathProgress}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
        
        <div className="mt-4 space-y-2">
          {criticalPathSteps.map((step, index) => (
            <div key={step.id} className="flex items-center gap-3 text-sm">
              <span className={cn(
                "w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium",
                step.status === 'completed' ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300" :
                step.status === 'active' ? "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300" :
                "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300"
              )}>
                {index + 1}
              </span>
              <span className={cn(
                "flex-1",
                step.status === 'completed' && "line-through text-gray-500"
              )}>
                {step.name}
              </span>
              {step.status === 'completed' && <CheckCircle2 className="w-4 h-4 text-green-500" />}
              {step.status === 'active' && <Activity className="w-4 h-4 text-blue-500" />}
            </div>
          ))}
        </div>
      </div>
      
      {/* Time Metrics */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-blue-500" />
          Time Metrics
        </h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Elapsed Time</p>
            <p className="text-xl font-semibold">
              {workflow.startTime ? formatTime(Date.now() - workflow.startTime.getTime()) : '-'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Est. Time Remaining</p>
            <p className="text-xl font-semibold text-blue-600 dark:text-blue-400">
              {metrics ? formatTime(metrics.estimatedTimeRemaining) : '-'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Avg. Step Duration</p>
            <p className="text-xl font-semibold">
              {metrics ? formatTime(metrics.averageStepDuration) : '-'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Duration</p>
            <p className="text-xl font-semibold">
              {workflow.totalDuration ? formatTime(workflow.totalDuration) : '-'}
            </p>
          </div>
        </div>
      </div>
      
      {/* Bottlenecks */}
      {metrics && metrics.bottlenecks.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-500" />
            Bottlenecks Detected
          </h3>
          
          <div className="space-y-3">
            {metrics.bottlenecks.map((bottleneck, index) => {
              const step = workflow.steps.find(s => s.id === bottleneck.stepId);
              return (
                <motion.div
                  key={bottleneck.stepId}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={cn(
                    "flex items-center justify-between p-3 rounded-lg",
                    bottleneck.impact === 'high' ? "bg-red-50 dark:bg-red-950" :
                    bottleneck.impact === 'medium' ? "bg-yellow-50 dark:bg-yellow-950" :
                    "bg-gray-50 dark:bg-gray-900"
                  )}
                >
                  <div>
                    <p className="font-medium">{step?.name || bottleneck.stepId}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{bottleneck.reason}</p>
                  </div>
                  <span className={cn(
                    "px-2 py-1 rounded text-xs font-medium",
                    bottleneck.impact === 'high' ? "bg-red-200 text-red-800 dark:bg-red-800 dark:text-red-200" :
                    bottleneck.impact === 'medium' ? "bg-yellow-200 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200" :
                    "bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
                  )}>
                    {bottleneck.impact} impact
                  </span>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};