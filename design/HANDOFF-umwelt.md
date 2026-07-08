# Handoff — Umwelt block on the BirdBrain result screen

Paste this to Claude (Code) alongside the current `birdbrain/frontend/` repo. The design mock (`umwelt-block-design.html`) shows the target visual and both interaction states.

## Context
The result screen (shown after a **correct** answer) already renders a fun-fact callout. Directly **below** it, add an **Umwelt** block — "what this bird's world is actually like." It reuses the exact left-border callout treatment of the fun-fact box, but tinted **ochre (#a9762a)** — the existing app accent. **Do not introduce any new colour.**

Relevant files: `app.js` (renders the result screen — see `renderExtras()` / `showResult()`), `style.css` (callout + badge styles), `index.html` (`#result-umwelt` container already exists).

## Structure
1. **Header row:** mono uppercase label `UMWELT` (8.5px, ochre, tracked 1.4px) + a muted mono subtitle `what this bird's world is actually like` (8px).
2. **Body:** one paragraph, Newsreader 15px / line-height 1.5, same length and tone as the fun fact.
3. **Footer row:** a confidence **badge** (left) and, on two birds only, a `learn more ↗` text link (right).

## Confidence badge — four tiers
A small pill: coloured dot + short label, mono 10px. Tiers:
- **A** — species-specific study → **green** dot (`#4a8c62`)
- **B** — extended from a close relative → **amber** dot (`var(--accent)`)
- **C** — general avian science → **grey** dot (`var(--text-muted)`)
- **FIX** — a corrected earlier claim → **amber**, label rendered *italic*

Badge border is a 30%-opacity tint of its own colour (grey uses `--line-strong`).

## Interaction
- The badge is the **only** tap target. Tapping toggles an inline **drawer** below the footer (top hairline border) containing a **1–3 sentence note** (IBM Plex Sans 12px, dim) and a **citations** line (mono 10.5px, muted, ` · `-separated). A second tap collapses it.
- Use `aria-expanded` on the badge button and toggle `hidden` on the drawer (matches the existing `toggleUmweltDrawer` pattern in `app.js`).
- **Optional (in mock, not required):** a chevron on the badge that rotates 180° when expanded. Drop it if you want text-only.

## Data shape (already produced by backend `birds.json`)
```
umwelt: "…paragraph…",
umwelt_sources: {
  confidence: "A" | "B" | "C" | "FIX",
  confidence_label: "Species-specific study",   // badge text
  note: "…1–3 sentences…",
  citations: ["Ali & Ripley 1987", "Kumar 2004"],
  reference_url: "https://…"                     // presence → show "learn more ↗"
}
```
Only render the block on correct answers (guard already exists via `umweltEl.dataset.correct === "1"`).

## Exact values (from `style.css` / the mock)
- Card: `padding: 13px 15px 12px; border-radius: 10px; background: color-mix(in oklab, var(--accent) 6%, var(--surface)); border: 1px solid var(--line); border-left: 3px solid var(--accent);`
- Badge: `padding: 4px 9px; border-radius: 20px; gap: 5px; font: 500 10px var(--mono); letter-spacing: 0.4px; white-space: nowrap;`
- Dot: `7px` circle. Drawer: `margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--line);`
- `learn more ↗`: mono 10px, muted, `border-bottom: 1px solid var(--line-strong)`; hover → ochre.

Match the mock pixel-for-pixel; keep the existing CSS variable names so the rest of the result screen is untouched.
