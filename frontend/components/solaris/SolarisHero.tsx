"use client";

import React, { useState } from "react";
import Image from "next/image";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Upload,
  Plus,
  Copy,
  Check,
  Sparkles,
  Bot,
  Cpu,
  Layers,
  Activity,
  Play,
  RotateCcw,
  Zap,
} from "lucide-react";

export default function SolarisHero() {
  const [activeTab, setActiveTab] = useState<"preview" | "interactive">("preview");
  const [copied, setCopied] = useState(false);
  const [simRunning, setSimRunning] = useState(false);
  const [activeStep, setActiveStep] = useState(0);

  const handleCopy = () => {
    navigator.clipboard?.writeText("npx create-solaris-agent@latest");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRunSimulation = () => {
    if (simRunning) return;
    setSimRunning(true);
    setActiveStep(1);
    setTimeout(() => setActiveStep(2), 1200);
    setTimeout(() => setActiveStep(3), 2400);
    setTimeout(() => {
      setActiveStep(4);
      setSimRunning(false);
    }, 3600);
  };

  return (
    <section className="relative min-h-screen pt-32 pb-20 md:pt-44 md:pb-32 overflow-hidden bg-[#0a0a0a]">
      {/* Background Radial Glow & Custom Rays */}
      <div className="absolute top-0 inset-0 w-full h-full pointer-events-none z-0">
        {/* Central blue light spotlight */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] md:w-[1000px] h-[500px] bg-[radial-gradient(ellipse_at_top,_rgba(0,101,252,0.22),_transparent_70%)] blur-3xl pointer-events-none" />
        
        {/* Secondary ambient glows */}
        <div className="absolute top-[20%] left-[10%] w-[400px] h-[400px] bg-[radial-gradient(circle,_rgba(84,162,255,0.08),_transparent_60%)] blur-3xl pointer-events-none" />
        <div className="absolute top-[30%] right-[10%] w-[400px] h-[400px] bg-[radial-gradient(circle,_rgba(0,101,252,0.1),_transparent_60%)] blur-3xl pointer-events-none" />

        {/* Subtle grid background */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff05_1px,transparent_1px),linear-gradient(to_bottom,#ffffff05_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_20%,#000_70%,transparent_100%)] opacity-70" />
      </div>

      <div className="max-w-7xl mx-auto px-4 md:px-12 xl:px-0 relative z-10 flex flex-col items-center">
        {/* Announcement Pill Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <a
            href="#features"
            className="group relative inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3.5 py-1 text-xs md:text-sm text-white/80 hover:text-white transition-all duration-300 backdrop-blur-md hover:border-white/20 hover:bg-white/[0.08]"
          >
            <span className="rounded-full bg-[#0065fc] px-2 py-0.5 text-xs font-semibold text-white shadow-[0_0_12px_rgba(0,101,252,0.8)]">
              New
            </span>
            <span className="font-medium">Agent orchestration is live</span>
            <div className="relative inline-flex size-4 items-center justify-center overflow-hidden">
              <ArrowRight className="size-3.5 transition-transform duration-300 group-hover:translate-x-0.5" />
            </div>

            {/* Glowing moving border beam */}
            <span className="pointer-events-none absolute -inset-px rounded-full overflow-hidden">
              <span className="absolute inset-0 bg-[conic-gradient(from_0deg,#0065fc,transparent_30%,#54a2ff,transparent_70%,#0065fc)] opacity-20 group-hover:opacity-60 transition-opacity duration-300" />
            </span>
          </a>
        </motion.div>

        {/* Main H1 Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 25 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="mt-8 max-w-4xl text-center text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight text-white leading-[1.1]"
        >
          Your{" "}
          <span className="bg-gradient-to-r from-[#6ea8ff] via-[#0065fc] to-[#54a2ff] bg-clip-text text-transparent">
            AI Workforce,
          </span>{" "}
          Ready for Production.
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="mt-6 max-w-2xl text-center text-base sm:text-lg text-white/60 leading-relaxed font-normal"
        >
          Stop building prototypes and start deploying autonomous agents that actually deliver.
          Solaris powers multi-agent workflows that scale with your growth, not your headcount.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.3 }}
          className="mt-8 flex flex-wrap items-center justify-center gap-4"
        >
          <a
            href="#pricing"
            className="group relative inline-flex items-center justify-center gap-2 rounded-full px-7 py-3 text-sm md:text-base font-medium text-white bg-[#0065fc] hover:bg-[#1a74fc] transition-all duration-300 shadow-[0_0_25px_rgba(0,101,252,0.5)] hover:shadow-[0_0_35px_rgba(0,101,252,0.8)]"
          >
            <span>Get Started Free</span>
            <ArrowRight className="size-4 transition-transform duration-300 group-hover:translate-x-1" />
          </a>

          <a
            href="#features"
            className="inline-flex items-center justify-center gap-2 rounded-full px-7 py-3 text-sm md:text-base font-medium text-white/80 hover:text-white bg-white/[0.04] hover:bg-white/[0.08] border border-white/10 hover:border-white/20 transition-all duration-300 backdrop-blur-md"
          >
            Book Demo
          </a>
        </motion.div>

        {/* Signature App Shell Mockup / Dashboard Preview */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="mt-14 md:mt-20 w-full max-w-6xl relative"
        >
          {/* Ambient outer backlight glow */}
          <div className="absolute -inset-1.5 rounded-2xl bg-gradient-to-b from-[#0065fc]/30 via-[#0065fc]/10 to-transparent blur-xl opacity-60 pointer-events-none" />

          {/* Window Chrome Container */}
          <div className="relative rounded-xl md:rounded-2xl border border-white/15 bg-[#121216]/90 backdrop-blur-xl shadow-[0_20px_50px_rgba(0,0,0,0.8)] overflow-hidden">
            {/* Window Title Bar */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-white/[0.02]">
              {/* macOS Style Traffic Dots */}
              <div className="flex items-center gap-2">
                <div className="size-3 rounded-full bg-[#ff5f56]/80 hover:bg-[#ff5f56] transition-colors" />
                <div className="size-3 rounded-full bg-[#ffbd2e]/80 hover:bg-[#ffbd2e] transition-colors" />
                <div className="size-3 rounded-full bg-[#27c93f]/80 hover:bg-[#27c93f] transition-colors" />
                <span className="ml-3 hidden sm:inline-block text-xs font-mono text-white/40">
                  solaris-agent-runtime v4.0.0 — production-cluster-01
                </span>
              </div>

              {/* View Switcher Tabs */}
              <div className="flex items-center bg-black/40 border border-white/10 rounded-lg p-0.5">
                <button
                  type="button"
                  onClick={() => setActiveTab("preview")}
                  className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
                    activeTab === "preview"
                      ? "bg-[#0065fc] text-white shadow-sm"
                      : "text-white/60 hover:text-white"
                  }`}
                >
                  Dashboard Preview
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab("interactive")}
                  className={`px-3 py-1 rounded-md text-xs font-medium flex items-center gap-1.5 transition-all ${
                    activeTab === "interactive"
                      ? "bg-[#0065fc] text-white shadow-sm"
                      : "text-white/60 hover:text-white"
                  }`}
                >
                  <Sparkles className="size-3 text-[#6ea8ff]" />
                  Live Swarm Simulator
                </button>
              </div>

              {/* Actions Icons */}
              <div className="hidden sm:flex items-center gap-2 text-white/60">
                <button
                  type="button"
                  onClick={handleCopy}
                  title="Copy install command"
                  className="p-1 hover:text-white hover:bg-white/5 rounded transition-colors"
                >
                  {copied ? <Check className="size-3.5 text-emerald-400" /> : <Copy className="size-3.5" />}
                </button>
                <button
                  type="button"
                  className="p-1 hover:text-white hover:bg-white/5 rounded transition-colors"
                >
                  <Plus className="size-3.5" />
                </button>
                <button
                  type="button"
                  className="p-1 hover:text-white hover:bg-white/5 rounded transition-colors"
                >
                  <Upload className="size-3.5" />
                </button>
              </div>
            </div>

            {/* Window Content Area */}
            {activeTab === "preview" ? (
              <div className="relative aspect-video w-full overflow-hidden bg-black/60">
                <Image
                  src="/assets/solaris-dashboard.png"
                  alt="Solaris AI Workforce Dashboard Preview"
                  fill
                  priority
                  className="object-cover object-top"
                />
                
                {/* Floating Live Badge inside image */}
                <div className="absolute bottom-4 left-4 sm:bottom-6 sm:left-6 flex items-center gap-2 bg-[#0a0a0a]/90 border border-white/10 rounded-full px-4 py-2 backdrop-blur-md shadow-lg">
                  <div className="size-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-xs font-mono text-white/90">
                    6 Agents Active • 0 ms Telemetry Overhead • Strict DAG
                  </span>
                </div>
              </div>
            ) : (
              /* Interactive Live Swarm Simulator */
              <div className="p-6 md:p-8 bg-[#0b0d11]">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Left: Swarm Pipeline */}
                  <div className="lg:col-span-2 space-y-4">
                    <div className="flex items-center justify-between pb-2 border-b border-white/10">
                      <div className="flex items-center gap-2">
                        <Layers className="size-4 text-[#54a2ff]" />
                        <h4 className="text-sm font-semibold text-white">Multi-Agent Pipeline DAG</h4>
                      </div>
                      <button
                        type="button"
                        onClick={handleRunSimulation}
                        disabled={simRunning}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#0065fc] hover:bg-[#1a74fc] text-xs font-medium text-white transition-all disabled:opacity-50"
                      >
                        {simRunning ? (
                          <>
                            <Activity className="size-3 animate-spin" />
                            Executing DAG...
                          </>
                        ) : (
                          <>
                            <Play className="size-3" />
                            Run Pipeline Simulation
                          </>
                        )}
                      </button>
                    </div>

                    {/* Nodes Visual Flow */}
                    <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                      {[
                        {
                          step: 1,
                          name: "Intent Router",
                          role: "Deterministic Classifier",
                          model: "qwen2.5-coder",
                          latency: "12ms",
                          status: activeStep >= 1 ? "completed" : "idle",
                        },
                        {
                          step: 2,
                          name: "Architect Agent",
                          role: "System & Schema Design",
                          model: "claude-3-7-sonnet",
                          latency: "240ms",
                          status: activeStep >= 2 ? "completed" : activeStep === 1 ? "active" : "idle",
                        },
                        {
                          step: 3,
                          name: "CodeGen Swarm",
                          role: "Parallel Implementation",
                          model: "claude-3-5-haiku",
                          latency: "180ms",
                          status: activeStep >= 3 ? "completed" : activeStep === 2 ? "active" : "idle",
                        },
                        {
                          step: 4,
                          name: "Reflexion Critic",
                          role: "Automated Verification",
                          model: "deterministic",
                          latency: "45ms",
                          status: activeStep >= 4 ? "completed" : activeStep === 3 ? "active" : "idle",
                        },
                      ].map((node) => (
                        <div
                          key={node.step}
                          className={`p-3.5 rounded-xl border transition-all duration-300 ${
                            node.status === "active"
                              ? "bg-[#0065fc]/15 border-[#0065fc] shadow-[0_0_15px_rgba(0,101,252,0.3)] scale-[1.02]"
                              : node.status === "completed"
                              ? "bg-white/[0.04] border-emerald-500/40"
                              : "bg-white/[0.02] border-white/10 opacity-70"
                          }`}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-[10px] font-mono text-white/50">NODE_0{node.step}</span>
                            <span
                              className={`size-2 rounded-full ${
                                node.status === "active"
                                  ? "bg-[#54a2ff] animate-ping"
                                  : node.status === "completed"
                                  ? "bg-emerald-400"
                                  : "bg-white/20"
                              }`}
                            />
                          </div>
                          <h5 className="text-xs font-semibold text-white truncate">{node.name}</h5>
                          <p className="text-[11px] text-white/50 truncate">{node.role}</p>
                          <div className="mt-3 pt-2 border-t border-white/10 flex items-center justify-between text-[10px] font-mono">
                            <span className="text-[#6ea8ff]">{node.model}</span>
                            <span className="text-white/40">{node.latency}</span>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Console Execution Stream */}
                    <div className="rounded-xl bg-black/60 border border-white/10 p-4 font-mono text-xs">
                      <div className="flex items-center justify-between text-white/40 mb-2 pb-1 border-b border-white/10">
                        <span>LIVE EXECUTION STREAM</span>
                        <span>ASYNC STRICT DAG</span>
                      </div>
                      <div className="space-y-1.5 text-white/70 max-h-28 overflow-y-auto">
                        <p className="text-emerald-400">
                          [00:00:01] Solaris runtime initialized. SQLite memory store indexed.
                        </p>
                        {activeStep >= 1 && (
                          <p className="text-[#54a2ff]">
                            [00:00:02] [Router] Prompt intent parsed: &quot;Build scalable microservice with FastAPI&quot; (Score: 0.98)
                          </p>
                        )}
                        {activeStep >= 2 && (
                          <p className="text-white/80">
                            [00:00:03] [Architect] Generated schema: 3 endpoints, JWT auth, SQLite session pool.
                          </p>
                        )}
                        {activeStep >= 3 && (
                          <p className="text-indigo-300">
                            [00:00:04] [CodeGen Swarm] 4 files generated in sandbox without filesystem escape.
                          </p>
                        )}
                        {activeStep >= 4 && (
                          <p className="text-emerald-300 font-semibold">
                            [00:00:05] [Reflexion] All 12 criteria verified. DAG run complete with 0 errors.
                          </p>
                        )}
                        {activeStep === 0 && (
                          <p className="text-white/30 italic">Click &quot;Run Pipeline Simulation&quot; to trace swarm execution...</p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Right: Telemetry & Memory Metrics */}
                  <div className="space-y-4 bg-white/[0.02] border border-white/10 rounded-xl p-4">
                    <div className="flex items-center gap-2 pb-2 border-b border-white/10">
                      <Activity className="size-4 text-emerald-400" />
                      <h4 className="text-sm font-semibold text-white">Cluster Telemetry</h4>
                    </div>

                    <div className="space-y-3">
                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-white/60">Execution Latency</span>
                          <span className="font-mono text-emerald-400">475 ms</span>
                        </div>
                        <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                          <div className="h-full bg-emerald-400 w-[24%]" />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-white/60">Deterministic Safety Score</span>
                          <span className="font-mono text-[#54a2ff]">99.8%</span>
                        </div>
                        <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                          <div className="h-full bg-[#0065fc] w-[99.8%]" />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-white/60">Vector Embeddings Indexed</span>
                          <span className="font-mono text-purple-400">14,280 chunks</span>
                        </div>
                        <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                          <div className="h-full bg-purple-500 w-[78%]" />
                        </div>
                      </div>

                      <div className="pt-3 border-t border-white/10">
                        <div className="grid grid-cols-2 gap-2 text-center">
                          <div className="p-2 rounded-lg bg-black/40 border border-white/5">
                            <div className="text-[10px] text-white/50">CONCURRENCY</div>
                            <div className="text-sm font-mono font-bold text-white">32 Tasks</div>
                          </div>
                          <div className="p-2 rounded-lg bg-black/40 border border-white/5">
                            <div className="text-[10px] text-white/50">EXTERNAL CALLS</div>
                            <div className="text-sm font-mono font-bold text-emerald-400">0 Forced</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
