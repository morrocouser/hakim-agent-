"use client";

import React from "react";
import { ArrowRight, Sparkles } from "lucide-react";

export default function SolarisCTA() {
  return (
    <section className="py-24 bg-[#0a0a0a] relative overflow-hidden border-t border-white/[0.06]">
      {/* Background ambient lighting */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-[radial-gradient(ellipse_at_center,_rgba(0,101,252,0.18),_transparent_70%)] blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 md:px-12 xl:px-0 relative z-10 flex flex-col items-center text-center">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs text-white/80 mb-6 backdrop-blur-md">
          <Sparkles className="size-3 text-[#54a2ff]" />
          <span>Instant Setup in under 2 minutes</span>
        </div>

        {/* Title */}
        <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-white tracking-tight max-w-3xl leading-tight">
          Build your first{" "}
          <span className="bg-gradient-to-r from-[#6ea8ff] via-[#0065fc] to-[#54a2ff] bg-clip-text text-transparent">
            AI Agent
          </span>{" "}
          today
        </h2>

        {/* Subtitle */}
        <p className="mt-5 max-w-xl text-base sm:text-lg text-white/60 leading-relaxed font-normal">
          Join thousands of teams already automating their mission-critical workflows with
          intelligent, reliable, and autonomous software.
        </p>

        {/* Buttons */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
          <a
            href="#pricing"
            className="group relative inline-flex items-center justify-center gap-2 rounded-full px-8 py-3.5 text-base font-semibold text-white bg-[#0065fc] hover:bg-[#1a74fc] transition-all duration-300 shadow-[0_0_30px_rgba(0,101,252,0.5)] hover:shadow-[0_0_45px_rgba(0,101,252,0.8)]"
          >
            <span>Get Started Free</span>
            <ArrowRight className="size-4 transition-transform duration-300 group-hover:translate-x-1" />
          </a>

          <a
            href="#features"
            className="inline-flex items-center justify-center gap-2 rounded-full px-8 py-3.5 text-base font-medium text-white/80 hover:text-white bg-white/[0.04] hover:bg-white/[0.08] border border-white/10 hover:border-white/20 transition-all duration-300 backdrop-blur-md"
          >
            Book Demo
          </a>
        </div>
      </div>
    </section>
  );
}
