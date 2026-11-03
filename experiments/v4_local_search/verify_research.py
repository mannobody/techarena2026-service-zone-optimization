"""Final reproducibility/validation audit, read only except its JSON report."""
from pathlib import Path
import json,hashlib,zipfile
R=Path(__file__).resolve().parent;ROOT=R.parents[1];checks={}
def check(name,b):
 checks[name]=bool(b)
 assert b,name
D=json.loads((R/'FINAL_METRICS.json').read_text())
check('all_declared_quality_series_complete',len(D['quality'])==12)
check('all_quality_processes_successful',all(q['runs']==q['success'] for q in D['quality'].values()))
check('geometry_state',all(x['rc']==0 for x in json.loads((R/'logs/geometry_state.json').read_text())))
check('cycle_state', 'checks=24000 accepted=4871 rejected=19129 cycle_invariants=80' in (R/'logs/cycle_invariants.txt').read_text())
for name,n,key in [('repair_oracle',60,'ok'),('repair_oracle_extended',24,'ok'),('gww_fixed',24,'success'),('package_contract',6,'success'),('boundary_counterfactual2_seeded',48,'success')]:
 a=json.loads((R/'logs'/name/'results.json').read_text());check(name,len(a)==n and all(x[key] for x in a))
check('failed_harness_preserved',sum(not x['success'] for x in json.loads((R/'logs/warm_operators2/results.json').read_text()))==12)
check('wall_failures_preserved',sum(not x['success'] for x in json.loads((R/'logs/repair10/results.json').read_text()))==3)
for v in ['2','3','4','FINAL']:
 d=R/'src'/('candidate_final' if v=='FINAL' else 'candidate_v'+v)
 for name,h in json.loads((R/('SOURCE_FINAL.json' if v=='FINAL' else 'SOURCE_V'+v+'.json')).read_text()).items():check('source_'+v+'_'+name,hashlib.sha256((d/name).read_bytes()).hexdigest()==h)
for name,h in json.loads((R/'SOURCE_FINAL.json').read_text()).items():check('working_'+name,hashlib.sha256((ROOT/'solver'/name).read_bytes()).hexdigest()==h)
P=json.loads((R/'PACKAGE_SAFE.json').read_text())
for name,h in P['files'].items():check(name,hashlib.sha256((R/name).read_bytes()).hexdigest()==h)
with zipfile.ZipFile(R/'artifacts/case03_cpp_v4_balanced_cycle_safe_experimental_O3.zip') as z:
 check('zip_two_files',sorted(z.namelist())==['Makefile','main.cpp'])
 for name in z.namelist():check('zip_payload_'+name,z.read(name)==(R/'artifacts/package_cycle_safe'/name).read_bytes())
check('frozen_v4_unchanged',hashlib.sha256((ROOT/'experiments/server_v4/artifacts/case03_cpp_server_v4_O3.zip').read_bytes()).hexdigest()=='b4e9ace4ed6cffe53b932bb1d10f7ecdfdcc4170458afaf05e16b3068ebae953')
check('canonical_cpu_intervals',not json.loads((R/'RUN_AUDIT.json').read_text())['cpu_overlap_conflicts'])
(R/'VERIFICATION.json').write_text(json.dumps({'passed':sum(checks.values()),'checks':checks},indent=2));print('verified',len(checks),'checks')
