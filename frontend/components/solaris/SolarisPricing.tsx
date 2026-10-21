"use client";

import React, { useState } from "react";
import Image from "next/image";
import { Check, Plus, Minus, ArrowRight, Sparkles } from "lucide-react";

export default function SolarisPricing() {
  const [isAnnual, setIsAnnual] = useState(false);
  const [userSeats, setUserSeats] = useState(3);

  // Pro price calculation from Solaris:
  // Base 3 users: $77/mo or $840/yr
  // Additional seats: $25/mo or $240/yr
  const extraSeats = Math.max(0, userSeats - 3);
  const proMonthly = 77 + 25 * extraSeats;
  const proAnnual = 840 + 240 * extraSeats;
  const displayPrice = isAnnual ? proAnnual : proMonthly;

  return (
    <section id="pricing" className="py-24 bg-[#0a0a0a] relative overflow-hidden">
      {/* Background radial ambient lights */}
      <div className="bg-[#0065FC]/10 absolute -top-[10%] left-[50%] h-[40%] w-[60%] -translate-x-1/2 rounded-full blur-3xl pointer-events-none" />
      <div className="bg-[#0065FC]/10 absolute -right-[10%] -bottom-[10%] h-[40%] w-[40%] rounded-full blur-3xl pointer-events-none" />
      <div className="bg-[#0065FC]/5 absolute -bottom-[10%] -left-[10%] h-[40%] w-[40%] rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 md:px-12 xl:px-0 relative z-10 flex flex-col items-center">
        {/* Title */}
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white text-center tracking-tight">
          Simple pricing, scaled to your needs
        </h2>
        <p className="mt-4 text-center text-sm md:text-base text-white/60 max-w-md leading-relaxed">
          Start for free, upgrade when your agent workforce scales.
        </p>

        {/* Billing cycle toggle */}
        <div className="mt-8 inline-flex bg-black/60 rounded-full p-1 items-center gap-1 border border-white/10 backdrop-blur-md">
          <button
            type="button"
            onClick={() => setIsAnnual(false)}
            className={`px-5 py-2 rounded-full text-xs sm:text-sm font-medium transition-all ${
              !isAnnual
                ? "bg-[#0065fc] text-white shadow-md"
                : "text-white/60 hover:text-white"
            }`}
          >
            Monthly
          </button>
          <button
            type="button"
            onClick={() => setIsAnnual(true)}
            className={`px-5 py-2 rounded-full text-xs sm:text-sm font-medium transition-all flex items-center gap-2 ${
              isAnnual
                ? "bg-[#0065fc] text-white shadow-md"
                : "text-white/60 hover:text-white"
            }`}
          >
            <span>Annual</span>
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              -10%
            </span>
          </button>
        </div>

        {/* 3 Pricing Cards Grid */}
        <div className="mt-14 grid grid-cols-1 md:grid-cols-3 gap-6 w-full items-stretch">
          {/* Card 1: Starter */}
          <div className="rounded-2xl p-6 sm:p-8 bg-[#121216]/80 border border-white/10 flex flex-col justify-between hover:border-white/20 transition-all duration-300 shadow-xl">
            <div>
              <div className="size-12 relative mb-4">
                <Image
                  src="/assets/starter.png"
                  alt="Starter Tier"
                  fill
                  className="object-contain"
                />
              </div>
              <h3 className="text-xl font-bold text-white">Starter</h3>
              <p className="text-xs text-white/50 mt-1">Perfect for trying out autonomous agents.</p>

              <div className="flex items-baseline gap-1 mt-6 mb-8">
                <span className="text-4xl sm:text-5xl font-bold text-white tracking-tight">$0</span>
                <span className="text-sm text-white/50">/free trial</span>
              </div>

              <div className="border-t border-white/10 pt-6">
                <p className="text-xs font-mono uppercase tracking-wider text-white/40 mb-4">
                  What&apos;s included:
                </p>
                <ul className="space-y-3 text-sm text-white/70">
                  <li className="flex items-center gap-2.5">
                    <Check className="size-4 text-[#54a2ff] shrink-0" />
                    <span>1 user included</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <Check className="size-4 text-[#54a2ff] shrink-0" />
                    <span>3 active agents</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <Check className="size-4 text-[#54a2ff] shrink-0" />
                    <span>1,000/month agent interactions</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <Check className="size-4 text-[#54a2ff] shrink-0" />
                    <span>Basic SQLite memory store</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <Check className="size-4 text-[#54a2ff] shrink-0" />
                    <span>Community support</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="mt-8 pt-4">
              <a
                href="#features"
                className="w-full inline-flex items-center justify-center gap-2 py-3 px-4 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-white font-medium text-sm transition-all"
              >
                <span>Get Started</span>
              </a>
              <div className="text-center text-[11px] text-white/40 mt-2 font-mono">
                No credit card required
              </div>
            </div>
          </div>

          {/* Card 2: Professional (Featured with electric blue glow) */}
          <div className="rounded-2xl p-6 sm:p-8 bg-gradient-to-b from-[#161a29] to-[#0e111d] border-2 border-[#0065fc] flex flex-col justify-between relative shadow-[0_0_50px_rgba(0,101,252,0.35)] scale-[1.02]">
            {/* Most popular badge */}
            <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-[#0065fc] text-white text-xs font-semibold flex items-center gap-1.5 shadow-[0_0_15px_rgba(0,101,252,0.8)]">
              <Sparkles className="size-3" />
              <span>Most Popular</span>
            </div>

            <div>
              <div className="size-12 relative mb-4">
                <Image
                  src="/assets/pro.png"
                  alt="Professional Tier"
                  fill
                  className="object-contain"
                />
              </div>
              <h3 className="text-xl font-bold text-white">Professional</h3>
              <p className="text-xs text-white/50 mt-1">For growing teams building production agents.</p>

              <div className="flex items-baseline justify-between mt-6 mb-4">
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl sm:text-5xl font-bold text-white tracking-tight">
                    ${displayPrice.toLocaleString()}
                  </span>
                  <span className="text-sm text-white/60">
                    /{isAnnual ? "year" : "month"}
                  </span>
                </div>
              </div>

              {/* Interactive user seats stepper */}
              <div className="p-3 rounded-xl bg-black/40 border border-white/10 flex items-center justify-between mb-6">
                <div>
                  <div className="text-xs font-semibold text-white">Team Members:</div>
                  <div className="text-[11px] text-white/50">{userSeats} users selected</div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setUserSeats((prev) => Math.max(3, prev - 1))}
                    disabled={userSeats <= 3}
                    className="size-7 rounded-lg bg-white/10 hover:bg-white/20 disabled:opacity-30 disabled:hover:bg-white/10 flex items-center justify-center text-white transition-colors"
                  >
                    <Minus className="size-3.5" />
                  </button>
                  <span className="text-sm font-mono font-bold text-white w-6 text-center">
                    {userSeats}
                  </span>
                  <button
                    type="button"
                    onClick={() => setUserSeats((prev) => prev + 1)}
                    className="size-7 rounded-lg bg-[#0065fc] hover:bg-[#1a74fc] flex items-center justify-center text-white transition-colors"
                  >
                    <Plus className="size-3.5" />
                  </button>
                </div>
              </div>

              <div className="border-t border-white/10 pt-4">
                <p className="text-xs font-mono uppercase tracking-wider text-white/40 mb-4">
                  What&apos;s included:
                </p>
                <ul className="space-y-3 text-sm text-white/80">
                  <li className="flex items-center gap-2.5">
                    <Check className="size-4 text-[#54a2ff] shrink-0" />
                    <span>{userSeats} users included (scalable)</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <Check className="size-4 text-[#54a2ff] shrink-0" />
                    <span>25 active concurrent agents</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <Check className="size-4 text-[#54a2ff] shrink-0" />
                    <span>50,000/month agent interactions</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <Check className="size-4 text-[#54a2ff] shrink-0" />
                    <span>Multi-agent orchestration protocols</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <Check className="size-4 text-[#54a2ff] shrink-0" />
                    <span>Vector memory &amp; semantic store</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <Check className="size-4 text-[#54a2ff] shrink-0" />
                    <span>Priority email &amp; Discord support</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="mt-8 pt-4">
              <a
                href="#features"
                className="w-full inline-flex items-center justify-center gap-2 py-3 px-4 rounded-full bg-[#0065fc] hover:bg-[#1a74fc] text-white font-semibold text-sm transition-all shadow-[0_0_20px_rgba(0,101,252,0.6)]"
              >
                <span>Start 14-Day Trial</span>
                <ArrowRight className="size-4" />
              </a>
              <div className="text-center text-[11px] text-[#6ea8ff] mt-2 font-mono">
                Cancel anytime • Full access
              </div>
            </div>
          </div>

          {/* Card 3: Enterprise */}
          <div className="rounded-2xl p-6 sm:p-8 bg-[#121216]/80 border border-white/10 flex flex-col justify-between hover:border-white/20 transition-all duration-300 shadow-xl">
            <div>
              <div className="size-12 relative mb-4">
                <Image
                  src="/assets/enterprise.png"
                  alt="Enterprise Tier"
                  fill
                  className="object-contain"
                />
              </div>
              <h3 className="text-xl font-bold text-white">Enterprise</h3>
              <p className="text-xs text-white/50 mt-1">Dedicated infrastructure and custom SLAs.</p>

              <div className="flex items-baseline gap-1 mt-6 mb-8">
                <span className="text-3xl sm:text-4xl font-bold text-white tracking-tight">Let&apos;s Talk</span>
              </div>

              <div className="border-t border-white/10 pt-6">
                <p className="text-xs font-mono uppercase tracking-wider text-white/40 mb-4">
                  What&apos;s included:
                </p>
                <ul className="space-y-3 text-sm text-white/70">
                  <li className="flex items-center gap-2.5">
                    <Check className="size-4 text-[#54a2ff] shrink-0" />
                    <span>Unlimited users &amp; workspaces</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <Check className="size-4 text-[#54a2ff] shrink-0" />
                    <span>Unlimited autonomous agents</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <Check className="size-4 text-[#54a2ff] shrink-0" />
                    <span>Dedicated VPC / On-premise runtime</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <Check className="size-4 text-[#54a2ff] shrink-0" />
                    <span>Custom LLM fine-tuning &amp; routing</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <Check className="size-4 text-[#54a2ff] shrink-0" />
                    <span>99.99% uptime SLA guarantee</span>
                  </li>
                  <li className="flex items-center gap-2.5">
                    <Check className="size-4 text-[#54a2ff] shrink-0" />
                    <span>24/7 dedicated engineering support</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="mt-8 pt-4">
              <a
                href="mailto:contact@solaris.ai"
                className="w-full inline-flex items-center justify-center gap-2 py-3 px-4 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-white font-medium text-sm transition-all"
              >
                <span>Contact Sales</span>
              </a>
              <div className="text-center text-[11px] text-white/40 mt-2 font-mono">
                Custom security &amp; BAA agreements
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
