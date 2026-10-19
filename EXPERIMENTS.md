# Журнал экспериментов

Читать перед работой над решателем. Строку **дописывать в конец** (при конфликте оставить обе строки).
Цифры — из `python3 bench.py <сек> [--runs N --base origin/main]` или из комментария CI.
Посылки на NSUTS — в `results/nsuts.md`.

`дата | кто | ветка | идея | результат (inst0..4 или Δ) | вердикт`

| дата | кто | ветка | идея | результат | вердикт |
|---|---|---|---|---|---|
| 10-16 | Claude | — | Вороной по евклиду + отжиг (v1) | 4941312 / 30.10 / 5.63 / 125675 / 15597 | база |
| 10-16 | Claude | — | MIP без геометрии → снять конфликтные сайты (inst3) | 124 из 341 точки в двух оболочках | ремонт слишком дорогой |
| 10-16 | Claude | — | power diagram с подбором весов h | +4–15% (inst0 +4, inst3 +8, inst4 +15) | принято |
| 10-16 | Claude | — | свободные генераторы G в power diagram | +0.02–3% | принято |
| 10-16 | Claude | — | лимит 270 с вместо 60 с | < +1% | время не узкое место |
| 10-16 | Claude | cpp-solver | перенос на C++ | 5160009 / 32.20 / 5.63 / 135636 / 18005 (60 с) | принято |
| 10-16 | Claude | lns-rewrite | гильотина, разные стратегии у потоков, фиксация набора офисов, случайный план навыков, широкий перебор наборов офисов | ±0.5% (шум) | оставлено в портфеле; не повторять без новой причины |
| 10-16 | Claude | lns-rewrite | inst3: принудительно 6 офисов с наибольшей оценкой | 101569 против 135989 | зазор геометрический; больше офисов вредно |
| 10-16 | Claude | lns-rewrite | лагранжева оценка (`tools/bound.py`) | доля: 97.3 / 97.0 / 100 / 63.4 / 89.5% | диагностика; цены π в поиске — шум |
| 10-16 | Claude | lns-rewrite | одиночный перенос сайта между зонами | 76 тыс. итераций, 2 принято | бесполезен: двигать границу целиком |
| 10-16 | Claude | lns-rewrite | переразрез двух зон прямой + точный DP подмножества + многопоточность | 5164995 / 32.23 / 5.63 / 137539 / 18226 (280 с) | принято |
| 10-16 | Claude | lns-rewrite | `try_open_office` с расчисткой места | inst4 18019 → 18226 (+1.15%) | принято |
| 10-16 | Claude | lns-rewrite | `greedy_fill`: выгодные допустимые сайты оставались неназначенными | gen5 +8.4%, gen3 +2.6%, gen12 +1.7% | принято |
| 10-16 | Claude | lns-rewrite | многопрофильные рабочие: `cntSkill[k] ≤ N_k` необходимо, но не достаточно → проверка назначением | ms0 +71%, ms2 +27%; 1 навык — без изменений | принято, критично для закрытых тестов |
| 10-17 | Claude | repo-cleanup | `SEED`, `bench.py --runs/--base/--synth`, edge-набор в `tools/gen.py` | синтетика 12 + 16 edge за 10 с — все VALID; перелёт лимита растёт с потоками: TL=10 NT=4 +4.9 с, TL=60 NT=16 +1.7 с (gen10 5000 сайтов, big10k) | на 280 с запас хватает; при лимите < 30 с не доверять TIME |
| 10-17 | Claude | repo-cleanup | перелёт лимита на > 1500 сайтах: время в `lns` проверялось раз в 64 итерации (итерация — десятки мс), `hardcap` пускал ход за `tend` | NT=1, TL=15: gen10 16.4 → 14.7 с (CI: 19.8 с → TIME); ≤ 1500 сайтов код не меняется | принято |
| 10-18 | Claude | suite | `bench.py --suite`: 46 инстансов, 12 классов закрытых тестов; калибровка `main`, 30 с × 3 зерна, 1 поток (медиана / лучшее из 3) | huge 0.841 (худший 0.785), multiskill 0.968 (0.876), tightA 0.982, large 0.989, medium 0.992, прочие ≥ 0.994; итого 0.985 | мерило для правок под закрытые тесты; слабые места — нестабильность на huge и multiskill |
| 10-18 | Claude | exact2 | текущий `main` против старого решателя (до lns-rewrite): 41 инстанс (открытые, gen, 24 малых s*), 30 с, 1 зерно | не хуже на 40/41 (до +24%), s13 −0.46% | провал NSUTS #4/#9/#10 был у промежуточной версии; старый в портфель не нужен |
| 10-18 | Claude | exact2 | `EXACT2=1`: точный перебор 1–2 офисов (все разбиения прямой × раздачи навыков × рюкзак «сайты × задачи»), отдельный поток ≤ 30% лимита, ≤ 600 сайтов | inst1/inst2 = рекорды за 0.7 с (поиск уже оптимален в этом классе); s* 30 с × 3 зерна: s3 +4.3%, s6 +0.6%, s12 +1.3…10%, s10 +0…3.5%, худшее −0.7%; открытые ±0 (inst4 +0.35%); синтетика VALID | принято за флагом. Решение перебора только в элиту и в ответ после join: как глобальное лучшее оно стягивало потоки (s10 −9%) |
| 10-18 | Claude | suite | `--suite`: `EXACT2=1` против `main` до #10, 30 с × 3 зерна | итого +0.05%; tightA +2.8, anti +1.5, multiskill +0.8, alphazero −1.4, large −1.5, huge −2.5% (там EXACT2 не запускается, > 600 сайтов → это шум) | на наборе нейтрально; шум классов large/huge при 30 с × 3 зерна ~±2.5% — для них нужно больше зёрен или времени |
| 10-18 | Claude | stability | huge1 280 с, DBG: жадный выбор офисов (`solve.cpp`) обрывается по `t_outer` на 8 офисах (оценка ≈ 0.4 с, полный перебор офисов на каждом шаге), кандидаты по размеру только `k ≤ 8`; итог 10–11 офисов — 590k / 628k. `FORCE_OPS` 13 офисов → 692k за 150 с | `LAZY=1` (ленивый жадный по устаревшим приросту + кандидаты размера ±2 от лучшего): huge1 280 с NT=8 → 690k / 722k (+10/+22%, 12–13 офисов). `--suite` 30 с × 3: итого +1.81%, huge +7.6, tightA +2.1, multiskill +1.3, прочие ±0.1 (large +12% — шум base на large2/3 с целью ≈ 10³); синтетика VALID | принято за флагом; кандидат во включение по умолчанию |
| 10-18 | Claude | lazy-default | `LAZY` включён по умолчанию (`LAZY=0` — старый жадный), `--suite` 30 с × 3 зерна против `main`, 2 прогона | итого +2.14% / +0.90%; huge +16.0/+7.7, large +13.4/+13.3; tightA +3.1/−3.3, multiskill −0.1/−1.0, cluster −0.1/−0.9, grid −1.0/−0.4, medium −0.6/−0.4 (знак не держится, кроме medium/grid: −0.5% в среднем); синтетика VALID | включено по умолчанию |
| 10-18 | Claude | multiskill | `WFIX`: `realize` (build.h) берёт сайт с новым для офиса навыком, только если `greedy_workers` раздаёт рабочих (план навыков считал по N_k — многопрофильный рабочий учитывался в нескольких офисах; старты с ≥5 офисами были невалидны, LNS из них не выходил, acc=0). `--suite` 30 с × 3 против `lazy-default` | multiskill2 6 зёрен: 32.4–37.4 → 42.0–42.24 (лучшее известное было 37.7). `--suite`: multiskill +6.1%, alphazero +1.0, итого +0.17%; tightA −3.7, small/huge −0.9 — шум: там `simple_workers`, код не меняется; синтетика VALID | включено по умолчанию (`WFIX=0` — старое) |
| 10-18 | Claude | ideas2 | `LEVEL`: `level_fill` (improve.h, в конце `greedy_fill`) — раунд «по сайту каждой зоне минимального размера», принимается целиком при росте цели. При A = 0 одиночное добавление всегда ломает баланс, DP только снимает: tightA1 застревал на 35–36 сайтах/зону вместо 37. `--suite` 30 с × 3 против `multiskill` | tightA +2.56% (tightA0/1/2 — новые лучшие, tightA1 24.4–25.8 → 26.17 на всех зёрнах), small +1.0, прочие ±0.5 (huge −0.5 — шум); итого +0.38%; синтетика VALID | включено по умолчанию (`LEVEL=0` — выключить) |

## Открытые вопросы

- Портфель «старый + новый поиск, отдать лучший»: на синтетике закрыто (строка 10-18, `main` не хуже на 40/41);
  на NSUTS подтвердит только следующая посылка.
- **Нестабильность на huge и multiskill** (калибровка `--suite`: медиана / лучшее из 3 зёрен — huge 0.84,
  multiskill 0.97). Цель — стабильнее один прогон, а не рекорд. Начато в ветке `claude/mannobody-stability`:
  - huge1, 60 с, NT=8, 2 зерна: 524 272 и 576 079. Быстрая оценка (`fast.h`) берёт наборы из 4 офисов
    (f ≈ 242k), а итог открывает 9–10 офисов — LNS добирает их медленно (`try_open_office`, ~50 итераций LNS
    на кусок), какие именно — дело случая. Гипотезы: (1) `Fast::evaluate` (`fast.h:84`) отдаёт дефицитный
    навык только топ-`N_k` зонам и обнуляет остальное, при многих офисах недооценка растёт; (2) жадный выбор
    наборов упирается во время `t_outer = min(0.22·limit, 60)` (при 60 с — 13 с, sets=75). **Подтверждено (2)**,
    см. строку `LAZY=1`. Осталось: разброс зёрен с `LAZY` на huge1 ещё 4.5% (690k / 722k), (1) не проверена.
  - multiskill: причина найдена и исправлена (`WFIX`, строка 10-18).
- tightA0: медиана 0.847 при неизменном коде (`simple_workers`) — сильный разброс зёрен, не разбирали.
  - Шум мерила: при 30 с × 3 зерна классы large/huge дают ±2.5% даже без изменений в коде — для них больше зёрен/времени.
- inst1 и inst4: зазор 3% и 10% до оценки, где геометрия, видимо, не главное.

| 10-18 | Codex | danil/colgen-research | Интеграция worker DFS + genetic office start | Синтетика: 30 с NT4 × 3 зерна, 8 задач; huge0 +13.687%, huge1 +24.481%, large2 +16.250%, multiskill0/2 +5.032/+7.580%, anti3 −1.020%; 48/48 VALID. Official synth28/28, package21/21 | Встроено; без коммита. experiments/evolution/REPORT.md §9; integrated_v1.zip |
| 10-18 | Codex | danil/colgen-research | Road profiles/PCA/spectral/UMAP/t-SNE, balanced LP, entropic Newton, affine soft profit, territory MIP | Новые seeds61000+: short huge gains +40–55% не держатся на30с; soft 30с NT4 ×3: huge0 −2.921%, large0 −1.546%, anti3 +2.007%. Territory IP tightA0 +1.50% к matched, 2с IP после5с NT1 | Новые кластерные defaults не включены; см. experiments/clustering/REPORT.md. Перспективен territory/boundary LNS |
| 10-18 | Codex | danil/colgen-research | Серверный кандидат: reuse Fast/hull/worker/warm buffers + monotone final territory/fill | 384 Fast calls: alloc166793→5 huge0, hull5000→0; checksum совпал. Oracle34681, package21/21, A/B12с48/48 VALID; короткие huge регрессии, дополнительно O2 large30с8/8 VALID. Synth28 valid, gen10 TIME13.5с, повтор11.5с | Экспериментальный ZIP server_candidate/artifacts/case03_cpp_server_v2.zip; полный отчёт experiments/server_candidate/REPORT.md; без коммита |
| 10-18 | Codex | danil/colgen-research | server_v3_O3: тот же C++ с -O3 в Makefile | 21/21 package VALID, TL2 NT2, max wall2.644с; score/throughput A/B не проводился | По просьбе пользователя; experiments/server_candidate/artifacts/case03_cpp_server_v3_O3.zip; прежний O2 сохранён |

| 10-19 | Codex | danil/boundary-beam-research | Native boundary B&B/beam, core CP-SAT/SCIP, tail placement | 60с NT2 ×3: tail 72/72 VALID; N≤1500 9 задач mean/median +0.330/+0.244%, худшая пара −8.806%, собственный tail 20/27 wins. Независимый early-wide 48/48 VALID, mean −0.116%, worst median −2.927%. Oracle96/96, CP24/24 | Основной solver сохранён; experimental boundary_tail_experimental_O3.zip и integration.patch; experiments/boundary_beam/REPORT.md. Без коммита/отправки |

| 10-19 | Codex | danil/boundary-beam-research | Deep geometry: islands/depth, anchored rank4 cuts, exact binary64 predicates, grid | 60с NT2×3: grid holdout60/60 VALID mean+0.4365%, exact holdout60/60 mean+0.4236% median−0.0204%, worst pair−10.875%; precision3×20→80; candidate55/55 VALID. Local SCIP anchored15/15 VALID: fresh anti+0.1843%, latent+0.0737%, conditional optimal24.4/40.5с vs old60с timeout. Shape operators weaker than control B&B | Main unchanged; geometry_islands/REPORT.md, 2 optional patches, geometry_exact_experimental_O3.zip; no commit/submission |

| 10-19 | Codex | danil/boundary-beam-research | v4 O3 по запросу: allocation reuse v3 + exact geometry/grid + final boundary B&B24 | Package60 NT2 SEED101:36/36 VALID, max wall59.803с; B&B oracle96/96. Без заявления общего превосходства компонентов | experiments/server_v4/artifacts/case03_cpp_server_v4_O3.zip; MANIFEST.json/README.md. Main сохранён, без коммита/отправки |

| 10-19 | Codex | danil/boundary-beam-research | DP window O(KGlogG), gcd; SCIP/HiGHS conditional selection/count/territory/workers | TL60 NT2 ×3 fresh:60/60 VALID mean−0.8792%, median0%, worst−8.6459%; edge21/21. Native10k81.2→34.5мс; gcd skip→opt14.1мс. MILP count90→130; HiGHS10k+0.3877% vsDP at60с without proof. Oracle3000 window,40 SCIP,40 HiGHS;35 MIP outputs validated | v4 frozen, DP not promoted; experiments/dp_milp/REPORT.md, optional patch, MANIFEST/PATHS. External60 cutoff cleanup≤0.117с. Main unchanged; no commit/submission |

| 10-19 | Codex | danil/boundary-beam-research | v5 MILP: safe envelope growth, grouped integer counts/continuous profit, worker profiles; lazy HiGHS C API tail | TL60 NT2×3 fresh final:60/60 VALID, mean+0.1945%, median+0.0112%, worst-2.5692%; own MIP16/30 improvements; package26/26, oracle Python80+native60. Fixed-inc alpha+1.91095%/.041s, tightA+.59033%/.218s. Max candidate wall60.149s (soft timer). Earlier independent +.3586% and −.3173% preserved | Experimental only; experiments/milp_v5/REPORT.md and artifacts/case03_cpp_server_v5_milp_lazy_O3.zip. v4/main solver unchanged; no commit/submission; boundary-variant master specified, not yet implemented |

| 10-19 | Codex | danil/boundary-beam-research | v5.2 regional perspective MILP: pair/power envelopes, transfers, optional joint office/workers; late 2s cooperative call | TL60 O3 NT2 ×3 fresh:60/60 successful VALID, mean+1.2517%, median+0.0025%, worst−0.9135%, wins/ties/losses15/4/11; own stage22/30. Package26/26, fallback2/2, oracle120 comparisons on30 tiny cases. Empty-office generator RE reproduced/fixed; failing prior series retained. Max wall60.199s, RSS47.961MiB NT2 | Experimental, not promoted; milp_v5_boundaries/REPORT.md, case03_cpp_server_v5_2_regions_safe_experimental_O3.zip. Mean sensitive to large wins; early call−2.8687% rejected. Old v4/v5 and main unchanged; no commit/submission |

| 10-19 | Codex | danil/service-zone-v4 | Перенос замороженной v4 в основной solver, O3 и документация | Payload побайтово совпал с v4; ZIP пересобран. Synth10 NT3:28/28 VALID; A/B60 NT3 ×3 против 102a0b8: inst0 +0.00%, inst1 +0.00%, inst2 +0.00%, inst3 +0.17%, inst4 +0.34%; benchmark rc0. Max wall кандидата 59.8с | В этой проверке регрессий более 1% по медианам не обнаружено; дополнительное подтверждение качества выполняется в CI при открытии PR. docs/v4.md; без staging, коммита и отправки |
