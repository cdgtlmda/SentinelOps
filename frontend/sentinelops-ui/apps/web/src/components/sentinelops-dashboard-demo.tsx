"use client";

import React, { useState, useEffect } from "react";
import { Sidebar, SidebarBody, SidebarLink } from "@v1/ui/sidebar";
import { 
  LayoutDashboard, 
  Shield, 
  Activity, 
  BarChart3, 
  Settings, 
  AlertTriangle,
  CheckCircle,
  Clock,
  Terminal,
  FileText,
  MessageSquare,
  Database,
  Cloud,
  Server,
  Eye,
  Zap,
  Mail,
  Slack,
  Phone,
  ExternalLink,
  Filter,
  Search,
  Download,
  Bell,
  Users,
  Cpu,
  HardDrive,
  Wifi,
  MonitorSpeaker
} from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import { cn } from "@v1/ui/cn";
import { Badge } from "@v1/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogPortal, DialogOverlay } from "@v1/ui/dialog";
import { Input } from "@v1/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@v1/ui/select";

interface Agent {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'error';
  efficiency: number;
  lastActivity: string;
  tasksCompleted: number;
  currentTask?: string;
  tools: string[];
}

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
  source: string;
  message: string;
  metadata?: Record<string, any>;
}

interface AuditEvent {
  id: string;
  timestamp: string;
  user: string;
  action: string;
  resource: string;
  outcome: 'success' | 'failure';
  riskScore: number;
}

interface Ticket {
  id: string;
  title: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'investigating' | 'resolving' | 'closed';
  assignedTo: string;
  createdAt: string;
  updatedAt: string;
  description: string;
  tags: string[];
}

interface GCPService {
  name: string;
  status: 'healthy' | 'degraded' | 'error';
  latency: number;
  usage: number;
  lastCheck: string;
}

interface RemediationAction {
  id: string;
  timestamp: string;
  action: string;
  target: string;
  status: 'pending' | 'executing' | 'completed' | 'failed';
  agent: string;
  details: string;
}

interface NotificationChannel {
  type: 'email' | 'slack' | 'sms' | 'webhook';
  name: string;
  status: 'active' | 'inactive';
  lastUsed: string;
  messagesSent: number;
}

interface CommunicationExample {
  type: 'email' | 'slack' | 'sms' | 'webhook';
  title: string;
  content: string;
  timestamp: string;
  recipient: string;
}

interface IncidentForm {
  title: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  assignedTo: string;
  tags: string;
}

const initialAgents: Agent[] = [
  {
    id: 'detection',
    name: 'Detection Agent',
    status: 'active',
    efficiency: 98.5,
    lastActivity: '2 seconds ago',
    tasksCompleted: 1247,
    currentTask: 'Scanning BigQuery audit logs',
    tools: ['RulesEngineTool', 'LogMonitoringTool', 'AnomalyDetectionTool', 'EventCorrelationTool']
  },
  {
    id: 'analysis',
    name: 'Analysis Agent', 
    status: 'active',
    efficiency: 97.2,
    lastActivity: '5 seconds ago',
    tasksCompleted: 892,
    currentTask: 'Gemini AI threat analysis',
    tools: ['GeminiAnalysisTool', 'ThreatIntelTool', 'RiskAssessmentTool', 'ContextEnrichmentTool']
  },
  {
    id: 'remediation',
    name: 'Remediation Agent',
    status: 'idle',
    efficiency: 96.8,
    lastActivity: '3 minutes ago',
    tasksCompleted: 456,
    currentTask: undefined,
    tools: ['CloudFunctionTool', 'IAMRemediationTool', 'FirewallTool', 'VMIsolationTool']
  },
  {
    id: 'communication',
    name: 'Communication Agent',
    status: 'active',
    efficiency: 99.1,
    lastActivity: '1 minute ago',
    tasksCompleted: 234,
    currentTask: 'Sending Slack notifications',
    tools: ['EmailNotificationTool', 'SlackIntegrationTool', 'SMSAlertTool', 'WebhookTool']
  },
  {
    id: 'orchestrator',
    name: 'Orchestrator Agent',
    status: 'active',
    efficiency: 99.7,
    lastActivity: '1 second ago',
    tasksCompleted: 2103,
    currentTask: 'Coordinating incident INC-2024-0621-001',
    tools: ['WorkflowEngineTool', 'AgentCoordinationTool', 'EscalationTool', 'MetricsTool']
  }
];

const initialLogEntries: LogEntry[] = [
  {
    id: '1',
    timestamp: '2024-06-21 21:44:15',
    level: 'WARN',
    source: 'BigQuery Audit',
    message: 'Unusual query pattern detected from user john.doe@company.com',
    metadata: { querySize: '15GB', duration: '45s', tables: 3 }
  },
  {
    id: '2',
    timestamp: '2024-06-21 21:44:08',
    level: 'INFO',
    source: 'VPC Flow Logs',
    message: 'New connection established from 203.45.67.89 to internal subnet',
    metadata: { protocol: 'TCP', port: 3306, bytes: 1024 }
  },
  {
    id: '3',
    timestamp: '2024-06-21 21:43:52',
    level: 'ERROR',
    source: 'IAM Audit',
    message: 'Failed authentication attempt for service account',
    metadata: { account: 'sentinel-detection@project.iam', attempts: 5 }
  },
  {
    id: '4',
    timestamp: '2024-06-21 21:43:45',
    level: 'INFO',
    source: 'Cloud Functions',
    message: 'Remediation function executed successfully',
    metadata: { function: 'isolate-vm', target: 'vm-web-001', duration: '2.3s' }
  }
];

const gcpServices: GCPService[] = [
  { name: 'BigQuery', status: 'healthy', latency: 45, usage: 78, lastCheck: '30s ago' },
  { name: 'Cloud Functions', status: 'healthy', latency: 120, usage: 34, lastCheck: '15s ago' },
  { name: 'Pub/Sub', status: 'healthy', latency: 25, usage: 56, lastCheck: '10s ago' },
  { name: 'Firestore', status: 'degraded', latency: 180, usage: 89, lastCheck: '45s ago' },
  { name: 'Cloud Monitoring', status: 'healthy', latency: 67, usage: 23, lastCheck: '20s ago' },
  { name: 'Gemini AI', status: 'healthy', latency: 340, usage: 67, lastCheck: '5s ago' }
];

const SentinelOpsLogo = () => {
  return (
    <Link
      href="#"
      className="font-normal flex space-x-2 items-center text-sm text-white py-1 relative z-20"
    >
      <div className="h-6 w-6 bg-gradient-to-r from-blue-500 to-purple-600 rounded-md flex-shrink-0 flex items-center justify-center">
        <Shield className="h-4 w-4 text-white" />
      </div>
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="font-semibold text-white whitespace-pre"
      >
        SentinelOps
      </motion.span>
    </Link>
  );
};

const SentinelOpsLogoIcon = () => {
  return (
    <Link
      href="#"
      className="font-normal flex space-x-2 items-center text-sm text-white py-1 relative z-20"
    >
      <div className="h-6 w-6 bg-gradient-to-r from-blue-500 to-purple-600 rounded-md flex-shrink-0 flex items-center justify-center">
        <Shield className="h-4 w-4 text-white" />
      </div>
    </Link>
  );
};

const OverviewDashboard = () => {
  const [mounted, setMounted] = useState(false);
  const [stats, setStats] = useState({
    threatsBlocked: 1249,
    activeIncidents: 3,
    systemHealth: 99.5,
    responseTime: 21
  });

  useEffect(() => {
    setMounted(true);
    const interval = setInterval(() => {
      setStats(prev => ({
        threatsBlocked: prev.threatsBlocked + Math.floor(Math.random() * 3),
        activeIncidents: Math.max(0, prev.activeIncidents + (Math.random() > 0.7 ? 1 : -1)),
        systemHealth: Math.max(95, Math.min(100, prev.systemHealth + (Math.random() - 0.5) * 0.5)),
        responseTime: Math.max(15, Math.min(45, prev.responseTime + (Math.random() - 0.5) * 5))
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  if (!mounted) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-green-400">Security Operations Center</h1>
          <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
            <CheckCircle className="w-3 h-3 mr-1" />
            All Systems Operational
          </Badge>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Threats Blocked Today"
            value="1249"
            icon={<Shield className="w-5 h-5 text-blue-400" />}
            trend="+12%"
            color="blue"
          />
          <MetricCard
            title="Active Incidents"
            value="3"
            icon={<AlertTriangle className="w-5 h-5 text-orange-400" />}
            trend="stable"
            color="orange"
          />
          <MetricCard
            title="System Health"
            value="99.5%"
            icon={<Activity className="w-5 h-5 text-green-400" />}
            trend="+0.2%"
            color="green"
          />
          <MetricCard
            title="Avg Response Time"
            value="21s"
            icon={<Clock className="w-5 h-5 text-purple-400" />}
            trend="-5s"
            color="purple"
          />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-black/50 border border-white/10 rounded-xl p-6 backdrop-blur-sm">
            <h3 className="text-lg font-semibold text-green-400 mb-4">AI Agent Status</h3>
            <div className="space-y-3">
              {initialAgents.map((agent) => (
                <AgentStatusCard key={agent.id} agent={agent} />
              ))}
            </div>
          </div>
          <div className="bg-black/50 border border-white/10 rounded-xl p-6 backdrop-blur-sm">
            <h3 className="text-lg font-semibold text-green-400 mb-4">Recent Activity</h3>
            <div className="space-y-3">
              {initialLogEntries.slice(0, 4).map((log) => (
                <div key={log.id} className="flex items-start gap-3 p-3 bg-white/5 rounded-lg">
                  <div className={cn(
                    "w-2 h-2 rounded-full mt-2",
                    log.level === 'ERROR' && "bg-red-400",
                    log.level === 'WARN' && "bg-yellow-400",
                    log.level === 'INFO' && "bg-blue-400",
                    log.level === 'DEBUG' && "bg-gray-400"
                  )} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-300 truncate">{log.message}</p>
                    <p className="text-xs text-gray-500">{log.source} • {log.timestamp}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="bg-black/50 border border-white/10 rounded-xl p-6 backdrop-blur-sm">
          <h3 className="text-lg font-semibold text-green-400 mb-4">Google Cloud Platform Services</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {gcpServices.map((service) => (
              <div key={service.name} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "w-3 h-3 rounded-full",
                    service.status === 'healthy' && "bg-green-400",
                    service.status === 'degraded' && "bg-yellow-400",
                    service.status === 'error' && "bg-red-400"
                  )} />
                  <span className="text-white font-medium">{service.name}</span>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-300">{service.latency}ms</p>
                  <p className="text-xs text-gray-500">{service.usage}% usage</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-green-400">Security Operations Center</h1>
        <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
          <CheckCircle className="w-3 h-3 mr-1" />
          All Systems Operational
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Threats Blocked Today"
          value={stats.threatsBlocked.toString()}
          icon={<Shield className="w-5 h-5 text-blue-400" />}
          trend="+12%"
          color="blue"
        />
        <MetricCard
          title="Active Incidents"
          value={stats.activeIncidents.toString()}
          icon={<AlertTriangle className="w-5 h-5 text-orange-400" />}
          trend={stats.activeIncidents > 5 ? "+2" : "stable"}
          color="orange"
        />
        <MetricCard
          title="System Health"
          value={`${stats.systemHealth.toFixed(1)}%`}
          icon={<Activity className="w-5 h-5 text-green-400" />}
          trend="+0.2%"
          color="green"
        />
        <MetricCard
          title="Avg Response Time"
          value={`${Math.round(stats.responseTime)}s`}
          icon={<Clock className="w-5 h-5 text-purple-400" />}
          trend="-5s"
          color="purple"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-black/50 border border-white/10 rounded-xl p-6 backdrop-blur-sm">
          <h3 className="text-lg font-semibold text-green-400 mb-4">AI Agent Status</h3>
          <div className="space-y-3">
            {initialAgents.map((agent) => (
              <AgentStatusCard key={agent.id} agent={agent} />
            ))}
          </div>
        </div>

        <div className="bg-black/50 border border-white/10 rounded-xl p-6 backdrop-blur-sm">
          <h3 className="text-lg font-semibold text-green-400 mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {initialLogEntries.slice(0, 4).map((log) => (
              <div key={log.id} className="flex items-start gap-3 p-3 bg-white/5 rounded-lg">
                <div className={cn(
                  "w-2 h-2 rounded-full mt-2",
                  log.level === 'ERROR' && "bg-red-400",
                  log.level === 'WARN' && "bg-yellow-400",
                  log.level === 'INFO' && "bg-blue-400",
                  log.level === 'DEBUG' && "bg-gray-400"
                )} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-300 truncate">{log.message}</p>
                  <p className="text-xs text-gray-500">{log.source} • {log.timestamp}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-black/50 border border-white/10 rounded-xl p-6 backdrop-blur-sm">
        <h3 className="text-lg font-semibold text-green-400 mb-4">Google Cloud Platform Services</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {gcpServices.map((service) => (
            <div key={service.name} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
              <div className="flex items-center gap-3">
                <div className={cn(
                  "w-3 h-3 rounded-full",
                  service.status === 'healthy' && "bg-green-400",
                  service.status === 'degraded' && "bg-yellow-400",
                  service.status === 'error' && "bg-red-400"
                )} />
                <span className="text-white font-medium">{service.name}</span>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-300">{service.latency}ms</p>
                <p className="text-xs text-gray-500">{service.usage}% usage</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const LiveLogsDashboard = () => {
  const [mounted, setMounted] = useState(false);
  const [logs, setLogs] = useState(initialLogEntries);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    setMounted(true);
    const interval = setInterval(() => {
      const newLog: LogEntry = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString().slice(0, 19).replace('T', ' '),
        level: ['INFO', 'WARN', 'ERROR', 'DEBUG'][Math.floor(Math.random() * 4)] as LogEntry['level'],
        source: ['BigQuery Audit', 'VPC Flow Logs', 'IAM Audit', 'Cloud Functions'][Math.floor(Math.random() * 4)],
        message: [
          'Authentication successful for user',
          'Firewall rule updated',
          'Suspicious activity detected',
          'Database query executed',
          'API call rate limit exceeded'
        ][Math.floor(Math.random() * 5)],
      };
      setLogs(prev => [newLog, ...prev.slice(0, 19)]);
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const filteredLogs = filter === 'all' ? logs : logs.filter(log => log.level === filter);

  if (!mounted) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-green-400">Live Security Logs</h1>
          <div className="flex items-center gap-2">
            <select 
              value="all" 
              className="bg-black/50 border border-white/10 text-white px-3 py-1 rounded-md"
            >
              <option value="all">All Levels</option>
              <option value="ERROR">Errors</option>
              <option value="WARN">Warnings</option>
              <option value="INFO">Info</option>
              <option value="DEBUG">Debug</option>
            </select>
            <button className="bg-blue-500/20 border border-blue-500/30 text-blue-400 px-3 py-1 rounded-md hover:bg-blue-500/30">
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>
        <div className="bg-black/50 border border-white/10 rounded-xl overflow-hidden">
          <div className="bg-gray-900/50 px-4 py-2 border-b border-white/10">
            <div className="grid grid-cols-6 gap-4 text-sm font-medium text-gray-400">
              <span>Timestamp</span>
              <span>Level</span>
              <span>Source</span>
              <span className="col-span-3">Message</span>
            </div>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {initialLogEntries.map((log) => (
              <div key={log.id} className="grid grid-cols-6 gap-4 px-4 py-3 border-b border-white/5 hover:bg-white/5">
                <span className="text-xs text-gray-400 font-mono">{log.timestamp}</span>
                <Badge className={cn(
                  "w-fit text-xs",
                  log.level === 'ERROR' && "bg-red-500/20 text-red-400 border-red-500/30",
                  log.level === 'WARN' && "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
                  log.level === 'INFO' && "bg-blue-500/20 text-blue-400 border-blue-500/30",
                  log.level === 'DEBUG' && "bg-gray-500/20 text-gray-400 border-gray-500/30"
                )}>
                  {log.level}
                </Badge>
                <span className="text-sm text-gray-300">{log.source}</span>
                <span className="col-span-3 text-sm text-white">{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-green-400">Live Security Logs</h1>
        <div className="flex items-center gap-2">
          <select 
            value={filter} 
            onChange={(e) => setFilter(e.target.value)}
            className="bg-black/50 border border-white/10 text-white px-3 py-1 rounded-md"
          >
            <option value="all">All Levels</option>
            <option value="ERROR">Errors</option>
            <option value="WARN">Warnings</option>
            <option value="INFO">Info</option>
            <option value="DEBUG">Debug</option>
          </select>
          <button className="bg-blue-500/20 border border-blue-500/30 text-blue-400 px-3 py-1 rounded-md hover:bg-blue-500/30">
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="bg-black/50 border border-white/10 rounded-xl overflow-hidden">
        <div className="bg-gray-900/50 px-4 py-2 border-b border-white/10">
          <div className="grid grid-cols-6 gap-4 text-sm font-medium text-gray-400">
            <span>Timestamp</span>
            <span>Level</span>
            <span>Source</span>
            <span className="col-span-3">Message</span>
          </div>
        </div>
        <div className="max-h-96 overflow-y-auto">
          {filteredLogs.map((log) => (
            <div key={log.id} className="grid grid-cols-6 gap-4 px-4 py-3 border-b border-white/5 hover:bg-white/5">
              <span className="text-xs text-gray-400 font-mono">{log.timestamp}</span>
              <Badge className={cn(
                "w-fit text-xs",
                log.level === 'ERROR' && "bg-red-500/20 text-red-400 border-red-500/30",
                log.level === 'WARN' && "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
                log.level === 'INFO' && "bg-blue-500/20 text-blue-400 border-blue-500/30",
                log.level === 'DEBUG' && "bg-gray-500/20 text-gray-400 border-gray-500/30"
              )}>
                {log.level}
              </Badge>
              <span className="text-sm text-gray-300">{log.source}</span>
              <span className="col-span-3 text-sm text-white">{log.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const AuditTrailDashboard = () => {
  const auditEvents: AuditEvent[] = [
    {
      id: '1',
      timestamp: '2024-06-21 21:44:12',
      user: 'admin@company.com',
      action: 'IAM Role Modified',
      resource: 'projects/sentinel-ops/roles/security-analyst',
      outcome: 'success',
      riskScore: 7.2
    },
    {
      id: '2',
      timestamp: '2024-06-21 21:43:58',
      user: 'john.doe@company.com',
      action: 'BigQuery Dataset Access',
      resource: 'projects/sentinel-ops/datasets/security_logs',
      outcome: 'success',
      riskScore: 4.1
    },
    {
      id: '3',
      timestamp: '2024-06-21 21:43:33',
      user: 'service-account@project.iam',
      action: 'Firewall Rule Created',
      resource: 'projects/sentinel-ops/global/firewalls/block-suspicious-ip',
      outcome: 'success',
      riskScore: 2.8
    }
  ];

  const handleExport = (format: 'csv' | 'xml') => {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `audit-trail-${timestamp}.${format}`;
    
    let content = '';
    let mimeType = '';
    
    if (format === 'csv') {
      // CSV format
      const headers = ['Timestamp', 'User', 'Action', 'Resource', 'Outcome', 'Risk Score'];
      const csvRows = [
        headers.join(','),
        ...auditEvents.map(event => [
          `"${event.timestamp}"`,
          `"${event.user}"`,
          `"${event.action}"`,
          `"${event.resource}"`,
          `"${event.outcome}"`,
          event.riskScore.toString()
        ].join(','))
      ];
      content = csvRows.join('\n');
      mimeType = 'text/csv';
    } else {
      // XML format
      content = `<?xml version="1.0" encoding="UTF-8"?>
<audit_trail>
  <metadata>
    <generated_at>${new Date().toISOString()}</generated_at>
    <total_events>${auditEvents.length}</total_events>
  </metadata>
  <events>
${auditEvents.map(event => `    <event id="${event.id}">
      <timestamp>${event.timestamp}</timestamp>
      <user>${event.user}</user>
      <action>${event.action}</action>
      <resource>${event.resource}</resource>
      <outcome>${event.outcome}</outcome>
      <risk_score>${event.riskScore}</risk_score>
    </event>`).join('\n')}
  </events>
</audit_trail>`;
      mimeType = 'application/xml';
    }
    
    // Create and download file
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-green-400">Audit Trail</h1>
        <div className="flex items-center gap-2">
          <button className="bg-blue-500/20 border border-blue-500/30 text-blue-400 px-3 py-1 rounded-md hover:bg-blue-500/30">
            <Filter className="w-4 h-4 mr-2" />
            Filter
          </button>
          <Select onValueChange={(value: 'csv' | 'xml') => handleExport(value)}>
            <SelectTrigger className="bg-green-500/20 border border-green-500/30 text-green-400 px-3 py-1 rounded-md hover:bg-green-500/30 w-auto">
              <Download className="w-4 h-4 mr-2" />
              <SelectValue placeholder="Export" />
            </SelectTrigger>
            <SelectContent className="bg-gray-900 border-white/10">
              <SelectItem value="csv" className="text-green-400 hover:bg-green-500/20">
                Export as CSV
              </SelectItem>
              <SelectItem value="xml" className="text-green-400 hover:bg-green-500/20">
                Export as XML
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="bg-black/50 border border-white/10 rounded-xl overflow-hidden">
        <div className="bg-gray-900/50 px-4 py-3 border-b border-white/10">
          <div className="grid grid-cols-7 gap-6 text-sm font-medium text-gray-400">
            <span>Timestamp</span>
            <span>User</span>
            <span>Action</span>
            <span className="col-span-2">Resource</span>
            <span>Outcome</span>
            <span>Risk Score</span>
          </div>
        </div>
        <div className="max-h-96 overflow-y-auto">
          {auditEvents.map((event) => (
            <div key={event.id} className="grid grid-cols-7 gap-6 px-4 py-3 border-b border-white/5 hover:bg-white/5">
              <span className="text-xs text-gray-400 font-mono">{event.timestamp}</span>
              <span className="text-sm text-white truncate">{event.user}</span>
              <span className="text-sm text-blue-400">{event.action}</span>
              <span className="col-span-2 text-sm text-gray-300 truncate">{event.resource}</span>
              <Badge className={cn(
                "w-fit text-xs",
                event.outcome === 'success' && "bg-green-500/20 text-green-400 border-green-500/30",
                event.outcome === 'failure' && "bg-red-500/20 text-red-400 border-red-500/30"
              )}>
                {event.outcome}
              </Badge>
              <span className={cn(
                "text-sm font-medium",
                event.riskScore > 6 && "text-red-400",
                event.riskScore > 3 && event.riskScore <= 6 && "text-yellow-400",
                event.riskScore <= 3 && "text-green-400"
              )}>
                {event.riskScore.toFixed(1)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const IncidentsDashboard = () => {
  const [incidentForm, setIncidentForm] = useState<IncidentForm>({
    title: '',
    severity: 'medium',
    description: '',
    assignedTo: 'Detection Agent',
    tags: ''
  });

  const tickets: Ticket[] = [
    {
      id: 'INC-2024-0621-001',
      title: 'Suspicious Database Access Pattern Detected',
      severity: 'high',
      status: 'investigating',
      assignedTo: 'Analysis Agent',
      createdAt: '2024-06-21 21:42:15',
      updatedAt: '2024-06-21 21:44:12',
      description: 'Unusual BigQuery access pattern detected from user account. Large data export outside normal hours.',
      tags: ['data-exfiltration', 'bigquery', 'after-hours']
    },
    {
      id: 'INC-2024-0621-002',
      title: 'Privilege Escalation Attempt',
      severity: 'critical',
      status: 'resolving',
      assignedTo: 'Remediation Agent',
      createdAt: '2024-06-21 21:41:33',
      updatedAt: '2024-06-21 21:44:08',
      description: 'Service account attempting to escalate privileges to project owner role.',
      tags: ['privilege-escalation', 'iam', 'service-account']
    }
  ];

  const handleCreateIncident = () => {
    // In a real app, this would submit to an API
    console.log('Creating incident:', incidentForm);
    // Reset form
    setIncidentForm({
      title: '',
      severity: 'medium',
      description: '',
      assignedTo: 'Detection Agent',
      tags: ''
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-green-400">Security Incidents</h1>
        <Dialog>
          <DialogTrigger asChild>
            <button className="bg-blue-500/20 border border-blue-500/30 text-blue-400 px-4 py-2 rounded-md hover:bg-blue-500/30">
              Create Incident
            </button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl bg-black border border-white/10 text-white shadow-2xl rounded-lg z-[100]">
            <DialogHeader>
              <DialogTitle className="text-green-400">Create New Security Incident</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-300 block mb-2">
                  Incident Title *
                </label>
                <Input
                  value={incidentForm.title}
                  onChange={(e) => setIncidentForm(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="Brief description of the security incident"
                  className="bg-gray-900/50 border-white/10 text-white"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-300 block mb-2">
                    Severity *
                  </label>
                  <Select 
                    value={incidentForm.severity} 
                    onValueChange={(value: 'low' | 'medium' | 'high' | 'critical') => 
                      setIncidentForm(prev => ({ ...prev, severity: value }))
                    }
                  >
                    <SelectTrigger className="bg-gray-900/50 border-white/10 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-900 border-white/10">
                      <SelectItem value="low" className="text-green-400">Low</SelectItem>
                      <SelectItem value="medium" className="text-yellow-400">Medium</SelectItem>
                      <SelectItem value="high" className="text-orange-400">High</SelectItem>
                      <SelectItem value="critical" className="text-red-400">Critical</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-300 block mb-2">
                    Assign to Agent
                  </label>
                  <Select 
                    value={incidentForm.assignedTo} 
                    onValueChange={(value) => setIncidentForm(prev => ({ ...prev, assignedTo: value }))}
                  >
                    <SelectTrigger className="bg-gray-900/50 border-white/10 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-900 border-white/10">
                      <SelectItem value="Detection Agent">Detection Agent</SelectItem>
                      <SelectItem value="Analysis Agent">Analysis Agent</SelectItem>
                      <SelectItem value="Remediation Agent">Remediation Agent</SelectItem>
                      <SelectItem value="Communication Agent">Communication Agent</SelectItem>
                      <SelectItem value="Orchestrator Agent">Orchestrator Agent</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-300 block mb-2">
                  Description *
                </label>
                <textarea
                  value={incidentForm.description}
                  onChange={(e) => setIncidentForm(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Detailed description of the security incident, including affected systems, potential impact, and any immediate actions taken..."
                  className="w-full h-24 bg-gray-900/50 border border-white/10 rounded-md px-3 py-2 text-white placeholder-gray-500 resize-none"
                />
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-300 block mb-2">
                  Tags (comma-separated)
                </label>
                <Input
                  value={incidentForm.tags}
                  onChange={(e) => setIncidentForm(prev => ({ ...prev, tags: e.target.value }))}
                  placeholder="e.g., malware, phishing, data-breach, insider-threat"
                  className="bg-gray-900/50 border-white/10 text-white"
                />
              </div>
              
              <div className="flex justify-end gap-3 pt-4">
                <DialogTrigger asChild>
                  <button className="px-4 py-2 text-gray-400 hover:text-white">
                    Cancel
                  </button>
                </DialogTrigger>
                <button 
                  onClick={handleCreateIncident}
                  disabled={!incidentForm.title || !incidentForm.description}
                  className="bg-green-500/20 border border-green-500/30 text-green-400 px-4 py-2 rounded-md hover:bg-green-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Incident
                </button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-4">
        {tickets.map((ticket) => (
          <div key={ticket.id} className="bg-black/50 border border-white/10 rounded-xl p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-semibold text-white">{ticket.title}</h3>
                  <Badge className={cn(
                    "text-xs",
                    ticket.severity === 'critical' && "bg-red-500/20 text-red-400 border-red-500/30",
                    ticket.severity === 'high' && "bg-orange-500/20 text-orange-400 border-orange-500/30",
                    ticket.severity === 'medium' && "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
                    ticket.severity === 'low' && "bg-green-500/20 text-green-400 border-green-500/30"
                  )}>
                    {ticket.severity.toUpperCase()}
                  </Badge>
                  <Badge className={cn(
                    "text-xs",
                    ticket.status === 'open' && "bg-blue-500/20 text-blue-400 border-blue-500/30",
                    ticket.status === 'investigating' && "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
                    ticket.status === 'resolving' && "bg-purple-500/20 text-purple-400 border-purple-500/30",
                    ticket.status === 'closed' && "bg-green-500/20 text-green-400 border-green-500/30"
                  )}>
                    {ticket.status.toUpperCase()}
                  </Badge>
                </div>
                <p className="text-sm text-gray-300 mb-3">{ticket.description}</p>
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span>ID: {ticket.id}</span>
                  <span>Assigned: {ticket.assignedTo}</span>
                  <span>Created: {ticket.createdAt}</span>
                </div>
              </div>
              <button className="text-blue-400 hover:text-blue-300">
                <ExternalLink className="w-4 h-4" />
              </button>
            </div>
            <div className="flex items-center gap-2">
              {ticket.tags.map((tag) => (
                <span key={tag} className="px-2 py-1 bg-white/10 text-gray-300 text-xs rounded">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const AgentStatusDashboard = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-green-400">AI Agent Status</h1>
      
      <div className="grid gap-6">
        {initialAgents.map((agent) => (
          <div key={agent.id} className="bg-black/50 border border-white/10 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={cn(
                  "w-4 h-4 rounded-full",
                  agent.status === 'active' && "bg-green-400",
                  agent.status === 'idle' && "bg-yellow-400",
                  agent.status === 'error' && "bg-red-400"
                )} />
                <h3 className="text-lg font-semibold text-white">{agent.name}</h3>
                <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30 text-xs">
                  {agent.efficiency}% efficiency
                </Badge>
              </div>
              <span className="text-sm text-gray-400">{agent.lastActivity}</span>
            </div>
            
            {agent.currentTask && (
              <div className="mb-4">
                <p className="text-sm text-gray-300 mb-2">Current Task:</p>
                <p className="text-white">{agent.currentTask}</p>
              </div>
            )}
            
            <div className="mb-4">
              <p className="text-sm text-gray-300 mb-2">ADK Tools:</p>
              <div className="flex flex-wrap gap-2">
                {agent.tools.map((tool) => (
                  <span key={tool} className="px-2 py-1 bg-purple-500/20 text-purple-400 text-xs rounded border border-purple-500/30">
                    {tool}
                  </span>
                ))}
              </div>
            </div>
            
            <div className="text-sm text-gray-400">
              Tasks Completed: {agent.tasksCompleted}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const CommunicationsDashboard = () => {
  const channels: NotificationChannel[] = [
    { type: 'email', name: 'Security Team Email', status: 'active', lastUsed: '2 min ago', messagesSent: 45 },
    { type: 'slack', name: '#security-alerts', status: 'active', lastUsed: '30 sec ago', messagesSent: 123 },
    { type: 'sms', name: 'On-call SMS', status: 'active', lastUsed: '5 min ago', messagesSent: 12 },
    { type: 'webhook', name: 'SIEM Integration', status: 'active', lastUsed: '1 min ago', messagesSent: 67 }
  ];

  const communicationExamples: Record<string, CommunicationExample> = {
    'email': {
      type: 'email',
      title: '🚨 CRITICAL: Privilege Escalation Detected',
      content: `Subject: [SENTINELOPS-CRITICAL] Privilege Escalation Attempt Detected

Dear Security Team,

SentinelOps has detected a critical security incident:

INCIDENT ID: INC-2024-0621-002
SEVERITY: Critical
DETECTED: 2024-06-21 21:41:33 UTC
AGENT: Detection Agent

DETAILS:
Service account 'automated-backup@project.iam' attempted to escalate privileges to project owner role. This is highly unusual behavior for this service account.

AUTOMATIC ACTIONS TAKEN:
✓ Account temporarily suspended
✓ Audit trail preserved
✓ Incident ticket created
✓ Remediation Agent notified

NEXT STEPS:
1. Review service account activity logs
2. Verify legitimacy of privilege escalation
3. Contact service account owner if needed

View full incident: https://sentinel-ops.com/incidents/INC-2024-0621-002

--
SentinelOps Security Platform
Powered by Google ADK`,
      timestamp: '2024-06-21 21:42:15',
      recipient: 'security-team@company.com'
    },
    'slack': {
      type: 'slack',
      title: '🔍 Suspicious Database Access',
      content: `🔍 **ALERT: Unusual BigQuery Activity**

**Incident:** INC-2024-0621-001
**User:** john.doe@company.com
**Time:** 21:44:12 UTC
**Risk Level:** HIGH ⚠️

**Details:**
• Large data export (15GB) detected
• Query executed outside normal business hours
• Access to sensitive customer data tables
• 3x larger than user's typical queries

**Status:** 🤖 Analysis Agent investigating
**ETA:** Response within 5 minutes

React with ✅ to acknowledge or 🚨 to escalate

*Powered by SentinelOps Detection Agent*`,
      timestamp: '2024-06-21 21:44:30',
      recipient: '#security-alerts'
    },
    'sms': {
      type: 'sms',
      title: 'Critical Security Alert',
      content: `🚨 SENTINELOPS ALERT

CRITICAL: Privilege escalation attempt detected

Incident: INC-2024-0621-002
Time: 21:41:33 UTC
Status: AUTO-REMEDIATED

Service account suspended. Review required.

Dashboard: https://bit.ly/sentinel-dash
Call: +1-800-SECURITY

-SentinelOps`,
      timestamp: '2024-06-21 21:41:45',
      recipient: '+1-555-0123 (On-call Engineer)'
    },
    'webhook': {
      type: 'webhook',
      title: 'SIEM Integration Event',
      content: `{
  "event_type": "security_incident",
  "source": "sentinelops",
  "timestamp": "2024-06-21T21:44:12Z",
  "incident_id": "INC-2024-0621-001",
  "severity": "high",
  "category": "data_exfiltration",
  "details": {
    "user": "john.doe@company.com",
    "action": "bigquery_large_export",
    "data_size": "15GB",
    "tables_accessed": [
      "customer_data",
      "payment_info", 
      "user_profiles"
    ],
    "risk_score": 8.5,
    "auto_actions": [
      "user_session_flagged",
      "query_logged",
      "analysis_initiated"
    ]
  },
  "agent_response": {
    "assigned_agent": "analysis_agent",
    "status": "investigating",
    "eta_minutes": 3
  }
}`,
      timestamp: '2024-06-21 21:44:15',
      recipient: 'https://siem.company.com/webhook/sentinelops'
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Communication Channels</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {channels.map((channel) => (
          <Dialog key={`${channel.type}-${channel.name}`}>
            <DialogTrigger asChild>
              <div className="bg-black/50 border border-white/10 rounded-xl p-6 cursor-pointer hover:bg-black/70 transition-colors">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    {channel.type === 'email' && <Mail className="w-5 h-5 text-blue-400" />}
                    {channel.type === 'slack' && <MessageSquare className="w-5 h-5 text-green-400" />}
                    {channel.type === 'sms' && <Phone className="w-5 h-5 text-purple-400" />}
                    {channel.type === 'webhook' && <ExternalLink className="w-5 h-5 text-orange-400" />}
                    <h3 className="text-white font-medium">{channel.name}</h3>
                  </div>
                  <Badge className={cn(
                    "text-xs",
                    channel.status === 'active' && "bg-green-500/20 text-green-400 border-green-500/30",
                    channel.status === 'inactive' && "bg-gray-500/20 text-gray-400 border-gray-500/30"
                  )}>
                    {channel.status}
                  </Badge>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Last Used:</span>
                    <span className="text-white">{channel.lastUsed}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Messages Sent:</span>
                    <span className="text-white">{channel.messagesSent}</span>
                  </div>
                </div>
                <div className="mt-3 text-xs text-blue-400">Click to view example →</div>
              </div>
            </DialogTrigger>
            <DialogContent className="max-w-2xl bg-black border border-white/10 text-white shadow-2xl rounded-lg z-[100]">
              <DialogHeader>
                <DialogTitle className="text-green-400 flex items-center gap-2">
                  {channel.type === 'email' && <Mail className="w-5 h-5" />}
                  {channel.type === 'slack' && <MessageSquare className="w-5 h-5" />}
                  {channel.type === 'sms' && <Phone className="w-5 h-5" />}
                  {channel.type === 'webhook' && <ExternalLink className="w-5 h-5" />}
                  {communicationExamples[channel.type]?.title}
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Sent to:</span>
                  <span className="text-white">{communicationExamples[channel.type]?.recipient}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Timestamp:</span>
                  <span className="text-white">{communicationExamples[channel.type]?.timestamp}</span>
                </div>
                <div className="bg-gray-900/50 border border-white/10 rounded-lg p-4">
                  <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">
                    {communicationExamples[channel.type]?.content}
                  </pre>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        ))}
      </div>
    </div>
  );
};

const GCPServicesDashboard = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Google Cloud Platform Services</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {gcpServices.map((service) => (
          <div key={service.name} className="bg-black/50 border border-white/10 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={cn(
                  "w-4 h-4 rounded-full",
                  service.status === 'healthy' && "bg-green-400",
                  service.status === 'degraded' && "bg-yellow-400",
                  service.status === 'error' && "bg-red-400"
                )} />
                <h3 className="text-white font-medium">{service.name}</h3>
              </div>
              <Badge className={cn(
                "text-xs",
                service.status === 'healthy' && "bg-green-500/20 text-green-400 border-green-500/30",
                service.status === 'degraded' && "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
                service.status === 'error' && "bg-red-500/20 text-red-400 border-red-500/30"
              )}>
                {service.status}
              </Badge>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Latency:</span>
                <span className="text-white">{service.latency}ms</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Usage:</span>
                <span className="text-white">{service.usage}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className={cn(
                    "h-2 rounded-full",
                    service.usage < 50 && "bg-green-400",
                    service.usage >= 50 && service.usage < 80 && "bg-yellow-400",
                    service.usage >= 80 && "bg-red-400"
                  )}
                  style={{ width: `${service.usage}%` }}
                />
              </div>
              <div className="text-xs text-gray-500">
                Last check: {service.lastCheck}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const SettingsDashboard = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">System Settings</h1>
      
      <div className="grid gap-6">
        <div className="bg-black/50 border border-white/10 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Detection Rules</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Suspicious Login Detection</span>
              <Badge className="bg-green-500/20 text-green-400 border-green-500/30">Enabled</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Privilege Escalation Detection</span>
              <Badge className="bg-green-500/20 text-green-400 border-green-500/30">Enabled</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Data Exfiltration Detection</span>
              <Badge className="bg-green-500/20 text-green-400 border-green-500/30">Enabled</Badge>
            </div>
          </div>
        </div>
        
        <div className="bg-black/50 border border-white/10 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Notification Settings</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Critical Alert Notifications</span>
              <Badge className="bg-green-500/20 text-green-400 border-green-500/30">Enabled</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Daily Summary Reports</span>
              <Badge className="bg-green-500/20 text-green-400 border-green-500/30">Enabled</Badge>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Utility Components
const MetricCard = ({ title, value, icon, trend, color }: {
  title: string;
  value: string;
  icon: React.ReactNode;
  trend: string;
  color: string;
}) => (
  <div className="bg-black/50 border border-white/10 rounded-xl p-6 backdrop-blur-sm">
    <div className="flex items-center justify-between mb-2">
      {icon}
      <span className={cn(
        "text-xs px-2 py-1 rounded",
        color === 'blue' && "bg-blue-500/20 text-blue-400",
        color === 'green' && "bg-green-500/20 text-green-400",
        color === 'orange' && "bg-orange-500/20 text-orange-400",
        color === 'purple' && "bg-purple-500/20 text-purple-400"
      )}>
        {trend}
      </span>
    </div>
    <div className="text-2xl font-bold text-white mb-1">{value}</div>
    <div className="text-sm text-gray-400">{title}</div>
  </div>
);

const AgentStatusCard = ({ agent }: { agent: Agent }) => (
  <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
    <div className="flex items-center gap-3">
      <div className={cn(
        "w-3 h-3 rounded-full",
        agent.status === 'active' && "bg-green-400",
        agent.status === 'idle' && "bg-yellow-400",
        agent.status === 'error' && "bg-red-400"
      )} />
      <div>
        <p className="text-white font-medium">{agent.name}</p>
        <p className="text-xs text-gray-400">{agent.currentTask || 'Idle'}</p>
      </div>
    </div>
    <div className="text-right">
      <p className="text-sm text-gray-300">{agent.efficiency}%</p>
      <p className="text-xs text-gray-500">{agent.lastActivity}</p>
    </div>
  </div>
);

const DashboardContent = ({ selectedView }: { selectedView: string }) => {
  const renderContent = () => {
    switch (selectedView) {
      case "overview":
        return <OverviewDashboard />;
      case "logs":
        return <LiveLogsDashboard />;
      case "audit":
        return <AuditTrailDashboard />;
      case "incidents":
        return <IncidentsDashboard />;
      case "agents":
        return <AgentStatusDashboard />;
      case "communications":
        return <CommunicationsDashboard />;
      case "gcp":
        return <GCPServicesDashboard />;
      case "settings":
        return <SettingsDashboard />;
      default:
        return <OverviewDashboard />;
    }
  };

  return (
    <div className="flex flex-1">
      <div className="p-4 md:p-8 rounded-tl-2xl border border-white/10 bg-black flex flex-col gap-4 flex-1 w-full h-full overflow-y-auto relative">
        {renderContent()}
      </div>
    </div>
  );
};

export function SentinelOpsDashboardDemo() {
  const [selectedView, setSelectedView] = useState("overview");
  
  const links = [
    {
      label: "Overview",
      href: "#",
      icon: <LayoutDashboard className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
      id: "overview"
    },
    {
      label: "Live Logs",
      href: "#",
      icon: <Terminal className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
      id: "logs"
    },
    {
      label: "Audit Trail",
      href: "#",
      icon: <FileText className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
      id: "audit"
    },
    {
      label: "Incidents",
      href: "#",
      icon: <AlertTriangle className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
      id: "incidents"
    },
    {
      label: "Agent Status",
      href: "#",
      icon: <Activity className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
      id: "agents"
    },
    {
      label: "Communications",
      href: "#",
      icon: <MessageSquare className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
      id: "communications"
    },
    {
      label: "GCP Services",
      href: "#",
      icon: <Cloud className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
      id: "gcp"
    },
    {
      label: "Settings",
      href: "#",
      icon: <Settings className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
      id: "settings"
    },
  ];

  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-lg flex flex-col md:flex-row bg-black w-full flex-1 border border-white/10 h-[80vh] relative">
      <Sidebar open={open} setOpen={setOpen}>
        <SidebarBody className="justify-between gap-10">
          <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
            {open ? <SentinelOpsLogo /> : <SentinelOpsLogoIcon />}
            <div className="mt-8 flex flex-col gap-2">
              {links.map((link, idx) => (
                <div
                  key={idx}
                  onClick={() => setSelectedView(link.id)}
                  className={cn(
                    "cursor-pointer",
                    selectedView === link.id && "bg-blue-500/20 border border-blue-500/30 rounded-md"
                  )}
                >
                  <SidebarLink link={link} />
                </div>
              ))}
            </div>
          </div>
          <div>
            <SidebarLink
              link={{
                label: "Security Admin",
                href: "#",
                icon: (
                  <div className="h-7 w-7 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
                    SA
                  </div>
                ),
              }}
            />
          </div>
        </SidebarBody>
      </Sidebar>
      <DashboardContent selectedView={selectedView} />
    </div>
  );
} 