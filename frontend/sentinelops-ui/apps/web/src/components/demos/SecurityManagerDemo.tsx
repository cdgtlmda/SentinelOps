"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity, 
  Users, 
  CheckCircle, 
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Clock,
  Shield,
  FileText,
  BarChart3,
  PieChart,
  Target,
  Zap,
  Eye,
  Settings,
  AlertCircle,
  CheckSquare,
  XCircle,
  UserCheck,
  Calendar,
  Briefcase
} from 'lucide-react';

interface SecurityManagerDemoProps {
  scenario: 'dashboard' | 'workflow' | 'compliance';
}

interface Metric {
  label: string;
  value: string | number;
  change: number;
  trend: 'up' | 'down' | 'stable';
  color: string;
}

interface Incident {
  id: string;
  title: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'OPEN' | 'INVESTIGATING' | 'RESOLVED' | 'CLOSED';
  assignee: string;
  created: string;
  updated: string;
  category: string;
}

interface ComplianceFramework {
  name: string;
  score: number;
  status: 'COMPLIANT' | 'PARTIAL' | 'NON_COMPLIANT';
  lastAudit: string;
  findings: number;
  controls: {
    total: number;
    passed: number;
    failed: number;
    pending: number;
  };
}

const SecurityManagerDemo: React.FC<SecurityManagerDemoProps> = ({ scenario }) => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [selectedIncident, setSelectedIncident] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Update time every second for dashboard
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Sample data
  const dashboardMetrics: Metric[] = [
    { label: 'Active Threats', value: 3, change: -2, trend: 'down', color: 'text-red-400' },
    { label: 'Resolved Today', value: 15, change: 8, trend: 'up', color: 'text-green-400' },
    { label: 'Response Time', value: '2.3m', change: -15, trend: 'down', color: 'text-blue-400' },
    { label: 'Coverage Score', value: '98.7%', change: 2, trend: 'up', color: 'text-purple-400' }
  ];

  const incidents: Incident[] = [
    {
      id: 'INC-001',
      title: 'Suspicious Login from North Korea',
      severity: 'HIGH',
      status: 'INVESTIGATING',
      assignee: 'Sarah Chen',
      created: '2024-01-15T10:30:00Z',
      updated: '2024-01-15T11:45:00Z',
      category: 'Authentication'
    },
    {
      id: 'INC-002',
      title: 'Privilege Escalation Attempt',
      severity: 'CRITICAL',
      status: 'OPEN',
      assignee: 'Mike Johnson',
      created: '2024-01-15T09:15:00Z',
      updated: '2024-01-15T09:15:00Z',
      category: 'IAM'
    },
    {
      id: 'INC-003',
      title: 'Unusual Data Transfer Pattern',
      severity: 'MEDIUM',
      status: 'RESOLVED',
      assignee: 'Alex Rodriguez',
      created: '2024-01-14T14:20:00Z',
      updated: '2024-01-15T08:30:00Z',
      category: 'Data Protection'
    }
  ];

  const complianceFrameworks: ComplianceFramework[] = [
    {
      name: 'SOC 2 Type II',
      score: 94,
      status: 'COMPLIANT',
      lastAudit: '2024-01-01',
      findings: 2,
      controls: { total: 150, passed: 145, failed: 2, pending: 3 }
    },
    {
      name: 'ISO 27001',
      score: 87,
      status: 'PARTIAL',
      lastAudit: '2023-12-15',
      findings: 8,
      controls: { total: 114, passed: 98, failed: 8, pending: 8 }
    },
    {
      name: 'GDPR',
      score: 96,
      status: 'COMPLIANT',
      lastAudit: '2024-01-10',
      findings: 1,
      controls: { total: 25, passed: 24, failed: 1, pending: 0 }
    }
  ];

  const refreshData = async () => {
    setRefreshing(true);
    await new Promise(resolve => setTimeout(resolve, 1500));
    setRefreshing(false);
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OPEN': return 'text-red-400 bg-red-500/10';
      case 'INVESTIGATING': return 'text-yellow-400 bg-yellow-500/10';
      case 'RESOLVED': return 'text-green-400 bg-green-500/10';
      case 'CLOSED': return 'text-gray-400 bg-gray-500/10';
      default: return 'text-gray-400 bg-gray-500/10';
    }
  };

  const getComplianceColor = (status: string) => {
    switch (status) {
      case 'COMPLIANT': return 'text-green-400 bg-green-500/10';
      case 'PARTIAL': return 'text-yellow-400 bg-yellow-500/10';
      case 'NON_COMPLIANT': return 'text-red-400 bg-red-500/10';
      default: return 'text-gray-400 bg-gray-500/10';
    }
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10">
        <div>
          <h3 className="text-lg font-semibold text-white">Security Operations Center</h3>
          <p className="text-sm text-gray-400">Real-time security monitoring and threat intelligence</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-sm text-gray-400">Last Updated</div>
            <div className="text-white font-mono">{currentTime.toLocaleTimeString()}</div>
          </div>
          <button
            onClick={refreshData}
            disabled={refreshing}
            className="px-4 py-2 text-sm bg-green-500 hover:bg-green-600 disabled:bg-gray-500 rounded-lg transition-colors text-white flex items-center gap-2"
          >
            {refreshing ? (
              <>
                <Activity className="w-4 h-4 animate-spin" />
                Refreshing...
              </>
            ) : (
              <>
                <Activity className="w-4 h-4" />
                Refresh
              </>
            )}
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {dashboardMetrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="p-4 bg-white/5 rounded-lg border border-white/10"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-gray-400">{metric.label}</div>
              <div className={`flex items-center gap-1 text-xs ${
                metric.trend === 'up' ? 'text-green-400' : 
                metric.trend === 'down' ? 'text-red-400' : 'text-gray-400'
              }`}>
                {metric.trend === 'up' && <TrendingUp className="w-3 h-3" />}
                {metric.trend === 'down' && <TrendingDown className="w-3 h-3" />}
                {metric.change !== 0 && `${metric.change > 0 ? '+' : ''}${metric.change}%`}
              </div>
            </div>
            <div className={`text-2xl font-bold ${metric.color}`}>
              {metric.value}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Live Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-green-400" />
            Live Security Activity
          </h4>
          
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {[
              { time: '11:47', event: 'Data exfiltration attempt blocked', type: 'blocked', severity: 'HIGH' },
              { time: '11:45', event: 'Suspicious login detected - North Korea', type: 'detected', severity: 'HIGH' },
              { time: '11:42', event: 'Privilege escalation attempt in progress', type: 'investigating', severity: 'CRITICAL' },
              { time: '11:40', event: 'Automated firewall rule deployed', type: 'resolved', severity: 'MEDIUM' },
              { time: '11:38', event: 'Compliance scan completed - SOC 2', type: 'info', severity: 'LOW' },
              { time: '11:35', event: 'Threat intelligence feed updated', type: 'info', severity: 'LOW' }
            ].map((activity, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-center gap-3 p-3 bg-white/5 rounded-lg border border-white/10"
              >
                <div className="text-xs text-gray-400 font-mono w-12">{activity.time}</div>
                <div className={`w-2 h-2 rounded-full ${
                  activity.type === 'blocked' ? 'bg-red-400' :
                  activity.type === 'detected' ? 'bg-orange-400' :
                  activity.type === 'investigating' ? 'bg-yellow-400' :
                  activity.type === 'resolved' ? 'bg-green-400' : 'bg-blue-400'
                }`} />
                <div className="flex-1">
                  <div className="text-sm text-white">{activity.event}</div>
                  <div className={`text-xs px-2 py-1 rounded-full w-fit mt-1 ${getSeverityColor(activity.severity)}`}>
                    {activity.severity}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Threat Intelligence */}
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-white flex items-center gap-2">
            <Target className="w-5 h-5 text-purple-400" />
            Threat Intelligence
          </h4>
          
          <div className="space-y-3">
            <div className="p-4 bg-gradient-to-r from-red-500/10 to-orange-500/10 rounded-lg border border-red-500/20">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-red-400" />
                <span className="text-sm font-medium text-white">Active Threat Campaigns</span>
              </div>
              <div className="text-xs text-gray-300">
                2 APT groups targeting cloud infrastructure detected in the last 24 hours
              </div>
            </div>
            
            <div className="p-4 bg-gradient-to-r from-yellow-500/10 to-orange-500/10 rounded-lg border border-yellow-500/20">
              <div className="flex items-center gap-2 mb-2">
                <Eye className="w-4 h-4 text-yellow-400" />
                <span className="text-sm font-medium text-white">Vulnerability Alerts</span>
              </div>
              <div className="text-xs text-gray-300">
                3 new CVEs affecting your infrastructure - auto-patching in progress
              </div>
            </div>
            
            <div className="p-4 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-lg border border-blue-500/20">
              <div className="flex items-center gap-2 mb-2">
                <Shield className="w-4 h-4 text-blue-400" />
                <span className="text-sm font-medium text-white">Protective Measures</span>
              </div>
              <div className="text-xs text-gray-300">
                12 new firewall rules deployed based on threat intelligence
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderWorkflow = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10">
        <div>
          <h3 className="text-lg font-semibold text-white">Incident Response Workflow</h3>
          <p className="text-sm text-gray-400">Manage and coordinate security incident response</p>
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2 text-sm bg-blue-500 hover:bg-blue-600 rounded-lg transition-colors text-white">
            Create Incident
          </button>
          <button className="px-4 py-2 text-sm bg-green-500 hover:bg-green-600 rounded-lg transition-colors text-white">
            Export Report
          </button>
        </div>
      </div>

      {/* Incident List */}
      <div className="space-y-4">
        <h4 className="text-lg font-semibold text-white flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-orange-400" />
          Active Incidents
        </h4>
        
        <div className="space-y-3">
          {incidents.map((incident, index) => (
            <motion.div
              key={incident.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`p-4 bg-white/5 rounded-lg border border-white/10 cursor-pointer transition-all duration-200 ${
                selectedIncident === incident.id ? 'ring-2 ring-green-400 bg-green-400/10' : 'hover:bg-white/10'
              }`}
              onClick={() => setSelectedIncident(selectedIncident === incident.id ? null : incident.id)}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="font-mono text-sm text-blue-400">{incident.id}</div>
                  <div className={`px-2 py-1 text-xs rounded-full ${getSeverityColor(incident.severity)}`}>
                    {incident.severity}
                  </div>
                  <div className={`px-2 py-1 text-xs rounded-full ${getStatusColor(incident.status)}`}>
                    {incident.status}
                  </div>
                </div>
                <div className="text-xs text-gray-400">
                  {new Date(incident.created).toLocaleDateString()}
                </div>
              </div>
              
              <h5 className="text-white font-medium mb-2">{incident.title}</h5>
              
              <div className="grid grid-cols-3 gap-4 text-xs">
                <div>
                  <span className="text-gray-400">Assignee: </span>
                  <span className="text-white">{incident.assignee}</span>
                </div>
                <div>
                  <span className="text-gray-400">Category: </span>
                  <span className="text-white">{incident.category}</span>
                </div>
                <div>
                  <span className="text-gray-400">Updated: </span>
                  <span className="text-white">{new Date(incident.updated).toLocaleTimeString()}</span>
                </div>
              </div>

              {/* Expanded Details */}
              <AnimatePresence>
                {selectedIncident === incident.id && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-4 pt-4 border-t border-white/10"
                  >
                    <div className="space-y-3">
                      <div className="flex gap-4">
                        <button className="px-3 py-1 text-xs bg-blue-500 hover:bg-blue-600 rounded transition-colors text-white">
                          Assign to Me
                        </button>
                        <button className="px-3 py-1 text-xs bg-green-500 hover:bg-green-600 rounded transition-colors text-white">
                          Update Status
                        </button>
                        <button className="px-3 py-1 text-xs bg-purple-500 hover:bg-purple-600 rounded transition-colors text-white">
                          Add Evidence
                        </button>
                      </div>
                      
                      <div className="bg-white/5 rounded p-3">
                        <div className="text-xs text-gray-400 mb-2">Timeline</div>
                        <div className="space-y-2 text-xs">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-green-400 rounded-full" />
                            <span className="text-gray-300">Incident created - automated detection</span>
                            <span className="text-gray-400">{new Date(incident.created).toLocaleString()}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-yellow-400 rounded-full" />
                            <span className="text-gray-300">Assigned to {incident.assignee}</span>
                            <span className="text-gray-400">{new Date(incident.updated).toLocaleString()}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderCompliance = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10">
        <div>
          <h3 className="text-lg font-semibold text-white">Compliance Management</h3>
          <p className="text-sm text-gray-400">Automated compliance monitoring and reporting</p>
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2 text-sm bg-blue-500 hover:bg-blue-600 rounded-lg transition-colors text-white">
            Run Audit
          </button>
          <button className="px-4 py-2 text-sm bg-green-500 hover:bg-green-600 rounded-lg transition-colors text-white">
            Generate Report
          </button>
        </div>
      </div>

      {/* Compliance Frameworks */}
      <div className="space-y-4">
        <h4 className="text-lg font-semibold text-white flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-green-400" />
          Compliance Frameworks
        </h4>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {complianceFrameworks.map((framework, index) => (
            <motion.div
              key={framework.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="p-6 bg-white/5 rounded-lg border border-white/10"
            >
              <div className="flex items-center justify-between mb-4">
                <h5 className="text-white font-semibold">{framework.name}</h5>
                <div className={`px-2 py-1 text-xs rounded-full ${getComplianceColor(framework.status)}`}>
                  {framework.status.replace('_', ' ')}
                </div>
              </div>
              
              <div className="space-y-4">
                {/* Compliance Score */}
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-400">Compliance Score</span>
                    <span className="text-white">{framework.score}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${framework.score >= 90 ? 'bg-green-400' : framework.score >= 70 ? 'bg-yellow-400' : 'bg-red-400'}`}
                      style={{ width: `${framework.score}%` }}
                    />
                  </div>
                </div>
                
                {/* Controls Summary */}
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-3 h-3 text-green-400" />
                    <span className="text-gray-400">Passed:</span>
                    <span className="text-white">{framework.controls.passed}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <XCircle className="w-3 h-3 text-red-400" />
                    <span className="text-gray-400">Failed:</span>
                    <span className="text-white">{framework.controls.failed}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-3 h-3 text-yellow-400" />
                    <span className="text-gray-400">Pending:</span>
                    <span className="text-white">{framework.controls.pending}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <FileText className="w-3 h-3 text-blue-400" />
                    <span className="text-gray-400">Total:</span>
                    <span className="text-white">{framework.controls.total}</span>
                  </div>
                </div>
                
                {/* Last Audit */}
                <div className="pt-3 border-t border-white/10">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-400">Last Audit:</span>
                    <span className="text-white">{new Date(framework.lastAudit).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between text-xs mt-1">
                    <span className="text-gray-400">Findings:</span>
                    <span className={framework.findings === 0 ? 'text-green-400' : 'text-orange-400'}>
                      {framework.findings}
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Recent Audit Activities */}
      <div className="space-y-4">
        <h4 className="text-lg font-semibold text-white flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-400" />
          Recent Audit Activities
        </h4>
        
        <div className="space-y-3">
          {[
            { time: '10:30', activity: 'SOC 2 automated control testing completed', status: 'success', framework: 'SOC 2' },
            { time: '09:15', activity: 'ISO 27001 vulnerability assessment started', status: 'in-progress', framework: 'ISO 27001' },
            { time: '08:45', activity: 'GDPR data processing audit completed', status: 'success', framework: 'GDPR' },
            { time: 'Yesterday', activity: 'Quarterly compliance report generated', status: 'success', framework: 'All Frameworks' }
          ].map((activity, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center gap-4 p-3 bg-white/5 rounded-lg border border-white/10"
            >
              <div className="text-xs text-gray-400 font-mono w-16">{activity.time}</div>
              <div className={`w-2 h-2 rounded-full ${
                activity.status === 'success' ? 'bg-green-400' :
                activity.status === 'in-progress' ? 'bg-yellow-400' : 'bg-red-400'
              }`} />
              <div className="flex-1">
                <div className="text-sm text-white">{activity.activity}</div>
                <div className="text-xs text-gray-400">{activity.framework}</div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderScenario = () => {
    switch (scenario) {
      case 'dashboard':
        return renderDashboard();
      case 'workflow':
        return renderWorkflow();
      case 'compliance':
        return renderCompliance();
      default:
        return renderDashboard();
    }
  };

  return (
    <div className="min-h-[600px]">
      {renderScenario()}
    </div>
  );
};

export default SecurityManagerDemo; 