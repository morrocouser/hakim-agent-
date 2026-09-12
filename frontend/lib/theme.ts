'use client'

import { useCallback, useEffect, useState } from 'react'

export function useTheme() {
  const [isDark, setIsDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return document.documentElement.classList.contains('dark')
    }
    return true
  })

  const applyTheme = useCallback((dark: boolean) => {
    document.documentElement.classList.toggle('dark', dark)
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
    localStorage.setItem('axiom_theme', dark ? 'dark' : 'light')
  }, [])

  const toggleTheme = useCallback(() => {
    setIsDark(prev => {
      const next = !prev
      applyTheme(next)
      return next
    })
  }, [applyTheme])

  useEffect(() => {
    applyTheme(isDark)
  }, [isDark, applyTheme])

  return { isDark, toggleTheme, setIsDark }
}
