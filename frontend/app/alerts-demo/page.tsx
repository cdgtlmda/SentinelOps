'use client';

import React from 'react';
import { useAlertContext } from '@/components/alerts';
import { AlertType } from '@/types/alerts';
import { alertSoundManager } from '@/lib/alert-sounds';

export default function AlertsDemoPage() {
  const { showAlert, preferences, updatePreferences } = useAlertContext();

  const showToast = (type: AlertType, options?: any) => {
    showAlert({
      type,
      title: `${type.charAt(0).toUpperCase() + type.slice(1)} Alert`,
      message: `This is a ${type} toast notification`,
      ...options,
    });
  };

  const showBanner = (type: AlertType, priority?: string) => {
    showAlert({
      type,
      title: `${type.charAt(0).toUpperCase() + type.slice(1)} Banner Alert`,
      message: 'This is a banner alert that stays at the top of the screen',
      persist: true,
      priority: priority as any,
      details: 'This is additional information that can be shown in a collapsible section. It provides more context about the alert and what actions the user might need to take.',
      actions: [
        {
          label: 'Take Action',
          onClick: () => console.log('Action taken'),
          variant: 'primary',
        },
        {
          label: 'Learn More',
          onClick: () => console.log('Learn more clicked'),
          variant: 'ghost',
        },
      ],
    });
  };

  const showMultipleToasts = () => {
    const types: AlertType[] = ['success', 'error', 'warning', 'info'];
    types.forEach((type, index) => {
      setTimeout(() => {
        showToast(type, {
          message: `Toast ${index + 1} of ${types.length}`,
        });
      }, index * 500);
    });
  };

  const showPriorityToast = (priority: string) => {
    showAlert({
      type: 'warning',
      title: `${priority.charAt(0).toUpperCase() + priority.slice(1)} Priority Alert`,
      message: `This is a ${priority} priority notification`,
      priority: priority as any,
    });
  };

  const showActionToast = () => {
    showAlert({
      type: 'info',
      title: 'Action Required',
      message: 'This alert has action buttons',
      duration: 0, // Don't auto-dismiss
      actions: [
        {
          label: 'Confirm',
          onClick: () => {
            showToast('success', { title: 'Confirmed!', message: 'Action was confirmed' });
          },
          variant: 'primary',
        },
        {
          label: 'Cancel',
          onClick: () => console.log('Cancelled'),
          variant: 'secondary',
        },
      ],
    });
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">Alert System Demo</h1>

      {/* Toast Notifications */}
      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Toast Notifications</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <button
            onClick={() => showToast('success')}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
          >
            Success Toast
          </button>
          <button
            onClick={() => showToast('error')}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
          >
            Error Toast
          </button>
          <button
            onClick={() => showToast('warning')}
            className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 transition-colors"
          >
            Warning Toast
          </button>
          <button
            onClick={() => showToast('info')}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            Info Toast
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={showMultipleToasts}
            className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 transition-colors"
          >
            Show Multiple Toasts
          </button>
          <button
            onClick={showActionToast}
            className="px-4 py-2 bg-indigo-500 text-white rounded hover:bg-indigo-600 transition-colors"
          >
            Toast with Actions
          </button>
        </div>
      </section>

      {/* Banner Alerts */}
      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Banner Alerts</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button
            onClick={() => showBanner('success')}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
          >
            Success Banner
          </button>
          <button
            onClick={() => showBanner('error', 'critical')}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
          >
            Critical Banner
          </button>
          <button
            onClick={() => showBanner('warning', 'high')}
            className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 transition-colors"
          >
            High Priority Banner
          </button>
          <button
            onClick={() => showBanner('info')}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            Info Banner
          </button>
        </div>
      </section>

      {/* Priority Queue */}
      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Priority Queue Demo</h2>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          These will queue if max toasts ({preferences.maxToasts}) are already showing
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button
            onClick={() => showPriorityToast('critical')}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
          >
            Critical Priority
          </button>
          <button
            onClick={() => showPriorityToast('high')}
            className="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 transition-colors"
          >
            High Priority
          </button>
          <button
            onClick={() => showPriorityToast('normal')}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            Normal Priority
          </button>
          <button
            onClick={() => showPriorityToast('low')}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
          >
            Low Priority
          </button>
        </div>
      </section>

      {/* Settings */}
      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Alert Settings</h2>
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <label className="font-medium">Sound Enabled:</label>
            <input
              type="checkbox"
              checked={preferences.soundEnabled}
              onChange={(e) => updatePreferences({ soundEnabled: e.target.checked })}
              className="w-5 h-5"
            />
          </div>
          
          <div className="flex items-center gap-4">
            <label className="font-medium">Sound Volume:</label>
            <input
              type="range"
              min="0"
              max="100"
              value={preferences.soundVolume * 100}
              onChange={(e) => updatePreferences({ soundVolume: Number(e.target.value) / 100 })}
              className="flex-1"
            />
            <span>{Math.round(preferences.soundVolume * 100)}%</span>
          </div>
          
          <div className="flex items-center gap-4">
            <label className="font-medium">Position:</label>
            <select
              value={preferences.position}
              onChange={(e) => updatePreferences({ position: e.target.value as any })}
              className="px-3 py-1 border rounded dark:bg-gray-800"
            >
              <option value="top-right">Top Right</option>
              <option value="top-left">Top Left</option>
              <option value="bottom-right">Bottom Right</option>
              <option value="bottom-left">Bottom Left</option>
              <option value="top-center">Top Center</option>
              <option value="bottom-center">Bottom Center</option>
            </select>
          </div>
          
          <div className="flex items-center gap-4">
            <label className="font-medium">Max Toasts:</label>
            <input
              type="number"
              min="1"
              max="10"
              value={preferences.maxToasts}
              onChange={(e) => updatePreferences({ maxToasts: Number(e.target.value) })}
              className="px-3 py-1 border rounded w-20 dark:bg-gray-800"
            />
          </div>
          
          <button
            onClick={() => alertSoundManager.testSound('info')}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
          >
            Test Sound
          </button>
        </div>
      </section>
    </div>
  );
}