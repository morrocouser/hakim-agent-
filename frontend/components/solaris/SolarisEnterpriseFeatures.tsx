"use client";

import React, { useState } from "react";
import {
  Target,
  Network,
  Database,
  Zap,
  ShieldCheck,
  BarChart3,
  CheckCircle,
} from "lucide-react";

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  tag: string;
}

function SpotlightCard({ icon, title, description, tag }: FeatureCardProps) {
  const [mousePos, setMousePos] = useState({ x: -200, y: -200 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMousePos({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  return (
    <div
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="group relative rounded-xl lg:rounded-2xl p-6 lg:p-8 overflow-hidden transition-all duration-500 bg-gradient-to-br from-[#141418] to-[#0a0a0d] border border-white/10 hover:border-white/20 shadow-xl"
      style={{
        background: `linear-gradient(var(--background, #0a0a0a) 0 0) padding-box, 
          radial-gradient(220px circle at ${mousePos.x}px ${mousePos.y}px, 
            #6EA8FF, 
            #0065FC, 
            rgba(255,255,255,0.1) 100% 
          ) border-box`,
      }}
    >
      {/* Background radial spotlight highlight */}
      <div
        className="pointer-events-none absolute inset-0 rounded-[inherit] transition-opacity duration-300"
        style={{
          opacity: isHovered ? 0.15 : 0,
          background: `radial-gradient(250px circle at ${mousePos.x}px ${mousePos.y}px, #0065FC, transparent 100%)`,
        }}
      />

      <div className="relative z-10 flex flex-col justify-between h-full">
        <div>
          <div className="flex items-center justify-between mb-6">
            <div className="size-12 lg:size-14 rounded-xl bg-white/[0.04] border border-white/10 flex items-center justify-center text-white group-hover:text-[#54a2ff] transition-colors duration-300">
              {icon}
            </div>
            <span className="text-[11px] font-mono font-medium px-2.5 py-1 rounded-full bg-white/[0.04] text-white/50 border border-white/5">
              {tag}
            </span>
          </div>

          <h4 className="text-xl font-bold text-white tracking-tight group-hover:text-white transition-colors">
            {title}
          </h4>

          <p className="mt-3 text-sm lg:text-base text-white/60 leading-relaxed">
            {description}
          </p>
        </div>

        <div className="mt-6 pt-4 border-t border-white/[0.07] flex items-center gap-2 text-xs font-mono text-[#6ea8ff]">
          <CheckCircle className="size-3.5" />
          <span>Production-grade validation</span>
        </div>
      </div>
    </div>
  );
}

export default function SolarisEnterpriseFeatures() {
  const features = [
    {
      icon: <Target className="size-6 lg:size-7" />,
      title: "Goal-Oriented Agents",
      tag: "AUTONOMOUS",
      description:
        "Agents that understand high-level objectives and autonomously determine the optimal path, tool selection, and retry sequences to achieve them.",
    },
    {
      icon: <Network className="size-6 lg:size-7" />,
      title: "Multi-Agent Orchestration",
      tag: "CONSENSUS",
      description:
        "Coordinate multiple agents working together on complex tasks with built-in collaboration protocols, role handoffs, and deterministic consensus.",
    },
    {
      icon: <Database className="size-6 lg:size-7" />,
      title: "Advanced Memory Systems",
      tag: "PERSISTENT",
      description:
        "Persistent long-term memory with SQLite-vec vector search, episodic context retrieval, structured key-value stores, and session caching.",
    },
    {
      icon: <Zap className="size-6 lg:size-7" />,
      title: "Real-Time Processing",
      tag: "ASYNCIO",
      description:
        "Sub-second streaming responses and parallel task execution with native async architecture, non-blocking I/O, and 0 ms telemetry overhead.",
    },
    {
      icon: <ShieldCheck className="size-6 lg:size-7" />,
      title: "Enterprise Security",
      tag: "ZERO-TRUST",
      description:
        "SOC 2 compliant with sandboxed filesystem execution, role-based access control, cryptographic verification, and private VPC deployment.",
    },
    {
      icon: <BarChart3 className="size-6 lg:size-7" />,
      title: "Analytics & Insights",
      tag: "TELEMETRY",
      description:
        "Comprehensive telemetry, execution traces, token usage breakdown, model routing breakdown, and automated agent benchmark evaluation.",
    },
  ];

  return (
    <section id="capabilities" className="py-24 bg-[#0a0a0a] relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-[radial-gradient(ellipse_at_center,_rgba(0,101,252,0.1),_transparent_70%)] blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 md:px-12 xl:px-0 relative z-10 flex flex-col items-center">
        {/* Section Heading */}
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white text-center tracking-tight max-w-2xl">
          Enterprise-Grade{" "}
          <span className="bg-gradient-to-r from-[#6ea8ff] via-[#0065fc] to-[#54a2ff] bg-clip-text text-transparent">
            AI Agents
          </span>
        </h2>

        <p className="mt-4 max-w-xl text-center text-sm md:text-base text-white/60 leading-relaxed">
          Stop building prototypes and start deploying autonomous agents that actually deliver.
          Solaris powers multi-agent workflows that scale with your growth, not your headcount.
        </p>

        {/* 6 Spotlight Cards Grid */}
        <div className="mt-14 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 w-full">
          {features.map((item) => (
            <SpotlightCard key={item.title} {...item} />
          ))}
        </div>
      </div>
    </section>
  );
}
