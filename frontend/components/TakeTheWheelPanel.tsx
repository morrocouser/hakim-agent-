'use client'

import { useState } from 'react'
import {
  Globe,
  Terminal,
  ShieldAlert,
  Play,
  RotateCcw,
  Hand,
  CheckCircle,
  Folder,
  Send,
  Loader2,
  Lock,
  ExternalLink,
} from 'lucide-react'
import {
  CoworkerProfile,
  takeTheWheel,
  releaseTheWheel,
  requestHelp,
  executeOnComputer,
} from '@/lib/api'

interface TakeTheWheelPanelProps {
  coworker: CoworkerProfile
  onCoworkerUpdated: (updated: CoworkerProfile) => void
}

export default function TakeTheWheelPanel({
  coworker,
  onCoworkerUpdated,
}: TakeTheWheelPanelProps) {
  const [activeTab, setActiveTab] = useState<'screen' | 'terminal' | 'workspace'>('screen')
  const [urlInput, setUrlInput] = useState(coworker.screen.current_url)
  const [commandInput, setCommandInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [feedback, setFeedback] = useState<string | null>(null)

  const isHumanControlled = coworker.control_state === 'HUMAN_CONTROLLED'
  const isHelpRequested = coworker.control_state === 'HELP_REQUESTED'

  const handleTakeWheel = async () => {
    setLoading(true);
    setFeedback(null)
    try {
      const res = await takeTheWheel(coworker.id, 'Opérateur Hakim')
      onCoworkerUpdated(res.coworker)
      setFeedback("Vous avez pris le contrôle de l'ordinateur de l'agent. Vous pouvez maintenant naviguer ou taper des commandes.")
    } catch (err: any) {
      setFeedback(`Erreur : ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleReleaseWheel = async () => {
    setLoading(true)
    setFeedback(null)
    try {
      const res = await releaseTheWheel(coworker.id, 'Opérateur Hakim')
      onCoworkerUpdated(res.coworker)
      setFeedback("Contrôle rendu au coworker. L'exécution autonome reprend.")
    } catch (err: any) {
      setFeedback(`Erreur : ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleSimulateHelp = async () => {
    setLoading(true)
    try {
      const res = await requestHelp(
        coworker.id,
        "Détection d'un challenge 2FA / CAPTCHA sur la session active."
      )
      onCoworkerUpdated(res.coworker)
      setFeedback("L'agent a déclenché une alerte 'computer.help_requested'.")
    } catch (err: any) {
      setFeedback(`Erreur : ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleNavigate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!urlInput.trim()) return

    setLoading(true)
    setFeedback(null)
    try {
      const res = await executeOnComputer(coworker.id, {
        tool_name: 'browser_navigate',
        intent: `Navigation web vers ${urlInput}`,
        url: urlInput.trim(),
        initiator_kind: isHumanControlled ? 'person' : 'routine',
      })
      if (res.coworker) {
        onCoworkerUpdated(res.coworker)
      }
      if (res.require_takeover) {
        setFeedback("⚠️ Politique de sécurité : cette URL requiert une intervention 'Take the Wheel'.")
      } else if (!res.success) {
        setFeedback(`🚫 Bloqué par la passerelle de gouvernance : ${res.reason}`)
      } else {
        setFeedback("Navigation exécutée avec succès.")
      }
    } catch (err: any) {
      setFeedback(`Erreur : ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleRunCommand = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!commandInput.trim()) return

    const cmd = commandInput.trim()
    setCommandInput('')
    setLoading(true)
    setFeedback(null)
    try {
      const res = await executeOnComputer(coworker.id, {
        tool_name: 'shell_exec',
        intent: `Exécution shell opérateur : ${cmd}`,
        command: cmd,
        initiator_kind: isHumanControlled ? 'person' : 'routine',
      })
      if (res.coworker) {
        onCoworkerUpdated(res.coworker)
      }
      if (!res.success) {
        setFeedback(`🚫 Bloqué par la passerelle de gouvernance : ${res.reason}`)
      } else {
        setFeedback("Commande exécutée dans le conteneur du coworker.")
      }
    } catch (err: any) {
      setFeedback(`Erreur : ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className={`rounded-2xl border transition-all duration-300 overflow-hidden ${
        isHumanControlled
          ? 'ring-2 ring-[var(--accent)] border-[var(--accent)]'
          : isHelpRequested
          ? 'ring-2 ring-amber-500/80 border-amber-500/60'
          : 'border-[var(--border)]'
      }`}
      style={{ background: 'var(--surface)' }}
    >
      {/* Top Banner / Control State Indicator */}
      <div
        className="px-5 py-3 border-b flex flex-wrap items-center justify-between gap-3"
        style={{
          background: isHumanControlled
            ? 'var(--accent-soft)'
            : isHelpRequested
            ? 'rgba(245, 158, 11, 0.12)'
            : 'var(--bg-secondary)',
          borderColor: 'var(--border)',
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-3.5 h-3.5 rounded-full animate-pulse"
            style={{
              backgroundColor: isHumanControlled
                ? 'var(--accent)'
                : isHelpRequested
                ? '#f59e0b'
                : '#10b981',
            }}
          />
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
              État de l'ordinateur dédié
            </div>
            <div className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
              {isHumanControlled && <span>🎮 Contrôle humain actif (Take the Wheel)</span>}
              {isHelpRequested && <span className="text-amber-400">⚠️ Intervention requise (2FA / CAPTCHA)</span>}
              {!isHumanControlled && !isHelpRequested && <span>🤖 Coworker autonome en écoute</span>}
            </div>
          </div>
        </div>

        {/* Handover Action Buttons */}
        <div className="flex items-center gap-2">
          {isHumanControlled ? (
            <button
              onClick={handleReleaseWheel}
              disabled={loading}
              className="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-[var(--surface-raised)] border border-[var(--border)] hover:border-[var(--accent)] text-[var(--accent)] flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              {loading ? <Loader2 size={14} className="animate-spin" /> : <RotateCcw size={14} />}
              Rendre le contrôle au bot
            </button>
          ) : (
            <button
              onClick={handleTakeWheel}
              disabled={loading}
              className="btn-primary px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 cursor-pointer shadow-md"
            >
              {loading ? <Loader2 size={14} className="animate-spin" /> : <Hand size={14} />}
              Prendre le volant (Take the Wheel)
            </button>
          )}

          {!isHelpRequested && !isHumanControlled && (
            <button
              onClick={handleSimulateHelp}
              disabled={loading}
              className="px-2.5 py-1.5 rounded-xl text-xs font-medium text-[var(--text-muted)] hover:text-amber-400 border border-transparent hover:border-amber-500/30 transition-colors cursor-pointer"
              title="Simule un défi 2FA/CAPTCHA pour tester le flux Take the Wheel"
            >
              Simuler 2FA
            </button>
          )}
        </div>
      </div>

      {/* Help Requested Alert Banner */}
      {isHelpRequested && (
        <div className="px-5 py-3 bg-amber-500/10 border-b border-amber-500/20 text-xs text-amber-300 flex items-center gap-2.5">
          <ShieldAlert size={16} className="text-amber-400 shrink-0" />
          <div className="flex-1">
            <strong>Aide requise :</strong> {coworker.help_reason || "L'agent sollicite une intervention humaine pour franchir un point de sécurité."}
          </div>
          <button
            onClick={handleTakeWheel}
            className="px-2.5 py-1 rounded-lg bg-amber-500 text-black font-semibold text-xs hover:bg-amber-400 transition-colors cursor-pointer"
          >
            Intervenir maintenant
          </button>
        </div>
      )}

      {/* Feedback banner */}
      {feedback && (
        <div className="px-5 py-2.5 bg-[var(--bg-tertiary)] border-b border-[var(--border)] text-xs text-[var(--text-secondary)] flex items-center justify-between">
          <span>{feedback}</span>
          <button
            onClick={() => setFeedback(null)}
            className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"
          >
            ×
          </button>
        </div>
      )}

      {/* Tab Switcher: Screen / Terminal / Workspace */}
      <div className="flex border-b border-[var(--border)] px-4 bg-[var(--bg-secondary)]">
        <button
          onClick={() => setActiveTab('screen')}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 flex items-center gap-2 transition-all cursor-pointer ${
            activeTab === 'screen'
              ? 'border-[var(--accent)] text-[var(--accent)]'
              : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]'
          }`}
        >
          <Globe size={14} />
          Écran / Navigateur dédié
        </button>
        <button
          onClick={() => setActiveTab('terminal')}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 flex items-center gap-2 transition-all cursor-pointer ${
            activeTab === 'terminal'
              ? 'border-[var(--accent)] text-[var(--accent)]'
              : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]'
          }`}
        >
          <Terminal size={14} />
          Console Virtuelle
        </button>
        <button
          onClick={() => setActiveTab('workspace')}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 flex items-center gap-2 transition-all cursor-pointer ${
            activeTab === 'workspace'
              ? 'border-[var(--accent)] text-[var(--accent)]'
              : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]'
          }`}
        >
          <Folder size={14} />
          Espace Isolé (/workspace)
        </button>
      </div>

      {/* Content Area */}
      <div className="p-5">
        {/* TAB 1: SCREEN (VIRTUAL BROWSER) */}
        {activeTab === 'screen' && (
          <div className="space-y-3">
            {/* Browser Address Bar */}
            <form onSubmit={handleNavigate} className="flex items-center gap-2">
              <div className="relative flex-1">
                <Globe size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
                <input
                  type="text"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="https://exemple.com"
                  className="input-axiom w-full pl-9 pr-3 py-1.5 text-xs font-mono"
                  disabled={!isHumanControlled && loading}
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="px-3 py-1.5 rounded-xl border border-[var(--border)] hover:border-[var(--accent)] text-xs text-[var(--text-primary)] hover:text-[var(--accent)] transition-colors flex items-center gap-1 cursor-pointer"
              >
                {loading ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />}
                Naviguer
              </button>
            </form>

            {/* Virtual Browser Canvas / Viewport */}
            <div
              className="rounded-xl border border-[var(--border)] overflow-hidden"
              style={{ background: 'var(--bg-secondary)', minHeight: '280px' }}
            >
              {/* Canvas header */}
              <div className="px-4 py-2 border-b border-[var(--border)] flex items-center justify-between text-xs text-[var(--text-muted)] bg-[var(--surface-raised)]">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-500/70" />
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500/70" />
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/70" />
                  <span className="ml-2 font-mono truncate max-w-xs">{coworker.screen.page_title}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Lock size={12} className="text-emerald-500" />
                  <span className="text-[10px]">Résolution: 1280x800</span>
                </div>
              </div>

              {/* Viewport display */}
              <div className="p-6 font-mono text-xs text-[var(--text-secondary)] space-y-4">
                <div className="p-4 rounded-lg bg-[var(--surface)] border border-[var(--border)]">
                  <div className="text-[var(--accent)] font-semibold mb-2">
                    {coworker.screen.page_title}
                  </div>
                  <div className="text-xs text-[var(--text-muted)] mb-3">
                    URL active : <code className="text-[var(--text-primary)]">{coworker.screen.current_url}</code>
                  </div>
                  <div className="p-4 rounded border border-[var(--border)] bg-[var(--bg)] text-xs leading-relaxed whitespace-pre-wrap">
                    {coworker.screen.dom_summary}
                  </div>
                </div>

                {isHumanControlled && (
                  <div className="p-3 rounded-lg bg-[var(--accent-soft)] border border-[var(--accent-soft-2)] text-[var(--accent)] text-xs flex items-center justify-between">
                    <span>🎮 Mode opérateur actif : Vous contrôlez la souris et le clavier du navigateur virtuel.</span>
                    <button
                      onClick={handleReleaseWheel}
                      className="text-xs underline font-semibold hover:opacity-80 cursor-pointer"
                    >
                      Terminer l'intervention
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: TERMINAL */}
        {activeTab === 'terminal' && (
          <div className="space-y-3">
            <div
              className="rounded-xl border border-[var(--border)] p-4 font-mono text-xs overflow-y-auto space-y-1.5"
              style={{ background: '#07090b', height: '300px' }}
            >
              {coworker.terminal_buffer.map((line, idx) => (
                <div
                  key={idx}
                  className={`leading-relaxed ${
                    line.type === 'command'
                      ? 'text-amber-400 font-semibold'
                      : line.type === 'stderr'
                      ? 'text-red-400'
                      : line.type === 'info'
                      ? 'text-sky-400'
                      : 'text-zinc-300'
                  }`}
                >
                  {line.text}
                </div>
              ))}
            </div>

            {/* Terminal Command Input */}
            <form onSubmit={handleRunCommand} className="flex items-center gap-2">
              <div className="relative flex-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-amber-500 font-mono text-xs">$</span>
                <input
                  type="text"
                  value={commandInput}
                  onChange={(e) => setCommandInput(e.target.value)}
                  placeholder="Tapez une commande (ex: ls, npm test, cat file)..."
                  className="input-axiom w-full pl-8 pr-3 py-1.5 text-xs font-mono"
                  disabled={loading}
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="btn-primary px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1 cursor-pointer"
              >
                {loading ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} />}
                Exécuter
              </button>
            </form>
          </div>
        )}

        {/* TAB 3: WORKSPACE */}
        {activeTab === 'workspace' && (
          <div className="space-y-3">
            <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] text-xs">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-[var(--text-primary)]">Emplacement isolé du Coworker :</span>
                <span className="font-mono text-[11px] text-[var(--text-muted)]">Container Sandboxed</span>
              </div>
              <code className="block p-2 rounded bg-[var(--surface)] text-[var(--accent)] font-mono break-all border border-[var(--border)]">
                {coworker.workspace_path}
              </code>
            </div>

            <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] text-xs space-y-2">
              <div className="font-semibold text-[var(--text-primary)]">Outils autorisés pour ce Coworker :</div>
              <div className="flex flex-wrap gap-1.5">
                {coworker.tools.map((tool) => (
                  <span
                    key={tool}
                    className="px-2.5 py-1 rounded-md text-[11px] font-mono border border-[var(--border)] bg-[var(--bg-tertiary)] text-[var(--text-secondary)]"
                  >
                    {tool}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
