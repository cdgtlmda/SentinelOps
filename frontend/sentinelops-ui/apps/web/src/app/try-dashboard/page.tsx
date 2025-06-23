"use client";

import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { 
  Shield,
  ArrowRight,
  Activity,
  CheckCircle,
  Zap,
  Brain,
  BarChart3
} from 'lucide-react';
import { SentinelOpsDashboardDemo } from "@/components/sentinelops-dashboard-demo";

export default function TryDashboardPage() {
  return (
    <div className="min-h-screen bg-black text-green-400">
      {/* Hero Section */}
      <motion.section 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="container px-4 pt-40 pb-12"
      >
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-white/10 text-green-400 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Activity className="w-4 h-4" />
            Interactive Demo Environment
          </div>
          <h1 className="mb-6 tracking-tight text-white">
            Try SentinelOps
            <span className="block text-green-400">Dashboard</span>
          </h1>
          <p className="text-lg md:text-xl text-gray-400 mb-8 max-w-4xl mx-auto leading-relaxed">
            Experience the power of our AI-driven security operations center. Navigate through different views 
            to see how our <span className="text-emerald-400">5 specialized agents</span> work together to protect your organization.
          </p>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-gray-400 mb-8">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span>Live Demo Environment</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
              <span>Real-time Simulations</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
              <span>Interactive Components</span>
            </div>
          </div>
        </div>
      </motion.section>

      {/* Dashboard Demo */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="container px-4 mb-12"
      >
        <div className="max-w-7xl mx-auto">
          <div className="bg-black/50 border border-white/10 rounded-xl p-8 backdrop-blur-sm">
            <SentinelOpsDashboardDemo />
          </div>
        </div>
      </motion.section>

      {/* Features Section */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="container px-4 mb-12"
      >
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-semibold text-green-400 mb-4">
              Dashboard Features
            </h2>
            <p className="text-gray-400 max-w-3xl mx-auto">
              Explore the comprehensive capabilities of our multi-agent security operations platform.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-black/50 border border-white/10 rounded-xl p-6 backdrop-blur-sm"
            >
              <div className="w-12 h-12 bg-blue-500/10 border border-blue-500/20 rounded-lg flex items-center justify-center mb-4">
                <Activity className="w-6 h-6 text-blue-400" />
              </div>
              <h3 className="text-lg font-semibold text-green-400 mb-2">Real-time Monitoring</h3>
              <p className="text-gray-400 text-sm">
                Monitor threats, system health, and agent performance in real-time with live updates.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-black/50 border border-white/10 rounded-xl p-6 backdrop-blur-sm"
            >
              <div className="w-12 h-12 bg-green-500/10 border border-green-500/20 rounded-lg flex items-center justify-center mb-4">
                <Zap className="w-6 h-6 text-green-400" />
              </div>
              <h3 className="text-lg font-semibold text-green-400 mb-2">AI Agent Orchestration</h3>
              <p className="text-gray-400 text-sm">
                Watch our 5 specialized AI agents collaborate to detect, analyze, and remediate threats.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-black/50 border border-white/10 rounded-xl p-6 backdrop-blur-sm"
            >
              <div className="w-12 h-12 bg-purple-500/10 border border-purple-500/20 rounded-lg flex items-center justify-center mb-4">
                <BarChart3 className="w-6 h-6 text-purple-400" />
              </div>
              <h3 className="text-lg font-semibold text-green-400 mb-2">Advanced Analytics</h3>
              <p className="text-gray-400 text-sm">
                Gain insights with comprehensive analytics and performance metrics across all security operations.
              </p>
            </motion.div>
          </div>
        </div>
      </motion.section>

      {/* Early Access CTA */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="container px-4 pb-20"
      >
        <div className="max-w-4xl mx-auto">
          <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 rounded-2xl p-8 text-center backdrop-blur-sm">
            <div className="flex items-center justify-center gap-2 mb-4">
              <Shield className="w-6 h-6 text-blue-400" />
              <h2 className="text-3xl font-bold text-green-400">Ready to Secure Your Organization?</h2>
            </div>
            <p className="text-xl text-gray-300 mb-6 max-w-2xl mx-auto">
              Join our early access program and be among the first to experience the future of autonomous security operations.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
              <Link
                href="mailto:cdgtlmda@pm.me?subject=SentinelOps%20Early%20Access%20Request"
                className="inline-flex items-center gap-2 bg-white text-black px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
              >
                Request Early Access
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/demos"
                className="inline-flex items-center gap-2 border border-white/20 px-8 py-3 rounded-lg font-semibold hover:bg-white/10 transition-colors text-white"
              >
                View All Demos
              </Link>
            </div>
            <div className="flex items-center justify-center gap-6 text-sm text-gray-400">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span>Expected availability: Q4 2025</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span>No credit card required</span>
              </div>
            </div>
          </div>
        </div>
      </motion.section>
    </div>
  );
} 