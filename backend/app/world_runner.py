"""APEXGRID continuous world runner with paced sessions and persistent seasons."""
import os,random,time
from . import world
from .simulation.grid_generator import generate_grid
from .simulation.engine import RaceEngine
from .simulation import db
from .simulation import newsroom
from .simulation.qualifying import run_qualifying
from .simulation.weather import Weather
from .simulation.track import geometry

CALENDAR=[('Meridian Circuit',55),('Solstice Street Course',48),('Halcyon Ring',60),('Obsidian Grand Prix Circuit',52),('Voltage Speedway',44),('Zenith Highlands',58),('Ironclad Docklands',50),('Kestrel Coastal Loop',56),('Aurora Park',53),('Titan Valley',49),('Neon Harbour',51),('Atlas International',57),('Vortex Raceway',46),('Silver Coast',54),('Granite Peak',61),('Sapphire City',47),('Solaris Circuit',58),('Black Forest Ring',52),('Crown Street Circuit',45),('Redline International',59),('Northstar Circuit',50),('Eclipse Bay',55),('Thunder Plains',48),('Finale Grand Prix Circuit',62)]
STARTING_SEASON=int(os.getenv('APEXGRID_START_SEASON','1'));RACE_MINUTES=float(os.getenv('APEXGRID_RACE_MINUTES','90'));QUALIFYING_MINUTES=float(os.getenv('APEXGRID_QUALIFYING_MINUTES','20'));PRACTICE_MINUTES=float(os.getenv('APEXGRID_PRACTICE_MINUTES','5'));ROUND_GAP_HOURS=float(os.getenv('APEXGRID_ROUND_GAP_HOURS','2'));SEASON_GAP_HOURS=float(os.getenv('APEXGRID_SEASON_GAP_HOURS','4'))
COLORS=['#ff3b30','#ffd60a','#30d158','#0a84ff','#bf5af2','#64d2ff','#ff9f0a','#ff375f','#5e5ce6','#ac8e68']
def sleep_minutes(minutes):
 end=time.monotonic()+max(0,minutes*60)
 while time.monotonic()<end: time.sleep(min(1,end-time.monotonic()))
def season_name(n): return f'Season {n:03d}'
def cards_for(teams,drivers):
 ordered=sorted(drivers.values(),key=lambda d:d.base_pace_score(),reverse=True)
 return [{'driver_id':d.driver_id,'number':d.number,'driver_name':d.name,'team':teams[d.team_id].name,'team_id':d.team_id,'position':i+1,'color':COLORS[i%len(COLORS)],'speed':0,'gap':'—','tyres':'MEDIUM','tyre_wear':0,'tyre_laps':0,'fuel':100,'energy':100,'lap_time':0,'progress':i*.01,'x':0,'y':0,'heading':0,'sector':1,'pit_stops':0,'dnf':False,'health':{'engine':100,'gearbox':100,'battery':100,'brakes':100,'suspension':100,'aero':100,'cooling':100},'driver_rating':round(d.base_pace_score(),1),'morale':d.attributes.morale} for i,d in enumerate(ordered)]
def sync_cards(engine,cards):
 for car in engine.cars.values():
  card=next((x for x in cards if x['driver_id']==car.driver_id),None)
  if card: card.update(x=car.x,y=car.y,heading=car.heading,sector=car.sector,progress=car.track_progress,speed=round(3600/max(1,car.last_lap_time),1),tyres=car.tyres.compound.value,tyre_wear=round(car.tyres.wear,1),tyre_laps=car.tyres.laps_on,fuel=round(car.fuel_level,1),energy=round(car.energy_battery,1),pit_stops=car.pit_stops,dnf=car.dnf,health={'engine':round(car.health.engine,1),'gearbox':round(car.health.gearbox,1),'battery':round(car.health.battery,1),'brakes':round(car.health.brakes,1),'suspension':round(car.health.suspension,1),'aero':round(car.health.aero,1),'cooling':round(car.health.cooling,1)})
def publish_tick(engine,lap,tick,cumulative,lap_times,cards,season,round_number,track):
 sync_cards(engine,cards)
 world.update(state='RACE_LIVE',season=season,round=round_number,track=track,lap=lap,lap_total=engine.total_laps,weather=engine.weather.state_label(),track_temp=round(engine.weather.track_temp,1),air_temp=round(engine.weather.air_temp,1),humidity=round(engine.weather.humidity,1),wind_speed=round(engine.weather.wind_speed,1),track_wetness=round(engine.weather.track_wetness,1),race_control=engine.race_control.flag,cars=cards,message=f'{track} — Lap {lap}/{engine.total_laps}')
def publish_lap(engine,lap,cumulative,lap_times,cards,season,round_number,track):
 ordered=sorted(engine.cars.values(),key=lambda car:(car.dnf,car.total_time if not car.dnf else float('inf')));leader=next((c.total_time for c in ordered if not c.dnf),0.0)
 for pos,car in enumerate(ordered,1):
  card=next((x for x in cards if x['driver_id']==car.driver_id),None)
  if card: card.update(position=pos,gap='LEADER' if pos==1 else f'+{max(0,car.total_time-leader):.3f}s',lap_time=round(car.last_lap_time,3))
 for event in engine.events:
  if event.lap==lap: world.publish_event(event.kind,event.text,lap)
 sync_cards(engine,cards)
 world.update(state='RACE_LIVE',season=season,round=round_number,track=track,lap=lap,lap_total=engine.total_laps,weather=engine.weather.state_label(),track_temp=round(engine.weather.track_temp,1),air_temp=round(engine.weather.air_temp,1),humidity=round(engine.weather.humidity,1),wind_speed=round(engine.weather.wind_speed,1),track_wetness=round(engine.weather.track_wetness,1),race_control=engine.race_control.flag,cars=cards,message=f'{track} — Lap {lap}/{engine.total_laps}')
def run_season(number):
 seed=int(os.getenv('APEXGRID_SEED','1001'))+number;rng=random.Random(seed);name=season_name(number);teams,drivers=generate_grid(seed=seed)
 world.update(state='SEASON_STARTING',season=name,round=1,calendar=[{'round':i+1,'track':t,'laps':l} for i,(t,l) in enumerate(CALENDAR)],drivers=[{'driver_id':d.driver_id,'number':d.number,'name':d.name,'team':teams[d.team_id].name,'team_id':d.team_id} for d in drivers.values()],teams=[{'team_id':t.team_id,'name':t.name,'pit_crew_skill':t.pit_crew_skill} for t in teams.values()],message=f'{name} is starting')
 for round_number,(track,laps) in enumerate(CALENDAR,1):
  world.update(state='PRACTICE',season=name,round=round_number,track=track,lap=0,lap_total=laps,track_geometry=geometry(track),message='Practice session underway');sleep_minutes(PRACTICE_MINUTES)
  weather=Weather.generate(rng,rain_chance=.2);world.update(state='QUALIFYING',season=name,round=round_number,track=track,track_geometry=geometry(track),weather=weather.state_label(),track_temp=round(weather.track_temp,1),air_temp=round(weather.air_temp,1),humidity=round(weather.humidity,1),wind_speed=round(weather.wind_speed,1),track_wetness=round(weather.track_wetness,1),message='Qualifying underway')
  quali=run_qualifying(teams,drivers,weather,rng);sleep_minutes(QUALIFYING_MINUTES);cards=cards_for(teams,drivers)
  engine=RaceEngine(teams,drivers,total_laps=laps,track_name=track,seed=rng.randint(0,10**9),grid_order=quali.grid_order,weather=weather,on_lap=lambda e,l,c,lt:publish_lap(e,l,c,lt,cards,name,round_number,track),on_tick=lambda e,l,t,c,lt:publish_tick(e,l,t,c,lt,cards,name,round_number,track),wall_clock_lap_seconds=RACE_MINUTES*60/max(1,laps),ticks_per_lap=12)
  world.update(state='RACE_LIVE',season=name,round=round_number,track=track,track_geometry=geometry(track),lap=0,lap_total=laps,race_lap_seconds=RACE_MINUTES*60/max(1,laps),weather=weather.state_label(),track_temp=round(weather.track_temp,1),air_temp=round(weather.air_temp,1),humidity=round(weather.humidity,1),wind_speed=round(weather.wind_speed,1),track_wetness=round(weather.track_wetness,1),race_control=engine.race_control.flag,cars=cards,message=f'{track} is LIVE')
  result=engine.run();report=newsroom.generate_report(track,result.classification,result.events,result.fastest_lap,result.penalties,season_name=name);db.save_race(name,round_number,track,laps,result.classification,result.fastest_lap,report=report)
  winner=result.classification[0]['driver_name'] if result.classification else 'Unknown';standings_now=db.season_standings(name);world.update(state='RACE_COMPLETE',season=name,round=round_number,track=track,lap=laps,lap_total=laps,cars=cards,message=f'{track} complete — winner {winner}',last_report=report,standings=standings_now);sleep_minutes(ROUND_GAP_HOURS)
 standings=db.season_standings(name);leader=standings[0]['driver_name'] if standings else None;world.update(state='SEASON_COMPLETE',season=name,round=len(CALENDAR),message=f'{name} complete',championship_leader=leader,standings=standings);sleep_minutes(SEASON_GAP_HOURS)
def main():
 n=STARTING_SEASON
 while True:
  try: run_season(n);n+=1
  except Exception as exc: world.update(state='ERROR',message=f'World runner recovered: {type(exc).__name__}: {exc}');time.sleep(10)
if __name__=='__main__': main()
