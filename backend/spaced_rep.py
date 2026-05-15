"""Spaced repetition engine using a simplified Leitner box system.

Box 1: Show every round (new / frequently missed)
Box 2: Show every 3rd round
Box 3: Show every 5th round
Box 4: Mastered — show every 10th round (to prevent forgetting)

Getting it RIGHT moves a bird up one box.
Getting it WRONG sends it back to Box 1.
"""

from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Optional


class SpacedRepetition:
    """Per-user spaced repetition state."""

    SAVE_FILE = "progress.json"

    # Box intervals: how many rounds between appearances
    BOX_INTERVALS = {1: 1, 2: 3, 3: 5, 4: 10}

    def __init__(self, data_dir: Path, user_id: str = "default"):
        self._dir = data_dir / "users" / user_id
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / self.SAVE_FILE
        self._state: dict = self._load()

    def _load(self) -> dict:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text("utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {
            "round": 0,
            "birds": {},  # bird_id -> {box, correct_streak, total_correct, total_wrong, last_seen_round}
            "history": [],  # last 50 answers
            "stats": {"total_correct": 0, "total_wrong": 0, "best_streak": 0, "current_streak": 0},
        }

    def _save(self) -> None:
        self._path.write_text(json.dumps(self._state, indent=2), "utf-8")

    def _ensure_bird(self, bird_id: str) -> dict:
        if bird_id not in self._state["birds"]:
            self._state["birds"][bird_id] = {
                "box": 1,
                "correct_streak": 0,
                "total_correct": 0,
                "total_wrong": 0,
                "last_seen_round": 0,
            }
        return self._state["birds"][bird_id]

    def pick_bird(self, all_bird_ids: list[str]) -> str:
        """Pick the next bird to quiz on, favoring lower boxes."""
        current_round = self._state["round"]

        # Ensure all birds have state
        for bid in all_bird_ids:
            self._ensure_bird(bid)

        # Gather eligible birds (due this round based on box interval)
        eligible = []
        for bid in all_bird_ids:
            b = self._state["birds"][bid]
            interval = self.BOX_INTERVALS.get(b["box"], 10)
            rounds_since = current_round - b["last_seen_round"]
            if rounds_since >= interval:
                # Weight: lower box = higher priority
                weight = (5 - b["box"]) ** 2
                eligible.append((bid, weight))

        if not eligible:
            # All birds seen recently — pick the one with lowest box
            eligible = [(bid, (5 - self._state["birds"][bid]["box"]) ** 2) for bid in all_bird_ids]

        # Weighted random selection
        ids, weights = zip(*eligible)
        return random.choices(ids, weights=weights, k=1)[0]

    def record_answer(self, bird_id: str, correct: bool) -> dict:
        """Record an answer and return updated stats."""
        self._state["round"] += 1
        b = self._ensure_bird(bird_id)
        b["last_seen_round"] = self._state["round"]
        stats = self._state["stats"]

        if correct:
            b["correct_streak"] += 1
            b["total_correct"] += 1
            stats["total_correct"] += 1
            stats["current_streak"] += 1
            if stats["current_streak"] > stats["best_streak"]:
                stats["best_streak"] = stats["current_streak"]
            # Move up one box (max 4)
            if b["box"] < 4:
                b["box"] += 1
        else:
            b["correct_streak"] = 0
            b["total_wrong"] += 1
            stats["total_wrong"] += 1
            stats["current_streak"] = 0
            # Back to box 1
            b["box"] = 1

        # Record in history (keep last 50)
        self._state["history"].append({
            "bird_id": bird_id,
            "correct": correct,
            "round": self._state["round"],
            "ts": int(time.time()),
        })
        self._state["history"] = self._state["history"][-50:]

        self._save()

        total = stats["total_correct"] + stats["total_wrong"]
        return {
            "box": b["box"],
            "streak": stats["current_streak"],
            "best_streak": stats["best_streak"],
            "accuracy": round(stats["total_correct"] / total * 100) if total else 0,
            "total_rounds": self._state["round"],
            "mastered": sum(1 for v in self._state["birds"].values() if v["box"] >= 4),
            "total_birds": len(self._state["birds"]),
        }

    def get_stats(self) -> dict:
        stats = self._state["stats"]
        total = stats["total_correct"] + stats["total_wrong"]
        birds_state = self._state["birds"]
        return {
            "total_rounds": self._state["round"],
            "accuracy": round(stats["total_correct"] / total * 100) if total else 0,
            "current_streak": stats["current_streak"],
            "best_streak": stats["best_streak"],
            "mastered": sum(1 for v in birds_state.values() if v["box"] >= 4),
            "learning": sum(1 for v in birds_state.values() if 2 <= v["box"] <= 3),
            "new": sum(1 for v in birds_state.values() if v["box"] == 1),
            "total_birds": len(birds_state),
            "birds": {
                bid: {"box": v["box"], "correct": v["total_correct"], "wrong": v["total_wrong"]}
                for bid, v in birds_state.items()
            },
        }

    def reset(self) -> None:
        self._state = {
            "round": 0,
            "birds": {},
            "history": [],
            "stats": {"total_correct": 0, "total_wrong": 0, "best_streak": 0, "current_streak": 0},
        }
        self._save()
