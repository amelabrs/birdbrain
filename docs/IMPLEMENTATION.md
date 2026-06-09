# BirdBrain — Implementation Guide

A spaced-repetition bird identification game for Karnataka birds. Built with FastAPI (Python) backend and vanilla JS frontend, installable as a PWA.

---

## Running the App

### Prerequisites

- Python 3.9+
- pip

### Setup and Launch

```bash
cd ~/birdbrain
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.app:app --reload --port 8000
```

Open **http://localhost:8000** in a browser or phone.

No database, no environment variables needed — all data lives in `data/birds.json`.

---

## Project Structure

```
birdbrain/
├── backend/
│   ├── app.py          # FastAPI server + all API routes
│   ├── quiz.py         # Question generation (1 correct + 3 distractors)
│   └── spaced_rep.py   # Leitner box spaced repetition engine
├── frontend/
│   ├── index.html      # Single-page app shell
│   ├── style.css       # Dark theme, mobile-first
│   ├── app.js          # Quiz logic, audio playback, stats UI
│   └── manifest.json   # PWA manifest (installable on phones)
├── data/
│   ├── birds.json      # Bird catalogue (photos, sounds, facts)
│   └── users/          # Per-user progress files (auto-created)
│       └── default/
│           └── progress.json
├── scripts/
│   ├── add_bird.py         # Interactive: add one bird from eBird URL
│   ├── fetch_bird_urls.py  # Batch: fetch image+sound URLs for a list of names
│   └── download_assets.py  # Download media locally
├── docs/
└── requirements.txt        # fastapi, uvicorn
```

---

## Architecture

### Backend (`backend/app.py`)

FastAPI app with these endpoints:

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/question?mode=photo\|sound\|reverse` | Get next quiz question |
| `POST` | `/api/answer` | Submit an answer, update spaced repetition state |
| `GET` | `/api/stats` | Get user progress summary |
| `POST` | `/api/reset` | Reset all progress |
| `POST` | `/api/session-complete` | End a session; may unlock more birds |
| `GET` | `/api/birds` | List all birds in the catalogue |
| `GET` | `/` | Serve the frontend SPA |

The server is single-user: one shared `SpacedRepetition` instance for all sessions (stored at `data/users/default/progress.json`).

### Quiz Engine (`backend/quiz.py`)

`generate_question(target_bird, all_birds, mode)` returns a question dict with:
- `mode` — photo / sound / reverse
- `prompt` — the image URL, audio URL, or bird name shown to the user
- `choices` — 4 shuffled options (1 correct + 3 random distractors)
- `correct_index` — index of the right answer
- `bird_id`, `fun_fact`

**Variant images/sounds** (30% chance): if a bird has `extra_images` or `extra_sounds` in its JSON entry, one of those may be shown instead of the main one, labelled e.g. "Female" or "Female call".

### Spaced Repetition (`backend/spaced_rep.py`)

Leitner box system — four boxes with different review intervals:

| Box | Review interval | Meaning |
|-----|----------------|---------|
| 1 | Every round | New / recently missed |
| 2 | Every 3rd round | Learning |
| 3 | Every 5th round | Getting there |
| 4 | Every 10th round | Mastered |

- Correct answer → move up one box (max 4)
- Wrong answer → back to Box 1
- Birds in lower boxes get higher random-selection weight: `weight = (5 - box)²`

**Unlocking**: starts with 5 birds. After each session, if accuracy ≥ 80%, 3 more birds unlock (up to the total catalogue size).

**Progress persistence**: saved to `data/users/default/progress.json` after every answer. Tracks per-bird box, correct/wrong counts, last seen round, plus global streak and accuracy.

---

## Data Format (`data/birds.json`)

Each entry:

```json
{
  "id": "white-cheeked-barbet",
  "name": "White-cheeked Barbet",
  "scientific_name": "Psilopogon viridis",
  "image_url": "https://cdn.download.ams.birds.cornell.edu/api/v1/asset/12345/2400",
  "image_credit": "Photographer / Macaulay Library",
  "sound_url": "https://cdn.download.ams.birds.cornell.edu/api/v2/asset/67890/mp3",
  "xc_id": "",
  "sound_tip": "A loud 'kutroo kutroo' — hard to miss",
  "fun_fact": "Drums on hollow branches like a woodpecker.",
  "habitat": "Forests, gardens",
  "karnataka_spots": "Bangalore, Coorg, Western Ghats",
  "ebird_code": "whcbar1",
  "extra_images": [
    { "url": "https://...", "label": "Juvenile", "credit": "..." }
  ],
  "extra_sounds": [
    { "url": "https://...", "label": "Alarm call", "tip": "A sharp chitter." }
  ]
}
```

Bird order in `birds.json` controls unlock order — put easier, common birds first.

---

## Scripts: Running Python for a Series of Bird Names

### Fetch image + sound URLs for multiple birds at once

`scripts/fetch_bird_urls.py` accepts any number of bird names as command-line arguments, looks each one up on eBird, and returns the top-rated Macaulay Library photo and audio URLs.

```bash
python3 scripts/fetch_bird_urls.py "Ashy Prinia" "Indian Pitta" "Coppersmith Barbet"
```

Output: a JSON array printed to stdout with `image_url`, `sound_url`, `image_credit`, `species_code`, and `audio_label` for each bird. Errors (bird not found, network issue) are included per-entry as `"error": "..."` without stopping the batch.

This is the right tool when you have a list of names and want to collect media URLs before manually adding them to `birds.json`.

### Add a single bird interactively

```bash
# From an eBird URL
python3 scripts/add_bird.py https://ebird.org/species/lescou1

# From a bare species code
python3 scripts/add_bird.py lescou1

# Interactive (asks for name or URL)
python3 scripts/add_bird.py
```

Auto-fetches: name, scientific name, top photo, top audio. Prompts for sound tip, fun fact, and Karnataka spots. Writes directly to `data/birds.json`.

After running:
```bash
git add data/birds.json
git commit -m "Add Lesser Coucal"
git push
```

---

## Adding Birds Without Scripts

Edit `data/birds.json` directly — append a new entry before the closing `]`. The app reads bird count dynamically, so no code changes are needed. See [ADDING_BIRDS.md](ADDING_BIRDS.md) for full field reference.

---

## Deploying

The README covers Render deployment. The server start time is captured at startup and exposed at `GET /api/version` so you can confirm when a deploy went live.
