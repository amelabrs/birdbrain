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

    INITIAL_UNLOCK = 5
    UNLOCK_STEP = 3
    UNLOCK_THRESHOLD = 80  # session accuracy % needed to unlock

    def _load(self) -> dict:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text("utf-8"))
                # Migrate: add unlocked_count if missing
                if "unlocked_count" not in data:
                    data["unlocked_count"] = max(self.INITIAL_UNLOCK, len(data.get("birds", {})))
                return data
            except (json.JSONDecodeError, OSError):
                pass
        return {
            "round": 0,
            "unlocked_count": self.INITIAL_UNLOCK,
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
            # All birds seen recently — pick the most overdue one
            # (highest ratio of rounds_waited / interval)
            overdue = []
            for bid in all_bird_ids:
                b = self._state["birds"][bid]
                interval = self.BOX_INTERVALS.get(b["box"], 10)
                rounds_since = current_round - b["last_seen_round"]
                overdue.append((bid, rounds_since / interval))
            overdue.sort(key=lambda x: x[1], reverse=True)
            # Pick randomly from the top few most-overdue birds
            top = overdue[:max(3, len(overdue) // 4)]
            return random.choice(top)[0]

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
            "unlocked_count": self.get_unlocked_count(),
            "birds": {
                bid: {"box": v["box"], "correct": v["total_correct"], "wrong": v["total_wrong"]}
                for bid, v in birds_state.items()
            },
        }

    def get_unlocked_count(self) -> int:
        return self._state.get("unlocked_count", self.INITIAL_UNLOCK)

    def get_unlocked_ids(self, all_bird_ids: list[str]) -> list[str]:
        """Return the first N bird IDs that are unlocked."""
        n = self.get_unlocked_count()
        return all_bird_ids[:n]

    def try_unlock(self, total_birds: int, session_pct: int) -> dict:
        """After a session, maybe unlock more birds. Returns unlock info."""
        current = self.get_unlocked_count()
        newly_unlocked = 0
        if session_pct >= self.UNLOCK_THRESHOLD and current < total_birds:
            new_count = min(current + self.UNLOCK_STEP, total_birds)
            newly_unlocked = new_count - current
            self._state["unlocked_count"] = new_count
            self._save()
        return {
            "unlocked_count": self.get_unlocked_count(),
            "total_birds": total_birds,
            "newly_unlocked": newly_unlocked,
        }

    def reset(self) -> None:
        self._state = {
            "round": 0,
            "unlocked_count": self.INITIAL_UNLOCK,
            "birds": {},
            "history": [],
            "stats": {"total_correct": 0, "total_wrong": 0, "best_streak": 0, "current_streak": 0},
        }
        self._save()
