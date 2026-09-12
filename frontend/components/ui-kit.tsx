import type { PropsWithChildren, ReactNode } from 'react'

export function Panel({ children, className = '' }: PropsWithChildren<{ className?: string }>) {
  return <section className={`control-panel ${className}`}>{children}</section>
}

export function StatusBadge({ tone, children }: PropsWithChildren<{ tone: 'success' | 'warning' | 'danger' | 'neutral' }>) {
  return <span className={`status-badge status-badge--${tone}`}><span aria-hidden="true">●</span>{children}</span>
}

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <section className="control-panel p-8 text-center"><h2 className="text-lg font-semibold">{title}</h2><p className="mx-auto mt-2 max-w-md text-sm" style={{ color: 'var(--text-muted)' }}>{description}</p>{action && <div className="mt-5">{action}</div>}</section>
}
