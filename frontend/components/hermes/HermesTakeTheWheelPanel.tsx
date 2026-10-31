'use client'

import React, { useState } from 'react'
import {
  Monitor,
  Terminal,
  ShieldCheck,
  ShieldAlert,
  Play,
  RotateCcw,
  ExternalLink,
  Lock,
} from 'lucide-react'

export default function HermesTakeTheWheelPanel() {
  const [isHumanInControl, setIsHumanInControl] = useState(false)
  const [terminalLogs, setTerminalLogs] = useState<string[]>([
    '[SYSTEM] Agent OpenBot initialisé dans le conteneur sandboxé.',
    '[BROWSER] Navigateur headless Chromium démarré sur port 9222.',
    '[ROUTER] Navigation effectuée vers https://docs.github.com/fr.',
    '[GOVERNANCE] Règle stricte : 0 fuite de clés API, isolation du réseau.',
  ])
  const [commandInput, setCommandInput] = useState('')

  const handleToggleControl = () => {
    setIsHumanInControl(!isHumanInControl)
    const log = !isHumanInControl
      ? '[OPERATEUR] L’opérateur a PRIS LE VOLANT (Mode Manuel Actif).'
      : '[OPERATEUR] Contrôle rendu à l’agent autonome HakimAgent.'
    setTerminalLogs((prev) => [...prev, log])
  }

  const handleSendCommand = (e: React.FormEvent) => {
    e.preventDefault()
    if (!commandInput.trim()) return
    const cmd = commandInput.trim()
    setCommandInput('')
    setTerminalLogs((prev) => [
      ...prev,
      `$ ${cmd}`,
      `[SANDBOX] Commande "${cmd}" exécutée avec statut code 0.`,
    ])
  }

  return (
    <div className="flex flex-col h-full bg-neutral-950/60 overflow-hidden text-neutral-200">
      {/* Top Banner with Control State */}
      <div className="p-3 border-b border-white/5 bg-neutral-900/40 flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-neutral-200">
          <Monitor className="w-4 h-4 text-cyan-400" />
          <span>Écran Virtuel & Take The Wheel</span>
        </div>
        <span
          className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
            isHumanInControl
              ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
              : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
          }`}
        >
          {isHumanInControl ? 'Contrôle Humain' : 'Mode Autonome'}
        </span>
      </div>

      {/* Virtual Browser Preview Frame */}
      <div className="p-2.5 border-b border-white/5">
        <div className="rounded-xl border border-white/10 bg-black/60 overflow-hidden shadow-lg">
          {/* Browser Address Bar */}
          <div className="flex items-center justify-between px-2.5 py-1.5 bg-neutral-900/80 border-b border-white/5 text-[11px] font-mono">
            <div className="flex items-center gap-1.5 text-neutral-400">
              <span className="w-2 h-2 rounded-full bg-red-500/80" />
              <span className="w-2 h-2 rounded-full bg-yellow-500/80" />
              <span className="w-2 h-2 rounded-full bg-emerald-500/80" />
              <span className="ml-1 text-[10px] text-neutral-500">https://docs.github.com</span>
            </div>
            <Lock className="w-3 h-3 text-emerald-400" />
          </div>

          {/* Browser Screen Simulation */}
          <div className="p-4 min-h-[140px] flex flex-col items-center justify-center text-center bg-gradient-to-b from-neutral-900/50 to-black/80 space-y-2">
            <Monitor className="w-8 h-8 text-cyan-400/70 animate-pulse" />
            <p className="text-xs text-neutral-300 font-medium">
              Conteneur Virtuel Headless Synchronisé
            </p>
            <p className="text-[10px] text-neutral-500 max-w-xs">
              L'agent navigue et interagit avec les pages web et les formulaires en temps réel.
            </p>

            <button
              type="button"
              onClick={handleToggleControl}
              className={`mt-2 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold shadow-md transition-all cursor-pointer ${
                isHumanInControl
                  ? 'bg-amber-500 hover:bg-amber-400 text-black'
                  : 'bg-cyan-600 hover:bg-cyan-500 text-white'
              }`}
            >
              {isHumanInControl ? (
                <>
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Rendre le volant à l'Agent</span>
                </>
              ) : (
                <>
                  <ShieldAlert className="w-3.5 h-3.5" />
                  <span>Prendre le volant</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Terminal Output & Input */}
      <div className="flex-1 flex flex-col min-h-0 bg-black/80">
        <div className="px-3 py-1.5 bg-neutral-900/80 border-b border-white/5 flex items-center justify-between text-[10px] font-mono text-neutral-400 uppercase tracking-wider">
          <div className="flex items-center gap-1.5">
            <Terminal className="w-3 h-3 text-emerald-400" />
            <span>Console Sandbox en direct</span>
          </div>
          <button
            type="button"
            onClick={() => setTerminalLogs(['[SYSTEM] Console réinitialisée.'])}
            className="hover:text-neutral-200 transition-colors"
          >
            Vider
          </button>
        </div>

        <div className="flex-1 p-2.5 overflow-y-auto font-mono text-[11px] text-neutral-300 space-y-1">
          {terminalLogs.map((log, idx) => (
            <div key={idx} className="leading-relaxed">
              <span className="text-emerald-500/80 mr-1.5">›</span>
              {log}
            </div>
          ))}
        </div>

        {/* Interactive Terminal Input */}
        <form onSubmit={handleSendCommand} className="p-2 border-t border-white/10 bg-neutral-950 flex items-center gap-2">
          <span className="text-xs font-mono text-emerald-400">$</span>
          <input
            type="text"
            value={commandInput}
            onChange={(e) => setCommandInput(e.target.value)}
            placeholder="Tapez une commande shell ou un script..."
            className="flex-1 bg-transparent text-xs font-mono text-neutral-200 placeholder-neutral-600 focus:outline-none"
          />
          <button
            type="submit"
            className="p-1 rounded bg-white/5 hover:bg-white/10 text-neutral-300 text-xs font-mono"
          >
            Entrée
          </button>
        </form>
      </div>
    </div>
  )
}
