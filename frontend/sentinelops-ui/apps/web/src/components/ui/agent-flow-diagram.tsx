"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye, Brain, Zap, Users, Activity, ArrowRight, AlertTriangle, CheckCircle } from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  role: string;
  description: string;
  icon: React.ElementType;
  color: string;
  bgColor: string;
  tools?: string[];
}

const agents: Agent[] = [
  {
    id: 'detection',
    name: 'Detection Agent',
    role: 'Continuous Monitoring',
    description: 'Scans logs, monitors network traffic, and identifies suspicious patterns.',
    icon: Eye,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
    tools: ['LogMonitoringTool', 'EventCorrelatorTool', 'TransferToOrchestratorAgentTool'],
  },
  {
    id: 'orchestration',
    name: 'Orchestration Agent',
    role: 'Workflow Coordination',
    description: 'Coordinates all agents, manages handoffs, and ensures seamless collaboration.',
    icon: Activity,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
    tools: ['WorkflowManagementTool', 'IncidentPrioritizationTool', 'Transfer[Agent]Tool'],
  },
  {
    id: 'analysis',
    name: 'Analysis Agent',
    role: 'Threat Intelligence',
    description: 'Uses Gemini models to understand attack vectors and assess impact.',
    icon: Brain,
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/10',
    tools: ['IncidentAnalysisTool', 'RecommendationTool', 'ContextTool'],
  },
  {
    id: 'remediation',
    name: 'Remediation Agent',
    role: 'Automated Response',
    description: 'Executes containment actions with precision.',
    icon: Zap,
    color: 'text-orange-500',
    bgColor: 'bg-orange-500/10',
    tools: ['BlockIPTool', 'IsolateVMTool', 'RevokeIAMTool'],
  },
  {
    id: 'communication',
    name: 'Communication Agent',
    role: 'Stakeholder Updates',
    description: 'Manages notifications and keeps teams informed.',
    icon: Users,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    tools: ['SlackNotificationTool', 'EmailNotificationTool', 'WebhookTool'],
  },
];

interface DataFlow {
  from: string;
  to: string;
  data: string;
  delay: number;
  toolUsed?: string;
  metadata?: string;
}

const dataFlows: DataFlow[] = [
  { 
    from: 'detection', 
    to: 'orchestration', 
    data: 'Suspicious API Activity Detected', 
    delay: 0,
    toolUsed: 'TransferToOrchestratorAgentTool',
    metadata: 'incident_id: inc-12345, severity: high'
  },
  { 
    from: 'orchestration', 
    to: 'analysis', 
    data: 'Analyze Incident Context', 
    delay: 1,
    toolUsed: 'TransferToAnalysisAgentTool',
    metadata: 'workflow_stage: analysis_requested'
  },
  { 
    from: 'analysis', 
    to: 'orchestration', 
    data: 'Threat: Privilege Escalation (95% confidence)', 
    delay: 2,
    toolUsed: 'IncidentAnalysisTool + Gemini Pro',
    metadata: 'threat_level: critical'
  },
  { 
    from: 'orchestration', 
    to: 'remediation', 
    data: 'Execute: Block IP + Isolate VM', 
    delay: 3,
    toolUsed: 'TransferToRemediationAgentTool',
    metadata: 'auto_approve: true'
  },
  { 
    from: 'orchestration', 
    to: 'communication', 
    data: 'Alert Security Team', 
    delay: 3.5,
    toolUsed: 'TransferToCommunicationAgentTool',
    metadata: 'channels: [slack, email]'
  },
  { 
    from: 'remediation', 
    to: 'orchestration', 
    data: 'Actions Complete: IP Blocked, VM Isolated', 
    delay: 4,
    toolUsed: 'BlockIPTool + IsolateVMTool',
    metadata: 'status: success'
  },
  { 
    from: 'communication', 
    to: 'orchestration', 
    data: 'Team Notified via Slack + Email', 
    delay: 4.5,
    toolUsed: 'SlackNotificationTool',
    metadata: 'delivered: true'
  },
];

export function AgentFlowDiagram() {
  const [activeFlow, setActiveFlow] = useState<number>(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeAgents, setActiveAgents] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (isPlaying && activeFlow < dataFlows.length - 1) {
      const currentFlow = dataFlows[activeFlow + 1];
      const timer = setTimeout(() => {
        setActiveFlow(activeFlow + 1);
        setActiveAgents(new Set([currentFlow.from, currentFlow.to]));
      }, activeFlow === -1 ? 0 : 1000);
      return () => clearTimeout(timer);
    } else if (isPlaying && activeFlow === dataFlows.length - 1) {
      setTimeout(() => {
        setIsPlaying(false);
        setActiveFlow(-1);
        setActiveAgents(new Set());
      }, 2000);
    }
  }, [activeFlow, isPlaying]);

  const handlePlayDemo = () => {
    setActiveFlow(-1);
    setActiveAgents(new Set());
    setIsPlaying(true);
  };

  const getAgentPosition = (agentId: string) => {
    const positions = {
      detection: { x: 20, y: 40 },
      orchestration: { x: 50, y: 20 },
      analysis: { x: 80, y: 40 },
      remediation: { x: 30, y: 60 },
      communication: { x: 70, y: 60 },
    };
    return positions[agentId as keyof typeof positions] || { x: 50, y: 50 };
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.6 }}
      className="mb-16"
    >
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold text-foreground mb-4">
          Five Specialized AI Agents in Action
        </h2>
        <p className="text-lg text-muted-foreground max-w-3xl mx-auto mb-6">
          Watch how agents collaborate through Google ADK's Transfer System to detect and respond to threats
        </p>
        <button
          onClick={handlePlayDemo}
          disabled={isPlaying}
          className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isPlaying ? (
            <>
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="w-4 h-4 border-2 border-white border-t-transparent rounded-full"
              />
              Demo Running...
            </>
          ) : (
            <>
              <AlertTriangle className="w-4 h-4" />
              Simulate Security Incident
            </>
          )}
        </button>
      </div>

      <div className="relative bg-card border border-border rounded-xl p-8 overflow-visible" style={{ minHeight: '500px', paddingBottom: '80px' }}>
        {/* Connection Lines */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none">
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 10 3, 0 6" fill="#666" />
            </marker>
          </defs>
          
          {/* Draw connections */}
          {dataFlows.map((flow, index) => {
            const from = getAgentPosition(flow.from);
            const to = getAgentPosition(flow.to);
            const isActive = index === activeFlow;
            
            return (
              <g key={index}>
                <line
                  x1={`${from.x}%`}
                  y1={`${from.y}%`}
                  x2={`${to.x}%`}
                  y2={`${to.y}%`}
                  stroke={isActive ? '#3b82f6' : '#333'}
                  strokeWidth={isActive ? 3 : 1}
                  strokeDasharray={isActive ? '0' : '5,5'}
                  markerEnd="url(#arrowhead)"
                  className="transition-all duration-300"
                />
              </g>
            );
          })}
        </svg>

        {/* Agents */}
        {agents.map((agent) => {
          const position = getAgentPosition(agent.id);
          const isActive = activeAgents.has(agent.id);
          
          return (
            <motion.div
              key={agent.id}
              className="absolute transform -translate-x-1/2 -translate-y-1/2"
              style={{ left: `${position.x}%`, top: `${position.y}%` }}
              animate={{
                scale: isActive ? 1.1 : 1,
                transition: { duration: 0.3 }
              }}
            >
              <div className={`relative ${isActive ? 'z-10' : 'z-0'}`}>
                {isActive && (
                  <motion.div
                    className="absolute inset-0 bg-blue-500/20 rounded-2xl blur-xl"
                    animate={{
                      scale: [1, 1.5, 1],
                      opacity: [0.5, 0.2, 0.5],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                    }}
                  />
                )}
                <div className={`bg-card border-2 ${isActive ? 'border-blue-500' : 'border-border'} rounded-xl p-4 transition-all duration-300 ${isActive ? 'shadow-xl' : 'shadow-md'} hover:shadow-lg cursor-pointer`}>
                  <div className={`w-12 h-12 ${agent.bgColor} rounded-lg flex items-center justify-center mb-3 mx-auto`}>
                    <agent.icon className={`w-6 h-6 ${agent.color}`} />
                  </div>
                  <h4 className="text-sm font-semibold text-foreground text-center mb-1">{agent.name}</h4>
                  <p className="text-xs text-muted-foreground text-center">{agent.role}</p>
                </div>
              </div>
            </motion.div>
          );
        })}

        {/* Data Transfer Animation */}
        <AnimatePresence>
          {activeFlow >= 0 && activeFlow < dataFlows.length && (
            <motion.div
              key={activeFlow}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20"
            >
              <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg px-4 py-3 shadow-2xl max-w-sm">
                <div className="flex items-center gap-2 mb-2">
                  <ArrowRight className="w-4 h-4" />
                  <span className="text-sm font-semibold">Google ADK Transfer</span>
                </div>
                <p className="text-sm font-medium mb-1">{dataFlows[activeFlow].data}</p>
                <p className="text-xs opacity-80">Tool: {dataFlows[activeFlow].toolUsed}</p>
                {dataFlows[activeFlow].metadata && (
                  <p className="text-xs opacity-70 mt-1">{dataFlows[activeFlow].metadata}</p>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Status Display */}
        {isPlaying && (
          <div className="absolute bottom-4 left-4 right-4">
            <div className="bg-black/80 backdrop-blur-sm rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white">Security Incident Response Progress</span>
                <span className="text-xs text-gray-400">{activeFlow + 1} / {dataFlows.length}</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <motion.div
                  className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                  initial={{ width: '0%' }}
                  animate={{ width: `${((activeFlow + 1) / dataFlows.length) * 100}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Completion Message */}
        {!isPlaying && activeFlow === -1 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 flex items-center justify-center"
          >
            <div className="text-center">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">Threat Neutralized</h3>
              <p className="text-sm text-muted-foreground max-w-md">
                The multi-agent system successfully detected, analyzed, and responded to the security threat in under 30 seconds
              </p>
            </div>
          </motion.div>
        )}
      </div>

      {/* Agent Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mt-8">
        {agents.map((agent) => (
          <div
            key={agent.id}
            className="bg-card border border-border rounded-lg p-4 flex flex-col"
          >
            <div className="flex-grow">
              <div className={`w-10 h-10 ${agent.bgColor} rounded-lg flex items-center justify-center mb-2 mx-auto`}>
                <agent.icon className={`w-5 h-5 ${agent.color}`} />
              </div>
              <h4 className="text-sm font-semibold text-foreground mb-1 text-center">{agent.name}</h4>
              <p className="text-xs text-muted-foreground mb-2 text-center">{agent.description}</p>
            </div>
            {agent.tools && (
              <div className="border-t pt-2 mt-2">
                <p className="text-xs font-medium text-foreground mb-1 text-center">ADK Tools:</p>
                <ul className="text-xs text-muted-foreground space-y-0.5 text-center">
                  {agent.tools.map((tool, idx) => (
                    <li key={idx} className="text-xs">{tool}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Google ADK Implementation Notes */}
      <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-500" />
            Google ADK in Action
          </h3>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <span className="text-blue-500 mt-1">•</span>
              <span><strong>Transfer System:</strong> ADK's native transfer_to_agent mechanism enables seamless handoffs between agents with full context preservation</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-500 mt-1">•</span>
              <span><strong>Tool Integration:</strong> All agents extend google.adk.tools.BaseTool with async execution and Pydantic validation</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-500 mt-1">•</span>
              <span><strong>LLM Agent Base:</strong> Agents built on google.adk.agents.LlmAgent for intelligent decision making</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-500 mt-1">•</span>
              <span><strong>Sequential Workflows:</strong> Orchestrator uses ADK's SequentialAgent pattern for complex multi-step operations</span>
            </li>
          </ul>
        </div>

        <div className="bg-gradient-to-br from-green-500/10 to-orange-500/10 border border-green-500/20 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
            <Zap className="w-5 h-5 text-green-500" />
            Custom SentinelOps Patterns
          </h3>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <span className="text-green-500 mt-1">•</span>
              <span><strong>SentinelOpsBaseAgent:</strong> Custom base class adding GCP auth, Cloud Logging, and telemetry to all agents</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-500 mt-1">•</span>
              <span><strong>Workflow Metadata:</strong> Each transfer includes workflow_stage and incident context for stateful processing</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-500 mt-1">•</span>
              <span><strong>Dry Run Mode:</strong> All remediation tools support safe testing without executing actual changes</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-500 mt-1">•</span>
              <span><strong>Auto-scaling:</strong> Agents handle concurrent workflows using ADK's async capabilities</span>
            </li>
          </ul>
        </div>
      </div>
    </motion.div>
  );
}