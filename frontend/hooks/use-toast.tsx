'use client';

import * as React from 'react';

export interface Toast {
  id: string;
  title?: string;
  description?: string;
  action?: React.ReactNode;
  variant?: 'default' | 'destructive' | 'success';
}

interface ToastContextType {
  toasts: Toast[];
  toast: (toast: Omit<Toast, 'id'>) => void;
  dismiss: (toastId?: string) => void;
}

const ToastContext = React.createContext<ToastContextType | undefined>(undefined);

const TOAST_LIMIT = 3;
const TOAST_REMOVE_DELAY = 5000;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  const toast = React.useCallback(
    ({ ...props }: Omit<Toast, 'id'>) => {
      const id = Math.random().toString(36).substr(2, 9);
      const newToast: Toast = { ...props, id };

      setToasts((prevToasts) => {
        const updatedToasts = [...prevToasts, newToast];
        if (updatedToasts.length > TOAST_LIMIT) {
          return updatedToasts.slice(-TOAST_LIMIT);
        }
        return updatedToasts;
      });

      // Auto dismiss after delay
      setTimeout(() => {
        dismiss(id);
      }, TOAST_REMOVE_DELAY);
    },
    []
  );

  const dismiss = React.useCallback((toastId?: string) => {
    setToasts((prevToasts) => {
      if (!toastId) {
        return [];
      }
      return prevToasts.filter((t) => t.id !== toastId);
    });
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, toast, dismiss }}>
      {children}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = React.useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}