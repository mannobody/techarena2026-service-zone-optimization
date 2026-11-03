import hashlib,json,subprocess,time,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
f=json.loads((R/'FREEZE.json').read_text());contract=json.loads((R/'logs/contract/results.json').read_text())
assert all(r['rc']==0 and r['valid'] and r.get('optimal_tiny',True) and r['wall']<=1.1 for r in contract)
for p,h in f['files'].items():assert sha(ROOT/p)==h,(p,'freeze changed')
z=R/'artifacts/case03_cpp_exact_neighborhoods_experimental_O3.zip';assert not z.exists()
with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as out:
    for name in ['main.cpp','Makefile']:
        info=zipfile.ZipInfo(name,date_time=(2026,10,20,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=0o644<<16;out.writestr(info,(R/'artifacts/final'/name).read_bytes())
d=R/'artifacts/zip_check';d.mkdir(exist_ok=False)
with zipfile.ZipFile(z) as archive:assert archive.namelist()==['main.cpp','Makefile'];archive.extractall(d)
with (R/'logs/build_zip.log').open('w') as log:
    subprocess.run(['taskset','-c','14,15','make','-C',str(d),'build'],stdout=log,stderr=log,check=True)
assert sha(d/'solution')==sha(R/'artifacts/final/solution'),'ZIP rebuilt binary differs'
record=dict(status='experimental; quality decision in REPORT_RU.md and FINAL_DECISION.json',
    zip=str(z.relative_to(ROOT)),zip_sha256=sha(z),entries=['main.cpp','Makefile'],
    source_sha256=sha(d/'main.cpp'),makefile_sha256=sha(d/'Makefile'),binary_sha256=sha(d/'solution'),
    byte_identical_to_frozen_test_binary=True,freeze_sha256=sha(R/'FREEZE.json'),
    contract_valid=len(contract),default_seconds=280,default_threads=2,
    no_external_solver_runtime=True,no_network_runtime=True,no_runtime_checkpoint=True,
    build_flags='-O3 -std=c++17 -pthread',packaged_unix=time.time())
(R/'PACKAGE.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
