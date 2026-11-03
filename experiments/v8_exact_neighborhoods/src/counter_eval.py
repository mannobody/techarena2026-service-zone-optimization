import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];dest=R/'logs/worker_full'
rows=json.loads((dest/'results.json').read_text());complete=json.loads((dest/'COMPLETE.json').read_text());assert complete['completed']==18
expected={'v4':36,'v8':36,'off':36,'worker_only':45,'tiny_only':45,'candidate':45};audits=[]
for r in rows:
    text=(dest/f"{r['case']}_{r['seed']}_{r['variant']}.stderr").read_text()
    single='XN global_complete=1' in text and r['actual_nt'] is None
    ok=r['rc']==0 and r['valid'] and r['wall']<=2.1 and (r['actual_nt']==2 or single or r.get('hard_stopped') or r.get('watchdog_exit_inferred'))
    assert ok and r['objective']==expected[r['variant']],r
    audits.append(dict(seed=r['seed'],variant=r['variant'],objective=r['objective'],wall=r['wall'],
        raw_runner_success=r['success'],contract_success=ok,
        threads_basis='One thread; proved global optimum before native thread creation' if single else r.get('thread_count_basis','NT=2'),
        note='Original runner expects threads=2 final log and marks early exact return false; preserved raw record, not a solver failure' if not r['success'] and single else None))
result=dict(inputs=1,repeats=3,valid=18,contract_success=18,
    global_optimum=45,global_upper_bound_proof='maxSize=1, pr<=10, every nonempty office cost1 => each of five sites contributes at most9; known identity certificate attains45',
    native_upper_bound_without_false_rejected_identity=36,
    observed_native={'v4':[36]*3,'v8':[36]*3,'off':[36]*3},observed_new={'worker_only':[45]*3,'tiny_only':[45]*3,'candidate':[45]*3},
    delta_pct=25,WTL=[3,0,0],generalization='One constructed mechanism case, not broad full-solver superiority',
    raw_runner_false_early_exact=sum(not r['raw_runner_success'] for r in audits),audits=audits)
(dest/'COUNTEREXAMPLE_EVALUATION.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='audits'}))
