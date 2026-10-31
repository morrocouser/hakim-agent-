'use client'

import { useEffect, useState, createContext, useContext, ReactNode } from 'react'

type ThemeContextType = {
  isDark: boolean
  toggleTheme: () => void
  setIsDark: (dark: boolean) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [isDark, setIsDark] = useState(false)

  const applyTheme = (dark: boolean) => {
    if (typeof window !== 'undefined') {
      document.documentElement.classList.toggle('dark', dark)
      document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
      try {
        localStorage.setItem('claude_theme_mode', dark ? 'dark' : 'light')
      } catch {}
    }
  }

  useEffect(() => {
    try {
      // Clear legacy dark cache if present
      localStorage.removeItem('axiom_theme')
      const saved = localStorage.getItem('claude_theme_mode')
      // Claude signature: default to warm cream canvas (#faf9f5)
      const initialDark = saved === 'dark'
      setIsDark(initialDark)
      applyTheme(initialDark)
    } catch {
      applyTheme(false)
    }
  }, [])

  const toggleTheme = () => {
    setIsDark(prev => {
      const next = !prev
      applyTheme(next)
      return next
    })
  }

  const setTheme = (dark: boolean) => {
    setIsDark(dark)
    applyTheme(dark)
  }

  return (
    <ThemeContext.Provider value={{ isDark, toggleTheme, setIsDark: setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useThemeContext() {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useThemeContext must be used within a ThemeProvider')
  }
  return context
}