import type { Metadata } from 'next'
import './globals.css'
import { ThemeProvider } from '@/components/ThemeProvider'
import { AuthProvider } from '@/contexts/AuthContext'

export const metadata: Metadata = {
  title: 'HakimAgent / APEX v4.0 — Orchestrateur Multi-Agents IA',
  description: 'Plateforme et orchestrateur d\'agents IA haute performance avec routage intelligent, scoring et interface responsive moderne.',
  metadataBase: new URL('http://localhost:3000'),
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    title: 'HakimAgent — Orchestrateur Multi-Agents IA',
    description: 'Système d\'orchestration d\'agents IA autonome avec scoring algorithmique et interface glassmorphic.',
    url: 'http://localhost:3000',
    siteName: 'HakimAgent',
    locale: 'fr_FR',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'HakimAgent — Multi-Agent AI Suite',
    description: 'Orchestrateur multi-agents IA autonome',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'HakimAgent',
    url: 'http://localhost:3000',
    description: 'Orchestrateur multi-agents IA autonome avec scoring algorithmique',
  }

  return (
    <html lang="fr" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Geist+Mono:wght@100..900&family=Geist:wght@100..900&family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600;6..72,700&display=swap" rel="stylesheet" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className="min-h-[100dvh] antialiased ambient-bg">
        {/* Accessibilité WCAG 2.1 AA : Skip Link */}
        <a href="#main-content" className="skip-link">
          Aller au contenu principal
        </a>
        <ThemeProvider>
          <AuthProvider>
            <main id="main-content">
              {children}
            </main>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}

