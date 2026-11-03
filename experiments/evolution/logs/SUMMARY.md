# Измерения evolution

Все задачи сгенерированы. `score` — значение исходной целевой функции.
В ячейке: медиана по доступным зёрнам; число прогонов указано отдельно.
Таблица автоматически строится из logs/*/results.json. Незаконченные серии помечены числом строк.

## cross_diagnostics_v3

Данные: ./experiments/evolution/logs/cross_diagnostics_v3/results.json; строк: 18.

`{"seconds": 30.0, "runs": 1, "threads": 1, "jobs": 2, "variants": "genetic,memetic,mutation", "suite": "all", "only": "large0,large2,anti3,small0,alphabig0,multiskill0", "tag": "cross_diagnostics_v3", "inputs": ["./experiments/evolution/data/suite_alphabig0.json", "./experiments/evolution/data/suite_anti3.json", "./experiments/evolution/data/suite_large0.json", "./experiments/evolution/data/suite_large2.json", "./experiments/evolution/data/suite_multiskill0.json", "./experiments/evolution/data/suite_small0.json"]}`

| Задача | genetic | memetic | mutation | n по вариантам |
|---|---:|---:|---:|---|
| suite_alphabig0 | 20282967.566517 | 20300075.695299 | 20122574.827853 | 1, 1, 1 |
| suite_anti3 | 385716.153439 | 353424.514093 | 330344.368940 | 1, 1, 1 |
| suite_large0 | 169209.329651 | 168782.229409 | 162529.834879 | 1, 1, 1 |
| suite_large2 | 59781.185713 | 57848.142344 | 58298.200818 | 1, 1, 1 |
| suite_multiskill0 | 50.076205 | 50.309442 | 50.309442 | 1, 1, 1 |
| suite_small0 | 2053.062289 | 2127.850292 | 2127.850292 | 1, 1, 1 |

VALID: 18/18; wall min/max: 29.456/30.058 с.

## edges_v2

Данные: ./experiments/evolution/logs/edges_v2/results.json; строк: 48.

`{"seconds": 5.0, "runs": 1, "threads": 1, "jobs": 3, "variants": "base,genetic,combined", "suite": "edge", "only": "", "tag": "edges_v2", "inputs": ["./experiments/evolution/data/edge/edge_A0.json", "./experiments/evolution/data/edge/edge_A_big.json", "./experiments/evolution/data/edge/edge_alpha0.json", "./experiments/evolution/data/edge/edge_alpha_huge.json", "./experiments/evolution/data/edge/edge_big10k.json", "./experiments/evolution/data/edge/edge_collinear.json", "./experiments/evolution/data/edge/edge_empty.json", "./experiments/evolution/data/edge/edge_maxsize0.json", "./experiments/evolution/data/edge/edge_multiskill.json", "./experiments/evolution/data/edge/edge_no_offices.json", "./experiments/evolution/data/edge/edge_no_tasks.json", "./experiments/evolution/data/edge/edge_no_workers.json", "./experiments/evolution/data/edge/edge_one_site.json", "./experiments/evolution/data/edge/edge_same_point.json", "./experiments/evolution/data/edge/edge_skill_missing.json", "./experiments/evolution/data/edge/edge_unit_coords_big_dist.json"]}`

| Задача | base | combined | genetic | n по вариантам |
|---|---:|---:|---:|---|
| edge_A0 | 64.330482 | 64.330482 | 64.330482 | 1, 1, 1 |
| edge_A_big | 64.330482 | 64.330482 | 64.330482 | 1, 1, 1 |
| edge_alpha0 | 64.330482 | 64.330482 | 64.330482 | 1, 1, 1 |
| edge_alpha_huge | 64.330482 | 64.330482 | 64.330482 | 1, 1, 1 |
| edge_big10k | 55438.384589 | 177889.854670 | 166601.370571 | 1, 1, 1 |
| edge_collinear | 111.000000 | 111.000000 | 111.000000 | 1, 1, 1 |
| edge_empty | 0.000000 | 0.000000 | 0.000000 | 1, 1, 1 |
| edge_maxsize0 | 0.000000 | 0.000000 | 0.000000 | 1, 1, 1 |
| edge_multiskill | 178.535844 | 178.535844 | 178.535844 | 1, 1, 1 |
| edge_no_offices | 0.000000 | 0.000000 | 0.000000 | 1, 1, 1 |
| edge_no_tasks | 64.330482 | 64.330482 | 64.330482 | 1, 1, 1 |
| edge_no_workers | 0.000000 | 0.000000 | 0.000000 | 1, 1, 1 |
| edge_one_site | 7.585786 | 7.585786 | 7.585786 | 1, 1, 1 |
| edge_same_point | 49.000000 | 49.000000 | 49.000000 | 1, 1, 1 |
| edge_skill_missing | 0.000000 | 0.000000 | 0.000000 | 1, 1, 1 |
| edge_unit_coords_big_dist | 334916.827909 | 334916.827909 | 334916.827909 | 1, 1, 1 |

VALID: 48/48; wall min/max: 0.004/5.661 с.

## generalization_v2

Данные: ./experiments/evolution/logs/generalization_v2/results.json; строк: 92.

`{"seconds": 5.0, "runs": 1, "threads": 1, "jobs": 3, "variants": "base,genetic", "suite": "all", "only": "", "tag": "generalization_v2", "inputs": ["./experiments/evolution/data/suite_alphabig0.json", "./experiments/evolution/data/suite_alphabig1.json", "./experiments/evolution/data/suite_alphabig2.json", "./experiments/evolution/data/suite_alphabig3.json", "./experiments/evolution/data/suite_alphazero0.json", "./experiments/evolution/data/suite_alphazero1.json", "./experiments/evolution/data/suite_alphazero2.json", "./experiments/evolution/data/suite_alphazero3.json", "./experiments/evolution/data/suite_anti0.json", "./experiments/evolution/data/suite_anti1.json", "./experiments/evolution/data/suite_anti2.json", "./experiments/evolution/data/suite_anti3.json", "./experiments/evolution/data/suite_cluster0.json", "./experiments/evolution/data/suite_cluster1.json", "./experiments/evolution/data/suite_cluster2.json", "./experiments/evolution/data/suite_cluster3.json", "./experiments/evolution/data/suite_deficit0.json", "./experiments/evolution/data/suite_deficit1.json", "./experiments/evolution/data/suite_deficit2.json", "./experiments/evolution/data/suite_deficit3.json", "./experiments/evolution/data/suite_grid0.json", "./experiments/evolution/data/suite_grid1.json", "./experiments/evolution/data/suite_grid2.json", "./experiments/evolution/data/suite_grid3.json", "./experiments/evolution/data/suite_huge0.json", "./experiments/evolution/data/suite_huge1.json", "./experiments/evolution/data/suite_large0.json", "./experiments/evolution/data/suite_large1.json", "./experiments/evolution/data/suite_large2.json", "./experiments/evolution/data/suite_large3.json", "./experiments/evolution/data/suite_medium0.json", "./experiments/evolution/data/suite_medium1.json", "./experiments/evolution/data/suite_medium2.json", "./experiments/evolution/data/suite_medium3.json", "./experiments/evolution/data/suite_multiskill0.json", "./experiments/evolution/data/suite_multiskill1.json", "./experiments/evolution/data/suite_multiskill2.json", "./experiments/evolution/data/suite_multiskill3.json", "./experiments/evolution/data/suite_small0.json", "./experiments/evolution/data/suite_small1.json", "./experiments/evolution/data/suite_small2.json", "./experiments/evolution/data/suite_small3.json", "./experiments/evolution/data/suite_tightA0.json", "./experiments/evolution/data/suite_tightA1.json", "./experiments/evolution/data/suite_tightA2.json", "./experiments/evolution/data/suite_tightA3.json"]}`

| Задача | base | genetic | n по вариантам |
|---|---:|---:|---|
| suite_alphabig0 | 20282967.566517 | 20122574.827853 | 1, 1 |
| suite_alphabig1 | 28812971.498455 | 28630654.501561 | 1, 1 |
| suite_alphabig2 | 8083598.964883 | 7957795.727426 | 1, 1 |
| suite_alphabig3 | 19706178.032203 | 19898048.818583 | 1, 1 |
| suite_alphazero0 | 71485.195562 | 71485.195562 | 1, 1 |
| suite_alphazero1 | 37.736953 | 37.736953 | 1, 1 |
| suite_alphazero2 | 81025.716980 | 81026.575270 | 1, 1 |
| suite_alphazero3 | 15120.078474 | 15251.098251 | 1, 1 |
| suite_anti0 | 15871.782174 | 15871.782174 | 1, 1 |
| suite_anti1 | 48.480784 | 49.928508 | 1, 1 |
| suite_anti2 | 80043.414457 | 80043.414457 | 1, 1 |
| suite_anti3 | 384784.657661 | 336174.289865 | 1, 1 |
| suite_cluster0 | 368397.980131 | 368397.980131 | 1, 1 |
| suite_cluster1 | 33.315838 | 32.860946 | 1, 1 |
| suite_cluster2 | 40.559172 | 40.555522 | 1, 1 |
| suite_cluster3 | 89.861213 | 89.726733 | 1, 1 |
| suite_deficit0 | 38829.071841 | 38819.100543 | 1, 1 |
| suite_deficit1 | 2677.506758 | 2678.206667 | 1, 1 |
| suite_deficit2 | 12941.887737 | 12941.887737 | 1, 1 |
| suite_deficit3 | 35.591128 | 35.591128 | 1, 1 |
| suite_grid0 | 26465.056152 | 25396.498100 | 1, 1 |
| suite_grid1 | 32802.656420 | 32851.293825 | 1, 1 |
| suite_grid2 | 18737.771317 | 18737.771317 | 1, 1 |
| suite_grid3 | 14713.320380 | 14713.320380 | 1, 1 |
| suite_huge0 | 154529.679706 | 467066.155807 | 1, 1 |
| suite_huge1 | 133589.993112 | 273948.499678 | 1, 1 |
| suite_large0 | 83132.155014 | 145667.149173 | 1, 1 |
| suite_large1 | 71816.874468 | 120272.834514 | 1, 1 |
| suite_large2 | 36002.514406 | 57363.634101 | 1, 1 |
| suite_large3 | 93229.656920 | 68819.141151 | 1, 1 |
| suite_medium0 | 139698.290107 | 135678.569828 | 1, 1 |
| suite_medium1 | 28.395848 | 28.395848 | 1, 1 |
| suite_medium2 | 12610.768286 | 12358.224390 | 1, 1 |
| suite_medium3 | 85.028813 | 85.027631 | 1, 1 |
| suite_multiskill0 | 50.076205 | 50.076205 | 1, 1 |
| suite_multiskill1 | 10464.702867 | 10464.702867 | 1, 1 |
| suite_multiskill2 | 24582.608975 | 24582.608975 | 1, 1 |
| suite_multiskill3 | 15213.302428 | 15231.344609 | 1, 1 |
| suite_small0 | 2052.507889 | 2047.310870 | 1, 1 |
| suite_small1 | 38.949910 | 38.949910 | 1, 1 |
| suite_small2 | 32844.424547 | 32933.441100 | 1, 1 |
| suite_small3 | 5933.582916 | 5933.582916 | 1, 1 |
| suite_tightA0 | 34363.796800 | 34363.796800 | 1, 1 |
| suite_tightA1 | 17.511682 | 17.313119 | 1, 1 |
| suite_tightA2 | 7777.827723 | 7777.827723 | 1, 1 |
| suite_tightA3 | 28.723443 | 28.664989 | 1, 1 |

VALID: 92/92; wall min/max: 4.504/5.553 с.

## holdout_long_v2

Данные: ./experiments/evolution/logs/holdout_long_v2/results.json; строк: 6.

`{"seconds": 280.0, "runs": 1, "threads": 4, "jobs": 2, "variants": "base,random,genetic", "suite": "holdout", "only": "huge0,huge1", "tag": "holdout_long_v2", "inputs": ["./experiments/evolution/data/holdout/holdout_huge0.json", "./experiments/evolution/data/holdout/holdout_huge1.json"]}`

| Задача | base | genetic | random | n по вариантам |
|---|---:|---:|---:|---|
| holdout_huge0 | 625272438.325413 | 782563228.040250 | 767999216.235952 | 1, 1, 1 |
| holdout_huge1 | 6124556.151165 | 9490617.522691 | 9250599.159430 | 1, 1, 1 |

VALID: 6/6; wall min/max: 278.283/279.248 с.

## holdout_repeat_v5

Данные: ./experiments/evolution/logs/holdout_repeat_v5/results.json; строк: 12.

`{"seconds": 60.0, "runs": 2, "threads": 8, "jobs": 2, "variants": "base,random,combined", "suite": "holdout", "only": "huge0,huge1", "tag": "holdout_repeat_v5", "inputs": ["./experiments/evolution/data/holdout/holdout_huge0.json", "./experiments/evolution/data/holdout/holdout_huge1.json"]}`

| Задача | base | combined | random | n по вариантам |
|---|---:|---:|---:|---|
| holdout_huge0 | 386421647.139440 | 781218552.605151 | 774489457.817352 | 2, 2, 2 |
| holdout_huge1 | 5127289.985105 | 9699699.335455 | 9201373.196365 | 2, 2, 2 |

VALID: 12/12; wall min/max: 59.592/60.404 с.

## local_v1

Данные: ./experiments/evolution/logs/local_v1/results.json; строк: 6.

`{"source": "screen_v1", "limit": 2.0, "attempts": 3, "radius": 12, "only": "anti0,multiskill0,tightA0,small0,large0,huge0", "tag": "local_v1"}`

| Задача | Исходное | После MIP | Контроль, то же время | Время MIP, с |
|---|---:|---:|---:|---:|
| anti0 | 15871.782174 | 15871.782174 | 15871.782174 | 6.057323 |
| multiskill0 | 50.076205 | 51.859545 | 50.076205 | 0.218217 |
| tightA0 | 34363.796800 | 34812.270910 | 34363.796800 | 2.801516 |
| small0 | 2051.271105 | 2051.271105 | 2056.762239 | 0.862030 |
| large0 | 68778.631452 | 68791.436607 | 109426.469979 | 3.226636 |
| huge0 | 261059.073363 | 261257.382782 | 304322.999246 | 6.345284 |

## local_workers_v2

Данные: ./experiments/evolution/logs/local_workers_v2/results.json; строк: 4.

`{"source": "workers_v2", "source_variant": "workers", "seed": 1, "limit": 1.0, "attempts": 3, "radius": 12, "only": "multiskill0,multiskill1,multiskill2,multiskill3", "tag": "local_workers_v2"}`

| Задача | Исходное | После MIP | Контроль, то же время | Время MIP, с |
|---|---:|---:|---:|---:|
| multiskill0 | 52.482001 | 52.482001 | 52.670166 | 3.069546 |
| multiskill1 | 10582.856976 | 10609.342688 | 10617.368980 | 2.839416 |
| multiskill2 | 26445.943523 | 26445.943523 | 26445.943523 | 2.642980 |
| multiskill3 | 15240.909905 | 15240.909905 | 15240.909905 | 0.377431 |

## long_v2

Данные: ./experiments/evolution/logs/long_v2/results.json; строк: 3.

`{"seconds": 280.0, "runs": 1, "threads": 4, "jobs": 2, "variants": "base,random,genetic", "suite": "all", "only": "huge2,large2", "tag": "long_v2", "inputs": ["./experiments/evolution/data/suite_large2.json"]}`

| Задача | base | genetic | random | n по вариантам |
|---|---:|---:|---:|---|
| suite_large2 | 64384.012079 | 64784.415331 | 63606.208975 | 1, 1, 1 |

VALID: 3/3; wall min/max: 277.528/277.836 с.

## memetic_screen_v1

Данные: ./experiments/evolution/logs/memetic_screen_v1/results.json; строк: 36.

`{"seconds": 6.0, "runs": 1, "threads": 1, "jobs": 3, "variants": "genetic,memetic,mutation", "suite": "screen", "only": "", "tag": "memetic_screen_v1", "inputs": ["./experiments/evolution/data/suite_alphabig0.json", "./experiments/evolution/data/suite_alphazero0.json", "./experiments/evolution/data/suite_anti0.json", "./experiments/evolution/data/suite_cluster0.json", "./experiments/evolution/data/suite_deficit0.json", "./experiments/evolution/data/suite_grid0.json", "./experiments/evolution/data/suite_huge0.json", "./experiments/evolution/data/suite_large0.json", "./experiments/evolution/data/suite_medium0.json", "./experiments/evolution/data/suite_multiskill0.json", "./experiments/evolution/data/suite_small0.json", "./experiments/evolution/data/suite_tightA0.json"]}`

| Задача | genetic | memetic | mutation | n по вариантам |
|---|---:|---:|---:|---|
| suite_alphabig0 | 20282967.566517 | 19812527.495249 | 20506545.774582 | 1, 1, 1 |
| suite_alphazero0 | 71485.195562 | 71485.195562 | 71485.195562 | 1, 1, 1 |
| suite_anti0 | 15871.782174 | 16110.005057 | 16110.005057 | 1, 1, 1 |
| suite_cluster0 | 368397.980131 | 368060.721361 | 368182.983419 | 1, 1, 1 |
| suite_deficit0 | 38829.071841 | 38829.071841 | 38829.071841 | 1, 1, 1 |
| suite_grid0 | 26637.320943 | 26111.962388 | 26666.829440 | 1, 1, 1 |
| suite_huge0 | 392643.302080 | 466313.841706 | 466313.841706 | 1, 1, 1 |
| suite_large0 | 159723.764783 | 145907.792171 | 169016.263577 | 1, 1, 1 |
| suite_medium0 | 139617.442067 | 137247.438573 | 137740.445633 | 1, 1, 1 |
| suite_multiskill0 | 50.076205 | 50.309442 | 50.076205 | 1, 1, 1 |
| suite_small0 | 2047.310870 | 2120.445677 | 2127.850292 | 1, 1, 1 |
| suite_tightA0 | 34363.796800 | 34363.796800 | 34388.186411 | 1, 1, 1 |

VALID: 36/36; wall min/max: 5.511/6.193 с.

## package_genetic_v5

Данные: ./experiments/evolution/logs/package_genetic_v5/results.json; строк: 21.

`{}`

VALID 21/21; seconds=2.0; NT=2; max wall=3.059s.

## package_smoke_v4

Данные: ./experiments/evolution/logs/package_smoke_v4/results.json; строк: 21.

`{}`

VALID 21/21; seconds=2.0; NT=2; max wall=5.212s.

## patch_validation_v5

Данные: ./experiments/evolution/logs/patch_validation_v5/results.json; строк: 24.

`{"seconds": 30.0, "runs": 1, "threads": 1, "jobs": 2, "variants": "genetic,memetic,patch,mutation", "suite": "all", "only": "large0,large2,anti3,small0,alphabig0,multiskill0", "tag": "patch_validation_v5", "inputs": ["./experiments/evolution/data/suite_alphabig0.json", "./experiments/evolution/data/suite_anti3.json", "./experiments/evolution/data/suite_large0.json", "./experiments/evolution/data/suite_large2.json", "./experiments/evolution/data/suite_multiskill0.json", "./experiments/evolution/data/suite_small0.json"]}`

| Задача | genetic | memetic | mutation | patch | n по вариантам |
|---|---:|---:|---:|---:|---|
| suite_alphabig0 | 20282967.566517 | 20905284.028428 | 20191776.504473 | 20282967.566517 | 1, 1, 1, 1 |
| suite_anti3 | 386705.456728 | 326001.361961 | 376855.965500 | 346224.489604 | 1, 1, 1, 1 |
| suite_large0 | 186505.157512 | 185001.881406 | 168782.229409 | 168782.229409 | 1, 1, 1, 1 |
| suite_large2 | 59917.349703 | 59421.802622 | 58344.480377 | 59206.090829 | 1, 1, 1, 1 |
| suite_multiskill0 | 50.076205 | 50.309442 | 50.076205 | 50.332695 | 1, 1, 1, 1 |
| suite_small0 | 2053.062289 | 2127.850292 | 2127.850292 | 2127.850292 | 1, 1, 1, 1 |

VALID: 24/24; wall min/max: 29.408/30.402 с.

## portfolio_v2

Данные: ./experiments/evolution/logs/portfolio_v2/results.json; строк: 16.

`{"seconds": 60.0, "runs": 2, "threads": 4, "jobs": 2, "variants": "base,genetic,memetic,mutation", "suite": "all", "only": "huge2,huge3,large2,large3", "tag": "portfolio_v2", "inputs": ["./experiments/evolution/data/suite_large2.json", "./experiments/evolution/data/suite_large3.json"]}`

| Задача | base | genetic | memetic | mutation | n по вариантам |
|---|---:|---:|---:|---:|---|
| suite_large2 | 63733.776691 | 62187.800959 | 61472.456877 | 62092.907505 | 2, 2, 2, 2 |
| suite_large3 | 111732.734104 | 110216.026898 | 110433.564669 | 110097.473254 | 2, 2, 2, 2 |

VALID: 16/16; wall min/max: 59.418/60.006 с.

## scout_generalization_v3

Данные: ./experiments/evolution/logs/scout_generalization_v3/results.json; строк: 138.

`{"seconds": 5.0, "runs": 1, "threads": 4, "jobs": 2, "variants": "base,scout,all", "suite": "all", "only": "", "tag": "scout_generalization_v3", "inputs": ["./experiments/evolution/data/suite_alphabig0.json", "./experiments/evolution/data/suite_alphabig1.json", "./experiments/evolution/data/suite_alphabig2.json", "./experiments/evolution/data/suite_alphabig3.json", "./experiments/evolution/data/suite_alphazero0.json", "./experiments/evolution/data/suite_alphazero1.json", "./experiments/evolution/data/suite_alphazero2.json", "./experiments/evolution/data/suite_alphazero3.json", "./experiments/evolution/data/suite_anti0.json", "./experiments/evolution/data/suite_anti1.json", "./experiments/evolution/data/suite_anti2.json", "./experiments/evolution/data/suite_anti3.json", "./experiments/evolution/data/suite_cluster0.json", "./experiments/evolution/data/suite_cluster1.json", "./experiments/evolution/data/suite_cluster2.json", "./experiments/evolution/data/suite_cluster3.json", "./experiments/evolution/data/suite_deficit0.json", "./experiments/evolution/data/suite_deficit1.json", "./experiments/evolution/data/suite_deficit2.json", "./experiments/evolution/data/suite_deficit3.json", "./experiments/evolution/data/suite_grid0.json", "./experiments/evolution/data/suite_grid1.json", "./experiments/evolution/data/suite_grid2.json", "./experiments/evolution/data/suite_grid3.json", "./experiments/evolution/data/suite_huge0.json", "./experiments/evolution/data/suite_huge1.json", "./experiments/evolution/data/suite_large0.json", "./experiments/evolution/data/suite_large1.json", "./experiments/evolution/data/suite_large2.json", "./experiments/evolution/data/suite_large3.json", "./experiments/evolution/data/suite_medium0.json", "./experiments/evolution/data/suite_medium1.json", "./experiments/evolution/data/suite_medium2.json", "./experiments/evolution/data/suite_medium3.json", "./experiments/evolution/data/suite_multiskill0.json", "./experiments/evolution/data/suite_multiskill1.json", "./experiments/evolution/data/suite_multiskill2.json", "./experiments/evolution/data/suite_multiskill3.json", "./experiments/evolution/data/suite_small0.json", "./experiments/evolution/data/suite_small1.json", "./experiments/evolution/data/suite_small2.json", "./experiments/evolution/data/suite_small3.json", "./experiments/evolution/data/suite_tightA0.json", "./experiments/evolution/data/suite_tightA1.json", "./experiments/evolution/data/suite_tightA2.json", "./experiments/evolution/data/suite_tightA3.json"]}`

| Задача | all | base | scout | n по вариантам |
|---|---:|---:|---:|---|
| suite_alphabig0 | 19156609.074091 | 20282967.566517 | 20973705.633011 | 1, 1, 1 |
| suite_alphabig1 | 28630654.501561 | 28304783.991043 | 28276615.685733 | 1, 1, 1 |
| suite_alphabig2 | 7754338.360935 | 7360144.659212 | 7851198.902364 | 1, 1, 1 |
| suite_alphabig3 | 22021838.065418 | 19706178.032203 | 19522858.330122 | 1, 1, 1 |
| suite_alphazero0 | 71485.195562 | 71485.195562 | 71485.195562 | 1, 1, 1 |
| suite_alphazero1 | 37.736953 | 37.736953 | 37.736953 | 1, 1, 1 |
| suite_alphazero2 | 81025.716980 | 81342.173641 | 81025.716980 | 1, 1, 1 |
| suite_alphazero3 | 15204.754777 | 15218.165849 | 15088.546236 | 1, 1, 1 |
| suite_anti0 | 16110.005057 | 15871.782174 | 17076.214595 | 1, 1, 1 |
| suite_anti1 | 53.214724 | 52.661883 | 53.376513 | 1, 1, 1 |
| suite_anti2 | 109759.826852 | 80043.414457 | 80043.414457 | 1, 1, 1 |
| suite_anti3 | 339069.032458 | 365535.294643 | 340093.292669 | 1, 1, 1 |
| suite_cluster0 | 368127.509643 | 368397.980131 | 373231.377592 | 1, 1, 1 |
| suite_cluster1 | 33.037819 | 33.276886 | 33.685938 | 1, 1, 1 |
| suite_cluster2 | 40.559172 | 40.559727 | 40.559933 | 1, 1, 1 |
| suite_cluster3 | 88.678472 | 89.561646 | 89.851630 | 1, 1, 1 |
| suite_deficit0 | 38829.071841 | 38829.071841 | 38829.071841 | 1, 1, 1 |
| suite_deficit1 | 2674.914525 | 2678.244328 | 2677.737144 | 1, 1, 1 |
| suite_deficit2 | 12941.887737 | 12941.887737 | 12941.887737 | 1, 1, 1 |
| suite_deficit3 | 35.591128 | 35.591128 | 35.591128 | 1, 1, 1 |
| suite_grid0 | 26463.809046 | 26666.829440 | 26274.551447 | 1, 1, 1 |
| suite_grid1 | 32851.293825 | 32851.293825 | 32851.293825 | 1, 1, 1 |
| suite_grid2 | 18737.771317 | 18737.771317 | 18746.837669 | 1, 1, 1 |
| suite_grid3 | 14713.320380 | 14996.442106 | 15013.959423 | 1, 1, 1 |
| suite_huge0 | 337336.527443 | 277753.852841 | 385301.958425 | 1, 1, 1 |
| suite_huge1 | 334769.144257 | 163151.802999 | 399498.242874 | 1, 1, 1 |
| suite_large0 | 149401.570667 | 111535.715450 | 143307.125131 | 1, 1, 1 |
| suite_large1 | 130158.767519 | 105960.364830 | 121603.210616 | 1, 1, 1 |
| suite_large2 | 58460.521951 | 42510.478568 | 51733.376566 | 1, 1, 1 |
| suite_large3 | 104529.068054 | 81203.786912 | 96656.833577 | 1, 1, 1 |
| suite_medium0 | 135639.135262 | 138253.394053 | 140762.046974 | 1, 1, 1 |
| suite_medium1 | 28.395848 | 28.395848 | 28.395848 | 1, 1, 1 |
| suite_medium2 | 12321.877173 | 12537.553637 | 12933.958719 | 1, 1, 1 |
| suite_medium3 | 83.190417 | 84.152882 | 84.152882 | 1, 1, 1 |
| suite_multiskill0 | 52.685184 | 50.076205 | 50.870503 | 1, 1, 1 |
| suite_multiskill1 | 10562.867151 | 10464.702867 | 10487.445707 | 1, 1, 1 |
| suite_multiskill2 | 26445.943523 | 24427.813380 | 24332.079874 | 1, 1, 1 |
| suite_multiskill3 | 15240.909905 | 15240.909905 | 15240.909905 | 1, 1, 1 |
| suite_small0 | 2127.850292 | 2052.674234 | 2056.762239 | 1, 1, 1 |
| suite_small1 | 38.949910 | 38.949910 | 38.949910 | 1, 1, 1 |
| suite_small2 | 32999.896689 | 33075.271647 | 33010.870556 | 1, 1, 1 |
| suite_small3 | 5933.582916 | 5933.582916 | 5933.582916 | 1, 1, 1 |
| suite_tightA0 | 34440.430383 | 34363.796800 | 34467.417959 | 1, 1, 1 |
| suite_tightA1 | 17.511682 | 17.511682 | 17.511682 | 1, 1, 1 |
| suite_tightA2 | 7777.827723 | 7777.827723 | 7777.827723 | 1, 1, 1 |
| suite_tightA3 | 28.723443 | 28.723443 | 28.723443 | 1, 1, 1 |

VALID: 138/138; wall min/max: 4.893/6.617 с.

## scout_validation_v4

Данные: ./experiments/evolution/logs/scout_validation_v4/results.json; строк: 36.

`{"seconds": 30.0, "runs": 2, "threads": 4, "jobs": 2, "variants": "base,scout,all", "suite": "all", "only": "huge0,huge1,large2,large3,multiskill2,anti3", "tag": "scout_validation_v4", "inputs": ["./experiments/evolution/data/suite_anti3.json", "./experiments/evolution/data/suite_huge0.json", "./experiments/evolution/data/suite_huge1.json", "./experiments/evolution/data/suite_large2.json", "./experiments/evolution/data/suite_large3.json", "./experiments/evolution/data/suite_multiskill2.json"]}`

| Задача | all | base | scout | n по вариантам |
|---|---:|---:|---:|---|
| suite_anti3 | 367062.484222 | 390334.312187 | 374188.864328 | 2, 2, 2 |
| suite_huge0 | 521461.693871 | 343758.709228 | 475755.787777 | 2, 2, 2 |
| suite_huge1 | 503056.067699 | 399667.594793 | 431860.979445 | 2, 2, 2 |
| suite_large2 | 59136.732943 | 54947.097439 | 56010.574309 | 2, 2, 2 |
| suite_large3 | 104459.235631 | 102530.239659 | 102714.370844 | 2, 2, 2 |
| suite_multiskill2 | 26445.943523 | 24550.368410 | 24807.767216 | 2, 2, 2 |

VALID: 36/36; wall min/max: 29.712/30.228 с.

## screen_v1

Данные: ./experiments/evolution/logs/screen_v1/results.json; строк: 36.

`{"seconds": 5.0, "runs": 1, "threads": 1, "jobs": 3, "variants": "base,random,genetic", "suite": "screen", "only": "", "tag": "screen_v1", "inputs": ["./experiments/evolution/data/suite_alphabig0.json", "./experiments/evolution/data/suite_alphazero0.json", "./experiments/evolution/data/suite_anti0.json", "./experiments/evolution/data/suite_cluster0.json", "./experiments/evolution/data/suite_deficit0.json", "./experiments/evolution/data/suite_grid0.json", "./experiments/evolution/data/suite_huge0.json", "./experiments/evolution/data/suite_large0.json", "./experiments/evolution/data/suite_medium0.json", "./experiments/evolution/data/suite_multiskill0.json", "./experiments/evolution/data/suite_small0.json", "./experiments/evolution/data/suite_tightA0.json"]}`

| Задача | base | genetic | random | n по вариантам |
|---|---:|---:|---:|---|
| suite_alphabig0 | 20282967.566517 | 20122574.827853 | 20122574.827853 | 1, 1, 1 |
| suite_alphazero0 | 71485.195562 | 71485.195562 | 71485.195562 | 1, 1, 1 |
| suite_anti0 | 15871.782174 | 15871.782174 | 15871.782174 | 1, 1, 1 |
| suite_cluster0 | 368397.980131 | 368397.980131 | 368397.980131 | 1, 1, 1 |
| suite_deficit0 | 38829.071841 | 38819.100543 | 38819.100543 | 1, 1, 1 |
| suite_grid0 | 26677.160787 | 26574.667949 | 26662.669012 | 1, 1, 1 |
| suite_huge0 | 261059.073363 | 487819.009439 | 398040.238393 | 1, 1, 1 |
| suite_large0 | 68778.631452 | 156272.911971 | 161652.211961 | 1, 1, 1 |
| suite_medium0 | 139698.290107 | 139617.442067 | 139617.442067 | 1, 1, 1 |
| suite_multiskill0 | 50.076205 | 50.076205 | 50.076205 | 1, 1, 1 |
| suite_small0 | 2051.271105 | 2053.062289 | 2124.829050 | 1, 1, 1 |
| suite_tightA0 | 34363.796800 | 34363.796800 | 34363.796800 | 1, 1, 1 |

VALID: 36/36; wall min/max: 4.505/5.413 с.

## validation_v1

Данные: ./experiments/evolution/logs/validation_v1/results.json; строк: 36.

`{"seconds": 30.0, "runs": 3, "threads": 1, "jobs": 3, "variants": "base,random,genetic", "suite": "all", "only": "huge0,huge1,large0,large1", "tag": "validation_v1", "inputs": ["./experiments/evolution/data/suite_huge0.json", "./experiments/evolution/data/suite_huge1.json", "./experiments/evolution/data/suite_large0.json", "./experiments/evolution/data/suite_large1.json"]}`

| Задача | base | genetic | random | n по вариантам |
|---|---:|---:|---:|---|
| suite_huge0 | 375666.370636 | 524243.445589 | 499550.394653 | 3, 3, 3 |
| suite_huge1 | 383921.259623 | 482409.437544 | 446445.451849 | 3, 3, 3 |
| suite_large0 | 162182.845877 | 186063.777677 | 178160.229948 | 3, 3, 3 |
| suite_large1 | 139383.757925 | 141972.961789 | 149019.306793 | 3, 3, 3 |

VALID: 36/36; wall min/max: 29.476/30.153 с.

## worker_holdout_v4

Данные: ./experiments/evolution/logs/worker_holdout_v4/results.json; строк: 24.

`{"seconds": 12.0, "runs": 3, "threads": 1, "jobs": 2, "variants": "base,workers", "suite": "holdout", "only": "", "tag": "worker_holdout_v4", "inputs": ["./experiments/evolution/data/holdout/holdout_anti0.json", "./experiments/evolution/data/holdout/holdout_balance0.json", "./experiments/evolution/data/holdout/holdout_huge0.json", "./experiments/evolution/data/holdout/holdout_huge1.json"]}`

| Задача | base | workers | n по вариантам |
|---|---:|---:|---|
| holdout_anti0 | 9825741.550655 | 9838004.851816 | 3, 3 |
| holdout_balance0 | 199063.876233 | 199063.876233 | 3, 3 |
| holdout_huge0 | 204983944.305181 | 204984057.003323 | 3, 3 |
| holdout_huge1 | 1860627.498953 | 2127835.795235 | 3, 3 |

VALID: 24/24; wall min/max: 11.572/13.227 с.

## workers_v2

Данные: ./experiments/evolution/logs/workers_v2/results.json; строк: 54.

`{"seconds": 12.0, "runs": 3, "threads": 1, "jobs": 3, "variants": "base,workers,combined", "suite": "all", "only": "multiskill0,multiskill1,multiskill2,multiskill3,deficit0,deficit1", "tag": "workers_v2", "inputs": ["./experiments/evolution/data/suite_deficit0.json", "./experiments/evolution/data/suite_deficit1.json", "./experiments/evolution/data/suite_multiskill0.json", "./experiments/evolution/data/suite_multiskill1.json", "./experiments/evolution/data/suite_multiskill2.json", "./experiments/evolution/data/suite_multiskill3.json"]}`

| Задача | base | combined | workers | n по вариантам |
|---|---:|---:|---:|---|
| suite_deficit0 | 38829.071841 | 38829.071841 | 38829.071841 | 3, 3, 3 |
| suite_deficit1 | 2683.094999 | 2677.506758 | 2683.094999 | 3, 3, 3 |
| suite_multiskill0 | 50.076205 | 52.670166 | 52.506699 | 3, 3, 3 |
| suite_multiskill1 | 10471.623224 | 10602.296061 | 10595.911731 | 3, 3, 3 |
| suite_multiskill2 | 24518.127844 | 26445.943523 | 26445.943523 | 3, 3, 3 |
| suite_multiskill3 | 15231.344609 | 15240.909905 | 15240.909905 | 3, 3, 3 |

VALID: 54/54; wall min/max: 11.513/11.896 с.

