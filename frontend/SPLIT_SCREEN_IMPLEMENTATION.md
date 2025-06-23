# Split-Screen Architecture Implementation

## Overview
A responsive two-panel split-screen layout has been implemented for the SentinelOps dashboard, featuring a chat interface on the left and an activity viewer on the right.

## Components Created

### 1. `/components/layout/split-screen.tsx`
- Main split-screen container component
- Features:
  - Resizable panels with drag handle
  - Collapsible panels with smooth animations
  - Responsive behavior (stacks vertically on mobile)
  - Keyboard shortcuts support
  - Min/max width constraints for panels

### 2. `/components/layout/panel-header.tsx`
- Header component for each panel
- Features:
  - Panel title display
  - Collapse/expand toggle button
  - Action buttons slot for custom actions
  - Keyboard shortcut tooltips

### 3. `/hooks/use-panel-state.ts`
- Custom hook for managing panel state
- Features:
  - Panel size management
  - Collapsed state tracking
  - LocalStorage persistence
  - Mobile panel switching

## Usage

The split-screen is implemented in the dashboard page:

```tsx
<SplitScreen
  leftPanel={{
    id: 'chat',
    title: 'Chat',
    content: <ChatInterface />,
    minWidth: 30,
    maxWidth: 70
  }}
  rightPanel={{
    id: 'activity',
    title: 'Activity',
    content: <ActivityViewer />,
    actions: loadDemoButton,
    minWidth: 30,
    maxWidth: 70
  }}
  defaultLeftWidth={50}
  className="h-full"
/>
```

## Keyboard Shortcuts

- **Cmd/Ctrl + [** - Toggle left panel
- **Cmd/Ctrl + ]** - Toggle right panel
- **Cmd/Ctrl + \\** - Reset layout to default

## Responsive Behavior

- **Desktop (≥768px)**: Side-by-side panels with resizable divider
- **Mobile (<768px)**: Stacked panels with tab navigation

## CSS Enhancements

Added custom CSS classes in `globals.css`:
- Smooth panel transitions
- Resize handle styling
- Collapse/expand animations
- Mobile tab styling

## State Persistence

Panel states are automatically saved to localStorage:
- Panel widths
- Collapsed states
- Active panel (mobile)

The state persists across browser sessions for better user experience.