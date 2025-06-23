'use client';

import { useState, useEffect, useCallback } from 'react';
import { 
  getColorBlindPalette, 
  generateColorBlindCSS,
  simulateColorBlindness 
} from '@/lib/design/color-blind-palette';

export type ColorBlindMode = 'normal' | 'protanopia' | 'deuteranopia' | 'tritanopia' | 'monochromacy';
export type PatternPreference = 'auto' | 'always' | 'never';
export type IconLabelPreference = 'auto' | 'always' | 'tooltip' | 'hidden';

interface VisualAccessibilitySettings {
  colorBlindMode: ColorBlindMode;
  usePatterns: PatternPreference;
  iconLabels: IconLabelPreference;
  highContrast: boolean;
  reduceMotion: boolean;
  fontSize: 'normal' | 'large' | 'extra-large';
}

const STORAGE_KEY = 'visual-accessibility-settings';

const defaultSettings: VisualAccessibilitySettings = {
  colorBlindMode: 'normal',
  usePatterns: 'auto',
  iconLabels: 'auto',
  highContrast: false,
  reduceMotion: false,
  fontSize: 'normal',
};

export function useVisualAccessibility() {
  const [settings, setSettings] = useState<VisualAccessibilitySettings>(defaultSettings);
  const [isInitialized, setIsInitialized] = useState(false);

  // Load settings from localStorage
  useEffect(() => {
    const loadSettings = () => {
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          const parsed = JSON.parse(stored);
          setSettings({ ...defaultSettings, ...parsed });
        }

        // Check system preferences
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches;
        
        setSettings(prev => ({
          ...prev,
          reduceMotion: prev.reduceMotion || prefersReducedMotion,
          highContrast: prev.highContrast || prefersHighContrast,
        }));
      } catch (error) {
        console.error('Failed to load visual accessibility settings:', error);
      } finally {
        setIsInitialized(true);
      }
    };

    loadSettings();
  }, []);

  // Apply settings to document
  useEffect(() => {
    if (!isInitialized) return;

    const html = document.documentElement;

    // Apply color blind mode
    html.setAttribute('data-color-blind-mode', settings.colorBlindMode);

    // Apply other settings as classes
    html.classList.toggle('high-contrast', settings.highContrast);
    html.classList.toggle('reduce-motion', settings.reduceMotion);
    html.classList.toggle('use-patterns', settings.usePatterns === 'always');
    html.classList.toggle('show-icon-labels', settings.iconLabels === 'always');

    // Apply font size
    const fontSizeMap = {
      'normal': '16px',
      'large': '18px',
      'extra-large': '20px',
    };
    html.style.fontSize = fontSizeMap[settings.fontSize];

    // Inject color blind CSS
    let styleElement = document.getElementById('color-blind-styles');
    if (!styleElement) {
      styleElement = document.createElement('style');
      styleElement.id = 'color-blind-styles';
      document.head.appendChild(styleElement);
    }
    
    if (settings.colorBlindMode !== 'normal') {
      styleElement.textContent = generateColorBlindCSS(settings.colorBlindMode);
    } else {
      styleElement.textContent = '';
    }

    // Save to localStorage
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }, [settings, isInitialized]);

  // Update individual settings
  const updateSetting = useCallback(<K extends keyof VisualAccessibilitySettings>(
    key: K,
    value: VisualAccessibilitySettings[K]
  ) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  }, []);

  // Reset to defaults
  const resetSettings = useCallback(() => {
    setSettings(defaultSettings);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  // Check if patterns should be shown
  const shouldShowPatterns = useCallback(() => {
    if (settings.usePatterns === 'always') return true;
    if (settings.usePatterns === 'never') return false;
    // Auto: show patterns in color blind modes
    return settings.colorBlindMode !== 'normal';
  }, [settings.usePatterns, settings.colorBlindMode]);

  // Check if icon labels should be shown
  const getIconLabelMode = useCallback(() => {
    if (settings.iconLabels !== 'auto') return settings.iconLabels;
    // Auto: show labels in color blind modes
    return settings.colorBlindMode !== 'normal' ? 'always' : 'tooltip';
  }, [settings.iconLabels, settings.colorBlindMode]);

  // Simulate color for current mode
  const simulateColor = useCallback((color: string) => {
    if (settings.colorBlindMode === 'normal') return color;
    return simulateColorBlindness(color, settings.colorBlindMode);
  }, [settings.colorBlindMode]);

  // Get appropriate color palette
  const getColorPalette = useCallback(() => {
    return getColorBlindPalette(
      settings.colorBlindMode === 'normal' ? undefined : settings.colorBlindMode
    );
  }, [settings.colorBlindMode]);

  return {
    settings,
    updateSetting,
    resetSettings,
    shouldShowPatterns,
    getIconLabelMode,
    simulateColor,
    getColorPalette,
    isInitialized,
  };
}

// Hook for checking if user prefers reduced motion
export function usePrefersReducedMotion() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handler = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches);
    };

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  return prefersReducedMotion;
}

// Hook for checking if user prefers high contrast
export function usePrefersHighContrast() {
  const [prefersHighContrast, setPrefersHighContrast] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-contrast: high)');
    setPrefersHighContrast(mediaQuery.matches);

    const handler = (event: MediaQueryListEvent) => {
      setPrefersHighContrast(event.matches);
    };

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  return prefersHighContrast;
}