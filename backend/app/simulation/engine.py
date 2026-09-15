"""RaceEngine — APEXGRID simulation kernel."""
import random,time
from dataclasses import dataclass,field
from typing import Dict,List,Optional
from .driver import Driver
from .team import Team
from .car import CarState
from .tyres import TyreSet,Compound
from .weather import Weather
from .race_control import RaceControlState
from .incidents import check_incident
from .pit_stop import execute_pit_stop
from .stewards import Stewards
from . import strategy_ai,driver_ai,radio
from .track import point_at
POINTS_TABLE=[25,18,15,12,10,8,6,4,2,1]
@dataclass
class LapEvent: lap:int; kind:str; text:str
@dataclass
class RaceResult:
 classification:List[dict]; fastest_lap:Optional[dict]; events:List[LapEvent]; points_awarded:Dict[str,int]; penalties:List=field(default_factory=list)
class RaceEngine:
 def __init__(self,teams:Dict[str,Team],drivers:Dict[str,Driver],total_laps:int=55,track_name:str='Meridian Circuit',seed:int=None,base_lap_time:float=92.0,grid_order:Optional[List[str]]=None,weather:Optional[Weather]=None,on_lap=None,on_tick=None,wall_clock_lap_seconds:float=0.0,ticks_per_lap:int=12):
  self.teams=teams;self.drivers=drivers;self.total_laps=total_laps;self.track_name=track_name;self.base_lap_time=base_lap_time;self.rng=random.Random(seed);self.weather=weather or Weather.generate(self.rng,rain_chance=.2);self.race_control=RaceControlState();self.stewards=Stewards();self.events=[];self.fastest_lap=None;self.on_lap=on_lap;self.on_tick=on_tick;self.wall_clock_lap_seconds=wall_clock_lap_seconds;self.ticks_per_lap=max(1,ticks_per_lap);self.cars={};fuel_per_lap=92.0/total_laps
  for did,d in drivers.items(): self.cars[did]=CarState(driver_id=did,team_id=d.team_id,tyres=TyreSet(compound=Compound.MEDIUM),fuel_consumption_per_lap=fuel_per_lap)
  if grid_order is not None:self._apply_grid_order(grid_order)
  else:self._set_grid_order()
 def _apply_grid_order(self,order):
  for p,did in enumerate(order,1):self.cars[did].position=p
 def _set_grid_order(self):
  scores=[]
  for did,d in self.drivers.items():scores.append((d.base_pace_score()*.5+self.teams[d.team_id].car.performance_score()*.5+self.rng.uniform(-3,3),did))
  for p,(_,did) in enumerate(sorted(scores,reverse=True),1):self.cars[did].position=p
 def _log(self,lap,kind,text):self.events.append(LapEvent(lap,kind,text))
 def _lap_time_for(self,d,t,c):
  pace=d.base_pace_score();car_score=t.car.performance_score();skill=self.base_lap_time-(pace-65)*.045;car_time=-(car_score-65)*.05;tyre=c.tyres.grip_penalty_seconds()+c.tyres.cold_penalty_seconds()+c.tyres.compound_advantage_seconds();fuel=c.fuel_weight_penalty_seconds();wet=0;w=self.weather.track_wetness
  if w>5:
   wet+=(0 if c.tyres.compound in (Compound.INTERMEDIATE,Compound.WET) else w/100*6)+(100-d.attributes.wet_performance)/100*(w/100)*2
  noise=self.rng.gauss(0,.25+(100-d.attributes.consistency)/300);return max(60,(skill+car_time+tyre+fuel+wet+noise)*self.race_control.pace_multiplier())
 def _update_spatial(self,lap,tick,lap_times,active):
  elapsed=(tick+1)/self.ticks_per_lap
  for did in active:
   car=self.cars[did]
   if car.dnf:continue
   fraction=min(.999,elapsed*max(.1,self.base_lap_time/max(lap_times.get(did,self.base_lap_time),1)))
   car.track_progress=((lap-1)+fraction)/self.total_laps
   pos=point_at(self.track_name,car.track_progress);car.x=pos['x'];car.y=pos['y'];car.heading=pos['heading'];car.sector=min(3,max(1,int(car.track_progress%1*3)+1))
 def run(self):
  order=sorted(self.cars.values(),key=lambda c:c.position);cumulative={c.driver_id:0.0 for c in order}
  for lap in range(1,self.total_laps+1):
   self.weather.step(self.rng);self.race_control.step();active=[did for did,c in self.cars.items() if not c.dnf];ranking=sorted(active,key=lambda d:cumulative[d]);gaps={}
   for i,did in enumerate(ranking):gaps[did]=((cumulative[did]-cumulative[ranking[i-1]]) if i else None,(cumulative[ranking[i+1]]-cumulative[did]) if i<len(ranking)-1 else None)
   lap_times={};decisions={}
   for did in active:
    d=self.drivers[did];t=self.teams[d.team_id];c=self.cars[did];ga,gb=gaps[did];decision=driver_ai.decide(d,c,ga,gb,self.total_laps-lap,self.rng);decisions[did]=decision;strat=strategy_ai.decide(c,self.weather,lap,self.total_laps,self.rng,team_aggression=.5);lt=self._lap_time_for(d,t,c)
    if decision.mode=='PUSH':lt-=.15
    elif decision.mode=='SAVE':lt+=.2
    lt+=c.energy_step(decision.deploy_energy)
    if strat.action=='BOX':
     pit=execute_pit_stop(t.pit_crew_skill,self.rng);lt+=pit.total_pit_lane_seconds;c.change_tyres(strat.target_compound);self._log(lap,'PIT',f'{d.name} pits: {pit.description} -> {strat.target_compound.value}');self._log(lap,'RADIO','; '.join(f'{s}: {x}' for s,x in radio.pit_call(d.name)));pen=self.stewards.check_unsafe_release(d,pit,self.rng)
     if pen:lt+=pen.seconds;self._log(lap,'PENALTY',pen.description)
    else:c.tyres.step_lap(d.attributes.aggression,d.attributes.tyre_management,self.weather.track_temp)
    pen=self.stewards.check_track_limits(d,self.rng)
    if pen:lt+=pen.seconds;self._log(lap,'STEWARDS',pen.description)
    c.burn_fuel();c.degrade(t.car.reliability,self.rng,aggression_factor=1+max(0,d.attributes.aggression-60)/100);c.laps_completed=lap;incident=check_incident(d,c,self.weather,self.rng,under_pressure=(gb is not None and gb<1))
    if incident:
     lt+=incident.time_penalty_seconds;self._log(lap,incident.kind,incident.description)
     if incident.dnf:c.dnf=True;c.dnf_reason=incident.kind
     if incident.triggers_safety_car:self.race_control.trigger_safety_car();self._log(lap,'SAFETY_CAR','; '.join(x for _,x in radio.safety_car_call()))
    lap_times[did]=lt
   for did in active:cumulative[did]+=lap_times[did]
   ranking_after=sorted(active,key=lambda d:cumulative[d])
   for i in range(1,len(ranking_after)):
    a,b=ranking_after[i-1],ranking_after[i];gap=cumulative[b]-cumulative[a];ad=decisions.get(b)
    if 0<gap<1 and ad and ad.attack_gap:
     if self.rng.random()<driver_ai.overtake_probability(self.drivers[b],self.cars[b],self.drivers[a],self.cars[a],lap_times[a]-lap_times[b],self.rng):cumulative[b]=cumulative[a]-.1;self._log(lap,'OVERTAKE',f'{self.drivers[b].name} passes {self.drivers[a].name}!')
   for did in active:
    if self.fastest_lap is None or lap_times[did]<self.fastest_lap['time']:self.fastest_lap={'driver_id':did,'driver_name':self.drivers[did].name,'lap':lap,'time':round(lap_times[did],3)}
    self.cars[did].last_lap_time=lap_times[did];self.cars[did].total_time=cumulative[did]
   for tick in range(self.ticks_per_lap):
    self._update_spatial(lap,tick,lap_times,active)
    if self.on_tick:self.on_tick(self,lap,tick,cumulative,lap_times)
    if self.wall_clock_lap_seconds>0:time.sleep(self.wall_clock_lap_seconds/self.ticks_per_lap)
   if self.on_lap:self.on_lap(self,lap,cumulative,lap_times)
  return self._finalize(cumulative)
 def _finalize(self,cumulative):
  finishers=sorted([d for d,c in self.cars.items() if not c.dnf],key=lambda d:cumulative[d]);dnfs=sorted([d for d,c in self.cars.items() if c.dnf],key=lambda d:-self.cars[d].laps_completed);final=finishers+dnfs;classification=[];points_awarded={}
  for pos,did in enumerate(final,1):
   d=self.drivers[did];c=self.cars[did];points=POINTS_TABLE[pos-1] if pos<=len(POINTS_TABLE) and not c.dnf else 0;points_awarded[did]=points;d.career['races']+=1;d.career['points']+=points
   if pos==1 and not c.dnf:d.career['wins']+=1
   if pos<=3 and not c.dnf:d.career['podiums']+=1
   if c.dnf:d.career['dnfs']+=1
   self.teams[d.team_id].constructors_points+=points
   classification.append({'position':pos,'driver_id':did,'driver_name':d.name,'team':self.teams[d.team_id].name,'total_time':None if c.dnf else round(cumulative[did],3),'status':c.dnf_reason if c.dnf else 'FINISHED','pit_stops':c.pit_stops,'points':points})
  return RaceResult(classification,self.fastest_lap,self.events,points_awarded,self.stewards.log)
