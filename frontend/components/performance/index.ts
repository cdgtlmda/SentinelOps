// Dynamic imports and code splitting
export {
  LoadingFallback,
  ErrorFallback,
  TableSkeleton,
  ChartSkeleton,
  CardGridSkeleton,
  ChatSkeleton,
  createDynamicComponent,
  DynamicIncidentTable,
  DynamicAgentsTable,
  DynamicIncidentChart,
  DynamicChatInterface,
  DynamicActivityViewer,
  DynamicOnboardingFlow,
  DynamicHelpSidebar,
  DynamicDashboardPage,
  DynamicIncidentsPage,
  DynamicAgentsPage,
  DynamicAnalyticsPage,
  preloadComponent,
  useLazyLoad,
  LazyLoad
} from './dynamic-imports'

// Image optimization
export {
  OptimizedImage,
  OptimizedAvatar,
  ProgressiveImage,
  OptimizedBackgroundImage,
  preloadImage,
  preloadImages,
  getOptimalFormat,
  generateSrcSet,
  generateBlurDataURL
} from './optimized-image'

// Cache management
export {
  CacheManager,
  apiCache,
  imageCache,
  queryCache,
  memoize,
  QueryCache,
  globalQueryCache,
  cacheStrategies,
  PrefetchManager,
  prefetchManager
} from '@/lib/performance/cache-manager'

// Bundle optimization
export {
  loadChartLibrary,
  loadTableLibrary,
  loadAnimationLibrary,
  loadDateLibrary,
  loadIcon,
  loadPolyfills,
  routeComponents,
  loadFeature,
  chunkNames,
  federatedModules,
  isProduction,
  isDevelopment,
  isTest,
  debug,
  warn,
  withFeature,
  addResourceHints,
  moduleReplacements,
  BUILD_TIME,
  VERSION,
  COMMIT_SHA
} from '@/lib/performance/bundle-optimization'

// Timing utilities
export {
  debounce,
  throttle,
  rafThrottle,
  requestIdleCallback,
  cancelIdleCallback,
  mark,
  measure,
  defer
} from '@/lib/performance/utils/timing'

// Classname utilities
export {
  cn,
  twMerge,
  clsx,
  cva
} from '@/lib/performance/utils/classnames'

// Date utilities
export {
  formatDate,
  formatTime,
  formatDateTime,
  formatRelativeTime,
  formatDuration,
  isToday,
  isYesterday,
  isSameDay,
  addDays,
  startOfDay,
  endOfDay,
  getDaysBetween
} from '@/lib/performance/utils/date'

// Types
export type {
  OptimizedComponent,
  LazyComponentProps,
  PerformanceMetrics,
  BundleStats,
  ChunkInfo,
  CacheStats,
  ResourceTiming
} from '@/lib/performance/types'