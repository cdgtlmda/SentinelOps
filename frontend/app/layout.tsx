import type { Metadata } from "next";
import dynamic from "next/dynamic";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Navigation } from "@/components/navigation";
import { ThemeProvider } from "@/components/theme-provider";
import { LayoutWrapper } from "@/components/layout-wrapper";
import { AlertProvider } from "@/components/alerts";
import { SkipNavigation, LandmarkNavigator } from "@/components/accessibility";
import { AccessibilityAudit } from "@/components/accessibility/accessibility-audit";
import { ClientInit } from "@/components/client-init";
import { ToastProvider } from "@/hooks/use-toast";
import { PerformanceMonitor } from "@/components/performance/performance-monitor";

import { WebSocketWrapper } from "@/components/websocket-wrapper";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: 'swap',
  preload: true,
  fallback: ['system-ui', '-apple-system', 'sans-serif'],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: 'swap',
  preload: true,
  fallback: ['ui-monospace', 'monospace'],
});

export const metadata: Metadata = {
  title: "SentinelOps - AI-Powered Incident Response",
  description: "Automated incident response and management platform",
  manifest: "/manifest.json",
  themeColor: "#09090b",
  viewport: {
    width: "device-width",
    initialScale: 1,
    maximumScale: 5,
    userScalable: true,
    viewportFit: "cover",
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "SentinelOps",
  },
  formatDetection: {
    telephone: false,
  },
  icons: {
    icon: [
      { url: "/icon-192x192.svg", sizes: "192x192", type: "image/svg+xml" },
      { url: "/icon-512x512.svg", sizes: "512x512", type: "image/svg+xml" },
    ],
    apple: [
      { url: "/icon-180x180.svg", sizes: "180x180", type: "image/svg+xml" },
    ],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="dns-prefetch" href="https://fonts.googleapis.com" />
        <link rel="dns-prefetch" href="https://fonts.gstatic.com" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100`}
      >
        <ThemeProvider>
          <ToastProvider>
            <WebSocketWrapper>
              <AlertProvider>
                <ClientInit />
                <PerformanceMonitor />
                <SkipNavigation />
                <Navigation />
                <LayoutWrapper>
                  <main id="main-content" tabIndex={-1}>
                    {children}
                  </main>
                </LayoutWrapper>
                {process.env.NODE_ENV === 'development' && (
                  <>
                    <LandmarkNavigator showVisualIndicator={true} />
                    <AccessibilityAudit />
                  </>
                )}
              </AlertProvider>
            </WebSocketWrapper>
          </ToastProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
