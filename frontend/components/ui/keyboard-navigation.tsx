'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { zIndex } from '@/lib/design-system';

/**
 * SkipLink component for keyboard navigation
 * Provides quick access to main content for screen reader and keyboard users
 */
interface SkipLinkProps {
  /**
   * The ID of the element to skip to
   * @default 'main-content'
   */
  targetId?: string;
  /**
   * The text to display in the skip link
   * @default 'Skip to main content'
   */
  children?: React.ReactNode;
}

export const SkipLink: React.FC<SkipLinkProps> = ({
  targetId = 'main-content',
  children = 'Skip to main content'
}) => {
  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const target = document.getElementById(targetId);
    if (target) {
      target.focus();
      target.scrollIntoView();
    }
  };

  return (
    <a
      href={`#${targetId}`}
      onClick={handleClick}
      className={cn(
        'fixed top-4 left-4 transform -translate-y-full',
        'bg-background text-foreground px-4 py-2 rounded-md',
        'border border-border shadow-lg',
        'transition-transform duration-200',
        'focus:translate-y-0',
        'sr-only focus:not-sr-only'
      )}
      style={{ zIndex: zIndex.skipLink }}
    >
      {children}
    </a>
  );
};

/**
 * FocusTrap component that traps focus within a container
 * Useful for modals, dialogs, and other overlay components
 */
interface FocusTrapProps {
  /**
   * Whether the focus trap is active
   */
  active: boolean;
  /**
   * Whether to return focus to the trigger element on deactivation
   * @default true
   */
  returnFocus?: boolean;
  /**
   * Whether to focus the first element on activation
   * @default true
   */
  autoFocus?: boolean;
  /**
   * Callback when escape key is pressed
   */
  onEscape?: () => void;
  children: React.ReactNode;
}

export const FocusTrap: React.FC<FocusTrapProps> = ({
  active,
  returnFocus = true,
  autoFocus = true,
  onEscape,
  children
}) => {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const previousFocusRef = React.useRef<HTMLElement | null>(null);

  // Store the previously focused element
  React.useEffect(() => {
    if (active && returnFocus) {
      previousFocusRef.current = document.activeElement as HTMLElement;
    }
  }, [active, returnFocus]);

  // Focus first focusable element when activated
  React.useEffect(() => {
    if (active && autoFocus && containerRef.current) {
      const focusableElements = getFocusableElements(containerRef.current);
      if (focusableElements.length > 0) {
        focusableElements[0].focus();
      }
    }
  }, [active, autoFocus]);

  // Return focus when deactivated
  React.useEffect(() => {
    return () => {
      if (!active && returnFocus && previousFocusRef.current) {
        previousFocusRef.current.focus();
      }
    };
  }, [active, returnFocus]);

  // Handle keyboard navigation
  React.useEffect(() => {
    if (!active) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && onEscape) {
        onEscape();
        return;
      }

      if (e.key !== 'Tab' || !containerRef.current) return;

      const focusableElements = getFocusableElements(containerRef.current);
      if (focusableElements.length === 0) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];
      const activeElement = document.activeElement;

      if (e.shiftKey) {
        // Shift + Tab
        if (activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab
        if (activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [active, onEscape]);

  return (
    <div ref={containerRef} data-focus-trap-active={active}>
      {children}
    </div>
  );
};

/**
 * KeyboardShortcuts provider for managing global keyboard shortcuts
 */
interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  alt?: boolean;
  shift?: boolean;
  meta?: boolean;
  description: string;
  handler: () => void;
}

interface KeyboardShortcutsContextValue {
  shortcuts: KeyboardShortcut[];
  registerShortcut: (shortcut: KeyboardShortcut) => void;
  unregisterShortcut: (key: string) => void;
}

const KeyboardShortcutsContext = React.createContext<KeyboardShortcutsContextValue | null>(null);

export const useKeyboardShortcuts = () => {
  const context = React.useContext(KeyboardShortcutsContext);
  if (!context) {
    throw new Error('useKeyboardShortcuts must be used within KeyboardShortcutsProvider');
  }
  return context;
};

interface KeyboardShortcutsProviderProps {
  children: React.ReactNode;
}

export const KeyboardShortcutsProvider: React.FC<KeyboardShortcutsProviderProps> = ({
  children
}) => {
  const [shortcuts, setShortcuts] = React.useState<KeyboardShortcut[]>([]);

  const registerShortcut = React.useCallback((shortcut: KeyboardShortcut) => {
    setShortcuts(prev => [...prev.filter(s => s.key !== shortcut.key), shortcut]);
  }, []);

  const unregisterShortcut = React.useCallback((key: string) => {
    setShortcuts(prev => prev.filter(s => s.key !== key));
  }, []);

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const activeShortcut = shortcuts.find(shortcut => {
        const keyMatch = e.key.toLowerCase() === shortcut.key.toLowerCase();
        const ctrlMatch = !shortcut.ctrl || e.ctrlKey;
        const altMatch = !shortcut.alt || e.altKey;
        const shiftMatch = !shortcut.shift || e.shiftKey;
        const metaMatch = !shortcut.meta || e.metaKey;

        return keyMatch && ctrlMatch && altMatch && shiftMatch && metaMatch;
      });

      if (activeShortcut) {
        e.preventDefault();
        activeShortcut.handler();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);

  return (
    <KeyboardShortcutsContext.Provider
      value={{ shortcuts, registerShortcut, unregisterShortcut }}
    >
      {children}
    </KeyboardShortcutsContext.Provider>
  );
};

/**
 * Hook for registering a keyboard shortcut
 */
export const useKeyboardShortcut = (
  key: string,
  handler: () => void,
  options: {
    ctrl?: boolean;
    alt?: boolean;
    shift?: boolean;
    meta?: boolean;
    description?: string;
    enabled?: boolean;
  } = {}
) => {
  const { registerShortcut, unregisterShortcut } = useKeyboardShortcuts();
  const { enabled = true, description = '', ...modifiers } = options;

  React.useEffect(() => {
    if (!enabled) return;

    const shortcut: KeyboardShortcut = {
      key,
      handler,
      description,
      ...modifiers
    };

    registerShortcut(shortcut);
    return () => unregisterShortcut(key);
  }, [key, handler, enabled, description, modifiers, registerShortcut, unregisterShortcut]);
};

// Utility function to get focusable elements
function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const focusableSelectors = [
    'a[href]:not([disabled])',
    'button:not([disabled])',
    'textarea:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    '[tabindex]:not([tabindex="-1"])'
  ];

  const elements = container.querySelectorAll<HTMLElement>(focusableSelectors.join(','));
  return Array.from(elements).filter(el => {
    return el.offsetParent !== null && !el.hasAttribute('aria-hidden');
  });
}