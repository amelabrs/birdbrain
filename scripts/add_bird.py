#!/usr/bin/env python3
"""Add a new bird to birds.json from an eBird URL.

Usage:
    python3 scripts/add_bird.py https://ebird.org/species/lescou1
    python3 scripts/add_bird.py lescou1
    python3 scripts/add_bird.py              (interactive — asks for name)

Auto-fetches: name, scientific name, photo, sound, eBird code.
Auto-generates: sound_tip, fun_fact, habitat, karnataka_spots via Claude API.
Set ANTHROPIC_API_KEY in your environment (falls back to manual input if not set).
"""

import json
import os
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
    """Get top-rated asset ID from Macaulay Library for a species (v2 API)."""
    import http.cookiejar
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    opener.addheaders = [("User-Agent", ua)]
    # Establish session and collect XSRF token
    opener.open("https://search.macaulaylibrary.org/")
    xsrf = next((c.value for c in jar if c.name == "XSRF-TOKEN"), "")
    url = (
        f"https://search.macaulaylibrary.org/api/v2/search"
        f"?taxonCode={species_code}&mediaType={media_type}&sort=rating_rank_desc&count=1"
    )
    req = urllib.request.Request(url, headers={
        "User-Agent": ua,
        "Accept": "application/json",
        "Referer": "https://search.macaulaylibrary.org/",
        "X-XSRF-TOKEN": xsrf,
    })
    with opener.open(req) as resp:
        data = json.loads(resp.read())
    if isinstance(data, list) and data:
        item = data[0]
        return item["assetId"], item.get("userDisplayName", "Cornell Lab / Macaulay Library")
    return None, None


def generate_bird_info(name: str, scientific_name: str) -> dict | None:
    """Call Claude API to generate sound_tip, fun_fact, habitat, karnataka_spots."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
    except ImportError:
        print("  (anthropic package not installed — run: pip3 install anthropic)")
        return None

    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""You are helping build a bird identification quiz app for Karnataka, India.

Generate the following for {name} ({scientific_name}):

1. sound_tip: A memorable 1–2 sentence mnemonic for remembering the call. Use sound analogies or comparison words. Example: "A loud rhythmic 'towit-towit-towit' — like a tiny sewing machine. Relentless once you know it."
2. fun_fact: One vivid, memorable fact. 1–2 sentences. Example: "Stitches leaves together with plant fibre to cradle its nest — nature's own tailor."
3. habitat: Brief habitat description for Karnataka. 4–8 words. Example: "Gardens, scrub, forest edges, urban greenery"
4. karnataka_spots: Specific Karnataka locations where birders find this species. 1 sentence. Example: "Dandeli, Coorg, Bhadra Wildlife Sanctuary, Nagarhole"

Respond with ONLY valid JSON with keys: sound_tip, fun_fact, habitat, karnataka_spots. No markdown, no extra text."""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
        text = text.rsplit("```", 1)[0].strip()
    return json.loads(text)


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

    # Auto-generate text fields via Claude
    print(f"\n  Generating bird info with Claude...")
    info = None
    try:
        info = generate_bird_info(name, scientific_name)
    except Exception as e:
        print(f"  ⚠️  Claude generation failed: {e}")

    if info:
        sound_tip       = info.get("sound_tip", "")
        fun_fact        = info.get("fun_fact", "")
        habitat         = info.get("habitat", "")
        karnataka_spots = info.get("karnataka_spots", "")
        print(f"  ✓ Generated:\n")
        print(f"    Sound tip  : {sound_tip}")
        print(f"    Fun fact   : {fun_fact}")
        print(f"    Habitat    : {habitat}")
        print(f"    KA spots   : {karnataka_spots}")
        edit = input("\n  Accept all? [Y/n]: ").strip().lower()
        if edit == "n":
            sound_tip       = input(f"  Sound tip [{sound_tip}]: ").strip() or sound_tip
            fun_fact        = input(f"  Fun fact [{fun_fact[:40]}...]: ").strip() or fun_fact
            habitat         = input(f"  Habitat [{habitat}]: ").strip() or habitat
            karnataka_spots = input(f"  KA spots [{karnataka_spots[:40]}...]: ").strip() or karnataka_spots
    else:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("  (set ANTHROPIC_API_KEY to enable auto-generation)")
        print(f"\n── Manual input ──")
        sound_tip       = ask("Sound tip (how to remember the call)")
        fun_fact        = ask("Fun fact (one interesting thing)")
        habitat         = ask("Habitat (brief, e.g. 'Gardens, scrub, forest edges')", required=False)
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
        "habitat": habitat,
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
