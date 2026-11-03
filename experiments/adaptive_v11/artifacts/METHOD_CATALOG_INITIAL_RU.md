# Карта текущих решений и классификация входов

Все прежние данные, включая прежние holdout, в этой работе считаются development. Отчёты использованы как указатели; количественная таблица ниже пересчитана из сырых results/MANIFEST с exact-v4 binary SHA и текущими совпадающими хешами входов/кандидатов. Разные TL и checkpoint-only эксперименты не объединяются.

| Семейство | Представление/метод | Роль в адаптивной версии |
|---|---|---|
| [Server v4](../../server_v4/MANIFEST.json) | Неизменный контроль: GA наборов офисов, геометрические/дорожные старты, LNS, финальный B&B. | Контрольный эксперт, точный source SHA5b3914…. |
| [v2/v3 и память](../../server_candidate/REPORT.md) | Повторное использование буферов/геометрии, worker DFS, finish-fill. | Предки v4; экономию allocations нельзя автоматически считать приростом качества. |
| [Evolution](../../evolution/REPORT.md) | Генетический поиск наборов офисов, worker certificates и SCIP-прототипы. | Нативные полезные части уже в v4. Не отдельный независимый современный эксперт. |
| [Geometry islands](../../geometry_islands/REPORT.md) | Точная геометрия по всем входным точкам, spatial grid, острова/anchor. | Геометрическая проверка и индекс уже в v4; отдельные kernel/локальные улучшения не метки победителя полного solver. |
| [Boundary/beam](../../boundary_beam/REPORT.md) | Граничный B&B, support/beam и финальный хвост. | Финальный B&B включён в v4; ранние/support версии требуют собственных полных сравнений. |
| [Column generation](../../colgen/REPORT.md) | SCIP pricing, restricted LP/IP master по зонам. | Исследовательский solver/подзадачи; restricted bound не глобальный и checkpoint gain не full-run label. |
| [Clustering](../../clustering/REPORT.md) | Road profiles/PCA/MDS/UMAP, balanced LP, кластер→геометрическая проекция. | Дорогие offline embeddings и restricted master; нет основания включать как быстрый старт по одной метке «road». |
| [MILP v5](../../milp_v5/REPORT.md) | Выбор/назначения/работники в ограниченной окрестности. | Сохраняет истинную цель, но полные серии содержат регрессии; выигрыши отдельных checkpoint не классификатор. |
| [MILP boundaries](../../milp_v5_boundaries/REPORT.md) | Более сильная boundary-модель, переменные группы и геометрические cuts. | Известны ранние RE и исправленные варианты; стоимость интеграции существенна. Старые результаты не удаляются. |
| [DP/MILP](../../dp_milp/REPORT.md) | Оптимизация фиксированного размещения: count/task-load и профили работников. | Условная точность требует фиксированных параметров; не глобальное решение. |
| [V4 local search](../../v4_local_search/REPORT.md) | Циклы, repair, exchange, fair/ILS и tail. | Небольшой независимый mean при существенных регрессиях; локальные механизмы не дают надёжного широкого routing. |
| [Декомпозиция/поиск → server v6](../../v4_deep_parallel/integration/REPORT.md) | Batch/ALNS/archive/niches/memo/wide; geometry→joint→boundary. | Две длинные лаборатории; TL280 hybrid не подтвердил общую замену. Флагам нужен свой evidence, не объединять все улучшения. |
| [Server v6](../../server_v6/MANIFEST.json) | Упаковка проверенного hybrid из предыдущей строки. | Не считать тем же алгоритмом, что v4; не добавлять повторно как независимые наблюдения. |
| [Server v7](../../server_v7) | Историческая серверная упаковка; нет стандартного matched-manifest в каталоге. | Неполные метки: нельзя придумывать среднее или предпочтительный класс. |
| [Plateau/support → server v8](../../v4_perturbation/integration/REPORT.md) | Support-kick, boundary-only, late acceptance/tabu и их абляции. | Есть полные TL280, но лишь шесть независимых входов для конфигурации; недостаточно для сложного классификатора. |
| [Server v8](../../server_v8/RESULTS_RU.md) | Упаковка support-kick/boundary на exactv4. | Те же данные integration; не дублировать их как новую выборку. |
| [Exact neighborhoods](../../v8_exact_neighborhoods/REPORT_RU.md) | Полный домен локального выбора, геометрические cuts, worker deadline вместо node cap, whole-zone packets. | Доказан worker false negative, но общие серии только TL10/60. Tiny exact v9 закрывает часть этих случаев. |
| [Structural v9](../../structural_v9/REPORT_RU.md) | Полные зоны на малых, restricted master, signed atomic exchanges. | Tiny exact нужен как математически проверяемая ветка; tail наследуется геометрическим экспертом. Resource repeat не поддержал общую замену. |
| [Warm v10](../../warm_v10/REPORT_RU.md) | Геометрические геномы/реальные назначения/feasible fitness. | Основной второй эксперт: средний выигрыш, но существенные регрессии. Mode2, singleton shortcut и mass balancing не путать с выбранной v5 geometry. |
| [Текущий solver/](../../../solver/solve.cpp) | Накопленные модульные изменения, snapshot собран в adaptive_v11/artifacts/current_modular. | Не является exactv4. Отдельное текущее matched-screen; пользовательские файлы не изменяются. |
| [Интеграции](../../v4_main_integration/MANIFEST.json) | Исторические переносы изменений в модульный solver. | Не отдельные независимые наборы результатов: происхождение/snapshot сверять по хешам. |

## Проверяемые признаки

Числа сайтов/офисов/работников, site/office и skill/office; доля многопрофильных работников и необслуживаемых сайтов; суммарная ёмкость относительно сайтов; A относительно среднего количества сайтов на офис; α×среднее число задач/средняя награда; корреляция истинных расстояний с геометрическими и совпадение ближайшего офиса; доля положительных назначений; анизотропия координат. Все масштабные экономические признаки нормированы. Файл/название/seed/хеш/ответ в признаки не входят.

Метки: 100×(candidate−v4)/abs(v4). При baseline=0 процент не выдумывается. Все строки и причины исключений сохранены в HISTORICAL_PAIRS/EXCLUSIONS; классификационный анализ не скрывает неудачные выполнения. Неравные affinity не используются как доказательство причинного выигрыша. Полные длинные серии остаются наблюдениями на общей машине.

## Что реально видно на TL280

| Источник бинарника/флаги | Класс | Разных входов | Пар | Средний по входам, % | Худшая пара, % | Обе рабочие успешны |
|---|---|---:|---:|---:|---:|---:|
| v4_deep_parallel/search/bin/lab2 {"LAB_BATCH": "1"} | нерегулярные расстояния | 1 | 2 | +0.2526 | +0.2383 | 2/2 |
| v4_deep_parallel/search/bin/lab2 {"LAB_BATCH": "1"} | расстояния против геометрии | 1 | 2 | +12.3986 | +0.0000 | 2/2 |
| v4_deep_parallel/search/bin/lab2 {"LAB_WIDE": "1"} | нерегулярные расстояния | 1 | 2 | -0.2211 | -0.3767 | 2/2 |
| v4_deep_parallel/search/bin/lab2 {"LAB_WIDE": "1"} | расстояния против геометрии | 1 | 2 | +26.2201 | +15.3578 | 2/2 |
| v4_deep_parallel/search/bin/lab2 {} | нерегулярные расстояния | 1 | 2 | -0.1252 | -0.4779 | 2/2 |
| v4_deep_parallel/search/bin/lab2 {} | расстояния против геометрии | 1 | 2 | +8.2175 | +0.0000 | 2/2 |
| structural_v9/artifacts/final_research/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0"} | дефицит навыков | 2 | 6 | +0.0995 | -0.0362 | 6/6 |
| structural_v9/artifacts/final_research/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0"} | крупные ≥4096 | 3 | 10 | -1.1042 | -7.2512 | 10/10 |
| structural_v9/artifacts/final_research/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0"} | малые ≤16 | 5 | 15 | +5.7395 | +0.0000 | 15/15 |
| structural_v9/artifacts/final_research/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0"} | нерегулярные расстояния | 5 | 22 | -0.3472 | -4.7582 | 20/22 |
| structural_v9/artifacts/final_research/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0"} | прочие | 4 | 12 | +1.1804 | -0.8043 | 12/12 |
| structural_v9/artifacts/final_research/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0"} | расстояния против геометрии | 4 | 18 | +0.7598 | -0.4040 | 18/18 |
| structural_v9/artifacts/final_research/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0"} | тесный count/load баланс | 5 | 16 | -0.1502 | -10.0374 | 16/16 |
| structural_v9/artifacts/final_research/candidate {} | малые ≤16 | 2 | 6 | +3.2351 | +0.0000 | 6/6 |
| structural_v9/artifacts/final_research/candidate {} | нерегулярные расстояния | 1 | 3 | -2.3029 | -6.2177 | 3/3 |
| structural_v9/artifacts/final_research/candidate {} | прочие | 1 | 3 | +1.3354 | +0.0000 | 3/3 |
| structural_v9/artifacts/final_research/candidate {} | расстояния против геометрии | 2 | 6 | +2.2944 | -0.1814 | 6/6 |
| structural_v9/artifacts/final_research/candidate {} | тесный count/load баланс | 1 | 3 | -0.0774 | -0.3733 | 3/3 |
| warm_v10/artifacts/v6/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0", "GW_MODE": "1"} | крупные ≥4096 | 1 | 2 | +2.7048 | +0.3854 | 2/2 |
| warm_v10/artifacts/v6/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0", "GW_MODE": "1"} | нерегулярные расстояния | 1 | 2 | -1.2678 | -2.1897 | 1/2 |
| warm_v10/artifacts/v6/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0", "GW_MODE": "1"} | расстояния против геометрии | 1 | 2 | +21.5979 | +20.2942 | 2/2 |
| warm_v10/artifacts/v8/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0", "GW_MODE": "1"} | крупные ≥4096 | 1 | 2 | -8.9518 | -17.2221 | 2/2 |
| warm_v10/artifacts/v8/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0", "GW_MODE": "1"} | нерегулярные расстояния | 1 | 2 | -0.9617 | -2.0519 | 1/2 |
| warm_v10/artifacts/v8/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0", "GW_MODE": "1"} | расстояния против геометрии | 1 | 2 | +26.7608 | +22.4429 | 2/2 |
| warm_v10/artifacts/v5/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0", "GW_MODE": "1"} | дефицит навыков | 1 | 3 | +0.1523 | +0.0000 | 3/3 |
| warm_v10/artifacts/v5/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0", "GW_MODE": "1"} | крупные ≥4096 | 2 | 7 | +2.0961 | -8.5776 | 7/7 |
| warm_v10/artifacts/v5/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0", "GW_MODE": "1"} | нерегулярные расстояния | 3 | 10 | +2.9309 | -0.1335 | 9/10 |
| warm_v10/artifacts/v5/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0", "GW_MODE": "1"} | прочие | 1 | 3 | +1.1991 | +0.6306 | 3/3 |
| warm_v10/artifacts/v5/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0", "GW_MODE": "1"} | расстояния против геометрии | 3 | 9 | +10.4819 | -3.6800 | 9/9 |
| warm_v10/artifacts/v5/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0", "GW_MODE": "1"} | тесный count/load баланс | 4 | 10 | +4.9932 | -1.5215 | 10/10 |
| warm_v10/artifacts/v5/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0", "GW_MODE": "2"} | крупные ≥4096 | 1 | 2 | -1.7850 | -3.4681 | 2/2 |
| warm_v10/artifacts/v5/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0", "GW_MODE": "2"} | нерегулярные расстояния | 1 | 2 | -0.2018 | -0.2766 | 2/2 |
| warm_v10/artifacts/v5/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0", "GW_MODE": "2"} | расстояния против геометрии | 2 | 4 | +11.6693 | -0.3868 | 4/4 |
| warm_v10/artifacts/v5/candidate {"ZM_POOL": "0", "ZM_RESERVE": "0", "GW_MODE": "2"} | тесный count/load баланс | 2 | 4 | +3.4933 | -0.2855 | 4/4 |
| v4_perturbation/integration/final_candidate/solve {"ESCAPE_MODE": "0"} | дефицит навыков | 1 | 2 | +0.0000 | +0.0000 | 2/2 |
| v4_perturbation/integration/final_candidate/solve {"ESCAPE_MODE": "0"} | крупные ≥4096 | 1 | 3 | +0.4098 | -0.0006 | 3/3 |
| v4_perturbation/integration/final_candidate/solve {"ESCAPE_MODE": "0"} | прочие | 3 | 7 | +0.1864 | -1.6447 | 7/7 |
| v4_perturbation/integration/final_candidate/solve {"ESCAPE_MODE": "0"} | расстояния против геометрии | 1 | 2 | +2.7870 | +2.4330 | 2/2 |
| v4_perturbation/integration/final_candidate/solve {} | дефицит навыков | 1 | 2 | +0.0000 | +0.0000 | 2/2 |
| v4_perturbation/integration/final_candidate/solve {} | крупные ≥4096 | 1 | 3 | -0.4591 | -1.1789 | 3/3 |
| v4_perturbation/integration/final_candidate/solve {} | прочие | 3 | 7 | +0.3171 | -1.6063 | 7/7 |
| v4_perturbation/integration/final_candidate/solve {} | расстояния против геометрии | 1 | 4 | +6.0478 | -0.0378 | 4/4 |
| v4_deep_parallel/integration/bin/hybrid_frozen {} | дефицит навыков | 1 | 1 | -2.0007 | -2.0007 | 1/1 |
| v4_deep_parallel/integration/bin/hybrid_frozen {} | крупные ≥4096 | 3 | 5 | -0.1556 | -0.9610 | 5/5 |
| v4_deep_parallel/integration/bin/hybrid_frozen {} | нерегулярные расстояния | 1 | 1 | +0.6445 | +0.6445 | 1/1 |
| v4_deep_parallel/integration/bin/hybrid_frozen {} | прочие | 5 | 8 | +0.2090 | -0.1389 | 8/8 |
| v4_deep_parallel/integration/bin/hybrid_frozen {} | расстояния против геометрии | 2 | 3 | +2.5284 | +0.1523 | 3/3 |

## Ограничение статического выбора

Для выбранного v10 имеются лишь14 различных входов с matched TL280. На двух входах по10000 сайтов/24офиса/64работника/6навыков/A100/af.01 средние дельты составляют −3.5094% и+7.7016%. Размер сам по себе не определяет победителя. Название «anti» тоже не гарантирует одинаковый эффект: два рассмотренных входа дают примерно+30.52% и+0.01%.

Неглубокие деревья с заранее заданными физическими порогами, минимум3–5 входов в листе, проверены leave-one-input-out: все seeds исключаемого входа уходят вместе. Лучший постоянный geometry даёт исторический mean+4.6968%; лучший depth>0 вариант+4.1467%, обе оценки сохраняют worst−8.5776%. Это development model-selection, не независимая оценка. Выученное дерево не включено в runtime.

Вместо недоказанной метки победителя реализованы: сертифицируемые single-office/collinear/tiny ветки и online racing двух разных полных поисков. Признаки меняют время наблюдения, реальная допустимая цель и её прогресс — последующий выбор. Все затраты входят в общий wall budget. Соревнование не гарантирует результат не хуже каждого отдельного двухпоточного solver: каждый эксперт сначала получает один CPU.

## Точные подклассы

Single office: при неотрицательной стоимости максимум достигается на самых прибыльных обслуживаемых сайтах до maxSize; все работники могут быть назначены единственному офису, межофисных конфликтов и штрафа диапазона нет. Сравнение с пустым решением обязательно.

Collinear: все исходные сайты и офисы точно на одной прямой; α=0; A≥maxSize всех офисов; либо нет задач, либо работников≥офисов и каждый покрывает все требуемые навыки. Совместимость зон эквивалентна непересечению интервалов входных точек. Для каждого интервала, включающего офис, берём top-cap положительные вклады минус стоимость. Weighted interval DP выбирает совместимый набор. Две зоны одного офиса не могут попасть в него, поскольку обе содержат одну и ту же офисную точку. Любое допустимое решение представлено своими истинными крайними точками; замена на top-cap внутри того же интервала сохраняет допустимость и не уменьшает цель. Значит DP точен в указанном подклассе. Дубликаты объединяются по геометрической позиции, незадействованные точки и закрытые офисы остаются в пространстве интервалов.

Общая проверка и native verify обязательны. Почти коллинеарные точки, binding A, α>0, недостаточные универсальные навыки возвращаются в общий поиск. При deadline незаконченная ветка не объявляется точным оптимумом. Ограничение256сайтов/16офисов — ограничение стоимости перебора, не подпись конкретного теста.

Single/line oracle:80 полных независимых enumerations,84/84 official VALID с четырьмя проверками отказа от ветки. Общая конкурентная часть: monotone arbiter, выдача/отмена второго worker, обмен лучшим состоянием; QA v2 66/66 VALID. Количественные полные сравнения новых версий публикуются отдельно после окончания серий.
