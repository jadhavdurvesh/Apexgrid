# APEXGRID Deployment

## Architecture

APEXGRID is split into a static frontend and a persistent simulation worker:

- `frontend/` — static live dashboard, suitable for GitHub Pages.
- `backend/app/main.py` — FastAPI REST + WebSocket API.
- `backend/app/world_runner.py` — persistent championship process.
- `backend/app/simulation/` — actual lap-by-lap simulation kernel.

## GitHub Pages

The repository includes `.github/workflows/pages.yml`. Enable **Settings → Pages → Source: GitHub Actions**. Every push to `main` publishes `frontend/`.

The frontend needs the deployed API URL. Before loading `app.js`, production hosting can set `window.APEXGRID_API_URL`; otherwise the dashboard falls back to local development at `http://localhost:8000`.

## Persistent worker

GitHub Pages cannot execute Python or keep a simulation process alive. The worker must run on a compute service. `render.yaml` contains a web service and a worker service definition.

Default compressed championship timing:

- Practice: 5 minutes
- Qualifying: 20 minutes
- Race: 90 minutes
- Gap between rounds: 2 hours
- Gap between seasons: 4 hours
- 24 rounds per season

Set `APEXGRID_RACE_MINUTES` to change the real wall-clock duration. The race engine is paced while its actual per-lap physics/AI loop executes; it is not a precomputed result followed by a fake animation.

For a portfolio/demo deployment, use shorter values such as `APEXGRID_RACE_MINUTES=2`, `APEXGRID_QUALIFYING_MINUTES=1`, and `APEXGRID_PRACTICE_MINUTES=1`. For the intended long-running world, restore the defaults.

## Persistence

The current local development database is SQLite. Production should use persistent PostgreSQL/Supabase storage so a worker restart does not erase championship history. The JSON world snapshot is also intended as a local/dev resume mechanism; production persistence should be moved to the shared database.

## Local

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

In a second terminal:

```bash
cd backend
python -m app.world_runner
```

Then serve `frontend/` with any static HTTP server and point it at the API.
