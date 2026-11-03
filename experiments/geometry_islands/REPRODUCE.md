# Воспроизведение

Корень исследований:
`./experiments/geometry_islands`.
Python: `/tmp/ta-boundary-venv/bin/python`; версии пакетов — `requirements-research.txt`.
GCC/ветка/HEAD/сохранность базы — `AUDIT.json`. Исследовательские зависимости не входят в ZIP.
Полный перечень абсолютных путей и SHA256 — `PATHS.json`.

Скомпилированные исходники версий неизменяемы. Для повторов используйте новый tag и новый
выходной бинарник; генераторы/oracle со статическими именами логов запускайте в отдельной
копии каталога, чтобы не заменить исходные результаты. В командах ниже текущий каталог —
корень исследований, указанный выше. Архивы не пересобирайте поверх существующих.

```sh
g++ -O3 -std=c++17 artifacts/robust_v1.cpp -o /tmp/geometry_exact_rebuild
/tmp/ta-boundary-venv/bin/python bench.py --tag repeat_exact60_new --split validation2 --variants base,exact --exe robust_v1 --seeds 71,72,73 --seconds 60 --threads 2 --jobs 4
/tmp/ta-boundary-venv/bin/python bench.py --tag repeat_index60_new --split holdout --variants base,grid --exe index_v1 --seeds 61,62,63 --seconds 60 --threads 2 --jobs 4
/tmp/ta-boundary-venv/bin/python bench.py --tag repeat_post60_new --split train --variants 4,8 --exe post_v3_finalize --post-from train_base60 --seeds 12 --seconds 60 --threads 1 --jobs 4
```

Для сравнения MIP: `bench_anchor_v2.py` и `bench_anchor_holdout.py`; меняйте имена
логов в копии скриптов. Источник incumbent и выбор пары зафиксированы внутри них.
Все сохранённые JSON-решения проверяет
`./task/validate_solution.py`.

Конкурсная проверка воспроизведена в `logs/package60`: запуск `make build`, затем
`TL=60 NT=2 SEED=81 make run` при наличии только `instance.json` как входных данных.
Результат `solution.json`; четыре готовых прогона и их score — `logs/package60/results.json`.
Default без TL остаётся280 секунд. Проверки полного solver выполнялись с внутренним
лимитом60; wall включает небольшой выход за этот бюджет на завершение/планирование,
это не внешний жёсткий SIGKILL на ровно60.000.

`integration.patch` не применён: модульный C++-вариант лежит в `integration/solver`;
его склейка побайтно равна проверенному `artifacts/robust_v1.cpp`.
`anchor_integration.patch` не применён: меняет только offline-функцию support в colgen,
которую импортирует исследовательский local_mip. Оба патча проходят `git apply --check`
на зафиксированной рабочей базе. На другой ветке сначала сверяйте baseline hashes.
