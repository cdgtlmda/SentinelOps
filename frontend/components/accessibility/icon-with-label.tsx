import React from 'react';
import { cn } from '@/lib/utils';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { LucideIcon } from 'lucide-react';

export type LabelPosition = 'right' | 'left' | 'below' | 'above' | 'tooltip' | 'hidden';

interface IconWithLabelProps {
  icon: LucideIcon;
  label: string;
  position?: LabelPosition;
  iconSize?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  iconClassName?: string;
  labelClassName?: string;
  showLabel?: boolean;
  'aria-label'?: string;
}

const iconSizes = {
  sm: 'h-4 w-4',
  md: 'h-5 w-5',
  lg: 'h-6 w-6',
  xl: 'h-8 w-8',
};

const labelSizes = {
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-base',
  xl: 'text-lg',
};

export function IconWithLabel({
  icon: Icon,
  label,
  position = 'right',
  iconSize = 'md',
  className,
  iconClassName,
  labelClassName,
  showLabel = true,
  'aria-label': ariaLabel,
}: IconWithLabelProps) {
  const iconElement = (
    <Icon 
      className={cn(iconSizes[iconSize], iconClassName)}
      aria-hidden={showLabel && position !== 'hidden'}
    />
  );

  const labelElement = showLabel && position !== 'tooltip' && position !== 'hidden' && (
    <span className={cn(labelSizes[iconSize], labelClassName)}>
      {label}
    </span>
  );

  const containerClasses = cn(
    'inline-flex items-center gap-2',
    {
      'flex-row': position === 'right',
      'flex-row-reverse': position === 'left',
      'flex-col': position === 'below',
      'flex-col-reverse': position === 'above',
    },
    className
  );

  // Screen reader only label
  const srOnlyLabel = position === 'hidden' && (
    <span className="sr-only">{label}</span>
  );

  // Tooltip variant
  if (position === 'tooltip') {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              className={cn('inline-flex items-center justify-center', className)}
              aria-label={ariaLabel || label}
            >
              {iconElement}
            </button>
          </TooltipTrigger>
          <TooltipContent>
            <p>{label}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return (
    <div 
      className={containerClasses}
      aria-label={!showLabel ? (ariaLabel || label) : undefined}
    >
      {iconElement}
      {labelElement}
      {srOnlyLabel}
    </div>
  );
}

// Compound component for icon groups
interface IconGroupProps {
  children: React.ReactNode;
  className?: string;
  orientation?: 'horizontal' | 'vertical';
  spacing?: 'tight' | 'normal' | 'loose';
}

export function IconGroup({
  children,
  className,
  orientation = 'horizontal',
  spacing = 'normal',
}: IconGroupProps) {
  const spacingClasses = {
    tight: orientation === 'horizontal' ? 'gap-2' : 'gap-1',
    normal: orientation === 'horizontal' ? 'gap-4' : 'gap-2',
    loose: orientation === 'horizontal' ? 'gap-6' : 'gap-4',
  };

  return (
    <div
      className={cn(
        'flex',
        orientation === 'horizontal' ? 'flex-row' : 'flex-col',
        spacingClasses[spacing],
        className
      )}
      role="group"
    >
      {children}
    </div>
  );
}

// Preset icon components for common actions
export const CommonIcons = {
  Save: (props: Omit<IconWithLabelProps, 'icon' | 'label'>) => (
    <IconWithLabel icon={require('lucide-react').Save} label="Save" {...props} />
  ),
  Delete: (props: Omit<IconWithLabelProps, 'icon' | 'label'>) => (
    <IconWithLabel icon={require('lucide-react').Trash2} label="Delete" {...props} />
  ),
  Edit: (props: Omit<IconWithLabelProps, 'icon' | 'label'>) => (
    <IconWithLabel icon={require('lucide-react').Edit} label="Edit" {...props} />
  ),
  Settings: (props: Omit<IconWithLabelProps, 'icon' | 'label'>) => (
    <IconWithLabel icon={require('lucide-react').Settings} label="Settings" {...props} />
  ),
  Search: (props: Omit<IconWithLabelProps, 'icon' | 'label'>) => (
    <IconWithLabel icon={require('lucide-react').Search} label="Search" {...props} />
  ),
  Filter: (props: Omit<IconWithLabelProps, 'icon' | 'label'>) => (
    <IconWithLabel icon={require('lucide-react').Filter} label="Filter" {...props} />
  ),
  Download: (props: Omit<IconWithLabelProps, 'icon' | 'label'>) => (
    <IconWithLabel icon={require('lucide-react').Download} label="Download" {...props} />
  ),
  Upload: (props: Omit<IconWithLabelProps, 'icon' | 'label'>) => (
    <IconWithLabel icon={require('lucide-react').Upload} label="Upload" {...props} />
  ),
  Refresh: (props: Omit<IconWithLabelProps, 'icon' | 'label'>) => (
    <IconWithLabel icon={require('lucide-react').RefreshCw} label="Refresh" {...props} />
  ),
  Close: (props: Omit<IconWithLabelProps, 'icon' | 'label'>) => (
    <IconWithLabel icon={require('lucide-react').X} label="Close" {...props} />
  ),
};