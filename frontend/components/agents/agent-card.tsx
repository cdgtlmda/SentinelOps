'use client';

import { memo, useState } from 'react';
import { cn } from '@/lib/utils';
import { Agent } from '@/types/agent';
import { AgentStatusIndicator } from './agent-status-indicator';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  MoreVertical,
  Play,
  Square,
  RotateCw,
  FileText,
  Activity,
  Cpu,
  MemoryStick,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface AgentCardProps {
  agent: Agent;
  onAction: (action: 'start' | 'stop' | 'restart' | 'viewLogs') => void;
  className?: string;
}

const agentTypeIcons = {
  security: '🛡️',
  monitoring: '👁️',
  remediation: '🔧',
  analysis: '📊',
  network: '🌐',
};

export const AgentCard = memo(function AgentCard({
  agent,
  onAction,
  className,
}: AgentCardProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const getProgressColor = (progress: number) => {
    if (progress < 30) return 'bg-blue-500';
    if (progress < 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const formatMetric = (value: number, suffix: string = '%') => {
    return `${Math.round(value)}${suffix}`;
  };

  return (
    <Card className={cn('relative overflow-hidden', className)}>
      {/* Background gradient based on status */}
      <div
        className={cn(
          'absolute inset-0 opacity-5',
          agent.status === 'error' && 'bg-gradient-to-br from-red-500 to-red-600',
          agent.status === 'processing' && 'bg-gradient-to-br from-blue-500 to-blue-600',
          agent.status === 'completed' && 'bg-gradient-to-br from-green-500 to-green-600'
        )}
      />

      <CardHeader className="relative">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl" role="img" aria-label={agent.type}>
              {agentTypeIcons[agent.type]}
            </span>
            <div>
              <CardTitle className="text-lg">{agent.name}</CardTitle>
              <CardDescription className="capitalize">
                {agent.type} Agent
              </CardDescription>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <AgentStatusIndicator status={agent.status} size="small" />
            
            <DropdownMenu open={isMenuOpen} onOpenChange={setIsMenuOpen}>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  aria-label="Agent actions"
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {agent.status === 'idle' && (
                  <DropdownMenuItem onClick={() => onAction('start')}>
                    <Play className="mr-2 h-4 w-4" />
                    Start Agent
                  </DropdownMenuItem>
                )}
                {(agent.status === 'processing' || agent.status === 'waiting') && (
                  <DropdownMenuItem onClick={() => onAction('stop')}>
                    <Square className="mr-2 h-4 w-4" />
                    Stop Agent
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem onClick={() => onAction('restart')}>
                  <RotateCw className="mr-2 h-4 w-4" />
                  Restart Agent
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => onAction('viewLogs')}>
                  <FileText className="mr-2 h-4 w-4" />
                  View Logs
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>

      <CardContent className="relative space-y-4">
        {/* Current Task */}
        {agent.currentTask && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">Current Task</span>
              <span className="text-muted-foreground">
                {formatMetric(agent.currentTask.progress)}
              </span>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground line-clamp-2">
                {agent.currentTask.description}
              </p>
              <div className="relative h-2 w-full overflow-hidden rounded-full bg-secondary">
                <div
                  className={cn(
                    'h-full transition-all duration-500',
                    getProgressColor(agent.currentTask.progress)
                  )}
                  style={{ width: `${agent.currentTask.progress}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Error Details */}
        {agent.error && (
          <div className="rounded-md bg-red-50 p-3 text-sm">
            <p className="font-medium text-red-800">Error</p>
            <p className="mt-1 text-red-700">{agent.error.message}</p>
            {agent.error.code && (
              <p className="mt-1 text-xs text-red-600">Code: {agent.error.code}</p>
            )}
          </div>
        )}

        {/* Metrics */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-muted-foreground" />
                  <span>{formatMetric(agent.metrics.cpuUsage)}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>CPU Usage</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-2">
                  <MemoryStick className="h-4 w-4 text-muted-foreground" />
                  <span>{formatMetric(agent.metrics.memoryUsage)}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>Memory Usage</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        {/* Last Action */}
        <div className="flex items-center justify-between border-t pt-3 text-xs text-muted-foreground">
          <span>Last action</span>
          <span>{formatDistanceToNow(agent.lastActionTimestamp, { addSuffix: true })}</span>
        </div>

        {/* Performance Stats */}
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-1">
            <Activity className="h-3 w-3" />
            <span>{agent.metrics.tasksCompleted} completed</span>
          </div>
          {agent.metrics.tasksFailed > 0 && (
            <span className="text-red-600">{agent.metrics.tasksFailed} failed</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
});