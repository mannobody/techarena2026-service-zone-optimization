"""Audited paired statistics and solution-level diagnosis; no run is discarded."""
import hashlib,itertools,json,math,random,statistics,sys
from functools import lru_cache
from pathlib import Path
from shapely.geometry import MultiPoint
ROOT=Path(__file__).resolve().parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def describe(values):
    return dict(n=len(values),mean=statistics.mean(values),median=statistics.median(values),min=min(values),max=max(values),sample_sd=statistics.stdev(values) if len(values)>1 else 0) if values else {'n':0}
@lru_cache(maxsize=192)
def solution_metrics(inp,sol):
    data=json.loads(inp.read_text()); zones=json.loads(sol.read_text())
    asg=[-1]*len(data['sites']);workers=[-1]*len(data['workers']);hulls={};counts={};loads={};reward=distance=cost=0.
    for z in zones:
        o=z['officeId'];off=data['offices'][o];counts[o]=len(z['sites']);loads[o]=sum(len(data['sites'][x]['tasks']) for x in z['sites']);cost+=off['cost']
        pts=[(off['x'],off['y'])]
        for x in z['sites']:
            asg[x]=o;s=data['sites'][x];reward+=s['reward'];distance+=data['distances'][o][x];pts.append((s['x'],s['y']))
        for w in z['workers']:workers[w]=o
        hulls[o]=MultiPoint(pts).convex_hull
    penalty=data['balanceCoefficient']*(max(loads.values())-min(loads.values())) if loads else 0.
    return {'objective':reward-distance-cost-penalty,'reward':reward,'distance':distance,'office_cost':cost,'penalty':penalty,'offices':sorted(counts),'counts':counts,'loads':loads,'assignment':asg,'workers':workers,'hulls':hulls}
def compare(inp,left,right):
    a,b=solution_metrics(inp,left),solution_metrics(inp,right)
    changed=[x for x,(u,v) in enumerate(zip(a['assignment'],b['assignment'])) if u!=v]
    same=set(a['hulls'])&set(b['hulls'])
    return {'base':{k:a[k] for k in ['objective','reward','distance','office_cost','penalty','offices','counts','loads']},
            'candidate':{k:b[k] for k in ['objective','reward','distance','office_cost','penalty','offices','counts','loads']},
            'delta':{k:b[k]-a[k] for k in ['objective','reward','distance','office_cost','penalty']},
            'assignment_changes':len(changed),'additions':sum(a['assignment'][x]<0 for x in changed),'removals':sum(b['assignment'][x]<0 for x in changed),
            'reassignments':sum(a['assignment'][x]>=0 and b['assignment'][x]>=0 for x in changed),
            'office_set_changed':a['offices']!=b['offices'],'worker_changes':sum(x!=y for x,y in zip(a['workers'],b['workers'])),
            'hulls_changed_common_offices':sum(not a['hulls'][o].equals(b['hulls'][o]) for o in same),
            'hull_symmetric_difference_area':sum(a['hulls'][o].symmetric_difference(b['hulls'][o]).area for o in same),
            'base_sha256':sha(left),'candidate_sha256':sha(right),'input_sha256':sha(inp)}
def analyze(directory):
    d=Path(directory).resolve();m=json.loads((d/'MANIFEST.json').read_text());s=m['spec'];rows=json.loads((d/'results.json').read_text())
    expected=set(itertools.product(s['cases'],s['seeds'],s['variants']));keys=[(r['case'],r['seed'],r['variant']) for r in rows]
    assert len(keys)==len(set(keys)),'duplicate rows'
    assert set(keys)==expected,('missing',expected-set(keys))
    comp=json.loads((d/'COMPLETE.json').read_text());assert comp['completed']==len(rows)==comp['expected']
    lookup={k:r for k,r in zip(keys,rows)};summary={'runs':len(rows),'success':sum(r['success'] for r in rows),'failures':[r for r in rows if not r['success']],
        'max_wall':max(r['wall'] for r in rows),'comparisons':{},'hash_audit':{}}
    for k,h in m['binaries'].items():summary['hash_audit'][f'binary:{k}']=sha(ROOT/s['variants'][k]['binary'])==h
    for k,h in m.get('sources',{}).items():summary['hash_audit'][f'source:{k}']=sha(ROOT/s['variants'][k]['source'])==h
    for k,h in m['inputs'].items():summary['hash_audit'][f'input:{k}']=sha(ROOT/s['cases'][k])==h
    for ref in ['v4','off']:
        if ref not in s['variants']:continue
        for variant in s['variants']:
            if variant==ref:continue
            pairs=[]
            for case,seed in itertools.product(s['cases'],s['seeds']):
                a,b=lookup[case,seed,ref],lookup[case,seed,variant];assert a['affinity']==b['affinity']
                x={'case':case,'seed':seed,'success':a['success'] and b['success'],'baseline':a['objective'],'candidate':b['objective']}
                if a['valid'] and b['valid']:
                    delta=b['objective']-a['objective'];eps=1e-9*max(1,abs(a['objective']))
                    x.update(delta=delta,pct=100*delta/abs(a['objective']) if abs(a['objective'])>1e-9 else None,result='win' if delta>eps else 'loss' if delta<-eps else 'tie')
                    x['configuration']=compare(ROOT/s['cases'][case],d/f'{case}_{seed}_{ref}.solution.json',d/f'{case}_{seed}_{variant}.solution.json')
                pairs.append(x)
            vals=[p['pct'] for p in pairs if p.get('pct') is not None]
            report={'pairs':pairs,'distribution_valid_outputs_including_failed_processes':describe(vals),
                'wtl':{k:sum(p.get('result')==k for p in pairs) for k in ['win','tie','loss']},'failed_pairs':sum(not p['success'] for p in pairs),
                'by_case':{c:describe([p['pct'] for p in pairs if p['case']==c and p.get('pct') is not None]) for c in s['cases']}}
            means=[v['mean'] for v in report['by_case'].values() if v['n']]
            rng=random.Random(351);boot=sorted(statistics.mean(rng.choices(means,k=len(means))) for _ in range(10000)) if means else []
            report['instance_bootstrap95_mean']=[boot[249],boot[9749]] if boot else None
            summary['comparisons'][variant+'_vs_'+ref]=report
    return summary
if __name__=='__main__':
    result=analyze(sys.argv[1]);Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps({k:{j:v for j,v in x.items() if j not in ['pairs']} for k,x in result['comparisons'].items()},indent=2))
