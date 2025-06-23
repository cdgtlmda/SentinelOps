'use client'

import dynamic from 'next/dynamic'
import { ComponentType, ReactNode } from 'react'
import { Skeleton } from '@/components/ui/skeleton'
import { Card } from '@/components/ui/card'
import { Loader2 } from 'lucide-react'

// Loading components for different types of content
export const TableSkeleton = () => (
  <div className="space-y-3">
    <div className="flex gap-3">
      <Skeleton className="h-10 w-[200px]" />
      <Skeleton className="h-10 w-[100px]" />
      <Skeleton className="h-10 flex-1" />
    </div>
    {Array.from({ length: 5 }).map((_, i) => (
      <div key={i} className="flex gap-3">
        <Skeleton className="h-12 w-[200px]" />
        <Skeleton className="h-12 w-[100px]" />
        <Skeleton className="h-12 flex-1" />
      </div>
    ))}
  </div>
)

export const ChartSkeleton = () => (
  <Card className="p-6">
    <Skeleton className="h-6 w-[200px] mb-4" />
    <Skeleton className="h-[300px] w-full" />
  </Card>
)

export const CardGridSkeleton = () => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {Array.from({ length: 6 }).map((_, i) => (
      <Card key={i} className="p-6">
        <Skeleton className="h-12 w-12 rounded-lg mb-4" />
        <Skeleton className="h-6 w-3/4 mb-2" />
        <Skeleton className="h-4 w-full mb-1" />
        <Skeleton className="h-4 w-5/6" />
      </Card>
    ))}
  </div>
)

export const ChatSkeleton = () => (
  <div className="flex flex-col h-full">
    <div className="flex-1 space-y-4 p-4">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className={`flex ${i % 2 === 0 ? 'justify-start' : 'justify-end'}`}>
          <div className={`max-w-[70%] ${i % 2 === 0 ? '' : 'text-right'}`}>
            <Skeleton className="h-4 w-20 mb-2" />
            <Skeleton className="h-20 w-full rounded-lg" />
          </div>
        </div>
      ))}
    </div>
    <div className="p-4 border-t">
      <Skeleton className="h-10 w-full rounded-lg" />
    </div>
  </div>
)

// Generic loading component
export const LoadingFallback = ({ 
  message = 'Loading...', 
  fullHeight = false 
}: { 
  message?: string
  fullHeight?: boolean 
}) => (
  <div className={`flex items-center justify-center p-8 ${fullHeight ? 'h-full' : ''}`}>
    <div className="text-center">
      <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
      <p className="text-sm text-gray-500">{message}</p>
    </div>
  </div>
)

// Error boundary fallback
export const ErrorFallback = ({ 
  error, 
  retry 
}: { 
  error: Error
  retry?: () => void 
}) => (
  <Card className="p-6 text-center">
    <div className="text-red-600 mb-4">
      <svg className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </div>
    <h3 className="text-lg font-semibold mb-2">Something went wrong</h3>
    <p className="text-sm text-gray-600 mb-4">{error.message}</p>
    {retry && (
      <button
        onClick={retry}
        className="text-blue-600 hover:text-blue-700 text-sm font-medium"
      >
        Try again
      </button>
    )}
  </Card>
)

// Dynamic import wrapper with custom loading states
export function createDynamicComponent<P = {}>(
  importFn: () => Promise<{ default: ComponentType<P> }>,
  options?: {
    loading?: ComponentType
    ssr?: boolean
  }
) {
  return dynamic(importFn, {
    loading: options?.loading || (() => <LoadingFallback />),
    ssr: options?.ssr ?? true
  })
}

// Pre-configured dynamic imports for heavy components
export const DynamicIncidentTable = dynamic(
  () => import('@/components/tables/incidents-table').then(mod => mod.IncidentsTable),
  { 
    loading: () => <TableSkeleton />,
    ssr: false 
  }
)

export const DynamicAgentsTable = dynamic(
  () => import('@/components/tables/agents-table').then(mod => mod.AgentsTable),
  { 
    loading: () => <TableSkeleton />,
    ssr: false 
  }
)

export const DynamicIncidentChart = dynamic(
  () => import('@/components/charts/incident-trends').then(mod => mod.IncidentTrends),
  { 
    loading: () => <ChartSkeleton />,
    ssr: false 
  }
)

export const DynamicChatInterface = dynamic(
  () => import('@/components/chat/chat-interface').then(mod => mod.ChatInterface),
  { 
    loading: () => <ChatSkeleton />,
    ssr: false 
  }
)

export const DynamicActivityViewer = dynamic(
  () => import('@/components/activity/activity-viewer').then(mod => mod.ActivityViewer),
  { 
    loading: () => <LoadingFallback message="Loading activity viewer..." />,
    ssr: false 
  }
)

export const DynamicOnboardingFlow = dynamic(
  () => import('@/components/onboarding/onboarding-flow').then(mod => mod.OnboardingFlow),
  { 
    loading: () => null, // Don't show loading for onboarding
    ssr: false 
  }
)

export const DynamicHelpSidebar = dynamic(
  () => import('@/components/help/help-sidebar').then(mod => mod.HelpSidebar),
  { 
    loading: () => null, // Don't show loading for help
    ssr: false 
  }
)

// Route-based code splitting helpers
export const DynamicDashboardPage = dynamic(
  () => import('@/app/dashboard/page'),
  { 
    loading: () => <LoadingFallback fullHeight message="Loading dashboard..." /> 
  }
)

export const DynamicIncidentsPage = dynamic(
  () => import('@/app/incidents/page'),
  { 
    loading: () => <LoadingFallback fullHeight message="Loading incidents..." /> 
  }
)

export const DynamicAgentsPage = dynamic(
  () => import('@/app/agents/page'),
  { 
    loading: () => <LoadingFallback fullHeight message="Loading agents..." /> 
  }
)

export const DynamicAnalyticsPage = dynamic(
  () => import('@/app/analytics/page'),
  { 
    loading: () => <LoadingFallback fullHeight message="Loading analytics..." /> 
  }
)

// Utility to preload components
export const preloadComponent = (
  componentName: keyof typeof componentMap
) => {
  const component = componentMap[componentName]
  if (component && typeof component.preload === 'function') {
    component.preload()
  }
}

// Map of all dynamic components for easy preloading
const componentMap = {
  IncidentTable: DynamicIncidentTable,
  AgentsTable: DynamicAgentsTable,
  IncidentChart: DynamicIncidentChart,
  ChatInterface: DynamicChatInterface,
  ActivityViewer: DynamicActivityViewer,
  OnboardingFlow: DynamicOnboardingFlow,
  HelpSidebar: DynamicHelpSidebar,
  DashboardPage: DynamicDashboardPage,
  IncidentsPage: DynamicIncidentsPage,
  AgentsPage: DynamicAgentsPage,
  AnalyticsPage: DynamicAnalyticsPage
}

// Intersection Observer hook for lazy loading
import { useEffect, useRef, useState } from 'react'

export function useLazyLoad<T extends HTMLElement = HTMLDivElement>(
  options?: IntersectionObserverInit
) {
  const ref = useRef<T>(null)
  const [isIntersecting, setIsIntersecting] = useState(false)
  const [hasLoaded, setHasLoaded] = useState(false)

  useEffect(() => {
    const element = ref.current
    if (!element) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsIntersecting(true)
          setHasLoaded(true)
          observer.unobserve(element)
        }
      },
      {
        threshold: 0.1,
        rootMargin: '50px',
        ...options
      }
    )

    observer.observe(element)

    return () => {
      observer.disconnect()
    }
  }, [options])

  return { ref, isIntersecting, hasLoaded }
}

// Lazy load wrapper component
export function LazyLoad({ 
  children,
  fallback = <LoadingFallback />,
  height = 300,
  offset = 50
}: {
  children: ReactNode
  fallback?: ReactNode
  height?: number | string
  offset?: number
}) {
  const { ref, hasLoaded } = useLazyLoad({
    rootMargin: `${offset}px`
  })

  return (
    <div ref={ref} style={{ minHeight: hasLoaded ? 'auto' : height }}>
      {hasLoaded ? children : fallback}
    </div>
  )
}