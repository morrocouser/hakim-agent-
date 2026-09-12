'use client'

import { Sun, Moon } from '@phosphor-icons/react'

interface Props {
  isDark: boolean
  onToggle: () => void
  compact?: boolean
}

export default function ThemeToggle({ isDark, onToggle, compact }: Props) {
  return (
    <button
      onClick={onToggle}
      className="theme-pill"
      aria-label={isDark ? 'Passer en mode clair' : 'Passer en mode sombre'}
    >
      {isDark ? (
        <>
          <Sun className="w-3.5 h-3.5 text-yellow-400" weight="fill" />
          {!compact && <span>Clair</span>}
        </>
      ) : (
        <>
          <Moon className="w-3.5 h-3.5" weight="fill" />
          {!compact && <span>Sombre</span>}
        </>
      )}
    </button>
  )
}
