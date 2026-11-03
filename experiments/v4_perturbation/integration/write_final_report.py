"""Render completed independent evidence, preserving primary/extra separation."""
import csv,json,re,statistics
from pathlib import Path
I=Path(__file__).resolve().parent;R=I.parent;ROOT=R.parents[1]
def read(p):return json.loads(p.read_text())
def fmt(x,n=6):return '—' if x is None else f'{x:+.{n}f}'
def wtl(x):return '/'.join(str(x[k]) for k in ['win','tie','loss'])
freeze=read(I/'FINAL_FREEZE.json')
decision=read(I/'FINAL_DECISION.json')
audit=read(I/'EVIDENCE_AUDIT.json')
contract=read(I/'logs/final_contract10/COMPLETE.json')
contract_rows=read(I/'logs/final_contract10/results.json')
contract_slowest=max(contract_rows,key=lambda x:x['wall'])
assert all((I/f'HOLDOUT{t}_FINAL.json').exists() for t in [60,280])
contract_ok=contract['expected']==contract['completed']==contract['success']
accepted=decision['accepted'] and audit['all_record_checks_pass'] and contract_ok
decision.update(final_contract_pass=contract_ok,final_record_audit_pass=audit['all_record_checks_pass'],
                recommended_as_replacement=accepted)
(I/'FINAL_DECISION_WITH_AUDIT.json').write_text(json.dumps(decision,indent=2))
lines=['# Независимая проверка малых возмущений v4','',
       ('Кандидат выполнил зарегистрированные локальные критерии; это не гарантия скрытого серверного балла.' if accepted else
        '**Устойчивое улучшение серверной v4 не подтверждено. Кандидат не рекомендуется как замена v4. Подготовка экспериментальной v8 по дополнительному поручению пользователя не означает прохождения критериев качества.**'),'',
       'Финальный исследовательский вариант: balanced support-kick на плато и короткое native boundary-восстановление. Development-отбор и отрицательные гипотезы описаны в [RESEARCH_NOTES_RU.md](RESEARCH_NOTES_RU.md) и [BOUNDARY_FULL_DEVELOPMENT_NOTES.md](BOUNDARY_FULL_DEVELOPMENT_NOTES.md).',
       '', '## Первичные независимые результаты','',
       'Δ%=100×(candidate−base)/abs(base). SD — выборочное отклонение парных процентов; W/T/L — выигрыши/равенства/проигрыши. Несколько seed одного входа не являются независимыми задачами. Ошибочные процессы остаются в учёте.', '',
       '| TL | Сравнение | Пар | mean,% | median,% | worst,% | SD,п.п. | W/T/L | 95% bootstrap по входам |',
       '|---:|---|---:|---:|---:|---:|---:|---|---|']
primary={}; finals={}
for t in [60,280]:
    s=read(I/f'HOLDOUT{t}_SUMMARY.json');primary[t]=s;finals[t]=read(I/f'HOLDOUT{t}_FINAL.json')
    for k in ['candidate_vs_v4','off_vs_v4','candidate_vs_off']:
        c=s['comparisons'][k];x=c['distribution_valid_outputs_including_failed_processes'];ci=c['instance_bootstrap95_mean']
        lines.append(f"|{t}|{k}|{len(c['pairs'])}|{fmt(x.get('mean'))}|{fmt(x.get('median'))}|{fmt(x.get('min'))}|{fmt(x.get('sample_sd'))}|{wtl(c['wtl'])}|{fmt(ci[0])+' … '+fmt(ci[1]) if ci else '—'}|")
lines+=['','TL60:12 новых входов×3seed×3варианта=108 процессов. TL280:6 из тех же12 входов×2seed×3варианта=36 процессов. Всего12 независимых входов; TL280 не добавляет шесть новых задач.', '', '## По классам: candidate против exact v4','',
        '| TL | Класс | Пар | mean,% | median,% | worst,% | SD,п.п. |','|---:|---|---:|---:|---:|---:|---:|']
for t,s in primary.items():
    for case,x in s['comparisons']['candidate_vs_v4']['by_case'].items():
        lines.append(f"|{t}|{case}|{x['n']}|{fmt(x.get('mean'))}|{fmt(x.get('median'))}|{fmt(x.get('min'))}|{fmt(x.get('sample_sd'))}|")
lines+=['','## Дополнительные seed и объединение','',
        'Порог расширения задан до holdout:SD>0.5п.п. либо range>1п.п. для любого обязательного парного контраста. Все три варианта на выбранном входе получают два дополнительных seed. В combined mean входы имеют одинаковый вес независимо от числа повторов; первичные итоги выше не заменяются.', '',
        '| TL | Дополнительные классы | Доп. процессы успешны/всего | Доп. mean candidate−v4,% | Combined input-weighted mean,% | Combined worst,% | Combined 95% CI |',
        '|---:|---|---:|---:|---:|---:|---|']
for t,f in finals.items():
    d=read(I/f'HOLDOUT{t}_DECISION.json');p=I/f'HOLDOUT{t}_VARIANCE_SUMMARY.json'
    if f.get('status')=='primary_only_extension_interrupted_by_user':
        stop=read(I/'USER_STOP.json')
        lines.append(f"|{t}|{', '.join(d['variance_extension_reasons'])}; остановлено пользователем|{stop['successful_completed_records']}/{stop['expected']} завершённых успешных|не вычислялось|не вычислялось|не вычислялось|не вычислялось|")
        continue
    extra=read(p) if p.exists() else None;c=f['comparisons']['candidate_vs_v4'];ci=c['input_bootstrap95_mean']
    lines.append(f"|{t}|{', '.join(d['variance_extension_reasons']) or 'нет'}|{str(extra['success'])+'/'+str(extra['runs']) if extra else '0/0'}|{fmt(extra['comparisons']['candidate_vs_v4']['distribution_valid_outputs_including_failed_processes'].get('mean')) if extra else '—'}|{fmt(c['input_weighted_mean'])}|{fmt(c['pair_distribution_descriptive_only'].get('min'))}|{fmt(ci[0])+' … '+fmt(ci[1]) if ci else '—'}|")
lines+=['','## Допуск и надёжность','',
        'Зарегистрированы:mean≥+0.1% на обоих лимитах, неотрицательные медиана и медианы каждого класса, worst≥−1%, нижний bootstrap≥0, mean против all-off≥0, успешны все процессы и проверки происхождения. Combined тоже должен выполнить эти пороги. Благоприятные новые seed не отменяют провал первичной проверки.', '']
for t,f in finals.items():
    failed=[k for k,v in f['checks'].items() if not v]
    scope='первичных процессов; дополнительная серия прервана пользователем' if f.get('status') else 'первичных+дополнительных процессов'
    lines.append(f"* TL{t}: успешны{f['success']}/{f['runs']} {scope}; первичный max wall{primary[t]['max_wall']:.6f}с. Невыполненные условия: {', '.join(failed) or 'нет'}.")
lines += [f"* No-argument контракт, известные28 входов, TL10: {contract['success']}/{contract['expected']}; max wall{contract_slowest['wall']:.6f}с ({contract_slowest['case']}). Успех здесь использует прежний допуск TL+3, а не строгий10с bound. В рабочем каталоге только instance.json и solution.json; runtime читает default280 из исходника при отсутствии TL/аргумента.",
          f"* Финальный аудит: {len(audit['series'])} завершённых серий, {sum(x['rows'] for x in audit['series'])} процессов; пересечения CPU: {len(audit['overlaps'])}; изменения прежних файлов: {len(audit['preexisting_changes'])}; проверки записей: {audit['all_record_checks_pass']}.",
          '* В раннем combined-прототипе сохранены два превышения допуска при TL3, оба с валидным output. Они не исключены из общего evidence audit. Сборочные/подготовительные ошибки записаны отдельно; они не выдаются за solver-запуски.',
          '* Дедлайны native resplit/worker verification и setup boundary остаются мягкими. Номинальный40мс cutoff boundary не является строгой максимальной длительностью вызова; явного дополнительного времени к TL не добавлено.', '']
lines+=['Повторы одного входа могут попасть на разные пары физических ядер. Внутри каждого case/seed блока все варианты используют строго одинаковую пару; поэтому парный контраст сохраняется. Межseed-разброс включает также тип ядра и системную/thermal-нагрузку и не называется чистой дисперсией RNG.', '',
        'Все измерения качества выполнялись с DBG=1 у всех вариантов. Проверка стандартного запуска без DBG подтверждает интерфейс и валидность, но не является отдельным исследованием качества при DBG=0.', '']
lines+=['## Конфигурации ключевых побед и проигрышей','',
        'Ниже показаны крайние первичные пары, а не самостоятельное доказательство причинного эффекта оператора. Полные компоненты и сравнения с off находятся в JSON summaries. Временные траектории: [HOLDOUT280_REVIEW.md](../geometry_lab/HOLDOUT280_REVIEW.md); подробный разбор конфигураций: [HOLDOUT_CONFIGURATION_NOTES.md](HOLDOUT_CONFIGURATION_NOTES.md).', '']
for t,s in primary.items():
    pairs=[x for x in s['comparisons']['candidate_vs_v4']['pairs'] if x.get('pct') is not None]
    for tag,x in [('Худшая',min(pairs,key=lambda x:x['pct'])),('Лучшая',max(pairs,key=lambda x:x['pct']))]:
        c=x['configuration'];de=c['delta']
        lines.append(f"* {tag} TL{t}: {x['case']},seed{x['seed']},Δ{fmt(x['pct'])}%. Офисы{c['base']['offices']}→{c['candidate']['offices']}; изменены{c['assignment_changes']} назначений,{c['worker_changes']} worker assignments,{c['hulls_changed_common_offices']} общих оболочек. Δreward={fmt(de['reward'])},Δdistance={fmt(de['distance'])},Δoffice_cost={fmt(de['office_cost'])},Δpenalty={fmt(de['penalty'])}; objective меняется как reward−distance−cost−penalty.")
lines+=['','## Происхождение и воспроизведение','',
        f"* Exact v4 source SHA256:5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25.",
        f"* Final source SHA256:{freeze['source_sha256']}.", f"* Final binary SHA256:{freeze['binary_sha256']}.",
        '* Все независимые входы созданы после FINAL_FREEZE.json; algorithms/parameters после просмотра holdout не менялись. Sources, binary, input, output, runner, validator, spec и полный состав seeds/cases проверяются. Итоговые проверки процедуры отдельно рецензировал субагент.',
        '* Сборка:-O3 -std=c++17 -pthread, GCC16.2.1. Runtime single-file main.cpp+Makefile, default280с, instance.json→solution.json без аргументов. Нет checkpoint-reader, сети или внешних solver-зависимостей.', '',
        'Из корня репозитория собрать копию без изменения замороженного binary:', '', '```sh',
        'g++ -O3 -std=c++17 -pthread experiments/v4_perturbation/integration/final_candidate/main.cpp -o /tmp/szo_perturbation_rebuilt',
        '```', '',
        'Для повторного benchmark скопировать HOLDOUT60.json/HOLDOUT280.json или соответствующий development spec, задать новый destination и свободные cpu_pairs. Сохранённые каталоги не перезаписываются. Воспроизводить на тех же входах можно, но они уже не являются новым независимым holdout:', '', '```sh',
        '.venv/bin/python experiments/v4_perturbation/shared/run_blocks.py NEW_SPEC.json',
        '.venv/bin/python experiments/v4_perturbation/shared/analyze.py NEW_LOG_DIR NEW_SUMMARY.json',
        '.venv/bin/python experiments/v4_perturbation/shared/audit.py', '```', '',
        'Ничего не закоммичено, не добавлено в staging, не отправлено в Git или на сервер. v4/v6 и прежние пользовательские файлы сохранены. Очистка/карантин не требовались.']
lines += ['', 'Дополнительная худшая пара TL60: anti/2104, −9.017136% к exact v4 и +10.382235% к собственному off. Разные наборы офисов и потеря reward объясняют итоговый разрыв; он возник до финального boundary. Подробности и промежуточные состояния: [HOLDOUT_EXTRA60_REVIEW.md](../geometry_lab/HOLDOUT_EXTRA60_REVIEW.md). Причинный вред самого kick из этого сравнения не следует.', '']
trace_path=I/'FINAL_TRACE_ACCOUNTING.json'
if trace_path.exists():
    traces=read(trace_path)['rows']
    lines += ['## Цена возмущений и наблюдение плато', '',
              '| TL | Запусков | Доля sampled plateau ticks | Эпизодов | Improved episode records | Geometry/boundary вызовов | Сумма времени вызовов по потокам, с | Max вызов, с |',
              '|---:|---:|---:|---:|---:|---:|---:|---:|']
    for t in [60,280]:
        rows=[x for x in traces if x['seconds']==t]
        total=lambda k:sum(x[k] for x in rows)
        ticks=total('ticks');flat=total('plateau_ticks')
        calls=[x['construction_plus_repair_call_seconds'] for x in rows if x['construction_plus_repair_call_seconds']['n']]
        lines.append(f"|{t}|{len(rows)}|{flat/ticks:.6f}|{total('episodes'):.0f}|{total('improved_episode_records'):.0f}|{total('geometry_boundary_calls')}|{sum(x['sum'] for x in calls):.6f}|{max((x['max'] for x in calls),default=0):.6f}|")
    lines += ['', 'Суммы по потокам не равны процессному wall time. Проверки плато выполняются не через равные интервалы времени; improved episodes могут включать улучшения обычным native search. Это наблюдения контроллера, а не доказанная вероятность причинного успеха kick. Полные endpoint changes и длительности: [FINAL_TRACE_ACCOUNTING.json](FINAL_TRACE_ACCOUNTING.json); одинаковые checkpoint-состояния и gain/second: [OPERATOR_EFFICIENCY.json](OPERATOR_EFFICIENCY.json).', '']
package_path=I/'V8_PACKAGE.json'
if package_path.exists():
    package=read(package_path)
    lines += ['## Экспериментальная посылка v8', '',
              '[Проверенный ZIP](../../server_v8/artifacts/case03_cpp_server_v8_O3.zip) · [Происхождение и проверки](../../server_v8/PROVENANCE.json) · [Описание](../../server_v8/README.md)', '',
              f"Статус: {package['status']}. SHA256 ZIP: `{package['zip_sha256']}`. Исходник не менялся после независимой проверки; сборка распакованного ZIP побайтово совпала с замороженным бинарником.", '']
lines += ['', 'По уточнённому поручению пользователя этот исследовательский кандидат оформлен как v8. V7 содержит только точную v4: новых изменений с подтверждённой устойчивостью в этом исследовании не найдено. [Стабильная основа v7](../../server_v7/README.md).', '']
lines += ['', 'По просьбе пользователя длинные повторы остановлены: в дополнительной TL280-серии 16 завершённых успешных записей, 8 прерванных без итоговой записи и 6 не начатых запусков. Они сохранены в USER_STOP.json; их hashes проверены USER_STOP_AUDIT.json. Полная первичная TL280-серия завершена. Незавершённая дополнительная серия не объединяется со статистикой и не считается успешным полным протоколом. Аудит выше охватывает завершённые серии; отдельный журнал сохраняет все прерванные и не начатые позиции.', '']
(I/'REPORT.md').write_text('\n'.join(lines)+'\n')
short=['# Итог исследования возмущений v4','',lines[2],'',
       '| Первичный независимый тест | Среднее к v4 | Медиана | Худшая пара | W/T/L |',
       '|---|---:|---:|---:|---|']
for t,s in primary.items():
    c=s['comparisons']['candidate_vs_v4'];x=c['distribution_valid_outputs_including_failed_processes']
    short.append(f"|TL{t}|{fmt(x.get('mean'))}%|{fmt(x.get('median'))}%|{fmt(x.get('min'))}%|{wtl(c['wtl'])}|")
short+=['','Реализованы согласованные обмены/циклы, замена опорных точек, bounded kick/refill, late acceptance, adaptive tabu и best retention. Проверки на одинаковых состояниях, полноценные абляции и независимый holdout сохранены вместе с отрицательными результатами. Польза дешёвого kick ограничена дорогим восстановлением, зрелыми геометрическими бассейнами и вариативностью выбора офисов.', '',
        '[Полный итог и воспроизводимые команды](integration/REPORT.md) · [Development-разбор](integration/RESEARCH_NOTES_RU.md) · [Геометрическая лаборатория](geometry_lab/REPORT.md) · [Управление плато](escape_lab/REPORT.md)', '',
        'Исходники финального исследовательского варианта:integration/final_candidate/main.cpp и Makefile. Они сохранены для воспроизведения; статус допуска — integration/FINAL_DECISION_WITH_AUDIT.json. Никаких commit/staging/push/отправки на сервер.']
if package_path.exists():
    short += ['', '[Экспериментальная посылка v8](../server_v8/artifacts/case03_cpp_server_v8_O3.zip) · [Статус и происхождение](../server_v8/README.md). Подготовка архива не означает прохождения критериев качества.']
short += ['', '[Стабильная основа v7](../server_v7/README.md) сохраняет точную v4 без новых алгоритмических изменений. V8 содержит экспериментальный кандидат с отдельным выигрышем +24.245460%. Длинные дополнительные повторы остановлены пользователем; первичные TL60/TL280 завершены, неполная серия сохранена отдельно.']
(R/'REPORT.md').write_text('\n'.join(short)+'\n')
export=[]
for t in [60,280]:
    for suffix in ['', '_VARIANCE']:
        p=I/f'HOLDOUT{t}{suffix}_SUMMARY.json'
        if not p.exists():continue
        for comparison,c in read(p)['comparisons'].items():
            for x in c['pairs']:
                row={'seconds':t,'stage':'extra' if suffix else 'primary','comparison':comparison,
                     **{k:x.get(k) for k in ['case','seed','success','baseline','candidate','delta','pct','result']}}
                if 'configuration' in x:
                    q=x['configuration'];row.update({f'delta_{k}':v for k,v in q['delta'].items()})
                    row.update({k:q[k] for k in ['assignment_changes','office_set_changed','worker_changes','hulls_changed_common_offices']})
                export.append(row)
with (I/'HOLDOUT_PAIRS.csv').open('w') as f:
    fields=list(dict.fromkeys(k for x in export for k in x));writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(export)
print('Reports written; recommended replacement:',accepted)
