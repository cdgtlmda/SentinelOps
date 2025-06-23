'use client'

import React, { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { 
  ChevronDown, 
  ChevronRight, 
  AlertTriangle, 
  CheckCircle, 
  Navigation,
  Eye,
  EyeOff
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { LANDMARK_REGIONS } from '@/lib/accessibility/semantic-html-guide'

interface Landmark {
  element: Element
  role: string
  label?: string
  level: number
  parent?: Landmark
  children: Landmark[]
  issues: string[]
}

interface LandmarkNavigatorProps {
  /**
   * Whether to show the visual indicator
   * Set to false in production
   */
  showVisualIndicator?: boolean
  className?: string
}

/**
 * Development tool for visualizing and navigating landmark regions
 * Helps developers ensure proper landmark structure
 */
export const LandmarkNavigator: React.FC<LandmarkNavigatorProps> = ({
  showVisualIndicator = process.env.NODE_ENV === 'development',
  className
}) => {
  const [landmarks, setLandmarks] = useState<Landmark[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [highlightedLandmark, setHighlightedLandmark] = useState<Element | null>(null)
  const [showIndicators, setShowIndicators] = useState(showVisualIndicator)

  // Scan for landmarks
  const scanLandmarks = () => {
    const landmarkSelectors = [
      '[role="banner"], header:not([role])',
      '[role="navigation"], nav:not([role])',
      '[role="main"], main:not([role])',
      '[role="complementary"], aside:not([role])',
      '[role="contentinfo"], footer:not([role])',
      '[role="search"], search:not([role])',
      '[role="form"][aria-label], [role="form"][aria-labelledby]',
      '[role="region"][aria-label], [role="region"][aria-labelledby], section[aria-label], section[aria-labelledby]'
    ]

    const elements = document.querySelectorAll(landmarkSelectors.join(', '))
    const landmarkMap = new Map<Element, Landmark>()

    // Build landmark hierarchy
    elements.forEach(element => {
      const role = getLandmarkRole(element)
      const label = getLandmarkLabel(element)
      const issues = validateLandmark(element, role)

      const landmark: Landmark = {
        element,
        role,
        label,
        level: 0,
        children: [],
        issues
      }

      landmarkMap.set(element, landmark)
    })

    // Establish parent-child relationships
    landmarkMap.forEach((landmark, element) => {
      let parent = element.parentElement
      while (parent) {
        if (landmarkMap.has(parent)) {
          landmark.parent = landmarkMap.get(parent)
          landmark.parent!.children.push(landmark)
          landmark.level = landmark.parent!.level + 1
          break
        }
        parent = parent.parentElement
      }
    })

    // Get top-level landmarks
    const topLevel = Array.from(landmarkMap.values()).filter(l => !l.parent)
    setLandmarks(topLevel)
  }

  // Get the role of a landmark element
  const getLandmarkRole = (element: Element): string => {
    if (element.hasAttribute('role')) {
      return element.getAttribute('role')!
    }
    
    const tagName = element.tagName.toLowerCase()
    const roleMap: Record<string, string> = {
      header: 'banner',
      nav: 'navigation',
      main: 'main',
      aside: 'complementary',
      footer: 'contentinfo',
      search: 'search',
      form: 'form',
      section: 'region'
    }
    
    return roleMap[tagName] || tagName
  }

  // Get the accessible label of a landmark
  const getLandmarkLabel = (element: Element): string | undefined => {
    // Check aria-label
    if (element.hasAttribute('aria-label')) {
      return element.getAttribute('aria-label')!
    }

    // Check aria-labelledby
    if (element.hasAttribute('aria-labelledby')) {
      const ids = element.getAttribute('aria-labelledby')!.split(' ')
      const labels = ids
        .map(id => document.getElementById(id)?.textContent?.trim())
        .filter(Boolean)
      if (labels.length > 0) {
        return labels.join(' ')
      }
    }

    // For forms, check for legend
    if (element.tagName.toLowerCase() === 'form') {
      const legend = element.querySelector('legend')
      if (legend) {
        return legend.textContent?.trim()
      }
    }

    return undefined
  }

  // Validate landmark for common issues
  const validateLandmark = (element: Element, role: string): string[] => {
    const issues: string[] = []

    // Check for multiple banner/contentinfo landmarks
    if (role === 'banner' || role === 'contentinfo') {
      const selector = `[role="${role}"], ${role === 'banner' ? 'header' : 'footer'}:not([role])`
      const similar = document.querySelectorAll(selector)
      if (similar.length > 1) {
        issues.push(`Multiple ${role} landmarks found. Only one should exist per page.`)
      }
    }

    // Check for missing labels on generic landmarks
    if ((role === 'navigation' || role === 'region' || role === 'form') && !getLandmarkLabel(element)) {
      const selector = role === 'navigation' ? 'nav' : role === 'region' ? 'section' : 'form'
      const similar = document.querySelectorAll(`[role="${role}"], ${selector}:not([role])`)
      if (similar.length > 1) {
        issues.push(`Multiple ${role} landmarks found without labels. Add aria-label or aria-labelledby to distinguish them.`)
      }
    }

    // Check for missing main landmark
    if (role === 'main') {
      const mains = document.querySelectorAll('[role="main"], main:not([role])')
      if (mains.length === 0) {
        issues.push('No main landmark found. Every page should have one main landmark.')
      } else if (mains.length > 1) {
        issues.push('Multiple main landmarks found. Only one should exist per page.')
      }
    }

    // Check for form without accessible name
    if (role === 'form' && !getLandmarkLabel(element)) {
      issues.push('Form landmark without accessible name. Add aria-label or aria-labelledby.')
    }

    return issues
  }

  // Navigate to a landmark
  const navigateToLandmark = (landmark: Landmark) => {
    landmark.element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    ;(landmark.element as HTMLElement).focus({ preventScroll: true })
    setHighlightedLandmark(landmark.element)
    
    // Remove highlight after 2 seconds
    setTimeout(() => {
      setHighlightedLandmark(null)
    }, 2000)
  }

  // Render landmark tree item
  const renderLandmarkItem = (landmark: Landmark, index: number) => {
    const hasIssues = landmark.issues.length > 0
    const isHighlighted = landmark.element === highlightedLandmark

    return (
      <div key={`${landmark.role}-${index}`} className="space-y-2">
        <div 
          className={cn(
            "flex items-start gap-2 p-2 rounded-md transition-colors",
            isHighlighted && "bg-blue-100 dark:bg-blue-900",
            hasIssues && "bg-red-50 dark:bg-red-900/20"
          )}
        >
          <Button
            variant="ghost"
            size="sm"
            className="h-auto p-1 flex items-center gap-2"
            onClick={() => navigateToLandmark(landmark)}
          >
            <Navigation className="h-4 w-4" />
            <span className="font-medium">{landmark.role}</span>
            {landmark.label && (
              <span className="text-muted-foreground">"{landmark.label}"</span>
            )}
          </Button>
          
          {hasIssues && (
            <Collapsible>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm" className="h-auto p-1">
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="ml-6 mt-1 space-y-1">
                  {landmark.issues.map((issue, i) => (
                    <p key={i} className="text-sm text-red-600 dark:text-red-400">
                      {issue}
                    </p>
                  ))}
                </div>
              </CollapsibleContent>
            </Collapsible>
          )}
        </div>

        {landmark.children.length > 0 && (
          <div className="ml-6 border-l-2 border-gray-200 dark:border-gray-700 pl-4">
            {landmark.children.map((child, i) => renderLandmarkItem(child, i))}
          </div>
        )}
      </div>
    )
  }

  // Add visual indicators to landmarks
  useEffect(() => {
    if (!showIndicators) return

    const styleId = 'landmark-indicators-style'
    let styleElement = document.getElementById(styleId) as HTMLStyleElement

    if (!styleElement) {
      styleElement = document.createElement('style')
      styleElement.id = styleId
      document.head.appendChild(styleElement)
    }

    styleElement.textContent = `
      [role="banner"], header:not([role]),
      [role="navigation"], nav:not([role]),
      [role="main"], main:not([role]),
      [role="complementary"], aside:not([role]),
      [role="contentinfo"], footer:not([role]),
      [role="search"], search:not([role]),
      [role="form"][aria-label], [role="form"][aria-labelledby],
      [role="region"][aria-label], [role="region"][aria-labelledby],
      section[aria-label], section[aria-labelledby] {
        position: relative;
        outline: 2px dashed rgba(59, 130, 246, 0.5);
        outline-offset: 2px;
      }

      [role="banner"]::before, header:not([role])::before,
      [role="navigation"]::before, nav:not([role])::before,
      [role="main"]::before, main:not([role])::before,
      [role="complementary"]::before, aside:not([role])::before,
      [role="contentinfo"]::before, footer:not([role])::before,
      [role="search"]::before, search:not([role])::before,
      [role="form"][aria-label]::before, [role="form"][aria-labelledby]::before,
      [role="region"][aria-label]::before, [role="region"][aria-labelledby]::before,
      section[aria-label]::before, section[aria-labelledby]::before {
        content: attr(role) " landmark";
        position: absolute;
        top: -24px;
        left: 0;
        font-size: 11px;
        font-weight: bold;
        background: rgba(59, 130, 246, 0.9);
        color: white;
        padding: 2px 6px;
        border-radius: 3px;
        z-index: 9999;
        pointer-events: none;
      }

      header:not([role])::before { content: "banner landmark"; }
      nav:not([role])::before { content: "navigation landmark"; }
      main:not([role])::before { content: "main landmark"; }
      aside:not([role])::before { content: "complementary landmark"; }
      footer:not([role])::before { content: "contentinfo landmark"; }
      search:not([role])::before { content: "search landmark"; }
      section[aria-label]::before, section[aria-labelledby]::before { content: "region landmark"; }
    `

    return () => {
      if (styleElement && styleElement.parentNode) {
        styleElement.parentNode.removeChild(styleElement)
      }
    }
  }, [showIndicators])

  // Scan landmarks on mount and when DOM changes
  useEffect(() => {
    scanLandmarks()

    // Watch for DOM changes
    const observer = new MutationObserver(() => {
      scanLandmarks()
    })

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['role', 'aria-label', 'aria-labelledby']
    })

    return () => {
      observer.disconnect()
    }
  }, [])

  if (!showVisualIndicator) return null

  const totalIssues = landmarks.reduce((sum, l) => {
    const countIssues = (landmark: Landmark): number => {
      return landmark.issues.length + landmark.children.reduce((s, c) => s + countIssues(c), 0)
    }
    return sum + countIssues(l)
  }, 0)

  return (
    <div className={cn("fixed bottom-4 right-4 z-50", className)}>
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <Button 
            variant="outline" 
            size="sm"
            className={cn(
              "gap-2",
              totalIssues > 0 && "border-red-500"
            )}
          >
            <Navigation className="h-4 w-4" />
            Landmarks
            {totalIssues > 0 ? (
              <Badge variant="destructive">{totalIssues}</Badge>
            ) : (
              <CheckCircle className="h-4 w-4 text-green-500" />
            )}
            {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </Button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <Card className="mt-2 w-96 max-h-[600px] overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center justify-between">
                Landmark Navigator
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowIndicators(!showIndicators)}
                  title={showIndicators ? "Hide indicators" : "Show indicators"}
                >
                  {showIndicators ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 overflow-y-auto max-h-[500px]">
              {landmarks.length === 0 ? (
                <p className="text-sm text-muted-foreground">No landmarks found</p>
              ) : (
                <div className="space-y-2">
                  {landmarks.map((landmark, index) => renderLandmarkItem(landmark, index))}
                </div>
              )}

              <div className="border-t pt-4 space-y-2">
                <p className="text-xs text-muted-foreground">
                  Click on a landmark to navigate to it. Visual indicators {showIndicators ? 'shown' : 'hidden'}.
                </p>
                {totalIssues > 0 && (
                  <p className="text-xs text-red-600 dark:text-red-400">
                    {totalIssues} accessibility {totalIssues === 1 ? 'issue' : 'issues'} found
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </CollapsibleContent>
      </Collapsible>
    </div>
  )
}