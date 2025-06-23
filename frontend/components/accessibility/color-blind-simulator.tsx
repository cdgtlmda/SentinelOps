'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Eye, AlertTriangle, Check } from 'lucide-react';
import { simulateColorBlindness, getContrastRatio, contrastRatios } from '@/lib/design/color-blind-palette';

type ColorBlindMode = 'normal' | 'protanopia' | 'deuteranopia' | 'tritanopia' | 'monochromacy';

interface ColorBlindSimulatorProps {
  children?: React.ReactNode;
  showSideBySide?: boolean;
  detectProblems?: boolean;
}

export function ColorBlindSimulator({
  children,
  showSideBySide = true,
  detectProblems = true,
}: ColorBlindSimulatorProps) {
  const [mode, setMode] = useState<ColorBlindMode>('normal');
  const [problems, setProblems] = useState<string[]>([]);
  const normalRef = useRef<HTMLDivElement>(null);
  const simulatedRef = useRef<HTMLDivElement>(null);

  // Apply color-blind simulation
  useEffect(() => {
    if (!simulatedRef.current) return;

    const root = simulatedRef.current;
    root.setAttribute('data-color-blind-mode', mode);

    // Apply CSS filters for more accurate simulation
    const filters = {
      protanopia: 'url(#protanopia-filter)',
      deuteranopia: 'url(#deuteranopia-filter)',
      tritanopia: 'url(#tritanopia-filter)',
      monochromacy: 'grayscale(100%)',
      normal: 'none',
    };

    root.style.filter = filters[mode] || 'none';
  }, [mode]);

  // Detect problematic color usage
  useEffect(() => {
    if (!detectProblems || !normalRef.current) return;

    const detectColorProblems = () => {
      const issues: string[] = [];
      const elements = normalRef.current!.querySelectorAll('*');

      elements.forEach((element) => {
        const styles = window.getComputedStyle(element);
        const bgColor = styles.backgroundColor;
        const textColor = styles.color;

        // Check if element relies only on color for meaning
        if (element.classList.contains('status-indicator') || 
            element.classList.contains('severity-badge')) {
          const hasIcon = element.querySelector('svg, i, .icon');
          const hasText = element.textContent?.trim();
          
          if (!hasIcon && !hasText) {
            issues.push(`Element relies solely on color for status indication`);
          }
        }

        // Check contrast ratios
        if (bgColor !== 'rgba(0, 0, 0, 0)' && textColor) {
          const ratio = getContrastRatio(textColor, bgColor);
          if (ratio < contrastRatios.AA) {
            issues.push(`Low contrast detected: ${ratio.toFixed(2)} (minimum ${contrastRatios.AA})`);
          }
        }
      });

      setProblems([...new Set(issues)]);
    };

    const observer = new MutationObserver(detectColorProblems);
    observer.observe(normalRef.current, { subtree: true, childList: true, attributes: true });
    
    detectColorProblems();

    return () => observer.disconnect();
  }, [detectProblems, children]);

  const modeDescriptions = {
    normal: 'Normal color vision',
    protanopia: 'Red-blind (1% of males)',
    deuteranopia: 'Green-blind (6% of males)',
    tritanopia: 'Blue-blind (rare)',
    monochromacy: 'Complete color blindness (very rare)',
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Eye className="h-5 w-5" />
            <Select value={mode} onValueChange={(value) => setMode(value as ColorBlindMode)}>
              <SelectTrigger className="w-[250px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(modeDescriptions).map(([key, description]) => (
                  <SelectItem key={key} value={key}>
                    {description}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {problems.length > 0 && (
            <div className="flex items-center gap-2 text-sm text-yellow-600">
              <AlertTriangle className="h-4 w-4" />
              {problems.length} accessibility {problems.length === 1 ? 'issue' : 'issues'} detected
            </div>
          )}
        </div>
      </Card>

      {/* Problem Detection */}
      {detectProblems && problems.length > 0 && (
        <Alert className="border-yellow-500/50">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-1">
              <p className="font-medium">Color accessibility issues detected:</p>
              <ul className="list-disc list-inside space-y-1 text-sm">
                {problems.map((problem, index) => (
                  <li key={index}>{problem}</li>
                ))}
              </ul>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Comparison View */}
      {showSideBySide ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="p-4">
            <h3 className="text-sm font-medium mb-2 flex items-center gap-2">
              <Check className="h-4 w-4 text-green-600" />
              Normal Vision
            </h3>
            <div ref={normalRef} className="min-h-[200px]">
              {children || <DefaultContent />}
            </div>
          </Card>

          <Card className="p-4">
            <h3 className="text-sm font-medium mb-2">
              {modeDescriptions[mode]}
            </h3>
            <div ref={simulatedRef} className="min-h-[200px]">
              {children || <DefaultContent />}
            </div>
          </Card>
        </div>
      ) : (
        <Card className="p-4">
          <div ref={simulatedRef}>
            {children || <DefaultContent />}
          </div>
        </Card>
      )}

      {/* SVG Filters for accurate color blindness simulation */}
      <svg className="hidden">
        <defs>
          <filter id="protanopia-filter">
            <feColorMatrix
              type="matrix"
              values="0.567 0.433 0.000 0 0
                      0.558 0.442 0.000 0 0
                      0.000 0.242 0.758 0 0
                      0.000 0.000 0.000 1 0"
            />
          </filter>
          
          <filter id="deuteranopia-filter">
            <feColorMatrix
              type="matrix"
              values="0.625 0.375 0.000 0 0
                      0.700 0.300 0.000 0 0
                      0.000 0.300 0.700 0 0
                      0.000 0.000 0.000 1 0"
            />
          </filter>
          
          <filter id="tritanopia-filter">
            <feColorMatrix
              type="matrix"
              values="0.950 0.050 0.000 0 0
                      0.000 0.433 0.567 0 0
                      0.000 0.475 0.525 0 0
                      0.000 0.000 0.000 1 0"
            />
          </filter>
        </defs>
      </svg>
    </div>
  );
}

// Default content for demonstration
function DefaultContent() {
  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <span className="px-2 py-1 bg-green-500 text-white rounded text-sm">Success</span>
        <span className="px-2 py-1 bg-yellow-500 text-white rounded text-sm">Warning</span>
        <span className="px-2 py-1 bg-red-500 text-white rounded text-sm">Danger</span>
        <span className="px-2 py-1 bg-blue-500 text-white rounded text-sm">Info</span>
      </div>
      
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-500 rounded-full" />
          <span>Active Status</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-500 rounded-full" />
          <span>Error Status</span>
        </div>
      </div>
      
      <p className="text-sm text-gray-600">
        This simulator helps identify color accessibility issues in your UI.
      </p>
    </div>
  );
}