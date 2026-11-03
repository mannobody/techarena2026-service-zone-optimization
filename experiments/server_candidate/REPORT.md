# Кандидат для серверной проверки: методы и аллокации

18 октября 2026. Ветка `research/colgen-research`, без коммитов и push. Ничего не удалялось.

## Состав

Сохранены power diagrams со свободными генераторами/весами, дорожные/секторные/
гильотинные старты, lazy office search, DP выбора сайтов/окна нагрузки, многопоточный
LNS с переразрезами двух зон, отжиг, элита и balanced level-fill. Включены ранее
проверенные worker DFS и genetic office-subset warm start. Runtime — C++17,
стандартная библиотека, instance.json → solution.json, default 280 с, без сети и кешей.

Добавлен `solver/finish.h`: после join всех потоков использует оставшийся хвост
времени. При alpha=0 выбирает оптимальные profit-prefix в count window внутри
фиксированных прежних оболочек/команд, разрешая закрытие bottleneck office.
Затем пробует допустимые следующие офисы при геометрическом отказе лучшего дорожного.
Изменение публикуется только при улучшении и полной проверке. Бюджет до
`limit−max(0.5,0.002*limit)`; основной поиск ради этого не сокращается. Если хвоста
нет, оператор пропускается. Флаг `FINAL_POLISH=0` отключает его.

UMAP/t-SNE, entropic OT, soft affine-profit, полный memetic GA и SCIP/column-generation
прототипы не включены: устойчивого выигрыша в этом портфеле они не показали.
EXACT2 по-прежнему доступен через `EXACT2=1`; включение по умолчанию не подтверждено
общим выигрышем. Новый архив не требует ручной установки флагов.

## Оптимизация памяти

- `solver/fast.h`: повторно используются per-thread cells, profits, маски, списки
  сайтов и prefix buffers. Матрица allow плоская, индексная сортировка сохраняет
  прежний порядок при равенстве. Состояние очищается перед каждым вызовом.
- `solver/geom.h`: scratch для монотонной цепи; готовая оболочка записывается в
  существующий вектор вместо передачи временного большого allocation.
- `solver/sol.h`, `solver/engine.h`: буферы построения/вставки оболочки сохраняют
  capacity; greedy workers и каждый уровень DFS используют отдельные повторные
  buffers. DFS frames heap-owned: рост индекса глубин не инвалидирует ссылки.
- `solver/evolution_warm.h`: повторные masks/permutation buffers и ссылки на
  родительские геномы вместо ненужных копий Cand. Все scratch независимы по потокам.

`profile.cpp` считает вызовы operator new после прогрева на фиксированном объёме
работы: 384 Fast.evaluate с 64 разными наборами офисов, включая получение members;
5000 hull_of по 500 точкам. Четыре синтетических входа, три повтора; checksum
вычислений старой/новой версии совпадает во всех случаях.

| Вход | Fast allocations до → после | Hull allocations до → после |
|---|---:|---:|
| huge0 | 166793 → 5 | 5000 → 0 |
| huge1 | 137712 → 0 | 5000 → 0 |
| multiskill2 | 35388 → 0 | 5000 → 0 |
| tightA0 | 39570 → 0 | 5000 → 0 |

Это число выделений, не процент прироста throughput. Wall microbenchmark шумит
из-за совместных измерений и нагрузки: например Fast huge0 медиана 1.188→1.514 с,
multiskill2 0.028→0.010 с. Отдельный `/usr/bin/time` CPU/RSS контроль и порядок
before/candidate, затем candidate/before сохранён в `logs/cpu_profile.json`.
Снижение allocations доказано на этом объёме; устойчивое ускорение всей эвристики
и увеличение hidden score пока не доказаны.

## Проверки

- 34681 независимых worker oracle задач, включая 80 навыков: 223 false negatives
  прежнего greedy, 0 у bounded fallback на выборке; ложных true нет.
- Territory witness: 21→60, число сайтов 2/2/2→4/4/0; полная native verify.
- Retry fill: covered 300→390, uncovered 400→490, journal rollback; native verify.
- Собранный из ZIP-layout Makefile бинарник без аргументов, 21 edge/синтетический
  вход, TL2 NT2: 21/21 VALID; max wall 4.872 с. Только instance.json/solution.json
  в рабочем каталоге. Первая версия теста retry неверно вызывала старый greedy
  вместо нового finish_fill; тест исправлен, production код не менялся.
- Штатный bench.py10 --synth: все 28 решений валидны, но gen10 получил TIME
  (13.5 с при пороге 13 с) под конкурентной нагрузкой. Повтор gen10: 11.5 с,
  прошёл. Это ограничение короткого wall теста; скрытый TLE не исключён проверками.
- A/B 12 с, NT2, 8 задач × 3 зерна × before/candidate: 48/48 VALID.
  Дельты медиан: alphazero2 +3.065%, anti3 +0.121%, multiskill0/2 0%,
  tightA0 −0.418%, large2 −3.478%, huge1 −8.446%, huge0 −30.898%.
  Эти регрессии не скрыты и не объявлены шумом. Очень короткие фазы запуска
  чувствительны к wall scheduling; поэтому отдельно повторены большие случаи
  за 30 с с явно пересобранной базой теми же `g++ -O2 -std=c++17`.
  Данные и окончательные цифры повторов — `logs/large30/results.json` и
  `logs/SUMMARY.json`. Кандидат предлагается для экспериментального серверного
  измерения, а не как доказанно более высокий итоговый рейтинг.

Проверки проводились на синтетике `experiments/clustering/data` (seeds61000+,
46 задач штатной SUITE), edge-наборе и holdout из evolution. Открытые примеры
не читались, настройки от их результатов не зависят. 300-секундная серия не запускалась;
проверку всех 11 скрытых тестов должен дать сервер. В зачёт идёт последняя посылка.

## Полные пути и воспроизведение

Архив для отправки:
`./experiments/server_candidate/artifacts/case03_cpp_server_v2.zip`.
В корне только `Makefile` и `main.cpp`; компиляция `make build`, запуск `make run`.
SHA и проверка соответствия текущим production исходникам:
`./experiments/server_candidate/MANIFEST.json`.

Основной код —
`./solver/`.
Предыдущие исходники и бинарник до этого этапа —
`./experiments/server_candidate/before/solver/`,
`./experiments/server_candidate/artifacts/before.cpp`,
`./experiments/server_candidate/artifacts/before`.
Сборка текущего кода и упаковка —
`./experiments/evolution/build_current.py`,
`./experiments/evolution/package_current.py`.
Benchmarks, profile, tests —
`./experiments/server_candidate/bench.py`,
`./experiments/server_candidate/bench_large.py`,
`./experiments/server_candidate/profile.cpp`,
`./experiments/server_candidate/test_fill.cpp`,
`./experiments/server_candidate/test_territory.cpp`.
Сырые логи и сводка —
`./experiments/server_candidate/logs/`;
JSON `profile.json`, `cpu_profile.json`, `worker_oracle.json`, `repeat12/results.json`,
`large30/results.json`; stdout штатных/упаковочных проверок сохранён отдельно.
Исходные данные —
`./experiments/clustering/data/`,
`./experiments/evolution/data/`.

```sh
/tmp/ta-colgen-venv/bin/python experiments/evolution/build_current.py
/tmp/ta-colgen-venv/bin/python experiments/evolution/package_current.py --tag server_v3
/tmp/ta-colgen-venv/bin/python experiments/server_candidate/bench.py
/tmp/ta-colgen-venv/bin/python experiments/server_candidate/bench_large.py
/tmp/ta-colgen-venv/bin/python experiments/server_candidate/summarize.py
```

Для новых измерений выбирать новые tags/каталоги, чтобы сохранить старые логи.
Следующий шаг после сервера — разбор регрессий крупных режимов и профилирование
целого LNS, включая стоимость геометрии/DP, а не дальнейшее сокращение new ради new.

## Итог повторов 30 с

8/8 VALID, NT2, по два зерна на двух больших задачах. huge0: 317398.752→317398.752 (+0.000%); huge1: 3907.965→3904.247 (-0.095%).
Разница с 12-секундным A/B показывает чувствительность короткого старта и важность
явно пересобранной базы. Нельзя объявить все короткие регрессии исправленными
или эти два случая доказательством общей эквивалентности.

Поле wall в large30 включает последующую Python validation; оно не равно времени
работы самого solver. В repeat12 wall измерен до validation. Сравнение качества
использует одинаковый переданный solver limit; CPU profile измерен отдельно.

## Версия O3 по просьбе пользователя

Исходный C++ побайтно совпадает с server_v2; в Makefile заменён только `-O2` на `-O3`.
Сборка `g++ -O3 -std=c++17 -o solution main.cpp`.
Готовый ZIP:
`./experiments/server_candidate/artifacts/case03_cpp_server_v3_O3.zip`.
SHA256 `b40fc3a499a8a3b4aeb5067ebe993b4e505f1fd1a9349bfea7f5f0f85041d959`.
Изолированные запуски с contest filenames, TL2 NT2: **21/21 VALID**, max wall2.644с.
Это проверка допустимости/упаковки; оценка прироста скорости или score от O3
отдельным A/B не проводилась.
Логи:
`./experiments/evolution/logs/server_v3_o3_package/results.json`.
Хеши:
`./experiments/server_candidate/MANIFEST_O3.json`.
Воспроизведение:
`/tmp/ta-colgen-venv/bin/python experiments/evolution/package_current.py --tag server_v3_o3 --optimization O3`.
Предыдущий O2 ZIP сохранён. Коммитов нет.
