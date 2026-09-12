'use client'

import { useEffect, useState, type ReactNode } from 'react'
import Link from 'next/link'
import { List, X, Pulse } from '@phosphor-icons/react'
import Sidebar from './Sidebar'

const links = [['/', 'Accueil'], ['/agents', 'Agents'], ['/memory', 'Mémoire'], ['/chat', 'Chat'], ['/tools', 'Outils']]

export default function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false)
  useEffect(() => { const close = (event: KeyboardEvent) => event.key === 'Escape' && setOpen(false); window.addEventListener('keydown', close); return () => window.removeEventListener('keydown', close) }, [])
  return <div className="app-shell flex"><div className="hidden lg:block"><Sidebar /></div><div className="flex min-w-0 flex-1 flex-col"><header className="app-topbar flex items-center justify-between px-5 lg:px-8"><button type="button" className="lg:hidden sidebar-item !w-auto" aria-label="Ouvrir la navigation" aria-expanded={open} aria-controls="mobile-navigation" onClick={() => setOpen(true)}><List size={22} /></button><div className="hidden items-center gap-2 text-xs sm:flex" style={{ color: 'var(--text-muted)' }}><Pulse size={14} style={{ color: 'var(--success)' }} />Système opérationnel</div></header><main className="app-main"><div className="app-content">{children}</div></main></div>{open && <><button type="button" className="mobile-nav-backdrop" aria-label="Fermer la navigation" onClick={() => setOpen(false)} /><aside id="mobile-navigation" className="mobile-nav" role="dialog" aria-label="Navigation principale"><div className="mb-8 flex items-center justify-between"><strong>HakimAgent</strong><button type="button" className="sidebar-item !w-auto" aria-label="Fermer la navigation" onClick={() => setOpen(false)}><X size={20} /></button></div><nav>{links.map(([href, label]) => <Link key={href} href={href} onClick={() => setOpen(false)}>{label}</Link>)}</nav></aside></>}</div>
}
