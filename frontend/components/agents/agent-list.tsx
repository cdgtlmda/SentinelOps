'use client';

import { memo, useMemo, useState } from 'react';
import { cn } from '@/lib/utils';
import { Agent, AgentFilter, AgentSortOption, AgentStatus, AgentType } from '@/types/agent';
import { AgentCard } from './agent-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Search, Filter, X } from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';

interface AgentListProps {
  agents: Agent[];
  onAgentAction: (agentId: string, action: 'start' | 'stop' | 'restart' | 'viewLogs') => void;
  className?: string;
}

const agentTypes: { value: AgentType; label: string }[] = [
  { value: 'security', label: 'Security' },
  { value: 'monitoring', label: 'Monitoring' },
  { value: 'remediation', label: 'Remediation' },
  { value: 'analysis', label: 'Analysis' },
  { value: 'network', label: 'Network' },
];

const agentStatuses: { value: AgentStatus; label: string }[] = [
  { value: 'idle', label: 'Idle' },
  { value: 'processing', label: 'Processing' },
  { value: 'waiting', label: 'Waiting' },
  { value: 'error', label: 'Error' },
  { value: 'completed', label: 'Completed' },
];

const sortOptions: { value: AgentSortOption; label: string }[] = [
  { value: 'name', label: 'Name' },
  { value: 'status', label: 'Status' },
  { value: 'lastAction', label: 'Last Action' },
  { value: 'performance', label: 'Performance' },
];

export const AgentList = memo(function AgentList({
  agents,
  onAgentAction,
  className,
}: AgentListProps) {
  const [filter, setFilter] = useState<AgentFilter>({});
  const [sortBy, setSortBy] = useState<AgentSortOption>('name');
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  const filteredAndSortedAgents = useMemo(() => {
    let filtered = agents;

    // Apply search filter
    if (filter.searchQuery) {
      const query = filter.searchQuery.toLowerCase();
      filtered = filtered.filter(
        (agent) =>
          agent.name.toLowerCase().includes(query) ||
          agent.type.toLowerCase().includes(query)
      );
    }

    // Apply type filter
    if (filter.types && filter.types.length > 0) {
      filtered = filtered.filter((agent) => filter.types!.includes(agent.type));
    }

    // Apply status filter
    if (filter.statuses && filter.statuses.length > 0) {
      filtered = filtered.filter((agent) => filter.statuses!.includes(agent.status));
    }

    // Sort agents
    const sorted = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'status':
          return a.status.localeCompare(b.status);
        case 'lastAction':
          return b.lastActionTimestamp.getTime() - a.lastActionTimestamp.getTime();
        case 'performance':
          const aScore = a.metrics.tasksCompleted / (a.metrics.tasksCompleted + a.metrics.tasksFailed || 1);
          const bScore = b.metrics.tasksCompleted / (b.metrics.tasksCompleted + b.metrics.tasksFailed || 1);
          return bScore - aScore;
        default:
          return 0;
      }
    });

    return sorted;
  }, [agents, filter, sortBy]);

  const handleTypeToggle = (type: AgentType) => {
    setFilter((prev) => ({
      ...prev,
      types: prev.types?.includes(type)
        ? prev.types.filter((t) => t !== type)
        : [...(prev.types || []), type],
    }));
  };

  const handleStatusToggle = (status: AgentStatus) => {
    setFilter((prev) => ({
      ...prev,
      statuses: prev.statuses?.includes(status)
        ? prev.statuses.filter((s) => s !== status)
        : [...(prev.statuses || []), status],
    }));
  };

  const clearFilters = () => {
    setFilter({});
  };

  const hasActiveFilters = filter.searchQuery || filter.types?.length || filter.statuses?.length;

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header with search and filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search agents..."
            value={filter.searchQuery || ''}
            onChange={(e) => setFilter((prev) => ({ ...prev, searchQuery: e.target.value }))}
            className="pl-10"
          />
        </div>

        <div className="flex items-center gap-2">
          <Select value={sortBy} onValueChange={(value: AgentSortOption) => setSortBy(value)}>
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              {sortOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Sheet open={isFilterOpen} onOpenChange={setIsFilterOpen}>
            <SheetTrigger asChild>
              <Button variant="outline" size="icon" className="relative">
                <Filter className="h-4 w-4" />
                {hasActiveFilters && (
                  <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-primary" />
                )}
              </Button>
            </SheetTrigger>
            <SheetContent>
              <SheetHeader>
                <SheetTitle>Filter Agents</SheetTitle>
                <SheetDescription>
                  Filter agents by type and status
                </SheetDescription>
              </SheetHeader>

              <div className="mt-6 space-y-6">
                {/* Type filters */}
                <div className="space-y-3">
                  <Label className="text-base font-semibold">Agent Type</Label>
                  {agentTypes.map((type) => (
                    <div key={type.value} className="flex items-center space-x-2">
                      <Checkbox
                        id={`type-${type.value}`}
                        checked={filter.types?.includes(type.value) || false}
                        onCheckedChange={() => handleTypeToggle(type.value)}
                      />
                      <Label
                        htmlFor={`type-${type.value}`}
                        className="text-sm font-normal cursor-pointer"
                      >
                        {type.label}
                      </Label>
                    </div>
                  ))}
                </div>

                {/* Status filters */}
                <div className="space-y-3">
                  <Label className="text-base font-semibold">Status</Label>
                  {agentStatuses.map((status) => (
                    <div key={status.value} className="flex items-center space-x-2">
                      <Checkbox
                        id={`status-${status.value}`}
                        checked={filter.statuses?.includes(status.value) || false}
                        onCheckedChange={() => handleStatusToggle(status.value)}
                      />
                      <Label
                        htmlFor={`status-${status.value}`}
                        className="text-sm font-normal cursor-pointer"
                      >
                        {status.label}
                      </Label>
                    </div>
                  ))}
                </div>

                {hasActiveFilters && (
                  <Button
                    variant="outline"
                    onClick={clearFilters}
                    className="w-full"
                  >
                    <X className="mr-2 h-4 w-4" />
                    Clear Filters
                  </Button>
                )}
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>

      {/* Active filters display */}
      {hasActiveFilters && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-muted-foreground">Active filters:</span>
          {filter.types?.map((type) => (
            <Button
              key={type}
              variant="secondary"
              size="sm"
              onClick={() => handleTypeToggle(type)}
              className="h-7 gap-1 px-2"
            >
              {type}
              <X className="h-3 w-3" />
            </Button>
          ))}
          {filter.statuses?.map((status) => (
            <Button
              key={status}
              variant="secondary"
              size="sm"
              onClick={() => handleStatusToggle(status)}
              className="h-7 gap-1 px-2"
            >
              {status}
              <X className="h-3 w-3" />
            </Button>
          ))}
        </div>
      )}

      {/* Agent grid */}
      {filteredAndSortedAgents.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filteredAndSortedAgents.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onAction={(action) => onAgentAction(agent.id, action)}
            />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <p className="text-lg font-medium text-muted-foreground">No agents found</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Try adjusting your filters or search query
          </p>
        </div>
      )}
    </div>
  );
});