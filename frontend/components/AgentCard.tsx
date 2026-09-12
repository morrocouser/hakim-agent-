'use client'

import { motion } from 'framer-motion'
import { AgentInfo } from '@/lib/api'
import { ArrowUpRight } from '@phosphor-icons/react'

interface Props {
  name: string
  info: AgentInfo
  index: number
}

export default function AgentCard({ name, info, index }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, type: 'spring', stiffness: 120, damping: 22 }}
      className="pro-card group cursor-pointer p-5 relative overflow-hidden"
    >
      <div
        className="absolute -top-10 -left-10 w-32 h-32 rounded-full pointer-events-none opacity-60"
        style={{ background: 'radial-gradient(circle, var(--accent-soft) 0%, transparent 70%)' }}
      />

      <div className="flex items-start justify-between mb-4 relative z-10">
        <div
          className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl transition-all duration-300 group-hover:scale-110"
          style={{
            background: 'var(--accent-soft)',
            border: '1.5px solid var(--border)',
          }}
        >
          {info.icon}
        </div>
        <ArrowUpRight
          className="w-5 h-5 opacity-0 group-hover:opacity-100 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 transition-all duration-200"
          style={{ color: 'var(--text-muted)' }}
        />
      </div>

      <div className="relative z-10">
        <h3
          className="text-base font-bold mb-1 tracking-tight"
          style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}
        >
          {info.label}
        </h3>
        <p className="text-mono mb-3 uppercase" style={{ color: 'var(--accent)', fontSize: 10 }}>
          {info.speciality}
        </p>
        <p className="text-sm leading-relaxed mb-4 line-clamp-2" style={{ color: 'var(--text-secondary)' }}>
          {info.description}
        </p>

        <div
          className="flex items-center justify-between pt-3"
          style={{ borderTop: '1.5px solid var(--border)' }}
        >
          <span className="text-mono" style={{ color: 'var(--text-muted)', fontSize: 10 }}>
            {name.replace('AGENT_', '')}
          </span>
          <span
            className="text-mono px-2 py-0.5 rounded-md"
            style={{
              fontSize: 10,
              background: 'var(--accent-soft)',
              border: '1px solid var(--border)',
              color: 'var(--accent)',
            }}
          >
            {info.default_model.split('/').pop()}
          </span>
        </div>
      </div>
    </motion.div>
  )
}
