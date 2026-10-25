'use client'

import { useState, type FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import { LockKey } from '@phosphor-icons/react'
import { useAuth } from '@/contexts/AuthContext'

// Redirection post-login posée par le middleware (?redirect=/agent) ; on
// n'accepte que les chemins internes pour éviter l'open redirect.
function safeRedirect(): string | null {
  if (typeof window === 'undefined') return null
  const target = new URLSearchParams(window.location.search).get('redirect')
  return target && target.startsWith('/') && !target.startsWith('//') ? target : null
}

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, register } = useAuth()
  const router = useRouter()

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      isLogin ? await login(username, password) : await register(username, password, displayName || undefined)
      router.push(safeRedirect() ?? '/chat')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Connexion impossible')
    } finally {
      setLoading(false)
    }
  }

  // Render register field only when not logging in
  const registerField = isLogin ? null : (
    <>
      <label className="block text-sm font-medium" htmlFor="displayName">Nom d'affichage</label>
      <input
        id="displayName"
        className="input-axiom mt-1.5 w-full"
        value={displayName}
        onChange={e => setDisplayName(e.target.value)}
      />
    </>
  )

  return (
    <main className="flex min-h-screen items-center justify-center p-5" aria-labelledby="login-title">
      <section className="control-panel w-full max-w-md p-7 sm:p-9">
        <div className="mb-12 text-center">
          <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl" style={{ background: 'var(--accent-soft)' }}>
            <LockKey size={22} style={{ color: 'var(--accent)' }} />
          </span>
          <div>
            <h1 className="text-3xl font-bold text-[var(--accent)] tracking-tight">
              Real code. Zero babysitting.
            </h1>
            <p className="text-lg text-[var(--text-muted)] mt-4 max-w-xl mx-auto">
              HakimAgent orchestrates autonomous agents that don't just generate snippets — they actually finish the job.
            </p>
          </div>
        </div>
        <form onSubmit={submit} className="space-y-5" noValidate>
          {registerField}
          <label className="block text-sm font-medium" htmlFor="username">Nom d'utilisateur</label>
          <div className="relative mt-1.5">
            <input
              id="username"
              type="text"
              className="input-axiom w-full pl-10"
              placeholder="votre_nom"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              autoComplete="username"
            />
          </div>
          <label className="block text-sm font-medium" htmlFor="password">Mot de passe</label>
          <div className="relative mt-1.5">
            <LockKey className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" size={18} />
            <input
              id="password"
              type="password"
              className="input-axiom w-full pl-10"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              autoComplete={isLogin ? "current-password" : "new-password"}
            />
          </div>
          {error && (
            <p className="text-sm text-red-400 bg-red-900/20 border border-red-500/20 rounded p-3" role="alert">
              {error}
            </p>
          )}
          <div className="flex items-center justify-between pt-2">
            <button
              type="submit"
              className="btn-primary w-full"
              disabled={loading}
            >
              {loading ? 'Chargement…' : isLogin ? 'Se connecter' : 'Créer le compte'}
            </button>
          </div>
          <button
            type="button"
            className="w-full text-sm font-medium text-[var(--accent)] hover:underline"
            onClick={() => { setIsLogin(value => !value); setError('') }}
          >
            {isLogin ? "Pas de compte ? S'inscrire" : 'Déjà un compte ? Se connecter'}
          </button>
        </form>
      </section>
    </main>
  )
}