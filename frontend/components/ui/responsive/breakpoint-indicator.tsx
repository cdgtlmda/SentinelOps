'use client';

import * as React from 'react';
import { breakpoints } from '@/lib/design-system';
import { useResponsive } from '@/hooks/use-responsive';
import { cn } from '@/lib/utils';

interface BreakpointIndicatorProps {
  /**
   * Whether to show the indicator
   * @default process.env.NODE_ENV === 'development'
   */
  show?: boolean;
  /**
   * Position of the indicator
   * @default 'bottom-left'
   */
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
}

/**
 * BreakpointIndicator component that displays the current breakpoint (development only)
 */
export const BreakpointIndicator: React.FC<BreakpointIndicatorProps> = ({
  show = process.env.NODE_ENV === 'development',
  position = 'bottom-left'
}) => {
  const { currentBreakpoint, isTouch, dimensions } = useResponsive();
  
  if (!show) {
    return null;
  }

  const positionClasses = {
    'top-left': 'top-4 left-4',
    'top-right': 'top-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-right': 'bottom-4 right-4'
  };

  return (
    <div
      className={cn(
        'fixed z-[9999] rounded-md bg-black/90 px-3 py-2 text-xs font-mono text-white shadow-lg',
        positionClasses[position]
      )}
    >
      <div className="space-y-1">
        <div>
          Breakpoint: <span className="font-bold text-green-400">{currentBreakpoint}</span>
        </div>
        <div>
          Width: <span className="text-blue-400">{dimensions.width}px</span>
        </div>
        <div>
          Height: <span className="text-blue-400">{dimensions.height}px</span>
        </div>
        <div>
          Touch: <span className={cn('font-bold', isTouch ? 'text-green-400' : 'text-red-400')}>
            {isTouch ? 'Yes' : 'No'}
          </span>
        </div>
        <div className="mt-2 pt-2 border-t border-white/20 space-y-0.5">
          {Object.entries(breakpoints).map(([name, width]) => (
            <div key={name} className="flex items-center justify-between">
              <span className={cn(
                dimensions.width >= width ? 'text-green-400' : 'text-gray-500'
              )}>
                {name}
              </span>
              <span className="text-gray-400 ml-2">≥{width}px</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};