'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  House, Brain, Database, ChatsCircle, Wrench, Gear
} from '@phosphor-icons/react'
import ThemeToggle from '@/components/ThemeToggle'
import { useThemeContext } from '@/components/ThemeProvider'

const NAV = [
  { href: '/', label: 'Accueil', icon: House },
  { href: '/agents', label: 'Agents', icon: Brain },
  { href: '/memory', label: 'Mémoire', icon: Database },
  { href: '/chat', label: 'Chat', icon: ChatsCircle },
  { href: '/tools', label: 'Outils', icon: Wrench },
]

export default function Sidebar() {
  const path = usePathname()
  const { isDark, toggleTheme } = useThemeContext()

  return (
    <aside
      aria-label="Navigation principale"
      className="w-[260px] h-[100dvh] sticky top-0 flex flex-col shrink-0 overflow-hidden z-40"
      style={{
        background: 'var(--surface)',
        borderRight: '1.5px solid var(--border)',
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 pt-5 pb-4">
        <div className="logo-mark" style={{ width: 34, height: 34, borderRadius: 9 }}>H</div>
        <div>
          <div
            className="font-bold text-sm tracking-wide"
            style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}
          >
            HakimAgent
          </div>
          <div className="text-mono" style={{ color: 'var(--accent)', fontSize: 10 }}>
            APEX v4.0
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-0.5 px-3 flex-1" aria-label="Pages">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = path === href
          return (
            <Link
              key={href}
              href={href}
              className={`sidebar-item ${active ? 'active' : ''}`}
            >
              <Icon
                className="w-4 h-4 shrink-0"
                weight={active ? 'fill' : 'regular'}
              />
              {label}
              {active && (
                <div
                  className="ml-auto w-1.5 h-1.5 rounded-full"
                  style={{
                    background: 'var(--accent)',
                    boxShadow: '0 0 6px var(--accent)',
                  }}
                />
              )}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 space-y-3" style={{ borderTop: '1.5px solid var(--border)' }}>
        {/* API Status */}
        <div
          className="rounded-xl p-3.5"
          style={{
            background: 'var(--bg-tertiary)',
            border: '1.5px solid var(--border)',
          }}
        >
          <div className="flex items-center gap-2 text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse-emerald" />
            API connectée
          </div>
          <div className="text-mono mt-1" style={{ color: 'var(--text-muted)', fontSize: 10 }}>
            localhost:8000
          </div>
        </div>

        <div className="flex items-center justify-between">
          <button
            className="sidebar-item"
            style={{ width: 'auto', padding: '8px 12px' }}
            title="Paramètres"
            aria-label="Paramètres"
          >
            <Gear className="w-4 h-4" />
            <span className="text-xs">Paramètres</span>
          </button>
          <ThemeToggle isDark={isDark} onToggle={toggleTheme} compact />
        </div>
      </div>
    </aside>
  )
}
