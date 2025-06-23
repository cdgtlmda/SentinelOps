'use client'

import { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Sparkles,
  X,
  ChevronRight,
  Star,
  Zap,
  TrendingUp,
  Shield,
  Clock,
  Users,
  BarChart3,
  MessageSquare,
  Settings,
  Lightbulb
} from 'lucide-react'

interface Feature {
  id: string
  title: string
  description: string
  icon: React.ElementType
  category: 'new' | 'improved' | 'tip'
  targetSelector?: string
  position?: 'top' | 'bottom' | 'left' | 'right'
  image?: string
  learnMoreUrl?: string
}

const FEATURE_HIGHLIGHTS: Feature[] = [
  {
    id: 'ai-chat',
    title: 'AI-Powered Chat Assistant',
    description: 'Ask questions in natural language and get instant insights about your security posture.',
    icon: MessageSquare,
    category: 'new',
    targetSelector: '[data-feature="chat-interface"]',
    position: 'left'
  },
  {
    id: 'smart-remediation',
    title: 'One-Click Smart Remediation',
    description: 'AI analyzes incidents and suggests the best remediation actions. Just review and approve!',
    icon: Zap,
    category: 'improved',
    targetSelector: '[data-feature="remediation-panel"]',
    position: 'top'
  },
  {
    id: 'real-time-collab',
    title: 'Real-Time Agent Collaboration',
    description: 'Watch AI agents work together in real-time to investigate and resolve incidents.',
    icon: Users,
    category: 'new',
    targetSelector: '[data-feature="agent-collaboration"]',
    position: 'bottom'
  },
  {
    id: 'predictive-analytics',
    title: 'Predictive Security Analytics',
    description: 'ML models predict potential security issues before they become incidents.',
    icon: TrendingUp,
    category: 'new',
    targetSelector: '[data-feature="analytics-dashboard"]',
    position: 'right'
  },
  {
    id: 'quick-actions',
    title: 'Quick Actions Toolbar',
    description: 'Access your most-used actions instantly. Customize it to match your workflow!',
    icon: Lightbulb,
    category: 'tip',
    targetSelector: '[data-feature="quick-actions"]',
    position: 'bottom'
  }
]

interface FeatureHighlightsProps {
  onComplete?: () => void
  autoStart?: boolean
  features?: Feature[]
}

export function FeatureHighlights({ 
  onComplete,
  autoStart = true,
  features = FEATURE_HIGHLIGHTS
}: FeatureHighlightsProps) {
  const [isActive, setIsActive] = useState(autoStart)
  const [currentFeatureIndex, setCurrentFeatureIndex] = useState(0)
  const [dismissedFeatures, setDismissedFeatures] = useState<Set<string>>(
    new Set(JSON.parse(localStorage.getItem('dismissedFeatures') || '[]'))
  )
  const [highlightElement, setHighlightElement] = useState<HTMLElement | null>(null)
  const highlightRef = useRef<HTMLDivElement>(null)

  const activeFeaturesLocal = features.filter(f => !dismissedFeatures.has(f.id))
  const currentFeature = activeFeaturesLocal[currentFeatureIndex]
  const hasFeatures = activeFeaturesLocal.length > 0

  useEffect(() => {
    if (!isActive || !currentFeature || !currentFeature.targetSelector) {
      setHighlightElement(null)
      return
    }

    const element = document.querySelector(currentFeature.targetSelector) as HTMLElement
    if (element) {
      setHighlightElement(element)
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      
      // Add pulse animation
      element.classList.add('feature-highlight-pulse')
      
      return () => {
        element.classList.remove('feature-highlight-pulse')
      }
    }
  }, [currentFeature, isActive])

  useEffect(() => {
    // Add global styles
    const style = document.createElement('style')
    style.textContent = `
      @keyframes feature-pulse {
        0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }
        100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
      }
      
      .feature-highlight-pulse {
        animation: feature-pulse 2s infinite;
        position: relative;
        z-index: 9998;
      }
      
      .feature-highlight-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.3);
        z-index: 9997;
      }
    `
    document.head.appendChild(style)

    return () => {
      document.head.removeChild(style)
    }
  }, [])

  const handleNext = () => {
    if (currentFeatureIndex < activeFeaturesLocal.length - 1) {
      setCurrentFeatureIndex(currentFeatureIndex + 1)
    } else {
      handleComplete()
    }
  }

  const handleSkip = () => {
    handleComplete()
  }

  const handleDismiss = () => {
    if (currentFeature) {
      const newDismissed = new Set([...dismissedFeatures, currentFeature.id])
      setDismissedFeatures(newDismissed)
      localStorage.setItem('dismissedFeatures', JSON.stringify([...newDismissed]))
      
      if (currentFeatureIndex >= activeFeaturesLocal.length - 1) {
        handleComplete()
      }
    }
  }

  const handleComplete = () => {
    setIsActive(false)
    if (onComplete) {
      onComplete()
    }
  }

  const getHighlightPosition = () => {
    if (!highlightElement || !highlightRef.current) return {}

    const targetRect = highlightElement.getBoundingClientRect()
    const highlightRect = highlightRef.current.getBoundingClientRect()
    const position = currentFeature?.position || 'bottom'
    const offset = 20

    let style: React.CSSProperties = {}

    switch (position) {
      case 'top':
        style = {
          left: targetRect.left + targetRect.width / 2 - highlightRect.width / 2,
          bottom: window.innerHeight - targetRect.top + offset
        }
        break
      case 'bottom':
        style = {
          left: targetRect.left + targetRect.width / 2 - highlightRect.width / 2,
          top: targetRect.bottom + offset
        }
        break
      case 'left':
        style = {
          right: window.innerWidth - targetRect.left + offset,
          top: targetRect.top + targetRect.height / 2 - highlightRect.height / 2
        }
        break
      case 'right':
        style = {
          left: targetRect.right + offset,
          top: targetRect.top + targetRect.height / 2 - highlightRect.height / 2
        }
        break
    }

    // Keep within viewport
    if (style.left && typeof style.left === 'number') {
      style.left = Math.max(10, Math.min(style.left, window.innerWidth - highlightRect.width - 10))
    }
    if (style.top && typeof style.top === 'number') {
      style.top = Math.max(10, Math.min(style.top, window.innerHeight - highlightRect.height - 10))
    }

    return style
  }

  const getCategoryColor = (category: Feature['category']) => {
    switch (category) {
      case 'new':
        return 'bg-green-500'
      case 'improved':
        return 'bg-blue-500'
      case 'tip':
        return 'bg-purple-500'
    }
  }

  const getCategoryLabel = (category: Feature['category']) => {
    switch (category) {
      case 'new':
        return 'NEW'
      case 'improved':
        return 'IMPROVED'
      case 'tip':
        return 'TIP'
    }
  }

  if (!isActive || !hasFeatures || !currentFeature) return null

  const Icon = currentFeature.icon

  const content = (
    <>
      {/* Overlay */}
      {highlightElement && (
        <div className="feature-highlight-overlay" onClick={handleSkip} />
      )}

      {/* Highlight Card */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentFeature.id}
          ref={highlightRef}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          className="fixed z-[9999] w-96"
          style={highlightElement ? getHighlightPosition() : {
            left: '50%',
            top: '50%',
            transform: 'translate(-50%, -50%)'
          }}
        >
          <Card className="shadow-2xl border-2 border-blue-200 dark:border-blue-800">
            <div className="p-4">
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">{currentFeature.title}</h3>
                      <Badge className={`${getCategoryColor(currentFeature.category)} text-white text-xs`}>
                        {getCategoryLabel(currentFeature.category)}
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Feature {currentFeatureIndex + 1} of {activeFeaturesLocal.length}
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleSkip}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {/* Content */}
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                {currentFeature.description}
              </p>

              {/* Actions */}
              <div className="flex items-center justify-between">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleDismiss}
                >
                  Don't show again
                </Button>
                
                <div className="flex gap-2">
                  {currentFeature.learnMoreUrl && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => window.open(currentFeature.learnMoreUrl, '_blank')}
                    >
                      Learn More
                    </Button>
                  )}
                  <Button size="sm" onClick={handleNext}>
                    {currentFeatureIndex < activeFeaturesLocal.length - 1 ? (
                      <>
                        Next
                        <ChevronRight className="h-4 w-4 ml-1" />
                      </>
                    ) : (
                      'Got it!'
                    )}
                  </Button>
                </div>
              </div>
            </div>

            {/* Progress dots */}
            <div className="px-4 pb-3">
              <div className="flex justify-center gap-1">
                {activeFeaturesLocal.map((_, index) => (
                  <div
                    key={index}
                    className={`w-1.5 h-1.5 rounded-full transition-colors ${
                      index === currentFeatureIndex
                        ? 'bg-blue-600'
                        : index < currentFeatureIndex
                        ? 'bg-blue-400'
                        : 'bg-gray-300'
                    }`}
                  />
                ))}
              </div>
            </div>
          </Card>
        </motion.div>
      </AnimatePresence>
    </>
  )

  return typeof document !== 'undefined' 
    ? createPortal(content, document.body)
    : null
}

// Feature announcement banner for new releases
export function FeatureAnnouncement({ 
  version,
  features,
  onDismiss
}: {
  version: string
  features: string[]
  onDismiss: () => void
}) {
  const [show, setShow] = useState(true)

  useEffect(() => {
    const dismissedVersion = localStorage.getItem('dismissedFeatureVersion')
    if (dismissedVersion === version) {
      setShow(false)
    }
  }, [version])

  const handleDismiss = () => {
    localStorage.setItem('dismissedFeatureVersion', version)
    setShow(false)
    onDismiss()
  }

  if (!show) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="bg-gradient-to-r from-blue-600 to-purple-600 text-white"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="py-3 sm:py-4">
          <div className="flex items-center justify-between flex-wrap">
            <div className="flex-1 flex items-center">
              <span className="flex p-2 rounded-lg bg-white/20">
                <Sparkles className="h-6 w-6" />
              </span>
              <div className="ml-3">
                <p className="font-medium">
                  What's new in v{version}
                </p>
                <p className="text-sm text-white/90">
                  {features.join(' • ')}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4 mt-2 sm:mt-0">
              <Button
                variant="secondary"
                size="sm"
                className="bg-white/20 hover:bg-white/30 text-white border-0"
                onClick={() => {/* Show feature highlights */}}
              >
                <Star className="h-4 w-4 mr-1" />
                Show me
              </Button>
              <button
                onClick={handleDismiss}
                className="text-white/80 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

// Inline feature callout
export function FeatureCallout({
  title,
  description,
  icon: Icon = Lightbulb,
  onTryIt
}: {
  title: string
  description: string
  icon?: React.ElementType
  onTryIt?: () => void
}) {
  return (
    <Card className="p-4 border-blue-200 dark:border-blue-800 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/50 dark:to-purple-950/50">
      <div className="flex items-start gap-3">
        <div className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
          <Icon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
        </div>
        <div className="flex-1">
          <h4 className="font-semibold mb-1">{title}</h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {description}
          </p>
          {onTryIt && (
            <Button
              variant="link"
              size="sm"
              onClick={onTryIt}
              className="mt-2 p-0 h-auto text-blue-600 dark:text-blue-400"
            >
              Try it now →
            </Button>
          )}
        </div>
      </div>
    </Card>
  )
}