'use client'

import React, { useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Home,
  AlertCircle,
  MessageSquare,
  Activity,
  Menu,
  X,
  Bell,
  ChevronRight,
  Settings,
  Users,
  Shield,
  BarChart3,
  Workflow
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'

interface NavItem {
  id: string
  label: string
  icon: React.ElementType
  href: string
  badge?: number
  isPrimary?: boolean
}

const navigationItems: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: Home, href: '/dashboard', isPrimary: true },
  { id: 'incidents', label: 'Incidents', icon: AlertCircle, href: '/incidents', badge: 5, isPrimary: true },
  { id: 'chat', label: 'AI Chat', icon: MessageSquare, href: '/demo/ai-chat', isPrimary: true },
  { id: 'activity', label: 'Activity', icon: Activity, href: '/incidents-dashboard', isPrimary: true },
  { id: 'agents', label: 'Agents', icon: Shield, href: '/agents' },
  { id: 'workflows', label: 'Workflows', icon: Workflow, href: '/workflows' },
  { id: 'analytics', label: 'Analytics', icon: BarChart3, href: '/analytics' },
  { id: 'collaboration', label: 'Collaboration', icon: Users, href: '/collaboration' },
  { id: 'settings', label: 'Settings', icon: Settings, href: '/settings' }
]

interface MobileNavigationProps {
  notifications?: number
  onSwipeLeft?: () => void
  onSwipeRight?: () => void
}

export function MobileNavigation({ 
  notifications = 0,
  onSwipeLeft,
  onSwipeRight 
}: MobileNavigationProps) {
  const router = useRouter()
  const pathname = usePathname()
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [touchStart, setTouchStart] = useState<number | null>(null)
  const [touchEnd, setTouchEnd] = useState<number | null>(null)

  const primaryItems = navigationItems.filter(item => item.isPrimary)
  const secondaryItems = navigationItems.filter(item => !item.isPrimary)

  const handleNavigation = (href: string) => {
    router.push(href)
    setIsMenuOpen(false)
  }

  // Handle swipe gestures
  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null)
    setTouchStart(e.targetTouches[0].clientX)
  }

  const handleTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX)
  }

  const handleTouchEnd = () => {
    if (!touchStart || !touchEnd) return
    
    const distance = touchStart - touchEnd
    const isLeftSwipe = distance > 50
    const isRightSwipe = distance < -50

    if (isLeftSwipe && onSwipeLeft) {
      onSwipeLeft()
    }
    if (isRightSwipe && onSwipeRight) {
      onSwipeRight()
    }
  }

  return (
    <>
      {/* Bottom Tab Navigation */}
      <motion.nav
        initial={{ y: 100 }}
        animate={{ y: 0 }}
        className="fixed bottom-0 left-0 right-0 z-50 bg-background border-t border-border safe-bottom"
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        <div className="flex items-center justify-around h-16 px-2">
          {primaryItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            
            return (
              <motion.button
                key={item.id}
                whileTap={{ scale: 0.95 }}
                onClick={() => handleNavigation(item.href)}
                className={cn(
                  "flex flex-col items-center justify-center flex-1 h-full px-2 py-2 relative",
                  "transition-colors duration-200",
                  isActive ? "text-primary" : "text-muted-foreground"
                )}
              >
                <div className="relative">
                  <Icon className="h-5 w-5" />
                  {item.badge && item.badge > 0 && (
                    <Badge 
                      variant="destructive" 
                      className="absolute -top-2 -right-2 h-4 w-4 p-0 flex items-center justify-center text-[10px]"
                    >
                      {item.badge}
                    </Badge>
                  )}
                </div>
                <span className="text-xs mt-1">{item.label}</span>
                {isActive && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute top-0 left-0 right-0 h-0.5 bg-primary"
                  />
                )}
              </motion.button>
            )
          })}
          
          {/* Menu Button */}
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={() => setIsMenuOpen(true)}
            className="flex flex-col items-center justify-center flex-1 h-full px-2 py-2 text-muted-foreground"
          >
            <div className="relative">
              <Menu className="h-5 w-5" />
              {notifications > 0 && (
                <Badge 
                  variant="destructive" 
                  className="absolute -top-2 -right-2 h-4 w-4 p-0 flex items-center justify-center text-[10px]"
                >
                  {notifications}
                </Badge>
              )}
            </div>
            <span className="text-xs mt-1">More</span>
          </motion.button>
        </div>
      </motion.nav>

      {/* Hamburger Menu Sheet */}
      <Sheet open={isMenuOpen} onOpenChange={setIsMenuOpen}>
        <SheetContent side="right" className="w-[300px] sm:w-[400px]">
          <SheetHeader>
            <SheetTitle>Menu</SheetTitle>
          </SheetHeader>
          
          <ScrollArea className="flex-1 mt-6">
            {/* Notifications */}
            {notifications > 0 && (
              <div className="mb-6">
                <Button
                  variant="outline"
                  className="w-full justify-between"
                  onClick={() => handleNavigation('/notifications')}
                >
                  <div className="flex items-center gap-2">
                    <Bell className="h-4 w-4" />
                    <span>Notifications</span>
                  </div>
                  <Badge variant="destructive">{notifications}</Badge>
                </Button>
              </div>
            )}

            {/* Secondary Navigation Items */}
            <div className="space-y-1">
              {secondaryItems.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href
                
                return (
                  <motion.button
                    key={item.id}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleNavigation(item.href)}
                    className={cn(
                      "w-full flex items-center justify-between px-4 py-3 rounded-lg",
                      "transition-colors duration-200",
                      isActive 
                        ? "bg-primary/10 text-primary" 
                        : "hover:bg-accent text-foreground"
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className="h-5 w-5" />
                      <span className="font-medium">{item.label}</span>
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  </motion.button>
                )
              })}
            </div>

            {/* App Version */}
            <div className="mt-8 pt-8 border-t border-border">
              <p className="text-xs text-muted-foreground text-center">
                SentinelOps v1.0.0
              </p>
            </div>
          </ScrollArea>
        </SheetContent>
      </Sheet>
    </>
  )
}

export default MobileNavigation