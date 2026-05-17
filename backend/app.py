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
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.quiz import generate_question
from backend.spaced_rep import SpacedRepetition

app = FastAPI(title="BirdBrain", version="1.0.0")

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


# ── API Endpoints ────────────────────────────────────────────────────


@app.get("/api/question")
def get_question(mode: str = Query("photo", regex="^(photo|sound|reverse)$")):
    bird_id = sr.pick_bird(ALL_IDS)
    bird = BIRD_MAP[bird_id]

    # For sound mode, skip birds without sound URLs
    if mode == "sound":
        birds_with_sound = [b for b in BIRDS if b.get("sound_url")]
        if birds_with_sound:
            bird_id = sr.pick_bird([b["id"] for b in birds_with_sound])
            bird = BIRD_MAP[bird_id]
        else:
            mode = "photo"  # fallback

    return generate_question(bird, BIRDS, mode=mode)


@app.post("/api/answer")
def submit_answer(req: AnswerRequest):
    correct = req.chosen_index == req.correct_index
    stats = sr.record_answer(req.bird_id, correct)
    bird = BIRD_MAP.get(req.bird_id, {})
    return {
        "correct": correct,
        "correct_name": bird.get("name", ""),
        "fun_fact": bird.get("fun_fact", ""),
        "sound_tip": bird.get("sound_tip", ""),
        "scientific_name": bird.get("scientific_name", ""),
        "habitat": bird.get("habitat", ""),
        "karnataka_spots": bird.get("karnataka_spots", ""),
        **stats,
    }


@app.get("/api/stats")
def get_stats():
    return sr.get_stats()


@app.post("/api/reset")
def reset_progress():
    sr.reset()
    return {"status": "ok"}


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


# ── Serve frontend & data assets ─────────────────────────────────────

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def serve_index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))
