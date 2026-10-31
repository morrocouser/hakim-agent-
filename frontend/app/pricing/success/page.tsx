"use client";

import React, { Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, Sparkles, ArrowRight, ShieldCheck, Cpu } from "lucide-react";
import AppShell from "@/components/AppShell";

function SuccessContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session_id");
  const isSimulated = searchParams.get("simulated") === "true";

  return (
    <div className="max-w-xl mx-auto px-4 py-16 text-center">
      <div className="w-16 h-16 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 flex items-center justify-center mx-auto mb-6 shadow-sm">
        <CheckCircle2 size={36} />
      </div>

      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider mb-3 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
        <Sparkles size={12} />
        <span>Paiement Validé avec Succès</span>
      </div>

      <h1 className="text-2xl sm:text-3xl font-extrabold text-[var(--text-primary)] mb-3 tracking-tight">
        Bienvenue dans HakimAgent Pro !
      </h1>

      <p className="text-sm text-[var(--text-muted)] leading-relaxed mb-8">
        Votre paiement Stripe a été confirmé. Vos privilèges Pro (accès illimité aux modèles avancés,
        orchestration DAG multi-agents et sandbox isolée) sont immédiatement déverrouillés sur votre compte.
      </p>

      {sessionId && (
        <div className="p-4 rounded-xl bg-[var(--surface-soft)] border border-[var(--border)] text-left mb-8 font-mono text-xs">
          <div className="text-[var(--text-muted)] text-[10px] uppercase tracking-wider mb-1">
            Référence transaction Stripe
          </div>
          <div className="text-[var(--text-primary)] truncate">{sessionId}</div>
          {isSimulated && (
            <div className="text-[11px] text-amber-500 mt-2 font-sans flex items-center gap-1.5">
              <span>⚡ Transaction en mode simulation/test locale réussie.</span>
            </div>
          )}
        </div>
      )}

      <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
        <Link
          href="/chat"
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-[#cc785c] hover:bg-[#a9583e] text-white font-medium text-xs tracking-normal shadow-sm transition-all cursor-pointer"
        >
          <Sparkles size={14} />
          <span>Lancer l'Agent Pro</span>
          <ArrowRight size={14} />
        </Link>

        <Link
          href="/pricing"
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-[var(--surface)] hover:bg-[var(--surface-soft)] border border-[var(--border)] text-[var(--text-primary)] font-medium text-xs transition-colors cursor-pointer"
        >
          <span>Voir mon abonnement</span>
        </Link>
      </div>
    </div>
  );
}

export default function PricingSuccessPage() {
  return (
    <AppShell>
      <Suspense fallback={<div className="p-12 text-center text-xs text-[var(--text-muted)]">Chargement de la confirmation...</div>}>
        <SuccessContent />
      </Suspense>
    </AppShell>
  );
}
