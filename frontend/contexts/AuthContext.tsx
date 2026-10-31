'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

interface User {
  id: number;
  username: string;
  display_name?: string;
  email?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, displayName?: string, email?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Base API - configurable via environment, default to same-origin proxy
const API_BASE = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE || '';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [initFailed, setInitFailed] = useState(false);

  // Au montage : récupérer le user via /auth/me (le cookie httpOnly voyage
  // automatiquement grâce à credentials: 'include').
  const loadUser = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/me`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      } else {
        // User not authenticated - this is OK, just clear state
        setUser(null);
      }
    } catch (err) {
      // Network error or CORS issue - don't crash the app
      console.warn('Auth load failed (may be CORS or not yet initialized):', err);
      setUser(null);
    } finally {
      setIsLoading(false);
      setInitFailed(false);
    }
  }, [API_BASE]);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  // Reset loading state after a short delay if still loading
  useEffect(() => {
    if (isLoading) {
      const timer = setTimeout(() => {
        setIsLoading(false);
      }, 5000); // 5 second timeout fallback
      return () => clearTimeout(timer);
    }
  }, [isLoading]);

  const login = async (username: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
        credentials: 'include',
      });
      if (!res.ok) {
        let errorMsg = 'Erreur de connexion';
        try {
          const err = await res.json();
          if (typeof err.detail === 'string') {
            errorMsg = err.detail;
          } else if (Array.isArray(err.detail)) {
            errorMsg = err.detail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join(', ');
          }
        } catch {
          // ignore json parsing error
        }
        throw new Error(errorMsg);
      }
      const data = await res.json();
      // Le backend pose le cookie httpOnly ; on garde l'user en mémoire.
      setToken(data.access_token ?? null);
      setUser(data.user);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Connexion impossible';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (username: string, password: string, displayName?: string, email?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const payload: Record<string, any> = { username, password };
      if (displayName) payload.display_name = displayName;
      if (email) payload.email = email;

      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        credentials: 'include',
      });
      if (!res.ok) {
        let errorMsg = "Erreur d'inscription";
        try {
          const err = await res.json();
          if (typeof err.detail === 'string') {
            errorMsg = err.detail;
          } else if (Array.isArray(err.detail)) {
            errorMsg = err.detail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join(', ');
          }
        } catch {
          // ignore json parsing error
        }
        throw new Error(errorMsg);
      }
      const data = await res.json();
      setToken(data.access_token ?? null);
      setUser(data.user);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erreur d'inscription";
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await fetch(`${API_BASE}/auth/logout`, { method: 'POST', credentials: 'include' });
    } catch {
      /* ignore */
    }
    setToken(null);
    setUser(null);
  };

  // Si l'initialisation a échoué, réessayer après un délai
  useEffect(() => {
    if (initFailed) {
      const timer = setTimeout(() => {
        loadUser();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [initFailed]);

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, isLoading, error }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
