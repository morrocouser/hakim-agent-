"use client";

import React from "react";
import SolarisNavbar from "@/components/solaris/SolarisNavbar";
import SolarisHero from "@/components/solaris/SolarisHero";
import SolarisLogos from "@/components/solaris/SolarisLogos";
import SolarisBento from "@/components/solaris/SolarisBento";
import SolarisEnterpriseFeatures from "@/components/solaris/SolarisEnterpriseFeatures";
import SolarisUseCases from "@/components/solaris/SolarisUseCases";
import SolarisTestimonials from "@/components/solaris/SolarisTestimonials";
import SolarisPricing from "@/components/solaris/SolarisPricing";
import SolarisCTA from "@/components/solaris/SolarisCTA";
import SolarisFooter from "@/components/solaris/SolarisFooter";

export default function SolarisHomePage() {
  return (
    <main className="min-h-screen bg-[#0a0a0a] text-white selection:bg-[#0065fc] selection:text-white font-sans antialiased overflow-x-hidden">
      {/* Sticky Navigation */}
      <SolarisNavbar />

      {/* Hero Section with Live App Shell & Swarm Simulator */}
      <SolarisHero />

      {/* Social Proof / Companies using Solaris */}
      <SolarisLogos />

      {/* Core Bento Grid Features */}
      <SolarisBento />

      {/* 6-Card Spotlight Enterprise Capabilities */}
      <SolarisEnterpriseFeatures />

      {/* Business Use Cases & Live Simulations */}
      <SolarisUseCases />

      {/* Customer Testimonials & Reviews Slider */}
      <SolarisTestimonials />

      {/* Scalable Pricing Calculator */}
      <SolarisPricing />

      {/* Call to Action Banner */}
      <SolarisCTA />

      {/* Rich Footer */}
      <SolarisFooter />
    </main>
  );
}
