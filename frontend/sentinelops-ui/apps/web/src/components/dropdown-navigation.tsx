"use client";

import { useState, useEffect, useRef } from "react";
import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown } from "lucide-react";

interface NavItem {
  id: number;
  label: string;
  subMenus?: {
    title: string;
    items: {
      label: string;
      description: string;
      icon: React.ElementType;
      href?: string;
    }[];
  }[];
  link?: string;
}

interface Props {
  navItems: NavItem[];
}

export function DropdownNavigation({ navItems }: Props) {
  const [openMenu, setOpenMenu] = React.useState<string | null>(null);
  const [isHover, setIsHover] = useState<number | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const handleHover = (menuLabel: string | null) => {
    setOpenMenu(menuLabel);
  };

  const handleClick = (menuLabel: string) => {
    setOpenMenu(openMenu === menuLabel ? null : menuLabel);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpenMenu(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  
  return (
    <div className="relative" ref={dropdownRef}>
      <ul className="relative flex items-center space-x-2">
          {navItems.map((navItem) => (
            <li
              key={navItem.label}
              className="relative"
              onMouseEnter={() => handleHover(navItem.label)}
              onMouseLeave={() => handleHover(null)}
            >
              {navItem.link ? (
                <a
                  href={navItem.link}
                  className="text-sm py-1.5 px-4 flex cursor-pointer group transition-colors duration-300 items-center justify-center gap-1 text-muted-foreground hover:text-foreground relative"
                  onMouseEnter={() => setIsHover(navItem.id)}
                  onMouseLeave={() => setIsHover(null)}
                >
                  <span>{navItem.label}</span>
                  {(isHover === navItem.id || openMenu === navItem.label) && (
                    <motion.div
                      layoutId="hover-bg"
                      className="absolute inset-0 size-full bg-primary/10"
                      style={{ borderRadius: 99 }}
                    />
                  )}
                </a>
              ) : (
                <button
                  className="text-sm py-1.5 px-4 flex cursor-pointer group transition-colors duration-300 items-center justify-center gap-1 text-muted-foreground hover:text-foreground relative"
                  onMouseEnter={() => setIsHover(navItem.id)}
                  onMouseLeave={() => setIsHover(null)}
                  onClick={() => handleClick(navItem.label)}
                >
                  <span>{navItem.label}</span>
                  {navItem.subMenus && (
                    <ChevronDown
                      className={`h-4 w-4 group-hover:rotate-180 duration-300 transition-transform
                        ${openMenu === navItem.label ? "rotate-180" : ""}`}
                    />
                  )}
                  {(isHover === navItem.id || openMenu === navItem.label) && (
                    <motion.div
                      layoutId="hover-bg"
                      className="absolute inset-0 size-full bg-primary/10"
                      style={{ borderRadius: 99 }}
                    />
                  )}
                </button>
              )}

              <AnimatePresence>
                {openMenu === navItem.label && navItem.subMenus && (
                  <div className="w-auto absolute left-0 top-full pt-2 z-[100]">
                    <motion.div
                      className="bg-background border border-border shadow-xl p-6 w-max relative"
                      style={{ borderRadius: 16 }}
                      layoutId="menu"
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ duration: 0.2 }}
                    >
                      <div className="w-fit shrink-0 flex space-x-12 overflow-hidden">
                        {navItem.subMenus.map((sub) => (
                          <motion.div layout className="w-full min-w-[240px]" key={sub.title}>
                            <h3 className="mb-4 text-sm font-semibold capitalize text-foreground border-b border-border pb-2">
                              {sub.title}
                            </h3>
                            <ul className="space-y-4">
                              {sub.items.map((item) => {
                                const Icon = item.icon;
                                return (
                                  <li key={item.label}>
                                    <a
                                      href={item.href || "#"}
                                      className="flex items-start space-x-3 group p-2 rounded-lg hover:bg-accent/50 transition-colors duration-200"
                                    >
                                      <div className="border border-border text-foreground bg-background rounded-lg flex items-center justify-center size-10 shrink-0 group-hover:bg-primary group-hover:text-primary-foreground group-hover:border-primary transition-colors duration-200">
                                        <Icon className="h-5 w-5 flex-none" />
                                      </div>
                                      <div className="leading-5 w-max">
                                        <p className="text-sm font-medium text-foreground shrink-0 group-hover:text-primary transition-colors duration-200">
                                          {item.label}
                                        </p>
                                        <p className="text-xs text-muted-foreground shrink-0 group-hover:text-foreground transition-colors duration-200 mt-1">
                                          {item.description}
                                        </p>
                                      </div>
                                    </a>
                                  </li>
                                );
                              })}
                            </ul>
                          </motion.div>
                        ))}
                      </div>
                    </motion.div>
                  </div>
                )}
              </AnimatePresence>
            </li>
          ))}
        </ul>
    </div>
  );
} 