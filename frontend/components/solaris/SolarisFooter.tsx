"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { Github, Twitter, Linkedin, Disc as Discord, Shield, CheckCircle2 } from "lucide-react";

export default function SolarisFooter() {
  const footerSections = [
    {
      title: "Platform",
      links: [
        { label: "Autonomous Agents", href: "#features" },
        { label: "Multi-Agent Orchestration", href: "#capabilities" },
        { label: "Memory Systems", href: "/memory" },
        { label: "Enterprise Security", href: "#capabilities" },
        { label: "API Gateway", href: "/demo" },
      ],
    },
    {
      title: "Resources",
      links: [
        { label: "Documentation", href: "#features" },
        { label: "API Reference", href: "/demo" },
        { label: "Agent Templates", href: "/agents" },
        { label: "Thinking & Planning", href: "/planning-demo" },
        { label: "Changelog", href: "#" },
      ],
    },
    {
      title: "Use Cases",
      links: [
        { label: "Customer Support", href: "#solutions" },
        { label: "Sales & Marketing", href: "#solutions" },
        { label: "Process Automation", href: "#solutions" },
        { label: "Data Analysis", href: "#solutions" },
        { label: "Autonomous Coding", href: "/diff-demo" },
      ],
    },
    {
      title: "Company",
      links: [
        { label: "About Us", href: "#" },
        { label: "Careers", href: "#" },
        { label: "Contact Sales", href: "mailto:contact@solaris.ai" },
        { label: "Privacy Policy", href: "#" },
        { label: "Terms of Service", href: "#" },
      ],
    },
  ];

  return (
    <footer className="w-full bg-[#0a0a0a] border-t border-white/10 relative overflow-hidden">
      {/* Subtle background grid pattern */}
      <div className="absolute inset-0 h-full w-full opacity-30 bg-[linear-gradient(to_right,#ffffff08_1px,transparent_1px),linear-gradient(to_bottom,#ffffff08_1px,transparent_1px)] bg-[size:4rem_4rem] pointer-events-none" />

      <div className="mx-auto max-w-7xl px-6 md:px-12 pt-16 pb-12 relative z-10">
        <div className="flex flex-col lg:flex-row gap-12 lg:gap-16 justify-between">
          {/* Brand info */}
          <div className="flex flex-col items-start gap-5 max-w-sm">
            <Link href="/" className="inline-block">
              <div className="relative h-10 w-36">
                <Image
                  src="/assets/solaris-logo.svg"
                  alt="Solaris Logo"
                  fill
                  className="object-contain object-left"
                />
              </div>
            </Link>

            <p className="text-sm text-white/60 leading-relaxed">
              Solaris empowers teams to create, deploy, &amp; manage intelligent AI agents at scale.
            </p>

            {/* Social Icons */}
            <div className="flex items-center gap-4 text-white/50">
              <a
                href="https://github.com"
                target="_blank"
                rel="noreferrer"
                className="hover:text-white transition-colors"
                aria-label="GitHub"
              >
                <Github className="size-5" />
              </a>
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noreferrer"
                className="hover:text-white transition-colors"
                aria-label="Twitter / X"
              >
                <Twitter className="size-5" />
              </a>
              <a
                href="https://linkedin.com"
                target="_blank"
                rel="noreferrer"
                className="hover:text-white transition-colors"
                aria-label="LinkedIn"
              >
                <Linkedin className="size-5" />
              </a>
            </div>

            {/* System Status Pill */}
            <div className="mt-2 inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs font-mono text-emerald-400">
              <span className="size-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>All Systems Operational (99.99%)</span>
            </div>
          </div>

          {/* Links Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 flex-1">
            {footerSections.map((section) => (
              <div key={section.title} className="flex flex-col gap-3">
                <h4 className="text-xs font-mono uppercase tracking-wider text-white font-semibold">
                  {section.title}
                </h4>
                <ul className="space-y-2 text-sm">
                  {section.links.map((link) => (
                    <li key={link.label}>
                      <a
                        href={link.href}
                        className="text-white/60 hover:text-white transition-colors duration-200"
                      >
                        {link.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom copyright row */}
        <div className="mt-14 pt-8 border-t border-white/[0.08] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-white/40">
          <div>
            Solaris Labs Software, Inc. © {new Date().getFullYear()}. All rights reserved.
          </div>
          <div className="flex items-center gap-6">
            <a href="#" className="hover:text-white transition-colors">
              Privacy Notice
            </a>
            <a href="#" className="hover:text-white transition-colors">
              Terms of Use
            </a>
            <a href="#" className="hover:text-white transition-colors">
              Security
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
