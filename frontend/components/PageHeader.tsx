import type { ReactNode } from 'react'

export default function PageHeader({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description?: string; actions?: ReactNode }) {
  return <header className="page-header"><div>{eyebrow && <div className="page-header__eyebrow">{eyebrow}</div>}<h1 className="page-header__title">{title}</h1>{description && <p className="page-header__description">{description}</p>}</div>{actions && <div className="flex shrink-0 flex-wrap gap-2">{actions}</div>}</header>
}
