'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Cpu } from 'lucide-react'

interface HermesContextRingProps {
  usedTokens?: number
  maxTokens?: number
  size?: number
  strokeWidth?: number
  compact?: boolean
}

export default function HermesContextRing({
  usedTokens = 24580,
  maxTokens = 128000,
  size = 34,
  strokeWidth = 3,
  compact = false,
}: HermesContextRingProps) {
  const [showTooltip, setShowTooltip] = useState(false)

  const radius = (size - strokeWidth * 2) / 2
  const circumference = 2 * Math.PI * radius
  const percentage = Math.min(100, Math.max(0, (usedTokens / maxTokens) * 100))
  const strokeDashoffset = circumference - (percentage / 100) * circumference

  // Dynamic color based on usage
  let strokeColor = '#5db872' // Claude success
  let glowColor = 'rgba(93, 184, 114, 0.3)'
  if (percentage > 85) {
    strokeColor = '#c64545' // Claude danger
    glowColor = 'rgba(198, 69, 69, 0.4)'
  } else if (percentage > 60) {
    strokeColor = '#d4a017' // Claude warning
    glowColor = 'rgba(212, 160, 23, 0.4)'
  }

  const formatTokens = (val: number) => {
    if (val >= 1000) return `${(val / 1000).toFixed(1)}k`
    return `${val}`
  }

  return (
    <div
      className="relative flex items-center gap-2 cursor-pointer select-none"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="rotate-[-90deg] transition-all duration-500"
        >
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="var(--border)"
            strokeWidth={strokeWidth}
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{
              transition: 'stroke-dashoffset 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
              filter: `drop-shadow(0 0 3px ${glowColor})`,
            }}
          />
        </svg>

        {/* Center label or icon */}
        <span className="absolute text-[9px] font-mono font-medium text-[var(--text-primary)]">
          {Math.round(percentage)}%
        </span>
      </div>

      {!compact && (
        <div className="hidden sm:flex flex-col text-left leading-none">
          <span className="text-[10px] font-mono text-[var(--text-secondary)]">
            {formatTokens(usedTokens)} / {formatTokens(maxTokens)}
          </span>
          <span className="text-[9px] text-[var(--text-muted)] font-sans">tokens</span>
        </div>
      )}

      {/* Hover Tooltip */}
      <AnimatePresence>
        {showTooltip && (
          <motion.div
            initial={{ opacity: 0, y: 6, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 6, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full right-0 mt-2 z-50 w-52 p-2.5 rounded-xl bg-[var(--surface-card)] border border-[var(--border)] shadow-xl backdrop-blur-md pointer-events-none text-left"
          >
            <div className="flex items-center justify-between pb-1.5 border-b border-[var(--border)] mb-2">
              <span className="text-[11px] font-medium text-[var(--text-primary)] flex items-center gap-1.5">
                <Cpu className="w-3 h-3 text-[#cc785c]" />
                Fenêtre de Contexte
              </span>
              <span className="text-[10px] font-mono text-[#cc785c] font-semibold">
                {percentage.toFixed(1)}%
              </span>
            </div>
            <div className="space-y-1 text-[10px] font-mono text-[var(--text-muted)]">
              <div className="flex justify-between">
                <span>Utilisés :</span>
                <span className="text-[var(--text-primary)] font-semibold">{usedTokens.toLocaleString('fr-FR')} tokens</span>
              </div>
              <div className="flex justify-between">
                <span>Capacité max :</span>
                <span className="text-[var(--text-secondary)]">{maxTokens.toLocaleString('fr-FR')} tokens</span>
              </div>
              <div className="flex justify-between">
                <span>Restant :</span>
                <span className="text-[#5db872]">{Math.max(0, maxTokens - usedTokens).toLocaleString('fr-FR')} tokens</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
