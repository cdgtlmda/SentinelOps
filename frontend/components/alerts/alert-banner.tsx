'use client';

import React, { useState } from 'react';
import { Alert, AlertType } from '@/types/alerts';
import { X, ChevronDown, ChevronUp, AlertCircle, CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AlertBannerProps {
  alert: Alert;
  onDismiss: (id: string) => void;
  position?: 'top' | 'bottom';
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

const priorityBorderMap: Record<string, string> = {
  critical: 'border-l-4',
  high: 'border-l-3',
  normal: 'border-l-2',
  low: 'border-l',
};

export function AlertBanner({ alert, onDismiss, position = 'top' }: AlertBannerProps) {
  const [isExiting, setIsExiting] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => {
      onDismiss(alert.id);
    }, 300);
  };

  const animationClass = position === 'top'
    ? isExiting ? 'animate-slide-up' : 'animate-slide-down'
    : isExiting ? 'animate-slide-out-panel' : 'animate-slide-in-panel';

  const borderStyle = alert.priority ? priorityBorderMap[alert.priority] : '';

  return (
    <div
      className={cn(
        'fixed left-0 right-0 transition-all duration-300',
        position === 'top' ? 'top-0' : 'bottom-0',
        animationClass
      )}
      style={{ zIndex: 'var(--z-alert-banner)' }}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <div className={cn(
        'px-4 py-3 border-b shadow-lg',
        styleMap[alert.type],
        borderStyle
      )}>
        <div className="max-w-7xl mx-auto">
          <div className="flex items-start gap-3">
            <div className={cn('flex-shrink-0 mt-0.5', iconColorMap[alert.type])}>
              {iconMap[alert.type]}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-start gap-2">
                <div className="flex-1">
                  <h3 className="font-medium">{alert.title}</h3>
                  {alert.message && (
                    <p className="mt-1 text-sm opacity-90">{alert.message}</p>
                  )}
                  
                  {alert.details && isExpanded && (
                    <div className="mt-3 p-3 rounded-md bg-black/5 dark:bg-white/5">
                      <p className="text-sm whitespace-pre-wrap">{alert.details}</p>
                    </div>
                  )}
                  
                  <div className="mt-3 flex items-center gap-3">
                    {alert.actions && alert.actions.map((action, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          action.onClick();
                          if (action.variant !== 'ghost') {
                            handleDismiss();
                          }
                        }}
                        className={cn(
                          'text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 rounded px-3 py-1.5',
                          action.variant === 'primary' && 'bg-current text-white hover:opacity-90',
                          action.variant === 'secondary' && 'border border-current hover:bg-current hover:text-white',
                          (!action.variant || action.variant === 'ghost') && 'hover:underline'
                        )}
                      >
                        {action.label}
                      </button>
                    ))}
                    
                    {alert.details && (
                      <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="text-sm font-medium hover:underline focus:outline-none focus:ring-2 focus:ring-offset-2 rounded flex items-center gap-1"
                        aria-expanded={isExpanded}
                        aria-controls={`alert-details-${alert.id}`}
                      >
                        {isExpanded ? (
                          <>
                            Hide Details
                            <ChevronUp className="w-4 h-4" />
                          </>
                        ) : (
                          <>
                            Show Details
                            <ChevronDown className="w-4 h-4" />
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
                
                {alert.dismissible !== false && (
                  <button
                    onClick={handleDismiss}
                    className="flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity focus:outline-none focus:ring-2 focus:ring-offset-2 rounded p-1"
                    aria-label="Dismiss alert"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}