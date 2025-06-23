'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Check, X, AlertCircle } from 'lucide-react'

interface ContrastResult {
  ratio: number
  normalAAA: boolean
  normalAA: boolean
  largeAAA: boolean
  largeAA: boolean
}

function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null
}

function getLuminance(r: number, g: number, b: number): number {
  const [rs, gs, bs] = [r, g, b].map((c) => {
    c = c / 255
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
  })
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs
}

function getContrastRatio(color1: string, color2: string): number {
  const rgb1 = hexToRgb(color1)
  const rgb2 = hexToRgb(color2)
  
  if (!rgb1 || !rgb2) return 1
  
  const lum1 = getLuminance(rgb1.r, rgb1.g, rgb1.b)
  const lum2 = getLuminance(rgb2.r, rgb2.g, rgb2.b)
  
  const brightest = Math.max(lum1, lum2)
  const darkest = Math.min(lum1, lum2)
  
  return (brightest + 0.05) / (darkest + 0.05)
}

function checkContrast(ratio: number): ContrastResult {
  return {
    ratio,
    normalAAA: ratio >= 7,
    normalAA: ratio >= 4.5,
    largeAAA: ratio >= 4.5,
    largeAA: ratio >= 3,
  }
}

function suggestAlternative(color: string, targetRatio: number, background: string): string {
  const rgb = hexToRgb(color)
  if (!rgb) return color
  
  let { r, g, b } = rgb
  const bgRgb = hexToRgb(background)
  if (!bgRgb) return color
  
  const bgLum = getLuminance(bgRgb.r, bgRgb.g, bgRgb.b)
  
  // Try darkening or lightening the color
  let bestColor = color
  let bestRatio = getContrastRatio(color, background)
  
  for (let factor = 0.1; factor <= 1; factor += 0.1) {
    // Try darker
    const darker = `#${Math.floor(r * (1 - factor))
      .toString(16)
      .padStart(2, '0')}${Math.floor(g * (1 - factor))
      .toString(16)
      .padStart(2, '0')}${Math.floor(b * (1 - factor))
      .toString(16)
      .padStart(2, '0')}`
    
    const darkerRatio = getContrastRatio(darker, background)
    if (darkerRatio >= targetRatio && darkerRatio < bestRatio * 1.5) {
      bestColor = darker
      bestRatio = darkerRatio
      break
    }
    
    // Try lighter
    const lighter = `#${Math.floor(255 - (255 - r) * (1 - factor))
      .toString(16)
      .padStart(2, '0')}${Math.floor(255 - (255 - g) * (1 - factor))
      .toString(16)
      .padStart(2, '0')}${Math.floor(255 - (255 - b) * (1 - factor))
      .toString(16)
      .padStart(2, '0')}`
    
    const lighterRatio = getContrastRatio(lighter, background)
    if (lighterRatio >= targetRatio && lighterRatio < bestRatio * 1.5) {
      bestColor = lighter
      bestRatio = lighterRatio
      break
    }
  }
  
  return bestColor
}

export function ColorContrastChecker() {
  const [foreground, setForeground] = useState('#000000')
  const [background, setBackground] = useState('#ffffff')
  const [contrast, setContrast] = useState<ContrastResult | null>(null)
  const [suggestedForeground, setSuggestedForeground] = useState<string | null>(null)

  useEffect(() => {
    const ratio = getContrastRatio(foreground, background)
    setContrast(checkContrast(ratio))
    
    if (ratio < 4.5) {
      setSuggestedForeground(suggestAlternative(foreground, 4.5, background))
    } else {
      setSuggestedForeground(null)
    }
  }, [foreground, background])

  const ComplianceBadge = ({ passes, label }: { passes: boolean; label: string }) => (
    <Badge 
      variant={passes ? 'default' : 'destructive'} 
      className="flex items-center gap-1"
    >
      {passes ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
      {label}
    </Badge>
  )

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>Color Contrast Checker</CardTitle>
        <CardDescription>
          Verify WCAG color contrast compliance for text and background combinations
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="foreground">Text Color</Label>
            <div className="flex gap-2">
              <Input
                id="foreground"
                type="color"
                value={foreground}
                onChange={(e) => setForeground(e.target.value)}
                className="w-16 h-10 p-1 cursor-pointer"
                aria-label="Select text color"
              />
              <Input
                type="text"
                value={foreground}
                onChange={(e) => setForeground(e.target.value)}
                placeholder="#000000"
                pattern="^#[0-9A-Fa-f]{6}$"
                aria-label="Enter text color hex value"
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="background">Background Color</Label>
            <div className="flex gap-2">
              <Input
                id="background"
                type="color"
                value={background}
                onChange={(e) => setBackground(e.target.value)}
                className="w-16 h-10 p-1 cursor-pointer"
                aria-label="Select background color"
              />
              <Input
                type="text"
                value={background}
                onChange={(e) => setBackground(e.target.value)}
                placeholder="#ffffff"
                pattern="^#[0-9A-Fa-f]{6}$"
                aria-label="Enter background color hex value"
              />
            </div>
          </div>
        </div>

        {/* Live Preview */}
        <div
          className="p-8 rounded-lg border-2 border-dashed"
          style={{ backgroundColor: background }}
          role="region"
          aria-label="Color combination preview"
        >
          <p
            className="text-lg font-medium mb-2"
            style={{ color: foreground }}
          >
            The quick brown fox jumps over the lazy dog
          </p>
          <p
            className="text-sm"
            style={{ color: foreground }}
          >
            Regular text (14px) - Lorem ipsum dolor sit amet, consectetur adipiscing elit.
          </p>
        </div>

        {contrast && (
          <>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="font-medium">Contrast Ratio</span>
                <span className="text-2xl font-bold">{contrast.ratio.toFixed(2)}:1</span>
              </div>

              <div className="grid gap-3">
                <div>
                  <p className="text-sm font-medium mb-2">Normal Text (≤18pt)</p>
                  <div className="flex gap-2">
                    <ComplianceBadge passes={contrast.normalAA} label="AA (4.5:1)" />
                    <ComplianceBadge passes={contrast.normalAAA} label="AAA (7:1)" />
                  </div>
                </div>
                
                <div>
                  <p className="text-sm font-medium mb-2">Large Text (&gt;18pt or &gt;14pt bold)</p>
                  <div className="flex gap-2">
                    <ComplianceBadge passes={contrast.largeAA} label="AA (3:1)" />
                    <ComplianceBadge passes={contrast.largeAAA} label="AAA (4.5:1)" />
                  </div>
                </div>
              </div>
            </div>

            {suggestedForeground && (
              <div className="p-4 bg-amber-50 dark:bg-amber-950 rounded-lg space-y-3">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-medium text-amber-900 dark:text-amber-100">
                      Suggested Improvement
                    </p>
                    <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
                      The current combination doesn't meet WCAG AA standards. 
                      Try this alternative:
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <div
                    className="w-12 h-12 rounded border"
                    style={{ backgroundColor: suggestedForeground }}
                    aria-label={`Suggested color: ${suggestedForeground}`}
                  />
                  <span className="font-mono text-sm">{suggestedForeground}</span>
                  <Button
                    size="sm"
                    onClick={() => setForeground(suggestedForeground)}
                    aria-label="Apply suggested color"
                  >
                    Apply
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}