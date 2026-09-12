'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  PaperPlaneRight, SidebarSimple, CaretLeft, CaretRight,
  Plus, ClockCounterClockwise, Clock,
  MagnifyingGlass, SlidersHorizontal,
  Paperclip, Microphone, Code, ArrowRight,
  Lightning, TreeStructure, Robot, Sparkle, Trash, X,
  Users, Kanban, ChatCircleDots
} from '@phosphor-icons/react'
import {
  PanelLeft, FolderPlus, ArrowUpIcon, Code2, Rocket,
  Layers, Palette, CircleUserRound, MonitorIcon, FileUp, ImageIcon
} from 'lucide-react'
import { getHealth, chat, HealthStatus, getSkills, getSkillDetails, SkillInfo } from '@/lib/api'
import { Message, ConversationSession, ScheduledTask, Toast } from '@/lib/types'
import { loadState, saveState } from '@/lib/storage'
import Link from 'next/link'
import { useThemeContext } from '@/components/ThemeProvider'
import ThemeToggle from '@/components/ThemeToggle'
import { Component as SquishyPricing } from '@/components/ui/squishy-pricing'
import Editor from '@monaco-editor/react'

/* ================================================================
   CONSTANTS
   ================================================================ */
const AGENT_CONFIG: Record<string, { name: string; color: string; dotClass: string }> = {
  AGENT_QUICKSHOT:   { name: 'QUICKSHOT',  color: '#10b981', dotClass: 'bg-emerald-500' },
  AGENT_CODER:       { name: 'CODER',      color: '#3b82f6', dotClass: 'bg-blue-500' },
  AGENT_DEBUGGER:    { name: 'DEBUGGER',   color: '#ef4444', dotClass: 'bg-rose-500' },
  AGENT_RESEARCHER:  { name: 'RESEARCHER', color: '#f59e0b', dotClass: 'bg-amber-500' },
  AGENT_ARCHITECT:   { name: 'ARCHITECT',  color: '#ec4899', dotClass: 'bg-pink-500' },
  AGENT_WRITER:      { name: 'WRITER',     color: '#a855f7', dotClass: 'bg-purple-500' },
  AGENT_ANALYST:     { name: 'ANALYST',    color: '#14b8a6', dotClass: 'bg-teal-500' },
  AGENT_SYSADMIN:    { name: 'SYSADMIN',   color: '#D97757', dotClass: 'bg-[#D97757]' },
}

const NAV_LINKS = [
  { href: '/agents', label: 'Agents', icon: Robot },
  { href: '/memory', label: 'Mémoire', icon: TreeStructure },
  { href: '/tools', label: 'Outils', icon: Lightning },
]

const SUGGESTIONS = [
  { icon: '⚡', text: 'Résume le théorème CAP en 2 phrases' },
  { icon: '🏗️', text: 'Conçois une architecture microservices' },
  { icon: '🐛', text: 'Debug ce code Python avec asyncio' },
  { icon: '📊', text: 'Analyse les performances d\'une API REST' },
]

const ACCEPTED_EXTENSIONS = [
  'txt', 'md', 'markdown', 'py', 'js', 'mjs', 'ts', 'tsx', 'jsx',
  'json', 'csv', 'html', 'css', 'scss', 'sql', 'yaml', 'yml', 'xml',
  'sh', 'bat', 'cmd', 'ps1', 'ini', 'cfg', 'toml', 'env', 'log',
]

const MAX_FILE_SIZE = 100 * 1024

export type ExecutionPolicy = 'ALWAYS-PROCEED' | 'REQUEST-REVIEW' | 'STRICT' | 'SANDBOX'

export const POLICY_CONFIGS: Record<ExecutionPolicy, { label: string; badgeClass: string; dotClass: string; desc: string }> = {
  'ALWAYS-PROCEED': {
    label: 'ALWAYS-PROCEED',
    badgeClass: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:border-emerald-500/60',
    dotClass: 'bg-emerald-400 animate-pulse-emerald',
    desc: 'Exécution automatique sans confirmation (recommandé)',
  },
  'REQUEST-REVIEW': {
    label: 'REQUEST-REVIEW',
    badgeClass: 'bg-amber-500/10 text-amber-400 border-amber-500/30 hover:border-amber-500/60',
    dotClass: 'bg-amber-400',
    desc: 'Demande de validation avant chaque commande/écriture',
  },
  'STRICT': {
    label: 'STRICT',
    badgeClass: 'bg-rose-500/10 text-rose-400 border-rose-500/30 hover:border-rose-500/60',
    dotClass: 'bg-rose-400',
    desc: 'Mode strict : approbation manuelle obligatoire',
  },
  'SANDBOX': {
    label: 'SANDBOX',
    badgeClass: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30 hover:border-cyan-500/60',
    dotClass: 'bg-cyan-400',
    desc: 'Exécution restreinte en bac à sable isolé',
  },
}

const EXT_TO_LANG: Record<string, string> = {
  py: 'python', js: 'javascript', mjs: 'javascript', ts: 'typescript',
  tsx: 'typescript', jsx: 'javascript', json: 'json', md: 'markdown',
  markdown: 'markdown', html: 'html', css: 'css', scss: 'scss',
  sql: 'sql', yml: 'yaml', yaml: 'yaml', xml: 'xml', sh: 'bash',
  bat: 'batch', cmd: 'batch', ps1: 'powershell', ini: 'ini',
  cfg: 'ini', toml: 'toml', env: 'bash', log: 'text', txt: 'text',
  csv: 'csv',
}

function getAgent(key?: string) {
  if (!key) return { name: 'APEX', color: '#10b981', dotClass: 'bg-emerald-500' }
  return AGENT_CONFIG[key] || { name: key.replace('AGENT_', ''), color: '#10b981', dotClass: 'bg-emerald-500' }
}

/* ================================================================
   TOAST COMPONENT (21st.dev notification pattern)
   ================================================================ */
function ToastStack({ toasts, remove }: { toasts: Toast[]; remove: (id: string) => void }) {
  return (
    <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2 pointer-events-none">
      <AnimatePresence>
        {toasts.map(t => (
          <motion.div
            key={t.id}
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ type: 'spring', stiffness: 300, damping: 28 }}
            className="toast pointer-events-auto"
            style={{ minWidth: 240, maxWidth: 340 }}
          >
            <span className="text-lg">
              {t.type === 'success' ? '✓' : t.type === 'error' ? '✕' : 'ℹ'}
            </span>
            <span className="flex-1 text-sm">{t.message}</span>
            <button
              onClick={() => remove(t.id)}
              className="input-action-btn opacity-60 hover:opacity-100"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}

/* ================================================================
   TYPING INDICATOR (21st.dev animated dots)
   ================================================================ */
function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 py-2 pl-1">
      <div className="flex gap-1.5">
        <div className="typing-dot" />
        <div className="typing-dot" />
        <div className="typing-dot" />
      </div>
      <span className="text-mono" style={{ color: 'var(--text-muted)' }}>
        orchestration...
      </span>
    </div>
  )
}

/* ================================================================
   INTERACTIVE PERMISSION DIALOG (Antigravity 2.0 / Claude Code style)
   ================================================================ */
interface PermissionDialogProps {
  title?: string
  path?: string
  onAllow?: (option: number) => void
  onDeny?: () => void
}

function PermissionDialog({
  title = "Allow read access to this path?",
  path = "C:\\Users\\hp\\Desktop\\ntrsitecursur\\server.cjs",
  onAllow,
  onDeny
}: PermissionDialogProps) {
  const [selectedOption, setSelectedOption] = useState<number>(1)

  const options = [
    "Yes, allow this time",
    "Yes, and always allow in this conversation",
    "Yes, and always allow when not in a project",
    "Yes, and always allow",
    "No (tell the agent what to do instead)"
  ]

  const handleSubmit = () => {
    if (selectedOption === 5) {
      if (onDeny) onDeny()
    } else {
      if (onAllow) onAllow(selectedOption)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      className="my-4 p-5 rounded-2xl border shadow-2xl space-y-4 max-w-xl mx-auto text-left font-sans"
      style={{
        background: 'var(--surface-raised)',
        borderColor: 'var(--border)',
        boxShadow: '0 20px 50px rgba(10, 10, 12, 0.14)'
      }}
    >
      <div className="flex items-center gap-2.5 font-bold text-sm" style={{ color: 'var(--text-primary)' }}>
        <span className="text-base">📄</span>
        <span>{title}</span>
      </div>

      <div className="px-3.5 py-2.5 rounded-lg font-mono text-xs truncate" style={{ color: 'var(--accent)', background: 'var(--bg-tertiary)', border: '1px solid var(--border)' }}>
        {path}
      </div>

      <div className="space-y-2 pt-1">
        {options.map((opt, idx) => {
          const num = idx + 1
          const isSelected = selectedOption === num
          return (
            <button
              key={num}
              onClick={() => setSelectedOption(num)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl border text-xs font-medium transition-all text-left cursor-pointer ${
                isSelected
                  ? 'text-white shadow-sm'
                  : 'hover:bg-opacity-60'
              }`}
              style={
                isSelected
                  ? { background: 'var(--accent)', borderColor: 'var(--accent)', color: '#fff' }
                  : { background: 'var(--bg-tertiary)', borderColor: 'var(--border)', color: 'var(--text-secondary)' }
              }
            >
              <span className="font-mono text-xs px-2 py-0.5 rounded border font-semibold" style={{
                background: 'var(--surface)',
                borderColor: 'var(--border)',
                color: 'var(--text-secondary)'
              }}>
                {num}
              </span>
              <span className="flex-1">{opt}</span>
            </button>
          )
        })}
      </div>

      <div className="flex items-center justify-end gap-3 pt-2" style={{ borderTop: '1px solid var(--border)' }}>
        <button
          onClick={onDeny}
          className="px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer"
          style={{ color: 'var(--text-muted)' }}
        >
          Skip
        </button>
        <button
          onClick={handleSubmit}
          className="px-5 py-1.5 rounded-lg text-xs font-bold text-white shadow-md transition-all flex items-center gap-1.5 cursor-pointer"
          style={{ background: 'var(--accent)' }}
        >
          <span>Submit</span>
          <span className="text-[10px]">↵</span>
        </button>
      </div>
    </motion.div>
  )
}

/* ================================================================
   THINKING PROCESS ACCORDION
   ================================================================ */
interface ThinkingAccordionProps {
  durationSeconds?: number
  heading?: string
  thoughts?: string
}

function ThinkingAccordion({
  durationSeconds = 11,
  heading = "Prioritizing Tool Specificity",
  thoughts = "I'm focusing now on tool specificity..."
}: ThinkingAccordionProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="my-3 font-sans text-left">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-xs font-semibold hover:text-slate-200 transition-colors py-1 cursor-pointer"
        style={{ color: 'var(--text-muted)' }}
      >
        <span>Thinking for {durationSeconds}s</span>
        <motion.span
          animate={{ rotate: expanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-[10px] inline-block"
        >
          ∨
        </motion.span>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden mt-1.5 pl-3.5 border-l-2 space-y-1.5"
            style={{ borderColor: 'var(--border)' }}
          >
            {heading && (
              <div className="text-xs font-bold tracking-wide" style={{ color: 'var(--text-primary)' }}>
                {heading}
              </div>
            )}
            <div className="text-xs leading-relaxed font-normal" style={{ color: 'var(--text-secondary)' }}>
              {thoughts}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

/* ================================================================
   CODE BADGE & TEXT FORMATTER
   ================================================================ */
function CodeBlock({ lang, codeBody }: { lang: string, codeBody: string }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = () => {
    navigator.clipboard.writeText(codeBody)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <div className="my-3 rounded-xl overflow-hidden" style={{ border: '1px solid var(--border)', background: 'var(--bg-tertiary)' }}>
      <div className="flex items-center justify-between px-3.5 py-1.5 text-[11px] font-mono border-b" style={{ borderColor: 'var(--border)', color: 'var(--text-muted)' }}>
        <span>{lang.toUpperCase()}</span>
        <button onClick={handleCopy} className="hover:text-white transition-colors cursor-pointer">
          {copied ? '✓ Copié' : 'Copier'}
        </button>
      </div>
      <div style={{ height: '400px' }}>
        <Editor
          height="100%"
          language={lang.toLowerCase() === 'code' ? 'javascript' : lang.toLowerCase()}
          theme="vs-dark"
          value={codeBody}
          options={{ readOnly: true, minimap: { enabled: false }, scrollBeyondLastLine: false }}
        />
      </div>
    </div>
  )
}

function FormatText({ content }: { content: string }) {
  if (content.includes('<think>')) {
    const thinkParts = content.split(/(<think>[\s\S]*?<\/think>)/g)
    return (
      <div className="msg-assistant space-y-2">
        {thinkParts.map((part, ti) => {
          if (part.startsWith('<think>') && part.endsWith('</think>')) {
            const rawThoughts = part.slice(7, -8).trim()
            const lines = rawThoughts.split('\n')
            const heading = lines[0].length < 60 ? lines[0] : "Analyzing Request & Reasoning"
            const body = lines[0].length < 60 ? lines.slice(1).join('\n') : rawThoughts
            return (
              <ThinkingAccordion
                key={ti}
                durationSeconds={11}
                heading={heading}
                thoughts={body || rawThoughts}
              />
            )
          }
          return <FormatText key={ti} content={part} />
        })}
      </div>
    )
  }

  if (content.includes('```')) {
    const parts = content.split(/(```[\s\S]*?```)/g)
    return (
      <div className="msg-assistant space-y-3">
        {parts.map((part, i) => {
          if (part.startsWith('```') && part.endsWith('```')) {
            const lines = part.slice(3, -3).trim().split('\n')
            const firstLine = lines[0].trim()
            const lang = firstLine && !firstLine.includes(' ') ? firstLine : 'code'
            const codeBody = lang !== 'code' ? lines.slice(1).join('\n') : lines.join('\n')
            return <CodeBlock key={i} lang={lang} codeBody={codeBody} />
          }
          return <FormatText key={i} content={part} />
        })}
      </div>
    )
  }

  const lines = content.split('\n')
  return (
    <div className="msg-assistant space-y-2">
      {lines.map((line, li) => {
        if (!line.trim()) return <div key={li} className="h-1" />

        if (/^(tool call|executed|tool:|appel outil|exécution)/i.test(line.trim())) {
          return (
            <div key={li} className="my-2 p-3 rounded-xl text-xs font-mono flex items-center gap-2.5"
                 style={{ background: 'var(--bg-secondary)', border: '1px solid var(--accent-cyan)', color: 'var(--accent-cyan)' }}>
              <span className="text-sm">⚡</span>
              <span className="font-semibold">{line.trim()}</span>
            </div>
          )
        }

        if (/attention|pci-dss|points d'attention/i.test(line)) {
          return (
            <div key={li} className="flex items-start gap-2 pt-3 mt-2 text-xs font-mono"
              style={{ borderTop: '1px solid var(--border)', color: 'var(--text-muted)' }}>
              <span style={{ color: '#f59e0b' }}>⚠</span>
              <span>{line.replace(/^[⚠\s\-\*]*attention\s*[:\.]?/i, '')}</span>
            </div>
          )
        }
        const parts = line.split(/(`[^`]+`|\*\*[^*]+\*\*)/g)
        return (
          <p key={li} style={{ color: 'var(--text-primary)' }}>
            {parts.map((p, pi) => {
              if (p.startsWith('`') && p.endsWith('`'))
                return <span key={pi} className="code-badge">{p.slice(1, -1)}</span>
              if (p.startsWith('**') && p.endsWith('**'))
                return <strong key={pi} style={{ fontWeight: 700 }}>{p.slice(2, -2)}</strong>
              return <span key={pi}>{p}</span>
            })}
          </p>
        )
      })}
    </div>
  )
}

/* ================================================================
   MAIN AGENT PAGE
   ================================================================ */
export default function AgentPage() {
  const { isDark, toggleTheme } = useThemeContext()

  /* --- Navigation --- */
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [view, setView] = useState<'chat' | 'history' | 'tasks' | 'skills' | 'teamwork' | 'preview' | 'bots' | 'pricing'>('chat')

  /* --- Extended Features States --- */
  const [isListening, setIsListening] = useState(false)

  /* --- Voice Dictation Handler --- */
  const toggleVoiceDictation = () => {
    if (typeof window === 'undefined') return
    const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRec) {
      pushToast('error', "La reconnaissance vocale n'est pas supportée sur ce navigateur.")
      return
    }
    if (isListening) {
      setIsListening(false)
      pushToast('info', 'Dictée vocale arrêtée.')
      return
    }

    try {
      const recognition = new SpeechRec()
      recognition.lang = 'fr-FR'
      recognition.interimResults = true
      recognition.continuous = false

      recognition.onstart = () => {
        setIsListening(true)
        pushToast('info', '🎙️ Dictée vocale active... Écoute en cours.')
      }

      recognition.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((res: any) => res[0].transcript)
          .join('')
        setInput(transcript)
      }

      recognition.onerror = (err: any) => {
        setIsListening(false)
        pushToast('error', `Erreur dictée vocale: ${err.error}`)
      }

      recognition.onend = () => {
        setIsListening(false)
      }

      recognition.start()
    } catch (e: any) {
      setIsListening(false)
      pushToast('error', `Impossible de démarrer la voix: ${e.message}`)
    }
  }

  /* --- Search --- */
  const [historySearch, setHistorySearch] = useState('')
  const [taskSearch, setTaskSearch] = useState('')
  const [skillsSearch, setSkillsSearch] = useState('')

  /* --- Skills State --- */
  const [skills, setSkills] = useState<SkillInfo[]>([])
  const [selectedSkill, setSelectedSkill] = useState<SkillInfo | null>(null)
  const [skillsLoading, setSkillsLoading] = useState(false)

  /* --- Tool Execution Policy State --- */
  const [executionPolicy, setExecutionPolicy] = useState<ExecutionPolicy>('ALWAYS-PROCEED')
  const [showPolicyMenu, setShowPolicyMenu] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem('axiom_execution_policy') as ExecutionPolicy
    if (saved && POLICY_CONFIGS[saved]) {
      setExecutionPolicy(saved)
    }
  }, [])

  const changePolicy = (newPolicy: ExecutionPolicy) => {
    setExecutionPolicy(newPolicy)
    localStorage.setItem('axiom_execution_policy', newPolicy)
    setShowPolicyMenu(false)
    pushToast('info', `Politique d'exécution : ${newPolicy}`)
  }

  /* --- Toasts --- */
  const [toasts, setToasts] = useState<Toast[]>([])
  const pushToast = useCallback((type: Toast['type'], message: string) => {
    const id = Date.now().toString()
    setToasts(prev => [...prev, { id, type, message }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3500)
  }, [])
  const removeToast = (id: string) => setToasts(prev => prev.filter(t => t.id !== id))

  /* --- Data --- */
  const [health, setHealth] = useState<HealthStatus | null>(null)

  const [sessions, setSessions] = useState<ConversationSession[]>([])
  const [currentId, setCurrentId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [tasks, setTasks] = useState<ScheduledTask[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  /* --- New task form --- */
  const [creatingTask, setCreatingTask] = useState(false)
  const [newTaskName, setNewTaskName] = useState('')
  const [newTaskSched, setNewTaskSched] = useState('')

  const [attachedFile, setAttachedFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement | HTMLInputElement | any>(null)

  useEffect(() => { getHealth().then(setHealth).catch(() => {}) }, [])
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, loading])

  const [hydrated, setHydrated] = useState(false)

  useEffect(() => {
    const state = loadState()
    setSessions(state.sessions)
    setTasks(state.tasks)
    const active = state.sessions.find(s => s.id === state.activeSessionId)
    if (active) {
      setCurrentId(active.id)
      setMessages(active.messages)
    } else if (state.sessions.length > 0) {
      setCurrentId(state.sessions[0].id)
      setMessages(state.sessions[0].messages)
    }
    setHydrated(true)
  }, [])

  useEffect(() => {
    if (!hydrated) return
    const ok = saveState({ version: 1, sessions, tasks, activeSessionId: currentId })
    if (!ok) pushToast('error', 'Stockage local plein — conversation non enregistrée')
  }, [sessions, tasks, currentId, hydrated])

  useEffect(() => {
    if (view !== 'skills') return
    setSkillsLoading(true)
    getSkills(skillsSearch)
      .then(res => {
        setSkills(res.skills)
      })
      .catch(() => {
        pushToast('error', 'Erreur lors du chargement des skills')
      })
      .finally(() => {
        setSkillsLoading(false)
      })
  }, [view, skillsSearch, pushToast])

  const loadSkillDetails = async (s: SkillInfo) => {
    try {
      const details = await getSkillDetails(s.repo, s.skill, true)
      setSelectedSkill(details)
    } catch {
      pushToast('error', 'Erreur lors du chargement du fichier SKILL.md')
    }
  }

  const newConversation = () => {
    const id = 'new-' + Date.now()
    setSessions(p => [{ id, title: 'Nouvelle conversation', subtitle: 'Outside of Project', messages: [] }, ...p])
    setCurrentId(id)
    setMessages([])
    setView('chat')
    pushToast('info', 'Nouvelle conversation créée')
  }

  const selectSession = (s: ConversationSession) => {
    setCurrentId(s.id)
    setMessages(s.messages)
    setView('chat')
  }

  const deleteSession = (id: string) => {
    setSessions(p => p.filter(x => x.id !== id))
    if (id === currentId) newConversation()
    pushToast('success', 'Conversation supprimée')
  }

  const useSuggestion = (text: string) => {
    setInput(text)
    inputRef.current?.focus()
  }

  const handleAttachClick = () => fileInputRef.current?.click()

  const handleFileSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    const ext = (file.name.split('.').pop() || '').toLowerCase()
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      pushToast('error', 'Type de fichier non supporté')
      return
    }
    if (file.size === 0) {
      pushToast('error', 'Fichier vide')
      return
    }
    if (file.size > MAX_FILE_SIZE) {
      pushToast('error', 'Fichier trop volumineux (max 100 Ko)')
      return
    }
    setAttachedFile(file)
    pushToast('success', `Fichier joint : ${file.name}`)
  }

  const readFileContent = (file: File): Promise<string> =>
    new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = () => reject(new Error('read-failed'))
      reader.readAsText(file, 'utf-8')
    })

  const createTask = () => {
    if (!newTaskName.trim() || !newTaskSched.trim()) return
    const t: ScheduledTask = { id: 't-' + Date.now(), name: newTaskName, schedule: newTaskSched, status: 'active' }
    setTasks(p => [t, ...p])
    setNewTaskName(''); setNewTaskSched('')
    setCreatingTask(false)
    pushToast('success', `Tâche "${t.name}" créée`)
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return
    const text = input.trim()
    setInput('')

    const t0 = Date.now()
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
        pushToast('error', 'Impossible de lire le fichier')
        return
      }
    }
    const um: Message = { id: 'u-' + t0, role: 'user', content: text, file: fileName }
    const next = [...messages, um]
    setMessages(next)
    setLoading(true)

    try {
      const res = await chat(text)
      const elapsed = ((Date.now() - t0) / 1000).toFixed(1) + 's'
      const am: Message = {
        id: 'a-' + Date.now(),
        role: 'assistant',
        content: res.response,
        agent: res.task.agent || 'AGENT_QUICKSHOT',
        model: (res.task.model || '').split('/').pop(),
        score: res.task.score,
        duration: elapsed,
      }
      const final = [...next, am]
      setMessages(final)
      setSessions(p => p.map(s => s.id === currentId
        ? { ...s, title: s.title === 'Nouvelle conversation' ? text.slice(0, 38) + '…' : s.title, messages: final }
        : s))
      pushToast('success', `Réponse de ${am.agent?.replace('AGENT_', '') || 'APEX'} · ${elapsed}`)
    } catch {
      const em: Message = { id: 'e-' + Date.now(), role: 'assistant', content: 'Erreur de connexion au backend APEX.' }
      setMessages(p => [...p, em])
      pushToast('error', 'Impossible de contacter le serveur APEX')
    } finally {
      setLoading(false)
      setAttachedFile(null)
    }
  }

  const filteredSessions = sessions.filter(s =>
    s.title.toLowerCase().includes(historySearch.toLowerCase()))
  const filteredTasks = tasks.filter(t =>
    t.name.toLowerCase().includes(taskSearch.toLowerCase()))

  return (
    <div
      style={{ fontFamily: 'var(--font-sans)', background: 'var(--bg)', color: 'var(--text-primary)' }}
      className="ambient-bg flex h-[100dvh] overflow-hidden antialiased"
    >
      <ToastStack toasts={toasts} remove={removeToast} />

      {/* ── SIDEBAR ──────────────────────────────────────────── */}
      <AnimatePresence initial={false}>
        {sidebarOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSidebarOpen(false)}
              className="fixed inset-0 bg-black/50 z-40"
            />
            <motion.aside
              key="sidebar"
              initial={{ x: -272, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -272, opacity: 0 }}
              transition={{ duration: 0.22, ease: [0.4, 0, 0.2, 1] }}
              style={{ width: 272, background: 'var(--surface)', borderRight: '1.5px solid var(--border)' }}
              className="fixed inset-y-0 left-0 flex flex-col h-full overflow-hidden z-50"
            >
            <div className="flex items-center gap-2 p-4">
              <button onClick={() => setSidebarOpen(false)} className="input-action-btn">
                <SidebarSimple className="w-4.5 h-4.5" />
              </button>
              <div className="flex gap-0.5">
                <button onClick={() => setView('chat')} className="input-action-btn">
                  <CaretLeft className="w-4 h-4" />
                </button>
                <button className="input-action-btn">
                  <CaretRight className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="px-3 pt-2">
              <button
                onClick={newConversation}
                className="sidebar-item px-4 justify-center"
                style={{ background: 'var(--bg-tertiary)', fontWeight: 600, color: 'var(--text-primary)' }}
              >
                <Plus className="w-4 h-4 shrink-0" weight="bold" />
                Nouvelle conversation
              </button>
            </div>

            <div className="px-3 pt-4">
              <details className="group">
                <summary className="text-mono px-2 pb-2 cursor-pointer select-none list-none flex items-center justify-between [&::-webkit-details-marker]:hidden" style={{ color: 'var(--text-secondary)' }}>
                  <span>WORKSPACE</span>
                  <CaretRight className="w-3 h-3 transition-transform group-open:rotate-90" />
                </summary>
                <div className="space-y-0.5 pt-1">
                  {NAV_LINKS.map(({ href, label, icon: Icon }) => (
                    <Link key={href} href={href} className="sidebar-item">
                      <Icon className="w-4 h-4 shrink-0" />
                      {label}
                    </Link>
                  ))}
                </div>
              </details>
            </div>

            <div className="flex-1 overflow-y-auto px-3 pt-5 pb-2 space-y-0.5">
              <p className="text-mono px-2 pb-2" style={{ color: 'var(--text-secondary)' }}>
                RÉCENTES
              </p>
              {sessions.map(s => (
                <button
                  key={s.id}
                  onClick={() => selectSession(s)}
                  className={`sidebar-item w-full ${s.id === currentId && view === 'chat' ? 'active' : ''}`}
                >
                  <span className="line-clamp-1 text-left text-xs">{s.title}</span>
                </button>
              ))}
            </div>

            <div className="p-4 flex items-center justify-between" style={{ borderTop: '1px solid var(--border)' }}>
              <Link href="/" className="flex items-center gap-2">
                <div className="logo-mark">H</div>
                <span className="text-mono font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>HakimAgent</span>
              </Link>
              <ThemeToggle isDark={isDark} onToggle={toggleTheme} />
            </div>
          </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* ── MAIN ─────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 h-full">
        <header
          style={{ borderBottom: '1px solid var(--border)', background: 'var(--glass-bg)', backdropFilter: 'blur(16px) saturate(180%)' }}
          className="h-[60px] flex items-center justify-between px-5 shrink-0 sticky top-0 z-30 glass-panel"
        >
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 border-r border-[var(--border)] pr-3">
              {!sidebarOpen && (
                <button onClick={() => setSidebarOpen(true)} className="input-action-btn hover:scale-105 transition-transform" title="Toggle Sidebar">
                  <PanelLeft className="w-5 h-5 text-[var(--text-muted)] hover:text-[var(--text-primary)]" strokeWidth={1.5} />
                </button>
              )}
              <button className="input-action-btn hover:scale-105 transition-transform" title="Open Folder">
                <FolderPlus className="w-5 h-5 text-[var(--text-muted)] hover:text-[var(--text-primary)]" strokeWidth={1.5} />
              </button>
            </div>
            <Link href="/" className="flex items-center gap-2.5">
              <div className="logo-mark">H</div>
              <span className="font-extrabold text-sm tracking-wider uppercase text-[var(--text-primary)]">
                HAKIMAGENT IDE
              </span>
            </Link>
          </div>

          <div className="flex items-center gap-2.5 relative">

            <ThemeToggle isDark={isDark} onToggle={toggleTheme} />

            <div className="cmd-hint" title="Recherche rapide">
              <span className="kbd">Ctrl</span>
              <span className="kbd">K</span>
            </div>

            <button
              onClick={() => setView('pricing')}
              className="shimmer-btn px-4 py-1.5 rounded-full text-xs font-bold bg-[var(--text-primary)] text-[var(--bg)] border border-[var(--border)] shadow-none hover:opacity-90 transition-all cursor-pointer flex items-center gap-1.5 active:scale-95 shrink-0"
              title="Voir les offres et passer à la version Pro"
            >
              <span>Upgrade to Pro</span>
            </button>
          </div>
        </header>

        {/* ──────── VIEW: CHAT ──────── */}
        {view === 'chat' && (
          <div
            className="flex-1 flex flex-col min-h-0 relative transition-all duration-500"
            style={{}}
          >
            <div ref={scrollRef} className="flex-1 overflow-y-auto relative z-10 progressive-blur-top">
              <div className="max-w-2xl mx-auto px-4 py-10 space-y-8">
                {messages.length === 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col items-center justify-center h-[50vh] text-center dot-pattern rounded-3xl"
                  >
                    <h2 className="text-lg font-mono text-[var(--text-muted)] animate-blur-fade">
                      Bonjour. Comment puis-je vous aider ?
                    </h2>
                    <p className="text-xs text-[var(--text-muted)] mt-3 animate-blur-fade" style={{ animationDelay: '0.15s' }}>
                      <span className="kbd">Ctrl</span> + <span className="kbd">Enter</span> pour envoyer
                    </p>
                  </motion.div>
                )}

                <AnimatePresence initial={false}>
                  {messages.map((msg) => {
                    const ag = getAgent(msg.agent)

                    if (msg.role === 'user') return (
                      <motion.div
                        key={msg.id}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ type: 'spring', stiffness: 260, damping: 26 }}
                        className="flex justify-end"
                      >
                        <div className="flex flex-col items-end gap-1.5 max-w-[85%]">
                          <div className="msg-user text-left whitespace-pre-wrap [overflow-wrap:anywhere] [word-break:normal] inline-block">{msg.content}</div>
                          {msg.file && (
                            <div
                              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono"
                              style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}
                            >
                              <span>📎</span>
                              <span className="truncate max-w-[240px]">{msg.file}</span>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )

                    return (
                      <motion.div
                        key={msg.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ type: 'spring', stiffness: 260, damping: 28 }}
                        className="space-y-2"
                      >
                        <div className="flex items-center justify-between text-mono">
                          <div className="flex items-center gap-1.5">
                            <div className={`w-2 h-2 rounded-full ${ag.dotClass}`} />
                            <span style={{ color: ag.color, fontWeight: 700 }}>{ag.name}</span>
                            {msg.model && <>
                              <span style={{ color: 'var(--border)' }}>·</span>
                              <span style={{ color: 'var(--text-muted)' }}>{msg.model}</span>
                            </>}
                            {msg.score != null && <>
                              <span style={{ color: 'var(--border)' }}>·</span>
                              <span style={{ color: 'var(--text-muted)' }}>score {msg.score}</span>
                            </>}
                          </div>
                          {msg.duration && <span style={{ color: 'var(--text-muted)' }}>{msg.duration}</span>}
                        </div>

                        <div className="pl-4" style={{ borderLeft: '2px solid var(--border)' }}>
                          <FormatText content={msg.content} />
                        </div>
                      </motion.div>
                    )
                  })}
                </AnimatePresence>

                {(executionPolicy === 'REQUEST-REVIEW' || executionPolicy === 'STRICT') && (
                  <PermissionDialog
                    title="Allow read access to this path?"
                    path="C:\Users\hp\Desktop\ntrsitecursur\server.cjs"
                    onAllow={(opt) => pushToast('success', `Autorisation accordée (Option ${opt})`)}
                    onDeny={() => pushToast('info', 'Autorisation refusée')}
                  />
                )}

                {loading && (
                  <motion.div
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    <TypingIndicator />
                  </motion.div>
                )}
              </div>
            </div>

            {attachedFile && (
              <div className="max-w-2xl mx-auto w-full px-4 pt-2">
                <div
                  className="flex items-center gap-2.5 px-3 py-2 rounded-xl"
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
                    aria-label="Retirer le fichier"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}

            <div className="px-4 pb-6 pt-2 max-w-3xl mx-auto w-full z-20 relative group">
              {input.startsWith('/') && !input.includes(' ') && (
                <div className="absolute bottom-full mb-2 left-4 right-4 bg-[var(--surface)] border border-[var(--border)] rounded-xl shadow-2xl p-2 z-30 max-h-56 overflow-y-auto space-y-1 animate-fade-in">
                  {[
                    { cmd: '/goal', desc: 'Activer le mode objectif long terme autonome', icon: '🎯' },
                    { cmd: '/schedule', desc: 'Planifier une tâche répétitive ou différée', icon: '⏰' },
                    { cmd: '/browser', desc: 'Lancer une session de recherche & navigation web', icon: '🌐' },
                    { cmd: '/learn', desc: 'Enregistrer une consigne permanente dans la mémoire', icon: '🧠' },
                    { cmd: '/teamwork', desc: 'Activer le mode orchestration multi-agents', icon: '👥' },
                    { cmd: '/skills', desc: 'Inspecter les 92 compétences du catalogue', icon: '✨' },
                    { cmd: '/compact', desc: 'Compacter l\'historique de conversation', icon: '📦' },
                    { cmd: '/undo', desc: 'Annuler la dernière modification de fichier (Rollback)', icon: '↩️' },
                    { cmd: '/clear', desc: 'Effacer la conversation active', icon: '🧹' },
                    { cmd: '/help', desc: 'Afficher la liste des commandes', icon: '❓' },
                  ]
                  .filter(c => c.cmd.toLowerCase().startsWith(input.toLowerCase()))
                  .map((item) => (
                    <button
                      key={item.cmd}
                      type="button"
                      onClick={() => {
                        setInput(item.cmd + ' ');
                        if (inputRef.current) inputRef.current.focus();
                      }}
                      className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-[var(--bg-tertiary)] text-xs text-left cursor-pointer transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <span>{item.icon}</span>
                        <span className="font-mono font-bold text-[var(--text-primary)]">{item.cmd}</span>
                      </div>
                      <span className="text-[var(--text-muted)] truncate max-w-[320px]">{item.desc}</span>
                    </button>
                  ))}
                </div>
              )}
              <div className="relative bg-[var(--surface-raised)] rounded-2xl border border-[var(--border)] shadow-2xl p-2.5 space-y-2 focus-ring">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => {
                    setInput(e.target.value)
                    e.target.style.height = 'auto'
                    e.target.style.height = e.target.scrollHeight + 'px'
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Entrez votre requête... (Ctrl + Entrée pour envoyer)"
                  rows={1}
                  className="w-full px-3 py-2 resize-none bg-transparent text-[var(--text-primary)] text-sm focus:outline-none placeholder:text-[var(--text-muted)] min-h-[48px]"
                  style={{ maxHeight: '60vh' }}
                />

                <div className="flex items-center justify-between px-2 pt-1 border-t border-[var(--border)]">
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={handleAttachClick}
                      disabled={loading}
                      className="p-2 rounded-xl text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors cursor-pointer"
                      title="Joindre un fichier"
                    >
                      <Paperclip className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={toggleVoiceDictation}
                      className={`p-2 rounded-xl transition-all cursor-pointer ${isListening ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'}`}
                      title={isListening ? 'Arrêter la dictée' : 'Dictée vocale'}
                    >
                      <span className="text-sm">{isListening ? '🔴' : '🎙️'}</span>
                    </button>
                  </div>

                    <div className="flex items-center gap-2">
                      <div className="hidden sm:flex items-center gap-1 mr-1">
                        <span className="kbd">Ctrl</span>
                        <span className="text-[10px] text-[var(--text-muted)]">+</span>
                        <span className="kbd">↵</span>
                      </div>
                      <button
                        type="button"
                        onClick={handleSend}
                        disabled={loading || !input.trim()}
                        className={`flex items-center justify-center p-2.5 rounded-xl transition-all ${input.trim() && !loading
                          ? 'bg-[var(--text-primary)] text-[var(--bg)] font-semibold cursor-pointer shimmer-btn pulsate'
                          : 'bg-[var(--bg-tertiary)] text-[var(--text-muted)] cursor-not-allowed'
                        }`}
                        title="Envoyer"
                      >
                        <ArrowUpIcon className="w-4 h-4 relative z-10" />
                      </button>
                    </div>
                </div>
              </div>

              <div className="flex items-center justify-center flex-wrap gap-2 mt-4 opacity-0 focus-within:opacity-100 group-hover:opacity-100 transition-opacity duration-300">
                <button
                  type="button"
                  onClick={() => setInput((p) => (p ? p + ' Generate React Code' : 'Generate React Code'))}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-raised)] text-xs transition-colors cursor-pointer"
                >
                  <Code2 className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                  <span>Generate Code</span>
                </button>
                <button
                  type="button"
                  onClick={() => setInput((p) => (p ? p + ' Launch App Deployment' : 'Launch App Deployment'))}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-raised)] text-xs transition-colors cursor-pointer"
                >
                  <Rocket className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                  <span>Launch App</span>
                </button>
                <button
                  type="button"
                  onClick={() => setInput((p) => (p ? p + ' Build UI Components' : 'Build UI Components'))}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-raised)] text-xs transition-colors cursor-pointer"
                >
                  <Layers className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                  <span>UI Components</span>
                </button>
                <button
                  type="button"
                  onClick={() => setInput((p) => (p ? p + ' Explore Theme Ideas' : 'Explore Theme Ideas'))}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-raised)] text-xs transition-colors cursor-pointer"
                >
                  <Palette className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                  <span>Theme Ideas</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleAttachClick()}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-raised)] text-xs transition-colors cursor-pointer"
                >
                  <FileUp className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                  <span>Upload Docs</span>
                </button>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPTED_EXTENSIONS.map((e) => '.' + e).join(',')}
                onChange={handleFileSelected}
                className="hidden"
                tabIndex={-1}
                aria-hidden="true"
              />
            </div>
          </div>
        )}

        {/* ──────── VIEW: HISTORY ──────── */}
        {view === 'history' && (
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-2xl mx-auto px-5 py-10 space-y-7 animate-fade-up">
              <h1 className="text-display">Historique des conversations</h1>
              <div className="flex gap-3">
                <div className="flex-1 ai-input-wrap flex items-center gap-2.5 px-4 py-2.5">
                  <MagnifyingGlass className="w-4 h-4 shrink-0" style={{ color: 'var(--text-muted)' }} />
                  <input
                    value={historySearch}
                    onChange={e => setHistorySearch(e.target.value)}
                    placeholder="Rechercher une conversation..."
                    className="flex-1 text-sm"
                  />
                </div>
                <button
                  className="theme-pill"
                  style={{ borderRadius: 14, padding: '0 16px', fontSize: 13 }}
                >
                  <SlidersHorizontal className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
                  Filtrer
                </button>
              </div>

              <p className="text-mono" style={{ color: 'var(--text-muted)' }}>TOUTES LES CONVERSATIONS</p>

              <div className="space-y-3">
                {filteredSessions.map(s => (
                  <motion.div
                    key={s.id}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    onClick={() => selectSession(s)}
                    className="conv-item"
                  >
                    <div>
                      <p className="font-semibold text-sm">{s.title}</p>
                      <p className="text-mono mt-0.5" style={{ color: 'var(--text-muted)' }}>{s.subtitle}</p>
                    </div>
                    <div className="flex items-center gap-1.5">
                      {s.id === currentId && (
                        <div className="w-2.5 h-2.5 rounded-full bg-cyan-400" style={{ boxShadow: '0 0 8px rgba(6,182,212,.8)' }} />
                      )}
                      <button
                        className="input-action-btn"
                        onClick={e => e.stopPropagation()}
                        title="Supprimer la conversation"
                        aria-label="Supprimer la conversation"
                      >
                        <Trash className="w-4 h-4" />
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ──────── VIEW: TASKS ──────── */}
        {view === 'tasks' && (
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-2xl mx-auto px-5 py-10 space-y-7 animate-fade-up">
              <div className="flex items-center justify-between">
                <h1 className="text-display">Tâches planifiées</h1>
                <button
                  onClick={() => setCreatingTask(true)}
                  className="theme-pill"
                  style={{ borderRadius: 12, padding: '7px 14px', fontSize: 13, fontFamily: 'var(--font-sans)' }}
                >
                  <Plus className="w-4 h-4" weight="bold" />
                  Nouvelle
                </button>
              </div>

              <div className="ai-input-wrap flex items-center gap-2.5 px-4 py-2.5">
                <MagnifyingGlass className="w-4 h-4 shrink-0" style={{ color: 'var(--text-muted)' }} />
                <input
                  value={taskSearch}
                  onChange={e => setTaskSearch(e.target.value)}
                  placeholder="Rechercher une tâche..."
                  className="flex-1 text-sm"
                />
              </div>

              <AnimatePresence>
                {creatingTask && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    style={{ border: '1.5px solid var(--accent)', borderRadius: 16, overflow: 'hidden', background: 'var(--surface)' }}
                    className="p-5 space-y-4"
                  >
                    <p className="text-mono font-bold" style={{ color: 'var(--accent)' }}>NOUVELLE TÂCHE</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {[
                        { val: newTaskName, set: setNewTaskName, ph: 'Nom de la tâche...' },
                        { val: newTaskSched, set: setNewTaskSched, ph: 'Fréquence (ex: Toutes les 1h)' },
                      ].map((f, i) => (
                        <div key={i} className="ai-input-wrap px-3 py-2">
                          <input value={f.val} onChange={e => f.set(e.target.value)} placeholder={f.ph} className="w-full text-sm" />
                        </div>
                      ))}
                    </div>
                    <div className="flex justify-end gap-2">
                      <button onClick={() => setCreatingTask(false)} className="input-action-btn px-3 text-xs" style={{ width: 'auto' }}>Annuler</button>
                      <button
                        onClick={createTask}
                        className="send-btn send-btn-active px-4"
                        style={{ width: 'auto', borderRadius: 10, fontSize: 12, fontFamily: 'var(--font-mono)' }}
                      >
                        Créer
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {filteredTasks.length === 0 ? (
                <div className="text-center py-20 space-y-3">
                  <p className="text-mono text-2xl">⏱</p>
                  <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    Aucune tâche planifiée pour le moment.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredTasks.map(t => (
                    <div key={t.id} className="conv-item">
                      <div>
                        <p className="font-semibold text-sm">{t.name}</p>
                        <p className="text-mono mt-0.5" style={{ color: 'var(--text-muted)' }}>{t.schedule}</p>
                      </div>
                      <span className="text-mono px-2 py-0.5 rounded-full text-[11px] bg-emerald-500/10 text-emerald-600" style={{ border: '1px solid rgba(16,185,129,.2)' }}>
                        {t.status.toUpperCase()}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ──────── VIEW: SKILLS ──────── */}
        {view === 'skills' && (
          <div className="flex-1 flex flex-col min-h-0 relative">
            <div className="flex-1 overflow-y-auto px-5 py-10">
              <div className="max-w-3xl mx-auto space-y-7 animate-fade-up">
                <div className="flex items-center justify-between">
                  <div>
                    <h1 className="text-display">Skills de l'Agent</h1>
                    <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                      Catalogue des compétences et super-pouvoirs intégrés à l'écosystème AXIOM
                    </p>
                  </div>
                  <span className="text-mono px-3 py-1 rounded-full text-xs" style={{ background: 'var(--bg-tertiary)', border: '1.5px solid var(--border)', color: 'var(--text-secondary)' }}>
                    {skills.length} skills
                  </span>
                </div>

                <div className="ai-input-wrap flex items-center gap-2.5 px-4 py-2.5">
                  <MagnifyingGlass className="w-4 h-4 shrink-0" style={{ color: 'var(--text-muted)' }} />
                  <input
                    value={skillsSearch}
                    onChange={e => setSkillsSearch(e.target.value)}
                    placeholder="Rechercher des skills (ex: browser, docker, validation, terminal...)"
                    className="flex-1 text-sm"
                  />
                  {skillsSearch && (
                    <button onClick={() => setSkillsSearch('')} className="input-action-btn">
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>

                {skillsLoading ? (
                  <div className="space-y-4">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="shimmer h-24 w-full rounded-xl" />
                    ))}
                  </div>
                ) : skills.length === 0 ? (
                  <div className="text-center py-20 space-y-3">
                    <p className="text-mono text-2xl">🔍</p>
                    <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                      Aucun skill correspondant dans le catalogue.
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-3.5">
                    {skills.map((s, idx) => (
                      <motion.div
                        key={`${s.repo}-${s.skill}-${idx}`}
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: Math.min(idx * 0.02, 0.2) }}
                        onClick={() => loadSkillDetails(s)}
                        className="conv-item text-left flex flex-col items-start gap-2.5 p-5 cursor-pointer group"
                      >
                        <div className="w-full flex items-start justify-between gap-4">
                          <div>
                            <span className="text-mono text-[10px] uppercase px-2 py-0.5 rounded" style={{ background: 'var(--accent-soft)', color: 'var(--accent)', border: '1px solid var(--border)' }}>
                              {s.repo}
                            </span>
                            <h3 className="font-bold text-base mt-1.5 group-hover:text-[var(--accent)] transition-colors">
                              {s.skill.replace(/-/g, ' ')}
                            </h3>
                          </div>
                          <span className="text-xs font-mono opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: 'var(--accent)' }}>
                            Inspecter SKILL.md ➜
                          </span>
                        </div>
                        <p className="text-sm line-clamp-2" style={{ color: 'var(--text-secondary)' }}>
                          {s.description}
                        </p>
                        <div className="text-[11px] font-mono" style={{ color: 'var(--text-muted)' }}>
                          Chemin: {s.path}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <AnimatePresence>
              {selectedSkill && (
                <>
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 0.4 }}
                    exit={{ opacity: 0 }}
                    onClick={() => setSelectedSkill(null)}
                    className="absolute inset-0 bg-black z-40 cursor-pointer"
                  />
                  <motion.div
                    initial={{ translateX: '100%' }}
                    animate={{ translateX: 0 }}
                    exit={{ translateX: '100%' }}
                    transition={{ type: 'spring', damping: 25, stiffness: 220 }}
                    style={{ background: 'var(--surface)', borderLeft: '1.5px solid var(--border)' }}
                    className="absolute right-0 top-0 bottom-0 w-full sm:w-[500px] z-50 flex flex-col shadow-2xl overflow-hidden"
                  >
                    <div className="p-5 flex items-center justify-between border-b" style={{ borderColor: 'var(--border)' }}>
                      <div className="min-w-0">
                        <span className="text-mono text-[9px] uppercase px-2 py-0.5 rounded" style={{ background: 'var(--accent-soft)', color: 'var(--accent)', border: '1px solid var(--border)' }}>
                          {selectedSkill.repo}
                        </span>
                        <h2 className="font-bold text-lg mt-1 truncate">
                          {selectedSkill.skill}
                        </h2>
                      </div>
                      <button onClick={() => setSelectedSkill(null)} className="input-action-btn">
                        <X className="w-5 h-5" />
                      </button>
                    </div>

                    <div className="flex-1 overflow-y-auto p-6 space-y-6">
                      <div className="space-y-2">
                        <h3 className="text-xs font-mono uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Description</h3>
                        <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                          {selectedSkill.description}
                        </p>
                      </div>

                      <div className="grid grid-cols-2 gap-4 py-3 px-4 rounded-xl text-xs font-mono" style={{ background: 'var(--bg-secondary)', border: '1.5px solid var(--border)' }}>
                        <div>
                          <div style={{ color: 'var(--text-muted)' }}>Source</div>
                          <a href={selectedSkill.source_url} target="_blank" rel="noreferrer" className="text-blue-500 hover:underline truncate block mt-0.5">
                            GitHub Repository
                          </a>
                        </div>
                        <div>
                          <div style={{ color: 'var(--text-muted)' }}>Chemin local</div>
                          <div className="truncate mt-0.5" style={{ color: 'var(--text-secondary)' }}>{selectedSkill.path}</div>
                        </div>
                      </div>

                      {selectedSkill.content ? (
                        <div className="space-y-3.5 border-t pt-5" style={{ borderColor: 'var(--border)' }}>
                          <h3 className="text-xs font-mono uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Fichier SKILL.md</h3>
                          <div className="text-xs font-mono p-4 rounded-xl overflow-x-auto whitespace-pre-wrap leading-relaxed" 
                               style={{ background: 'var(--bg-tertiary)', border: '1.5px solid var(--border)', color: 'var(--text-primary)' }}>
                            {selectedSkill.content}
                          </div>
                        </div>
                      ) : (
                        <div className="text-center py-8 text-xs font-mono" style={{ color: 'var(--text-muted)' }}>
                          Pas de fichier SKILL.md associé trouvé.
                        </div>
                      )}
                    </div>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* ──────── VIEW: TEAMWORK MODE ──────── */}
        {view === 'teamwork' && (
          <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-8">
            <div className="max-w-4xl mx-auto space-y-6">
              <div>
                <div className="page-eyebrow">Orchestration Multi-Agents</div>
                <h1 className="page-title">Mode Équipe (/teamwork-preview)</h1>
                <p className="page-subtitle">
                  Lancement simultané de sous-agents spécialisés travaillant en parallèle sur des tâches complexes.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="teamwork-card space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-[var(--accent)]">🏗️ AGENT_ARCHITECT</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400">100% Terminée</span>
                  </div>
                  <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>Conception des schémas de données et de l'architecture microservices.</p>
                  <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-tertiary)' }}>
                    <div className="bg-emerald-400 h-full w-full" />
                  </div>
                </div>

                <div className="teamwork-card space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-cyan-400">💻 AGENT_CODER</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400">85% En cours</span>
                  </div>
                  <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>Génération des outils Google Services et composants React.</p>
                  <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-tertiary)' }}>
                    <div className="bg-cyan-400 h-full w-[85%]" />
                  </div>
                </div>

                <div className="teamwork-card space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-purple-400">🔍 AGENT_DEBUGGER</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-purple-500/10 text-purple-400">90% Validation</span>
                  </div>
                  <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>Vérification des erreurs d'encodage et validation des endpoints HTTP.</p>
                  <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-tertiary)' }}>
                    <div className="bg-purple-400 h-full w-[90%]" />
                  </div>
                </div>

                <div className="teamwork-card space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-amber-400">🎨 AGENT_REVIEWER</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400">100% Validé</span>
                  </div>
                  <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>Revue d'interface selon les critères d'élite UI/UX Pro Max.</p>
                  <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-tertiary)' }}>
                    <div className="bg-emerald-400 h-full w-full" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ──────── VIEW: LIVE UI PREVIEW (CANVAS) ──────── */}
        {view === 'preview' && (
          <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-6">
            <div className="max-w-4xl mx-auto space-y-6">
              <div>
                <div className="page-eyebrow">Rendu RAG & Artifacts</div>
                <h1 className="page-title">Live UI Preview (Canvas)</h1>
                <p className="page-subtitle">
                  Visualisez en direct les composants HTML/React générés par l'agent dans un bac à sable interactif.
                </p>
              </div>

              <div className="preview-pane p-6 space-y-4">
                <div className="flex items-center justify-between border-b pb-3" style={{ borderColor: 'var(--border)' }}>
                  <span className="font-mono text-xs font-bold" style={{ color: 'var(--text-primary)' }}>⚡ Live Sandbox Component</span>
                  <span className="text-xs font-mono text-emerald-600 bg-emerald-100 px-2 py-0.5 rounded" style={{ color: 'var(--accent)' }}>Rendu 60fps</span>
                </div>

                <div className="p-6 rounded-xl space-y-4 shadow-xl" style={{ background: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}>
                  <div className="flex items-center justify-between">
                    <h3 className="font-extrabold text-lg text-emerald-400">Antigravity Widget</h3>
                    <span className="text-xs font-mono bg-cyan-500/20 text-cyan-300 px-2.5 py-1 rounded-full">Actif</span>
                  </div>
                  <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>Ce composant a été généré dynamiquement et rendu en temps réel dans la toile Canvas.</p>
                  <button className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-xs transition-all">
                    Déclencher l'Action Agent
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ──────── VIEW: BOTS INTEGRATIONS ──────── */}
        {view === 'bots' && (
          <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-6">
            <div className="max-w-4xl mx-auto space-y-6">
              <div>
                <div className="page-eyebrow">Contrôle à Distance</div>
                <h1 className="page-title">Bots Telegram & Discord</h1>
                <p className="page-subtitle">
                  Recevez des notifications et pilotez votre agent AXIOM à distance depuis votre téléphone mobile.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="agent-card space-y-4">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">📱</span>
                    <h3 className="font-bold text-base">Bot Telegram</h3>
                  </div>
                  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    Configurez votre token Telegram pour recevoir les alertes de fin de tâche et envoyer des commandes à distance.
                  </p>
                  <input
                    type="password"
                    placeholder="TELEGRAM_BOT_TOKEN"
                    className="w-full text-xs p-2.5 rounded-lg border bg-tertiary"
                    style={{ background: 'var(--bg-tertiary)', borderColor: 'var(--border)' }}
                  />
                  <button
                    onClick={() => pushToast('info', '📱 Notification de test envoyée vers Telegram !')}
                    className="w-full py-2 rounded-lg text-xs font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:bg-cyan-500/30"
                  >
                    Tester la connexion Telegram
                  </button>
                </div>

                <div className="agent-card space-y-4">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">💬</span>
                    <h3 className="font-bold text-base">Webhook Discord</h3>
                  </div>
                  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    Recevez les rapports d'exécution et les synthèses sous forme d'Embeds dans vos canaux Discord.
                  </p>
                  <input
                    type="password"
                    placeholder="DISCORD_WEBHOOK_URL"
                    className="w-full text-xs p-2.5 rounded-lg border bg-tertiary"
                    style={{ background: 'var(--bg-tertiary)', borderColor: 'var(--border)' }}
                  />
                  <button
                    onClick={() => pushToast('info', '💬 Notification de test envoyée vers Discord !')}
                    className="w-full py-2 rounded-lg text-xs font-bold bg-purple-500/20 text-purple-400 border border-purple-500/30 hover:bg-purple-500/30"
                  >
                    Tester la connexion Discord
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ──────── VIEW: PRICING (Cartes de Tarifs) ──────── */}
        {view === 'pricing' && (
          <div className="flex-1 overflow-y-auto">
            <SquishyPricing onSelectPlan={(planName) => {
              pushToast('success', `Souscription au plan ${planName} activée avec succès ! 🎉`)
              setView('chat')
            }} />
          </div>
        )}

      </div>
    </div>
  )
}
