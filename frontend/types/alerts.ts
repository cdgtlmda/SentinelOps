export type AlertType = 'success' | 'error' | 'warning' | 'info';
export type AlertPosition = 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';

export interface Alert {
  id: string;
  type: AlertType;
  title: string;
  message?: string;
  duration?: number; // in milliseconds, 0 for no auto-dismiss
  actions?: AlertAction[];
  dismissible?: boolean;
  timestamp: Date;
  read?: boolean;
  sound?: boolean;
  persist?: boolean; // whether to persist in notification center
  priority?: 'low' | 'normal' | 'high' | 'critical';
  details?: string; // collapsible details for banners
}

export interface AlertAction {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
}

export interface AlertSound {
  type: AlertType;
  priority?: Alert['priority'];
  url: string;
  volume?: number;
}

export interface AlertPreferences {
  soundEnabled: boolean;
  position: AlertPosition;
  maxToasts: number;
  defaultDuration: number;
  soundVolume: number;
}

export interface NotificationGroup {
  id: string;
  title: string;
  alerts: Alert[];
  collapsed?: boolean;
}