"""Track geometry owned by the APEXGRID simulation layer."""
import math
import random

BASE_TRACK = [(120,380),(105,300),(120,210),(190,130),(300,105),(420,145),(550,200),(680,175),(770,220),(790,320),(740,405),(620,435),(500,400),(400,340),(300,300),(220,350),(160,430),(120,380)]
META = {
    "Meridian Circuit": (4.82,14,2), "Solstice Street Course": (3.76,18,2),
    "Halcyon Ring": (5.21,12,2), "Obsidian Grand Prix Circuit": (4.91,16,3),
    "Voltage Speedway": (4.12,10,3), "Zenith Highlands": (5.34,15,3),
    "Ironclad Docklands": (4.65,17,3), "Kestrel Coastal Loop": (5.08,13,2),
    "Aurora Park": (4.39,19,2), "Titan Valley": (5.02,11,3),
    "Neon Harbour": (4.17,20,2), "Atlas International": (5.44,14,3),
    "Vortex Raceway": (4.73,12,3), "Silver Coast": (4.88,16,2),
    "Granite Peak": (5.57,18,3), "Sapphire City": (4.26,21,2),
    "Solaris Circuit": (5.11,13,3), "Black Forest Ring": (5.36,15,3),
    "Crown Street Circuit": (3.92,22,2), "Redline International": (5.03,12,3),
    "Northstar Circuit": (4.71,17,3), "Eclipse Bay": (5.18,14,2),
    "Thunder Plains": (4.43,11,3), "Finale Grand Prix Circuit": (5.62,20,3),
}

def geometry(track_name: str):
    rng = random.Random(track_name)
    angle, scale = rng.uniform(-0.22,0.22), rng.uniform(0.92,1.08)
    cx, cy = 450, 270
    pts=[]
    for x,y in BASE_TRACK:
        dx,dy=(x-cx)*scale,(y-cy)*scale
        rx=dx*math.cos(angle)-dy*math.sin(angle); ry=dx*math.sin(angle)+dy*math.cos(angle)
        pts.append([round(cx+rx,2),round(cy+ry,2)])
    length_km,corners,sectors=META.get(track_name,(4.8,14,3))
    return {"points":pts,"length_km":length_km,"corners":corners,"sectors":sectors}

def point_at(track_name: str, progress: float):
    pts=geometry(track_name)["points"]; target=(progress%1.0)
    lengths=[]; total=0.0
    for a,b in zip(pts,pts[1:]):
        length=math.hypot(b[0]-a[0],b[1]-a[1]); lengths.append(length); total+=length
    target*=total
    for i,length in enumerate(lengths):
        if target<=length:
            a,b=pts[i],pts[i+1]; u=target/max(length,1e-9)
            return {"x":round(a[0]+(b[0]-a[0])*u,2),"y":round(a[1]+(b[1]-a[1])*u,2),"heading":round(math.degrees(math.atan2(b[1]-a[1],b[0]-a[0])),1)}
        target-=length
    return {"x":pts[-1][0],"y":pts[-1][1],"heading":0.0}
