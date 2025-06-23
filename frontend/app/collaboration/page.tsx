'use client';

import React from 'react';
import { CollaborationDashboard } from '@/components/collaboration/collaboration-dashboard';

export default function CollaborationPage() {
  return (
    <div className="container mx-auto py-6 px-4">
      <CollaborationDashboard initialTopology="mesh" />
    </div>
  );
}