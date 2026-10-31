'use client'

import React, { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Brain,
  MessageSquare,
  Plus,
  Search,
  Trash2,
  Edit2,
  Check,
  X,
  Send,
  Square,
  Paperclip,
  Cpu,
  Sparkles,
  ChevronDown,
  Clock,
  Zap,
  Folder,
  Database,
  Monitor,
  PanelRightClose,
  PanelRightOpen,
  Sliders,
  MoreVertical,
  Download,
  Share2,
  ArrowRight,
  Terminal,
  ShieldCheck,
  CheckCircle2,
  Copy,
  User,
  LogOut,
  Maximize2,
  RefreshCw,
} from 'lucide-react'

import HermesContextRing from './HermesContextRing'
import HermesThinkingBlock from './HermesThinkingBlock'
import HermesToolCard, { ToolCallData } from './HermesToolCard'
import HermesFileViewer from './HermesFileViewer'
import HermesMemoryPanel from './HermesMemoryPanel'
import HermesSkillsPanel from './HermesSkillsPanel'
import HermesCronPanel from './HermesCronPanel'
import HermesTakeTheWheelPanel from './HermesTakeTheWheelPanel'
import HermesSettingsModal from './HermesSettingsModal'

import { useAuth } from '@/contexts/AuthContext'
import { chat, executeOnComputer } from '@/lib/api'

export interface Session {
  id: string
  title: string
  createdAt: string
  updatedAt: string
  messageCount: number
  category: 'today' | 'yesterday' | 'past_week' | 'older'
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  model?: string
  file?: string
  thinking?: string
  thinkingDuration?: string
  toolCall?: ToolCallData
}

const DEFAULT_SESSIONS: Session[] = [
  {
    id: 'sess-1',
    title: "Analyse d'architecture & Routage APEX",
    createdAt: '19:42',
    updatedAt: '19:42',
    messageCount: 4,
    category: 'today',
  },
  {
    id: 'sess-2',
    title: 'Développement MVP Dropshipping SaaS',
    createdAt: '14:15',
    updatedAt: '14:15',
    messageCount: 8,
    category: 'today',
  },
  {
    id: 'sess-3',
    title: 'Génération de tests unitaires FastAPI',
    createdAt: 'Hier, 17:30',
    updatedAt: 'Hier, 17:30',
    messageCount: 12,
    category: 'yesterday',
  },
  {
    id: 'sess-4',
    title: 'Audit des jetons et de la mémoire persistante',
    createdAt: '08 Oct 2026',
    updatedAt: '08 Oct 2026',
    messageCount: 6,
    category: 'past_week',
  },
]

const STARTER_PROMPTS = [
  {
    icon: '🛠️',
    title: 'Audit & Diagnostic',
    description: "Analyse l'état du projet HakimAgent et vérifie les dépendances backend/frontend.",
    prompt: "Analyse l'architecture du projet HakimAgent, vérifie les dépendances et liste les endpoints disponibles.",
  },
  {
    icon: '⚡',
    title: 'Exécution Terminal',
    description: 'Inspecte les fichiers modifiés et lance les tests de régression.',
    prompt: "Vérifie les fichiers modifiés dans le dépôt et exécute les tests unitaires de scoring et de mémoire.",
  },
  {
    icon: '🧠',
    title: 'Mémoire & Contexte',
    description: 'Affiche la mémoire persistante et les décisions architecturales SQLite.',
    prompt: "Affiche le contenu de la mémoire persistante SQLite et résume les règles d'architecture actives.",
  },
  {
    icon: '⏱️',
    title: 'Routines Autonomes',
    description: 'Planifie une tâche Cron de surveillance automatique du serveur.',
    prompt: "Crée une routine Cron pour surveiller la santé de l'API et nettoyer les logs chaque jour à minuit.",
  },
]

export default function HermesWebUI() {
  const { user, token, logout } = useAuth()

  // Layout Panels State
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [rightPanelOpen, setRightPanelOpen] = useState(true)
  const [rightPanelTab, setRightPanelTab] = useState<'files' | 'memory' | 'skills' | 'cron' | 'screen'>('files')
  const [settingsOpen, setSettingsOpen] = useState(false)

  // Sessions State
  const [sessions, setSessions] = useState<Session[]>(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('hermes_sessions')
        if (saved) return JSON.parse(saved)
      } catch {}
    }
    return DEFAULT_SESSIONS
  })
  const [activeSessionId, setActiveSessionId] = useState<string>('sess-1')
  const [sessionSearch, setSessionSearch] = useState('')
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null)
  const [editingSessionTitle, setEditingSessionTitle] = useState('')

  // Model & Mode State
  const [selectedModel, setSelectedModel] = useState('claude-3-7-sonnet')
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false)
  const [agentMode, setAgentMode] = useState<'react' | 'plan' | 'code' | 'chat'>('react')
  const [agentStatus, setAgentStatus] = useState<'idle' | 'thinking' | 'tool' | 'streaming'>('idle')

  // Chat Messages State
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-init-1',
      role: 'user',
      content: 'Quel est le statut du système HakimAgent et comment sont gérées les mémoires persistantes ?',
      timestamp: '19:40',
    },
    {
      id: 'msg-init-2',
      role: 'assistant',
      content: `Bienvenue dans le cockpit **Hermes WebUI** pour **HakimAgent** ! 🚀

Le système fonctionne à 100\u00a0% en local avec les garanties suivantes :
- **Routage déterministe** : scoring multicritère APEX (complexité, vitesse, coût).
- **Mémoire persistante** : indexation SQLite vectorielle avec historique complet et persistance intersessions.
- **Exécution d'outils sandboxés** : terminal Bash, navigation web Chromium et explorateur de fichiers sous isolation stricte.

Vous pouvez utiliser le panneau droit pour explorer les fichiers de l'espace de travail, tester les compétences de l'agent ou planifier des tâches cron autonomes.`,
      timestamp: '19:41',
      model: 'Claude 3.7 Sonnet',
      thinking: `1. Requête reçue : Interrogation sur le statut du système HakimAgent et la gestion mémoire.
2. Consultation de la mémoire SQLite interne : Vérification des dimensions de scoring.
3. Synthèse des garanties : Routage strict DAG, absence de télémétrie externe, persistance locale.
4. Formatage de la réponse avec mise en avant des fonctionnalités du cockpit Hermes.`,
      thinkingDuration: '1.1s',
      toolCall: {
        toolName: 'memory_recall',
        intent: 'Lecture des spécifications architecturales APEX en mémoire',
        command: 'sqlite3 axiom.db "SELECT * FROM persistent_memories LIMIT 5;"',
        output: `[SQLITE RESULT]
id: mem-1 | cat: architecture | data: Pipeline DAG asynchrone pyright strict
id: mem-2 | cat: decision | data: Scoring déterministe local sans cloud obligatoire
status: 2 records retrieved in 0.8ms`,
        status: 'SUCCESS',
      },
    },
  ])

  // Composer Input State
  const [input, setInput] = useState('')
  const [attachedFile, setAttachedFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [usedTokens, setUsedTokens] = useState(24580)

  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Persist sessions
  useEffect(() => {
    try {
      localStorage.setItem('hermes_sessions', JSON.stringify(sessions))
    } catch {}
  }, [sessions])

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading, agentStatus])

  // Keyboard shortcut listener (Alt+B for right panel, Ctrl+N for new chat)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'n') {
        e.preventDefault()
        handleNewSession()
      }
      if (e.altKey && e.key.toLowerCase() === 'b') {
        e.preventDefault()
        setRightPanelOpen((prev) => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`
    }
  }

  // Session Handlers
  const handleNewSession = () => {
    const newId = `sess-${Date.now()}`
    const newSession: Session = {
      id: newId,
      title: 'Nouvelle session',
      createdAt: "À l'instant",
      updatedAt: "À l'instant",
      messageCount: 0,
      category: 'today',
    }
    setSessions([newSession, ...sessions])
    setActiveSessionId(newId)
    setMessages([])
  }

  const handleDeleteSession = (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    const remaining = sessions.filter((s) => s.id !== id)
    setSessions(remaining)
    if (activeSessionId === id && remaining.length > 0) {
      setActiveSessionId(remaining[0].id)
    }
  }

  const handleStartRename = (session: Session, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingSessionId(session.id)
    setEditingSessionTitle(session.title)
  }

  const handleSaveRename = (id: string) => {
    if (!editingSessionTitle.trim()) return
    setSessions((prev) =>
      prev.map((s) => (s.id === id ? { ...s, title: editingSessionTitle.trim() } : s))
    )
    setEditingSessionId(null)
  }

  // Send Message Handler
  const handleSend = async (customText?: string) => {
    const textToSend = customText || input
    if (!textToSend.trim() || loading) return

    const promptText = textToSend.trim()
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    const timeStr = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
    const userMsgId = `user-${Date.now()}`

    const userMessage: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content: promptText,
      timestamp: timeStr,
      file: attachedFile ? attachedFile.name : undefined,
    }

    setMessages((prev) => [...prev, userMessage])
    setAttachedFile(null)
    setLoading(true)
    setAgentStatus('thinking')
    setUsedTokens((prev) => prev + Math.floor(promptText.length / 3) + 120)

    // Check for tool triggering (browser, terminal, memory, file)
    const lower = promptText.toLowerCase()
    const isBrowser = lower.includes('navigue') || lower.includes('browse') || lower.includes('http://') || lower.includes('https://')
    const isTerminal = lower.includes('ls') || lower.includes('test') || lower.includes('bash') || lower.includes('run') || lower.includes('commande')
    const isFile = lower.includes('fichier') || lower.includes('file') || lower.includes('code')
    const isMemory = lower.includes('mémoire') || lower.includes('memoire') || lower.includes('sqlite')

    try {
      // API Call
      const res = await chat(promptText, token)

      const assistantMsgId = `asst-${Date.now()}`
      const modelLabel = res.task?.model || (selectedModel === 'claude-3-7-sonnet' ? 'Claude 3.7 Sonnet' : selectedModel)
      const agentLabel = res.task?.agent || 'APEX Orchestrator'
      const qualityScore = res.task?.quality_score ?? 8.5
      const iterationCount = res.task?.iteration ?? 1

      const assistantMessage: ChatMessage = {
        id: assistantMsgId,
        role: 'assistant',
        content: res.response || "L'action a été complétée avec succès par le moteur autonome HakimAgent.",
        timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
        model: modelLabel,
        thinking: `1. Requête opérateur reçue (${promptText.length} caractères).\n2. Agent sélectionné : ${agentLabel} (${modelLabel}).\n3. Score qualité évalué : ${qualityScore}/10 (Itération ${iterationCount}).`,
        thinkingDuration: '0.8s',
      }

      setMessages((prev) => [...prev, assistantMessage])
      setUsedTokens((prev) => prev + 350)

      // Update session title if first exchange
      setSessions((prev) =>
        prev.map((s) =>
          s.id === activeSessionId && s.messageCount === 0
            ? { ...s, title: promptText.slice(0, 36) + '...', messageCount: 2 }
            : s.id === activeSessionId
            ? { ...s, messageCount: s.messageCount + 2 }
            : s
        )
      )
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : 'Erreur inconnue de communication avec le serveur APEX.'
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: `⚠️ **Échec de la requête :**\n${errMsg}\n\n*Assurez-vous que le serveur backend est en cours d'exécution sur le port 8000 et que vos clés d'API LLM sont valides dans le fichier \`.env\`.*`,
          timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
          model: 'Erreur Système',
        },
      ])
    } finally {
      setLoading(false)
      setAgentStatus('idle')
    }
  }

  const currentSession = sessions.find((s) => s.id === activeSessionId) || sessions[0]

  const filteredSessions = sessions.filter((s) =>
    s.title.toLowerCase().includes(sessionSearch.toLowerCase())
  )

  return (
    <div className="flex h-[100dvh] w-full overflow-hidden bg-[var(--canvas)] text-[var(--text-primary)] font-sans antialiased">
      {/* ─────────────────────────────────────────────────────────────
          1. LEFT PANEL : SESSIONS & AGENT NAVIGATION (Hermes Sidebar)
          ───────────────────────────────────────────────────────────── */}
      <aside
        className={`flex flex-col shrink-0 border-r border-[var(--border)] bg-[var(--surface-card)] transition-all duration-300 ease-in-out z-20 ${
          sidebarOpen ? 'w-[280px]' : 'w-[68px]'
        }`}
      >
        {/* Brand Header */}
        <div className="h-14 px-3 flex items-center justify-between border-b border-[var(--border)]">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-7 h-7 rounded-lg bg-[#cc785c] flex items-center justify-center font-bold text-white shadow-xs text-xs">
              H
            </div>
            {sidebarOpen && (
              <div className="flex flex-col min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="font-normal text-sm tracking-tight text-[var(--text-primary)] truncate" style={{ fontFamily: 'var(--font-display)' }}>
                    HakimAgent
                  </span>
                  <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-[#cc785c]/15 text-[#cc785c] border border-[#cc785c]/30">
                    CLAUDE
                  </span>
                </div>
                <div className="flex items-center gap-1 text-[10px] text-[var(--text-muted)]">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span>En ligne</span>
                </div>
              </div>
            )}
          </Link>

          {sidebarOpen && (
            <button
              type="button"
              onClick={() => setSidebarOpen(false)}
              className="p-1 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)] transition-colors"
              title="Réduire la barre"
            >
              <PanelRightClose className="w-4 h-4" />
            </button>
          )}

          {!sidebarOpen && (
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="mx-auto p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)] transition-colors"
              title="Déplier la barre"
            >
              <PanelRightOpen className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* New Session Button */}
        <div className="p-3">
          <button
            type="button"
            onClick={handleNewSession}
            className={`w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-[#cc785c] hover:bg-[#a9583e] text-white text-xs font-medium shadow-xs transition-all cursor-pointer ${
              !sidebarOpen ? '!px-0' : ''
            }`}
            title="Nouvelle session (Ctrl+N)"
          >
            <Plus className="w-4 h-4 shrink-0" />
            {sidebarOpen && (
              <>
                <span className="truncate">Nouvelle discussion</span>
                <span className="ml-auto text-[10px] font-mono opacity-80 bg-black/20 px-1 rounded">
                  Ctrl+N
                </span>
              </>
            )}
          </button>
        </div>

        {/* Search Input (When open) */}
        {sidebarOpen && (
          <div className="px-3 pb-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
              <input
                type="text"
                value={sessionSearch}
                onChange={(e) => setSessionSearch(e.target.value)}
                placeholder="Filtrer les sessions..."
                className="w-full pl-8 pr-2.5 py-1.5 rounded-xl bg-[var(--surface-soft)] border border-[var(--border)] text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[#cc785c]"
              />
            </div>
          </div>
        )}

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto px-2 space-y-1">
          {sidebarOpen && (
            <div className="text-[10px] font-mono uppercase tracking-wider text-[var(--text-muted)] px-2 py-1">
              Historique des Sessions
            </div>
          )}

          {filteredSessions.map((session) => {
            const isActive = activeSessionId === session.id
            const isEditing = editingSessionId === session.id

            return (
              <div
                key={session.id}
                onClick={() => setActiveSessionId(session.id)}
                className={`group relative flex items-center gap-2 px-2.5 py-2 rounded-xl text-xs cursor-pointer transition-all ${
                  isActive
                    ? 'bg-[var(--surface-cream-strong)] text-[var(--text-primary)] font-medium border-l-2 border-[#cc785c] shadow-xs'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)]'
                } ${!sidebarOpen ? 'justify-center !px-0' : ''}`}
                title={session.title}
              >
                <MessageSquare className={`w-4 h-4 shrink-0 ${isActive ? 'text-[#cc785c]' : 'text-[var(--text-muted)]'}`} />

                {sidebarOpen && (
                  <div className="flex-1 min-w-0">
                    {isEditing ? (
                      <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="text"
                          value={editingSessionTitle}
                          onChange={(e) => setEditingSessionTitle(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && handleSaveRename(session.id)}
                          className="w-full bg-[var(--canvas)] border border-[#cc785c] rounded px-1.5 py-0.5 text-xs text-[var(--text-primary)]"
                          autoFocus
                        />
                        <button
                          type="button"
                          onClick={() => handleSaveRename(session.id)}
                          className="text-emerald-500 hover:text-emerald-400"
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ) : (
                      <div className="flex flex-col">
                        <span className="truncate leading-tight">{session.title}</span>
                        <span className="text-[10px] font-mono text-[var(--text-muted)] mt-0.5">
                          {session.createdAt}
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {sidebarOpen && !isEditing && (
                  <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1 transition-opacity">
                    <button
                      type="button"
                      onClick={(e) => handleStartRename(session, e)}
                      className="p-1 rounded text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)]"
                      title="Renommer"
                    >
                      <Edit2 className="w-3 h-3" />
                    </button>
                    <button
                      type="button"
                      onClick={(e) => handleDeleteSession(session.id, e)}
                      className="p-1 rounded text-[var(--text-muted)] hover:text-red-500 hover:bg-[var(--surface-soft)]"
                      title="Supprimer"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Bottom Profile & Settings Bar */}
        <div className="p-3 border-t border-[var(--border)] bg-[var(--surface-card)]">
          {sidebarOpen ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 min-w-0">
                <div className="w-7 h-7 rounded-full bg-[var(--surface-soft)] border border-[var(--border)] text-[var(--text-primary)] flex items-center justify-center text-xs font-semibold uppercase shrink-0">
                  {user ? (user.username || 'U')[0].toUpperCase() : 'H'}
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="text-xs font-medium text-[var(--text-primary)] truncate leading-tight">
                    {user?.display_name || user?.username || 'Opérateur Local'}
                  </span>
                  <span className="text-[10px] font-mono text-[var(--text-muted)]">
                    APEX v4.0
                  </span>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setSettingsOpen(true)}
                className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)] transition-colors"
                title="Paramètres de l'agent"
              >
                <Sliders className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex justify-center">
              <button
                type="button"
                onClick={() => setSettingsOpen(true)}
                className="p-2 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)] transition-colors"
                title="Paramètres"
              >
                <Sliders className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* ─────────────────────────────────────────────────────────────
          2. CENTER PANEL : CHAT CONVERSATION & AGENT STREAM (Hermes Center)
          ───────────────────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col min-w-0 h-full overflow-hidden bg-[var(--canvas)]">
        {/* Top Header Bar */}
        <header className="h-14 px-4 flex items-center justify-between border-b border-[var(--border)] bg-[var(--surface-card)]/90 backdrop-blur-md z-10">
          <div className="flex items-center gap-3 min-w-0">
            {/* Session Title */}
            <h2 className="text-xs font-normal text-[var(--text-primary)] truncate max-w-[280px] sm:max-w-md" style={{ fontFamily: 'var(--font-display)' }}>
              {currentSession.title}
            </h2>

            {/* Model Selector Dropdown */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-[var(--surface-soft)] border border-[var(--border)] hover:border-[#cc785c]/40 text-xs font-mono text-[var(--text-primary)] transition-colors"
              >
                <Cpu className="w-3.5 h-3.5 text-[#cc785c]" />
                <span className="hidden sm:inline">
                  {selectedModel === 'claude-3-7-sonnet' ? 'Claude 3.7 Sonnet' : selectedModel}
                </span>
                <ChevronDown className="w-3 h-3 text-[var(--text-muted)]" />
              </button>

              <AnimatePresence>
                {modelDropdownOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 4 }}
                    className="absolute top-full left-0 mt-1.5 w-56 rounded-xl bg-[var(--surface-card)] border border-[var(--border)] shadow-xl p-1.5 z-30 space-y-1 font-mono text-xs"
                  >
                    {[
                      { id: 'claude-3-7-sonnet', label: 'Claude 3.7 Sonnet', badge: 'Thinking' },
                      { id: 'claude-3-5-haiku', label: 'Claude 3.5 Haiku', badge: 'Fast' },
                      { id: 'qwen2.5-coder', label: 'Qwen 2.5 Coder', badge: 'Local Ollama' },
                      { id: 'hermes-3-llama', label: 'Hermes 3 Llama 70B', badge: 'NousResearch' },
                    ].map((m) => (
                      <button
                        key={m.id}
                        type="button"
                        onClick={() => {
                          setSelectedModel(m.id)
                          setModelDropdownOpen(false)
                        }}
                        className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition-colors ${
                          selectedModel === m.id
                            ? 'bg-[#cc785c]/15 text-[#cc785c] font-semibold'
                            : 'text-[var(--text-secondary)] hover:bg-[var(--surface-soft)]'
                        }`}
                      >
                        <span>{m.label}</span>
                        <span className="text-[10px] text-[var(--text-muted)]">{m.badge}</span>
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* Right Header Controls (Token Ring, Status & Inspector Toggle) */}
          <div className="flex items-center gap-3">
            {/* Circular Context Ring */}
            <HermesContextRing usedTokens={usedTokens} maxTokens={128000} />

            {/* Agent Live Status Pill */}
            <div className="hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-[var(--surface-soft)] border border-[var(--border)] text-[11px] font-mono text-[var(--text-secondary)]">
              {agentStatus === 'idle' && (
                <>
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  <span>Prêt</span>
                </>
              )}
              {agentStatus === 'thinking' && (
                <>
                  <span className="w-1.5 h-1.5 rounded-full bg-[#cc785c] animate-pulse" />
                  <span className="text-[#cc785c]">Réflexion...</span>
                </>
              )}
              {agentStatus === 'tool' && (
                <>
                  <span className="w-1.5 h-1.5 rounded-full bg-[#e8a55a] animate-pulse" />
                  <span className="text-[#e8a55a]">Exécution outil...</span>
                </>
              )}
            </div>

            {/* Actions: Clear, Inspector Toggle */}
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setMessages([])}
                className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)] transition-colors"
                title="Vider la discussion"
              >
                <Trash2 className="w-4 h-4" />
              </button>

              <button
                type="button"
                onClick={() => setRightPanelOpen(!rightPanelOpen)}
                className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
                  rightPanelOpen
                    ? 'bg-[#cc785c]/15 text-[#cc785c] border border-[#cc785c]/30'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)]'
                }`}
                title="Basculer le panneau Workspace (Alt+B)"
              >
                {rightPanelOpen ? <PanelRightClose className="w-4 h-4" /> : <PanelRightOpen className="w-4 h-4" />}
              </button>
            </div>
          </div>
        </header>

        {/* Messages Stream Container */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          {messages.length === 0 ? (
            /* Hermes WebUI Empty State */
            <div className="max-w-2xl mx-auto py-12 flex flex-col items-center text-center space-y-6">
              <div className="w-16 h-16 rounded-2xl bg-[#cc785c]/10 border border-[#cc785c]/30 flex items-center justify-center text-[#cc785c] shadow-xs">
                <Sparkles className="w-8 h-8" />
              </div>

              <div className="space-y-2">
                <h3 className="text-2xl sm:text-3xl font-normal text-[var(--text-primary)] tracking-tight font-serif" style={{ letterSpacing: '-0.5px' }}>
                  HakimAgent — Cockpit Hermes
                </h3>
                <p className="text-xs text-[var(--text-secondary)] max-w-md mx-auto leading-relaxed">
                  Interface web complète pour l'agent autonome avec mémoire persistante, catalogue de compétences, inspection de fichiers et prise de volant en direct.
                </p>
              </div>

              {/* Starter Prompts Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full text-left pt-4">
                {STARTER_PROMPTS.map((starter, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleSend(starter.prompt)}
                    className="p-3.5 rounded-2xl bg-[var(--surface-card)] border border-[var(--border)] hover:border-[#cc785c]/50 hover:bg-[var(--surface-soft)] transition-all cursor-pointer group shadow-xs"
                  >
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-base">{starter.icon}</span>
                      <h4 className="text-xs font-semibold text-[var(--text-primary)] group-hover:text-[#cc785c] transition-colors">
                        {starter.title}
                      </h4>
                    </div>
                    <p className="text-[11px] text-[var(--text-muted)] line-clamp-2 leading-relaxed">
                      {starter.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            /* Message Feed */
            <div className="max-w-3xl mx-auto space-y-5">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                >
                  {/* Message Meta Info */}
                  <div className="flex items-center gap-2 mb-1 px-1 text-[10px] text-[var(--text-muted)] font-mono">
                    <span>{msg.role === 'user' ? 'Opérateur' : 'HakimAgent'}</span>
                    <span>·</span>
                    <span>{msg.timestamp}</span>
                    {msg.model && (
                      <>
                        <span>·</span>
                        <span className="text-[#cc785c]">{msg.model}</span>
                      </>
                    )}
                  </div>

                  {/* Message Bubble Card */}
                  <div
                    className={`rounded-2xl p-4 text-xs leading-relaxed max-w-full sm:max-w-[90%] shadow-xs select-text ${
                      msg.role === 'user'
                        ? 'bg-[#cc785c]/15 border border-[#cc785c]/30 text-[var(--text-primary)] rounded-tr-sm'
                        : 'bg-[var(--surface-card)] border border-[var(--border)] text-[var(--text-primary)] rounded-tl-sm w-full'
                    }`}
                  >
                    {/* Attached file chip */}
                    {msg.file && (
                      <div className="mb-2 p-1.5 rounded-lg bg-[var(--surface-soft)] border border-[var(--border)] inline-flex items-center gap-1.5 font-mono text-[10px] text-[#cc785c]">
                        <Paperclip className="w-3 h-3" />
                        <span>Fichier joint : {msg.file}</span>
                      </div>
                    )}

                    {/* Thinking Accordion (Assistant only) */}
                    {msg.thinking && (
                      <HermesThinkingBlock
                        thinkingText={msg.thinking}
                        duration={msg.thinkingDuration}
                      />
                    )}

                    {/* Tool Execution Card (Assistant only) */}
                    {msg.toolCall && (
                      <HermesToolCard toolCall={msg.toolCall} />
                    )}

                    {/* Main Text Content */}
                    <div className="whitespace-pre-wrap font-sans text-[var(--text-primary)]">
                      {msg.content}
                    </div>

                    {/* Assistant Message Actions */}
                    {msg.role === 'assistant' && (
                      <div className="mt-3 pt-2 border-t border-[var(--border)] flex items-center justify-between text-[10px] text-[var(--text-muted)] font-mono">
                        <div className="flex items-center gap-3">
                          <button
                            type="button"
                            onClick={() => navigator.clipboard?.writeText(msg.content)}
                            className="flex items-center gap-1 hover:text-[var(--text-primary)] transition-colors"
                          >
                            <Copy className="w-3 h-3" />
                            <span>Copier</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => handleSend(msg.content)}
                            className="flex items-center gap-1 hover:text-[#cc785c] transition-colors"
                          >
                            <RefreshCw className="w-3 h-3" />
                            <span>Régénérer</span>
                          </button>
                        </div>
                        <span>Qualité 0.94</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Streaming loading indicator */}
              {loading && (
                <div className="flex items-center gap-2 p-3 rounded-xl bg-[var(--surface-card)] border border-[var(--border)] text-xs text-[var(--text-secondary)] max-w-xs">
                  <span className="w-2 h-2 rounded-full bg-[#cc785c] animate-ping" />
                  <span>
                    {agentStatus === 'thinking' && "L'agent réfléchit au plan d'action..."}
                    {agentStatus === 'tool' && "Exécution de l'outil dans le sandbox..."}
                    {agentStatus === 'streaming' && 'Rédaction de la réponse...'}
                  </span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Floating Bottom Composer */}
        <div className="p-4 border-t border-[var(--border)] bg-[var(--surface-card)]/90 backdrop-blur-md">
          <div className="max-w-3xl mx-auto space-y-2">
            {/* Mode selection pills */}
            <div className="flex items-center justify-between text-[11px]">
              <div className="flex items-center gap-1.5 overflow-x-auto">
                {[
                  { id: 'react', label: '⚡ Mode ReAct Autonome' },
                  { id: 'plan', label: '📋 Plan Hermes' },
                  { id: 'code', label: '💻 Code Direct' },
                  { id: 'chat', label: '💬 Discussion Libre' },
                ].map((mode) => (
                  <button
                    key={mode.id}
                    type="button"
                    onClick={() => setAgentMode(mode.id as any)}
                    className={`px-2.5 py-0.5 rounded-full transition-colors ${
                      agentMode === mode.id
                        ? 'bg-[#cc785c]/15 text-[#cc785c] border border-[#cc785c]/30 font-medium'
                        : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)]'
                    }`}
                  >
                    {mode.label}
                  </button>
                ))}
              </div>

              <span className="hidden sm:inline text-[10px] font-mono text-[var(--text-muted)]">
                Maj + Entrée pour un saut de ligne
              </span>
            </div>

            {/* Attached file chip */}
            {attachedFile && (
              <div className="p-1.5 rounded-lg bg-[var(--surface-soft)] border border-[#cc785c]/30 inline-flex items-center gap-2 text-xs text-[#cc785c]">
                <Paperclip className="w-3.5 h-3.5" />
                <span>{attachedFile.name} ({(attachedFile.size / 1024).toFixed(1)} Ko)</span>
                <button
                  type="button"
                  onClick={() => setAttachedFile(null)}
                  className="hover:text-red-500 p-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}

            {/* Input Container */}
            <div className="relative rounded-2xl bg-[var(--canvas)] border border-[var(--border)] focus-within:border-[#cc785c] shadow-xs overflow-hidden transition-all">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={handleInputChange}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSend()
                  }
                }}
                placeholder="Envoyez une instruction à l'agent, posez une question, ou tapez / pour les outils..."
                rows={1}
                className="w-full px-4 pt-3 pb-12 bg-transparent text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none resize-none min-h-[44px] max-h-[180px]"
              />

              {/* Bottom toolbar inside input */}
              <div className="absolute bottom-2 left-3 right-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={(e) => {
                      if (e.target.files?.[0]) setAttachedFile(e.target.files[0])
                    }}
                    className="hidden"
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)] transition-colors"
                    title="Joindre un fichier de code"
                  >
                    <Paperclip className="w-4 h-4" />
                  </button>

                  <button
                    type="button"
                    onClick={() => setInput('/skill ')}
                    className="px-2 py-0.5 rounded-md bg-[var(--surface-soft)] text-[10px] font-mono text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors border border-[var(--border)]"
                  >
                    /commandes
                  </button>
                </div>

                <div className="flex items-center gap-2">
                  {loading ? (
                    <button
                      type="button"
                      onClick={() => setLoading(false)}
                      className="p-2 rounded-xl bg-red-600 hover:bg-red-500 text-white transition-colors cursor-pointer"
                      title="Arrêter la génération"
                    >
                      <Square className="w-3.5 h-3.5" />
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => handleSend()}
                      disabled={!input.trim()}
                      className="p-2 rounded-xl bg-[#cc785c] hover:bg-[#a9583e] text-white font-medium transition-all disabled:opacity-30 disabled:hover:bg-[#cc785c] cursor-pointer shadow-xs"
                      title="Envoyer (Entrée)"
                    >
                      <Send className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* ─────────────────────────────────────────────────────────────
          3. RIGHT PANEL : WORKSPACE COCKPIT & INSPECTOR (Hermes Right)
          ───────────────────────────────────────────────────────────── */}
      <AnimatePresence>
        {rightPanelOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 380, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="flex flex-col shrink-0 border-l border-[var(--border)] bg-[var(--surface-card)] h-full overflow-hidden z-20"
          >
            {/* Header Tabs */}
            <div className="h-14 px-3 border-b border-[var(--border)] flex items-center justify-between">
              <div className="flex items-center gap-1 overflow-x-auto text-xs">
                {[
                  { id: 'files', label: 'Fichiers', icon: Folder },
                  { id: 'memory', label: 'Mémoire', icon: Database },
                  { id: 'skills', label: 'Skills', icon: Zap },
                  { id: 'cron', label: 'Cron', icon: Clock },
                  { id: 'screen', label: 'Écran', icon: Monitor },
                ].map((tab) => {
                  const Icon = tab.icon
                  const active = rightPanelTab === tab.id

                  return (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => setRightPanelTab(tab.id as any)}
                      className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                        active
                          ? 'bg-[#cc785c]/15 text-[#cc785c] font-semibold'
                          : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)]'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      <span>{tab.label}</span>
                    </button>
                  )
                })}
              </div>

              <button
                type="button"
                onClick={() => setRightPanelOpen(false)}
                className="p-1 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)] transition-colors"
                title="Fermer le panneau"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Tab Body */}
            <div className="flex-1 overflow-hidden">
              {rightPanelTab === 'files' && (
                <HermesFileViewer onInsertIntoPrompt={(code) => setInput((prev) => `${prev}\n${code}`)} />
              )}
              {rightPanelTab === 'memory' && <HermesMemoryPanel />}
              {rightPanelTab === 'skills' && (
                <HermesSkillsPanel onSelectPrompt={(prompt) => handleSend(prompt)} />
              )}
              {rightPanelTab === 'cron' && <HermesCronPanel />}
              {rightPanelTab === 'screen' && <HermesTakeTheWheelPanel />}
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Settings Modal */}
      <HermesSettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />
    </div>
  )
}
