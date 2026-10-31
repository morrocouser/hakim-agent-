'use client'

import { useState, useEffect } from 'react'
import AppShell from '@/components/AppShell'
import PageHeader from '@/components/PageHeader'
import TakeTheWheelPanel from '@/components/TakeTheWheelPanel'
import {
  getCoworkers,
  CoworkerProfile,
  getRoutines,
  runRoutine,
  CoworkerRoutine,
} from '@/lib/api'
import {
  Users,
  Cpu,
  ShieldCheck,
  Globe,
  Terminal,
  Play,
  RotateCw,
  Clock,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  FolderLock,
} from 'lucide-react'

export default function CoworkersPage() {
  const [coworkers, setCoworkers] = useState<CoworkerProfile[]>([])
  const [selectedCoworkerId, setSelectedCoworkerId] = useState<string>('bot-browser')
  const [routines, setRoutines] = useState<CoworkerRoutine[]>([])
  const [loading, setLoading] = useState(true)
  const [routineRunning, setRoutineRunning] = useState<string | null>(null)
  const [bannerMsg, setBannerMsg] = useState<string | null>(null)

  const loadData = async () => {
    setLoading(true)
    try {
      const [cRes, rRes] = await Promise.all([getCoworkers(), getRoutines()])
      setCoworkers(cRes.coworkers)
      setRoutines(rRes.routines)
    } catch (err: any) {
      console.error('Erreur chargement coworkers:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const selectedCoworker = coworkers.find((c) => c.id === selectedCoworkerId) || coworkers[0]

  const handleCoworkerUpdated = (updated: CoworkerProfile) => {
    setCoworkers((prev) =>
      prev.map((c) => (c.id === updated.id ? updated : c))
    )
  }

  const handleRunRoutine = async (routineId: string, routineName: string) => {
    setRoutineRunning(routineId)
    setBannerMsg(null)
    try {
      const res = await runRoutine(routineId)
      setBannerMsg(
        `Routine '${routineName}' exécutée en autonomie ('Nobody watching'). L'action est enregistrée dans le registre d'audit.`
      )
      loadData()
    } catch (err: any) {
      setBannerMsg(`Erreur routine : ${err.message}`)
    } finally {
      setRoutineRunning(null)
    }
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="OpenBot AI Coworkers"
        title="Poste de Contrôle des Coworkers"
        description="Chaque agent dispose de son propre ordinateur virtuel isolé, d'un espace de travail dédié, et d'une passerelle de gouvernance avec passation de contrôle ('Take the Wheel')."
        actions={
          <button
            onClick={loadData}
            className="px-3.5 py-1.5 rounded-xl border border-[var(--border)] text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--accent)] flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <RotateCw size={14} />
            Actualiser
          </button>
        }
      />

      {bannerMsg && (
        <div className="mb-6 p-4 rounded-xl bg-[var(--accent-soft)] border border-[var(--accent-soft-2)] text-xs text-[var(--accent)] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={16} />
            <span>{bannerMsg}</span>
          </div>
          <button
            onClick={() => setBannerMsg(null)}
            className="text-xs font-semibold hover:opacity-80"
          >
            Fermer
          </button>
        </div>
      )}

      {/* Grid Coworkers Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {coworkers.map((c) => {
          const isSelected = c.id === selectedCoworker?.id
          const isHelp = c.control_state === 'HELP_REQUESTED'
          const isHuman = c.control_state === 'HUMAN_CONTROLLED'

          return (
            <div
              key={c.id}
              onClick={() => setSelectedCoworkerId(c.id)}
              className={`p-5 rounded-2xl border transition-all cursor-pointer relative overflow-hidden ${
                isSelected
                  ? 'border-[var(--accent)] shadow-lg ring-1 ring-[var(--accent)]'
                  : 'border-[var(--border)] hover:border-[var(--border-subtle)]'
              }`}
              style={{ background: 'var(--surface)' }}
            >
              <div className="flex items-start justify-between mb-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-white text-sm"
                  style={{ backgroundColor: c.avatar_color }}
                >
                  {c.name.slice(0, 2).toUpperCase()}
                </div>
                <div className="flex items-center gap-1.5">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{
                      backgroundColor: isHuman
                        ? 'var(--accent)'
                        : isHelp
                        ? '#f59e0b'
                        : '#10b981',
                    }}
                  />
                  <span className="text-[10px] font-mono uppercase text-[var(--text-muted)]">
                    {isHuman ? 'Humain' : isHelp ? 'Aide' : 'Actif'}
                  </span>
                </div>
              </div>

              <h3 className="font-semibold text-sm text-[var(--text-primary)] mb-0.5">
                {c.name}
              </h3>
              <div className="text-xs font-mono text-[var(--accent)] mb-2">
                {c.role}
              </div>
              <p className="text-xs text-[var(--text-secondary)] line-clamp-2 mb-3">
                {c.speciality}
              </p>

              <div className="pt-2 border-t border-[var(--border)] flex items-center justify-between text-[11px] text-[var(--text-muted)]">
                <span className="flex items-center gap-1">
                  <Cpu size={12} /> {c.tools.length} outils
                </span>
                <span className="flex items-center gap-1">
                  <FolderLock size={12} /> Isolé
                </span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Main Section: Selected Coworker Virtual Computer & Take the Wheel */}
      {selectedCoworker && (
        <div className="mb-10 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                <span>Environnement virtuel de {selectedCoworker.name}</span>
                <span className="text-xs font-mono px-2 py-0.5 rounded-md border border-[var(--border)] bg-[var(--bg-tertiary)] text-[var(--text-muted)]">
                  {selectedCoworker.id}
                </span>
              </h2>
              <p className="text-xs text-[var(--text-secondary)]">
                {selectedCoworker.description}
              </p>
            </div>
          </div>

          <TakeTheWheelPanel
            coworker={selectedCoworker}
            onCoworkerUpdated={handleCoworkerUpdated}
          />
        </div>
      )}

      {/* Section: Autonomous Routines (Nobody Watching) */}
      <div className="mt-8 border-t border-[var(--border)] pt-8">
        <div className="mb-4">
          <h2 className="text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
            <Clock size={18} className="text-[var(--accent)]" />
            Routines Autonomes & Tâches d'Arrière-plan
          </h2>
          <p className="text-xs text-[var(--text-secondary)]">
            Ces tâches s'exécutent en mode 'Sans surveillance' (Nobody watching). Chaque exécution fait l'objet d'un contrôle de gouvernance strict et est consignée dans le registre d'audit.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {routines.map((r) => {
            const isRunning = routineRunning === r.id
            return (
              <div
                key={r.id}
                className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h4 className="font-semibold text-xs text-[var(--text-primary)]">
                      {r.name}
                    </h4>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[var(--bg-tertiary)] text-[var(--text-muted)] border border-[var(--border)]">
                      {r.cron_schedule}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text-secondary)] mb-3">
                    {r.description}
                  </p>
                  <div className="font-mono text-[10px] p-2 rounded bg-[var(--bg-secondary)] text-[var(--text-muted)] mb-4 truncate border border-[var(--border)]">
                    $ {r.command_to_run}
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-[var(--border)]">
                  <span className="text-[10px] text-[var(--accent)] font-medium">
                    Coworker : {r.coworker_name}
                  </span>
                  <button
                    onClick={() => handleRunRoutine(r.id, r.name)}
                    disabled={isRunning}
                    className="px-3 py-1 rounded-lg text-xs font-semibold btn-primary flex items-center gap-1.5 cursor-pointer"
                  >
                    <Play size={12} />
                    {isRunning ? 'Exécution…' : 'Lancer'}
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </AppShell>
  )
}
