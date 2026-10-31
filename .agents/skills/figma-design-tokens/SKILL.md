---
name: 'figma-design-tokens'
description: 'Expert Figma design systems & UI/UX translation engineer - inspect files, extract frames, components, design tokens (colors, typography, spacing, shadows), and convert to React/Tailwind code.'
---

# Figma Design Tokens & Code Generation Skill

Translate Figma designs into production-ready frontend code, design tokens, and components with 1:1 visual fidelity.

## Core Capabilities

1. **Design Token Extraction**:
   - Extract color palettes (HEX, RGBA, HSL) with semantic naming (`background/paper`, `brand/primary`, `status/warning`).
   - Extract typography scales (font-family, font-size, line-height, letter-spacing, font-weight).
   - Extract spacing rules, border-radii, grid alignments, and drop-shadow definitions.
   - Output directly to Tailwind CSS `tailwind.config.ts`, CSS custom properties (`:root`), or JSON format.

2. **Component Tree Mapping**:
   - Convert Auto Layout frames to Flexbox/Grid (`layoutMode: VERTICAL` -> `flex flex-col`, `itemSpacing` -> `gap-*`).
   - Map padding, margins, and alignments (`paddingLeft`, `paddingTop` -> `px-* py-*`).
   - Identify component variants and props (e.g. `Button` [primary | secondary | outline], sizes [sm | md | lg]).

3. **Asset & Image Pipeline**:
   - Query image exports via Figma REST API (`/v1/images/:key?ids=...&format=svg/png`).
   - Clean SVG vectors and convert them to React components or Lucide-compatible icons.

4. **Integration with HakimAgent**:
   - Tool `figma_manager`:
     - `get_file`: Retrieve entire file metadata and document structure.
     - `get_nodes`: Focus on a single frame or component ID.
     - `get_components`: List reusable components across the library.
     - `get_styles`: Inspect color, text, and effect styles.
     - `export_images`: Get download URLs for renders.
     - `extract_tokens`: Generate structured CSS variables and token objects.
     - `status`: Validate API key and connectivity.

## Design to Tailwind Translation Cheatsheet

| Figma Property | Tailwind Equivalent | CSS Variable |
| :--- | :--- | :--- |
| `layoutMode: HORIZONTAL` | `flex flex-row items-center` | `display: flex; flex-direction: row;` |
| `layoutMode: VERTICAL` | `flex flex-col` | `display: flex; flex-direction: column;` |
| `itemSpacing: 16` | `gap-4` | `gap: 1rem;` |
| `paddingTop: 24, paddingLeft: 24` | `p-6` | `padding: 1.5rem;` |
| `cornerRadius: 12` | `rounded-xl` | `border-radius: 0.75rem;` |
| `backgroundColor: #0b0f19` | `bg-slate-950` / `bg-[#0b0f19]` | `background: var(--bg-dark);` |
| `effects: DROP_SHADOW` | `shadow-lg shadow-black/20` | `box-shadow: 0 10px 15px -3px ...;` |
