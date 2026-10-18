# Идеи (10-18)

Обзор методов в ширину. Перед реализацией — `EXPERIMENTS.md` (отброшено: цены π в поиске, одиночный перенос).

## Не проработано
- **Колонки-зоны.** Set packing по допустимым зонам (офис + «чистое» выпуклое множество) из элиты и истории LNS;
  мастер — свой B&B или локальный поиск на графе конфликтов. Column generation с ценами — ещё и оценка жёстче `bound.py`.
- **Геометрия.** Ремонт разделимости двух кластеров по дорогам (вращающаяся развёртка O(n² log n));
  разрез тройки зон двумя прямыми / «веером»; power-граница вместо прямой; перебор двумя прямыми на ≤ 3 офисах.
- **Power diagram / OT.** Веса Ньютоном (Kitagawa–Mérigot–Thibert) вместо координатного спуска; unbalanced OT
  (сайты можно не брать); CMA-ES по (h, G) с честной целью; centroidal (Ллойд) как конструктор; MDS дорожных расстояний.
- **Баланс.** Окно [lo, hi] через min-cost flow; цепочки и циклы переносов (VLSN, Ahuja); strategic oscillation.
- **Навыки.** b-matching / max-flow «рабочие → (офис, навык)» инкрементально; дефицитные навыки — Венгерский/аукцион.
- **Поиск.** Path relinking, parallel tempering, LAHC / great deluge, бандит по стратегиям и конструкторам.

## Проработано (цифры — `EXPERIMENTS.md`)
- Merge по зонам → `XOVER`, ALNS → `ALNS` (оба вкл., suite +0.5% каждый).
- Optimal islands DP — отложено: с ёмкостью вес острова неаддитивен, без неё ≈ «переразрез + DP».
- Зоны, не разделимые прямой, частично достижимы через ruin & recreate и одиночные ходы.
- **Бассейны** (главный остаток потерь на малых/средних: anti3, small3, grid1) → `OVNS` + `CHUNK=0.04` (за флагами,
  suite +1.15% до исправления счётчика); `OSWAP` слабее.

## Источники
- Capoyleas, Rote, Woeginger — Geometric clusterings; Caplan — power diagrams for semi-discrete OT (arXiv 2106.14730);
  generalized Laguerre diagrams (arXiv 1808.01962); capacitated clustering by OT (arXiv 1602.08156);
  centroidal power diagrams (arXiv 2509.06903); capacitated districting (INFORMS JoC 2022);
  balanced k-means через min-cost flow (AIIPCC 2025); HA-CCP (PMC8799340).
