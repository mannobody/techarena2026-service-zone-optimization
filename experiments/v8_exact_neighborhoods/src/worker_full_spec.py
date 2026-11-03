"""Turn the independently found node-cap rejection into a full-runtime barrier.
No tuning of candidate: source/binary are exactly the existing frozen package.
Off-diagonal distances isolate the known feasible identity allocation, so a
different permutation cannot conceal the false negative. Global optimum is45.
Three seeds of ONE input are repeats, not three independent tasks.
"""
import hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
data=json.loads((R/'inputs/worker_budget.json').read_text());n=len(data['sites'])
data['distances']=[[0 if o==s else 1000 for s in range(n)] for o in range(n)]
p=R/'inputs/worker_budget_isolated.json';assert not p.exists();p.write_text(json.dumps(data))
f=json.loads((R/'FREEZE.json').read_text());vs={k:v for k,v in f['variants'].items() if k in ['v4','v8','off','worker_only','candidate']}
tiny=dict(f['variants']['off']);tiny['env']=tiny['env']|{'XN_TINY':'1'};vs['tiny_only']=tiny
spec=dict(destination=str((R/'logs/worker_full').relative_to(ROOT)),seconds=2,seeds=[3601,3602,3603],cpu_pairs=[[14,15]],
    variants=vs,cases={'worker_budget_isolated':str(p.relative_to(ROOT))},order_seed=20261024,hard_wall=True,snapshots=[1],
    note='One mechanism counterexample, 3 repeats; not a new general holdout. No instance-ID branch. Source/binary frozen unchanged.',
    declared_unix=time.time(),input_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),known_optimum=45)
(R/'WORKER_FULL.json').write_text(json.dumps(spec,indent=2));print('18 full-runtime runs TL2, one independently derived counterexample, 3 seeds.')
