"""Audit complete evidence and produce compact Russian report, no solver changes."""
import hashlib,json,statistics,time,zipfile,re,random
from pathlib import Path

# Serialize an observation copy without altering commands or subprocess env.
import sys as _report_sys
_REPORT_ROOT = next(p for p in Path(__file__).resolve().parents
                    if (p / 'tools/public_metadata.py').is_file())
_report_sys.path.insert(0, str(_REPORT_ROOT / 'tools'))
from public_metadata import public_json as _public_json
def report_json(value, **kwargs):
    return _public_json(value, _REPORT_ROOT, **kwargs)

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
assert json.loads((R/'CAMPAIGN_STATUS.json').read_text())['stage']=='complete'
assert json.loads((R/'RESOURCE_REPEAT_STATUS.json').read_text())['stage']=='complete'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((R/'FREEZE.json').read_text())
for p,h in freeze['files'].items():assert sha(ROOT/p)==h,p
assert sha(ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp')=='5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25'
selection=json.loads((R/'HOLDOUT_SELECTION.json').read_text());selected=selection['selected']
summaries={};audits={}
for name in ['screen8','screen20_v3','pilot20_signed_v5','mechanism10_signed','negative_swap8','development280','independent280','resource_repeat280']:
    d=R/'logs'/name;s=json.loads((d/'SUMMARY.json').read_text())if (d/'SUMMARY.json').exists()else None
    if s is None:continue
    rows=json.loads((d/'results.json').read_text());man=json.loads((d/'MANIFEST.json').read_text());spec=man['spec']
    expected={(c,seed,v)for c in spec['cases']for seed in spec['seeds']for v in spec['variants']}
    assert {(r['case'],r['seed'],r['variant'])for r in rows}==expected and len(rows)==len(expected)
    assert sha(ROOT/'task/validate_solution.py')==man['validator']
    for c,h in man['inputs'].items():assert sha(ROOT/spec['cases'][c])==h
    for v,h in man['binaries'].items():assert sha(ROOT/spec['variants'][v]['binary'])==h
    by={(r['case'],r['seed'],r['variant']):r for r in rows}
    for c in spec['cases']:
        for seed in spec['seeds']:assert len({tuple(by[c,seed,v]['affinity'])for v in spec['variants']})==1
    audits[name]=dict(expected=len(expected),rows=len(rows),valid=sum(r['valid']for r in rows),success=sum(r['success']for r in rows),nonzero_rc=sum(r['rc']!=0 for r in rows),timeouts=sum(r['timeout']for r in rows),invalid=sum(not r['valid']for r in rows),error_log=sum(r['error']for r in rows),over_wall=sum(r['wall']>spec['seconds']+.2 for r in rows),max_wall=max(r['wall']for r in rows),internal_deadline_stops=sum(r.get('internal_deadline_stop',False)for r in rows))
    audits[name]['invalid_validated_snapshots']=[dict(case=r['case'],seed=r['seed'],variant=r['variant'],snapshot=x)for r in rows for x in r.get('snapshots',[])if isinstance(x.get('official'),str)]
    for r in rows:
        out=d/f"{r['case']}_{r['seed']}_{r['variant']}.solution.json"
        assert sha(out)==r['solution_sha256']
    summaries[name]=s
# Check actual solver intervals for overlap on any CPU across the two long stages.
longrows=[]
for name in ['development280','independent280','resource_repeat280']:longrows += [dict(**r,series=name)for r in json.loads((R/'logs'/name/'results.json').read_text())]
overlap=[]
for j,a in enumerate(longrows):
    for b in longrows[:j]:
        if set(a['affinity'])&set(b['affinity'])and min(a['ended_unix'],b['ended_unix'])>max(a['started_unix'],b['started_unix'])+.01:
            overlap.append([a['case'],a['seed'],a['variant'],b['case'],b['seed'],b['variant']])
assert not overlap,overlap
audits['cpu_intervals']=dict(overlapping_solver_runs=overlap,parent_affinity=[14,15],solver_cpu_pairs=json.loads((R/'DEVELOPMENT280.json').read_text())['cpus'],note='All pairs use different physical cores according to stored lscpu topology. Full-machine power/thermal noise remains possible.')
efficiency=[]
for r in longrows:
    if r['wall']<252:continue
    q=r.get('resource_fields',{});cpu=q['user']+q['sys']if 'user'in q and 'sys'in q else None
    efficiency.append(dict(series=r['series'],case=r['case'],seed=r['seed'],variant=r['variant'],affinity=r['affinity'],cpu_seconds=cpu,wall=r['wall'],cpu_per_wall=cpu/r['wall']if cpu is not None else None))
audits['cpu_efficiency']=dict(runs=efficiency,below_one_cpu=[r for r in efficiency if r['cpu_per_wall']is not None and r['cpu_per_wall']<.9],missing_cpu=[r for r in efficiency if r['cpu_per_wall']is None],interpretation='Low accumulated CPU time observed in some wall-limited native runs; cause unresolved. CPU pinning is verified, equal actual CPU consumption is not claimed. No rows removed or relabelled as independent repeats.')
(R/'FINAL_AUDIT.json').write_text(report_json(audits,indent=2))
stages=[]
for name in ['development280','independent280','resource_repeat280']:
    for r in json.loads((R/'logs'/name/'results.json').read_text()):
        if r['variant']=='v4':continue
        txt=(R/'logs'/name/f"{r['case']}_{r['seed']}_{r['variant']}.stderr").read_text()
        signed=re.search(r'ZMSIGNED .*before=([-0-9.]+) after=([-0-9.]+) seconds=([-0-9.]+)',txt)
        pool=re.search(r'ZM full=0 complete=(\d+).*objective=([-0-9.]+) seconds=([-0-9.]+)',txt)
        item=dict(series=name,case=r['case'],seed=r['seed'],variant=r['variant'],final=r['official'],exact_complete='ZM full=1 complete=1'in txt)
        if signed:item.update(pre_tail=float(signed[1]),signed_after=float(signed[2]),signed_gain=float(signed[2])-float(signed[1]),signed_seconds=float(signed[3]))
        if pool:item.update(master_complete=bool(int(pool[1])),master_after=float(pool[2]),master_seconds=float(pool[3]))
        if signed and pool:item['master_gain']=float(pool[2])-float(signed[2]);item['old_boundary_gain']=r['official']-float(pool[2])
        elif signed:item['old_boundary_gain']=r['official']-float(signed[2])
        stages.append(item)
(R/'STAGE_AUDIT.json').write_text(report_json(stages,indent=2))

ind=summaries['independent280']['variants']['candidate'];dev=summaries['development280']['variants'][selected]
def subset_metric(variant,cases):
    ps=[p for p in variant['pairs']if p['case']in cases];groups={c:[p for p in ps if p['case']==c]for c in cases}
    means=[statistics.mean(p['percent']for p in g if p['percent']is not None)for g in groups.values()if any(p['percent']is not None for p in g)]
    pct=[p['percent']for p in ps if p['percent']is not None]
    rng=random.Random(717);boot=sorted(statistics.mean(rng.choices(means,k=len(means)))for _ in range(5000))if means else []
    return dict(inputs=len(groups),pairs=len(ps),mean_case_percent=statistics.mean(means)if means else None,median_pair_percent=statistics.median(pct)if pct else None,worst_percent=min(pct,default=None),bootstrap_cases_95=[boot[125],boot[4875]]if boot else None,wins=sum(p['delta']>1e-7 for p in ps),ties=sum(abs(p['delta'])<=1e-7 for p in ps),losses=sum(p['delta']<-1e-7 for p in ps))
small=[c for c in ind['per_case']if c.startswith('small_')];normal=[c for c in ind['per_case']if not c.startswith('small_')]
metrics=dict(selected=selected,development=dev,independent=ind,independent_small=subset_metric(ind,small),independent_normal=subset_metric(ind,normal))
medians=[p['median_delta']for p in ind['per_case'].values()if abs(p['median_delta'])>1e-7]
criteria=dict(mean_positive=ind['successful_pairs']['mean_case_percent']>0,worst_at_least_minus1=ind['all_valid_pairs']['worst_percent']is not None and ind['all_valid_pairs']['worst_percent']>=-1,half_nontied_input_medians_improve=not medians or sum(x>0 for x in medians)*2>=len(medians),all_candidate_runs_successful=all(r['success']for r in longrows if r['series']=='independent280'and r['variant']=='candidate'))
criteria['bootstrap_lower_nonnegative']=ind['bootstrap_cases_95']is not None and ind['bootstrap_cases_95'][0]>=0
criteria['non_small_mean_positive']=metrics['independent_normal']['mean_case_percent']is not None and metrics['independent_normal']['mean_case_percent']>0
dm=[p['median_delta']for p in dev['per_case'].values()if abs(p['median_delta'])>1e-7]
criteria['development_acceptance']=dev['successful_pairs']['mean_case_percent']>0 and dev['all_valid_pairs']['worst_percent']>=-1 and (not dm or sum(x>0 for x in dm)*2>=len(dm))
repeat=summaries['resource_repeat280']['variants']['candidate']
repeat_rows=json.loads((R/'logs/resource_repeat280/results.json').read_text())
diagnostic=dict(candidate_success=all(r['success']for r in repeat_rows if r['variant']=='candidate'),worst_at_least_minus1=repeat['all_valid_pairs']['worst_percent']is not None and repeat['all_valid_pairs']['worst_percent']>=-1)
metrics['criteria']=criteria;metrics['primary_criteria_passed']=all(criteria.values());metrics['diagnostic_gate']=diagnostic;metrics['resource_repeat']=repeat;metrics['promotion']=all(criteria.values())and all(diagnostic.values())
(R/'FINAL_METRICS.json').write_text(report_json(metrics,indent=2))

def fmt(x):return '—'if x is None else f'{x:+.4f}'
lines=['# Структурное исследование SZO: результат против exact frozen v4','',
('**Замороженный кандидат прошёл описанные критерии на новой проверке; преимущество ограничено этой выборкой.**'if metrics['promotion']else '**Устойчивое общее превосходство над exact v4 не подтверждено. Автоматическая замена конкурсной v4 не рекомендуется.**'),'',
f'Для независимой проверки development выбрал режим `{selected}`. Алгоритм после FREEZE.json не менялся. '
'Новые входы созданы после выбора режима; ранее просмотренные данные нигде не названы новым holdout. '
'До создания holdout в EVALUATION_ADDENDUM.json добавлены более строгие условия продвижения: '
'неотрицательная нижняя граница case-bootstrap95 и положительное среднее на немалых входах. '
'Для дополнительного диагностического повтора тот же порог существенной регрессии−1% зафиксирован '
'в RESOURCE_DECISION_NOTE до завершения пар, после просмотра отдельных первых запусков. '
'Все критерии и их исходы находятся в FINAL_METRICS.json.', '',
'Реализованы exact whole-zone B&B, restricted whole-zone master с count×task-load DP и signed atomic exchanges. '
'Нативная конкурсная программа автономна: instance.json→solution.json, default280с, максимум2CPU; Python/MILP только снаружи. '
'Точный контроль сохранён с SHA256 `5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25`.', '',
'## Длинные полные сравнения','',
'Проценты:100*(candidate-base)/abs(base). Среднее с равным весом входов; seed не считается отдельным входом. '
'Медиана, SD и W/T/L — по совпадающим парам. Нулевой baseline исключается только из процентов. '
'Все валидные пары включают также неуспешные по времени процессы; отдельная строка показывает только successful pairs. '
'Успех:rc0, нет emergency timeout/error, официальный VALID, wall<=TL+0.2с. Все отказы перечислены в SUMMARY/FINAL_AUDIT.', '',
'|Серия / режим|Входы×seed|Mean,%|Median,%|SD,%|Worst,%|W/T/L|',
'|---|---:|---:|---:|---:|---:|---|']
for name in ['development280','independent280','resource_repeat280']:
    sm=summaries[name]
    for v,data in sm['variants'].items():
        for kind in ['all_valid_pairs','successful_pairs']:
            x=data[kind];spec=json.loads((R/'logs'/name/'MANIFEST.json').read_text())['spec']
            lines.append(f"|{name}/{v}/{kind}|{len(spec['cases'])}×{len(spec['seeds'])}|{fmt(x['mean_case_percent'])}|{fmt(x['median_pair_percent'])}|{x['sd_pair_percent']:.4f}|{fmt(x['worst_percent'])}|{x['wins']}/{x['ties']}/{x['losses']}|")
lines += ['',f"95% case-bootstrap независимой mean: {ind['bootstrap_cases_95']}. Это описательная неопределённость по новым входам тех же генераторов, не гарантия на распределении жюри.", '',
'|Независимый вход|Mean,%|Worst,%|Baseline mean±SD|Candidate mean±SD|',
'|---|---:|---:|---:|---:|']
for c,p in ind['per_case'].items():
    a=p['base_values'];b=p['candidate_values'];sd=lambda x:statistics.stdev(x)if len(x)>1 else 0
    lines.append(f"|{c}|{fmt(p['mean_percent'])}|{fmt(p['worst_percent'])}|{statistics.mean(a):.8g}±{sd(a):.4g}|{statistics.mean(b):.8g}±{sd(b):.4g}|")
lines += ['',f"Малые входы отдельно: `{report_json(metrics['independent_small'])}`.",f"Обычные/крупные отдельно: `{report_json(metrics['independent_normal'])}`.", '',
'Диагностическая resource_repeat280 повторяет тот же просмотренный large на всех3seed при3 параллельных парах '
'вместо7. Запущена только после завершения primary; строки не заменены и не объединены с primary. '
'Причина: baseline large/9401 вернул VALID за281.318с при65.68CPUс. Это перелёт рабочего280-бюджета, '
'но не нарушение конкурсного потолка300с. Повтор не является новым holdout; bootstrap по одному входу '
'не интерпретируется как оценка обобщения. Все времена/ресурсы и оба набора ответов сохранены.', '',
'## Что доказано и что не удалось','',
'38 независимых exhaustive assignment проверок, 15 ручных validator checks, 55 contract cases на финальном бинарнике. '
'Минимальный4-site пример: legacy DP111→repair10, сохранённый incumbent21, joint master110=exhaustive optimum. '
'Минимальный5-site signed exchange200→299, но полный v4 тоже находит299: это доказательство механизма. '
'Два пересекающихся треугольника без входных точек на пересечении дают40 и официально VALID. '
'На multiskill counterexample relaxed counts20 против true optimum10.', '',
'На development TL8 small_grid:228.042679466→254.089814790 (+11.422%), small_load:6959.450586377→7364.395513715 (+5.819%). '
'HiGHS отдельно подтвердил оба оптимума assignment MILP, SCIP подтвердил small_grid. '
'Однако на первом длинном small_grid v4 тоже достигла254.089814790; краткий выигрыш не выдан за280-секундный. '
'Полные длинные цифры находятся выше и в сырых JSON.', '',
'Restricted master при complete=1 доказывает отсутствие улучшения в построенном пуле относительно сохранённого incumbent. '
'Если incumbent не представлен в пуле, это оптимум объединения пула и готового incumbent, не численное значение оптимума одного пула. '
'Глобального доказательства для restricted режима нет. Он не улучшил три известных зрелых small checkpoints, '
'хотя exact master нашёл лучшие ответы на всех трёх. Причина: недостаток столбцов/совместного изменения территорий, '
'а не доказательство бесполезности set packing. DP только внутри прежних оболочек не может включить выгодную внешнюю точку. '
'Signed exchange исправляет этот частный барьер, сохраняя число сайтов, но не умеет открывать новый офис. '
'Exact global zone enumeration меняет маску офисов, но экспоненциальна и ограниченаN<=16/M<=6/workers<=32.', '',
'В development instance3/9303 full145429.106 против baseline136596.633 получены **до** новых финальных операторов; '
'signed gain=0 и master gain=0. Этот удачный полный запуск не является доказательством эффективности master. '
'Все локальные вклады signed/master и последующей прежней boundary-стадии разложены отдельно в STAGE_AUDIT.json. '
'Tail тоже ограничивает последний чанк LNS, поэтому это перераспределение оставшегося бюджета, а не гарантированно бесплатная стадия.', '',
'Короткая абляция на padded inputs не выделила signed-effect: на части запусков основной поиск не дошёл до хвоста. '
'Первый ручной negative_swap также успешно решает v4. Оба отрицательных результата сохранены. '
'Изменение фаз поиска в v3 давало крупные регрессии; финальный код сохраняет раннее расписание и тестирует opportunity cost новых стадий целиком.', '',
'## Надёжность, данные и воспроизведение','',
'|Серия|Запусков|VALID|Успешно|Wall>TL+0.2|Emergency timeout|',
'|---|---:|---:|---:|---:|---:|']
for name,a in audits.items():
    if name in ['cpu_intervals','cpu_efficiency']:continue
    lines.append(f"|{name}|{a['rows']}|{a['valid']}|{a['success']}|{a['over_wall']}|{a['timeouts']}|")
lines += ['',
'CPU pairs/полная топология, команды, SEED/NT, source/binary/input hashes и SHA валидатора сохранены в MANIFEST/BUILD/FREEZE. '
'Каждая пара вариантов идёт последовательно на тех же двух физических ядрах, порядок рандомизирован. '
'В длинных сериях runner/validator работают на CPU14,15, вне CPU решателей; пересечений интервалов на одном solver CPU не найдено. '
'У некоторых почти280-секундных процессов накоплено меньше одного CPU-second на wall-second; причина не установлена, '
'список сохранён в FINAL_AUDIT.cpu_efficiency. Одинаковое закрепление за ядрами не выдано за одинаковое фактическое CPU time. '
'Такие строки не исключены из результатов. '
'Полные ответы, официальные результаты, reward/distance/cost/penalty, assignments/workers/hulls, '
'RSS/user/sys/wall/rc и снимки70/140/238с лежат в logs. Ранний exact-return может использовать один CPU из выделенных двух. '
'Ограниченное wall-time многопоточного поиска не означает побитовой повторяемости решений.', '',
'Baseline собран заново g++-O3-std=c++17; тот же компилятор/флаги у кандидата. '
'Архивный main.cpp серверного ZIP побайтно совпал с frozen5b3914…; '
'проверенные runtime sections старого и пересобранного ELF также совпали (SERVER_BASELINE_PROVENANCE/BINARY_PROVENANCE). '
'Локальный compiler указан в PROVENANCE_INITIAL, версия контейнера жюри из PDF не выдана за локальную. '
'Нет новых внешних библиотек в посылке. При отрицательных cost/alpha и nsk>63 новый master выключается; '
'унаследованные ограничения v4 в таких нештатных режимах не исправлены.', '',
'Ни чужие solver/*, ни прежние результаты не менялись. Единственное перемещение — неудачная QA-серия до окончания компиляции '
'в to_delet/structural_v9, с полным MOVES.json (старый/новый путь, SHA, причина). '
'Остальные промежуточные исходники/бинарники/неудачные серии сохранены.', '',
'Воспроизведение из корня проекта (для повторного запуска задайте новое имя каталога через replay.py):','',
'```sh',
'g++ -O3 -std=c++17 experiments/v4_local_search/baseline/frozen_v4.cpp -o /tmp/szo_v4',
'g++ -O3 -std=c++17 experiments/structural_v9/artifacts/final_research/main.cpp -o /tmp/szo_candidate',
'.venv/bin/python experiments/structural_v9/src/replay.py experiments/structural_v9/INDEPENDENT280.json repeat_independent280',
'```','',
'Упакованный выбранный кандидат:package/main.cpp + Makefile, ZIP candidate_selected.zip. '
'Makefile явно задаёт выбранный режим; build/run не используют исследовательские файлы. '
'Использовать как конкурсную замену следует только с учётом вывода в начале отчёта. '
'Подробная проверка постановки и ограничений:AUDIT_RU.md. Сырые итоговые метрики:FINAL_METRICS.json.']
(R/'REPORT_RU.md').write_text('\n'.join(lines)+'\n')
# Package the exact measured source, configured with the exact selected env.
pkg=R/'package';pkg.mkdir(exist_ok=False);(pkg/'main.cpp').write_bytes((R/'artifacts/final_research/main.cpp').read_bytes())
env={'NT':'2',**selection['config'].get('env',{})};prefix=' '.join(f'{k}={v}'for k,v in env.items())
(pkg/'Makefile').write_text('build:\n\tg++ -O3 -std=c++17 -o solution main.cpp\n\nrun:\n\t'+(prefix+' 'if prefix else '')+'./solution\n')
with zipfile.ZipFile(R/'candidate_selected.zip','w',zipfile.ZIP_DEFLATED)as z:
    for p in pkg.iterdir():z.write(p,p.name)
(R/'PACKAGE.json').write_text(report_json(dict(config=selection['config'],runtime_env=env,files={str(p.relative_to(ROOT)):sha(p)for p in [pkg/'main.cpp',pkg/'Makefile',R/'candidate_selected.zip']},promotion=metrics['promotion']),indent=2))
control=R/'control_v4_nt2';control.mkdir(exist_ok=False)
(control/'main.cpp').write_bytes((ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp').read_bytes())
(control/'Makefile').write_text('build:\n\tg++ -O3 -std=c++17 -o solution main.cpp\n\nrun:\n\tNT=2 ./solution\n')
with zipfile.ZipFile(R/'control_v4_nt2.zip','w',zipfile.ZIP_DEFLATED)as z:
    for p in control.iterdir():z.write(p,p.name)
(R/'CONTROL_PACKAGE.json').write_text(report_json(dict(unchanged_source_sha256=sha(control/'main.cpp'),env={'NT':'2'},files={str(p.relative_to(ROOT)):sha(p)for p in [control/'main.cpp',control/'Makefile',R/'control_v4_nt2.zip']}),indent=2))
with (R/'REPORT_RU.md').open('a')as f:f.write('\nКонтроль для воспроизведения:control_v4_nt2.zip. Внутри неизменный frozen source5b3914… и Makefile с явным NT=2; defaultTL280.\n')
print(report_json(dict(selected=selected,promotion=metrics['promotion'],criteria=criteria,independent=ind['all_valid_pairs'],small=metrics['independent_small'],normal=metrics['independent_normal'])))
