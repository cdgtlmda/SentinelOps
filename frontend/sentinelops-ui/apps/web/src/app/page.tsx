"use client";

import { motion } from 'framer-motion';
import Link from 'next/link';
import { 
  Shield, 
  Zap, 
  Brain, 
  ArrowRight, 
  Play, 
  CheckCircle,
  Activity,
  AlertTriangle,
  Users,
  Target
} from 'lucide-react';
import { AnimatedText } from "@/components/animated-text";
import { CopyText } from "@/components/copy-text";

export default function Page() {
  return (
    <div className="h-screen w-screen flex flex-col items-center justify-center relative overflow-hidden" style={{ fontFamily: 'var(--font-departure-mono), monospace' }}>
      <div className="absolute -top-[118px] inset-0 bg-[linear-gradient(to_right,#222_1px,transparent_1px),linear-gradient(to_bottom,#222_1px,transparent_1px)] bg-[size:4.5rem_2rem] -z-10 [transform:perspective(1000px)_rotateX(-63deg)] h-[80%] pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-t from-background to-transparent pointer-events-none -z-10" />
      
      <h1 className="font-departure text-[40px] md:text-[84px] relative z-10 text-center h-[120px] md:h-auto leading-tight">
        <AnimatedText text="Experience SentinelOps in Action" />
      </h1>

      <p className="relative z-10 text-center max-w-[80%] mt-0 md:mt-4">
        Built on Google's Agent Development Kit (ADK), our multi-agent platform orchestrates five specialized AI agents for autonomous cloud security operations with sub-30 second threat detection and intelligent incident response.
      </p>

      <div className="mt-10 mb-8 flex flex-col sm:flex-row gap-4 items-center">
        <Link
          href="/try-dashboard"
          className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl"
        >
          <Play className="w-4 h-4" />
          Try Dashboard Demo
        </Link>
        <CopyText value="gh repo clone cdgtlmda/SentinelOps" />
      </div>



      <div className="absolute -bottom-[280px] inset-0 bg-[linear-gradient(to_right,#222_1px,transparent_1px),linear-gradient(to_bottom,#222_1px,transparent_1px)] bg-[size:4.5rem_2rem] -z-10 [transform:perspective(560px)_rotateX(63deg)] pointer-events-none" />
      <div className="absolute w-full bottom-[100px] h-1/2 bg-gradient-to-b from-background to-transparent pointer-events-none -z-10" />
    </div>
  );
}