'use client'

import { motion } from 'framer-motion'

interface Props {
  score: number
  max?: number
}

export default function ScoreGauge({ score, max = 10 }: Props) {
  const percentage = Math.min((score / max) * 100, 100)
  const radius = 40
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (percentage / 100) * circumference

  return (
    <div className="relative w-[100px] h-[100px]">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="6"
          className="text-axiom-border"
        />
        <motion.circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="6"
          strokeLinecap="round"
          className="text-axiom-accent"
          initial={{ strokeDasharray: circumference, strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1, delay: 0.5, ease: 'easeOut' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-bold font-mono">{Math.round(score)}</span>
        <span className="text-[10px] text-axiom-muted">tokens</span>
      </div>
    </div>
  )
}
