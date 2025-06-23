"use client"

import { useState } from 'react'
import { useUIStore } from '@/store'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Palette, Monitor, Moon, Sun, Sparkles } from 'lucide-react'

export default function AppearanceSettings() {
  const { theme, setTheme } = useUIStore()
  const [fontSize, setFontSize] = useState(16)
  const [colorScheme, setColorScheme] = useState('default')
  const [uiDensity, setUiDensity] = useState('comfortable')
  const [enableAnimations, setEnableAnimations] = useState(true)
  const [reduceMotion, setReduceMotion] = useState(false)
  const [highContrast, setHighContrast] = useState(false)

  const colorSchemes = [
    { value: 'default', label: 'Default', color: '#0ea5e9' },
    { value: 'purple', label: 'Purple', color: '#8b5cf6' },
    { value: 'green', label: 'Green', color: '#10b981' },
    { value: 'orange', label: 'Orange', color: '#f97316' },
    { value: 'pink', label: 'Pink', color: '#ec4899' },
    { value: 'custom', label: 'Custom', color: '#6b7280' },
  ]

  const handleColorSchemeChange = (scheme: string) => {
    setColorScheme(scheme)
    // Apply color scheme to root CSS variables
    if (scheme !== 'custom') {
      const schemeColor = colorSchemes.find(s => s.value === scheme)?.color
      if (schemeColor) {
        document.documentElement.style.setProperty('--primary', schemeColor)
      }
    }
  }

  return (
    <div className="space-y-6">
      {/* Theme Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="w-5 h-5" />
            Theme
          </CardTitle>
          <CardDescription>
            Choose your preferred color theme for the interface
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-3">
            <Label>Theme Mode</Label>
            <RadioGroup value={theme} onValueChange={(value) => setTheme(value as any)}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="light" id="light" />
                <Label htmlFor="light" className="flex items-center gap-2 cursor-pointer">
                  <Sun className="w-4 h-4" />
                  Light
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="dark" id="dark" />
                <Label htmlFor="dark" className="flex items-center gap-2 cursor-pointer">
                  <Moon className="w-4 h-4" />
                  Dark
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="system" id="system" />
                <Label htmlFor="system" className="flex items-center gap-2 cursor-pointer">
                  <Monitor className="w-4 h-4" />
                  System
                </Label>
              </div>
            </RadioGroup>
          </div>

          {/* Color Scheme */}
          <div className="space-y-3">
            <Label>Color Scheme</Label>
            <div className="grid grid-cols-3 gap-3">
              {colorSchemes.map(scheme => (
                <button
                  key={scheme.value}
                  onClick={() => handleColorSchemeChange(scheme.value)}
                  className={`relative p-4 rounded-lg border-2 transition-all ${
                    colorScheme === scheme.value
                      ? 'border-primary shadow-lg'
                      : 'border-border hover:border-primary/50'
                  }`}
                  aria-label={`Select ${scheme.label} color scheme`}
                >
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-6 h-6 rounded-full" 
                      style={{ backgroundColor: scheme.color }}
                    />
                    <span className="text-sm font-medium">{scheme.label}</span>
                  </div>
                  {colorScheme === scheme.value && (
                    <div className="absolute top-1 right-1">
                      <div className="w-2 h-2 bg-primary rounded-full" />
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Typography & Layout */}
      <Card>
        <CardHeader>
          <CardTitle>Typography & Layout</CardTitle>
          <CardDescription>
            Adjust text size and interface density
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Font Size */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Font Size</Label>
              <span className="text-sm text-muted-foreground">{fontSize}px</span>
            </div>
            <Slider
              value={[fontSize]}
              onValueChange={([value]) => setFontSize(value)}
              min={12}
              max={20}
              step={1}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Small</span>
              <span>Default</span>
              <span>Large</span>
            </div>
          </div>

          {/* UI Density */}
          <div className="space-y-3">
            <Label>UI Density</Label>
            <RadioGroup value={uiDensity} onValueChange={setUiDensity}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="compact" id="compact" />
                <Label htmlFor="compact" className="cursor-pointer">
                  Compact - More content, less spacing
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="comfortable" id="comfortable" />
                <Label htmlFor="comfortable" className="cursor-pointer">
                  Comfortable - Balanced spacing
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="spacious" id="spacious" />
                <Label htmlFor="spacious" className="cursor-pointer">
                  Spacious - More breathing room
                </Label>
              </div>
            </RadioGroup>
          </div>
        </CardContent>
      </Card>

      {/* Animations & Effects */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5" />
            Animations & Effects
          </CardTitle>
          <CardDescription>
            Control motion and visual effects
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="animations">Enable Animations</Label>
              <p className="text-sm text-muted-foreground">
                Smooth transitions and hover effects
              </p>
            </div>
            <Switch
              id="animations"
              checked={enableAnimations}
              onCheckedChange={setEnableAnimations}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="reduce-motion">Reduce Motion</Label>
              <p className="text-sm text-muted-foreground">
                Minimize animations for accessibility
              </p>
            </div>
            <Switch
              id="reduce-motion"
              checked={reduceMotion}
              onCheckedChange={setReduceMotion}
              disabled={!enableAnimations}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="high-contrast">High Contrast</Label>
              <p className="text-sm text-muted-foreground">
                Increase contrast for better visibility
              </p>
            </div>
            <Switch
              id="high-contrast"
              checked={highContrast}
              onCheckedChange={setHighContrast}
            />
          </div>
        </CardContent>
      </Card>

      {/* Preview Section */}
      <Card>
        <CardHeader>
          <CardTitle>Preview</CardTitle>
          <CardDescription>
            See how your appearance settings look
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div 
            className={`p-6 rounded-lg border ${
              theme === 'dark' ? 'bg-gray-900' : 'bg-white'
            }`}
            style={{ fontSize: `${fontSize}px` }}
          >
            <h3 className="font-semibold mb-2">Sample Content</h3>
            <p className="text-muted-foreground mb-4">
              This is how your content will appear with the current settings.
            </p>
            <div className="flex gap-2">
              <Button size={uiDensity === 'compact' ? 'sm' : uiDensity === 'spacious' ? 'lg' : 'default'}>
                Primary Action
              </Button>
              <Button 
                variant="outline"
                size={uiDensity === 'compact' ? 'sm' : uiDensity === 'spacious' ? 'lg' : 'default'}
              >
                Secondary
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}