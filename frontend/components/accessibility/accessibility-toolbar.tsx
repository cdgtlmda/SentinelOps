'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import {
  Settings2,
  ZoomIn,
  ZoomOut,
  Eye,
  Move,
  Volume2,
  Focus,
  RotateCcw,
  Keyboard,
} from 'lucide-react'

interface AccessibilitySettings {
  fontSize: number
  highContrast: boolean
  reducedMotion: boolean
  focusIndicator: 'default' | 'enhanced' | 'custom'
  screenReaderAnnouncements: boolean
  keyboardShortcuts: boolean
}

const DEFAULT_SETTINGS: AccessibilitySettings = {
  fontSize: 100,
  highContrast: false,
  reducedMotion: false,
  focusIndicator: 'default',
  screenReaderAnnouncements: true,
  keyboardShortcuts: true,
}

export function AccessibilityToolbar() {
  const [settings, setSettings] = useState<AccessibilitySettings>(DEFAULT_SETTINGS)
  const [isOpen, setIsOpen] = useState(false)

  // Load settings from localStorage
  useEffect(() => {
    const savedSettings = localStorage.getItem('accessibilitySettings')
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings))
    }
  }, [])

  // Apply settings
  useEffect(() => {
    const root = document.documentElement
    
    // Font size
    root.style.setProperty('--base-font-size', `${settings.fontSize}%`)
    root.style.fontSize = `${settings.fontSize}%`
    
    // High contrast
    if (settings.highContrast) {
      root.classList.add('high-contrast')
    } else {
      root.classList.remove('high-contrast')
    }
    
    // Reduced motion
    if (settings.reducedMotion) {
      root.classList.add('reduce-motion')
    } else {
      root.classList.remove('reduce-motion')
    }
    
    // Focus indicator
    root.setAttribute('data-focus-indicator', settings.focusIndicator)
    
    // Screen reader announcements
    root.setAttribute('data-sr-announcements', settings.screenReaderAnnouncements.toString())
    
    // Keyboard shortcuts
    root.setAttribute('data-keyboard-shortcuts', settings.keyboardShortcuts.toString())
    
    // Save to localStorage
    localStorage.setItem('accessibilitySettings', JSON.stringify(settings))
  }, [settings])

  const updateSetting = <K extends keyof AccessibilitySettings>(
    key: K,
    value: AccessibilitySettings[K]
  ) => {
    setSettings((prev) => ({ ...prev, [key]: value }))
  }

  const resetSettings = () => {
    setSettings(DEFAULT_SETTINGS)
  }

  const adjustFontSize = (delta: number) => {
    const newSize = Math.max(50, Math.min(200, settings.fontSize + delta))
    updateSetting('fontSize', newSize)
  }

  return (
    <>
      {/* Add CSS for accessibility features */}
      <style jsx global>{`
        :root {
          --base-font-size: 100%;
        }
        
        /* High contrast mode */
        .high-contrast {
          filter: contrast(1.5);
        }
        
        .high-contrast * {
          border-color: currentColor !important;
        }
        
        .high-contrast button,
        .high-contrast a,
        .high-contrast input,
        .high-contrast textarea,
        .high-contrast select {
          outline: 2px solid currentColor !important;
          outline-offset: 2px !important;
        }
        
        /* Reduced motion */
        .reduce-motion * {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0.01ms !important;
        }
        
        /* Enhanced focus indicators */
        [data-focus-indicator="enhanced"] *:focus {
          outline: 3px solid #2563eb !important;
          outline-offset: 3px !important;
        }
        
        [data-focus-indicator="custom"] *:focus {
          outline: 4px dashed #dc2626 !important;
          outline-offset: 4px !important;
          border-radius: 4px;
        }
      `}</style>

      <Popover open={isOpen} onOpenChange={setIsOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            size="icon"
            className="fixed bottom-4 right-4 z-50 shadow-lg"
            aria-label="Open accessibility settings"
          >
            <Settings2 className="h-5 w-5" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-96 p-6" align="end">
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Accessibility Settings</h2>
              <Button
                variant="ghost"
                size="icon"
                onClick={resetSettings}
                aria-label="Reset all settings to default"
              >
                <RotateCcw className="h-4 w-4" />
              </Button>
            </div>

            {/* Font Size */}
            <div className="space-y-3">
              <Label className="flex items-center gap-2">
                <ZoomIn className="h-4 w-4" />
                Font Size: {settings.fontSize}%
              </Label>
              <div className="flex items-center gap-2">
                <Button
                  size="icon"
                  variant="outline"
                  onClick={() => adjustFontSize(-10)}
                  aria-label="Decrease font size"
                  disabled={settings.fontSize <= 50}
                >
                  <ZoomOut className="h-4 w-4" />
                </Button>
                <input
                  type="range"
                  min="50"
                  max="200"
                  step="10"
                  value={settings.fontSize}
                  onChange={(e) => updateSetting('fontSize', parseInt(e.target.value))}
                  className="flex-1"
                  aria-label="Font size slider"
                />
                <Button
                  size="icon"
                  variant="outline"
                  onClick={() => adjustFontSize(10)}
                  aria-label="Increase font size"
                  disabled={settings.fontSize >= 200}
                >
                  <ZoomIn className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* High Contrast */}
            <div className="flex items-center justify-between">
              <Label htmlFor="high-contrast" className="flex items-center gap-2 cursor-pointer">
                <Eye className="h-4 w-4" />
                High Contrast Mode
              </Label>
              <Switch
                id="high-contrast"
                checked={settings.highContrast}
                onCheckedChange={(checked) => updateSetting('highContrast', checked)}
                aria-describedby="high-contrast-desc"
              />
            </div>
            <p id="high-contrast-desc" className="text-xs text-muted-foreground -mt-2">
              Increases contrast for better visibility
            </p>

            {/* Reduced Motion */}
            <div className="flex items-center justify-between">
              <Label htmlFor="reduced-motion" className="flex items-center gap-2 cursor-pointer">
                <Move className="h-4 w-4" />
                Reduce Motion
              </Label>
              <Switch
                id="reduced-motion"
                checked={settings.reducedMotion}
                onCheckedChange={(checked) => updateSetting('reducedMotion', checked)}
                aria-describedby="reduced-motion-desc"
              />
            </div>
            <p id="reduced-motion-desc" className="text-xs text-muted-foreground -mt-2">
              Minimizes animations and transitions
            </p>

            {/* Focus Indicator */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Focus className="h-4 w-4" />
                Focus Indicator Style
              </Label>
              <select
                value={settings.focusIndicator}
                onChange={(e) => updateSetting('focusIndicator', e.target.value as any)}
                className="w-full p-2 border rounded-md"
                aria-label="Select focus indicator style"
              >
                <option value="default">Default</option>
                <option value="enhanced">Enhanced (Blue)</option>
                <option value="custom">Custom (Red Dashed)</option>
              </select>
            </div>

            {/* Screen Reader Announcements */}
            <div className="flex items-center justify-between">
              <Label htmlFor="sr-announcements" className="flex items-center gap-2 cursor-pointer">
                <Volume2 className="h-4 w-4" />
                Screen Reader Announcements
              </Label>
              <Switch
                id="sr-announcements"
                checked={settings.screenReaderAnnouncements}
                onCheckedChange={(checked) => updateSetting('screenReaderAnnouncements', checked)}
                aria-describedby="sr-announcements-desc"
              />
            </div>
            <p id="sr-announcements-desc" className="text-xs text-muted-foreground -mt-2">
              Enable live region announcements
            </p>

            {/* Keyboard Shortcuts */}
            <div className="flex items-center justify-between">
              <Label htmlFor="keyboard-shortcuts" className="flex items-center gap-2 cursor-pointer">
                <Keyboard className="h-4 w-4" />
                Keyboard Shortcuts
              </Label>
              <Switch
                id="keyboard-shortcuts"
                checked={settings.keyboardShortcuts}
                onCheckedChange={(checked) => updateSetting('keyboardShortcuts', checked)}
                aria-describedby="keyboard-shortcuts-desc"
              />
            </div>
            <p id="keyboard-shortcuts-desc" className="text-xs text-muted-foreground -mt-2">
              Enable keyboard navigation shortcuts
            </p>
          </div>
        </PopoverContent>
      </Popover>
    </>
  )
}