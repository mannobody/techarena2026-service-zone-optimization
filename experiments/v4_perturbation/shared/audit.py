"""Independent record/product/identity/affinity audit of every completed series."""
import hashlib,itertools,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report={'time':time.time(),'series':[],'overlaps':[],'preexisting_changes':[]};intervals=[]
spec_hashes={sha(p):str(p.relative_to(R)) for folder in ['shared','geometry_lab','escape_lab','integration'] for p in (R/folder).glob('*.json')}
for mp in sorted(R.rglob('MANIFEST.json')):
 m=json.loads(mp.read_text());d=mp.parent
 if 'spec' not in m or not (d/'COMPLETE.json').exists():continue
 s=m['spec'];rows=json.loads((d/'results.json').read_text())
 if 'cases' not in s:
  # Dedicated no-argument contract series has its own schema and early exits.
  errors=[]
  for k in ['source','binary']:
   if sha(ROOT/s[k])!=m[k+'_sha256']:errors.append(k+' hash')
  if sha(R/'integration/contract.py')!=m['runner_sha256']:errors.append('contract runner hash')
  if len(rows)!=len(m['inputs']):errors.append('contract row count')
  for r in rows:
   inp=d/r['case']/'instance.json';out=d/r['case']/'solution.json'
   if sha(inp)!=r['input_sha256'] or sha(out)!=r['solution_sha256']:errors.append('contract artifact hash '+r['case'])
   intervals.append((r['started_unix'],r['ended_unix'],set(r['affinity']),str(d.relative_to(R))+'/'+r['case']))
  report['series'].append({'directory':str(d.relative_to(R)),'expected':len(m['inputs']),'rows':len(rows),'success':sum(r['success'] for r in rows),'errors':errors});continue
 expected=set(itertools.product(s['cases'],s['seeds'],s['variants']))
 keys=[(r['case'],r['seed'],r['variant']) for r in rows];errors=[]
 if len(keys)!=len(set(keys)) or set(keys)!=expected:errors.append('expected key product mismatch')
 if m.get('spec_sha256') not in spec_hashes:errors.append('spec hash missing or altered')
 if sha(R/'shared/run_blocks.py')!=m['runner_sha256']:errors.append('runner hash')
 if m.get('validator_sha256')!=sha(ROOT/'task/validate_solution.py'):errors.append('validator hash')
 complete=json.loads((d/'COMPLETE.json').read_text())
 if complete!={'expected':len(expected),'completed':len(rows),'success':sum(r['success'] for r in rows)}:errors.append('COMPLETE mismatch')
 for label,h in m['binaries'].items():
  if sha(ROOT/s['variants'][label]['binary'])!=h:errors.append('binary hash '+label)
 for label,h in m.get('sources',{}).items():
  if sha(ROOT/s['variants'][label]['source'])!=h:errors.append('source hash '+label)
 for key,paths in [('inputs',s['cases']),('checkpoints',s.get('checkpoints',{}))]:
  for label,h in m.get(key,{}).items():
   if sha(ROOT/paths[label])!=h:errors.append(key+' hash '+label)
 byblock={}
 for r in rows:
  stem=f"{r['case']}_{r['seed']}_{r['variant']}"
  if json.loads((d/(stem+'.json')).read_text())!=r:errors.append('row differs '+stem)
  if r.get('solution_sha256') and sha(d/(stem+'.solution.json'))!=r['solution_sha256']:errors.append('solution hash '+stem)
  expected_success=r['rc']==0 and not r['timeout'] and r['wall']<=s['seconds']+3 and r['valid'] and not r['error_log'] and r['actual_nt']==2
  if expected_success!=r['success']:errors.append('success mismatch '+stem)
  block=(r['case'],r['seed']);a=tuple(r['affinity'])
  if block in byblock and byblock[block]!=a:errors.append('affinity mismatch '+str(block))
  byblock[block]=a
  intervals.append((r['started_unix'],r['ended_unix'],set(a),str(d.relative_to(R))+'/'+stem))
 report['series'].append({'directory':str(d.relative_to(R)),'expected':len(expected),'rows':len(rows),'success':sum(r['success'] for r in rows),'errors':errors})
intervals.sort()
for i,a in enumerate(intervals):
 for b in intervals[i+1:]:
  if b[0]>=a[1]:break
  if a[2]&b[2]:report['overlaps'].append([a[3],b[3],sorted(a[2]&b[2])])
before=json.loads((R/'PREEXISTING_HASHES.json').read_text())
for path,h in before.items():
 p=ROOT/path
 if not p.exists() or sha(p)!=h:report['preexisting_changes'].append(path)
report['all_record_checks_pass']=not report['overlaps'] and not report['preexisting_changes'] and not any(x['errors'] for x in report['series'])
(R/'integration/EVIDENCE_AUDIT.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='series'},indent=2));print('series',len(report['series']),'runs',sum(x['rows'] for x in report['series']))
