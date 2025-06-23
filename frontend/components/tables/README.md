# Data Table Components

Comprehensive data table components for SentinelOps with advanced features including sorting, filtering, pagination, row selection, bulk actions, and data export.

## Features

### Core Features
- **Sortable columns** - Click column headers to sort ascending/descending
- **Advanced filtering** - Text search, date ranges, multi-select filters
- **Column visibility** - Show/hide columns with dropdown menu
- **Row selection** - Single or multi-row selection with checkbox
- **Sticky headers** - Header stays visible when scrolling
- **Loading states** - Skeleton loader while data is fetching
- **Empty states** - Custom message when no data found
- **Responsive design** - Horizontal scroll on mobile
- **Keyboard navigation** - Navigate with keyboard shortcuts

### Data Management
- **Pagination** - Navigate through large datasets efficiently
- **Page size selection** - Choose rows per page (10, 20, 30, 50, 100)
- **Page jumping** - Jump directly to any page number
- **Export functionality** - Export to CSV, Excel, or JSON
- **Bulk actions** - Perform actions on multiple selected rows

## Usage

### Basic Data Table

```tsx
import { DataTable } from '@/components/tables'
import { ColumnDef } from '@tanstack/react-table'

const columns: ColumnDef<YourDataType>[] = [
  {
    accessorKey: 'name',
    header: 'Name',
  },
  {
    accessorKey: 'status',
    header: 'Status',
  },
]

function MyTable() {
  return (
    <DataTable
      columns={columns}
      data={data}
      pageSize={20}
      enableRowSelection
      enableMultiSelect
    />
  )
}
```

### With Filters

```tsx
import { DataTable, DataTableFilters, FilterConfig } from '@/components/tables'
import { useTable } from '@/hooks/use-table'

const filterConfigs: FilterConfig[] = [
  {
    id: 'name',
    label: 'Name',
    type: 'text',
    placeholder: 'Search by name...',
  },
  {
    id: 'status',
    label: 'Status',
    type: 'multiselect',
    options: [
      { label: 'Active', value: 'active' },
      { label: 'Inactive', value: 'inactive' },
    ],
  },
]

function FilteredTable() {
  const { table } = useTable({
    data,
    columns,
  })

  return (
    <>
      <DataTableFilters
        table={table}
        filters={filterConfigs}
      />
      <DataTable
        table={table}
        columns={columns}
        data={data}
      />
    </>
  )
}
```

### With Bulk Actions

```tsx
import { DataTableBulkActions, BulkAction } from '@/components/tables'

const bulkActions: BulkAction<YourDataType>[] = [
  {
    label: 'Delete',
    icon: <Trash2 className="h-4 w-4" />,
    variant: 'destructive',
    confirmMessage: 'Are you sure?',
    onClick: (rows) => {
      // Handle delete
    },
  },
]

function TableWithActions() {
  const { table } = useTable({ data, columns })

  return (
    <>
      <DataTableBulkActions
        table={table}
        actions={bulkActions}
      />
      <DataTable table={table} columns={columns} data={data} />
    </>
  )
}
```

### With Export

```tsx
import { DataTableExport } from '@/components/tables'

function ExportableTable() {
  const { table } = useTable({ data, columns })

  return (
    <>
      <DataTableExport
        table={table}
        filename="my-data"
        exportFormats={['csv', 'excel', 'json']}
      />
      <DataTable table={table} columns={columns} data={data} />
    </>
  )
}
```

## Pre-built Tables

### Incidents Table
```tsx
import { IncidentsTable } from '@/components/tables'

<IncidentsTable
  incidents={incidents}
  onIncidentClick={(incident) => console.log(incident)}
  onIncidentUpdate={(incident) => console.log(incident)}
/>
```

### Agents Table
```tsx
import { AgentsTable } from '@/components/tables'

<AgentsTable
  agents={agents}
  onAgentClick={(agent) => console.log(agent)}
  onAgentAction={(agentId, action) => console.log(agentId, action)}
/>
```

### Alerts Table
```tsx
import { AlertsTable } from '@/components/tables'

<AlertsTable
  alerts={alerts}
  onAlertClick={(alert) => console.log(alert)}
  onAlertAction={(alertId, action) => console.log(alertId, action)}
/>
```

### Audit Log Table
```tsx
import { AuditLogTable } from '@/components/tables'

<AuditLogTable
  entries={auditLogs}
  onEntryClick={(entry) => console.log(entry)}
/>
```

## Filter Types

- **text** - Free text search
- **select** - Single selection dropdown
- **multiselect** - Multiple selection with checkboxes
- **date** - Single date picker
- **daterange** - Date range picker

## Hook Usage

The `useTable` hook provides full control over table state:

```tsx
const {
  table,
  sorting,
  columnFilters,
  columnVisibility,
  rowSelection,
  pagination,
  setSorting,
  setColumnFilters,
  resetFilters,
  resetSorting,
  getSelectedRows,
} = useTable({
  data,
  columns,
  pageSize: 20,
  enableRowSelection: true,
  enableMultiSelect: true,
  manualPagination: false, // Set true for server-side pagination
  initialState: {
    sorting: [{ id: 'createdAt', desc: true }],
  },
})
```

## Performance Considerations

- Tables are optimized for datasets up to 10,000 rows
- For larger datasets, consider:
  - Server-side pagination (`manualPagination: true`)
  - Virtual scrolling (coming soon)
  - Lazy loading
- Column resizing uses CSS resize for better performance
- Exports are processed in chunks for large datasets

## Accessibility

- Full keyboard navigation support
- Screen reader announcements
- ARIA labels on all interactive elements
- Focus management for dialogs and dropdowns
- High contrast mode support

## Styling

Tables use the design system tokens and can be customized:

```tsx
<DataTable
  className="my-custom-table"
  // Custom styles will be applied to the container
/>
```

## Mobile Support

- Horizontal scroll on small screens
- Touch-optimized controls
- Responsive column visibility
- Simplified filters on mobile