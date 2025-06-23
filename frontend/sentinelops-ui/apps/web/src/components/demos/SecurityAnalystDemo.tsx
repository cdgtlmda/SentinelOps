"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  AlertTriangle, 
  Eye, 
  MapPin, 
  Clock,
  User,
  Activity,
  Shield,
  Zap,
  CheckCircle,
  XCircle,
  Target,
  Brain,
  AlertCircle,
  TrendingUp,
  Globe,
  Lock,
  Database,
  Network
} from 'lucide-react';

interface SecurityAnalystDemoProps {
  scenario: 'suspicious-login' | 'privilege-escalation' | 'data-exfiltration';
}

interface ThreatEvent {
  id: string;
  timestamp: string;
  type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  source: string;
  description: string;
  details: Record<string, any>;
  status: 'DETECTED' | 'ANALYZING' | 'RESOLVED' | 'BLOCKED';
}

interface AnalysisStep {
  id: string;
  step: string;
  status: 'pending' | 'active' | 'complete';
  duration: number;
  result?: string;
  confidence?: number;
}

const SecurityAnalystDemo: React.FC<SecurityAnalystDemoProps> = ({ scenario }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [events, setEvents] = useState<ThreatEvent[]>([]);
  const [analysisSteps, setAnalysisSteps] = useState<AnalysisStep[]>([]);
  const [aiInsights, setAiInsights] = useState<string[]>([]);

  // Debug logging
  console.log('SecurityAnalystDemo received scenario:', scenario);

  // Scenario configurations
  const scenarios = {
    'suspicious-login': {
      title: 'Suspicious Login Detection',
      initialEvents: [
        {
          id: '1',
          timestamp: new Date().toISOString(),
          type: 'Authentication',
          severity: 'HIGH' as const,
          source: 'IAM Audit Logs',
          description: 'Login attempt from unusual geographic location',
          details: {
            user: 'john.doe@company.com',
            location: 'Pyongyang, North Korea',
            ip: '175.45.176.0',
            previousLocation: 'San Francisco, CA',
            timeDeviation: '14 hours ahead of normal pattern',
            deviceFingerprint: 'Unknown device'
          },
          status: 'DETECTED' as const
        }
      ],
      analysisSteps: [
        { id: '1', step: 'Correlating user login patterns', status: 'pending' as const, duration: 2000 },
        { id: '2', step: 'Analyzing geographic impossibility', status: 'pending' as const, duration: 1500 },
        { id: '3', step: 'Checking device fingerprints', status: 'pending' as const, duration: 1000 },
        { id: '4', step: 'Querying threat intelligence feeds', status: 'pending' as const, duration: 2500 },
        { id: '5', step: 'Generating AI risk assessment', status: 'pending' as const, duration: 3000 }
      ],
      insights: [
        'User typically logs in from San Francisco during business hours',
        'Geographic jump of 5,000+ miles detected in 2 hours (impossible travel)',
        'Device fingerprint does not match any known user devices',
        'IP address associated with known malicious infrastructure',
        'Gemini AI Assessment: 94% confidence of credential compromise'
      ]
    },
    'privilege-escalation': {
      title: 'Privilege Escalation Attack',
      initialEvents: [
        {
          id: '1',
          timestamp: new Date().toISOString(),
          type: 'IAM Policy Change',
          severity: 'CRITICAL' as const,
          source: 'Cloud IAM Logs',
          description: 'Unauthorized admin role assignment detected',
          details: {
            user: 'service-account@project.iam.gserviceaccount.com',
            action: 'roles/editor → roles/owner',
            resource: 'projects/production-env',
            initiator: 'temp-user@company.com',
            method: 'gcloud CLI',
            timestamp: 'Outside business hours'
          },
          status: 'DETECTED' as const
        }
      ],
      analysisSteps: [
        { id: '1', step: 'Analyzing permission escalation path', status: 'pending' as const, duration: 1800 },
        { id: '2', step: 'Checking user authorization history', status: 'pending' as const, duration: 2200 },
        { id: '3', step: 'Correlating with recent security events', status: 'pending' as const, duration: 1500 },
        { id: '4', step: 'Validating business justification', status: 'pending' as const, duration: 2000 },
        { id: '5', step: 'Assessing blast radius and impact', status: 'pending' as const, duration: 2800 }
      ],
      insights: [
        'Service account elevated from Editor to Owner permissions',
        'Elevation performed by temp-user with no previous admin activity',
        'Action occurred at 2:30 AM outside normal business hours',
        'No change request or approval workflow detected',
        'Gemini AI Assessment: 96% confidence of malicious privilege escalation'
      ]
    },
    'data-exfiltration': {
      title: 'Data Exfiltration Prevention',
      initialEvents: [
        {
          id: '1',
          timestamp: new Date().toISOString(),
          type: 'Data Transfer',
          severity: 'HIGH' as const,
          source: 'VPC Flow Logs',
          description: 'Unusual large data transfer to external IP',
          details: {
            source: 'database-server-prod',
            destination: '45.33.32.156',
            dataVolume: '2.4 GB',
            duration: '15 minutes',
            protocol: 'HTTPS',
            port: '443',
            time: '11:47 PM',
            normalBaseline: '50 MB average'
          },
          status: 'DETECTED' as const
        }
      ],
      analysisSteps: [
        { id: '1', step: 'Analyzing network traffic patterns', status: 'pending' as const, duration: 2100 },
        { id: '2', step: 'Comparing against baseline behavior', status: 'pending' as const, duration: 1800 },
        { id: '3', step: 'Investigating destination IP reputation', status: 'pending' as const, duration: 2500 },
        { id: '4', step: 'Checking data classification and sensitivity', status: 'pending' as const, duration: 2000 },
        { id: '5', step: 'Calculating exfiltration risk score', status: 'pending' as const, duration: 3200 }
      ],
      insights: [
        'Data transfer 4,800% above normal baseline for this server',
        'Transfer occurred during off-hours when minimal activity expected',
        'Destination IP traced to bulletproof hosting provider',
        'Source server contains customer PII and financial records',
        'Gemini AI Assessment: 91% confidence of data exfiltration attempt'
      ]
    }
  };

  const currentScenario = scenarios[scenario];

  // Safety check - if scenario doesn't exist, use the first available scenario
  if (!currentScenario) {
    console.error('Invalid scenario:', scenario, 'Available scenarios:', Object.keys(scenarios));
    return <div className="text-red-400 p-4">Invalid scenario: {scenario}</div>;
  }

  const resetDemo = () => {
    setCurrentStep(0);
    setIsRunning(false);
    setEvents(currentScenario.initialEvents);
    setAnalysisSteps(currentScenario.analysisSteps);
    setAiInsights([]);
  };

  const startDemo = async () => {
    setIsRunning(true);
    setCurrentStep(0);
    setEvents(currentScenario.initialEvents);
    setAiInsights([]);

    // Start analysis process
    for (let i = 0; i < currentScenario.analysisSteps.length; i++) {
      setCurrentStep(i);
      
      // Update step status to active
      setAnalysisSteps(prev => prev.map((step, idx) => 
        idx === i ? { ...step, status: 'active' } : step
      ));

      // Wait for step duration
      const currentStep = currentScenario.analysisSteps?.[i];
      if (currentStep) {
        await new Promise(resolve => setTimeout(resolve, currentStep.duration));
      }

      // Complete step and add insight
      setAnalysisSteps(prev => prev.map((step, idx) => 
        idx === i ? { ...step, status: 'complete', confidence: 85 + Math.random() * 15 } : step
      ));

      const currentInsight = currentScenario.insights?.[i];
      if (currentInsight) {
        setAiInsights(prev => [...prev, currentInsight]);
      }

      // Update event status
      if (i === currentScenario.analysisSteps.length - 1) {
        setEvents(prev => prev.map(event => ({ ...event, status: 'RESOLVED' })));
      }
    }

    setIsRunning(false);
  };

  useEffect(() => {
    resetDemo();
  }, [scenario]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'text-red-400 bg-red-500/10 border-red-500/20';
      case 'HIGH': return 'text-orange-400 bg-orange-500/10 border-orange-500/20';
      case 'MEDIUM': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
      case 'LOW': return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
      default: return 'text-gray-400 bg-gray-500/10 border-gray-500/20';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'DETECTED': return <AlertTriangle className="w-4 h-4 text-orange-400" />;
      case 'ANALYZING': return <Activity className="w-4 h-4 text-blue-400 animate-pulse" />;
      case 'RESOLVED': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'BLOCKED': return <Shield className="w-4 h-4 text-red-400" />;
      default: return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Control Panel */}
      <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10">
        <div>
          <h3 className="text-lg font-semibold text-white">{currentScenario.title}</h3>
          <p className="text-sm text-gray-400">Real-time security incident analysis</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={resetDemo}
            className="px-4 py-2 text-sm bg-white/10 hover:bg-white/20 rounded-lg transition-colors text-white"
          >
            Reset
          </button>
          <button
            onClick={startDemo}
            disabled={isRunning}
            className="px-4 py-2 text-sm bg-green-500 hover:bg-green-600 disabled:bg-gray-500 rounded-lg transition-colors text-white flex items-center gap-2"
          >
            {isRunning ? (
              <>
                <Activity className="w-4 h-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4" />
                Start Analysis
              </>
            )}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Threat Detection Panel */}
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-400" />
            Threat Detection
          </h4>
          
          <div className="space-y-3">
            {events.map((event) => (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="p-4 bg-white/5 rounded-lg border border-white/10"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(event.status)}
                    <span className="font-medium text-white">{event.type}</span>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full border ${getSeverityColor(event.severity)}`}>
                    {event.severity}
                  </span>
                </div>
                
                <p className="text-sm text-gray-300 mb-3">{event.description}</p>
                
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-gray-400">Source: </span>
                    <span className="text-white">{event.source}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Time: </span>
                    <span className="text-white">{new Date(event.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>

                {/* Event Details */}
                <div className="mt-3 pt-3 border-t border-white/10">
                  <div className="grid grid-cols-1 gap-2 text-xs">
                    {Object.entries(event.details).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-gray-400 capitalize">{key.replace(/([A-Z])/g, ' $1')}:</span>
                        <span className="text-white font-mono">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* AI Analysis Panel */}
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-white flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-400" />
            AI Analysis Pipeline
          </h4>
          
          <div className="space-y-3">
            {analysisSteps.map((step, index) => (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`p-3 rounded-lg border transition-all duration-300 ${
                  step.status === 'active' 
                    ? 'bg-blue-500/10 border-blue-500/30' 
                    : step.status === 'complete'
                    ? 'bg-green-500/10 border-green-500/30'
                    : 'bg-white/5 border-white/10'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {step.status === 'active' && <Activity className="w-4 h-4 text-blue-400 animate-spin" />}
                    {step.status === 'complete' && <CheckCircle className="w-4 h-4 text-green-400" />}
                    {step.status === 'pending' && <Clock className="w-4 h-4 text-gray-400" />}
                    <span className="text-sm text-white">{step.step}</span>
                  </div>
                  {step.confidence && (
                    <span className="text-xs text-green-400">{Math.round(step.confidence)}%</span>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Insights */}
      <AnimatePresence>
        {aiInsights.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-6 bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-lg border border-purple-500/20"
          >
            <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-400" />
              Gemini AI Insights
            </h4>
            <div className="space-y-3">
              {aiInsights.map((insight, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.2 }}
                  className="flex items-start gap-3 p-3 bg-white/5 rounded-lg"
                >
                  <div className="w-2 h-2 bg-purple-400 rounded-full mt-2 flex-shrink-0" />
                  <p className="text-sm text-gray-300">{insight}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <div className="p-4 bg-white/5 rounded-lg border border-white/10 text-center">
          <div className="text-2xl font-bold text-green-400">45s</div>
          <div className="text-xs text-gray-400">Detection Time</div>
        </div>
        <div className="p-4 bg-white/5 rounded-lg border border-white/10 text-center">
          <div className="text-2xl font-bold text-blue-400">94%</div>
          <div className="text-xs text-gray-400">AI Confidence</div>
        </div>
        <div className="p-4 bg-white/5 rounded-lg border border-white/10 text-center">
          <div className="text-2xl font-bold text-purple-400">5</div>
          <div className="text-xs text-gray-400">Analysis Steps</div>
        </div>
        <div className="p-4 bg-white/5 rounded-lg border border-white/10 text-center">
          <div className="text-2xl font-bold text-orange-400">HIGH</div>
          <div className="text-xs text-gray-400">Risk Level</div>
        </div>
      </div>
    </div>
  );
};

export default SecurityAnalystDemo; 