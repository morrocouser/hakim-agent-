'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Terminal,
  Globe,
  FileText,
  Database,
  Code2,
  ChevronDown,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Copy,
  Check,
  ShieldAlert,
} from 'lucide-react'

export interface ToolCallData {
  toolName: string
  intent: string
  command?: string
  output?: string
  status?: 'SUCCESS' | 'RUNNING' | 'ERROR' | 'REQUIRE_TAKEOVER' | 'DENIED'
  target?: string
}

interface HermesToolCardProps {
  toolCall: ToolCallData
}

export default function HermesToolCard({ toolCall }: HermesToolCardProps) {
  const [outputExpanded, setOutputExpanded] = useState(false)
  const [copied, setCopied] = useState(false)

  const {
    toolName,
    intent,
    command,
    output,
    status = 'SUCCESS',
    target,
  } = toolCall

  const getToolIcon = () => {
    const lower = toolName.toLowerCase()
    if (lower.includes('browser') || lower.includes('navigue') || lower.includes('web')) {
      return <Globe className="w-3.5 h-3.5 text-cyan-400" />
    }
    if (lower.includes('terminal') || lower.includes('bash') || lower.includes('cmd')) {
      return <Terminal className="w-3.5 h-3.5 text-emerald-400" />
    }
    if (lower.includes('file') || lower.includes('doc')) {
      return <FileText className="w-3.5 h-3.5 text-amber-400" />
    }
    if (lower.includes('memory') || lower.includes('memoire')) {
      return <Database className="w-3.5 h-3.5 text-purple-400" />
    }
    return <Code2 className="w-3.5 h-3.5 text-blue-400" />
  }

  const getStatusBadge = () => {
    switch (status) {
      case 'SUCCESS':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-2.5 h-2.5" />
            SUCCÈS
          </span>
        )
      case 'RUNNING':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-400 border border-amber-500/20">
            <Loader2 className="w-2.5 h-2.5 animate-spin" />
            EN COURS
          </span>
        )
      case 'REQUIRE_TAKEOVER':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
            <ShieldAlert className="w-2.5 h-2.5" />
            APPROBATION
          </span>
        )
      case 'DENIED':
      case 'ERROR':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded bg-red-500/15 text-red-400 border border-red-500/20">
            <AlertTriangle className="w-2.5 h-2.5" />
            REFUSÉ
          </span>
        )
      default:
        return null
    }
  }

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!output) return
    navigator.clipboard?.writeText(output)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="my-2 rounded-xl border border-[#252320] bg-[#181715] shadow-sm overflow-hidden transition-all duration-200 hover:border-[#322f2a]">
      {/* Tool Header */}
      <div
        className="flex items-center justify-between px-3.5 py-2.5 bg-[#1f1e1b] cursor-pointer"
        onClick={() => setOutputExpanded(!outputExpanded)}
      >
        <div className="flex items-center gap-2 min-w-0">
          <div className="p-1 rounded bg-white/5 border border-white/5">
            {getToolIcon()}
          </div>
          <span className="text-xs font-mono font-medium text-[#faf9f5] truncate">
            {toolName}
          </span>
          {target && (
            <span className="hidden sm:inline-block text-[10px] font-mono text-[#a09d96] truncate max-w-[200px]">
              ({target})
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {getStatusBadge()}
          {output && (
            <ChevronDown
              className={`w-3.5 h-3.5 text-[#a09d96] transition-transform duration-200 ${
                outputExpanded ? 'rotate-180' : ''
              }`}
            />
          )}
        </div>
      </div>

      {/* Tool Intent & Command */}
      <div className="px-3.5 py-2.5 text-xs text-[#d4cfc5] border-t border-[#252320] bg-[#181715] space-y-1.5">
        <p className="text-[11px] text-[#a09d96]">{intent}</p>
        {command && (
          <div className="p-2 rounded-lg bg-[#141413] border border-[#252320] font-mono text-[11px] text-[#5db872] overflow-x-auto whitespace-pre">
            $ {command}
          </div>
        )}
      </div>

      {/* Output Console (Expandable) */}
      {output && (
        <AnimatePresence>
          {outputExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="border-t border-[#252320] bg-[#141413] overflow-hidden"
            >
              <div className="flex items-center justify-between px-3 py-1.5 bg-[#181715] border-b border-[#252320]">
                <span className="text-[10px] font-mono text-[#a09d96] uppercase tracking-wider">
                  Terminal Output (stdout)
                </span>
                <button
                  type="button"
                  onClick={handleCopy}
                  className="p-1 rounded text-[#a09d96] hover:text-[#faf9f5] transition-colors"
                  title="Copier le retour"
                >
                  {copied ? <Check className="w-3 h-3 text-[#5db872]" /> : <Copy className="w-3 h-3" />}
                </button>
              </div>
              <pre className="p-3 text-[11px] font-mono text-[#faf9f5] max-h-48 overflow-y-auto whitespace-pre-wrap select-text">
                {output}
              </pre>
            </motion.div>
          )}
        </AnimatePresence>
      )}
    </div>
  )
}
