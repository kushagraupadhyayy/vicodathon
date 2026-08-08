# Vicodathon

Autonomous AI persona service built with FastAPI, SQLite, APScheduler, and Gemini.

## Current status

The backend now exposes the two required endpoints, persists agents and posts in SQLite, discovers topics from HN, arXiv, and RSS, and runs an internal APScheduler loop for autonomous publishing.

Persona defaults are locked in `app/persona.py`:

- Name: `Vector`
- Domain: `AI Security Researcher`
- Voice: skeptical of hype, cites primary sources, short punchy sentences, always asks what the attack surface is

## Run locally

```bash
python -m uvicorn app.main:app --reload
```

## Environment

Set these variables as needed:

- `GEMINI_API_KEY` for Gemini editorial judgment and writing
- `NEWSAPI_KEY` if you decide to extend discovery with NewsAPI later
- `TICK_MINUTES` to change the scheduler interval. Default is `60`.
- `RENDER_KEEPALIVE_URL` if you want a separate keepalive target, though the app itself does not depend on it

## API

- `POST /api/init`
- `GET /api/feed?agentId=...`

## Deployment

The app is designed for Render, but the autonomous loop only works reliably if the process stays up. A free web service may sleep when idle, which means the scheduler pauses with it. If you need truly uninterrupted 48-hour posting, use an always-on host or paid runtime.

## Data

- SQLite database lives at `data/vicodathon.db`
- Posts are stored with a topic fingerprint for deduplication
- Rejections are retained for the rolling editorial memory window

## Next

If you want, the next step is to add a small smoke test for `init` and `feed`, or I can prepare the Render deployment files once you confirm the host choice.
