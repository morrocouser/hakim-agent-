'use client'

import { useEffect, useState, type ReactNode } from 'react'
import Link from 'next/link'
import { List, X, SidebarSimple } from '@phosphor-icons/react'
import Sidebar from './Sidebar'

const links = [
  ['/', 'Accueil'],
  ['/agents', 'Agents'],
  ['/coworkers', 'Coworkers'],
  ['/audit', 'Gouvernance'],
  ['/memory', 'Mémoire'],
  ['/chat', 'Chat'],
  ['/tools', 'Outils'],
]

export default function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  // Persistance de l'état de la barre latérale
  useEffect(() => {
    try {
      const saved = localStorage.getItem('hakim_sidebar_collapsed')
      if (saved !== null) {
        setCollapsed(saved === 'true')
      }
    } catch {
      // Ignorer si localStorage non disponible
    }
  }, [])

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      const next = !prev
      try {
        localStorage.setItem('hakim_sidebar_collapsed', String(next))
      } catch {}
      return next
    })
  }

  useEffect(() => {
    const close = (event: KeyboardEvent) => event.key === 'Escape' && setOpen(false)
    window.addEventListener('keydown', close)
    return () => window.removeEventListener('keydown', close)
  }, [])

  return (
    <div className="app-shell flex min-h-[100dvh]">
      {/* Sidebar Desktop */}
      <div className="hidden lg:block">
        <Sidebar collapsed={collapsed} onToggleCollapse={toggleCollapsed} />
      </div>

      {/* Main Content Area */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Topbar ultra-épurée */}
        <header className="app-topbar flex items-center justify-between px-4 lg:px-6 h-12 border-b border-[var(--border)] bg-[var(--canvas)]/90 backdrop-blur-md sticky top-0 z-30">
          <div className="flex items-center gap-3">
            {/* Bouton mobile */}
            <button
              type="button"
              className="lg:hidden p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)] cursor-pointer"
              aria-label="Ouvrir la navigation"
              onClick={() => setOpen(true)}
            >
              <List size={20} />
            </button>

            {/* Bouton Desktop pour déplier la sidebar si collapsed */}
            {collapsed && (
              <button
                type="button"
                onClick={toggleCollapsed}
                className="hidden lg:flex p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)] cursor-pointer transition-colors"
                title="Déplier la barre latérale"
                aria-label="Déplier la barre latérale"
              >
                <SidebarSimple size={18} />
              </button>
            )}
          </div>

          {/* Statut unique miniature et discret */}
          <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[11px] tracking-wide text-[var(--text-muted)]">Opérationnel</span>
          </div>
        </header>

        {/* Corps principal */}
        <main className="app-main flex-1 overflow-y-auto">
          <div className="app-content h-full">{children}</div>
        </main>
      </div>

      {/* Mobile Drawer */}
      {open && (
        <>
          <button
            type="button"
            className="mobile-nav-backdrop"
            aria-label="Fermer la navigation"
            onClick={() => setOpen(false)}
          />
          <aside
            id="mobile-navigation"
            className="mobile-nav"
            role="dialog"
            aria-label="Navigation principale"
          >
            <div className="mb-6 flex items-center justify-between">
              <strong className="text-sm font-normal text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-display)' }}>HakimAgent</strong>
              <button
                type="button"
                className="p-1 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                aria-label="Fermer la navigation"
                onClick={() => setOpen(false)}
              >
                <X size={20} />
              </button>
            </div>
            <nav className="flex flex-col gap-1">
              {links.map(([href, label]) => (
                <Link
                  key={href}
                  href={href}
                  onClick={() => setOpen(false)}
                  className="px-3 py-2 rounded-xl text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)] transition-colors"
                >
                  {label}
                </Link>
              ))}
            </nav>
          </aside>
        </>
      )}
    </div>
  )
}
