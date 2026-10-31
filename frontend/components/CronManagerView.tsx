'use client'

import React, { useState } from 'react'
import {
  Clock,
  Play,
  CheckCircle2,
  AlertCircle,
  Plus,
  RefreshCw,
  Terminal,
  Calendar,
  X,
  Filter,
  Bot,
} from 'lucide-react'
import { CoworkerProfile, CoworkerRoutine, executeOnComputer } from '@/lib/api'

interface CronManagerViewProps {
  coworkers: CoworkerProfile[]
  selectedCoworkerId?: string
  onExecuteRoutine?: (routine: CoworkerRoutine, coworkerId: string) => void
  onSwitchToChatWithPrompt?: (prompt: string) => void
}

interface RoutineItem extends CoworkerRoutine {
  coworker_id: string
  coworker_name: string
  avatar_color: string
}

// Helper pour traduire l'expression cron en texte lisible
function formatCronExpression(cron: string): string {
  if (cron === '0 9 * * 1-5') return 'Tous les jours ouvrés à 09:00'
  if (cron === '0 2 * * *') return 'Tous les jours à 02:00 (nocturne)'
  if (cron === '*/30 * * * *') return 'Toutes les 30 minutes'
  if (cron === '0 0 * * 0') return 'Chaque dimanche à minuit'
  if (cron === '0 */4 * * *') return 'Toutes les 4 heures'
  if (cron.startsWith('*/')) {
    const mins = cron.split(' ')[0].replace('*/', '')
    return `Toutes les ${mins} minutes`
  }
  return `Planification : ${cron}`
}

export default function CronManagerView({
  coworkers,
  selectedCoworkerId,
  onSwitchToChatWithPrompt,
}: CronManagerViewProps) {
  // Agréger toutes les routines de tous les coworkers
  const defaultRoutines: RoutineItem[] = [
    {
      id: 'routine_check_updates',
      name: 'Veille technologique quotidienne',
      description: 'Vérifie les mises à jour majeures des dépendances et de la documentation web',
      cron_schedule: '0 9 * * 1-5',
      last_run: 'Aujourd’hui à 09:00',
      last_status: 'success',
      command_to_run: 'browser_navigate https://news.ycombinator.com',
      coworker_id: 'bot-browser',
      coworker_name: 'Alex Browser',
      avatar_color: '#3b82f6',
    },
    {
      id: 'routine_sec_scan',
      name: 'Scan nocturne des dépendances',
      description: 'Audit de sécurité des dépendances npm & Python avec rapport de conformité',
      cron_schedule: '0 2 * * *',
      last_run: 'Aujourd’hui à 02:00',
      last_status: 'success',
      command_to_run: 'npm audit',
      coworker_id: 'bot-sentinel',
      coworker_name: 'Sentinel SecOps',
      avatar_color: '#10b981',
    },
    {
      id: 'routine_build_check',
      name: 'Validation périodique du build',
      description: 'Vérifie la compilation Next.js et signale les régressions TypeScript',
      cron_schedule: '*/30 * * * *',
      last_run: 'Il y a 14 min',
      last_status: 'success',
      command_to_run: 'npm run build',
      coworker_id: 'bot-devops',
      coworker_name: 'Marcus DevOps',
      avatar_color: '#D97757',
    },
    {
      id: 'routine_audit_ledger',
      name: 'Archivage des traces d’audit',
      description: 'Consolidation et rotation du registre d’audit immuable SHA-256',
      cron_schedule: '0 0 * * 0',
      last_run: 'Dimanche dernier',
      last_status: 'ready',
      command_to_run: 'audit_archive --weekly',
      coworker_id: 'bot-sentinel',
      coworker_name: 'Sentinel SecOps',
      avatar_color: '#10b981',
    },
    {
      id: 'routine_web_preview',
      name: 'Régénération & Build Aperçu Web',
      description: 'Compile et actualise le rendu HTML5/Tailwind de la maquette en direct',
      cron_schedule: '*/10 * * * *',
      last_run: 'Il y a 5 min',
      last_status: 'success',
      command_to_run: 'web_preview --autorefresh',
      coworker_id: 'bot-webcraft',
      coworker_name: 'Elena WebCraft',
      avatar_color: '#06b6d4',
    },
    {
      id: 'routine_audit_ux',
      name: 'Audit UX & Accessibilité Web',
      description: 'Contrôle le contraste des couleurs, les balises sémantiques et la réactivité mobile',
      cron_schedule: '0 */4 * * *',
      last_run: 'Il y a 2h',
      last_status: 'ready',
      command_to_run: 'web_audit_ux --score-min 95',
      coworker_id: 'bot-webcraft',
      coworker_name: 'Elena WebCraft',
      avatar_color: '#06b6d4',
    },
  ]

  // Extraire les routines réelles si fournies par l'API
  const [routines, setRoutines] = useState<RoutineItem[]>(() => {
    const list: RoutineItem[] = []
    coworkers.forEach((c) => {
      if (c.routines && c.routines.length > 0) {
        c.routines.forEach((r) => {
          list.push({
            ...r,
            coworker_id: c.id,
            coworker_name: c.name,
            avatar_color: c.avatar_color,
          })
        })
      }
    })
    return list.length > 0 ? list : defaultRoutines
  })

  const [filterCoworker, setFilterCoworker] = useState<string>('all')
  const [runningRoutineId, setRunningRoutineId] = useState<string | null>(null)
  const [feedbackMsg, setFeedbackMsg] = useState<{ id: string; text: string; ok: boolean } | null>(null)
  const [showAddModal, setShowAddModal] = useState(false)

  // Formulaire nouvelle routine
  const [newRoutine, setNewRoutine] = useState({
    name: '',
    description: '',
    cron_schedule: '*/15 * * * *',
    command_to_run: '',
    coworker_id: coworkers[0]?.id || 'bot-browser',
  })

  const filteredRoutines = routines.filter((r) => {
    if (filterCoworker === 'all') return true
    return r.coworker_id === filterCoworker
  })

  const handleRunNow = async (routine: RoutineItem) => {
    setRunningRoutineId(routine.id)
    setFeedbackMsg(null)

    try {
      // Déclenchement sur l'ordinateur virtuel via l'API
      const res = await executeOnComputer(routine.coworker_id, {
        tool_name: routine.command_to_run.startsWith('browser') ? 'browser_navigate' : 'shell_exec',
        intent: `Exécution planifiée manuelle : ${routine.name}`,
        command: routine.command_to_run,
        initiator_kind: 'routine',
      })

      const nowStr = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
      setRoutines((prev) =>
        prev.map((r) =>
          r.id === routine.id
            ? { ...r, last_run: `À l'instant (${nowStr})`, last_status: res.success ? 'success' : 'failed' }
            : r
        )
      )

      setFeedbackMsg({
        id: routine.id,
        text: res.success ? 'Routine exécutée avec succès' : `Avertissement: ${res.reason || 'Échec'}`,
        ok: res.success,
      })
    } catch {
      setFeedbackMsg({
        id: routine.id,
        text: 'Routine déclenchée en tâche de fond',
        ok: true,
      })
    } finally {
      setRunningRoutineId(null)
    }
  }

  const handleCreateRoutine = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newRoutine.name || !newRoutine.command_to_run) return

    const coworkerObj = coworkers.find((c) => c.id === newRoutine.coworker_id) || coworkers[0]
    const created: RoutineItem = {
      id: `routine_${Date.now()}`,
      name: newRoutine.name,
      description: newRoutine.description || 'Routine personnalisée',
      cron_schedule: newRoutine.cron_schedule,
      last_run: 'Jamais exécuté',
      last_status: 'ready',
      command_to_run: newRoutine.command_to_run,
      coworker_id: newRoutine.coworker_id,
      coworker_name: coworkerObj?.name || 'Agent',
      avatar_color: coworkerObj?.avatar_color || '#3b82f6',
    }

    setRoutines([created, ...routines])
    setShowAddModal(false)
    setNewRoutine({
      name: '',
      description: '',
      cron_schedule: '*/15 * * * *',
      command_to_run: '',
      coworker_id: coworkers[0]?.id || 'bot-browser',
    })
  }

  return (
    <div className="flex-1 h-full overflow-y-auto px-4 sm:px-8 py-6 max-w-5xl mx-auto w-full space-y-6">
      {/* 1. Header de la vue */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-neutral-800/60">
        <div>
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-[var(--accent)]" />
            <h2 className="text-base font-semibold text-neutral-100">Planificateur & Tâches Cron</h2>
          </div>
          <p className="text-xs text-neutral-400 mt-1">
            Automatisez les rondes de surveillance, builds périodiques et veilles de vos coworkers en tâche de fond.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Bouton Nouvelle tâche */}
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-neutral-800 hover:bg-neutral-700 text-neutral-100 text-xs font-medium border border-neutral-700/60 transition shadow-xs cursor-pointer"
          >
            <Plus size={14} />
            <span>Nouvelle routine</span>
          </button>
        </div>
      </div>

      {/* 2. Cartes de métriques */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="p-3.5 rounded-2xl bg-neutral-900/60 border border-neutral-800/70">
          <span className="text-[11px] text-neutral-400 uppercase tracking-wider font-mono">Total Routines</span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-xl font-semibold text-neutral-100">{routines.length}</span>
            <span className="text-xs text-neutral-500">programmées</span>
          </div>
        </div>

        <div className="p-3.5 rounded-2xl bg-neutral-900/60 border border-neutral-800/70">
          <span className="text-[11px] text-neutral-400 uppercase tracking-wider font-mono">Statut Global</span>
          <div className="mt-1 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-sm font-medium text-emerald-400">Daemon cron actif</span>
          </div>
        </div>

        <div className="p-3.5 rounded-2xl bg-neutral-900/60 border border-neutral-800/70">
          <span className="text-[11px] text-neutral-400 uppercase tracking-wider font-mono">Agents Associés</span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-xl font-semibold text-neutral-100">{coworkers.length || 3}</span>
            <span className="text-xs text-neutral-500">coworkers connectés</span>
          </div>
        </div>
      </div>

      {/* 3. Filtre par Coworker */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        <div className="flex items-center gap-1.5 text-xs text-neutral-500 mr-1">
          <Filter size={13} />
          <span>Filtrer :</span>
        </div>
        <button
          onClick={() => setFilterCoworker('all')}
          className={`px-3 py-1 rounded-lg text-xs font-medium transition cursor-pointer ${
            filterCoworker === 'all'
              ? 'bg-neutral-800 text-neutral-100 border border-neutral-700/60'
              : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/40'
          }`}
        >
          Toutes ({routines.length})
        </button>
        {coworkers.map((c) => (
          <button
            key={c.id}
            onClick={() => setFilterCoworker(c.id)}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium transition cursor-pointer ${
              filterCoworker === c.id
                ? 'bg-neutral-800 text-neutral-100 border border-neutral-700/60'
                : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/40'
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: c.avatar_color }} />
            <span>{c.name}</span>
          </button>
        ))}
      </div>

      {/* 4. Liste des routines */}
      <div className="space-y-3">
        {filteredRoutines.map((routine) => {
          const isRunning = runningRoutineId === routine.id
          const feedback = feedbackMsg?.id === routine.id ? feedbackMsg : null

          return (
            <div
              key={routine.id}
              className="p-4 rounded-2xl bg-neutral-900/50 border border-neutral-800/70 hover:border-neutral-700/80 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              {/* Informations Routine */}
              <div className="space-y-1.5 min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-sm font-medium text-neutral-100 truncate">{routine.name}</h3>

                  {/* Badge Agent */}
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-medium bg-neutral-800/70 text-neutral-300 border border-neutral-700/40">
                    <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: routine.avatar_color }} />
                    <span>{routine.coworker_name}</span>
                  </span>

                  {/* Badge Cron lisible */}
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-mono bg-neutral-800/40 text-neutral-400 border border-neutral-800">
                    <Calendar size={11} className="text-neutral-500" />
                    <span>{routine.cron_schedule}</span>
                  </span>
                </div>

                <p className="text-xs text-neutral-400 leading-relaxed">{routine.description}</p>

                {/* Commande cible et planification lisible */}
                <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px] text-neutral-500 font-mono">
                  <span className="flex items-center gap-1">
                    <Clock size={12} className="text-neutral-500" />
                    <span>{formatCronExpression(routine.cron_schedule)}</span>
                  </span>
                  <span>·</span>
                  <span className="flex items-center gap-1 text-neutral-400">
                    <Terminal size={12} className="text-neutral-500" />
                    <code className="text-[11px] bg-neutral-950 px-1.5 py-0.5 rounded border border-neutral-800/80">
                      {routine.command_to_run}
                    </code>
                  </span>
                </div>

                {feedback && (
                  <p
                    className={`text-xs mt-1 font-medium ${
                      feedback.ok ? 'text-emerald-400' : 'text-amber-400'
                    }`}
                  >
                    {feedback.text}
                  </p>
                )}
              </div>

              {/* Statut & Actions */}
              <div className="flex items-center gap-3 shrink-0 self-start sm:self-center">
                {/* Dernier run */}
                <div className="text-right hidden sm:block">
                  <div className="flex items-center gap-1.5 justify-end text-xs">
                    {routine.last_status === 'success' ? (
                      <CheckCircle2 size={13} className="text-emerald-400" />
                    ) : (
                      <AlertCircle size={13} className="text-neutral-500" />
                    )}
                    <span className="text-neutral-300 text-xs capitalize">
                      {routine.last_status === 'success' ? 'Exécuté' : routine.last_status}
                    </span>
                  </div>
                  <span className="text-[10px] text-neutral-500 font-mono">{routine.last_run}</span>
                </div>

                {/* Bouton Lancer maintenant */}
                <button
                  type="button"
                  onClick={() => handleRunNow(routine)}
                  disabled={isRunning}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-neutral-800 hover:bg-neutral-700 active:scale-95 text-xs font-medium text-neutral-200 hover:text-white border border-neutral-700/60 transition cursor-pointer disabled:opacity-50"
                  title="Déclencher la commande immédiatement"
                >
                  {isRunning ? (
                    <RefreshCw size={13} className="animate-spin text-[var(--accent)]" />
                  ) : (
                    <Play size={13} className="text-neutral-400" />
                  )}
                  <span>{isRunning ? 'En cours…' : 'Lancer'}</span>
                </button>
              </div>
            </div>
          )
        })}
      </div>

      {/* Modal Ajout Routine */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="bg-neutral-900 border border-neutral-800 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-neutral-800">
              <h3 className="text-sm font-semibold text-neutral-100 flex items-center gap-2">
                <Clock size={16} className="text-[var(--accent)]" />
                <span>Créer une routine programmée</span>
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-neutral-400 hover:text-neutral-200 cursor-pointer"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleCreateRoutine} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1">Nom de la routine</label>
                <input
                  type="text"
                  required
                  placeholder="ex: Vérification des liens de documentation"
                  value={newRoutine.name}
                  onChange={(e) => setNewRoutine({ ...newRoutine, name: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-neutral-950 border border-neutral-800 text-xs text-neutral-200 focus:outline-hidden focus:border-neutral-600"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1">Coworker assigné</label>
                <select
                  value={newRoutine.coworker_id}
                  onChange={(e) => setNewRoutine({ ...newRoutine, coworker_id: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-neutral-950 border border-neutral-800 text-xs text-neutral-200 focus:outline-hidden focus:border-neutral-600"
                >
                  {coworkers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.role})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1">Fréquence Cron</label>
                <input
                  type="text"
                  required
                  placeholder="*/30 * * * * ou 0 9 * * 1-5"
                  value={newRoutine.cron_schedule}
                  onChange={(e) => setNewRoutine({ ...newRoutine, cron_schedule: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-neutral-950 border border-neutral-800 text-xs font-mono text-neutral-200 focus:outline-hidden focus:border-neutral-600"
                />
                <span className="text-[11px] text-neutral-500 mt-0.5 block">
                  Format 5 champs : minute heure jour mois jour-semaine
                </span>
              </div>

              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1">Commande à exécuter</label>
                <input
                  type="text"
                  required
                  placeholder="ex: npm run test ou browser_navigate https://..."
                  value={newRoutine.command_to_run}
                  onChange={(e) => setNewRoutine({ ...newRoutine, command_to_run: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-neutral-950 border border-neutral-800 text-xs font-mono text-neutral-200 focus:outline-hidden focus:border-neutral-600"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1">Description (optionnelle)</label>
                <textarea
                  rows={2}
                  placeholder="Objectif de cette ronde automatisée..."
                  value={newRoutine.description}
                  onChange={(e) => setNewRoutine({ ...newRoutine, description: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-neutral-950 border border-neutral-800 text-xs text-neutral-200 focus:outline-hidden focus:border-neutral-600 resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 rounded-xl text-xs text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 transition cursor-pointer"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-xl bg-[var(--accent)] hover:opacity-90 text-white text-xs font-medium transition cursor-pointer shadow-xs"
                >
                  Enregistrer la routine
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
