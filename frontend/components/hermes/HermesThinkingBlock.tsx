'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, Sparkles, Copy, Check } from 'lucide-react'

interface HermesThinkingBlockProps {
  thinkingText?: string
  duration?: string
  defaultOpen?: boolean
}

export default function HermesThinkingBlock({
  thinkingText = `1. Analyser la requête de l'utilisateur et identifier les objectifs clés.
2. Vérifier les outils disponibles (ReAct, Terminal, Navigateur, FileManager).
3. Consulter la mémoire persistante pour contextualiser le projet.
4. Structurer une réponse déterministe et actionnable.`,
  duration = '1.2s',
  defaultOpen = false,
}: HermesThinkingBlockProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  const [copied, setCopied] = useState(false)

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation()
    navigator.clipboard?.writeText(thinkingText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="my-2 rounded-xl border border-[#cc785c]/25 bg-[var(--surface-soft)] overflow-hidden transition-all duration-200">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3.5 py-2 text-left hover:bg-[#cc785c]/10 transition-colors cursor-pointer"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-2 text-xs font-medium text-[var(--text-primary)]">
          <Sparkles className="w-3.5 h-3.5 text-[#cc785c] animate-pulse" />
          <span>Réflexion de l'agent</span>
          {duration && (
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#cc785c]/15 text-[#cc785c]">
              {duration}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          {isOpen && (
            <span
              onClick={handleCopy}
              className="p-1 rounded hover:bg-[#cc785c]/20 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
              title="Copier la réflexion"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
            </span>
          )}
          <ChevronDown
            className={`w-3.5 h-3.5 text-[var(--text-muted)] transition-transform duration-200 ${
              isOpen ? 'rotate-180' : ''
            }`}
          />
        </div>
      </button>

      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-3.5 py-2.5 pt-1.5 text-[11px] font-mono text-[var(--text-secondary)] border-t border-[var(--border)] bg-[var(--surface-card)] leading-relaxed whitespace-pre-wrap select-text">
              {thinkingText}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
