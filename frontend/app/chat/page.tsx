'use client'

import { useEffect, useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import AppShell from '@/components/AppShell'
import PageHeader from '@/components/PageHeader'
import { useAuth } from '@/contexts/AuthContext'
import {
  PaperPlaneRight,
  Stop,
  Spinner,
  Brain,
  User,
  Paperclip,
  X,
  Sparkle,
  Terminal,
  Cpu,
  CaretDown,
  Globe,
  Eye,
  DownloadSimple,
  DeviceMobile,
  Desktop,
  DeviceTablet,
} from '@phosphor-icons/react'
import HermesWebUI from '@/components/hermes/HermesWebUI'
import { TaskResult } from '@/lib/api'

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

export interface ModelOption {
  id: string
  name: string
  provider: string
  badge: string
  description: string
}

const DEFAULT_MODELS: ModelOption[] = [
  {
    id: 'auto',
    name: 'Auto-Route Intelligent (APEX)',
    provider: 'APEX Router',
    badge: 'Auto',
    description: 'Sélectionne le meilleur modèle selon la complexité et les outils requis',
  },
  {
    id: 'gemini-2.5-flash',
    name: 'Gemini 2.5 Flash',
    provider: 'Google AI Studio',
    badge: 'Rapide',
    description: 'Ultra-rapide, multimodal, contexte large (1M tokens)',
  },
  {
    id: 'gemini-2.5-pro',
    name: 'Gemini 2.5 Pro',
    provider: 'Google AI Studio',
    badge: 'Raisonnement',
    description: 'Raisonnement poussé, analyse complexe et capacités mathématiques',
  },
  {
    id: 'anthropic/claude-3.7-sonnet',
    name: 'Claude 3.7 Sonnet',
    provider: 'Anthropic / OpenRouter',
    badge: 'Code Star',
    description: 'Référence d\'élite pour l\'ingénierie logicielle et le refactoring',
  },
  {
    id: 'anthropic/claude-3.5-haiku',
    name: 'Claude 3.5 Haiku',
    provider: 'Anthropic / OpenRouter',
    badge: 'Éco',
    description: 'Réponses instantanées et légères pour les requêtes rapides',
  },
  {
    id: 'openai/gpt-4o',
    name: 'GPT-4o',
    provider: 'OpenAI / OpenRouter',
    badge: 'GPT',
    description: 'Modèle phare d\'OpenAI, polyvalent et multimodal',
  },
  {
    id: 'deepseek/deepseek-chat',
    name: 'DeepSeek V3',
    provider: 'DeepSeek / OpenRouter',
    badge: 'V3',
    description: 'Excellente efficacité algorithmique et complétion de code',
  },
  {
    id: 'deepseek/deepseek-r1',
    name: 'DeepSeek R1',
    provider: 'DeepSeek / OpenRouter',
    badge: 'R1',
    description: 'Raisonnement profond en chaîne de pensée (Chain-of-Thought)',
  },
  {
    id: 'meta-llama/llama-3.3-70b-instruct',
    name: 'Llama 3.3 70B',
    provider: 'Meta / OpenRouter',
    badge: 'Llama',
    description: 'Grand modèle open source puissant et polyvalent',
  },
  {
    id: 'omniroute/auto/best-coding',
    name: 'OmniRoute · Best Coding (Local 20128)',
    provider: 'OmniRoute Gateway',
    badge: 'Omni Code',
    description: 'Sélection automatique du meilleur modèle de programmation via OmniRoute',
  },
  {
    id: 'omniroute/auto/best-fast',
    name: 'OmniRoute · Best Fast (Local 20128)',
    provider: 'OmniRoute Gateway',
    badge: 'Omni Fast',
    description: 'Modèle le plus rapide via la passerelle locale OmniRoute',
  },
  {
    id: 'omniroute/auto/best-reasoning',
    name: 'OmniRoute · Best Reasoning (Local 20128)',
    provider: 'OmniRoute Gateway',
    badge: 'Omni Think',
    description: 'Modèle de raisonnement logique via la passerelle locale OmniRoute',
  },
]

export interface AgentOption {
  id: string
  name: string
  icon: string
  badge: string
  description: string
}

const AVAILABLE_AGENTS: AgentOption[] = [
  {
    id: "auto",
    name: "Auto-Routing APEX",
    icon: "🤖",
    badge: "Auto",
    description: "Sélection algorithmique intelligente selon la complexité et les outils requis",
  },
  {
    id: "AGENT_WEB_BUILDER",
    name: "Créateur de Sites Web",
    icon: "🌐",
    badge: "Spécialiste Web",
    description: "Conçoit et génère des sites web complets, landing pages SaaS et interfaces interactives de A à Z",
  },
  {
    id: "AGENT_CODER",
    name: "Développeur Full-Stack",
    icon: "💻",
    badge: "Code",
    description: "Génération de code TypeScript/Python, refactoring et tests unitaires",
  },
  {
    id: "AGENT_ARCHITECT",
    name: "Architecte Système",
    icon: "🏗️",
    badge: "Archi",
    description: "Design patterns, C4 diagrams, décisions architecturales (ADR) et choix de stacks",
  },
  {
    id: "AGENT_DEBUGGER",
    name: "Débugger Avancé",
    icon: "🐛",
    badge: "Debug",
    description: "Isolation des root causes, correction de crashs et analyse de stack traces",
  },
  {
    id: "AGENT_RESEARCHER",
    name: "Chercheur & Veille",
    icon: "🔍",
    badge: "Recherche",
    description: "Recherche web en direct, benchmarks comparatifs et synthèses documentées",
  },
  {
    id: "AGENT_ANALYST",
    name: "Analyste Données",
    icon: "📊",
    badge: "Data",
    description: "Requêtes SQL optimisées, statistiques descriptives et extraction d'insights",
  },
  {
    id: "AGENT_WRITER",
    name: "Rédacteur Technique",
    icon: "✍️",
    badge: "Rédaction",
    description: "Documentation claire, guides techniques et fiches de spécification",
  },
]

function extractHtmlCode(content: string): string | null {
  const match = content.match(/```html\s*([\s\S]*?)```/i)
  if (match && match[1]) return match[1].trim()
  if (content.includes('<!DOCTYPE html>') || content.includes('<html')) {
    const start = content.indexOf('<!DOCTYPE html>') !== -1 ? content.indexOf('<!DOCTYPE html>') : content.indexOf('<html')
    const end = content.lastIndexOf('</html>')
    if (start !== -1 && end !== -1) {
      return content.slice(start, end + 7).trim()
    }
  }
  return null
}

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  task?: TaskResult
  file?: string
  modelUsed?: string
}

export default function ChatPage() {
  const { user, token } = useAuth()
  const [viewMode, setViewMode] = useState<'agent' | 'hermes'>('agent')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [attachedFile, setAttachedFile] = useState<File | null>(null)
  const [conversationId, setConversationId] = useState<number | null>(null)
  const [selectedModel, setSelectedModel] = useState<string>('auto')

  const [selectedAgent, setSelectedAgent] = useState<string>('auto')
  const [previewHtml, setPreviewHtml] = useState<string | null>(null)
  const [previewDevice, setPreviewDevice] = useState<'desktop' | 'tablet' | 'mobile'>('desktop')
  const [saveNotification, setSaveNotification] = useState<string | null>(null)
  const [availableModels, setAvailableModels] = useState<ModelOption[]>(DEFAULT_MODELS)
  const [activeProvider, setActiveProvider] = useState<string>('')
  const [omniRouteStatus, setOmniRouteStatus] = useState<{ online: boolean; models_count?: number } | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  // Charger la liste des modèles depuis le backend
  useEffect(() => {
    fetch('/api/v1/models')
      .then(res => res.json())
      .then(data => {
        if (data.models && Array.isArray(data.models)) {
          setAvailableModels(data.models)
        }
        if (data.active_provider) {
          setActiveProvider(data.active_provider)
        }
        if (data.omniroute) {
          setOmniRouteStatus(data.omniroute)
        }
      })
      .catch(() => {
        // Fallback transparent sur DEFAULT_MODELS
      })
  }, [])

  const handleModelChange = async (newModel: string) => {
    setSelectedModel(newModel)
    try {
      await fetch('/api/v1/models/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: newModel }),
      })
    } catch {
      // Ignore network errors in local dev
    }
  }

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

  
  const handleSaveWebsite = async (html: string, siteName: string = 'mon-site-web') => {
    try {
      const res = await fetch('/api/v1/websites/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: siteName, html }),
      })
      const data = await res.json()
      if (data.status === 'ok') {
        setSaveNotification(`✅ Site enregistré dans ${data.relative_path}`)
        setTimeout(() => setSaveNotification(null), 5000)
      }
    } catch {
      setSaveNotification('❌ Erreur lors de la sauvegarde du site')
      setTimeout(() => setSaveNotification(null), 4000)
    }
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return
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
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        credentials: 'include',
        headers,
        body: JSON.stringify({
          content: finalContent,
          conversation_id: conversationId,
          model: selectedModel,
          agent: selectedAgent,
        }),
      })
      const data = await res.json()
      if (res.ok) {
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content: data.response,
            task: data.task,
            modelUsed: data.task?.model || (selectedModel !== 'auto' ? selectedModel : undefined),
          },
        ])
        if (data.conversation_id && !conversationId) {
          setConversationId(data.conversation_id)
        }
      } else {
        setMessages(prev => [...prev, { role: 'system', content: data.detail || 'Erreur API' }])
      }
    } catch {
      setMessages(prev => [
        ...prev,
        { role: 'system', content: 'Erreur de connexion à l\'API. Vérifiez que le serveur backend est actif.' },
      ])
    } finally {
      setLoading(false)
      setAttachedFile(null)
    }
  }

  // Si l'utilisateur choisit le cockpit Hermes plein écran
  if (viewMode === 'hermes') {
    return (
      <div className="relative h-screen w-screen overflow-hidden">
        <div className="absolute top-3 right-4 z-50">
          <button
            onClick={() => setViewMode('agent')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-[var(--border)] bg-[var(--surface-card)] text-[var(--text-primary)] hover:border-[var(--accent)] hover:text-[var(--accent)] shadow-sm transition-all cursor-pointer"
          >
            <Brain size={14} />
            <span>Retour à l'interface Agent</span>
          </button>
        </div>
        <HermesWebUI />
      </div>
    )
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Orchestration"
        title="Interface de l'Agent"
        description="Décrivez une tâche ou posez une question. Choisissez votre modèle IA ou laissez APEX sélectionner dynamiquement le modèle optimal."
        actions={
          <div className="flex items-center gap-3 flex-wrap">
            {/* Statut OmniRoute Live */}
            {omniRouteStatus?.online && (
              <div
                className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-mono border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 bg-emerald-500/5 shadow-xs"
                title={`Passerelle OmniRoute active sur le port 20128 (${omniRouteStatus.models_count || 782} modèles connectés)`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span>OmniRoute :20128 ({omniRouteStatus.models_count || 782})</span>
              </div>
            )}

                        {/* Sélecteur d'Agent Dédié */}
            <div
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[var(--border)] shadow-xs transition-colors"
              style={{ background: 'var(--surface-card)' }}
            >
              <span className="text-sm">{AVAILABLE_AGENTS.find(a => a.id === selectedAgent)?.icon || '🤖'}</span>
              <label htmlFor="agent-select" className="text-xs font-medium text-[var(--text-secondary)] whitespace-nowrap">
                Agent :
              </label>
              <div className="relative inline-flex items-center">
                <select
                  id="agent-select"
                  value={selectedAgent}
                  onChange={e => setSelectedAgent(e.target.value)}
                  className="text-xs font-semibold bg-transparent text-[var(--text-primary)] outline-none pr-5 cursor-pointer appearance-none"
                >
                  {AVAILABLE_AGENTS.map(a => (
                    <option key={a.id} value={a.id} className="bg-[var(--surface-card)] text-[var(--text-primary)]">
                      {a.icon} {a.name} [{a.badge}]
                    </option>
                  ))}
                </select>
                <CaretDown size={12} className="absolute right-0 pointer-events-none text-[var(--text-muted)]" />
              </div>
            </div>

            {/* Sélecteur de Modèle IA */}
            <div
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[var(--border)] shadow-xs transition-colors"
              style={{ background: 'var(--surface-card)' }}
            >
              <Cpu size={15} style={{ color: 'var(--accent)' }} />
              <label htmlFor="model-select" className="text-xs font-medium text-[var(--text-secondary)] whitespace-nowrap">
                Modèle :
              </label>
              <div className="relative inline-flex items-center">
                <select
                  id="model-select"
                  value={selectedModel}
                  onChange={e => handleModelChange(e.target.value)}
                  className="text-xs font-semibold bg-transparent text-[var(--text-primary)] outline-none pr-5 cursor-pointer appearance-none"
                >
                  {availableModels.map(m => (
                    <option key={m.id} value={m.id} className="bg-[var(--surface-card)] text-[var(--text-primary)]">
                      {m.name} [{m.badge || m.provider}]
                    </option>
                  ))}
                </select>
                <CaretDown size={12} className="absolute right-0 pointer-events-none text-[var(--text-muted)]" />
              </div>
            </div>

            {/* Bascule Vue Agent / Cockpit Hermes */}
            <div
              className="inline-flex rounded-lg p-1 border border-[var(--border)]"
              style={{ background: 'var(--surface-soft)' }}
            >
              <button
                type="button"
                onClick={() => setViewMode('agent')}
                className="px-3 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer bg-[var(--surface-raised)] text-[var(--accent)] shadow-xs"
              >
                Agent Standard
              </button>
              <button
                type="button"
                onClick={() => setViewMode('hermes')}
                className="px-3 py-1 text-xs font-medium rounded-md text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-all cursor-pointer flex items-center gap-1"
              >
                <Terminal size={12} />
                Cockpit Hermes
              </button>
            </div>
          </div>
        }
      />

      {/* Messages */}
      <div ref={scrollRef} className="min-h-[55dvh] max-h-[64dvh] overflow-y-auto pb-6 space-y-4 pr-1">
        {messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center h-full py-12 text-center"
          >
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5 shadow-xs"
              style={{ background: 'var(--accent-soft)', border: '1px solid var(--accent-soft-2)' }}
            >
              <Brain size={32} style={{ color: 'var(--accent)' }} />
            </div>
            <h2 className="font-serif text-3xl font-normal tracking-[-0.5px] text-[var(--text-primary)] mb-2">
              APEX est prêt
            </h2>
            <p className="text-sm text-[var(--text-secondary)] max-w-md mx-auto leading-relaxed">
              Sélectionnez un modèle ci-dessus ({availableModels.find(m => m.id === selectedModel)?.name || 'Auto-Route'}) ou décrivez votre tâche. Le scoring algorithmique gère l'exécution avec les outils natifs et connecteurs MCP.
            </p>
            <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
              {[
                '🌐 Créer un site SaaS comme AutoDS avec Tailwind CSS',
                '🌐 Créer un portfolio moderne de développeur dark mode',
                'Créer une API REST avec FastAPI',
                'Analyser un fichier Python',
              ].map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => setInput(prompt)}
                  className="btn-ghost text-xs py-3 px-4 text-left transition-all hover:border-[var(--accent)] hover:text-[var(--accent)] cursor-pointer"
                  style={{ background: 'var(--surface-card)', borderRadius: 10 }}
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
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              className="flex gap-3.5 max-w-3xl mx-auto"
            >
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                  msg.role === 'user'
                    ? 'border border-[var(--border)] text-[var(--text-primary)]'
                    : msg.role === 'system'
                    ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                    : 'border border-[var(--accent)]/30 text-[var(--accent)]'
                }`}
                style={{
                  background: msg.role === 'assistant' ? 'var(--accent-soft)' : 'var(--surface-card)',
                }}
              >
                {msg.role === 'user' ? <User size={16} /> : <Brain size={16} />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-xs font-semibold text-[var(--text-primary)]">
                    {msg.role === 'user' ? 'Vous' : msg.role === 'system' ? 'Système' : 'APEX'}
                  </span>
                  {msg.file && (
                    <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border border-[var(--border)] bg-[var(--surface-soft)] text-[var(--text-muted)] font-mono">
                      📎 {msg.file}
                    </span>
                  )}
                  <span className="text-[10px] text-[var(--text-muted)] font-mono">
                    {new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <div
                  className={`rounded-2xl px-4 py-3.5 shadow-xs ${
                    msg.role === 'user'
                      ? 'border border-[var(--border)]'
                      : msg.role === 'system'
                      ? 'bg-red-950/20 text-red-300 border border-red-500/20'
                      : 'border border-[var(--border)]'
                  }`}
                  style={{
                    background: msg.role === 'user' ? 'var(--surface-soft)' : msg.role === 'assistant' ? 'var(--surface-card)' : undefined
                  }}
                >
                  <p className="text-sm leading-relaxed whitespace-pre-wrap text-[var(--text-primary)]">{msg.content}</p>

                  {/* Boutons d'Action Web Builder si du code HTML est présent */}
                  {msg.role === 'assistant' && extractHtmlCode(msg.content) && (
                    <div className="mt-3.5 p-3 rounded-xl border border-cyan-500/20 bg-cyan-500/5 flex flex-wrap items-center justify-between gap-3">
                      <div className="flex items-center gap-2 text-xs font-medium text-cyan-600 dark:text-cyan-400">
                        <Globe size={16} className="animate-spin-slow" />
                        <span>Site web interactif prêt à être prévisualisé</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => setPreviewHtml(extractHtmlCode(msg.content))}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 text-white shadow-xs transition-all cursor-pointer"
                        >
                          <Eye size={14} />
                          <span>Aperçu Live</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleSaveWebsite(extractHtmlCode(msg.content)!, 'site-web-apex')}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-[var(--border)] bg-[var(--surface-card)] hover:bg-[var(--surface-raised)] text-[var(--text-primary)] transition-all cursor-pointer"
                        >
                          <DownloadSimple size={14} />
                          <span>Sauvegarder</span>
                        </button>
                      </div>
                    </div>
                  )}

                  {msg.task && (
                    <div className="mt-3 pt-3 border-t border-[var(--border)] flex flex-wrap items-center gap-4 text-xs font-mono">
                      <span className="text-[var(--text-muted)]">
                        Agent: <strong className="text-[var(--accent)] font-semibold">{msg.task.agent}</strong>
                      </span>
                      {msg.task.model && (
                        <span className="text-[var(--text-muted)]">
                          Modèle: <strong className="text-[var(--text-primary)] font-semibold">{msg.task.model}</strong>
                        </span>
                      )}
                      <span className="text-[var(--text-muted)]">
                        Score: <span className="text-[var(--text-primary)] font-semibold">{msg.task.score}</span>
                      </span>
                      <span className="text-[var(--text-muted)]">
                        Itération: <span className="text-[var(--text-primary)] font-semibold">{msg.task.iteration}</span>
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {loading && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-3.5 max-w-3xl mx-auto"
          >
            <div
              className="w-8 h-8 rounded-lg border border-[var(--border)] flex items-center justify-center shrink-0"
              style={{ background: 'var(--surface-card)' }}
            >
              <Brain size={16} style={{ color: 'var(--accent)' }} />
            </div>
            <div
              className="border border-[var(--border)] rounded-2xl px-4 py-3 flex items-center gap-2.5 shadow-xs"
              style={{ background: 'var(--surface-card)' }}
            >
              <Spinner size={16} className="animate-spin text-[var(--accent)]" />
              <span className="text-xs font-medium text-[var(--text-secondary)]">
                APEX réfléchit avec {availableModels.find(m => m.id === selectedModel)?.name || selectedModel}...
              </span>
            </div>
          </motion.div>
        )}
      </div>

      {/* Attached file chip */}
      {attachedFile && (
        <div className="pb-2 max-w-3xl mx-auto">
          <div
            className="flex items-center gap-2.5 px-3 py-2 rounded-xl border border-[var(--border)] shadow-xs"
            style={{ background: 'var(--surface-card)' }}
          >
            <span className="text-sm">📎</span>
            <span className="text-xs font-mono flex-1 truncate text-[var(--text-primary)]">
              {attachedFile.name}
            </span>
            <span className="text-xs font-mono shrink-0 text-[var(--text-muted)]">
              {(attachedFile.size / 1024).toFixed(1)} Ko
            </span>
            <button
              onClick={() => setAttachedFile(null)}
              className="p-1 rounded-md text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)] transition-colors cursor-pointer"
              title="Retirer le fichier"
            >
              <X size={14} />
            </button>
          </div>
        </div>
      )}

      {/* Input */}
      <div className="sticky bottom-0 border-t border-[var(--border)] pt-4 pb-2" style={{ background: 'var(--canvas)' }}>
        <div className="ai-input-wrap max-w-3xl mx-auto">
          <div className="flex items-center px-4 py-3 gap-3">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Décrivez une tâche ou posez une question à APEX..."
              className="flex-1 text-sm py-1 bg-transparent outline-none text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
              disabled={loading}
            />
          </div>
          <div className="flex items-center justify-between px-3 pb-2.5 pt-0.5 border-t border-[var(--border)]">
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="input-action-btn hover:text-[var(--accent)] transition-colors cursor-pointer"
                title="Joindre un fichier"
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
              >
                <Paperclip size={16} />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPTED_EXTENSIONS.map(e => '.' + e).join(',')}
                onChange={handleFileSelected}
                className="hidden"
                tabIndex={-1}
              />

              {/* Quick model badge indicator */}
              <div
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-mono border border-[var(--border)] text-[var(--text-secondary)]"
                style={{ background: 'var(--surface-soft)' }}
                title="Modèle sélectionné pour cette session"
              >
                <Sparkle size={12} style={{ color: 'var(--accent)' }} />
                <span>{availableModels.find(m => m.id === selectedModel)?.badge || 'Auto'}</span>
              </div>
            </div>

            <button
              type="button"
              onClick={loading ? () => {} : handleSend}
              disabled={loading || !input.trim()}
              aria-label="Envoyer le message"
              className={`inline-flex items-center justify-center w-8 h-8 rounded-lg transition-all cursor-pointer ${
                input.trim() && !loading
                  ? 'bg-[#cc785c] text-white shadow-xs hover:bg-[#a9583e]'
                  : 'bg-[var(--surface-soft)] text-[var(--text-muted)] cursor-not-allowed'
              }`}
            >
              {loading ? <Stop size={16} /> : <PaperPlaneRight size={16} weight="bold" />}
            </button>
          </div>
        </div>
      </div>

      {/* Toast de Sauvegarde */}
      {saveNotification && (
        <div className="fixed bottom-20 right-6 z-50 bg-emerald-600 text-white px-4 py-2.5 rounded-xl shadow-lg text-xs font-semibold flex items-center gap-2 animate-bounce">
          <span>{saveNotification}</span>
        </div>
      )}

      {/* Modal d'Aperçu Live du Site Web */}
      <AnimatePresence>
        {previewHtml && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex flex-col p-4 sm:p-6"
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between pb-4 border-b border-white/10 shrink-0">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-cyan-500/20 text-cyan-400">
                  <Globe size={20} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">Prévisualisation du Site Web</h3>
                  <p className="text-xs text-slate-400">Généré par l'Agent Créateur de Sites Web (HTML5 + Tailwind CSS)</p>
                </div>
              </div>

              {/* Viewport Switcher */}
              <div className="hidden sm:flex items-center gap-1 bg-white/10 p-1 rounded-lg border border-white/10">
                <button
                  type="button"
                  onClick={() => setPreviewDevice('desktop')}
                  className={`p-1.5 rounded-md text-xs font-medium flex items-center gap-1 transition ${
                    previewDevice === 'desktop' ? 'bg-cyan-600 text-white shadow-xs' : 'text-slate-300 hover:text-white'
                  }`}
                  title="Écran large (Desktop 100%)"
                >
                  <Desktop size={14} />
                  <span>Desktop</span>
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewDevice('tablet')}
                  className={`p-1.5 rounded-md text-xs font-medium flex items-center gap-1 transition ${
                    previewDevice === 'tablet' ? 'bg-cyan-600 text-white shadow-xs' : 'text-slate-300 hover:text-white'
                  }`}
                  title="Tablette (768px)"
                >
                  <DeviceTablet size={14} />
                  <span>Tablette</span>
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewDevice('mobile')}
                  className={`p-1.5 rounded-md text-xs font-medium flex items-center gap-1 transition ${
                    previewDevice === 'mobile' ? 'bg-cyan-600 text-white shadow-xs' : 'text-slate-300 hover:text-white'
                  }`}
                  title="Mobile (375px)"
                >
                  <DeviceMobile size={14} />
                  <span>Mobile</span>
                </button>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleSaveWebsite(previewHtml, 'site-web-apex')}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition cursor-pointer"
                >
                  <DownloadSimple size={14} />
                  <span>Enregistrer</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const blob = new Blob([previewHtml], { type: 'text/html' })
                    const url = URL.createObjectURL(blob)
                    window.open(url, '_blank')
                  }}
                  className="hidden md:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white/10 hover:bg-white/20 text-white transition cursor-pointer"
                >
                  <span>Nouvel onglet ↗</span>
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewHtml(null)}
                  className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white transition cursor-pointer"
                  title="Fermer l'aperçu"
                >
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Iframe Viewport Container */}
            <div className="flex-1 overflow-auto flex items-center justify-center p-2 sm:p-4">
              <div
                className={`h-full transition-all duration-300 rounded-xl overflow-hidden shadow-2xl border border-white/10 bg-slate-950 ${
                  previewDevice === 'mobile'
                    ? 'w-[375px] max-w-full'
                    : previewDevice === 'tablet'
                    ? 'w-[768px] max-w-full'
                    : 'w-full'
                }`}
              >
                <iframe
                  title="Site Web Preview"
                  srcDoc={previewHtml}
                  className="w-full h-full border-0 bg-white"
                  sandbox="allow-scripts allow-modals allow-same-origin allow-forms"
                />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

    </AppShell>
  )
}
