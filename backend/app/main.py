"""APEXGRID production API: REST + live WebSocket world feed."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import threading
from .simulation.grid_generator import generate_grid
from .simulation.engine import RaceEngine
from .simulation import history
from . import world
from . import world_runner

app=FastAPI(title="APEXGRID API",version="0.2.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])

_world_thread=None
@app.on_event("startup")
def start_world_runner():
    global _world_thread
    if _world_thread is not None and _world_thread.is_alive():
        return
    _world_thread=threading.Thread(target=world_runner.main,daemon=True,name="apexgrid-world-runner")
    _world_thread.start()

class RaceRequest(BaseModel):
 seed:Optional[int]=None
 laps:int=55
@app.get("/")
def root():return {"name":"APEXGRID","status":"online","version":"0.2.0"}
@app.get("/health")
def health():return {"status":"ok","world":world.snapshot()["state"]}
@app.get("/world")
def get_world():return world.snapshot()
@app.post("/race/run")
def run_race(req:RaceRequest):
 teams,drivers=generate_grid(seed=req.seed);engine=RaceEngine(teams,drivers,total_laps=req.laps,seed=req.seed);result=engine.run()
 summary={"track":engine.track_name,"laps":req.laps,"classification":result.classification,"fastest_lap":result.fastest_lap,"event_count":len(result.events)}
 history.save_race_result(summary);world.update(state="RACE_COMPLETE",track=engine.track_name,lap=req.laps,lap_total=req.laps,message="Race complete");return summary
@app.get("/history")
def get_history():return history.load_history()
@app.websocket("/ws/live")
async def live(ws:WebSocket):
 await ws.accept();q=world.subscribe()
 try:
  await ws.send_json({"type":"world","data":world.snapshot()})
  while True:await ws.send_json(await q.get())
 except (WebSocketDisconnect,RuntimeError):pass
 finally:world.unsubscribe(q)
