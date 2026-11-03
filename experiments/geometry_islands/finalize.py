from pathlib import Path
import json,hashlib,subprocess,zipfile
H=Path(__file__).resolve().parent;R=H.parents[1]
subprocess.run(['/tmp/ta-boundary-venv/bin/python',str(H/'summarize.py')],check=True)
subprocess.run(['/tmp/ta-boundary-venv/bin/python',str(H/'final_tables.py')],check=True)
c=json.loads((H/'logs/COMPARISON.json').read_text());assert c['robust_holdout60']['stats']['completed']==60
for tag,n in [('robust_edges60',16),('precision60',10)]:
 rows=json.loads((H/'logs'/tag/'results.json').read_text())['results'];assert len(rows)==n and all(r['error'] is None and r['rc']==0 for r in rows)
p=json.loads((H/'logs/package60/results.json').read_text());assert len(p)==4 and all(r['error'] is None and r['rc']==0 for r in p)
manifest=json.loads((H/'PACKAGE_MANIFEST.json').read_text());manifest.update(status='Experimental precision fix; ordinary score superiority NOT established; primary unchanged; not submitted',validation=dict(ordinary_candidate_valid=30,edge_candidate_valid=16,precision_candidate_valid=5,contest_filename_valid=4),ordinary=c['robust_holdout60']['stats'])
z=Path(manifest['zip']);assert hashlib.sha256(z.read_bytes()).hexdigest()==manifest['sha256']
with zipfile.ZipFile(z) as zz:
 assert sorted(zz.namelist())==['Makefile','main.cpp'];assert hashlib.sha256(zz.read('main.cpp')).hexdigest()==manifest['source_sha256']
(H/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,indent=2))
report=(H/'REPORT.md').read_text().replace('Статус: эксперименты продолжаются; результаты ниже предварительные до итогового раздела.','Статус: этап завершён; все запланированные подтверждающие серии закончены. Основной solver не изменён.')
lead='''
**Результат этапа.** Найдено и проверено усиление геометрических ограничений локального
MIP: офис + два сайта вместо произвольных трёх сайтов. На независимых anti/latent
новый вариант за60 с нашёл небольшие улучшения и доказал условную оптимальность,
старый не улучшил incumbent и остановился по времени. Отдельно исправлены ложные
геометрические запреты от eps: на трёх узких диагностических задачах20→80 (точный
оптимум). Полная новая C++-версия на10 свежих обычных задачах×3 зерна: mean изменения
медиан+0.424%, медиана−0.020%, худшая парная регрессия−10.875%. Общего победителя
по score нет; новый ZIP остаётся экспериментальным, прежний основной кандидат сохранён.

'''
report=report.replace('## Литература и применимость',lead+'## Литература и применимость',1)
report+='''

## Итоговые подтверждения и решение об интеграции

Полная таблица: `COMPARISON.md`; все исходные серии, включая ошибки, `RESULTS.md`.
На обычных входах фиксировались одинаковые60 с, NT2, -O3 -std=c++17, jobs4.
Среднее ниже — равновзвешенное среднее относительных изменений медиан по10 входам;
это не официальный нормированный score жюри и не доверительный интервал.

| Версия / независимый набор | Runs VALID | Mean Δ медиан | Median Δ | Худшая медиана | Худшая пара |
|---|---:|---:|---:|---:|---:|
| grid / holdout seeds61,62,63 | 60/60 | +0.4365% | 0% | latent1 −0.6810% | latent1/61 −1.2797% |
| exact+grid / validation2 seeds71,72,73 | 60/60 | +0.4236% | −0.0204% | alphabig0 −0.5387% | anti0/71 −10.8751% |

Grid:8 побед,9 поражений,13 совпадений по парным зёрнам; лучший median huge+3.9214%.
Exact:9 побед,15 поражений,6 совпадений; лучший median anti+5.0334%.
На anti отдельные exact/base пары:−10.875%,+5.072%,+0.247%; три прогона не дают
уверенности в устойчивом преимуществе. На предварительном train spatial index уже
имел large median−4.832% при huge+6.273%; выбирать его только по huge было бы ошибкой.
Оба набора фиксировались до подтверждения, реализации после результатов не менялись.
Grid и exact использовали разные независимые наборы: сравнивать их means между собой
как прямой A/B нельзя. Превосходство exact над grid отдельно не измерено.

Для exact дополнительно16/16 edge VALID, пять диагностик против базы10/10 VALID,
четыре запуска из ZIP с конкурсными именами4/4 VALID. Всего именно candidate55/55
валидных полных запусков. Precision wide80→80, coincident20→20,
thin/thinner/translated20→80. Эти искусственные случаи доказывают устранение конкретной
потери качества, но не частоту её появления на скрытых данных.
Максимальное wall в ordinary index60.186 с, exact60.162 с, edge59.684 с,
package59.984 с. Это внутренний бюджет60 с плюс небольшой хвост завершения;
не проверялся внешний kill на ровно60.000 и не выполнялся300-секундный серверный прогон.

### Локальный MIP: подтверждённое сокращение поиска

Таблица всех15 запусков: `ANCHOR_RESULTS.md`. Лимит60 с, SCIP1 поток, jobs3,
radius16, ближайшая пара открытых офисов, тот же incumbent и все прежние ограничения
ресурсов. На train исходные SEED1 incumbents; на независимом holdout SEED61.
SCIP использует прежнее фиксированное зерно по умолчанию; повторов процессов нет.

| Вход | Old | Anchor | Изменение результата |
|---|---:|---:|---|
| train anti | 60.02 с, time limit | 29.50 с, optimal | тот же incumbent |
| train latent1 | 43.86 с, optimal | 7.03 с, optimal | одинаковые37562.169787 |
| train multiskill | 38.46 с, optimal | 1.02 с, optimal | одинаковые79.407829 |
| holdout anti | 60.04 с, time limit | 24.39 с, optimal | 60.371763→60.483042 (+0.1843%) |
| holdout latent1 | 60.18 с, time limit | 40.46 с, optimal | 38892.083712→38920.728970 (+0.0737%) |
| holdout multiskill | 1.57 с, optimal | 0.49 с, optimal | одинаковые46753.371815 |

Здесь optimal означает только выбранную пару/пул кандидатов/radius16. Это не сертификат
оптимальности исходной задачи. На holdout число cuts уменьшилось anti2858→871,
latent2543→841, multiskill360→39. На train shrink ещё быстрее на latent/multi,
но anti не доказал оптимальность за60 с: построение старого, затем нового свидетельства
дороже, а доминирование отдельного cut не гарантирует лучшую траекторию всего SCIP.
Выбранный для holdout вариант anchor зафиксирован в `ANCHOR_PREREGISTRATION.json`.
Все15 ответов проверены официальным валидатором. Начальные6 import failures из-за
отсутствия SciPy сохранены отдельно в anchor60; это не результаты оптимизации.

### Что переносить

1. **Первый приоритет — короткий anchored witness.** Готовый `anchor_integration.patch`
   заменяет offline support в colgen, автоматически используемый local_mip; старые файлы
   пока не менялись. Для конкурсного C++ разумный следующий шаг — перенос этого принципа
   в native B&B/LNS: ленивые запреты пар для фиксированных соседей и четвёрок для двух
   переменных зон. Python/SCIP в посылку не включать. Ускорение offline MIP не следует
   автоматически считать ускорением native B&B: нужно отдельное измерение.
2. **Точные предикаты — исправление конкретной численной модели.** Готовы C++ source,
   модульная интеграция и experimental ZIP. Не включать вслепую по среднему+0.424%:
   медиана эффекта отрицательна,15/30 пар хуже. Следующий опыт — более дешёвый точный
   fast path/портфель или безопасный финальный переход к точной геометрии, с новым
   holdout. Эти варианты здесь не реализованы и не выдаются за проверенные.
3. **Grid — опциональный ускоритель**, но выигрыш score не универсален. Отдельная
   адаптация по размеру/hull fraction потребует новой предварительно зафиксированной
   гипотезы; выбирать порог по этим подтверждающим данным без нового holdout нельзя.
4. **Islands/open/global/targeted** пока не заменяют контрольный B&B. Сильнее выглядит
   применение island к верхним оценкам pricing и угловой структуры — к компактному
   локальному MIP с совместными навыками. Prefix-MIP пока только выведен и проверен
   на уровне геометрических отношений, не измерен как решатель.

### Артефакты и сохранность

Экспериментальный архив `artifacts/geometry_exact_experimental_O3.zip`, SHA256
`d183d04b5ed84b6ed455dfd2c959346c4a4368956bfbc7225a76367de55f011d`.
Внутри только main.cpp и Makefile, -O3 -std=c++17; default280 с; читает instance.json,
пишет solution.json, без сети/кеша/внешних библиотек. Использует GNU unsigned __int128,
который поддерживает проверенный g++; это расширение компилятора, не ISO C++ тип.
Исследовательские данные/оракулы/решения/Scipy/SCIP в архив не входят.

`integration.patch` и `integration/solver` не применены. Склейка модулей побайтно
совпадает с проверенным robust_v1.cpp, SHA256
`78764b6f421149f079601444a2eacda396d7465b3c2e1a2001ad76d3598de002`.
Оба патча проходят git apply --check на текущей сохранённой базе. Полные абсолютные
пути и hashes — `PATHS.json`, команды — `REPRODUCE.md`, условия сборки — `AUDIT.json`,
версии исследовательских пакетов — `requirements-research.txt`.

Все18 исходников основной базы совпадают с начальным snapshot. Прежний server_v3_O3
ZIP и boundary_tail ZIP сохранены; genetic warm start и worker DFS по-прежнему находятся
в основной базе. HEAD/ветка прежние; staging пустой; коммитов и серверных отправок нет.
Из основного дерева дополнена только строка журнала EXPERIMENTS.md.
'''
(H/'REPORT.md').write_text(report)
entry='| 10-19 | Codex | research/boundary-beam-research | Deep geometry: islands/depth, anchored rank4 cuts, exact binary64 predicates, grid | 60с NT2×3: grid holdout60/60 VALID mean+0.4365%, exact holdout60/60 mean+0.4236% median−0.0204%, worst pair−10.875%; precision3×20→80; candidate55/55 VALID. Local SCIP anchored15/15 VALID: fresh anti+0.1843%, latent+0.0737%, conditional optimal24.4/40.5с vs old60с timeout. Shape operators weaker than control B&B | Main unchanged; geometry_islands/REPORT.md, 2 optional patches, geometry_exact_experimental_O3.zip; no commit/submission |\n'
p=R/'EXPERIMENTS.md';old=p.read_text();assert 'Deep geometry: islands/depth' not in old;p.write_text(old+'\n'+entry)
print('Final report and journal written; raw logs preserved')
