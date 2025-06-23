'use client'

import { useState, useEffect, useRef, ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { 
  X, 
  ChevronLeft, 
  ChevronRight, 
  RotateCcw,
  CheckCircle,
  Circle,
  Play,
  Pause,
  SkipForward,
  Target,
  MousePointer,
  Keyboard,
  Info
} from 'lucide-react'

interface TutorialStep {
  id: string
  title: string
  content: string | ReactNode
  target?: string // CSS selector for element to highlight
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center'
  action?: {
    type: 'click' | 'hover' | 'input' | 'scroll'
    description: string
  }
  validation?: () => boolean
  onNext?: () => void
  onBack?: () => void
}

interface TutorialSequence {
  id: string
  name: string
  description: string
  category: string
  estimatedTime: number // in minutes
  steps: TutorialStep[]
  onComplete?: () => void
}

interface InteractiveTutorialProps {
  sequence: TutorialSequence
  onClose: () => void
  onComplete?: () => void
  startStep?: number
}

export function InteractiveTutorial({
  sequence,
  onClose,
  onComplete,
  startStep = 0
}: InteractiveTutorialProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(startStep)
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set())
  const [isPaused, setIsPaused] = useState(false)
  const [highlightElement, setHighlightElement] = useState<HTMLElement | null>(null)
  const tutorialRef = useRef<HTMLDivElement>(null)

  const currentStep = sequence.steps[currentStepIndex]
  const progress = ((currentStepIndex + 1) / sequence.steps.length) * 100
  const isLastStep = currentStepIndex === sequence.steps.length - 1

  useEffect(() => {
    if (currentStep.target && !isPaused) {
      const element = document.querySelector(currentStep.target) as HTMLElement
      if (element) {
        setHighlightElement(element)
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
        
        // Add highlight class
        element.classList.add('tutorial-highlight')
        
        return () => {
          element.classList.remove('tutorial-highlight')
        }
      }
    } else {
      setHighlightElement(null)
    }
  }, [currentStep, isPaused])

  useEffect(() => {
    // Add global styles for tutorial
    const style = document.createElement('style')
    style.textContent = `
      .tutorial-highlight {
        position: relative;
        z-index: 9998;
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.5);
        animation: tutorial-pulse 2s infinite;
      }
      
      @keyframes tutorial-pulse {
        0% { box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.5); }
        50% { box-shadow: 0 0 0 8px rgba(59, 130, 246, 0.3); }
        100% { box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.5); }
      }
      
      .tutorial-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        z-index: 9997;
      }
      
      .tutorial-spotlight {
        position: absolute;
        border-radius: 8px;
        box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5);
        z-index: 9998;
      }
    `
    document.head.appendChild(style)

    return () => {
      document.head.removeChild(style)
    }
  }, [])

  const handleNext = () => {
    if (currentStep.validation && !currentStep.validation()) {
      // Show validation error
      return
    }

    if (currentStep.onNext) {
      currentStep.onNext()
    }

    setCompletedSteps(new Set([...completedSteps, currentStep.id]))

    if (isLastStep) {
      handleComplete()
    } else {
      setCurrentStepIndex(currentStepIndex + 1)
    }
  }

  const handleBack = () => {
    if (currentStepIndex > 0) {
      if (currentStep.onBack) {
        currentStep.onBack()
      }
      setCurrentStepIndex(currentStepIndex - 1)
    }
  }

  const handleComplete = () => {
    if (sequence.onComplete) {
      sequence.onComplete()
    }
    if (onComplete) {
      onComplete()
    }
    onClose()
  }

  const handleSkip = () => {
    if (confirm('Are you sure you want to skip this tutorial?')) {
      onClose()
    }
  }

  const getTooltipPosition = () => {
    if (!highlightElement || !tutorialRef.current) return {}

    const targetRect = highlightElement.getBoundingClientRect()
    const tooltipRect = tutorialRef.current.getBoundingClientRect()
    const position = currentStep.position || 'bottom'

    const offset = 20
    let style: React.CSSProperties = {}

    switch (position) {
      case 'top':
        style = {
          left: targetRect.left + targetRect.width / 2 - tooltipRect.width / 2,
          bottom: window.innerHeight - targetRect.top + offset
        }
        break
      case 'bottom':
        style = {
          left: targetRect.left + targetRect.width / 2 - tooltipRect.width / 2,
          top: targetRect.bottom + offset
        }
        break
      case 'left':
        style = {
          right: window.innerWidth - targetRect.left + offset,
          top: targetRect.top + targetRect.height / 2 - tooltipRect.height / 2
        }
        break
      case 'right':
        style = {
          left: targetRect.right + offset,
          top: targetRect.top + targetRect.height / 2 - tooltipRect.height / 2
        }
        break
      case 'center':
        style = {
          left: '50%',
          top: '50%',
          transform: 'translate(-50%, -50%)'
        }
        break
    }

    // Ensure tooltip stays within viewport
    if (style.left && typeof style.left === 'number') {
      style.left = Math.max(10, Math.min(style.left, window.innerWidth - tooltipRect.width - 10))
    }
    if (style.top && typeof style.top === 'number') {
      style.top = Math.max(10, Math.min(style.top, window.innerHeight - tooltipRect.height - 10))
    }

    return style
  }

  const tooltipContent = (
    <>
      {/* Overlay */}
      {!isPaused && highlightElement && (
        <div className="tutorial-overlay" onClick={() => setIsPaused(true)} />
      )}

      {/* Spotlight */}
      {!isPaused && highlightElement && (
        <div
          className="tutorial-spotlight"
          style={{
            left: highlightElement.getBoundingClientRect().left - 4,
            top: highlightElement.getBoundingClientRect().top - 4,
            width: highlightElement.getBoundingClientRect().width + 8,
            height: highlightElement.getBoundingClientRect().height + 8,
          }}
        />
      )}

      {/* Tutorial Card */}
      <Card
        ref={tutorialRef}
        className="fixed z-[9999] w-96 shadow-2xl"
        style={highlightElement ? getTooltipPosition() : {
          left: '50%',
          top: '50%',
          transform: 'translate(-50%, -50%)'
        }}
      >
        {/* Header */}
        <div className="p-4 border-b">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold">{currentStep.title}</h3>
              <p className="text-sm text-gray-500 mt-1">
                Step {currentStepIndex + 1} of {sequence.steps.length}
              </p>
            </div>
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsPaused(!isPaused)}
              >
                {isPaused ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleSkip}
              >
                <SkipForward className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
          <Progress value={progress} className="mt-3" />
        </div>

        {/* Content */}
        <div className="p-4">
          <div className="space-y-3">
            {typeof currentStep.content === 'string' ? (
              <p className="text-sm">{currentStep.content}</p>
            ) : (
              currentStep.content
            )}

            {currentStep.action && (
              <div className="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
                {currentStep.action.type === 'click' && <MousePointer className="h-4 w-4 text-blue-600" />}
                {currentStep.action.type === 'input' && <Keyboard className="h-4 w-4 text-blue-600" />}
                {currentStep.action.type === 'hover' && <Target className="h-4 w-4 text-blue-600" />}
                <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                  {currentStep.action.description}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t">
          <div className="flex items-center justify-between">
            <Button
              variant="outline"
              size="sm"
              onClick={handleBack}
              disabled={currentStepIndex === 0}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Back
            </Button>
            
            <div className="flex gap-1">
              {sequence.steps.map((step, index) => (
                <div
                  key={step.id}
                  className={`w-2 h-2 rounded-full transition-colors ${
                    index === currentStepIndex
                      ? 'bg-blue-600'
                      : completedSteps.has(step.id)
                      ? 'bg-green-600'
                      : 'bg-gray-300'
                  }`}
                />
              ))}
            </div>

            <Button
              size="sm"
              onClick={handleNext}
            >
              {isLastStep ? (
                <>
                  Complete
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
    </>
  )

  // Render in portal to ensure it's above everything
  return typeof document !== 'undefined' 
    ? createPortal(tooltipContent, document.body)
    : null
}

// Tutorial launcher component
export function TutorialLauncher({
  tutorials,
  className
}: {
  tutorials: TutorialSequence[]
  className?: string
}) {
  const [activeTutorial, setActiveTutorial] = useState<TutorialSequence | null>(null)
  const [completedTutorials, setCompletedTutorials] = useState<Set<string>>(
    new Set(JSON.parse(localStorage.getItem('completedTutorials') || '[]'))
  )

  const handleComplete = (tutorialId: string) => {
    const newCompleted = new Set([...completedTutorials, tutorialId])
    setCompletedTutorials(newCompleted)
    localStorage.setItem('completedTutorials', JSON.stringify([...newCompleted]))
  }

  const handleReset = (tutorialId: string) => {
    const newCompleted = new Set(completedTutorials)
    newCompleted.delete(tutorialId)
    setCompletedTutorials(newCompleted)
    localStorage.setItem('completedTutorials', JSON.stringify([...newCompleted]))
  }

  return (
    <>
      <div className={className}>
        <div className="space-y-2">
          {tutorials.map((tutorial) => {
            const isCompleted = completedTutorials.has(tutorial.id)
            
            return (
              <Card key={tutorial.id} className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium">{tutorial.name}</h4>
                      {isCompleted && (
                        <Badge variant="secondary" className="text-xs">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Completed
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      {tutorial.description}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                      <span>{tutorial.steps.length} steps</span>
                      <span>•</span>
                      <span>{tutorial.estimatedTime} min</span>
                      <span>•</span>
                      <span>{tutorial.category}</span>
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    {isCompleted && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleReset(tutorial.id)}
                      >
                        <RotateCcw className="h-4 w-4" />
                      </Button>
                    )}
                    <Button
                      variant={isCompleted ? 'outline' : 'default'}
                      size="sm"
                      onClick={() => setActiveTutorial(tutorial)}
                    >
                      {isCompleted ? 'Review' : 'Start'}
                    </Button>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      </div>

      {activeTutorial && (
        <InteractiveTutorial
          sequence={activeTutorial}
          onClose={() => setActiveTutorial(null)}
          onComplete={() => handleComplete(activeTutorial.id)}
        />
      )}
    </>
  )
}

// Pre-built tutorial sequences
export const TUTORIAL_SEQUENCES: TutorialSequence[] = [
  {
    id: 'getting-started',
    name: 'Getting Started with SentinelOps',
    description: 'Learn the basics of navigating and using SentinelOps',
    category: 'Basics',
    estimatedTime: 5,
    steps: [
      {
        id: 'welcome',
        title: 'Welcome to SentinelOps!',
        content: (
          <div className="space-y-3">
            <p>Let's take a quick tour to help you get familiar with the interface.</p>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Info className="h-4 w-4" />
              <span>You can pause or skip this tutorial at any time.</span>
            </div>
          </div>
        ),
        position: 'center'
      },
      {
        id: 'dashboard',
        title: 'Main Dashboard',
        content: 'This is your command center. Here you can see an overview of all incidents, agent activities, and system health.',
        target: '[data-tutorial="dashboard"]',
        position: 'bottom'
      },
      {
        id: 'incidents',
        title: 'Incident List',
        content: 'View and manage all security incidents. Click on any incident to see details and take action.',
        target: '[data-tutorial="incidents-list"]',
        position: 'right',
        action: {
          type: 'click',
          description: 'Click on an incident to view details'
        }
      },
      {
        id: 'agents',
        title: 'AI Agents Panel',
        content: 'Monitor the status and activities of all AI agents working on your behalf.',
        target: '[data-tutorial="agents-panel"]',
        position: 'left'
      },
      {
        id: 'chat',
        title: 'AI Assistant',
        content: 'Ask questions, get recommendations, and control the system using natural language.',
        target: '[data-tutorial="chat-interface"]',
        position: 'top',
        action: {
          type: 'input',
          description: 'Try typing a question'
        }
      }
    ]
  },
  {
    id: 'incident-response',
    name: 'Responding to Incidents',
    description: 'Learn how to investigate and respond to security incidents',
    category: 'Incidents',
    estimatedTime: 8,
    steps: [
      {
        id: 'incident-overview',
        title: 'Understanding Incidents',
        content: 'SentinelOps automatically detects and categorizes security incidents based on severity and type.',
        position: 'center'
      },
      {
        id: 'incident-details',
        title: 'Incident Details',
        content: 'Click on any incident to view comprehensive details including timeline, affected resources, and recommended actions.',
        target: '[data-tutorial="incident-card"]',
        position: 'bottom',
        action: {
          type: 'click',
          description: 'Click to open incident details'
        }
      },
      {
        id: 'remediation',
        title: 'Remediation Actions',
        content: 'Review AI-recommended remediation actions. You can approve, modify, or reject each action.',
        target: '[data-tutorial="remediation-actions"]',
        position: 'right'
      },
      {
        id: 'approval',
        title: 'Approval Workflow',
        content: 'Critical actions require approval. You can set up approval chains and automated policies.',
        target: '[data-tutorial="approval-button"]',
        position: 'top',
        action: {
          type: 'click',
          description: 'Click to approve or reject'
        }
      }
    ]
  }
]