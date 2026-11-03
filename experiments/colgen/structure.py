"""Finite witnesses for limitations of halfplane footprints and skill pricing."""
from itertools import combinations
import json
import math
from pathlib import Path

import numpy as np


def halfplanes():
    # Input point 0 is the office. Two profitable sites alternate with three
    # unprofitable/penalized input points on a strictly convex hexagon.
    P=np.array([(math.cos(i*math.pi/3),math.sin(i*math.pi/3)) for i in range(6)])
    reward=np.array([0.,0.,1.,0.,1.,0.]); rho=np.array([0.,10.,0.,10.,0.,10.])
    critical=sorted({round((math.atan2(*(P[j]-P[i])[::-1])+math.pi/2+flip)%(2*math.pi),12)
                     for i,j in combinations(range(6),2) for flip in (0.,math.pi)})
    angles=[(critical[i]+((critical[(i+1)%len(critical)]+(2*math.pi if i+1==len(critical) else 0.))-critical[i])/2)%(2*math.pi)
            for i in range(len(critical))]
    patterns=set()
    for theta in angles:
        proj=P@np.array([math.cos(theta),math.sin(theta)])
        for q in sorted(set(float(x) for x in proj)):
            mask=tuple(i for i in range(6) if proj[i]<=q+1e-12)
            if 0 in mask:
                patterns.add(mask)
    valid=[(float(reward[list(p)].sum()-rho[list(p)].sum()),p) for p in patterns if reward[list(p)].sum()>0]
    best=max(valid)
    assert len(patterns)==16
    # Convex hull {office 0, sites 2,4} covers no other hexagon vertex.
    full=2.
    assert full>best[0]
    return dict(unrestricted_pricing=full,halfplane_footprint_pricing=best[0],
                halfplane_footprint=best[1],halfplane_patterns_with_office=len(patterns),
                unrestricted_footprint=[0,2,4])


def min_union(graph,k):
    # Edges are sites, endpoints are required skills, maxSize=choose(k,2).
    # All coordinates coincide, so geometry contributes only a constant.
    r=k*(k-1)//2; B=len({v for e in graph for v in e})+1
    best=max((B*len(E)-len({v for e in E for v in e}),E)
             for q in range(1,min(r,len(graph))+1) for E in combinations(graph,q))
    return dict(k=k,capacity=r,B=B,value=best[0],clique_threshold=B*r-k,
                chosen_edges=best[1])


if __name__=='__main__':
    yes=min_union([(0,1),(0,2),(1,2),(2,3)],3)
    no=min_union([(0,1),(1,2),(2,3),(3,0)],3)
    assert yes['value']>=yes['clique_threshold'] and no['value']<no['clique_threshold']
    d=dict(halfplane=halfplanes(),skill_union_clique=yes,skill_union_no_clique=no)
    p=Path(__file__).parent/'logs/structure.json'; p.write_text(json.dumps(d,indent=2))
    print(json.dumps(d))
