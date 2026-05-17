"""Download bird images from Wikimedia and sounds from xeno-canto.

Usage:
    cd ~/birdbrain
    source .venv/bin/activate
    pip install requests
    python scripts/download_assets.py
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import unquote
from typing import Optional

import requests

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BIRDS_JSON = DATA_DIR / "birds.json"
IMAGES_DIR = DATA_DIR / "images"
SOUNDS_DIR = DATA_DIR / "sounds"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)
SOUNDS_DIR.mkdir(parents=True, exist_ok=True)

# xeno-canto API: search for bird sounds
XC_API = "https://xeno-canto.org/api/2/recordings"

HEADERS = {
    "User-Agent": "BirdBrain/1.0 (Karnataka bird quiz app; contact: amelabrs@gmail.com)"
}


def download_file(url: str, dest: Path, label: str = "") -> bool:
    """Download a file with retry."""
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"  ✓ Already exists: {dest.name}")
        return True

    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30, stream=True)
            if resp.status_code == 200:
                dest.write_bytes(resp.content)
                size_kb = dest.stat().st_size / 1024
                print(f"  ✓ Downloaded: {dest.name} ({size_kb:.0f} KB)")
                return True
            else:
                print(f"  ✗ HTTP {resp.status_code} for {label or url}")
        except Exception as e:
            print(f"  ✗ Attempt {attempt+1}/3 failed: {e}")
            time.sleep(2)
    return False


def fetch_xc_sound(scientific_name: str, bird_id: str) -> str | None:
    """Search xeno-canto for a good recording and download it.

    Returns the local filename if successful, None otherwise.
    """
    dest = SOUNDS_DIR / f"{bird_id}.mp3"
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"  ✓ Sound already exists: {dest.name}")
        return f"/static/../data/sounds/{bird_id}.mp3"

    try:
        # Search for high-quality recordings (A or B rating)
        params = {"query": f'{scientific_name} q:A', "page": 1}
        resp = requests.get(XC_API, params=params, headers=HEADERS, timeout=15)
        data = resp.json()

        recordings = data.get("recordings", [])
        if not recordings:
            # Try without quality filter
            params = {"query": scientific_name, "page": 1}
            resp = requests.get(XC_API, params=params, headers=HEADERS, timeout=15)
            data = resp.json()
            recordings = data.get("recordings", [])

        if not recordings:
            print(f"  ✗ No xeno-canto recordings for {scientific_name}")
            return None

        # Pick the first (highest quality) recording
        rec = recordings[0]
        sound_url = rec.get("file")
        if not sound_url:
            # Build URL from sono small path
            xc_id = rec.get("id")
            sound_url = f"https://xeno-canto.org/{xc_id}/download"

        # Ensure HTTPS
        if sound_url.startswith("//"):
            sound_url = "https:" + sound_url

        print(f"  → xeno-canto: XC{rec.get('id')} by {rec.get('rec', '?')} ({rec.get('q', '?')} quality)")

        if download_file(sound_url, dest, f"{bird_id} sound"):
            return f"data/sounds/{bird_id}.mp3"

    except Exception as e:
        print(f"  ✗ xeno-canto search failed: {e}")

    return None


def download_image(url: str, bird_id: str) -> str | None:
    """Download a Wikimedia image. Returns local path or None."""
    # Determine file extension from URL
    ext = ".jpg"
    lower = url.lower()
    if ".png" in lower:
        ext = ".png"
    elif ".svg" in lower:
        ext = ".svg"

    dest = IMAGES_DIR / f"{bird_id}{ext}"
    if download_file(url, dest, f"{bird_id} image"):
        return f"data/images/{bird_id}{ext}"
    return None


def main():
    birds = json.loads(BIRDS_JSON.read_text("utf-8"))
    print(f"Processing {len(birds)} birds...\n")

    updated = False
    for bird in birds:
        bid = bird["id"]
        name = bird["name"]
        sci = bird["scientific_name"]
        print(f"🐦 {name} ({sci})")

        # Download image
        if bird.get("image_url") and bird["image_url"].startswith("http"):
            local_img = download_image(bird["image_url"], bid)
            if local_img:
                bird["image_local"] = local_img
                updated = True

        # Download sound
        local_snd = fetch_xc_sound(sci, bid)
        if local_snd:
            bird["sound_local"] = local_snd
            updated = True
        time.sleep(1)  # Be polite to xeno-canto API

        print()

    if updated:
        BIRDS_JSON.write_text(json.dumps(birds, indent=2, ensure_ascii=False), "utf-8")
        print("✅ Updated birds.json with local file paths")

    # Summary
    img_count = len(list(IMAGES_DIR.glob("*")))
    snd_count = len(list(SOUNDS_DIR.glob("*.mp3")))
    print(f"\n📊 Assets: {img_count} images, {snd_count} sounds")
    print(f"📁 Images: {IMAGES_DIR}")
    print(f"📁 Sounds: {SOUNDS_DIR}")


if __name__ == "__main__":
    main()
