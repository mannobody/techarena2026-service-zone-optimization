"""Explicit development selection, immutable freeze, then untouched fresh confirmation."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];variant=sys.argv[1];assert variant in ['geometry','memetic']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stage(name,**kw):(R/'CONFIRMATION_STATUS.json').write_text(json.dumps(dict(stage=name,updated_unix=time.time(),**kw),indent=2))
def run(script,args,log):
 with (R/'logs'/log).open('x')as f:subprocess.run([sys.executable,str(R/'src'/script),*map(str,args)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
long='development280_v5_both';summary=json.loads((R/'logs'/long/'ANALYSIS.json').read_text());assert summary['runs']==summary['expected']==48
development_freeze=json.loads((R/'DEVELOPMENT_FREEZE_BOTH.json').read_text())
for p,h in development_freeze['files'].items():assert sha(ROOT/p)==h,p
assert not (R/'FRESH_INPUTS.json').exists()and not (R/'SELECTION.json').exists()
selection=dict(variant=variant,long_spec='DEVELOPMENT280_V5_BOTH.json',development_metrics={k:v['all_valid']for k,v in summary['comparisons'].items()},reason='Selected after complete long development comparison against both unchanged controls; independent inputs do not exist yet.',selected_unix=time.time(),independent_seen=False)
(R/'SELECTION.json').write_text(json.dumps(selection,indent=2))
files=[R/'artifacts/v5/main.cpp',R/'artifacts/v5/candidate',R/'artifacts/v5/geometry_warm.h',R/'artifacts/v5/build.py',R/'src/run.py',R/'src/run_instrumented.py',R/'src/analysis.py',R/'src/fresh.py',R/'src/select_and_confirm.py',ROOT/'tools/gen.py',ROOT/'task/validate_solution.py',R/'PROTOCOL.json',R/'INDEPENDENT_PLAN.json',R/'INDEPENDENT_RESOURCE_ADDENDUM.json',R/'SELECTION.json',R/('package_'+variant)/'main.cpp',R/('package_'+variant)/'Makefile',R/(variant+'_experimental.zip'),ROOT/'experiments/structural_v9/artifacts/v4',ROOT/'experiments/structural_v9/artifacts/final_research/candidate',ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp']
(R/'FREEZE.json').write_text(json.dumps(dict(files={str(p.relative_to(ROOT)):sha(p)for p in files},selected=variant,frozen_unix=time.time(),independent_not_generated=True),indent=2))
stage('generating_fresh',selected=variant);run('fresh.py',[],'fresh_generate.progress')
stage('independent280',selected=variant);run('run_instrumented.py',[R/'INDEPENDENT280.json'],'independent280.progress')
run('analysis.py',['independent280'],'independent280.summary')
for p,h in json.loads((R/'FREEZE.json').read_text())['files'].items():assert sha(ROOT/p)==h,p
stage('independent280_complete',selected=variant)
