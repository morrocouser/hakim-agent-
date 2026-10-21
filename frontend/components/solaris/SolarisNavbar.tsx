"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, ArrowRight, Sparkles, Terminal } from "lucide-react";

export default function SolarisNavbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { label: "Features", href: "#features" },
    { label: "Capabilities", href: "#capabilities" },
    { label: "Use Cases", href: "#solutions" },
    { label: "Pricing", href: "#pricing" },
    { label: "Reviews", href: "#testimonials" },
  ];

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-[#0a0a0a]/80 backdrop-blur-md border-b border-white/10 shadow-[0_4px_30px_rgba(0,0,0,0.5)]"
          : "bg-transparent border-b border-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 md:px-12 xl:px-0 h-16 md:h-20 flex items-center justify-between">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <div className="relative h-9 w-32 md:w-36">
            <Image
              src="/assets/solaris-logo.svg"
              alt="Solaris Logo"
              fill
              priority
              className="object-contain object-left"
            />
          </div>
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-1 lg:gap-2 bg-white/[0.03] border border-white/10 rounded-full px-4 py-1.5 backdrop-blur-md">
          {navLinks.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className="text-sm font-medium text-white/70 hover:text-white px-3 py-1 rounded-full transition-colors duration-200"
            >
              {item.label}
            </a>
          ))}
          <Link
            href="/demo"
            className="text-xs font-semibold text-[#54a2ff] hover:text-white px-2.5 py-1 rounded-full bg-[#0065fc]/15 border border-[#0065fc]/30 flex items-center gap-1 transition-colors"
          >
            <Sparkles className="size-3" />
            Console
          </Link>
        </nav>

        {/* Action Buttons */}
        <div className="hidden md:flex items-center gap-3">
          <Link
            href="/demo"
            className="text-sm text-white/80 hover:text-white font-medium px-4 py-2 transition-colors"
          >
            Sign in
          </Link>
          <a
            href="#pricing"
            className="group relative inline-flex items-center justify-center gap-2 rounded-full px-5 py-2 text-sm font-medium text-white bg-[#0065fc] hover:bg-[#1a74fc] transition-all duration-300 shadow-[0_0_20px_rgba(0,101,252,0.4)] hover:shadow-[0_0_30px_rgba(0,101,252,0.7)]"
          >
            <span>Get Started</span>
            <ArrowRight className="size-4 transition-transform duration-300 group-hover:translate-x-0.5" />
          </a>
        </div>

        {/* Mobile Menu Button */}
        <button
          type="button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2 text-white/80 hover:text-white focus:outline-none"
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? <X className="size-6" /> : <Menu className="size-6" />}
        </button>
      </div>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
            className="md:hidden bg-[#0a0a0a]/95 backdrop-blur-xl border-b border-white/10 px-6 py-6"
          >
            <div className="flex flex-col gap-4">
              {navLinks.map((item) => (
                <a
                  key={item.label}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="text-base text-white/80 hover:text-white font-medium py-1"
                >
                  {item.label}
                </a>
              ))}
              <div className="pt-4 border-t border-white/10 flex flex-col gap-3">
                <Link
                  href="/demo"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center justify-center gap-2 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white font-medium text-sm"
                >
                  <Terminal className="size-4 text-[#54a2ff]" />
                  Launch Agent Console
                </Link>
                <a
                  href="#pricing"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center justify-center gap-2 py-2.5 rounded-full bg-[#0065fc] text-white font-medium text-sm shadow-[0_0_20px_rgba(0,101,252,0.5)]"
                >
                  Get Started Free
                </a>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
