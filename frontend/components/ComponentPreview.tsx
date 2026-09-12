"use client";

/**
 * ComponentPreview — portage React/TypeScript de SmartComponentPreview
 * du clone 21st.dev.
 *
 * Ref: C:\Users\hp\Desktop\Scraping App Studio-20260811T223456Z-1-001\Scraping App Studio\21st-dev-clone\src\components\SmartComponentPreview.jsx
 *
 * Rend un preview interactif de composant selon la catégorie détectée
 * par le nom (buttons, cards, charts, navigation, chat, etc.).
 */
import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  Sparkles, Check, Bell, Search, Layers, Code2, Globe,
  CreditCard, Shield, Activity, Users, Play, Lock,
  Calendar, MessageSquare, Image, Upload, Zap,
  ArrowUpRight, Star, BookOpen, Heart, Sliders,
} from "lucide-react";

interface PreviewProps {
  name: string;
  apiSymbol?: string;
  platform?: "web" | "mobile" | "desktop";
}

// Helper: map icon name → lucide component
const iconMap: Record<string, React.ElementType> = {
  Sparkles, Check, Bell, Search, Layers, Code2, Globe,
  CreditCard, Shield, Activity, Users, Play, Lock,
  Calendar, MessageSquare, Image, Upload, Zap,
  ArrowUpRight, Star, BookOpen, Heart, Sliders,
};

function Icon({ name, size = 4 }: { name: string; size?: number }) {
  const Comp = iconMap[name];
  return Comp ? <Comp className={`w-${size} h-${size}`} /> : null;
}

export default function ComponentPreview({ name, apiSymbol = "", platform = "web" }: PreviewProps) {
  const n = name.toLowerCase().replace(/&/g, "&");
  const [isToggled, setIsToggled] = useState(true);

  // 1. Buttons, CTA, Actions
  if (n.includes("button") || n.includes("cta") || n.includes("action") || n.includes("glow") || n.includes("press") || n.includes("btn") || n.includes("click")) {
    return (
      <motion.div
        className="w-full flex flex-col items-center justify-center p-3 select-none"
        whileHover={{ scale: 1.02 }}
      >
        <motion.button
          className="relative group/b p-[1.5px] rounded-xl overflow-hidden shadow-lg shadow-indigo-500/20 active:scale-95 transition-transform"
          whileTap={{ scale: 0.95 }}
        >
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-indigo-500 via-purple-500 to-cyan-400 rounded-xl"
            animate={{ opacity: [0.8, 1, 0.8] }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="relative px-4 py-2 rounded-[11px] bg-slate-950/90 flex items-center gap-2 text-white text-xs font-bold transition-all group-hover/b:bg-slate-950/70"
            whileHover={{ backgroundColor: "rgba(17, 24, 39, 0.7)" }}
          >
            <motion.span
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <Icon name="Sparkles" size={3.5} />
            </motion.span>
            <span className="truncate max-w-[130px] tracking-tight">{name}</span>
            <motion.span
              className="text-slate-400"
              animate={{ x: [0, 4, 0] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <Icon name="ArrowUpRight" size={3} />
            </motion.span>
          </motion.div>
        </motion.button>
      </motion.div>
    );
  }

  // 2. Bento Grids, Cards
  if (n.includes("bento") || n.includes("card") || n.includes("tile") || n.includes("grid") || n.includes("spotlight") || n.includes("box")) {
    return (
      <motion.div
        className="w-full p-2 select-none"
        whileHover={{ scale: 1.02 }}
      >
        <motion.div
          className="rounded-2xl p-3 bg-gradient-to-br from-slate-900/90 via-slate-950 to-indigo-950/40 border border-white/10 flex flex-col justify-between h-20 shadow-md"
          whileHover={{ borderColor: "rgba(99, 102, 241, 0.4)" }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <motion.div
                className="w-6 h-6 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold"
                animate={{ rotate: [0, 5, -5, 0] }}
                transition={{ duration: 5, repeat: Infinity }}
              >
                <Icon name="Layers" size={3.5} />
              </motion.div>
              <span className="text-[11px] font-bold text-white tracking-tight truncate max-w-[110px]">{name}</span>
            </div>
            <motion.span
              className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
          </div>
          <div className="flex items-center justify-between mt-auto pt-1.5 border-t border-white/5 text-[9px] text-slate-400">
            <div className="w-20 h-1.5 rounded-full bg-gradient-to-r from-indigo-500 to-cyan-400" />
            <motion.span
              animate={{ opacity: [1, 0.7, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              Actif
            </motion.span>
          </div>
        </motion.div>
      </motion.div>
    );
  }

  // 3. Navigation, Docks
  if (n.includes("dock") || n.includes("nav") || n.includes("menu") || n.includes("tab") || n.includes("header") || n.includes("sidebar") || n.includes("bar")) {
    return (
      <motion.div
        className="w-full p-2 flex items-center justify-center select-none"
        whileHover={{ scale: 1.02 }}
      >
        <motion.div
          className="p-1 rounded-2xl bg-slate-900/90 border border-white/10 flex items-center gap-1 shadow-lg backdrop-blur-md"
          whileHover={{ borderColor: "rgba(99, 102, 241, 0.4)" }}
        >
          <motion.div
            className="px-3 py-1 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-[10px] font-bold shadow-sm flex items-center gap-1"
            whileHover={{ scale: 1.05 }}
          >
            <Icon name="Layers" size={3} />
            <span>Accueil</span>
          </motion.div>
          <motion.div
            className="px-2.5 py-1 text-slate-400 text-[10px] font-medium hover:text-white transition-colors"
            whileHover={{ color: "var(--text-primary)" }}
          >
            Composants
          </motion.div>
          <motion.div
            className="px-2.5 py-1 text-slate-400 text-[10px] font-medium hover:text-white transition-colors"
            whileHover={{ color: "var(--text-primary)" }}
          >
            Docs
          </motion.div>
        </motion.div>
      </motion.div>
    );
  }

  // 4. Chat, AI, Assistant
  if (n.includes("chat") || n.includes("ai") || n.includes("assistant") || n.includes("prompt") || n.includes("copilot") || n.includes("message") || n.includes("bot")) {
    return (
      <div className="w-full p-2 space-y-1.5 select-none">
        <motion.div
          className="flex justify-end"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <motion.div
            className="bg-indigo-600 text-white text-[10px] px-2.5 py-1 rounded-xl rounded-br-none shadow-sm max-w-[150px] truncate font-medium"
            animate={{ scale: [1, 1.02, 1] }}
            transition={{ duration: 0.3 }}
          >
            Générer un composant UI
          </motion.div>
        </motion.div>
        <motion.div
          className="flex items-start gap-1.5"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <motion.div
            className="w-5 h-5 rounded-full bg-gradient-to-tr from-cyan-400 to-indigo-600 flex items-center justify-center text-white text-[8px] font-bold shadow flex-shrink-0"
            animate={{ rotate: [0, 360] }}
            transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
          />
          <motion.div
            className="bg-slate-900/90 border border-indigo-500/30 text-slate-200 text-[10px] px-2.5 py-1 rounded-xl rounded-bl-none shadow-sm flex-1"
            whileHover={{ borderColor: "rgba(99, 102, 241, 0.5)" }}
          >
            <span className="text-cyan-400 font-bold">✓</span> Prêt à l'emploi !
          </motion.div>
        </motion.div>
      </div>
    );
  }

  // 5. Dashboards, KPIs, Charts
  if (n.includes("dashboard") || n.includes("stat") || n.includes("kpi") || n.includes("metric") || n.includes("analytics") || n.includes("chart") || n.includes("graph") || n.includes("sparkline")) {
    return (
      <motion.div
        className="w-full p-2 select-none"
        whileHover={{ scale: 1.02 }}
      >
        <motion.div
          className="rounded-2xl p-2.5 bg-slate-900/90 border border-indigo-500/30 flex items-center justify-between gap-2 shadow-md"
          whileHover={{ borderColor: "rgba(99, 102, 241, 0.5)" }}
        >
          <div>
            <span className="text-[10px] text-slate-400 font-medium block">Téléchargements</span>
            <motion.span
              className="font-display text-sm font-black text-white"
              animate={{ opacity: [1, 0.7, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              142,890
            </motion.span>
            <motion.div
              className="flex items-center gap-0.5 text-[9px] text-emerald-400 font-bold mt-0.5"
              animate={{ x: [0, 2, 0] }}
              transition={{ duration: 3, repeat: Infinity }}
            >
              <motion.span
                initial={{ opacity: [0.6, 1] }}
                animate={{ opacity: [1, 0.6] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                +28.4%
              </motion.span>
            </motion.div>
          </div>
          <div className="flex items-end gap-1 h-9 sparkline-bar">
            <motion.div className="bar short bg-indigo-500/30" />
            <motion.div className="bar md bg-indigo-500/60" />
            <motion.div
              className="bar tall bg-gradient-to-t from-indigo-500 to-cyan-400 shadow-sm shadow-cyan-500"
              animate={{ height: ["32px", "28px", "32px"] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
            <motion.div className="bar md bg-cyan-400" />
          </div>
        </motion.div>
      </motion.div>
    );
  }

  // 6. Inputs, Forms
  if (n.includes("input") || n.includes("form") || n.includes("search") || n.includes("field") || n.includes("select") || n.includes("otp") || n.includes("sign in") || n.includes("sign up") || n.includes("login")) {
    return (
      <motion.div
        className="w-full p-2 flex flex-col justify-center select-none"
        whileHover={{ scale: 1.02 }}
      >
        <motion.div
          className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-900/90 border border-indigo-500/40 text-[11px] text-slate-300 shadow-inner"
          whileHover={{ borderColor: "rgba(99, 102, 241, 0.6)" }}
        >
          <motion.div
            animate={{ scale: [1, 1.1, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <Icon name="Search" size={3.5} />
          </motion.div>
          <span className="truncate font-medium">{name}...</span>
        </motion.div>
      </motion.div>
    );
  }

  // 7. Toggles, Switches
  if (n.includes("toggle") || n.includes("switch") || n.includes("checkbox") || n.includes("radio")) {
    return (
      <div className="w-full flex items-center justify-center gap-3 p-2 select-none">
        <motion.button
          onClick={() => setIsToggled(!isToggled)}
          className={`w-11 h-6 rounded-full p-0.5 flex items-center transition-colors shadow-md ${
            isToggled
              ? "bg-gradient-to-r from-indigo-600 to-purple-600 justify-end shadow-indigo-500/30"
              : "bg-slate-800 justify-start"
          }`}
          whileTap={{ scale: 0.9 }}
        >
          <motion.div
            className="w-5 h-5 rounded-full bg-white shadow-sm"
            animate={{ x: isToggled ? 20 : 0 }}
            transition={{ type: "spring", stiffness: 400, damping: 20 }}
          />
        </motion.button>
        <motion.div
          className="flex items-center gap-1 text-[11px]"
          animate={{ color: isToggled ? "var(--accent)" : "var(--text-muted)" }}
        >
          <motion.div
            animate={{ opacity: [1, 0.5, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <Icon name="Check" size={3.5} />
          </motion.div>
          <span>{isToggled ? "Activé" : "Désactivé"}</span>
        </motion.div>
      </div>
    );
  }

  // 8. Pricing, Plans
  if (n.includes("pricing") || n.includes("plan") || n.includes("subscription") || n.includes("tier") || n.includes("billing") || n.includes("pay") || n.includes("wallet")) {
    return (
      <motion.div
        className="w-full p-2 select-none"
        whileHover={{ scale: 1.02 }}
      >
        <motion.div
          className="rounded-2xl p-2.5 bg-gradient-to-b from-slate-900 to-slate-950 border border-indigo-500/40 flex flex-col justify-between shadow-md"
          whileHover={{ borderColor: "rgba(99, 102, 241, 0.6)" }}
        >
          <div className="flex justify-between items-center">
            <motion.span
              className="text-[10px] font-bold text-slate-200"
              animate={{ opacity: [1, 0.8, 1] }}
              transition={{ duration: 3, repeat: Infinity }}
            >
              PRO PLAN
            </motion.span>
            <span className="text-[8px] bg-indigo-500/20 text-indigo-300 px-1.5 py-0.5 rounded-full font-bold">POPULAIRE</span>
          </div>
          <div className="my-0.5">
            <motion.span
              className="font-display text-base font-black text-white"
              animate={{ scale: [1, 1.02, 1] }}
              transition={{ duration: 3, repeat: Infinity }}
            >
              $29/mois
            </motion.span>
          </div>
          <motion.div
            className="flex items-center gap-1 text-[8px] text-emerald-400 font-medium"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Icon name="Check" size={2.5} />
            <span>Accès illimité aux composants</span>
          </motion.div>
        </motion.div>
      </motion.div>
    );
  }

  // 9. Calendars
  if (n.includes("calendar") || n.includes("date") || n.includes("picker") || n.includes("schedule") || n.includes("time") || n.includes("clock")) {
    return (
      <motion.div
        className="w-full p-2 select-none"
        whileHover={{ scale: 1.02 }}
      >
        <motion.div
          className="rounded-2xl p-2 bg-slate-950 border border-white/10 shadow-sm"
          whileHover={{ borderColor: "rgba(99, 102, 241, 0.3)" }}
        >
          <motion.div
            className="flex items-center justify-between text-[10px] font-bold text-slate-200 mb-1 pb-1 border-b border-white/5"
            animate={{ opacity: [1, 0.7, 1] }}
            transition={{ duration: 4, repeat: Infinity }}
          >
            <span>Août 2026</span>
            <motion.div
              animate={{ rotate: [0, 10, 0] }}
              transition={{ duration: 5, repeat: Infinity }}
            >
              <Icon name="Calendar" size={3.5} />
            </motion.div>
          </motion.div>
          <div className="grid grid-cols-7 gap-1 text-[8px] text-center text-slate-400 font-medium">
            <span>L</span><span>M</span><span>M</span><span>J</span><span>V</span><span>S</span><span>D</span>
            <span className="text-slate-600">28</span><span className="text-slate-600">29</span><span>1</span><span>2</span><span>3</span>
            <motion.span
              className="bg-indigo-600 text-white rounded font-bold shadow-sm"
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              4
            </motion.span>
            <span>5</span>
          </div>
        </motion.div>
      </motion.div>
    );
  }

  // 10. Avatars, Teams
  if (n.includes("avatar") || n.includes("profile") || n.includes("user") || n.includes("team") || n.includes("client") || n.includes("author")) {
    return (
      <motion.div
        className="w-full flex flex-col items-center justify-center gap-1 p-2 select-none"
        whileHover={{ scale: 1.05 }}
      >
        <motion.div
          className="flex -space-x-2"
          animate={{ rotate: [0, 1, -1, 0] }}
          transition={{ duration: 5, repeat: Infinity }}
        >
          {Array.from({ length: 3 }).map((_, i) => (
            <motion.div
              key={i}
              className="w-8 h-8 rounded-full border-2 border-slate-900 flex items-center justify-center text-[10px] font-bold text-white shadow-lg"
              style={{
                background: `linear-gradient(135deg, ${
                  i === 0 ? "var(--accent-strong)" : i === 1 ? "var(--color-axiom-green)" : "var(--color-axiom-yellow)"
                } 0%, ${i === 0 ? "var(--accent)" : i === 1 ? "var(--accent-cyan)" : "var(--color-axiom-red)"} 100%)`,
              }}
              initial={{ scale: 0, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              transition={{ delay: i * 0.1, type: "spring", stiffness: 300 }}
            />
          ))}
          <motion.div
            className="w-8 h-8 rounded-full bg-slate-800 border-2 border-slate-900 flex items-center justify-center text-[9px] font-bold text-slate-300"
            initial={{ scale: 0, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            transition={{ delay: 0.3, type: "spring", stiffness: 300 }}
          />
        </motion.div>
        <motion.span
          className="text-[9px] text-slate-400 font-semibold mt-0.5"
          animate={{ opacity: [0.7, 1, 0.7] }}
          transition={{ duration: 3, repeat: Infinity }}
        >
          Membres Actifs
        </motion.span>
      </motion.div>
    );
  }

  // 11. Badges, Tags
  if (n.includes("badge") || n.includes("tag") || n.includes("pill") || n.includes("chip") || n.includes("status") || n.includes("label")) {
    return (
      <motion.div
        className="w-full flex flex-col items-center justify-center gap-1.5 p-2 select-none"
        whileHover={{ scale: 1.05 }}
      >
        <motion.div
          className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-sm shadow-indigo-500/20"
          animate={{ opacity: [0.8, 1, 0.8] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <motion.span
            className="w-1.5 h-1.5 rounded-full bg-indigo-400"
            animate={{ scale: [1, 1.3, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <span className="truncate max-w-[120px]">{name}</span>
        </motion.div>
        <motion.div
          className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[8px] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
          animate={{ scale: [1, 1.03, 1] }}
          transition={{ duration: 3, repeat: Infinity }}
        >
          <Icon name="Check" size={2.5} />
          <span>Vérifié Pro</span>
        </motion.div>
      </motion.div>
    );
  }

  // 12. Accordions
  if (n.includes("accordion") || n.includes("collapse") || n.includes("faq")) {
    return (
      <div className="w-full p-2 space-y-1 select-none">
        <motion.div
          className="rounded-xl px-2.5 py-1.5 bg-slate-900/90 border border-indigo-500/30 flex items-center justify-between text-[10px] text-white shadow-sm"
          whileHover={{ borderColor: "rgba(99, 102, 241, 0.5)" }}
        >
          <span className="font-semibold truncate max-w-[130px]">{name}</span>
          <motion.div
            animate={{ rotate: 180 }}
            transition={{ duration: 0.3 }}
          >
            <Icon name="Check" size={3} />
          </motion.div>
        </motion.div>
        <motion.div
          className="rounded-xl px-2.5 py-1 bg-slate-950/60 border border-white/5 flex items-center justify-between text-[8px] text-slate-400"
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <span className="truncate max-w-[130px]">Section dépliée fluide...</span>
          <Icon name="Check" size={2.5} />
        </motion.div>
      </div>
    );
  }

  // 13. Media, Carousels
  if (n.includes("carousel") || n.includes("gallery") || n.includes("image") || n.includes("video") || n.includes("slider") || n.includes("media") || n.includes("music") || n.includes("audio") || n.includes("player")) {
    return (
      <motion.div
        className="w-full p-2 select-none"
        whileHover={{ scale: 1.02 }}
      >
        <motion.div
          className="rounded-2xl bg-slate-950 border border-white/10 p-2 flex flex-col items-center justify-between h-20 relative overflow-hidden group"
          whileHover={{ borderColor: "rgba(99, 102, 241, 0.4)" }}
        >
          <motion.div
            className="absolute inset-0 bg-gradient-to-tr from-indigo-500/20 via-purple-500/20 to-cyan-500/20"
            animate={{ opacity: [0.3, 0.4, 0.3] }}
            transition={{ duration: 3, repeat: Infinity }}
          />
          <motion.div
            className="w-8 h-8 rounded-full bg-black/70 backdrop-blur-md flex items-center justify-center text-white my-auto shadow-lg z-10"
            animate={{ scale: [1, 1.1, 1] }}
            transition={{ duration: 3, repeat: Infinity, repeatDelay: 1 }}
          >
            <Icon name="Play" size={4} />
          </motion.div>
          <div className="flex items-center gap-1 z-10">
            <motion.span
              className="w-3.5 h-1 rounded-full bg-white"
              animate={{ opacity: [1, 0.5, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
            <motion.span
              className="w-1 h-1 rounded-full bg-white/40"
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 2, repeat: Infinity, delay: 0.2 }}
            />
            <motion.span
              className="w-1 h-1 rounded-full bg-white/40"
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 2, repeat: Infinity, delay: 0.4 }}
            />
          </div>
        </motion.div>
      </motion.div>
    );
  }

  // 14. Loaders, Skeletons
  if (n.includes("loader") || n.includes("skeleton") || n.includes("spinner") || n.includes("progress") || n.includes("shimmer") || n.includes("loading")) {
    return (
      <motion.div
        className="w-full p-2 flex flex-col items-center justify-center gap-2 select-none"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <motion.div
          className="w-6 h-6 rounded-full border-2 border-indigo-500/20 border-t-indigo-400"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
        <motion.div
          className="w-28 h-1.5 rounded-full bg-slate-800 overflow-hidden"
          initial={{ width: "0%" }}
          animate={{ width: "100%" }}
          transition={{ duration: 1.5, repeat: Infinity, repeatType: "reverse" }}
        >
          <div className="h-full w-2/3 bg-gradient-to-r from-indigo-500 to-cyan-400 rounded-full animate-shimmer" />
        </motion.div>
      </motion.div>
    );
  }

  // 16. Default Universal Component (High-End UI)
  return (
    <motion.div
      className="w-full p-2 flex items-center justify-center select-none"
      whileHover={{ scale: 1.02 }}
    >
      <motion.div
        className="rounded-2xl p-3 bg-gradient-to-br from-slate-900 via-slate-950 to-indigo-950/60 border border-indigo-500/30 flex items-center justify-between gap-2 shadow-md w-full"
        whileHover={{ borderColor: "rgba(99, 102, 241, 0.6)" }}
      >
        <div className="flex items-center gap-2.5 truncate">
          <motion.div
            className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-md flex-shrink-0"
            animate={{ rotate: [0, 5, -5, 0] }}
            transition={{ duration: 5, repeat: Infinity }}
          >
            <Icon name="Zap" size={4} />
          </motion.div>
          <div className="truncate">
            <span className="text-xs font-bold text-white block truncate">{name}</span>
            <span className="text-[9px] text-indigo-300 font-mono font-medium">{apiSymbol || "UI Component"}</span>
          </div>
        </div>
        <motion.span
          className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse flex-shrink-0"
          animate={{ opacity: [1, 0.3, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
        />
      </motion.div>
    </motion.div>
  );
}
