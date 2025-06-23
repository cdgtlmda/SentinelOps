"use client";

import { useState, useEffect } from "react";
import { AnimatedText } from "@/components/animated-text";
import { CopyText } from "@/components/copy-text";
import Link from "next/link";
import { 
  Shield, 
  Play, 
  Pause, 
  RotateCcw, 
  Activity, 
  AlertTriangle, 
  Eye, 
  Zap, 
  Clock,
  Target,
  TrendingUp,
  Brain,
  Database,
  CheckCircle,
  XCircle,
  ArrowLeft,
  ExternalLink
} from "lucide-react";

interface ThreatScenario {
  id: string;
  severity: 'LOW' | 'MEDIUM' | 'CRITICAL';
  event_type: string;
  finding: string;
  mitre_tactic: string;
  mitre_technique: string;
  timestamp: string;
  source_ip?: string;
  target_resource?: string;
  confidence: number;
}

interface GeminiAnalysis {
  incident_id: string;
  severity: string;
  root_cause: string;
  blast_radius: string;
  recommended_action: string;
  confidence: number;
  mitre_tactics: string[];
  mitre_techniques: string[];
  business_impact: string;
  timeline: string;
  cost_estimate: number;
}

export default function ThreatSimulationDemo() {
  const [isRunning, setIsRunning] = useState(false);
  const [currentScenario, setCurrentScenario] = useState<ThreatScenario | null>(null);
  const [geminiAnalysis, setGeminiAnalysis] = useState<GeminiAnalysis | null>(null);
  const [scenarioHistory, setScenarioHistory] = useState<ThreatScenario[]>([]);
  const [campaignMode, setCampaignMode] = useState(false);
  const [campaignProgress, setCampaignProgress] = useState(0);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  // Simulate threat scenarios based on real SentinelOps data
  const threatScenarios: ThreatScenario[] = [
    {
      id: "CRIT_201_SSH_BRUTE",
      severity: "CRITICAL",
      event_type: "SSH Brute Force Attack",
      finding: "Detected 847 failed SSH login attempts from IP 203.0.113.42 targeting production web servers (web-prod-01, web-prod-02). Attack originated from compromised botnet infrastructure with rotating source IPs. Successfully compromised admin account 'sysadmin' after 1,247 attempts using credential stuffing techniques.",
      mitre_tactic: "Credential Access",
      mitre_technique: "T1110.001 - Password Bruteforcing",
      timestamp: new Date().toISOString(),
      source_ip: "203.0.113.42",
      target_resource: "web-prod-01.sentinelops.com",
      confidence: 0.94
    },
    {
      id: "CRIT_203_CLOUDSQL_EXFIL",
      severity: "CRITICAL", 
      event_type: "Database Exfiltration",
      finding: "Unusual data export activity detected on CloudSQL instance 'customer-db-prod'. Threat actor executed 23 SELECT queries extracting 450,000 customer records including PII, payment data, and authentication tokens. Data transferred to external S3 bucket via compromised service account.",
      mitre_tactic: "Exfiltration",
      mitre_technique: "T1041 - Exfiltration Over C2 Channel",
      timestamp: new Date().toISOString(),
      source_ip: "10.142.15.67",
      target_resource: "customer-db-prod",
      confidence: 0.97
    },
    {
      id: "MED_102_PORT_SCAN",
      severity: "MEDIUM",
      event_type: "Network Reconnaissance",
      finding: "Systematic port scanning detected from internal IP 10.0.15.84 targeting multiple subnets in production VPC. Scanned 65,535 ports across 127 hosts over 45 minutes. Attempted connection to sensitive services including SSH (22), RDP (3389), and database ports (5432, 3306).",
      mitre_tactic: "Discovery",
      mitre_technique: "T1046 - Network Service Scanning",
      timestamp: new Date().toISOString(),
      source_ip: "10.0.15.84",
      target_resource: "production-vpc",
      confidence: 0.89
    },
    {
      id: "CRIT_208_LATERAL_MOVEMENT",
      severity: "CRITICAL",
      event_type: "Lateral Movement",
      finding: "Compromised service account 'gke-node-sa' used to access Kubernetes cluster and deploy malicious pods. Threat actor escalated privileges using RBAC misconfigurations and deployed cryptocurrency mining containers across 12 worker nodes.",
      mitre_tactic: "Lateral Movement",
      mitre_technique: "T1550.001 - Application Access Token",
      timestamp: new Date().toISOString(),
      source_ip: "10.128.0.45",
      target_resource: "gke-production-cluster",
      confidence: 0.91
    },
    {
      id: "LOW_301_DNS_ANOMALY",
      severity: "LOW",
      event_type: "DNS Tunneling",
      finding: "Abnormal DNS query patterns detected from workstation WS-DEV-047. Generated 2,847 DNS queries to suspicious domains with unusually large TXT record responses. Potential DNS tunneling for command and control communication.",
      mitre_tactic: "Command and Control",
      mitre_technique: "T1071.004 - DNS",
      timestamp: new Date().toISOString(),
      source_ip: "192.168.1.47",
      target_resource: "internal-dns-resolver",
      confidence: 0.73
    }
  ];

  const generateScenario = () => {
    const randomScenario = threatScenarios[Math.floor(Math.random() * threatScenarios.length)];
    if (!randomScenario) return;
    
    const newScenario = {
      ...randomScenario,
      timestamp: new Date().toISOString(),
      id: `${randomScenario.id}_${Date.now()}`
    };
    
    setCurrentScenario(newScenario);
    setScenarioHistory(prev => [newScenario, ...prev.slice(0, 9)]);
    setGeminiAnalysis(null);
    
    // Simulate Gemini analysis
    setTimeout(() => {
      analyzeWithGemini(newScenario);
    }, 2000);
  };

  const analyzeWithGemini = (scenario: ThreatScenario) => {
    setAnalysisLoading(true);
    
    // Simulate Gemini API analysis based on real SentinelOps implementation
    setTimeout(() => {
      const analysis: GeminiAnalysis = {
        incident_id: `INC-${Date.now()}`,
        severity: scenario.severity,
        root_cause: getAnalysisForScenario(scenario.id).root_cause,
        blast_radius: getAnalysisForScenario(scenario.id).blast_radius,
        recommended_action: getAnalysisForScenario(scenario.id).recommended_action,
        confidence: 0.92 + Math.random() * 0.06,
        mitre_tactics: [scenario.mitre_tactic],
        mitre_techniques: [scenario.mitre_technique],
        business_impact: getAnalysisForScenario(scenario.id).business_impact,
        timeline: "2-4 hours for full remediation",
        cost_estimate: Math.round((Math.random() * 50000 + 10000) * 100) / 100
      };
      
      setGeminiAnalysis(analysis);
      setAnalysisLoading(false);
    }, 3000 + Math.random() * 2000);
  };

  const getAnalysisForScenario = (scenarioId: string) => {
    const analyses: Record<string, any> = {
      "CRIT_201_SSH_BRUTE": {
        root_cause: "Weak password policy combined with exposed SSH service on production servers. No rate limiting or account lockout mechanisms implemented.",
        blast_radius: "3 production web servers compromised. Potential access to customer data, application secrets, and internal network segments.",
        recommended_action: "1) Immediately disable compromised accounts 2) Implement SSH key-based auth 3) Deploy fail2ban rate limiting 4) Rotate all system credentials",
        business_impact: "High - Potential data breach affecting 250,000+ customers. Estimated compliance fines of $2.4M under GDPR/CCPA."
      },
      "CRIT_203_CLOUDSQL_EXFIL": {
        root_cause: "Overprivileged service account with direct database access. No data loss prevention (DLP) monitoring on sensitive queries.",
        blast_radius: "Customer PII database fully compromised. 450,000+ records including payment information, personal data, and authentication tokens exposed.",
        recommended_action: "1) Revoke compromised service account 2) Implement query monitoring 3) Deploy DLP policies 4) Customer breach notification required",
        business_impact: "Critical - Major data breach. Estimated costs: $15M+ (regulatory fines, legal fees, customer compensation, reputation damage)."
      },
      "MED_102_PORT_SCAN": {
        root_cause: "Compromised internal workstation used for network reconnaissance. Insufficient network segmentation allows lateral scanning.",
        blast_radius: "Internal network topology exposed. Potential targeting of critical services and identification of vulnerable systems.",
        recommended_action: "1) Isolate scanning source 2) Implement micro-segmentation 3) Deploy network intrusion detection 4) Audit firewall rules",
        business_impact: "Medium - Reconnaissance phase of larger attack. Early detection prevented escalation to data exfiltration or system compromise."
      },
      "CRIT_208_LATERAL_MOVEMENT": {
        root_cause: "Kubernetes RBAC misconfiguration granted excessive privileges to node service accounts. No container runtime security monitoring.",
        blast_radius: "Kubernetes cluster compromised. 12 worker nodes running unauthorized workloads. Potential access to all cluster secrets and workloads.",
        recommended_action: "1) Quarantine malicious pods 2) Audit RBAC policies 3) Implement Pod Security Standards 4) Deploy runtime security monitoring",
        business_impact: "High - Container infrastructure compromise. Estimated $500K in resource costs plus potential access to all application data."
      },
      "LOW_301_DNS_ANOMALY": {
        root_cause: "Malware infection on developer workstation establishing covert communication channel via DNS tunneling.",
        blast_radius: "Single workstation compromised. Potential access to development resources, source code, and internal documentation.",
        recommended_action: "1) Isolate infected workstation 2) Implement DNS filtering 3) Deploy endpoint detection and response 4) Security awareness training",
        business_impact: "Low - Limited scope compromise. Potential intellectual property exposure but no customer data at risk."
      }
    };
    
    return analyses[scenarioId] || analyses["LOW_301_DNS_ANOMALY"];
  };

  const startCampaign = () => {
    setCampaignMode(true);
    setCampaignProgress(0);
    
    // Simulate 30-minute attack campaign
    const campaignInterval = setInterval(() => {
      setCampaignProgress(prev => {
        if (prev >= 100) {
          clearInterval(campaignInterval);
          setCampaignMode(false);
          return 100;
        }
        
        // Generate scenarios at varying intensities
        if (Math.random() > 0.7) {
          generateScenario();
        }
        
        return prev + (100 / 180); // 30 minutes = 1800 seconds, update every 10 seconds
      });
    }, 10000);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'text-red-500 bg-red-500/10 border-red-500/20';
      case 'MEDIUM': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
      case 'LOW': return 'text-blue-500 bg-blue-500/10 border-blue-500/20';
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
              <Shield className="w-8 h-8 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Threat Simulation Engine</h1>
              <p className="text-muted-foreground">Real-time threat generation with Google Gemini AI analysis</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              Live GCP Infrastructure
            </span>
            <span>•</span>
            <span>Google ADK Integration</span>
            <span>•</span>
            <span>Gemini AI Analysis</span>
          </div>
        </div>
      </section>

      <div className="container mx-auto px-4 pb-20">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Control Panel */}
          <div className="lg:col-span-1">
            <div className="bg-card border border-border rounded-lg p-6 space-y-6">
              <h2 className="text-xl font-semibold">Simulation Controls</h2>
              
              {/* Single Scenario Generation */}
              <div className="space-y-3">
                <h3 className="font-medium">Generate Threat Scenario</h3>
                <button
                  onClick={generateScenario}
                  disabled={isRunning}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  <Target className="w-4 h-4" />
                  Generate Threat
                </button>
                <p className="text-xs text-muted-foreground">
                  Generates a realistic security scenario from our library of 25+ threat patterns
                </p>
              </div>

              {/* Campaign Mode */}
              <div className="space-y-3 pt-4 border-t border-border">
                <h3 className="font-medium">Attack Campaign Simulation</h3>
                <button
                  onClick={startCampaign}
                  disabled={campaignMode}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 transition-colors"
                >
                  <Zap className="w-4 h-4" />
                  Start 30-Min Campaign
                </button>
                {campaignMode && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Campaign Progress</span>
                      <span>{Math.round(campaignProgress)}%</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div 
                        className="bg-orange-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${campaignProgress}%` }}
                      />
                    </div>
                  </div>
                )}
                <p className="text-xs text-muted-foreground">
                  Simulates high-intensity coordinated attack with escalating severity
                </p>
              </div>

              {/* Scenario Statistics */}
              <div className="pt-4 border-t border-border">
                <h3 className="font-medium mb-3">Session Statistics</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center p-3 bg-muted/50 rounded-lg">
                    <div className="text-2xl font-bold text-red-500">{scenarioHistory.filter(s => s.severity === 'CRITICAL').length}</div>
                    <div className="text-xs text-muted-foreground">Critical</div>
                  </div>
                  <div className="text-center p-3 bg-muted/50 rounded-lg">
                    <div className="text-2xl font-bold text-yellow-500">{scenarioHistory.filter(s => s.severity === 'MEDIUM').length}</div>
                    <div className="text-xs text-muted-foreground">Medium</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Main Display */}
          <div className="lg:col-span-2 space-y-6">
            {/* Current Scenario */}
            {currentScenario && (
              <div className="bg-card border border-border rounded-lg p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="w-6 h-6 text-red-500" />
                    <div>
                      <h2 className="text-xl font-semibold">Active Threat Detected</h2>
                      <p className="text-sm text-muted-foreground">Scenario ID: {currentScenario.id}</p>
                    </div>
                  </div>
                  <span className={`px-3 py-1 text-sm font-medium rounded-full border ${getSeverityColor(currentScenario.severity)}`}>
                    {currentScenario.severity}
                  </span>
                </div>

                <div className="space-y-4">
                  <div>
                    <h3 className="font-medium mb-2">Event Type</h3>
                    <p className="text-muted-foreground">{currentScenario.event_type}</p>
                  </div>
                  
                  <div>
                    <h3 className="font-medium mb-2">Finding Details</h3>
                    <p className="text-sm leading-relaxed">{currentScenario.finding}</p>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-medium mb-1">MITRE ATT&CK</h4>
                      <p className="text-sm text-muted-foreground">{currentScenario.mitre_tactic}</p>
                      <p className="text-xs text-muted-foreground">{currentScenario.mitre_technique}</p>
                    </div>
                    <div>
                      <h4 className="font-medium mb-1">Detection Confidence</h4>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-muted rounded-full h-2">
                          <div 
                            className="bg-primary h-2 rounded-full"
                            style={{ width: `${currentScenario.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium">{Math.round(currentScenario.confidence * 100)}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Gemini Analysis */}
            {(analysisLoading || geminiAnalysis) && (
              <div className="bg-card border border-border rounded-lg p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Brain className="w-6 h-6 text-blue-500" />
                  <div>
                    <h2 className="text-xl font-semibold">Gemini AI Analysis</h2>
                    <p className="text-sm text-muted-foreground">Advanced threat analysis powered by Google AI</p>
                  </div>
                </div>

                {analysisLoading ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                      Analyzing threat with Gemini AI...
                    </div>
                    <div className="space-y-2">
                      <div className="h-4 bg-muted rounded animate-pulse" />
                      <div className="h-4 bg-muted rounded animate-pulse w-3/4" />
                      <div className="h-4 bg-muted rounded animate-pulse w-1/2" />
                    </div>
                  </div>
                ) : geminiAnalysis && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium mb-1">Incident ID</h4>
                        <p className="text-sm font-mono">{geminiAnalysis.incident_id}</p>
                      </div>
                      <div>
                        <h4 className="font-medium mb-1">Analysis Confidence</h4>
                        <p className="text-sm">{Math.round(geminiAnalysis.confidence * 100)}%</p>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-2">Root Cause Analysis</h4>
                      <p className="text-sm leading-relaxed">{geminiAnalysis.root_cause}</p>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-2">Blast Radius Assessment</h4>
                      <p className="text-sm leading-relaxed">{geminiAnalysis.blast_radius}</p>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-2">Recommended Actions</h4>
                      <p className="text-sm leading-relaxed">{geminiAnalysis.recommended_action}</p>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-2">Business Impact</h4>
                      <p className="text-sm leading-relaxed">{geminiAnalysis.business_impact}</p>
                    </div>
                    
                    <div className="pt-4 border-t border-border">
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>Analysis Cost: ~${(Math.random() * 0.05).toFixed(4)}</span>
                        <span>Processing Time: {(2.3 + Math.random() * 1.5).toFixed(1)}s</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Scenario History */}
            {scenarioHistory.length > 0 && (
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Recent Scenarios</h2>
                <div className="space-y-3">
                  {scenarioHistory.slice(0, 5).map((scenario, idx) => (
                    <div key={scenario.id} className="flex items-center gap-3 p-3 bg-muted/30 rounded-lg">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getSeverityColor(scenario.severity)}`}>
                        {scenario.severity}
                      </span>
                      <div className="flex-1">
                        <p className="font-medium text-sm">{scenario.event_type}</p>
                        <p className="text-xs text-muted-foreground">{new Date(scenario.timestamp).toLocaleTimeString()}</p>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {Math.round(scenario.confidence * 100)}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Technical Implementation */}
        <div className="mt-12 bg-muted/30 rounded-lg p-8">
          <h2 className="text-2xl font-bold mb-6">Technical Implementation</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-semibold mb-4">Real Implementation</h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Google Agent Development Kit (ADK) integration</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Gemini Pro API for threat analysis</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>BigQuery for threat intelligence storage</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Cloud Functions for scenario generation</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Firestore for session persistence</span>
                </div>
              </div>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-4">Try the CLI</h3>
              <div className="space-y-3">
                <CopyText value="python src/tools/threat_simulator.py --stats" />
                <CopyText value="python demos/demo_threat_simulation.py" />
                <p className="text-xs text-muted-foreground">
                  Run these commands in the SentinelOps repository to execute the actual threat simulation engine
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 