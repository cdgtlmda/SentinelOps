import "@v1/ui/globals.css";
import { Footer } from "@/components/ui/footer-section";
import { SentinelOpsHeader } from "@/components/sentinelops-header";
import { Provider as AnalyticsProvider } from "@v1/analytics/client";
import { cn } from "@v1/ui/cn";
import { GeistMono } from "geist/font/mono";
import { GeistSans } from "geist/font/sans";
import type { Metadata } from "next";
import localFont from "next/font/local";

const DepartureMono = localFont({
  src: "../fonts/DepartureMono-Regular.woff2",
  variable: "--font-departure-mono",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://sentinelops.com"),
  title: "SentinelOps - Advanced Security & Monitoring Platform",
  description:
    "Comprehensive security monitoring and threat detection platform for modern enterprises. Real-time alerts, AI-powered analysis, and automated incident response.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={cn(
          `${DepartureMono.variable} ${GeistSans.variable} ${GeistMono.variable}`,
          "antialiased dark font-sans bg-background text-foreground",
        )}
        suppressHydrationWarning
      >
        <SentinelOpsHeader />
        {children}
        <Footer />

        <AnalyticsProvider />
      </body>
    </html>
  );
}
