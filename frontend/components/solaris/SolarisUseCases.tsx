"use client";

import React, { useState } from "react";
import {
  TrendingUp,
  Headphones,
  Users,
  Cpu,
  BarChart,
  ArrowRight,
  CheckCircle2,
  Sparkles,
} from "lucide-react";

export default function SolarisUseCases() {
  const [activeUseCase, setActiveUseCase] = useState<number>(0);

  const useCases = [
    {
      category: "Customer Service",
      title: "24/7 Intelligent Support",
      metric: "95% customer satisfaction",
      description:
        "Deploy AI agents that handle customer inquiries, resolve issues, and escalate complex cases to human agents seamlessly.",
      icon: <Headphones className="size-5" />,
      features: [
        "Instant multi-lingual answers (< 200ms)",
        "Automated refund & ticket resolutions",
        "Deterministic escalation protocols",
      ],
      sampleOutput: {
        agent: "SupportAgent_01",
        input: "User: My payment failed on order #8921. Can you help?",
        action: "Verifying Stripe charge status... Retried with 3DS fallback.",
        status: "RESOLVED: Payment authorized, invoice #8921 sent to user email.",
      },
    },
    {
      category: "Sales & Marketing",
      title: "Automated Lead Generation",
      metric: "3.2x conversion rate",
      description:
        "Identify, qualify, and engage prospective customers with hyper-personalized outreach and intelligent follow-ups.",
      icon: <Users className="size-5" />,
      features: [
        "Automated ICP signal detection",
        "Contextual email & LinkedIn sequencing",
        "CRM data enrichment & qualification scoring",
      ],
      sampleOutput: {
        agent: "OutboundAgent_04",
        input: "Event: New CTO signed up from Series B fintech",
        action: "Enriching company metrics... Identified stack: Next.js + Postgres.",
        status: "SCHEDULED: Personalized demo sequence drafted & approved.",
      },
    },
    {
      category: "Operations",
      title: "Process Automation",
      metric: "80% operational cost reduction",
      description:
        "Automate repetitive tasks, data entry, report generation, and cross-system synchronization with precision and reliability.",
      icon: <Cpu className="size-5" />,
      features: [
        "Automated invoice & PDF document ingestion",
        "Cross-database synchronization without downtime",
        "Continuous compliance monitoring & alert triage",
      ],
      sampleOutput: {
        agent: "OpsWorkflowAgent",
        input: "Cron: Daily reconcile across Stripe & Postgres ledger",
        action: "Scanning 4,820 transaction records... Zero discrepancies detected.",
        status: "COMPLETED: Daily ledger reconciliation signed and committed.",
      },
    },
    {
      category: "Intelligence",
      title: "Intelligent Data Analysis",
      metric: "10x faster insights",
      description:
        "Analyze complex datasets, generate predictive insights, run ad-hoc SQL queries, and automate executive summaries.",
      icon: <BarChart className="size-5" />,
      features: [
        "Natural language to SQL schema querying",
        "Real-time anomaly detection & trend alerts",
        "Automated weekly metrics decks & Slack digests",
      ],
      sampleOutput: {
        agent: "AnalyticsCopilot",
        input: "Query: Compare Q3 customer retention by pricing tier",
        action: "Executing aggregate queries on SQLite warehouse...",
        status: "CHART READY: Pro tier retention is +24% YoY vs Starter tier.",
      },
    },
  ];

  return (
    <section id="solutions" className="py-24 bg-[#0a0a0a] relative overflow-hidden border-t border-white/[0.06]">
      {/* Ambient background glows */}
      <div className="absolute top-1/3 right-0 w-96 h-96 bg-[#0065fc]/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 md:px-12 xl:px-0 relative z-10 flex flex-col items-center">
        {/* Section Heading */}
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white text-center tracking-tight">
          Transform{" "}
          <span className="bg-gradient-to-r from-[#6ea8ff] via-[#0065fc] to-[#54a2ff] bg-clip-text text-transparent">
            Your Business
          </span>
        </h2>

        <p className="mt-4 text-center text-sm md:text-base text-white/60 max-w-lg leading-relaxed">
          AI agents working across your entire organization, delivering measurable ROI from day one.
        </p>

        {/* 4 Use Case Cards Grid */}
        <div className="mt-14 grid grid-cols-1 md:grid-cols-2 gap-5 w-full">
          {useCases.map((item, idx) => (
            <div
              key={item.title}
              onClick={() => setActiveUseCase(idx)}
              className={`rounded-xl lg:rounded-2xl p-6 sm:p-8 border transition-all duration-300 cursor-pointer flex flex-col justify-between ${
                activeUseCase === idx
                  ? "bg-gradient-to-br from-[#161822] to-[#0e1017] border-[#0065fc]/60 shadow-[0_0_30px_rgba(0,101,252,0.2)]"
                  : "bg-[#121216] border-white/10 hover:border-white/20"
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-[#0065fc]/20 text-[#6ea8ff] border border-[#0065fc]/30 flex items-center gap-1.5">
                    {item.icon}
                    {item.category}
                  </span>
                  <span className="text-xs font-mono text-emerald-400 font-bold flex items-center gap-1">
                    <TrendingUp className="size-3.5" />
                    {item.metric}
                  </span>
                </div>

                <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                  {item.title}
                </h3>

                <p className="mt-3 text-sm sm:text-base text-white/60 leading-relaxed">
                  {item.description}
                </p>

                <div className="mt-5 space-y-2">
                  {item.features.map((feat) => (
                    <div key={feat} className="flex items-center gap-2 text-xs sm:text-sm text-white/80">
                      <CheckCircle2 className="size-4 text-[#54a2ff] shrink-0" />
                      <span>{feat}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Sample Output Terminal Snippet */}
              <div className="mt-6 pt-4 border-t border-white/10 rounded-lg bg-black/40 p-3 font-mono text-xs">
                <div className="flex items-center justify-between text-white/40 text-[10px] mb-1.5">
                  <span className="text-[#54a2ff] font-semibold">{item.sampleOutput.agent}</span>
                  <span className="text-emerald-400">ACTIVE</span>
                </div>
                <div className="text-white/60 truncate">&gt; {item.sampleOutput.input}</div>
                <div className="text-emerald-300 text-[11px] mt-1 font-semibold truncate">
                  ✔ {item.sampleOutput.status}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
