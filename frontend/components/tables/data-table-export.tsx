"use client"

import * as React from "react"
import { Table } from "@tanstack/react-table"
import { Download, FileSpreadsheet, FileJson, FileText, Check } from "lucide-react"
import Papa from "papaparse"
import * as XLSX from "xlsx"
import { saveAs } from "file-saver"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuCheckboxItem,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"

interface DataTableExportProps<TData> {
  table: Table<TData>
  filename?: string
  onExport?: (format: ExportFormat, data: any[]) => void
  className?: string
  allowColumnSelection?: boolean
  exportFormats?: ExportFormat[]
}

export type ExportFormat = "csv" | "excel" | "json"

export function DataTableExport<TData>({
  table,
  filename = "export",
  onExport,
  className,
  allowColumnSelection = true,
  exportFormats = ["csv", "excel", "json"],
}: DataTableExportProps<TData>) {
  const [selectedColumns, setSelectedColumns] = React.useState<string[]>([])
  const [exportedFormat, setExportedFormat] = React.useState<ExportFormat | null>(null)

  // Initialize selected columns
  React.useEffect(() => {
    const visibleColumns = table
      .getAllColumns()
      .filter((column) => column.getIsVisible() && column.id !== "select")
      .map((column) => column.id)
    setSelectedColumns(visibleColumns)
  }, [table])

  const getExportData = (selectedOnly: boolean = false) => {
    const rows = selectedOnly
      ? table.getFilteredSelectedRowModel().rows
      : table.getFilteredRowModel().rows

    const columns = allowColumnSelection
      ? table.getAllColumns().filter((column) => selectedColumns.includes(column.id))
      : table.getAllColumns().filter((column) => column.getIsVisible() && column.id !== "select")

    const headers = columns.map((column) => {
      const header = column.columnDef.header
      if (typeof header === "string") return header
      if (typeof header === "function") {
        // Try to extract text from the header function
        const headerElement = header({ column, header: column, table } as any)
        if (React.isValidElement(headerElement) && typeof headerElement.props.children === "string") {
          return headerElement.props.children
        }
      }
      return column.id
    })

    const data = rows.map((row) => {
      const rowData: Record<string, any> = {}
      columns.forEach((column) => {
        const value = row.getValue(column.id)
        rowData[column.id] = value
      })
      return rowData
    })

    return { headers, data, columns }
  }

  const exportToCSV = (selectedOnly: boolean = false) => {
    const { headers, data } = getExportData(selectedOnly)
    
    const csvData = data.map((row) => {
      return headers.reduce((acc, header, index) => {
        const column = table.getAllColumns().find((col) => col.id === header)
        const value = row[column?.id || header]
        acc[header] = value
        return acc
      }, {} as Record<string, any>)
    })

    const csv = Papa.unparse(csvData, { headers })
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
    saveAs(blob, `${filename}.csv`)
    
    onExport?.("csv", csvData)
    showExportSuccess("csv")
  }

  const exportToExcel = (selectedOnly: boolean = false) => {
    const { headers, data } = getExportData(selectedOnly)
    
    const wsData = [
      headers,
      ...data.map((row) => headers.map((header) => {
        const column = table.getAllColumns().find((col) => col.id === header)
        return row[column?.id || header]
      }))
    ]

    const ws = XLSX.utils.aoa_to_sheet(wsData)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, "Sheet1")
    
    // Styling
    const range = XLSX.utils.decode_range(ws["!ref"] || "A1")
    for (let C = range.s.c; C <= range.e.c; ++C) {
      const address = XLSX.utils.encode_col(C) + "1"
      if (!ws[address]) continue
      ws[address].s = {
        font: { bold: true },
        fill: { fgColor: { rgb: "EFEFEF" } }
      }
    }

    XLSX.writeFile(wb, `${filename}.xlsx`)
    
    onExport?.("excel", data)
    showExportSuccess("excel")
  }

  const exportToJSON = (selectedOnly: boolean = false) => {
    const { data } = getExportData(selectedOnly)
    
    const jsonString = JSON.stringify(data, null, 2)
    const blob = new Blob([jsonString], { type: "application/json" })
    saveAs(blob, `${filename}.json`)
    
    onExport?.("json", data)
    showExportSuccess("json")
  }

  const showExportSuccess = (format: ExportFormat) => {
    setExportedFormat(format)
    setTimeout(() => setExportedFormat(null), 2000)
  }

  const handleExport = (format: ExportFormat, selectedOnly: boolean = false) => {
    switch (format) {
      case "csv":
        exportToCSV(selectedOnly)
        break
      case "excel":
        exportToExcel(selectedOnly)
        break
      case "json":
        exportToJSON(selectedOnly)
        break
    }
  }

  const toggleColumn = (columnId: string) => {
    setSelectedColumns((prev) =>
      prev.includes(columnId)
        ? prev.filter((id) => id !== columnId)
        : [...prev, columnId]
    )
  }

  const selectAllColumns = () => {
    const allColumns = table
      .getAllColumns()
      .filter((column) => column.id !== "select")
      .map((column) => column.id)
    setSelectedColumns(allColumns)
  }

  const deselectAllColumns = () => {
    setSelectedColumns([])
  }

  const hasSelectedRows = table.getFilteredSelectedRowModel().rows.length > 0

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className={cn("gap-2", className)}>
          {exportedFormat ? (
            <>
              <Check className="h-4 w-4" />
              Exported!
            </>
          ) : (
            <>
              <Download className="h-4 w-4" />
              Export
            </>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[200px]">
        <DropdownMenuLabel>Export Data</DropdownMenuLabel>
        <DropdownMenuSeparator />
        
        {exportFormats.includes("csv") && (
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <FileText className="mr-2 h-4 w-4" />
              CSV
            </DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              <DropdownMenuItem onClick={() => handleExport("csv", false)}>
                All rows ({table.getFilteredRowModel().rows.length})
              </DropdownMenuItem>
              {hasSelectedRows && (
                <DropdownMenuItem onClick={() => handleExport("csv", true)}>
                  Selected rows ({table.getFilteredSelectedRowModel().rows.length})
                </DropdownMenuItem>
              )}
            </DropdownMenuSubContent>
          </DropdownMenuSub>
        )}

        {exportFormats.includes("excel") && (
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <FileSpreadsheet className="mr-2 h-4 w-4" />
              Excel
            </DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              <DropdownMenuItem onClick={() => handleExport("excel", false)}>
                All rows ({table.getFilteredRowModel().rows.length})
              </DropdownMenuItem>
              {hasSelectedRows && (
                <DropdownMenuItem onClick={() => handleExport("excel", true)}>
                  Selected rows ({table.getFilteredSelectedRowModel().rows.length})
                </DropdownMenuItem>
              )}
            </DropdownMenuSubContent>
          </DropdownMenuSub>
        )}

        {exportFormats.includes("json") && (
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <FileJson className="mr-2 h-4 w-4" />
              JSON
            </DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              <DropdownMenuItem onClick={() => handleExport("json", false)}>
                All rows ({table.getFilteredRowModel().rows.length})
              </DropdownMenuItem>
              {hasSelectedRows && (
                <DropdownMenuItem onClick={() => handleExport("json", true)}>
                  Selected rows ({table.getFilteredSelectedRowModel().rows.length})
                </DropdownMenuItem>
              )}
            </DropdownMenuSubContent>
          </DropdownMenuSub>
        )}

        {allowColumnSelection && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuLabel>Select Columns</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <div className="px-2 py-1.5 space-x-2 text-xs">
              <Button
                variant="ghost"
                size="sm"
                className="h-auto p-0 text-xs"
                onClick={selectAllColumns}
              >
                Select all
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-auto p-0 text-xs"
                onClick={deselectAllColumns}
              >
                Clear
              </Button>
            </div>
            <DropdownMenuSeparator />
            <div className="max-h-[200px] overflow-y-auto">
              {table
                .getAllColumns()
                .filter((column) => column.id !== "select")
                .map((column) => (
                  <DropdownMenuCheckboxItem
                    key={column.id}
                    checked={selectedColumns.includes(column.id)}
                    onCheckedChange={() => toggleColumn(column.id)}
                  >
                    {column.id}
                  </DropdownMenuCheckboxItem>
                ))}
            </div>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}