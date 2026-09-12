'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { FileCode, ShieldWarning, Terminal, PencilSimple, FolderOpen } from '@phosphor-icons/react'

export interface PermissionRequest {
  id: string
  type: 'read' | 'write' | 'execute'
  path: string
  description: string
}

interface PermissionDialogProps {
  request: PermissionRequest
  onAllow: () => void
  onReject: () => void
}

export default function PermissionDialog({ request, onAllow, onReject }: PermissionDialogProps) {
  const getIcon = () => {
    switch (request.type) {
      case 'read': return <FolderOpen size={20} className="text-sky-500" />
      case 'write': return <PencilSimple size={20} className="text-amber-500" />
      case 'execute': return <Terminal size={20} className="text-rose-500" />
      default: return <FileCode size={20} className="text-axiom-accent" />
    }
  }

  const getTitle = () => {
    switch (request.type) {
      case 'read': return 'Permission de lecture requise'
      case 'write': return 'Permission de modification requise'
      case 'execute': return "Permission d'exécution requise"
      default: return 'Action requise'
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className="w-full max-w-md my-4 rounded-2xl border shadow-lg overflow-hidden"
      style={{
        background: 'var(--surface-raised)',
        borderColor: 'var(--border)',
        boxShadow: '0 20px 50px rgba(10, 10, 12, 0.14)',
      }}
    >
      <div
        className="p-4 border-b flex items-start gap-4"
        style={{ borderColor: 'var(--border)', background: 'linear-gradient(to right, var(--accent-soft), transparent)' }}
      >
        <div
          className="p-2.5 rounded-xl border mt-1"
          style={{ background: 'var(--bg-tertiary)', borderColor: 'var(--border)' }}
        >
          {getIcon()}
        </div>
        <div>
          <h3 className="text-[15px] font-semibold tracking-tight mb-1" style={{ color: 'var(--text-primary)' }}>{getTitle()}</h3>
          <div
            className="font-mono text-xs break-all px-2 py-1 rounded border inline-block"
            style={{ color: 'var(--text-secondary)', background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}
          >
            {request.path}
          </div>
        </div>
      </div>

      <div className="p-4">
        <p className="text-sm mb-5" style={{ color: 'var(--text-secondary)' }}>{request.description}</p>

        <div className="space-y-2.5 font-mono text-xs mb-6">
          {[
            'Autoriser cette fois',
            'Toujours autoriser pour ce dossier',
            'Rejeter cette fois',
            'Toujours rejeter pour ce dossier',
            'Quitter le mode agent',
          ].map((label, i) => (
            <div key={i} className="flex items-center gap-3 cursor-pointer group" style={{ color: 'var(--text-secondary)' }}>
              <span
                className="flex items-center justify-center w-5 h-5 rounded-full border font-semibold transition-colors"
                style={{ background: 'var(--accent-soft)', color: 'var(--accent)', borderColor: 'var(--accent-soft)' }}
              >
                {i + 1}
              </span>
              <span className="group-hover:opacity-80 transition-opacity">{label}</span>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between mt-2 pt-4" style={{ borderTop: '1px solid var(--border)' }}>
          <button
            onClick={onReject}
            className="px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 cursor-pointer"
            style={{ color: 'var(--text-muted)' }}
          >
            Skip
          </button>
          <button
            onClick={onAllow}
            className="px-6 py-2 text-sm font-semibold text-white rounded-lg transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer"
            style={{ background: 'var(--accent)', boxShadow: '0 4px 14px var(--accent-glow)' }}
          >
            Submit
          </button>
        </div>
      </div>
    </motion.div>
  )
}
