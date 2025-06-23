'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { 
  Sparkles,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  X,
  CheckCircle,
  Rocket,
  Shield,
  Users,
  BarChart3,
  MessageSquare,
  Zap,
  Play,
  Skip
} from 'lucide-react'
import confetti from 'canvas-confetti'

interface WelcomeStep {
  id: string
  title: string
  description: string
  icon: React.ElementType
  image?: string
  highlights?: string[]
  action?: {
    label: string
    onClick: () => void
  }
}

const WELCOME_STEPS: WelcomeStep[] = [
  {
    id: 'welcome',
    title: 'Welcome to SentinelOps!',
    description: 'Your AI-powered security operations platform is ready to protect your infrastructure.',
    icon: Rocket,
    highlights: [
      'Automated threat detection',
      'Intelligent incident response',
      'Real-time security monitoring'
    ]
  },
  {
    id: 'ai-agents',
    title: 'Meet Your AI Security Team',
    description: 'Four specialized AI agents work 24/7 to keep your systems secure.',
    icon: Users,
    highlights: [
      'Detection Agent: Monitors for threats',
      'Analysis Agent: Investigates incidents',
      'Remediation Agent: Executes fixes',
      'Communication Agent: Keeps you informed'
    ]
  },
  {
    id: 'incident-management',
    title: 'Intelligent Incident Response',
    description: 'SentinelOps automatically detects, analyzes, and responds to security incidents.',
    icon: Shield,
    highlights: [
      'Automated severity classification',
      'AI-powered root cause analysis',
      'One-click remediation actions',
      'Full audit trail'
    ]
  },
  {
    id: 'analytics',
    title: 'Actionable Security Insights',
    description: 'Get comprehensive visibility into your security posture with advanced analytics.',
    icon: BarChart3,
    highlights: [
      'Real-time security metrics',
      'Trend analysis and predictions',
      'Custom reports and dashboards',
      'Performance benchmarking'
    ]
  },
  {
    id: 'communication',
    title: 'Stay Connected',
    description: 'Multiple ways to interact with your AI security team and stay informed.',
    icon: MessageSquare,
    highlights: [
      'Natural language chat interface',
      'Smart notifications',
      'Integration with your tools',
      'Mobile-friendly design'
    ]
  },
  {
    id: 'get-started',
    title: 'Ready to Begin?',
    description: 'Your security operations center is set up and ready. Let\'s start protecting your infrastructure!',
    icon: Zap,
    action: {
      label: 'Go to Dashboard',
      onClick: () => window.location.href = '/dashboard'
    }
  }
]

interface WelcomeTourProps {
  onComplete: () => void
  onSkip: () => void
}

export function WelcomeTour({ onComplete, onSkip }: WelcomeTourProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [hasInteracted, setHasInteracted] = useState(false)
  const step = WELCOME_STEPS[currentStep]
  const progress = ((currentStep + 1) / WELCOME_STEPS.length) * 100
  const isLastStep = currentStep === WELCOME_STEPS.length - 1

  useEffect(() => {
    // Play confetti on last step
    if (isLastStep && !hasInteracted) {
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 }
      })
      setHasInteracted(true)
    }
  }, [isLastStep, hasInteracted])

  const handleNext = () => {
    if (isLastStep) {
      onComplete()
    } else {
      setCurrentStep(currentStep + 1)
    }
  }

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const Icon = step.icon

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <AnimatePresence mode="wait">
        <motion.div
          key={step.id}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.3 }}
          className="w-full max-w-2xl"
        >
          <Card className="relative overflow-hidden">
            {/* Background decoration */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-950/20 dark:to-purple-950/20 opacity-50" />
            
            {/* Skip button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={onSkip}
              className="absolute top-4 right-4 z-10"
            >
              <X className="h-4 w-4" />
            </Button>

            <div className="relative p-8">
              {/* Progress */}
              <div className="mb-8">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-500">
                    Step {currentStep + 1} of {WELCOME_STEPS.length}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onSkip}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    Skip tour
                    <Skip className="h-3 w-3 ml-1" />
                  </Button>
                </div>
                <Progress value={progress} className="h-2" />
              </div>

              {/* Content */}
              <div className="text-center space-y-6">
                {/* Icon */}
                <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-lg">
                  <Icon className="h-10 w-10" />
                </div>

                {/* Title and description */}
                <div>
                  <h2 className="text-3xl font-bold mb-3">{step.title}</h2>
                  <p className="text-lg text-gray-600 dark:text-gray-400">
                    {step.description}
                  </p>
                </div>

                {/* Highlights */}
                {step.highlights && (
                  <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6">
                    <div className="grid gap-3">
                      {step.highlights.map((highlight, index) => (
                        <div
                          key={index}
                          className="flex items-center gap-3 text-left"
                        >
                          <div className="flex-shrink-0">
                            <CheckCircle className="h-5 w-5 text-green-500" />
                          </div>
                          <span className="text-sm">{highlight}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Custom action */}
                {step.action && (
                  <Button
                    size="lg"
                    onClick={step.action.onClick}
                    className="mt-4"
                  >
                    {step.action.label}
                    <Sparkles className="h-4 w-4 ml-2" />
                  </Button>
                )}
              </div>

              {/* Navigation */}
              <div className="flex items-center justify-between mt-8">
                <Button
                  variant="outline"
                  onClick={handlePrevious}
                  disabled={currentStep === 0}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </Button>

                {/* Step indicators */}
                <div className="flex gap-2">
                  {WELCOME_STEPS.map((_, index) => (
                    <div
                      key={index}
                      className={`w-2 h-2 rounded-full transition-all ${
                        index === currentStep
                          ? 'w-8 bg-blue-600'
                          : index < currentStep
                          ? 'bg-blue-600'
                          : 'bg-gray-300'
                      }`}
                    />
                  ))}
                </div>

                <Button onClick={handleNext}>
                  {isLastStep ? (
                    <>
                      Complete Tour
                      <CheckCircle className="h-4 w-4 ml-1" />
                    </>
                  ) : (
                    <>
                      Next
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </>
                  )}
                </Button>
              </div>
            </div>
          </Card>
        </motion.div>
      </AnimatePresence>
    </div>
  )
}

// Mini welcome message for returning users
export function WelcomeBack({ userName }: { userName?: string }) {
  const [show, setShow] = useState(true)
  const [hasSeenToday, setHasSeenToday] = useState(false)

  useEffect(() => {
    const today = new Date().toDateString()
    const lastSeen = localStorage.getItem('welcomeBackLastSeen')
    
    if (lastSeen === today) {
      setHasSeenToday(true)
      setShow(false)
    } else {
      localStorage.setItem('welcomeBackLastSeen', today)
    }
  }, [])

  if (!show || hasSeenToday) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className="fixed top-20 right-4 z-40"
      >
        <Card className="p-4 shadow-lg border-blue-200 dark:border-blue-800 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/50 dark:to-purple-950/50">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white dark:bg-gray-800 rounded-full">
              <Sparkles className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="pr-8">
              <h3 className="font-semibold">
                Welcome back{userName ? `, ${userName}` : ''}!
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Your security operations are running smoothly.
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShow(false)}
              className="absolute top-2 right-2"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </Card>
      </motion.div>
    </AnimatePresence>
  )
}