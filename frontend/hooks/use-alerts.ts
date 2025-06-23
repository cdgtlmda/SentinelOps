'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { Alert, AlertType, AlertPreferences, AlertPosition } from '@/types/alerts';
import { alertSoundManager } from '@/lib/alert-sounds';

const DEFAULT_PREFERENCES: AlertPreferences = {
  soundEnabled: true,
  position: 'top-right',
  maxToasts: 5,
  defaultDuration: 5000,
  soundVolume: 0.5,
};

interface UseAlertsReturn {
  alerts: Alert[];
  toasts: Alert[];
  banners: Alert[];
  preferences: AlertPreferences;
  showAlert: (alert: Omit<Alert, 'id' | 'timestamp'>) => void;
  dismissAlert: (id: string) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearAll: () => void;
  updatePreferences: (prefs: Partial<AlertPreferences>) => void;
}

export function useAlerts(): UseAlertsReturn {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [preferences, setPreferences] = useState<AlertPreferences>(DEFAULT_PREFERENCES);
  const priorityQueue = useRef<Alert[]>([]);

  // Load preferences from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('alert-preferences');
    if (stored) {
      const prefs = JSON.parse(stored);
      setPreferences({ ...DEFAULT_PREFERENCES, ...prefs });
      alertSoundManager.setEnabled(prefs.soundEnabled ?? true);
      alertSoundManager.setVolume(prefs.soundVolume ?? 0.5);
    }
  }, []);

  // Save preferences to localStorage
  const updatePreferences = useCallback((prefs: Partial<AlertPreferences>) => {
    setPreferences(prev => {
      const updated = { ...prev, ...prefs };
      localStorage.setItem('alert-preferences', JSON.stringify(updated));
      
      if (prefs.soundEnabled !== undefined) {
        alertSoundManager.setEnabled(prefs.soundEnabled);
      }
      if (prefs.soundVolume !== undefined) {
        alertSoundManager.setVolume(prefs.soundVolume);
      }
      
      return updated;
    });
  }, []);

  // Process priority queue
  const processPriorityQueue = useCallback(() => {
    if (priorityQueue.current.length === 0) return;

    const toasts = alerts.filter(a => !a.persist);
    if (toasts.length >= preferences.maxToasts) return;

    const nextAlert = priorityQueue.current.shift();
    if (nextAlert) {
      setAlerts(prev => [...prev, nextAlert]);
      
      // Play sound for the alert
      if (preferences.soundEnabled && nextAlert.sound !== false) {
        alertSoundManager.play(nextAlert);
      }
    }
  }, [alerts, preferences]);

  // Check priority queue whenever alerts change
  useEffect(() => {
    processPriorityQueue();
  }, [alerts, processPriorityQueue]);

  const showAlert = useCallback((alertData: Omit<Alert, 'id' | 'timestamp'>) => {
    const newAlert: Alert = {
      ...alertData,
      id: `alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      duration: alertData.duration ?? (alertData.persist ? 0 : preferences.defaultDuration),
      dismissible: alertData.dismissible ?? true,
      read: false,
    };

    // If it's a high priority alert or we have room, show immediately
    const toasts = alerts.filter(a => !a.persist);
    const priority = newAlert.priority || 'normal';
    
    if (priority === 'critical' || priority === 'high' || toasts.length < preferences.maxToasts) {
      setAlerts(prev => [...prev, newAlert]);
      
      // Play sound for the alert
      if (preferences.soundEnabled && newAlert.sound !== false) {
        alertSoundManager.play(newAlert);
      }
    } else {
      // Add to priority queue
      priorityQueue.current.push(newAlert);
      // Sort by priority
      priorityQueue.current.sort((a, b) => {
        const priorityOrder = { critical: 0, high: 1, normal: 2, low: 3 };
        const aPriority = priorityOrder[a.priority || 'normal'];
        const bPriority = priorityOrder[b.priority || 'normal'];
        return aPriority - bPriority;
      });
    }
  }, [alerts, preferences]);

  const dismissAlert = useCallback((id: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== id));
    // Process queue after dismissing
    setTimeout(processPriorityQueue, 100);
  }, [processPriorityQueue]);

  const markAsRead = useCallback((id: string) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === id ? { ...alert, read: true } : alert
    ));
  }, []);

  const markAllAsRead = useCallback(() => {
    setAlerts(prev => prev.map(alert => ({ ...alert, read: true })));
  }, []);

  const clearAll = useCallback(() => {
    setAlerts([]);
    priorityQueue.current = [];
  }, []);

  // Separate toasts and banners
  const toasts = alerts.filter(alert => !alert.persist);
  const banners = alerts.filter(alert => alert.persist);

  return {
    alerts,
    toasts,
    banners,
    preferences,
    showAlert,
    dismissAlert,
    markAsRead,
    markAllAsRead,
    clearAll,
    updatePreferences,
  };
}