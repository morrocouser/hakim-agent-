'use client'

import React, { useState } from 'react'
import {
  Database,
  Search,
  Plus,
  Trash2,
  Sparkles,
  Layers,
  CheckCircle2,
  Brain,
  HardDrive,
} from 'lucide-react'

interface MemoryItem {
  id: string
  category: 'architecture' | 'decision' | 'stack' | 'rule'
  text: string
  createdAt: string
}

const defaultMemories: MemoryItem[] = [
  {
    id: 'mem-1',
    category: 'architecture',
    text: 'HakimAgent utilise un pipeline DAG asynchrone avec validation statique pyright et isolation des contextes.',
    createdAt: 'Hier, 16:40',
  },
  {
    id: 'mem-2',
    category: 'decision',
    text: 'Privilégier le routage déterministe par scoring algorithmique (qualité, complexité, coût) plutôt que le tout-LLM.',
    createdAt: 'Il y a 3 jours',
  },
  {
    id: 'mem-3',
    category: 'stack',
    text: 'Backend : FastAPI + SQLite vectoriel. Frontend : Next.js 16 + React 19 + Tailwind v4 + Framer Motion.',
    createdAt: '12 Sept 2026',
  },
  {
    id: 'mem-4',
    category: 'rule',
    text: 'Toute modification sur les fichiers de production requiert la validation humaine ou le mode Take The Wheel.',
    createdAt: '01 Oct 2026',
  },
]

export default function HermesMemoryPanel() {
  const [memories, setMemories] = useState<MemoryItem[]>(defaultMemories)
  const [searchQuery, setSearchQuery] = useState('')
  const [showAddForm, setShowAddForm] = useState(false)
  const [newText, setNewText] = useState('')
  const [newCategory, setNewCategory] = useState<MemoryItem['category']>('decision')

  const filteredMemories = memories.filter(
    (m) =>
      m.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.category.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newText.trim()) return

    const newItem: MemoryItem = {
      id: `mem-${Date.now()}`,
      category: newCategory,
      text: newText.trim(),
      createdAt: "À l'instant",
    }
    setMemories([newItem, ...memories])
    setNewText('')
    setShowAddForm(false)
  }

  const handleDelete = (id: string) => {
    setMemories(memories.filter((m) => m.id !== id))
  }

  const getCategoryBadge = (cat: MemoryItem['category']) => {
    switch (cat) {
      case 'architecture':
        return (
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-500/15 text-blue-400 border border-blue-500/20">
            ARCHITECTURE
          </span>
        )
      case 'decision':
        return (
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-400 border border-amber-500/20">
            DÉCISION
          </span>
        )
      case 'stack':
        return (
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-500/15 text-purple-400 border border-purple-500/20">
            STACK
          </span>
        )
      case 'rule':
        return (
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
            RÈGLE
          </span>
        )
    }
  }

  return (
    <div className="flex flex-col h-full bg-neutral-950/60 overflow-hidden text-neutral-200">
      {/* Top Stats Banner */}
      <div className="p-3 border-b border-white/5 bg-neutral-900/40">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-neutral-200">
            <Brain className="w-4 h-4 text-purple-400" />
            <span>Mémoire Persistante Hermes</span>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
            Active · SQLite
          </span>
        </div>

        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="p-1.5 rounded-lg bg-black/40 border border-white/5">
            <span className="block text-[10px] text-neutral-500">Faits</span>
            <span className="text-xs font-mono font-bold text-neutral-200">{memories.length}</span>
          </div>
          <div className="p-1.5 rounded-lg bg-black/40 border border-white/5">
            <span className="block text-[10px] text-neutral-500">Tokens</span>
            <span className="text-xs font-mono font-bold text-emerald-400">1,420</span>
          </div>
          <div className="p-1.5 rounded-lg bg-black/40 border border-white/5">
            <span className="block text-[10px] text-neutral-500">Vecteurs</span>
            <span className="text-xs font-mono font-bold text-cyan-400">Indexés</span>
          </div>
        </div>
      </div>

      {/* Search & Add Bar */}
      <div className="p-2.5 border-b border-white/5 flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-neutral-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Rechercher dans la mémoire..."
            className="w-full pl-8 pr-2.5 py-1 rounded-lg bg-neutral-900 border border-white/10 text-xs text-neutral-200 placeholder-neutral-500 focus:outline-none focus:border-purple-500/50"
          />
        </div>
        <button
          type="button"
          onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center gap-1 px-2 py-1 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-medium transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Ajouter</span>
        </button>
      </div>

      {/* Add Form Drawer */}
      {showAddForm && (
        <form onSubmit={handleAdd} className="p-3 bg-neutral-900/90 border-b border-white/10 space-y-2">
          <div className="flex items-center justify-between text-xs font-medium text-neutral-300">
            <span>Nouveau fait de mémoire :</span>
            <select
              value={newCategory}
              onChange={(e) => setNewCategory(e.target.value as MemoryItem['category'])}
              className="bg-neutral-800 border border-white/10 rounded px-1.5 py-0.5 text-xs text-neutral-200"
            >
              <option value="decision">Décision</option>
              <option value="architecture">Architecture</option>
              <option value="stack">Stack</option>
              <option value="rule">Règle</option>
            </select>
          </div>
          <textarea
            value={newText}
            onChange={(e) => setNewText(e.target.value)}
            placeholder="Ex: Le timeout par défaut pour les appels API est de 30 secondes..."
            rows={2}
            className="w-full p-2 rounded-lg bg-neutral-950 border border-white/10 text-xs text-neutral-200 placeholder-neutral-500 focus:outline-none focus:border-purple-500/50"
          />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowAddForm(false)}
              className="px-2 py-1 rounded text-xs text-neutral-400 hover:text-white"
            >
              Annuler
            </button>
            <button
              type="submit"
              className="px-3 py-1 rounded bg-purple-600 hover:bg-purple-500 text-white text-xs font-medium"
            >
              Enregistrer
            </button>
          </div>
        </form>
      )}

      {/* Memory Cards Feed */}
      <div className="flex-1 overflow-y-auto p-2.5 space-y-2">
        {filteredMemories.length === 0 ? (
          <div className="py-8 text-center text-xs text-neutral-500">
            Aucun fait de mémoire trouvé.
          </div>
        ) : (
          filteredMemories.map((item) => (
            <div
              key={item.id}
              className="p-3 rounded-xl bg-neutral-900/70 border border-white/5 hover:border-white/10 transition-colors group"
            >
              <div className="flex items-center justify-between mb-1.5">
                {getCategoryBadge(item.category)}
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-neutral-500">{item.createdAt}</span>
                  <button
                    type="button"
                    onClick={() => handleDelete(item.id)}
                    className="opacity-0 group-hover:opacity-100 p-0.5 rounded text-neutral-500 hover:text-red-400 transition-opacity"
                    title="Oublier ce fait"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
              <p className="text-xs text-neutral-300 leading-relaxed font-sans select-text">
                {item.text}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
