'use client'
import { useEffect, useState } from 'react'
import { Brain, Lightning, TrendUp } from '@phosphor-icons/react'
import AppShell from '@/components/AppShell'
import AgentCard from '@/components/AgentCard'
import PageHeader from '@/components/PageHeader'
import { EmptyState, Panel, StatusBadge } from '@/components/ui-kit'
import { getAgents, AgentInfo } from '@/lib/api'
export default function AgentsPage() {
 const [agents, setAgents] = useState<Record<string, AgentInfo> | null>(null)
 useEffect(() => { getAgents().then(setAgents).catch(() => setAgents({})) }, [])
 const count = agents ? Object.keys(agents).length : null
 const stats = [[Brain, count ?? '—', 'Agents disponibles'], [TrendUp, '5', 'Critères de scoring'], [Lightning, '3', 'Niveaux de mémoire']] as const
 return <AppShell><PageHeader eyebrow="Registre" title="Sous-agents" description="Les spécialistes disponibles et leur capacité de routage, dans un seul poste de contrôle." actions={<StatusBadge tone="success">Routage actif</StatusBadge>} /><div className="mb-6 grid gap-4 md:grid-cols-3">{stats.map(([Icon, value, label]) => <Panel key={label} className="p-5"><Icon size={20} style={{ color: 'var(--accent)' }} /><strong className="mt-5 block font-mono text-3xl">{value}</strong><span className="mt-1 block text-sm" style={{ color: 'var(--text-muted)' }}>{label}</span></Panel>)}</div>{agents === null ? <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{Array.from({ length: 8 }, (_, i) => <Panel key={i} className="h-60 animate-pulse p-5" />)}</div> : count ? <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{Object.entries(agents).map(([name, info], index) => <AgentCard key={name} name={name} info={info} index={index} />)}</div> : <EmptyState title="Aucun agent disponible" description="Le registre n'a pas pu être chargé. Vérifie que le backend est actif, puis actualise la page." />}</AppShell>
}
