'use client'

import React, { useState } from 'react'
import {
  Zap,
  Search,
  Globe,
  Shield,
  Terminal,
  Brain,
  FolderOpen,
  ArrowRight,
  CheckCircle2,
  Lock,
  Sparkles,
  Layout,
  Palette,
} from 'lucide-react'

interface SkillItem {
  id: string
  name: string
  category: 'web' | 'security' | 'devops' | 'ai' | 'system' | 'web_builder' | 'agency'
  categoryLabel: string
  description: string
  tools: string[]
  permission: 'ALLOWED' | 'FAIL_CLOSED' | 'HUMAN_TAKEOVER'
  coworkers: string[]
  samplePrompt: string
}

interface SkillsCatalogViewProps {
  onSelectPrompt?: (prompt: string) => void
}

export default function SkillsCatalogView({ onSelectPrompt }: SkillsCatalogViewProps) {
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  const skills: SkillItem[] = [
    {
      id: 'browser_navigator',
      name: 'Navigation & Extraction Web',
      category: 'web',
      categoryLabel: 'Web & Recherche',
      description: 'Pilotage complet du navigateur virtuel, extraction de texte, navigation multi-pages et interaction formulaires.',
      tools: ['browser_navigate', 'browser_click', 'browser_type', 'extract_content'],
      permission: 'HUMAN_TAKEOVER',
      coworkers: ['Alex Browser'],
      samplePrompt: 'Navigue vers https://docs.github.com et résume la documentation de l’API',
    },
    {
      id: 'web_search_engine',
      name: 'Recherche Web en Direct',
      category: 'web',
      categoryLabel: 'Web & Recherche',
      description: 'Recherche instantanée d’informations d’actualité et documentation en ligne sans interruption de session.',
      tools: ['web_search', 'serp_lookup'],
      permission: 'ALLOWED',
      coworkers: ['Alex Browser', 'APEX Orchestrator'],
      samplePrompt: 'Recherche les dernières actualités sur Next.js 16 et React 19',
    },
    {
      id: 'security_governance',
      name: 'Gouvernance Fail-Closed CEL',
      category: 'security',
      categoryLabel: 'Sécurité & CEL',
      description: 'Filtrage strict pré-exécution avec disjoncteur automatique et règles de rejet des actions destructives.',
      tools: ['policy_eval', 'security_scan', 'fail_closed_guard'],
      permission: 'FAIL_CLOSED',
      coworkers: ['Sentinel SecOps'],
      samplePrompt: 'Exécute un audit de sécurité complet des dépendances',
    },
    {
      id: 'audit_ledger_crypto',
      name: 'Registre d’Audit Immuable',
      category: 'security',
      categoryLabel: 'Sécurité & CEL',
      description: 'Journalisation cryptographique chaînée en SHA-256 de chaque outil appelé et décision de politique.',
      tools: ['audit_lookup', 'audit_append', 'verify_chain'],
      permission: 'ALLOWED',
      coworkers: ['Sentinel SecOps'],
      samplePrompt: 'Affiche les 10 dernières actions enregistrées dans le registre d’audit',
    },
    {
      id: 'shell_execution',
      name: 'Terminal & Commandes Sandboxed',
      category: 'devops',
      categoryLabel: 'DevOps & Shell',
      description: 'Exécution supervisée de scripts bash, compilations TypeScript et utilitaires locaux dans user_files.',
      tools: ['shell_exec', 'process_runner'],
      permission: 'FAIL_CLOSED',
      coworkers: ['Marcus DevOps'],
      samplePrompt: 'Exécute un test de compilation du projet Next.js',
    },
    {
      id: 'file_manager_workspace',
      name: 'Gestionnaire de Fichiers Dédié',
      category: 'system',
      categoryLabel: 'Système & Fichiers',
      description: 'Opérations de lecture, écriture et navigation sécurisées limitées au répertoire workspace de chaque agent.',
      tools: ['file_read', 'file_write', 'dir_list'],
      permission: 'ALLOWED',
      coworkers: ['Marcus DevOps', 'Alex Browser'],
      samplePrompt: 'Liste les fichiers présents dans mon répertoire de travail',
    },
    {
      id: 'react_reasoning',
      name: 'Raisonnement ReAct & Auto-Critique',
      category: 'ai',
      categoryLabel: 'Raisonnement & IA',
      description: 'Boucle réflexive Thought-Action-Observation avec notation de qualité dynamique et repli de modèle automatique.',
      tools: ['react_loop', 'self_critique', 'scoring_route'],
      permission: 'ALLOWED',
      coworkers: ['APEX Orchestrator'],
      samplePrompt: 'Rédige un plan d’architecture pour un système multi-agents autonome',
    },
    {
      id: 'error_recovery_5tiers',
      name: 'Protocole Résilience 5-Tiers',
      category: 'system',
      categoryLabel: 'Système & Fichiers',
      description: 'Système d’auto-guérison : Prévention, Auto-correction, Clarification, Dégradation gracieuse et Escalade.',
      tools: ['error_protocol', 'circuit_breaker', 'memory_lesson'],
      permission: 'ALLOWED',
      coworkers: ['Sentinel SecOps', 'APEX Orchestrator'],
      samplePrompt: 'Vérifie l’état de santé des services et du disjoncteur d’API',
    },
    {
      id: 'web_scaffolding',
      name: 'Générateur de Sites Web Complets',
      category: 'web_builder',
      categoryLabel: 'Création Web & Sites',
      description: 'Conception et génération de sites web complets, responsives et modernes avec HTML5, Tailwind CSS et animations fluides.',
      tools: ['web_scaffold', 'web_generate_page', 'export_website'],
      permission: 'ALLOWED',
      coworkers: ['Elena WebCraft'],
      samplePrompt: 'Crée un site vitrine moderne pour une agence digitale avec hero section, portfolio et formulaire de contact',
    },
    {
      id: 'component_builder',
      name: 'Constructeur de Composants UI',
      category: 'web_builder',
      categoryLabel: 'Création Web & Sites',
      description: 'Création de blocs modulaires : navbar glassmorphic, grilles de fonctionnalités, cartes tarifaires interactives et footers.',
      tools: ['component_builder', 'tailwind_styler'],
      permission: 'ALLOWED',
      coworkers: ['Elena WebCraft'],
      samplePrompt: 'Génère un composant de tarification avec 3 formules (Starter, Pro, Entreprise) avec design Tailwind',
    },
    {
      id: 'web_preview_engine',
      name: 'Prévisualisation & Rendu Web Live',
      category: 'web_builder',
      categoryLabel: 'Création Web & Sites',
      description: 'Compilation instantanée et affichage direct du prototype web dans l’écran virtuel de l’agent sans outil externe.',
      tools: ['web_preview', 'screen_render', 'dom_snapshot'],
      permission: 'ALLOWED',
      coworkers: ['Elena WebCraft'],
      samplePrompt: 'Prévisualise le site web dans l’écran virtuel et vérifie le responsive design',
    },
    {
      id: 'agency_code_reviewer',
      name: 'Agency Code Reviewer',
      category: 'agency',
      categoryLabel: 'Agency Agents (267)',
      description: 'Expert en revue de code : justesse, sécurité, maintenabilité et performance. Explications pédagogiques et suggestions actionnables.',
      tools: ['code_review', 'security_scan', 'git_diff', 'refactor_check'],
      permission: 'ALLOWED',
      coworkers: ['Alex Code Reviewer'],
      samplePrompt: 'Revois le code de cette pull request et identifie les failles de sécurité, bugs et régressions potentielles',
    },
    {
      id: 'agency_software_architect',
      name: 'Agency Software Architect',
      category: 'agency',
      categoryLabel: 'Agency Agents (267)',
      description: 'Architecte logiciel : systèmes modulaires, patterns distribués, fiches de décision ADR et scalabilité.',
      tools: ['architecture_design', 'system_specs', 'adr_writer', 'mermaid_graph'],
      permission: 'ALLOWED',
      coworkers: ['Atlas Software Architect'],
      samplePrompt: 'Conçois une architecture distribuée résiliente avec microservices et file de messages',
    },
    {
      id: 'agency_security_auditor',
      name: 'Agency Security Auditor',
      category: 'agency',
      categoryLabel: 'Agency Agents (267)',
      description: 'Audit de sécurité applicative, modélisation de menaces STRIDE, contrôles OWASP Top 10 et audit de dépendances.',
      tools: ['security_scan', 'policy_eval', 'threat_modeling', 'cve_check'],
      permission: 'FAIL_CLOSED',
      coworkers: ['Cipher Security Auditor'],
      samplePrompt: 'Exécute un audit de sécurité approfondi des endpoints de l’API et des dépendances npm / pip',
    },
    {
      id: 'agency_prompt_engineer',
      name: 'Agency Prompt Engineer',
      category: 'agency',
      categoryLabel: 'Agency Agents (267)',
      description: 'Ingénierie de prompts haute précision, évaluation des benchmarks LLM, few-shot tuning et réduction de coûts de tokens.',
      tools: ['prompt_eval', 'few_shot_tuner', 'token_optimizer', 'benchmark_test'],
      permission: 'ALLOWED',
      coworkers: ['Nova Prompt Engineer'],
      samplePrompt: 'Optimise le prompt système pour réduire les hallucinations et garantir des sorties JSON strictes',
    },
    {
      id: 'agency_growth_hacker',
      name: 'Agency Growth Hacker',
      category: 'agency',
      categoryLabel: 'Agency Agents (267)',
      description: 'Stratégies de croissance rapide, boucles virales, entonnoirs d’acquisition et optimisation du taux de conversion (CRO).',
      tools: ['funnel_analysis', 'cro_testing', 'growth_loops', 'analytics_audit'],
      permission: 'ALLOWED',
      coworkers: ['Blaze Growth Hacker'],
      samplePrompt: 'Élabore une stratégie d’acquisition et un tunnel de conversion viral pour un SaaS',
    },
  ]

  const categories = [
    { id: 'all', label: 'Toutes les compétences' },
    { id: 'agency', label: 'Agency Agents (267)' },
    { id: 'web_builder', label: 'Création Web & Sites' },
    { id: 'web', label: 'Web & Recherche' },
    { id: 'security', label: 'Sécurité & CEL' },
    { id: 'devops', label: 'DevOps & Shell' },
    { id: 'ai', label: 'Raisonnement & IA' },
    { id: 'system', label: 'Système' },
  ]

  const filteredSkills = skills.filter((s) => {
    const matchesCategory = selectedCategory === 'all' || s.category === selectedCategory
    const q = search.toLowerCase()
    const matchesSearch =
      s.name.toLowerCase().includes(q) ||
      s.description.toLowerCase().includes(q) ||
      s.tools.some((t) => t.toLowerCase().includes(q)) ||
      s.coworkers.some((c) => c.toLowerCase().includes(q))
    return matchesCategory && matchesSearch
  })

  const getPermissionBadge = (perm: SkillItem['permission']) => {
    switch (perm) {
      case 'ALLOWED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 size={11} />
            <span>Autorisé</span>
          </span>
        )
      case 'FAIL_CLOSED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <Shield size={11} />
            <span>Fail-Closed</span>
          </span>
        )
      case 'HUMAN_TAKEOVER':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Lock size={11} />
            <span>Prise en main dispo</span>
          </span>
        )
    }
  }

  const getCategoryIcon = (cat: SkillItem['category']) => {
    switch (cat) {
      case 'web_builder':
        return <Layout size={16} className="text-cyan-400" />
      case 'web':
        return <Globe size={16} className="text-blue-400" />
      case 'security':
        return <Shield size={16} className="text-emerald-400" />
      case 'devops':
        return <Terminal size={16} className="text-amber-400" />
      case 'ai':
        return <Brain size={16} className="text-purple-400" />
      case 'system':
        return <FolderOpen size={16} className="text-neutral-400" />
    }
  }

  return (
    <div className="flex-1 h-full overflow-y-auto px-4 sm:px-8 py-6 max-w-5xl mx-auto w-full space-y-6">
      {/* 1. Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-neutral-800/60">
        <div>
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-[var(--accent)]" />
            <h2 className="text-base font-semibold text-neutral-100">Catalogue des Compétences & Outils</h2>
          </div>
          <p className="text-xs text-neutral-400 mt-1">
            Chaque coworker est équipé de compétences spécialisées régies par la passerelle de gouvernance Fail-Closed.
          </p>
        </div>

        {/* Barre de recherche */}
        <div className="relative min-w-[240px]">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500" />
          <input
            type="text"
            placeholder="Rechercher un outil, commande..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-neutral-900 border border-neutral-800 text-xs text-neutral-200 placeholder:text-neutral-500 focus:outline-hidden focus:border-neutral-600 transition"
          />
        </div>
      </div>

      {/* 2. Filtres par catégorie */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        {categories.map((c) => (
          <button
            key={c.id}
            onClick={() => setSelectedCategory(c.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition cursor-pointer ${
              selectedCategory === c.id
                ? 'bg-neutral-800 text-neutral-100 border border-neutral-700/60 shadow-xs'
                : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/40'
            }`}
          >
            {c.label}
          </button>
        ))}
      </div>

      {/* 3. Grille des Skills */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredSkills.map((skill) => (
          <div
            key={skill.id}
            className="p-5 rounded-2xl bg-neutral-900/50 border border-neutral-800/70 hover:border-neutral-700/80 transition-all flex flex-col justify-between group space-y-4"
          >
            {/* Haut de carte */}
            <div className="space-y-2">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-xl bg-neutral-800/80 border border-neutral-700/50 shrink-0">
                    {getCategoryIcon(skill.category)}
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-neutral-100 group-hover:text-white transition-colors">
                      {skill.name}
                    </h3>
                    <span className="text-[11px] text-neutral-500">{skill.categoryLabel}</span>
                  </div>
                </div>

                {getPermissionBadge(skill.permission)}
              </div>

              <p className="text-xs text-neutral-400 leading-relaxed pt-1">
                {skill.description}
              </p>
            </div>

            {/* Outils & Agents assignés */}
            <div className="space-y-3 pt-2 border-t border-neutral-800/60">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-[10px] text-neutral-500 font-mono uppercase mr-1">Outils :</span>
                {skill.tools.map((t, idx) => (
                  <span
                    key={idx}
                    className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-neutral-950 text-neutral-300 border border-neutral-800"
                  >
                    {t}
                  </span>
                ))}
              </div>

              <div className="flex items-center justify-between pt-1">
                <div className="flex items-center gap-1.5 text-xs text-neutral-400">
                  <Sparkles size={12} className="text-neutral-500" />
                  <span className="text-[11px]">{skill.coworkers.join(', ')}</span>
                </div>

                {onSelectPrompt && (
                  <button
                    type="button"
                    onClick={() => onSelectPrompt(skill.samplePrompt)}
                    className="flex items-center gap-1 text-xs text-neutral-300 hover:text-white hover:underline cursor-pointer group-hover:translate-x-0.5 transition-transform"
                    title={`Tester : "${skill.samplePrompt}"`}
                  >
                    <span>Tester</span>
                    <ArrowRight size={12} />
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
