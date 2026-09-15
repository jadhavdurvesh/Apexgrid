"""FastAPI stub — wraps the simulation kernel over HTTP.

v0.1: one synchronous endpoint that runs a race and returns the result.
Next steps (Bible Part X): move this to WebSocket streaming so the client
watches the race lap-by-lap in real time instead of getting the result in
one shot, and back it with a real database instead of running everything
in memory per-request.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from .simulation.grid_generator import generate_grid
from .simulation.engine import RaceEngine
from .simulation import history

app = FastAPI(title="APEXGRID API", version="0.1.0")


class RaceRequest(BaseModel):
    seed: Optional[int] = None
    laps: int = 55


@app.get("/")
def root():
    return {"name": "APEXGRID", "status": "kernel v0.1 — one race per request, no persistence layer yet"}


@app.post("/race/run")
def run_race(req: RaceRequest):
    teams, drivers = generate_grid(seed=req.seed)
    engine = RaceEngine(teams, drivers, total_laps=req.laps, seed=req.seed)
    result = engine.run()

    summary = {
        "track": engine.track_name,
        "laps": req.laps,
        "classification": result.classification,
        "fastest_lap": result.fastest_lap,
        "event_count": len(result.events),
    }
    history.save_race_result(summary)
    return summary


@app.get("/history")
def get_history():
    return history.load_history()
