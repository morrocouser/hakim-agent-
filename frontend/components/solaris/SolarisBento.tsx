"use client";

import React, { useState } from "react";
import {
  ArrowRight,
  GitBranch,
  Brain,
  Repeat,
  Share2,
  CheckCircle2,
  Database,
  Terminal,
  Cpu,
  Layers,
  Sparkles,
  Zap,
} from "lucide-react";

export default function SolarisBento() {
  const [selectedModel, setSelectedModel] = useState<"sonnet" | "haiku" | "qwen" | "llama">("sonnet");

  const models = [
    {
      id: "sonnet",
      name: "claude-3-7-sonnet",
      tier: "CRITICAL",
      reasoning: 99,
      latency: "240ms",
      cost: "$3.00/1M",
    },
    {
      id: "haiku",
      name: "claude-3-5-haiku",
      tier: "ADVANCED",
      reasoning: 92,
      latency: "110ms",
      cost: "$0.80/1M",
    },
    {
      id: "qwen",
      name: "qwen2.5-coder (local)",
      tier: "STANDARD",
      reasoning: 89,
      latency: "28ms",
      cost: "$0.00 (Local)",
    },
    {
      id: "llama",
      name: "llama-3.3-70b (local)",
      tier: "FAST",
      reasoning: 87,
      latency: "22ms",
      cost: "$0.00 (Local)",
    },
  ];

  return (
    <section id="features" className="py-24 bg-[#0a0a0a] relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/2 left-0 w-96 h-96 bg-[#0065fc]/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-[#54a2ff]/5 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 md:px-12 xl:px-0 relative z-10">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end pb-12 gap-x-6 gap-y-6 items-center justify-between">
          <div className="max-w-2xl text-center md:text-left">
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white tracking-tight leading-tight">
              Everything needed to create{" "}
              <span className="bg-gradient-to-r from-[#6ea8ff] via-[#0065fc] to-[#54a2ff] bg-clip-text text-transparent">
                autonomous AI agents
              </span>
            </h2>
            <p className="mt-4 text-white/60 text-sm md:text-base leading-relaxed">
              From simple task automation to complex multi-agent orchestration, Solaris handles
              the entire AI agent lifecycle in one unified platform.
            </p>
          </div>

          <a
            href="#pricing"
            className="group hidden md:inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-medium text-white/90 bg-white/[0.04] hover:bg-white/[0.08] border border-white/10 hover:border-white/20 transition-all duration-300"
          >
            <span>Book Demo</span>
            <ArrowRight className="size-4 transition-transform duration-300 group-hover:translate-x-1" />
          </a>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
          {/* Card 1: Visual DAG Workflow Builder (Col 7) */}
          <div className="md:col-span-7 rounded-2xl bg-gradient-to-br from-[#141418] to-[#0d0d10] border border-white/10 p-6 sm:p-8 flex flex-col justify-between relative overflow-hidden group hover:border-[#0065fc]/40 transition-all duration-500 shadow-xl">
            <div className="relative z-10">
              <div className="size-10 rounded-xl bg-[#0065fc]/15 border border-[#0065fc]/30 flex items-center justify-center text-[#54a2ff] mb-5">
                <GitBranch className="size-5" />
              </div>
              <h3 className="text-xl sm:text-2xl font-semibold text-white tracking-tight">
                Design intelligent agents with intuitive workflows
              </h3>
              <p className="mt-2 text-sm sm:text-base text-white/60 leading-relaxed max-w-lg">
                Create sophisticated AI agents with drag-and-drop DAG interfaces, deterministic
                type safety, and automated parallel execution.
              </p>
            </div>

            {/* Interactive Visual DAG representation */}
            <div className="mt-8 rounded-xl bg-black/50 border border-white/10 p-5 relative overflow-hidden font-mono">
              <div className="flex items-center justify-between text-xs text-white/40 pb-3 border-b border-white/10">
                <span>GRAPH_ID: orchestrator_v4</span>
                <span className="text-emerald-400 flex items-center gap-1">
                  <span className="size-1.5 rounded-full bg-emerald-400 animate-ping" />
                  STRICT_DAG_COMPILED
                </span>
              </div>

              <div className="mt-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
                {/* Node 1 */}
                <div className="w-full sm:w-auto p-3 rounded-lg bg-[#0065fc]/20 border border-[#0065fc]/50 text-white text-center">
                  <div className="text-[10px] text-[#54a2ff] font-semibold">TRIGGER</div>
                  <div className="font-bold mt-0.5">Prompt Ingestion</div>
                  <div className="text-[10px] text-white/50">Async Queue</div>
                </div>

                <div className="hidden sm:block text-[#54a2ff] font-bold">➔</div>

                {/* Node 2 */}
                <div className="w-full sm:w-auto p-3 rounded-lg bg-white/5 border border-white/15 text-white text-center">
                  <div className="text-[10px] text-purple-400 font-semibold">ROUTER</div>
                  <div className="font-bold mt-0.5">Heuristic Scoring</div>
                  <div className="text-[10px] text-white/50">9 Deterministic Rules</div>
                </div>

                <div className="hidden sm:block text-[#54a2ff] font-bold">➔</div>

                {/* Node 3 */}
                <div className="w-full sm:w-auto p-3 rounded-lg bg-emerald-500/15 border border-emerald-500/40 text-white text-center">
                  <div className="text-[10px] text-emerald-400 font-semibold">EXECUTION</div>
                  <div className="font-bold mt-0.5">Agent Consensus</div>
                  <div className="text-[10px] text-white/50">Bounded Reflexion (max 3)</div>
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Advanced Reasoning & Model Selector (Col 5) */}
          <div className="md:col-span-5 rounded-2xl bg-gradient-to-br from-[#141418] to-[#0d0d10] border border-white/10 p-6 sm:p-8 flex flex-col justify-between relative overflow-hidden group hover:border-[#0065fc]/40 transition-all duration-500 shadow-xl">
            <div className="relative z-10">
              <div className="size-10 rounded-xl bg-purple-500/15 border border-purple-500/30 flex items-center justify-center text-purple-400 mb-5">
                <Brain className="size-5" />
              </div>
              <h3 className="text-xl sm:text-2xl font-semibold text-white tracking-tight">
                Advanced reasoning, fully customizable
              </h3>
              <p className="mt-2 text-sm sm:text-base text-white/60 leading-relaxed">
                Dynamically dispatch requests across cloud & local LLMs with fine-grained routing
                and zero vendor lock-in.
              </p>
            </div>

            {/* Interactive Model Selector list */}
            <div className="mt-6 space-y-2 font-mono text-xs">
              {models.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setSelectedModel(m.id as any)}
                  className={`w-full text-left p-3 rounded-xl border flex items-center justify-between transition-all ${
                    selectedModel === m.id
                      ? "bg-[#0065fc]/20 border-[#0065fc] text-white shadow-[0_0_15px_rgba(0,101,252,0.25)]"
                      : "bg-black/30 border-white/5 text-white/60 hover:border-white/15 hover:text-white"
                  }`}
                >
                  <div>
                    <div className="font-semibold text-white flex items-center gap-2">
                      <span>{m.name}</span>
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/10 text-white/80">
                        {m.tier}
                      </span>
                    </div>
                    <div className="text-[10px] text-white/40 mt-0.5">
                      Reasoning: {m.reasoning}% • Latency: {m.latency}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[11px] text-[#6ea8ff] font-bold">{m.cost}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Card 3: Autonomous Decision-Making & Reflexion Loop (Col 5) */}
          <div className="md:col-span-5 rounded-2xl bg-gradient-to-br from-[#141418] to-[#0d0d10] border border-white/10 p-6 sm:p-8 flex flex-col justify-between relative overflow-hidden group hover:border-[#0065fc]/40 transition-all duration-500 shadow-xl">
            <div className="relative z-10">
              <div className="size-10 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 mb-5">
                <Repeat className="size-5" />
              </div>
              <h3 className="text-xl sm:text-2xl font-semibold text-white tracking-tight">
                Autonomous decision-making
              </h3>
              <p className="mt-2 text-sm sm:text-base text-white/60 leading-relaxed">
                Bounded self-correcting reflexion loop. Agents autonomously critique, verify
                test suites, and remediate errors before delivering output.
              </p>
            </div>

            {/* Reflexion Loop visual meter */}
            <div className="mt-6 rounded-xl bg-black/50 border border-white/10 p-4 font-mono text-xs">
              <div className="flex items-center justify-between text-white/40 mb-3">
                <span>REFLEXION_LOOP</span>
                <span className="text-amber-400">STATUS: CONVERGED</span>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between p-2 rounded bg-white/5 border border-white/5 text-[11px]">
                  <span className="text-white/80">Pass 1: Initial Generation</span>
                  <span className="text-amber-400">Score 0.74 (Need fix)</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded bg-white/5 border border-white/5 text-[11px]">
                  <span className="text-white/80">Pass 2: Critic Self-Correction</span>
                  <span className="text-emerald-400 font-bold">Score 0.98 (PASS)</span>
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-white/10 flex items-center justify-between text-[10px] text-white/50">
                <span>Loop guard: max 3 cycles</span>
                <span className="text-emerald-400">Cost overhead: &lt; 0.002$</span>
              </div>
            </div>
          </div>

          {/* Card 4: Universal Connectors & Tools (Col 7) */}
          <div className="md:col-span-7 rounded-2xl bg-gradient-to-br from-[#141418] to-[#0d0d10] border border-white/10 p-6 sm:p-8 flex flex-col justify-between relative overflow-hidden group hover:border-[#0065fc]/40 transition-all duration-500 shadow-xl">
            <div className="relative z-10">
              <div className="size-10 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-5">
                <Share2 className="size-5" />
              </div>
              <h3 className="text-xl sm:text-2xl font-semibold text-white tracking-tight">
                Connect to any data source or API
              </h3>
              <p className="mt-2 text-sm sm:text-base text-white/60 leading-relaxed max-w-lg">
                Built-in sandboxed tools for databases, CLI commands, vector search, and web APIs.
                Runs locally with zero external telemetry leakage.
              </p>
            </div>

            {/* Connectors grid */}
            <div className="mt-6 grid grid-cols-2 sm:grid-cols-3 gap-3">
              {[
                { name: "PostgreSQL / SQLite", type: "DB Storage", icon: "🐘" },
                { name: "FastAPI REST API", type: "HTTP Port 8000", icon: "⚡" },
                { name: "Sandboxed Bash", type: "Local FS", icon: "💻" },
                { name: "ChromaDB / SQLite-Vec", type: "Vector Memory", icon: "🧠" },
                { name: "GitHub & Git Worktrees", type: "Version Control", icon: "🐙" },
                { name: "Docker & Container", type: "Isolation", icon: "🐳" },
              ].map((conn) => (
                <div
                  key={conn.name}
                  className="p-3 rounded-xl bg-black/40 border border-white/10 hover:border-white/20 transition-all flex items-center gap-3"
                >
                  <span className="text-xl">{conn.icon}</span>
                  <div className="overflow-hidden">
                    <div className="text-xs font-semibold text-white truncate">{conn.name}</div>
                    <div className="text-[10px] text-white/40 truncate">{conn.type}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
