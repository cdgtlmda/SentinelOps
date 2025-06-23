"use client";

import { useState } from "react";
import { AnimatedText } from "@/components/animated-text";
import { CopyText } from "@/components/copy-text";
import Link from "next/link";
import { 
  TrendingUp, 
  Play, 
  Pause, 
  Activity, 
  AlertTriangle, 
  Timer, 
  Target, 
  ArrowLeft,
  ArrowRight,
  BarChart3,
  Zap,
  Eye,
  Shield,
  Clock,
  CheckCircle
} from "lucide-react";

interface CampaignEvent {
  id: string;
  minute: number;
  severity: 'LOW' | 'MEDIUM' | 'CRITICAL';
  event_type: string;
  finding: string;
  mitre_stage: string;
  kill_chain_phase: string;
  source_ip: string;
  target: string;
}

interface CampaignMetrics {
  totalEvents: number;
  severityBreakdown: Record<string, number>;
  peakActivity: { minute: number; count: number };
  averageEventsPerMinute: number;
  killChainProgression: string[];
  estimatedImpact: string;
}

export default function AttackCampaignsDemo() {
  const [isRunning, setIsRunning] = useState(false);
  const [campaignProgress, setCampaignProgress] = useState(0);
  const [currentMinute, setCurrentMinute] = useState(0);
  const [events, setEvents] = useState<CampaignEvent[]>([]);
  const [metrics, setMetrics] = useState<CampaignMetrics | null>(null);
  const [timeline, setTimeline] = useState<Record<number, CampaignEvent[]>>({});

  // Simulated attack campaign based on real SentinelOps scenarios
  const campaignScenarios: Omit<CampaignEvent, 'id' | 'minute'>[] = [
    {
      severity: 'MEDIUM',
      event_type: 'Network Reconnaissance', 
      finding: 'Systematic port scanning detected from external IP targeting production infrastructure',
      mitre_stage: 'Discovery',
      kill_chain_phase: 'Reconnaissance',
      source_ip: '203.0.113.42',
      target: 'web-prod-cluster'
    },
    {
      severity: 'MEDIUM',
      event_type: 'Credential Enumeration',
      finding: 'Automated username enumeration on authentication service using common account names',
      mitre_stage: 'Discovery',
      kill_chain_phase: 'Reconnaissance', 
      source_ip: '203.0.113.42',
      target: 'auth-service-prod'
    },
    {
      severity: 'CRITICAL',
      event_type: 'SSH Brute Force',
      finding: 'High-volume SSH login attempts targeting production servers with credential stuffing',
      mitre_stage: 'Credential Access',
      kill_chain_phase: 'Initial Access',
      source_ip: '203.0.113.42',
      target: 'web-prod-01'
    },
    {
      severity: 'CRITICAL',
      event_type: 'Successful Compromise',
      finding: 'SSH authentication succeeded for admin account after 1,247 failed attempts',
      mitre_stage: 'Initial Access',
      kill_chain_phase: 'Initial Access',
      source_ip: '203.0.113.42',
      target: 'web-prod-01'
    },
    {
      severity: 'CRITICAL',
      event_type: 'Privilege Escalation',
      finding: 'Sudo access gained through exploitation of misconfigured SUID binary',
      mitre_stage: 'Privilege Escalation',
      kill_chain_phase: 'Execution',
      source_ip: '10.128.0.45',
      target: 'web-prod-01'
    },
    {
      severity: 'CRITICAL',
      event_type: 'Lateral Movement',
      finding: 'Compromised credentials used to access internal Kubernetes cluster',
      mitre_stage: 'Lateral Movement',
      kill_chain_phase: 'Lateral Movement',
      source_ip: '10.128.0.45',
      target: 'gke-production-cluster'
    },
    {
      severity: 'CRITICAL',
      event_type: 'Data Exfiltration',
      finding: 'Large data export detected from customer database to external S3 bucket',
      mitre_stage: 'Exfiltration',
      kill_chain_phase: 'Exfiltration',
      source_ip: '10.142.15.67',
      target: 'customer-db-prod'
    },
    {
      severity: 'CRITICAL',
      event_type: 'Persistence Mechanism',
      finding: 'Malicious cron job installed for continued access and cryptocurrency mining',
      mitre_stage: 'Persistence',
      kill_chain_phase: 'Installation',
      source_ip: '10.128.0.45',
      target: 'web-prod-01'
    }
  ];

  const startCampaign = async () => {
    setIsRunning(true);
    setCampaignProgress(0);
    setCurrentMinute(0);
    setEvents([]);
    setTimeline({});
    setMetrics(null);

    const campaignDuration = 30; // 30 minutes
    const totalSteps = campaignDuration * 6; // 6 updates per minute for smooth animation

    for (let step = 0; step <= totalSteps; step++) {
      if (!isRunning) break;

      const progress = (step / totalSteps) * 100;
      const minute = Math.floor(step / 6);
      
      setCampaignProgress(progress);
      setCurrentMinute(minute);

      // Generate events based on attack progression
      if (step % 6 === 0 && minute < campaignDuration) { // Every "minute"
        const eventsThisMinute = generateEventsForMinute(minute);
        
        setEvents(prev => [...prev, ...eventsThisMinute]);
        setTimeline(prev => ({
          ...prev,
          [minute]: eventsThisMinute
        }));
      }

      await new Promise(resolve => setTimeout(resolve, 100));
    }

    // Calculate final metrics
    calculateCampaignMetrics();
    setIsRunning(false);
  };

  const generateEventsForMinute = (minute: number): CampaignEvent[] => {
    const minuteEvents: CampaignEvent[] = [];
    
    // Escalation pattern: reconnaissance → initial access → lateral movement → exfiltration
    let eventProbability = 0.3;
    let eventCount = 0;

    if (minute < 5) {
      // Early reconnaissance phase
      eventProbability = 0.4;
      eventCount = Math.random() > 0.6 ? 1 : 0;
    } else if (minute < 15) {
      // Initial access and escalation
      eventProbability = 0.7;
      eventCount = Math.random() > 0.5 ? 1 : (Math.random() > 0.8 ? 2 : 0);
    } else if (minute < 25) {
      // Peak activity - lateral movement
      eventProbability = 0.9;
      eventCount = Math.random() > 0.3 ? 2 : (Math.random() > 0.7 ? 3 : 1);
    } else {
      // Final exfiltration phase
      eventProbability = 0.6;
      eventCount = Math.random() > 0.5 ? 1 : 0;
    }

    for (let i = 0; i < eventCount; i++) {
      const scenario = campaignScenarios[Math.floor(Math.random() * campaignScenarios.length)];
      if (scenario) {
        minuteEvents.push({
          id: `event-${minute}-${i}`,
          minute,
          severity: scenario.severity,
          event_type: scenario.event_type,
          finding: scenario.finding,
          mitre_stage: scenario.mitre_stage,
          kill_chain_phase: scenario.kill_chain_phase,
          source_ip: scenario.source_ip,
          target: scenario.target
        });
      }
    }

    return minuteEvents;
  };

  const calculateCampaignMetrics = () => {
    const allEvents = Object.values(timeline).flat();
    
    const severityBreakdown = allEvents.reduce((acc, event) => {
      acc[event.severity] = (acc[event.severity] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const eventsPerMinute = Object.entries(timeline).map(([minute, events]) => ({
      minute: parseInt(minute),
      count: events.length
    }));

    const peakActivity = eventsPerMinute.reduce((max, current) => 
      current.count > max.count ? current : max, { minute: 0, count: 0 });

    const killChainPhases = [...new Set(allEvents.map(e => e.kill_chain_phase))];

    setMetrics({
      totalEvents: allEvents.length,
      severityBreakdown,
      peakActivity,
      averageEventsPerMinute: allEvents.length / 30,
      killChainProgression: killChainPhases,
      estimatedImpact: `$${(Math.random() * 10 + 5).toFixed(1)}M potential damage`
    });
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
              <TrendingUp className="w-8 h-8 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Attack Campaign Analysis</h1>
              <p className="text-muted-foreground">Multi-stage attack simulation with behavioral analysis and pattern detection</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              Real-time Campaign Simulation
            </span>
            <span>•</span>
            <span>Kill Chain Mapping</span>
            <span>•</span>
            <span>MITRE ATT&CK Framework</span>
          </div>
        </div>
      </section>

      <div className="container mx-auto px-4 pb-20">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Control Panel */}
          <div className="lg:col-span-1">
            <div className="bg-card border border-border rounded-lg p-6 space-y-6">
              <h2 className="text-xl font-semibold">Campaign Simulation</h2>
              
              <div className="space-y-4">
                <div className="p-4 bg-orange-500/10 border border-orange-500/20 rounded-lg">
                  <h3 className="font-semibold mb-2">30-Minute Attack Campaign</h3>
                  <p className="text-sm text-muted-foreground mb-3">
                    Simulates a coordinated multi-stage cyber attack following the cyber kill chain methodology
                  </p>
                  <div className="space-y-2 text-xs">
                    <div><strong>Phases:</strong> Reconnaissance → Initial Access → Lateral Movement → Exfiltration</div>
                    <div><strong>Intensity:</strong> High (peak 3 events/minute)</div>
                    <div><strong>Framework:</strong> MITRE ATT&CK mapped</div>
                  </div>
                </div>

                <button
                  onClick={startCampaign}
                  disabled={isRunning}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  <Play className="w-4 h-4" />
                  {isRunning ? 'Campaign Running...' : 'Start Attack Campaign'}
                </button>

                {/* Progress Display */}
                {isRunning && (
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span>Campaign Progress</span>
                      <span>{Math.round(campaignProgress)}%</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-3">
                      <div 
                        className="bg-gradient-to-r from-orange-500 to-red-500 h-3 rounded-full transition-all duration-300"
                        style={{ width: `${campaignProgress}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Minute {currentMinute}/30</span>
                      <span>{events.length} events detected</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Live Metrics */}
              {metrics && (
                <div className="space-y-3">
                  <h3 className="font-medium">Campaign Metrics</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="text-center p-3 bg-muted/50 rounded-lg">
                      <div className="text-2xl font-bold text-red-500">{metrics.severityBreakdown.CRITICAL || 0}</div>
                      <div className="text-xs text-muted-foreground">Critical</div>
                    </div>
                    <div className="text-center p-3 bg-muted/50 rounded-lg">
                      <div className="text-2xl font-bold">{metrics.totalEvents}</div>
                      <div className="text-xs text-muted-foreground">Total Events</div>
                    </div>
                  </div>
                  <div className="text-xs space-y-1">
                    <div><strong>Peak Activity:</strong> Minute {metrics.peakActivity.minute} ({metrics.peakActivity.count} events)</div>
                    <div><strong>Avg/Min:</strong> {metrics.averageEventsPerMinute.toFixed(1)}</div>
                    <div><strong>Impact:</strong> {metrics.estimatedImpact}</div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Timeline Visualization */}
          <div className="lg:col-span-2 space-y-6">
            {/* Real-time Timeline */}
            <div className="bg-card border border-border rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-6">Attack Timeline</h2>
              
              {Object.keys(timeline).length === 0 && !isRunning && (
                <div className="text-center py-12 text-muted-foreground">
                  <Target className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Start a campaign to visualize the attack progression</p>
                </div>
              )}

              {/* Timeline Chart */}
              {Object.keys(timeline).length > 0 && (
                <div className="space-y-4">
                  <div className="h-32 flex items-end justify-between gap-1">
                    {Array.from({ length: 30 }, (_, i) => {
                      const eventCount = timeline[i]?.length || 0;
                      const maxEvents = Math.max(...Object.values(timeline).map(events => events.length), 1);
                      const height = (eventCount / maxEvents) * 100;
                      const isActive = i <= currentMinute;
                      
                      return (
                        <div key={i} className="flex-1 flex flex-col items-center">
                          <div 
                            className={`w-full rounded-t transition-all duration-300 ${
                              eventCount > 0 
                                ? timeline[i]?.some(e => e.severity === 'CRITICAL') 
                                  ? 'bg-red-500' 
                                  : 'bg-yellow-500'
                                : isActive 
                                  ? 'bg-muted' 
                                  : 'bg-muted/30'
                            }`}
                            style={{ height: `${Math.max(height, 2)}%` }}
                          />
                          <div className="text-xs text-muted-foreground mt-1">{i}</div>
                        </div>
                      );
                    })}
                  </div>
                  <div className="text-xs text-muted-foreground text-center">
                    Time (minutes) - Red: Critical events, Yellow: Medium/Low events
                  </div>
                </div>
              )}
            </div>

            {/* Recent Events */}
            {events.length > 0 && (
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Live Event Stream</h2>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {events.slice(-10).reverse().map((event) => (
                    <div key={event.id} className="p-4 bg-muted/30 rounded-lg">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4 text-orange-500" />
                          <span className="font-medium text-sm">{event.event_type}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-1 text-xs rounded-full border ${getSeverityColor(event.severity)}`}>
                            {event.severity}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            T+{event.minute}min
                          </span>
                        </div>
                      </div>
                      
                      <p className="text-sm text-muted-foreground mb-3">{event.finding}</p>
                      
                      <div className="grid grid-cols-2 gap-4 text-xs">
                        <div>
                          <span className="font-medium">Kill Chain:</span>
                          <div className="text-muted-foreground">{event.kill_chain_phase}</div>
                        </div>
                        <div>
                          <span className="font-medium">MITRE Stage:</span>
                          <div className="text-muted-foreground">{event.mitre_stage}</div>
                        </div>
                        <div>
                          <span className="font-medium">Source:</span>
                          <div className="text-muted-foreground font-mono">{event.source_ip}</div>
                        </div>
                        <div>
                          <span className="font-medium">Target:</span>
                          <div className="text-muted-foreground">{event.target}</div>
                        </div>
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
          <h2 className="text-2xl font-bold mb-6">Campaign Analysis Technology</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-semibold mb-4">Real Implementation</h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>BigQuery ML for pattern detection</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Pub/Sub for real-time event streaming</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Cloud Monitoring for metrics</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Dataflow for event correlation</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Custom ADK wrappers for orchestration</span>
                </div>
              </div>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-4">Try Campaign Simulation</h3>
              <div className="space-y-3">
                <CopyText value="python src/tools/threat_simulator.py --campaign --duration 30" />
                <CopyText value="python demos/demo_threat_simulation.py --batch-mode" />
                <p className="text-xs text-muted-foreground">
                  Run actual attack campaign simulations with behavioral analysis and kill chain progression tracking.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 