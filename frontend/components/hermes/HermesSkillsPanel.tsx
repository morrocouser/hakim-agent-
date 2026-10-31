'use client'

import React, { useState } from 'react'
import {
  Zap,
  Search,
  Code2,
  Terminal,
  Globe,
  FileCode,
  ShieldCheck,
  Cpu,
  ArrowRight,
  ExternalLink,
} from 'lucide-react'

interface SkillItem {
  id: string
  name: string
  category: 'system' | 'web' | 'code' | 'security'
  description: string
  samplePrompt: string
}

const defaultSkills: SkillItem[] = [
  {
    id: 'skill-terminal',
    name: 'Exécution Terminal (Bash / PowerShell)',
    category: 'system',
    description: "Exécution de commandes shell sécurisées dans l'environnement local ou conteneurisé.",
    samplePrompt: "Liste les processus actifs et l'espace disque disponible sur le serveur.",
  },
  {
    id: 'skill-web',
    name: 'Navigation & Recherche Web',
    category: 'web',
    description: 'Scraping, recherche DuckDuckGo/Google et navigation headless avec gestion du DOM.',
    samplePrompt: 'Recherche les dernières mises à jour du framework Hermes Agent et résume-les.',
  },
  {
    id: 'skill-file',
    name: 'Gestionnaire de Fichiers & Code',
    category: 'code',
    description: 'Lecture, écriture, analyse de diffs et refactorisation de code TypeScript et Python.',
    samplePrompt: "Analyse le fichier backend/axiom/core/scoring.py et propose 3 optimisations de performance.",
  },
  {
    id: 'skill-audit',
    name: 'Audit de Sécurité & Gouvernance',
    category: 'security',
    description: 'Vérification de conformance OWASP, analyse statique de sécurité et isolation sandbox.',
    samplePrompt: "Lance un scan de sécurité sur les points d'entrée de l'API FastAPI.",
  },
  {
    id: 'skill-cron',
    name: 'Planificateur de Routines Autonomes',
    category: 'system',
    description: 'Gestion des crons récurrents, alertes système et tâches périodiques sans supervision.',
    samplePrompt: "Crée une tâche planifiée pour vérifier la santé de l'API toutes les 15 minutes.",
  },
]

interface HermesSkillsPanelProps {
  onSelectPrompt?: (prompt: string) => void
}

export default function HermesSkillsPanel({ onSelectPrompt }: HermesSkillsPanelProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  const filtered = defaultSkills.filter((s) => {
    const matchSearch =
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchCat = selectedCategory === 'all' || s.category === selectedCategory
    return matchSearch && matchCat
  })

  const getCategoryIcon = (cat: SkillItem['category']) => {
    switch (cat) {
      case 'system':
        return <Terminal className="w-3.5 h-3.5 text-emerald-400" />
      case 'web':
        return <Globe className="w-3.5 h-3.5 text-cyan-400" />
      case 'code':
        return <Code2 className="w-3.5 h-3.5 text-blue-400" />
      case 'security':
        return <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
    }
  }

  return (
    <div className="flex flex-col h-full bg-neutral-950/60 overflow-hidden text-neutral-200">
      {/* Top Banner */}
      <div className="p-3 border-b border-white/5 bg-neutral-900/40 flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-neutral-200">
          <Zap className="w-4 h-4 text-amber-400" />
          <span>Catalogue de Compétences</span>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
          {defaultSkills.length} actives
        </span>
      </div>

      {/* Filter & Search Bar */}
      <div className="p-2.5 border-b border-white/5 space-y-2">
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-neutral-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Rechercher une compétence..."
            className="w-full pl-8 pr-2.5 py-1 rounded-lg bg-neutral-900 border border-white/10 text-xs text-neutral-200 placeholder-neutral-500 focus:outline-none focus:border-amber-500/50"
          />
        </div>

        <div className="flex items-center gap-1 overflow-x-auto text-[11px]">
          {['all', 'system', 'web', 'code', 'security'].map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setSelectedCategory(cat)}
              className={`px-2 py-0.5 rounded-md capitalize transition-colors ${
                selectedCategory === cat
                  ? 'bg-amber-500/20 text-amber-300 font-medium'
                  : 'text-neutral-400 hover:text-white hover:bg-neutral-800'
              }`}
            >
              {cat === 'all' ? 'Toutes' : cat}
            </button>
          ))}
        </div>
      </div>

      {/* Skills List Feed */}
      <div className="flex-1 overflow-y-auto p-2.5 space-y-2">
        {filtered.map((skill) => (
          <div
            key={skill.id}
            className="p-3 rounded-xl bg-neutral-900/70 border border-white/5 hover:border-amber-500/30 transition-all group"
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5">
                <div className="p-1 rounded bg-black/40 border border-white/5">
                  {getCategoryIcon(skill.category)}
                </div>
                <h4 className="text-xs font-medium text-neutral-200 group-hover:text-amber-300 transition-colors">
                  {skill.name}
                </h4>
              </div>
            </div>

            <p className="text-[11px] text-neutral-400 leading-relaxed mb-2">
              {skill.description}
            </p>

            <button
              type="button"
              onClick={() => onSelectPrompt?.(skill.samplePrompt)}
              className="w-full flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg bg-white/5 hover:bg-amber-500/20 text-[11px] font-medium text-neutral-300 hover:text-amber-300 border border-white/5 hover:border-amber-500/30 transition-colors"
            >
              <span>Tester cette compétence</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
