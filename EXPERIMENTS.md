# Журнал экспериментов

Читать перед работой над решателем. Строку **дописывать в конец** (при конфликте оставить обе).
Цифры — `python3 bench.py <сек> [--runs N --base origin/main]`, `--suite` или комментарий CI. Посылки NSUTS — `results/nsuts.md`.
Нормировка suite — среднее / лучшее известное (`results/local/suite_best.csv`); медиана — с `--agg median`.

| дата | ветка | идея | результат | вердикт |
|---|---|---|---|---|
| 10-16 | — | Вороной по евклиду + отжиг (v1) | inst0..4: 4941312 / 30.10 / 5.63 / 125675 / 15597 | база |
| 10-16 | — | MIP без геометрии → снять конфликтные сайты (inst3) | 124 из 341 точки в двух оболочках | ремонт дорогой |
| 10-16 | — | power diagram с подбором весов h; свободные генераторы G | +4–15%; ещё +0.02–3% | принято |
| 10-16 | — | лимит 270 с вместо 60 с | < +1% | время не узкое место |
| 10-16 | cpp-solver | перенос на C++ | 5160009 / 32.20 / 5.63 / 135636 / 18005 (60 с) | принято |
| 10-16 | lns-rewrite | гильотина, стратегии у потоков, фиксация набора офисов, случайный план навыков, широкий перебор наборов | ±0.5% (шум) | в портфеле; не повторять без причины |
| 10-16 | lns-rewrite | inst3: принудительно 6 офисов с лучшей оценкой | 101569 против 135989 | зазор геометрический |
| 10-16 | lns-rewrite | лагранжева оценка `tools/bound.py` | доля 97.3 / 97.0 / 100 / 63.4 / 89.5% | диагностика; цены π в поиске — шум |
| 10-16 | lns-rewrite | одиночный перенос сайта между зонами | 76k итераций, 2 принято | бесполезен |
| 10-16 | lns-rewrite | переразрез двух зон прямой + точный DP подмножества + потоки | 5164995 / 32.23 / 5.63 / 137539 / 18226 (280 с) | принято |
| 10-16 | lns-rewrite | `try_open_office` с расчисткой места | inst4 +1.15% | принято |
| 10-16 | lns-rewrite | `greedy_fill`: выгодные допустимые сайты оставались неназначенными | gen5 +8.4%, gen3 +2.6% | принято |
| 10-16 | lns-rewrite | многопрофильные: `cntSkill[k] ≤ N_k` не достаточно → проверка назначением | ms0 +71%, ms2 +27% | принято, критично |
| 10-17 | repo-cleanup | `SEED`, `bench.py --runs/--base/--synth`, edge-набор `tools/gen.py` | всё VALID; перелёт лимита растёт с потоками (TL=10 NT=4 +4.9 с) | на 280 с запаса хватает |
| 10-17 | repo-cleanup | > 1500 сайтов: время в `lns` проверялось раз в 64 итерации, `hardcap` пускал ход за `tend` | gen10 NT=1 TL=15: 16.4 → 14.7 с | принято |
| 10-18 | suite | `bench.py --suite`: 46 инстансов, 12 классов; калибровка `main` 30 с × 3, NT=1 | huge 0.841, multiskill 0.968, tightA 0.982, прочие ≥ 0.989; итого 0.985 | главное мерило |
| 10-18 | exact2 | `main` против решателя до lns-rewrite, 41 инстанс, 30 с | не хуже на 40/41 (до +24%), s13 −0.46% | старый в портфель не нужен |
| 10-18 | exact2 | `EXACT2=1`: точный перебор 1–2 офисов, поток ≤ 30% лимита, ≤ 600 сайтов | inst1/2 = рекорды за 0.7 с; s* +0.6…10%, худшее −0.7%; suite +0.05% (шум) | за флагом; решение только в элиту и в ответ (как глобальное лучшее стягивало потоки, s10 −9%) |
| 10-18 | stability | huge1: жадный выбор офисов обрывался по `t_outer` на 8 офисах | `LAZY` (ленивый жадный + размеры ±2): huge1 +10/+22%; suite +1.8…2.1%, huge +8…16% | вкл. по умолчанию (`LAZY=0`) |
| 10-18 | multiskill | `WFIX`: `realize` брал сайт с новым навыком, даже если `greedy_workers` не раздаёт рабочих (старты с ≥ 5 офисами невалидны) | multiskill2 32–37 → 42.2; suite multiskill +6.1% | вкл. (`WFIX=0`) |
| 10-18 | ideas2 | `LEVEL`: `level_fill` — по сайту каждой зоне минимального размера, целиком (при A=0 одиночное добавление ломает баланс) | tightA +2.6%, small +1.0, итого +0.38% | вкл. (`LEVEL=0`) |
| 10-18 | ideas3 | сетка точек `Inst::for_box`, инкрементальное покрытие, `begin_defer` (`apply_cov` было 45% времени) | итераций LNS ×3–4 на large/huge; suite +0.28% | принято |
| 10-18 | ideas3 | `ALNS` v2: вероятности ходов по очкам в секунду, очки 33/3, p = ½ базовое + ½ адаптивное (v1 Ropke–Pisinger схлопывается, p=0.88) | suite NT=1 +0.53%, все классы ≥ −0.16% | вкл. (`ALNS=0`) |
| 10-18 | ideas3 | `XOVER`: ruin «пересадить 1–3 зоны элитного решения» (12% разрушений) | suite NT=1 +0.54% | вкл. (`XOVER=0`) |
| 10-18 | ideas3 | `ALNS+XOVER` вместе, 60 с × 3, `--par 8` (NT=2) | +0.34%: anti +3.2, alphazero +0.6; grid −0.4 (бассейн) | вкл. по умолчанию |
| 10-18 | ideas3 | методика: huge на 30 с меряет число офисов, которое успела фаза 1 (бимодально 0.91/0.99) | — | huge мерить ≥ 120 с |
| 10-18 | ideas3 | потоки по измеренной параллельности (квоту `--cpus` affinity не видит); фаза 1 на nth потоках | CPUQuota=200% → 2 потока; huge0 фаза 1: 10 → 12 офисов | принято |
| 10-18 | basins | диагностика разброса малых: бассейны = набор офисов. main 280 с × 8 зёрен NT=2 | anti3 0.889 (5/8 в {0,2}=26.0 против {0,2,3}≈29.7), grid1 0.998, medium0 0.990, small3 0.996; tightA0/alphazero0 ±1% внутри одного набора | см. ниже |
| 10-18 | basins | `OVNS=1`: каждый 2-й раунд потока — сосед лучшего по набору офисов (drop/add/swap, без повторов, `office_neighbor`), ≤ 3000 сайтов; `CHUNK` — доля лимита на раунд (0.12); `OSWAP=1` — в ruin «открыть офис» заодно закрыть ближайший открытый. 280 с × 4, anti3/grid1/medium0/small3 | OVNS 0.969/0.996/0.988/0.992; **OVNS+CHUNK=0.04 0.948/1.000/0.997/1.000**; OSWAP 0.910/0.996/0.997/1.000 | лучшая связка OVNS+CHUNK |
| 10-18 | basins | `--suite` 120 с × 2, NT=2: OVNS+CHUNK=0.04 против main | итого +1.15%: anti +11.1, alphabig +0.9, huge +0.6, medium/small +0.4; large −0.5 (large3 0.972 против 0.998) | ошибка, исправлена ↓ |
| 10-18 | basins | причина large3: принудительные раунды занимали нечётные `round`, а старт выбирается `rank[round % 6]` → rank1/3/5 не стартовали (на large3 лучший — rank1). Отдельный счётчик `iter`. Отдельно CHUNK=0.04 на large3: 1335/1334 против 1328/1326 | после исправления 120 с × 2: large3 1.001/1.000, large2 0.999/1.001, anti0/1 ≈ 1.0, anti2 0.90/0.88, anti3 0.985/0.938 | за флагами (по умолч. выкл.); полный suite с исправлением не прогнан |

## Открытые вопросы

- Бимодальность зёрен — промах набора офисов: `fast.h` занижает большие наборы (жёсткий maxDifference, anti),
  оценка соседа в OVNS (короткий LNS из возмущённого решения) вдвое ниже истинной — соседи почти не принимаются.
  ALLOPS лечит tightA3/anti; alphabig2 (9 офисов вместо 8 при огромном α) ещё бимодален. `results/local/bimodal/`.
- huge: с `LAZY` разброс зёрен huge1 ещё 4.5%; гипотеза `fast.h:84` (дефицитный навык только топ-`N_k` зонам) не проверена.
- tightA0: разброс ~1% внутри одного набора офисов (`simple_workers`), не разбирали.
- Эталон (10-20, `tools/ref.py`): реальный зазор только в huge и alphabig. TLEVEL на 600–1800 с дал +3% на huge0/alphabig0,
  а suite 120 с звал его шумом — проверить на 280 с × 4 зерна; если подтвердится, включить по умолчанию.
- Шум мерила: large/huge при 30 с × 3 дают ±2.5% без изменений кода — больше зёрен/времени.
- inst1 и inst4: зазор 3% и 10% до оценки, геометрия, видимо, не главное.

## История исследований v4/v5 (Codex)

| дата | автор | ветка | идея | результат | вердикт |
|---|---|---|---|---|---|
| 10-18 | Codex | research/colgen-research | Интеграция worker DFS + genetic office start | Синтетика: 30 с NT4 × 3 зерна, 8 задач; huge0 +13.687%, huge1 +24.481%, large2 +16.250%, multiskill0/2 +5.032/+7.580%, anti3 −1.020%; 48/48 VALID. Official synth28/28, package21/21 | Встроено; без коммита. experiments/evolution/REPORT.md §9; integrated_v1.zip |
| 10-18 | Codex | research/colgen-research | Road profiles/PCA/spectral/UMAP/t-SNE, balanced LP, entropic Newton, affine soft profit, territory MIP | Новые seeds61000+: short huge gains +40–55% не держатся на30с; soft 30с NT4 ×3: huge0 −2.921%, large0 −1.546%, anti3 +2.007%. Territory IP tightA0 +1.50% к matched, 2с IP после5с NT1 | Новые кластерные defaults не включены; см. experiments/clustering/REPORT.md. Перспективен territory/boundary LNS |
| 10-18 | Codex | research/colgen-research | Серверный кандидат: reuse Fast/hull/worker/warm buffers + monotone final territory/fill | 384 Fast calls: alloc166793→5 huge0, hull5000→0; checksum совпал. Oracle34681, package21/21, A/B12с48/48 VALID; короткие huge регрессии, дополнительно O2 large30с8/8 VALID. Synth28 valid, gen10 TIME13.5с, повтор11.5с | Экспериментальный ZIP server_candidate/artifacts/case03_cpp_server_v2.zip; полный отчёт experiments/server_candidate/REPORT.md; без коммита |
| 10-18 | Codex | research/colgen-research | server_v3_O3: тот же C++ с -O3 в Makefile | 21/21 package VALID, TL2 NT2, max wall2.644с; score/throughput A/B не проводился | По просьбе пользователя; experiments/server_candidate/artifacts/case03_cpp_server_v3_O3.zip; прежний O2 сохранён |
| 10-19 | Codex | research/boundary-beam-research | Native boundary B&B/beam, core CP-SAT/SCIP, tail placement | 60с NT2 ×3: tail 72/72 VALID; N≤1500 9 задач mean/median +0.330/+0.244%, худшая пара −8.806%, собственный tail 20/27 wins. Независимый early-wide 48/48 VALID, mean −0.116%, worst median −2.927%. Oracle96/96, CP24/24 | Основной solver сохранён; experimental boundary_tail_experimental_O3.zip и integration.patch; experiments/boundary_beam/REPORT.md. Без коммита/отправки |
| 10-19 | Codex | research/boundary-beam-research | Deep geometry: islands/depth, anchored rank4 cuts, exact binary64 predicates, grid | 60с NT2×3: grid holdout60/60 VALID mean+0.4365%, exact holdout60/60 mean+0.4236% median−0.0204%, worst pair−10.875%; precision3×20→80; candidate55/55 VALID. Local SCIP anchored15/15 VALID: fresh anti+0.1843%, latent+0.0737%, conditional optimal24.4/40.5с vs old60с timeout. Shape operators weaker than control B&B | Main unchanged; geometry_islands/REPORT.md, 2 optional patches, geometry_exact_experimental_O3.zip; no commit/submission |
| 10-19 | Codex | research/boundary-beam-research | v4 O3 по запросу: allocation reuse v3 + exact geometry/grid + final boundary B&B24 | Package60 NT2 SEED101:36/36 VALID, max wall59.803с; B&B oracle96/96. Без заявления общего превосходства компонентов | experiments/server_v4/artifacts/case03_cpp_server_v4_O3.zip; MANIFEST.json/README.md. Main сохранён, без коммита/отправки |
| 10-19 | Codex | research/boundary-beam-research | DP window O(KGlogG), gcd; SCIP/HiGHS conditional selection/count/territory/workers | TL60 NT2 ×3 fresh:60/60 VALID mean−0.8792%, median0%, worst−8.6459%; edge21/21. Native10k81.2→34.5мс; gcd skip→opt14.1мс. MILP count90→130; HiGHS10k+0.3877% vsDP at60с without proof. Oracle3000 window,40 SCIP,40 HiGHS;35 MIP outputs validated | v4 frozen, DP not promoted; experiments/dp_milp/REPORT.md, optional patch, MANIFEST/PATHS. External60 cutoff cleanup≤0.117с. Main unchanged; no commit/submission |
| 10-19 | Codex | research/boundary-beam-research | v5 MILP: safe envelope growth, grouped integer counts/continuous profit, worker profiles; lazy HiGHS C API tail | TL60 NT2×3 fresh final:60/60 VALID, mean+0.1945%, median+0.0112%, worst-2.5692%; own MIP16/30 improvements; package26/26, oracle Python80+native60. Fixed-inc alpha+1.91095%/.041s, tightA+.59033%/.218s. Max candidate wall60.149s (soft timer). Earlier independent +.3586% and −.3173% preserved | Experimental only; experiments/milp_v5/REPORT.md and artifacts/case03_cpp_server_v5_milp_lazy_O3.zip. v4/main solver unchanged; no commit/submission; boundary-variant master specified, not yet implemented |
| 10-19 | Codex | research/boundary-beam-research | v5.2 regional perspective MILP: pair/power envelopes, transfers, optional joint office/workers; late 2s cooperative call | TL60 O3 NT2 ×3 fresh:60/60 successful VALID, mean+1.2517%, median+0.0025%, worst−0.9135%, wins/ties/losses15/4/11; own stage22/30. Package26/26, fallback2/2, oracle120 comparisons on30 tiny cases. Empty-office generator RE reproduced/fixed; failing prior series retained. Max wall60.199s, RSS47.961MiB NT2 | Experimental, not promoted; milp_v5_boundaries/REPORT.md, case03_cpp_server_v5_2_regions_safe_experimental_O3.zip. Mean sensitive to large wins; early call−2.8687% rejected. Old v4/v5 and main unchanged; no commit/submission |
| 10-19 | Codex | research/service-zone-v4 | Перенос замороженной v4 в основной solver, O3 и документация | Payload побайтово совпал с v4; ZIP пересобран. Synth10 NT3:28/28 VALID; A/B60 NT3 ×3 против 6878393: inst0 +0.00%, inst1 +0.00%, inst2 +0.00%, inst3 +0.17%, inst4 +0.34%; benchmark rc0. Max wall кандидата 59.8с | В этой проверке регрессий более 1% по медианам не обнаружено; дополнительное подтверждение качества выполняется в CI при открытии PR. docs/v4.md; без staging, коммита и отправки |
| 10-19 | Codex | research/service-zone-v4 | Разрешение конфликтов v4 с main e600dde: точная геометрия + кеш/defer, genetic + parallel phase1 | Geometry state25600/25600; synth10 NT2:28/28 VALID; A/B60 NT2 ×3:30/30 процессов rc0, head15/15 VALID, inst0 +0.00%, inst1 +0.00%, inst2 +0.00%, inst3 +0.00%, inst4 -3.67%; max wall 59.832с. ZIP rebuild OK | Регрессия >1%: критерий качества main НЕ выполнен; Изменения main сохранены, O3; docs/v4.md. Без коммита/push; качество на скрытых не доказано |
| 10-19 | Claude | claude/mannobody-warm-budget | v4: жадный выбор офисов снова до 22% лимита (≤60 с), генетика — только остаток (было 10%/30 с) | suite 120 NT2 ×2: v4 к 76d51ba +0.85% (anti +8.0, multiskill +2.4, huge −4.65); WARM_BUDGET к main +0.32%: huge +4.31 (0.944→0.988), anti +1.46, прочие классы в пределах ±0.3%. synth10: всё VALID |
| 10-19 | Claude | claude/mannobody-ovns-default | OVNS=1 и CHUNK=0.04 по умолчанию (поверх WARM_BUDGET) | suite 120 NT2 ×2 к HEAD: +0.52%, ни один класс не просел: anti +2.79 (anti1 0.887→1.0), tightA +1.58, alphazero +0.38, alphabig +0.35, huge +0.08. 280 с, сборка из zip, 2 ядра: huge0/1 VALID, wall ≤ 277.8 с. synth10: всё VALID |
| 10-19 | Claude | claude/mannobody-allops | ALLOPS: набор «все офисы» в портфель, второй в очереди глубоких прогонов (LNS сам закрывает лишние) | разбор 8 зёрен: tightA3 7/8 и anti2 5/8 в плохом наборе офисов; 4 зерна: tightA3 4355–4651 → 4856–4882, anti2 все зёрна ≥10444. suite 120 NT2 ×2 к main: +0.26% (= среднее по зёрнам), tightA +1.98 (tightA3 0.90→0.98), anti +0.50, grid +0.19, alphabig +0.20; cluster −0.09, multiskill −0.04, deficit −0.03 (шум). synth10: всё VALID | По умолчанию, ALLOPS=0 — выключить |
| 10-19 | Claude | claude/mannobody-tlevel | TLEVEL: `task_level_fill` — поднять все зоны до общего числа задач T+δ разом (при большом α одиночное добавление невыгодно) | 60 с ×2: alphabig2 0.913/0.957 → 0.956/0.989, alphabig0/1/3 шум. suite 120 NT2 ×2 (среднее) к main: итого +0.02%; alphabig2 0.939→0.947 (зёрна 0.92/0.97 — бимодальность осталась), tightA +0.29, grid +0.19, huge −0.32 | Шум; флаг TLEVEL=1, по умолчанию выкл. bench --suite теперь нормирует среднее (как жюри) + «хз» |
| 10-20 | Claude | claude/mannobody-ref | Эталон suite `tools/ref.py`: 46 инстансов × 3–4 конфигурации (default/TLEVEL/EXACT2/default, зёрна 101–104), 600 с (≤600 сайтов) / 900 с (≤3500) / 1800 с (huge), NT=2; поднимает `suite_best.csv` | 146/146 VALID. Прежнее лучшее / эталон: huge 0.974 (huge0 0.950), alphabig 0.991 (alphabig0 0.966), large 0.999; остальные 9 классов 1.000 (лучше не нашлось). Рекорды huge0 и alphabig0 — TLEVEL, отрыв +3% от прочих конфигураций (huge0 477459 против 460–463 тыс.; alphabig0 19.60 млн против 18.98–18.99) | Зазор только в huge/alphabig; малые сошлись. TLEVEL проверить на 280 с × 4 (alphabig, huge, large). Цифры `--suite` после этого ниже: поднята база |
| 10-21 | Claude | claude/mannobody-setrace | Точная модель всей задачи на CP-SAT (`tools/exact_cpsat.py`): геометрия точно — q в оболочке зоны ⇔ есть её сайты слева и справа от луча q→офис с разностью углов ≥ π («лестница», O(n) булевых на пару точка×зона); 17 малых, подсказка — лучшее из `results/local/ref` | 14/17 — доказанный оптимум = наше лучшее (inst1, inst2, small0–3, tightA1, grid1/2, deficit1/2, cluster3, thin3, scarce1/2). tightA2 46.9988 против 46.877; tightA0 8.9708 (= MIP); **inst4 18933.915 против 18226.33 (+3.88%)**, валидно, оболочки не пересекаются | На малых поиск не слаб; зазор — в другом |
| 10-21 | Claude | claude/mannobody-setrace | inst4: `FORCE_OPS=0,2,3,4` + новый отладочный `FORCE_PLAN=0:0,2;2:1,3,4;3:0,2;4:1,2,4` (разрешённые навыки офисов) | 30 с NT=2: 18933.915 (2 зерна из 3), 18889.6; только FORCE_OPS — 18094–18890 (нестабильно); по умолчанию — 18226 у всех зёрен | Внутренний LNS в порядке; проигрывает внешний выбор «набор офисов × раздача рабочих». Все 10 рабочих заняты: офису 3 надо сразу забрать навык 0 у офиса 4 и навык 2 у офиса 2 |
| 10-21 | Claude | claude/mannobody-setrace | CP-SAT-LNS (`tools/cplns.py`): из нашего решения освобождаем k соседних офисов (откр./закр.), подзадача точно | inst4: k=2 — 0 улучшений (наше решение 2-зонно-оптимально), F={2,3,4} — сразу 18933.915 (OPTIMAL за 41 с). **inst3: из нашего 280 с (146 230, {0,5}) k=2 → +28; из best3 (137 539) k=3 → 155 896.5 (+6.6% к нашему 280 с)**, набор {1,5,7}. inst0: 5 165 504 → 5 174 079 (+0.17%). Suite 10 мин: tightA3 +0.45%, medium2 +0.003%, прочие 13 — 0 | Нужны ходы глубины ≥ 3 зон (связь через баланс A, α по задачам и рабочих). Suite почти не воспроизводит эти структуры |
| 10-21 | Claude | claude/mannobody-setrace | Оценщики наборов: Fast, план с ёмкостью, MIP без геометрии | Fast: inst4 {0,2,3,4} 15 820 (истинно ≥ 18 934, −16%); inst3 {1,5,7} 77 836 (≥ 155 896, −50%: при «обратных» расстояниях выгодная территория далеко от офиса, а спуск по (h,G) стартует с генераторов в офисах). MIP без геометрии верно ставит {0,2,3,4} первым на inst4, но на inst3 потеря на геометрию 22–35% между наборами — ранжирует неверно | Ни один дешёвый оценщик не ранжирует наборы на anti |
| 10-21 | Claude | claude/mannobody-setrace | SETRACE (у набора своё лучшее, раунды продолжают его запертым, successive halving); RSBAL (размеры половин в переразрезе внутри окна баланса); PLANCAP (`plan_value` с maxSize и s_min+A); FASTPLAN (локальный поиск плана внутри Fast::evaluate) | inst4 60–120 с NT=2: 18161–18192 / 18162–18192 / 18164–18226 / Fast {0,2,3,4} 15 803 — все не лучше main (18226) | Отброшены, из кода убраны |
| 10-21 | Claude | claude/mannobody-setrace | HiGHS 1.15 (есть в образе жюри) на той же 3-зонной подзадаче, 2 потока | inst4: 44k перем./112k строк — 18 852 за 120 с, за 10–30 с хуже старта; inst3: 168k/467k — ничего за 30 с (CP-SAT 8 потоков — секунды) | MIP-ходы в посылке непрактичны; многозонные ходы — нативно |
| 10-21 | Claude | claude/mannobody-setrace | STRIPES (по умолчанию): при корреляции d[o][s] с евклидом < 0.3 («обратные» расстояния; у anti/inst3/off3 −0.82…−0.96, у всех прочих suite/inst/off4 ≥ +0.83) — конструктор 6 «параллельные полосы» (граница — середина между проекциями соседних офисов на θ; полосы выпуклы, офис внутри своей) + 3 набора из кэша фазы 1, лучшие по `stripe_estimate` (32 направления, прибыльные сайты до min(maxSize, s_min+A), выравнивание задач при α>0) | Без признака suite 120 NT2 ×2: итого +0.16% (anti +0.54, scarce +1.28), но large −0.17% (скан кэша 2.4 с в одном потоке + разбавление фазы A: large3 114/175 связок). С признаком (вне anti путь = main) 120 с NT2 ×2, main → STRIPES: inst3 145.6k → 155.6k (+6.8%, зерно 163 337 > CP-SAT-LNS 155 896), off3_1 79.8k → 114.6k (+44%), off3_3 +3.9%, off3_4 +10.8%, off3_2 −0.2%, anti0 +2.1%, anti1–3 = main. synth 10 (и со STRIPES=2) — всё VALID | Влить. Признак «оценка полос > Fast» отвергнут: оценка полос без навыков, включалась на deficit/grid/tightA и зависела от размера кэша. `STRIPES=0` — выключить, `2` — без признака |
| 10-21 | Claude | claude/mannobody-stripes | STRIPES: 280 с NT=2 ×3 зерна и остаточный зазор (CP-SAT-LNS k=3, 10 мин, из лучшего зерна 120 с) | 280 с (main 280 с → STRIPES, среднее): inst3 146.2k → 160.1k (+9.5%; зёрна 166 875 / 165 701 / 147 819 — третье застряло в {0,5}), off3_1 90.7k → 115.0k, off3_2 140.9k → 141.1k, off3_3 122.2k → 126.4k, off3_4 129.9k → 136.7k. CP-SAT-LNS из 120 с: inst3 163 337 → 165 309 (+1.2%), off3_1 +0.7%, off3_2 +2.8%, off3_3 +0.6%, off3_4 +0.2% (до STRIPES было +0.5…15%) | Локальный зазор на anti закрыт до 0.2–2.8%; остаток — разброс зёрен (бассейн набора): глубокий раунд с нуля за ≈11 с даёт 100–145k и не вытесняет рекорд 147.7k, а элита (топ-6 в 4%) заполнена вариациями того же набора |
| 10-21 | Claude | claude/mannobody-stripes | Бимодальность inst3 после STRIPES: ELDIV=k (в элите ≤ k решений с одним набором офисов); CHUNK 0.08/0.12; оценка полос с общим уровнем задач T | Механизм: плохой бассейн — {0,5} (оба офиса упёрлись в maxSize 128/114, 146–148k); хорошие — 4+ офиса с равными задачами по зонам (486×4, 160–167k), созревают за ≈30 с LNS, а глубокий раунд с нуля даёт ≤145k и рекорд не вытесняет. 280 с NT=2: по умолчанию 7 зёрен — среднее 160.0k (2 застряли); ELDIV=1 8 зёрен — 156.0k, ELDIV=2 4 зерна — 155.8k; off3_1..4 ELDIV=1: +0.95/+0.19/−0.51/+0.75% (шум); CHUNK=0.08 — 154.8k, 0.12 — 155.4k (по 4 зерна). Оценка с уровнем T: {0,5} 140.1k, {1,2,6,7} 139.4k (истинно 148k / 163k+) — ранжирование не исправляет | Отброшено. Потенциал многоофисного набора виден только после долгого LNS; дальше — гонка наборов из кандидатов STRIPES с продолжением (свой лучший у каждого), только при «обратной» геометрии |
| 10-21 | Claude | claude/mannobody-tl-safety | Страховка TL: `alarm` limit+14 → limit+5 (294 → 285 с); повод — 0 в одном из трёх прогонов #9 на NSUTS (посылка 49e92fb, похоже TL) | Замер `NT=2`, 280 с, 37 инстансов (thin2 ×9, instance0–4, suite small/grid/tightA/scarce/thin/multiskill/deficit/large/huge): конец 276.5–279.44 с, ни один не дошёл до alarm, пик RSS 215 МБ; переполнения не найдено → остаётся редкое зависание фазы или накладные Docker, 294 с оставляли лишь 6 с. `kill -ALRM` на 80 с (huge0) — валидное решение. Побочно: на huge0 первое решение только на 65 с (large1 37 с) — до этого в файле `[]`. `--synth 10` всё VALID. Оставлено |
| 10-21 | Claude | claude/mannobody-tl-safety | TLEVEL=1 на тонком классе (thin2_1–9, стоимость офиса 0.85–1.0 его автономной прибыли; 280 с NT=2 ×4 зерна, к MIP `bound.py`) | Без эффекта: среднее к MIP 0.9725 против 0.9732 (main, 6 зёрен); ход принимается (thin2_8 60–220 раз, thin2_4 ~3000), но итог тот же — thin2_8 187.2 в 3 из 4 (MIP 210.3, бассейн офисов {0,2,3}). Упор в набор офисов, не в уровень задач. Отброшено |

## Локальный поиск v4, 19 октября 2026

Исследовательская ветка `research/v4-local-search` создана от обновлённого origin/main
`5306583` (solver совпадает с `6d846d1`). Замороженные ZIP v4/v5 не изменены.
Новые методы выключены по умолчанию; коммита, push, merge и отправки нет.

| Идея | Проверка | Результат / решение |
|---|---|---|
| Локальный дедлайн DP, чередование конструкторов, обмены 1↔1/2↔2 | Development TL60 NT2 O3, 8 классов × 3 seed, 96 канонических запусков | local mean+0.1208%, median0; fair−0.8822%; exchange+0.0792%, median+0.0241%, worst−2.1585%; общая победа не доказана |
| Полный ILS и расширенный обход рангов | Отдельные 96 запусков | ILS mean−1.3523%, worst−9.0287%; cover−0.9260%, worst−6.9301%; отклонены |
| Финальный парный обмен | Независимый holdout48, открытые30, huge TL180×3 пары | Holdout mean+1.0612%, median0, worst−8.6162%; huge180 все три пары хуже; не принят |
| ILS/VNS/TS/GWW после фиксированного checkpoint | Ранние и зрелые состояния: по168 проверок операторов NT1×2с | Зрелые медианы0; GWW mean+0.05171% зависит от редкого выигрыша; полного преимущества не заявляем. Исправлен риск размера популяции, 24/24 дополнительных проверок |
| SCIP/HiGHS с геометрическими cuts и переменными назначениями/работниками | 84 сравнения с полным перебором на42 маленьких задачах; два вида окрестности на8 зрелых checkpoint | Выбор по выгоде: нет прироста, 3 нарушения wall-порога. Снятие слоёв оболочек: 32/32 успеха, совпадающие улучшения alphabig/large/cluster |
| Native цикл A→B→free→A, сохраняющий counts и tasks | На фиксированном alphabig повторяет MIP gain2674.688649 примерно за35мс | Общий оператор без зависимости от ID; отдельный ZIP, итоговые A/B ниже в отчёте |
| Повтор inst4 противe600dde | 6 новых seed, 12/12 успехов | Отношение медиан−0.06734%, среднее парных Δ−1.10273%, W/T/L2/0/4. Хороший старый бассейн18869.55 дважды достижим и валиден в новом Engine; исправление регрессии не доказано |

Полные распределения, времена/RSS, причинный разбор и неуспешные серии:
[REPORT](https://github.com/mannobody/techarena2026-service-zone-optimization/blob/ffe5018957b1e3405a7448c8d27057272429cd67/experiments/v4_local_search/REPORT.md),
[таблица](https://github.com/mannobody/techarena2026-service-zone-optimization/blob/ffe5018957b1e3405a7448c8d27057272429cd67/experiments/v4_local_search/RESULTS_TABLE.md),
[методы и первичные источники](docs/v4-local-search.md).
Координаторы двух неполных серий завершились143; журналы сохранены, серии повторены
целиком. Ошибка прежнего офлайн worker-certificate harness (12 rc6) также сохранена;
повтор168/168 успешен. Ничего не удалено; список кандидатов на очистку в исследовании.

Итог цикла: development48/48 — mean−0.3254%, median−0.0401%, worst−8.9308%;
независимый holdout48/48 — mean+0.0860%, median0, W/T/L8/5/11. Расширение до шести
seed на alphabig/large: отношение медиан −1.0489%/+0.2087%. Критерий принятия
не выполнен. Контроль с общего checkpoint «2с boundary» vs «2с цикл+boundary»:
48/48 успешных, W/T/L4/17/3; проигрыш tightA показывает конкуренцию финальных стадий.
Экспериментальный safe-ZIP проверен на28 синтетических и6 файловых запусках;
TL280/O3/C++17, внешних solver в нём нет. Основные defaults сохранены.

## Две лаборатории и интеграция, второй цикл 19 октября 2026

По просьбе пользователя работали две отдельные лаборатории: геометрия и
архитектура поиска. Новая первичная база — точная серверная v4 с исходником
SHA256 `5b3914fa9791cb879f3232fb2876a915de83b848ad4b353b0dbf25b574998c25`.
Модульный solver не подменяет эту базу. Источники, бинарники, входы, времена,
ошибки и фактический NT сохраняются в manifest каждого запуска.

| Направление | Проверка | Вывод |
|---|---|---|
| Count caps и расширение пула в глобальном resplit | 48/48 TL60; exhaustive count oracle | Глобальная замена отклонена: combined mean−0.704%, worst−7.374%; полезный отдельный финальный проход сохранён |
| Геометрия зрелых решений | TL280/TL600; 186 операторных проверок; SCIP и HiGHS | После TL600 новый проход даёт +939.286645 за≈0.118с; условная 66-site MILP-подзадача независимо решена обоими backend; это не глобальная оптимальность |
| Batch, ALNS, archive, niche/crossover, memo, rank coverage | 96 exploratory +40 корректно блокированных TL60; полный TL280 контроль | Batch ускоряет фиксированное remove/undo ядро в3.60–4.04раза; ALNS/niche/persistent-комбинации ухудшают полные результаты и не включены |
| Joint count/load DP | Tiny brute-force32/32, MILP32/32, зрелые native12/12 | Исправляет неполноту load-only+repair; воспроизводит MIP gain11007.487521 на alphabig за≈0.011с при фиксированном staff |
| Конструкторный rollback guard | Повтор24/24 TL60 | mean+0.090%, median0, worst−5.285%; не включён; прерванный первый координатор сохранён |
| Объединение batch+geometry+joint | Development36/36 TL60 | Выбран geometry→joint→boundary: mean+0.741%, median0, worst−1.588%; это выбор кандидата, не подтверждение превосходства |

Новый frozen ZIP проверен без изменения кода на полном TL280, новых
holdout-входах751000+ и открытых примерах. Пересборка ZIP совпадает с frozen
runtime после удаления ELF symbol-table/build-id; source совпадает побайтово.
Синтетика28/28 и файловый протокол6/6 пройдены. Старые архивы не изменены.

Окончательные распределения и решение о принятии опубликованы в
[отчёте интеграции](https://github.com/mannobody/techarena2026-service-zone-optimization/blob/ffe5018957b1e3405a7448c8d27057272429cd67/experiments/v4_deep_parallel/integration/REPORT.md).
Подробности лабораторий: [геометрия](https://github.com/mannobody/techarena2026-service-zone-optimization/blob/ffe5018957b1e3405a7448c8d27057272429cd67/experiments/v4_deep_parallel/geometry/REPORT.md),
[поиск](https://github.com/mannobody/techarena2026-service-zone-optimization/blob/ffe5018957b1e3405a7448c8d27057272429cd67/experiments/v4_deep_parallel/search/REPORT.md).
Все изменения локальные; коммит, staging, push, merge и отправка не выполнялись.

Итог frozen-кандидата: independent holdout60 —72/72 успешных, mean+0,1332%,
median0, W/T/L14/12/10, worst−1,5799%; holdout280 —12/12, mean−0,1765%,
W/T/L3/0/3, worst−2,0007%. Development280 положителен (+0,8896%), но не подменяет
holdout. Открытые20/20: inst0–3 равны, inst4 нестабилен; отдельный follow-up
расширил его до6 seed. Критерий принятия не выполнен, v4 не заменена.
Фиксированные checkpoint с общим3с бюджетом:36/36, новая финальная композиция
даёт6 побед /6 равенств /0 проигрышей; это операторный результат.

Follow-up inst4: дополнительные8/8 успешны, pooled6 seed —mean+0,7125%,
отношение медиан+0,1786%, W/T/L4/0/2, SD3,1888%, диапазон−4,5190%..+4,4096%.
Это подтверждает вариативность, не устойчивое исправление.

## Серверная v6, 19 октября 2026

По запросу пользователя frozen-гибрид второго цикла оформлен как отдельная v6:
`dist/case03_cpp_server_v6_O3.zip`. Исходник и ZIP побайтово совпадают с ранее
проверенным кандидатом; настройки geometry→joint→boundary включены по умолчанию,
TL280. Это версия для серверной проверки, не новый результат качества и не
замена стабильной v4. Сборка из фактического ZIP совпала с frozen runtime после
удаления ELF metadata; 28/28 синтетических случаев прошли официальный валидатор
при запуске без аргументов с конкурсными именами файлов (TL3, NT2).
Происхождение, воспроизводимая упаковка и проверки: `experiments/server_v6/`.
Ничего не коммитили, не отправляли и не удаляли.


## Exact neighborhoods v8, 20 октября 2026

Один агент, точные замороженные server-v4/v8. Пересечение hull без общей входной точки допустимо и уже поддерживается final geometry v8. Реализованы full-domain SCIP/HiGHS G/S с geometry cuts, native B&B, whole-zone atomic packets, full-office fill fallback и ограниченный временем worker DFS без node cap. Найден настоящий worker false negative: полный v4/v8/off36 против нового45 (+25%,3/3seed одного constructed входа); это не общее превосходство.

Независимый frozen TL10 NT2 O3:96/96 VALID, mean к v4−0.106045%, median0, worst−7.848337%. Дополненный до запуска TL60:32/32 VALID,4 тех же входа×2seed×4варианта, mean−0.789370%, median0, worst−6.477530%. Acceptance НЕ пройден; v4 не заменена. TL4 exploratory перелёты до6.4995с сохранены; TL10/60 wall ограничен снаружи и включает overhead. TL280 не запускался.

Материалы: experiments/v8_exact_neighborhoods/REPORT_RU.md, reports/AUDIT_RU.md, FREEZE.json, LONG_PROTOCOL_ADDENDUM.json, FINAL_DECISION.json, COMMANDS_RU.md. Отдельный experimental ZIP main.cpp+Makefile, default280/NT2; byte-identical rebuild, contract63/63 VALID. Старые версии и пользовательский solver/ сохранены; без staging/commit/push/server submit.


## Structural zones v9, 22 октября 2026

Точная server-v4 подтверждена исходником из ZIP (SHA5b3914…); собраны новые контроль/кандидат с одинаковыми O3/std17. Реализованы global whole-zone B&B на малых входах, restricted zone-pool/count×load DP и signed atomic exchanges. 38 exhaustive +15 ручных +55 contract проверок; минимальный joint-DP пример21→110, signed200→299, пересекающиеся треугольники40 VALID.

TL280/NT2: development63/63 успешны; свежая проверка11входов×3seed×2версии —66/66 VALID,65/66 в рабочем допуске (v4 large/9401:281.318с,65.68CPUс; потолок300с не превышен). Выбран tail: mean+2.4308%, median0, worst−0.8043%,15/12/6; без малых mean+0.5640%, case-bootstrap95[+0.1549;+1.1194]. Дополнительный повтор того же large,3seed/2версии/меньший параллелизм:6/6 успешны, mean−0.0636%, worst−1.7555%. Первичные строки сохранены и не заменены. Надёжная общая замена v4 не рекомендована; кандидат экспериментальный, baseline неизменён. Полный master хуже по устойчивости (dev worst−6.2177%); его вклад не приписывается удачным native траекториям.

Материалы: experiments/structural_v9/REPORT_RU.md, AUDIT_RU.md, FINAL_METRICS.json, FINAL_AUDIT.json, FREEZE.json; исходник/пакет candidate_selected.zip и контроль control_v4_nt2.zip. Проверка пакета: побайтно тот же измеренный бинарник,3/3 noarg/file-contract VALID. Чужой solver/ и старые результаты не менялись; build-race QA перенесён в to_delet с MOVES.json. Без staging/commit/push/server submit.


## Warm start v10, 22 октября 2026

Продолжение immutable structural-v9 tail и точной server-v4 SHA5b3914…: геометрические геномы, истинный feasible fitness, два warm-потока, разнообразие назначений, пространственный crossover целых зон и прямая передача стартов в LNS. Дополнительно singleton-invariant shortcut (24/24 точные оценки,9.709→0.140s для подзадачи) и массовая балансировка power cells (механизм20→40 VALID). Все старые версии сохранены, solver/ не переписан.

Выбран v10_v5_geometry; независимые8 новых входов120–10000 сайтов×3seed (включая0)×3версии,TL280/NT2: mean к v4 +3.9956%, median+0.7581%, worst-3.6800%,W/T/L19/1/4; к v9 mean+4.7753%. Рекомендация: exact_server_v4_NT2_TL280; promotion=False. Ресурсный повтор, если вызван, отдельный и не заменяет primary. Всего quality294,VALID294,рабочих успехов285; все ошибки/перелёты сохранены.

Материалы: experiments/warm_v10/REPORT_RU.md, AUDIT_RU.md, FINAL_METRICS.json, FINAL_AUDIT.json, FREEZE.json, candidate_selected.zip. Пакет побайтно воспроизводит измеренный бинарник; официальный noarg/file-contract пройден. Без staging/commit/push/submit и без удаления прежних результатов.

Уточнение выбранной конфигурации: v10/v5 GW_MODE1 включает геометрическую популяцию и передачу разнообразных готовых стартов. Whole-zone crossover и новая глобальная элита относятся к проверенному, но не выбранному GW_MODE2; singleton shortcut и mass balancing также остались отдельными прототипами. Наблюдаемый средний прирост на новых входах положительный (95% case-bootstrap к v4 [+0.9277%; +7.8716%]), но worst −3.6800% нарушает заранее заданный порог −1%. Неравномерно полученное CPU-время ограничивает интерпретацию; RESOURCE_REPORT_RU.md сохраняет измерения.


## 2026-10-22 — submission_1668601_v12

Неизменный контроль — пользовательская submit_1668601/source4144e63b (v5.2 safe regions). Испытаны8 кандидатных конфигураций с сохранённым исходным MIP. Выбран geometry; independent7новых входов×2seed/TL280/2CPU: 28/28 VALID, mean кпосылке +0.9658%, worst -5.8503%, W/T/L 9/0/5. Локальный критерий продвижения: False. Всего142 quality-прогона; supplementalgeometry development имеет fixed-last оговорку. Отчёт experiments/submission_1668601_v12/REPORT_RU.md, архив dist/case03_cpp_1668601_v12.zip; sourceSHA e3e5cf98c114bfe4627f791aff1b02e4933e338cdd0453e90de9dae981daf26d. Ни код solver/, ни прежние архивы не заменены; серверной отправки нет.
