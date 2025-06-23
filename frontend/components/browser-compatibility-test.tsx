'use client'

import { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CheckCircle2, XCircle, AlertCircle, Loader2 } from 'lucide-react'

interface FeatureSupport {
  name: string
  supported: boolean | null
  description: string
  critical: boolean
}

interface BrowserInfo {
  name: string
  version: string
  platform: string
  userAgent: string
}

export function BrowserCompatibilityTest() {
  const [browserInfo, setBrowserInfo] = useState<BrowserInfo | null>(null)
  const [features, setFeatures] = useState<FeatureSupport[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [cssSupport, setCssSupport] = useState<Record<string, boolean>>({})

  useEffect(() => {
    // Detect browser info
    const detectBrowser = () => {
      const ua = navigator.userAgent
      let browserName = 'Unknown'
      let browserVersion = ''

      if (ua.includes('Firefox/')) {
        browserName = 'Firefox'
        browserVersion = ua.match(/Firefox\/(\d+\.\d+)/)?.[1] || ''
      } else if (ua.includes('Edg/')) {
        browserName = 'Edge'
        browserVersion = ua.match(/Edg\/(\d+\.\d+)/)?.[1] || ''
      } else if (ua.includes('Chrome/')) {
        browserName = 'Chrome'
        browserVersion = ua.match(/Chrome\/(\d+\.\d+)/)?.[1] || ''
      } else if (ua.includes('Safari/') && !ua.includes('Chrome')) {
        browserName = 'Safari'
        browserVersion = ua.match(/Version\/(\d+\.\d+)/)?.[1] || ''
      }

      setBrowserInfo({
        name: browserName,
        version: browserVersion,
        platform: navigator.platform,
        userAgent: ua
      })
    }

    // Test feature support
    const testFeatures = () => {
      const featureTests: FeatureSupport[] = [
        {
          name: 'IntersectionObserver',
          supported: 'IntersectionObserver' in window,
          description: 'Used for lazy loading and visibility detection',
          critical: true
        },
        {
          name: 'ResizeObserver',
          supported: 'ResizeObserver' in window,
          description: 'Used for responsive component sizing',
          critical: true
        },
        {
          name: 'matchMedia',
          supported: 'matchMedia' in window,
          description: 'Used for responsive breakpoints',
          critical: true
        },
        {
          name: 'CSS Grid',
          supported: CSS.supports('display', 'grid'),
          description: 'Used for complex layouts',
          critical: true
        },
        {
          name: 'CSS Custom Properties',
          supported: CSS.supports('--test', '0'),
          description: 'Used for theming and design tokens',
          critical: true
        },
        {
          name: 'Flexbox Gap',
          supported: CSS.supports('gap', '1rem'),
          description: 'Used for spacing in flex layouts',
          critical: false
        },
        {
          name: 'Backdrop Filter',
          supported: CSS.supports('backdrop-filter', 'blur(10px)') || 
                     CSS.supports('-webkit-backdrop-filter', 'blur(10px)'),
          description: 'Used for glass morphism effects',
          critical: false
        },
        {
          name: 'Smooth Scroll',
          supported: 'scrollBehavior' in document.documentElement.style,
          description: 'Used for smooth scrolling animations',
          critical: false
        },
        {
          name: 'Service Worker',
          supported: 'serviceWorker' in navigator,
          description: 'Used for offline functionality',
          critical: false
        },
        {
          name: 'Web Storage',
          supported: typeof(Storage) !== 'undefined',
          description: 'Used for local data persistence',
          critical: true
        },
        {
          name: 'Fetch API',
          supported: 'fetch' in window,
          description: 'Used for API requests',
          critical: true
        },
        {
          name: 'Promise',
          supported: 'Promise' in window,
          description: 'Used for asynchronous operations',
          critical: true
        },
        {
          name: 'Array.from',
          supported: 'from' in Array,
          description: 'Used for array operations',
          critical: true
        },
        {
          name: 'Object.entries',
          supported: 'entries' in Object,
          description: 'Used for object iteration',
          critical: true
        }
      ]

      // Test CSS features
      const cssTests = {
        'sticky': CSS.supports('position', 'sticky') || CSS.supports('position', '-webkit-sticky'),
        'object-fit': CSS.supports('object-fit', 'cover'),
        'aspect-ratio': CSS.supports('aspect-ratio', '16/9'),
        'container-queries': CSS.supports('container-type', 'inline-size'),
        'has-selector': CSS.supports('selector(:has(*))')
      }

      setFeatures(featureTests)
      setCssSupport(cssTests)
      setIsLoading(false)
    }

    detectBrowser()
    testFeatures()
  }, [])

  const criticalFeatures = features.filter(f => f.critical)
  const optionalFeatures = features.filter(f => !f.critical)
  const allCriticalSupported = criticalFeatures.every(f => f.supported)
  const supportedCount = features.filter(f => f.supported).length

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Browser Compatibility Report</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Browser Info */}
          <div>
            <h3 className="font-semibold mb-2">Browser Information</h3>
            <div className="space-y-1 text-sm">
              <div>
                <span className="text-muted-foreground">Browser:</span>{' '}
                {browserInfo?.name} {browserInfo?.version}
              </div>
              <div>
                <span className="text-muted-foreground">Platform:</span>{' '}
                {browserInfo?.platform}
              </div>
            </div>
          </div>

          {/* Overall Status */}
          <Alert className={allCriticalSupported ? '' : 'border-destructive'}>
            <div className="flex items-center gap-2">
              {allCriticalSupported ? (
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              ) : (
                <XCircle className="h-4 w-4 text-destructive" />
              )}
              <AlertDescription>
                {allCriticalSupported
                  ? `All critical features are supported (${supportedCount}/${features.length} total)`
                  : 'Some critical features are not supported. The application may not work correctly.'}
              </AlertDescription>
            </div>
          </Alert>

          {/* Critical Features */}
          <div>
            <h3 className="font-semibold mb-3">Critical Features</h3>
            <div className="space-y-2">
              {criticalFeatures.map((feature) => (
                <div
                  key={feature.name}
                  className="flex items-center justify-between p-3 rounded-lg border"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      {feature.supported ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : (
                        <XCircle className="h-4 w-4 text-destructive" />
                      )}
                      <span className="font-medium">{feature.name}</span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {feature.description}
                    </p>
                  </div>
                  <Badge variant={feature.supported ? 'success' : 'destructive'}>
                    {feature.supported ? 'Supported' : 'Not Supported'}
                  </Badge>
                </div>
              ))}
            </div>
          </div>

          {/* Optional Features */}
          <div>
            <h3 className="font-semibold mb-3">Optional Features</h3>
            <div className="space-y-2">
              {optionalFeatures.map((feature) => (
                <div
                  key={feature.name}
                  className="flex items-center justify-between p-3 rounded-lg border"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      {feature.supported ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-yellow-500" />
                      )}
                      <span className="font-medium">{feature.name}</span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {feature.description}
                    </p>
                  </div>
                  <Badge
                    variant={feature.supported ? 'success' : 'secondary'}
                  >
                    {feature.supported ? 'Supported' : 'Not Supported'}
                  </Badge>
                </div>
              ))}
            </div>
          </div>

          {/* CSS Features */}
          <div>
            <h3 className="font-semibold mb-3">CSS Feature Support</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {Object.entries(cssSupport).map(([feature, supported]) => (
                <div
                  key={feature}
                  className="flex items-center gap-2 p-2 rounded border"
                >
                  {supported ? (
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-yellow-500" />
                  )}
                  <span className="text-sm capitalize">
                    {feature.replace('-', ' ')}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Recommendations */}
          {!allCriticalSupported && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-2">
                  <p className="font-semibold">Browser Update Recommended</p>
                  <p>
                    Some critical features are not supported in your browser.
                    Please update to the latest version or switch to a modern
                    browser like Chrome, Firefox, Edge, or Safari for the best
                    experience.
                  </p>
                </div>
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  )
}