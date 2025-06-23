'use client'

import { useState, useRef, ReactNode } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  Download, 
  Maximize2, 
  Minimize2, 
  RefreshCw, 
  Table as TableIcon 
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { ChartExportOptions } from '@/types/charts'
import { cn } from '@/lib/utils'

interface ChartContainerProps {
  title: string
  description?: string
  children: ReactNode
  data?: any[]
  onRefresh?: () => void
  onExport?: (options: ChartExportOptions) => void
  showDataTable?: boolean
  renderDataTable?: () => ReactNode
  className?: string
  loading?: boolean
  error?: string
}

export function ChartContainer({
  title,
  description,
  children,
  data,
  onRefresh,
  onExport,
  showDataTable = false,
  renderDataTable,
  className,
  loading = false,
  error
}: ChartContainerProps) {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showTable, setShowTable] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const chartRef = useRef<HTMLDivElement>(null)

  const handleRefresh = async () => {
    if (onRefresh) {
      setIsRefreshing(true)
      await onRefresh()
      setTimeout(() => setIsRefreshing(false), 500)
    }
  }

  const handleExport = (format: ChartExportOptions['format']) => {
    if (onExport) {
      onExport({ format, filename: `${title.toLowerCase().replace(/\s+/g, '-')}-${new Date().toISOString()}` })
    }
  }

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
  }

  const toggleDataTable = () => {
    setShowTable(!showTable)
  }

  const chartContent = (
    <div className={cn('relative', className)}>
      <div className="absolute top-2 right-2 z-10 flex gap-2">
        {renderDataTable && (
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleDataTable}
            className="h-8 w-8"
            aria-label="Toggle data table view"
            aria-pressed={showTable}
          >
            <TableIcon className="h-4 w-4" aria-hidden="true" />
          </Button>
        )}
        
        {onRefresh && (
          <Button
            variant="ghost"
            size="icon"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="h-8 w-8"
            aria-label="Refresh chart data"
            aria-busy={isRefreshing}
          >
            <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} aria-hidden="true" />
          </Button>
        )}

        {onExport && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                aria-label="Export chart data"
              >
                <Download className="h-4 w-4" aria-hidden="true" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => handleExport('png')}>
                Export as PNG
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleExport('svg')}>
                Export as SVG
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleExport('csv')}>
                Export as CSV
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleExport('json')}>
                Export as JSON
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {!isFullscreen && (
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleFullscreen}
            className="h-8 w-8"
            aria-label="Enter fullscreen mode"
          >
            <Maximize2 className="h-4 w-4" aria-hidden="true" />
          </Button>
        )}
      </div>

      <div ref={chartRef} className="w-full">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-pulse text-muted-foreground">Loading chart data...</div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-destructive">{error}</div>
          </div>
        ) : showTable && renderDataTable ? (
          <div className="overflow-auto max-h-96">
            {renderDataTable()}
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  )

  if (isFullscreen) {
    return (
      <Dialog open={isFullscreen} onOpenChange={setIsFullscreen}>
        <DialogContent className="max-w-[90vw] max-h-[90vh] overflow-auto">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold">{title}</h2>
                {description && <p className="text-muted-foreground">{description}</p>}
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleFullscreen}
                className="h-8 w-8"
              >
                <Minimize2 className="h-4 w-4" />
              </Button>
            </div>
            {chartContent}
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        {chartContent}
      </CardContent>
    </Card>
  )
}