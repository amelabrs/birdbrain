#!/usr/bin/env python3
"""Fetch bird image and sound URLs from eBird by parsing embedded page JSON.

Usage:
    python scripts/fetch_bird_urls.py "Ashy Prinia" "Indian Pitta"
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from urllib.parse import quote

import requests


API_KEY = "jfekjedvescr"  # public key from eBird species pages
SESSION = requests.Session()


def find_species_code(bird_name: str) -> tuple[str, str]:
    """Look up eBird species code via taxonomy search API.

    Returns (species_code, corrected_name).  corrected_name == bird_name
    when an exact match is found; otherwise it's the fuzzy-matched name.
    """
    headers = {"X-eBirdApiToken": API_KEY}

    # Collect all candidate common names from eBird search results
    search_terms = [bird_name, bird_name.split()[-1]]
    candidates: dict[str, str] = {}  # common_name_lower -> (code, display_name)

    for term in search_terms:
        url = f"https://api.ebird.org/v2/ref/taxon/find?q={quote(term)}&locale=en"
        taxa = SESSION.get(url, headers=headers, timeout=15).json()
        for t in taxa:
            cn = t["name"].split(" - ")[0].strip()
            candidates[cn.lower()] = (t["code"], cn)

    # 1) Exact match (case-insensitive)
    key = bird_name.lower()
    if key in candidates:
        code, display = candidates[key]
        return code, display

    # 2) Fuzzy match against all candidates
    if candidates:
        close = difflib.get_close_matches(key, candidates.keys(), n=1, cutoff=0.6)
        if close:
            code, display = candidates[close[0]]
            return code, display

    # 3) Last-resort: first API result for the full query
    url = f"https://api.ebird.org/v2/ref/taxon/find?q={quote(bird_name)}&locale=en"
    taxa = SESSION.get(url, headers=headers, timeout=15).json()
    if taxa:
        cn = taxa[0]["name"].split(" - ")[0].strip()
        return taxa[0]["code"], cn
    raise ValueError(f"No species found for '{bird_name}'")


def fetch_bird_urls(bird_name: str) -> dict:
    """Fetch the eBird species page and extract image + audio asset IDs from embedded JSON."""
    code, resolved_name = find_species_code(bird_name)
    if resolved_name.lower() != bird_name.lower():
        print(f"(corrected → {resolved_name})", end=" ", flush=True)
        bird_name = resolved_name
    url = f"https://ebird.org/species/{code}?siteLanguage=en_IN"
    resp = SESSION.get(url, timeout=30)
    resp.raise_for_status()
    html = resp.text

    # Extract photoAssetsJson
    photo_match = re.search(r"var\s+photoAssetsJson\s*=\s*(\{.*?\});\s*$", html, re.DOTALL | re.MULTILINE)
    if not photo_match:
        raise ValueError(f"Could not find photoAssetsJson for {bird_name}")
    photo_data = json.loads(photo_match.group(1))
    photo_asset_id = photo_data["galleryAssets"][0]["asset"]["assetId"]
    photo_credit = photo_data["galleryAssets"][0]["asset"].get("userDisplayName", "")

    # Extract audioAssetsJson
    audio_match = re.search(r"var\s+audioAssetsJson\s*=\s*(\{.*?\});\s*$", html, re.DOTALL | re.MULTILINE)
    if not audio_match:
        raise ValueError(f"Could not find audioAssetsJson for {bird_name}")
    audio_data = json.loads(audio_match.group(1))
    audio_asset_id = audio_data["galleryAssets"][0]["asset"]["assetId"]
    audio_title = audio_data["galleryAssets"][0].get("title", "")

    image_url = f"https://cdn.download.ams.birds.cornell.edu/api/v1/asset/{photo_asset_id}/2400"
    sound_url = f"https://cdn.download.ams.birds.cornell.edu/api/v2/asset/{audio_asset_id}/mp3"

    return {
        "name": bird_name,
        "species_code": code,
        "image_url": image_url,
        "image_credit": f"{photo_credit} / Macaulay Library",
        "sound_url": sound_url,
        "audio_label": f"ML{audio_asset_id} ({audio_title})",
    }


def main(bird_names: list[str]):
    results = []
    for bird in bird_names:
        print(f"Fetching: {bird}...", end=" ", flush=True)
        try:
            data = fetch_bird_urls(bird)
            results.append(data)
            print(f"OK  img=ML{data['image_url'].split('/asset/')[1].split('/')[0]}  "
                  f"snd={data['audio_label']}")
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"name": bird, "error": str(e)})

    print("\n" + "=" * 60)
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python scripts/fetch_bird_urls.py "Bird Name" "Another Bird" ...')
        sys.exit(1)

    main(sys.argv[1:])
