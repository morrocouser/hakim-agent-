"use client";

import { ThinkingTool } from "@/components/ui/thinking-tool";
import { useState } from "react";

export default function ThinkingDemoPage() {
  const [state, setState] = useState<"thinking" | "thought">("thinking");

  return (
    <main className="flex flex-col items-center justify-center w-full min-h-screen bg-background text-foreground p-8 overflow-hidden">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">AI Thinking Tool Component</h1>
          <p className="text-sm text-muted-foreground">Shimmer animation & expandable reasoning monologue</p>
        </div>

        <div className="flex justify-center gap-3">
          <button
            onClick={() => setState("thinking")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              state === "thinking"
                ? "bg-indigo-500/20 text-indigo-400 border-indigo-500/40"
                : "bg-muted text-muted-foreground border-transparent"
            }`}
          >
            State: Thinking (Shimmer)
          </button>
          <button
            onClick={() => setState("thought")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              state === "thought"
                ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                : "bg-muted text-muted-foreground border-transparent"
            }`}
          >
            State: Thought (Static)
          </button>
        </div>

        <div className="p-6 rounded-2xl border border-border bg-card shadow-sm">
          <ThinkingTool
            state={state}
            content="Analyzing input constraints...\nEvaluating tool selection parameters for maximum specificity...\nExecuting step 1: Querying vector database for component pattern matching.\nExecuting step 2: Injecting responsive CSS variables."
            defaultOpen
          />
        </div>
      </div>
    </main>
  );
}
