"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield,
  AlertTriangle,
  TrendingUp,
  Activity,
  Users,
  Clock,
  CheckCircle,
  XCircle,
  Eye,
  Zap,
  Globe,
  Server,
  Database,
  Target,
  Brain,
  ArrowRight,
  AlertCircle,
  Play,
  Pause,
  RotateCcw,
  Settings,
  Filter,
  Search,
  MapPin,
  Wifi,
  HardDrive,
  Cpu,
  Network,
  Lock
} from 'lucide-react';

interface ThreatEvent {
  id: string;
  timestamp: Date;
  type: 'login_anomaly' | 'privilege_escalation' | 'data_exfiltration' | 'malware_detected' | 'policy_violation';
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'detecting' | 'analyzing' | 'responding' | 'resolved' | 'escalated';
  source: string;
  target: string;
  description: string;
  agentResponse: string[];
  location: string;
  user?: string;
  riskScore: number;
}

interface Agent {
  id: string;
  name: string;
  type: 'detection' | 'analysis' | 'response' | 'compliance';
  status: 'active' | 'busy' | 'idle';
  currentTask?: string;
  performance: number;
  alertsProcessed: number;
}

interface SecurityMetrics {
  threatsDetected: number;
  threatsBlocked: number;
  averageResponseTime: string;
  falsePositiveRate: string;
  complianceScore: number;
  systemHealth: number;
}

export default function SOCDashboard() {
  const [isLive, setIsLive] = useState(true);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [threatEvents, setThreatEvents] = useState<ThreatEvent[]>([]);
  const [agents, setAgents] = useState<Agent[]>([
    {
      id: 'agent-1',
      name: 'Login Sentinel',
      type: 'detection',
      status: 'active',
      currentTask: 'Monitoring authentication patterns',
      performance: 98.5,
      alertsProcessed: 247
    },
    {
      id: 'agent-2', 
      name: 'Privilege Guardian',
      type: 'detection',
      status: 'active',
      currentTask: 'Scanning IAM policy changes',
      performance: 97.2,
      alertsProcessed: 189
    },
    {
      id: 'agent-3',
      name: 'Data Shield',
      type: 'detection', 
      status: 'active',
      currentTask: 'Analyzing network traffic patterns',
      performance: 99.1,
      alertsProcessed: 312
    },
    {
      id: 'agent-4',
      name: 'Gemini Analyst',
      type: 'analysis',
      status: 'busy',
      currentTask: 'Processing threat correlation analysis',
      performance: 96.8,
      alertsProcessed: 156
    },
    {
      id: 'agent-5',
      name: 'Auto Responder',
      type: 'response',
      status: 'idle',
      performance: 94.3,
      alertsProcessed: 78
    },
    {
      id: 'agent-6',
      name: 'Compliance Monitor',
      type: 'compliance',
      status: 'active',
      currentTask: 'SOC 2 audit trail validation',
      performance: 99.7,
      alertsProcessed: 445
    }
  ]);

  const [metrics, setMetrics] = useState<SecurityMetrics>({
    threatsDetected: 847,
    threatsBlocked: 831,
    averageResponseTime: '43s',
    falsePositiveRate: '0.3%',
    complianceScore: 98.2,
    systemHealth: 99.1
  });

  const [selectedThreat, setSelectedThreat] = useState<ThreatEvent | null>(null);
  const [auditLogs, setAuditLogs] = useState<string[]>([]);

  // Simulate real-time threat detection
  useEffect(() => {
    if (!isLive) return;

    const interval = setInterval(() => {
      setCurrentTime(new Date());
      
      // Generate new threat events randomly
      if (Math.random() < 0.3) {
        generateThreatEvent();
      }

      // Update existing threat events
      setThreatEvents(prev => prev.map(event => {
        if (event.status === 'detecting' && Math.random() < 0.4) {
          return { ...event, status: 'analyzing' };
        }
        if (event.status === 'analyzing' && Math.random() < 0.3) {
          return { ...event, status: 'responding' };
        }
        if (event.status === 'responding' && Math.random() < 0.5) {
          return { ...event, status: 'resolved' };
        }
        return event;
      }));

      // Update metrics
      setMetrics(prev => ({
        ...prev,
        threatsDetected: prev.threatsDetected + Math.floor(Math.random() * 3),
        threatsBlocked: prev.threatsBlocked + Math.floor(Math.random() * 2),
        systemHealth: 98 + Math.random() * 2
      }));

    }, 2000);

    return () => clearInterval(interval);
  }, [isLive]);

  const generateThreatEvent = () => {
    const threatTypes = [
      {
        type: 'login_anomaly' as const,
        severity: (['medium', 'high'] as const)[Math.floor(Math.random() * 2)],
        source: '89.34.56.' + Math.floor(Math.random() * 255),
        target: 'login.sentinelops.com',
        description: 'Suspicious login attempt from unusual geographic location',
        location: (['North Korea', 'Iran', 'Russia', 'Anonymous Proxy'] as const)[Math.floor(Math.random() * 4)],
        user: (['john.doe@company.com', 'admin@company.com', 'service@company.com'] as const)[Math.floor(Math.random() * 3)],
        riskScore: 65 + Math.random() * 30
      },
      {
        type: 'privilege_escalation' as const,
        severity: (['high', 'critical'] as const)[Math.floor(Math.random() * 2)],
        source: 'internal-user-' + Math.floor(Math.random() * 100),
        target: 'IAM Service',
        description: 'Unauthorized privilege escalation attempt detected',
        location: 'Internal Network',
        user: 'temp.user@company.com',
        riskScore: 80 + Math.random() * 20
      },
      {
        type: 'data_exfiltration' as const,
        severity: 'critical' as const,
        source: 'database-server-01',
        target: '45.67.89.' + Math.floor(Math.random() * 255),
        description: 'Large volume data transfer to external IP address',
        location: 'Data Center',
        riskScore: 90 + Math.random() * 10
      }
    ];

    const threat = threatTypes[Math.floor(Math.random() * threatTypes.length)];
    if (!threat) return;
    
    const newEvent: ThreatEvent = {
      id: 'threat-' + Date.now(),
      timestamp: new Date(),
      type: threat.type,
      severity: threat.severity,
      source: threat.source,
      target: threat.target,
      description: threat.description,
      location: threat.location || 'Unknown',
      user: threat.user,
      riskScore: threat.riskScore,
      status: 'detecting',
      agentResponse: [
        `[${new Date().toLocaleTimeString()}] Agent initiated threat analysis`,
        `[${new Date().toLocaleTimeString()}] Gathering additional context...`
      ]
    };

    setThreatEvents(prev => [newEvent, ...prev.slice(0, 9)]);
    addAuditLog(`New ${threat.severity.toUpperCase()} threat detected: ${threat.description}`);
  };

  const addAuditLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setAuditLogs(prev => [`[${timestamp}] ${message}`, ...prev.slice(0, 19)]);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return 'text-blue-400';
      case 'medium': return 'text-yellow-400';  
      case 'high': return 'text-orange-400';
      case 'critical': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'detecting': return <Eye className="w-4 h-4 text-yellow-400" />;
      case 'analyzing': return <Brain className="w-4 h-4 text-blue-400" />;
      case 'responding': return <Zap className="w-4 h-4 text-orange-400" />;
      case 'resolved': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'escalated': return <AlertTriangle className="w-4 h-4 text-red-400" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="min-h-screen bg-black text-white p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">SentinelOps SOC Dashboard</h1>
          <p className="text-gray-400">Real-time Security Operations Center</p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-sm text-gray-400">Current Time</div>
            <div className="font-mono text-green-400">{currentTime.toLocaleString()}</div>
          </div>
          
          <button
            onClick={() => setIsLive(!isLive)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
              isLive 
                ? 'bg-green-600 hover:bg-green-700 text-white' 
                : 'bg-gray-600 hover:bg-gray-700 text-white'
            }`}
          >
            {isLive ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {isLive ? 'Live' : 'Paused'}
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        <motion.div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <Target className="w-4 h-4 text-red-400" />
            <span className="text-xs text-gray-400">Threats Detected</span>
          </div>
          <div className="text-2xl font-bold text-white">{metrics.threatsDetected.toLocaleString()}</div>
        </motion.div>

        <motion.div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <Shield className="w-4 h-4 text-green-400" />
            <span className="text-xs text-gray-400">Threats Blocked</span>
          </div>
          <div className="text-2xl font-bold text-white">{metrics.threatsBlocked.toLocaleString()}</div>
        </motion.div>

        <motion.div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <Clock className="w-4 h-4 text-blue-400" />
            <span className="text-xs text-gray-400">Avg Response</span>
          </div>
          <div className="text-2xl font-bold text-white">{metrics.averageResponseTime}</div>
        </motion.div>

        <motion.div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className="w-4 h-4 text-yellow-400" />
            <span className="text-xs text-gray-400">False Positive</span>
          </div>
          <div className="text-2xl font-bold text-white">{metrics.falsePositiveRate}</div>
        </motion.div>

        <motion.div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle className="w-4 h-4 text-green-400" />
            <span className="text-xs text-gray-400">Compliance</span>
          </div>
          <div className="text-2xl font-bold text-white">{metrics.complianceScore}%</div>
        </motion.div>

        <motion.div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <Activity className="w-4 h-4 text-green-400" />
            <span className="text-xs text-gray-400">System Health</span>
          </div>
          <div className="text-2xl font-bold text-white">{metrics.systemHealth.toFixed(1)}%</div>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Threats */}
        <div className="lg:col-span-2">
          <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-white">Active Threat Events</h2>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                <span className="text-sm text-gray-400">{isLive ? 'Live' : 'Paused'}</span>
              </div>
            </div>
            
            <div className="space-y-3 max-h-96 overflow-y-auto">
              <AnimatePresence>
                {threatEvents.map((threat) => (
                  <motion.div
                    key={threat.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    className={`p-4 border rounded-lg cursor-pointer transition-all hover:border-green-400/50 ${
                      selectedThreat?.id === threat.id ? 'border-green-400 bg-green-400/10' : 'border-gray-600 bg-gray-800/50'
                    }`}
                    onClick={() => setSelectedThreat(threat)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        {getStatusIcon(threat.status)}
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-white">{threat.description}</span>
                            <span className={`text-xs px-2 py-1 rounded-full ${getSeverityColor(threat.severity)} bg-current bg-opacity-20`}>
                              {threat.severity.toUpperCase()}
                            </span>
                          </div>
                          <div className="text-sm text-gray-400 mb-2">
                            {threat.source} → {threat.target}
                          </div>
                          <div className="flex items-center gap-4 text-xs text-gray-400">
                            <span>{threat.timestamp.toLocaleTimeString()}</span>
                            <span>{threat.location}</span>
                            {threat.user && <span>{threat.user}</span>}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium text-white">Risk: {threat.riskScore.toFixed(0)}</div>
                        <div className="text-xs text-gray-400 capitalize">{threat.status}</div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* Agent Status */}
        <div>
          <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-white mb-4">Security Agents</h2>
            
            <div className="space-y-3">
              {agents.map((agent) => (
                <div key={agent.id} className="p-3 border border-gray-600 rounded-lg bg-gray-800/50">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium text-white">{agent.name}</div>
                    <div className={`w-2 h-2 rounded-full ${
                      agent.status === 'active' ? 'bg-green-400' :
                      agent.status === 'busy' ? 'bg-yellow-400' : 'bg-gray-400'
                    }`}></div>
                  </div>
                  <div className="text-xs text-gray-400 mb-2 capitalize">{agent.type}</div>
                  {agent.currentTask && (
                    <div className="text-xs text-gray-300 mb-2">{agent.currentTask}</div>
                  )}
                  <div className="flex justify-between text-xs text-gray-400">
                    <span>Performance: {agent.performance}%</span>
                    <span>Alerts: {agent.alertsProcessed}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* System Status */}
          <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-white mb-4">System Status</h2>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Server className="w-4 h-4 text-green-400" />
                  <span className="text-sm text-white">Detection Engine</span>
                </div>
                <span className="text-sm text-green-400">Online</span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Brain className="w-4 h-4 text-green-400" />
                  <span className="text-sm text-white">AI Analysis</span>
                </div>
                <span className="text-sm text-green-400">Active</span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-green-400" />
                  <span className="text-sm text-white">Data Pipeline</span>
                </div>
                <span className="text-sm text-green-400">Healthy</span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Lock className="w-4 h-4 text-green-400" />
                  <span className="text-sm text-white">Compliance</span>
                </div>
                <span className="text-sm text-green-400">Validated</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Threat Detail Panel */}
      {selectedThreat && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 bg-gray-900/50 border border-gray-700 rounded-lg p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Threat Analysis</h2>
            <button
              onClick={() => setSelectedThreat(null)}
              className="text-gray-400 hover:text-white"
            >
              <XCircle className="w-5 h-5" />
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-medium text-white mb-3">Threat Details</h3>
              <div className="space-y-2 text-sm">
                <div><span className="text-gray-400">ID:</span> <span className="text-white font-mono">{selectedThreat.id}</span></div>
                <div><span className="text-gray-400">Type:</span> <span className="text-white capitalize">{selectedThreat.type.replace('_', ' ')}</span></div>
                <div><span className="text-gray-400">Severity:</span> <span className={getSeverityColor(selectedThreat.severity)}>{selectedThreat.severity.toUpperCase()}</span></div>
                <div><span className="text-gray-400">Status:</span> <span className="text-white capitalize">{selectedThreat.status}</span></div>
                <div><span className="text-gray-400">Risk Score:</span> <span className="text-white">{selectedThreat.riskScore.toFixed(1)}/100</span></div>
                <div><span className="text-gray-400">Location:</span> <span className="text-white">{selectedThreat.location}</span></div>
                {selectedThreat.user && <div><span className="text-gray-400">User:</span> <span className="text-white">{selectedThreat.user}</span></div>}
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-medium text-white mb-3">Agent Response Log</h3>
              <div className="bg-black/50 border border-gray-700 rounded p-3 font-mono text-xs max-h-40 overflow-y-auto">
                {selectedThreat.agentResponse.map((log, index) => (
                  <div key={index} className="text-green-400 mb-1">{log}</div>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Audit Log */}
      <div className="mt-6 bg-gray-900/50 border border-gray-700 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Security Audit Log</h2>
        <div className="bg-black/50 border border-gray-700 rounded p-4 font-mono text-xs max-h-48 overflow-y-auto">
          {auditLogs.map((log, index) => (
            <div key={index} className="text-green-400 mb-1">{log}</div>
          ))}
        </div>
      </div>
    </div>
  );
} 