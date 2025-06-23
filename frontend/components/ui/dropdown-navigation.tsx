"use client"

import { useState, useRef, useEffect } from "react"
import Link from "next/link"
import { ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  Shield,
  AlertTriangle,
  Bot,
  BarChart3,
  Eye,
  Zap,
  Brain,
  BookOpen,
  FileText,
  Newspaper,
  Users,
  Settings,
} from "lucide-react"

interface NavItem {
  label: string
  description?: string
  icon?: string
  link?: string
}

interface SubMenu {
  title: string
  items: NavItem[]
}

interface NavMenuItem {
  id: number
  label: string
  link?: string
  subMenus?: SubMenu[]
}

interface DropdownNavigationProps {
  navItems: NavMenuItem[]
}

const IconMap = {
  Shield,
  AlertTriangle,
  Bot,
  BarChart3,
  Eye,
  Zap,
  Brain,
  BookOpen,
  FileText,
  Newspaper,
  Users,
  Settings,
}

export function DropdownNavigation({ navItems }: DropdownNavigationProps) {
  const [activeDropdown, setActiveDropdown] = useState<number | null>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  
  console.log('DropdownNavigation rendered with items:', navItems.map(item => item.label))

  const handleMouseEnter = (id: number) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setActiveDropdown(id)
  }

  const handleMouseLeave = () => {
    timeoutRef.current = setTimeout(() => {
      setActiveDropdown(null)
    }, 150) // Small delay to allow moving to dropdown
  }

  const handleDropdownMouseEnter = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
  }

  const handleDropdownMouseLeave = () => {
    setActiveDropdown(null)
  }

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return (
    <nav className="hidden md:flex items-center gap-8">
      {navItems.map((item) => (
        <div
          key={item.id}
          className="relative"
          onMouseEnter={() => handleMouseEnter(item.id)}
          onMouseLeave={handleMouseLeave}
        >
          {item.link ? (
            <Link
              href={item.link}
              className="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition-colors flex items-center gap-1 py-2"
            >
              {item.label}
            </Link>
          ) : (
            <button className="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition-colors flex items-center gap-1 py-2">
              {item.label}
              {item.subMenus && (
                <ChevronDown 
                  className={cn(
                    "w-4 h-4 transition-transform duration-200",
                    activeDropdown === item.id && "rotate-180"
                  )} 
                />
              )}
            </button>
          )}

          {/* Dropdown Menu */}
          {item.subMenus && activeDropdown === item.id && (
            <div 
              className="absolute top-full left-0 mt-1 w-[600px] bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl z-50 opacity-100 transform translate-y-0 transition-all duration-200"
              onMouseEnter={handleDropdownMouseEnter}
              onMouseLeave={handleDropdownMouseLeave}
            >
              {/* Small triangle pointer */}
              <div className="absolute -top-1 left-8 w-2 h-2 bg-white dark:bg-gray-800 border-l border-t border-gray-200 dark:border-gray-700 transform rotate-45"></div>
              
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                  {item.subMenus.map((subMenu, subIndex) => (
                    <div key={subIndex}>
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-4 text-sm uppercase tracking-wide">
                        {subMenu.title}
                      </h3>
                      <ul className="space-y-3">
                        {subMenu.items.map((subItem, itemIndex) => {
                          const Icon = subItem.icon ? IconMap[subItem.icon as keyof typeof IconMap] : null
                          return (
                            <li key={itemIndex}>
                              <Link
                                href={subItem.link || "#"}
                                className="group flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200"
                                onClick={() => setActiveDropdown(null)}
                              >
                                {Icon && (
                                  <div className="flex-shrink-0 w-8 h-8 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center group-hover:bg-blue-500/10 dark:group-hover:bg-blue-400/10 transition-colors duration-200">
                                    <Icon className="w-4 h-4 text-gray-600 dark:text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors duration-200" />
                                  </div>
                                )}
                                <div className="min-w-0">
                                  <div className="font-medium text-gray-900 dark:text-gray-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors duration-200">
                                    {subItem.label}
                                  </div>
                                  {subItem.description && (
                                    <div className="text-sm text-gray-500 dark:text-gray-400 mt-1 leading-relaxed">{subItem.description}</div>
                                  )}
                                </div>
                              </Link>
                            </li>
                          )
                        })}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </nav>
  )
}