"""Run once AFTER build, BEFORE creating new instances or reading their outcomes."""
import hashlib,json,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:str(p.relative_to(ROOT))
assert (R/'artifacts/final/solution').exists()
assert not (R/'FREEZE.json').exists()
inputs={
 'anti':dict(ns=240,no=8,nw=24,nsk=4,dist='anti',A=10,af=.01,span=1,dscale=10000),
 'tightA_alpha':dict(ns=300,no=7,nw=18,nsk=5,dist='road',A=0,af=20,span=100),
 'multi_deficit':dict(ns=200,no=6,nw=9,nsk=6,wsk=3,deficit=1,A=10000,af=.05),
 'cluster_alpha0':dict(ns=350,no=8,nw=24,nsk=4,layout='cluster',A=10000,af=0),
 'grid_onsite':dict(ns=220,no=7,nw=20,nsk=4,layout='grid',offices='onsite',A=0,af=.01),
 'elongated':dict(ns=450,no=8,nw=24,nsk=4,dist='road',A=10000,af=.05),
 'large':dict(ns=3500,no=20,nw=50,nsk=7,dist='road',A=50,af=.01),
 'huge':dict(ns=10000,no=25,nw=60,nsk=6,dist='road',A=200,af=.01)}
src=rel(R/'artifacts/final/main.cpp');exe=rel(R/'artifacts/final/solution')
off=dict(DBG='1',ESCAPE_MODE='0',XN_FILL='0',XN_WORKER='0',XN_TINY='0',XN_MODE='0',XN_SIG_FIX='0')
variants={'v4':dict(binary=rel(R/'artifacts/v4'),source='experiments/v4_local_search/baseline/frozen_v4.cpp',env={'DBG':'1'}),
 'v8':dict(binary=rel(R/'artifacts/v8'),source=rel(R/'src/frozen_v8.cpp'),env={'DBG':'1'}),
 'off':dict(binary=exe,source=src,env=off,internal_watchdog=True),
 'fill_only':dict(binary=exe,source=src,env=off|{'XN_FILL':'2'},internal_watchdog=True),
 'worker_only':dict(binary=exe,source=src,env=off|{'XN_WORKER':'1'},internal_watchdog=True),
 'candidate':dict(binary=exe,source=src,env={'DBG':'1'},internal_watchdog=True)}
record=dict(frozen_unix=time.time(),status='frozen before independent input generation; do not tune on outcomes',
 files={rel(p):sha(p) for p in [R/'artifacts/final/main.cpp',R/'artifacts/final/solution',R/'artifacts/final/Makefile',R/'artifacts/v4',R/'artifacts/v8',
    R/'src/run_blocks.py',R/'src/independent.py',ROOT/'tools/gen.py',ROOT/'task/validate_solution.py']},
 independent_inputs=inputs,generator_seeds={k:1051000+301*i for i,k in enumerate(inputs)},
 transforms={'elongated':'y *= 0.001 for every site and office; retain road distances'},
 test_seeds=[3301,3302],seconds=10,cpu_pairs=[[18,19],[20,21]],variants=variants,order_seed=20261022,
 accept=dict(all_rc_zero_valid=True,all_process_wall_at_most_TL_plus_point1=True,
     mean_input_weighted_vs_v4_at_least=.1,median_nonnegative=True,every_input_median_nonnegative=True,
     worst_vs_v4_at_least=-1,bootstrap_lower_95_nonnegative=True,mean_vs_off_nonnegative=True,mean_vs_v8_nonnegative=True,
     undefined_percentage_rejects=True),
 run_cap=dict(primary=96,additional_repeats=0,TL60=32,TL280=0),
 tl60_trigger='Only if all primary acceptance criteria pass. Same 8 inputs, seed3401, variants v4/v8/off/candidate, same frozen binaries, TL60. No changes after viewing primary.',
 compiler=subprocess.check_output(['g++','--version'],text=True).splitlines()[0],flags='-O3 -std=c++17 -pthread',
 no_instance_id_branches=True)
(R/'FREEZE.json').write_text(json.dumps(record,indent=2));print('Code, binaries, params, test composition, criteria and 128-run maximum frozen; TL280 forbidden.')
