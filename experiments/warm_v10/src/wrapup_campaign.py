import hashlib,json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def stage(name,**kw):(R/'WRAPUP_STATUS.json').write_text(json.dumps(dict(stage=name,updated_unix=time.time(),**kw),indent=2))
stage('waiting_measurements')
while not (R/'CONFIRMATION_STATUS.json').exists()or json.loads((R/'CONFIRMATION_STATUS.json').read_text())['stage']!='independent280_complete':time.sleep(1)
while not (R/'RESOURCE_DIAGNOSTIC_STATUS.json').exists()or json.loads((R/'RESOURCE_DIAGNOSTIC_STATUS.json').read_text())['stage']not in ['not_required','resource_diagnostic280_complete']:time.sleep(1)
stage('reporting')
for script in ['pair_report.py','resource_report.py','finalize.py']:
 with (R/'logs'/(script+'.output')).open('x')as f:subprocess.run([sys.executable,str(R/'src'/script)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
rec=json.loads((R/'FINAL_RECOMMENDATION.json').read_text());v4=rec['primary_vs_v4'];v9=rec['primary_vs_v9'];audit=json.loads((R/'FINAL_AUDIT.json').read_text());journal=ROOT/'EXPERIMENTS.md';before=journal.read_bytes();heading='## Warm start v10, 22 октября 2026'
assert heading.encode()not in before
text=f'''\n\n{heading}

Продолжение immutable structural-v9 tail и точной server-v4 SHA5b3914…: геометрические геномы, истинный feasible fitness, два warm-потока, разнообразие назначений, пространственный crossover целых зон и прямая передача стартов в LNS. Дополнительно singleton-invariant shortcut (24/24 точные оценки,9.709→0.140s для подзадачи) и массовая балансировка power cells (механизм20→40 VALID). Все старые версии сохранены, solver/ не переписан.

Выбран {rec['candidate']}; независимые8 новых входов120–10000 сайтов×3seed (включая0)×3версии,TL280/NT2: mean к v4 {v4['mean_case_percent']:+.4f}%, median{v4['median']:+.4f}%, worst{v4['worst']:+.4f}%,W/T/L{v4['wins']}/{v4['ties']}/{v4['losses']}; к v9 mean{v9['mean_case_percent']:+.4f}%. Рекомендация: {rec['recommended']}; promotion={rec['promote']}. Ресурсный повтор, если вызван, отдельный и не заменяет primary. Всего quality{audit['quality_runs']},VALID{audit['quality_valid']},рабочих успехов{audit['quality_working_success']}; все ошибки/перелёты сохранены.

Материалы: experiments/warm_v10/REPORT_RU.md, AUDIT_RU.md, FINAL_METRICS.json, FINAL_AUDIT.json, FREEZE.json, candidate_selected.zip. Пакет побайтно воспроизводит измеренный бинарник; официальный noarg/file-contract пройден. Без staging/commit/push/submit и без удаления прежних результатов.
'''
with journal.open('ab')as f:f.write(text.encode())
(R/'EXPERIMENT_LOG_UPDATE.json').write_text(json.dumps(dict(before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(journal.read_bytes()).hexdigest(),appended_bytes=len(text.encode()),preserved_prefix=journal.read_bytes().startswith(before)),indent=2))
stage('complete',promote=rec['promote'],candidate=rec['candidate'])
files={}
for p in R.rglob('*'):
 if p.is_file()and '__pycache__'not in p.parts and p.name!='FINAL_INVENTORY.json':files[str(p.relative_to(R))]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
(R/'FINAL_INVENTORY.json').write_text(json.dumps(dict(count=len(files),bytes=sum(a['bytes']for a in files.values()),files=files),indent=2))
print(json.dumps(dict(complete=True,promote=rec['promote'],candidate=rec['candidate'],vs_v4=v4,vs_v9=v9)),flush=True)
