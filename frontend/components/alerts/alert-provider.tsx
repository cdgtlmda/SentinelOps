'use client';

import React, { createContext, useContext } from 'react';
import { useAlerts } from '@/hooks/use-alerts';
import { ToastNotification } from './toast-notification';
import { AlertBanner } from './alert-banner';
import { Alert, AlertPreferences } from '@/types/alerts';

interface AlertContextValue {
  alerts: Alert[];
  showAlert: (alert: Omit<Alert, 'id' | 'timestamp'>) => void;
  dismissAlert: (id: string) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearAll: () => void;
  preferences: AlertPreferences;
  updatePreferences: (prefs: Partial<AlertPreferences>) => void;
}

const AlertContext = createContext<AlertContextValue | undefined>(undefined);

export function useAlertContext() {
  const context = useContext(AlertContext);
  if (!context) {
    throw new Error('useAlertContext must be used within an AlertProvider');
  }
  return context;
}

interface AlertProviderProps {
  children: React.ReactNode;
}

export function AlertProvider({ children }: AlertProviderProps) {
  const {
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
  } = useAlerts();

  const contextValue: AlertContextValue = {
    alerts,
    showAlert,
    dismissAlert,
    markAsRead,
    markAllAsRead,
    clearAll,
    preferences,
    updatePreferences,
  };

  return (
    <AlertContext.Provider value={contextValue}>
      {children}
      
      {/* Toast Container */}
      <div 
        className="fixed pointer-events-none"
        style={{ zIndex: 'var(--z-alert-toast)' }}
        aria-live="polite"
        aria-label="Notifications"
      >
        {toasts.map((toast, index) => (
          <div key={toast.id} className="pointer-events-auto">
            <ToastNotification
              alert={toast}
              onDismiss={dismissAlert}
              index={index}
              position={preferences.position}
            />
          </div>
        ))}
      </div>
      
      {/* Banner Container */}
      {banners.map(banner => (
        <AlertBanner
          key={banner.id}
          alert={banner}
          onDismiss={dismissAlert}
          position={banner.priority === 'critical' ? 'top' : 'bottom'}
        />
      ))}
    </AlertContext.Provider>
  );
}