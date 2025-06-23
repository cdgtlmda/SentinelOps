"use client";

import { useState, useEffect } from "react";
import { AnimatedText } from "@/components/animated-text";
import { CopyText } from "@/components/copy-text";
import Link from "next/link";
import { 
  Bot, 
  Play, 
  Users, 
  Activity, 
  AlertTriangle, 
  Eye, 
  Zap, 
  MessageSquare,
  CheckCircle,
  Clock,
  ArrowLeft,
  ArrowRight,
  Shield,
  Search,
  Wrench,
  Bell,
  Settings
} from "lucide-react";

interface Agent {
  id: string;
  name: string;
  type: 'detection' | 'analysis' | 'remediation' | 'communication' | 'orchestrator';
  status: 'idle' | 'active' | 'completed' | 'error';
  progress: number;
  currentTask: string;
  lastUpdate: string;
  icon: any;
}

interface IncidentStep {
  id: string;
  agent: string;
  action: string;
  details: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  timestamp: string;
  duration?: number;
  output?: any;
}

export default function IncidentResponseDemo() {
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [agents, setAgents] = useState<Agent[]>([
    {
      id: 'orchestrator',
      name: 'Orchestrator Agent',
      type: 'orchestrator',
      status: 'idle',
      progress: 0,
      currentTask: 'Waiting for incident trigger',
      lastUpdate: '',
      icon: Settings
    },
    {
      id: 'detection',
      name: 'Detection Agent',
      type: 'detection',
      status: 'idle',
      progress: 0,
      currentTask: 'Monitoring security feeds',
      lastUpdate: '',
      icon: Eye
    },
    {
      id: 'analysis',
      name: 'Analysis Agent',
      type: 'analysis',
      status: 'idle',
      progress: 0,
      currentTask: 'Ready for threat analysis',
      lastUpdate: '',
      icon: Search
    },
    {
      id: 'remediation',
      name: 'Remediation Agent',
      type: 'remediation',
      status: 'idle',
      progress: 0,
      currentTask: 'Standing by for response actions',
      lastUpdate: '',
      icon: Wrench
    },
    {
      id: 'communication',
      name: 'Communication Agent',
      type: 'communication',
      status: 'idle',
      progress: 0,
      currentTask: 'Ready to notify stakeholders',
      lastUpdate: '',
      icon: Bell
    }
  ]);

  const [incidentSteps, setIncidentSteps] = useState<IncidentStep[]>([]);

  const incidentScenario = {
    title: "Critical Database Breach",
    description: "Unauthorized access detected to customer database with potential data exfiltration",
    severity: "CRITICAL",
    initialTrigger: "Anomalous SQL queries detected on customer-db-prod CloudSQL instance"
  };

  const responseWorkflow: Omit<IncidentStep, 'status' | 'timestamp' | 'duration'>[] = [
    {
      id: 'step-1',
      agent: 'orchestrator',
      action: 'Initialize Response',
      details: 'Receive incident alert and coordinate agent responses',
      output: {
        session_id: 'INC-2024-001947',
        priority: 'P1-CRITICAL',
        stakeholders: ['Security Team', 'Database Team', 'Legal Team']
      }
    },
    {
      id: 'step-2',
      agent: 'detection',
      action: 'Threat Assessment',
      details: 'Analyze security logs and identify indicators of compromise',
      output: {
        threats_detected: 3,
        confidence: 0.94,
        attack_vectors: ['SQL Injection', 'Credential Stuffing', 'Lateral Movement'],
        affected_systems: ['customer-db-prod', 'web-app-01', 'auth-service']
      }
    },
    {
      id: 'step-3',
      agent: 'analysis',
      action: 'Deep Analysis',
      details: 'Correlate events, determine blast radius, and assess business impact',
      output: {
        timeline: '2024-01-15 14:23:00 - First malicious query detected',
        blast_radius: '450,000 customer records potentially accessed',
        business_impact: '$15M+ estimated cost including fines and remediation',
        mitre_tactics: ['Initial Access', 'Credential Access', 'Exfiltration']
      }
    },
    {
      id: 'step-4',
      agent: 'remediation',
      action: 'Immediate Response',
      details: 'Execute automated containment and mitigation actions',
      output: {
        actions_taken: [
          'Revoked compromised service account credentials',
          'Blocked malicious IP ranges at firewall',
          'Enabled enhanced logging on database',
          'Triggered backup verification process'
        ],
        success_rate: '100%',
        containment_time: '4.2 minutes'
      }
    },
    {
      id: 'step-5',
      agent: 'communication',
      action: 'Stakeholder Notification',
      details: 'Alert teams and prepare compliance reporting',
      output: {
        notifications_sent: 12,
        escalation_level: 'Executive',
        compliance_alerts: ['GDPR', 'CCPA', 'SOX'],
        estimated_notification_window: '72 hours per GDPR requirements'
      }
    }
  ];

  const startIncidentResponse = async () => {
    setIsRunning(true);
    setCurrentStep(0);
    setIncidentSteps([]);

    // Update orchestrator
    updateAgent('orchestrator', 'active', 10, 'Initializing incident response...');

    // Execute workflow steps
    for (let i = 0; i < responseWorkflow.length; i++) {
      const step = responseWorkflow[i];
      if (!step) continue;
      
      const newStep: IncidentStep = {
        id: step.id,
        agent: step.agent,
        action: step.action,
        details: step.details,
        output: step.output,
        status: 'running',
        timestamp: new Date().toISOString()
      };

      // Add step and update display
      setIncidentSteps(prev => [...prev, newStep]);
      setCurrentStep(i);

      // Update agent status
      updateAgent(step.agent, 'active', 0, step.action);

      // Simulate processing time
      const processingTime = 2000 + Math.random() * 3000;
      await new Promise(resolve => setTimeout(resolve, processingTime));

      // Complete the step
      const completedStep: IncidentStep = {
        ...newStep,
        status: 'completed',
        duration: Math.round(processingTime / 1000 * 10) / 10,
        output: step.output
      };

      setIncidentSteps(prev => 
        prev.map((s, idx) => idx === i ? completedStep : s)
      );

      updateAgent(step.agent, 'completed', 100, `Completed: ${step.action}`);

      // Brief pause between steps
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    // Final status update
    updateAgent('orchestrator', 'completed', 100, 'Incident response completed successfully');
    setIsRunning(false);
  };

  const updateAgent = (agentId: string, status: Agent['status'], progress: number, task: string) => {
    setAgents(prev => prev.map(agent => 
      agent.id === agentId 
        ? { 
            ...agent, 
            status, 
            progress, 
            currentTask: task,
            lastUpdate: new Date().toLocaleTimeString()
          }
        : agent
    ));
  };

  const getAgentStatusColor = (status: Agent['status']) => {
    switch (status) {
      case 'active': return 'text-blue-500 bg-blue-500/10 border-blue-500/20';
      case 'completed': return 'text-green-500 bg-green-500/10 border-green-500/20';
      case 'error': return 'text-red-500 bg-red-500/10 border-red-500/20';
      default: return 'text-gray-500 bg-gray-500/10 border-gray-500/20';
    }
  };

  const getStepStatusColor = (status: IncidentStep['status']) => {
    switch (status) {
      case 'running': return 'text-blue-500 bg-blue-500/10 border-blue-500/20';
      case 'completed': return 'text-green-500 bg-green-500/10 border-green-500/20';
      case 'failed': return 'text-red-500 bg-red-500/10 border-red-500/20';
      default: return 'text-gray-500 bg-gray-500/10 border-gray-500/20';
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <section className="relative pt-24 pb-12">
        <div className="container mx-auto px-4">
          <Link href="/demos" className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground mb-6">
            <ArrowLeft className="w-4 h-4" />
            Back to Demos
          </Link>
          
          <div className="flex items-center gap-4 mb-6">
            <div className="p-3 bg-primary/10 rounded-lg">
              <Bot className="w-8 h-8 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Multi-Agent Incident Response</h1>
              <p className="text-muted-foreground">Autonomous agents orchestrating end-to-end security incident handling</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              Google ADK Agents
            </span>
            <span>•</span>
            <span>Real-time Collaboration</span>
            <span>•</span>
            <span>Automated Remediation</span>
          </div>
        </div>
      </section>

      <div className="container mx-auto px-4 pb-20">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Control Panel */}
          <div className="lg:col-span-1">
            <div className="bg-card border border-border rounded-lg p-6 space-y-6">
              <h2 className="text-xl font-semibold">Incident Scenario</h2>
              
              <div className="space-y-4">
                <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="w-5 h-5 text-red-500" />
                    <span className="font-medium text-red-500">{incidentScenario.severity}</span>
                  </div>
                  <h3 className="font-semibold mb-2">{incidentScenario.title}</h3>
                  <p className="text-sm text-muted-foreground mb-3">{incidentScenario.description}</p>
                  <div className="text-xs text-muted-foreground">
                    <strong>Initial Trigger:</strong> {incidentScenario.initialTrigger}
                  </div>
                </div>

                <button
                  onClick={startIncidentResponse}
                  disabled={isRunning}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  <Play className="w-4 h-4" />
                  {isRunning ? 'Response in Progress...' : 'Trigger Incident Response'}
                </button>
              </div>

              {/* Agent Status */}
              <div className="space-y-3">
                <h3 className="font-medium">Agent Status</h3>
                {agents.map((agent) => {
                  const Icon = agent.icon;
                  return (
                    <div key={agent.id} className="p-3 bg-muted/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Icon className="w-4 h-4" />
                        <span className="font-medium text-sm">{agent.name}</span>
                        <span className={`px-2 py-1 text-xs rounded-full border ${getAgentStatusColor(agent.status)}`}>
                          {agent.status}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground mb-2">{agent.currentTask}</div>
                      {agent.status === 'active' && (
                        <div className="w-full bg-muted rounded-full h-1">
                          <div 
                            className="bg-primary h-1 rounded-full transition-all duration-300"
                            style={{ width: `${agent.progress}%` }}
                          />
                        </div>
                      )}
                      {agent.lastUpdate && (
                        <div className="text-xs text-muted-foreground mt-1">
                          Last update: {agent.lastUpdate}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Response Timeline */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-card border border-border rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-6">Response Timeline</h2>
              
              {incidentSteps.length === 0 && !isRunning && (
                <div className="text-center py-12 text-muted-foreground">
                  <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Click "Trigger Incident Response" to begin the demonstration</p>
                </div>
              )}

              <div className="space-y-4">
                {incidentSteps.map((step, index) => (
                  <div key={step.id} className="relative">
                    {/* Timeline connector */}
                    {index < incidentSteps.length - 1 && (
                      <div className="absolute left-6 top-12 w-0.5 h-8 bg-border" />
                    )}
                    
                    <div className="flex gap-4">
                      <div className={`flex-shrink-0 w-12 h-12 rounded-full border-2 flex items-center justify-center ${
                        step.status === 'completed' ? 'bg-green-500/10 border-green-500/20' :
                        step.status === 'running' ? 'bg-blue-500/10 border-blue-500/20 animate-pulse' :
                        'bg-muted border-border'
                      }`}>
                        {step.status === 'completed' ? (
                          <CheckCircle className="w-5 h-5 text-green-500" />
                        ) : step.status === 'running' ? (
                          <div className="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <Clock className="w-5 h-5 text-muted-foreground" />
                        )}
                      </div>
                      
                      <div className="flex-1 pb-6">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-medium">{step.action}</h3>
                          <span className={`px-2 py-1 text-xs rounded-full border ${getStepStatusColor(step.status)}`}>
                            {step.status}
                          </span>
                          {step.duration && (
                            <span className="text-xs text-muted-foreground">
                              {step.duration}s
                            </span>
                          )}
                        </div>
                        
                        <p className="text-sm text-muted-foreground mb-3">{step.details}</p>
                        
                        <div className="text-xs text-muted-foreground mb-3">
                          Agent: <span className="font-medium capitalize">{step.agent}</span> • 
                          Started: {new Date(step.timestamp).toLocaleTimeString()}
                        </div>

                        {/* Output Details */}
                        {step.output && step.status === 'completed' && (
                          <div className="bg-muted/30 rounded-lg p-4 space-y-3">
                            <h4 className="font-medium text-sm">Output:</h4>
                            {Object.entries(step.output).map(([key, value]) => (
                              <div key={key} className="text-sm">
                                <span className="font-medium capitalize text-muted-foreground">
                                  {key.replace(/_/g, ' ')}:
                                </span>
                                <div className="mt-1">
                                  {Array.isArray(value) ? (
                                    <ul className="list-disc list-inside space-y-1 text-xs">
                                      {value.map((item, idx) => (
                                        <li key={idx}>{item}</li>
                                      ))}
                                    </ul>
                                  ) : typeof value === 'object' ? (
                                    <pre className="text-xs bg-background rounded p-2 overflow-x-auto">
                                      {JSON.stringify(value, null, 2)}
                                    </pre>
                                  ) : (
                                    <span className="text-xs">{String(value)}</span>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Technical Architecture */}
        <div className="mt-12 bg-muted/30 rounded-lg p-8">
          <h2 className="text-2xl font-bold mb-6">ADK Agent Architecture</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-semibold mb-4">Agent Hierarchy</h3>
              <div className="space-y-3 text-sm font-mono">
                <div className="pl-0">SentinelOpsMultiAgent (ParallelAgent)</div>
                <div className="pl-4">├── OrchestratorAgent (SequentialAgent)</div>
                <div className="pl-8">├── DetectionAgent (LlmAgent)</div>
                <div className="pl-8">├── AnalysisAgent (LlmAgent)</div>
                <div className="pl-8">├── RemediationAgent (LlmAgent)</div>
                <div className="pl-8">└── CommunicationAgent (LlmAgent)</div>
              </div>
              
              <h3 className="text-lg font-semibold mb-4 mt-6">ADK Features</h3>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Multi-agent collaboration patterns</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Built-in Gemini integration</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Session persistence with Firestore</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Tool validation and schema enforcement</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Cloud Trace and Logging integration</span>
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-4">Try the Real Implementation</h3>
              <div className="space-y-3">
                <CopyText value="python demos/demo_sentinelops.py" />
                <CopyText value="python src/agents/orchestrator_agent.py" />
                <p className="text-xs text-muted-foreground">
                  Execute these commands to run the actual SentinelOps multi-agent system with real Google ADK integration.
                </p>
              </div>
              
              <h3 className="text-lg font-semibold mb-4 mt-6">Real GCP Services</h3>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Firestore for agent session state</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Cloud Trace for agent performance</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Secret Manager for credentials</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>BigQuery for incident storage</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 