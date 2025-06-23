"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Zap, 
  Shield, 
  Brain,
  Terminal,
  Server,
  Cloud,
  Lock,
  AlertTriangle,
  CheckCircle,
  Clock,
  Activity,
  Settings,
  Code,
  Cpu,
  Database,
  Network,
  FileText,
  Eye,
  Target,
  Gauge,
  PlayCircle,
  StopCircle,
  RefreshCw
} from 'lucide-react';

interface DevOpsEngineerDemoProps {
  scenario: 'auto-remediation' | 'infrastructure' | 'ai-analysis';
}

interface RemediationAction {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  duration: number;
  startTime?: Date;
  endTime?: Date;
  result?: string;
  commands?: string[];
}

interface InfrastructureComponent {
  id: string;
  name: string;
  type: 'compute' | 'network' | 'storage' | 'security';
  status: 'healthy' | 'warning' | 'critical' | 'protected';
  metrics: {
    cpu?: number;
    memory?: number;
    network?: number;
    security_score?: number;
  };
  policies: string[];
  lastChecked: Date;
}

interface AIAnalysis {
  id: string;
  title: string;
  confidence: number;
  category: 'threat' | 'anomaly' | 'optimization' | 'prediction';
  description: string;
  evidence: string[];
  recommendations: string[];
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

const DevOpsEngineerDemo: React.FC<DevOpsEngineerDemoProps> = ({ scenario }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [currentAction, setCurrentAction] = useState<number>(0);
  const [actions, setActions] = useState<RemediationAction[]>([]);
  const [infrastructure, setInfrastructure] = useState<InfrastructureComponent[]>([]);
  const [analyses, setAnalyses] = useState<AIAnalysis[]>([]);
  const [terminalOutput, setTerminalOutput] = useState<string[]>([]);

  // Sample data
  const remediationScenario = {
    title: 'Automated Threat Remediation',
    description: 'Detecting and automatically remediating a privilege escalation attack',
    actions: [
      {
        id: '1',
        name: 'Detect Threat',
        description: 'Analyzing IAM policy changes for unauthorized escalation',
        status: 'pending' as const,
        duration: 2000,
        commands: ['gcloud logging read "resource.type=gce_instance"', 'grep "roles/owner" audit.log']
      },
      {
        id: '2',
        name: 'Isolate Affected Resources',
        description: 'Quarantining compromised service account and resources',
        status: 'pending' as const,
        duration: 1500,
        commands: ['gcloud iam service-accounts disable sa@project.iam', 'gcloud compute instances stop compromised-instance']
      },
      {
        id: '3',
        name: 'Deploy Firewall Rules',
        description: 'Blocking malicious traffic patterns automatically',
        status: 'pending' as const,
        duration: 3000,
        commands: ['gcloud compute firewall-rules create block-suspicious --deny tcp:22 --source-ranges 175.45.176.0/24']
      },
      {
        id: '4',
        name: 'Revoke Permissions',
        description: 'Rolling back unauthorized permission changes',
        status: 'pending' as const,
        duration: 2500,
        commands: ['gcloud projects remove-iam-policy-binding --member=serviceAccount:sa@project.iam --role=roles/owner']
      },
      {
        id: '5',
        name: 'Notify Security Team',
        description: 'Sending automated incident report to security team',
        status: 'pending' as const,
        duration: 1000,
        commands: ['curl -X POST /api/notify -d "incident_id=INC-001&severity=HIGH"']
      }
    ]
  };

  const infrastructureComponents: InfrastructureComponent[] = [
    {
      id: 'web-tier',
      name: 'Web Application Tier',
      type: 'compute',
      status: 'protected',
      metrics: { cpu: 45, memory: 67, security_score: 94 },
      policies: ['DDoS Protection', 'WAF Rules', 'Rate Limiting'],
      lastChecked: new Date()
    },
    {
      id: 'database',
      name: 'Production Database',
      type: 'storage',
      status: 'healthy',
      metrics: { cpu: 23, memory: 34, security_score: 98 },
      policies: ['Encryption at Rest', 'Access Control', 'Backup Retention'],
      lastChecked: new Date()
    },
    {
      id: 'vpc-network',
      name: 'VPC Network',
      type: 'network',
      status: 'warning',
      metrics: { network: 78, security_score: 89 },
      policies: ['Private Subnets', 'Network Segmentation', 'Traffic Monitoring'],
      lastChecked: new Date()
    },
    {
      id: 'iam-service',
      name: 'Identity & Access Management',
      type: 'security',
      status: 'critical',
      metrics: { security_score: 76 },
      policies: ['MFA Required', 'Principle of Least Privilege', 'Regular Audit'],
      lastChecked: new Date()
    }
  ];

  const aiAnalysisData: AIAnalysis[] = [
    {
      id: 'analysis-1',
      title: 'Privilege Escalation Pattern Detected',
      confidence: 94,
      category: 'threat',
      description: 'AI detected suspicious pattern of privilege escalation attempts across multiple service accounts',
      evidence: [
        'Unusual IAM policy modifications outside business hours',
        'Service account elevation from viewer to owner roles',
        'Multiple failed authentication attempts preceding escalation',
        'Geographic anomaly: requests originating from blacklisted IP ranges'
      ],
      recommendations: [
        'Immediately revoke elevated permissions for affected service accounts',
        'Enable additional monitoring for IAM policy changes',
        'Implement break-glass procedures for emergency access',
        'Review and update service account naming conventions'
      ],
      severity: 'CRITICAL'
    },
    {
      id: 'analysis-2',
      title: 'Network Traffic Anomaly',
      confidence: 87,
      category: 'anomaly',
      description: 'Gemini AI identified unusual network traffic patterns suggesting potential data exfiltration',
      evidence: [
        'Data transfer volume 450% above baseline during off-hours',
        'Traffic to previously unseen external IP addresses',
        'Encrypted tunneling protocols detected in unusual contexts',
        'Pattern matches known APT data exfiltration techniques'
      ],
      recommendations: [
        'Deploy additional network monitoring on affected subnets',
        'Implement DLP (Data Loss Prevention) policies',
        'Review and restrict egress traffic rules',
        'Enable advanced threat protection on network gateways'
      ],
      severity: 'HIGH'
    },
    {
      id: 'analysis-3',
      title: 'Infrastructure Optimization Opportunity',
      confidence: 91,
      category: 'optimization',
      description: 'AI analysis suggests security and cost optimization opportunities in current infrastructure',
      evidence: [
        'Underutilized compute resources with overprivileged access',
        'Security policies not aligned with actual usage patterns',
        'Legacy configurations increasing attack surface',
        'Redundant security controls causing performance impact'
      ],
      recommendations: [
        'Right-size compute instances based on actual usage',
        'Consolidate and optimize security policy rules',
        'Migrate legacy services to modern secure architectures',
        'Implement automated scaling based on security posture'
      ],
      severity: 'MEDIUM'
    }
  ];

  const runRemediation = async () => {
    setIsRunning(true);
    setActions(remediationScenario.actions);
    setTerminalOutput(['Starting automated remediation sequence...', '']);

    for (let i = 0; i < remediationScenario.actions.length; i++) {
      setCurrentAction(i);
      
      // Update action status to running
      setActions(prev => prev.map((action, idx) => 
        idx === i ? { ...action, status: 'running', startTime: new Date() } : action
      ));

      // Add terminal output
      const currentAction = remediationScenario.actions?.[i];
      if (currentAction) {
        setTerminalOutput(prev => [
          ...prev,
          `[${new Date().toLocaleTimeString()}] Executing: ${currentAction.name}`,
          ...(currentAction.commands || []).map(cmd => `$ ${cmd}`),
          ''
        ]);

        // Wait for action duration
        await new Promise(resolve => setTimeout(resolve, currentAction.duration));
      }

      // Complete action
      setActions(prev => prev.map((action, idx) => 
        idx === i ? { 
          ...action, 
          status: 'completed', 
          endTime: new Date(),
          result: 'Success: Action completed successfully'
        } : action
      ));

      if (currentAction) {
        setTerminalOutput(prev => [
          ...prev,
          `✓ ${currentAction.name} completed successfully`,
          ''
        ]);
      }
    }

    setTerminalOutput(prev => [
      ...prev,
      '🎉 Automated remediation sequence completed successfully!',
      'All threats have been contained and security posture restored.',
      ''
    ]);

    setIsRunning(false);
  };

  const resetDemo = () => {
    setIsRunning(false);
    setCurrentAction(0);
    setActions([]);
    setTerminalOutput([]);
  };

  useEffect(() => {
    if (scenario === 'infrastructure') {
      setInfrastructure(infrastructureComponents);
    } else if (scenario === 'ai-analysis') {
      setAnalyses(aiAnalysisData);
    }
  }, [scenario]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': case 'protected': case 'completed': return 'text-green-400 bg-green-500/10';
      case 'warning': case 'running': return 'text-yellow-400 bg-yellow-500/10';
      case 'critical': case 'failed': return 'text-red-400 bg-red-500/10';
      case 'pending': return 'text-gray-400 bg-gray-500/10';
      default: return 'text-gray-400 bg-gray-500/10';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'text-red-400 bg-red-500/10 border-red-500/20';
      case 'HIGH': return 'text-orange-400 bg-orange-500/10 border-orange-500/20';
      case 'MEDIUM': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
      case 'LOW': return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
      default: return 'text-gray-400 bg-gray-500/10 border-gray-500/20';
    }
  };

  const renderAutoRemediation = () => (
    <div className="space-y-6">
      {/* Control Panel */}
      <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10">
        <div>
          <h3 className="text-lg font-semibold text-white">{remediationScenario.title}</h3>
          <p className="text-sm text-gray-400">{remediationScenario.description}</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={resetDemo}
            className="px-4 py-2 text-sm bg-white/10 hover:bg-white/20 rounded-lg transition-colors text-white"
          >
            Reset
          </button>
          <button
            onClick={runRemediation}
            disabled={isRunning}
            className="px-4 py-2 text-sm bg-green-500 hover:bg-green-600 disabled:bg-gray-500 rounded-lg transition-colors text-white flex items-center gap-2"
          >
            {isRunning ? (
              <>
                <Activity className="w-4 h-4 animate-spin" />
                Running...
              </>
            ) : (
              <>
                <PlayCircle className="w-4 h-4" />
                Start Remediation
              </>
            )}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Action Pipeline */}
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-white flex items-center gap-2">
            <Zap className="w-5 h-5 text-yellow-400" />
            Remediation Pipeline
          </h4>
          
          <div className="space-y-3">
            {actions.map((action, index) => (
              <motion.div
                key={action.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`p-4 rounded-lg border transition-all duration-300 ${
                  action.status === 'running' 
                    ? 'bg-yellow-500/10 border-yellow-500/30' 
                    : action.status === 'completed'
                    ? 'bg-green-500/10 border-green-500/30'
                    : action.status === 'failed'
                    ? 'bg-red-500/10 border-red-500/30'
                    : 'bg-white/5 border-white/10'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {action.status === 'running' && <Activity className="w-4 h-4 text-yellow-400 animate-spin" />}
                    {action.status === 'completed' && <CheckCircle className="w-4 h-4 text-green-400" />}
                    {action.status === 'failed' && <AlertTriangle className="w-4 h-4 text-red-400" />}
                    {action.status === 'pending' && <Clock className="w-4 h-4 text-gray-400" />}
                    <span className="text-white font-medium">{action.name}</span>
                  </div>
                  <div className={`px-2 py-1 text-xs rounded-full ${getStatusColor(action.status)}`}>
                    {action.status.toUpperCase()}
                  </div>
                </div>
                <p className="text-sm text-gray-300 mb-3">{action.description}</p>
                
                {action.result && (
                  <div className="text-xs text-green-400 bg-green-500/10 p-2 rounded">
                    {action.result}
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>

        {/* Terminal Output */}
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-white flex items-center gap-2">
            <Terminal className="w-5 h-5 text-green-400" />
            Command Output
          </h4>
          
          <div className="bg-black/50 rounded-lg p-4 font-mono text-sm border border-white/10">
            <div className="flex items-center gap-2 mb-3 pb-2 border-b border-white/10">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-gray-400 ml-2">sentinel-ops-terminal</span>
            </div>
            <div className="max-h-80 overflow-y-auto space-y-1">
              {terminalOutput.length === 0 ? (
                <div className="text-gray-400">Ready to execute automated remediation...</div>
              ) : (
                terminalOutput.map((line, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: index * 0.05 }}
                    className={line.startsWith('$') ? 'text-blue-400' : 
                              line.startsWith('✓') ? 'text-green-400' :
                              line.startsWith('🎉') ? 'text-yellow-400' : 'text-gray-300'}
                  >
                    {line}
                  </motion.div>
                ))
              )}
              {isRunning && (
                <motion.div
                  animate={{ opacity: [1, 0] }}
                  transition={{ repeat: Infinity, duration: 1 }}
                  className="text-green-400"
                >
                  ▋
                </motion.div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderInfrastructure = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10">
        <div>
          <h3 className="text-lg font-semibold text-white">Infrastructure Security Monitoring</h3>
          <p className="text-sm text-gray-400">Real-time security posture and policy enforcement</p>
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2 text-sm bg-blue-500 hover:bg-blue-600 rounded-lg transition-colors text-white">
            Scan Infrastructure
          </button>
          <button className="px-4 py-2 text-sm bg-green-500 hover:bg-green-600 rounded-lg transition-colors text-white">
            Apply Policies
          </button>
        </div>
      </div>

      {/* Infrastructure Components */}
      <div className="space-y-4">
        <h4 className="text-lg font-semibold text-white flex items-center gap-2">
          <Shield className="w-5 h-5 text-blue-400" />
          Infrastructure Components
        </h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {infrastructure.map((component, index) => (
            <motion.div
              key={component.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="p-6 bg-white/5 rounded-lg border border-white/10"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  {component.type === 'compute' && <Cpu className="w-5 h-5 text-blue-400" />}
                  {component.type === 'storage' && <Database className="w-5 h-5 text-green-400" />}
                  {component.type === 'network' && <Network className="w-5 h-5 text-purple-400" />}
                  {component.type === 'security' && <Lock className="w-5 h-5 text-red-400" />}
                  <div>
                    <h5 className="text-white font-semibold">{component.name}</h5>
                    <div className="text-xs text-gray-400 capitalize">{component.type}</div>
                  </div>
                </div>
                <div className={`px-2 py-1 text-xs rounded-full ${getStatusColor(component.status)}`}>
                  {component.status.toUpperCase()}
                </div>
              </div>

              {/* Metrics */}
              <div className="space-y-3 mb-4">
                {component.metrics.cpu && (
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-400">CPU Usage</span>
                      <span className="text-white">{component.metrics.cpu}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${component.metrics.cpu > 80 ? 'bg-red-400' : component.metrics.cpu > 60 ? 'bg-yellow-400' : 'bg-green-400'}`}
                        style={{ width: `${component.metrics.cpu}%` }}
                      />
                    </div>
                  </div>
                )}
                
                {component.metrics.memory && (
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-400">Memory Usage</span>
                      <span className="text-white">{component.metrics.memory}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${component.metrics.memory > 80 ? 'bg-red-400' : component.metrics.memory > 60 ? 'bg-yellow-400' : 'bg-green-400'}`}
                        style={{ width: `${component.metrics.memory}%` }}
                      />
                    </div>
                  </div>
                )}

                {component.metrics.security_score && (
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-400">Security Score</span>
                      <span className="text-white">{component.metrics.security_score}/100</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${component.metrics.security_score >= 90 ? 'bg-green-400' : component.metrics.security_score >= 70 ? 'bg-yellow-400' : 'bg-red-400'}`}
                        style={{ width: `${component.metrics.security_score}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Security Policies */}
              <div>
                <div className="text-sm text-gray-400 mb-2">Active Security Policies</div>
                <div className="flex flex-wrap gap-2">
                  {component.policies.map((policy, idx) => (
                    <span key={idx} className="px-2 py-1 text-xs bg-green-500/10 text-green-400 rounded">
                      {policy}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-white/10 text-xs text-gray-400">
                Last checked: {component.lastChecked.toLocaleString()}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderAIAnalysis = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10">
        <div>
          <h3 className="text-lg font-semibold text-white">AI-Powered Security Analysis</h3>
          <p className="text-sm text-gray-400">Gemini AI threat intelligence and recommendations</p>
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2 text-sm bg-purple-500 hover:bg-purple-600 rounded-lg transition-colors text-white">
            Run Analysis
          </button>
          <button className="px-4 py-2 text-sm bg-green-500 hover:bg-green-600 rounded-lg transition-colors text-white">
            Apply Recommendations
          </button>
        </div>
      </div>

      {/* AI Analyses */}
      <div className="space-y-6">
        {analyses.map((analysis, index) => (
          <motion.div
            key={analysis.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.2 }}
            className="p-6 bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-lg border border-purple-500/20"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <Brain className="w-6 h-6 text-purple-400" />
                <div>
                  <h4 className="text-lg font-semibold text-white">{analysis.title}</h4>
                  <div className="flex items-center gap-3 mt-1">
                    <div className={`px-2 py-1 text-xs rounded-full border ${getSeverityColor(analysis.severity)}`}>
                      {analysis.severity}
                    </div>
                    <div className="text-sm text-gray-400 capitalize">{analysis.category}</div>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-purple-400">{analysis.confidence}%</div>
                <div className="text-xs text-gray-400">Confidence</div>
              </div>
            </div>

            <p className="text-gray-300 mb-6">{analysis.description}</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Evidence */}
              <div>
                <h5 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <Eye className="w-4 h-4 text-blue-400" />
                  Evidence
                </h5>
                <div className="space-y-2">
                  {analysis.evidence.map((evidence, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-sm">
                      <div className="w-1.5 h-1.5 bg-blue-400 rounded-full mt-2 flex-shrink-0" />
                      <span className="text-gray-300">{evidence}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recommendations */}
              <div>
                <h5 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <Target className="w-4 h-4 text-green-400" />
                  Recommendations
                </h5>
                <div className="space-y-2">
                  {analysis.recommendations.map((recommendation, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-sm">
                      <div className="w-1.5 h-1.5 bg-green-400 rounded-full mt-2 flex-shrink-0" />
                      <span className="text-gray-300">{recommendation}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 mt-6 pt-4 border-t border-white/10">
              <button className="px-4 py-2 text-sm bg-green-500 hover:bg-green-600 rounded-lg transition-colors text-white">
                Apply Recommendations
              </button>
              <button className="px-4 py-2 text-sm bg-blue-500 hover:bg-blue-600 rounded-lg transition-colors text-white">
                Create Incident
              </button>
              <button className="px-4 py-2 text-sm bg-purple-500 hover:bg-purple-600 rounded-lg transition-colors text-white">
                Deep Analysis
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );

  const renderScenario = () => {
    switch (scenario) {
      case 'auto-remediation':
        return renderAutoRemediation();
      case 'infrastructure':
        return renderInfrastructure();
      case 'ai-analysis':
        return renderAIAnalysis();
      default:
        return renderAutoRemediation();
    }
  };

  return (
    <div className="min-h-[600px]">
      {renderScenario()}
    </div>
  );
};

export default DevOpsEngineerDemo; 