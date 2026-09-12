'use client'
import { useEffect, useState } from 'react'
import { Database } from '@phosphor-icons/react'
import AppShell from '@/components/AppShell'
import PageHeader from '@/components/PageHeader'
import { Panel, StatusBadge } from '@/components/ui-kit'
import { getMemory } from '@/lib/api'
const layers = [['working', 'Mémoire de travail', 'Contexte actif'], ['episodic', 'Mémoire épisodique', 'Historique des exécutions'], ['semantic', 'Mémoire sémantique', 'Connaissances consolidées']] as const
export default function MemoryPage() {
 const [memory, setMemory] = useState<Record<string, unknown> | null>(null)
 useEffect(() => { getMemory().then(setMemory).catch(() => setMemory({})) }, [])
 const tokens = Number(memory?.tokens_estimate ?? 0), percentage = Math.min(tokens / 5000 * 100, 100), nearLimit = tokens > 4500
 return <AppShell><PageHeader eyebrow="Contexte" title="Mémoire" description="État du contexte disponible pour les décisions et les tâches en cours." actions={<StatusBadge tone={nearLimit ? 'warning' : 'success'}>{nearLimit ? 'Compression prochaine' : 'Dans les limites'}</StatusBadge>} /><Panel className="mb-5 p-5"><div className="flex items-end justify-between"><div><span className="text-sm" style={{ color: 'var(--text-muted)' }}>Budget de contexte</span><strong className="mt-1 block font-mono text-2xl">{tokens.toLocaleString('fr-FR')} <span className="text-sm font-normal" style={{ color: 'var(--text-muted)' }}>/ 5 000 tokens</span></strong></div><span className="font-mono text-sm" style={{ color: nearLimit ? 'var(--warning)' : 'var(--accent)' }}>{Math.round(percentage)}%</span></div><div className="mt-4 h-2 overflow-hidden rounded-full" style={{ background: 'var(--bg-tertiary)' }}><div className="h-full rounded-full" style={{ width: `${percentage}%`, background: nearLimit ? 'var(--warning)' : 'var(--accent)' }} /></div></Panel><div className="grid gap-4 lg:grid-cols-3">{layers.map(([key, title, description]) => <Panel key={key} className="p-5"><div className="flex items-center gap-3"><span className="rounded-xl p-2" style={{ background: 'var(--accent-soft)' }}><Database size={20} style={{ color: 'var(--accent)' }} /></span><div><h2 className="font-semibold">{title}</h2><p className="text-xs" style={{ color: 'var(--text-muted)' }}>{description}</p></div></div><pre tabIndex={0} aria-label={`Contenu de ${title}`} className="mt-5 max-h-72 overflow-auto rounded-xl p-4 text-xs" style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}>{memory ? JSON.stringify(memory[key], null, 2) || 'Aucune donnée.' : 'Chargement…'}</pre></Panel>)}</div></AppShell>
}
