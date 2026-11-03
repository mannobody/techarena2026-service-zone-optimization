# Воспроизведение

Все команды от корня проекта. Данные и код уже сохранены; существующие каталоги
запусков не перезаписываются. Повтор на тех же входах — regression/development,
не новый независимый holdout. TL280 в этом раунде не запускался.

## Конкурсный код и проверка

`artifacts/final/main.cpp` + `Makefile` — замороженный standalone. ZIP содержит
ровно эти два файла. `PACKAGE.json` связывает ZIP, исходник и побайтово
пересобранный binary с frozen benchmark. Обычный `make run` использует280с;
для проверки ниже явно задан короткий бюджет.

```sh
taskset -c 14,15 g++ -O3 -std=c++17 -pthread experiments/v8_exact_neighborhoods/artifacts/final/main.cpp -o /tmp/szo-exact-rebuilt
NT=2 SEED=3601 /tmp/szo-exact-rebuilt experiments/v8_exact_neighborhoods/inputs/worker_budget_isolated.json /tmp/szo-exact-solution.json 2
.venv/bin/python task/validate_solution.py experiments/v8_exact_neighborhoods/inputs/worker_budget_isolated.json /tmp/szo-exact-solution.json
```

Ожидается45. Frozen v4/v8/all-off на этом примере дают36. Это один доказанный
механизм с3 seed, не общая оценка качества.

No-argument контракт проверен в `logs/contract/noarg_*`: в каждом рабочем
каталоге `instance.json`, программа создаёт `solution.json`; TL1 через env,
DBG и NT unset. Отдельный файл stderr создаёт harness, не runtime.

## Параметры frozen runtime

|Переменная|Default|Смысл|
|---|---:|---|
|TL|280|Общий wall-budget; парсинг, все операторы, восстановление и публикация внутри|
|NT|2|Default не превышает2 CPU; make run явно NT2|
|XN_FILL|2|0 native;1 обе версии;2 greedy/finish fallback;3 recreate fallback|
|XN_WORKER|1|Без node cap, с caller deadline и локальным2мс cutoff; timeout не proof|
|XN_TINY|1|Полный native B&B при N≤10,M≤5, ≤0.15с внутри общего TL|
|XN_MODE|0|1 geo-tail;2 structural-tail;3 смешанный;4 whole-zone templates|
|XN_SIG_FIX|0|Канонический open-bit при realize/open/close; quality отдельно не доказан|
|ESCAPE_MODE|0|Прежний controller v8 сохранён, но default выключен|

Baseline v8 запускается отдельным **неизменённым** `artifacts/v8`; её default
ESCAPE_MODE5. Новый all-off: XN_FILL0, XN_WORKER0, XN_TINY0, XN_MODE0,
XN_SIG_FIX0, ESCAPE_MODE0. Контроли не подменяются текущим solver/.

## Полные сравнения

`FULL_DEV4.json`:144 exploratory процессов, мягкий TL4, перелёты явно сохранены.
`INDEPENDENT10.json`:96 процессов с внешним hard wall,8 входов ×2seed ×6вариантов.
`LONG60_DIAGNOSTIC.json`:32 процесса,4 из тех же входов ×2seed ×4варианта.
32 длинных запуска зарегистрированы до их результатов в
`LONG_PROTOCOL_ADDENDUM.json`; отрицательный TL10 ими не заменяется.

Для повторного запуска скопировать выбранный spec, задать **новый** destination
и свободные CPU пары, затем:

```sh
.venv/bin/python experiments/v8_exact_neighborhoods/src/run_blocks.py NEW_SPEC.json
python3 experiments/v8_exact_neighborhoods/src/evaluate.py NEW_LOG_DIRECTORY
.venv/bin/python experiments/v8_exact_neighborhoods/src/trajectories.py NEW_LOG_DIRECTORY
```

Runner сохраняет источники/binaries/input hashes, affinity, raw stderr, wall,
RSS/user/sys, rc, остановки на deadline, validator result и snapshots. Внешний
SIGTERM адресуется solver-child, time-parent успевает записать RSS. Изначальный
runner для checkpoint остался в старой лаборатории, здесь копия с resume/hard wall.
Freeze защищает код/параметры/композицию/лимит128 независимых процессов.

## Exact oracle и MILP

Локальные solver-зависимости находятся в `offline_deps/`; они **не используются**
конкурсным C++. Версии и .so hashes: OFFLINE_DEPENDENCIES.json.

```sh
PYTHONPATH=experiments/v8_exact_neighborhoods/offline_deps .venv/bin/python experiments/v8_exact_neighborhoods/src/mip.py INSTANCE.json INCUMBENT.json NEW_MODEL_RESULT.json --kind structure --backend highs --seconds 2 --budget 12
PYTHONPATH=experiments/v8_exact_neighborhoods/offline_deps .venv/bin/python experiments/v8_exact_neighborhoods/src/mip.py INSTANCE.json INCUMBENT.json NEW_MODEL_RESULT_SCIP.json --kind geometry --backend scip --seconds 2 --budget 12
```

API `mip.improve(..., selected=[...], offices=[...])` даёт точно одинаковые
домены обеим backend; CLI structure выбирает первые budget сайтов только как
простую демонстрацию. Для mature screen использован peel/whole-small-zone selection
в src/mip_checkpoints.py, а не CLI fallback.

`logs/verify_complete/`:133 сравнения с полным oracle; LP/matrix в models/verify_complete.
`logs/extra_cases/`, SKILL_COUNT_CASE.json, WORKER_MODELS.json — отдельные сильные
свидетельства; logs/mip_checkpoints_uncontended — timed repeat28 моделей с8с.
Ранние2с MIP-измерения сохранены, но часть их времени пересеклась с подготовкой
на тех же ядрах и не используется как честное backend speed comparison.

Checkpoint binaries:
`artifacts/checkpoint` — первая геометрическая/структурная лаборатория;
`artifacts/candidate_v2/checkpoint` — дополнительно packet/fill/open ablations.
Интерфейс: input checkpoint output seconds mode; **только офлайн**, в ZIP не входит.

## Где смотреть детали

* REPORT_RU.md — вывод и таблицы, FINAL_DECISION.json — исходные критерии.
* reports/AUDIT_RU.md — правило→код→контрпример→исправление; математика моделей.
* logs/*/TRAJECTORIES.json — reward/distance/cost/penalty, counts, loads, workers,
  изменения назначений/оболочек и первое наблюдаемое расхождение.
* reports/COUNT_BARRIERS.json — почему q12 не может открыть/закрыть зрелые зоны.
* logs/worker_full/COUNTEREXAMPLE_EVALUATION.json — воспроизводимый +25% и разбор
  шести raw harness flags, вызванных ранним точным выходом с1потоком.
* logs/INTERRUPTION.json —29 завершённых +1 interrupted; resumed series70 полных.
* PREPARATION_EVENTS.json — ошибки подготовки, не замаскированные под solver успех.

Никаких commits/staging/push/server submit. Активные зависимости/промежуточные
версии нужны для воспроизведения и сохранены. Ненужных собственных файлов для
карантина не оказалось; старый to_delet/ не изменялся.
