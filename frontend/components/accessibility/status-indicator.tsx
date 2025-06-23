import React from 'react';
import { cn } from '@/lib/utils';
import { 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Info, 
  Clock,
  Activity,
  Pause,
  Play,
  Loader2
} from 'lucide-react';
import { LucideIcon } from 'lucide-react';

export type StatusType = 'success' | 'error' | 'warning' | 'info' | 'pending' | 'active' | 'paused' | 'loading';

interface StatusIndicatorProps {
  status: StatusType;
  label?: string;
  showIcon?: boolean;
  showText?: boolean;
  showPattern?: boolean;
  size?: 'sm' | 'md' | 'lg';
  animate?: boolean;
  className?: string;
  customIcon?: LucideIcon;
  customColor?: string;
  'aria-label'?: string;
}

const statusConfig: Record<StatusType, {
  icon: LucideIcon;
  color: string;
  bgColor: string;
  pattern: string;
  label: string;
}> = {
  success: {
    icon: CheckCircle,
    color: 'text-green-700',
    bgColor: 'bg-green-100',
    pattern: 'pattern-diagonal-stripes',
    label: 'Success',
  },
  error: {
    icon: XCircle,
    color: 'text-red-700',
    bgColor: 'bg-red-100',
    pattern: 'pattern-cross',
    label: 'Error',
  },
  warning: {
    icon: AlertCircle,
    color: 'text-yellow-700',
    bgColor: 'bg-yellow-100',
    pattern: 'pattern-dots',
    label: 'Warning',
  },
  info: {
    icon: Info,
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
    pattern: 'pattern-vertical-stripes',
    label: 'Information',
  },
  pending: {
    icon: Clock,
    color: 'text-gray-700',
    bgColor: 'bg-gray-100',
    pattern: 'pattern-horizontal-stripes',
    label: 'Pending',
  },
  active: {
    icon: Activity,
    color: 'text-green-700',
    bgColor: 'bg-green-100',
    pattern: 'pattern-pulse',
    label: 'Active',
  },
  paused: {
    icon: Pause,
    color: 'text-orange-700',
    bgColor: 'bg-orange-100',
    pattern: 'pattern-diagonal-stripes-reverse',
    label: 'Paused',
  },
  loading: {
    icon: Loader2,
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
    pattern: 'pattern-spin',
    label: 'Loading',
  },
};

const sizeConfig = {
  sm: {
    container: 'px-2 py-1 text-xs gap-1',
    icon: 'h-3 w-3',
    dot: 'h-2 w-2',
  },
  md: {
    container: 'px-3 py-1.5 text-sm gap-1.5',
    icon: 'h-4 w-4',
    dot: 'h-2.5 w-2.5',
  },
  lg: {
    container: 'px-4 py-2 text-base gap-2',
    icon: 'h-5 w-5',
    dot: 'h-3 w-3',
  },
};

export function StatusIndicator({
  status,
  label,
  showIcon = true,
  showText = true,
  showPattern = false,
  size = 'md',
  animate = true,
  className,
  customIcon,
  customColor,
  'aria-label': ariaLabel,
}: StatusIndicatorProps) {
  const config = statusConfig[status];
  const Icon = customIcon || config.icon;
  const displayLabel = label || config.label;
  const sizes = sizeConfig[size];

  const containerClasses = cn(
    'inline-flex items-center rounded-full font-medium',
    sizes.container,
    config.bgColor,
    config.color,
    {
      [config.pattern]: showPattern,
      'animate-pulse': animate && status === 'loading',
    },
    className
  );

  const iconClasses = cn(
    sizes.icon,
    {
      'animate-spin': status === 'loading',
      'animate-pulse': animate && status === 'active',
    }
  );

  return (
    <div
      className={containerClasses}
      role="status"
      aria-label={ariaLabel || displayLabel}
      aria-live={status === 'loading' || status === 'active' ? 'polite' : 'off'}
    >
      {showIcon && <Icon className={iconClasses} aria-hidden="true" />}
      {showText && <span>{displayLabel}</span>}
      {!showIcon && !showText && (
        <>
          <span className="sr-only">{displayLabel}</span>
          <span className={cn(sizes.dot, 'rounded-full', config.bgColor)} />
        </>
      )}
    </div>
  );
}

// Multi-status indicator for showing multiple statuses at once
interface MultiStatusIndicatorProps {
  statuses: Array<{
    status: StatusType;
    label?: string;
    count?: number;
  }>;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function MultiStatusIndicator({
  statuses,
  size = 'md',
  className,
}: MultiStatusIndicatorProps) {
  return (
    <div className={cn('flex flex-wrap gap-2', className)} role="group" aria-label="Status indicators">
      {statuses.map((item, index) => (
        <StatusIndicator
          key={`${item.status}-${index}`}
          status={item.status}
          label={item.count ? `${item.label || statusConfig[item.status].label} (${item.count})` : item.label}
          size={size}
        />
      ))}
    </div>
  );
}

// Status dot for minimal space usage
interface StatusDotProps {
  status: StatusType;
  size?: 'sm' | 'md' | 'lg';
  animate?: boolean;
  showTooltip?: boolean;
  className?: string;
}

export function StatusDot({
  status,
  size = 'md',
  animate = true,
  className,
}: StatusDotProps) {
  const config = statusConfig[status];
  const sizes = {
    sm: 'h-2 w-2',
    md: 'h-3 w-3',
    lg: 'h-4 w-4',
  };

  return (
    <div
      className={cn(
        'rounded-full',
        sizes[size],
        config.bgColor,
        'border-2',
        config.color.replace('text-', 'border-'),
        {
          'animate-pulse': animate && (status === 'active' || status === 'loading'),
        },
        className
      )}
      role="status"
      aria-label={config.label}
    >
      <span className="sr-only">{config.label}</span>
    </div>
  );
}

// CSS for patterns (add to globals.css)
export const patternStyles = `
  .pattern-diagonal-stripes {
    background-image: repeating-linear-gradient(
      45deg,
      transparent,
      transparent 5px,
      rgba(0, 0, 0, 0.1) 5px,
      rgba(0, 0, 0, 0.1) 10px
    );
  }

  .pattern-diagonal-stripes-reverse {
    background-image: repeating-linear-gradient(
      -45deg,
      transparent,
      transparent 5px,
      rgba(0, 0, 0, 0.1) 5px,
      rgba(0, 0, 0, 0.1) 10px
    );
  }

  .pattern-dots {
    background-image: radial-gradient(circle, rgba(0, 0, 0, 0.1) 1px, transparent 1px);
    background-size: 10px 10px;
  }

  .pattern-horizontal-stripes {
    background-image: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 5px,
      rgba(0, 0, 0, 0.1) 5px,
      rgba(0, 0, 0, 0.1) 10px
    );
  }

  .pattern-vertical-stripes {
    background-image: repeating-linear-gradient(
      90deg,
      transparent,
      transparent 5px,
      rgba(0, 0, 0, 0.1) 5px,
      rgba(0, 0, 0, 0.1) 10px
    );
  }

  .pattern-cross {
    background-image: 
      repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(0, 0, 0, 0.1) 10px, rgba(0, 0, 0, 0.1) 11px),
      repeating-linear-gradient(-45deg, transparent, transparent 10px, rgba(0, 0, 0, 0.1) 10px, rgba(0, 0, 0, 0.1) 11px);
  }

  .pattern-pulse {
    position: relative;
    overflow: hidden;
  }

  .pattern-pulse::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    animation: pulse-wave 2s infinite;
  }

  @keyframes pulse-wave {
    0% { left: -100%; }
    100% { left: 100%; }
  }
`;