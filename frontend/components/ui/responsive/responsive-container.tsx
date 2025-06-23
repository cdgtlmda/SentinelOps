'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { containers, type Container } from '@/lib/design-system';

interface ResponsiveContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * The maximum width of the container
   * @default 'xl'
   */
  maxWidth?: Container;
  /**
   * Whether to add horizontal padding
   * @default true
   */
  padding?: boolean;
  /**
   * Whether to center the container
   * @default true
   */
  center?: boolean;
  /**
   * The element to render as
   * @default 'div'
   */
  as?: React.ElementType;
}

/**
 * ResponsiveContainer component that provides consistent container sizing across breakpoints
 */
export const ResponsiveContainer = React.forwardRef<
  HTMLDivElement,
  ResponsiveContainerProps
>(({
  className,
  maxWidth = 'xl',
  padding = true,
  center = true,
  as: Component = 'div',
  ...props
}, ref) => {
  const containerStyles = React.useMemo(() => {
    const styles: React.CSSProperties = {};
    
    if (maxWidth !== 'fluid') {
      styles.maxWidth = containers[maxWidth];
    }
    
    return styles;
  }, [maxWidth]);

  return (
    <Component
      ref={ref}
      className={cn(
        'w-full',
        center && 'mx-auto',
        padding && 'px-4 sm:px-6 lg:px-8',
        className
      )}
      style={containerStyles}
      {...props}
    />
  );
});

ResponsiveContainer.displayName = 'ResponsiveContainer';