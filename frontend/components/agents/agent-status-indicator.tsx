'use client';

import { memo } from 'react';
import { cn } from '@/lib/utils';
import { AgentStatus } from '@/types/agent';
import {
  CheckCircle2,
  AlertCircle,
  Loader2,
  Clock,
  Circle,
} from 'lucide-react';

interface AgentStatusIndicatorProps {
  status: AgentStatus;
  size?: 'small' | 'medium' | 'large';
  showLabel?: boolean;
  className?: string;
}

const statusConfig: Record<
  AgentStatus,
  {
    icon: React.ComponentType<{ className?: string }>;
    color: string;
    bgColor: string;
    label: string;
    animate?: boolean;
  }
> = {
  idle: {
    icon: Circle,
    color: 'text-gray-500',
    bgColor: 'bg-gray-100',
    label: 'Idle',
  },
  processing: {
    icon: Loader2,
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
    label: 'Processing',
    animate: true,
  },
  waiting: {
    icon: Clock,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-100',
    label: 'Waiting',
  },
  error: {
    icon: AlertCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-100',
    label: 'Error',
  },
  completed: {
    icon: CheckCircle2,
    color: 'text-green-600',
    bgColor: 'bg-green-100',
    label: 'Completed',
  },
};

const sizeClasses = {
  small: {
    container: 'h-6 px-2',
    icon: 'h-3 w-3',
    text: 'text-xs',
    gap: 'gap-1',
  },
  medium: {
    container: 'h-8 px-3',
    icon: 'h-4 w-4',
    text: 'text-sm',
    gap: 'gap-1.5',
  },
  large: {
    container: 'h-10 px-4',
    icon: 'h-5 w-5',
    text: 'text-base',
    gap: 'gap-2',
  },
};

export const AgentStatusIndicator = memo(function AgentStatusIndicator({
  status,
  size = 'medium',
  showLabel = true,
  className,
}: AgentStatusIndicatorProps) {
  const config = statusConfig[status];
  const sizeClass = sizeClasses[size];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        'inline-flex items-center rounded-full font-medium transition-all duration-200',
        sizeClass.container,
        sizeClass.gap,
        config.bgColor,
        config.color,
        className
      )}
      role="status"
      aria-label={`Agent status: ${config.label}`}
    >
      <Icon
        className={cn(
          sizeClass.icon,
          config.animate && 'animate-spin'
        )}
        aria-hidden="true"
      />
      {showLabel && (
        <span className={sizeClass.text}>{config.label}</span>
      )}
    </div>
  );
});

export const AgentStatusDot = memo(function AgentStatusDot({
  status,
  size = 'medium',
  className,
}: Omit<AgentStatusIndicatorProps, 'showLabel'>) {
  const config = statusConfig[status];
  const sizeMap = {
    small: 'h-2 w-2',
    medium: 'h-3 w-3',
    large: 'h-4 w-4',
  };

  return (
    <div className="relative inline-flex">
      <div
        className={cn(
          'rounded-full',
          sizeMap[size],
          config.bgColor.replace('bg-', 'bg-opacity-20 bg-'),
          className
        )}
        role="status"
        aria-label={`Agent status: ${config.label}`}
      >
        <div
          className={cn(
            'absolute inset-0 rounded-full',
            config.bgColor,
            config.animate && 'animate-pulse'
          )}
        />
        {status === 'processing' && (
          <div
            className={cn(
              'absolute inset-0 rounded-full animate-ping',
              config.bgColor,
              'opacity-75'
            )}
          />
        )}
      </div>
    </div>
  );
});