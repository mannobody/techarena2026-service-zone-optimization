"""Explain largest frozen holdout deltas without attributing them to one move."""
import json,re,sys
from pathlib import Path
import shapely
from shapely import MultiPoint
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
series=sys.argv[1]if len(sys.argv)>1 else 'independent280';variant=sys.argv[2]if len(sys.argv)>2 else 'candidate'
output='PAIR_ANALYSIS'if series=='independent280'else 'PAIR_ANALYSIS_'+series.upper()+'_'+variant.upper()
d=R/'logs'/series;sm=json.loads((d/'SUMMARY.json').read_text())['variants'][variant];man=json.loads((d/'MANIFEST.json').read_text())
rows=json.loads((d/'results.json').read_text());by={(r['case'],r['seed'],r['variant']):r for r in rows}
rank=sorted((p for p in sm['pairs']if p['percent']is not None),key=lambda p:p['percent']);picked=[]
for p in rank[:3]+rank[-3:]:
    if (p['case'],p['seed'])not in picked:picked.append((p['case'],p['seed']))
reports=[]
for case,seed in picked:
    data=json.loads((ROOT/man['spec']['cases'][case]).read_text());sol={};desc={};raw={};coverage={};logs={}
    points=shapely.points([(x['x'],x['y'])for x in data['sites']+data['offices']])
    for v in ['v4','candidate']:
        label='v4'if v=='v4'else variant
        prefix=d/f'{case}_{seed}_{label}';sol[v]=json.loads(prefix.with_suffix('.solution.json').read_text());desc[v]=json.loads(prefix.with_suffix('.analysis.json').read_text());raw[v]=by[case,seed,label];logs[v]=prefix.with_suffix('.stderr').read_text()
        coverage[v]={}
        for o in sol[v]:
            k=o['officeId'];xy=[(data['sites'][x]['x'],data['sites'][x]['y'])for x in o['sites']]+[(data['offices'][k]['x'],data['offices'][k]['y'])]
            h=MultiPoint(xy).convex_hull;mask=shapely.covers(h,points);coverage[v][k]=[j for j,b in enumerate(mask)if b]
    owners=lambda v:{x:o['officeId']for o in sol[v]for x in o['sites']}
    workers=lambda v:{w:o['officeId']for o in sol[v]for w in o['workers']}
    a,b=owners('v4'),owners('candidate');wa,wb=workers('v4'),workers('candidate');oa=set(coverage['v4']);ob=set(coverage['candidate'])
    comp={k:desc['candidate'][k]-desc['v4'][k]for k in ['reward','distance','cost','penalty','objective']}
    p=next(p for p in sm['pairs']if p['case']==case and p['seed']==seed)
    assert abs(comp['objective']-p['delta'])<1e-5*max(1,abs(p['delta']))
    trajectory={v:dict(snapshots=raw[v]['snapshots'],final_wall=raw[v]['wall'],final_value=raw[v]['official'],early_terminal=raw[v]['wall']<252)for v in ['v4','candidate']}
    native=re.findall(r'ZMSIGNED .*before=([-0-9.]+) after=([-0-9.]+)',logs['candidate'])
    reports.append(dict(case=case,seed=seed,percent=p['percent'],delta_components=comp,base_objective=p['base'],candidate_objective=p['candidate'],changed_site_assignments=sum(a.get(x,-1)!=b.get(x,-1)for x in range(len(data['sites']))),changed_worker_assignments=sum(wa.get(w,-1)!=wb.get(w,-1)for w in range(len(data['workers']))),opened=sorted(ob-oa),closed=sorted(oa-ob),changed_coverage={o:len(set(coverage['candidate'][o])^set(coverage['v4'][o]))for o in sorted(oa&ob)},coverage=coverage,solutions=sol,trajectory=trajectory,signed_local_gain=sum(float(b)-float(a)for a,b in native),scope='Whole-run delta. Different pre-tail trajectories can occur with wall-limited parallel search; within-run signed gain is separately logged.'))
(R/(output+'.json')).write_text(json.dumps(reports,indent=2))
lines=[f'## Крупнейшие различия: {series}/{variant}','',
'Δobjective = Δreward − Δdistance − Δcost − Δpenalty. Это сравнение полных траекторий; '
'локальный signed gain из stderr не объявляется причиной всего эффекта. Подробные assignments, workers, '
f'point footprints и промежуточные ответы:{output}.json.','',
'|Вход/seed|Δ,%|Δreward|Δdistance|Δcost|Δpenalty|Изменено sites/workers|Открыты/закрыты|',
'|---|---:|---:|---:|---:|---:|---|---|']
for r in reports:
    c=r['delta_components'];lines.append(f"|{r['case']}/{r['seed']}|{r['percent']:+.4f}|{c['reward']:+.6g}|{c['distance']:+.6g}|{c['cost']:+.6g}|{c['penalty']:+.6g}|{r['changed_site_assignments']}/{r['changed_worker_assignments']}|{r['opened']}/{r['closed']}|")
(R/(output+'_RU.md')).write_text('\n'.join(lines)+'\n');print(json.dumps([dict(case=r['case'],seed=r['seed'],percent=r['percent'],signed_local_gain=r['signed_local_gain'])for r in reports]))
