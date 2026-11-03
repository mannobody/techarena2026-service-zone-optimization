import json,time,os,hashlib,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];os.sched_setaffinity(0,{14,15});sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text())
def save(p,a):
 q=R/p;assert not q.exists(),q;q.write_text(json.dumps(a,indent=2))
# Source/policy selected on the completed screen; ongoing development cannot change it.
assert read('CORRECTED_STATUS.json')['stage']=='complete'
assert read('QA_FINAL_STATUS.json')['stage']=='complete'
assert not (R/'FREEZE.json').exists()
assert len(read('logs/scale_qa_v4/results.json'))==411
check=read('PACKAGE_CHECK_FINAL.json');assert check['byte_identical']and all(x['valid']and x['rc']==0 for x in check['tests'])
assert not (R/'inputs/fresh').exists()and not (R/'FRESH_INPUTS.json').exists()
source=R/'artifacts/v4/main.cpp';binary=R/'artifacts/v4/candidate';assert sha(source)==check['source_sha256']and sha(binary)==check['measured_binary_sha256']
selected=read('SCREEN_SELECTION.json')['selected'];assert selected['env']==check['configuration']
selection=dict(revision='v4',variant='adaptive',configuration=selected['env'],source='artifacts/v4/main.cpp',binary='artifacts/v4/candidate',package='adaptive_v11_final.zip',package_source='package_final',screen_selection=selected,development='logs/development280_v3 (prior numerical revision, same racing policy)',corrected_development='logs/corrected280_v4 (final source, directTL280)',certified_mechanism='logs/line_corrected280_v4',reason='Policy selected on completed16-input screen; final numerical source validated by411 oracle tests,66 QA,5 package contracts and completed6 directTL280 runs. Remaining development/clean-line blocks continue on disjoint CPUs and cannot change the frozen algorithm. User speed request permits independent evaluation to start on five already freed slots.',selected_unix=time.time())
save('SELECTION.json',selection)
plan=read('INDEPENDENT_ACCELERATED_PLAN.json');s=read('DEVELOPMENT280_V3.json');s['name']='independent280_v4';s['seconds']=plan['seconds'];s['seeds']=plan['seeds'];s['case_seeds']=plan['case_seeds'];s['cpus']=plan['cpus'];s['cases']={name:str((R/'inputs/fresh'/(name+'.json')).relative_to(ROOT))for name,_ in plan['parameters']};s['variants']['adaptive']['binary']=str(binary.relative_to(ROOT));save('INDEPENDENT280_V4.json',s)
paths=[source,binary,R/'adaptive_v11_final.zip',R/'package_final/main.cpp',R/'package_final/Makefile',R/'PACKAGE_CHECK_FINAL.json',R/'SELECTION.json',R/'INDEPENDENT280_V4.json',R/'INDEPENDENT_ACCELERATED_PLAN.json',R/'INDEPENDENT_PLAN.json',R/'PROTOCOL.json',R/'SPEED_ADDENDUM.json',R/'SPECIALIST_PLAN.json',R/'SCALE_CORRECTION_PLAN.json',ROOT/'tools/gen.py',ROOT/'task/validate_solution.py',ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp',ROOT/'experiments/structural_v9/artifacts/v4',ROOT/'experiments/warm_v10/artifacts/v5/main.cpp',ROOT/'experiments/warm_v10/artifacts/v5/candidate']
paths +=[R/'src'/p for p in ['build.py','portfolio.h','router.h','specialists.h','run_accelerated.py','analysis_accelerated.py','fresh_accelerated.py','resource_accelerated.py','freeze_early.py']]
save('FREEZE.json',dict(created_unix=time.time(),files={str(p.relative_to(ROOT)):sha(p)for p in paths},note='Final revisionv4/AP_POLICY1/AP_SHARE0; no source/config/data/threshold tuning after unseen generation. Report helpers may be added.'))
save('SELECTION_REVIEW_REQUIRED.json',dict(stage='frozen_before_fresh',freeze_sha256=sha(R/'FREEZE.json'),development_pending=True,corrected=read('logs/corrected280_v4/ANALYSIS.json')['comparisons'],inputs_not_generated=True))
(R/'FREEZE_STATUS.json').write_text(json.dumps(dict(stage='await_local_review',freeze_sha256=sha(R/'FREEZE.json')),indent=2));print('frozen; local review before fresh required',flush=True)
subprocess.run([sys.executable,str(R/'src/fresh_accelerated.py')],cwd=ROOT,check=True)
