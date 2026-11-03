"""Read-only verification of measurements plus additive completion records."""
import hashlib,json,time,zipfile,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text())
def save(p,v):
 q=R/p
 assert not q.exists(),q
 q.write_text(json.dumps(v,indent=2))
# Verify the original final inventory before writing additive review artifacts.
initial=read('FINAL_INVENTORY.json')
for p,v in initial['files'].items():assert sha(R/p)==v['sha256'],p
for p,h in read('FREEZE.json')['files'].items():assert sha(ROOT/p)==h,p
assert sha(ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp')=='5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25'
s=read('SELECTION.json');source=R/s['package_source']/'main.cpp'
assert sha(source)==read('PACKAGE_CHECK.json')['source_sha256']
assert sha(R/'candidate_selected.zip')==read('PACKAGE_CHECK.json')['zip_sha256']['geometry']
with zipfile.ZipFile(R/'candidate_selected.zip')as z:
 assert set(z.namelist())=={'main.cpp','Makefile'}
 assert z.read('main.cpp')==source.read_bytes()
for p in ['REPORT_RU.md','PAIR_ANALYSIS_RU.md','RESOURCE_REPORT_RU.md']:
 for target in re.findall(r'\]\((/[^)]+)\)',(R/p).read_text()):assert Path(target).exists(),target
provenance={}
for name in ['screen30_v2','screen30_v4','screen30_v5','development280_v5_both','acceleration280','independent280']:
 m=read('logs/'+name+'/MANIFEST.json');h=m['runner_sha256']
 candidates=list((R/'artifacts/runners').glob('*.py'))+[R/'src/run.py',R/'src/run_instrumented.py']
 matches=[str(p.relative_to(ROOT))for p in candidates if sha(p)==h]
 assert matches,(name,h)
 provenance[name]=dict(runner_sha256=h,available_sources=matches,manifest_sha256=sha(R/'logs'/name/'MANIFEST.json'))
save('RUNNER_PROVENANCE_FINAL.json',provenance)
# Add a scope clarification without changing any existing journal bytes.
journal=ROOT/'EXPERIMENTS.md';before=journal.read_bytes();record=read('EXPERIMENT_LOG_UPDATE.json')
assert sha(journal)==record['after_sha256']
extra='\nУточнение выбранной конфигурации: v10/v5 GW_MODE1 включает геометрическую популяцию и передачу разнообразных готовых стартов. Whole-zone crossover и новая глобальная элита относятся к проверенному, но не выбранному GW_MODE2; singleton shortcut и mass balancing также остались отдельными прототипами. Наблюдаемый средний прирост на новых входах положительный (95% case-bootstrap к v4 [+0.9277%; +7.8716%]), но worst −3.6800% нарушает заранее заданный порог −1%. Неравномерно полученное CPU-время ограничивает интерпретацию; RESOURCE_REPORT_RU.md сохраняет измерения.\n'
with journal.open('ab')as f:f.write(extra.encode())
assert journal.read_bytes().startswith(before)
rows=read('logs/independent280/results.json');audit=read('FINAL_AUDIT.json');rec=read('FINAL_RECOMMENDATION.json')
assert len(rows)==72 and all(x['valid']and x['success']for x in rows)
assert max(x['wall']for x in rows)<300
save('FINAL_REVIEW.json',dict(status='complete',updated_unix=time.time(),initial_inventory_verified=True,initial_inventory_sha256=sha(R/'FINAL_INVENTORY.json'),frozen_files_unchanged=True,package_verified=True,report_links_exist=True,primary_runs=72,primary_valid=72,primary_working_success=72,quality_runs=audit['quality_runs'],qa_valid=audit['qa_valid'],candidate=rec['candidate'],promote=rec['promote'],journal_before_sha256=hashlib.sha256(before).hexdigest(),journal_after_sha256=sha(journal),journal_preserved_prefix=True,notes=['LIVE_STATE.json is a historical progress snapshot; CONFIRMATION_STATUS, WRAPUP_STATUS, COMPLETION and this record are final.','No algorithm/configuration/input/threshold changes after freeze.','RUNNER_PROVENANCE_FINAL.json extends the original screen-only provenance.']))
files={}
for p in R.rglob('*'):
 if p.is_file()and '__pycache__'not in p.parts and p.name!='FINAL_INVENTORY_POSTCHECK.json':files[str(p.relative_to(R))]=dict(bytes=p.stat().st_size,sha256=sha(p))
save('FINAL_INVENTORY_POSTCHECK.json',dict(count=len(files),bytes=sum(v['bytes']for v in files.values()),files=files))
print(json.dumps(dict(review='passed',candidate=rec['candidate'],promote=rec['promote'],vs_v4=rec['primary_vs_v4'],vs_v9=rec['primary_vs_v9'],inventory_files=len(files))))
