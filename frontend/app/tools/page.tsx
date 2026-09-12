'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import AppShell from '@/components/AppShell'
import PageHeader from '@/components/PageHeader'
import { Panel } from '@/components/ui-kit'
import { Wrench, MagnifyingGlass, Play, FileText, Bug } from '@phosphor-icons/react'
import { webSearch, executeCode, createFile, getErrors, logError } from '@/lib/api'

export default function ToolsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState('')
  const [codeLang, setCodeLang] = useState('python')
  const [codeInput, setCodeInput] = useState('')
  const [codeOutput, setCodeOutput] = useState('')
  const [filePath, setFilePath] = useState('')
  const [fileContent, setFileContent] = useState('')
  const [errors, setErrors] = useState<any[]>([])
  const [status, setStatus] = useState('')

  const handleSearch = async () => {
    setStatus('Recherche...')
    try {
      const res: any = await webSearch(searchQuery)
      const content = typeof res.results === 'string' ? res.results : JSON.stringify(res.results, null, 2)
      setSearchResults(content)
      setStatus('Terminé')
    } catch (e: any) {
      setStatus(e.message)
    }
  }

  const handleRun = async () => {
    setStatus('Exécution...')
    try {
      const res: any = await executeCode(codeLang, codeInput)
      setCodeOutput(typeof res.output === 'string' ? res.output : JSON.stringify(res.output, null, 2))
      setStatus('Terminé')
    } catch (e: any) {
      setStatus(e.message)
    }
  }

  const handleCreateFile = async () => {
    if (!filePath) {
      setStatus('Chemin requis')
      return
    }
    setStatus('Création...')
    try {
      const res: any = await createFile(filePath, fileContent)
      setStatus(typeof res.result === 'string' ? res.result : 'Fichier créé')
      setFilePath('')
      setFileContent('')
    } catch (e: any) {
      setStatus(e.message)
    }
  }

  const loadErrors = async () => {
    try {
      const res: any = await getErrors()
      setErrors(res.errors || [])
    } catch (e: any) {
      setStatus((e as Error).message)
    }
  }

  const handleLogError = async () => {
    const symptom = prompt('Symptôme de l\'erreur:')
    if (!symptom) return
    const cause = prompt('Cause racine:')
    if (!cause) return
    const fix = prompt('Fix appliqué:')
    if (!fix) return
    try {
      await logError({
        tier: 1,
        agent: 'AGENT_CODER',
        context: 'manuel',
        symptom,
        root_cause: cause,
        fix,
        lesson: '',
        score: 6,
      })
      setStatus('Erreur loggée')
      loadErrors()
    } catch (e: any) {
      setStatus((e as Error).message)
    }
  }

  return (
    <AppShell>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-[1200px] mx-auto space-y-6"
        >
          <PageHeader eyebrow="Atelier" title="Outils" description="Recherche, exécution, fichiers et journal d'erreurs." />

          <div className="grid grid-cols-12 gap-5">
            {/* Search */}
            <Panel className="col-span-12 p-5 lg:col-span-6">
              <div className="flex items-center gap-2 mb-3">
                <MagnifyingGlass className="w-4 h-4 text-axiom-accent" />
                <h2 className="text-sm font-medium">Recherche Web</h2>
              </div>
              <div className="flex gap-2">
                <input
                  className="input-axiom flex-1"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Rechercher sur le web..."
                />
                <button className="btn-primary" onClick={handleSearch}>Rechercher</button>
              </div>
              {searchResults && (
                <pre className="mt-3 p-3 rounded-xl bg-axiom-dark border border-axiom-border text-xs whitespace-pre-wrap">
                  {searchResults}
                </pre>
              )}
            </Panel>

            {/* Code execution */}
            <Panel className="col-span-12 p-5 lg:col-span-6">
              <div className="flex items-center gap-2 mb-3">
                <Play className="w-4 h-4 text-axiom-accent" />
                <h2 className="text-sm font-medium">Exécuteur de Code</h2>
              </div>
              <div className="flex gap-2 mb-2">
                <select
                  className="input-axiom"
                  value={codeLang}
                  onChange={(e) => setCodeLang(e.target.value)}
                >
                  <option value="python">Python</option>
                  <option value="javascript">JavaScript</option>
                  <option value="bash">Bash</option>
                  <option value="sql">SQL (simulation)</option>
                </select>
              </div>
              <textarea
                className="input-axiom h-28 font-mono text-xs"
                value={codeInput}
                onChange={(e) => setCodeInput(e.target.value)}
                placeholder="Code..."
              />
              <div className="flex justify-end mt-2">
                <button className="btn-primary" onClick={handleRun}>Exécuter</button>
              </div>
              {codeOutput && (
                <pre className="mt-3 p-3 rounded-xl bg-axiom-dark border border-axiom-border text-xs whitespace-pre-wrap">
                  {codeOutput}
                </pre>
              )}
            </Panel>

            {/* File creation */}
            <Panel className="col-span-12 p-5 lg:col-span-6">
              <div className="flex items-center gap-2 mb-3">
                <FileText className="w-4 h-4 text-axiom-accent" />
                <h2 className="text-sm font-medium">Création de Fichier</h2>
              </div>
              <input
                className="input-axiom mb-2"
                value={filePath}
                onChange={(e) => setFilePath(e.target.value)}
                placeholder="ex: src/app/utils.ts"
              />
              <textarea
                className="input-axiom h-24 font-mono text-xs"
                value={fileContent}
                onChange={(e) => setFileContent(e.target.value)}
                placeholder="Contenu du fichier..."
              />
              <div className="flex justify-end mt-2">
                <button className="btn-primary" onClick={handleCreateFile}>Créer</button>
              </div>
            </Panel>

            {/* Error log */}
            <Panel className="col-span-12 p-5 lg:col-span-6">
              <div className="flex items-center gap-2 mb-3">
                <Bug className="w-4 h-4 text-axiom-accent" />
                <h2 className="text-sm font-medium">Error Log</h2>
                <div className="ml-auto flex gap-2">
                  <button className="btn-ghost text-xs" onClick={loadErrors}>Actualiser</button>
                  <button className="btn-ghost text-xs" onClick={handleLogError}>Logger une erreur</button>
                </div>
              </div>
              <div className="space-y-2 max-h-64 overflow-auto">
                {errors.length === 0 && <p className="text-xs text-axiom-muted">Aucune erreur enregistrée.</p>}
                {errors.map((e) => (
                  <div key={e.id} className="p-3 rounded-xl bg-axiom-dark border border-axiom-border text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-mono text-axiom-text">{e.id}</span>
                      <span className="text-axiom-muted">score {e.score}</span>
                    </div>
                    <div className="text-axiom-muted mb-1">{e.symptom}</div>
                    <div className="text-axiom-subtle whitespace-pre-wrap">{e.root_cause}</div>
                  </div>
                ))}
              </div>
            </Panel>
          </div>

          {status && (
            <div className="text-xs font-mono text-axiom-muted border-t border-axiom-border pt-3">
              {status}
            </div>
          )}
        </motion.div>
    </AppShell>
  )
}
