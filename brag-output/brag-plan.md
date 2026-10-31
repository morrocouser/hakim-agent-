# Brag Plan: HakimAgent

## What is this app?
HakimAgent (Axiom v4) est un orchestrateur multi-agents open-source et local-first en Python asynchrone, doté d'un routage déterministe par DAG strict et d'une persistance SQLite intégrée — sans cloud propriétaire ni boîte noire.

## The angle
La plupart des frameworks d'agents IA imposent des clouds opaques, de la télémétrie cachée et des appels séquentiels lents. HakimAgent renverse la table : zéro dépendance externe, routage DAG déterministe typé de bout en bout, et exécution parallèle native en local.

## Hook (first 2-3 seconds)
Une question directe et tranchante qui interpelle tout ingénieur IA :
"Et si vos agents IA ne dépendaient d'aucun cloud propriétaire ?"
Avec le sous-titre : "Ni télémétrie cachée · Ni latence réseau · 100% local."

## Key moments (the middle)
- **Le Reveal de marque** : Typographie éditoriale chaude Claude, badge corail "H", présentation de HakimAgent et de ses 4 piliers chiffrés (0 ms overhead, Strict DAG, asyncio natif, SQLite).
- **La démonstration du DAG en action** : Le graphe interactif du produit s'anime :
  1. Input Node ("prompt utilisateur")
  2. RouterAgent (scoring déterministe 0.94 en 3 ms)
  3. Dispatch parallèle asynchrone sur 3 agents (Scraper 12 ms, Analyzer 48 ms, Writer 21 ms)
  4. Synthèse et streaming SQLite sans un seul appel cloud.
- **La console terminale synchronisée** : Les logs bruts de décision s'affichent en temps réel au rythme de l'exécution.

## Outro / punchline
"Vos agents. Votre machine. Zéro compromis."
La commande d'installation prête à copier : `uv add hakimagent`
Accompagné du label : "Open Source · Local First · Python 3.12+".

## User flow worth showing
Le flow réel du produit :
Prompt utilisateur ("Résume ce dépôt...") → RouterAgent scoring 0.94 (3 ms) → Dispatch parallèle (Scraper, Analyzer, Writer) → Synthèse locale persistée en SQLite (0 cloud call).

## Tone
- Preset: `polished`
- Creative direction: "Sleek, high-performance local AI orchestration for serious engineers"
- Interpretation: Typographie serif élégante (Copernicus / Cormorant Garamond), toile crème chaude `#faf9f5`, touches corail `#cc785c`, panneau de code sombre `#181715`. Animations calmes, fluides et précises. Rien de criard ni de gadget.

## Format: landscape — 1920x1080
## Duration: 18.0s (30 fps)

## Visual identity (from the project)
- Background: `#faf9f5` (warm cream)
- Accent: `#cc785c` (warm coral)
- Secondary Accent: `#5db8a6` (teal) & `#e8a55a` (amber)
- Text primary: `#141413` (warm ink)
- Text muted: `#6c6a64`
- Surface dark: `#181715` (editor / terminal slate)
- Border: `#e6dfd8`
- Display font: `Copernicus, "Cormorant Garamond", Georgia, serif`
- Body font: `Inter, -apple-system, system-ui, sans-serif`
- Mono font: `"JetBrains Mono", ui-monospace, monospace`
- Strongest visual element: Le composant DAG interactif avec nœuds typés et connecteurs verticaux/horizontaux.

## Share copy (draft)
Orchestrez des équipes d'agents IA en local, sans cloud propriétaire ni boîte noire. HakimAgent : DAG déterministe, Python asynchrone et 0 ms d'overhead. 🦀⚡

## Audio direction
- Role: Warm energetic business bed with crisp subtle UI accents
- Music: `happy-beats-business-moves-vol-10-by-ende-dot-app.mp3` (Tempo ~110 BPM)
- Music treatment: Start at 0.0s (volume 0.70), steady upbeat rhythm, swell into outro, gentle fade out at 17.5s - 18.0s.
- Music cue guidance: Preset cues at 109.96 BPM (~0.545s beat interval). Strong cue at 15.82s for the outro punchline reveal.
- Audio-reactive treatment: Subtle breathing glow on the active RouterAgent card and metric badges matching the music cadence.
- SFX posture: Sparse, motion-matched, polished restraint.
- Audio-coupled moments:
  - Scene 2: Soft card reveals on metric badges (`ui/rollover2.ogg` or `ui/click2.ogg`)
  - Scene 3: Subtle tap/click on node dispatch and terminal stream appearance (`interface/click_003.ogg`)
  - Scene 4: Soft impact bell on final CTA reveal (`impact/impactBell_heavy_000.ogg` or `impact/impactSoft_medium_001.ogg`)
- Restraint rule: Pas de sons stridents, pas d'effets sonores de jeu vidéo, volume équilibré sous le mix musical.

## Storyboard

### Scene 1 — Le Hook : Boîtes Noires — 3.0s (0.0s - 3.0s)
Grand titre serif centré avec texte percutant :
"Et si vos agents IA ne dépendaient d'aucun cloud propriétaire ?"
Sous-titre : "Ni télémétrie cachée · Ni latence réseau · 100% en local."
Sequential/interaction: Entrée progressive du titre (0.4s), puis révélation du sous-titre (0.8s), maintien lisible jusqu'à 3.0s.
Audio intent: Ambiance claire et directe, le beat musical s'installe.
Audio-coupled idea: Entrée fluide synchronisée avec le premier temps musical.
Transition mood: Soft crossfade → Scene 2

### Scene 2 — Le Reveal : HakimAgent — 4.0s (3.0s - 7.0s)
Badge corail `H`, nom en grand "HakimAgent", sous-titre "L'orchestrateur multi-agents en Python asynchrone".
En dessous, les 4 cartes métriques du produit arrivent séquentiellement :
1. `0 ms` — Telemetry overhead
2. `Strict DAG` — Routage typé
3. `asyncio` — Parallélisme natif
4. `SQLite` — Persistance locale
Sequential/interaction: yes — les 4 métriques apparaissent l'une après l'autre à 0.4s d'intervalle.
Audio intent: Rythmique, sensation d'efficacité et de précision d'ingénierie.
Audio-coupled idea: Soft UI ticks à chaque carte métrique.
Transition mood: Slide / clean wipe → Scene 3

### Scene 3 — Le Moteur : Strict DAG & Parallélisme — 7.5s (7.0s - 14.5s)
Reproduction fidèle de l'interface DAG et de la console terminale :
- En haut : Pipeline visuel avec le nœud `Input Node`, le nœud central `RouterAgent` (scoring 0.94 · dispatch 3 ms), bifurquant vers 3 branches parallèles (`Scraper 12 ms`, `Analyzer 48 ms`, `Writer 21 ms`), convergeant vers `Synthèse SQLite`.
- En bas : Panneau sombre `#181715` affichant en direct les logs :
  `→ RouterAgent scoring 0.94 dispatch (3 ms)`
  `→ Scraper ·········· OK (12 ms)`
  `→ Analyzer ·········· OK (48 ms)`
  `→ Writer ············ OK (21 ms)`
  `✓ synthèse prête · persistance SQLite · 0 cloud call`
Sequential/interaction: yes — simulation du run : dispatch à 7.8s, exécution parallèle à 8.6s, convergence à 11.2s.
Audio intent: Dynamique, démontrant la puissance et la rapidité du moteur en direct.
Audio-coupled idea: Ticks légers lors de l'activation des nœuds et des logs.
Transition mood: Dramatic wipe → Scene 4

### Scene 4 — L'Outro : uv add hakimagent — 3.5s (14.5s - 18.0s)
Punchline finale :
"Vos agents. Votre machine. Zéro compromis."
Terminal pill centré :
`$ uv add hakimagent` [Copier]
Sous-titre : "Open Source · Local First · Typage Strict Python"
Sequential/interaction: yes — Le dock s'anime, le bouton copier s'active brièvement ("Copié !").
Audio intent: Aboutissement valorisant et satisfaisant.
Audio-coupled idea: Soft impact bell à 15.82s (strong cue), fondu musical en douceur jusqu'à 18.0s.

**Music mood for this video:** Upbeat, polished, clean business-tech.
**Audio summary:** Une montée en puissance rythmée et professionnelle, passant du constat initial au déploiement du DAG, pour finir sur un appel à l'action percutant et élégant.
