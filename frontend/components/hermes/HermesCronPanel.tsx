'use client'

import React, { useState } from 'react'
import {
  Clock,
  Play,
  CheckCircle2,
  AlertCircle,
  Plus,
  RefreshCw,
  Calendar,
  Terminal,
} from 'lucide-react'

interface RoutineItem {
  id: string
  name: string
  cron: string
  description: string
  lastRun: string
  status: 'SUCCESS' | 'RUNNING' | 'IDLE'
  command: string
}

const defaultRoutines: RoutineItem[] = [
  {
    id: 'cron-1',
    name: 'Inspection Quotidienne de Santé',
    cron: '0 8 * * *',
    description: "Vérifie les logs d'erreurs, l'espace disque et la disponibilité des endpoints FastAPI.",
    lastRun: "Aujourd'hui à 08:00 (Succès)",
    status: 'SUCCESS',
    command: 'python -m axiom.tools.healthcheck',
  },
  {
    id: 'cron-2',
    name: 'Indexation Mémoire & Vecteurs',
    cron: '*/30 * * * *',
    description: "Synchronise les mémoires récentes de l'agent dans SQLite FTS5 et la base vectorielle.",
    lastRun: 'Il y a 12 minutes (Succès)',
    status: 'SUCCESS',
    command: 'python -m axiom.core.memory --sync',
  },
  {
    id: 'cron-3',
    name: 'Veille & Veille Concurrentielle Web',
    cron: '0 18 * * 1-5',
    description: 'Scrape les dépôts GitHub populaires et les flux RSS sur les architectures multi-agents.',
    lastRun: 'Hier à 18:00 (Succès)',
    status: 'IDLE',
    command: 'python -m axiom.tools.web_research --daily',
  },
]

export default function HermesCronPanel() {
  const [routines, setRoutines] = useState<RoutineItem[]>(defaultRoutines)
  const [runningId, setRunningId] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const handleRunNow = (routine: RoutineItem) => {
    setRunningId(routine.id)
    setTimeout(() => {
      setRunningId(null)
      setSuccessMsg(`Routine "${routine.name}" exécutée avec succès !`)
      setRoutines((prev) =>
        prev.map((r) =>
          r.id === routine.id
            ? { ...r, lastRun: "À l'instant (Succès)", status: 'SUCCESS' }
            : r
        )
      )
      setTimeout(() => setSuccessMsg(null), 3000)
    }, 1200)
  }

  return (
    <div className="flex flex-col h-full bg-neutral-950/60 overflow-hidden text-neutral-200">
      {/* Top Banner */}
      <div className="p-3 border-b border-white/5 bg-neutral-900/40 flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-neutral-200">
          <Clock className="w-4 h-4 text-emerald-400" />
          <span>Planificateur Cron Hermes</span>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
          Système Actif
        </span>
      </div>

      {successMsg && (
        <div className="mx-2.5 mt-2 p-2 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-1.5">
          <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Routine Cards Feed */}
      <div className="flex-1 overflow-y-auto p-2.5 space-y-2">
        {routines.map((routine) => {
          const isRunning = runningId === routine.id

          return (
            <div
              key={routine.id}
              className="p-3 rounded-xl bg-neutral-900/70 border border-white/5 hover:border-white/10 transition-all space-y-2"
            >
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-medium text-neutral-200">{routine.name}</h4>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-black/60 text-amber-400 border border-white/5">
                  {routine.cron}
                </span>
              </div>

              <p className="text-[11px] text-neutral-400 leading-relaxed">
                {routine.description}
              </p>

              <div className="p-1.5 rounded-lg bg-black/40 border border-white/5 font-mono text-[10px] text-neutral-400 truncate">
                $ {routine.command}
              </div>

              <div className="flex items-center justify-between pt-1 border-t border-white/5 text-[10px] text-neutral-500">
                <span>Dernier run : {routine.lastRun}</span>
                <button
                  type="button"
                  disabled={isRunning}
                  onClick={() => handleRunNow(routine)}
                  className="flex items-center gap-1 px-2 py-1 rounded-lg bg-white/5 hover:bg-emerald-500/20 text-neutral-300 hover:text-emerald-300 transition-colors disabled:opacity-50"
                >
                  <Play className={`w-2.5 h-2.5 ${isRunning ? 'animate-spin' : ''}`} />
                  <span>{isRunning ? 'En cours...' : 'Exécuter'}</span>
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
