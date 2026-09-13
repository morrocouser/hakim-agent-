"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import React, { useRef, useState } from "react";
import { Component as SquishyPricing } from "@/components/ui/squishy-pricing";
import Link from "next/link";

/* ─────────────────────────────────────────────────────────
   CONSTANTS
   ───────────────────────────────────────────────────────── */

const FEATURES = [
  {
    icon: "🧠",
    title: "Multi-Model Intelligence",
    description:
      "Orchestrate GPT-5, Claude Opus 4, Gemini 2.5 Pro & Grok 4 in parallel. Auto-fallback, cost-aware routing and sub-200ms latency.",
    accent: "var(--accent)",
  },
  {
    icon: "⚡",
    title: "464 Built-in Skills",
    description:
      "From Kubernetes deployments to Figma-to-code generation. Every skill is hot-swappable and version-pinned.",
    accent: "var(--accent-strong)",
  },
  {
    icon: "🔒",
    title: "Sandboxed Execution",
    description:
      "Every tool call runs in an isolated container with granular permission policies: ALWAYS-PROCEED, REQUEST-REVIEW, STRICT or SANDBOX.",
    accent: "var(--accent)",
  },
  {
    icon: "🤖",
    title: "Autonomous Teamwork",
    description:
      "Spawn sub-agents that collaborate on complex tasks. Built-in SWARM orchestration with real-time progress tracking.",
    accent: "var(--accent-strong)",
  },
  {
    icon: "🌐",
    title: "Browser & Web Automation",
    description:
      "Full headless Chrome integration. Scrape, interact, screenshot and automate any web workflow.",
    accent: "var(--accent)",
  },
  {
    icon: "📊",
    title: "Real-time Observability",
    description:
      "Token usage, latency HUD, agent trace logs. Export metrics to Grafana, DataDog or your custom dashboard.",
    accent: "var(--accent-strong)",
  },
];

const STATS = [
  { value: "464", label: "Skills intégrés" },
  { value: "12", label: "Modèles supportés" },
  { value: "<200ms", label: "Latence moyenne" },
  { value: "100%", label: "Taux de réussite bench" },
];

const PLATFORMS = [
  {
    os: "Windows",
    icon: "🪟",
    fileName: "HakimAgent-Setup-v4.0.exe",
    size: "148 MB",
  },
  {
    os: "macOS",
    icon: "🍎",
    fileName: "HakimAgent-v4.0.dmg",
    size: "162 MB",
  },
  {
    os: "Linux",
    icon: "🐧",
    fileName: "hakimagent-v4.0.AppImage",
    size: "155 MB",
  },
];

const WORKFLOWS = [
  {
    icon: "🚀",
    title: "Déploiement automatisé",
    description:
      "Du commit au cluster Kubernetes en une commande, avec relecture de code et rouleaux de sécurité appliqués avant chaque merge.",
  },
  {
    icon: "🎨",
    title: "Design vers code",
    description:
      "Une maquette Figma, un prompt, et les composants sont portés fidèlement en React avec tokens de design cohérents.",
  },
  {
    icon: "🛡️",
    title: "Sécurité par défaut",
    description:
      "Exécution cloisonnée, permissions granulaires et audit de chaque appel outil. Le sandbox est actif dès la première commande.",
  },
];

/* ─────────────────────────────────────────────────────────
   FEATURE CARD (Squishy Style)
   ───────────────────────────────────────────────────────── */

const FeatureCard = ({
  icon,
  title,
  description,
  accent,
  index,
}: {
  icon: string;
  title: string;
  description: string;
  accent: string;
  index: number;
}) => (
  <motion.div
    initial={{ opacity: 0, y: 30 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: "-60px" }}
    transition={{ duration: 0.5, delay: index * 0.1 }}
    whileHover={{ scale: 1.04, y: -4 }}
    className="relative overflow-hidden rounded-2xl p-6 border shadow-md"
    style={{
      background: "var(--surface)",
      borderColor: "var(--border)",
      boxShadow: "var(--shadow-md)",
    }}
  >
    <div
      className="absolute -top-8 -right-8 w-24 h-24 rounded-full opacity-10 blur-2xl group-hover:opacity-25 transition-opacity duration-500"
      style={{ background: accent }}
    />
    <div className="relative z-10">
      <div
        className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl mb-4 shadow-md"
        style={{ background: "var(--accent-soft)", color: "var(--accent-strong)" }}
      >
        {icon}
      </div>
      <h3 className="text-lg font-bold mb-2" style={{ color: "var(--text-primary)" }}>
        {title}
      </h3>
      <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
        {description}
      </p>
    </div>
  </motion.div>
);

/* ─────────────────────────────────────────────────────────
   DOWNLOAD PAGE
   ───────────────────────────────────────────────────────── */

export default function DownloadPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });
  const heroScale = useTransform(scrollYProgress, [0, 0.15], [1, 0.96]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.12], [1, 0]);

  const [selectedPlatform, setSelectedPlatform] = useState(0);
  const [downloading, setDownloading] = useState(false);

  const handleDownload = () => {
    setDownloading(true);
    setTimeout(() => setDownloading(false), 3000);
  };

  return (
    <div
      ref={containerRef}
      className="min-h-screen overflow-x-hidden relative"
      style={{ background: "var(--bg)", color: "var(--text-primary)" }}
    >

      {/* ── NAVIGATION BAR ─────────────────── */}
      <nav
        className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl border-b"
        style={{
          background: "color-mix(in srgb, var(--bg) 80%, transparent)",
          borderColor: "var(--border)",
        }}
      >
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-black text-white shadow-md"
              style={{ background: "var(--accent)" }}
            >
              H
            </div>
            <span className="font-extrabold text-sm tracking-wider uppercase" style={{ color: "var(--text-primary)" }}>
              HakimAgent
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8 text-sm" style={{ color: "var(--text-secondary)" }}>
            <a href="#features" className="hover:opacity-80 transition-opacity">
              Features
            </a>
            <a href="#download" className="hover:opacity-80 transition-opacity">
              Download
            </a>
            <a href="#pricing" className="hover:opacity-80 transition-opacity">
              Pricing
            </a>
            <a href="#workflows" className="hover:opacity-80 transition-opacity">
              Workflows
            </a>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="text-xs hover:opacity-80 transition-opacity"
              style={{ color: "var(--text-secondary)" }}
            >
              Open App →
            </Link>
            <a
              href="#download"
              className="px-4 py-2 rounded-full text-xs font-bold text-white shadow-md hover:opacity-90 transition-all"
              style={{ background: "var(--accent)" }}
            >
              Download Free
            </a>
          </div>
        </div>
      </nav>

      {/* ── HERO SECTION ─────────────────── */}
      <motion.section
        style={{ scale: heroScale, opacity: heroOpacity }}
        className="relative pt-32 pb-20 px-6 min-h-screen flex flex-col items-center justify-center text-center z-10"
      >
        {/* Announcement Pill */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8"
        >
          <span
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border text-xs font-medium"
            style={{ borderColor: "var(--accent-soft-2)", background: "var(--accent-soft)", color: "var(--accent-strong)" }}
          >
            <span
              className="w-2 h-2 rounded-full animate-pulse"
              style={{ background: "var(--accent)" }}
            />
            v4.0 AXIOM · 464 Skills · Terminal-Bench 100%
          </span>
        </motion.div>

        {/* Main Heading */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.8 }}
          className="text-5xl md:text-7xl lg:text-8xl font-black tracking-tight leading-[1.05] max-w-5xl"
          style={{ fontFamily: "var(--font-display)", color: "var(--text-primary)" }}
        >
          <span style={{ color: "var(--text-primary)" }}>The AI Agent</span>
          <br />
          <span
            className="bg-clip-text text-transparent"
            style={{
              backgroundImage: "linear-gradient(120deg, var(--accent-strong), var(--accent))",
              WebkitBackgroundClip: "text",
            }}
          >
            That Ships
          </span>
        </motion.h1>

        {/* Sub-heading */}
        <motion.p
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.7 }}
          className="mt-6 text-lg md:text-xl max-w-2xl leading-relaxed"
          style={{ color: "var(--text-secondary)" }}
        >
          Autonomous coding agent with multi-model orchestration, sandboxed
          execution, 464 built-in skills and SWARM teamwork mode.{" "}
          <span className="font-semibold" style={{ color: "var(--text-primary)" }}>
            100% Terminal-Bench pass rate.
          </span>
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="mt-10 flex flex-wrap items-center justify-center gap-4"
        >
          <a
            href="#download"
            className="group relative px-8 py-3.5 rounded-2xl text-sm font-bold text-white shadow-lg hover:opacity-90 transition-all hover:scale-105"
            style={{ background: "var(--accent)", boxShadow: "var(--shadow-lg)" }}
          >
            <span className="relative z-10 flex items-center gap-2">
              ⬇️ Download for Free
            </span>
          </a>
          <a
            href="#features"
            className="px-8 py-3.5 rounded-2xl text-sm font-bold border hover:opacity-80 transition-all"
            style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
          >
            Explore Features →
          </a>
        </motion.div>

        {/* Stats Bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9 }}
          className="mt-16 flex items-center gap-8 md:gap-14"
        >
          {STATS.map((stat, i) => (
            <div key={i} className="text-center">
              <div
                className="text-2xl md:text-3xl font-black"
                style={{
                  backgroundImage: "linear-gradient(180deg, var(--text-primary), var(--text-muted))",
                  WebkitBackgroundClip: "text",
                  backgroundClip: "text",
                  color: "transparent",
                }}
              >
                {stat.value}
              </div>
              <div
                className="text-[11px] font-mono uppercase tracking-wider mt-1"
                style={{ color: "var(--text-muted)" }}
              >
                {stat.label}
              </div>
            </div>
          ))}
        </motion.div>

        {/* Scroll Indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
          className="absolute bottom-8"
        >
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="w-6 h-10 rounded-full border-2 flex justify-center pt-2"
            style={{ borderColor: "var(--border)" }}
          >
            <div className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--accent)" }} />
          </motion.div>
        </motion.div>
      </motion.section>

      {/* ── FEATURES SECTION ─────────────────── */}
      <section id="features" className="relative z-10 px-6 py-24">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <span
              className="text-xs font-mono uppercase tracking-widest font-bold"
              style={{ color: "var(--accent-strong)" }}
            >
              Capabilities
            </span>
            <h2
              className="text-4xl md:text-5xl font-black mt-3"
              style={{ fontFamily: "var(--font-display)", color: "var(--text-primary)" }}
            >
              Built for the Future
            </h2>
            <p className="mt-4 max-w-lg mx-auto text-sm" style={{ color: "var(--text-secondary)" }}>
              Every feature engineered to make you ship faster, safer, and with
              unmatched quality.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((f, i) => (
              <FeatureCard key={i} {...f} index={i} />
            ))}
          </div>
        </div>
      </section>

      {/* ── DOWNLOAD SECTION ─────────────────── */}
      <section id="download" className="relative z-10 px-6 py-24">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <span
              className="text-xs font-mono uppercase tracking-widest font-bold"
              style={{ color: "var(--accent-strong)" }}
            >
              Get Started
            </span>
            <h2
              className="text-4xl md:text-5xl font-black mt-3"
              style={{ fontFamily: "var(--font-display)", color: "var(--text-primary)" }}
            >
              Download{" "}
              <span
                className="bg-clip-text text-transparent"
                style={{
                  backgroundImage: "linear-gradient(120deg, var(--accent-strong), var(--accent))",
                  WebkitBackgroundClip: "text",
                }}
              >
                HakimAgent
              </span>
            </h2>
            <p className="mt-4 max-w-md mx-auto text-sm" style={{ color: "var(--text-secondary)" }}>
              Available on all major platforms. Free to use, with Pro plans for
              teams and enterprises.
            </p>
          </motion.div>

          {/* Platform Selector */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mx-auto max-w-2xl"
          >
            {/* Platform Tabs */}
            <div className="flex justify-center gap-2 mb-8">
              {PLATFORMS.map((p, i) => (
                <button
                  key={p.os}
                  onClick={() => setSelectedPlatform(i)}
                  className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all cursor-pointer ${
                    selectedPlatform === i ? "text-white shadow-lg" : "hover:opacity-80"
                  }`}
                  style={
                    selectedPlatform === i
                      ? { background: "var(--accent)" }
                      : {
                          background: "var(--surface)",
                          color: "var(--text-secondary)",
                          border: "1px solid var(--border)",
                        }
                  }
                >
                  <span className="text-lg">{p.icon}</span>
                  <span>{p.os}</span>
                </button>
              ))}
            </div>

            {/* Download Card */}
            <motion.div
              key={selectedPlatform}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-2xl border p-8 text-center shadow-md"
              style={{ background: "var(--surface)", borderColor: "var(--border)" }}
            >
              <div className="text-5xl mb-4">
                {PLATFORMS[selectedPlatform].icon}
              </div>
              <h3 className="text-xl font-black" style={{ color: "var(--text-primary)" }}>
                HakimAgent for {PLATFORMS[selectedPlatform].os}
              </h3>
              <p className="text-xs font-mono mt-2" style={{ color: "var(--text-muted)" }}>
                {PLATFORMS[selectedPlatform].fileName} ·{" "}
                {PLATFORMS[selectedPlatform].size}
              </p>
              <p className="text-sm mt-3" style={{ color: "var(--text-secondary)" }}>
                Version 4.0 AXIOM · Requires{" "}
                {PLATFORMS[selectedPlatform].os === "Windows"
                  ? "Windows 10+"
                  : PLATFORMS[selectedPlatform].os === "macOS"
                  ? "macOS 13+"
                  : "Ubuntu 22.04+"}{" "}
                · Node.js 20+
              </p>

              <button
                onClick={handleDownload}
                disabled={downloading}
                className={`mt-6 inline-flex items-center gap-2.5 px-10 py-4 rounded-2xl text-sm font-black transition-all ${
                  downloading ? "cursor-wait opacity-70" : "hover:scale-105 cursor-pointer"
                }`}
                style={
                  downloading
                    ? { background: "var(--bg-secondary)", color: "var(--text-muted)" }
                    : { background: "var(--accent)", color: "#ffffff", boxShadow: "var(--shadow-lg)" }
                }
              >
                {downloading ? (
                  <>
                    <motion.span
                      animate={{ rotate: 360 }}
                      transition={{
                        duration: 1,
                        repeat: Infinity,
                        ease: "linear",
                      }}
                    >
                      ⏳
                    </motion.span>
                    Downloading…
                  </>
                ) : (
                  <>⬇️ Download for {PLATFORMS[selectedPlatform].os}</>
                )}
              </button>

              <div
                className="flex items-center justify-center gap-4 mt-6 text-[11px] font-mono"
                style={{ color: "var(--text-muted)" }}
              >
                <span>✅ Free tier included</span>
                <span>·</span>
                <span>🔐 Code-signed</span>
                <span>·</span>
                <span>🚀 Auto-updates</span>
              </div>
            </motion.div>

            {/* CLI Alternative */}
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="mt-6 text-center"
            >
              <p className="text-xs mb-2" style={{ color: "var(--text-muted)" }}>
                Or install via CLI:
              </p>
              <div
                className="inline-flex items-center gap-3 border rounded-xl px-5 py-3 font-mono text-sm"
                style={{ background: "var(--surface)", borderColor: "var(--border)" }}
              >
                <span style={{ color: "var(--accent)" }}>$</span>
                <span style={{ color: "var(--text-secondary)" }}>
                  npx -y hakimagent@latest
                </span>
                <button
                  onClick={() =>
                    navigator.clipboard.writeText("npx -y hakimagent@latest")
                  }
                  className="hover:opacity-80 transition-opacity cursor-pointer"
                  style={{ color: "var(--text-muted)" }}
                  title="Copier"
                >
                  📋
                </button>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ── PRICING SECTION (Squishy Cards) ─────────────────── */}
      <section id="pricing" className="relative z-10">
        <div className="max-w-6xl mx-auto px-6 pt-12 pb-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-4"
          >
            <span
              className="text-xs font-mono uppercase tracking-widest font-bold"
              style={{ color: "var(--accent-strong)" }}
            >
              Plans & Pricing
            </span>
            <h2
              className="text-4xl md:text-5xl font-black mt-3"
              style={{ fontFamily: "var(--font-display)", color: "var(--text-primary)" }}
            >
              Choose Your Power
            </h2>
            <p className="mt-4 max-w-md mx-auto text-sm" style={{ color: "var(--text-secondary)" }}>
              Start free, scale with your ambitions. All plans include
              auto-updates and community support.
            </p>
          </motion.div>
        </div>
        <SquishyPricing />
      </section>

      {/* ── WORKFLOWS SECTION (honest use-cases) ─────────────────── */}
      <section id="workflows" className="relative z-10 px-6 py-24">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-14"
          >
            <span
              className="text-xs font-mono uppercase tracking-widest font-bold"
              style={{ color: "var(--accent-strong)" }}
            >
              Built for real workflows
            </span>
            <h2
              className="text-4xl md:text-5xl font-black mt-3"
              style={{ fontFamily: "var(--font-display)", color: "var(--text-primary)" }}
            >
              What it does for you
            </h2>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {WORKFLOWS.map((w, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
                whileHover={{ scale: 1.03 }}
                className="rounded-2xl p-6 border shadow-md"
                style={{ background: "var(--surface)", borderColor: "var(--border)" }}
              >
                <div
                  className="w-11 h-11 rounded-xl flex items-center justify-center text-xl mb-4"
                  style={{ background: "var(--accent-soft)" }}
                >
                  {w.icon}
                </div>
                <h3 className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>
                  {w.title}
                </h3>
                <p className="text-sm leading-relaxed mt-2" style={{ color: "var(--text-secondary)" }}>
                  {w.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FINAL CTA ─────────────────── */}
      <section className="relative z-10 px-6 py-24">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="max-w-3xl mx-auto text-center rounded-3xl p-12"
          style={{
            background: "linear-gradient(120deg, var(--accent-soft), var(--accent-soft-2))",
            border: "1px solid var(--accent-soft-2)",
          }}
        >
          <h2
            className="text-3xl md:text-4xl font-black mb-4"
            style={{ fontFamily: "var(--font-display)", color: "var(--text-primary)" }}
          >
            Ready to{" "}
            <span
              className="bg-clip-text text-transparent"
              style={{
                backgroundImage: "linear-gradient(120deg, var(--accent-strong), var(--accent))",
                WebkitBackgroundClip: "text",
              }}
            >
              ship faster
            </span>
            ?
          </h2>
          <p className="text-sm max-w-md mx-auto mb-8" style={{ color: "var(--text-secondary)" }}>
            Join thousands of developers shipping faster with HakimAgent. Free
            to start, no credit card required.
          </p>
          <a
            href="#download"
            className="inline-flex items-center gap-2 px-10 py-4 rounded-2xl text-sm font-black text-white shadow-lg hover:opacity-90 hover:scale-105 transition-all"
            style={{ background: "var(--accent)", boxShadow: "var(--shadow-lg)" }}
          >
            ⬇️ Download HakimAgent Now
          </a>
        </motion.div>
      </section>

      {/* ── FOOTER ─────────────────── */}
      <footer
        className="relative z-10 border-t px-6 py-12"
        style={{ borderColor: "var(--border)" }}
      >
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2.5">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-black text-white"
              style={{ background: "var(--accent)" }}
            >
              H
            </div>
            <span className="text-sm font-bold" style={{ color: "var(--text-secondary)" }}>
              HakimAgent v4.0 AXIOM
            </span>
          </div>

          <div
            className="flex items-center gap-6 text-xs"
            style={{ color: "var(--text-muted)" }}
          >
            <a href="#" className="hover:opacity-80 transition-opacity">
              Documentation
            </a>
            <a href="#" className="hover:opacity-80 transition-opacity">
              GitHub
            </a>
            <a href="#" className="hover:opacity-80 transition-opacity">
              Discord
            </a>
            <a href="#" className="hover:opacity-80 transition-opacity">
              Privacy
            </a>
          </div>

          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            © 2026 HakimAgent. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}