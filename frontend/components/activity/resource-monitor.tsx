import React from 'react'
import type { ResourceMetrics } from '@/types/activity'

interface ResourceMonitorProps {
  metrics: ResourceMetrics
}

export function ResourceMonitor({ metrics }: ResourceMonitorProps) {
  const formatCost = (cents: number) => {
    return `$${(cents / 100).toFixed(2)}`
  }

  const formatBytes = (bytes: number) => {
    const gb = bytes / 1024
    return `${gb.toFixed(1)} GB`
  }

  return (
    <div className="space-y-6">
      {/* Cloud Resources */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
          Cloud Resources
        </h3>
        
        <div className="space-y-4">
          {/* Compute */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Compute
            </h4>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gray-50 dark:bg-gray-900 rounded p-3">
                <p className="text-xs text-gray-500 dark:text-gray-400">Instances</p>
                <p className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  {metrics.cloudResources.compute.instances}
                </p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 rounded p-3">
                <p className="text-xs text-gray-500 dark:text-gray-400">vCPUs</p>
                <p className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  {metrics.cloudResources.compute.vcpus}
                </p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 rounded p-3">
                <p className="text-xs text-gray-500 dark:text-gray-400">Memory</p>
                <p className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  {metrics.cloudResources.compute.memoryGB} GB
                </p>
              </div>
            </div>
          </div>

          {/* Storage */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Storage
            </h4>
            <div className="bg-gray-50 dark:bg-gray-900 rounded p-3">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-gray-500 dark:text-gray-400">Usage</span>
                <span className="text-sm text-gray-900 dark:text-gray-100">
                  {formatBytes(metrics.cloudResources.storage.usedGB)} / {formatBytes(metrics.cloudResources.storage.totalGB)}
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                  style={{
                    width: `${(metrics.cloudResources.storage.usedGB / metrics.cloudResources.storage.totalGB) * 100}%`
                  }}
                />
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {((metrics.cloudResources.storage.usedGB / metrics.cloudResources.storage.totalGB) * 100).toFixed(1)}% used
              </p>
            </div>
          </div>

          {/* Network */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Network
            </h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 dark:bg-gray-900 rounded p-3">
                <p className="text-xs text-gray-500 dark:text-gray-400">Ingress</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {metrics.cloudResources.network.ingressMbps.toFixed(1)} Mbps
                </p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 rounded p-3">
                <p className="text-xs text-gray-500 dark:text-gray-400">Egress</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {metrics.cloudResources.network.egressMbps.toFixed(1)} Mbps
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* API Usage */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
          API Usage
        </h3>
        
        <div className="space-y-4">
          {metrics.apiUsage.map((api, index) => (
            <div key={index} className="bg-gray-50 dark:bg-gray-900 rounded p-4">
              <div className="flex items-start justify-between mb-3">
                <h4 className="font-medium text-gray-900 dark:text-gray-100">
                  {api.provider}
                </h4>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {api.callCount} calls
                </span>
              </div>
              
              {api.tokensUsed && (
                <div className="mb-3">
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Tokens Used</p>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {api.tokensUsed.toLocaleString()}
                  </p>
                </div>
              )}
              
              {api.rateLimit && (
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-gray-500 dark:text-gray-400">Rate Limit</span>
                    <span className="text-xs text-gray-900 dark:text-gray-100">
                      {api.rateLimit.remaining} / {api.rateLimit.limit}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full transition-all duration-500 ${
                        (api.rateLimit.remaining / api.rateLimit.limit) < 0.2
                          ? 'bg-red-500'
                          : (api.rateLimit.remaining / api.rateLimit.limit) < 0.5
                          ? 'bg-yellow-500'
                          : 'bg-green-500'
                      }`}
                      style={{
                        width: `${(api.rateLimit.remaining / api.rateLimit.limit) * 100}%`
                      }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Resets at {new Date(api.rateLimit.resetAt).toLocaleTimeString()}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Cost Estimates */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
          Cost Estimates (Hourly)
        </h3>
        
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">Compute</span>
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {formatCost(metrics.estimatedCost.compute)}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">Storage</span>
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {formatCost(metrics.estimatedCost.storage)}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">Network</span>
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {formatCost(metrics.estimatedCost.network)}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">API Calls</span>
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {formatCost(metrics.estimatedCost.api)}
            </span>
          </div>
          
          <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
            <div className="flex justify-between items-center">
              <span className="text-base font-medium text-gray-900 dark:text-gray-100">Total</span>
              <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {formatCost(metrics.estimatedCost.total)}
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Projected daily: {formatCost(metrics.estimatedCost.total * 24)}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}