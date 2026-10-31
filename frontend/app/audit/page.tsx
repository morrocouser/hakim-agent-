'use client'

import { useState, useEffect } from 'react'
import AppShell from '@/components/AppShell'
import PageHeader from '@/components/PageHeader'
import {
  getAuditTrail,
  AuditEntry,
  AuditQueryResult,
} from '@/lib/api'
import {
  ShieldCheck,
  ShieldAlert,
  Search,
  Filter,
  EyeOff,
  UserCheck,
  Hand,
  Clock,
  RotateCw,
  FileCode,
  Terminal,
  Globe,
  ArrowRight,
  CheckCircle,
  XCircle,
} from 'lucide-react'

export default function AuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([])
  const [total, setTotal] = useState<number>(0)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [activeFilter, setActiveFilter] = useState<'all' | 'unattended' | 'takeover' | 'denied'>('all')
  const [selectedEntry, setSelectedEntry] = useState<AuditEntry | null>(null)

  const loadAudit = async () => {
    setLoading(true)
    try {
      const params: any = { limit: 100 }
      if (activeFilter === 'unattended') {
        params.nobody_watching = true
      } else if (activeFilter === 'takeover') {
        params.decision = 'REQUIRE_TAKEOVER'
      } else if (activeFilter === 'denied') {
        params.decision = 'DENIED'
      }

      if (search.trim()) {
        params.search = search.trim()
      }

      const res = await getAuditTrail(params)
      setEntries(res.items)
      setTotal(res.total)
    } catch (err: any) {
      console.error('Erreur chargement audit ledger:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAudit()
  }, [activeFilter])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    loadAudit()
  }

  // Calculate statistics from loaded entries
  const stats = {
    allowed: entries.filter((e) => e.decision === 'ALLOWED').length,
    denied: entries.filter((e) => e.decision === 'DENIED').length,
    takeovers: entries.filter((e) => e.decision === 'REQUIRE_TAKEOVER').length,
    unattended: entries.filter((e) =>
      ['routine', 'handoff', 'responsibility', 'memory'].includes(e.initiator_kind)
    ).length,
  }

  const getInitiatorBadge = (kind: string) => {
    switch (kind) {
      case 'person':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-mono bg-sky-500/10 text-sky-400 border border-sky-500/20">
            <UserCheck size={11} /> Personne présente
          </span>
        )
      case 'routine':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-mono bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Clock size={11} /> Routine autonome
          </span>
        )
      case 'handoff':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <ArrowRight size={11} /> Handoff inter-bots
          </span>
        )
      case 'responsibility':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <ShieldCheck size={11} /> Responsabilité
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-mono bg-zinc-500/10 text-zinc-400 border border-zinc-500/20">
            {kind}
          </span>
        )
    }
  }

  const getDecisionBadge = (decision: string) => {
    switch (decision) {
      case 'ALLOWED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle size={11} /> Autorisé
          </span>
        )
      case 'DENIED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-red-500/10 text-red-400 border border-red-500/30">
            <XCircle size={11} /> Refusé
          </span>
        )
      case 'REQUIRE_TAKEOVER':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/40">
            <Hand size={11} /> Take the Wheel
          </span>
        )
      default:
        return <span>{decision}</span>
    }
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="OpenBot Traceability & Governance"
        title="Registre d'Audit & Gouvernance (Audit Ledger)"
        description="Traçabilité exhaustive et vérifiable de toutes les décisions de la passerelle de gouvernance fail-closed, avec distinction précise entre exécution assistée et exécution sans surveillance."
        actions={
          <button
            onClick={loadAudit}
            className="px-3.5 py-1.5 rounded-xl border border-[var(--border)] text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--accent)] flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <RotateCw size={14} />
            Actualiser
          </button>
        }
      />

      {/* KPI Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        <div className="p-4 rounded-2xl border border-[var(--border)] bg-[var(--surface)]">
          <div className="text-xs text-[var(--text-muted)] uppercase tracking-wider font-semibold">
            Actions totales
          </div>
          <div className="text-2xl font-bold font-mono text-[var(--text-primary)] mt-1">
            {total}
          </div>
          <div className="text-[11px] text-[var(--text-secondary)] mt-1">
            Événements enregistrés
          </div>
        </div>

        <div className="p-4 rounded-2xl border border-[var(--border)] bg-[var(--surface)]">
          <div className="text-xs text-emerald-400 uppercase tracking-wider font-semibold">
            Conformes (Autorisées)
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
            {stats.allowed}
          </div>
          <div className="text-[11px] text-[var(--text-secondary)] mt-1">
            Validées par les règles CEL
          </div>
        </div>

        <div className="p-4 rounded-2xl border border-[var(--border)] bg-[var(--surface)]">
          <div className="text-xs text-amber-400 uppercase tracking-wider font-semibold">
            Take the Wheel (2FA/Sensible)
          </div>
          <div className="text-2xl font-bold font-mono text-amber-400 mt-1">
            {stats.takeovers}
          </div>
          <div className="text-[11px] text-[var(--text-secondary)] mt-1">
            Passation de contrôle requise
          </div>
        </div>

        <div className="p-4 rounded-2xl border border-[var(--border)] bg-[var(--surface)]">
          <div className="text-xs text-purple-400 uppercase tracking-wider font-semibold">
            Sans surveillance (Nobody Watching)
          </div>
          <div className="text-2xl font-bold font-mono text-purple-400 mt-1">
            {stats.unattended}
          </div>
          <div className="text-[11px] text-[var(--text-secondary)] mt-1">
            Routines & Handoffs autonomes
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 mb-6 p-3 rounded-2xl border border-[var(--border)] bg-[var(--surface)]">
        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => setActiveFilter('all')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors cursor-pointer ${
              activeFilter === 'all'
                ? 'bg-[var(--accent)] text-white'
                : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] bg-[var(--bg-secondary)]'
            }`}
          >
            Tous les événements
          </button>
          <button
            onClick={() => setActiveFilter('unattended')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors cursor-pointer flex items-center gap-1 ${
              activeFilter === 'unattended'
                ? 'bg-purple-600 text-white'
                : 'text-[var(--text-muted)] hover:text-purple-400 bg-[var(--bg-secondary)]'
            }`}
          >
            <EyeOff size={13} />
            Sans surveillance (Nobody Watching)
          </button>
          <button
            onClick={() => setActiveFilter('takeover')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors cursor-pointer flex items-center gap-1 ${
              activeFilter === 'takeover'
                ? 'bg-amber-600 text-white'
                : 'text-[var(--text-muted)] hover:text-amber-400 bg-[var(--bg-secondary)]'
            }`}
          >
            <Hand size={13} />
            Take the Wheel
          </button>
          <button
            onClick={() => setActiveFilter('denied')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors cursor-pointer flex items-center gap-1 ${
              activeFilter === 'denied'
                ? 'bg-red-600 text-white'
                : 'text-[var(--text-muted)] hover:text-red-400 bg-[var(--bg-secondary)]'
            }`}
          >
            <ShieldAlert size={13} />
            Refusés (Fail-Closed)
          </button>
        </div>

        {/* Search Input */}
        <form onSubmit={handleSearchSubmit} className="relative sm:w-72">
          <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Rechercher intention, outil..."
            className="input-axiom w-full pl-9 pr-3 py-1.5 text-xs"
          />
        </form>
      </div>

      {/* Audit Table */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-[var(--border)] bg-[var(--bg-secondary)] text-[var(--text-muted)] font-mono text-[11px]">
              <tr>
                <th className="p-3.5 pl-4">Horodatage</th>
                <th className="p-3.5">Coworker</th>
                <th className="p-3.5">Initiateur</th>
                <th className="p-3.5">Outil & Intention</th>
                <th className="p-3.5">Cible / Commande</th>
                <th className="p-3.5">Gouvernance</th>
                <th className="p-3.5 pr-4 text-right">Détails</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)] font-sans">
              {entries.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-[var(--text-muted)]">
                    Aucun événement d'audit ne correspond aux filtres sélectionnés.
                  </td>
                </tr>
              ) : (
                entries.map((entry) => {
                  const formattedTime = new Date(entry.timestamp).toLocaleTimeString('fr-FR', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                  })

                  return (
                    <tr
                      key={entry.id}
                      className="hover:bg-[var(--bg-tertiary)] transition-colors cursor-pointer"
                      onClick={() => setSelectedEntry(entry)}
                    >
                      <td className="p-3.5 pl-4 font-mono text-[11px] text-[var(--text-muted)] whitespace-nowrap">
                        {formattedTime}
                      </td>
                      <td className="p-3.5 font-semibold text-[var(--text-primary)] whitespace-nowrap">
                        {entry.coworker_name}
                      </td>
                      <td className="p-3.5 whitespace-nowrap">
                        {getInitiatorBadge(entry.initiator_kind)}
                      </td>
                      <td className="p-3.5 max-w-xs">
                        <div className="font-mono text-[11px] text-[var(--accent)] truncate">
                          {entry.tool_name}
                        </div>
                        <div className="text-[11px] text-[var(--text-secondary)] truncate">
                          {entry.intent}
                        </div>
                      </td>
                      <td className="p-3.5 max-w-xs">
                        <code className="block font-mono text-[10px] text-[var(--text-muted)] truncate bg-[var(--bg-secondary)] px-2 py-0.5 rounded border border-[var(--border)]">
                          {entry.target || '—'}
                        </code>
                      </td>
                      <td className="p-3.5 whitespace-nowrap">
                        {getDecisionBadge(entry.decision)}
                      </td>
                      <td className="p-3.5 pr-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedEntry(entry)
                          }}
                          className="px-2.5 py-1 rounded-lg text-[11px] font-mono text-[var(--text-secondary)] hover:text-[var(--accent)] hover:bg-[var(--accent-soft)] transition-colors cursor-pointer"
                        >
                          Examiner
                        </button>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal / Inspector for selected entry */}
      {selectedEntry && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
          onClick={() => setSelectedEntry(null)}
        >
          <div
            className="w-full max-w-lg p-6 rounded-2xl border border-[var(--border)] bg-[var(--surface-raised)] shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between">
              <div>
                <span className="text-xs font-mono text-[var(--text-muted)] uppercase">
                  Identifiant : {selectedEntry.id}
                </span>
                <h3 className="text-base font-bold text-[var(--text-primary)] mt-0.5">
                  Inspection de la décision de gouvernance
                </h3>
              </div>
              <button
                onClick={() => setSelectedEntry(null)}
                className="text-[var(--text-muted)] hover:text-[var(--text-primary)] text-lg cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Règle de sécurité :</span>
                  <code className="font-mono text-[var(--accent)]">{selectedEntry.rule_id}</code>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Décision :</span>
                  <span>{getDecisionBadge(selectedEntry.decision)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Initiateur :</span>
                  <span>{getInitiatorBadge(selectedEntry.initiator_kind)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Durée d'évaluation :</span>
                  <span className="font-mono">{selectedEntry.duration_ms} ms</span>
                </div>
              </div>

              <div>
                <span className="font-semibold text-[var(--text-primary)]">Motif de la passerelle :</span>
                <p className="mt-1 p-3 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border)] text-[var(--text-secondary)] leading-relaxed">
                  {selectedEntry.reason}
                </p>
              </div>

              <div>
                <span className="font-semibold text-[var(--text-primary)]">Cible & Paramètres :</span>
                <code className="block mt-1 p-3 rounded-lg bg-[#07090b] border border-[var(--border)] font-mono text-zinc-300 break-all">
                  {selectedEntry.target || 'Aucune cible explicite'}
                </code>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedEntry(null)}
                className="px-4 py-1.5 rounded-xl text-xs font-semibold btn-primary cursor-pointer"
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  )
}
