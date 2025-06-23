'use client';

import React, { useState } from 'react';
import { AgentHandoff, Agent } from '@/types/workflow';
import { 
  ArrowRight, 
  Package, 
  CheckCircle2, 
  XCircle, 
  Clock,
  FileText,
  Database,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

interface AgentHandoffProps {
  handoffs: AgentHandoff[];
  agents: Map<string, Agent>;
  onHandoffClick?: (handoff: AgentHandoff) => void;
}

const getStatusIcon = (status: AgentHandoff['status']) => {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="w-5 h-5 text-green-500" />;
    case 'in-progress':
      return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
    case 'failed':
      return <XCircle className="w-5 h-5 text-red-500" />;
    default:
      return <Clock className="w-5 h-5 text-gray-400" />;
  }
};

const getStatusColor = (status: AgentHandoff['status']) => {
  switch (status) {
    case 'completed':
      return 'border-green-400 bg-green-50 dark:bg-green-950';
    case 'in-progress':
      return 'border-blue-400 bg-blue-50 dark:bg-blue-950';
    case 'failed':
      return 'border-red-400 bg-red-50 dark:bg-red-950';
    default:
      return 'border-gray-300 dark:border-gray-600';
  }
};

const formatTime = (date: Date): string => {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  }).format(date);
};

export const AgentHandoffView: React.FC<AgentHandoffProps> = ({ 
  handoffs, 
  agents,
  onHandoffClick 
}) => {
  const [expandedHandoffs, setExpandedHandoffs] = useState<Set<string>>(new Set());

  const toggleHandoff = (handoffId: string) => {
    setExpandedHandoffs(prev => {
      const next = new Set(prev);
      if (next.has(handoffId)) {
        next.delete(handoffId);
      } else {
        next.add(handoffId);
      }
      return next;
    });
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold mb-4">Agent Handoffs</h3>
      
      {handoffs.map((handoff, index) => {
        const fromAgent = agents.get(handoff.fromAgentId);
        const toAgent = agents.get(handoff.toAgentId);
        const isExpanded = expandedHandoffs.has(handoff.id);
        
        return (
          <motion.div
            key={handoff.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className={cn(
              "rounded-lg border p-4 transition-all cursor-pointer",
              "hover:shadow-md dark:hover:shadow-gray-800",
              getStatusColor(handoff.status)
            )}
            onClick={() => {
              toggleHandoff(handoff.id);
              onHandoffClick?.(handoff);
            }}
          >
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4 flex-1">
                {/* From Agent */}
                <div className="flex items-center gap-2">
                  <div className="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                    <span className="text-sm font-medium">
                      {fromAgent?.name.charAt(0) || '?'}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm font-medium">{fromAgent?.name || 'Unknown'}</p>
                    <p className="text-xs text-gray-500">{fromAgent?.specialization}</p>
                  </div>
                </div>
                
                {/* Arrow with animation */}
                <div className="relative flex-1 max-w-[200px]">
                  <div className="h-0.5 bg-gray-300 dark:bg-gray-600 relative">
                    {handoff.status === 'in-progress' && (
                      <motion.div
                        className="absolute top-0 left-0 h-full bg-blue-500"
                        initial={{ width: '0%' }}
                        animate={{ width: '100%' }}
                        transition={{ duration: 3, repeat: Infinity }}
                      />
                    )}
                  </div>
                  <ArrowRight className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  
                  {/* Data package indicator */}
                  {handoff.status === 'in-progress' && (
                    <motion.div
                      className="absolute top-1/2 -translate-y-1/2"
                      initial={{ left: '0%' }}
                      animate={{ left: '90%' }}
                      transition={{ duration: 3, repeat: Infinity }}
                    >
                      <Package className="w-4 h-4 text-blue-500" />
                    </motion.div>
                  )}
                </div>
                
                {/* To Agent */}
                <div className="flex items-center gap-2">
                  <div className="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                    <span className="text-sm font-medium">
                      {toAgent?.name.charAt(0) || '?'}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm font-medium">{toAgent?.name || 'Unknown'}</p>
                    <p className="text-xs text-gray-500">{toAgent?.specialization}</p>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                {getStatusIcon(handoff.status)}
                <button className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                  {isExpanded ? <ChevronDown /> : <ChevronRight />}
                </button>
              </div>
            </div>
            
            {/* Summary */}
            <div className="mt-3 flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
              <span className="flex items-center gap-1">
                <FileText className="w-4 h-4" />
                {handoff.dataPackage.summary}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {formatTime(handoff.startTime)}
              </span>
              {handoff.endTime && (
                <span>
                  Duration: {Math.round((handoff.endTime.getTime() - handoff.startTime.getTime()) / 1000)}s
                </span>
              )}
            </div>
            
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
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 space-y-3">
                    {/* Context data */}
                    <div>
                      <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                        <Database className="w-4 h-4" />
                        Context Data
                      </h4>
                      <div className="bg-gray-100 dark:bg-gray-800 rounded p-3">
                        <pre className="text-xs overflow-x-auto">
                          {JSON.stringify(handoff.dataPackage.context, null, 2)}
                        </pre>
                      </div>
                    </div>
                    
                    {/* Artifacts */}
                    {handoff.dataPackage.artifacts && handoff.dataPackage.artifacts.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium mb-2">Artifacts</h4>
                        <div className="flex flex-wrap gap-2">
                          {handoff.dataPackage.artifacts.map((artifact, i) => (
                            <span
                              key={i}
                              className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-800"
                            >
                              {artifact}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Error info */}
                    {handoff.error && (
                      <div className="flex items-start gap-2 text-sm text-red-600 dark:text-red-400">
                        <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                        <span>{handoff.error}</span>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        );
      })}
      
      {handoffs.length === 0 && (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          No handoffs have occurred yet
        </div>
      )}
    </div>
  );
};