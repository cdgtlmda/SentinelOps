'use client';

import React from 'react';
import { 
  ResponsiveContainer, 
  TouchTarget, 
  BreakpointIndicator 
} from '@/components/ui/responsive';
import { 
  SkipLink, 
  FocusTrap, 
  KeyboardShortcutsProvider, 
  useKeyboardShortcut 
} from '@/components/ui/keyboard-navigation';
import { useResponsive } from '@/hooks/use-responsive';

function DemoContent() {
  const { currentBreakpoint, isTouch, isKeyboardNav, dimensions, isAtLeast } = useResponsive();
  const [modalOpen, setModalOpen] = React.useState(false);
  const [count, setCount] = React.useState(0);

  // Register keyboard shortcuts
  useKeyboardShortcut('k', () => setModalOpen(true), {
    ctrl: true,
    description: 'Open modal'
  });

  useKeyboardShortcut('Escape', () => setModalOpen(false), {
    enabled: modalOpen,
    description: 'Close modal'
  });

  useKeyboardShortcut('+', () => setCount(c => c + 1), {
    description: 'Increment counter'
  });

  useKeyboardShortcut('-', () => setCount(c => c - 1), {
    description: 'Decrement counter'
  });

  return (
    <>
      <SkipLink />
      
      <ResponsiveContainer maxWidth="xl" className="py-8">
        <div className="space-y-8">
          {/* Header */}
          <header>
            <h1 className="text-3xl font-bold mb-4">Responsive Design System Demo</h1>
            <p className="text-muted-foreground">
              This page demonstrates the responsive design system components and utilities.
            </p>
          </header>

          {/* Current State Info */}
          <section className="bg-card p-6 rounded-lg border" id="main-content" tabIndex={-1}>
            <h2 className="text-xl font-semibold mb-4">Current Device State</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p><strong>Breakpoint:</strong> {currentBreakpoint}</p>
                <p><strong>Viewport:</strong> {dimensions.width}x{dimensions.height}</p>
              </div>
              <div>
                <p><strong>Touch Device:</strong> {isTouch ? 'Yes' : 'No'}</p>
                <p><strong>Keyboard Navigation:</strong> {isKeyboardNav ? 'Active' : 'Inactive'}</p>
              </div>
            </div>
          </section>

          {/* Touch Target Examples */}
          <section className="bg-card p-6 rounded-lg border">
            <h2 className="text-xl font-semibold mb-4">Touch Target Examples</h2>
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium mb-2">Minimum Size (44px)</h3>
                <TouchTarget size="minimum" className="bg-primary text-primary-foreground rounded">
                  <button className="px-3 py-1">Min Touch</button>
                </TouchTarget>
              </div>
              
              <div>
                <h3 className="text-sm font-medium mb-2">Recommended Size (48px)</h3>
                <TouchTarget size="recommended" className="bg-secondary text-secondary-foreground rounded">
                  <button className="px-4 py-2">Recommended</button>
                </TouchTarget>
              </div>
              
              <div>
                <h3 className="text-sm font-medium mb-2">Comfortable Size (56px)</h3>
                <TouchTarget size="comfortable" className="bg-accent text-accent-foreground rounded">
                  <button className="px-5 py-3">Comfortable</button>
                </TouchTarget>
              </div>
            </div>
          </section>

          {/* Responsive Container Examples */}
          <section className="space-y-4">
            <h2 className="text-xl font-semibold mb-4">Responsive Container Sizes</h2>
            
            {(['sm', 'md', 'lg', 'xl', '2xl'] as const).map(size => (
              <ResponsiveContainer 
                key={size}
                maxWidth={size} 
                className="bg-muted p-4 rounded"
              >
                <p className="text-center">Container: {size}</p>
              </ResponsiveContainer>
            ))}
          </section>

          {/* Keyboard Shortcuts Demo */}
          <section className="bg-card p-6 rounded-lg border">
            <h2 className="text-xl font-semibold mb-4">Keyboard Shortcuts</h2>
            <p className="mb-4">Counter: <strong>{count}</strong></p>
            <ul className="space-y-2 text-sm">
              <li><kbd>Ctrl+K</kbd> - Open modal</li>
              <li><kbd>+</kbd> - Increment counter</li>
              <li><kbd>-</kbd> - Decrement counter</li>
              <li><kbd>Tab</kbd> - Navigate between focusable elements</li>
            </ul>
            <button
              onClick={() => setModalOpen(true)}
              className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded hover:opacity-90"
            >
              Open Modal (Ctrl+K)
            </button>
          </section>

          {/* Responsive Grid Example */}
          <section>
            <h2 className="text-xl font-semibold mb-4">Responsive Grid</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="bg-card p-4 rounded-lg border text-center">
                  <p>Item {i + 1}</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {isAtLeast('xl') && '4 cols'}
                    {!isAtLeast('xl') && isAtLeast('lg') && '3 cols'}
                    {!isAtLeast('lg') && isAtLeast('sm') && '2 cols'}
                    {!isAtLeast('sm') && '1 col'}
                  </p>
                </div>
              ))}
            </div>
          </section>
        </div>
      </ResponsiveContainer>

      {/* Modal with Focus Trap */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4" style={{ zIndex: 1400 }}>
          <FocusTrap active={modalOpen} onEscape={() => setModalOpen(false)}>
            <div className="bg-background p-6 rounded-lg max-w-md w-full">
              <h2 className="text-xl font-semibold mb-4">Modal with Focus Trap</h2>
              <p className="mb-4">
                Tab navigation is trapped within this modal. Press Escape to close.
              </p>
              <div className="space-y-2">
                <input
                  type="text"
                  placeholder="First input"
                  className="w-full px-3 py-2 border rounded"
                />
                <input
                  type="text"
                  placeholder="Second input"
                  className="w-full px-3 py-2 border rounded"
                />
              </div>
              <div className="mt-4 flex gap-2">
                <button
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 bg-secondary text-secondary-foreground rounded"
                >
                  Cancel
                </button>
                <button
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded"
                >
                  Confirm
                </button>
              </div>
            </div>
          </FocusTrap>
        </div>
      )}

      {/* Breakpoint Indicator (dev only) */}
      <BreakpointIndicator />
    </>
  );
}

export default function ResponsiveDemoPage() {
  return (
    <KeyboardShortcutsProvider>
      <DemoContent />
    </KeyboardShortcutsProvider>
  );
}