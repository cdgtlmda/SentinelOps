'use client';

import { AgentList } from '@/components/agents/agent-list';
import { useAgents } from '@/hooks/use-agents';
import { Button } from '@/components/ui/button';
import { PlusCircle, RefreshCw } from 'lucide-react';
import { useState } from 'react';

export default function AgentsPage() {
  const { agents, isLoading, handleAgentAction } = useAgents();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    // Simulate refresh delay
    setTimeout(() => {
      setIsRefreshing(false);
    }, 1000);
  };

  const handleAgentActionWithLogs = (agentId: string, action: 'start' | 'stop' | 'restart' | 'viewLogs') => {
    if (action === 'viewLogs') {
      // In a real app, this would open a logs modal or navigate to logs page
      console.log(`Viewing logs for agent ${agentId}`);
      return;
    }
    handleAgentAction(agentId, action);
  };

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-200px)] items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent motion-reduce:animate-[spin_1.5s_linear_infinite]" />
          <p className="mt-4 text-muted-foreground">Loading agents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Agents</h1>
            <p className="mt-2 text-muted-foreground">
              Monitor and manage your security agents in real-time
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleRefresh}
              disabled={isRefreshing}
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button>
              <PlusCircle className="mr-2 h-4 w-4" />
              Deploy Agent
            </Button>
          </div>
        </div>
      </div>

      {/* Agent Statistics */}
      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Agents"
          value={agents.length}
          description="Active in your environment"
        />
        <StatCard
          title="Active"
          value={agents.filter(a => a.status === 'processing').length}
          description="Currently processing tasks"
          valueClassName="text-blue-600"
        />
        <StatCard
          title="Idle"
          value={agents.filter(a => a.status === 'idle').length}
          description="Available for new tasks"
          valueClassName="text-gray-600"
        />
        <StatCard
          title="Errors"
          value={agents.filter(a => a.status === 'error').length}
          description="Require attention"
          valueClassName="text-red-600"
        />
      </div>

      {/* Agent List */}
      <AgentList
        agents={agents}
        onAgentAction={handleAgentActionWithLogs}
      />
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: number;
  description: string;
  valueClassName?: string;
}

function StatCard({ title, value, description, valueClassName }: StatCardProps) {
  return (
    <div className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
      <p className="text-sm font-medium text-muted-foreground">{title}</p>
      <p className={`mt-2 text-3xl font-bold ${valueClassName || ''}`}>{value}</p>
      <p className="mt-1 text-xs text-muted-foreground">{description}</p>
    </div>
  );
}