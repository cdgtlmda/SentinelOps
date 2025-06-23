'use client'

import { useState, useEffect } from 'react'
import Image from 'next/image'
import { cn } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'

interface OptimizedImageProps {
  src: string
  alt: string
  width?: number
  height?: number
  className?: string
  priority?: boolean
  quality?: number
  placeholder?: 'blur' | 'empty'
  blurDataURL?: string
  sizes?: string
  objectFit?: 'contain' | 'cover' | 'fill' | 'none' | 'scale-down'
  onLoad?: () => void
  onError?: () => void
  fallback?: string
}

export function OptimizedImage({
  src,
  alt,
  width,
  height,
  className,
  priority = false,
  quality = 75,
  placeholder = 'empty',
  blurDataURL,
  sizes,
  objectFit = 'cover',
  onLoad,
  onError,
  fallback = '/images/placeholder.png'
}: OptimizedImageProps) {
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)
  const [imageSrc, setImageSrc] = useState(src)

  useEffect(() => {
    setImageSrc(src)
    setHasError(false)
  }, [src])

  const handleLoad = () => {
    setIsLoading(false)
    onLoad?.()
  }

  const handleError = () => {
    setHasError(true)
    setIsLoading(false)
    setImageSrc(fallback)
    onError?.()
  }

  // Generate responsive sizes if not provided
  const responsiveSizes = sizes || generateSizes()

  return (
    <div className={cn('relative overflow-hidden', className)}>
      {isLoading && (
        <Skeleton className="absolute inset-0 z-10" />
      )}
      
      <Image
        src={imageSrc}
        alt={alt}
        width={width || 500}
        height={height || 300}
        quality={quality}
        priority={priority}
        placeholder={placeholder}
        blurDataURL={blurDataURL}
        sizes={responsiveSizes}
        onLoad={handleLoad}
        onError={handleError}
        className={cn(
          'duration-300 ease-in-out',
          isLoading ? 'scale-105 blur-sm' : 'scale-100 blur-0',
          className
        )}
        style={{
          objectFit: objectFit
        }}
      />
    </div>
  )
}

// Avatar image with fallback
export function OptimizedAvatar({
  src,
  alt,
  size = 40,
  fallbackText,
  className
}: {
  src?: string
  alt: string
  size?: number
  fallbackText?: string
  className?: string
}) {
  const [hasError, setHasError] = useState(false)

  const initials = fallbackText
    ? fallbackText
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : alt[0]?.toUpperCase() || '?'

  if (!src || hasError) {
    return (
      <div
        className={cn(
          'flex items-center justify-center bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 font-medium rounded-full',
          className
        )}
        style={{ width: size, height: size }}
      >
        {initials}
      </div>
    )
  }

  return (
    <div
      className={cn('relative rounded-full overflow-hidden', className)}
      style={{ width: size, height: size }}
    >
      <Image
        src={src}
        alt={alt}
        width={size}
        height={size}
        quality={90}
        onError={() => setHasError(true)}
        className="object-cover"
      />
    </div>
  )
}

// Progressive image loading
export function ProgressiveImage({
  src,
  alt,
  thumbnailSrc,
  className,
  ...props
}: OptimizedImageProps & { thumbnailSrc?: string }) {
  const [currentSrc, setCurrentSrc] = useState(thumbnailSrc || src)
  const [isLoaded, setIsLoaded] = useState(false)

  useEffect(() => {
    if (!thumbnailSrc) return

    // Load full image
    const img = new window.Image()
    img.src = src
    img.onload = () => {
      setCurrentSrc(src)
      setIsLoaded(true)
    }
  }, [src, thumbnailSrc])

  return (
    <OptimizedImage
      {...props}
      src={currentSrc}
      alt={alt}
      className={cn(
        className,
        !isLoaded && thumbnailSrc && 'filter blur-sm'
      )}
    />
  )
}

// Background image with optimization
export function OptimizedBackgroundImage({
  src,
  alt,
  className,
  children,
  overlay = true,
  overlayOpacity = 0.5
}: {
  src: string
  alt: string
  className?: string
  children?: React.ReactNode
  overlay?: boolean
  overlayOpacity?: number
}) {
  return (
    <div className={cn('relative', className)}>
      <Image
        src={src}
        alt={alt}
        fill
        quality={75}
        sizes="100vw"
        className="object-cover"
        priority
      />
      {overlay && (
        <div 
          className="absolute inset-0 bg-black" 
          style={{ opacity: overlayOpacity }} 
        />
      )}
      {children && (
        <div className="relative z-10">
          {children}
        </div>
      )}
    </div>
  )
}

// Utility functions
function generateSizes(): string {
  return [
    '(max-width: 640px) 100vw',
    '(max-width: 768px) 50vw',
    '(max-width: 1024px) 33vw',
    '25vw'
  ].join(', ')
}

// Image preloader
export function preloadImage(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const img = new window.Image()
    img.src = src
    img.onload = () => resolve()
    img.onerror = reject
  })
}

// Batch image preloader
export async function preloadImages(srcs: string[]): Promise<void> {
  await Promise.all(srcs.map(src => preloadImage(src)))
}

// Image format detection
export function getOptimalFormat(userAgent?: string): 'webp' | 'avif' | 'default' {
  if (!userAgent) {
    if (typeof navigator !== 'undefined') {
      userAgent = navigator.userAgent
    } else {
      return 'default'
    }
  }

  // Check for WebP support
  const supportsWebP = userAgent.includes('Chrome') || 
                      userAgent.includes('Opera') || 
                      userAgent.includes('Edge')

  // Check for AVIF support (Chrome 85+, Firefox 93+)
  const supportsAvif = userAgent.includes('Chrome/8') || 
                       userAgent.includes('Chrome/9') ||
                       userAgent.includes('Firefox/9')

  if (supportsAvif) return 'avif'
  if (supportsWebP) return 'webp'
  return 'default'
}

// Responsive image srcset generator
export function generateSrcSet(
  baseSrc: string,
  sizes: number[] = [320, 640, 768, 1024, 1280, 1536]
): string {
  return sizes
    .map(size => `${baseSrc}?w=${size} ${size}w`)
    .join(', ')
}

// Blur data URL generator (for placeholder)
export function generateBlurDataURL(width = 10, height = 10): string {
  const canvas = typeof document !== 'undefined' ? document.createElement('canvas') : null
  if (!canvas) return ''
  
  canvas.width = width
  canvas.height = height
  
  const ctx = canvas.getContext('2d')
  if (!ctx) return ''
  
  // Create a simple gradient
  const gradient = ctx.createLinearGradient(0, 0, width, height)
  gradient.addColorStop(0, '#f3f4f6')
  gradient.addColorStop(1, '#e5e7eb')
  
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, width, height)
  
  return canvas.toDataURL()
}