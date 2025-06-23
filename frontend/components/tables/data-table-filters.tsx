"use client"

import * as React from "react"
import { Table } from "@tanstack/react-table"
import { X, Search, Calendar, Filter } from "lucide-react"
import { format } from "date-fns"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Checkbox } from "@/components/ui/checkbox"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { useDebouncedCallback } from "@/hooks/use-debounced-callback"

export interface FilterOption {
  label: string
  value: string
}

export interface FilterConfig {
  id: string
  label: string
  type: "text" | "select" | "multiselect" | "date" | "daterange"
  options?: FilterOption[]
  placeholder?: string
}

export interface DataTableFiltersProps<TData> {
  table: Table<TData>
  filters: FilterConfig[]
  onFiltersChange?: (filters: Record<string, any>) => void
  className?: string
}

export function DataTableFilters<TData>({
  table,
  filters,
  onFiltersChange,
  className,
}: DataTableFiltersProps<TData>) {
  const [activeFilters, setActiveFilters] = React.useState<Record<string, any>>({})
  const [dateRanges, setDateRanges] = React.useState<Record<string, { from?: Date; to?: Date }>>({})
  const [textInputValues, setTextInputValues] = React.useState<Record<string, string>>({})

  const handleFilterChange = (filterId: string, value: any) => {
    const newFilters = { ...activeFilters }
    
    if (value === undefined || value === null || value === "" || 
        (Array.isArray(value) && value.length === 0)) {
      delete newFilters[filterId]
    } else {
      newFilters[filterId] = value
    }

    setActiveFilters(newFilters)
    onFiltersChange?.(newFilters)

    // Apply the filter to the table
    if (table.getColumn(filterId)) {
      table.getColumn(filterId)?.setFilterValue(value)
    }
  }

  // Create debounced version for text inputs (300ms delay)
  const debouncedTextFilterChange = useDebouncedCallback((filterId: string, value: string) => {
    handleFilterChange(filterId, value)
  }, 300)

  // Create debounced version for date range inputs (500ms delay)
  const debouncedDateRangeChange = useDebouncedCallback((filterId: string, value: any) => {
    handleFilterChange(filterId, value)
  }, 500)

  const clearAllFilters = () => {
    setActiveFilters({})
    setDateRanges({})
    setTextInputValues({})
    table.resetColumnFilters()
    onFiltersChange?.({})
  }

  const activeFilterCount = Object.keys(activeFilters).length

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex flex-wrap gap-2">
        {filters.map((filter) => (
          <div key={filter.id} className="flex items-center space-x-2">
            {filter.type === "text" && (
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder={filter.placeholder || `Search ${filter.label}...`}
                  value={textInputValues[filter.id] ?? (activeFilters[filter.id] as string) || ""}
                  onChange={(e) => {
                    const value = e.target.value
                    setTextInputValues({ ...textInputValues, [filter.id]: value })
                    debouncedTextFilterChange(filter.id, value)
                  }}
                  className="pl-8 w-[200px]"
                />
              </div>
            )}

            {filter.type === "select" && filter.options && (
              <Select
                value={(activeFilters[filter.id] as string) || ""}
                onValueChange={(value) => handleFilterChange(filter.id, value === "all" ? undefined : value)}
              >
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder={filter.placeholder || `Select ${filter.label}`} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  {filter.options.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            {filter.type === "multiselect" && filter.options && (
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="h-10 border-dashed">
                    <Filter className="mr-2 h-4 w-4" />
                    {filter.label}
                    {activeFilters[filter.id] && (activeFilters[filter.id] as string[]).length > 0 && (
                      <>
                        <div className="mx-2 h-4 w-px bg-border" />
                        <Badge variant="secondary" className="rounded-sm px-1 font-normal">
                          {(activeFilters[filter.id] as string[]).length}
                        </Badge>
                      </>
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-[200px] p-0" align="start">
                  <div className="p-4 space-y-2">
                    <div className="flex items-center justify-between mb-2">
                      <Label className="text-sm font-medium">{filter.label}</Label>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleFilterChange(filter.id, [])}
                        className="h-auto p-0 text-xs"
                      >
                        Clear
                      </Button>
                    </div>
                    {filter.options.map((option) => {
                      const isChecked = (activeFilters[filter.id] as string[])?.includes(option.value) || false
                      return (
                        <div key={option.value} className="flex items-center space-x-2">
                          <Checkbox
                            id={`${filter.id}-${option.value}`}
                            checked={isChecked}
                            onCheckedChange={(checked) => {
                              const currentValues = (activeFilters[filter.id] as string[]) || []
                              const newValues = checked
                                ? [...currentValues, option.value]
                                : currentValues.filter((v) => v !== option.value)
                              handleFilterChange(filter.id, newValues)
                            }}
                          />
                          <Label
                            htmlFor={`${filter.id}-${option.value}`}
                            className="text-sm font-normal cursor-pointer"
                          >
                            {option.label}
                          </Label>
                        </div>
                      )
                    })}
                  </div>
                </PopoverContent>
              </Popover>
            )}

            {filter.type === "date" && (
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-[180px] justify-start text-left font-normal",
                      !activeFilters[filter.id] && "text-muted-foreground"
                    )}
                  >
                    <Calendar className="mr-2 h-4 w-4" />
                    {activeFilters[filter.id] ? (
                      format(new Date(activeFilters[filter.id] as string), "PPP")
                    ) : (
                      <span>{filter.placeholder || `Select ${filter.label}`}</span>
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <div className="p-4">
                    <Input
                      type="date"
                      value={activeFilters[filter.id] || ""}
                      onChange={(e) => handleFilterChange(filter.id, e.target.value)}
                    />
                  </div>
                </PopoverContent>
              </Popover>
            )}

            {filter.type === "daterange" && (
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-[280px] justify-start text-left font-normal",
                      !dateRanges[filter.id]?.from && "text-muted-foreground"
                    )}
                  >
                    <Calendar className="mr-2 h-4 w-4" />
                    {dateRanges[filter.id]?.from ? (
                      dateRanges[filter.id]?.to ? (
                        <>
                          {format(dateRanges[filter.id].from!, "LLL dd, y")} -{" "}
                          {format(dateRanges[filter.id].to!, "LLL dd, y")}
                        </>
                      ) : (
                        format(dateRanges[filter.id].from!, "LLL dd, y")
                      )
                    ) : (
                      <span>{filter.placeholder || "Pick a date range"}</span>
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <div className="p-4 space-y-2">
                    <div className="space-y-2">
                      <Label>From</Label>
                      <Input
                        type="date"
                        value={dateRanges[filter.id]?.from ? format(dateRanges[filter.id].from!, "yyyy-MM-dd") : ""}
                        onChange={(e) => {
                          const newDate = e.target.value ? new Date(e.target.value) : undefined
                          const newRange = { ...dateRanges[filter.id], from: newDate }
                          setDateRanges({ ...dateRanges, [filter.id]: newRange })
                          debouncedDateRangeChange(filter.id, newRange)
                        }}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>To</Label>
                      <Input
                        type="date"
                        value={dateRanges[filter.id]?.to ? format(dateRanges[filter.id].to!, "yyyy-MM-dd") : ""}
                        onChange={(e) => {
                          const newDate = e.target.value ? new Date(e.target.value) : undefined
                          const newRange = { ...dateRanges[filter.id], to: newDate }
                          setDateRanges({ ...dateRanges, [filter.id]: newRange })
                          debouncedDateRangeChange(filter.id, newRange)
                        }}
                      />
                    </div>
                  </div>
                </PopoverContent>
              </Popover>
            )}
          </div>
        ))}

        {activeFilterCount > 0 && (
          <Button
            variant="ghost"
            onClick={clearAllFilters}
            className="h-10 px-2 lg:px-3"
          >
            Clear all
            <X className="ml-2 h-4 w-4" />
          </Button>
        )}
      </div>

      {activeFilterCount > 0 && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(activeFilters).map(([key, value]) => {
            const filter = filters.find((f) => f.id === key)
            if (!filter) return null

            let displayValue: string = ""
            
            if (filter.type === "multiselect" && Array.isArray(value)) {
              displayValue = `${value.length} selected`
            } else if (filter.type === "date" && value) {
              displayValue = format(new Date(value), "PPP")
            } else if (filter.type === "daterange" && value) {
              const range = value as { from?: Date; to?: Date }
              if (range.from && range.to) {
                displayValue = `${format(range.from, "LLL dd")} - ${format(range.to, "LLL dd, y")}`
              } else if (range.from) {
                displayValue = `From ${format(range.from, "LLL dd, y")}`
              }
            } else if (filter.type === "select" && filter.options) {
              const option = filter.options.find((o) => o.value === value)
              displayValue = option?.label || value
            } else {
              displayValue = String(value)
            }

            return (
              <Badge key={key} variant="secondary" className="gap-1 pr-1">
                <span className="font-medium">{filter.label}:</span>
                <span>{displayValue}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-auto p-0 pl-1 hover:bg-transparent"
                  onClick={() => handleFilterChange(key, undefined)}
                >
                  <X className="h-3 w-3" />
                </Button>
              </Badge>
            )
          })}
        </div>
      )}
    </div>
  )
}