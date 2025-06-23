'use client';

import React, { useEffect, useState } from 'react';
import { Alert, AlertType } from '@/types/alerts';
import { X, CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ToastNotificationProps {
  alert: Alert;
  onDismiss: (id: string) => void;
  index: number;
  position: string;
}

const iconMap: Record<AlertType, React.ReactNode> = {
  success: <CheckCircle className="w-5 h-5" />,
  error: <XCircle className="w-5 h-5" />,
  warning: <AlertTriangle className="w-5 h-5" />,
  info: <Info className="w-5 h-5" />,
};

const styleMap: Record<AlertType, string> = {
  success: 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200 border-green-200 dark:border-green-800',
  error: 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 border-red-200 dark:border-red-800',
  warning: 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-200 border-yellow-200 dark:border-yellow-800',
  info: 'bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-200 border-blue-200 dark:border-blue-800',
};

const iconColorMap: Record<AlertType, string> = {
  success: 'text-green-600 dark:text-green-400',
  error: 'text-red-600 dark:text-red-400',
  warning: 'text-yellow-600 dark:text-yellow-400',
  info: 'text-blue-600 dark:text-blue-400',
};

export function ToastNotification({ alert, onDismiss, index, position }: ToastNotificationProps) {
  const [isExiting, setIsExiting] = useState(false);
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    if (alert.duration && alert.duration > 0) {
      const startTime = Date.now();
      const interval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const remaining = Math.max(0, 100 - (elapsed / alert.duration!) * 100);
        setProgress(remaining);
        
        if (remaining === 0) {
          clearInterval(interval);
          handleDismiss();
        }
      }, 10);

      return () => clearInterval(interval);
    }
  }, [alert.duration]);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => {
      onDismiss(alert.id);
    }, 300);
  };

  const getPositionStyles = () => {
    const baseOffset = 16;
    const toastHeight = 80;
    const gap = 8;
    const offset = baseOffset + (index * (toastHeight + gap));

    switch (position) {
      case 'top-right':
        return { top: `${offset}px`, right: '16px' };
      case 'top-left':
        return { top: `${offset}px`, left: '16px' };
      case 'bottom-right':
        return { bottom: `${offset}px`, right: '16px' };
      case 'bottom-left':
        return { bottom: `${offset}px`, left: '16px' };
      case 'top-center':
        return { top: `${offset}px`, left: '50%', transform: 'translateX(-50%)' };
      case 'bottom-center':
        return { bottom: `${offset}px`, left: '50%', transform: 'translateX(-50%)' };
      default:
        return { top: `${offset}px`, right: '16px' };
    }
  };

  const animationClass = position.includes('right') 
    ? isExiting ? 'animate-slide-out-right' : 'animate-slide-in-right'
    : position.includes('left')
    ? isExiting ? 'animate-slide-out-left' : 'animate-slide-in-left'
    : isExiting ? 'animate-fade-out' : 'animate-fade-in';

  return (
    <div
      className={cn(
        'fixed w-full max-w-sm p-4 rounded-lg border shadow-lg transition-all duration-300',
        styleMap[alert.type],
        animationClass
      )}
      style={getPositionStyles()}
      role="alert"
      aria-live="polite"
      aria-atomic="true"
    >
      <div className="flex items-start gap-3">
        <div className={cn('flex-shrink-0 mt-0.5', iconColorMap[alert.type])}>
          {iconMap[alert.type]}
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className="font-medium">{alert.title}</h3>
          {alert.message && (
            <p className="mt-1 text-sm opacity-90">{alert.message}</p>
          )}
          
          {alert.actions && alert.actions.length > 0 && (
            <div className="mt-3 flex items-center gap-2">
              {alert.actions.map((action, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    action.onClick();
                    if (action.variant !== 'ghost') {
                      handleDismiss();
                    }
                  }}
                  className={cn(
                    'text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 rounded px-2 py-1',
                    action.variant === 'primary' && 'bg-current text-white hover:opacity-90',
                    action.variant === 'secondary' && 'border border-current hover:bg-current hover:text-white',
                    (!action.variant || action.variant === 'ghost') && 'hover:underline'
                  )}
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>
        
        {alert.dismissible !== false && (
          <button
            onClick={handleDismiss}
            className="flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity focus:outline-none focus:ring-2 focus:ring-offset-2 rounded"
            aria-label="Dismiss notification"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
      
      {alert.duration && alert.duration > 0 && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-current opacity-20 rounded-b-lg overflow-hidden">
          <div
            className="h-full bg-current opacity-60 transition-all duration-100 ease-linear"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
}