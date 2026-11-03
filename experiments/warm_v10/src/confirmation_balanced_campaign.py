"""Choose v5/v6 using the declared paired development rule, freeze, generate fresh inputs."""
import hashlib,json,statistics,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stage(name,**kw):(R/'CONFIRMATION_STATUS.json').write_text(json.dumps(dict(stage=name,updated_unix=time.time(),**kw),indent=2))
def run(script,args,log):
 with (R/'logs'/log).open('x')as f:subprocess.run([sys.executable,str(R/'src'/script),*map(str,args)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
stage('waiting_acceleration_development')
while not (R/'ACCELERATION_STATUS.json').exists()or json.loads((R/'ACCELERATION_STATUS.json').read_text())['stage']!='acceleration280_complete':time.sleep(1)
summary=json.loads((R/'logs/acceleration280/ANALYSIS.json').read_text());assert summary['runs']==summary['expected']==30
rows=json.loads((R/'logs/acceleration280/results.json').read_text());by={(x['case'],x['seed'],x['variant']):x for x in rows};spec=json.loads((R/'ACCELERATION280.json').read_text());methods={}
def sound(v):
 a=[x for x in rows if x['variant']==v]
 return len(a)==6 and all(x['valid']and x['rc']==0 and not x['timeout']and not x['error']and x['wall']<300 for x in a)
for label in ['candidate','balanced']:
 pairs=[]
 for c in spec['cases']:
  for seed in spec['seeds']:
   a=by[(c,seed,label)];b=by[(c,seed,'prior')];assert a['affinity']==b['affinity']
   if not a['valid']or not b['valid']:continue
   delta=a['official']-b['official'];percent=100*delta/abs(b['official'])if abs(b['official'])>1e-9 else None
   pairs.append(dict(case=c,seed=seed,base=b['official'],candidate=a['official'],delta=delta,percent=percent))
 means=[statistics.mean(x['percent']for x in pairs if x['case']==c and x['percent']is not None)for c in spec['cases']if any(x['percent']is not None for x in pairs if x['case']==c)]
 mean=statistics.mean(means)if means else None;worst=min((x['percent']for x in pairs if x['percent']is not None),default=None)
 eligible=sound(label)and len(pairs)==6 and mean is not None and mean>0 and worst is not None and worst>=-1.
 methods[label]=dict(pairs=pairs,mean_case_percent=mean,worst_pair_percent=worst,eligible=eligible)
eligible=[k for k,m in methods.items()if m['eligible']]
variant=max(eligible,key=lambda k:methods[k]['mean_case_percent'])if eligible else 'prior'
revision={'candidate':'v6','balanced':'v8','prior':'v5'}[variant];assert sound(variant),('no sound selected candidate',variant)
post=dict(methods=methods,selected=variant,rule=json.loads((R/'ACCELERATION_SELECTION_RULE.json').read_text()))
(R/'ACCELERATION_DECISION.json').write_text(json.dumps(post,indent=2))
architecture=json.loads((R/'ACCELERATION_FREEZE.json').read_text())['selected_architecture'];mode=int(spec['variants'][variant]['env']['GW_MODE'])
assert architecture==('geometry'if mode==1 else 'memetic')
assert not (R/'FRESH_INPUTS.json').exists()and not (R/'SELECTION.json').exists()and not (R/'FREEZE.json').exists()
pkg=R/('package_'+architecture if revision=='v5'else 'package_'+revision+'_'+architecture)
zip_path=R/(architecture+'_experimental.zip'if revision=='v5'else architecture+'_'+revision+'_experimental.zip')
check_path=R/('PACKAGE_CHECK.json'if revision=='v5'else 'PACKAGE_CHECK_'+revision+'.json')
check=json.loads(check_path.read_text());assert check['byte_identical']and all(x['valid']for x in check['cases'])
selection=dict(variant=variant,revision=revision,architecture=architecture,mode=mode,long_spec='ACCELERATION280.json',source='artifacts/'+revision+'/main.cpp',binary='artifacts/'+revision+'/candidate',package=str(zip_path.relative_to(R)),package_source=str(pkg.relative_to(R)),post_development=post,selected_unix=time.time(),independent_seen=False,reason='Architecture selected from full six-input v5 development; singleton acceleration and explicit geometric mass balancing selected only by the declared paired TL280 rule. No independent inputs exist yet.')
(R/'SELECTION.json').write_text(json.dumps(selection,indent=2));(R/'candidate_selected.zip').write_bytes(zip_path.read_bytes())
for freeze_name in ['DEVELOPMENT_FREEZE_BOTH.json','ACCELERATION_FREEZE.json']:
 for p,h in json.loads((R/freeze_name).read_text())['files'].items():assert sha(ROOT/p)==h,p
files=[R/'artifacts'/revision/'main.cpp',R/'artifacts'/revision/'candidate',R/'artifacts'/revision/'geometry_warm.h',R/'artifacts'/revision/'build.py',R/'src/run.py',R/'src/run_instrumented.py',R/'src/analysis.py',R/'src/fresh.py',R/'src/confirmation_balanced_campaign.py',ROOT/'tools/gen.py',ROOT/'task/validate_solution.py',R/'PROTOCOL.json',R/'INDEPENDENT_PLAN.json',R/'INDEPENDENT_RESOURCE_ADDENDUM.json',R/'SELECTION.json',R/'ACCELERATION_DECISION.json',R/'ACCELERATION_SELECTION_RULE.json',pkg/'main.cpp',pkg/'Makefile',zip_path,R/'candidate_selected.zip',check_path,ROOT/'experiments/structural_v9/artifacts/v4',ROOT/'experiments/structural_v9/artifacts/final_research/main.cpp',ROOT/'experiments/structural_v9/artifacts/final_research/candidate',ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp']
if revision=='v8':files.append(R/'artifacts/v8/balanced_warm.h')
(R/'FREEZE.json').write_text(json.dumps(dict(files={str(p.relative_to(ROOT)):sha(p)for p in files},selected=variant,revision=revision,architecture=architecture,frozen_unix=time.time(),independent_not_generated=True),indent=2))
stage('generating_fresh',**{k:selection[k]for k in ['variant','revision','architecture']});run('fresh.py',[],'fresh_generate.progress')
stage('independent280',**{k:selection[k]for k in ['variant','revision','architecture']});run('run_instrumented.py',[R/'INDEPENDENT280.json'],'independent280.progress')
run('analysis.py',['independent280'],'independent280.summary')
for p,h in json.loads((R/'FREEZE.json').read_text())['files'].items():assert sha(ROOT/p)==h,p
stage('independent280_complete',**{k:selection[k]for k in ['variant','revision','architecture']})
print(json.dumps(dict(status='independent280_complete',selection=selection['revision']+'_'+selection['architecture'])),flush=True)
