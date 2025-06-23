'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Switch } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  ColorBlindSimulator,
  IconWithLabel,
  IconGroup,
  CommonIcons,
  StatusIndicator,
  MultiStatusIndicator,
  StatusDot
} from '@/components/accessibility';
import { 
  useVisualAccessibility,
  ColorBlindMode,
  PatternPreference,
  IconLabelPreference
} from '@/hooks/use-visual-accessibility';
import { 
  getColorBlindPalette,
  getContrastSafeCombinations,
  meetsContrastRequirements,
  colorBlindPalettes
} from '@/lib/design/color-blind-palette';
import {
  Activity,
  AlertCircle,
  Bell,
  CheckCircle,
  Clock,
  Download,
  Edit,
  Filter,
  Heart,
  Home,
  Info,
  Mail,
  RefreshCw,
  Save,
  Search,
  Settings,
  Trash2,
  Upload,
  User,
  XCircle
} from 'lucide-react';

export default function VisualAccessibilityPage() {
  const {
    settings,
    updateSetting,
    resetSettings,
    shouldShowPatterns,
    getIconLabelMode
  } = useVisualAccessibility();

  const [showSimulator, setShowSimulator] = useState(true);

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Visual Accessibility Features</h1>
        <p className="text-muted-foreground">
          Comprehensive visual accessibility tools and components to ensure your interface is usable by everyone.
        </p>
      </div>

      {/* Settings Panel */}
      <Card>
        <CardHeader>
          <CardTitle>Visual Accessibility Settings</CardTitle>
          <CardDescription>
            Configure visual accessibility preferences for the entire application
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Color Blind Mode */}
            <div className="space-y-2">
              <Label htmlFor="color-blind-mode">Color Blind Mode</Label>
              <Select
                value={settings.colorBlindMode}
                onValueChange={(value) => updateSetting('colorBlindMode', value as ColorBlindMode)}
              >
                <SelectTrigger id="color-blind-mode">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="normal">Normal Vision</SelectItem>
                  <SelectItem value="protanopia">Protanopia (Red-blind)</SelectItem>
                  <SelectItem value="deuteranopia">Deuteranopia (Green-blind)</SelectItem>
                  <SelectItem value="tritanopia">Tritanopia (Blue-blind)</SelectItem>
                  <SelectItem value="monochromacy">Monochromacy (Complete)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Pattern Preference */}
            <div className="space-y-2">
              <Label htmlFor="pattern-preference">Pattern Overlays</Label>
              <Select
                value={settings.usePatterns}
                onValueChange={(value) => updateSetting('usePatterns', value as PatternPreference)}
              >
                <SelectTrigger id="pattern-preference">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">Auto (Based on mode)</SelectItem>
                  <SelectItem value="always">Always Show</SelectItem>
                  <SelectItem value="never">Never Show</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Icon Labels */}
            <div className="space-y-2">
              <Label htmlFor="icon-labels">Icon Labels</Label>
              <Select
                value={settings.iconLabels}
                onValueChange={(value) => updateSetting('iconLabels', value as IconLabelPreference)}
              >
                <SelectTrigger id="icon-labels">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">Auto (Based on mode)</SelectItem>
                  <SelectItem value="always">Always Show</SelectItem>
                  <SelectItem value="tooltip">Show as Tooltip</SelectItem>
                  <SelectItem value="hidden">Hidden</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Font Size */}
            <div className="space-y-2">
              <Label htmlFor="font-size">Font Size</Label>
              <Select
                value={settings.fontSize}
                onValueChange={(value) => updateSetting('fontSize', value as 'normal' | 'large' | 'extra-large')}
              >
                <SelectTrigger id="font-size">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="normal">Normal (16px)</SelectItem>
                  <SelectItem value="large">Large (18px)</SelectItem>
                  <SelectItem value="extra-large">Extra Large (20px)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* High Contrast */}
            <div className="flex items-center space-x-2">
              <Switch
                id="high-contrast"
                checked={settings.highContrast}
                onCheckedChange={(checked) => updateSetting('highContrast', checked)}
              />
              <Label htmlFor="high-contrast">High Contrast Mode</Label>
            </div>

            {/* Reduce Motion */}
            <div className="flex items-center space-x-2">
              <Switch
                id="reduce-motion"
                checked={settings.reduceMotion}
                onCheckedChange={(checked) => updateSetting('reduceMotion', checked)}
              />
              <Label htmlFor="reduce-motion">Reduce Motion</Label>
            </div>
          </div>

          <div className="flex justify-end">
            <Button variant="outline" onClick={resetSettings}>
              Reset to Defaults
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Tabs for different features */}
      <Tabs defaultValue="simulator" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="simulator">Color Blind Simulator</TabsTrigger>
          <TabsTrigger value="status">Status Indicators</TabsTrigger>
          <TabsTrigger value="icons">Icons & Labels</TabsTrigger>
          <TabsTrigger value="palettes">Color Palettes</TabsTrigger>
        </TabsList>

        {/* Color Blind Simulator Tab */}
        <TabsContent value="simulator" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Color Blind Simulator</CardTitle>
              <CardDescription>
                Preview how UI elements appear to users with different types of color vision
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowSimulator(!showSimulator)}
                >
                  {showSimulator ? 'Hide' : 'Show'} Simulator
                </Button>
              </div>
              
              {showSimulator && (
                <ColorBlindSimulator showSideBySide={true} detectProblems={true}>
                  <div className="space-y-4">
                    {/* Sample UI elements */}
                    <div className="flex gap-2 flex-wrap">
                      <Badge variant="default">Primary</Badge>
                      <Badge variant="secondary">Secondary</Badge>
                      <Badge variant="destructive">Destructive</Badge>
                      <Badge variant="outline">Outline</Badge>
                    </div>

                    <div className="flex gap-2 flex-wrap">
                      <Button variant="default" size="sm">Primary Action</Button>
                      <Button variant="secondary" size="sm">Secondary</Button>
                      <Button variant="destructive" size="sm">Delete</Button>
                      <Button variant="outline" size="sm">Cancel</Button>
                    </div>

                    <div className="space-y-2">
                      <Alert>
                        <Info className="h-4 w-4" />
                        <AlertTitle>Information</AlertTitle>
                        <AlertDescription>
                          This is an informational message.
                        </AlertDescription>
                      </Alert>
                      
                      <Alert className="border-yellow-500/50 text-yellow-600">
                        <AlertCircle className="h-4 w-4" />
                        <AlertTitle>Warning</AlertTitle>
                        <AlertDescription>
                          This is a warning message.
                        </AlertDescription>
                      </Alert>
                      
                      <Alert className="border-red-500/50 text-red-600">
                        <XCircle className="h-4 w-4" />
                        <AlertTitle>Error</AlertTitle>
                        <AlertDescription>
                          This is an error message.
                        </AlertDescription>
                      </Alert>
                    </div>
                  </div>
                </ColorBlindSimulator>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Status Indicators Tab */}
        <TabsContent value="status" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Multi-Modal Status Indicators</CardTitle>
              <CardDescription>
                Status indicators that don't rely solely on color
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Basic Status Indicators */}
              <div>
                <h3 className="text-sm font-medium mb-3">Basic Status Indicators</h3>
                <div className="flex flex-wrap gap-4">
                  <StatusIndicator status="success" />
                  <StatusIndicator status="error" />
                  <StatusIndicator status="warning" />
                  <StatusIndicator status="info" />
                  <StatusIndicator status="pending" />
                  <StatusIndicator status="active" animate />
                  <StatusIndicator status="paused" />
                  <StatusIndicator status="loading" animate />
                </div>
              </div>

              {/* With Patterns */}
              <div>
                <h3 className="text-sm font-medium mb-3">With Pattern Overlays</h3>
                <div className="flex flex-wrap gap-4">
                  <StatusIndicator status="success" showPattern />
                  <StatusIndicator status="error" showPattern />
                  <StatusIndicator status="warning" showPattern />
                  <StatusIndicator status="info" showPattern />
                </div>
              </div>

              {/* Different Sizes */}
              <div>
                <h3 className="text-sm font-medium mb-3">Size Variations</h3>
                <div className="flex items-center gap-4">
                  <StatusIndicator status="success" size="sm" />
                  <StatusIndicator status="success" size="md" />
                  <StatusIndicator status="success" size="lg" />
                </div>
              </div>

              {/* Status Dots */}
              <div>
                <h3 className="text-sm font-medium mb-3">Minimal Status Dots</h3>
                <div className="flex items-center gap-4">
                  <StatusDot status="success" />
                  <StatusDot status="error" />
                  <StatusDot status="warning" />
                  <StatusDot status="active" animate />
                </div>
              </div>

              {/* Multi-Status */}
              <div>
                <h3 className="text-sm font-medium mb-3">Multi-Status Display</h3>
                <MultiStatusIndicator
                  statuses={[
                    { status: 'success', count: 12 },
                    { status: 'warning', count: 3 },
                    { status: 'error', count: 1 },
                    { status: 'pending', count: 5 }
                  ]}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Icons & Labels Tab */}
        <TabsContent value="icons" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Icons with Labels</CardTitle>
              <CardDescription>
                Icons should always be accompanied by text labels for clarity
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Position Variations */}
              <div>
                <h3 className="text-sm font-medium mb-3">Label Positions</h3>
                <div className="flex flex-wrap gap-6">
                  <IconWithLabel icon={Save} label="Save" position="right" />
                  <IconWithLabel icon={Save} label="Save" position="left" />
                  <IconWithLabel icon={Save} label="Save" position="below" />
                  <IconWithLabel icon={Save} label="Save" position="above" />
                  <IconWithLabel icon={Save} label="Save" position="tooltip" />
                </div>
              </div>

              {/* Size Variations */}
              <div>
                <h3 className="text-sm font-medium mb-3">Size Variations</h3>
                <div className="flex items-center gap-6">
                  <IconWithLabel icon={Settings} label="Settings" iconSize="sm" />
                  <IconWithLabel icon={Settings} label="Settings" iconSize="md" />
                  <IconWithLabel icon={Settings} label="Settings" iconSize="lg" />
                  <IconWithLabel icon={Settings} label="Settings" iconSize="xl" />
                </div>
              </div>

              {/* Icon Groups */}
              <div>
                <h3 className="text-sm font-medium mb-3">Icon Groups</h3>
                <IconGroup orientation="horizontal" spacing="normal">
                  <IconWithLabel icon={Home} label="Home" />
                  <IconWithLabel icon={Search} label="Search" />
                  <IconWithLabel icon={Bell} label="Notifications" />
                  <IconWithLabel icon={User} label="Profile" />
                </IconGroup>
              </div>

              {/* Common Actions */}
              <div>
                <h3 className="text-sm font-medium mb-3">Common Action Icons</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  <CommonIcons.Save />
                  <CommonIcons.Delete />
                  <CommonIcons.Edit />
                  <CommonIcons.Settings />
                  <CommonIcons.Search />
                  <CommonIcons.Filter />
                  <CommonIcons.Download />
                  <CommonIcons.Upload />
                  <CommonIcons.Refresh />
                  <CommonIcons.Close />
                </div>
              </div>

              {/* Action Buttons */}
              <div>
                <h3 className="text-sm font-medium mb-3">Icon Buttons with Labels</h3>
                <div className="flex flex-wrap gap-4">
                  <Button size="sm">
                    <IconWithLabel icon={Save} label="Save Changes" position="right" />
                  </Button>
                  <Button variant="destructive" size="sm">
                    <IconWithLabel icon={Trash2} label="Delete" position="right" />
                  </Button>
                  <Button variant="outline" size="sm">
                    <IconWithLabel icon={Download} label="Export" position="right" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Color Palettes Tab */}
        <TabsContent value="palettes" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Color-Blind Safe Palettes</CardTitle>
              <CardDescription>
                Recommended color palettes for different types of color vision deficiencies
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Universal Palette */}
              <div>
                <h3 className="text-sm font-medium mb-3">Universal Design Palette</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Works for all types of color blindness
                </p>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                  {Object.entries(colorBlindPalettes.universal).map(([key, value]) => {
                    if (typeof value === 'string') {
                      return (
                        <div key={key} className="text-center">
                          <div
                            className="w-full h-20 rounded-md mb-2 border"
                            style={{ backgroundColor: value }}
                          />
                          <p className="text-xs font-mono">{value}</p>
                          <p className="text-xs text-muted-foreground capitalize">{key}</p>
                        </div>
                      );
                    }
                    return null;
                  })}
                </div>
              </div>

              {/* Specific Palettes */}
              {Object.entries(colorBlindPalettes).map(([type, palette]) => {
                if (type === 'universal') return null;
                
                return (
                  <div key={type}>
                    <h3 className="text-sm font-medium mb-3 capitalize">{type} Palette</h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                      {Object.entries(palette).map(([key, value]) => {
                        if (typeof value === 'string') {
                          return (
                            <div key={key} className="text-center">
                              <div
                                className="w-full h-20 rounded-md mb-2 border"
                                style={{ backgroundColor: value }}
                              />
                              <p className="text-xs font-mono">{value}</p>
                              <p className="text-xs text-muted-foreground capitalize">{key}</p>
                            </div>
                          );
                        }
                        return null;
                      })}
                    </div>
                  </div>
                );
              })}

              {/* Contrast Checker */}
              <div>
                <h3 className="text-sm font-medium mb-3">Contrast Safe Combinations</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Color combinations that meet WCAG AA standards
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {getContrastSafeCombinations(colorBlindPalettes.universal)
                    .slice(0, 8)
                    .map(({ foreground, background, ratio }, index) => (
                      <div
                        key={index}
                        className="p-4 rounded-md border"
                        style={{ backgroundColor: background, color: foreground }}
                      >
                        <p className="font-medium">Sample Text</p>
                        <p className="text-sm">Contrast Ratio: {ratio.toFixed(2)}:1</p>
                        <div className="flex gap-2 mt-2">
                          <Badge
                            variant={ratio >= 7 ? "default" : ratio >= 4.5 ? "secondary" : "destructive"}
                          >
                            {ratio >= 7 ? "AAA" : ratio >= 4.5 ? "AA" : "Fail"}
                          </Badge>
                          <Badge variant="outline">
                            {ratio >= 3 ? "Large Text OK" : "Large Text Fail"}
                          </Badge>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}