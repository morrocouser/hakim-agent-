'use client'

import React, { useState, useEffect } from 'react'
import {
  Folder,
  FolderOpen,
  FileText,
  FileCode,
  FileJson,
  Search,
  RefreshCw,
  Copy,
  Check,
  Send,
  X,
  ChevronRight,
  ChevronDown,
  Terminal,
} from 'lucide-react'

interface FileNode {
  name: string
  path: string
  isDirectory: boolean
  children?: FileNode[]
  size?: string
}

// Initial workspace tree representing hakimagent
const initialFileTree: FileNode[] = [
  {
    name: 'backend',
    path: 'backend',
    isDirectory: true,
    children: [
      {
        name: 'axiom',
        path: 'backend/axiom',
        isDirectory: true,
        children: [
          { name: 'core', path: 'backend/axiom/core', isDirectory: true, children: [
            { name: 'scoring.py', path: 'backend/axiom/core/scoring.py', isDirectory: false, size: '7.8 Ko' },
            { name: 'react_loop.py', path: 'backend/axiom/core/react_loop.py', isDirectory: false, size: '9.4 Ko' },
            { name: 'memory.py', path: 'backend/axiom/core/memory.py', isDirectory: false, size: '6.2 Ko' },
          ]},
          { name: 'api', path: 'backend/axiom/api', isDirectory: true, children: [
            { name: 'main.py', path: 'backend/axiom/api/main.py', isDirectory: false, size: '7.2 Ko' },
            { name: 'routes.py', path: 'backend/axiom/api/routes.py', isDirectory: false, size: '19.6 Ko' },
            { name: 'conversation_routes.py', path: 'backend/axiom/api/conversation_routes.py', isDirectory: false, size: '6.3 Ko' },
            { name: 'openbot_routes.py', path: 'backend/axiom/api/openbot_routes.py', isDirectory: false, size: '7.0 Ko' },
          ]},
          { name: 'tools', path: 'backend/axiom/tools', isDirectory: true, children: [
            { name: 'file_manager.py', path: 'backend/axiom/tools/file_manager.py', isDirectory: false, size: '9.2 Ko' },
            { name: 'code_executor.py', path: 'backend/axiom/tools/code_executor.py', isDirectory: false, size: '5.1 Ko' },
            { name: 'web_search.py', path: 'backend/axiom/tools/web_search.py', isDirectory: false, size: '4.3 Ko' },
          ]},
        ],
      },
      { name: 'requirements.txt', path: 'backend/requirements.txt', isDirectory: false, size: '385 B' },
      { name: 'pyproject.toml', path: 'backend/pyproject.toml', isDirectory: false, size: '964 B' },
    ],
  },
  {
    name: 'frontend',
    path: 'frontend',
    isDirectory: true,
    children: [
      {
        name: 'app',
        path: 'frontend/app',
        isDirectory: true,
        children: [
          { name: 'layout.tsx', path: 'frontend/app/layout.tsx', isDirectory: false, size: '2.3 Ko' },
          { name: 'page.tsx', path: 'frontend/app/page.tsx', isDirectory: false, size: '25.0 Ko' },
          { name: 'chat', path: 'frontend/app/chat', isDirectory: true, children: [
            { name: 'page.tsx', path: 'frontend/app/chat/page.tsx', isDirectory: false, size: '32.6 Ko' },
          ]},
          { name: 'globals.css', path: 'frontend/app/globals.css', isDirectory: false, size: '54.4 Ko' },
        ],
      },
      {
        name: 'components',
        path: 'frontend/components',
        isDirectory: true,
        children: [
          { name: 'AppShell.tsx', path: 'frontend/components/AppShell.tsx', isDirectory: false, size: '4.8 Ko' },
          { name: 'Sidebar.tsx', path: 'frontend/components/Sidebar.tsx', isDirectory: false, size: '7.5 Ko' },
          { name: 'CronManagerView.tsx', path: 'frontend/components/CronManagerView.tsx', isDirectory: false, size: '21.6 Ko' },
        ],
      },
      { name: 'package.json', path: 'frontend/package.json', isDirectory: false, size: '844 B' },
    ],
  },
  {
    name: '.hermes',
    path: '.hermes',
    isDirectory: true,
    children: [
      {
        name: 'plans',
        path: '.hermes/plans',
        isDirectory: true,
        children: [
          { name: '2026-09-20_dropship-saas-mvp-plan.md', path: '.hermes/plans/2026-09-20_dropship-saas-mvp-plan.md', isDirectory: false, size: '20.1 Ko' },
        ],
      },
    ],
  },
  {
    name: 'skills',
    path: 'skills',
    isDirectory: true,
    children: [
      { name: 'SKILL.md', path: 'skills/SKILL.md', isDirectory: false, size: '3.4 Ko' },
    ],
  },
  { name: 'run.bat', path: 'run.bat', isDirectory: false, size: '3.0 Ko' },
  { name: 'LANCER.bat', path: 'LANCER.bat', isDirectory: false, size: '30 B' },
  { name: 'AXIOM_v4_MEGA_PROMPT.md', path: 'AXIOM_v4_MEGA_PROMPT.md', isDirectory: false, size: '47.6 Ko' },
]

// Mock file contents for preview
const mockFileContents: Record<string, string> = {
  'run.bat': `@echo off
chcp 65001 >nul
title HakimAgent - Lanceur Global
set "ROOT_DIR=%~dp0"
echo Démarrage du Backend FastAPI (Port 8000)...
start "Backend" cmd /k ".\backend\.venv\Scripts\python.exe -m uvicorn axiom.api.main:app --port 8000"
echo Démarrage du Frontend Next.js (Port 3000)...
start "Frontend" cmd /k "npm run dev"
echo Prêt sur http://localhost:3000`,

  'backend/axiom/core/scoring.py': `"""Scoring déterministe pour le routage d'agents APEX."""
from typing import Dict, Any

def score_and_route(prompt: str) -> Dict[str, Any]:
    # Évaluation de la complexité, du risque et de la vitesse requise
    is_code = any(kw in prompt.lower() for kw in ['code', 'python', 'def ', 'class '])
    return {
        "agent": "CodeExpert" if is_code else "GeneralAssistant",
        "model": "claude-3-7-sonnet" if is_code else "claude-3-5-haiku",
        "confidence": 0.94,
    }`,

  '.hermes/plans/2026-09-20_dropship-saas-mvp-plan.md': `# Plan de Développement Dropship SaaS MVP
- Date: 2026-09-20
- Agent: Hermes Planner
- Statut: En cours d'exécution

## Objectifs :
1. Architecture FastAPI asynchrone
2. Intégration SQLite persistante
3. Interface WebUI 3 panneaux réactive`,

  'frontend/package.json': `{
  "name": "axiom-frontend",
  "version": "4.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev --webpack -p 3000",
    "build": "next build"
  },
  "dependencies": {
    "next": "^16.2.12",
    "react": "^19.0.0",
    "framer-motion": "^12.40.0",
    "lucide-react": "^0.460.0"
  }
}`,
}

interface HermesFileViewerProps {
  onInsertIntoPrompt?: (content: string) => void
}

export default function HermesFileViewer({ onInsertIntoPrompt }: HermesFileViewerProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({
    backend: true,
    'backend/axiom': true,
    frontend: false,
    '.hermes': false,
  })
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState<string>('')
  const [copied, setCopied] = useState(false)

  const toggleFolder = (path: string) => {
    setExpandedFolders((prev) => ({ ...prev, [path]: !prev[path] }))
  }

  const handleSelectFile = (file: FileNode) => {
    if (file.isDirectory) {
      toggleFolder(file.path)
      return
    }

    setSelectedFile(file.path)
    const content =
      mockFileContents[file.path] ||
      `// Fichier : ${file.path}\n// Taille : ${file.size || 'Inconnue'}\n\n// Contenu chargé depuis le workspace HakimAgent\nexport const file_path = "${file.path}";\nconsole.log("Lecture du fichier synchronisée.");`
    setFileContent(content)
  }

  const handleCopyCode = () => {
    if (!fileContent) return
    navigator.clipboard?.writeText(fileContent)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleInsert = () => {
    if (!fileContent || !selectedFile) return
    const snippet = `\`\`\`${selectedFile.split('.').pop() || ''}\n// ${selectedFile}\n${fileContent}\n\`\`\``
    onInsertIntoPrompt?.(snippet)
  }

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase()
    if (ext === 'json') return <FileJson className="w-3.5 h-3.5 text-amber-400" />
    if (['ts', 'tsx', 'js', 'jsx'].includes(ext || '')) return <FileCode className="w-3.5 h-3.5 text-cyan-400" />
    if (ext === 'py') return <FileCode className="w-3.5 h-3.5 text-emerald-400" />
    if (ext === 'bat' || ext === 'sh') return <Terminal className="w-3.5 h-3.5 text-purple-400" />
    return <FileText className="w-3.5 h-3.5 text-neutral-400" />
  }

  const renderNode = (node: FileNode, level = 0) => {
    const isExpanded = !!expandedFolders[node.path]
    const isSelected = selectedFile === node.path

    if (
      searchQuery &&
      !node.name.toLowerCase().includes(searchQuery.toLowerCase()) &&
      (!node.children || !node.children.some((c) => c.name.toLowerCase().includes(searchQuery.toLowerCase())))
    ) {
      return null
    }

    return (
      <div key={node.path} className="select-none">
        <div
          onClick={() => handleSelectFile(node)}
          style={{ paddingLeft: `${level * 12 + 8}px` }}
          className={`flex items-center justify-between py-1 px-2 rounded-lg text-xs cursor-pointer transition-colors ${
            isSelected
              ? 'bg-amber-500/15 text-amber-300 font-medium'
              : 'text-neutral-300 hover:bg-white/5 hover:text-white'
          }`}
        >
          <div className="flex items-center gap-1.5 min-w-0">
            {node.isDirectory ? (
              <>
                {isExpanded ? (
                  <ChevronDown className="w-3 h-3 text-neutral-500 shrink-0" />
                ) : (
                  <ChevronRight className="w-3 h-3 text-neutral-500 shrink-0" />
                )}
                {isExpanded ? (
                  <FolderOpen className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                ) : (
                  <Folder className="w-3.5 h-3.5 text-amber-500/80 shrink-0" />
                )}
              </>
            ) : (
              <>
                <span className="w-3 shrink-0" />
                {getFileIcon(node.name)}
              </>
            )}
            <span className="truncate">{node.name}</span>
          </div>

          {!node.isDirectory && node.size && (
            <span className="text-[10px] font-mono text-neutral-500 shrink-0 ml-2">
              {node.size}
            </span>
          )}
        </div>

        {node.isDirectory && isExpanded && node.children && (
          <div>
            {node.children.map((child) => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-neutral-950/60 overflow-hidden text-neutral-200">
      {/* Search & Actions Bar */}
      <div className="p-2.5 border-b border-white/5 flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-neutral-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filtrer les fichiers..."
            className="w-full pl-8 pr-2.5 py-1 rounded-lg bg-neutral-900 border border-white/10 text-xs text-neutral-200 placeholder-neutral-500 focus:outline-none focus:border-amber-500/50"
          />
        </div>
        <button
          type="button"
          onClick={() => {
            setSearchQuery('')
            setSelectedFile(null)
          }}
          className="p-1.5 rounded-lg bg-neutral-900 border border-white/10 text-neutral-400 hover:text-neutral-200 transition-colors"
          title="Rafraîchir"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Main File Layout */}
      <div className="flex-1 flex flex-col min-h-0">
        {/* File Tree List */}
        <div className={`overflow-y-auto p-1.5 ${selectedFile ? 'h-44 border-b border-white/5' : 'flex-1'}`}>
          <div className="text-[10px] font-mono uppercase tracking-wider text-neutral-500 px-2 py-1 flex justify-between">
            <span>Workspace : hakimagent</span>
            <span>Local</span>
          </div>
          {initialFileTree.map((node) => renderNode(node))}
        </div>

        {/* Inline Code Viewer (when a file is clicked) */}
        {selectedFile && (
          <div className="flex-1 flex flex-col min-h-0 bg-neutral-950 border-t border-white/5">
            {/* Code Viewer Header */}
            <div className="flex items-center justify-between px-3 py-1.5 bg-neutral-900/90 border-b border-white/5">
              <div className="flex items-center gap-1.5 min-w-0">
                <FileCode className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                <span className="text-[11px] font-mono text-neutral-200 truncate">
                  {selectedFile}
                </span>
              </div>

              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={handleInsert}
                  className="p-1 rounded text-neutral-400 hover:text-amber-400 transition-colors"
                  title="Insérer dans le prompt"
                >
                  <Send className="w-3 h-3" />
                </button>
                <button
                  type="button"
                  onClick={handleCopyCode}
                  className="p-1 rounded text-neutral-400 hover:text-neutral-200 transition-colors"
                  title="Copier le code"
                >
                  {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedFile(null)}
                  className="p-1 rounded text-neutral-400 hover:text-neutral-200 transition-colors"
                  title="Fermer la prévisualisation"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            </div>

            {/* Code Editor Preview */}
            <div className="flex-1 overflow-auto p-2.5 font-mono text-[11px] text-neutral-300 leading-relaxed bg-black/70">
              <pre className="whitespace-pre">
                {fileContent.split('\n').map((line, idx) => (
                  <div key={idx} className="table-row">
                    <span className="table-cell pr-3 text-neutral-600 select-none text-right w-6">
                      {idx + 1}
                    </span>
                    <span className="table-cell">{line}</span>
                  </div>
                ))}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
