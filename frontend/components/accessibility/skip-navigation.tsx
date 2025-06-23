'use client'

import React from 'react'
import { useAccessibility } from '@/hooks/use-accessibility'

interface SkipLink {
  id: string
  text: string
}

const DEFAULT_SKIP_LINKS: SkipLink[] = [
  { id: 'main-content', text: 'Skip to main content' },
  { id: 'navigation', text: 'Skip to navigation' },
  { id: 'search', text: 'Skip to search' },
]

interface SkipNavigationProps {
  links?: SkipLink[]
  className?: string
}

export function SkipNavigation({ 
  links = DEFAULT_SKIP_LINKS,
  className = ''
}: SkipNavigationProps) {
  const { createSkipLink } = useAccessibility()

  return (
    <nav
      className={`skip-navigation ${className}`}
      aria-label="Skip navigation"
    >
      {links.map((link) => (
        <a
          key={link.id}
          {...createSkipLink(link.id, link.text)}
        />
      ))}
      
      {/* Landmark navigation for screen readers */}
      <div className="sr-only" role="navigation" aria-label="Landmark navigation">
        <h2>Page Landmarks</h2>
        <ul>
          <li><a href="#header">Header</a></li>
          <li><a href="#navigation">Navigation</a></li>
          <li><a href="#main-content">Main Content</a></li>
          <li><a href="#sidebar">Sidebar</a></li>
          <li><a href="#footer">Footer</a></li>
        </ul>
      </div>

      <style jsx>{`
        .skip-navigation a {
          position: absolute;
          left: -10000px;
          top: auto;
          width: 1px;
          height: 1px;
          overflow: hidden;
          background-color: hsl(var(--primary));
          color: hsl(var(--primary-foreground));
          padding: 0.75rem 1.5rem;
          text-decoration: none;
          border-radius: 0.375rem;
          z-index: 999;
        }

        .skip-navigation a:focus {
          position: fixed;
          left: 1rem;
          top: 1rem;
          width: auto;
          height: auto;
          overflow: visible;
          outline: 3px solid hsl(var(--ring));
          outline-offset: 2px;
        }

        /* High contrast mode support */
        @media (prefers-contrast: high) {
          .skip-navigation a:focus {
            outline-width: 4px;
            outline-style: solid;
          }
        }

        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
          .skip-navigation a {
            transition: none;
          }
        }
      `}</style>
    </nav>
  )
}

// Additional component for landmark-based navigation
export function LandmarkNavigation() {
  const landmarks = [
    { role: 'banner', label: 'Site header' },
    { role: 'navigation', label: 'Main navigation' },
    { role: 'main', label: 'Main content' },
    { role: 'complementary', label: 'Sidebar' },
    { role: 'contentinfo', label: 'Site footer' },
  ]

  const navigateToLandmark = (role: string) => {
    const landmark = document.querySelector(`[role="${role}"]`)
    if (landmark instanceof HTMLElement) {
      landmark.focus()
      landmark.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  return (
    <div
      className="sr-only focus-within:not-sr-only focus-within:fixed focus-within:top-20 focus-within:right-4 focus-within:z-50 focus-within:bg-background focus-within:border focus-within:rounded-lg focus-within:shadow-lg focus-within:p-4"
      role="navigation"
      aria-label="Landmark navigation"
    >
      <h2 className="text-sm font-semibold mb-2">Jump to section</h2>
      <ul className="space-y-1">
        {landmarks.map((landmark) => (
          <li key={landmark.role}>
            <button
              onClick={() => navigateToLandmark(landmark.role)}
              className="text-sm text-muted-foreground hover:text-foreground focus:text-foreground focus:underline"
            >
              {landmark.label}
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}