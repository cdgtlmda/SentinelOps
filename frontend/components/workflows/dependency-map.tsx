'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Workflow, WorkflowStep, WorkflowConstraint } from '@/types/workflow';
import { 
  GitBranch, 
  Lock, 
  Clock, 
  Users,
  AlertTriangle,
  Info,
  Layers
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

interface DependencyMapProps {
  workflow: Workflow;
  constraints?: WorkflowConstraint[];
  onNodeClick?: (step: WorkflowStep) => void;
}

interface GraphNode {
  id: string;
  x: number;
  y: number;
  level: number;
  step: WorkflowStep;
}

const RADIUS = 250;
const NODE_SIZE = 60;

export const DependencyMap: React.FC<DependencyMapProps> = ({ 
  workflow, 
  constraints = [],
  onNodeClick 
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [graphNodes, setGraphNodes] = useState<Map<string, GraphNode>>(new Map());

  // Calculate node positions in a circular layout with levels
  useEffect(() => {
    const nodes = new Map<string, GraphNode>();
    const levels = new Map<string, number>();
    
    // Calculate levels using topological sort
    const visited = new Set<string>();
    const calculateLevel = (stepId: string): number => {
      if (levels.has(stepId)) return levels.get(stepId)!;
      
      const step = workflow.steps.find(s => s.id === stepId);
      if (!step) return 0;
      
      if (step.dependencies.length === 0) {
        levels.set(stepId, 0);
        return 0;
      }
      
      const maxDepLevel = Math.max(
        ...step.dependencies.map(depId => calculateLevel(depId))
      );
      
      const level = maxDepLevel + 1;
      levels.set(stepId, level);
      return level;
    };
    
    // Calculate levels for all steps
    workflow.steps.forEach(step => calculateLevel(step.id));
    
    // Group by level
    const levelGroups = new Map<number, WorkflowStep[]>();
    workflow.steps.forEach(step => {
      const level = levels.get(step.id) || 0;
      if (!levelGroups.has(level)) {
        levelGroups.set(level, []);
      }
      levelGroups.get(level)!.push(step);
    });
    
    // Position nodes
    const maxLevel = Math.max(...Array.from(levelGroups.keys()));
    
    levelGroups.forEach((steps, level) => {
      const levelRadius = RADIUS * (level + 1) / (maxLevel + 1);
      const angleStep = (2 * Math.PI) / steps.length;
      
      steps.forEach((step, index) => {
        const angle = angleStep * index - Math.PI / 2;
        nodes.set(step.id, {
          id: step.id,
          x: Math.cos(angle) * levelRadius,
          y: Math.sin(angle) * levelRadius,
          level,
          step
        });
      });
    });
    
    setGraphNodes(nodes);
  }, [workflow]);

  // Draw dependency line
  const drawDependencyLine = (fromId: string, toId: string, isOnCriticalPath: boolean) => {
    const fromNode = graphNodes.get(fromId);
    const toNode = graphNodes.get(toId);
    
    if (!fromNode || !toNode) return null;
    
    const dx = toNode.x - fromNode.x;
    const dy = toNode.y - fromNode.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    // Calculate edge points
    const fromEdgeX = fromNode.x + (dx / distance) * (NODE_SIZE / 2);
    const fromEdgeY = fromNode.y + (dy / distance) * (NODE_SIZE / 2);
    const toEdgeX = toNode.x - (dx / distance) * (NODE_SIZE / 2);
    const toEdgeY = toNode.y - (dy / distance) * (NODE_SIZE / 2);
    
    const isHighlighted = hoveredNode === fromId || hoveredNode === toId ||
                         selectedNode === fromId || selectedNode === toId;
    
    return (
      <g key={`${fromId}-${toId}`}>
        <line
          x1={fromEdgeX}
          y1={fromEdgeY}
          x2={toEdgeX}
          y2={toEdgeY}
          stroke={isOnCriticalPath ? '#f97316' : '#9ca3af'}
          strokeWidth={isHighlighted ? 3 : isOnCriticalPath ? 2 : 1}
          strokeDasharray={isOnCriticalPath ? undefined : '5,5'}
          opacity={isHighlighted ? 1 : 0.6}
          className="transition-all duration-200"
        />
        {/* Arrow */}
        <polygon
          points={`${toEdgeX},${toEdgeY} ${toEdgeX - 8},${toEdgeY - 4} ${toEdgeX - 8},${toEdgeY + 4}`}
          fill={isOnCriticalPath ? '#f97316' : '#9ca3af'}
          transform={`rotate(${Math.atan2(dy, dx) * 180 / Math.PI}, ${toEdgeX}, ${toEdgeY})`}
        />
      </g>
    );
  };

  // Get constraint icon
  const getConstraintIcon = (type: WorkflowConstraint['type']) => {
    switch (type) {
      case 'resource':
        return <Users className="w-4 h-4" />;
      case 'time':
        return <Clock className="w-4 h-4" />;
      case 'dependency':
        return <Lock className="w-4 h-4" />;
    }
  };

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node.id === selectedNode ? null : node.id);
    onNodeClick?.(node.step);
  };

  return (
    <div className="relative h-full w-full">
      {/* Legend */}
      <div className="absolute top-4 left-4 bg-white dark:bg-gray-800 rounded-lg p-4 shadow-lg">
        <h4 className="text-sm font-semibold mb-2">Legend</h4>
        <div className="space-y-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-orange-500" />
            <span>Critical Path</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-gray-400 border-dashed border-b-2" />
            <span>Dependency</span>
          </div>
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-500" />
            <span>Parallel Tasks</span>
          </div>
        </div>
      </div>
      
      {/* Constraints panel */}
      {constraints.length > 0 && (
        <div className="absolute top-4 right-4 bg-white dark:bg-gray-800 rounded-lg p-4 shadow-lg max-w-xs">
          <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-yellow-500" />
            Constraints
          </h4>
          <div className="space-y-2">
            {constraints.map((constraint, index) => (
              <motion.div
                key={constraint.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className={cn(
                  "text-xs p-2 rounded flex items-start gap-2",
                  constraint.severity === 'high' ? "bg-red-50 dark:bg-red-950" :
                  constraint.severity === 'medium' ? "bg-yellow-50 dark:bg-yellow-950" :
                  "bg-gray-50 dark:bg-gray-900"
                )}
              >
                {getConstraintIcon(constraint.type)}
                <div className="flex-1">
                  <p className="font-medium">{constraint.description}</p>
                  <p className="text-gray-600 dark:text-gray-400 mt-1">
                    Affects: {constraint.affectedSteps.length} steps
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}
      
      {/* Graph */}
      <svg
        ref={svgRef}
        className="w-full h-full"
        viewBox={`${-RADIUS * 1.5} ${-RADIUS * 1.5} ${RADIUS * 3} ${RADIUS * 3}`}
      >
        <g>
          {/* Draw concentric circles for levels */}
          {Array.from(new Set(Array.from(graphNodes.values()).map(n => n.level))).map(level => (
            <circle
              key={level}
              cx={0}
              cy={0}
              r={RADIUS * (level + 1) / (Math.max(...Array.from(graphNodes.values()).map(n => n.level)) + 1)}
              fill="none"
              stroke="currentColor"
              strokeWidth="1"
              opacity="0.1"
              className="text-gray-400"
            />
          ))}
          
          {/* Draw dependencies */}
          {workflow.steps.map(step => 
            step.dependencies.map(depId => {
              const isOnCriticalPath = 
                workflow.criticalPath.includes(step.id) && 
                workflow.criticalPath.includes(depId);
              return drawDependencyLine(depId, step.id, isOnCriticalPath);
            })
          )}
          
          {/* Draw nodes */}
          {Array.from(graphNodes.values()).map((node, index) => {
            const isOnCriticalPath = workflow.criticalPath.includes(node.id);
            const hasParallelSteps = node.step.parallelSteps && node.step.parallelSteps.length > 0;
            const isHighlighted = hoveredNode === node.id || selectedNode === node.id;
            const constraint = constraints.find(c => c.affectedSteps.includes(node.id));
            
            return (
              <motion.g
                key={node.id}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: index * 0.05 }}
                transform={`translate(${node.x}, ${node.y})`}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                onClick={() => handleNodeClick(node)}
                className="cursor-pointer"
              >
                <circle
                  r={NODE_SIZE / 2}
                  className={cn(
                    "transition-all duration-200",
                    node.step.status === 'completed' ? "fill-green-500" :
                    node.step.status === 'active' ? "fill-blue-500" :
                    node.step.status === 'failed' ? "fill-red-500" :
                    "fill-gray-300 dark:fill-gray-600",
                    isHighlighted && "stroke-4"
                  )}
                  stroke={isOnCriticalPath ? '#f97316' : '#e5e7eb'}
                  strokeWidth={isHighlighted ? 4 : 2}
                  opacity={node.step.status === 'skipped' ? 0.5 : 1}
                />
                
                {/* Icon */}
                <foreignObject
                  x={-NODE_SIZE / 4}
                  y={-NODE_SIZE / 4}
                  width={NODE_SIZE / 2}
                  height={NODE_SIZE / 2}
                  className="pointer-events-none"
                >
                  <div className="flex items-center justify-center h-full">
                    {node.step.isDecisionPoint ? (
                      <GitBranch className="w-6 h-6 text-white" />
                    ) : hasParallelSteps ? (
                      <Layers className="w-6 h-6 text-white" />
                    ) : (
                      <div className="w-6 h-6 rounded-full bg-white/20" />
                    )}
                  </div>
                </foreignObject>
                
                {/* Constraint indicator */}
                {constraint && (
                  <g transform={`translate(${NODE_SIZE / 3}, ${-NODE_SIZE / 3})`}>
                    <circle
                      r="10"
                      className={cn(
                        constraint.severity === 'high' ? "fill-red-500" :
                        constraint.severity === 'medium' ? "fill-yellow-500" :
                        "fill-gray-500"
                      )}
                    />
                    <text
                      textAnchor="middle"
                      dominantBaseline="middle"
                      className="text-white text-xs font-bold"
                    >
                      !
                    </text>
                  </g>
                )}
                
                {/* Label */}
                <text
                  y={NODE_SIZE / 2 + 20}
                  textAnchor="middle"
                  className="text-sm fill-current"
                  style={{ 
                    fontSize: isHighlighted ? '14px' : '12px',
                    fontWeight: isHighlighted ? 600 : 400
                  }}
                >
                  {node.step.name}
                </text>
                
                {/* Progress indicator for active nodes */}
                {node.step.status === 'active' && node.step.progress !== undefined && (
                  <g transform={`translate(0, ${NODE_SIZE / 2 + 35})`}>
                    <rect
                      x={-30}
                      y={-3}
                      width={60}
                      height={6}
                      rx={3}
                      className="fill-gray-200 dark:fill-gray-700"
                    />
                    <rect
                      x={-30}
                      y={-3}
                      width={60 * node.step.progress / 100}
                      height={6}
                      rx={3}
                      className="fill-blue-500"
                    />
                  </g>
                )}
              </motion.g>
            );
          })}
        </g>
      </svg>
      
      {/* Selected node details */}
      {selectedNode && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute bottom-4 left-4 bg-white dark:bg-gray-800 rounded-lg p-4 shadow-lg max-w-sm"
        >
          {(() => {
            const node = graphNodes.get(selectedNode);
            if (!node) return null;
            
            return (
              <>
                <h4 className="font-semibold mb-2">{node.step.name}</h4>
                {node.step.description && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    {node.step.description}
                  </p>
                )}
                <div className="text-xs space-y-1">
                  <p>Status: <span className="font-medium">{node.step.status}</span></p>
                  {node.step.agent && (
                    <p>Agent: <span className="font-medium">{node.step.agent.name}</span></p>
                  )}
                  {node.step.dependencies.length > 0 && (
                    <p>Dependencies: <span className="font-medium">{node.step.dependencies.length}</span></p>
                  )}
                </div>
              </>
            );
          })()}
        </motion.div>
      )}
    </div>
  );
};