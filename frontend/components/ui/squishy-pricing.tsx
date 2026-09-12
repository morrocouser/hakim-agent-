"use client";

import { motion, AnimatePresence } from 'framer-motion';
import React, { useState } from 'react';

export const Component = ({ onSelectPlan }: { onSelectPlan?: (plan: string) => void }) => {
  const [selectedPlan, setSelectedPlan] = useState<{ label: string; price: string } | null>(null);
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [subscribed, setSubscribed] = useState(false);

  const handlePlanClick = (label: string, price: string) => {
    setSelectedPlan({ label, price });
    setSubscribed(false);
  };

  const executeSubscription = () => {
    if (!selectedPlan) return;
    setSubscribed(true);
    const planName = selectedPlan.label;
    setTimeout(() => {
      if (onSelectPlan) {
        onSelectPlan(planName);
      }
      setSelectedPlan(null);
      setSubscribed(false);
    }, 1200);
  };

  return (
    <section className="bg-background px-4 py-12 min-h-screen transition-colors relative">
      <div className="mx-auto flex w-fit flex-wrap justify-center gap-6">
        <PricingCard
          label="Individual"
          monthlyPrice="299"
          description="For individuals who want to understand why their landing pages aren't working"
          cta="Sign up"
          background="bg-indigo-500 dark:bg-indigo-600"
          BGComponent={BGComponent1}
          onClick={() => handlePlanClick("Individual", "299")}
        />
        <PricingCard
          label="Company"
          monthlyPrice="999"
          description="For mid-sized companies who are serious about boosting their revenue by 30%"
          cta="Sign up"
          background="bg-purple-500 dark:bg-purple-600"
          BGComponent={BGComponent2}
          onClick={() => handlePlanClick("Company", "999")}
        />
        <PricingCard
          label="Enterprise"
          monthlyPrice="4,999"
          description="For large enterprises looking to outsource their conversion rate optimization"
          cta="Book a call"
          background="bg-pink-500 dark:bg-pink-600"
          BGComponent={BGComponent3}
          onClick={() => handlePlanClick("Enterprise", "4,999")}
        />
      </div>

      {/* Interactive Sign Up / Checkout Modal */}
      <AnimatePresence>
        {selectedPlan && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedPlan(null)}
              className="fixed inset-0 bg-black/75 backdrop-blur-md"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="relative z-10 w-full max-w-md overflow-hidden rounded-2xl border border-white/20 bg-neutral-900 p-6 text-white shadow-2xl"
            >
              {!subscribed ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-white/10 pb-3">
                    <div>
                      <span className="text-xs font-mono uppercase tracking-wider text-amber-400 font-bold">Plan Sélectionné</span>
                      <h3 className="text-2xl font-black text-white mt-0.5">{selectedPlan.label}</h3>
                    </div>
                    <div className="text-right">
                      <span className="font-mono text-3xl font-black text-emerald-400">${selectedPlan.price}</span>
                      <span className="text-xs text-neutral-400 block">/ mois</span>
                    </div>
                  </div>

                  <div className="space-y-3 pt-2">
                    <div>
                      <label className="block text-xs font-medium text-neutral-300 mb-1">Nom complet</label>
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Alex Dupont"
                        className="w-full rounded-xl border border-white/15 bg-neutral-800/90 px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-neutral-300 mb-1">Adresse Email</label>
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="alex@example.com"
                        className="w-full rounded-xl border border-white/15 bg-neutral-800/90 px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      />
                    </div>
                  </div>

                  <div className="pt-4 flex gap-3">
                    <button
                      type="button"
                      onClick={() => setSelectedPlan(null)}
                      className="flex-1 rounded-xl border border-white/15 bg-neutral-800 py-3 text-xs font-semibold text-neutral-300 hover:bg-neutral-700 transition-colors cursor-pointer"
                    >
                      Annuler
                    </button>
                    <button
                      type="button"
                      onClick={executeSubscription}
                      className="flex-1 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 py-3 text-xs font-bold text-neutral-950 hover:brightness-110 transition-all shadow-lg shadow-emerald-500/25 cursor-pointer"
                    >
                      Confirmer l'inscription
                    </button>
                  </div>
                </div>
              ) : (
                <div className="py-8 text-center space-y-3">
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400 text-3xl border border-emerald-500/40 animate-bounce">
                    ✓
                  </div>
                  <h4 className="text-xl font-black text-white">Souscription Confirmée !</h4>
                  <p className="text-xs text-neutral-300">
                    Bienvenue dans le plan <strong className="text-amber-400">{selectedPlan.label}</strong>. Redirection en cours...
                  </p>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </section>
  );
};

const PricingCard = ({ label, monthlyPrice, description, cta, background, BGComponent, onClick }: any) => {
  return (
    <motion.div
      whileHover="hover"
      transition={{ duration: 1, ease: "backInOut" }}
      variants={{ hover: { scale: 1.05 } }}
      className={`relative h-96 w-80 shrink-0 overflow-hidden rounded-xl p-8 ${background} shadow-lg hover:shadow-xl transition-shadow cursor-pointer`}
      onClick={onClick}
    >
      <div className="relative z-10 text-white">
        <span className="mb-3 block w-fit rounded-full bg-white/20 backdrop-blur-sm px-3 py-0.5 text-sm font-medium text-white border border-white/20">
          {label}
        </span>
        <motion.span
          initial={{ scale: 0.85 }}
          variants={{ hover: { scale: 1 } }}
          transition={{ duration: 1, ease: "backInOut" }}
          className="my-2 block origin-top-left font-mono text-6xl font-black leading-[1.2]"
        >
          ${monthlyPrice}/<br />Month
        </motion.span>
        <p className="text-lg text-white/90">{description}</p>
      </div>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onClick();
        }}
        className="absolute bottom-4 left-4 right-4 z-20 rounded-lg border-2 border-white bg-white py-2 text-center font-mono font-black uppercase text-neutral-800 backdrop-blur-sm transition-all duration-200 hover:bg-white/10 hover:text-white hover:border-white/80 focus:outline-none focus:ring-2 focus:ring-white/50 focus:ring-offset-2 focus:ring-offset-transparent cursor-pointer"
      >
        {cta}
      </button>
      <BGComponent />
    </motion.div>
  );
};

const BGComponent1 = () => (
  <motion.svg
    width="320"
    height="384"
    viewBox="0 0 320 384"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    variants={{ hover: { scale: 1.5 } }}
    transition={{ duration: 1, ease: "backInOut" }}
    className="absolute inset-0 z-0 pointer-events-none"
  >
    <motion.circle
      variants={{ hover: { scaleY: 0.5, y: -25 } }}
      transition={{ duration: 1, ease: "backInOut", delay: 0.2 }}
      cx="160.5"
      cy="114.5"
      r="101.5"
      fill="rgba(0, 0, 0, 0.2)"
      className="dark:fill-white/10"
    />
    <motion.ellipse
      variants={{ hover: { scaleY: 2.25, y: -25 } }}
      transition={{ duration: 1, ease: "backInOut", delay: 0.2 }}
      cx="160.5"
      cy="265.5"
      rx="101.5"
      ry="43.5"
      fill="rgba(0, 0, 0, 0.2)"
      className="dark:fill-white/10"
    />
  </motion.svg>
);

const BGComponent2 = () => (
  <motion.svg
    width="320"
    height="384"
    viewBox="0 0 320 384"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    variants={{ hover: { scale: 1.05 } }}
    transition={{ duration: 1, ease: "backInOut" }}
    className="absolute inset-0 z-0 pointer-events-none"
  >
    <motion.rect
      x="14"
      width="153"
      height="153"
      rx="15"
      fill="rgba(0, 0, 0, 0.2)"
      className="dark:fill-white/10"
      variants={{ hover: { y: 219, rotate: "90deg", scaleX: 2 } }}
      style={{ y: 12 }}
      transition={{ delay: 0.2, duration: 1, ease: "backInOut" }}
    />
    <motion.rect
      x="155"
      width="153"
      height="153"
      rx="15"
      fill="rgba(0, 0, 0, 0.2)"
      className="dark:fill-white/10"
      variants={{ hover: { y: 219, rotate: "90deg", scaleX: 2 } }}
      style={{ y: 219 }}
      transition={{ delay: 0.2, duration: 1, ease: "backInOut" }}
    />
  </motion.svg>
);

const BGComponent3 = () => (
  <motion.svg
    width="320"
    height="384"
    viewBox="0 0 320 384"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    variants={{ hover: { scale: 1.25 } }}
    transition={{ duration: 1, ease: "backInOut" }}
    className="absolute inset-0 z-0 pointer-events-none"
  >
    <motion.path
      variants={{ hover: { y: -50 } }}
      transition={{ delay: 0.3, duration: 1, ease: "backInOut" }}
      d="M148.893 157.531C154.751 151.673 164.249 151.673 170.107 157.531L267.393 254.818C273.251 260.676 273.251 270.173 267.393 276.031L218.75 324.674C186.027 357.397 132.973 357.397 100.25 324.674L51.6068 276.031C45.7489 270.173 45.7489 260.676 51.6068 254.818L148.893 157.531Z"
      fill="rgba(0, 0, 0, 0.2)"
      className="dark:fill-white/10"
    />
    <motion.path
      variants={{ hover: { y: -50 } }}
      transition={{ delay: 0.2, duration: 1, ease: "backInOut" }}
      d="M148.893 99.069C154.751 93.2111 164.249 93.2111 170.107 99.069L267.393 196.356C273.251 202.213 273.251 211.711 267.393 217.569L218.75 266.212C186.027 298.935 132.973 298.935 100.25 266.212L51.6068 217.569C45.7489 211.711 45.7489 202.213 51.6068 196.356L148.893 99.069Z"
      fill="rgba(0, 0, 0, 0.2)"
      className="dark:fill-white/10"
    />
    <motion.path
      variants={{ hover: { y: -50 } }}
      transition={{ delay: 0.1, duration: 1, ease: "backInOut" }}
      d="M148.893 40.6066C154.751 34.7487 164.249 34.7487 170.107 40.6066L267.393 137.893C273.251 143.751 273.251 153.249 267.393 159.106L218.75 207.75C186.027 240.473 132.973 240.473 100.25 207.75L51.6068 159.106C45.7489 153.249 45.7489 143.751 51.6068 137.893L148.893 40.6066Z"
      fill="rgba(0, 0, 0, 0.2)"
      className="dark:fill-white/10"
    />
  </motion.svg>
);
