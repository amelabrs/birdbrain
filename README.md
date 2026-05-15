# 🐦 BirdBrain

**A spaced-repetition bird identification game for Karnataka birds.**

Learn to identify 20 common Karnataka birds by photo and sound. Uses a Leitner box system — birds you get wrong appear more often, birds you master fade into review.

## Game Modes

| Mode | How it works |
|------|-------------|
| 📷 **Photo** | See a bird photo → pick the correct name from 4 choices |
| 🔊 **Sound** | Hear a bird call → pick the correct name from 4 choices |
| 🔄 **Reverse** | See a bird name → pick the correct photo from 4 choices |

## Spaced Repetition

- **Box 1**: Every round (new birds, recently missed)
- **Box 2**: Every 3rd round
- **Box 3**: Every 5th round
- **Box 4**: Mastered — every 10th round to prevent forgetting
- Get it **right** → move up one box
- Get it **wrong** → back to Box 1

## The Birds (20 Karnataka Starters)

Indian Peafowl · White-cheeked Barbet · Indian Roller · Black Kite · Brahminy Kite · Indian Pond Heron · Purple Sunbird · Red-whiskered Bulbul · Asian Koel · Greater Coucal · White-throated Kingfisher · Spotted Owlet · Rose-ringed Parakeet · Indian Robin · Jungle Myna · Malabar Whistling Thrush · Black Drongo · Coppersmith Barbet · Oriental Magpie-Robin · Painted Stork

## Quick Start

```bash
git clone https://github.com/amelabrs/birdbrain.git
cd birdbrain
pip install -r requirements.txt
uvicorn backend.app:app --reload
```

Open **http://localhost:8000** on your phone or browser.

## Install as Phone App (PWA)

1. Open `http://localhost:8000` in your phone browser
2. Tap **Share → Add to Home Screen** (iOS) or the install banner (Android)
3. It now looks and feels like a native app

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla HTML/CSS/JS — mobile-first, no frameworks
- **Spaced Repetition**: Leitner box system with weighted random selection
- **Images**: Wikimedia Commons (Creative Commons)
- **PWA**: Installable on any phone via Add to Home Screen

## Project Structure

```
birdbrain/
├── backend/
│   ├── app.py           # FastAPI server + routes
│   ├── quiz.py          # Question generation (1 correct + 3 distractors)
│   └── spaced_rep.py    # Leitner box spaced repetition engine
├── frontend/
│   ├── index.html       # Single-page app
│   ├── style.css        # Dark theme, mobile-first
│   ├── app.js           # Quiz logic, audio playback, stats
│   └── manifest.json    # PWA manifest
├── data/
│   └── birds.json       # 20 Karnataka birds with photos, sounds, facts
└── requirements.txt
```

## Adding More Birds

Edit `data/birds.json` — add entries with:
```json
{
  "id": "your-bird-id",
  "name": "Bird Name",
  "scientific_name": "Genus species",
  "image_url": "https://...",
  "sound_url": "https://...",
  "fun_fact": "Something memorable",
  "habitat": "Where it lives",
  "karnataka_spots": "Where to see it in Karnataka"
}
```

## License

MIT
