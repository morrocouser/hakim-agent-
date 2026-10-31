'use client'

import { useState, type FormEvent, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import {
  Lock,
  User,
  Mail,
  Eye,
  EyeOff,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Sparkles,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

function LoginForm() {
  const [isLogin, setIsLogin] = useState(true)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  const { login, register } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()

  const switchMode = (loginMode: boolean) => {
    setIsLogin(loginMode)
    setError('')
    setSuccess('')
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setSuccess('')

    const cleanUsername = username.trim()
    if (!cleanUsername) {
      setError("Veuillez renseigner un nom d'utilisateur.")
      return
    }

    if (!isLogin && cleanUsername.length < 3) {
      setError("Le nom d'utilisateur doit comporter au moins 3 caractères.")
      return
    }

    if (!password) {
      setError('Veuillez saisir votre mot de passe.')
      return
    }

    if (!isLogin && password.length < 6) {
      setError('Le mot de passe doit comporter au moins 6 caractères.')
      return
    }

    if (!isLogin && password !== confirmPassword) {
      setError('Les mots de passe ne correspondent pas.')
      return
    }

    if (!isLogin && email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setError('Veuillez saisir une adresse e-mail valide.')
      return
    }

    setLoading(true)
    try {
      if (isLogin) {
        await login(cleanUsername, password)
      } else {
        await register(
          cleanUsername,
          password,
          displayName.trim() || undefined,
          email.trim() || undefined
        )
        setSuccess('Compte créé avec succès ! Redirection en cours...')
      }

      const redirectPath = searchParams.get('redirect') || '/chat'
      router.push(redirectPath)
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : isLogin
          ? 'Connexion impossible. Vérifiez vos identifiants.'
          : "Échec de l'inscription. Veuillez réessayer."
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-4 sm:p-6" aria-labelledby="auth-title">
      <section className="control-panel w-full max-w-md p-6 sm:p-8">
        {/* Header avec logo/icône */}
        <div className="mb-6 text-center">
          <span
            className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl mb-3"
            style={{ background: 'var(--accent-soft)', border: '1px solid var(--accent-soft-2)' }}
          >
            {isLogin ? (
              <Lock size={22} style={{ color: 'var(--accent)' }} />
            ) : (
              <Sparkles size={22} style={{ color: 'var(--accent)' }} />
            )}
          </span>
          <h1 id="auth-title" className="font-serif text-2xl font-normal tracking-[-0.5px] text-[var(--text-primary)]">
            {isLogin ? 'Connexion à HakimAgent' : 'Créer votre compte'}
          </h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1.5 max-w-sm mx-auto">
            {isLogin
              ? 'Accédez à votre espace d’orchestration multi-agents'
              : 'Rejoignez la plateforme et déployez vos agents autonomes'}
          </p>
        </div>

        {/* Sélecteur d'onglets Connexion / Inscription */}
        <div
          className="flex rounded-xl p-1 mb-6"
          style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}
          role="tablist"
        >
          <button
            type="button"
            role="tab"
            aria-selected={isLogin}
            onClick={() => switchMode(true)}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              isLogin
                ? 'bg-[var(--surface-raised)] text-[var(--accent)] shadow-sm'
                : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
            }`}
          >
            Se connecter
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={!isLogin}
            onClick={() => switchMode(false)}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              !isLogin
                ? 'bg-[var(--surface-raised)] text-[var(--accent)] shadow-sm'
                : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
            }`}
          >
            Créer un compte
          </button>
        </div>

        {/* Message d'erreur */}
        {error && (
          <div
            className="flex items-start gap-2.5 p-3.5 mb-5 rounded-xl text-sm text-red-300 bg-red-950/40 border border-red-500/30"
            role="alert"
          >
            <AlertCircle size={18} className="text-red-400 shrink-0 mt-0.5" />
            <span className="flex-1 leading-snug">{error}</span>
          </div>
        )}

        {/* Message de succès */}
        {success && (
          <div
            className="flex items-start gap-2.5 p-3.5 mb-5 rounded-xl text-sm text-emerald-300 bg-emerald-950/40 border border-emerald-500/30"
            role="status"
          >
            <CheckCircle2 size={18} className="text-emerald-400 shrink-0 mt-0.5" />
            <span className="flex-1 leading-snug">{success}</span>
          </div>
        )}

        {/* Formulaire */}
        <form onSubmit={submit} className="space-y-4" noValidate>
          {/* Champ nom d'affichage (uniquement en inscription) */}
          {!isLogin && (
            <div>
              <label className="block text-xs font-semibold text-[var(--text-secondary)] mb-1" htmlFor="displayName">
                Nom d'affichage <span className="text-[var(--text-muted)] font-normal">(optionnel)</span>
              </label>
              <div className="relative">
                <User size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
                <input
                  id="displayName"
                  type="text"
                  className="input-axiom w-full pl-10"
                  placeholder="ex. Hakim M."
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  disabled={loading}
                  autoComplete="name"
                />
              </div>
            </div>
          )}

          {/* Champ email (uniquement en inscription) */}
          {!isLogin && (
            <div>
              <label className="block text-xs font-semibold text-[var(--text-secondary)] mb-1" htmlFor="email">
                Adresse e-mail <span className="text-[var(--text-muted)] font-normal">(optionnel)</span>
              </label>
              <div className="relative">
                <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
                <input
                  id="email"
                  type="email"
                  className="input-axiom w-full pl-10"
                  placeholder="exemple@domaine.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                  autoComplete="email"
                />
              </div>
            </div>
          )}

          {/* Champ nom d'utilisateur */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-[var(--text-secondary)]" htmlFor="username">
                Nom d'utilisateur <span className="text-[var(--accent)]">*</span>
              </label>
              {!isLogin && (
                <span className="text-[10px] text-[var(--text-muted)]">Min. 3 caractères</span>
              )}
            </div>
            <div className="relative">
              <User size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
              <input
                id="username"
                type="text"
                className="input-axiom w-full pl-10"
                placeholder={isLogin ? 'votre_nom' : 'ex. hakim_dev'}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={loading}
                autoComplete="username"
              />
            </div>
          </div>

          {/* Champ mot de passe */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-[var(--text-secondary)]" htmlFor="password">
                Mot de passe <span className="text-[var(--accent)]">*</span>
              </label>
              {!isLogin && (
                <span className="text-[10px] text-[var(--text-muted)]">Min. 6 caractères</span>
              )}
            </div>
            <div className="relative">
              <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                className="input-axiom w-full pl-10 pr-10"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
                autoComplete={isLogin ? 'current-password' : 'new-password'}
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors p-1"
                aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Champ confirmation de mot de passe (uniquement en inscription) */}
          {!isLogin && (
            <div>
              <label className="block text-xs font-semibold text-[var(--text-secondary)] mb-1" htmlFor="confirmPassword">
                Confirmer le mot de passe <span className="text-[var(--accent)]">*</span>
              </label>
              <div className="relative">
                <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  className="input-axiom w-full pl-10 pr-10"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  disabled={loading}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors p-1"
                  aria-label={showConfirmPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                >
                  {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
          )}

          {/* Bouton de soumission */}
          <div className="pt-2">
            <button
              type="submit"
              className="btn-primary w-full py-2.5 text-sm font-semibold flex items-center justify-center gap-2 cursor-pointer"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>{isLogin ? 'Connexion en cours…' : 'Création du compte…'}</span>
                </>
              ) : (
                <span>{isLogin ? 'Se connecter' : 'Créer mon compte'}</span>
              )}
            </button>
          </div>

          {/* Lien d'inversion en bas */}
          <div className="text-center pt-3 border-t border-[var(--border)] mt-4">
            {isLogin ? (
              <p className="text-xs text-[var(--text-secondary)]">
                Vous n'avez pas de compte ?{' '}
                <button
                  type="button"
                  onClick={() => switchMode(false)}
                  className="text-[var(--accent)] hover:underline font-semibold ml-1 cursor-pointer"
                >
                  Créer un compte
                </button>
              </p>
            ) : (
              <p className="text-xs text-[var(--text-secondary)]">
                Vous possédez déjà un compte ?{' '}
                <button
                  type="button"
                  onClick={() => switchMode(true)}
                  className="text-[var(--accent)] hover:underline font-semibold ml-1 cursor-pointer"
                >
                  Se connecter
                </button>
              </p>
            )}
          </div>
        </form>
      </section>
    </main>
  )
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center p-4">
          <div className="control-panel w-full max-w-md p-8 text-center">
            <Loader2 size={24} className="animate-spin mx-auto text-[var(--accent)]" />
          </div>
        </main>
      }
    >
      <LoginForm />
    </Suspense>
  )
}