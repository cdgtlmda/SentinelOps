"use client"

import React from 'react'
import { cn } from '@/lib/utils'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Home,
  Shield,
  Users,
  Activity,
  Settings,
  Bell,
  MessageSquare,
  BarChart3,
  FileText,
  Menu,
  X
} from 'lucide-react'

interface TabletNavigationProps {
  children?: React.ReactNode
  orientation: 'portrait' | 'landscape'
  className?: string
}

const navigationItems = [
  { href: '/dashboard', icon: Home, label: 'Dashboard' },
  { href: '/incidents', icon: Shield, label: 'Incidents' },
  { href: '/agents', icon: Users, label: 'Agents' },
  { href: '/monitoring', icon: Activity, label: 'Monitoring' },
  { href: '/analytics', icon: BarChart3, label: 'Analytics' },
  { href: '/workflows', icon: FileText, label: 'Workflows' },
  { href: '/chat', icon: MessageSquare, label: 'Chat' },
  { href: '/notifications', icon: Bell, label: 'Alerts' },
  { href: '/settings', icon: Settings, label: 'Settings' }
]

export function TabletNavigation({ children, orientation, className }: TabletNavigationProps) {
  const pathname = usePathname()
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false)
  const isLandscape = orientation === 'landscape'

  // If custom navigation provided, use it
  if (children) {
    return (
      <nav className={cn(
        isLandscape 
          ? "w-20 lg:w-64 border-r bg-gray-50/50 flex-shrink-0" 
          : "h-16 border-b bg-white",
        className
      )}>
        {children}
      </nav>
    )
  }

  // Landscape - Side Navigation
  if (isLandscape) {
    return (
      <nav className={cn(
        "w-20 lg:w-64 border-r bg-gray-50/50 flex-shrink-0 flex flex-col",
        className
      )}>
        {/* Logo */}
        <div className="h-16 border-b flex items-center justify-center px-4">
          <Shield className="w-8 h-8 text-blue-600" />
          <span className="ml-2 text-xl font-bold text-gray-900 hidden lg:block">
            SentinelOps
          </span>
        </div>

        {/* Navigation Items */}
        <div className="flex-1 overflow-y-auto py-4">
          {navigationItems.map((item) => {
            const isActive = pathname === item.href
            const Icon = item.icon
            
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center px-4 py-3 mx-2 rounded-lg transition-colors relative group",
                  isActive 
                    ? "bg-blue-50 text-blue-600" 
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                )}
              >
                <Icon className={cn(
                  "flex-shrink-0",
                  "w-6 h-6 lg:w-5 lg:h-5"
                )} />
                <span className="ml-3 hidden lg:block font-medium">
                  {item.label}
                </span>
                
                {/* Tooltip for collapsed state */}
                <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-sm rounded opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity lg:hidden whitespace-nowrap z-50">
                  {item.label}
                </div>
                
                {/* Active indicator */}
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-blue-600 rounded-r" />
                )}
              </Link>
            )
          })}
        </div>

        {/* User Profile */}
        <div className="border-t p-4">
          <div className="flex items-center">
            <div className="w-10 h-10 rounded-full bg-gray-300 flex-shrink-0" />
            <div className="ml-3 hidden lg:block">
              <div className="text-sm font-medium text-gray-900">John Doe</div>
              <div className="text-xs text-gray-500">john@example.com</div>
            </div>
          </div>
        </div>
      </nav>
    )
  }

  // Portrait - Top Navigation
  return (
    <nav className={cn(
      "h-16 border-b bg-white flex items-center justify-between px-4",
      className
    )}>
      {/* Logo and Menu Toggle */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 rounded-lg hover:bg-gray-100 lg:hidden"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
        <Shield className="w-8 h-8 text-blue-600" />
        <span className="text-xl font-bold text-gray-900">SentinelOps</span>
      </div>

      {/* Desktop Navigation Items */}
      <div className="hidden lg:flex items-center gap-1">
        {navigationItems.slice(0, 6).map((item) => {
          const isActive = pathname === item.href
          const Icon = item.icon
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-lg transition-colors",
                isActive 
                  ? "bg-blue-50 text-blue-600" 
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              )}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </Link>
          )
        })}
      </div>

      {/* User and Actions */}
      <div className="flex items-center gap-3">
        <button className="p-2 rounded-lg hover:bg-gray-100 relative">
          <Bell className="w-6 h-6 text-gray-600" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
        </button>
        <div className="w-10 h-10 rounded-full bg-gray-300" />
      </div>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div className="absolute top-16 left-0 right-0 bg-white border-b shadow-lg z-50 lg:hidden">
          <div className="py-2">
            {navigationItems.map((item) => {
              const isActive = pathname === item.href
              const Icon = item.icon
              
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-6 py-3 transition-colors",
                    isActive 
                      ? "bg-blue-50 text-blue-600" 
                      : "text-gray-600 hover:bg-gray-50"
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.label}</span>
                </Link>
              )
            })}
          </div>
        </div>
      )}
    </nav>
  )
}

// Adaptive Navigation Item with touch-friendly sizing
interface AdaptiveNavItemProps {
  href: string
  icon: React.ElementType
  label: string
  isActive?: boolean
  orientation: 'portrait' | 'landscape'
  showLabel?: boolean
  badge?: number
}

export function AdaptiveNavItem({
  href,
  icon: Icon,
  label,
  isActive,
  orientation,
  showLabel = true,
  badge
}: AdaptiveNavItemProps) {
  const isLandscape = orientation === 'landscape'
  
  return (
    <Link
      href={href}
      className={cn(
        "relative flex items-center justify-center transition-all",
        isLandscape 
          ? "flex-col gap-1 px-4 py-3 min-w-[80px]"
          : "gap-3 px-6 py-4",
        isActive 
          ? "text-blue-600 bg-blue-50" 
          : "text-gray-600 hover:text-gray-900 hover:bg-gray-50",
        "rounded-lg touch-manipulation"
      )}
    >
      <div className="relative">
        <Icon className={cn(
          isLandscape ? "w-6 h-6" : "w-5 h-5"
        )} />
        {badge !== undefined && badge > 0 && (
          <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] flex items-center justify-center bg-red-500 text-white text-xs font-medium rounded-full px-1">
            {badge > 99 ? '99+' : badge}
          </span>
        )}
      </div>
      {showLabel && (
        <span className={cn(
          "font-medium",
          isLandscape ? "text-xs" : "text-sm"
        )}>
          {label}
        </span>
      )}
    </Link>
  )
}