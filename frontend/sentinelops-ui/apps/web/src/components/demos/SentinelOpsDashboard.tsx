"use client";

import React, { useState, useEffect } from 'react';
import { Button } from '@v1/ui/button';
import { Badge } from '@v1/ui/badge';
import { motion } from 'framer-motion';
import { 
  Shield, 
  Activity, 
  AlertTriangle,
  CheckCircle,
  Play,
  TrendingUp,
  TrendingDown,
  Users,
  Clock,
  Target,
  Zap,
  Brain,
  Network,
  Eye,
  Wrench,
  MessageSquare,
  Settings,
  BarChart3,
  Globe,
  Server,
  Database,
  Cpu,
  HardDrive,
  Wifi,
  Lock,
  Unlock,
  FileText,
  Search,
  Filter,
  RefreshCw
} from 'lucide-react';

const SentinelOpsDashboard: React.FC = () => {
  const [activeView, setActiveView] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [selectedTimeframe, setSelectedTimeframe] = useState('24h');
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [agentStatus, setAgentStatus] = useState({
    detection: 'active',
    analysis: 'active', 
    remediation: 'standby',
    communication: 'active',
    orchestrator: 'active'
  });

  const timeframes = [
    { code: '1h', name: 'Last Hour', incidents: 3 },
    { code: '24h', name: 'Last 24 Hours', incidents: 47 },
    { code: '7d', name: 'Last 7 Days', incidents: 312 },
    { code: '30d', name: 'Last 30 Days', incidents: 1247 }
  ];

  const severityLevels = [
    { code: 'all', name: 'All Severities', count: 47 },
    { code: 'critical', name: 'Critical', count: 3, color: 'text-red-400' },
    { code: 'high', name: 'High', count: 8, color: 'text-orange-400' },
    { code: 'medium', name: 'Medium', count: 21, color: 'text-yellow-400' },
    { code: 'low', name: 'Low', count: 15, color: 'text-blue-400' }
  ];

  const dashboardViews = [
    {
      id: 'agent-orchestration',
      title: 'Multi-Agent Orchestration',
      description: 'Real-time coordination between five specialized security agents using Google ADK',
      stats: [
        { label: 'Active Agents', value: '5/5', trend: '100%', icon: <Network className="w-5 h-5" />, color: 'text-green-400' },
        { label: 'Agent Coordination', value: '<5s', trend: '-2.3s', icon: <Zap className="w-5 h-5" />, color: 'text-blue-400' },
        { label: 'ADK Operations', value: '2,847', trend: '+12%', icon: <Cpu className="w-5 h-5" />, color: 'text-purple-400' },
        { label: 'Transfer Success', value: '99.7%', trend: '+0.3%', icon: <CheckCircle className="w-5 h-5" />, color: 'text-green-400' }
      ],
      agents: [
        { 
          name: 'Detection Agent', 
          status: 'active', 
          role: 'Continuous monitoring & threat detection',
          tools: ['RulesEngineTool', 'EventCorrelatorTool', 'QueryBuilderTool'],
          lastActivity: '2s ago',
          performance: '94.7%'
        },
        { 
          name: 'Analysis Agent', 
          status: 'active', 
          role: 'Gemini-powered incident analysis',
          tools: ['GeminiAnalysisTool', 'RecommendationTool', 'RiskScoringTool'],
          lastActivity: '15s ago',
          performance: '89.2%'
        },
        { 
          name: 'Remediation Agent', 
          status: 'standby', 
          role: 'Automated response execution',
          tools: ['BlockIPTool', 'IsolateVMTool', 'RevokeCredentialsTool'],
          lastActivity: '3m ago',
          performance: '97.3%'
        },
        { 
          name: 'Communication Agent', 
          status: 'active', 
          role: 'Stakeholder notifications & reports',
          tools: ['SlackNotificationTool', 'EmailReportTool', 'DashboardUpdateTool'],
          lastActivity: '8s ago',
          performance: '99.1%'
        },
        { 
          name: 'Orchestrator Agent', 
          status: 'active', 
          role: 'Workflow coordination & oversight',
          tools: ['TransferCoordinatorTool', 'WorkflowManagerTool', 'AuditTrailTool'],
          lastActivity: '1s ago',
          performance: '99.8%'
        }
      ]
    },
    {
      id: 'threat-detection',
      title: 'Real-Time Threat Detection',
      description: 'Continuous monitoring of Google Cloud infrastructure with sub-30 second detection',
      stats: [
        { label: 'Events Processed', value: '2.4M', trend: '+18%', icon: <Activity className="w-5 h-5" />, color: 'text-blue-400' },
        { label: 'Detection Speed', value: '<30s', trend: '-12s', icon: <Clock className="w-5 h-5" />, color: 'text-green-400' },
        { label: 'False Positives', value: '1.8%', trend: '-0.5%', icon: <Target className="w-5 h-5" />, color: 'text-purple-400' },
        { label: 'Coverage', value: '100%', trend: '0%', icon: <Shield className="w-5 h-5" />, color: 'text-green-400' }
      ],
      threats: [
        { 
          type: 'Brute Force Attack', 
          severity: 'HIGH', 
          source: '198.51.100.23',
          target: 'web-server-prod-3',
          detected: '23s ago',
          status: 'Analyzing'
        },
        { 
          type: 'Privilege Escalation', 
          severity: 'CRITICAL', 
          source: 'internal',
          target: 'admin-console',
          detected: '2m ago',
          status: 'Remediating'
        },
        { 
          type: 'Data Exfiltration', 
          severity: 'MEDIUM', 
          source: '45.123.67.89',
          target: 'database-cluster-1',
          detected: '5m ago',
          status: 'Resolved'
        },
        { 
          type: 'Malware Execution', 
          severity: 'HIGH', 
          source: 'email-attachment',
          target: 'workstation-dev-12',
          detected: '8m ago',
          status: 'Blocked'
        }
      ]
    },
    {
      id: 'incident-response',
      title: 'Autonomous Incident Response',
      description: 'End-to-end incident lifecycle management with AI-powered analysis and remediation',
      stats: [
        { label: 'Active Incidents', value: '3', trend: '-2', icon: <AlertTriangle className="w-5 h-5" />, color: 'text-orange-400' },
        { label: 'Avg Resolution', value: '8.4m', trend: '-3.2m', icon: <Clock className="w-5 h-5" />, color: 'text-green-400' },
        { label: 'Auto-Resolved', value: '89%', trend: '+12%', icon: <CheckCircle className="w-5 h-5" />, color: 'text-green-400' },
        { label: 'MTTR', value: '12m', trend: '-8m', icon: <TrendingDown className="w-5 h-5" />, color: 'text-green-400' }
      ],
      incidents: [
        {
          id: 'INC-2024-001',
          title: 'Suspicious Login Activity',
          severity: 'HIGH',
          status: 'In Progress',
          assignedAgent: 'Analysis Agent',
          timeToDetection: '18s',
          progress: 75,
          actions: ['IP Blocked', 'User Notified', 'Session Terminated']
        },
        {
          id: 'INC-2024-002', 
          title: 'Anomalous Network Traffic',
          severity: 'MEDIUM',
          status: 'Analyzing',
          assignedAgent: 'Detection Agent',
          timeToDetection: '45s',
          progress: 35,
          actions: ['Traffic Isolated', 'Logs Collected']
        },
        {
          id: 'INC-2024-003',
          title: 'Failed Authentication Spike',
          severity: 'LOW',
          status: 'Monitoring',
          assignedAgent: 'Communication Agent',
          timeToDetection: '2m',
          progress: 90,
          actions: ['Rate Limiting Applied', 'Admin Notified']
        }
      ]
    },
    {
      id: 'system-performance',
      title: 'Platform Performance Metrics',
      description: 'Real-time monitoring of SentinelOps infrastructure and Google Cloud integration',
      stats: [
        { label: 'System Uptime', value: '99.97%', trend: '+0.02%', icon: <Server className="w-5 h-5" />, color: 'text-green-400' },
        { label: 'BigQuery Queries', value: '15.2K', trend: '+8%', icon: <Database className="w-5 h-5" />, color: 'text-blue-400' },
        { label: 'Gemini API Calls', value: '3,847', trend: '+15%', icon: <Brain className="w-5 h-5" />, color: 'text-purple-400' },
        { label: 'Cloud Functions', value: '99.2%', trend: '+1.1%', icon: <Zap className="w-5 h-5" />, color: 'text-green-400' }
      ],
      services: [
        { name: 'BigQuery Analytics', status: 'Healthy', latency: '120ms', usage: '78%' },
        { name: 'Gemini AI Processing', status: 'Healthy', latency: '3.2s', usage: '65%' },
        { name: 'Cloud Functions', status: 'Healthy', latency: '85ms', usage: '45%' },
        { name: 'Pub/Sub Messaging', status: 'Warning', latency: '250ms', usage: '89%' },
        { name: 'Firestore Database', status: 'Healthy', latency: '45ms', usage: '34%' },
        { name: 'Cloud Monitoring', status: 'Healthy', latency: '95ms', usage: '56%' }
      ]
    }
  ];

  const runDemo = () => {
    setIsRunning(true);
    setActiveView(0);

    // Simulate agent activity
    const interval = setInterval(() => {
      setAgentStatus(prev => ({
        ...prev,
        detection: Math.random() > 0.8 ? 'processing' : 'active',
        analysis: Math.random() > 0.9 ? 'processing' : 'active',
        remediation: Math.random() > 0.7 ? 'active' : 'standby'
      }));
    }, 2000);

    const cycleViews = () => {
      setActiveView(prev => {
        if (prev >= dashboardViews.length - 1) {
          setTimeout(() => {
            setIsRunning(false);
            setActiveView(0);
            clearInterval(interval);
          }, 3000);
          return prev;
        }
        return prev + 1;
      });
    };

    const viewInterval = setInterval(() => {
      cycleViews();
      if (activeView >= dashboardViews.length - 1) {
        clearInterval(viewInterval);
      }
    }, 6000);
  };

  const currentView = dashboardViews[activeView] || dashboardViews[0];
  const selectedTimeframeData = timeframes.find(t => t.code === selectedTimeframe);
  const selectedSeverityData = severityLevels.find(s => s.code === selectedSeverity);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400';
      case 'processing': return 'text-blue-400 animate-pulse';
      case 'standby': return 'text-yellow-400';
      case 'error': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'text-red-400 bg-red-900/20 border-red-500/30';
      case 'high': return 'text-orange-400 bg-orange-900/20 border-orange-500/30';
      case 'medium': return 'text-yellow-400 bg-yellow-900/20 border-yellow-500/30';
      case 'low': return 'text-blue-400 bg-blue-900/20 border-blue-500/30';
      default: return 'text-gray-400 bg-gray-900/20 border-gray-500/30';
    }
  };

  return (
    <div className="w-full">
      {/* Demo Overview */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-2xl font-semibold text-white mb-2">
              SentinelOps Security Operations Dashboard
            </h3>
            <p className="text-gray-300">
              Multi-agent AI-powered platform for autonomous cloud security operations using Google ADK
            </p>
          </div>
          <Button
            onClick={runDemo}
            disabled={isRunning}
            className="bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-white"
          >
            <Play className="mr-2 w-4 h-4" />
            {isRunning ? 'Operations Active...' : 'Start Demo'}
          </Button>
        </div>

        {/* Controls */}
        <div className="flex items-center space-x-4 mb-6">
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-gray-400" />
            <span className="text-white text-sm">
              {timeframes.find(t => t.code === selectedTimeframe)?.name} ({timeframes.find(t => t.code === selectedTimeframe)?.incidents})
            </span>
          </div>
          
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-gray-400" />
            <span className="text-white text-sm">
              {severityLevels.find(s => s.code === selectedSeverity)?.name} ({severityLevels.find(s => s.code === selectedSeverity)?.count})
            </span>
          </div>

          <div className="flex items-center space-x-4 text-sm text-gray-400">
            <span>5 Agents Active</span>
            <span>•</span>
            <span>Google Cloud Native</span>
            <span>•</span>
            <span>ADK Powered</span>
          </div>
        </div>
      </div>

      {/* Current Dashboard View */}
      <div className="bg-black/50 border border-white/10 rounded-xl p-6 backdrop-blur-sm">
        {/* View Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h4 className="text-xl font-semibold text-white mb-1">{currentView?.title}</h4>
            <p className="text-gray-300 text-sm">{currentView?.description}</p>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="border-white/20 text-gray-400">
              View {activeView + 1} of {dashboardViews.length}
            </Badge>
            {isRunning && (
              <Badge className="bg-green-600 text-white">
                <Activity className="w-3 h-3 mr-1 animate-pulse" />
                Live
              </Badge>
            )}
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {currentView?.stats?.map((stat, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: isRunning ? 1 : 0.7, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white/5 rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <div className={stat.color}>
                  {stat.icon}
                </div>
                <Badge variant="outline" className={`text-xs ${
                  stat.trend.includes('+') || stat.trend.includes('-') && !stat.trend.includes('ms') && !stat.trend.includes('s') ? 
                    (stat.trend.includes('+') ? 'border-green-500/30 text-green-400' : 'border-red-500/30 text-red-400') :
                  'border-blue-500/30 text-blue-400'
                }`}>
                  {stat.trend}
                </Badge>
              </div>
              <div className="text-2xl font-bold text-white mb-1">{stat.value}</div>
              <div className="text-xs text-gray-400">{stat.label}</div>
            </motion.div>
          ))}
        </div>

        {/* Detailed Data */}
        <div className="space-y-4">
          <h5 className="text-lg font-semibold text-white mb-4">
            {activeView === 0 && 'Agent Status & Performance'}
            {activeView === 1 && 'Active Threat Detection'}
            {activeView === 2 && 'Incident Response Pipeline'}
            {activeView === 3 && 'Infrastructure Health'}
          </h5>
          
          {/* Agent Orchestration View */}
          {activeView === 0 && currentView?.agents?.map((agent, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: isRunning ? 1 : 0.5, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white/5 rounded-lg p-4"
            >
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-center">
                <div>
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${
                      agent.status === 'active' ? 'bg-green-400' :
                      agent.status === 'processing' ? 'bg-blue-400 animate-pulse' :
                      agent.status === 'standby' ? 'bg-yellow-400' : 'bg-gray-400'
                    }`} />
                    <div className="text-white font-medium">{agent.name}</div>
                  </div>
                  <div className="text-xs text-gray-400 mt-1">{agent.role}</div>
                </div>
                <div>
                  <div className="text-white font-medium">{agent.performance}</div>
                  <div className="text-xs text-gray-400">Success Rate</div>
                </div>
                <div>
                  <div className="text-white font-medium">{agent.lastActivity}</div>
                  <div className="text-xs text-gray-400">Last Activity</div>
                </div>
                <div className="col-span-2">
                  <div className="text-xs text-gray-400 mb-1">ADK Tools</div>
                  <div className="flex flex-wrap gap-1">
                    {agent.tools.map((tool, toolIndex) => (
                      <Badge key={toolIndex} variant="outline" className="text-xs border-white/20 text-gray-300">
                        {tool}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}

          {/* Threat Detection View */}
          {activeView === 1 && currentView?.threats?.map((threat, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: isRunning ? 1 : 0.5, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white/5 rounded-lg p-4"
            >
              <div className="grid grid-cols-1 md:grid-cols-6 gap-4 items-center">
                <div>
                  <div className="text-white font-medium">{threat.type}</div>
                  <div className="text-xs text-gray-400">Threat Type</div>
                </div>
                <div>
                  <Badge className={getSeverityColor(threat.severity)}>
                    {threat.severity}
                  </Badge>
                </div>
                <div>
                  <div className="text-white font-medium">{threat.source}</div>
                  <div className="text-xs text-gray-400">Source</div>
                </div>
                <div>
                  <div className="text-white font-medium">{threat.target}</div>
                  <div className="text-xs text-gray-400">Target</div>
                </div>
                <div>
                  <div className="text-white font-medium">{threat.detected}</div>
                  <div className="text-xs text-gray-400">Detected</div>
                </div>
                <div>
                  <Badge variant="outline" className={`${
                    threat.status === 'Resolved' ? 'border-green-500/30 text-green-400' :
                    threat.status === 'Analyzing' ? 'border-blue-500/30 text-blue-400' :
                    threat.status === 'Remediating' ? 'border-orange-500/30 text-orange-400' :
                    'border-gray-500/30 text-gray-400'
                  }`}>
                    {threat.status}
                  </Badge>
                </div>
              </div>
            </motion.div>
          ))}

          {/* Incident Response View */}
          {activeView === 2 && currentView?.incidents?.map((incident, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: isRunning ? 1 : 0.5, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white/5 rounded-lg p-4"
            >
              <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
                <div>
                  <div className="text-white font-medium">{incident.id}</div>
                  <div className="text-xs text-gray-400">Incident ID</div>
                </div>
                <div>
                  <div className="text-white font-medium text-sm">{incident.title}</div>
                  <div className="text-xs text-gray-400">Description</div>
                </div>
                <div>
                  <Badge className={getSeverityColor(incident.severity)}>
                    {incident.severity}
                  </Badge>
                </div>
                <div>
                  <div className="text-white font-medium">{incident.assignedAgent}</div>
                  <div className="text-xs text-gray-400">Assigned Agent</div>
                </div>
                <div>
                  <div className="text-white font-medium">{incident.timeToDetection}</div>
                  <div className="text-xs text-gray-400">Detection Time</div>
                </div>
                <div>
                  <div className="w-full bg-gray-700 rounded-full h-2 mb-1">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-500" 
                      style={{ width: `${incident.progress}%` }}
                    />
                  </div>
                  <div className="text-xs text-gray-400">{incident.progress}% Complete</div>
                </div>
              </div>
              <div className="mt-3">
                <div className="text-xs text-gray-400 mb-1">Actions Taken</div>
                <div className="flex flex-wrap gap-1">
                  {incident.actions.map((action, actionIndex) => (
                    <Badge key={actionIndex} variant="outline" className="text-xs border-green-500/30 text-green-400">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      {action}
                    </Badge>
                  ))}
                </div>
              </div>
            </motion.div>
          ))}

          {/* System Performance View */}
          {activeView === 3 && currentView?.services?.map((service, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: isRunning ? 1 : 0.5, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white/5 rounded-lg p-4"
            >
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
                <div>
                  <div className="text-white font-medium">{service.name}</div>
                  <div className="text-xs text-gray-400">Service</div>
                </div>
                <div>
                  <Badge className={`${
                    service.status === 'Healthy' ? 'bg-green-600' :
                    service.status === 'Warning' ? 'bg-orange-600' : 'bg-red-600'
                  } text-white text-xs`}>
                    {service.status}
                  </Badge>
                </div>
                <div>
                  <div className="text-white font-medium">{service.latency}</div>
                  <div className="text-xs text-gray-400">Latency</div>
                </div>
                <div>
                  <div className="text-white font-medium">{service.usage}</div>
                  <div className="text-xs text-gray-400">Usage</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Demo Complete */}
      {isRunning && activeView === dashboardViews.length - 1 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 bg-gradient-to-r from-green-900/20 to-blue-900/20 border border-green-500/30 rounded-xl p-6 text-center"
        >
          <h4 className="text-lg font-semibold text-white mb-2">
            SentinelOps Operations Dashboard Complete
          </h4>
          <p className="text-gray-300 text-sm mb-4">
            Autonomous multi-agent security operations with sub-30 second threat detection and response
          </p>
          <div className="flex items-center justify-center space-x-4 text-sm text-gray-400">
            <span>🤖 5 AI Agents</span>
            <span>☁️ Google Cloud Native</span>
            <span>⚡ ADK Powered</span>
            <span>🛡️ 99.7% Success Rate</span>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default SentinelOpsDashboard; 