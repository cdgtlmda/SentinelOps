'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Play,
  Pause,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  Shield,
  Zap,
  Users,
  Activity,
  Target,
  FileText,
  MessageSquare,
  TrendingUp,
  Clock,
  ChevronRight
} from 'lucide-react'

interface ScenarioStep {
  id: string
  title: string
  description: string
  duration: number // in seconds
  action?: {
    type: 'detection' | 'analysis' | 'remediation' | 'communication'
    agent: string
    details: string
  }
  expectedResult?: string
}

interface Scenario {
  id: string
  title: string
  description: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  duration: number // total duration in minutes
  category: string
  icon: React.ElementType
  steps: ScenarioStep[]
  learningOutcomes: string[]
}

const SAMPLE_SCENARIOS: Scenario[] = [
  {
    id: 'suspicious-login',
    title: 'Suspicious Login Detection',
    description: 'Learn how SentinelOps detects and responds to suspicious login attempts.',
    difficulty: 'beginner',
    duration: 5,
    category: 'Security Threats',
    icon: AlertTriangle,
    steps: [
      {
        id: 'step1',
        title: 'Unusual Login Detected',
        description: 'Detection agent identifies login from new location and device.',
        duration: 10,
        action: {
          type: 'detection',
          agent: 'Detection Agent',
          details: 'Analyzing login patterns and geographic anomalies'
        }
      },
      {
        id: 'step2',
        title: 'Risk Assessment',
        description: 'Analysis agent evaluates the threat level and user behavior.',
        duration: 15,
        action: {
          type: 'analysis',
          agent: 'Analysis Agent',
          details: 'Checking user history, device fingerprint, and location data'
        },
        expectedResult: 'High risk score due to impossible travel detected'
      },
      {
        id: 'step3',
        title: 'Automated Response',
        description: 'Remediation agent takes immediate protective action.',
        duration: 8,
        action: {
          type: 'remediation',
          agent: 'Remediation Agent',
          details: 'Forcing MFA verification and temporary account lock'
        }
      },
      {
        id: 'step4',
        title: 'User Notification',
        description: 'Communication agent alerts the user and security team.',
        duration: 5,
        action: {
          type: 'communication',
          agent: 'Communication Agent',
          details: 'Sending email and SMS alerts with verification link'
        }
      }
    ],
    learningOutcomes: [
      'Understand login anomaly detection',
      'Learn about risk scoring methodology',
      'See automated response workflow',
      'Experience multi-channel notifications'
    ]
  },
  {
    id: 'ddos-mitigation',
    title: 'DDoS Attack Mitigation',
    description: 'Experience how AI agents collaborate to stop a DDoS attack.',
    difficulty: 'intermediate',
    duration: 8,
    category: 'Network Security',
    icon: Shield,
    steps: [
      {
        id: 'step1',
        title: 'Traffic Spike Detected',
        description: 'Unusual traffic patterns trigger immediate investigation.',
        duration: 5,
        action: {
          type: 'detection',
          agent: 'Detection Agent',
          details: 'Monitoring traffic volume and request patterns'
        }
      },
      {
        id: 'step2',
        title: 'Attack Pattern Analysis',
        description: 'AI identifies DDoS signature and attack vectors.',
        duration: 20,
        action: {
          type: 'analysis',
          agent: 'Analysis Agent',
          details: 'Analyzing source IPs, request types, and payload patterns'
        },
        expectedResult: 'Confirmed DDoS attack from 50,000+ botnet IPs'
      },
      {
        id: 'step3',
        title: 'Deploy Countermeasures',
        description: 'Automatic deployment of DDoS protection measures.',
        duration: 15,
        action: {
          type: 'remediation',
          agent: 'Remediation Agent',
          details: 'Enabling rate limiting, IP blocking, and CDN rerouting'
        }
      },
      {
        id: 'step4',
        title: 'Stakeholder Updates',
        description: 'Real-time updates to relevant teams and management.',
        duration: 10,
        action: {
          type: 'communication',
          agent: 'Communication Agent',
          details: 'Incident report generation and executive briefing'
        }
      }
    ],
    learningOutcomes: [
      'Recognize DDoS attack patterns',
      'Understand mitigation strategies',
      'Learn about automated scaling',
      'See incident communication flow'
    ]
  },
  {
    id: 'data-exfiltration',
    title: 'Data Exfiltration Prevention',
    description: 'Advanced scenario showing data breach detection and prevention.',
    difficulty: 'advanced',
    duration: 12,
    category: 'Data Security',
    icon: Target,
    steps: [
      {
        id: 'step1',
        title: 'Abnormal Data Access',
        description: 'Unusual database queries detected from internal system.',
        duration: 15,
        action: {
          type: 'detection',
          agent: 'Detection Agent',
          details: 'Monitoring query patterns and data volume transfers'
        }
      },
      {
        id: 'step2',
        title: 'Behavioral Analysis',
        description: 'Deep analysis of user behavior and access patterns.',
        duration: 30,
        action: {
          type: 'analysis',
          agent: 'Analysis Agent',
          details: 'Correlating access logs, user activity, and network traffic'
        },
        expectedResult: 'Compromised service account attempting data theft'
      },
      {
        id: 'step3',
        title: 'Immediate Containment',
        description: 'Multi-layered response to prevent data loss.',
        duration: 20,
        action: {
          type: 'remediation',
          agent: 'Remediation Agent',
          details: 'Revoking credentials, blocking egress, isolating systems'
        }
      },
      {
        id: 'step4',
        title: 'Forensic Collection',
        description: 'Automated evidence collection for investigation.',
        duration: 25,
        action: {
          type: 'analysis',
          agent: 'Analysis Agent',
          details: 'Capturing logs, memory dumps, and network traces'
        }
      },
      {
        id: 'step5',
        title: 'Compliance Reporting',
        description: 'Generate required compliance and legal reports.',
        duration: 10,
        action: {
          type: 'communication',
          agent: 'Communication Agent',
          details: 'Creating breach notifications and regulatory reports'
        }
      }
    ],
    learningOutcomes: [
      'Master data breach detection',
      'Understand containment strategies',
      'Learn forensic procedures',
      'Navigate compliance requirements'
    ]
  }
]

interface SampleScenariosProps {
  onScenarioComplete?: (scenarioId: string) => void
}

export function SampleScenarios({ onScenarioComplete }: SampleScenariosProps) {
  const [activeScenario, setActiveScenario] = useState<Scenario | null>(null)
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [stepProgress, setStepProgress] = useState(0)
  const [completedScenarios, setCompletedScenarios] = useState<Set<string>>(
    new Set(JSON.parse(localStorage.getItem('completedScenarios') || '[]'))
  )

  const currentStep = activeScenario?.steps[currentStepIndex]

  const startScenario = (scenario: Scenario) => {
    setActiveScenario(scenario)
    setCurrentStepIndex(0)
    setStepProgress(0)
    setIsPlaying(true)
  }

  const resetScenario = () => {
    setCurrentStepIndex(0)
    setStepProgress(0)
    setIsPlaying(false)
  }

  const completeScenario = () => {
    if (activeScenario) {
      const newCompleted = new Set([...completedScenarios, activeScenario.id])
      setCompletedScenarios(newCompleted)
      localStorage.setItem('completedScenarios', JSON.stringify([...newCompleted]))
      
      if (onScenarioComplete) {
        onScenarioComplete(activeScenario.id)
      }
    }
    
    setActiveScenario(null)
    setIsPlaying(false)
  }

  const nextStep = () => {
    if (activeScenario && currentStepIndex < activeScenario.steps.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1)
      setStepProgress(0)
    } else {
      completeScenario()
    }
  }

  const getAgentIcon = (type: string) => {
    switch (type) {
      case 'detection':
        return Target
      case 'analysis':
        return Activity
      case 'remediation':
        return Shield
      case 'communication':
        return MessageSquare
      default:
        return Users
    }
  }

  const getDifficultyColor = (difficulty: Scenario['difficulty']) => {
    switch (difficulty) {
      case 'beginner':
        return 'text-green-600 bg-green-50 border-green-200'
      case 'intermediate':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'advanced':
        return 'text-red-600 bg-red-50 border-red-200'
    }
  }

  return (
    <div className="space-y-6">
      {!activeScenario ? (
        // Scenario Selection
        <>
          <div>
            <h2 className="text-2xl font-bold mb-2">Interactive Scenarios</h2>
            <p className="text-gray-600 dark:text-gray-400">
              Practice handling real-world security incidents in a safe environment
            </p>
          </div>

          <Tabs defaultValue="all" className="space-y-4">
            <TabsList>
              <TabsTrigger value="all">All Scenarios</TabsTrigger>
              <TabsTrigger value="beginner">Beginner</TabsTrigger>
              <TabsTrigger value="intermediate">Intermediate</TabsTrigger>
              <TabsTrigger value="advanced">Advanced</TabsTrigger>
            </TabsList>

            {['all', 'beginner', 'intermediate', 'advanced'].map((level) => (
              <TabsContent key={level} value={level} className="space-y-4">
                {SAMPLE_SCENARIOS
                  .filter(s => level === 'all' || s.difficulty === level)
                  .map((scenario) => {
                    const Icon = scenario.icon
                    const isCompleted = completedScenarios.has(scenario.id)
                    
                    return (
                      <Card key={scenario.id} className="p-6">
                        <div className="flex items-start justify-between">
                          <div className="flex gap-4">
                            <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded-lg">
                              <Icon className="h-6 w-6" />
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <h3 className="text-lg font-semibold">{scenario.title}</h3>
                                <Badge className={getDifficultyColor(scenario.difficulty)}>
                                  {scenario.difficulty}
                                </Badge>
                                {isCompleted && (
                                  <Badge variant="secondary">
                                    <CheckCircle className="h-3 w-3 mr-1" />
                                    Completed
                                  </Badge>
                                )}
                              </div>
                              <p className="text-gray-600 dark:text-gray-400 mb-3">
                                {scenario.description}
                              </p>
                              <div className="flex items-center gap-4 text-sm text-gray-500">
                                <span className="flex items-center gap-1">
                                  <Clock className="h-4 w-4" />
                                  {scenario.duration} minutes
                                </span>
                                <span>•</span>
                                <span>{scenario.steps.length} steps</span>
                                <span>•</span>
                                <span>{scenario.category}</span>
                              </div>
                            </div>
                          </div>
                          
                          <Button
                            onClick={() => startScenario(scenario)}
                            variant={isCompleted ? 'outline' : 'default'}
                          >
                            {isCompleted ? 'Replay' : 'Start'}
                            <ChevronRight className="h-4 w-4 ml-1" />
                          </Button>
                        </div>

                        {/* Learning Outcomes */}
                        <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                          <h4 className="font-medium text-sm mb-2">What you'll learn:</h4>
                          <ul className="grid grid-cols-2 gap-2">
                            {scenario.learningOutcomes.map((outcome, index) => (
                              <li key={index} className="flex items-start gap-2 text-sm">
                                <CheckCircle className="h-4 w-4 text-green-500 mt-0.5" />
                                <span>{outcome}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </Card>
                    )
                  })}
              </TabsContent>
            ))}
          </Tabs>
        </>
      ) : (
        // Active Scenario
        <Card className="p-6">
          {/* Scenario Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold">{activeScenario.title}</h2>
              <p className="text-gray-500">
                Step {currentStepIndex + 1} of {activeScenario.steps.length}
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsPlaying(!isPlaying)}
              >
                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={resetScenario}
              >
                <RotateCcw className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setActiveScenario(null)}
              >
                Exit
              </Button>
            </div>
          </div>

          {/* Progress */}
          <div className="mb-6">
            <Progress 
              value={(currentStepIndex / activeScenario.steps.length) * 100} 
              className="h-2"
            />
          </div>

          {/* Current Step */}
          {currentStep && (
            <div className="space-y-6">
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-2">{currentStep.title}</h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {currentStep.description}
                </p>

                {currentStep.action && (
                  <div className="flex items-start gap-3 p-4 bg-white dark:bg-gray-800 rounded-lg border">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded">
                      {(() => {
                        const AgentIcon = getAgentIcon(currentStep.action.type)
                        return <AgentIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                      })()}
                    </div>
                    <div className="flex-1">
                      <div className="font-medium mb-1">{currentStep.action.agent}</div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {currentStep.action.details}
                      </p>
                    </div>
                  </div>
                )}

                {currentStep.expectedResult && (
                  <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                    <div className="flex items-start gap-2">
                      <TrendingUp className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                      <div>
                        <div className="font-medium text-yellow-800 dark:text-yellow-200">
                          Expected Result
                        </div>
                        <p className="text-sm text-yellow-700 dark:text-yellow-300">
                          {currentStep.expectedResult}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Step Progress Simulation */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-500">Processing...</span>
                  <span className="text-sm text-gray-500">
                    {Math.round((stepProgress / currentStep.duration) * 100)}%
                  </span>
                </div>
                <Progress 
                  value={(stepProgress / currentStep.duration) * 100} 
                  className="h-2"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    if (currentStepIndex > 0) {
                      setCurrentStepIndex(currentStepIndex - 1)
                      setStepProgress(0)
                    }
                  }}
                  disabled={currentStepIndex === 0}
                >
                  Previous
                </Button>
                <Button onClick={nextStep}>
                  {currentStepIndex === activeScenario.steps.length - 1 ? 'Complete' : 'Next Step'}
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  )
}