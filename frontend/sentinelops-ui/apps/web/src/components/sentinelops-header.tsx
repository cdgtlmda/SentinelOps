"use client";

import { DropdownNavigation } from "./dropdown-navigation";
import { Shield } from "lucide-react";
import Link from "next/link";
import { AnimatedText } from "@/components/animated-text";

export function SentinelOpsHeader() {
  const NAV_ITEMS = [
    {
      id: 1,
      label: "Pricing",
      link: "/pricing",
    },
  ];

  return (
    <header className="absolute top-0 w-full flex items-center justify-between p-4 z-50 bg-background/80 backdrop-blur-sm border-b border-border/50">
      <Link href="/" className="flex items-center gap-2">
        <div className="w-8 h-8 bg-primary rounded-md flex items-center justify-center">
          <Shield className="w-5 h-5 text-primary-foreground" />
        </div>
        <span className="font-departure text-lg" style={{ fontFamily: 'var(--font-departure-mono), monospace' }}>
          <AnimatedText text="SentinelOps" />
        </span>
      </Link>

      <nav className="hidden md:block">
        <div className="flex items-center space-x-2">
          <Link href="/overview" className="text-sm py-1.5 px-4 flex cursor-pointer group transition-colors duration-300 items-center justify-center gap-1 text-muted-foreground hover:text-foreground relative rounded-full hover:bg-primary/10">
            Overview
          </Link>
          <Link href="/build" className="text-sm py-1.5 px-4 flex cursor-pointer group transition-colors duration-300 items-center justify-center gap-1 text-muted-foreground hover:text-foreground relative rounded-full hover:bg-primary/10">
            The Build
          </Link>
          <DropdownNavigation navItems={NAV_ITEMS} />
          <Link href="/demos" className="text-sm py-1.5 px-4 flex cursor-pointer group transition-colors duration-300 items-center justify-center gap-1 text-muted-foreground hover:text-foreground relative rounded-full hover:bg-primary/10">
            Demos
          </Link>
          <Link href="/try-dashboard" className="text-sm py-1.5 px-4 flex cursor-pointer group transition-colors duration-300 items-center justify-center gap-1 text-muted-foreground hover:text-foreground relative rounded-full hover:bg-primary/10">
            Try Dashboard
          </Link>
        </div>
      </nav>

      <div className="flex items-center gap-2">
        <Link
          href="/about"
          className="text-sm px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-full font-medium transition-all duration-300"
        >
          About the Dev
        </Link>
      </div>
    </header>
  );
} 