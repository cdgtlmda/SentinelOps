'use client';

import * as React from 'react';
import { breakpoints, type Breakpoint } from '@/lib/design-system';

interface ResponsiveState {
  /**
   * Current window dimensions
   */
  dimensions: {
    width: number;
    height: number;
  };
  /**
   * Current breakpoint based on window width
   */
  currentBreakpoint: Breakpoint;
  /**
   * Whether the device supports touch
   */
  isTouch: boolean;
  /**
   * Whether keyboard navigation is being used
   */
  isKeyboardNav: boolean;
  /**
   * Check if current viewport is at or above a specific breakpoint
   */
  isAtLeast: (breakpoint: Breakpoint) => boolean;
  /**
   * Check if current viewport is below a specific breakpoint
   */
  isBelow: (breakpoint: Breakpoint) => boolean;
}

/**
 * Hook for responsive design utilities
 */
export function useResponsive(): ResponsiveState {
  const [dimensions, setDimensions] = React.useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
    height: typeof window !== 'undefined' ? window.innerHeight : 0
  });
  
  const [isTouch, setIsTouch] = React.useState(false);
  const [isKeyboardNav, setIsKeyboardNav] = React.useState(false);

  // Calculate current breakpoint
  const currentBreakpoint = React.useMemo((): Breakpoint => {
    const width = dimensions.width;
    const breakpointEntries = Object.entries(breakpoints) as [Breakpoint, number][];
    
    // Find the largest breakpoint that is smaller than or equal to current width
    let current: Breakpoint = 'xs';
    
    for (const [name, minWidth] of breakpointEntries) {
      if (width >= minWidth) {
        current = name;
      }
    }
    
    return current;
  }, [dimensions.width]);

  // Handle window resize
  React.useEffect(() => {
    const handleResize = () => {
      setDimensions({
        width: window.innerWidth,
        height: window.innerHeight
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Detect touch support
  React.useEffect(() => {
    const checkTouch = () => {
      setIsTouch(
        'ontouchstart' in window ||
        navigator.maxTouchPoints > 0 ||
        window.matchMedia('(hover: none) and (pointer: coarse)').matches
      );
    };

    checkTouch();
    
    // Check on media query change
    const mediaQuery = window.matchMedia('(hover: none) and (pointer: coarse)');
    const handleChange = () => checkTouch();
    
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, []);

  // Detect keyboard navigation
  React.useEffect(() => {
    let mouseTimeout: NodeJS.Timeout;
    
    const handleMouseMove = () => {
      setIsKeyboardNav(false);
      document.body.classList.remove('keyboard-nav');
      
      clearTimeout(mouseTimeout);
      mouseTimeout = setTimeout(() => {
        document.body.classList.add('mouse-nav');
      }, 100);
    };
    
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Tab' || e.key === 'Enter' || e.key === ' ' || e.key === 'Escape') {
        setIsKeyboardNav(true);
        document.body.classList.add('keyboard-nav');
        document.body.classList.remove('mouse-nav');
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('keydown', handleKeyDown);
    
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('keydown', handleKeyDown);
      clearTimeout(mouseTimeout);
    };
  }, []);

  // Utility functions
  const isAtLeast = React.useCallback((breakpoint: Breakpoint): boolean => {
    return dimensions.width >= breakpoints[breakpoint];
  }, [dimensions.width]);

  const isBelow = React.useCallback((breakpoint: Breakpoint): boolean => {
    return dimensions.width < breakpoints[breakpoint];
  }, [dimensions.width]);

  return {
    dimensions,
    currentBreakpoint,
    isTouch,
    isKeyboardNav,
    isAtLeast,
    isBelow
  };
}