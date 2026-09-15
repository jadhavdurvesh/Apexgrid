# APEXGRID Deployment

## Architecture

- `frontend/` is a static live dashboard and is deployed by GitHub Pages.
- `backend/` contains FastAPI and the simulation engine.
- `backend/app/world_runner.py` is the persistent world worker.
- Production persistence should use PostgreSQL/Supabase; SQLite is for local development/tests.

## GitHub Pages

Enable **Settings → Pages → Source: GitHub Actions**. The `pages.yml` workflow publishes `frontend/` from `main`.

The browser needs the production API URL. For a simple deployment, set `window.APEXGRID_API_URL` before `app.js` loads, or configure it in `frontend/app.js`.

## Persistent worker

Run the worker on an always-on VM/container:

```bash
cd backend
pip install -r requirements.txt
python -m app.world_runner
```

The worker continuously runs 24 rounds per season and then starts the next season. Race duration defaults to 90 minutes and can be changed with `APEXGRID_RACE_MINUTES`.

## Live 2D viewer

The dashboard connects to `/ws/live`. During a race, the backend publishes lap state, driver telemetry, weather and race events. The browser renders each car on a 2D circuit path and smoothly advances it between server updates.

## Cloud note

GitHub Pages cannot execute the Python worker. Use an always-on VM/container for the worker/API. A free VM may be suitable for development, but free compute quotas and availability can change; do not treat a provider's free tier as a permanent SLA.

## Local demo

```bash
cd backend
python -m pytest tests/ -v
uvicorn app.main:app --reload
```

In a second terminal:

```bash
cd backend
APEXGRID_RACE_MINUTES=2 APEXGRID_PRACTICE_MINUTES=0 APEXGRID_QUALIFYING_MINUTES=0 APEXGRID_ROUND_GAP_HOURS=0 APEXGRID_SEASON_GAP_HOURS=0 python -m app.world_runner
```

Use short durations for development only. Production should use the real-time values.
