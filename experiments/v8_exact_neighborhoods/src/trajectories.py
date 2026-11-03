import json,math,sys
from pathlib import Path
import shapely
from shapely import MultiPoint
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
dest=Path(sys.argv[1]);summary=json.loads((dest/'EVALUATION.json').read_text())
spec=json.loads((dest/'MANIFEST.json').read_text())['spec'];rows=json.loads((dest/'results.json').read_text())
lookup={(r['case'],r['seed'],r['variant']):r for r in rows}

def state(data,sol):
    n=len(data['sites']);a=[-1]*n;w=[-1]*len(data['workers']);h={};counts={};loads={}
    xy=[(s['x'],s['y']) for s in data['sites']]+[(o['x'],o['y']) for o in data['offices']]
    reward=distance=cost=0
    for r in sol:
        o=r['officeId'];counts[o]=len(r['sites']);loads[o]=sum(len(data['sites'][s]['tasks']) for s in r['sites']);cost+=data['offices'][o]['cost']
        for s in r['sites']:a[s]=o;reward+=data['sites'][s]['reward'];distance+=data['distances'][o][s]
        for v in r['workers']:w[v]=o
        h[o]=MultiPoint([xy[n+o]]+[xy[s] for s in r['sites']]).convex_hull
    penalty=data['balanceCoefficient']*(max(loads.values())-min(loads.values())) if loads else 0
    points=shapely.points(xy);owners=[-1]*len(xy)
    for o,hull in h.items():
        for q,inside in enumerate(shapely.covers(hull,points)):
            if inside:
                assert owners[q]<0,'invalid geometry';owners[q]=o
    return dict(reward=reward,distance=distance,cost=cost,penalty=penalty,objective=reward-distance-cost-penalty,
        offices=sorted(h),counts=counts,loads=loads,worker_count=sum(x>=0 for x in w),site_count=sum(x>=0 for x in a)),a,w,h,owners

def comparison(data,ba,ca):
    b,a,w,h,owners=state(data,ba);c,aa,ww,hh,own=state(data,ca);common=set(h)&set(hh)
    return dict(baseline=b,candidate=c,component_delta={k:c[k]-b[k] for k in ['reward','distance','cost','penalty','objective']},
        changed_assignments=sum(x!=y for x,y in zip(a,aa)),changed_workers=sum(x!=y for x,y in zip(w,ww)),
        office_set_difference=sorted(set(h)^set(hh)),common_hulls_changed=sum(not h[o].equals(hh[o]) for o in common),
        common_hulls_symmetric_difference_area=sum(h[o].symmetric_difference(hh[o]).area for o in common),
        input_point_footprint_owners_changed=sum(x!=y for x,y in zip(owners,own)))

chosen=[]
for base in ['v4','off']:
    details=sorted(summary['summary'][f'candidate_vs_{base}']['details'],key=lambda r:r['delta_pct'])
    for r in [details[0],details[-1]]:chosen.append((r['case'],r['seed'],base))
records=[]
for case,seed,base in chosen:
    data=json.loads((ROOT/spec['cases'][case]).read_text());br=lookup[case,seed,base];cr=lookup[case,seed,'candidate']
    def origin(row):return ROOT/row['imported_from'] if row.get('imported_from') else dest
    bpath=origin(br)/f'{case}_{seed}_{base}.solution.json';cpath=origin(cr)/f'{case}_{seed}_candidate.solution.json'
    compare=comparison(data,json.loads(bpath.read_text()),json.loads(cpath.read_text()));trace=[]
    bs={s['target_seconds']:s for s in br['snapshots'] if s.get('valid')};cs={s['target_seconds']:s for s in cr['snapshots'] if s.get('valid')}
    for t in sorted(set(bs)&set(cs)):
        b=bs[t];c=cs[t];bb=json.loads((ROOT/b['file']).read_text());cc=json.loads((ROOT/c['file']).read_text())
        trace.append(dict(target=t,baseline_objective=b['objective'],candidate_objective=c['objective'],
            baseline_offices=sorted(r['officeId'] for r in bb),candidate_offices=sorted(r['officeId'] for r in cc),
            same_assignments={s:r['officeId'] for r in bb for s in r['sites']}=={s:r['officeId'] for r in cc for s in r['sites']}))
    records.append(dict(case=case,seed=seed,baseline_variant=base,delta_pct=100*(cr['objective']-br['objective'])/abs(br['objective']),trace=trace,**compare))
(dest/'TRAJECTORIES.json').write_text(json.dumps(records,indent=2));print(json.dumps([dict(case=r['case'],seed=r['seed'],base=r['baseline_variant'],delta_pct=r['delta_pct'],components=r['component_delta']) for r in records]))
