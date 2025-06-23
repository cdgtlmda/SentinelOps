'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { touchTargets, type TouchTarget as TouchTargetSize } from '@/lib/design-system';

interface TouchTargetProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * The minimum size of the touch target
   * @default 'minimum'
   */
  size?: TouchTargetSize;
  /**
   * Whether to apply the touch target size as minimum dimensions
   * @default true
   */
  asMinimum?: boolean;
  /**
   * The element to render as
   * @default 'div'
   */
  as?: React.ElementType;
  /**
   * Whether to center the content within the touch target
   * @default true
   */
  center?: boolean;
}

/**
 * TouchTarget component that ensures interactive elements meet WCAG touch target guidelines
 */
export const TouchTarget = React.forwardRef<
  HTMLDivElement,
  TouchTargetProps
>(({
  className,
  size = 'minimum',
  asMinimum = true,
  as: Component = 'div',
  center = true,
  style,
  ...props
}, ref) => {
  const touchTargetStyles = React.useMemo(() => {
    const targetSize = touchTargets[size];
    const styles: React.CSSProperties = {
      ...style
    };
    
    if (asMinimum) {
      styles.minWidth = targetSize;
      styles.minHeight = targetSize;
    } else {
      styles.width = targetSize;
      styles.height = targetSize;
    }
    
    return styles;
  }, [size, asMinimum, style]);

  return (
    <Component
      ref={ref}
      className={cn(
        'relative',
        center && 'flex items-center justify-center',
        className
      )}
      style={touchTargetStyles}
      {...props}
    />
  );
});

TouchTarget.displayName = 'TouchTarget';