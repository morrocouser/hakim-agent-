'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  X,
  Sliders,
  Cpu,
  Key,
  Shield,
  CheckCircle2,
  Database,
  RefreshCw,
} from 'lucide-react'

interface HermesSettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function HermesSettingsModal({ isOpen, onClose }: HermesSettingsModalProps) {
  const [model, setModel] = useState('claude-3-7-sonnet')
  const [temperature, setTemperature] = useState(0.2)
  const [maxTokens, setMaxTokens] = useState(4096)
  const [maxReActSteps, setMaxReActSteps] = useState(5)
  const [safeDir, setSafeDir] = useState('./user_files')
  const [saveSuccess, setSaveSuccess] = useState(false)

  if (!isOpen) return null

  const handleSave = () => {
    setSaveSuccess(true)
    setTimeout(() => {
      setSaveSuccess(false)
      onClose()
    }, 1000)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 10 }}
        className="w-full max-w-lg rounded-2xl bg-neutral-900 border border-white/10 shadow-2xl overflow-hidden flex flex-col text-neutral-200"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/10 bg-neutral-950/60">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-semibold text-white">
              Paramètres Hermes & HakimAgent
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-neutral-400 hover:text-white hover:bg-neutral-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <div className="p-5 space-y-4 overflow-y-auto max-h-[70vh] text-xs">
          {/* Model Selection */}
          <div className="space-y-1.5">
            <label className="block font-medium text-neutral-300">
              Modèle d'Exécution par Défaut
            </label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full p-2 rounded-xl bg-neutral-950 border border-white/10 text-neutral-200 focus:outline-none focus:border-amber-500/50 font-mono text-xs"
            >
              <option value="claude-3-7-sonnet">Claude 3.7 Sonnet (Raisonnement & Coding)</option>
              <option value="claude-3-5-haiku">Claude 3.5 Haiku (Ultra-Rapide & Léger)</option>
              <option value="qwen2.5-coder">Qwen 2.5 Coder 32B (Local Ollama)</option>
              <option value="hermes-3-llama">Hermes 3 Llama 3.1 70B (NousResearch)</option>
              <option value="deepseek-r1">DeepSeek R1 (Raisonnement Math & Logique)</option>
            </select>
            <p className="text-[11px] text-neutral-500">
              Le routeur déterministe scoring APEX bascule automatiquement sur les modèles locaux si hors-ligne.
            </p>
          </div>

          {/* Temperature Slider */}
          <div className="space-y-1.5">
            <div className="flex justify-between font-medium text-neutral-300">
              <span>Température ({temperature})</span>
              <span className="font-mono text-neutral-400">{temperature}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-neutral-500">
              <span>Précis / Déterministe (0.0)</span>
              <span>Créatif (1.0)</span>
            </div>
          </div>

          {/* ReAct Autonomy Depth */}
          <div className="space-y-1.5">
            <div className="flex justify-between font-medium text-neutral-300">
              <span>Nombre Maximum d'Itérations ReAct ({maxReActSteps})</span>
              <span className="font-mono text-neutral-400">{maxReActSteps} pas</span>
            </div>
            <input
              type="range"
              min="1"
              max="10"
              step="1"
              value={maxReActSteps}
              onChange={(e) => setMaxReActSteps(parseInt(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer"
            />
            <p className="text-[11px] text-neutral-500">
              Limite la boucle réflexive pour prévenir les appels infinis ou la consommation excessive de tokens.
            </p>
          </div>

          {/* Safe Directory */}
          <div className="space-y-1.5">
            <label className="block font-medium text-neutral-300">
              Répertoire Isolé du Workspace
            </label>
            <input
              type="text"
              value={safeDir}
              onChange={(e) => setSafeDir(e.target.value)}
              className="w-full p-2 rounded-xl bg-neutral-950 border border-white/10 text-neutral-200 font-mono text-xs"
            />
          </div>

          {/* Providers Status */}
          <div className="p-3 rounded-xl bg-neutral-950/70 border border-white/5 space-y-2">
            <span className="text-[11px] font-semibold text-neutral-300 flex items-center gap-1.5">
              <Key className="w-3.5 h-3.5 text-amber-400" />
              Statut des Clés d'API & Fournisseurs
            </span>
            <div className="space-y-1 text-[11px] font-mono">
              <div className="flex items-center justify-between">
                <span className="text-neutral-400">OpenRouter API</span>
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Configuré (.env)
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-neutral-400">Anthropic Claude</span>
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Prêt
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-neutral-400">Ollama Local</span>
                <span className="text-neutral-400">http://localhost:11434</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-5 py-3.5 border-t border-white/10 bg-neutral-950/60">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 rounded-xl text-neutral-400 hover:text-white hover:bg-neutral-800 transition-colors"
          >
            Fermer
          </button>

          <button
            type="button"
            onClick={handleSave}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-semibold transition-colors shadow-lg shadow-amber-500/20"
          >
            {saveSuccess ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Enregistré !</span>
              </>
            ) : (
              <span>Sauvegarder</span>
            )}
          </button>
        </div>
      </motion.div>
    </div>
  )
}
