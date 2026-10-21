"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";

const reviews = [
  {
    id: 1,
    quote:
      "I want to literally chat with nine hours of the footage that we have. “What do they think about this? What do they think about that?” I want to really test my own assumptions very quickly.",
    author: "Martin Jerkovic",
    role: "Lead Product Designer",
    companyLogo: "/assets/c-logo-1.png",
    avatar: "/assets/review-1.png",
  },
  {
    id: 2,
    quote:
      "The distinct yet familiar interface allows us to focus on the core user problems rather than reinventing interaction patterns. It's truly a game changer for our design system velocity.",
    author: "Sarah Chen",
    role: "Head of UX",
    companyLogo: "/assets/c-logo-2.png",
    avatar: "/assets/review-2.png",
  },
  {
    id: 3,
    quote:
      "Integrating these blocks has streamlined our workflow significantly. We're shipping features twice as fast with higher consistency across all our product lines.",
    author: "Alex Rivera",
    role: "VP of Engineering",
    companyLogo: "/assets/c-logo-3.png",
    avatar: "/assets/review-3.png",
  },
];

export default function SolarisTestimonials() {
  const [currentIdx, setCurrentIdx] = useState(0);

  // Auto rotate every 8 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIdx((prev) => (prev + 1) % reviews.length);
    }, 8000);
    return () => clearInterval(timer);
  }, [currentIdx]);

  const activeReview = reviews[currentIdx];

  return (
    <section id="testimonials" className="py-24 bg-[#0a0a0a] relative overflow-hidden">
      {/* Background Grid Texture */}
      <div
        className="absolute inset-0 z-0 opacity-40 pointer-events-none"
        style={{
          backgroundImage: "url('/assets/grid-bg.png')",
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      />

      <div className="max-w-5xl mx-auto px-6 md:px-12 relative z-10">
        <div className="min-h-[380px] md:min-h-[320px] flex flex-col justify-between">
          {/* Animated Quote & Author */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeReview.id}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.4 }}
              className="space-y-6"
            >
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 sm:gap-6">
                {/* Author Avatar */}
                <div className="relative size-16 sm:size-20 rounded-2xl overflow-hidden border border-white/20 shrink-0 shadow-xl">
                  <Image
                    src={activeReview.avatar}
                    alt={activeReview.author}
                    fill
                    className="object-cover"
                  />
                </div>

                {/* Company Logo & Author info on top */}
                <div>
                  <div className="relative h-7 w-28 mb-1">
                    <Image
                      src={activeReview.companyLogo}
                      alt="Company Logo"
                      fill
                      className="object-contain object-left filter contrast-125 brightness-150"
                    />
                  </div>
                  <div className="text-base sm:text-lg font-bold text-white">
                    {activeReview.author}
                  </div>
                  <div className="text-xs sm:text-sm text-white/60">
                    {activeReview.role}
                  </div>
                </div>
              </div>

              {/* Quote Headline */}
              <blockquote className="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-normal leading-relaxed text-white tracking-tight">
                “{activeReview.quote}”
              </blockquote>
            </motion.div>
          </AnimatePresence>

          {/* Slider Controls: 01, 02, 03 */}
          <div className="mt-10 pt-6 border-t border-white/10 flex items-center justify-between">
            <span className="text-xs font-mono text-white/40 uppercase tracking-widest">
              Verified Production Impact
            </span>

            <div className="flex items-center gap-3">
              {reviews.map((rev, idx) => (
                <button
                  key={rev.id}
                  type="button"
                  onClick={() => setCurrentIdx(idx)}
                  className={`relative px-3 py-1 text-sm font-mono transition-all duration-300 rounded-lg flex items-center gap-2 ${
                    currentIdx === idx
                      ? "text-white font-bold bg-white/10 border border-white/20"
                      : "text-white/40 hover:text-white/80"
                  }`}
                >
                  <span>0{rev.id}</span>
                  {currentIdx === idx && (
                    <span className="w-6 h-0.5 bg-[#0065fc] rounded-full inline-block" />
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
