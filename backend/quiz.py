"""Quiz engine — generates questions with distractors."""

from __future__ import annotations

import random
from typing import Any


def generate_question(
    target_bird: dict,
    all_birds: list[dict],
    mode: str = "photo",
) -> dict:
    """Generate a quiz question.

    Parameters
    ----------
    target_bird : dict
        The correct bird entry.
    all_birds : list[dict]
        All bird entries (used to pick distractors).
    mode : str
        "photo" (show image, pick name) or "sound" (play call, pick name)
        or "reverse" (show name, pick image).

    Returns
    -------
    dict with keys: mode, prompt (image/sound URL or name),
    choices (4 items), correct_index, bird_id, fun_fact.
    """
    # Pick 3 random distractors (different from target)
    others = [b for b in all_birds if b["id"] != target_bird["id"]]
    distractors = random.sample(others, min(3, len(others)))

    if mode == "reverse":
        # Show name → pick image
        choices = [
            {"label": target_bird["name"], "image_url": target_bird["image_url"], "id": target_bird["id"]},
        ] + [
            {"label": d["name"], "image_url": d["image_url"], "id": d["id"]}
            for d in distractors
        ]
        random.shuffle(choices)
        correct_index = next(i for i, c in enumerate(choices) if c["id"] == target_bird["id"])

        return {
            "mode": "reverse",
            "prompt": target_bird["name"],
            "prompt_type": "text",
            "choices": choices,
            "correct_index": correct_index,
            "bird_id": target_bird["id"],
            "fun_fact": target_bird["fun_fact"],
        }

    # photo or sound mode → pick name from 4 choices
    choices = [
        {"label": target_bird["name"], "id": target_bird["id"]},
    ] + [
        {"label": d["name"], "id": d["id"]}
        for d in distractors
    ]
    random.shuffle(choices)
    correct_index = next(i for i, c in enumerate(choices) if c["id"] == target_bird["id"])

    if mode == "sound":
        prompt = target_bird.get("sound_url", "")
        prompt_type = "audio"
    else:
        prompt = target_bird["image_url"]
        prompt_type = "image"

    return {
        "mode": mode,
        "prompt": prompt,
        "prompt_type": prompt_type,
        "choices": choices,
        "correct_index": correct_index,
        "bird_id": target_bird["id"],
        "fun_fact": target_bird["fun_fact"],
    }
