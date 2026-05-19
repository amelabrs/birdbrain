#!/usr/bin/env python3
"""Add a new bird to birds.json from an eBird URL.

Usage:
    python3 scripts/add_bird.py https://ebird.org/species/lescou1
    python3 scripts/add_bird.py lescou1
    python3 scripts/add_bird.py              (interactive — asks for name)

Auto-fetches: name, scientific name, photo, sound, eBird code.
You only answer 3 questions: sound_tip, fun_fact, karnataka_spots.
"""

import json
import re
import sys
import urllib.request
import urllib.parse
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "birds.json"
EBIRD_API_KEY = "jfekjedvescr"


def load_birds():
    return json.loads(DATA_FILE.read_text("utf-8"))


def save_birds(birds):
    DATA_FILE.write_text(json.dumps(birds, indent=2, ensure_ascii=False) + "\n", "utf-8")


def make_id(name):
    """Generate bird ID from name: 'Indian Robin' → 'indian-robin'"""
    return name.lower().replace("'", "").replace(" ", "-")


def ask(prompt, required=True):
    while True:
        val = input(f"  {prompt}: ").strip()
        if val or not required:
            return val
        print("    (required — please enter a value)")


def fetch_json(url, headers=None):
    """Fetch JSON from a URL."""
    hdrs = headers or {}
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_taxonomy(species_code):
    """Get bird name and scientific name from eBird taxonomy API."""
    url = f"https://api.ebird.org/v2/ref/taxonomy/ebird?species={species_code}&fmt=json"
    data = fetch_json(url, {"X-eBirdApiToken": EBIRD_API_KEY})
    if data:
        return data[0]["comName"], data[0]["sciName"]
    return None, None


def get_macaulay_asset(species_code, media_type):
    """Get top-rated asset ID from Macaulay Library for a species."""
    url = f"https://search.macaulaylibrary.org/api/v1/search?taxonCode={species_code}&mediaType={media_type}&sort=rating_rank_desc&count=1"
    data = fetch_json(url, {"User-Agent": "BirdBrain/1.0"})
    if data.get("results") and data["results"].get("content"):
        item = data["results"]["content"][0]
        return item["assetId"], item.get("userDisplayName", "Cornell Lab / Macaulay Library")
    return None, None


def lookup_code_from_name(bird_name):
    """Look up eBird species code from bird name."""
    url = f"https://api.ebird.org/v2/ref/taxon/find?locale=en&cat=species&key={EBIRD_API_KEY}&q={urllib.parse.quote(bird_name)}"
    data = fetch_json(url)
    if data:
        return data[0]["code"]
    return None


def parse_species_code(arg):
    """Extract species code from URL or bare code."""
    # Handle: https://ebird.org/species/lescou1
    m = re.search(r"ebird\.org/species/([a-zA-Z0-9]+)", arg)
    if m:
        return m.group(1)
    # Handle bare code like: lescou1
    if re.match(r"^[a-zA-Z0-9]+$", arg):
        return arg
    return None


def main():
    birds = load_birds()
    print(f"\n🐦 BirdBrain — Add New Bird")
    print(f"   Currently {len(birds)} birds in the database.\n")

    species_code = None

    # Check if URL/code was passed as argument
    if len(sys.argv) > 1:
        species_code = parse_species_code(sys.argv[1])
        if not species_code:
            print(f"  ❌ Could not parse species code from: {sys.argv[1]}")
            print(f"  Usage: python3 scripts/add_bird.py https://ebird.org/species/CODE")
            return

    # If no argument, ask for name or URL
    if not species_code:
        user_input = ask("eBird URL or bird name (e.g. https://ebird.org/species/lescou1)")
        species_code = parse_species_code(user_input)
        if not species_code:
            # Treat as bird name, look up code
            print(f"  Looking up '{user_input}' on eBird...")
            species_code = lookup_code_from_name(user_input)
            if not species_code:
                print(f"  ❌ Could not find '{user_input}' on eBird.")
                return

    # Fetch taxonomy
    print(f"  Fetching taxonomy for: {species_code}...")
    name, scientific_name = get_taxonomy(species_code)
    if not name:
        print(f"  ❌ Species code '{species_code}' not found in eBird taxonomy.")
        return

    bird_id = make_id(name)
    print(f"  ✓ {name} ({scientific_name})")

    # Check for duplicates
    if any(b["id"] == bird_id for b in birds):
        print(f"\n  ❌ Bird '{name}' (id: {bird_id}) already exists!")
        return

    # Fetch photo
    print(f"  Fetching top-rated photo...")
    photo_id, photo_credit = get_macaulay_asset(species_code, "photo")
    if photo_id:
        image_url = f"https://cdn.download.ams.birds.cornell.edu/api/v1/asset/{photo_id}/2400"
        print(f"  ✓ Photo found (asset {photo_id}, by {photo_credit})")
    else:
        print(f"  ⚠️  No photo found. You'll need to provide one.")
        image_url = ask("Image URL")
        photo_credit = ask("Image credit")

    # Fetch sound
    print(f"  Fetching top-rated audio...")
    audio_id, audio_credit = get_macaulay_asset(species_code, "audio")
    if audio_id:
        sound_url = f"https://cdn.download.ams.birds.cornell.edu/api/v2/asset/{audio_id}/mp3"
        print(f"  ✓ Sound found (asset {audio_id}, by {audio_credit})")
    else:
        print(f"  ⚠️  No audio found. You'll need to provide one.")
        sound_url = ask("Sound URL (MP3 link)")

    # Only 3 questions!
    print(f"\n── Just 3 questions ──")
    sound_tip = ask("Sound tip (how to remember the call)")
    fun_fact = ask("Fun fact (one interesting thing)")
    karnataka_spots = ask("Karnataka spots (where to find it)")

    # Build bird entry
    bird = {
        "id": bird_id,
        "name": name,
        "scientific_name": scientific_name,
        "image_url": image_url,
        "image_credit": photo_credit,
        "sound_url": sound_url,
        "xc_id": "",
        "sound_tip": sound_tip,
        "fun_fact": fun_fact,
        "habitat": "",
        "karnataka_spots": karnataka_spots,
        "ebird_code": species_code,
    }

    # Optional: extra sounds
    print(f"\n── Extras (optional) ──")
    extra_sounds = []
    while True:
        add = input("  Extra sound? [y/N or paste URL]: ").strip()
        if add.lower() == "n" or add == "":
            break
        if add.startswith("http"):
            es_url = add
        elif add.lower() == "y":
            es_url = ask("  Sound URL")
        else:
            break
        label = ask("  Label (e.g. 'Female call')")
        tip = ask("  Sound tip for this variant", required=False)
        extra_sounds.append({"url": es_url, "label": label, "tip": tip} if tip else {"url": es_url, "label": label, "tip": ""})
    if extra_sounds:
        bird["extra_sounds"] = extra_sounds

    extra_images = []
    while True:
        add = input("  Extra image? [y/N or paste URL]: ").strip()
        if add.lower() == "n" or add == "":
            break
        if add.startswith("http"):
            ei_url = add
        elif add.lower() == "y":
            ei_url = ask("  Image URL")
        else:
            break
        label = ask("  Label (e.g. 'Female')")
        credit = ask("  Image credit", required=False) or "Cornell Lab / Macaulay Library"
        extra_images.append({"url": ei_url, "label": label, "credit": credit})
    if extra_images:
        bird["extra_images"] = extra_images

    # Add to list
    birds.append(bird)
    save_birds(birds)

    print(f"\n  ✅ Added '{name}' to birds.json!")
    print(f"  Total birds now: {len(birds)}")
    print(f"\n  Next steps:")
    print(f"    git add data/birds.json")
    print(f"    git commit -m 'Add {name}'")
    print(f"    git push")
    print(f"  Render will auto-deploy. No code changes needed!\n")


if __name__ == "__main__":
    main()
