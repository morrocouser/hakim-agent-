'use client'

import { motion } from 'framer-motion'
import { AgentInfo } from '@/lib/api'

interface Props {
  name: string
  info: AgentInfo
  index: number
}

export default function AgentMiniCard({ name, info, index }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05, type: 'spring', stiffness: 100, damping: 20 }}
      className="flex items-center gap-3 p-2.5 rounded-xl hover:bg-axiom-card-hover transition-colors cursor-pointer group"
    >
      <div className="w-9 h-9 rounded-lg bg-axiom-accent/10 flex items-center justify-center text-base group-hover:bg-axiom-accent/20 transition-colors">
        {info.icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate">{info.label}</div>
        <div className="text-[11px] text-axiom-muted truncate">{info.speciality}</div>
      </div>
      <div className="text-[10px] text-axiom-subtle font-mono opacity-0 group-hover:opacity-100 transition-opacity">
        {info.default_model.split('/').pop()}
      </div>
    </motion.div>
  )
}
