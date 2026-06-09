#!/usr/bin/env python3
"""
Look up bird names on eBird and print review links before adding to birds.json.

OK  → shows resolved name + clickable eBird species page
FAIL → shows a manual search URL; verify the name yourself before adding

Usage:
    python3 scripts/lookup_birds.py
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

API_KEY = "jfekjedvescr"
EBIRD_SPECIES  = "https://ebird.org/species"
EBIRD_SEARCH   = "https://ebird.org/search?q="
TAXONOMY_API   = "https://api.ebird.org/v2/ref/taxonomy/ebird?species={code}&fmt=json"

# (label, search_query, note, hardcoded_code)
# hardcoded_code != "" → skip search, use this code directly (name fetched from taxonomy API)
# hardcoded_code = ""  → search via taxon/find API
# Cotton Teal and Green bird removed per user instruction
LOOKUP_LIST: list[tuple[str, str, str, str]] = [
    # ── Kingfishers ────────────────────────────────────────────────────
    ("White throated kingfisher",  "White-throated Kingfisher",   "",                                                             ""),
    ("Common kingfisher",          "Common Kingfisher",           "",                                                             ""),
    ("Pied Kingfisher",            "Pied Kingfisher",             "",                                                             ""),
    # ── Egrets / Herons ────────────────────────────────────────────────
    ("Little egret",               "Little Egret",                "",                                                             ""),
    ("Greater egret",              "Great Egret",                 "eBird name is 'Great Egret'",                                  ""),
    ("Pond heron",                 "Indian Pond Heron",           "",                                                             ""),
    ("Grey heron",                 "Gray Heron",                  "eBird uses US spelling 'Gray Heron'",                          ""),
    ("Night heron",                "Black-crowned Night Heron",   "most common in Karnataka",                                     ""),
    ("Purple grey heron",          "Purple Heron",                "ambiguous — Grey Heron already listed; trying Purple Heron",  ""),
    # ── Rails / Coots ──────────────────────────────────────────────────
    ("Purple hen",                 "",                            "local name for Purple Swamphen",                               "purswa3"),
    ("Moor hen",                   "",                            "user-resolved on eBird",                                       "lesmoo1"),
    # ── Ducks ──────────────────────────────────────────────────────────
    ("Spotted ducks",              "Indian Spot-billed Duck",     "likely Spot-billed Duck",                                     ""),
    # ── Cormorants ─────────────────────────────────────────────────────
    ("Greater Cormorant",          "Great Cormorant",             "eBird name is 'Great Cormorant'",                             ""),
    ("Lesser Cormorant",           "",                            "Little Cormorant (Microcarbo niger) — fixed from last run",    "litcor1"),
    # ── Storks ─────────────────────────────────────────────────────────
    ("Painted stork",              "Painted Stork",               "",                                                             ""),
    ("Wooly bellied stork",        "",                            "Indian Woolly-necked Stork — fixed from last run (not African wonsto2)", "wonsto1"),
    # ── Raptors ────────────────────────────────────────────────────────
    ("Indian bald eagle",          "White-bellied Sea Eagle",     "no eBird entry for this name; trying White-bellied Sea Eagle", ""),
    ("Brown kite",                 "Black Kite",                  "Black Kite is brown; alt: Brahminy Kite",                     ""),
    ("Black shouldered kite",      "Black-winged Kite",           "eBird calls it Black-winged Kite",                            ""),
    ("Honey buzzard",              "Oriental Honey-buzzard",      "",                                                             ""),
    # ── Bee-eaters ─────────────────────────────────────────────────────
    # avoid="African" so we skip African Green Bee-eater and get the Indian species
    ("Green bee eater",            "Green Bee-eater",             "Indian species (Merops orientalis) — skips African result",    ""),
    # ── Robins / Wagtails ──────────────────────────────────────────────
    ("Indian robin",               "Indian Robin",                "",                                                             ""),
    ("White browed waftail",       "White-browed Wagtail",        "typo fixed: wagtail",                                         ""),
    ("Yellow wagtail",             "Western Yellow Wagtail",      "eBird splits wagtails; Western most common in Karnataka",     ""),
    # ── Barbets / Mynas / Crows / Fowl ────────────────────────────────
    ("Coppersmith batbet",         "Coppersmith Barbet",          "typo fixed: barbet",                                          ""),
    ("Jungle myna",                "Jungle Myna",                 "",                                                             ""),
    ("Jungle crow",                "Large-billed Crow",           "Jungle Crow = Large-billed Crow on eBird",                    ""),
    ("Jungle fowl",                "Red Junglefowl",              "",                                                             ""),
    ("Grey francolin",             "",                            "user-resolved on eBird",                                       "gryfra"),
    # ── Owls ───────────────────────────────────────────────────────────
    ("Scops owl",                  "Indian Scops Owl",            "most likely Karnataka scops owl",                             ""),
    ("Mottled wood owl",           "Mottled Wood Owl",            "",                                                             ""),
    # ── Flycatchers / Monarchs / Flowerpeckers ─────────────────────────
    ("Grey flowerpecker",          "Thick-billed Flowerpecker",   "no 'grey flowerpecker'; trying Thick-billed Flowerpecker",    ""),
    ("Black naped monarch",        "Black-naped Monarch",         "",                                                             ""),
    # ── Pittas ─────────────────────────────────────────────────────────
    ("Indian pita",                "Indian Pitta",                "typo fixed: pitta",                                           ""),
    # ── Weavers / Babblers ─────────────────────────────────────────────
    ("Weaver bird",                "Baya Weaver",                 "most common Karnataka weaver",                                ""),
    ("Jungle babbler",             "Jungle Babbler",              "",                                                             ""),
    ("Yellow babbler",             "Yellow-billed Babbler",       "no 'yellow babbler'; trying Yellow-billed Babbler",           ""),
    # ── Thrushes ───────────────────────────────────────────────────────
    ("Orange headed thrush",       "Orange-headed Thrush",        "",                                                             ""),
    # ── Drongos ────────────────────────────────────────────────────────
    ("Drongo (type 1)",            "Black Drongo",                "two Karnataka drongos: Black and Ashy",                       ""),
    ("Drongo (type 2)",            "Ashy Drongo",                 "",                                                             ""),
    # ── Leafbirds ──────────────────────────────────────────────────────
    ("Leaf bird",                  "Golden-fronted Leafbird",     "Chloropsis aurifrons; most common Karnataka leafbird",        ""),
]


def fetch_json(url: str) -> list | dict:
    headers = {"User-Agent": "BirdBrain/1.0", "X-eBirdApiToken": API_KEY}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def name_from_code(code: str) -> str:
    """Resolve a known species code to its eBird common name."""
    url = TAXONOMY_API.format(code=code)
    data = fetch_json(url)
    if data:
        return data[0]["comName"]
    return f"(code: {code})"


def find_species(query: str, avoid: str = "") -> tuple[str, str]:
    """Return (species_code, resolved_name). If avoid is set, skip results containing that word."""
    url = (
        "https://api.ebird.org/v2/ref/taxon/find"
        f"?locale=en&cat=species&q={urllib.parse.quote(query)}"
    )
    data = fetch_json(url)
    if not data:
        raise ValueError("no results")

    candidates = [(item["code"], item["name"].split(" - ")[0].strip()) for item in data[:10]]

    if avoid:
        preferred = [(c, n) for c, n in candidates if avoid.lower() not in n.lower()]
        if preferred:
            return preferred[0]

    return candidates[0]


def main() -> None:
    L0, L1, L2, L3 = 4, 28, 8, 32

    header = f"{'#':<{L0}}{'Your Name':<{L1}}{'Status':<{L2}}{'Resolved As':<{L3}}eBird URL"
    bar    = "─" * (L0 + L1 + L2 + L3 + 48)

    print(f"\nBirdBrain — eBird lookup ({len(LOOKUP_LIST)} birds)\n")
    print(header)
    print(bar)

    ok_count = fail_count = 0

    for i, (label, query, note, code) in enumerate(LOOKUP_LIST, 1):
        try:
            if code:
                # Hardcoded code — just resolve the display name
                resolved  = name_from_code(code)
                ebird_url = f"{EBIRD_SPECIES}/{code}"
                status    = "OK"
                ok_count += 1
            else:
                avoid = "African" if label == "Green bee eater" else ""
                code, resolved = find_species(query, avoid=avoid)
                ebird_url = f"{EBIRD_SPECIES}/{code}"
                status    = "OK"
                ok_count += 1
        except Exception:
            resolved  = f"(tried: {query or code})"
            ebird_url = f"{EBIRD_SEARCH}{urllib.parse.quote(query or label)}"
            status    = "FAIL"
            fail_count += 1

        print(f"{i:<{L0}}{label:<{L1}}{status:<{L2}}{resolved:<{L3}}{ebird_url}")
        if note:
            indent = " " * (L0 + L1)
            print(f"{indent}↳ {note}")

        time.sleep(0.25)

    print(bar)
    print(f"\n  {ok_count} OK   {fail_count} FAIL   ({len(LOOKUP_LIST)} total)\n")


if __name__ == "__main__":
    main()
