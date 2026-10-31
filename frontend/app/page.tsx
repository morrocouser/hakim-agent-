"use client";

import React, { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowDownRight,
  Check,
  Clipboard,
  Copy,
  Cpu,
  Globe,
  Layers3,
  Menu,
  ShieldAlert,
  Terminal,
  X,
  ExternalLink,
  GitBranch,
  Database,
  Boxes,
  Sparkles,
  Zap,
  ArrowRight,
  TrendingUp,
  Layers,
  Code2,
  Compass,
  RefreshCw,
  CreditCard,
} from "lucide-react";

import GlassCard, { InteractiveButton, MetricCard } from "@/components/GlassCard";

const productName = "HakimAgent";

const metricCards: { metric: string; title: string; detail: string }[] = [
  { metric: "0 ms", title: "Telemetry overhead", detail: "Tourne en local sans télémétrie ni appel externe forcé." },
  { metric: "Strict DAG", title: "Execution", detail: "Graphe orienté acyclique avec typage statique (pyright strict)." },
  { metric: "asyncio", title: "Parallélisme", detail: "Isolation des contextes d'agents via tâches async sans blocage." },
  { metric: "SQLite", title: "Persistance", detail: "Historique des runs et état des mémoires indexés en local." },
];

const navigationItems = [
  { label: "Tarifs & Pro", href: "/pricing" },
  { label: "Installation", href: "#installation" },
  { label: "Utilisation", href: "#utilisation" },
  { label: "Architecture", href: "#architecture" },
  { label: "Comparatif", href: "#comparatif" },
  { label: "Limites + tests", href: "#limites-tests" },
] as const;

const envManagers = ["uv", "Poetry", "pip"] as const;

const installCommand = `cd /home/ubuntu/hakim-agent
python3 -m venv .venv
. .venv/bin/activate
pip install hakimagent`;

const environmentCommand = `export OPENAI_API_KEY="..."
export OPENAI_API_BASE="..."

# Affiner le routage par modèle
export HAKIM_MODEL_CRITICAL="claude-3-7-sonnet"
export HAKIM_MODEL_ADVANCED="claude-3-5-haiku"
export HAKIM_MODEL_STANDARD="ollama/qwen2.5-coder"
export HAKIM_MODEL_FAST="ollama/llama3.1"`;

const cliCommand = `hakimagent "Explique le problème et propose un plan de correction"
hakimagent --json "Analyse ce fichier CSV et donne les tendances principales"
cat demande.txt | hakimagent`;

const httpCommand = `uvicorn hakim_agent.api:app --host 127.0.0.1 --port 8000

curl http://127.0.0.1:8000/health

curl -X POST http://127.0.0.1:8000/run \\
  -H 'Content-Type: application/json' \\
  -d '{"prompt":"Conçois une architecture pour une API FastAPI"}'`;

const architectureTree = [
  { depth: 0, icon: "📁", name: "backend/", note: "" },
  { depth: 1, icon: "📁", name: "core/", note: "" },
  { depth: 2, icon: "📄", name: "score.py", note: "Routage déterministe & scoring" },
  { depth: 2, icon: "📄", name: "router.py", note: "Dispatch parallèle asynchrone" },
  { depth: 2, icon: "📄", name: "reflexion.py", note: "Boucle d'évaluation bornée (max 3)" },
  { depth: 1, icon: "📁", name: "memory/", note: "" },
  { depth: 2, icon: "📄", name: "store.py", note: "Persistance SQLite + Vector embeddings" },
  { depth: 1, icon: "📁", name: "tools/", note: "" },
  { depth: 2, icon: "📄", name: "sandbox.py", note: "Isolation du système de fichiers" },
  { depth: 1, icon: "📄", name: "api/server.py", note: "Serveur REST FastAPI (port 8000)" },
];

const comparisonRows: [string, string, string][] = [
  ["Routage", "Déterministe par scoring", "Heuristique cachée"],
  ["Cloud", "Zéro dépendance externe", "Backend propriétaire requis"],
  ["Mémoire", "Locale, typée, SQL", "Opaque, verrouillé"],
  ["Parallélisme", "Tâches asyncio natives", "Séquentiel par défaut"],
  ["Audit", "Logs de décision bruts", "Boîte noire"],
];

const runtimeOptions = envManagers;

const dagCode = `import { createWorkflow, RouterAgent, MemoryLayer, CodeExecutor } from "hakimagent";

const pipeline = createWorkflow({
  router: RouterAgent,        // routage déterministe
  memory: MemoryLayer,        // persistance SQLite
  executors: [CodeExecutor],  // exécution parallèle
});

await pipeline.run(prompt);  // streaming de la réponse`;

const dagTerm = [
  '$ hakimagent run "Résume ce dépôt et propose 3 issues"',
  "",
  "→ RouterAgent        scoring 0.94   dispatch (3 ms)",
  "→ Scraper   ·········· OK  (12 ms)  fork",
  "→ Analyzer  ·········· OK  (48 ms)  join",
  "→ Writer    ·········· OK  (21 ms)  stream",
  "",
  "✓ synthèse prête         overhead mémoire 3.1 MB",
  "✓ persistance SQLite     0 cloud call",
];


function CodePanel({
  title,
  code,
}: {
  title: string;
  code: string;
}) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="code-panel">
      <div className="code-panel__bar">
        <span className="code-panel__index">{title}</span>
        <button
          className="copy-button"
          onClick={() => {
            navigator.clipboard?.writeText(code);
            setCopied(true);
            setTimeout(() => setCopied(false), 1800);
          }}
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          {copied ? "COPIÉ" : "COPIER"}
        </button>
      </div>
      <pre className="code-panel pre">{code}</pre>
    </div>
  );
}

function PipelineVisualizer() {
  const [tab, setTab] = useState<"dag" | "code" | "term">("dag");
  const tabs = [
    { id: "dag", label: "Visual DAG" },
    { id: "code", label: "TypeScript" },
    { id: "term", label: "Terminal" },
  ] as const;

  return (
    <div className="pipeline">
      <div className="pipeline__bar">
        <div className="pipeline__dots">
          <span />
          <span />
          <span />
        </div>
        <span className="pipeline__file">pipeline.trace.ts</span>
        <span className="pipeline__meta">
          <Cpu size={14} className="text-indigo-400" />
          3 sous-agents actifs · 12 ms
        </span>
      </div>

      <div className="pipeline__tabs" role="tablist" aria-label="Aperçu du pipeline">
        {tabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            className="pipeline__tab"
            data-active={tab === t.id}
            onClick={() => setTab(t.id)}
          >
            {t.label}
            {tab === t.id && (
              <motion.span
                layoutId="pipeline-tab-glow"
                className="pipeline__tab-glow"
                transition={{ type: "spring", stiffness: 380, damping: 30 }}
              />
            )}
          </button>
        ))}
      </div>

      <div className="pipeline__body">
        <AnimatePresence mode="wait">
          {tab === "dag" && (
            <motion.div
              key="dag"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.22 }}
              className="dag"
            >
              <div className="dag__node">
                <span className="ic">
                  <Terminal size={16} />
                </span>
                <span className="meta">
                  <b>Input Node</b>
                  <small>prompt utilisateur</small>
                </span>
              </div>
              <div className="dag__edge dag__edge--v" />
              <div className="dag__node">
                <span className="ic">
                  <GitBranch size={16} />
                </span>
                <span className="meta">
                  <b>RouterAgent</b>
                  <small>scoring 0.94 · dispatch 3 ms</small>
                </span>
              </div>
              <div className="dag__connector">
                <div className="dag__edge" />
                <div className="dag__edge" />
                <div className="dag__edge" />
              </div>
              <div className="dag__branches">
                <div className="dag__branch">
                  <div className="dag__node">
                    <span className="ic">
                      <Globe size={16} />
                    </span>
                    <span className="meta">
                      <b>Scraper</b>
                      <small>OK · 12 ms</small>
                    </span>
                  </div>
                </div>
                <div className="dag__branch">
                  <div className="dag__node">
                    <span className="ic">
                      <Boxes size={16} />
                    </span>
                    <span className="meta">
                      <b>Analyzer</b>
                      <small>OK · 48 ms</small>
                    </span>
                  </div>
                </div>
                <div className="dag__branch">
                  <div className="dag__node">
                    <span className="ic">
                      <Layers3 size={16} />
                    </span>
                    <span className="meta">
                      <b>Writer</b>
                      <small>OK · 21 ms</small>
                    </span>
                  </div>
                </div>
              </div>
              <div className="dag__edge dag__edge--v" />
              <div className="dag__node">
                <span className="ic">
                  <Database size={16} />
                </span>
                <span className="meta">
                  <b>Synthèse + Stream</b>
                  <small>SQLite · 0 cloud call</small>
                </span>
              </div>
            </motion.div>
          )}

          {tab === "code" && (
            <motion.pre
              key="code"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.22 }}
              className="pipeline__code"
            >
              <span className="com">// Graphe de décision typé</span>
              {"\n"}
              <span className="kw">import</span> {"{ createWorkflow, RouterAgent, MemoryLayer, CodeExecutor }"}{" "}
              <span className="kw">from</span> <span className="str">"hakimagent"</span>;
              {"\n\n"}
              <span className="kw">const</span> pipeline = <span className="fn">createWorkflow</span>({"{"}
              {"\n"} router: RouterAgent,{"        "}
              <span className="com">{"// routage déterministe"}</span>
              {"\n"} memory: MemoryLayer,{"        "}
              <span className="com">{"// persistance SQLite"}</span>
              {"\n"} executors: [CodeExecutor],{"   "}
              <span className="com">{"// exécution parallèle"}</span>
              {"\n"} {"});"}
              {"\n\n"}
              <span className="kw">await</span> pipeline.<span className="fn">run</span>(prompt);{"  "}
              <span className="com">{"// streaming de la réponse"}</span>
            </motion.pre>
          )}

          {tab === "term" && (
            <motion.div
              key="term"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.22 }}
              className="pipeline__term"
            >
              {dagTerm.map((line, i) => {
                const ok = line.startsWith("✓");
                const arrow = line.startsWith("→");
                return (
                  <div key={i} className={ok ? "ok" : ""}>
                    {arrow && <span className="ok">{"→ "}</span>}
                    {arrow ? line.slice(2) : line}
                  </div>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default function Home() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [runtime, setRuntime] = useState<(typeof envManagers)[number]>("uv");
  const [copied, setCopied] = useState(false);
  const closeMenu = () => setMobileMenuOpen(false);

  const copyCommand = () => {
    navigator.clipboard?.writeText("uv add hakimagent");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="landing" id="top">
      {/* ─── 1. TOPBAR ─── */}
      <header className="topbar">
        <a className="wordmark" href="#top" aria-label="Retour en haut HakimAgent">
          <span className="wordmark__mark">H</span>
          <span>{productName}</span>
        </a>

        <nav className="desktop-nav" aria-label="Navigation principale">
          {navigationItems.map((item) => (
            <a key={item.href} href={item.href}>
              {item.label}
            </a>
          ))}
          <Link href="/coworkers" className="text-xs font-semibold text-[var(--accent)] hover:underline">
            Coworkers
          </Link>
          <Link href="/audit" className="text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
            Audit
          </Link>
          <Link href="/chat" className="nav-cta">
            <span>▶</span>OUVRIR L'AGENT
          </Link>
        </nav>

        <button
          className="menu-button"
          type="button"
          aria-label={mobileMenuOpen ? "Fermer le menu" : "Ouvrir le menu"}
          aria-expanded={mobileMenuOpen}
          onClick={() => setMobileMenuOpen((open) => !open)}
        >
          {mobileMenuOpen ? <X size={24} strokeWidth={3} /> : <Menu size={24} strokeWidth={3} />}
        </button>
      </header>

      {mobileMenuOpen && (
        <nav className="mobile-nav" aria-label="Navigation mobile">
          {navigationItems.map((item) => (
            <a key={item.href} href={item.href} onClick={closeMenu}>
              {item.label}
            </a>
          ))}
          <Link href="/coworkers" onClick={closeMenu}>
            Coworkers (OpenBot)
          </Link>
          <Link href="/audit" onClick={closeMenu}>
            Audit & Gouvernance
          </Link>
          <Link href="/chat" onClick={closeMenu} className="nav-cta" style={{ color: "#fff", textDecoration: "none" }}>
            <span>▶</span>OUVRIR L'AGENT
          </Link>
        </nav>
      )}

      <main id="main-content">
      {/* ─── 2. HERO ─── */}
      <section className="hero" aria-labelledby="hero-title">
        <div className="hero__inner">
          <p className="eyebrow">ORCHESTRATEUR MULTI-AGENTS · OPEN SOURCE</p>
          <h1 id="hero-title">
            Orchestrez vos agents IA locaux
            <br />
            en Python asynchrone.
          </h1>
          <p className="hero__description">
            Un moteur d'orchestration local, typé de bout en bout, pour faire tourner des équipes d'agents sans dépendre d'un cloud propriétaire.
          </p>

          {/* Dock unifié : gestionnaire d'env + commande + copier */}
          <div className="hero__dock">
            <div className="dock-runtime" role="group" aria-label="Gestionnaire d'environnement">
              {runtimeOptions.map((r) => (
                <button
                  key={r}
                  className="dock-runtime__btn"
                  data-active={runtime === r}
                  onClick={() => setRuntime(r)}
                >
                  {r}
                </button>
              ))}
            </div>

            <div className="dock-sep" />

            <div className="cmd-bar">
              <span className="prompt">$</span>
              <span>uv add hakimagent</span>
              <button className="cmd-bar__copy" onClick={copyCommand} aria-label="Copier la commande">
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? "COPIÉ" : "COPIER"}
              </button>
            </div>

            <Link href="#installation" className="btn-doc">
              <span>Explorer la doc</span>
              <ExternalLink size={16} strokeWidth={2.5} />
            </Link>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 my-6">
            <Link
              href="/chat"
              className="inline-flex items-center gap-2.5 px-6 py-3 rounded-lg bg-[#cc785c] hover:bg-[#a9583e] text-white font-medium text-sm tracking-normal shadow-sm transition-all transform hover:-translate-y-0.5 cursor-pointer"
            >
              <Sparkles size={16} className="text-white" />
              <span>Ouvrir l'Interface de l'Agent</span>
              <ArrowRight size={14} className="text-white" />
            </Link>
            <Link
              href="/pricing"
              className="inline-flex items-center gap-2.5 px-6 py-3 rounded-lg bg-[var(--surface-soft)] hover:bg-[var(--surface)] text-[var(--text-primary)] border border-[var(--border)] font-medium text-sm tracking-normal shadow-sm transition-all transform hover:-translate-y-0.5 cursor-pointer"
            >
              <CreditCard size={16} className="text-[#cc785c]" />
              <span>Tarifs & Abonnements</span>
            </Link>
          </div>

          <div className="metric-grid" aria-label="Métriques d'ingénierie HakimAgent">
            {metricCards.map((m) => (
              <div key={m.title} className="metric-card">
                <span className="metric-card__value">{m.metric}</span>
                <strong className="metric-card__title">{m.title}</strong>
                <span className="metric-card__detail">{m.detail}</span>
              </div>
            ))}
          </div>

          <PipelineVisualizer />
        </div>
      </section>

      {/* ─── 3. INSTALLATION ─── */}
      <section id="installation" className="doc-section" aria-labelledby="install-title">
        <div className="section-kicker">
          <span className="eyebrow">DÉPLOIEMENT RAPIDE</span>
        </div>

        <div className="section-heading">
          <h2 id="install-title">
            Installation
          </h2>
          <p>
            Mise en place de l'environnement virtuel Python 3.11+, activation et configuration des variables d'environnement.
          </p>
        </div>

        <div className="code-stack">
          <CodePanel title="1. Configuration de l'environnement" code={installCommand} />
          <CodePanel title="2. Variables d'environnement & Modèles" code={environmentCommand} />
        </div>

        <div className="memory-note">
          <ShieldAlert size={20} className="shrink-0" color="var(--accent)" />
          <p>
            <strong>Note de sécurité :</strong> Pour un environnement isolé, définissez <code>HAKIM_WORKSPACE_DIR</code> sur un répertoire dédié afin d'activer la sandbox automatique des outils de fichiers.
          </p>
        </div>
      </section>

      {/* ─── 4. UTILISATION ─── */}
      <section id="utilisation" className="doc-section" aria-labelledby="usage-title">
        <div className="section-kicker">
          <span className="eyebrow">MODES D'EXÉCUTION</span>
        </div>

        <div className="section-heading">
          <h2 id="usage-title">
            Utilisation
          </h2>
          <p>
            Interagissez directement via la ligne de commande (CLI REPL) ou l'API REST FastAPI.
          </p>
        </div>

        <div className="usage-layout">
          <div className="usage-label">
            <div>
              <Terminal size={24} strokeWidth={2.5} />
              <span>TERMINAL / CLI REPL</span>
            </div>
            <h3>CLI</h3>
            <p>Exécution instantanée en terminal avec rendu Rich et commandes slash (/compact, /undo, /skills).</p>
          </div>
          <CodePanel title="Commandes Terminal & REPL" code={cliCommand} />

          <div className="usage-label">
            <div>
              <Clipboard size={24} strokeWidth={2.5} />
              <span>SERVEUR HTTP / REST API</span>
            </div>
            <h3>API</h3>
            <p>Serveur Uvicorn / FastAPI exposant les routes /chat, /score, /commands et /skills sur le port 8000.</p>
          </div>
          <CodePanel title="Démarrage & Requêtes API HTTP" code={httpCommand} />
        </div>
      </section>

      {/* ─── 5. ARCHITECTURE ─── */}
      <section id="architecture" className="doc-section" aria-labelledby="arch-title">
        <div className="section-kicker">
          <span className="eyebrow">ANATOMIE DU SYSTÈME</span>
        </div>

        <div className="section-heading">
          <h2 id="arch-title">
            Architecture du système
          </h2>
          <p>
            Découpage modulaire du moteur d'orchestration sous <code>backend/hakim_agent/</code>.
          </p>
        </div>

        <div className="architecture-stamp" style={{ marginBottom: 8 }}>
          <Layers3 size={24} strokeWidth={2} />
          <span>ARCHITECTURE MODULAIRE · 8 SOUS-AGENTS</span>
        </div>

        <div className="tree-view" role="tree" aria-label="Arborescence du backend HakimAgent">
          {architectureTree.map((node, i) => (
            <div key={i} className="tree-row" style={{ paddingLeft: `${node.depth * 22 + 8}px` }}>
              <span className="tree-icon">{node.icon}</span>
              <code className="tree-name">{node.name}</code>
              {node.note && <span className="tree-note">{node.note}</span>}
            </div>
          ))}
        </div>
      </section>

      {/* ─── 6. COMPARATIF ─── */}
      <section id="comparatif" className="doc-section" aria-labelledby="comp-title">
        <div className="section-kicker">
          <span className="eyebrow">BENCHMARK TECHNIQUE</span>
        </div>

        <div className="section-heading">
          <h2 id="comp-title">
            Comparatif
          </h2>
          <p>
            Analyse comparative de l'architecture HakimAgent par rapport aux assistants de code standards du marché.
          </p>
        </div>

        <div className="architecture-table" role="table" aria-label="Tableau comparatif">
          <div className="architecture-table__head" role="row" style={{ gridTemplateColumns: "180px 1fr 1fr" }}>
            <span role="columnheader">PILIER</span>
            <span role="columnheader">HAKIMAGENT (NOTRE AGENT)</span>
            <span role="columnheader">AUTRES ASSISTANTS (CLAUDE CODE / CURSOR)</span>
          </div>
          {comparisonRows.map(([pillar, hakimDesc, othersDesc]) => (
            <div
              key={pillar}
              className="architecture-table__row"
              role="row"
              style={{ gridTemplateColumns: "180px 1fr 1fr" }}
            >
              <strong role="cell" style={{ color: "var(--accent)", fontSize: "13px" }}>{pillar}</strong>
              <span role="cell" style={{ fontSize: "14px", fontWeight: 700 }}>{hakimDesc}</span>
              <span role="cell" style={{ fontSize: "13px", color: "var(--text-muted)" }}>{othersDesc}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ─── 7. LIMITES & TESTS ─── */}
      <section id="limites-tests" className="doc-section" aria-labelledby="tests-title">
        <div className="section-kicker">
          <span className="eyebrow">VALIDATION &amp; QUALITÉ</span>
        </div>

        <div className="section-heading">
          <h2 id="tests-title">
            Tests & limites
          </h2>
          <p>
            Validation automatisée : 100% type-checked (pyright strict) et 48 tests unitaires & benchmarks passés. Garde-fous stricts contre les hallucinations.
          </p>
        </div>

        <div className="limits-grid">
          <div className="limit-card">
            <div className="tag">GARDE-FOU #01</div>
            <h3>Réflexion Bornée (Max 3 passes)</h3>
            <p>La boucle de réflexion s'arrête après 3 itérations pour éviter les boucles infinies et limiter le coût.</p>
          </div>
          <div className="limit-card">
            <div className="tag">GARDE-FOU #02</div>
            <h3>Sandbox de Fichiers</h3>
            <p>Les outils de fichiers sont restreints à <code>HAKIM_WORKSPACE_DIR</code> quand défini, isolant l'exécution.</p>
          </div>
          <div className="limit-card">
            <div className="tag">GARDE-FOU #03</div>
            <h3>Logging de Décision</h3>
            <p>Chaque routage est tracé et auditable, sans boîte noire, pour comprendre le comportement de l'agent.</p>
          </div>
        </div>
      </section>

      </main>

      {/* ─── 8. FOOTER ─── */}
      <footer className="footer">
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span className="wordmark__mark" style={{ width: 30, height: 30 }}>H</span>
          <span style={{ fontWeight: 800, fontSize: "16px", letterSpacing: "-0.02em" }}>{productName}</span>
          <span style={{ fontSize: "12px", fontFamily: "ui-monospace, monospace", color: "var(--text-muted)" }}>· Orchestrateur IA</span>
        </div>

        <div style={{ display: "flex", gap: "24px", fontSize: "13px", fontWeight: 600 }}>
          <a href="#top">HAUT DE PAGE ↑</a>
          <Link href="/agent">OUVRIR WEB IDE ↗</Link>
        </div>

        <p style={{ margin: 0, fontSize: "12px", color: "var(--text-muted)" }}>
          Système Orchestrateur Multi-Agents · Tous droits réservés.
        </p>
      </footer>
    </div>
  );
}
