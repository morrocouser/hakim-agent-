'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  House,
  Brain,
  Database,
  ChatsCircle,
  Wrench,
  Gear,
  Users,
  ShieldCheck,
  SidebarSimple,
  Robot,
  CreditCard,
} from '@phosphor-icons/react'
import ThemeToggle from '@/components/ThemeToggle'
import { useThemeContext } from '@/components/ThemeProvider'
import { useAuth } from '@/contexts/AuthContext'

const NAV = [
  { href: '/', label: 'Accueil', icon: House },
  { href: '/chat', label: 'Chat Agent', icon: ChatsCircle },
  { href: '/agent', label: 'Studio IDE', icon: Robot },
  { href: '/agents', label: 'Catalogue', icon: Brain },
  { href: '/coworkers', label: 'Coworkers', icon: Users },
  { href: '/audit', label: 'Gouvernance', icon: ShieldCheck },
  { href: '/memory', label: 'Mémoire', icon: Database },
  { href: '/tools', label: 'Outils', icon: Wrench },
  { href: '/pricing', label: 'Tarifs & Pro', icon: CreditCard },
]

interface SidebarProps {
  collapsed?: boolean
  onToggleCollapse?: () => void
}

export default function Sidebar({ collapsed = false, onToggleCollapse }: SidebarProps) {
  const path = usePathname()
  const { isDark, toggleTheme } = useThemeContext()
  const { user } = useAuth()

  const userInitial = (user?.display_name || user?.username || 'U')[0].toUpperCase()

  return (
    <aside
      aria-label="Navigation principale"
      className={`h-[100dvh] sticky top-0 flex flex-col shrink-0 overflow-hidden z-40 transition-all duration-300 ease-in-out ${
        collapsed ? 'w-[68px]' : 'w-[250px]'
      }`}
      style={{
        background: 'var(--surface)',
        borderRight: '1px solid var(--border)',
      }}
    >
      {/* Header avec Logo et bouton Collapse */}
      <div className={`flex items-center pt-4 pb-3 ${collapsed ? 'justify-center px-2' : 'justify-between px-4'}`}>
        <Link href="/" className="flex items-center gap-2.5 group">
          <div
            className="flex items-center justify-center font-bold text-xs text-white bg-[#cc785c] shadow-xs"
            style={{ width: 28, height: 28, borderRadius: 7 }}
          >
            H
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span
                className="font-normal text-sm tracking-tight leading-tight"
                style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}
              >
                HakimAgent
              </span>
              <span className="text-[10px] text-[var(--text-muted)] font-mono">
                Claude Theme
              </span>
            </div>
          )}
        </Link>

        {onToggleCollapse && !collapsed && (
          <button
            type="button"
            onClick={onToggleCollapse}
            className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)] transition-colors cursor-pointer"
            title="Réduire la barre latérale"
            aria-label="Réduire la barre latérale"
          >
            <SidebarSimple size={18} />
          </button>
        )}
      </div>

      {/* Bouton pour ré-ouvrir quand collapsed */}
      {onToggleCollapse && collapsed && (
        <div className="flex justify-center pb-2">
          <button
            type="button"
            onClick={onToggleCollapse}
            className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)] transition-colors cursor-pointer"
            title="Agrandir la barre latérale"
            aria-label="Agrandir la barre latérale"
          >
            <SidebarSimple size={18} />
          </button>
        </div>
      )}

      {/* Navigation épurée — Claude warm editorial */}
      <nav className="flex flex-col gap-1 px-2.5 flex-1 mt-2" aria-label="Pages">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = path === href
          return (
            <Link
              key={href}
              href={href}
              title={collapsed ? label : undefined}
              className={`flex items-center gap-3 px-3 py-2 rounded-xl text-[13px] transition-all ${
                active
                  ? 'bg-[var(--surface-cream-strong)] text-[var(--text-primary)] font-medium shadow-xs'
                  : 'text-[var(--text-muted)] font-normal hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)]'
              } ${collapsed ? 'justify-center !px-0' : ''}`}
            >
              <Icon
                className="w-4 h-4 shrink-0"
                weight={active ? 'fill' : 'regular'}
                style={{ color: active ? 'var(--accent)' : 'inherit' }}
              />
              {!collapsed && <span className="truncate">{label}</span>}
              {!collapsed && active && (
                <div
                  className="ml-auto w-1.5 h-1.5 rounded-full"
                  style={{
                    background: 'var(--accent)',
                    boxShadow: '0 0 6px var(--accent-glow)',
                  }}
                />
              )}
            </Link>
          )
        })}
      </nav>

      {/* Footer minimaliste — espacement aéré sans chevauchement */}
      <div className="p-3 border-t border-[var(--border)] flex flex-col gap-2.5">
        {/* Badge profil utilisateur si connecté */}
        {user && !collapsed && (
          <div className="flex items-center gap-3 px-2 py-1.5 rounded-xl hover:bg-[var(--surface-soft)] transition-colors">
            <div className="w-6 h-6 rounded-full bg-[var(--surface-soft)] border border-[var(--border)] text-[var(--text-primary)] flex items-center justify-center text-xs font-medium uppercase shrink-0">
              {userInitial}
            </div>
            <div className="flex flex-col min-w-0 flex-1">
              <span className="text-xs font-medium text-[var(--text-primary)] truncate leading-tight">
                {user.display_name || user.username}
              </span>
              <span className="text-[10px] text-[var(--text-muted)] truncate font-mono">
                {user.email || 'Opérateur'}
              </span>
            </div>
          </div>
        )}

        {user && collapsed && (
          <div className="flex justify-center py-1" title={user.display_name || user.username}>
            <div className="w-6 h-6 rounded-full bg-[var(--surface-soft)] border border-[var(--border)] text-[var(--text-primary)] flex items-center justify-center text-xs font-medium uppercase shrink-0">
              {userInitial}
            </div>
          </div>
        )}

        {/* Ligne inférieure : Statut discret + Paramètres & Thème */}
        <div
          className={`flex items-center ${
            collapsed ? 'flex-col gap-3 justify-center' : 'justify-between px-2 pt-1'
          }`}
        >
          {/* Statut API discret */}
          <div
            className="flex items-center gap-2 text-xs text-[var(--text-muted)]"
            title="API connectée sur localhost:8000"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shrink-0" />
            {!collapsed && (
              <span className="text-[11px] text-[var(--text-muted)] font-mono truncate">
                Connecté
              </span>
            )}
          </div>

          {/* Outils : Paramètres & Theme */}
          <div className="flex items-center gap-2">
            <button
              className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-soft)] transition-colors cursor-pointer"
              title="Paramètres"
              aria-label="Paramètres"
            >
              <Gear className="w-4 h-4" />
            </button>
            <ThemeToggle isDark={isDark} onToggle={toggleTheme} compact />
          </div>
        </div>
      </div>
    </aside>
  )
}
