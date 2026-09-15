"""Persistent world state and WebSocket event hub for deployment."""
import asyncio,json,os,threading
from datetime import datetime,timezone
DATA_DIR=os.path.join(os.path.dirname(__file__),'..','data');STATE_PATH=os.path.join(DATA_DIR,'world_state.json');LOCK=threading.Lock();SUBS=set();DEFAULT={'title':'APEXGRID World','season':'Season 001','round':1,'track':'Meridian Circuit','state':'OFFLINE','lap':0,'lap_total':55,'weather':'Clear','track_wetness':0,'message':'Persistent AI motorsport simulation','cars':[],'events':[],'updated_at':None}
def load():
 os.makedirs(DATA_DIR,exist_ok=True)
 try:
  with open(STATE_PATH,encoding='utf-8') as f:x=json.load(f)
  d=DEFAULT.copy();d.update(x);return d
 except (OSError,ValueError):return DEFAULT.copy()
WORLD=load()
def snapshot():
 with LOCK:return json.loads(json.dumps(WORLD))
def update(**changes):
 with LOCK:
  WORLD.update(changes);WORLD['updated_at']=datetime.now(timezone.utc).isoformat();os.makedirs(DATA_DIR,exist_ok=True)
  with open(STATE_PATH,'w',encoding='utf-8') as f:json.dump(WORLD,f,indent=2)
  data=json.loads(json.dumps(WORLD))
 publish({'type':'world','data':data});return data
def subscribe():
 q=asyncio.Queue(maxsize=50);SUBS.add(q);return q
def unsubscribe(q):SUBS.discard(q)
def publish(message):
 for q in tuple(SUBS):
  try:q.put_nowait(message)
  except asyncio.QueueFull:
   try:q.get_nowait();q.put_nowait(message)
   except asyncio.QueueEmpty:pass
def publish_event(kind,text,lap=None):publish({'type':'event','data':{'kind':kind,'text':text,'lap':lap}})
