import itertools,json
from oracle import R,instance,official,enumerate_all
from mip import improve
d=instance([(-4,1),(0,1),(4,1)],[(-4,0),(0,0),(4,0)],tasks=[[0],[1],[2]],workers=[[0,1],[1,2]],A=0,cap=1)
bad=[dict(officeId=i,sites=[i],workers=[i] if i<2 else []) for i in range(3)]
assert official(d,bad)=='Missing skills'
assert all(sum(k in s['tasks'] for s in d['sites'])<=sum(k in w for w in d['workers']) for k in range(3))
exact=enumerate_all(d);assert exact['value']==18
(R/'inputs/worker_counts_false_positive.json').write_text(json.dumps(d))
(R/'solutions/worker_counts_false_positive.INVALID.json').write_text(json.dumps(bad))
(R/'solutions/worker_counts_false_positive.json').write_text(json.dumps(exact['solution']))
rows=[]
for label in ['highs','scip']:
    v=improve(d,[],[0,1,2],seconds=2,backend=label,export=R/'models'/f'worker_counts_{label}')
    assert v['value']==18 and v['conditional_optimal'];rows.append(v)
(R/'logs/SKILL_COUNT_CASE.json').write_text(json.dumps(dict(official_bad='Missing skills',count_relaxation=27,exact=exact,models=rows),indent=2))
print('Necessary skill counts falsely allow 27; true optimum18 confirmed by exhaustive workers, SCIP, HiGHS.')
