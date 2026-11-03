"""Final auditable summary; consumes frozen measurements without changing selection."""
import hashlib,json,statistics,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def read(p):return json.loads((R/p).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,a):(R/p).write_text(json.dumps(a,indent=2))
def link(p,label=None):
 q=R/p;return '['+(label or p)+']('+str(q)+')'
def pct(x):return '—'if x is None else f'{x:+.4f}%'
selection=read('SELECTION.json');variant=selection['variant'];revision=selection['revision'];architecture=selection['architecture']
assert read('CONFIRMATION_STATUS.json')['stage']=='independent280_complete'
resource_status=read('RESOURCE_DIAGNOSTIC_STATUS.json');assert resource_status['stage']in ['not_required','resource_diagnostic280_complete']
primary=read('logs/independent280/ANALYSIS.json');v4=primary['comparisons'][variant+'_vs_v4'];v9=primary['comparisons'][variant+'_vs_v9']
resource=read('RESOURCE_DIAGNOSTIC_DECISION.json');gate=resource['primary_gate'];diag=read('RESOURCE_DIAGNOSTIC_RESULT.json')if resource['trigger']else None
promote=gate and (diag is None or diag['passed'])
cohorts=['screen30_v2','screen30_v4','screen30_v5','development280_v5_both','acceleration280','independent280']
if resource['trigger']:cohorts.append('resource_diagnostic280')
audits=[];allrows=[]
for name in cohorts:
 d=R/'logs'/name;m=json.loads((d/'MANIFEST.json').read_text());rows=json.loads((d/'results.json').read_text());s=m['spec']
 expected=len(s['cases'])*len(s['seeds'])*len(s['variants']);assert len(rows)==expected
 for x in rows:
  out=Path(x['command'][-2]);assert out.exists()and sha(out)==x['solution_sha256'],out
  assert x['affinity']in s['cpus']
 for label,config in s['variants'].items():assert sha(ROOT/config['binary'])==m['binaries'][label]
 for case,p in s['cases'].items():assert sha(ROOT/p)==m['inputs'][case]
 audits.append(dict(series=name,expected=expected,runs=len(rows),valid=sum(x['valid']for x in rows),working_success=sum(x['success']for x in rows),emergency_timeouts=sum(x['timeout']for x in rows),solver_errors=sum(x['error']for x in rows),max_wall=max(x['wall']for x in rows),failures=[{k:x[k]for k in ['case','seed','variant','valid','rc','timeout','wall','error']}for x in rows if not x['success']]))
 allrows+=rows
for p,h in read('FREEZE.json')['files'].items():assert sha(ROOT/p)==h,p
baseline=ROOT/'experiments/v4_local_search/baseline/frozen_v4.cpp';assert sha(baseline)=='5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25'
assert sha(R/'src/resource_diagnostic_campaign.py')==read('PROTOCOL.json')['resource_veto']['script_sha256']
fresh=read('FRESH_INPUTS.json');old_inputs=set()
for name in cohorts[:-1]:
 if name=='independent280':continue
 p=R/'logs'/name/'MANIFEST.json'
 if p.exists():old_inputs.update(json.loads(p.read_text())['inputs'].values())
assert len(fresh)==8 and all(x['sha256']not in old_inputs for x in fresh.values())
qa=[]
for p in (R/'logs').glob('qa_v*/results.json'):
 rows=json.loads(p.read_text());errors=[]
 for f in p.parent.glob('*.stderr'):
  if any(w in f.read_text()for w in ['error:','VERIFY','INVALID']):errors.append(str(f))
 qa.append(dict(revision=p.parent.name,cases=len(rows),valid=sum(x['valid']for x in rows),rc0=sum(x['rc']==0 for x in rows),stderr_errors=errors));assert not errors
recommendation=dict(promote=promote,primary_gate=gate,resource_diagnostic=diag,recommended='v10_'+revision+'_'+architecture if promote else 'exact_server_v4_NT2_TL280',candidate='v10_'+revision+'_'+architecture,configuration=read('INDEPENDENT280.json')['variants'][variant],primary_vs_v4=v4['all_valid'],primary_vs_v9=v9['all_valid'],selection=selection,reason='All predeclared primary and triggered resource gates pass'if promote else 'Primary or predeclared resource-risk gate fails; selected candidate remains experimental')
save('FINAL_RECOMMENDATION.json',recommendation)
save('FINAL_METRICS.json',dict(primary=primary,development=read('logs/development280_v5_both/ANALYSIS.json'),post_development=read('logs/acceleration280/ANALYSIS.json'),selection=read('ACCELERATION_DECISION.json'),resource=diag,quality_cohorts=audits))
endpoint={}
for name in ['OFFICE_TRANSPLANT_DIAGNOSTIC.json','OFFICE_PAIR_DIAGNOSTIC.json','logs/office_assignment_diagnostic/result.json']:
 if (R/name).exists():endpoint[name]=read(name)
save('FINAL_AUDIT.json',dict(frozen_files_unchanged=True,exact_v4_sha256=sha(baseline),fresh_inputs=8,fresh_no_overlap=True,quality_runs=len(allrows),quality_valid=sum(x['valid']for x in allrows),quality_working_success=sum(x['success']for x in allrows),quality_emergency_timeouts=sum(x['timeout']for x in allrows),cohorts=audits,qa=qa,qa_total=sum(x['cases']for x in qa),qa_valid=sum(x['valid']for x in qa),viewed_endpoint_diagnostics=endpoint,notes=['Superseded orchestrations did not create extra quality rows.','No selected algorithm changes after freeze or independent generation.','Resource diagnostic reuses viewed input and never replaces primary rows.','Endpoint proposal diagnostics include rejected invalid proposals, separately from completed-solver quality rows.','Same CPU allocation is not a claim of equal consumed CPU time or exclusive hardware.']))
metrics=v4['all_valid'];lines=['# Warm start v10 — итог','',('Рекомендация: использовать выбранную v10.'if promote else 'Надёжная общая замена v4 не подтверждена; для конкурсного запуска сохранить точную v4 NT2/TL280.'),'',f"Кандидат: **{revision}, {architecture}**. Независимая проверка: 8 новых входов, 3 seed (включая штатный 0), 280 секунд, 2 CPU, три версии, без DBG. Входы сгенерированы после фиксации исходника/конфигурации; все они имеют 120–10000 сайтов, без вклада tiny-exact ветки.",'', '| Контроль | Среднее по входам | Медиана пар | SD пар | Худшая пара | Победы/ничьи/поражения | Case-bootstrap 95% |','|---|---:|---:|---:|---:|---:|---|']
for label,comp in [('точная v4',v4),('прежний v9 tail',v9)]:
 m=comp['all_valid'];lines.append(f"| {label} | {pct(m['mean_case_percent'])} | {pct(m['median'])} | {m['sd']:.4f} п.п. | {pct(m['worst'])} | {m['wins']}/{m['ties']}/{m['losses']} | [{pct(m['case_bootstrap95'][0])}; {pct(m['case_bootstrap95'][1])}] |")
lines+=['',f"Официально валидны {primary['valid']}/{primary['runs']} ответов; рабочих успехов {primary['success']}/{primary['runs']}. Подробности каждого перелёта/ошибки: "+link('logs/independent280/ANALYSIS.json')+'. Средние равновзвешены по входам; seed не считаются независимыми задачами. Bootstrap: 5000 повторов по входам, фиксированный RNG717. Отдельно сохранена статистика только успешных пар; первичные выводы не скрывают остальные строки.','', '## Новые входы','', '| Вход | Сайты/офисы/рабочие | Среднее к v4 | Среднее к v9 | Худшее к v4 |','|---|---:|---:|---:|---:|']
for c,f in fresh.items():
 p=f['parameters'];a=v4['per_case'][c];b=v9['per_case'][c]
 lines.append(f"| {c} | {p['ns']}/{p['no']}/{p['nw']} | {pct(a['mean_case_percent'])} | {pct(b['mean_case_percent'])} | {pct(a['worst'])} |")
lines+=['','## Что изменено','','1. Гены теперь включают параметры геометрии и полные допустимые назначения; их fitness — настоящая цель после проверки работников и всех входных точек.','2. Перед дорогой популяцией сохранён дешёвый поиск разнообразных наборов офисов без декодирования. Далее два потока создают настоящие пространственные варианты.','3. Наследуются генераторы/веса, используются центры реальных зон, разные геометрические и дорожные конструкторы, короткий локальный поиск. Разные решения с одинаковым баллом сохраняются.','4. В режиме memetic скрещиваются целые зоны по пространственному срезу; конфликтующая зона откатывается целиком. Отбор учитывает различие назначений. В основной поиск передаётся готовое решение.']
if revision in ['v6','v8']:lines.append('5. Для одного офиса геометрический поиск пропускается: разбиение от параметров не зависит. На всех 24 офисах большого входа оценки совпали точно, а подзадача заняла 0.14035 с вместо 9.70895 с. Это не ускорение всего решателя в 69 раз.')
if revision=='v8':lines.append('6. Конструктор power cells явно выравнивает полезную массу сайтов/задач с учётом maxSize, maxDifference и дефицитных навыков; веса сдвигаются при сохранении принадлежности офисов своим областям. Вспомогательная mass-loss не заменяет настоящую целевую функцию.')
if architecture=='geometry':lines+=['','Выбран GW_MODE1: разнообразие сохраняется в геометрической популяции и готовых стартах. Включение пространственного crossover и новой глобальной элиты (GW_MODE2) проверено в development, но не выбрано. Нативная глобальная элита выбранной конфигурации остаётся прежней.']
lines+=['','Сохранены все прототипы. Минимальные проверки: равные по баллу разные зоны 20/20 сохраняются и дают совместимого ребёнка40; балансировка геометрии исправляет старт3/1 →2/2 и20→40. Это проверки механизмов, а не доказательство, что полный v4 не решает эти маленькие входы. Ссылки: '+link('BALANCED_MECHANISM.json')+', '+link('logs/mechanism.json')+'.','','## Выбор и отрицательные результаты','','Первоначальная замена office-subset GA дорогими phenotype-стартами привела к провалам до −60.99% на 10k: перед ней не успевал возникнуть широкий набор офисов. Затем выяснилось, что предварительный legacy GA всё ещё тратил время на первые декодирования. Все эти результаты оставлены в screen30_v2/v4/v5. Исправленный предварительный этап строго proxy-only.','', 'Полное development: 6 просмотренных входов ×2seed ×4версии ×TL280. Затем отдельное сопоставление v5/v6/v8 с обоими неизменными контролями: 3 входа ×2seed ×5версий ×TL280. Выбор сделан до генерации независимых данных по '+link('ACCELERATION_SELECTION_RULE.json')+'; исходные данные: '+link('ACCELERATION_DECISION.json')+'. Режимы geometry/memetic различаются одновременно crossover и глобальной элитой; это не отдельная причинная оценка каждого оператора.','', '| Серия | Запуски | VALID | Рабочий успех | Аварийный TL+2 |','|---|---:|---:|---:|---:|']
for a in audits:lines.append(f"| {a['series']} | {a['runs']} | {a['valid']} | {a['working_success']} | {a['emergency_timeouts']} |")
lines+=['','Рабочая метка требует wall≤TL+0.2. Её нарушение не равнозначно конкурсному TLE300; фактические времена и сигналы сохранены. Без удаления/замены неудачных строк. Отменённые до запуска старые оркестрации и промежуточная v7 не входят в число quality-прогонов.','', '## Ресурсы и надёжность','']
if diag:lines.append(f"Предписанный заранее повтор ресурсоёмкого входа **{diag['case']}**, те же три seed и версии, меньший параллелизм: worst к v4 {pct(diag['metrics_vs_v4']['worst'])}; риск-критерий {'пройден'if diag['passed']else 'НЕ пройден'}. Первичная серия не заменена и не объединена с повтором.")
else:lines.append('Ресурсный повтор не потребовался: '+resource_status['reason']+'.')
lines+=['','Фактические user/sys/RSS, wall, CPU pressure, назначения, работники, оболочки и промежуточные решения сохранены. В post-development/независимой серии runner дополнительно наблюдает runtime/runqueue/state потоков и I/O через /proc. Исследовательские процессы исполняются на ядрах контроллера; конкурсный C++ читает только свой instance и пишет solution. Исключительность всей машины и равенство реально полученного CPU-времени не заявляются. Подробности: '+link('RESOURCE_REPORT_RU.md')+'.','', 'Геометрический phenotype остаётся эвристическим. Fast proxy и планы по отдельным навыкам могут ошибаться; окончательный fitness проверяется по реальным работникам и истинной цели. Мягкие внутренние дедлайны могут удлинять фазу старта; это время включено в общий бюджет. Два потока и wall-дедлайны не дают побитового воспроизведения траектории по одному seed. За пределами проверенных классов оптимальность и отсутствие любых регрессий не доказаны.','', '## Код и воспроизведение','', 'Выбранный пакет: '+link('candidate_selected.zip')+'. Исходник: '+link(selection['package_source']+'/main.cpp')+'; настройки: '+link(selection['package_source']+'/Makefile')+'. `make build`, затем `make run` задают проверенную конфигурацию NT2/ZM_POOL0/ZM_RESERVE0/GW_MODE'+str(selection['mode'])+'; обычный бюджет280. Пакет содержит только main.cpp и Makefile, не требует Python/MIP или внешних ответов.','', 'Фиксация до новых данных: '+link('FREEZE.json')+'. Полная рекомендация: '+link('FINAL_RECOMMENDATION.json')+'. Аудит: '+link('FINAL_AUDIT.json')+'. Разбор худших/лучших пар: '+link('PAIR_ANALYSIS_RU.md')+'. Ограничения и история методов: '+link('AUDIT_RU.md')+'.','', 'Контрольная v4 не менялась: SHA256 `5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25`. Прежний v9 tail сохранён отдельно. Пользовательские solver/, README, SOLVER и прежние результаты не переписывались; без staging/commit/push/submit.']
(R/'REPORT_RU.md').write_text('\n'.join(lines)+'\n')
save('COMPLETION.json',dict(status='complete',promote=promote,candidate=revision+'_'+architecture,quality_runs=len(allrows),quality_valid=sum(x['valid']for x in allrows),fresh_inputs=8,primary_runs=72,updated_unix=time.time()))
print(json.dumps(dict(promote=promote,revision=revision,architecture=architecture,vs_v4=v4['all_valid'],vs_v9=v9['all_valid'],quality_runs=len(allrows))))
