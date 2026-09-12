'use client'

import { useEffect, useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { PaperPlaneRight, Stop, CaretDown, Database, Cpu, Coin, CircleDashed } from '@phosphor-icons/react'
import { chat } from '@/lib/api'
import PermissionDialog, { PermissionRequest } from './PermissionDialog'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [agentStatus, setAgentStatus] = useState<'idle' | 'executing' | 'waiting_permission'>('idle')
  const [mockPermission, setMockPermission] = useState<PermissionRequest | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, loading])

  const handleSend = async () => {
    if (!input.trim() || loading) return
    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const res = await chat(userMessage)

      // Simulate permission request for specific keywords
      if (userMessage.toLowerCase().includes('supprimer') || userMessage.toLowerCase().includes('installer')) {
        setAgentStatus('waiting_permission')
        setMockPermission({
          id: '123',
          type: 'execute',
          path: '/home/user/project/script.sh',
          description: "L'agent APEX demande l'autorisation d'exécuter un script potentiellement destructeur."
        })
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: res.response }])
      }
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: '❌ Erreur de connexion à l\'API APEX.' }])
    } finally {
      setLoading(false)
      if (agentStatus !== 'waiting_permission') setAgentStatus('idle')
    }
  }

  const handleAllowPermission = () => {
    setMockPermission(null)
    setAgentStatus('executing')
    setTimeout(() => {
      setAgentStatus('idle')
      setMessages(prev => [...prev, { role: 'assistant', content: '✅ Action exécutée avec succès après votre autorisation.' }])
    }, 1500)
  }

  const handleRejectPermission = () => {
    setMockPermission(null)
    setAgentStatus('idle')
    setMessages(prev => [...prev, { role: 'assistant', content: '🛑 Action annulée par l\'utilisateur.' }])
  }

  return (
    <div
      className="flex flex-col h-full rounded-lg overflow-hidden border shadow-lg"
      style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
    >
      {/* Top Bar: Model Selector, Cost, Status */}
      <div
        className="h-12 px-4 flex items-center justify-between border-b"
        style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}
      >
        <div className="flex items-center gap-3">
          {/* Model Selector Dropdown */}
          <div
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md cursor-pointer transition-colors text-xs font-medium border hover:border-axiom-accent/40"
            style={{ color: 'var(--text-secondary)', borderColor: 'var(--border)' }}
          >
            <Cpu size={14} className="text-axiom-accent" />
            <span>Claude 3.5 Sonnet</span>
            <CaretDown size={12} className="opacity-50" />
          </div>

          <div className="w-px h-4" style={{ background: 'var(--border)' }} />

          {/* Tokens / Cost */}
          <div className="flex items-center gap-1.5 px-2 text-xs font-mono" style={{ color: 'var(--text-muted)' }}>
            <Coin size={14} className="text-axiom-accent" />
            <span>$0.024</span>
            <span className="opacity-50 ml-1">· 8.4k tkns</span>
          </div>
        </div>

        {/* Agent Status */}
        <div className="flex items-center gap-2">
          {agentStatus === 'idle' && (
            <div
              className="flex items-center gap-1.5 px-2 py-1 rounded text-[11px] font-semibold border"
              style={{ background: 'var(--bg-tertiary)', color: 'var(--text-muted)', borderColor: 'var(--border)' }}
            >
              <div className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--text-muted)' }} /> Idle
            </div>
          )}
          {agentStatus === 'executing' && (
            <div
              className="flex items-center gap-1.5 px-2 py-1 rounded text-[11px] font-semibold border"
              style={{ background: 'var(--accent-soft)', color: 'var(--accent)', borderColor: 'var(--accent-soft)' }}
            >
              <CircleDashed size={10} className="animate-spin" /> Exécution...
            </div>
          )}
          {agentStatus === 'waiting_permission' && (
            <div
              className="flex items-center gap-1.5 px-2 py-1 rounded text-[11px] font-semibold border animate-pulse"
              style={{ background: 'color-mix(in srgb, var(--color-axiom-yellow) 12%, transparent)', color: 'var(--color-axiom-yellow)', borderColor: 'color-mix(in srgb, var(--color-axiom-yellow) 30%, transparent)' }}
            >
              <div className="w-1.5 h-1.5 rounded-full bg-axiom-yellow" /> En attente de permission
            </div>
          )}
        </div>
      </div>

      {/* Messages area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-5 space-y-6">
        {messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="flex flex-col items-center justify-center h-full text-center py-12"
          >
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5 text-3xl border"
              style={{ background: 'var(--accent-soft)', borderColor: 'var(--border)' }}
            >
              ⌘
            </div>
            <h3 className="text-base font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
              APEX Prêt
            </h3>
            <p className="text-sm max-w-[28ch] leading-relaxed" style={{ color: 'var(--text-muted)' }}>
              Décrivez une tâche et l&apos;orchestrateur acheminera vers le meilleur agent.
            </p>
          </motion.div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ type: 'spring', stiffness: 150, damping: 25 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[78%] rounded-2xl px-4 py-3 ${
                  msg.role === 'user'
                    ? 'text-white'
                    : 'border'
                }`}
                style={
                  msg.role === 'user'
                    ? { background: 'var(--accent)', boxShadow: '0 4px 20px var(--accent-glow)' }
                    : { background: 'var(--bg-tertiary)', borderColor: 'var(--border)', color: 'var(--text-primary)' }
                }
              >
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing indicator */}
        {loading && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex justify-start"
          >
            <div
              className="rounded-2xl px-4 py-3.5 border flex items-center gap-1.5"
              style={{ background: 'var(--bg-tertiary)', borderColor: 'var(--border)' }}
            >
              {[0, 1, 2].map(i => (
                <motion.div
                  key={i}
                  className="w-1.5 h-1.5 rounded-full"
                  style={{ background: 'var(--accent)' }}
                  animate={{ opacity: [0.3, 1, 0.3], scale: [0.8, 1.1, 0.8] }}
                  transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
                />
              ))}
            </div>
          </motion.div>
        )}

        {/* Permission Dialog Injection */}
        <AnimatePresence>
          {mockPermission && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="flex justify-center my-6"
            >
              <PermissionDialog
                request={mockPermission}
                onAllow={handleAllowPermission}
                onReject={handleRejectPermission}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Input area */}
      <div
        className="p-4 border-t"
        style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}
      >
        <div className="mb-2 px-1 flex items-center gap-2">
          <Database size={12} style={{ color: 'var(--text-muted)' }} />
          <span className="text-[10px] font-mono uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Projet : ntrsitecursur</span>
        </div>
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Décrivez une tâche pour APEX..."
            className="input-axiom flex-1"
            disabled={loading || agentStatus === 'waiting_permission'}
            aria-label="Saisir une tâche pour APEX"
          />
          <motion.button
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.95 }}
            onClick={loading ? () => {} : handleSend}
            className="p-3 rounded-xl flex-shrink-0 min-w-[44px] min-h-[44px] flex items-center justify-center transition-all duration-200"
            style={
              loading
                ? { background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)' }
                : { background: 'var(--accent)', boxShadow: '0 4px 14px var(--accent-glow)' }
            }
            aria-label={loading ? 'Arrêter la génération' : 'Envoyer le message'}
          >
            {loading
              ? <Stop className="w-5 h-5" style={{ color: 'var(--color-axiom-red)' }} />
              : <PaperPlaneRight className="w-5 h-5 text-white" />}
          </motion.button>
        </div>
      </div>
    </div>
  )
}
