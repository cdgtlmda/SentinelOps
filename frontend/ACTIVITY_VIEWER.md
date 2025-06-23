# Activity Viewer Implementation

## Overview

The Activity Viewer provides a comprehensive real-time monitoring interface for SentinelOps. It displays agent status, workflow visualizations, action logs, and resource usage in an organized, responsive layout.

## Components Structure

### 1. **ActivityViewer** (`components/activity/activity-viewer.tsx`)
Main container component that orchestrates all activity views.

**Features:**
- Tab-based navigation on desktop
- Accordion layout on mobile
- Real-time data updates with configurable refresh intervals
- Five different views: Overview, Agents, Workflows, Logs, Resources

**Usage:**
```tsx
import { ActivityViewer } from '@/components/activity'

<ActivityViewer />
```

### 2. **AgentStatus** (`components/activity/agent-status.tsx`)
Displays real-time status of all agents in the system.

**Features:**
- Agent cards with status indicators
- Current task display
- Task completion statistics
- Error count tracking
- Last action timestamps
- Visual status indicators (idle, processing, waiting, error, completed)

### 3. **WorkflowVisualizer** (`components/activity/workflow-visualizer.tsx`)
Shows workflow execution with timeline visualization.

**Features:**
- Timeline view of workflow steps
- Progress bars for each workflow
- Step-by-step execution status
- Duration tracking
- Dependency visualization
- Animated status indicators

### 4. **ActionLog** (`components/activity/action-log.tsx`)
Chronological list of all system activities with filtering.

**Features:**
- Real-time activity feed
- Severity-based filtering
- Activity type filtering
- Search functionality
- Expandable filter options
- Color-coded severity indicators

### 5. **ResourceMonitor** (`components/activity/resource-monitor.tsx`)
Displays cloud resource usage and cost estimates.

**Features:**
- Cloud resource metrics (compute, storage, network)
- API usage tracking with rate limits
- Cost estimation (hourly and daily projections)
- Visual progress bars for resource utilization

## Data Management

### Hook: `useActivity` (`hooks/use-activity.ts`)
Central hook for managing all activity-related state and data.

**Features:**
- Aggregates data from multiple stores
- Provides filtering and sorting capabilities
- Manages real-time updates
- Calculates derived metrics
- Mock data generation for demo purposes

**API:**
```typescript
const {
  activities,              // All activities
  groupedActivities,      // Activities grouped by criteria
  agentActivities,        // Agent-specific activities
  workflowVisualizations, // Workflow visualization data
  resourceMetrics,        // Resource usage metrics
  filter,                 // Current filter state
  viewMode,              // Current view configuration
  isLoading,             // Loading state
  refreshInterval,        // Auto-refresh interval
  updateFilter,          // Update filter function
  updateViewMode,        // Update view mode function
  clearFilter,           // Clear all filters
  setAutoRefresh,        // Set refresh interval
  totalCount,            // Total activity count
  filteredCount          // Filtered activity count
} = useActivity()
```

## TypeScript Types

All activity-related types are defined in `types/activity.ts`:

- `Activity` - Base activity interface
- `ActivityType` - Activity type enumeration
- `ActivitySeverity` - Severity levels
- `ActivityFilter` - Filter configuration
- `AgentActivity` - Agent-specific activity data
- `WorkflowStep` - Individual workflow step
- `WorkflowVisualization` - Complete workflow visualization
- `ResourceMetrics` - Resource usage metrics

## Responsive Design

### Desktop View
- Horizontal tabs for navigation
- Full-width content area
- Persistent auto-refresh controls

### Mobile View
- Accordion-based navigation
- Collapsible sections
- Touch-optimized controls
- Reduced information density

## Real-time Updates

The activity viewer supports real-time updates through:
1. Configurable auto-refresh intervals (Off, 5s, 10s, 30s)
2. Simulated real-time data generation
3. Smooth animations for status changes
4. Progressive data loading

## Integration with Dashboard

The ActivityViewer is integrated into the dashboard's right panel:

```tsx
<SplitScreen
  leftPanel={{
    id: 'chat',
    title: 'Chat',
    content: <ChatInterface />
  }}
  rightPanel={{
    id: 'activity',
    title: 'Activity',
    content: <ActivityViewer />
  }}
/>
```

## Future Enhancements

1. **WebSocket Integration**: Replace mock data with real-time WebSocket connections
2. **Advanced Filtering**: Add date range selection and complex filter combinations
3. **Export Functionality**: Allow exporting activity logs and metrics
4. **Custom Dashboards**: Enable users to create custom activity views
5. **Alerting**: Add threshold-based alerts for resource usage and errors
6. **Performance Optimization**: Implement virtual scrolling for large activity lists