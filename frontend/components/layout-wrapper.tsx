"use client"

import { useUIStore } from '@/store'

export function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const isSidebarOpen = useUIStore((state) => state.isSidebarOpen)
  
  return (
    <div className={`min-h-screen pt-16 transition-all ${isSidebarOpen ? 'ml-64' : 'ml-0'}`}>
      {children}
    </div>
  )
}