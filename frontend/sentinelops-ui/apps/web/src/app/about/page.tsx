"use client";

import Link from "next/link";
import { Shield, Github, Youtube, BookOpen, MessageCircle, ArrowRight, Zap, Users, Brain, Activity, Target } from "lucide-react";
import { motion } from "framer-motion";
import { Component as ProfileCard } from "@/components/ui/profile-card";

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-4">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 bg-green-500/10 text-green-400 px-4 py-2 rounded-full text-sm font-medium mb-6 border border-green-500/20">
              <Shield className="w-4 h-4" />
              About the Developer
            </div>
            <h1 className="text-4xl md:text-6xl font-bold mb-6 tracking-tight">
              Hi, I'm <span className="text-green-400">Cadence</span>
            </h1>
            <div className="w-24 h-1 bg-green-400 mx-auto mb-8 rounded-full" />
          </motion.div>

          {/* Main Content */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="prose prose-lg prose-invert max-w-none"
          >
            <div className="bg-white/5 border border-white/10 rounded-xl p-8 backdrop-blur-sm space-y-6 text-gray-300 leading-relaxed">
              <p>
                I've always been fascinated by the intersection of cybersecurity and storytelling—long before I ever wrote my first line of code, I was deep in DarkNet Diaries, fascinated by real-world exploits featured on Zerodium, and engrossed in books like Ghost in the Wires and Countdown to Zero Day. Those weren't just hacker stories—they were real accounts of high-stakes systems being broken into, defended, and rebuilt. They taught me that security isn't just about defense—it's about visibility, precision, and resilience.
              </p>

              <p>
                In 2025, I set out to challenge myself in a big way. I joined the Google Agent Development Kit Hackathon with a simple but bold idea: what if a solo builder could automate an entire incident response workflow using AI agents? Not just a script or a chatbot—but a fully orchestrated, cloud-native, multi-agent security team.
              </p>

              <p className="text-green-400 font-semibold text-xl">
                That's where SentinelOps began.
              </p>

              <p>
                This project is my submission to the Google ADK Hackathon—a 28-day intensive development effort to build an autonomous, multi-agent cloud security response platform using the Agent Development Kit and Google Cloud. SentinelOps isn't just a concept; it's a functioning system with real integration into BigQuery, Cloud Functions, Pub/Sub, and Gemini-powered reasoning.
              </p>
            </div>
          </motion.div>

          {/* Agent Architecture */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
            className="mt-12"
          >
            <h2 className="text-2xl font-bold text-white mb-8 text-center">Every agent in SentinelOps is designed with a specific job:</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[
                {
                  icon: Target,
                  title: "Detection Agent",
                  description: "Scans logs for suspicious behavior.",
                  color: "text-red-400"
                },
                {
                  icon: Brain,
                  title: "Analysis Agent",
                  description: "Uses Gemini models to understand impact and root cause.",
                  color: "text-purple-400"
                },
                {
                  icon: Zap,
                  title: "Remediation Agent",
                  description: "Acts—with caution and auditability.",
                  color: "text-yellow-400"
                },
                {
                  icon: Users,
                  title: "Communication Agent",
                  description: "Keeps stakeholders informed.",
                  color: "text-blue-400"
                },
                {
                  icon: Activity,
                  title: "Orchestrator Agent",
                  description: "Ties it all together.",
                  color: "text-green-400"
                }
              ].map((agent, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 + index * 0.1, duration: 0.5 }}
                  className="bg-white/5 border border-white/10 rounded-lg p-6 backdrop-blur-sm hover:bg-white/10 transition-colors"
                >
                  <div className={`w-12 h-12 ${agent.color} bg-current/10 rounded-lg flex items-center justify-center mb-4`}>
                    <agent.icon className={`w-6 h-6 ${agent.color}`} />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">{agent.title}</h3>
                  <p className="text-gray-400 text-sm">{agent.description}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Development Story */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.5 }}
            className="mt-12"
          >
            <div className="bg-white/5 border border-white/10 rounded-xl p-8 backdrop-blur-sm space-y-6 text-gray-300 leading-relaxed">
              <p>
                As a solo engineer, this build was intense. But I leaned into the constraints—focusing on modularity, explainability, and GCP-native primitives. I wrote 100% type-safe code. I documented every interface. The end result is a security response system that mirrors how real teams operate, but without the bottlenecks.
              </p>

              <p>
                Most importantly, SentinelOps shows what's possible when generative AI and multi-agent systems are applied to real enterprise problems, not just demos.
              </p>

              <p>
                If you're curious about how it works, check out the architectural deep-dive, agent walkthroughs, and incident response simulations on the rest of this site. I've also included a section comparing SentinelOps to legacy SIEM/SOAR tools—because this isn't just about building a hackathon MVP. It's about asking what the next 5 years of security automation should actually look like.
              </p>
            </div>
          </motion.div>

          {/* Closing */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8, duration: 0.5 }}
            className="mt-12 text-center"
          >
            <p className="text-xl text-gray-300 mb-8">
              Thanks for stopping by.
            </p>
            <p className="text-2xl font-bold text-green-400 mb-8">
              — Cadence
            </p>
          </motion.div>

          {/* Profile Card Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.0, duration: 0.5 }}
            className="mt-16"
          >
            <ProfileCard />
          </motion.div>


        </div>
      </section>
    </div>
  );
} 