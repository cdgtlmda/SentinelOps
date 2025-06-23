"use client";

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { 
  Shield,
  AlertTriangle, 
  Eye, 
  Users, 
  Settings,
  ArrowRight,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  Target,
  Brain,
  Activity
} from 'lucide-react';

// Demo Components
import SecurityAnalystDemo from '@/components/demos/SecurityAnalystDemo';
import SecurityManagerDemo from '@/components/demos/SecurityManagerDemo';
import DevOpsEngineerDemo from '@/components/demos/DevOpsEngineerDemo';
import SentinelOpsDashboard from '@/components/demos/SentinelOpsDashboard';

export default function DemosPage() {
  const [selectedPerspective, setSelectedPerspective] = useState<'analyst' | 'manager' | 'devops' | 'operations'>('analyst');
  const [selectedDemo, setSelectedDemo] = useState('');

  const audienceTypes = [
    {
      id: 'analyst',
      title: 'Security Analyst',
      description: 'Experience real-time incident detection and AI-powered analysis',
      icon: <Shield className="w-6 h-6" />,
      color: 'text-blue-400'
    },
    {
      id: 'manager',
      title: 'Security Manager',
      description: 'Monitor security posture and oversee incident response workflows',
      icon: <Users className="w-6 h-6" />,
      color: 'text-green-400'
    },
    {
      id: 'devops',
      title: 'DevOps Engineer',
      description: 'See automated remediation and infrastructure protection in action',
      icon: <Settings className="w-6 h-6" />,
      color: 'text-purple-400'
    },
    {
      id: 'operations',
      title: 'Operations Dashboard',
      description: 'Comprehensive multi-agent security operations platform overview',
      icon: <Activity className="w-6 h-6" />,
      color: 'text-orange-400'
    }
  ];

  const allDemos = {
    analyst: [
      {
        id: 'suspicious-login',
        title: 'Suspicious Login Detection',
        description: 'Watch SentinelOps detect and analyze a suspicious login attempt from an unusual location',
        icon: <Eye className="w-8 h-8" />,
        glowColor: 'blue' as const,
        audience: 'See how AI correlates login patterns and geo-location data',
        scenario: 'User login from North Korea at 3 AM',
        componentType: 'SecurityAnalystDemo',
        componentProps: { scenario: 'suspicious-login' }
      },
      {
        id: 'privilege-escalation',
        title: 'Privilege Escalation Attack',
        description: 'Experience how SentinelOps detects and responds to privilege escalation attempts',
        icon: <AlertTriangle className="w-8 h-8" />,
        glowColor: 'red' as const,
        audience: 'Watch real-time detection of IAM policy changes',
        scenario: 'Unauthorized admin role assignment',
        componentType: 'SecurityAnalystDemo',
        componentProps: { scenario: 'privilege-escalation' }
      },
      {
        id: 'data-exfiltration',
        title: 'Data Exfiltration Prevention',
        description: 'See how AI detects unusual data transfer patterns and prevents data theft',
        icon: <Target className="w-8 h-8" />,
        glowColor: 'orange' as const,
        audience: 'AI analysis of network traffic patterns',
        scenario: 'Large data download to external IP',
        componentType: 'SecurityAnalystDemo',
        componentProps: { scenario: 'data-exfiltration' }
      }
    ],
    manager: [
      {
        id: 'dashboard-overview',
        title: 'Security Operations Dashboard',
        description: 'Real-time security posture monitoring across your entire Google Cloud infrastructure',
        icon: <Activity className="w-8 h-8" />,
        glowColor: 'green' as const,
        audience: 'Complete visibility into security operations',
        scenario: 'Live security metrics and trends',
        componentType: 'SecurityManagerDemo',
        componentProps: { scenario: 'dashboard' }
      },
      {
        id: 'incident-workflow',
        title: 'Incident Response Workflow',
        description: 'Manage and coordinate incident response across your security team',
        icon: <Users className="w-8 h-8" />,
        glowColor: 'blue' as const,
        audience: 'Streamlined incident management',
        scenario: 'Multi-incident coordination',
        componentType: 'SecurityManagerDemo',
        componentProps: { scenario: 'workflow' }
      },
      {
        id: 'compliance-reporting',
        title: 'Automated Compliance Reporting',
        description: 'Generate compliance reports and track security metrics automatically',
        icon: <CheckCircle className="w-8 h-8" />,
        glowColor: 'purple' as const,
        audience: 'Automated compliance documentation',
        scenario: 'SOC 2 compliance audit trail',
        componentType: 'SecurityManagerDemo',
        componentProps: { scenario: 'compliance' }
      }
    ],
    devops: [
      {
        id: 'auto-remediation',
        title: 'Automated Threat Remediation',
        description: 'Watch SentinelOps automatically contain and remediate security threats',
        icon: <Zap className="w-8 h-8" />,
        glowColor: 'yellow' as const,
        audience: 'Zero-touch incident resolution',
        scenario: 'Automatic firewall rule deployment',
        componentType: 'DevOpsEngineerDemo',
        componentProps: { scenario: 'auto-remediation' }
      },
      {
        id: 'infrastructure-protection',
        title: 'Infrastructure Hardening',
        description: 'See how SentinelOps continuously monitors and hardens your cloud infrastructure',
        icon: <Shield className="w-8 h-8" />,
        glowColor: 'green' as const,
        audience: 'Proactive security posture management',
        scenario: 'Automatic security policy enforcement',
        componentType: 'DevOpsEngineerDemo',
        componentProps: { scenario: 'infrastructure' }
      },
      {
        id: 'ai-analysis',
        title: 'AI-Powered Threat Analysis',
        description: 'Experience how Gemini AI provides contextual threat intelligence and recommendations',
        icon: <Brain className="w-8 h-8" />,
        glowColor: 'purple' as const,
        audience: 'Intelligent security insights',
        scenario: 'AI threat pattern recognition',
        componentType: 'DevOpsEngineerDemo',
        componentProps: { scenario: 'ai-analysis' }
      }
    ],
    operations: [
      {
        id: 'sentinelops-dashboard',
        title: 'SentinelOps Operations Center',
        description: 'Comprehensive multi-agent security operations dashboard with real-time monitoring',
        icon: <Activity className="w-8 h-8" />,
        glowColor: 'orange' as const,
        audience: 'Full platform overview with all agents',
        scenario: 'Live security operations monitoring',
        componentType: 'SentinelOpsDashboard',
        componentProps: {}
      }
    ]
  };

  const currentDemos = allDemos[selectedPerspective] || [];
  
  // Auto-select first demo when perspective changes
  React.useEffect(() => {
    if (currentDemos.length > 0 && currentDemos[0]) {
      setSelectedDemo(currentDemos[0].id);
    }
  }, [selectedPerspective, currentDemos]);

  const currentDemo = React.useMemo(() => {
    const found = currentDemos.find((demo: any) => demo.id === selectedDemo) || currentDemos[0] || null;
    console.log('=== CURRENT DEMO CALCULATION ===');
    console.log('Selected demo ID:', selectedDemo);
    console.log('Available demos:', currentDemos.map(d => d.id));
    console.log('Found demo:', found?.id, found?.title);
    console.log('=== END CURRENT DEMO CALCULATION ===');
    return found;
  }, [currentDemos, selectedDemo]);



  return (
    <div className="min-h-screen bg-black text-white">
      {/* Hero Section */}
      <motion.section 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="container px-4 pt-40 pb-12"
      >
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-white/10 text-green-400 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Play className="w-4 h-4" />
            Interactive Security Demos
          </div>
          <h1 className="mb-6 tracking-tight text-white">
            Explore Hands‑On
            <span className="block text-green-400">Scenarios</span>
          </h1>
                      <p className="text-lg md:text-xl text-gray-400 mb-8 max-w-4xl mx-auto leading-relaxed">
              Experience our multi-agent AI platform in action. Built on Google's ADK with five specialized agents for autonomous security operations: 
              <span className="text-white">Detection, Analysis, Remediation, Communication, and Orchestration</span> — featuring 25+ realistic threat scenarios and sub-30 second response times.
            </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/contact"
              className="inline-flex items-center gap-2 bg-white text-black px-6 py-3 rounded-lg font-medium hover:bg-gray-100 transition-colors"
            >
              Get Live Demo
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/pricing"
              className="inline-flex items-center gap-2 border border-white/20 px-6 py-3 rounded-lg font-medium hover:bg-white/10 transition-colors text-white"
            >
              View Pricing
            </Link>
          </div>
        </div>
      </motion.section>

      <div className="container px-4 py-8">
        {/* Audience Selection */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="max-w-6xl mx-auto mb-16"
        >
          <h2 className="text-3xl font-semibold text-white mb-8 text-center">
            Choose Your Role
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {audienceTypes.map((audience, index) => (
              <motion.div
                key={audience.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * index }}
                className={`cursor-pointer transition-all duration-300 ${
                  selectedPerspective === audience.id 
                    ? 'ring-2 ring-green-400' 
                    : ''
                }`}
                onClick={() => setSelectedPerspective(audience.id as 'analyst' | 'manager' | 'devops' | 'operations')}
              >
                <div className={`bg-black/50 border border-white/10 rounded-xl p-6 backdrop-blur-sm hover:border-white/20 transition-all duration-300 h-full ${
                  selectedPerspective === audience.id ? 'bg-green-400/10 border-green-400/30' : ''
                }`}>
                  <div className={`${audience.color} mb-4`}>
                    {audience.icon}
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-3">
                    {audience.title}
                  </h3>
                  <p className="text-gray-400 text-sm leading-relaxed">
                    {audience.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Demo Selection */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="max-w-6xl mx-auto mb-12"
        >
          <h3 className="text-2xl font-semibold text-white mb-8 text-center">
            Select a Security Scenario
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {currentDemos.map((demo, index) => (
              <motion.div
                key={demo.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * index }}
                className={`cursor-pointer transition-all duration-300 ${
                  selectedDemo === demo.id 
                    ? 'ring-2 ring-green-400' 
                    : ''
                }`}
                onClick={() => {
                  console.log('=== DEMO CLICK ===');
                  console.log('Clicked demo ID:', demo.id);
                  console.log('Demo title:', demo.title);
                  console.log('Component type:', demo.componentType);
                  console.log('Component props:', demo.componentProps);
                  console.log('Current selected demo before:', selectedDemo);
                  setSelectedDemo(demo.id);
                  console.log('Set selected demo to:', demo.id);
                  console.log('=== END DEMO CLICK ===');
                }}
              >
                <div className={`bg-black/50 border border-white/10 rounded-xl p-6 backdrop-blur-sm hover:border-white/20 transition-all duration-300 h-full ${
                  selectedDemo === demo.id ? 'bg-green-400/10 border-green-400/30' : ''
                }`}>
                  <div className="text-green-400 mb-4">
                    {demo.icon}
                  </div>
                  <h4 className="text-lg font-semibold text-white mb-3">
                    {demo.title}
                  </h4>
                  <p className="text-gray-400 text-sm mb-3 leading-relaxed">
                    {demo.description}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-green-400">
                    <Clock className="w-3 h-3" />
                    {demo.scenario}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Live Demo Display */}
        {currentDemo && currentDemo.componentType && (
          <motion.div
            key={`${selectedPerspective}-${selectedDemo}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="max-w-7xl mx-auto"
          >
            <div className="bg-black/50 border border-white/10 rounded-xl p-8 backdrop-blur-sm">
              <div className="text-center mb-8">
                <h4 className="text-2xl font-semibold text-white mb-3">
                  {currentDemo.title}
                </h4>
                <p className="text-gray-400 max-w-2xl mx-auto">
                  {currentDemo.audience}
                </p>
              </div>
              
              {/* Demo Component */}
              <div className="min-h-[600px]">
                {(() => {
                  console.log('Rendering component:', currentDemo.componentType, 'with props:', currentDemo.componentProps);
                  
                  if (currentDemo.componentType === 'SecurityAnalystDemo') {
                    return <SecurityAnalystDemo {...(currentDemo.componentProps as any)} />;
                  }
                  if (currentDemo.componentType === 'SecurityManagerDemo') {
                    return <SecurityManagerDemo {...(currentDemo.componentProps as any)} />;
                  }
                  if (currentDemo.componentType === 'DevOpsEngineerDemo') {
                    return <DevOpsEngineerDemo {...(currentDemo.componentProps as any)} />;
                  }
                  if (currentDemo.componentType === 'SentinelOpsDashboard') {
                    return <SentinelOpsDashboard {...(currentDemo.componentProps as any)} />;
                  }
                  
                  return <div className="text-red-400 p-4">Unknown component type: {currentDemo.componentType}</div>;
                })()}
              </div>
            </div>
          </motion.div>
        )}
      </div>


    </div>
  );
} 