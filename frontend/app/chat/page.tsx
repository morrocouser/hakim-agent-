'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import AppShell from '@/components/AppShell'
import PageHeader from '@/components/PageHeader'
import { useAuth } from '@/contexts/AuthContext'
import { PaperPlaneRight, Stop, Spinner, Brain, User, Paperclip, X } from '@phosphor-icons/react'
import { chat, executeTask, scoreTask, TaskResult } from '@/lib/api'

const ACCEPTED_EXTENSIONS = [
  'txt', 'md', 'py', 'js', 'ts', 'tsx', 'jsx', 'json', 'csv',
  'html', 'css', 'yaml', 'yml', 'xml', 'sh', 'sql', 'toml',
]
const MAX_FILE_SIZE = 100 * 1024
const EXT_TO_LANG: Record<string, string> = {
  py: 'python', js: 'javascript', ts: 'typescript', tsx: 'typescript',
  jsx: 'javascript', json: 'json', md: 'markdown', html: 'html',
  css: 'css', yaml: 'yaml', xml: 'xml', sh: 'bash', sql: 'sql', txt: 'text',
}

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  task?: TaskResult
  file?: string
}

export default function ChatPage() {
  const { user, token } = useAuth()
  const router = useRouter()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [attachedFile, setAttachedFile] = useState<File | null>(null)
  const [conversationId, setConversationId] = useState<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!user) {
      router.push('/login')
    }
  }, [user, router])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const readFileContent = (file: File): Promise<string> =>
    new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = () => reject(new Error('read-failed'))
      reader.readAsText(file, 'utf-8')
    })

  const handleFileSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    const ext = (file.name.split('.').pop() || '').toLowerCase()
    if (!ACCEPTED_EXTENSIONS.includes(ext)) return
    if (file.size === 0 || file.size > MAX_FILE_SIZE) return
    setAttachedFile(file)
  }

  const handleSend = async () => {
    if (!input.trim() || loading || !token) return
    const text = input.trim()
    setInput('')
    let finalContent = text
    let fileName: string | undefined

    if (attachedFile) {
      try {
        const content = await readFileContent(attachedFile)
        const ext = (attachedFile.name.split('.').pop() || '').toLowerCase()
        const lang = EXT_TO_LANG[ext] || ''
        const sizeKo = (attachedFile.size / 1024).toFixed(1)
        fileName = attachedFile.name
        finalContent =
          `Fichier joint "${attachedFile.name}" (${sizeKo} Ko) :\n` +
          '```' + lang + '\n' + content + '\n```\n\n' +
          `Question : ${text}`
      } catch {
        return
      }
    }

    setMessages(prev => [...prev, { role: 'user', content: text, file: fileName }])
    setLoading(true)

    try {
      const res = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ content: finalContent, conversation_id: conversationId }),
      })
      const data = await res.json()
      if (res.ok) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.response, task: data.task }])
        if (data.conversation_id && !conversationId) {
          setConversationId(data.conversation_id)
        }
      } else {
        setMessages(prev => [...prev, { role: 'system', content: data.detail || 'Erreur API' }])
      }
    } catch {
      setMessages(prev => [...prev, { role: 'system', content: 'Erreur de connexion à l\'API. Vérifiez que le serveur backend est actif.' }])
    } finally {
      setLoading(false)
      setAttachedFile(null)
    }
  }

  return (
    <AppShell>
        <PageHeader eyebrow="Conversation" title="Chat direct" description="Décris une tâche, joins un fichier ou consulte le résultat de l'orchestration." />

        {/* Messages */}
        <div ref={scrollRef} className="min-h-[55dvh] overflow-y-auto pb-6 space-y-4">
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center justify-center h-full text-center"
            >
              <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-axiom-accent/20 to-emerald-500/5 flex items-center justify-center mb-6 animate-float">
                <Brain className="w-10 h-10 text-axiom-accent" />
              </div>
              <h2 className="text-2xl font-bold mb-3 tracking-tight">APEX Prêt</h2>
              <p className="text-axiom-muted max-w-[40ch] text-sm leading-relaxed">
                Posez une question ou décrivez une tâche. Le système orchestrera automatiquement les agents appropriés.
              </p>
              <div className="mt-8 grid grid-cols-2 gap-3 max-w-[400px]">
                {[
                  'Analyser un fichier Python',
                  'Créer une API REST',
                  'Déboguer une erreur',
                  'Rédiger de la documentation',
                ].map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => setInput(prompt)}
                    className="btn-ghost text-xs py-3 text-left"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          <AnimatePresence>
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ type: 'spring', stiffness: 100, damping: 20 }}
                className="flex gap-4 max-w-[800px] mx-auto"
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  msg.role === 'user'
                    ? 'bg-axiom-accent/20'
                    : msg.role === 'system'
                    ? 'bg-axiom-red/20'
                    : 'bg-axiom-card border border-axiom-border'
                }`}>
                  {msg.role === 'user' ? (
                    <User className="w-4 h-4 text-axiom-accent" />
                  ) : (
                    <Brain className="w-4 h-4 text-axiom-muted" />
                  )}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-medium">
                      {msg.role === 'user' ? 'Vous' : msg.role === 'system' ? 'Système' : 'APEX'}
                    </span>
                    <span className="text-[10px] text-axiom-subtle font-mono">
                      {new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <div className={`rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-axiom-accent/10 border border-axiom-accent/20'
                      : msg.role === 'system'
                      ? 'bg-axiom-red/10 border border-axiom-red/20'
                      : 'bg-axiom-card border border-axiom-border'
                  }`}>
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    {msg.task && (
                      <div className="mt-3 pt-3 border-t border-axiom-border">
                        <div className="flex items-center gap-4 text-xs text-axiom-muted font-mono">
                          <span>Agent: <span className="text-axiom-text">{msg.task.agent}</span></span>
                          <span>Score: <span className="text-axiom-accent">{msg.task.score}</span></span>
                          <span>Itération: <span className="text-axiom-text">{msg.task.iteration}</span></span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex gap-4 max-w-[800px] mx-auto"
            >
              <div className="w-8 h-8 rounded-lg bg-axiom-card border border-axiom-border flex items-center justify-center">
                <Brain className="w-4 h-4 text-axiom-muted" />
              </div>
              <div className="bg-axiom-card border border-axiom-border rounded-2xl px-4 py-3 flex items-center gap-2">
                <Spinner className="w-4 h-4 text-axiom-accent animate-spin" />
                <span className="text-sm text-axiom-muted">Réflexion en cours...</span>
              </div>
            </motion.div>
          )}
        </div>

        {/* Attached file chip */}
        {attachedFile && (
          <div className="px-8 pb-2">
            <div
              className="flex items-center gap-2.5 px-3 py-2 rounded-xl max-w-[800px] mx-auto"
              style={{ background: 'var(--bg-tertiary)', border: '1.5px solid var(--border)' }}
            >
              <span>📎</span>
              <span className="text-xs font-mono flex-1 truncate" style={{ color: 'var(--text-primary)' }}>
                {attachedFile.name}
              </span>
              <span className="text-xs font-mono shrink-0" style={{ color: 'var(--text-muted)' }}>
                {(attachedFile.size / 1024).toFixed(1)} Ko
              </span>
              <button
                onClick={() => setAttachedFile(null)}
                className="input-action-btn shrink-0"
                title="Retirer le fichier"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {/* Input */}
        <div className="sticky bottom-0 border-t border-axiom-border py-5" style={{ background: 'var(--surface-raised)' }}>
          <div className="ai-input-wrap max-w-[800px] mx-auto">
            <div className="flex items-center px-4 py-2.5 gap-3">
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
                placeholder="Décrivez une tâche ou posez une question..."
                className="flex-1 text-sm py-1"
                disabled={loading}
              />
            </div>
            <div className="flex items-center justify-between px-3 pb-2.5 pt-0.5">
              <div className="flex items-center gap-1">
                <button
                  className="input-action-btn"
                  title="Joindre un fichier"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={loading}
                >
                  <Paperclip className="w-4 h-4" />
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={ACCEPTED_EXTENSIONS.map(e => '.' + e).join(',')}
                  onChange={handleFileSelected}
                  className="hidden"
                  tabIndex={-1}
                />
              </div>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={loading ? () => {} : handleSend}
                disabled={loading || !input.trim()}
                aria-label="Envoyer le message"
                className={`send-btn ${input.trim() && !loading ? 'send-btn-active' : 'send-btn-disabled'}`}
              >
                {loading ? <Stop className="w-4 h-4" /> : <PaperPlaneRight className="w-4 h-4" weight="bold" />}
              </motion.button>
            </div>
          </div>
        </div>
    </AppShell>
  )
}
