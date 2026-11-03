"""Office-anchored witness: any footprint point needs at most two sites."""
from shapely.geometry import MultiPoint,Point

def support(I,o,sites,p):
 anchor=I.n+o;target=Point(I.xy[p]);origin=tuple(I.xy[anchor]);ids=[*sites,anchor]
 if target.equals(Point(origin)):return ()
 bycoord={tuple(I.xy[i]):i for i in ids};h=MultiPoint(I.xy[ids]).convex_hull
 assert h.covers(target)
 if h.geom_type=='Point':return ()
 if h.geom_type=='LineString':edges=[list(h.coords)]
 else:
  xy=list(h.exterior.coords);edges=[xy[i:i+2] for i in range(len(xy)-1)]
 for edge in edges:
  if MultiPoint([origin,*edge]).convex_hull.covers(target):
   w=sorted(set(bycoord[tuple(q)] for q in edge)-{anchor})
   for i in w:
    if MultiPoint([origin,tuple(I.xy[i])]).convex_hull.covers(target):return (i,)
   assert len(w)<=2
   return tuple(w)
 raise AssertionError('No anchored witness: numerical inconsistency')
