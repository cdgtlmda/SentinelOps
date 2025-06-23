'use client';

import { AgentStatusIndicator, AgentStatusDot } from '@/components/agents';
import { AgentStatus } from '@/types/agent';

export default function AgentStatusDemo() {
  const statuses: AgentStatus[] = ['idle', 'processing', 'waiting', 'error', 'completed'];
  const sizes = ['small', 'medium', 'large'] as const;

  return (
    <div className="container mx-auto p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-2">Agent Status Indicators</h1>
        <p className="text-muted-foreground">
          Visual indicators for different agent states with animations and accessibility features
        </p>
      </div>

      {/* Status Indicators with Labels */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Status Indicators with Labels</h2>
        <div className="space-y-6">
          {sizes.map((size) => (
            <div key={size}>
              <h3 className="text-lg font-medium mb-3 capitalize">{size} Size</h3>
              <div className="flex flex-wrap gap-3">
                {statuses.map((status) => (
                  <AgentStatusIndicator
                    key={status}
                    status={status}
                    size={size}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Status Indicators without Labels */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Status Indicators without Labels</h2>
        <div className="space-y-6">
          {sizes.map((size) => (
            <div key={size}>
              <h3 className="text-lg font-medium mb-3 capitalize">{size} Size</h3>
              <div className="flex flex-wrap gap-3">
                {statuses.map((status) => (
                  <AgentStatusIndicator
                    key={status}
                    status={status}
                    size={size}
                    showLabel={false}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Status Dots */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Status Dots</h2>
        <div className="space-y-6">
          {sizes.map((size) => (
            <div key={size}>
              <h3 className="text-lg font-medium mb-3 capitalize">{size} Size</h3>
              <div className="flex flex-wrap gap-6 items-center">
                {statuses.map((status) => (
                  <div key={status} className="flex items-center gap-2">
                    <AgentStatusDot status={status} size={size} />
                    <span className="text-sm capitalize">{status}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Dark Mode Preview */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Dark Mode Preview</h2>
        <div className="rounded-lg bg-gray-900 p-6">
          <div className="space-y-4">
            <div className="flex flex-wrap gap-3">
              {statuses.map((status) => (
                <AgentStatusIndicator
                  key={status}
                  status={status}
                  size="medium"
                />
              ))}
            </div>
            <div className="flex flex-wrap gap-6 items-center">
              {statuses.map((status) => (
                <div key={status} className="flex items-center gap-2">
                  <AgentStatusDot status={status} size="medium" />
                  <span className="text-sm capitalize text-gray-300">{status}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Animation States */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Animation States</h2>
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <AgentStatusIndicator status="processing" size="large" />
            <span className="text-sm text-muted-foreground">
              Processing status has a spinning animation
            </span>
          </div>
          <div className="flex items-center gap-3">
            <AgentStatusDot status="processing" size="large" />
            <span className="text-sm text-muted-foreground">
              Processing dot has pulse and ping animations
            </span>
          </div>
        </div>
      </section>

      {/* Accessibility */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Accessibility Features</h2>
        <div className="rounded-lg border p-6 bg-muted/50">
          <ul className="space-y-2 text-sm">
            <li>✓ All indicators have proper ARIA labels</li>
            <li>✓ Status is announced to screen readers</li>
            <li>✓ Color is not the only indicator (icons provide meaning)</li>
            <li>✓ Animations respect prefers-reduced-motion</li>
            <li>✓ Sufficient color contrast ratios</li>
            <li>✓ Keyboard navigable when interactive</li>
          </ul>
        </div>
      </section>
    </div>
  );
}