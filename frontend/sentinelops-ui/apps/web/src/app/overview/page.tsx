"use client";

import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import {
  Shield,
  Zap,
  Brain,
  Eye,
  Users,
  Activity,
  AlertTriangle,
  Lock,
  Network,
  Clock,
  Target,
  CheckCircle
} from 'lucide-react';
import { AgentFlowDiagram } from '@/components/ui/agent-flow-diagram';

const features = [
  {
    Icon: Shield,
    name: "Multi-Agent Security Orchestration",
    description: "Five specialized AI agents working in perfect coordination - Detection, Analysis, Remediation, Communication, and Orchestration - powered by Google's Agent Development Kit.",
    href: "/demos",
    cta: "See How It Works",
    className: "lg:row-start-1 lg:row-end-4 lg:col-start-2 lg:col-end-3",
    details: [
      {
        title: "SentinelOpsBaseAgent Pattern",
        description: "Custom base class extending google.adk.agents.LlmAgent with built-in GCP authentication, Cloud Logging, and telemetry for all agents"
      },
      {
        title: "ADK Transfer System",
        description: "Implements TransferTo[Agent]Tool for each agent using ADK's native transfer_to_agent mechanism with full context preservation"
      },
      {
        title: "Workflow Management",
        description: "Orchestrator uses ADK's SequentialAgent pattern with WorkflowManagementTool for complex multi-step security operations"
      },
      {
        title: "Concurrent Processing",
        description: "Agents handle multiple incidents simultaneously using Python's asyncio and ADK's async tool execution"
      }
    ]
  },
  {
    Icon: Eye,
    name: "Sub-30 Second Threat Detection",
    description: "Continuous monitoring of Google Cloud infrastructure with intelligent pattern recognition and real-time threat correlation across all security events.",
    href: "/demos",
    cta: "See Demo",
    className: "lg:col-start-1 lg:col-end-2 lg:row-start-1 lg:row-end-3",
    details: [
      {
        title: "LogMonitoringTool Implementation",
        description: "Monitors BigQuery security logs using streaming queries with 5-second polling intervals for near real-time detection"
      },
      {
        title: "EventCorrelatorTool",
        description: "Correlates events across multiple GCP services using temporal and contextual patterns to reduce false positives"
      },
      {
        title: "RulesEngineTool",
        description: "YAML-based detection rules with hot-reload capability, supporting complex conditions and regex patterns"
      },
      {
        title: "DeduplicatorTool",
        description: "Prevents alert fatigue by intelligently grouping related incidents using similarity hashing"
      }
    ]
  },
  {
    Icon: Brain,
    name: "Gemini-Powered Analysis",
    description: "Advanced AI analysis using Google's Gemini models to understand attack vectors, assess impact, and provide contextual threat intelligence.",
    href: "/demos",
    cta: "Try Analysis",
    className: "lg:col-start-1 lg:col-end-2 lg:row-start-3 lg:row-end-4",
    details: [
      {
        title: "IncidentAnalysisTool",
        description: "Uses Vertex AI Gemini Pro model with custom security-focused prompts and RAG for threat intelligence"
      },
      {
        title: "ContextTool Integration",
        description: "Enriches incidents with asset metadata, historical incidents, and threat intelligence feeds from Firestore"
      },
      {
        title: "RecommendationTool",
        description: "Generates prioritized remediation steps based on MITRE ATT&CK framework and organization policies"
      },
      {
        title: "Confidence Scoring",
        description: "Multi-factor scoring system combining AI confidence, rule matches, and historical accuracy"
      }
    ]
  },
  {
    Icon: Zap,
    name: "Autonomous Remediation",
    description: "Intelligent automated response with human oversight - from network isolation to credential revocation, all executed with precision and auditability.",
    href: "/try-dashboard",
    cta: "Try Dashboard",
    className: "lg:col-start-3 lg:col-end-3 lg:row-start-1 lg:row-end-2",
    details: [
      {
        title: "BlockIPTool",
        description: "Updates GCP firewall rules using Compute Engine API with automatic rollback on failure"
      },
      {
        title: "IsolateVMTool",
        description: "Applies network isolation tags to compromised instances while preserving forensic data"
      },
      {
        title: "RevokeIAMTool",
        description: "Temporarily suspends IAM permissions with automatic restoration after investigation"
      },
      {
        title: "Dry Run Mode",
        description: "All remediation tools support --dry-run flag for safe testing in production environments"
      }
    ]
  },
  {
    Icon: Users,
    name: "Seamless Human-AI Collaboration",
    description: "Smart notifications, approval workflows, and real-time communication channels that keep security teams informed and in control of critical decisions.",
    href: "/demos",
    cta: "Explore Features",
    className: "lg:col-start-3 lg:col-end-3 lg:row-start-2 lg:row-end-4",
    details: [
      {
        title: "SlackNotificationTool",
        description: "Rich Slack messages with interactive buttons for approval workflows using Block Kit"
      },
      {
        title: "Multi-Channel Routing",
        description: "Severity-based routing to different channels (critical→pager, high→slack, medium→email)"
      },
      {
        title: "WebhookTool",
        description: "Generic webhook support for integration with existing SOC tools and SIEM systems"
      },
      {
        title: "Approval Workflows",
        description: "Human-in-the-loop controls for high-risk remediation actions with audit logging"
      }
    ]
  },
];

function BentoCard({ Icon, name, description, href, cta, className }: any) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={`group relative overflow-hidden rounded-xl border border-border bg-card p-6 hover:bg-accent/50 transition-all duration-300 ${className}`}
    >
      <div className="flex h-full flex-col justify-between">
        <div>
          <div className="mb-4 flex items-center gap-3">
            <div className="rounded-lg bg-gradient-to-r from-green-500 to-green-600 p-2">
              <Icon className="h-6 w-6 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-foreground">{name}</h3>
          </div>
          <p className="text-muted-foreground leading-relaxed">{description}</p>
        </div>
        <Link
          href={href}
          className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-green-400 hover:text-green-500 transition-colors"
        >
          {cta} →
        </Link>
      </div>
    </motion.div>
  );
}

function BentoGrid({ children, className }: any) {
  return (
    <div className={`grid auto-rows-[22rem] grid-cols-1 gap-4 lg:grid-cols-3 ${className}`}>
      {children}
    </div>
  );
}

export default function OverviewPage() {
  return (
    <div className="min-h-screen bg-background pt-24 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Hero Section */}
        <motion.section 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 bg-green-500/10 text-green-400 px-4 py-2 rounded-full text-sm font-medium mb-6 border border-green-500/20">
            <Shield className="w-4 h-4" />
            Available Q4 2025 - Join Early Access
          </div>
          <h1 className="text-foreground mb-6">
            SentinelOps <span className="text-green-400">Overview</span>
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-3xl mx-auto leading-relaxed">
            Multi-agent AI security operations platform that autonomously detects, analyzes, and responds to cloud security threats in real-time
          </p>
        </motion.section>

        {/* Introduction */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="max-w-4xl mx-auto mb-16"
        >
          <div className="prose prose-lg max-w-none">
            <p className="text-lg text-muted-foreground leading-relaxed mb-8">
              SentinelOps revolutionizes cloud security operations through intelligent multi-agent coordination. Built on Google's Agent Development Kit, our platform deploys five specialized AI agents that work together to provide comprehensive, autonomous security coverage for your Google Cloud infrastructure.
            </p>

            <h3 className="text-2xl font-semibold text-foreground mb-4">The Vision</h3>
            <p className="text-muted-foreground leading-relaxed mb-8">
              Traditional security operations centers (SOCs) struggle with alert fatigue, slow response times, and the complexity of modern cloud environments. SentinelOps envisions a future where AI agents handle the heavy lifting of security operations, allowing human experts to focus on strategic decisions and complex investigations.
            </p>

            <h3 className="text-2xl font-semibold text-foreground mb-6">Core Capabilities</h3>
          </div>
        </motion.div>

        {/* Features Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mb-16"
        >
          <BentoGrid className="lg:grid-rows-3 max-w-6xl mx-auto">
            {features.map((feature) => (
              <BentoCard key={feature.name} {...feature} />
            ))}
          </BentoGrid>
        </motion.div>

        {/* Agent Architecture Overview */}
        <AgentFlowDiagram />

        {/* Additional Features */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="max-w-4xl mx-auto"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-card border border-border rounded-xl p-6">
              <div className="flex items-center mb-4">
                <Lock className="w-8 h-8 text-green-500 mr-3" />
                <h4 className="text-xl font-semibold text-foreground">Zero-Trust Architecture</h4>
              </div>
              <p className="text-muted-foreground leading-relaxed">
                Built with security-first principles, every agent action is verified, logged, and auditable. Human oversight is maintained for critical decisions while enabling autonomous response for routine threats.
              </p>
            </div>

            <div className="bg-card border border-border rounded-xl p-6">
              <div className="flex items-center mb-4">
                <Network className="w-8 h-8 text-blue-500 mr-3" />
                <h4 className="text-xl font-semibold text-foreground">Continuous Learning</h4>
              </div>
              <p className="text-muted-foreground leading-relaxed">
                Agents continuously improve through machine learning, adapting to new threat patterns and optimizing response strategies based on your environment's unique characteristics.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}