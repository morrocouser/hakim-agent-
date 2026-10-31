"use client";

import React from "react";
import Link from "next/link";
import { XCircle, ArrowLeft, CreditCard, ShieldCheck } from "lucide-react";
import AppShell from "@/components/AppShell";

export default function PricingCancelPage() {
  return (
    <AppShell>
      <div className="max-w-xl mx-auto px-4 py-16 text-center">
        <div className="w-16 h-16 rounded-full bg-amber-500/10 text-amber-500 border border-amber-500/20 flex items-center justify-center mx-auto mb-6 shadow-sm">
          <XCircle size={36} />
        </div>

        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider mb-3 bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
          <CreditCard size={12} />
          <span>Paiement Non Finalisé</span>
        </div>

        <h1 className="text-2xl sm:text-3xl font-extrabold text-[var(--text-primary)] mb-3 tracking-tight">
          La souscription a été interrompue
        </h1>

        <p className="text-sm text-[var(--text-muted)] leading-relaxed mb-8">
          Vous avez annulé ou fermé la page de paiement Stripe Checkout. Rassurez-vous,{" "}
          <strong>aucun montant n'a été prélevé</strong> sur votre carte. Votre compte reste actif
          sur le forfait gratuit.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            href="/pricing"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-[#cc785c] hover:bg-[#a9583e] text-white font-medium text-xs tracking-normal shadow-sm transition-all cursor-pointer"
          >
            <ArrowLeft size={14} />
            <span>Retourner aux forfaits</span>
          </Link>

          <Link
            href="/chat"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-[var(--surface)] hover:bg-[var(--surface-soft)] border border-[var(--border)] text-[var(--text-primary)] font-medium text-xs transition-colors cursor-pointer"
          >
            <span>Continuer en version Starter</span>
          </Link>
        </div>
      </div>
    </AppShell>
  );
}
