"use client";

import React from "react";
import AgentPlanning from "@/components/ui/agent-planning";
import { Component as AiPlanningComponent } from "@/components/ui/ai-planning";

export default function PlanningDemoPage() {
  return (
    <main className="min-h-screen w-full bg-background text-foreground p-8 flex flex-col items-center">
      <div className="w-full max-w-3xl space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">AI Agent Planning & Timeline Component</h1>
          <p className="text-muted-foreground text-sm">Interactive step-by-step agent reasoning timeline accordion</p>
        </div>

        {/* Agent Planning Timeline Component */}
        <AgentPlanning />

        {/* AI Planning Counter Component */}
        <div className="border border-border rounded-xl p-6 bg-card shadow-sm">
          <h2 className="text-lg font-semibold mb-4 text-center">Interactive Counter Component (ai-planning.tsx)</h2>
          <AiPlanningComponent />
        </div>
      </div>
    </main>
  );
}
