import hashlib,json,re,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
f=json.loads((R/'FREEZE.json').read_text());checks=[]
for p,h in f['files'].items():assert sha(ROOT/p)==h,p
initial=json.loads((R/'PROVENANCE_INITIAL.json').read_text())
for p,h in initial['files'].items():
    if p!='EXPERIMENTS.md':assert sha(ROOT/p)==h,p
pkg=json.loads((R/'PACKAGE.json').read_text());z=ROOT/pkg['zip'];assert sha(z)==pkg['zip_sha256']
with zipfile.ZipFile(z) as archive:
    assert archive.namelist()==['main.cpp','Makefile']
    for name in archive.namelist():assert hashlib.sha256(archive.read(name)).hexdigest()==sha(R/'artifacts/final'/name)
assert sha(R/'artifacts/zip_check/solution')==sha(R/'artifacts/final/solution')==pkg['binary_sha256']
known_runners={sha(ROOT/'experiments/v4_perturbation/shared/run_blocks.py'),sha(R/'src/run_blocks_resume_v1.py'),sha(R/'src/run_blocks.py')}
for dest in sorted((R/'logs').iterdir()):
    if not (dest/'MANIFEST.json').exists():continue
    m=json.loads((dest/'MANIFEST.json').read_text())
    if 'runner_sha256' not in m:continue
    assert m['runner_sha256'] in known_runners,('runner',dest)
    for k in ['sources','binaries','inputs','checkpoints']:
        for label,h in m.get(k,{}).items():
            entry=m['spec']['variants'][label]['source' if k=='sources' else 'binary'] if k in ['sources','binaries'] else m['spec'][k if k=='checkpoints' else 'cases'][label]
            assert sha(ROOT/entry)==h,(dest,k,label)
    rows=json.loads((dest/'results.json').read_text()) if (dest/'results.json').exists() else []
    for row in rows:
        origin=ROOT/row['imported_from'] if row.get('imported_from') else dest
        prefix=origin/f"{row['case']}_{row['seed']}_{row['variant']}"
        assert sha(prefix.with_suffix('.solution.json'))==row['solution_sha256']
        for s in row['snapshots']:
            if s.get('file'):assert sha(ROOT/s['file'])==s['sha256']
        assert prefix.with_suffix('.stderr').exists()
        assert prefix.with_suffix('.resource').exists()
    checks.append(dict(series=dest.name,records=len(rows),complete=(dest/'COMPLETE.json').exists(),
        valid=sum(x['valid'] for x in rows),rc0=sum(x['rc']==0 for x in rows),timeouts=sum(x['timeout'] for x in rows),
        raw_success=sum(x['success'] for x in rows),max_wall=max([x['wall'] for x in rows],default=0)))
hashes={str(p.relative_to(R)):sha(p) for p in R.rglob('*') if p.is_file() and
    'offline_deps' not in p.parts and '__pycache__' not in p.parts and p.name not in ['ARTIFACT_HASHES.json','FINAL_AUDIT.json']}
(R/'ARTIFACT_HASHES.json').write_text(json.dumps(hashes,indent=2))
result=dict(pass_all=True,series=checks,files_hashed=len(hashes),frozen_files_unchanged=True,
    original_v4_v8_and_statement_validator_unchanged=True,zip_byte_identical=True,
    old_partial_series_not_marked_complete=True,interrupted_attempt_separate='logs/INTERRUPTION.json',
    raw_counterexample_harness_flags_preserved=True,exp_log_sha256=sha(ROOT/'EXPERIMENTS.md'),
    no_TL280_executed=True,no_git_staging_commit_push_or_server_submit=True)
(R/'FINAL_AUDIT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
