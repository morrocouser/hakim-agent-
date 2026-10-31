"use client";

/**
 * GlassCard — portage React/TypeScript du `glass-card` du clone 21st.dev.
 *
 * Ref: C:\Users\hp\Desktop\Scrapling App Studio-20260811T223456Z-1-001\Scraping App Studio\21st-dev-clone\src\index.css
 */
import React, { useState } from "react";
import { motion } from "framer-motion";

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  active?: boolean;
  onClick?: () => void;
}

export default function GlassCard({
  children,
  className = "",
  hover = true,
  active = false,
  onClick,
}: GlassCardProps) {
  return (
    <motion.div
      className={`glass-card-21 ${className}`}
      whileHover={hover ? { y: -4, transition: { duration: 0.25 } } : undefined}
      whileTap={onClick ? { scale: 0.98 } : undefined}
      data-active={active}
      onClick={onClick}
    >
      {children}
    </motion.div>
  );
}

/**
 * BentoGrid — portage du bento-grid 21st.dev avec grid-cols-12.
 * Garantit un remplissage dense (grid-flow-dense équivalent).
 */
export function BentoGrid({
  children,
  cols = 12,
  gap = "gap-5",
  className = "",
}: {
  children: React.ReactNode;
  cols?: 6 | 12 | 24;
  gap?: string;
  className?: string;
}) {
  const colMap = { 6: "grid-cols-6", 12: "grid-cols-12", 24: "grid-cols-24" };
  return (
    <div className={`bento-grid-21 ${colMap[cols]} ${gap} ${className}`}>
      {children}
    </div>
  );
}

/**
 * InteractiveButton — portage du bouton animé de HeroShowcase.
 * Effet gradient + hover physics + active scale.
 */
export function InteractiveButton({
  children,
  variant = "coral",
  onClick,
  className = "",
}: {
  children: React.ReactNode;
  variant?: "coral" | "indigo" | "cyan" | "emerald" | "purple";
  onClick?: () => void;
  className?: string;
}) {
  const gradientMap: Record<string, string> = {
    coral: "from-[#cc785c] to-[#a9583e]",
    indigo: "from-[#cc785c] via-[#e8a55a] to-[#5db8a6]",
    cyan: "from-[#5db8a6] via-[#cc785c] to-[#a9583e]",
    emerald: "from-[#5db872] via-[#5db8a6] to-[#cc785c]",
    purple: "from-[#cc785c] via-[#a9583e] to-[#252320]",
  };

  return (
    <motion.button
      className={`btn-21 ${className}`}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
    >
      <motion.span
        className={`absolute inset-0 rounded-2xl bg-gradient-to-r ${gradientMap[variant]}`}
        animate={{
          opacity: [0.8, 1, 0.8],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      <span className="btn-21__inner relative z-10">{children}</span>
    </motion.button>
  );
}

/**
 * MetricCard — portage du Spotlight KPI de HeroShowcase.
 * Affiche une valeur, un label et un detail avec sparkline.
 */
export function MetricCard({
  value,
  label,
  detail,
  trend,
  className = "",
}: {
  value: string;
  label: string;
  detail?: string;
  trend?: "up" | "down" | "neutral";
  className?: string;
}) {
  const [sparkle, setSparkle] = useState(false);

  return (
    <motion.div
      className={`metric-card-21 ${className}`}
      whileHover={{ y: -2 }}
      onMouseEnter={() => setSparkle(true)}
      onMouseLeave={() => setSparkle(false)}
    >
      <span className="value">{value}</span>
      <strong className="label">{label}</strong>
      {detail && <span className="detail">{detail}</span>}
      {trend && (
        <motion.span
          className="detail"
          animate={{ opacity: sparkle ? 1 : 0.6 }}
          style={{ color: "var(--accent)" }}
        >
          {trend === "up" ? "↗" : trend === "down" ? "↘" : "→"} Tendance
        </motion.span>
      )}
    </motion.div>
  );
}
