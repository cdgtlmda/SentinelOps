"use client";

import React from "react";
import Link from "next/link";
import { Check, X, ArrowRight, Shield, Building, Zap, Users, Phone, Mail, Clock, Globe, AlertTriangle, Database, Cpu, Network } from "lucide-react";
import { motion } from "framer-motion";
import { FaqSection } from "@/components/ui/faq";

export default function PricingPage() {
  const faqItems = [
    {
      question: "How do I get started with SentinelOps?",
      answer: "Contact our sales team to schedule a personalized demo and discuss your specific security requirements. We'll work with you to determine the best plan and implementation approach."
    },
    {
      question: "How does SentinelOps differ from traditional SIEMs?",
      answer: "Unlike traditional SIEMs that rely on rule-based detection, SentinelOps uses multi-agent AI orchestration with Google's Gemini for contextual threat analysis, providing 30x faster detection with 98% fewer false positives."
    },
    {
      question: "What's included in the Enterprise plan?",
      answer: "Enterprise includes unlimited agents, AI-powered analysis, 24/7 dedicated support, custom analytics, SSO & RBAC, unlimited integrations, and a dedicated Customer Success Manager with SLA guarantees."
    },
    {
      question: "Can I change plans at any time?",
      answer: "Absolutely. You can upgrade or downgrade your plan at any time through your dashboard. Changes take effect immediately, and we'll prorate any billing adjustments."
    },
    {
      question: "What integrations are supported?",
      answer: "SentinelOps offers out-of-the-box connectors for Google Cloud (Audit Logs, VPC Flow Logs, IAM), AWS, Azure, and 50+ security tools. Enterprise customers get unlimited custom integrations."
    },
    {
      question: "How does endpoint-based pricing work?",
      answer: "Our transparent pricing is based on the number of endpoints (servers, workstations, network devices) we monitor. Each plan includes a set number of endpoints and daily log processing capacity, with clear per-endpoint pricing for additional scale."
    },
    {
      question: "How quickly can I see ROI?",
      answer: "Most organizations see positive ROI within 6 months through reduced analyst workload (90% reduction in manual tasks), faster incident response (hours to minutes), and 60-80% savings vs DIY SIEM licensing costs."
    },
    {
      question: "Is my data secure with SentinelOps?",
      answer: "Yes. We maintain SOC 2 Type II compliance, encrypt all data in transit and at rest, and operate with enterprise-grade security. Your data never leaves your control - our agents analyze metadata, not sensitive content."
    },
    {
      question: "How does SentinelOps compare to traditional SIEM costs?",
      answer: "Traditional DIY solutions like Splunk can cost $250k+ annually for 100GB/day, while Chronicle averages $315k+ annually. SentinelOps delivers superior AI-powered detection and response at 60-80% lower cost with no infrastructure overhead."
    },
    {
      question: "What payment methods do you accept?",
      answer: "We accept all major credit cards, ACH transfers, and can accommodate purchase orders for Enterprise customers. Annual billing includes 8-10% discount."
    }
  ];

  const pricingTiers = [
    {
      name: "Core",
      price: "$2,500",
      period: "/month",
      description: "Essential managed security operations for small businesses",
      capacity: "Up to 25 endpoints / 25 GB-day",
      features: [
        "24×7 monitoring & AI triage",
        "Automated threat detection",
        "Compliance dashboards", 
        "7-day log retention",
        "Email & Slack alerts",
        "Business hours support"
      ],
      limitations: [],
      cta: "Get Started",
      href: "mailto:cdgtlmda@pm.me?subject=SentinelOps Core Plan - Early Access Interest",
      popular: false,
      pricePerEndpoint: "~$100"
    },
    {
      name: "Growth", 
      price: "$6,000",
      period: "/month",
      description: "Advanced security operations for growing organizations",
      capacity: "Up to 100 endpoints / 100 GB-day",
      features: [
        "All Core features",
        "90-day log retention",
        "Quarterly threat hunting reviews",
        "Advanced analytics & reporting",
        "API access",
        "Priority support",
        "Custom alert tuning"
      ],
      limitations: [],
      cta: "Get Started", 
      href: "mailto:cdgtlmda@pm.me?subject=SentinelOps Growth Plan - Early Access Interest",
      popular: true,
      pricePerEndpoint: "~$60"
    },
    {
      name: "Scale",
      price: "$12,000", 
      period: "/month",
      description: "Enterprise-grade security operations with dedicated support",
      capacity: "Up to 250 endpoints / 250 GB-day",
      features: [
        "All Growth features",
        "Bespoke security playbooks",
        "Dedicated Customer Success Manager",
        "1-year log retention",
        "Custom integrations",
        "24/7 phone support",
        "SLA guarantees"
      ],
      limitations: [],
      cta: "Get Started",
      href: "mailto:cdgtlmda@pm.me?subject=SentinelOps Scale Plan - Early Access Interest", 
      popular: false,
      pricePerEndpoint: "~$48"
    },
    {
      name: "Enterprise",
      price: "$20,000+",
      period: "/month", 
      description: "Custom security operations for large enterprises",
      capacity: "Unlimited endpoints & log ingest",
      features: [
        "All Scale features",
        "Unlimited log ingest",
        "Custom SLAs & response times",
        "Dedicated security analysts",
        "Advanced threat intelligence",
        "Regulatory compliance support",
        "Custom reporting & dashboards"
      ],
      limitations: [],
      cta: "Contact Sales",
      href: "mailto:cdgtlmda@pm.me?subject=SentinelOps Enterprise Plan - Early Access Interest",
      popular: false,
      pricePerEndpoint: "Custom"
    }
  ];

  const features = [
    {
      category: "Core Platform",
      items: [
        { name: "Multi-Agent Architecture", starter: true, professional: true, enterprise: true },
        { name: "Real-time Monitoring", starter: true, professional: true, enterprise: true },
        { name: "Threat Detection", starter: "Basic", professional: "Advanced", enterprise: "AI-Powered" },
        { name: "Incident Response", starter: true, professional: true, enterprise: true },
        { name: "Custom Agents", starter: false, professional: "Limited", enterprise: "Unlimited" }
      ]
    },
    {
      category: "Integrations",
      items: [
        { name: "Cloud Platforms", starter: "Basic", professional: true, enterprise: true },
        { name: "SIEM Integration", starter: false, professional: true, enterprise: true },
        { name: "API Access", starter: false, professional: true, enterprise: "Full" },
        { name: "Webhooks", starter: false, professional: true, enterprise: true },
        { name: "Custom Connectors", starter: false, professional: "Limited", enterprise: "Unlimited" }
      ]
    },
    {
      category: "Support & SLA",
      items: [
        { name: "Support Hours", starter: "Business", professional: "Extended", enterprise: "24/7" },
        { name: "Response Time", starter: "24 hours", professional: "4 hours", enterprise: "1 hour" },
        { name: "Dedicated CSM", starter: false, professional: false, enterprise: true },
        { name: "Uptime SLA", starter: "99.5%", professional: "99.9%", enterprise: "99.99%" },
        { name: "Training", starter: false, professional: "Self-service", enterprise: "White-glove" }
      ]
    }
  ];

  const addOns = [
    {
      name: "Additional Endpoints",
      description: "Scale beyond your plan's endpoint limit",
      price: "$18/endpoint/month"
    },
    {
      name: "Extra Log Ingest",
      description: "Additional data processing beyond plan limits",
      price: "$1.20/GB-day (monthly average)"
    },
    {
      name: "Onboarding & Setup",
      description: "Data-source mapping and playbook tuning",
      price: "$3,000 one-time"
    },
    {
      name: "Annual Prepay Discount",
      description: "Save with annual billing commitment",
      price: "8-10% discount"
    }
  ];

  function renderFeatureValue(value: string | boolean) {
    if (value === true) {
      return <Check className="w-5 h-5 text-green-500 mx-auto" />;
    }
    if (value === false) {
      return <X className="w-5 h-5 text-muted-foreground mx-auto" />;
    }
    return <span className="text-sm text-center">{value}</span>;
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Hero Section */}
      <motion.section 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="container px-4 pt-40 pb-16"
      >
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-white/10 text-green-400 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Shield className="w-4 h-4" />
            Advanced Security Platform
          </div>
          <h1 className="mb-6 tracking-tight text-white">
            Choose Your
            <span className="block text-green-400">Security Plan</span>
          </h1>
          <p className="text-lg md:text-xl text-gray-400 mb-8 max-w-4xl mx-auto leading-relaxed">
            Managed security operations that scale with your business. Transparent endpoint-based pricing with no hidden fees, delivering 60-80% savings vs DIY SIEM solutions.
          </p>
          <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4 mb-8 max-w-2xl mx-auto">
            <p className="text-green-400 text-sm font-medium">
              🚀 Early Access Program - SentinelOps will be available for market consumption in Q4 2025
            </p>
          </div>
        </div>
      </motion.section>

      {/* Pricing Cards */}
      <motion.section 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="py-20"
      >
        <div className="container mx-auto px-4">
          {/* First three plans */}
          <div className="grid lg:grid-cols-3 gap-8 max-w-6xl mx-auto mb-12">
            {pricingTiers.slice(0, 3).map((tier, index) => (
              <motion.div 
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + index * 0.1, duration: 0.5 }}
                className={`flex flex-col border border-white/20 rounded-xl p-8 bg-black/50 backdrop-blur-sm transition-all duration-300 ${
                  tier.popular 
                    ? 'relative border-green-400/50 bg-green-400/5' 
                    : 'hover:border-white/30 hover:bg-white/5'
                }`}
              >
                {tier.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-green-400 text-black px-4 py-1 rounded-full text-sm font-medium">
                    Most Popular
                  </div>
                )}
                
                <div className="text-center mb-8">
                  <h3 className="text-2xl font-semibold mb-2 text-white">{tier.name}</h3>
                  <div className="mb-2">
                    <span className="text-4xl font-normal text-white">{tier.price}</span>
                    <span className="text-gray-400">{tier.period}</span>
                  </div>
                  <div className="mb-4">
                    <span className="text-sm text-green-400 font-medium">{tier.capacity}</span>
                    <div className="text-xs text-gray-500 mt-1">{tier.pricePerEndpoint} per endpoint</div>
                  </div>
                  <p className="text-gray-400">{tier.description}</p>
                </div>

                <ul className="space-y-4 mb-8 flex-grow">
                  {tier.features.map((feature, idx) => (
                    <li key={idx} className="flex items-center gap-3">
                      <Check className="w-5 h-5 text-green-400 flex-shrink-0" />
                      <span className="text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>

                <Link
                  href={tier.href}
                  className={`block w-full text-center py-3 px-6 rounded-lg font-medium transition-colors mt-auto ${
                    tier.popular
                      ? 'bg-white text-black hover:bg-gray-100'
                      : 'border border-white/20 text-white hover:bg-white/10'
                  }`}
                >
                  {tier.cta}
                </Link>
              </motion.div>
            ))}
          </div>

          {/* Enterprise plan - horizontal layout */}
          {pricingTiers.slice(3).map((tier, index) => (
            <motion.div 
              key={index + 3}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.5 }}
              className="border border-white/20 rounded-xl p-8 bg-black/50 backdrop-blur-sm transition-all duration-300 hover:border-white/30 hover:bg-white/5 max-w-4xl mx-auto"
            >
              <div className="grid md:grid-cols-3 gap-8 items-center">
                {/* Left: Plan details */}
                <div className="md:col-span-1">
                  <h3 className="text-2xl font-semibold mb-2 text-white">{tier.name}</h3>
                  <div className="mb-2">
                    <span className="text-3xl font-normal text-white">{tier.price}</span>
                    <span className="text-gray-400">{tier.period}</span>
                  </div>
                  <div className="mb-4">
                    <span className="text-sm text-green-400 font-medium">{tier.capacity}</span>
                    <div className="text-xs text-gray-500 mt-1">{tier.pricePerEndpoint} per endpoint</div>
                  </div>
                  <p className="text-gray-400 text-sm">{tier.description}</p>
                </div>

                {/* Center: Features */}
                <div className="md:col-span-1">
                  <ul className="space-y-3">
                    {tier.features.map((feature, idx) => (
                      <li key={idx} className="flex items-center gap-3">
                        <Check className="w-4 h-4 text-green-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Right: CTA */}
                <div className="md:col-span-1 flex justify-center md:justify-end">
                  <Link
                    href={tier.href}
                    className="inline-flex items-center justify-center px-8 py-3 bg-white text-black rounded-lg font-medium hover:bg-gray-100 transition-colors min-w-[150px]"
                  >
                    {tier.cta}
                  </Link>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* Competitive Analysis */}
      <motion.section 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.5 }}
        className="py-20"
      >
        <div className="container mx-auto px-4">
          <div className="max-w-7xl mx-auto">
            <div className="flex text-center justify-center items-center gap-3 flex-col mb-16">
              <div className="flex gap-2 flex-col">
                <h2 className="tracking-tight max-w-4xl text-center font-semibold text-white">
                  Why SentinelOps Delivers Superior Value
                </h2>
                <p className="text-base leading-relaxed tracking-tight text-gray-400 max-w-3xl text-center">
                  SentinelOps vs. traditional security operations platforms. See why organizations choose 
                  <span className="text-green-400"> AI-powered multi-agent security</span> over legacy SIEM and manual security operations.
                </p>
              </div>
            </div>

            <div className="overflow-hidden rounded-xl border border-white/20 bg-white/5 backdrop-blur-sm">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-white/10 border-white/20">
                      <th className="text-left p-6 font-semibold text-white">Feature</th>
                      <th className="text-center p-6 font-medium text-gray-400">Traditional SIEM</th>
                      <th className="text-center p-6 font-medium text-gray-400">Splunk Enterprise</th>
                      <th className="text-center p-6 font-medium text-gray-400">IBM QRadar</th>
                      <th className="text-center p-6 font-semibold bg-green-400/10 text-green-400">SentinelOps</th>
                      <th className="text-center p-6 font-semibold text-green-400">Competitive Advantage</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-white/10 hover:bg-white/5">
                      <td className="p-6 font-medium text-white flex items-center gap-2">
                        <Clock className="w-4 h-4 text-blue-400" />
                        Threat Detection Speed
                      </td>
                      <td className="p-6 text-center text-sm text-gray-300">15-30 minutes (manual correlation)</td>
                      <td className="p-6 text-center text-sm text-gray-300">5-15 minutes (rule-based)</td>
                      <td className="p-6 text-center text-sm text-gray-300">8-20 minutes (limited AI)</td>
                      <td className="p-6 text-center text-sm font-medium bg-green-400/5 text-white">30 seconds (AI multi-agent)</td>
                      <td className="p-6 text-center text-sm font-medium text-green-400">30x faster threat detection</td>
                    </tr>
                    <tr className="border-white/10 hover:bg-white/5">
                      <td className="p-6 font-medium text-white flex items-center gap-2">
                        <Zap className="w-4 h-4 text-yellow-400" />
                        Automated Response Time
                      </td>
                      <td className="p-6 text-center text-sm text-gray-300">Manual only (hours)</td>
                      <td className="p-6 text-center text-sm text-gray-300">Basic playbooks (15-30 min)</td>
                      <td className="p-6 text-center text-sm text-gray-300">Limited automation (10-20 min)</td>
                      <td className="p-6 text-center text-sm font-medium bg-green-400/5 text-white">Instant (AI-driven)</td>
                      <td className="p-6 text-center text-sm font-medium text-green-400">1800x faster incident response</td>
                    </tr>
                    <tr className="border-white/10 hover:bg-white/5">
                      <td className="p-6 font-medium text-white flex items-center gap-2">
                        <Users className="w-4 h-4 text-purple-400" />
                        Analyst Productivity
                      </td>
                      <td className="p-6 text-center text-sm text-gray-300">100% manual investigation</td>
                      <td className="p-6 text-center text-sm text-gray-300">30% reduction in manual work</td>
                      <td className="p-6 text-center text-sm text-gray-300">40% efficiency improvement</td>
                      <td className="p-6 text-center text-sm font-medium bg-green-400/5 text-white">90% reduction in manual tasks</td>
                      <td className="p-6 text-center text-sm font-medium text-green-400">Analysts focus on strategic threats</td>
                    </tr>
                    <tr className="border-white/10 hover:bg-white/5">
                      <td className="p-6 font-medium text-white flex items-center gap-2">
                        <Database className="w-4 h-4 text-green-400" />
                        Data Integration
                      </td>
                      <td className="p-6 text-center text-sm text-gray-300">Limited sources</td>
                      <td className="p-6 text-center text-sm text-gray-300">100+ connectors</td>
                      <td className="p-6 text-center text-sm text-gray-300">150+ integrations</td>
                      <td className="p-6 text-center text-sm font-medium bg-green-400/5 text-white">500+ AI-enhanced connectors</td>
                      <td className="p-6 text-center text-sm font-medium text-green-400">Universal data normalization</td>
                    </tr>
                    <tr className="border-white/10 hover:bg-white/5">
                      <td className="p-6 font-medium text-white flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-red-400" />
                        False Positive Rate
                      </td>
                      <td className="p-6 text-center text-sm text-gray-300">60-80% false positives</td>
                      <td className="p-6 text-center text-sm text-gray-300">40-60% false positives</td>
                      <td className="p-6 text-center text-sm text-gray-300">30-50% false positives</td>
                      <td className="p-6 text-center text-sm font-medium bg-green-400/5 text-white">5-10% false positives</td>
                      <td className="p-6 text-center text-sm font-medium text-green-400">AI context reduces noise by 85%</td>
                    </tr>
                    <tr className="border-white/10 hover:bg-white/5">
                      <td className="p-6 font-medium text-white flex items-center gap-2">
                        <Cpu className="w-4 h-4 text-blue-400" />
                        AI/ML Capabilities
                      </td>
                      <td className="p-6 text-center text-sm text-gray-300">Basic correlation rules</td>
                      <td className="p-6 text-center text-sm text-gray-300">Machine learning add-ons</td>
                      <td className="p-6 text-center text-sm text-gray-300">Watson AI integration</td>
                      <td className="p-6 text-center text-sm font-medium bg-green-400/5 text-white">Multi-agent AI orchestration</td>
                      <td className="p-6 text-center text-sm font-medium text-green-400">Self-improving threat intelligence</td>
                    </tr>
                    <tr className="border-white/10 hover:bg-white/5">
                      <td className="p-6 font-medium text-white flex items-center gap-2">
                        <Network className="w-4 h-4 text-indigo-400" />
                        Scalability
                      </td>
                      <td className="p-6 text-center text-sm text-gray-300">Hardware-limited</td>
                      <td className="p-6 text-center text-sm text-gray-300">Cloud + on-premise</td>
                      <td className="p-6 text-center text-sm text-gray-300">Hybrid deployment</td>
                      <td className="p-6 text-center text-sm font-medium bg-green-400/5 text-white">Elastic cloud-native</td>
                      <td className="p-6 text-center text-sm font-medium text-green-400">Auto-scaling to petabyte scale</td>
                    </tr>
                    <tr className="border-white/10 hover:bg-white/5">
                      <td className="p-6 font-medium text-white flex items-center gap-2">
                        <Shield className="w-4 h-4 text-purple-400" />
                        Compliance Reporting
                      </td>
                      <td className="p-6 text-center text-sm text-gray-300">Manual report generation</td>
                      <td className="p-6 text-center text-sm text-gray-300">Pre-built compliance apps</td>
                      <td className="p-6 text-center text-sm text-gray-300">Compliance dashboard</td>
                      <td className="p-6 text-center text-sm font-medium bg-green-400/5 text-white">AI-generated audit trails</td>
                      <td className="p-6 text-center text-sm font-medium text-green-400">Real-time compliance monitoring</td>
                    </tr>
                    <tr className="border-white/10 hover:bg-white/5">
                      <td className="p-6 font-medium text-white flex items-center gap-2">
                        <Globe className="w-4 h-4 text-green-400" />
                        Total Cost of Ownership
                      </td>
                      <td className="p-6 text-center text-sm text-gray-300">$500K+ annually (10-person SOC)</td>
                      <td className="p-6 text-center text-sm text-gray-300">$300K+ annually (licensing + staff)</td>
                      <td className="p-6 text-center text-sm text-gray-300">$400K+ annually (enterprise)</td>
                      <td className="p-6 text-center text-sm font-medium bg-green-400/5 text-white">$150K annually (AI-automated)</td>
                      <td className="p-6 text-center text-sm font-medium text-green-400">70% cost reduction vs traditional</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

                        {/* Advantage Cards */}
            <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-black/50 border border-white/10 rounded-xl p-6 backdrop-blur-sm hover:border-white/20 transition-all duration-300">
                <div className="flex items-center gap-3 mb-3">
                  <Clock className="w-5 h-5 text-blue-400" />
                  <h3 className="text-lg font-semibold text-white">Speed Revolution</h3>
                </div>
                <p className="text-gray-400 text-sm leading-relaxed">
                  <span className="text-blue-400 font-bold">30x faster</span> threat detection eliminates 
                  the critical minutes that separate successful attacks from thwarted attempts.
                </p>
              </div>

              <div className="bg-black/50 border border-white/10 rounded-xl p-6 backdrop-blur-sm hover:border-white/20 transition-all duration-300">
                <div className="flex items-center gap-3 mb-3">
                  <Cpu className="w-5 h-5 text-purple-400" />
                  <h3 className="text-lg font-semibold text-white">AI-First Architecture</h3>
                </div>
                <p className="text-gray-400 text-sm leading-relaxed">
                  <span className="text-purple-400 font-bold">Multi-agent orchestration</span> provides 
                  contextual threat intelligence impossible with traditional rule-based systems.
                </p>
              </div>

              <div className="bg-black/50 border border-white/10 rounded-xl p-6 backdrop-blur-sm hover:border-white/20 transition-all duration-300">
                <div className="flex items-center gap-3 mb-3">
                  <Users className="w-5 h-5 text-green-400" />
                  <h3 className="text-lg font-semibold text-white">Analyst Empowerment</h3>
                </div>
                <p className="text-gray-400 text-sm leading-relaxed">
                  <span className="text-green-400 font-bold">90% reduction</span> in manual tasks 
                  lets security teams focus on strategic threat hunting and incident response.
                </p>
              </div>
            </div>

             {/* Value Proposition Summary */}
             <div className="mt-12 bg-gradient-to-r from-green-600 to-blue-600 rounded-xl p-6 md:p-8 text-center">
               <h3 className="text-xl md:text-2xl font-semibold mb-4 text-white">
                 The Bottom Line: Revolutionary AI Security for Modern Enterprises
               </h3>
               <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left max-w-4xl mx-auto">
                 <div>
                   <h4 className="font-semibold mb-3 text-white">Cost Justification</h4>
                   <ul className="space-y-1 text-white/90 text-sm">
                     <li>• 70% reduction in total security operations costs</li>
                     <li>• Eliminate need for 6-8 additional security analysts</li>
                     <li>• ROI positive within 6 months for most organizations</li>
                     <li>• 90% reduction in false positive investigation time</li>
                   </ul>
                 </div>
                 <div>
                   <h4 className="font-semibold mb-3 text-white">Security Impact</h4>
                   <ul className="space-y-1 text-white/90 text-sm">
                     <li>• 30x faster threat detection and response</li>
                     <li>• 85% reduction in security alert fatigue</li>
                     <li>• Proactive threat hunting vs reactive monitoring</li>
                     <li>• 99.9% uptime with elastic cloud scaling</li>
                   </ul>
                 </div>
               </div>
             </div>
           </div>
         </div>
       </motion.section>

      {/* Add-ons */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">Add-ons & Services</h2>
              <p className="text-xl text-muted-foreground">
                Extend your SentinelOps platform with additional services and capabilities
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              {addOns.map((addon, index) => (
                <div key={index} className="border border-border rounded-lg p-6">
                  <h3 className="text-lg font-semibold mb-2">{addon.name}</h3>
                  <p className="text-muted-foreground mb-4">{addon.description}</p>
                  <div className="text-primary font-semibold">{addon.price}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <FaqSection
        title="Frequently Asked Questions"
        description="Everything you need to know about SentinelOps pricing and platform"
        items={faqItems}
      />

      {/* CTA Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">Interested in Early Access?</h2>
            <p className="text-xl text-muted-foreground mb-8">
              Be among the first to experience next-generation AI-powered security operations when SentinelOps launches in Q4 2025
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="mailto:cdgtlmda@pm.me?subject=SentinelOps Early Access Program - Schedule Demo"
                className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-8 py-4 rounded-lg font-medium hover:bg-primary/90 transition-colors"
              >
                Join Early Access
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="mailto:cdgtlmda@pm.me?subject=SentinelOps Enterprise - Early Access Interest"
                className="inline-flex items-center gap-2 border border-border px-8 py-4 rounded-lg font-medium hover:bg-accent transition-colors"
              >
                Contact Sales
                <Phone className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
} 