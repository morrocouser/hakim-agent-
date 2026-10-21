import type { Metadata } from 'next'
import './globals.css'
import { ThemeProvider } from '@/components/ThemeProvider'
import { AuthProvider } from '@/contexts/AuthContext'

export const metadata: Metadata = {
  title: 'Solaris — Your AI Workforce, Ready for Production',
  description: 'Deploy autonomous AI agents that collaborate, reason, and execute complex workflows with human-level precision. Scale your operations, not your headcount.',
  metadataBase: new URL('http://localhost:3000'),
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    title: 'Solaris — Your AI Workforce, Ready for Production',
    description: 'Autonomous AI agent platform built with Next.js, Tailwind CSS, and shadcn/ui.',
    url: 'http://localhost:3000',
    siteName: 'Solaris',
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Solaris — Your AI Workforce, Ready for Production',
    description: 'Autonomous AI agent platform built with Next.js, Tailwind CSS, and shadcn/ui.',
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
    name: 'Solaris',
    url: 'http://localhost:3000',
    description: 'Autonomous AI agent platform built with Next.js, Tailwind CSS, and shadcn/ui.',
  }

  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Geist+Mono:wght@100..900&family=Geist:wght@100..900&display=swap" rel="stylesheet" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className="bg-[#0a0a0a] text-white antialiased min-h-screen selection:bg-[#0065fc] selection:text-white font-sans">
        <ThemeProvider>
          <AuthProvider>
            {children}
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
