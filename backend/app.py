"""BirdBrain — FastAPI Backend.

Endpoints:
    GET  /api/question?mode=photo|sound|reverse  — Get a quiz question
    POST /api/answer                              — Submit an answer
    GET  /api/stats                               — Get user progress
    POST /api/reset                               — Reset progress
    GET  /api/birds                               — List all birds
    GET  /                                         — Serve frontend
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.quiz import generate_question
from backend.spaced_rep import SpacedRepetition

app = FastAPI(title="BirdBrain", version="1.0.0")

# Server start time = deploy time on Render
DEPLOY_TIME = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")

# ── Data ─────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BIRDS: list[dict] = json.loads((DATA_DIR / "birds.json").read_text("utf-8"))
BIRD_MAP: dict[str, dict] = {b["id"]: b for b in BIRDS}
ALL_IDS: list[str] = [b["id"] for b in BIRDS]

# ── Spaced repetition (single-user for now) ──────────────────────────

sr = SpacedRepetition(DATA_DIR)

# ── Models ───────────────────────────────────────────────────────────


class AnswerRequest(BaseModel):
    bird_id: str
    chosen_index: int
    correct_index: int


class SessionCompleteRequest(BaseModel):
    score_pct: int


# ── API Endpoints ────────────────────────────────────────────────────


@app.get("/api/question")
def get_question(
    mode: str = Query("photo", pattern="^(photo|sound|reverse)$"),
    seen: str = Query(""),
):
    unlocked_ids = ALL_IDS
    seen_ids = set(seen.split(",")) if seen else set()
    available = [bid for bid in unlocked_ids if bid not in seen_ids] or unlocked_ids

    if mode == "sound":
        sound_ids = [b["id"] for b in BIRDS if b.get("sound_url")]
        unlocked_sound = [bid for bid in sound_ids if bid in set(unlocked_ids)]
        available_sound = [bid for bid in unlocked_sound if bid not in seen_ids] or unlocked_sound
        bird_id = sr.pick_bird(available_sound)
    else:
        bird_id = sr.pick_bird(available)

    bird = BIRD_MAP[bird_id]
    unlocked_birds = [BIRD_MAP[bid] for bid in unlocked_ids]
    q = generate_question(bird, unlocked_birds, mode=mode)
    q["unlocked_count"] = len(unlocked_ids)
    q["total_bird_count"] = len(ALL_IDS)
    return q


@app.post("/api/answer")
def submit_answer(req: AnswerRequest):
    correct = req.chosen_index == req.correct_index
    stats = sr.record_answer(req.bird_id, correct)
    bird = BIRD_MAP.get(req.bird_id, {})
    return {
        "correct": correct,
        "correct_name": bird.get("name", ""),
        "image_url": bird.get("image_url", ""),
        "fun_fact": bird.get("fun_fact", ""),
        "sound_tip": bird.get("sound_tip", ""),
        "scientific_name": bird.get("scientific_name", ""),
        "habitat": bird.get("habitat", ""),
        "karnataka_spots": bird.get("karnataka_spots", ""),
        "sound_url": bird.get("sound_url", ""),
        "ebird_code": bird.get("ebird_code", ""),
        **stats,
    }


@app.get("/api/stats")
def get_stats():
    return sr.get_stats()


@app.post("/api/reset")
def reset_progress():
    sr.reset()
    return {"status": "ok"}


@app.post("/api/session-complete")
def session_complete(req: SessionCompleteRequest):
    """Called when a session ends. May unlock new birds."""
    result = sr.try_unlock(len(ALL_IDS), req.score_pct)
    return result


@app.get("/api/birds")
def list_birds():
    return [
        {
            "id": b["id"],
            "name": b["name"],
            "scientific_name": b["scientific_name"],
            "image_url": b["image_url"],
            "fun_fact": b["fun_fact"],
            "has_sound": bool(b.get("sound_url")),
        }
        for b in BIRDS
    ]


@app.get("/api/version")
def get_version():
    return {"deploy_time": DEPLOY_TIME, "birds": len(BIRDS)}


# ── Serve frontend & data assets ─────────────────────────────────────

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def serve_index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))
