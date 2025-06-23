'use client'

import { useState, useEffect } from 'react'
import { WelcomeTour, WelcomeBack } from './welcome-tour'
import { FeatureHighlights, FeatureAnnouncement } from './feature-highlights'
import { SampleScenarios } from './sample-scenarios'
import { ProgressTracking } from './progress-tracking'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { 
  Rocket,
  Skip,
  ChevronRight,
  CheckCircle,
  X,
  HelpCircle,
  BookOpen,
  PlayCircle,
  Trophy,
  Settings
} from 'lucide-react'

interface OnboardingState {
  hasCompletedTour: boolean
  hasSeenFeatures: boolean
  currentStep: 'tour' | 'features' | 'scenarios' | 'complete'
  skippedSteps: string[]
  completedAt?: Date
}

interface OnboardingFlowProps {
  forceShow?: boolean
  onComplete?: () => void
  showProgress?: boolean
}

export function OnboardingFlow({ 
  forceShow = false,
  onComplete,
  showProgress = true
}: OnboardingFlowProps) {
  const [state, setState] = useState<OnboardingState>({
    hasCompletedTour: false,
    hasSeenFeatures: false,
    currentStep: 'tour',
    skippedSteps: []
  })
  const [showFlow, setShowFlow] = useState(false)
  const [showSkipConfirm, setShowSkipConfirm] = useState(false)
  const [showProgressDialog, setShowProgressDialog] = useState(false)

  // Load saved state
  useEffect(() => {
    const savedState = localStorage.getItem('onboardingState')
    if (savedState) {
      const parsed = JSON.parse(savedState)
      setState({
        ...parsed,
        completedAt: parsed.completedAt ? new Date(parsed.completedAt) : undefined
      })
      
      // Show onboarding if forced or not completed
      if (forceShow || !parsed.completedAt) {
        setShowFlow(true)
      }
    } else if (forceShow) {
      setShowFlow(true)
    } else {
      // First time user
      setShowFlow(true)
    }
  }, [forceShow])

  // Save state changes
  const saveState = (newState: OnboardingState) => {
    setState(newState)
    localStorage.setItem('onboardingState', JSON.stringify(newState))
  }

  const handleTourComplete = () => {
    saveState({
      ...state,
      hasCompletedTour: true,
      currentStep: 'features'
    })
  }

  const handleTourSkip = () => {
    setShowSkipConfirm(true)
  }

  const confirmSkip = () => {
    saveState({
      ...state,
      skippedSteps: [...state.skippedSteps, state.currentStep],
      currentStep: 'complete',
      completedAt: new Date()
    })
    setShowFlow(false)
    setShowSkipConfirm(false)
    
    if (onComplete) {
      onComplete()
    }
  }

  const handleFeatureComplete = () => {
    saveState({
      ...state,
      hasSeenFeatures: true,
      currentStep: 'complete',
      completedAt: new Date()
    })
    
    if (onComplete) {
      onComplete()
    }
    
    // Show progress tracking after features
    if (showProgress) {
      setShowProgressDialog(true)
    }
  }

  const resetOnboarding = () => {
    localStorage.removeItem('onboardingState')
    localStorage.removeItem('completedTutorials')
    localStorage.removeItem('completedScenarios')
    localStorage.removeItem('onboardingProgress')
    localStorage.removeItem('dismissedFeatures')
    setState({
      hasCompletedTour: false,
      hasSeenFeatures: false,
      currentStep: 'tour',
      skippedSteps: []
    })
    setShowFlow(true)
  }

  // Don't render if onboarding is complete and not forced
  if (!showFlow && !forceShow) {
    return state.completedAt ? <WelcomeBack /> : null
  }

  return (
    <>
      {/* Main onboarding flow */}
      {showFlow && (
        <>
          {state.currentStep === 'tour' && !state.hasCompletedTour && (
            <WelcomeTour
              onComplete={handleTourComplete}
              onSkip={handleTourSkip}
            />
          )}

          {state.currentStep === 'features' && !state.hasSeenFeatures && (
            <FeatureHighlights
              onComplete={handleFeatureComplete}
              autoStart={true}
            />
          )}
        </>
      )}

      {/* Skip confirmation dialog */}
      <Dialog open={showSkipConfirm} onOpenChange={setShowSkipConfirm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Skip Onboarding?</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p>
              The onboarding process helps you get familiar with SentinelOps quickly. 
              Are you sure you want to skip it?
            </p>
            <Card className="p-4 bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
              <p className="text-sm">
                You can always access the onboarding content later from the Help menu.
              </p>
            </Card>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button
              variant="outline"
              onClick={() => setShowSkipConfirm(false)}
            >
              Continue Onboarding
            </Button>
            <Button
              variant="ghost"
              onClick={confirmSkip}
            >
              Skip for Now
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Progress tracking dialog */}
      <Dialog open={showProgressDialog} onOpenChange={setShowProgressDialog}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Your Learning Journey</DialogTitle>
          </DialogHeader>
          <ProgressTracking />
        </DialogContent>
      </Dialog>
    </>
  )
}

// Onboarding menu for accessing content later
export function OnboardingMenu({ className }: { className?: string }) {
  const [showMenu, setShowMenu] = useState(false)
  const [showScenarios, setShowScenarios] = useState(false)
  const [showProgress, setShowProgress] = useState(false)

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setShowMenu(true)}
        className={className}
      >
        <BookOpen className="h-4 w-4 mr-1" />
        Learning Center
      </Button>

      <Dialog open={showMenu} onOpenChange={setShowMenu}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Learning Center</DialogTitle>
          </DialogHeader>
          
          <div className="grid gap-4">
            <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => {
                setShowMenu(false)
                // Restart welcome tour
                const flow = new OnboardingFlow({ forceShow: true })
              }}
            >
              <div className="flex items-start gap-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                  <Rocket className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold">Welcome Tour</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Get reacquainted with SentinelOps features
                  </p>
                </div>
                <ChevronRight className="h-5 w-5 text-gray-400" />
              </div>
            </Card>

            <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => {
                setShowMenu(false)
                setShowScenarios(true)
              }}
            >
              <div className="flex items-start gap-3">
                <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                  <PlayCircle className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold">Practice Scenarios</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Interactive security incident simulations
                  </p>
                </div>
                <ChevronRight className="h-5 w-5 text-gray-400" />
              </div>
            </Card>

            <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => {
                setShowMenu(false)
                setShowProgress(true)
              }}
            >
              <div className="flex items-start gap-3">
                <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                  <Trophy className="h-5 w-5 text-green-600 dark:text-green-400" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold">Progress & Achievements</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Track your learning journey and unlock rewards
                  </p>
                </div>
                <ChevronRight className="h-5 w-5 text-gray-400" />
              </div>
            </Card>

            <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => window.open('/help', '_blank')}
            >
              <div className="flex items-start gap-3">
                <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
                  <HelpCircle className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold">Help & Documentation</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Comprehensive guides and tutorials
                  </p>
                </div>
                <ChevronRight className="h-5 w-5 text-gray-400" />
              </div>
            </Card>
          </div>
        </DialogContent>
      </Dialog>

      {/* Sample Scenarios Dialog */}
      <Dialog open={showScenarios} onOpenChange={setShowScenarios}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Practice Scenarios</DialogTitle>
          </DialogHeader>
          <SampleScenarios />
        </DialogContent>
      </Dialog>

      {/* Progress Dialog */}
      <Dialog open={showProgress} onOpenChange={setShowProgress}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Your Progress</DialogTitle>
          </DialogHeader>
          <ProgressTracking />
        </DialogContent>
      </Dialog>
    </>
  )
}

// Quick onboarding status indicator
export function OnboardingStatus() {
  const [status, setStatus] = useState<'new' | 'in-progress' | 'completed' | null>(null)

  useEffect(() => {
    const savedState = localStorage.getItem('onboardingState')
    if (!savedState) {
      setStatus('new')
    } else {
      const state = JSON.parse(savedState)
      if (state.completedAt) {
        setStatus('completed')
      } else {
        setStatus('in-progress')
      }
    }
  }, [])

  if (!status || status === 'completed') return null

  return (
    <Badge 
      variant={status === 'new' ? 'default' : 'secondary'}
      className="text-xs"
    >
      {status === 'new' ? 'New User' : 'Onboarding'}
    </Badge>
  )
}