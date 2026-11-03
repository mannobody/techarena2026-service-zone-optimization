import hashlib,json,re,statistics,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
load=lambda p:json.loads(p.read_text())
p=load(R/'logs/independent10/EVALUATION.json');l=load(R/'logs/long60_diagnostic/EVALUATION.json')
pkg=load(R/'PACKAGE.json');f=load(R/'FREEZE.json');counter=load(R/'logs/worker_full/COUNTEREXAMPLE_EVALUATION.json')
accepted=p['accepted_this_budget'] and l['accepted_this_budget']
decision=dict(accepted=accepted,recommended_as_v4_replacement=accepted,
    primary=p['criteria'],long_diagnostic=l['criteria'],
    primary_failure_cannot_be_replaced_by_long=True,TL280_runs=0,
    independent_inputs=8,long_inputs_are_subset_of_primary=4,
    candidate_source_sha256=pkg['source_sha256'],candidate_binary_sha256=pkg['binary_sha256'],
    zip_sha256=pkg['zip_sha256'],frozen_code_unchanged=True,
    note='General full-solver superiority requires both budgets; a constructed worker-counterexample is separately reproducible, not a general quality claim.')
(R/'FINAL_DECISION.json').write_text(json.dumps(decision,indent=2))
def line(budget,name,x):
    return f"|{budget}|{name}|{x['input_weighted_mean']:+.6f}|{x['median']:+.6f}|{x['worst']:+.6f}|{'/'.join(map(str,x['WTL']))}|[{x['bootstrap95'][0]:+.6f}; {x['bootstrap95'][1]:+.6f}]|"
table=['|TL|Сравнение|mean,%|median,%|worst,%|W/T/L|95% bootstrap по входам|','|---:|---|---:|---:|---:|---|---|']
for budget,e in [(10,p),(60,l)]:
    for name in ['candidate_vs_v4','candidate_vs_v8','candidate_vs_off','off_vs_v4']:table.append(line(budget,name,e['summary'][name]))
by=['|Вход|TL10 mean к v4,%|TL10 worst,%|TL60 mean к v4,%|TL60 worst,%|','|---|---:|---:|---:|---:|']
for k,v in p['summary']['candidate_vs_v4']['by_input'].items():
    q=l['summary']['candidate_vs_v4']['by_input'].get(k)
    longval=f"{q['mean']:+.6f}|{q['worst']:+.6f}" if q else 'не запускался|не запускался'
    by.append(f"|{k}|{v['mean']:+.6f}|{v['worst']:+.6f}|{longval}|")
ab=['|TL10 абляция|mean к all-off,%|median,%|worst,%|W/T/L|','|---|---:|---:|---:|---|']
for name in ['fill_only_vs_off','worker_only_vs_off','candidate_vs_off']:
    x=p['summary'][name];ab.append(f"|{name}|{x['input_weighted_mean']:+.6f}|{x['median']:+.6f}|{x['worst']:+.6f}|{'/'.join(map(str,x['WTL']))}|")
dev=load(R/'logs/full_dev4/results.json');model=load(R/'reports/MIP_SUMMARY.json')
traces=[]
for budget,d in [(10,R/'logs/independent10'),(60,R/'logs/long60_diagnostic')]:
    rows=load(d/'TRAJECTORIES.json')
    for row in rows[:2]:
        b,c=row['baseline'],row['candidate'];delta=row['component_delta']
        text=f"* TL{budget} {row['case']}/{row['seed']} против {row['baseline_variant']}: {row['delta_pct']:+.6f}%; offices {b['offices']} → {c['offices']}; sites {b['site_count']}→{c['site_count']}; изменено {row['changed_assignments']} назначений/{row['changed_workers']} workers/{row['common_hulls_changed']} общих hulls."
        text+=f" Reward {delta['reward']:+.6f}, distance {delta['distance']:+.6f}, cost {delta['cost']:+.6f}, penalty {delta['penalty']:+.6f}; итог Δ={delta['objective']:+.6f}."
        text+=' Снимки '+', '.join(f"{s['target']}с: {s['baseline_objective']:.4f}/{s['candidate_objective']:.4f}" for s in row['trace'])+'.'
        traces.append(text)
status='Критерии пройдены на проверенных лимитах.' if accepted else '**Устойчивое превосходство полного решателя над exact v4 не подтверждено. Замена v4 не рекомендуется.**'
text=f'''# v8 exact neighborhoods: результаты, 20 октября 2026

{status}

Есть воспроизводимое исправление настоящего ограничения: на constructed worker
counterexample полный v4/v8/all-off =36, новый runtime =45 (**+25% на всех 3 seed**).
Это один вход и доказанный класс node-cap барьеров, не три независимые задачи
и не доказательство общего преимущества. Глобальная верхняя оценка45 достигнута.

## Полный поиск, замороженный кандидат

{chr(10).join(table)}

TL10: 8 новых входов ×2seed ×6вариантов =96 процессов; valid/успешны
{p['complete']['success']}/96, max wall={p['max_wall']:.6f}с.
TL60: 4 из тех же входов ×2seed ×4варианта =32 процесса; valid/успешны
{l['complete']['success']}/32, max wall={l['max_wall']:.6f}с.
**Ни одного нового TL280.** Старые просмотренные holdout использованы только как
известные development/checkpoint данные, их старые серии не переобъявлены полными.

Проценты:100*(candidate-base)/abs(base). Mean имеет равный вес входов, seed не
считается независимой задачей. Медиана/worst/W-T-L по парам; bootstrap ресэмплирует
входы, а не seeds. Нулевые baseline не превращаются в проценты. Бюджеты не объединены.

{chr(10).join(by)}

{chr(10).join(ab)}

Исходные критерии в FREEZE.json. TL10 failed:
{', '.join(k for k,v in p['criteria'].items() if not v) or 'нет'}.
TL60 failed: {', '.join(k for k,v in l['criteria'].items() if not v) or 'нет'}.
По замечанию пользователя о недостаточности10с до длинных запусков зарегистрировано
LONG_PROTOCOL_ADDENDUM.json: один неизменный кандидат, фиксированные4 класса/2seed,
32 процесса из прежнего cap. Даже удачный TL60 не отменяет первичный провал TL10.
Четыре длинных входа не добавляют четыре новых независимых задачи.

## Что реально исправлено

* Нет общего запрета пересечений полигонов: PDF/validator допускают их без общих
  входных точек. Default v8 уже это поддерживает в geo_ok/verify. Отвергнута
  гипотеза об ошибке финальной геометрии; ограничены семейства стартов/resplit.
* Полный домен новой MILP: fourth_office 36→43, legacy top3+old+nearest оставляет36.
* Жадный fill пробует следующий офис после отказа геометрии:18→27.
* Отрицательный raw profit разрешён, если уменьшается настоящий global penalty:
 208→293; counts1/2, loads10/10. Safe filter pr+alpha*ntask≤0 исключает только
 заведомо невыгодную одиночную вставку.
* A=0: одновременное открытие +6переносов +workers даёт63→114, native_open63.
* Worker count по навыку не заменяет совместимость: отдельный пример relaxed27
 против true optimum18 подтверждён exhaustive worker allocation, SCIP, HiGHS.
* Настоящий default worker false negative:309 посещённых nodes при cap300,
 known certificate45. Frozen XN_WORKER принимает его за0.000517с/478nodes;
 old отказывает за0.000384с. Это не доказательство полной разрешимости за2мс:
 timeout остаётся unknown/консервативным отказом, native LNS может кешировать bool.
* Исправление canonical open-bit sig реализовано за XN_SIG_FIX, state-test
 проверяет2000 изменений. Оно не включено в default и не объявлено причиной выигрыша.

Правило→код→свидетельство→проверка→исправление: reports/AUDIT_RU.md.
Все контрпримеры, включая намеренно INVALID, сохранены; INVALID не считается
валидным solver output. Во всех128 timed-процессах новой замороженной серии ответ проверен
официальным task/validate_solution.py.

## Точные окрестности и ограничения

G: boundary/support нескольких зон, фиксированные site assignments снаружи и
набор открытых офисов, совместные workers. S: переменная маска офисов, сайты,
workers, включая открытие/закрытие. Обе учитывают reward-distance-cost, capacity,
counts/maxDifference, task-load и global balance с внешней частью. Worker profiles
целые; это не агрегатная сумма навыков. Геометрия: solve → все input points →
минимизированные supporting-set cuts → repeat. LP и матрицы сохранены.

133/133 начальных сравнения с независимым полным перебором прошли:92 MILP и41
standalone runtime. Дополнительно11000 независимых rational/Caratheodory проверок
покрытия; нет расхождений. Новый native B&B не требует SCIP/HiGHS в посылке.

Локальные backend: SCIP10.0.2/PySCIPOpt6.3.0, HiGHS1.15.1. В официальном PDF
перечислены SCIP10.1 и HiGHS1.15: зависимости разрешены, но точное совпадение
локального SCIP с серверной версией не заявляется. Runtime ZIP внешних solver
библиотек не использует. Не выдаём Python-oracle за конкурсное ускорение.

Повтор зрелых MILP-моделей на одинаковой affinity14,15 без компиляций на ней:
28 моделей,0 улучшений,22 conditional optimal; прочие6 не доказали оптимальность
после геометрических cuts. Status optimal последней relaxation сам по себе не
означает conditional optimal. Python initial/final official validation доминирует
на10k; max total8.1724с при requested8с учтён как overhead/незавершённая подзадача.
Все build/solve/check/restore/bound/gap/nodes/status лежат в JSON.

На worker counterexample G доказывает36, S доказывает45 обоими backend (≈0.05–0.11с).
Результат переносится в полный native runtime: worker_only и tiny_only тоже45,
v4/v8/off36 на трёх seeds. В raw runner6 ранних exact-return отмечены false из-за
отсутствия строки threads=2; отдельный COUNTEREXAMPLE_EVALUATION сохраняет raw
флаги и подтверждает rc0, VALID, wall и выход с1потоком до создания native threads.

## Барьеры, плато и отрицательные результаты

70 сравнений от одинаковых известных checkpoint,2с: G против boundary mean
−0.006599%,0/8/6; S −0.013143%,0/8/6. Новые хвосты не включены в default.
При q12 все7 зрелых конфигураций запрещают закрытие, потому что min_count>12.
Для tightA/alphabig/large/huge даже открытие невозможно: новому офису нужно
минимум34/46/203/266сайтов. Это математический барьер пространства переменных,
а не «слабость SCIP». См. reports/COUNT_BARRIERS.json.

Whole-zone packets снимают этот q-барьер, перечисляя согласованные road/cell
шаблоны целых зон и маски офисов. Это **не** полная точная окрестность, хотя
транзакция проверяется точно; пример63→114 не доказывает полезность полного поиска.
Нативный B&B допускает временно плохие частичные состояния, но сохраняет лучший
валидный incumbent. Все удаления предшествуют добавлениям; окончательный worker
certificate и verify обязательны. Сам B&B ограничен временем и может потратить
его на текущую маску прежде альтернатив; complete=false не выдаётся за proof.

Native elite сохраняет6 решений, отсеивает одинаковый objective даже при разных
масках и try_elite применяет96% quality threshold. Это ограничивает разнообразие,
но не доказанный глобальный запрет: cands по размерам, starts и native ruin могут
попасть в другие маски. Новую нишевую политику здесь не продвигали: прежние
отрицательные эксперименты в v4_deep_parallel уже известны. Аналогично не
повторяли late-acceptance/tabu/support-kick без устранения конкретного барьера:
их failure/recovery разбор сохранён в прежнем integration/RESEARCH_NOTES_RU.md.

## Конфигурации и момент расхождения

{chr(10).join(traces)}

Снимки дают только первое наблюдение расхождения. Нет утверждения, что весь
timed-эффект вызван одним оператором: меняются рабочие, наборы офисов, итерационные
бюджеты, публикации между потоками. Площадь считается только на общих офисах;
нулевая площадь у отрезков/смены маски не означает неизменную геометрию.

## Честный учёт времени и воспроизведение

Первичный TL4-screen:144/144 VALID, но114 wall>4с,78>4.25с, max6.4995с. Его
не используем как честное доказательство качества при жёстком4с. Он сохранён
с негативными результатами. TL10/60 используют одинаковое внешнее ограничение;
сигнал завершает child, time-parent сохраняет RSS. Новый runtime дополнительно
имеет собственный watchdog, публикующий отдельный проверенный incumbent.

TL10 external budget stops={p['external_budget_stops']}, inferred internal watchdog
stops={p['inferred_internal_watchdog_stops']}; TL60 external={l['external_budget_stops']},
inferred internal={l['inferred_internal_watchdog_stops']}. Inferred значит отсутствие
финальной строки при rc0 и времени около deadline; не выдуманный замер thread count.

NT=2; одинаковые входы/seeds/compiler/-O3 внутри пары; CPU18,19 и20,21 — две
непересекающиеся пары физических ядер. Сборка14,15. Порядок вариантов случайный.
Первый exploratory MIP-screen частично пересёкся с подготовительной компиляцией
на14,15: его времена не используются для сравнения backend; отдельный timed
repeat выполнен после окончания компиляций. Thermal/power вариативность машины
остаётся общей оговоркой; побитовая повторяемость wall-limited поиска не обещается.

Прерванный пользователем checkpoint-screen:29 завершённых +1незавершённый запуск;
исходный каталог остаётся INTERRUPTED. Resume проверил hashes, выполнил41
недостающую позицию и дал70 полных записей. Незавершённый запуск не превращён
в успех и не вошёл в paired mean. Ранние preparation failures (build race,
неверная launcher affinity, отсутствие large TL280 checkpoint) сохранены отдельно.

Команды: COMMANDS_RU.md. Freeze: FREEZE.json; параметры: artifacts/final/SELECTION.json;
зависимости oracle: OFFLINE_DEPENDENCIES.json. Полный исходник и Makefile:
artifacts/final/. Default TL280, NT2, без argv instance.json→solution.json.
Проверка контракта63/63 VALID, max wall1.020239с при override TL1; три no-argv
проверки с DBG/NT unset. Default280 подтверждён исходником, не TL280-запуском.

ZIP: artifacts/{Path(pkg['zip']).name}. Внутри ровно main.cpp +Makefile; сборка
после распаковки побайтово совпала с frozen tested binary.

* source SHA256 `{pkg['source_sha256']}`
* binary SHA256 `{pkg['binary_sha256']}`
* ZIP SHA256 `{pkg['zip_sha256']}`
* exact v4 source `5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25`
* unchanged v8 source `1857bec7e0882d15cf3091e79aeb0df1608ced5d4ee6883c1cb02656cfbd8e03`

Original v8 binary SHA совпал с PROVENANCE, а .text rebuilt v8 побайтово
совпадает с original v8: reports/V8_BINARY_AUDIT.json. Current solver/ не был
baseline и не менялся. Старые v4/v6/v7/v8 сохранены; commit/staging/push/серверных
отправок нет. Карантин не понадобился: промежуточные версии нужны для воспроизведения,
активные offline_deps сохранены и не входят в ZIP. Поддерживается неотрицательный
экономический domain cost/alpha; произвольный signed JSON не покрыт доказательством
доминирования пустого офиса. Для рекомендации на длинном серверном бюджете
TL280 доказательств нет; запуск возможен только по отдельной команде пользователя.
'''
(R/'REPORT_RU.md').write_text(text)
print('Report/decision written; accepted:',accepted)
