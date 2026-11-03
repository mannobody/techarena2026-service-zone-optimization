"""Descriptive paired metrics; never promote a checkpoint after process failure."""
import json,statistics,sys
from pathlib import Path

def summary(path):
    path=Path(path);rows=json.loads((path/'results.json').read_text())
    base={(r['case'],r['seed']):r for r in rows if r['variant']=='v4'}
    output={'series':str(path),'completed_marker':(path/'COMPLETE.json').exists(),
        'runs':len(rows),'successful':sum(r['success'] for r in rows),'variants':{}}
    for variant in sorted({r['variant'] for r in rows}-{'v4'}):
        pairs=[];values=[];wins=ties=losses=0
        for row in rows:
            if row['variant']!=variant:continue
            key=row['case'],row['seed'];b=base.get(key)
            if not b or not row['success'] or not b['success']:continue
            delta=row['objective']-b['objective'];eps=1e-9*max(1,abs(b['objective']))
            status='win' if delta>eps else 'loss' if delta<-eps else 'tie'
            wins+=status=='win';losses+=status=='loss';ties+=status=='tie'
            pct=100*delta/abs(b['objective']) if abs(b['objective'])>1e-9 else None
            if pct is not None:values.append(pct)
            pairs.append({'case':row['case'],'seed':row['seed'],'base':b['objective'],
                          'candidate':row['objective'],'delta':delta,'pct':pct,'status':status,
                          'same_affinity':row['affinity']==b['affinity']})
        cases={}
        for case in sorted({p['case'] for p in pairs}):
            ps=[p for p in pairs if p['case']==case]
            bm=statistics.median(p['base'] for p in ps);cm=statistics.median(p['candidate'] for p in ps)
            pcs=[p['pct'] for p in ps if p['pct'] is not None]
            cases[case]={'pairs':len(ps),'baseline_median':bm,'candidate_median':cm,
                'median_objective_ratio_pct':100*(cm-bm)/abs(bm) if abs(bm)>1e-9 else None,
                'paired_mean_pct':statistics.mean(pcs) if pcs else None,
                'paired_min_pct':min(pcs) if pcs else None,'paired_max_pct':max(pcs) if pcs else None}
        output['variants'][variant]={'pairs':len(pairs),'nonzero_reference_pairs':len(values),
            'mean_pct':statistics.mean(values) if values else None,
            'median_pct':statistics.median(values) if values else None,
            'min_pct':min(values) if values else None,'max_pct':max(values) if values else None,
            'stdev_pct':statistics.stdev(values) if len(values)>1 else None,
            'wins':wins,'ties':ties,'losses':losses,'same_affinity':all(p['same_affinity'] for p in pairs),
            'cases':cases,'paired':pairs}
    output['max_wall']=max((r['wall'] for r in rows),default=0)
    return output

if __name__=='__main__':
    data=summary(sys.argv[1]);target=Path(sys.argv[2]);target.write_text(json.dumps(data,indent=2))
    for k,v in data['variants'].items():print(k,{x:v[x] for x in ['pairs','mean_pct','median_pct','min_pct','max_pct','wins','ties','losses']})
