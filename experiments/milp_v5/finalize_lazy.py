from pathlib import Path

# Serialize an observation copy without altering commands or subprocess env.
import sys as _report_sys
_REPORT_ROOT = next(p for p in Path(__file__).resolve().parents
                    if (p / 'tools/public_metadata.py').is_file())
_report_sys.path.insert(0, str(_REPORT_ROOT / 'tools'))
from public_metadata import public_json as _public_json
def report_json(value, **kwargs):
    return _public_json(value, _REPORT_ROOT, **kwargs)

import json,hashlib,statistics,re,zipfile,subprocess,difflib,tempfile
H=Path(__file__).resolve().parent;R=H.parents[1]
def load(tag):
 d=json.loads((H/'logs'/tag/'results.json').read_text());return d['results'] if isinstance(d,dict) else d
summaries={};tables={};tails={}
for tag,n in [('native_train60',30),('full_holdout60',60),('tail_holdout60',60),('lazy_holdout60',60)]:
 rows=load(tag);assert len(rows)==n;assert all(r['rc']==0 and r['error'] is None for r in rows);by={(r['case'],r['seed'],r['variant']):r for r in rows};cases=sorted({r['case'] for r in rows});seeds=sorted({r['seed'] for r in rows});delta=[];table=[];miprows=[]
 for c in cases:
  ds=[]
  for s in seeds:
   b=by[c,s,'base'];v=by[c,s,'candidate'];d=100*(v['score']-b['score'])/max(abs(b['score']),1e-9);ds.append(d)
   lines=Path(v['solution']).with_suffix('.stderr').read_text().splitlines();phases=[]
   for line in lines:
    if not line.startswith('v5_mip'):continue
    fields=dict(re.findall(r'(\w+)=([\d.e+\-]+)',line));fields={k:float(val) for k,val in fields.items()};phases.append(fields)
   gain=sum(p['after']-p['before'] for p in phases);start=phases[0]['before'] if phases else v['score'];miprows.append(dict(case=c,seed=s,phases=phases,gain=gain,pct=100*gain/max(1e-9,abs(start)),ran=bool(phases)))
  delta+=ds;table.append('| '+c+' | '+' | '.join(f'{x:+.4f}%' for x in ds+[statistics.mean(ds),statistics.median(ds)])+' |')
 summaries[tag]=dict(runs=n,valid=n,pairs=n//2,mean_pct=statistics.mean(delta),median_pct=statistics.median(delta),worst_pct=min(delta),best_pct=max(delta),wins=sum(x>1e-8 for x in delta),ties=sum(abs(x)<=1e-8 for x in delta),losses=sum(x< -1e-8 for x in delta),max_base_wall=max(r['wall'] for r in rows if r['variant']=='base'),max_candidate_wall=max(r['wall'] for r in rows if r['variant']=='candidate'),mip_ran=sum(x['ran'] for x in miprows),mip_improved=sum(x['gain']>1e-7 for x in miprows),mean_mip_pct=statistics.mean(x['pct'] for x in miprows))
 tables[tag]='\n'.join(table);tails[tag]=miprows
for tag,n in [('package60',26),('package_tail60',26),('grouped60',45),('flow_fixed60',30),('expand60_v2',20),('native_post60',30),('split60',6),('fallback60',2),('fallback_lazy60',2),('package_lazy60',26)]:
 rows=load(tag);assert len(rows)==n
 if tag.startswith('package'):assert all(r['error'] is None and r['rc']==0 for r in rows)
 else:assert all(r.get('valid') for r in rows)
assert json.loads((H/'logs/zip_lazy_check.json').read_text())['valid']
assert len(json.loads((H/'logs/oracle.json').read_text()))==80
assert len(json.loads((H/'logs/native_oracle_first40.json').read_text()))==40
assert len(load('native_oracle_v2'))==20
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
v4=json.loads((H.parent/'server_v4/MANIFEST.json').read_text());assert sha(v4['zip'])==v4['sha256'];assert all(sha(p)==s for p,s in v4['primary_snapshot'].items())
preg=json.loads((H/'LAZY_PREREGISTRATION.json').read_text());assert sha(preg['candidate'])==preg['sha256'];assert sha(H/'artifacts/package_lazy/main.cpp')==preg['sha256']
z=H/'artifacts/case03_cpp_server_v5_milp_lazy_O3.zip'
if not z.exists():
 with zipfile.ZipFile(z,'x',compression=zipfile.ZIP_DEFLATED) as f:
  for name in ['main.cpp','Makefile']:f.write(H/'artifacts/package_lazy'/name,name)
with zipfile.ZipFile(z) as f:assert hashlib.sha256(f.read('main.cpp')).hexdigest()==preg['sha256'];assert sorted(f.namelist())==['Makefile','main.cpp']
base=(H.parent/'server_v4/artifacts/package/main.cpp').read_text();cand=(H/'artifacts/native_v5.cpp').read_text();(H/'artifacts/v4_to_v5_milp_lazy.patch').write_text(''.join(difflib.unified_diff(base.splitlines(True),cand.splitlines(True),fromfile='a/main.cpp',tofile='b/main.cpp')))
with tempfile.TemporaryDirectory(prefix='v5-patch-') as td:
 target=Path(td)/'main.cpp';target.write_text(base)
 pr=subprocess.run(['patch','-p1','-i',str(H/'artifacts/v4_to_v5_milp_lazy.patch')],cwd=td,capture_output=True,text=True)
 assert pr.returncode==0,pr.stderr
 assert target.read_text()==cand
 (H/'logs/patch_check.json').write_text(report_json(dict(applied=True,exact_source_match=True,source_sha256=sha(target)),indent=2))
(H/'SUMMARY.json').write_text(report_json(summaries,indent=2));(H/'MIP_ATTRIBUTION.json').write_text(report_json(tails,indent=2))
intro=f'''# Результат исследования MILP для v5

Подготовлен **экспериментальный v5 preview**: `{z.relative_to(_REPORT_ROOT)}`. SHA256 `{sha(z)}`. Это отдельный архив, v4 сохранён. На сервер ничего не отправлено. По умолчанию используется оставшееся время после всех стадий v4; оператор **не резервирует время** у основного поиска. Ограничение тестов60 с, стандартный бюджет посылки280 с.

Финальная независимая проверка: mean **{summaries['lazy_holdout60']['mean_pct']:+.4f}%**, median **{summaries['lazy_holdout60']['median_pct']:+.4f}%**, худшая пара **{summaries['lazy_holdout60']['worst_pct']:+.4f}%**, wins/ties/losses **{summaries['lazy_holdout60']['wins']}/{summaries['lazy_holdout60']['ties']}/{summaries['lazy_holdout60']['losses']}**. Сам MILP улучшил своё входное решение в **{summaries['lazy_holdout60']['mip_improved']}/30** запусках; подробная атрибуция в MIP_ATTRIBUTION.json. Это первые измерения кандидата, не гарантия превосходства на скрытых тестах.

'''
body=(H/'REPORT_TEMPLATE.md').read_text()
sections=[]
configs=[('native_train60','Разработка: первоначальный joint-only хвост с резервом2 с','validation2 из geometry_islands, seeds121/122/123,5 классов, jobs6, NT2, O3, HiGHS1. Только обучение/выбор механизма.'),('full_holdout60','Первый независимый набор: staged хвост с резервом0.5 с','Новые генераторные seeds271000+100*j, latent272000/272001, solver131/132/133.10 классов, jobs6, NT2, O3. Исходник и настройки зафиксированы в PREREGISTRATION.json до запуска.'),('tail_holdout60','Второй независимый набор: хвост без резерва, с ранней загрузкой библиотеки','Ещё новые генераторные seeds281000+100*j, latent282000/282001, solver151/152/153.10 классов, jobs6, NT2, O3. TAIL_PREREGISTRATION.json создан до запуска. После анализа этой серии подготовлена следующая ревизия, проверенная на новом наборе.')]
configs.append(('lazy_holdout60','Третий независимый набор: финальный lazy MILP tail','Ещё новые генераторные seeds291000+100*j, latent292000/292001, solver161/162/163.10 классов, jobs6, NT2, O3. LAZY_PREREGISTRATION.json создан до запуска. Ни ранней загрузки HiGHS, ни дополнительного копирования работников во время поиска, ни изменения временных бюджетов v4.'))
for tag,title,config in configs:
 s=summaries[tag];seeds=sorted({r['seed'] for r in load(tag)})
 sections.append(f'''## {title}

{config} Общий TL60 для baseline и candidate; baseline — frozen v4. Mean {s['mean_pct']:+.4f}%, median {s['median_pct']:+.4f}%, worst {s['worst_pct']:+.4f}%. Все{s['valid']}/{s['runs']} VALID. Max wall: база{s['max_base_wall']:.3f} с, кандидат{s['max_candidate_wall']:.3f} с. Значения wall выше60, если есть, явно сохранены, не округлены до заявления «строго≤60».

| Задача | seed{seeds[0]} | seed{seeds[1]} | seed{seeds[2]} | Среднее | Медиана |
|---|---:|---:|---:|---:|---:|
{tables[tag]}

MILP вызывался в{s['mip_ran']}/{s['pairs']} запусках, собственное улучшение в{s['mip_improved']} запусках; средний собственный прирост по всем кандидатным запускам{s['mean_mip_pct']:.4f}%. Разница с baseline включает изменения случайной траектории и взаимодействие финальных стадий; её нельзя целиком приписать MILP. Формулировка и само улучшение проверяются постобработкой одного фиксированного incumbent отдельно.
''')
reg=[]
for tag in ['full_holdout60','tail_holdout60','lazy_holdout60']:
 rows=load(tag);by={(r['case'],r['seed'],r['variant']):r for r in rows};rr=[]
 for m in tails[tag]:
  b=by[m['case'],m['seed'],'base'];v=by[m['case'],m['seed'],'candidate'];delta=100*(v['score']/b['score']-1) if b['score'] else 0
  if delta<-.5:rr.append((delta,m,b,v))
 for delta,m,b,v in sorted(rr,key=lambda x:x[0])[:4]:
  before=m['phases'][0]['before'] if m['phases'] else v['score'];reg.append(f"| {tag}/{m['case']}/{m['seed']} | {delta:+.4f}% | {b['score']:.6f} | {before:.6f} | {m['gain']:.6f} | {v['score']:.6f} |")
sections.append('## Разбор существенных регрессий\n\n| Серия/задача/seed | Изменение | Base final | Candidate перед MILP | Собственный MIP gain | Candidate final |\n|---|---:|---:|---:|---:|---:|\n'+'\n'.join(reg)+'\n\nMILP публикует только прошедшее verify улучшение. Если candidate уже отстаёт до первого вызова, эту потерю нельзя объяснять ухудшением его решения внутри MILP. Изменение бюджета, размещения финальных стадий, загрузки библиотеки и многопоточного расписания меняет траекторию. Какой вклад даёт каждый фактор, отдельно не доказано; крупные отрицательные пары сохранены, а не списаны автоматически на шум. Положительное среднее не означает отсутствия риска регрессии.\n')

post=load('native_post60');posttable=[]
for case in sorted({r['case'] for r in post}):
 rs={r['mode']:r for r in post if r['case']==case};cells=[]
 for mode in ['0','1','2']:
  r=rs[mode];cells.append(f"{100*(r['value']/r['before']-1):+.5f}% / {r['stats']['seconds']:.3f} с")
 posttable.append('| '+case+' | '+' | '.join(cells)+' |')
sections.append('## Native post: одинаковые исходные решения\n\nИсходные incumbents v4 package60 SEED101 NT2; постобработка NT1 с лимитом60, jobs4, O3. Это native_v1 operator, до изменения размещения/двухступенчатости. Время — весь native post process elapsed (парсинг/подготовка включены), внешний validator вне него.\n\n| Задача | Старые оболочки, те же работники | Расширение, те же работники | Расширение, совместные работники |\n|---|---:|---:|---:|\n'+'\n'.join(posttable)+'\n')
sections.append('''## Почему не включён split/reopen

Дополнительно проверены6 диагностических случаев, до60 с на пакет из до9 локальных MILP: закрытый офис внутри старой оболочки получает половину этой территории, задаваемую разделителем между офисами; затем совместно выбираются сайты и работники. Везде сохранён исходный score. Часть узких моделей доказала оптимальность, часть исчерпала бюджет. В диагностике прежнего провала DP/large0 не предлагался пропущенный офис5: он не входил в выбранные пары покрывающий офис→закрытый офис. Поэтому этот эксперимент не доказывает невозможность исправить тот провал — он показывает ограниченность данного генератора пула. Три фиксированных направления и top3 пары не исчерпывают геометрические перестройки. Bounds только для каждого пула. В default этот оператор не включён.

В split60 измеренный wall включает повторную проверку результата после выхода дочернего solver; у huge0 получилось61.518 с, хотя дочерний процесс имел cutoff60. Это исследовательская диагностика, не часть native60 A/B и не заявленная серверная реализация split.

## Диагностика открытия пропущенного офиса5

На прежнем DP-regression large0/seed111 входное решение163270.803884 имело8 офисов; известный native-baseline с9 офисами —178722.967019. Закрытый офис5 не покрыт старой зоной, поэтому split/reopen его не рассматривает. Обычное safe-grow с предложением нового офиса создало для него пул64 сайтов; решение выросло лишь до163335.211282, офис5 остался закрытым.

Проверен отдельный new-first вариант: сначала расширять новый офис, до2048 предложений для него и5000 попыток всего, затем старые зоны. Пул офиса5 вырос до120 сайтов, но максимум текущих количеств318 при A116 означает минимальные202 сайта для нового офиса без сокращения остальных. Модель могла сокращать другие зоны, однако доказала условный оптимум163334.222851 за7.574 с вместе с построением. Большого выигрыша нет. Этот bound относится только к полученному пулу;120 — размер эвристически построенной оболочки, не верхняя оценка любой возможной зоны офиса5.

Таким образом, больше времени на эту MILP не восстановит известное решение178722.967019: его нет в пуле. Нужно совместно менять границы/освобождать пространство, либо предлагать несколько согласованных вариантов оболочек. Это отдельный диагностический вход, выбранный из известной регрессии; его нельзя выдавать за независимое подтверждение среднего прироста. New-first не включён в ZIP. Код и результаты: envelopes_newfirst.py, diagnose_newfirst.py, logs/reopen_newfirst60/; native diagnostic: logs/reopen_diagnostic60/.

## Проверки посылки, память и воспроизведение

Три packaged версии (с резервом0.5, без резерва и финальная lazy) проверены на26 edge/precision/crossing входах с конкурсными именами instance.json/solution.json, TL60 NT2 SEED101, jobs3. Все результаты валидны. Проверены отсутствие libhighs и MIP=0 (прототип native_v3, общий loader/disabled path): два60-секундных запуска валидны; ещё два таких запуска выполнены на финальной lazy версии. Native MILP не требует файлов модели. На10k-сайтовом incumbent staged post60 занял59.68 с с пиковым RSS158.594 МиБ; это измерение одного NT1 post процесса, не верхняя оценка памяти полного16-поточного solver.

Основная команда финального A/B (использовать новый tag, чтобы не переписывать сырые логи):

```sh
/tmp/ta-boundary-venv/bin/python experiments/milp_v5/bench_full_tail.py --tag repeat_lazy60 --split lazy_holdout --variants base,candidate --seeds 161,162,163 --seconds 60 --threads 2 --jobs 6 --exe native_v5
```

Финальный исходник `artifacts/native_v5.cpp`; это внутренняя пятая ревизия прототипа MILP, **не архив v4**. Посылка именуется v5_milp_lazy. Patch `artifacts/v4_to_v5_milp_lazy.patch` применяется к main.cpp распакованной v4 и даёт точно протестированный исходник. Для Makefile дополнительно нужен `-ldl`; новый ZIP уже содержит эту команду. Без внешней библиотеки runtime остаётся native; фактический hidden-host не проверялся.

Следующий предметный шаг для v5 — улучшать генерацию безопасных пулов: сдвиг общей границы пары зон, полезное открытие/закрытие офисов и перенос сайтов с пересчётом геометрии. Текущие результаты показывают, что быстрый count/load MILP уже умеет использовать свободные сайты; более дорогая постановка без подходящего пула часто не даёт ничего. Новый оператор сначала следует проверять на неизменном incumbent, затем — в полном равном60-секундном бюджете с новыми seeds.
''')
(H/'REPORT.md').write_text(intro+body+'\n\n'+(H/'NEXT_MODEL.md').read_text()+'\n\n'+'\n'.join(sections))
(H/'README.md').write_text(f'''# v5 MILP preview\n\nZIP: `{z.relative_to(_REPORT_ROOT)}`. SHA256 `{sha(z)}`.\n\n- `make build`: g++ -O3 -std=c++17 -o solution main.cpp -ldl\n- `make run`: ./solution; instance.json → solution.json\n- По умолчанию 280 с; MILP только в свободном хвосте после стадий v4, без резерва времени.\n- Требуется доступная libhighs.so или libhighs.so.1 с32-bit HighsInt; проверено на1.15.1. При отсутствии/несовместимости работает native fallback. Библиотека в ZIP не включена.\n- `MIP=0` отключает MILP; `DBG=1` показывает v5_mip в stderr при запуске оператора.\n- Независимый60-секундный A/B: mean{summaries['lazy_holdout60']['mean_pct']:+.4f}%, median{summaries['lazy_holdout60']['median_pct']:+.4f}%, worst{summaries['lazy_holdout60']['worst_pct']:+.4f}%. Все60 VALID; package26 VALID. Экспериментальный кандидат, не гарантия скрытого score.\n- На TL=60 фактический max wall финального кандидата: {summaries['lazy_holdout60']['max_candidate_wall']:.3f} с; таймер HiGHS мягкий.
- v4 и основной solver/ сохранены. Без коммита и отправки на сервер.\n\nПодробности, сравнения, ограничения и отрицательные результаты: REPORT.md.\n''')
for name in ['REPORT.md','README.md']:
 p=H/name
 prose=p.read_text()
 prose=re.sub(r'(?<=[А-Яа-яЁё])(?=\d)', ' ', prose)
 prose=re.sub(r'(?<=\d)(?=[А-Яа-яЁё])', ' ', prose)
 p.write_text(prose)
paths=[p for p in H.rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.name not in ['MANIFEST.json','PATHS.json']]
(H/'PATHS.json').write_text(report_json(dict(root=str(H),files=sorted(str(p) for p in paths)),indent=2))
tracked=[H/'logs/patch_check.json',H/'NEXT_MODEL.md',H/'logs/zip_lazy_check.json',H/'REPORT.md',H/'README.md',H/'SUMMARY.json',H/'MIP_ATTRIBUTION.json',H/'PREREGISTRATION.json',H/'TAIL_PREREGISTRATION.json',H/'LAZY_PREREGISTRATION.json',H/'LAZY_SOURCE_AUDIT.json',H/'PATHS.json',H/'artifacts/native_v5.cpp',H/'artifacts/native_v5',H/'artifacts/v4_to_v5_milp_lazy.patch',z]+[H/'logs'/tag/'results.json' for tag in ['native_train60','full_holdout60','tail_holdout60','lazy_holdout60','package60','package_lazy60','package_tail60','grouped60','flow_fixed60','expand60_v2','native_post60','split60','fallback60','fallback_lazy60']]
tracked=sorted(p for p in H.rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.name!='MANIFEST.json')
(H/'MANIFEST.json').write_text(report_json(dict(status='Experimental v5 MILP preview; not submitted',zip=str(z),v4_sha256=v4['sha256'],primary_snapshot_unchanged=True,source_sha256=sha(H/'artifacts/native_v5.cpp'),files={str(p):sha(p) for p in tracked}),indent=2));print(report_json(summaries,indent=2));print(z.relative_to(_REPORT_ROOT))
