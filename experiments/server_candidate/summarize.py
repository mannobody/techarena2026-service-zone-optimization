from pathlib import Path
import hashlib,json,statistics,re,zipfile,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
summary={}
for tag in ['repeat12','large30']:
 p=HERE/'logs'/tag/'results.json'
 if not p.exists():continue
 d=json.loads(p.read_text());rows=d['results'];groups={}
 for case in sorted({r['case'] for r in rows}):
  values={v:[r['score'] for r in rows if r['case']==case and r['variant']==v and not r['error']] for v in sorted({r['variant'] for r in rows})}
  med={v:statistics.median(a) for v,a in values.items() if a};base=med.get('before',med.get('before_o2'))
  groups[case]=dict(medians=med,count={v:len(a) for v,a in values.items()},percent=(100*(med['candidate']/base-1) if base and 'candidate' in med else None))
 summary[tag]=dict(rows=len(rows),errors=sum(bool(r['error']) or r['returncode']!=0 for r in rows),groups=groups)
p=HERE/'logs/profile.json'
if p.exists():
 rows=json.loads(p.read_text());summary['allocation_profile']={}
 for case in sorted({r['case'] for r in rows}):
  for kind in ['fast','hull']:
   info={v:dict(allocations=[r['allocations'] for r in rows if r['case']==case and r['kind']==kind and r['variant']==v],median_wall=statistics.median(r['seconds'] for r in rows if r['case']==case and r['kind']==kind and r['variant']==v)) for v in ['before','candidate']}
   summary['allocation_profile'][case+'/'+kind]=info
(HERE/'logs/SUMMARY.json').write_text(json.dumps(summary,indent=2))
archive=ROOT/'experiments/evolution/artifacts/server_v2.zip';dest=HERE/'artifacts/case03_cpp_server_v2.zip';shutil.copy2(archive,dest)
manifest=json.loads((ROOT/'experiments/evolution/artifacts/server_v2/manifest.json').read_text())
for name,h in manifest['source_build']['source_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==h,name
assert hashlib.sha256(dest.read_bytes()).hexdigest()==manifest['archive_sha256']
with zipfile.ZipFile(dest) as z:assert sorted(z.namelist())==['Makefile','main.cpp']
manifest['archive_path']=str(dest);manifest['research_files_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*HERE.glob('*.py'),*HERE.glob('*.cpp'),*HERE.glob('*.md'),*HERE.glob('logs/*.json'),*HERE.glob('logs/*/results.json')]}
(HERE/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(summary,indent=2))
