// Convenient selectors for common store operations
import { useIncidentStore, useAgentStore } from './index'

export const useActiveIncidents = () => 
  useIncidentStore((state) => state.incidents.filter(inc => inc.status === 'active'))

export const useInvestigatingIncidents = () => 
  useIncidentStore((state) => state.incidents.filter(inc => inc.status === 'investigating'))

export const useCriticalIncidents = () => 
  useIncidentStore((state) => state.incidents.filter(inc => inc.severity === 'critical'))

export const useUnacknowledgedAlerts = () => 
  useIncidentStore((state) => state.alerts.filter(alert => !alert.acknowledged))

export const useOnlineAgents = () => 
  useAgentStore((state) => state.agents.filter(agent => agent.status === 'online'))

export const useActiveWorkflows = () => 
  useAgentStore((state) => state.workflows.filter(wf => wf.status === 'running'))

export const useFailedWorkflows = () => 
  useAgentStore((state) => state.workflows.filter(wf => wf.status === 'failed'))