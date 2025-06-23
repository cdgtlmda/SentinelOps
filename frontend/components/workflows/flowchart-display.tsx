'use client';

import React, { useRef, useState, useEffect } from 'react';
import { Workflow, WorkflowStep, WorkflowConnection } from '@/types/workflow';
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  Move,
  GitBranch,
  CheckCircle2,
  Circle,
  XCircle,
  Loader2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

interface FlowchartDisplayProps {
  workflow: Workflow;
  onNodeClick?: (step: WorkflowStep) => void;
}

interface NodePosition {
  x: number;
  y: number;
}

const NODE_WIDTH = 200;
const NODE_HEIGHT = 100;
const NODE_SPACING_X = 280;
const NODE_SPACING_Y = 150;

const getStatusColor = (status: WorkflowStep['status']) => {
  switch (status) {
    case 'completed':
      return 'border-green-500 bg-green-50 dark:bg-green-950';
    case 'active':
      return 'border-blue-500 bg-blue-50 dark:bg-blue-950';
    case 'failed':
      return 'border-red-500 bg-red-50 dark:bg-red-950';
    case 'skipped':
      return 'border-gray-400 bg-gray-50 dark:bg-gray-800 opacity-50';
    default:
      return 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900';
  }
};

const getStatusIcon = (status: WorkflowStep['status']) => {
  const className = "w-5 h-5";
  switch (status) {
    case 'completed':
      return <CheckCircle2 className={cn(className, "text-green-500")} />;
    case 'active':
      return <Loader2 className={cn(className, "text-blue-500 animate-spin")} />;
    case 'failed':
      return <XCircle className={cn(className, "text-red-500")} />;
    default:
      return <Circle className={cn(className, "text-gray-400")} />;
  }
};

export const FlowchartDisplay: React.FC<FlowchartDisplayProps> = ({ 
  workflow, 
  onNodeClick 
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [nodePositions, setNodePositions] = useState<Map<string, NodePosition>>(new Map());

  // Calculate node positions
  useEffect(() => {
    const positions = new Map<string, NodePosition>();
    const visited = new Set<string>();
    const levels = new Map<string, number>();
    
    // Find root nodes (no dependencies)
    const rootNodes = workflow.steps.filter(step => 
      step.dependencies.length === 0
    );
    
    // BFS to assign levels
    const queue: { step: WorkflowStep; level: number }[] = 
      rootNodes.map(step => ({ step, level: 0 }));
    
    while (queue.length > 0) {
      const { step, level } = queue.shift()!;
      
      if (visited.has(step.id)) continue;
      visited.add(step.id);
      levels.set(step.id, level);
      
      // Find dependent steps
      const dependents = workflow.steps.filter(s => 
        s.dependencies.includes(step.id)
      );
      
      dependents.forEach(dep => {
        queue.push({ step: dep, level: level + 1 });
      });
    }
    
    // Group steps by level
    const levelGroups = new Map<number, WorkflowStep[]>();
    workflow.steps.forEach(step => {
      const level = levels.get(step.id) || 0;
      if (!levelGroups.has(level)) {
        levelGroups.set(level, []);
      }
      levelGroups.get(level)!.push(step);
    });
    
    // Assign positions
    levelGroups.forEach((steps, level) => {
      const totalWidth = (steps.length - 1) * NODE_SPACING_X;
      const startX = -totalWidth / 2;
      
      steps.forEach((step, index) => {
        positions.set(step.id, {
          x: startX + index * NODE_SPACING_X,
          y: level * NODE_SPACING_Y
        });
      });
    });
    
    setNodePositions(positions);
  }, [workflow]);

  // Zoom handlers
  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.1, 2));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.1, 0.5));
  const handleFitToScreen = () => {
    if (containerRef.current && nodePositions.size > 0) {
      const container = containerRef.current.getBoundingClientRect();
      
      // Find bounds
      let minX = Infinity, maxX = -Infinity;
      let minY = Infinity, maxY = -Infinity;
      
      nodePositions.forEach(pos => {
        minX = Math.min(minX, pos.x - NODE_WIDTH / 2);
        maxX = Math.max(maxX, pos.x + NODE_WIDTH / 2);
        minY = Math.min(minY, pos.y - NODE_HEIGHT / 2);
        maxY = Math.max(maxY, pos.y + NODE_HEIGHT / 2);
      });
      
      const graphWidth = maxX - minX + 100;
      const graphHeight = maxY - minY + 100;
      
      const scaleX = container.width / graphWidth;
      const scaleY = container.height / graphHeight;
      const newZoom = Math.min(scaleX, scaleY, 1);
      
      setZoom(newZoom);
      setPan({ x: container.width / 2, y: 100 });
    }
  };

  // Pan handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) { // Left click
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Draw connection path
  const drawConnection = (connection: WorkflowConnection) => {
    const fromPos = nodePositions.get(connection.fromStepId);
    const toPos = nodePositions.get(connection.toStepId);
    
    if (!fromPos || !toPos) return null;
    
    const startX = fromPos.x;
    const startY = fromPos.y + NODE_HEIGHT / 2;
    const endX = toPos.x;
    const endY = toPos.y - NODE_HEIGHT / 2;
    
    // Create curved path
    const midY = (startY + endY) / 2;
    const path = `M ${startX} ${startY} C ${startX} ${midY}, ${endX} ${midY}, ${endX} ${endY}`;
    
    const color = connection.type === 'conditional' ? 'stroke-purple-400' :
                  connection.type === 'parallel' ? 'stroke-orange-400' :
                  'stroke-gray-400';
    
    return (
      <g key={connection.id}>
        <path
          d={path}
          fill="none"
          className={cn("stroke-2", color)}
          strokeDasharray={connection.type === 'conditional' ? '5,5' : undefined}
        />
        {/* Arrow */}
        <polygon
          points={`${endX},${endY - 5} ${endX - 5},${endY - 15} ${endX + 5},${endY - 15}`}
          className={cn("fill-current", color.replace('stroke-', 'text-'))}
        />
        {/* Label */}
        {connection.label && (
          <text
            x={(startX + endX) / 2}
            y={(startY + endY) / 2}
            textAnchor="middle"
            className="text-xs fill-gray-600 dark:fill-gray-400"
          >
            {connection.label}
          </text>
        )}
      </g>
    );
  };

  return (
    <div className="relative h-full w-full bg-gray-50 dark:bg-gray-900 rounded-lg overflow-hidden">
      {/* Controls */}
      <div className="absolute top-4 right-4 z-10 flex gap-2">
        <button
          onClick={handleZoomIn}
          className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-md transition-shadow"
          title="Zoom In"
        >
          <ZoomIn className="w-5 h-5" />
        </button>
        <button
          onClick={handleZoomOut}
          className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-md transition-shadow"
          title="Zoom Out"
        >
          <ZoomOut className="w-5 h-5" />
        </button>
        <button
          onClick={handleFitToScreen}
          className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-md transition-shadow"
          title="Fit to Screen"
        >
          <Maximize2 className="w-5 h-5" />
        </button>
      </div>
      
      {/* Canvas */}
      <div
        ref={containerRef}
        className="relative w-full h-full cursor-move"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <svg
          ref={svgRef}
          className="w-full h-full"
          style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
        >
          <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
            {/* Connections */}
            <g className="connections">
              {workflow.connections.map(drawConnection)}
            </g>
            
            {/* Nodes */}
            <g className="nodes">
              {workflow.steps.map((step, index) => {
                const pos = nodePositions.get(step.id);
                if (!pos) return null;
                
                const isOnCriticalPath = workflow.criticalPath.includes(step.id);
                
                return (
                  <motion.g
                    key={step.id}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.05 }}
                    transform={`translate(${pos.x - NODE_WIDTH / 2}, ${pos.y - NODE_HEIGHT / 2})`}
                    className="cursor-pointer"
                    onClick={(e) => {
                      e.stopPropagation();
                      onNodeClick?.(step);
                    }}
                  >
                    <rect
                      width={NODE_WIDTH}
                      height={NODE_HEIGHT}
                      rx={8}
                      className={cn(
                        "stroke-2 transition-all",
                        getStatusColor(step.status),
                        isOnCriticalPath && "stroke-orange-400 stroke-[3]"
                      )}
                    />
                    
                    {/* Node content */}
                    <foreignObject width={NODE_WIDTH} height={NODE_HEIGHT}>
                      <div className="p-3 h-full flex flex-col justify-between">
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            {getStatusIcon(step.status)}
                            {step.isDecisionPoint && (
                              <GitBranch className="w-4 h-4 text-purple-500" />
                            )}
                          </div>
                          <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 line-clamp-2">
                            {step.name}
                          </h4>
                        </div>
                        
                        {step.agent && (
                          <p className="text-xs text-gray-600 dark:text-gray-400">
                            {step.agent.name}
                          </p>
                        )}
                        
                        {step.status === 'active' && step.progress !== undefined && (
                          <div className="mt-2">
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1">
                              <div
                                className="bg-blue-500 h-1 rounded-full transition-all duration-500"
                                style={{ width: `${step.progress}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    </foreignObject>
                  </motion.g>
                );
              })}
            </g>
          </g>
        </svg>
        
        {/* Pan indicator */}
        {isDragging && (
          <div className="absolute bottom-4 left-4 flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <Move className="w-4 h-4" />
            <span>Dragging to pan</span>
          </div>
        )}
      </div>
    </div>
  );
};