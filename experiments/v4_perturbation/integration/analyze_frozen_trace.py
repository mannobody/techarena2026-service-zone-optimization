"""Offline episode-cost accounting; never changes the frozen solver or inputs."""
import json,re,statistics
from pathlib import Path
I=Path(__file__).resolve().parent;ROOT=I.parents[2]
def stats(x):
    return {'n':len(x),'sum':sum(x),'mean':statistics.mean(x),'median':statistics.median(x),'max':max(x)} if x else {'n':0}
def records(text,prefix):
    return [{k:float(v) for k,v in re.findall(r'([a-z_]+)=([-+0-9.eE]+)',s)} for s in re.findall(prefix+r' ([^\n]+)',text)]
out=[];incomplete=[]
for t in [60,280]:
    for suffix in ['', '_VARIANCE']:
        sp=I/f'HOLDOUT{t}{suffix}.json'
        if not sp.exists():continue
        spec=json.loads(sp.read_text());d=ROOT/spec['destination']
        if not (d/'COMPLETE.json').exists():
            incomplete.append(str(d));continue
        for row in json.loads((d/'results.json').read_text()):
            if row['variant']!='candidate':continue
            text=(d/f"{row['case']}_{row['seed']}_candidate.stderr").read_text()
            g=records(text,'GEOBOUND');e=records(text,'ESCAPE')
            assert all(x['mode']==5 for x in g+e)
            def total(rows,k):return sum(x.get(k,0) for x in rows)
            ticks=total(e,'ticks');flat=total(e,'plateau_ticks')
            out.append({'seconds':t,'stage':'extra' if suffix else 'primary','case':row['case'],'seed':row['seed'],
                'success':row['success'],'wall':row['wall'],'objective':row['objective'],
                'controller_records':len(e),'ticks':ticks,'plateau_ticks':flat,
                'iteration_sample_plateau_fraction':flat/ticks if ticks else None,
                'episodes':total(e,'episodes'),'improved_episode_records':total(e,'improved_episodes'),
                'same_max_records':total(e,'same_max'),'episode_thread_seconds':total(e,'escape_seconds'),
                'controller_thread_seconds':total(e,'seconds'),
                'geometry_boundary_calls':len(g),'raw_successes':total(g,'raw_success'),'retained_calls':total(g,'retained'),
                'proposal_attempts':total(g,'attempts'),'accepted_transactions':total(g,'accepted'),
                'moved_sites':total(g,'moved'),'freed_points':total(g,'freed_points'),
                'repair_call_seconds':stats([x['repair_seconds'] for x in g]),
                'construction_plus_repair_call_seconds':stats([x['total_seconds'] for x in g]),
                'repair_calls_above_nominal_40ms':sum(x['repair_seconds']>.04 for x in g),
                'endpoint_changes':{k:total(e,k) for k in ['changed_assignment','changed_office','changed_hull','changed_worker']}})
report={'rows':out,'incomplete_series_not_pooled':incomplete,'note':'Sums are thread-local observations, not process wall or distinct global improvements. Sampled plateau ticks are not uniform-time samples. Endpoint changes include restore-best and native moves. Improved episodes can be caused by native search, not necessarily the kick. repair_seconds includes boundary plus resync/observe/offer; nominal40ms is a DFS cutoff, not a guaranteed total call bound.'}
(I/'FINAL_TRACE_ACCOUNTING.json').write_text(json.dumps(report,indent=2))
print('candidate traces',len(out))
