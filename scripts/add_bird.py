#!/usr/bin/env python3
"""Add a new bird to birds.json interactively.

Run: python3 scripts/add_bird.py

It will ask you for each field and add the bird to data/birds.json.
It can also look up the eBird species code automatically.
"""

import json
import urllib.request
import urllib.parse
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "birds.json"


def load_birds():
    return json.loads(DATA_FILE.read_text("utf-8"))


def save_birds(birds):
    DATA_FILE.write_text(json.dumps(birds, indent=2, ensure_ascii=False) + "\n", "utf-8")


def lookup_ebird_code(bird_name):
    """Look up eBird species code from bird name."""
    url = f"https://api.ebird.org/v2/ref/taxon/find?locale=en&cat=species&key=jfekjedvescr&q={urllib.parse.quote(bird_name)}"
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read())
            if data:
                code = data[0]["code"]
                print(f"  Found: {data[0]['name']} → {code}")
                return code
            else:
                print("  ⚠️  Not found on eBird. You can add it manually later.")
                return ""
    except Exception as e:
        print(f"  ⚠️  Lookup failed: {e}")
        return ""


def make_id(name):
    """Generate bird ID from name: 'Indian Robin' → 'indian-robin'"""
    return name.lower().replace("'", "").replace(" ", "-")


def ask(prompt, required=True):
    while True:
        val = input(f"  {prompt}: ").strip()
        if val or not required:
            return val
        print("    (required — please enter a value)")


def main():
    birds = load_birds()
    print(f"\n🐦 BirdBrain — Add New Bird")
    print(f"   Currently {len(birds)} birds in the database.\n")

    name = ask("Bird name (e.g. 'Indian Robin')")
    bird_id = make_id(name)

    # Check for duplicates
    if any(b["id"] == bird_id for b in birds):
        print(f"\n  ❌ Bird '{name}' (id: {bird_id}) already exists!")
        return

    print(f"\n  ID will be: {bird_id}")
    print(f"\n── Required fields ──")

    scientific_name = ask("Scientific name (e.g. 'Copsychus fulicatus')")
    image_url = ask("Image URL (full URL to a bird photo)")
    image_credit = ask("Image credit (e.g. 'Wikimedia Commons (CC BY-SA)')")
    sound_url = ask("Sound URL (MP3 link — from xeno-canto or Cornell)")
    xc_id = ask("Xeno-canto ID (e.g. 'XC955886', or leave blank)", required=False)
    sound_tip = ask("Sound tip (mnemonic to remember the call)")
    fun_fact = ask("Fun fact (one interesting thing about this bird)")
    habitat = ask("Habitat (e.g. 'Open fields, gardens')")
    karnataka_spots = ask("Karnataka spots (where to find it)")

    # eBird code
    print(f"\n── eBird code ──")
    print(f"  Looking up '{name}' on eBird...")
    ebird_code = lookup_ebird_code(name)
    if not ebird_code:
        ebird_code = ask("Enter eBird species code manually (or leave blank)", required=False)

    # Build bird entry
    bird = {
        "id": bird_id,
        "name": name,
        "scientific_name": scientific_name,
        "image_url": image_url,
        "image_credit": image_credit,
        "sound_url": sound_url,
        "xc_id": xc_id,
        "sound_tip": sound_tip,
        "fun_fact": fun_fact,
        "habitat": habitat,
        "karnataka_spots": karnataka_spots,
        "ebird_code": ebird_code,
    }

    # Optional: extra sounds
    print(f"\n── Extra sounds (optional) ──")
    extra_sounds = []
    while True:
        add = input("  Add an extra sound (e.g. female call)? [y/N]: ").strip().lower()
        if add != "y":
            break
        url = ask("  Sound URL")
        label = ask("  Label (e.g. 'Female call')")
        tip = ask("  Sound tip for this variant")
        extra_sounds.append({"url": url, "label": label, "tip": tip})

    if extra_sounds:
        bird["extra_sounds"] = extra_sounds

    # Optional: extra images
    print(f"\n── Extra images (optional) ──")
    extra_images = []
    while True:
        add = input("  Add an extra image (e.g. female plumage)? [y/N]: ").strip().lower()
        if add != "y":
            break
        url = ask("  Image URL")
        label = ask("  Label (e.g. 'Female')")
        credit = ask("  Image credit")
        extra_images.append({"url": url, "label": label, "credit": credit})

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
