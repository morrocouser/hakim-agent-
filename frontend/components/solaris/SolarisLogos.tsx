"use client";

import React from "react";
import Image from "next/image";
import { ArrowRight } from "lucide-react";

const companies = [
  { name: "Linear", file: "company-logo-1.png", width: 140, height: 36 },
  { name: "OpenAI", file: "company-logo-2.png", width: 140, height: 36 },
  { name: "Supabase", file: "company-logo-3.png", width: 140, height: 36 },
  { name: "Vercel", file: "company-logo-4.png", width: 140, height: 36 },
  { name: "Retool", file: "company-logo-5.png", width: 140, height: 36 },
  { name: "Attentive", file: "company-logo-6.png", width: 140, height: 36 },
  { name: "Rippling", file: "company-logo-7.png", width: 140, height: 36 },
  { name: "Descript", file: "company-logo-8.png", width: 140, height: 36 },
];

export default function SolarisLogos() {
  return (
    <section className="relative py-12 bg-[#0a0a0a] border-y border-white/[0.06] overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 md:px-12 xl:px-0">
        <div className="max-w-4xl mx-auto grid grid-cols-2 sm:grid-cols-4 gap-6 md:gap-10 py-6 px-6 relative group items-center justify-items-center">
          {/* Interactive Hover Overlay with Link */}
          <div className="absolute inset-0 bg-[#0a0a0a]/75 backdrop-blur-xs z-20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 ease-in-out rounded-xl">
            <a
              href="#testimonials"
              className="flex items-center gap-2 text-white hover:text-white/80 text-sm font-medium transform translate-y-3 group-hover:translate-y-0 transition-transform duration-300 bg-white/10 px-5 py-2 rounded-full border border-white/20 shadow-lg"
            >
              <span>Companies using Solaris</span>
              <ArrowRight className="size-4" />
            </a>
          </div>

          {/* Logo Grid */}
          {companies.map((company) => (
            <div
              key={company.name}
              className="relative h-10 w-[140px] flex items-center justify-center opacity-60 hover:opacity-100 transition-opacity duration-300"
            >
              <Image
                src={`/assets/${company.file}`}
                alt={company.name}
                fill
                sizes="140px"
                className="object-contain filter grayscale contrast-125 brightness-150"
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
