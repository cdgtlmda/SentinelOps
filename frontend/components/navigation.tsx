"use client"

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useUIStore } from '@/store'
import { Home, AlertCircle, Settings, Menu, X, Moon, Sun, Bot, BarChart3, Table, Accessibility, Smartphone, Github } from 'lucide-react'
import { NotificationCenter } from '@/components/alerts'
import { useAlertContext } from '@/components/alerts'
import { useResponsive } from '@/hooks/use-responsive'
import { MobileNavigation } from '@/components/mobile'
import { DropdownNavigation } from '@/components/ui/dropdown-navigation'
import { Button } from '@/components/ui/button'

export function Navigation() {
  const pathname = usePathname()
  const { isSidebarOpen, toggleSidebar, theme, setTheme } = useUIStore()
  const { alerts, markAsRead, markAllAsRead, clearAll, dismissAlert } = useAlertContext()
  const { isMobile } = useResponsive()
  
  // Debug log
  console.log('Navigation component loaded - SentinelOps Frontend')
  
  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: Home },
    { href: '/incidents', label: 'Incidents (Old)', icon: AlertCircle },
    { href: '/incidents-dashboard', label: 'Incidents', icon: AlertCircle },
    { href: '/agents', label: 'Agents', icon: Bot },
    { href: '/analytics', label: 'Analytics', icon: BarChart3 },
    { href: '/tables', label: 'Data Tables', icon: Table },
    { href: '/alerts-demo', label: 'Alerts Demo', icon: AlertCircle },
    { href: '/accessibility', label: 'Accessibility', icon: Accessibility },
    { href: '/mobile-demo', label: 'Mobile Demo', icon: Smartphone },
    { href: '/settings', label: 'Settings', icon: Settings },
  ]

  const DROPDOWN_NAV_ITEMS = [
    {
      id: 1,
      label: "Platform",
      subMenus: [
        {
          title: "Core Features",
          items: [
            {
              label: "Autonomous Detection",
              description: "AI-powered threat identification",
              icon: "Eye",
              link: "/platform/detection",
            },
            {
              label: "Auto Remediation",
              description: "Zero-touch incident response",
              icon: "Zap",
              link: "/platform/remediation",
            },
            {
              label: "Multi-Agent System",
              description: "Coordinated security agents",
              icon: "Bot",
              link: "/platform/agents",
            },
          ],
        },
        {
          title: "Intelligence",
          items: [
            {
              label: "Threat Analysis",
              description: "Gemini-powered insights",
              icon: "Brain",
              link: "/platform/analysis",
            },
            {
              label: "Risk Assessment",
              description: "Real-time security scoring",
              icon: "BarChart3",
              link: "/platform/risk",
            },
            {
              label: "Compliance",
              description: "Automated audit trails",
              icon: "Shield",
              link: "/platform/compliance",
            },
          ],
        },
        {
          title: "Integrations",
          items: [
            {
              label: "Google Cloud",
              description: "Native GCP integration",
              icon: "Settings",
              link: "/platform/gcp",
            },
            {
              label: "BigQuery",
              description: "Security log analysis",
              icon: "BarChart3",
              link: "/platform/bigquery",
            },
            {
              label: "Cloud Functions",
              description: "Serverless remediation",
              icon: "Zap",
              link: "/platform/functions",
            },
          ],
        },
      ],
    },
    {
      id: 2,
      label: "Solutions",
      subMenus: [
        {
          title: "Use Cases",
          items: [
            {
              label: "Cloud Security",
              description: "Comprehensive cloud protection",
              icon: "Shield",
              link: "/solutions/cloud-security",
            },
            {
              label: "Incident Response",
              description: "Automated threat remediation",
              icon: "AlertTriangle",
              link: "/solutions/incident-response",
            },
            {
              label: "Compliance Monitoring",
              description: "Continuous compliance checks",
              icon: "FileText",
              link: "/solutions/compliance",
            },
            {
              label: "Security Operations",
              description: "24/7 autonomous monitoring",
              icon: "Eye",
              link: "/solutions/secops",
            },
          ],
        },
        {
          title: "Industries",
          items: [
            {
              label: "Enterprise",
              description: "Large-scale security automation",
              icon: "Users",
              link: "/solutions/enterprise",
            },
            {
              label: "Financial Services",
              description: "Regulatory compliance focus",
              icon: "Shield",
              link: "/solutions/financial",
            },
            {
              label: "Healthcare",
              description: "HIPAA-compliant security",
              icon: "FileText",
              link: "/solutions/healthcare",
            },
          ],
        },
      ],
    },
    {
      id: 3,
      label: "Resources",
      subMenus: [
        {
          title: "Documentation",
          items: [
            {
              label: "Quick Start",
              description: "Deploy in 5 minutes",
              icon: "BookOpen",
              link: "/docs/quickstart",
            },
            {
              label: "API Reference",
              description: "Complete API documentation",
              icon: "FileText",
              link: "/docs/api",
            },
            {
              label: "Architecture Guide",
              description: "System design and patterns",
              icon: "Settings",
              link: "/docs/architecture",
            },
            {
              label: "Best Practices",
              description: "Security implementation guide",
              icon: "Shield",
              link: "/docs/best-practices",
            },
          ],
        },
        {
          title: "Community",
          items: [
            {
              label: "Case Studies",
              description: "Real-world implementations",
              icon: "Newspaper",
              link: "/resources/case-studies",
            },
            {
              label: "Blog",
              description: "Latest security insights",
              icon: "FileText",
              link: "/resources/blog",
            },
            {
              label: "Security Research",
              description: "Threat intelligence reports",
              icon: "Brain",
              link: "/resources/research",
            },
          ],
        },
      ],
    },
    {
      id: 4,
      label: "Enterprise",
      link: "/enterprise",
    },
    {
      id: 5,
      label: "Docs",
      link: "/docs",
    },
    {
      id: 6,
      label: "Pricing",
      link: "/pricing",
    },
  ]
  
  const handleThemeToggle = () => {
    if (theme === 'light') setTheme('dark')
    else if (theme === 'dark') setTheme('system')
    else setTheme('light')
  }
  
  // Use mobile navigation on small screens
  if (isMobile) {
    const unreadCount = alerts.filter(alert => !alert.isRead).length
    return <MobileNavigation notifications={unreadCount} />
  }
  
  return (
    <>
      {/* Top Navigation Bar */}
      <header 
        role="banner"
        id="header"
        className="bg-white dark:bg-gray-800 border-b dark:border-gray-700 h-16 fixed top-0 left-0 right-0 z-50"
      >
        <div className="flex items-center justify-between h-full px-4">
          <div className="flex items-center gap-4">
            <button
              onClick={toggleSidebar}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              aria-label={isSidebarOpen ? "Close navigation menu" : "Open navigation menu"}
              aria-expanded={isSidebarOpen}
              aria-controls="navigation-sidebar"
            >
              {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
            <Link href="/" className="flex items-center gap-3">
              <span className="text-xl font-bold">SentinelOps</span>
            </Link>

          </div>

          {/* Center Navigation */}
          <div className="flex items-center gap-8 flex-1 justify-center">
            <DropdownNavigation navItems={DROPDOWN_NAV_ITEMS} />
          </div>

          {/* Right Side Actions */}
          <div className="hidden lg:flex items-center gap-4">
            <Link href="/dashboard" className="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition-colors">
              Dashboard
            </Link>
            <Link href="https://github.com" className="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
              <Github className="w-5 h-5" />
            </Link>
            <Button
              variant="outline"
              size="sm"
              className="font-medium"
            >
              Contact
            </Button>
          </div>
          
          <div className="flex items-center gap-2">
            <NotificationCenter
              alerts={alerts}
              onMarkAsRead={markAsRead}
              onMarkAllAsRead={markAllAsRead}
              onClearAll={clearAll}
              onDismiss={dismissAlert}
            />
            
            <button
              onClick={handleThemeToggle}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              aria-label={`Current theme: ${theme}. Click to change theme`}
            >
              {theme === 'light' ? <Sun size={20} aria-hidden="true" /> : 
               theme === 'dark' ? <Moon size={20} aria-hidden="true" /> :
               <div className="w-5 h-5 rounded-full bg-gradient-to-r from-gray-400 to-gray-600" aria-hidden="true" />}
            </button>
          </div>
        </div>
      </header>
      
      {/* Sidebar Navigation */}
      <aside 
        id="navigation-sidebar"
        role="navigation"
        aria-label="Main navigation"
        className={`fixed left-0 top-16 bottom-0 w-64 lg:w-64 md:w-56 bg-white dark:bg-gray-800 border-r dark:border-gray-700 transition-transform ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } z-10 lg:translate-x-0`}
      >
        <nav id="navigation" className="p-4">
          <ul className="space-y-2" role="list">
            {navItems.map(({ href, label, icon: Icon }) => {
              const isActive = pathname === href
              return (
                <li key={href}>
                  <Link
                    href={href}
                    className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <Icon size={20} aria-hidden="true" />
                    <span>{label}</span>
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>
      </aside>
      
    </>
  )
}