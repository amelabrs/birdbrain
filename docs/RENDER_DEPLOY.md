# Deploying BirdBrain to Render

## Overview

BirdBrain is a single-service Python web app (FastAPI + uvicorn) that serves both the API and static frontend. No database, no environment variables required.

## Repository

- **GitHub**: `https://github.com/amelabrs/birdbrain`
- **Branch**: `main`

## Project Structure

```
birdbrain/
├── backend/
│   ├── __init__.py
│   ├── app.py          ← FastAPI app entry point
│   ├── quiz.py
│   └── spaced_rep.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── data/
│   └── birds.json      ← bird data + image/sound URLs
├── requirements.txt
└── docs/
```

## Render Configuration

### Service Settings

| Setting | Value |
|---------|-------|
| **Type** | Web Service |
| **Name** | `birdbrain` (or any name) |
| **Runtime** | Python |
| **Region** | Oregon (US West) or any |
| **Branch** | `main` |
| **Plan** | Free |

### Build & Start Commands

| Field | Command |
|-------|---------|
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn backend.app:app --host 0.0.0.0 --port $PORT` |

### Environment Variables

None required. The app has no secrets or API keys needed at runtime.

## Step-by-Step (Render Dashboard)

1. Go to https://dashboard.render.com
2. Click **New** → **Web Service**
3. Connect the GitHub repo `amelabrs/birdbrain`
4. Set the following:
   - **Name**: `birdbrain`
   - **Root Directory**: *(leave blank)*
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
5. Select **Free** plan
6. Click **Create Web Service**

## Alternative: render.yaml (Infrastructure as Code)

Add this file to the repo root to enable auto-configuration:

```yaml
services:
  - type: web
    name: birdbrain
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn backend.app:app --host 0.0.0.0 --port $PORT
```

Then go to https://dashboard.render.com → **New** → **Blueprint** → select the repo.

## Auto-Deploy

Render automatically redeploys on every push to `main`. No manual action needed after initial setup.

## Verifying Deployment

- Visit the Render URL (e.g. `https://birdbrain-xxxx.onrender.com`)
- The app should show the quiz UI immediately
- Check `/api/version` to confirm deploy time and bird count

## Notes

- Free tier spins down after 15 minutes of inactivity; first request after idle takes ~30s
- All bird images and sounds are external URLs (Macaulay Library); no local media files are served
- The `$PORT` variable is provided automatically by Render
- Python version: 3.9+ (Render uses 3.11 by default, which is fine)
