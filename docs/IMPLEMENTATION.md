# BirdBrain — Implementation Guide

A spaced-repetition field-identification quiz. Runs entirely in the browser — no backend, no database. Deployed as a GitHub Pages static site and installable as a PWA.

> **Note:** This document is the source of truth for anyone building a second app in the same pattern (e.g. SnakeBrain). A full adaptation guide is at the bottom.

---

## Current Architecture

**100% static.** No server, no API, no build step.

```
User browser
  └── docs/index.html          ← app shell
  └── docs/app.js              ← quiz logic, UI, audio, session tracking
  └── docs/engine.js           ← spaced repetition engine (Leitner boxes)
  └── docs/style.css           ← field-guide visual theme
  └── docs/sw.js               ← service worker (offline / PWA)
  └── docs/birds.json          ← the entire catalogue (this is what the app reads)
  └── docs/manifest.json       ← PWA manifest (icons, name, theme colour)
```

`data/birds.json` is the **edit copy** kept in the repo root for convenience. It must be manually synced to `docs/birds.json` before pushing (or set up a copy step). The deployed app reads only `docs/birds.json`.

GitHub Pages serves the `docs/` folder. No Render, no server.

---

## File Responsibilities

### `engine.js` — Spaced Repetition

Self-contained Leitner-box engine. Exposes a single global `BirdEngine` object.

| Method | Purpose |
|--------|---------|
| `BirdEngine.init(arr)` | Load the full catalogue array |
| `BirdEngine.getQuestion(mode, overrideIds?)` | Pick a bird and generate a 4-choice question. Pass `overrideIds` for retry-wrong sessions. |
| `BirdEngine.submitAnswer(birdId, chosen, correct)` | Record the answer, update boxes, return result data |
| `BirdEngine.getStats()` | Return accuracy, mastered count, per-bird box state |
| `BirdEngine.reset()` | Wipe all progress from localStorage |

**Leitner boxes:**

| Box | Review interval | Status |
|-----|----------------|--------|
| 1 | Every round | New / missed |
| 2 | Every 3rd round | Learning |
| 3 | Every 5th round | Getting there |
| 4 | Every 10th round | Mastered |

- Correct → move up one box (max 4)
- Wrong → back to Box 1
- Selection weight: `(5 − box)²` — lower boxes appear more often
- Progress stored in `localStorage` under key `birdbrain_progress`

### `app.js` — Quiz Logic

Owns all UI state. Key globals:

| Variable | Purpose |
|----------|---------|
| `currentMode` | `"photo"` / `"sound"` / `"reverse"` |
| `sessions` | Per-mode object tracking `bird`, `total`, `correct`, `wrong[]`, `seen` |
| `autoPlaySound` | Whether to auto-play call on correct answer (persisted) |
| `globalMute` | Master mute — blocks all audio immediately (persisted) |
| `retryIds` | Array of bird IDs for a retry-wrong session; `null` for normal play |
| `_sessionWrongIds` | Snapshot of wrong IDs when summary is shown; used by retry button |

Key functions:

| Function | Purpose |
|----------|---------|
| `loadQuestion()` | Pick next bird, render question screen |
| `submitAnswer(i)` | Check answer, update session, show result |
| `showResult(data, correct)` | Render result screen with fact, umwelt, extras |
| `showSessionSummary()` | End-of-session screen with score, wrong list, retry button |
| `startNewSession()` | Reset session, clear retryIds, restart |
| `startRetrySession()` | Start a mini-session with only the wrong birds from `_sessionWrongIds` |
| `toggleMute()` | Toggle globalMute, stop all audio, update button icon |
| `renderExtras(birdId)` | Render extra images (plumages) and extra sound buttons |
| `toggleUmweltDrawer()` | Expand/collapse the umwelt source citation drawer |

### `style.css` — Visual Theme

Field-guide palette. Key CSS variables:

```css
--bg: #efe8d8           /* warm parchment */
--primary: #3f6b4f      /* forest green — primary buttons */
--accent: #a9762a       /* ochre — retry button, highlights */
--error: #b4472f        /* terracotta — wrong answers, muted state */
--text: #2c2a22
--text-dim: #756d5b
```

Notable utility classes: `.primary-btn`, `.retry-btn`, `.icon-btn`, `.icon-btn.muted`, `.needs-work`, `.umwelt-card`.

---

## Quiz Modes

| Mode | Prompt shown | Answer choices |
|------|-------------|----------------|
| `photo` | A photo of the subject | 4 name labels |
| `sound` | An audio player (auto-plays) | 4 name labels |
| `reverse` | The subject's name | 4 photos |

**Variant system (30% chance):** if a subject has `extra_images` or `extra_sounds`, one may be shown instead of the main one. A gold label appears (e.g. "Female", "Non-breeding adult"). This also applies in reverse mode.

---

## Features

- **Three quiz modes** — photo, sound, reverse
- **Spaced repetition** — Leitner box engine in `engine.js`; progress persists in localStorage
- **Session summary** — score, accuracy %, list of wrong answers
- **Retry wrong** — after a session, button appears to re-quiz only the missed subjects
- **Global mute** — header button instantly silences all audio; icon switches to crossed-out speaker; persists across reloads
- **Auto-play toggle** — option to auto-play sound on correct answer in photo/reverse mode
- **Extra images** — shown in a horizontal scroll strip on the result screen ("Plumages · also look for")
- **Extra sounds** — playable buttons below result ("More calls")
- **Umwelt card** — shown only on correct answers; a short sensory description of the subject's world, with an expandable source drawer (confidence level + citations)
- **Progress stats panel** — accuracy, mastered count, per-subject box state, "needs work" list
- **PWA** — installable on iOS and Android; service worker for offline use

---

## Complete Data Format

Each entry in `birds.json` (rename to `snakes.json` etc. when adapting):

```json
{
  "id": "white-cheeked-barbet",
  "name": "White-cheeked Barbet",
  "scientific_name": "Psilopogon viridis",

  "image_url": "https://cdn.download.ams.birds.cornell.edu/api/v1/asset/126555281/2400",
  "image_credit": "Cornell Lab of Ornithology / Macaulay Library",

  "sound_url": "https://cdn.download.ams.birds.cornell.edu/api/v2/asset/540333/mp3",
  "xc_id": "XC644204",
  "sound_tip": "A loud 'kutroo-kutroo-kutroo' — like a broken record.",

  "fun_fact": "Endemic to the Western Ghats.",
  "habitat": "Moist deciduous forests, gardens, plantations",
  "karnataka_spots": "Coorg, Chikmagalur, Agumbe",
  "ebird_code": "whcbar1",

  "extra_images": [
    {
      "url": "https://...",
      "label": "Female",
      "credit": "Photographer / Source"
    }
  ],

  "extra_sounds": [
    {
      "url": "https://...",
      "label": "Alarm call",
      "tip": "A sharp chitter."
    }
  ],

  "umwelt": "Short paragraph (3 sentences max) describing how this subject perceives its world — not how we see it, but what it senses and attends to. Written in storytelling prose, no technical jargon.",

  "umwelt_sources": {
    "confidence": "A",
    "confidence_label": "Species-specific study",
    "note": "Where the facts come from and any caveats.",
    "citations": [
      "Author Year, Title, Journal"
    ]
  }
}
```

### Field reference

| Field | Required | Notes |
|-------|----------|-------|
| `id` | Yes | Lowercase, hyphenated. Used as the unique key. |
| `name` | Yes | Display name |
| `scientific_name` | Yes | Latin binomial |
| `image_url` | Yes | Direct image URL. Cornell format: `.../asset/ID/2400` |
| `image_credit` | Yes | Attribution string |
| `sound_url` | Yes* | MP3 URL. Leave `""` if no sound. *Not needed if sound mode is removed. |
| `xc_id` | No | Xeno-canto ID for attribution. Can be `""`. |
| `sound_tip` | No | Memory mnemonic for the call |
| `fun_fact` | Yes | One interesting sentence shown on result screen |
| `habitat` | Yes | Shown on result screen |
| `karnataka_spots` | Yes | Location context (rename this field when adapting) |
| `ebird_code` | No | Links to eBird species page. Can be `""`. |
| `extra_images` | No | Array of `{url, label, credit}`. 30% chance of appearing in photo/reverse mode. |
| `extra_sounds` | No | Array of `{url, label, tip}`. 30% chance in sound mode. Playable buttons on result. |
| `umwelt` | No | Sensory world description. Only shown on correct answers. |
| `umwelt_sources` | No | `{confidence, confidence_label, note, citations[]}`. Confidence: A/B/C/FIX. |

**Confidence levels for umwelt:**
- `A` — Species-specific study (direct evidence for this species)
- `B` — Close relative or genus-level evidence
- `C` — General / textbook-level (extrapolated)
- `FIX` — Flagged as needing verification

**Subject order in the JSON controls unlock order.** Put the most common/easiest subjects first.

---

## Image URL Formats

### Cornell Lab / Macaulay Library
```
https://cdn.download.ams.birds.cornell.edu/api/v1/asset/{ASSET_ID}/2400   ← photos
https://cdn.download.ams.birds.cornell.edu/api/v2/asset/{ASSET_ID}/mp3    ← sounds
```
Replace `2400` with `480`, `640`, `1200`, or `1800` for different sizes. The app uses `sizedUrl()` to rewrite sizes dynamically.

### Xeno-canto
```
https://xeno-canto.org/sounds/uploaded/{UPLOADER}/{FILENAME}.mp3
```

Finding asset IDs: Cornell/eBird media pages are currently behind bot protection. The most reliable method is browsing the Macaulay Library directly in a browser, finding the recording or photo, and copying the asset ID from the URL.

---

## Deploying

The `docs/` folder is served by GitHub Pages. To deploy:

```bash
# Edit docs/birds.json (or sync from data/birds.json)
git add docs/birds.json docs/app.js  # etc.
git commit -m "Description of changes"
git push
```

GitHub Pages auto-deploys on push. No build step.

---

## Adapting This App for a New Subject (e.g. SnakeBrain)

### What stays the same
- `engine.js` — copy verbatim, zero changes needed
- `style.css` — copy as-is; just update colour variables and any bird-specific wording
- `sw.js` — copy verbatim (update the cache name string at the top)
- `manifest.json` — update name, short_name, description, icons, theme_color
- The entire spaced repetition, retry-wrong, mute, umwelt, and stats system

### What to rename / change in `app.js`

| Current | Change to |
|---------|-----------|
| `"birdbrain_progress"` (localStorage key) | `"snakebrain_progress"` |
| `"birdbrain_autoplay"` | `"snakebrain_autoplay"` |
| `"birdbrain_mute"` | `"snakebrain_mute"` |
| `fetch("birds.json")` | `fetch("snakes.json")` |

### What to change in `index.html`

- `<title>` and `<h1>` — update to SnakeBrain
- `.subtitle` span text — e.g. "Karnataka · Field Guide"
- Remove the **Sound mode button** if snakes have no audio (or repurpose it — e.g. "Video" or "Habitat")
- Update `manifest.json` link and icon `href`s

### Removing sound mode

If the new subject has no audio, delete the sound mode button from `index.html` and remove the `sound` handling in `app.js`:
- Remove `"sound"` from `setMode()` / mode button logic
- Remove the `#prompt-audio` block from `renderQuestion()`
- Remove sound-mode branches in `showResult()`
- In `engine.js`, the `_soundIds` filter and `mode === "sound"` branch in `getQuestion` can be removed or left (they'll just never be called)

### Data fields for snakes

Replace bird-specific fields with snake-relevant ones. Suggested schema:

```json
{
  "id": "indian-cobra",
  "name": "Indian Cobra",
  "scientific_name": "Naja naja",
  "image_url": "https://...",
  "image_credit": "...",
  "fun_fact": "Can spread a hood up to 10 cm wide as a threat display.",
  "habitat": "Agricultural land, forests, urban outskirts",
  "karnataka_spots": "Widespread across Karnataka — most common in farmland",
  "venomous": true,
  "max_length_cm": 220,
  "iucn_status": "Least Concern",
  "extra_images": [
    { "url": "https://...", "label": "Hood spread" },
    { "url": "https://...", "label": "Juvenile" }
  ],
  "umwelt": "...",
  "umwelt_sources": { ... }
}
```

For fields like `venomous` or `iucn_status` to appear in the UI, add them to `showResult()` in `app.js` (same pattern as `habitat` and `karnataka_spots`).

### Image sources for snakes

- **iNaturalist** (`inaturalist.org`) — large open CC-licensed photo library; direct image URLs work
- **Wikimedia Commons** — reliable, stable URLs
- **Snake India** and **herpetological society pages** — may have downloadable photos with attribution

### Umwelt for snakes

Snakes offer rich umwelt content:
- **Heat-sensing pit organs** (vipers, pythons) — infrared detection of warm-blooded prey
- **Jacobson's organ** — chemosensory tongue-flicking to "taste" the air
- **No external ears** — sense vibration through the jaw and ground
- **Colour vision** limited; UV sensitivity in some species
- **Pressure detection** through body contact with the ground

These are well-documented in herpetological literature — umwelt confidence can often reach A or B.

### Suggested repo name and folder structure

```
snakebrain/
├── docs/
│   ├── index.html
│   ├── app.js
│   ├── engine.js
│   ├── style.css
│   ├── sw.js
│   ├── snakes.json       ← renamed from birds.json
│   └── manifest.json
├── data/
│   └── snakes.json       ← edit copy
└── docs/IMPLEMENTATION.md
```

Enable GitHub Pages on the `docs/` folder. Done.
