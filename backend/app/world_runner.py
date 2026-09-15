"""APEXGRID continuous world runner with a genuinely paced race loop."""
import os,random,time
from . import world
from .simulation.grid_generator import generate_grid
from .simulation.engine import RaceEngine
from .simulation import db
from .simulation import newsroom
from .simulation.qualifying import run_qualifying
from .simulation.weather import Weather

CALENDAR=[('Meridian Circuit',55),('Solstice Street Course',48),('Halcyon Ring',60),('Obsidian Grand Prix Circuit',52),('Voltage Speedway',44),('Zenith Highlands',58),('Ironclad Docklands',50),('Kestrel Coastal Loop',56),('Aurora Park',53),('Titan Valley',49),('Neon Harbour',51),('Atlas International',57),('Vortex Raceway',46),('Silver Coast',54),('Granite Peak',61),('Sapphire City',47),('Solaris Circuit',58),('Black Forest Ring',52),('Crown Street GP',45),('Redline International',59),('Northstar Circuit',50),('Eclipse Bay',55),('Thunder Plains',48),('Finale Grand Prix Circuit',62)]
STARTING_SEASON=int(os.getenv('APEXGRID_START_SEASON','1'));RACE_MINUTES=float(os.getenv('APEXGRID_RACE_MINUTES','90'));QUALIFYING_MINUTES=float(os.getenv('APEXGRID_QUALIFYING_MINUTES','20'));PRACTICE_MINUTES=float(os.getenv('APEXGRID_PRACTICE_MINUTES','5'));ROUND_GAP_HOURS=float(os.getenv('APEXGRID_ROUND_GAP_HOURS','2'));SEASON_GAP_HOURS=float(os.getenv('APEXGRID_SEASON_GAP_HOURS','4'))
COLORS=['#ff3b30','#ffd60a','#30d158','#0a84ff','#bf5af2','#64d2ff','#ff9f0a','#ff375f','#5e5ce6','#ac8e68']
def sleep_minutes(minutes):
 end=time.monotonic()+max(0,minutes*60)
 while time.monotonic()<end: time.sleep(min(1,end-time.monotonic()))
def season_name(n): return f'Season {n:03d}'
def cards_for(teams,drivers):
 ordered=sorted(drivers.values(),key=lambda d:d.base_pace_score(),reverse=True)
 return [{'driver_id':d.driver_id,'driver_name':d.name,'team':teams[d.team_id].name,'position':i+1,'color':COLORS[i%len(COLORS)],'speed':0,'gap':'—','tyres':'MEDIUM','fuel':100,'energy':100,'lap_time':0,'progress':0} for i,d in enumerate(ordered)]
def publish_lap(engine,lap,cumulative,lap_times,cards,season,round_number,track):
 ordered=sorted(engine.cars.values(),key=lambda car:(car.dnf,car.total_time if not car.dnf else float('inf')));leader=next((c.total_time for c in ordered if not c.dnf),0.0)
 for pos,car in enumerate(ordered,1):
  card=next((x for x in cards if x['driver_id']==car.driver_id),None)
  if not card: continue
  card.update(position=pos,speed=round(3600/max(1,car.last_lap_time),1),gap='LEADER' if pos==1 else f"+{max(0,car.total_time-leader):.3f}s",tyres=car.tyres.compound.value,fuel=round(car.fuel_level,1),energy=round(car.energy_battery,1),lap_time=round(car.last_lap_time,3),dnf=car.dnf,progress=getattr(car,'track_progress',0.0))
 for event in engine.events:
  if event.lap==lap: world.publish_event(event.kind,event.text,lap)
 world.update(state='RACE_LIVE',season=season,round=round_number,track=track,lap=lap,lap_total=engine.total_laps,race_lap_seconds=RACE_MINUTES*60/max(1,engine.total_laps),weather=engine.weather.state_label(),track_wetness=round(engine.weather.track_wetness,1),cars=cards,message=f'{track} — Lap {lap}/{engine.total_laps}')
 time.sleep((RACE_MINUTES*60)/max(1,engine.total_laps))
def run_season(number):
 seed=int(os.getenv('APEXGRID_SEED','1001'))+number;rng=random.Random(seed);name=season_name(number);teams,drivers=generate_grid(seed=seed)
 world.update(state='SEASON_STARTING',season=name,round=1,message=f'{name} is starting')
 for round_number,(track,laps) in enumerate(CALENDAR,1):
  world.update(state='PRACTICE',season=name,round=round_number,track=track,lap=0,lap_total=laps,message='Practice session underway');sleep_minutes(PRACTICE_MINUTES)
  weather=Weather.generate(rng,rain_chance=.2);world.update(state='QUALIFYING',season=name,round=round_number,track=track,weather=weather.state_label(),track_wetness=weather.track_wetness,message='Qualifying underway')
  quali=run_qualifying(teams,drivers,weather,rng);sleep_minutes(QUALIFYING_MINUTES);cards=cards_for(teams,drivers)
  engine=RaceEngine(teams,drivers,total_laps=laps,track_name=track,seed=rng.randint(0,10**9),grid_order=quali.grid_order,weather=weather,on_lap=lambda e,l,c,lt:publish_lap(e,l,c,lt,cards,name,round_number,track))
  world.update(state='RACE_LIVE',season=name,round=round_number,track=track,lap=0,lap_total=laps,race_lap_seconds=RACE_MINUTES*60/max(1,laps),weather=weather.state_label(),track_wetness=weather.track_wetness,cars=cards,message=f'{track} is LIVE')
  result=engine.run();report=newsroom.generate_report(track,result.classification,result.events,result.fastest_lap,result.penalties,season_name=name);db.save_race(name,round_number,track,laps,result.classification,result.fastest_lap,report=report)
  winner=result.classification[0]['driver_name'] if result.classification else 'Unknown';world.update(state='RACE_COMPLETE',season=name,round=round_number,track=track,lap=laps,lap_total=laps,cars=cards,message=f'{track} complete — winner {winner}',last_report=report);sleep_minutes(ROUND_GAP_HOURS)
 standings=db.season_standings(name);leader=standings[0]['driver_name'] if standings else None;world.update(state='SEASON_COMPLETE',season=name,round=len(CALENDAR),message=f'{name} complete',championship_leader=leader);sleep_minutes(SEASON_GAP_HOURS)
def main():
 n=STARTING_SEASON
 while True:
  try: run_season(n);n+=1
  except Exception as exc: world.update(state='ERROR',message=f'World runner recovered: {type(exc).__name__}');time.sleep(10)
if __name__=='__main__': main()
