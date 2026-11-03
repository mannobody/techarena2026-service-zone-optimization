"""Audit stored evidence without rerunning any solver or changing manifests."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
report={}
for name in ['screen60','phase2_block60','synthetic_all5','counter_pilot30','control280']:
 D=R/'logs'/name;M=json.loads((D/'MANIFEST.json').read_text());S=M['spec'];rows=json.loads((D/'results.json').read_text())
 expected={(c,s,v) for c in S['cases'] for s in S['seeds'] for v in S['variants']}
 assert {(r['case'],r['seed'],r['variant']) for r in rows}==expected
 assert len(rows)==len(expected)
 for key,path in S['cases'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==M['inputs'][key]
 for key,v in S['variants'].items():assert hashlib.sha256((ROOT/v['binary']).read_bytes()).hexdigest()==M['binaries'][key]
 groups={}
 for r in rows:
  p=D/f"{r['case']}_{r['seed']}_{r['variant']}.json"
  assert r==json.loads(p.read_text()),p
  assert r['actual_nt']==2 or (name=='synthetic_all5' and r['case'] in ['edge_empty','edge_no_offices'] and r['actual_nt'] is None)
  groups.setdefault((r['case'],r['seed']),set()).add(tuple(r['affinity']))
 blocked=name!='screen60'
 if blocked:assert all(len(x)==1 for x in groups.values()),name
 report[name]={'runs':len(rows),'successes':sum(r['success'] for r in rows),'failures':sum(not r['success'] for r in rows),'current_binary_input_hashes_match':True,'all_rows_present_and_identical':True,'actual_nt_2_count':sum(r['actual_nt']==2 for r in rows),'trivial_preworker_exits_without_thread_log':[r['case'] for r in rows if r['actual_nt'] is None],'blocked_hardware_verified':blocked,'max_wall':max(r['wall'] for r in rows)}
report['artifacts']={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for pattern in ['src/*.cpp','*.patch','build*.py','run*.py','compile_locked.py'] for p in sorted(R.glob(pattern))}
(R/'EVIDENCE_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='artifacts'},indent=2))
