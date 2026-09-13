'use client'

import { useEffect, useState, createContext, useContext, ReactNode } from 'react'

type ThemeContextType = {
  isDark: boolean
  toggleTheme: () => void
  setIsDark: (dark: boolean) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [isDark, setIsDark] = useState(true)

  const applyTheme = (dark: boolean) => {
    if (typeof window !== 'undefined') {
      document.documentElement.classList.toggle('dark', dark)
      document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
    }
  }

  useEffect(() => {
    // Design system = dark único. On ignore le localStorage (aucun retour light accidentel).
    applyTheme(true)
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