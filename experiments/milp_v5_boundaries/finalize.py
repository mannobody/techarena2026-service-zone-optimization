from pathlib import Path

# Serialize an observation copy without altering commands or subprocess env.
import sys as _report_sys
_REPORT_ROOT = next(p for p in Path(__file__).resolve().parents
                    if (p / 'tools/public_metadata.py').is_file())
_report_sys.path.insert(0, str(_REPORT_ROOT / 'tools'))
from public_metadata import public_json as _public_json
def report_json(value, **kwargs):
    return _public_json(value, _REPORT_ROOT, **kwargs)

import json,hashlib,statistics,re,zipfile,difflib,subprocess,tempfile
H=Path(__file__).resolve().parent;R=H.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(tag):
 d=json.loads((H/'logs'/tag/'results.json').read_text());return d.get('results',[]) if isinstance(d,dict) else d
summary={};tables={};attrib={}
for tag,n in [('full_train60',30),('coop_holdout60',60)]:
 rows=load(tag);assert len(rows)==n;assert all(r['rc']==0 and r['error'] is None for r in rows);by={(r['case'],r['seed'],r['variant']):r for r in rows};seeds=sorted({r['seed'] for r in rows});cases=sorted({r['case'] for r in rows});delta=[];table=[];own=[]
 for c in cases:
  ds=[]
  for seed in seeds:
   b=by[c,seed,'base'];v=by[c,seed,'candidate'];d=100*(v['score']-b['score'])/max(abs(b['score']),1e-9);ds.append(d);ph=[]
   for line in Path(v['solution']).with_suffix('.stderr').read_text().splitlines():
    if line.startswith('v52_mip '):ph.append({k:float(val) for k,val in re.findall(r'(\w+)=([\d.e+\-]+)',line)})
   gain=sum(p.get('own_gain',p['after']-p['before']) for p in ph);own.append(dict(case=c,seed=seed,phases=ph,gain=gain,ran=bool(ph),pct=100*gain/max(1e-9,ph[0]['before']) if ph else 0))
  delta+=ds;table.append('| '+c+' | '+' | '.join(f'{x:+.4f}%' for x in ds+[statistics.mean(ds),statistics.median(ds)])+' |')
 summary[tag]=dict(runs=n,valid=n,pairs=n//2,mean_pct=statistics.mean(delta),median_pct=statistics.median(delta),worst_pct=min(delta),best_pct=max(delta),wins=sum(x>1e-8 for x in delta),ties=sum(abs(x)<=1e-8 for x in delta),losses=sum(x< -1e-8 for x in delta),max_base_wall=max(r['wall'] for r in rows if r['variant']=='base'),max_candidate_wall=max(r['wall'] for r in rows if r['variant']=='candidate'),region_ran=sum(r['ran'] for r in own),region_improved=sum(r['gain']>1e-7 for r in own),mean_own_pct=statistics.mean(r['pct'] for r in own))
 tables[tag]='\n'.join(table);attrib[tag]=own
for tag,n in [('master_train60',15),('perspective_train60',15),('fixed_train60',15),('configs_train60',5),('native_quick',20),('native_post60',20),('native_power60',10)]:
 rows=load(tag);assert len(rows)==n,(tag,len(rows));assert all(r['valid'] for r in rows);assert all(not r.get('invalid',[]) for r in rows)
for tag in ['oracle_v2','oracle_perspective_v2','native_oracle','native_fixed_oracle']:
 rows=load(tag);assert len(rows)==30;assert all(abs(r['value']-r['expected'])<1e-6 for r in rows)
rows=load('package60');assert len(rows)==26 and all(r['rc']==0 and r['error'] is None for r in rows)
rows=load('fallback60');assert len(rows)==2 and all(r['valid'] for r in rows)
memory=json.loads((H/'logs/memory60/results.json').read_text());assert memory['valid']
zcheck=json.loads((H/'logs/zip_check.json').read_text());assert zcheck['valid'] and zcheck['compiled_from_zip'];z=Path(zcheck['zip'])
preg=json.loads((H/'COOP_PREREGISTRATION.json').read_text());assert sha(preg['candidate'])==preg['sha256'];assert sha(H/'artifacts/package/main.cpp')==preg['sha256']
with zipfile.ZipFile(z) as f:assert sorted(f.namelist())==['Makefile','main.cpp'];assert hashlib.sha256(f.read('main.cpp')).hexdigest()==preg['sha256']
v4=json.loads((H.parent/'server_v4/MANIFEST.json').read_text());assert sha(v4['zip'])==v4['sha256'];assert all(sha(p)==v for p,v in v4['primary_snapshot'].items())
v5=json.loads((H.parent/'milp_v5/MANIFEST.json').read_text());assert all(sha(p)==v for p,v in v5['files'].items())
base=(H.parent/'milp_v5/artifacts/native_v5.cpp').read_text();cand=(H/'artifacts/native_coop.cpp').read_text();patch=H/'artifacts/v5_to_v5_2_regions.patch';patch.write_text(''.join(difflib.unified_diff(base.splitlines(True),cand.splitlines(True),fromfile='a/main.cpp',tofile='b/main.cpp')))
with tempfile.TemporaryDirectory(prefix='v52-patch-') as td:
 p=Path(td)/'main.cpp';p.write_text(base);q=subprocess.run(['patch','-p1','-i',str(patch)],cwd=td,capture_output=True,text=True);assert q.returncode==0,q.stderr;assert p.read_text()==cand
(H/'logs/patch_check.json').write_text(report_json(dict(applied=True,exact_source_match=True,source_sha256=preg['sha256']),indent=2))
(H/'SUMMARY.json').write_text(report_json(summary,indent=2));(H/'ATTRIBUTION.json').write_text(report_json(attrib,indent=2))
s=summary['coop_holdout60'];intro=f'''# v5.2: MILP выбора границ зон

Подготовлен экспериментальный кандидат `{z.relative_to(_REPORT_ROOT)}`. SHA256 `{sha(z)}`. Старые v4/v5 сохранены; на сервер не отправлено.

Независимый полный A/B против предыдущего v5, общий TL=60 с, NT=2, 10 новых входов × 3 solver seed: среднее **{s['mean_pct']:+.4f}%**, медиана **{s['median_pct']:+.4f}%**, худшая пара **{s['worst_pct']:+.4f}%**, wins/ties/losses **{s['wins']}/{s['ties']}/{s['losses']}**. Все 60 ответов валидны. Новый региональный оператор вызывался в {s['region_ran']}/30 и сам улучшил общий best в {s['region_improved']}/30 запусков. Эти собственные улучшения не равны полному эффекту изменения алгоритма.

Максимальное фактическое время: baseline {s['max_base_wall']:.3f} с, кандидат {s['max_candidate_wall']:.3f} с. Значения сверх 60 не скрыты; внутренний таймер HiGHS мягкий. Результат остаётся исследовательским, без гарантии превосходства на скрытых тестах.

'''
decision=('Среднее в этой независимой серии отрицательное: заменять предыдущую v5 этой сборкой пока не обосновано. Архив оставлен для исследования.' if summary['coop_holdout60']['mean_pct']<=0 else 'Среднее положительное, но регрессии в отдельных парах сохраняются: кандидат остаётся экспериментальным, без заявления устойчивого превосходства.')
intro+=decision+'\n\n'
parts=[]
for tag,title,desc in [('full_train60','Отброшенный ранний вызов','Development: предыдущие данные lazy_holdout, solver seeds 171/172/173, 5 классов. Вызов до workers, максимум 2 с. O3/NT2/jobs6. TRAIN_PREREGISTRATION.json.'),('coop_holdout60','Финальный вызов внутри рабочего потока','Новые generator seeds 321000+100*j, latent322000/322001; solver seeds 181/182/183. O3/NT2/jobs6. COOP_PREREGISTRATION.json создан до запуска. После просмотра этой серии код не менялся.')]:
 t=summary[tag];seeds=sorted({r['seed'] for r in load(tag)});parts.append(f'''## {title}

{desc} Среднее {t['mean_pct']:+.4f}%, медиана {t['median_pct']:+.4f}%, худшая пара {t['worst_pct']:+.4f}%. Валидность {t['valid']}/{t['runs']}. Max wall base/candidate: {t['max_base_wall']:.3f}/{t['max_candidate_wall']:.3f} с. Собственное улучшение новой стадией: {t['region_improved']}/{t['pairs']}; среднее собственное относительное улучшение входного best по всем запускам: {t['mean_own_pct']:.4f}%.

| Класс | seed {seeds[0]} | seed {seeds[1]} | seed {seeds[2]} | Среднее | Медиана |
|---|---:|---:|---:|---:|---:|
{tables[tag]}
''')
rows=[]
for tag in ['master_train60','perspective_train60','fixed_train60','configs_train60']:
 for r in sorted(load(tag),key=lambda r:(r['case'],r['mode'])):
  rows.append(f"| {tag} | {r['case']} | {r['mode']} | {100*(r['value']/r['before']-1):+.5f}% | {r.get('seconds',r['wall']):.3f} | {r.get('variables','—')} | {r.get('nodes','—')} | {r['status'].replace('HighsModelStatus.k','')} |")
parts.append('## Python: сравнение постановок на одних incumbents\n\nВремя включает подготовку внутри модели; region_seconds и общий process wall сохранены отдельно в JSON. Ограничение дочернего процесса 60 с. Это дополнительная постобработка готового v5, а не полный равный бюджет.\n\n| Модель | Класс | Области | Прирост | Время модели, с | Переменные | Узлы | Статус |\n|---|---|---|---:|---:|---:|---:|---|\n'+'\n'.join(rows)+'\n')
rows=[]
for tag in ['native_quick','native_post60','native_power60']:
 for r in sorted(load(tag),key=lambda r:(r['case'],r['mode'])):rows.append(f"| {tag} | {r['case']} | {r['mode']} | {100*(r['value']/r['before']-1):+.5f}% | {r['wall']:.3f} |")
parts.append('## C++ post: одинаковые сайты и работники на входе\n\nИсходные назначения работников передаются без повторной эвристической реконструкции. native_quick — дополнительный эксперимент с внутренним бюджетом 2 с; основные проверки имеют TL=60. В native_power60 используются только исходные и power-области; первые две серии используют оба генератора. Время wall включает весь процесс, внешний валидатор выполняется после него.\n\n| Серия | Класс | Работники | Прирост | Wall, с |\n|---|---|---|---:|---:|\n'+'\n'.join(rows)+'\n')
parts.append(f'''## Проверка архива и воспроизведение

26 edge/precision/crossing входов, TL60 NT2 SEED101: все валидны. Дополнительно два 60-секундных запуска без библиотеки/с MIP=0: валидны, обе MILP-стадии отключены. Архив распакован, пересобран через make build и отдельно запущен на 60 с, NT2, SEED155; wall {zcheck['wall']:.3f} с, ответ валиден. На 10k-входе полный NT2 solver с TL60 имел peak RSS {memory['max_rss_kib']/1024:.3f} МиБ, wall {memory['wall']:.3f} с; это одно измерение, не верхняя оценка для NT16. Native source hash: `{preg['sha256']}`. Patch применён к исходнику старого v5 и побайтово воспроизвёл финальный source.

```sh
/tmp/ta-boundary-venv/bin/python experiments/milp_v5_boundaries/bench_full.py --tag repeat_new_tag --split coop_holdout --variants base,candidate --seeds 181,182,183 --seconds 60 --threads 2 --jobs 6 --exe native_coop
```

Главные файлы: `src/region_mip_coop.h`, `artifacts/native_coop.cpp`, `regions.py`, `master_perspective.py`, `master_fixed.py`. Старый early-кандидат сохранён отдельно в `artifacts/native.cpp`. PATHS.json содержит полные пути ко всем данным и логам, MANIFEST.json — hashes. Ранние ошибки компиляции (локальная переменная pair закрыла std::pair), oracle-bound tolerance и неудачные постановки сохранены.

Следующий шаг определяется измерениями: дорабатывать генерацию совместимых областей и быстро проверять новые офисы с локальным перераспределением работников. Полная совместная модель при слишком широком наборе областей часто тратит минуту без улучшения; увеличение её бюджета без изменения постановки не обосновано текущими данными.
''')
(H/'REPORT.md').write_text(intro+(H/'REPORT_TEMPLATE.md').read_text()+'\n\n'+'\n'.join(parts))
(H/'README.md').write_text(f'''# v5.2 regions — экспериментальная сборка

ZIP: `{z.relative_to(_REPORT_ROOT)}`\nSHA256: `{sha(z)}`

- Сборка: `make build` (`g++ -O3 -std=c++17 -ldl`), запуск: `make run`.
- Только instance.json → solution.json. Default 280 с; проверено с TL=60, NT=2.
- HiGHS загружается динамически; нужна доступная libhighs.so/.so.1 с 32-bit HighsInt. Без неё работает native fallback.
- `REGION=0` отключает новую стадию; `MIP=0` отключает обе MILP-стадии.
- Полный новый A/B против v5: mean {s['mean_pct']:+.4f}%, median {s['median_pct']:+.4f}%, worst {s['worst_pct']:+.4f}%; 60/60 VALID, package 26/26 VALID.
- Собственное улучшение региональной стадией: {s['region_improved']}/30. Max wall кандидата: {s['max_candidate_wall']:.3f} с при TL=60; таймер библиотеки мягкий.
- v4/v5 и solver/ не заменены; без коммита и отправки.

{decision}\n\nПодробности и отрицательные результаты: REPORT.md.
''')
paths=sorted(p for p in H.rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.name not in ['PATHS.json','MANIFEST.json']);(H/'PATHS.json').write_text(report_json(dict(root=str(H),files=[str(p) for p in paths]),indent=2));paths.append(H/'PATHS.json')
(H/'MANIFEST.json').write_text(report_json(dict(status='Experimental; not submitted',zip=str(z),source_sha256=preg['sha256'],old_v5_unchanged=True,promoted=False,old_v4_unchanged=True,primary_snapshot_unchanged=True,files={str(p):sha(p) for p in paths}),indent=2))
print(report_json(summary,indent=2));print(z.relative_to(_REPORT_ROOT))
