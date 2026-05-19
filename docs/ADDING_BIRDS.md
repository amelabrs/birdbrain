# BirdBrain — Adding New Birds

This guide explains how to add birds to the quiz **without writing any code**.

---

## Quick Summary

1. Run `python3 scripts/add_bird.py`
2. Answer the prompts
3. `git push`
4. Done — Render auto-deploys

---

## Method 1: Use the Helper Script (Recommended)

```bash
cd ~/birdbrain
python3 scripts/add_bird.py
```

The script will:
- Ask you for each field (name, image URL, sound URL, etc.)
- Auto-generate the bird ID from the name
- Look up the eBird species code automatically
- Offer to add female/variant images and sounds
- Save everything to `data/birds.json`

After running it:
```bash
git add data/birds.json
git commit -m "Add [bird name]"
git push
```

Render will auto-deploy. The UI will automatically show the new bird count.

---

## Method 2: Edit birds.json Manually

Open `data/birds.json` and add a new entry at the end (before the closing `]`):

```json
  {
    "id": "indian-robin",
    "name": "Indian Robin",
    "scientific_name": "Copsychus fulicatus",
    "image_url": "https://example.com/photo.jpg",
    "image_credit": "Photographer Name / Source (License)",
    "sound_url": "https://example.com/call.mp3",
    "xc_id": "XC123456",
    "sound_tip": "A short descending whistle...",
    "fun_fact": "Something interesting about this bird.",
    "habitat": "Open scrubland, gardens",
    "karnataka_spots": "Bangalore, Mysore",
    "ebird_code": "indrob1"
  }
```

### Required Fields

| Field | What it is | Where to find it |
|-------|-----------|------------------|
| `id` | Lowercase name with dashes (e.g. `indian-robin`) | Make it yourself |
| `name` | Display name | — |
| `scientific_name` | Latin name | Wikipedia or eBird |
| `image_url` | Direct link to a bird photo | Wikimedia, Cornell Macaulay Library |
| `image_credit` | Credit for the photo | — |
| `sound_url` | Direct MP3 link to bird call | [xeno-canto.org](https://xeno-canto.org) or Cornell |
| `xc_id` | Xeno-canto recording ID (optional, can be `""`) | xeno-canto.org |
| `sound_tip` | Mnemonic to remember the call | Write your own! |
| `fun_fact` | One-liner about the bird | — |
| `habitat` | Habitat description | — |
| `karnataka_spots` | Where to find it in Karnataka | — |
| `ebird_code` | eBird species code | See below |

### Finding the eBird Code

Go to: `https://ebird.org` → search for the bird → the code is in the URL:
```
https://ebird.org/species/indrob1  ← "indrob1" is the code
```

Or the script does this automatically.

---

## Adding a Female / Variant Image

Add an `extra_images` array to any bird:

```json
{
  "id": "purple-sunbird",
  "name": "Purple Sunbird",
  ...
  "extra_images": [
    {
      "url": "https://example.com/female.jpg",
      "label": "Female",
      "credit": "Photographer / Source"
    },
    {
      "url": "https://example.com/nonbreeding.jpg",
      "label": "Non-breeding male",
      "credit": "Photographer / Source"
    }
  ]
}
```

These will appear with a 30% chance in Photo mode, showing a gold "📷 Female" label.

---

## Adding Extra Bird Calls

Add an `extra_sounds` array to any bird:

```json
{
  "id": "asian-koel",
  "name": "Asian Koel",
  ...
  "extra_sounds": [
    {
      "url": "https://example.com/female-call.mp3",
      "label": "Female call",
      "tip": "A rapid 'kik-kik-kik' — completely different from the male."
    }
  ]
}
```

These will appear with a 30% chance in Sound mode, showing a gold "🎵 Female call" label.

---

## Where to Find Bird Media

### Photos
- **Macaulay Library** (Cornell): https://macaulaylibrary.org — use asset URLs like `https://cdn.download.ams.birds.cornell.edu/api/v1/asset/ASSET_ID/2400`
- **Wikimedia Commons**: search for bird, use the direct image URL

### Sounds
- **Xeno-canto**: https://xeno-canto.org — find the recording, use the download MP3 link
- **Cornell/Macaulay**: `https://cdn.download.ams.birds.cornell.edu/api/v2/asset/ASSET_ID/mp3`

---

## Bird Order Matters (for Memory Mode)

Birds are quizzed in **the order they appear in birds.json** when using Memory (drip feed) mode. The first 5 birds are unlocked initially. Put easier/common birds first, rare ones last.

---

## No Code Changes Needed

The app dynamically counts birds from `birds.json`. Adding or removing entries automatically updates:
- "Bird X of Y" counter
- Session length
- Unlock progress ("5 of 29 birds unlocked")
- Stats panel

Just edit `birds.json` and push!
