"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Check,
  Sparkles,
  Zap,
  ShieldCheck,
  CreditCard,
  ArrowRight,
  ExternalLink,
  Layers,
  Clock,
  HelpCircle,
  AlertCircle,
  Crown,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { useAuth } from "@/contexts/AuthContext";
import {
  getBillingConfig,
  getBillingStatus,
  createCheckoutSession,
  createPortalSession,
  BillingPlan,
  BillingStatus,
} from "@/lib/api";

export default function PricingPage() {
  const { user, token } = useAuth();
  const [interval, setInterval] = useState<"month" | "year">("month");
  const [plans, setPlans] = useState<Record<string, BillingPlan> | null>(null);
  const [billingStatus, setBillingStatus] = useState<BillingStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Charger la configuration et le statut de facturation
  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      setError(null);
      try {
        const config = await getBillingConfig();
        if (config?.plans) {
          setPlans(config.plans);
        }

        if (user) {
          try {
            const status = await getBillingStatus(token);
            setBillingStatus(status);
          } catch (err) {
            console.warn("Impossible de charger le statut de facturation:", err);
          }
        }
      } catch (err: any) {
        console.error("Erreur chargement facturation:", err);
        setError("Impossible de contacter le service de facturation.");
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, [user, token]);

  const handleCheckout = async (tier: string) => {
    if (!user) {
      // Rediriger vers la connexion avec paramètre de retour
      window.location.href = `/login?redirect=/pricing`;
      return;
    }

    setActionLoading(tier);
    setError(null);
    try {
      const data = await createCheckoutSession(tier, interval, token);
      if (data?.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        throw new Error("URL de paiement non reçue");
      }
    } catch (err: any) {
      console.error("Erreur checkout:", err);
      setError(err.message || "Une erreur est survenue lors de l'accès au paiement.");
      setActionLoading(null);
    }
  };

  const handlePortal = async () => {
    setActionLoading("portal");
    setError(null);
    try {
      const data = await createPortalSession(window.location.href, token);
      if (data?.portal_url) {
        window.location.href = data.portal_url;
      } else {
        throw new Error("Lien du portail client introuvable");
      }
    } catch (err: any) {
      console.error("Erreur portail:", err);
      setError(err.message || "Impossible d'ouvrir le portail de facturation.");
      setActionLoading(null);
    }
  };

  const currentTier = billingStatus?.tier || "free";

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto px-4 py-12">
        {/* En-tête */}
        <div className="text-center max-w-2xl mx-auto mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider mb-4 border border-[var(--border)] bg-[var(--surface-soft)] text-[#cc785c]">
            <CreditCard size={14} />
            <span>Paiement Sécurisé avec Stripe</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[var(--text-primary)] mb-4">
            Tarifs simples, clairs et sans engagement
          </h1>
          <p className="text-sm sm:text-base text-[var(--text-muted)] leading-relaxed">
            Déployez des essaims d'agents autonomes, accédez aux meilleurs modèles LLM
            et orchestrez vos tâches d'ingénierie en toute fluidité.
          </p>

          {/* Toggle Mensuel / Annuel */}
          <div className="flex items-center justify-center gap-3 mt-8">
            <span
              className={`text-sm font-medium cursor-pointer transition-colors ${
                interval === "month"
                  ? "text-[var(--text-primary)] font-semibold"
                  : "text-[var(--text-muted)]"
              }`}
              onClick={() => setInterval("month")}
            >
              Facturation mensuelle
            </span>
            <button
              type="button"
              onClick={() => setInterval(interval === "month" ? "year" : "month")}
              aria-label="Basculer entre facturation mensuelle et annuelle"
              className="relative w-12 h-6 bg-[var(--surface-soft)] border border-[var(--border)] rounded-full transition-colors cursor-pointer flex items-center p-0.5"
            >
              <div
                className={`w-4 h-4 rounded-full bg-[#cc785c] shadow-sm transform transition-transform ${
                  interval === "year" ? "translate-x-6" : "translate-x-0.5"
                }`}
              />
            </button>
            <span
              className={`text-sm font-medium cursor-pointer transition-colors flex items-center gap-1.5 ${
                interval === "year"
                  ? "text-[var(--text-primary)] font-semibold"
                  : "text-[var(--text-muted)]"
              }`}
              onClick={() => setInterval("year")}
            >
              Annuelle
              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                -20%
              </span>
            </span>
          </div>
        </div>

        {/* Message d'erreur éventuel */}
        {error && (
          <div className="max-w-md mx-auto mb-8 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 text-xs flex items-center gap-2.5">
            <AlertCircle size={16} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Bannière d'état pour utilisateur déjà abonné */}
        {billingStatus && currentTier !== "free" && (
          <div className="mb-10 p-4 rounded-2xl bg-[var(--surface-soft)] border border-[var(--border)] flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#cc785c]/10 text-[#cc785c] flex items-center justify-center font-bold">
                <Crown size={20} />
              </div>
              <div>
                <div className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
                  <span>Votre formule actuelle : {billingStatus.tier_name}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 uppercase">
                    {billingStatus.status}
                  </span>
                </div>
                <div className="text-xs text-[var(--text-muted)] mt-0.5">
                  {billingStatus.cancel_at_period_end
                    ? "Résiliation programmée à la fin de la période"
                    : billingStatus.current_period_end
                    ? `Prochain renouvellement le ${new Date(billingStatus.current_period_end).toLocaleDateString()}`
                    : "Abonnement actif"}
                </div>
              </div>
            </div>

            <button
              onClick={handlePortal}
              disabled={actionLoading === "portal"}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--surface)] hover:bg-[var(--surface-soft)] border border-[var(--border)] text-[var(--text-primary)] transition-all cursor-pointer shadow-xs disabled:opacity-50"
            >
              <CreditCard size={14} />
              <span>{actionLoading === "portal" ? "Ouverture..." : "Gérer mon abonnement (Factures & CB)"}</span>
              <ExternalLink size={12} />
            </button>
          </div>
        )}

        {/* Grille des 3 offres */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          {/* 1. Starter / Gratuit */}
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 flex flex-col justify-between shadow-xs relative transition-all hover:border-[var(--border-strong,var(--border))]">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
                  Starter
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-[var(--surface-soft)] text-[var(--text-muted)] border border-[var(--border)]">
                  Découverte
                </span>
              </div>

              <div className="mb-4">
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-extrabold text-[var(--text-primary)]">0 €</span>
                  <span className="text-xs text-[var(--text-muted)]">/ mois</span>
                </div>
                <p className="text-xs text-[var(--text-muted)] mt-2 min-h-[32px]">
                  Pour tester l'orchestration multi-agents et prototyper vos workflows en local.
                </p>
              </div>

              <div className="w-full h-px bg-[var(--border)] my-6" />

              <ul className="space-y-3 mb-6 text-xs text-[var(--text-primary)]">
                <li className="flex items-start gap-2.5">
                  <Check size={14} className="text-emerald-500 shrink-0 mt-0.5" />
                  <span>Modèles locaux open-source (Qwen 2.5, Llama 3.1)</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check size={14} className="text-emerald-500 shrink-0 mt-0.5" />
                  <span>10 tâches d'agents par jour</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check size={14} className="text-emerald-500 shrink-0 mt-0.5" />
                  <span>Exécution séquentielle (1 agent actif)</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check size={14} className="text-emerald-500 shrink-0 mt-0.5" />
                  <span>Persistance SQLite locale</span>
                </li>
              </ul>
            </div>

            <div>
              {currentTier === "free" ? (
                <button
                  disabled
                  className="w-full py-2.5 rounded-xl text-xs font-semibold border border-[var(--border)] bg-[var(--surface-soft)] text-[var(--text-muted)] cursor-default"
                >
                  Plan actuel
                </button>
              ) : (
                <button
                  onClick={() => handleCheckout("free")}
                  className="w-full py-2.5 rounded-xl text-xs font-semibold border border-[var(--border)] hover:bg-[var(--surface-soft)] text-[var(--text-primary)] transition-colors cursor-pointer"
                >
                  Revenir au Starter
                </button>
              )}
            </div>
          </div>

          {/* 2. Pro Développeur (Recommandé) */}
          <div className="rounded-2xl border-2 border-[#cc785c] bg-[var(--surface)] p-6 flex flex-col justify-between shadow-lg relative transition-all transform hover:-translate-y-1">
            <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase bg-[#cc785c] text-white shadow-xs">
              Recommandé
            </div>

            <div>
              <div className="flex items-center justify-between mb-4 mt-1">
                <span className="text-xs font-bold uppercase tracking-wider text-[#cc785c]">
                  Pro Développeur
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-[#cc785c]/10 text-[#cc785c] border border-[#cc785c]/20">
                  Complet
                </span>
              </div>

              <div className="mb-4">
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-extrabold text-[var(--text-primary)]">
                    {interval === "year" ? "23 €" : "29 €"}
                  </span>
                  <span className="text-xs text-[var(--text-muted)]">
                    / mois {interval === "year" && "(279 € facturés/an)"}
                  </span>
                </div>
                <p className="text-xs text-[var(--text-muted)] mt-2 min-h-[32px]">
                  Pleine puissance d'automatisation avec modèles de pointe et orchestration parallèle.
                </p>
              </div>

              <div className="w-full h-px bg-[var(--border)] my-6" />

              <ul className="space-y-3 mb-6 text-xs text-[var(--text-primary)]">
                <li className="flex items-start gap-2.5">
                  <Check size={14} className="text-[#cc785c] shrink-0 mt-0.5" />
                  <span className="font-medium">
                    Claude 3.7 Sonnet, GPT-4o & Gemini 2.0
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check size={14} className="text-[#cc785c] shrink-0 mt-0.5" />
                  <span className="font-medium">Tâches et exécutions illimitées</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check size={14} className="text-[#cc785c] shrink-0 mt-0.5" />
                  <span>Orchestration DAG jusqu'à 8 agents simultanés</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check size={14} className="text-[#cc785c] shrink-0 mt-0.5" />
                  <span>Boucle de réflexion ReAct & Scoring déterministe</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check size={14} className="text-[#cc785c] shrink-0 mt-0.5" />
                  <span>Sandbox d'exécution sécurisée des fichiers</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check size={14} className="text-[#cc785c] shrink-0 mt-0.5" />
                  <span>Web Search, Code Executor, MCP & Connecteurs</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check size={14} className="text-[#cc785c] shrink-0 mt-0.5" />
                  <span>Support prioritaire Discord & e-mail</span>
                </li>
              </ul>
            </div>

            <div>
              {currentTier === "pro" ? (
                <button
                  onClick={handlePortal}
                  className="w-full py-2.5 rounded-xl text-xs font-semibold bg-[#cc785c] text-white hover:bg-[#a9583e] transition-colors cursor-pointer flex items-center justify-center gap-2"
                >
                  <CreditCard size={14} />
                  <span>Gérer mon forfait Pro</span>
                </button>
              ) : (
                <button
                  onClick={() => handleCheckout("pro")}
                  disabled={actionLoading === "pro"}
                  className="w-full py-2.5 rounded-xl text-xs font-semibold bg-[#cc785c] text-white hover:bg-[#a9583e] transition-all transform hover:scale-[1.02] cursor-pointer flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
                >
                  <Sparkles size={14} />
                  <span>
                    {actionLoading === "pro" ? "Préparation Stripe..." : "Passer à l'offre Pro"}
                  </span>
                  <ArrowRight size={14} />
                </button>
              )}
            </div>
          </div>

          {/* 3. Entreprise & Équipe */}
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 flex flex-col justify-between shadow-xs relative transition-all hover:border-[var(--border-strong,var(--border))]">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
                  Entreprise
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-[var(--surface-soft)] text-[var(--text-muted)] border border-[var(--border)]">
                  Sur-mesure
                </span>
              </div>

              <div className="mb-4">
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-extrabold text-[var(--text-primary)]">
                    {interval === "year" ? "79 €" : "99 €"}
                  </span>
                  <span className="text-xs text-[var(--text-muted)]">
                    / mois {interval === "year" && "(950 € facturés/an)"}
                  </span>
                </div>
                <p className="text-xs text-[var(--text-muted)] mt-2 min-h-[32px]">
                  Pour les organisations nécessitant une gouvernance stricte, des personas sur-mesure et un SLA.
                </p>
              </div>

              <div className="w-full h-px bg-[var(--border)] my-6" />

              <ul className="space-y-3 mb-6 text-xs text-[var(--text-primary)]">
                <li className="flex items-start gap-2.5">
                  <Check size={14} className="text-emerald-500 shrink-0 mt-0.5" />
                  <span>Tout le forfait Pro inclus</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check size={14} className="text-emerald-500 shrink-0 mt-0.5" />
                  <span>Coworkers & Personas spécialisés illimités</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check size={14} className="text-emerald-500 shrink-0 mt-0.5" />
                  <span>Routage hybride multi-fournisseurs (clés d'entreprise)</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check size={14} className="text-emerald-500 shrink-0 mt-0.5" />
                  <span>Gouvernance, audit trail & traçabilité tokens</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check size={14} className="text-emerald-500 shrink-0 mt-0.5" />
                  <span>Garantie de disponibilité SLA 99.9%</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check size={14} className="text-emerald-500 shrink-0 mt-0.5" />
                  <span>Ingénieur support dédié & onboarding</span>
                </li>
              </ul>
            </div>

            <div>
              {currentTier === "enterprise" ? (
                <button
                  onClick={handlePortal}
                  className="w-full py-2.5 rounded-xl text-xs font-semibold bg-[var(--surface-soft)] text-[var(--text-primary)] border border-[var(--border)] hover:bg-[var(--surface)] transition-colors cursor-pointer flex items-center justify-center gap-2"
                >
                  <CreditCard size={14} />
                  <span>Gérer mon forfait Entreprise</span>
                </button>
              ) : (
                <button
                  onClick={() => handleCheckout("enterprise")}
                  disabled={actionLoading === "enterprise"}
                  className="w-full py-2.5 rounded-xl text-xs font-semibold border border-[var(--border)] hover:bg-[var(--surface-soft)] text-[var(--text-primary)] transition-colors cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <span>
                    {actionLoading === "enterprise" ? "Préparation..." : "Choisir l'offre Entreprise"}
                  </span>
                  <ArrowRight size={14} />
                </button>
              )}
            </div>
          </div>
        </div>

        {/* FAQ - Foire Aux Questions */}
        <div className="max-w-3xl mx-auto border-t border-[var(--border)] pt-12">
          <div className="text-center mb-8">
            <h2 className="text-xl font-bold text-[var(--text-primary)] mb-2 flex items-center justify-center gap-2">
              <HelpCircle size={18} className="text-[#cc785c]" />
              <span>Questions Fréquentes sur la Facturation</span>
            </h2>
            <p className="text-xs text-[var(--text-muted)]">
              Toutes les réponses pour gérer votre compte en toute sérénité.
            </p>
          </div>

          <div className="space-y-4">
            <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface)]">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-1">
                Comment s'effectue le paiement ?
              </h3>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                Le paiement est géré de bout en bout par <strong>Stripe</strong> via une page sécurisée
                Stripe Checkout. Vos données bancaires ne transitent jamais par nos serveurs, vous garantissant
                le plus haut standard de sécurité financière (PCI-DSS niveau 1).
              </p>
            </div>

            <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface)]">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-1">
                Puis-je résilier ou modifier mon abonnement à tout moment ?
              </h3>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                Oui, sans aucun frais ni engagement. Vous disposez d'un bouton direct
                <strong> "Gérer mon abonnement"</strong> qui ouvre votre portail client Stripe officiel pour
                mettre à jour votre carte bancaire, télécharger vos factures PDF ou résilier en un clic.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface)]">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-1">
                Quels sont les moyens de paiement acceptés ?
              </h3>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                Toutes les cartes bancaires principales (Visa, Mastercard, American Express),
                ainsi qu'Apple Pay, Google Pay et les prélèvements SEPA selon votre localisation géographique.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface)]">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-1">
                Puis-je utiliser mes propres clés API d'entreprise ?
              </h3>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                Absolument. HakimAgent est conçu pour supporter le routage hybride : vous pouvez utiliser les modèles
                fournis dans le forfait Pro ou brancher directement vos propres clés Anthropic, OpenAI, Google Gemini
                ou OpenRouter.
              </p>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
