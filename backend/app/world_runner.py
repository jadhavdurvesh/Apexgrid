"""APEXGRID continuous world runner."""
import os, random, time
from . import world
from .simulation.grid_generator import generate_grid
from .simulation.engine import RaceEngine
from .simulation import db
from .simulation.qualifying import run_qualifying
from .simulation import newsroom

CALENDAR=[
('Meridian Circuit',55),('Solstice Street Course',48),('Halcyon Ring',60),('Obsidian Grand Prix Circuit',52),
('Voltage Speedway',44),('Zenith Highlands',58),('Ironclad Docklands',50),('Kestrel Coastal Loop',56),
('Aurora Park',53),('Titan Valley',49),('Neon Harbour',51),('Atlas International',57),
('Vortex Raceway',46),('Silver Coast',54),('Granite Peak',61),('Sapphire City',47),
('Solaris Circuit',58),('Black Forest Ring',52),('Crown Street GP',45),('Redline International',59),
('Northstar Circuit',50),('Eclipse Bay',55),('Thunder Plains',48),('Finale Grand Prix Circuit',62)
]
SEASON_NAME=os.getenv('APEXGRID_SEASON','Season 001')
RACE_MINUTES=float(os.getenv('APEXGRID_RACE_MINUTES','90'))
QUALIFYING_MINUTES=float(os.getenv('APEXGRID_QUALIFYING_MINUTES','20'))
PRACTICE_MINUTES=float(os.getenv('APEXGRID_PRACTICE_MINUTES','5'))
ROUND_GAP_HOURS=float(os.getenv('APEXGRID_ROUND_GAP_HOURS','10'))
SEASON_GAP_HOURS=float(os.getenv('APEXGRID_SEASON_GAP_HOURS','12'))
COLORS=['#ff3b30','#ffd60a','#30d158','#0a84ff','#bf5af2','#64d2ff','#ff9f0a','#ff375f','#5e5ce6','#ac8e68']

def sleep_minutes(minutes):
    end=time.monotonic()+max(0.0,minutes*60.0)
    while time.monotonic()<end: time.sleep(min(1.0,end-time.monotonic()))

def cards_for(teams,drivers):
    ordered=sorted(drivers.values(),key=lambda d:d.base_pace_score(),reverse=True)
    return [{'driver_id':d.driver_id,'driver_name':d.name,'team':teams[d.team_id].name,'position':i+1,
             'color':COLORS[i%len(COLORS)],'speed':0,'gap':'—','tyres':'MEDIUM','fuel':100,'energy':100}
            for i,d in enumerate(ordered)]

def project_positions(cards,classification,lap,laps,rng):
    ordered=sorted(classification,key=lambda x:(999 if x['status']!='FINISHED' else x['position']))
    for i,row in enumerate(ordered):
        c=next((x for x in cards if x['driver_id']==row['driver_id']),None)
        if not c: continue
        p=max(0.0,min(1.0,lap/max(1,laps)));c['position']=i+1;c['speed']=round(285+rng.uniform(-12,12),1)
        c['fuel']=round(max(0,100-p*100),1);c['energy']=round(55+rng.uniform(0,45),1)
        c['tyres']=['SOFT','MEDIUM','HARD'][int(p*3)%3];c['gap']='LEADER' if i==0 else '+%.3fs'%(0.62*i+rng.uniform(0,0.8))

def run_season():
    seed=int(os.getenv('APEXGRID_SEED','1001'));rng=random.Random(seed);teams,drivers=generate_grid(seed=seed)
    world.update(state='SEASON_STARTING',season=SEASON_NAME,round=1,message='New championship starting')
    for number,(track,laps) in enumerate(CALENDAR,1):
        world.update(state='PRACTICE',round=number,track=track,lap=0,lap_total=laps,message='Practice session underway');sleep_minutes(PRACTICE_MINUTES)
        from .simulation.weather import Weather
        weather=Weather.generate(rng,rain_chance=0.2)
        world.update(state='QUALIFYING',weather=weather.state_label(),track_wetness=weather.track_wetness,message='Qualifying underway')
        quali=run_qualifying(teams,drivers,weather,rng);sleep_minutes(QUALIFYING_MINUTES)
        engine=RaceEngine(teams,drivers,total_laps=laps,track_name=track,seed=rng.randint(0,10**9),grid_order=quali.grid_order,weather=weather)
        result=engine.run()
        report=newsroom.generate_report(track,result.classification,result.events,result.fastest_lap,result.penalties,season_name=SEASON_NAME)
        db.save_race(SEASON_NAME,number,track,laps,result.classification,result.fastest_lap,report=report)
        cards=cards_for(teams,drivers);events={}
        for e in result.events: events.setdefault(e.lap,[]).append(e)
        world.update(state='RACE_LIVE',track=track,lap=0,lap_total=laps,weather=weather.state_label(),track_wetness=weather.track_wetness,cars=cards,message=track+' is LIVE')
        lap_seconds=RACE_MINUTES*60.0/max(1,laps)
        for lap in range(1,laps+1):
            project_positions(cards,result.classification,lap,laps,rng)
            weather.step(rng)
            for e in events.get(lap,[])[:6]: world.publish_event(e.kind,e.text,lap)
            world.update(state='RACE_LIVE',lap=lap,lap_total=laps,weather=weather.state_label(),track_wetness=weather.track_wetness,cars=cards,message='%s — Lap %d/%d'%(track,lap,laps))
            sleep_minutes(lap_seconds/60.0)
        winner=result.classification[0]['driver_name'] if result.classification else 'Unknown'
        world.update(state='RACE_COMPLETE',lap=laps,lap_total=laps,cars=cards,message=track+' complete — winner '+winner)
        sleep_minutes(ROUND_GAP_HOURS)
    standings=db.season_standings(SEASON_NAME);leader=standings[0]['driver_name'] if standings else None
    world.update(state='SEASON_COMPLETE',message=SEASON_NAME+' complete',championship_leader=leader);sleep_minutes(SEASON_GAP_HOURS)

def main():
    while True:
        try: run_season()
        except Exception as exc: world.update(state='ERROR',message='World runner recovered: '+type(exc).__name__);time.sleep(10)
if __name__=='__main__': main()
