# BirdBrain — Local Development Setup

## Requirements

- Python 3.9+
- pip

## Create Virtual Environment

```bash
cd ~/birdbrain
python3 -m venv .venv
source .venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `fastapi` — web framework
- `uvicorn` — ASGI server

## Run Locally

```bash
uvicorn backend.app:app --reload --port 8000
```

Then open http://localhost:8000

## Notes

- No database required — data lives in `data/birds.json`
- No environment variables needed
- The `.venv/` directory is already in `.gitignore`
