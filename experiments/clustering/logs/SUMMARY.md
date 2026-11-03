# Сохранённые измерения кластеризации

Дельты — отношение медиан score; все входы синтетические.

## balanced_teacher

Источник: ./experiments/clustering/logs/balanced_teacher/results.json
Строк: 18

{"rows": 18, "config": {"tag": "balanced_teacher", "only": "anti0,anti1,tightA0,multiskill0,alphabig0,medium0", "methods": "balanced_lp,balanced_geom_lp,road", "seed": 1, "base_seconds": 5.0, "ip_seconds": 3.0, "matched": true}, "improvements": [{"case": "tightA0", "method": "balanced_lp", "percent": 0.7238360672103816, "matched_percent": 3.487370692665137}, {"case": "tightA0", "method": "road", "percent": 0.7648257274671222, "matched_percent": 0.8562486651715551}], "algorithm_seconds": {"seconds": [0.08491864400093618, 4.307188714999938], "embedding_seconds": [0.0, 0.42223217399987334]}}

## embedding_metrics

Источник: ./experiments/clustering/logs/embedding_metrics/results.json
Строк: 32

{"rows": 32, "config": {"tag": "embedding_metrics", "only": "anti0,multiskill0,tightA0,grid0", "methods": "raw,rank,unit,positive,umap_high,umap_cosine,umap_manhattan,pca2", "seed": 1, "base_seconds": 5.0, "ip_seconds": 5.0, "matched": true}, "improvements": [{"case": "tightA0", "method": "raw", "percent": 0.5455614528220298, "matched_percent": 0.31493819013637125}, {"case": "tightA0", "method": "rank", "percent": 0.283585434546918, "matched_percent": 0.4866155177148279}, {"case": "tightA0", "method": "unit", "percent": 0.3142018776831401, "matched_percent": 0.0841092888462347}, {"case": "tightA0", "method": "positive", "percent": 0.5455614528220298, "matched_percent": 3.508640389627393}, {"case": "tightA0", "method": "umap_cosine", "percent": 0.3512672887278301, "matched_percent": 0.6488079942602143}, {"case": "tightA0", "method": "pca2", "percent": 0.5453721372498777, "matched_percent": 3.5084454949229738}], "algorithm_seconds": {"seconds": [0.04558410299978277, 7.014235925000321], "embedding_seconds": [1.8120008462574333e-06, 24.52929521599981]}}

## embedding_screen

Источник: ./experiments/clustering/logs/embedding_screen/results.json
Строк: 64

{"rows": 64, "config": {"tag": "embedding_screen", "only": "anti0,anti1,grid0,multiskill0,alphabig0,tightA0,medium0,cluster0", "methods": "geo,raw,pca2,spectral2,umap2,umap_high,tsne2,road", "seed": 1, "base_seconds": 5.0, "ip_seconds": 1.0, "matched": false}, "improvements": [{"case": "tightA0", "method": "pca2", "percent": 1.360267023471895, "matched_percent": null}, {"case": "tightA0", "method": "tsne2", "percent": 0.303933349113672, "matched_percent": null}], "algorithm_seconds": {"seconds": [0.04266753000047174, 3.696323575999486], "embedding_seconds": [0.0, 27.991988444000526]}}

## embedding_seed2

Источник: ./experiments/clustering/logs/embedding_seed2/results.json
Строк: 15

{"rows": 15, "config": {"tag": "embedding_seed2", "only": "anti0,tightA0,multiskill0", "methods": "raw,pca2,umap_high,tsne2,balanced_lp", "seed": 2, "base_seconds": 5.0, "ip_seconds": 3.0, "matched": true}, "improvements": [{"case": "tightA0", "method": "raw", "percent": 0.4184060429181846, "matched_percent": 0.8601086189891749}, {"case": "tightA0", "method": "balanced_lp", "percent": 0.3776875504798216, "matched_percent": 0.3776875504798216}], "algorithm_seconds": {"seconds": [0.1744957640003122, 3.625310981999064], "algorithm_seconds": [0.23506997199729085, 27.064315578998503], "embedding_seconds": [1.7890015442389995e-06, 24.239281526999548]}}

## embedding_seed3

Источник: ./experiments/clustering/logs/embedding_seed3/results.json
Строк: 15

{"rows": 15, "config": {"tag": "embedding_seed3", "only": "anti0,tightA0,multiskill0", "methods": "raw,pca2,umap_high,tsne2,balanced_lp", "seed": 3, "base_seconds": 5.0, "ip_seconds": 3.0, "matched": true}, "improvements": [{"case": "tightA0", "method": "pca2", "percent": 1.3657104926797947, "matched_percent": -1.8361558989733795}, {"case": "tightA0", "method": "tsne2", "percent": 0.303933349113672, "matched_percent": -2.3121283093221923}], "algorithm_seconds": {"seconds": [0.17513657699964824, 4.341777019999427], "algorithm_seconds": [0.23851660699983768, 41.429844954000146], "embedding_seconds": [1.8869995983550325e-06, 38.52290109800015]}}

## embedding_v2

Источник: ./experiments/clustering/logs/embedding_v2/results.json
Строк: 80

{"rows": 80, "config": {"tag": "embedding_v2", "only": "anti0,anti1,grid0,multiskill0,alphabig0,tightA0,medium0,cluster0", "methods": "geo,raw,pca2,spectral2,umap2,umap_high,tsne2,road,balanced_lp,balanced_geom_lp", "seed": 1, "base_seconds": 5.0, "ip_seconds": 2.0, "matched": true}, "improvements": [{"case": "tightA0", "method": "raw", "percent": 1.3262954442874397, "matched_percent": 0.6945388119905083}, {"case": "tightA0", "method": "pca2", "percent": 1.326105444144754, "matched_percent": 0.8940354722039912}, {"case": "tightA0", "method": "spectral2", "percent": 1.2705919122820042, "matched_percent": 0.6391825844595189}, {"case": "tightA0", "method": "tsne2", "percent": 0.2963004042310091, "matched_percent": -0.32903433930610015}, {"case": "tightA0", "method": "road", "percent": 1.3262954442874397, "matched_percent": 1.0904718381727907}, {"case": "tightA0", "method": "balanced_lp", "percent": 1.285238813953038, "matched_percent": 0.6537381645517648}], "algorithm_seconds": {"seconds": [0.041387467999811633, 4.1091926470016915], "algorithm_seconds": [0.05581591600093816, 24.507338333998632], "embedding_seconds": [0.0, 21.831429486999696]}}

## fill_screen

Источник: ./experiments/clustering/logs/fill_screen/results.json
Строк: 36

alphabig0: {"median_scores": {"base": 10594860.077636909, "fill": 10594860.077636909, "fill_all": 10364947.470618913}, "percent": {"fill": 0.0, "fill_all": -2.170039107012689}}
alphazero0: {"median_scores": {"base": 40011.716356981255, "fill": 40011.885638670334, "fill_all": 40012.11854897575}, "percent": {"fill": 0.00042308029870596897, "fill_all": 0.0010051855584114477}}
anti0: {"median_scores": {"base": 92397.64748921874, "fill": 92397.64748921874, "fill_all": 92397.64748921874}, "percent": {"fill": 0.0, "fill_all": 0.0}}
cluster0: {"median_scores": {"base": 35.37519021158633, "fill": 35.37519021158633, "fill_all": 35.37519021158633}, "percent": {"fill": 0.0, "fill_all": 0.0}}
deficit0: {"median_scores": {"base": 61.87886650439248, "fill": 61.87886650439248, "fill_all": 61.87886650439248}, "percent": {"fill": 0.0, "fill_all": 0.0}}
grid0: {"median_scores": {"base": 45.45436481908553, "fill": 45.485812267793705, "fill_all": 45.965125514097686}, "percent": {"fill": 0.06918466209646645, "fill_all": 1.1236779945007491}}
huge0: {"median_scores": {"base": 207729.66644039718, "fill": 240356.81775776422, "fill_all": 244427.90321658456}, "percent": {"fill": 15.706543931089678, "fill_all": 17.666343669173035}}
large0: {"median_scores": {"base": 75016.42325803511, "fill": 62142.02723057168, "fill_all": 69366.5884050629}, "percent": {"fill": -17.162103267945984, "fill_all": -7.531463921624725}}
medium0: {"median_scores": {"base": 316350.41414843075, "fill": 324567.6609583671, "fill_all": 324249.39367957896}, "percent": {"fill": 2.5975141622798237, "fill_all": 2.4969082314657776}}
multiskill0: {"median_scores": {"base": 58535.856331999006, "fill": 58535.856331999006, "fill_all": 58535.856331999006}, "percent": {"fill": 0.0, "fill_all": 0.0}}
small0: {"median_scores": {"base": 2437.0627724283304, "fill": 2437.0627724283304, "fill_all": 2437.0627724283304}, "percent": {"fill": 0.0, "fill_all": 0.0}}
tightA0: {"median_scores": {"base": 91529.54861547748, "fill": 91529.54861547748, "fill_all": 91529.54861547748}, "percent": {"fill": 0.0, "fill_all": 0.0}}

## native_repeat

Источник: ./experiments/clustering/logs/native_repeat/results.json
Строк: 60

alphabig0: {"median_scores": {"affine": 11162980.969001787, "base": 11162980.969001787, "mix": 11162980.969001787, "ot": 11162980.969001787, "schedule": 11162980.969001787}, "percent": {"affine": 0.0, "mix": 0.0, "ot": 0.0, "schedule": 0.0}}
anti0: {"median_scores": {"affine": 92397.64748921874, "base": 92397.64748921874, "mix": 92404.76307406348, "ot": 92397.64748921874, "schedule": 92397.64748921874}, "percent": {"affine": 0.0, "mix": 0.007701045468255785, "ot": 0.0, "schedule": 0.0}}
anti2: {"median_scores": {"affine": 262648.7552829272, "base": 262949.1366698831, "mix": 262827.35606030165, "ot": 263072.3337571634, "schedule": 262799.42171348527}, "percent": {"affine": -0.1142355478934376, "mix": -0.04631337114231471, "ot": 0.04685205999932496, "schedule": -0.056936850333066946}}
grid0: {"median_scores": {"affine": 45.826456373411034, "base": 45.826456373411034, "mix": 45.72546889094569, "ot": 45.826456373411034, "schedule": 45.7097451665916}, "percent": {"affine": 0.0, "mix": -0.22036939021088386, "ot": 0.0, "schedule": -0.2546808460781369}}
huge0: {"median_scores": {"affine": 317922.0298066872, "base": 316929.29551174893, "mix": 317792.40606221394, "ot": 314386.93526800745, "schedule": 316428.5372195479}, "percent": {"affine": 0.3132352575154984, "mix": 0.27233536397175406, "ot": -0.8021853074946295, "schedule": -0.15800315694781686}}
large0: {"median_scores": {"affine": 73719.9771674977, "base": 76243.50123875875, "mix": 74819.07526117872, "ot": 75086.1531005271, "schedule": 73599.20625192914}, "percent": {"affine": -3.3098218605656204, "mix": -1.868258873788342, "ot": -1.517962999374045, "schedule": -3.4682234470698403}}

## native_screen

Источник: ./experiments/clustering/logs/native_screen/results.json
Строк: 72

alphabig0: {"median_scores": {"affine": 10382932.221288681, "base": 10594860.077636909, "mix": 10467836.994063124, "ot": 10196791.711831564, "portfolio": 10196791.711831564, "schedule": 10196791.711831564}, "percent": {"affine": -2.0002893364826413, "mix": -1.1989123277040603, "ot": -3.7571837937300123, "portfolio": -3.7571837937300123, "schedule": -3.7571837937300123}}
alphazero0: {"median_scores": {"affine": 40067.67936249651, "base": 39985.45742252115, "mix": 40013.179300322896, "ot": 40011.716356981255, "portfolio": 39985.45742252115, "schedule": 40011.716356981255}, "percent": {"affine": 0.20562960955161635, "mix": 0.06932990039056897, "ot": 0.06567121186744629, "portfolio": 0.0, "schedule": 0.06567121186744629}}
anti0: {"median_scores": {"affine": 92397.64748921874, "base": 92397.64748921874, "mix": 92397.64748921874, "ot": 92397.64748921874, "portfolio": 92397.64748921874, "schedule": 92397.64748921874}, "percent": {"affine": 0.0, "mix": 0.0, "ot": 0.0, "portfolio": 0.0, "schedule": 0.0}}
cluster0: {"median_scores": {"affine": 35.37519021158633, "base": 35.37519021158633, "mix": 35.37519021158633, "ot": 35.37519021158633, "portfolio": 35.37519021158633, "schedule": 35.37519021158633}, "percent": {"affine": 0.0, "mix": 0.0, "ot": 0.0, "portfolio": 0.0, "schedule": 0.0}}
deficit0: {"median_scores": {"affine": 61.87886650439248, "base": 61.87886650439248, "mix": 61.87886650439248, "ot": 61.87886650439248, "portfolio": 61.87886650439248, "schedule": 61.87886650439248}, "percent": {"affine": 0.0, "mix": 0.0, "ot": 0.0, "portfolio": 0.0, "schedule": 0.0}}
grid0: {"median_scores": {"affine": 45.45436481908553, "base": 45.06093106293317, "mix": 45.130390060771326, "ot": 45.45436481908553, "portfolio": 45.45436481908553, "schedule": 45.965125514097686}, "percent": {"affine": 0.8731150175367519, "mix": 0.1541446130821189, "ot": 0.8731150175367519, "portfolio": 0.8731150175367519, "schedule": 2.0066040133562613}}
huge0: {"median_scores": {"affine": 270792.9576546614, "base": 191130.63746347724, "mix": 254259.61516216336, "ot": 273187.2505317954, "portfolio": 240058.7901136362, "schedule": 281747.735376425}, "percent": {"affine": 41.679513681529286, "mix": 33.02922992173314, "ot": 42.93221335799613, "portfolio": 25.599324786173305, "schedule": 47.41107920506129}}
large0: {"median_scores": {"affine": 71809.34239322817, "base": 74532.88662928282, "mix": 74532.88662928282, "ot": 74532.88662928282, "portfolio": 66854.09378461883, "schedule": 71716.73968292587}, "percent": {"affine": -3.6541510187324544, "mix": 0.0, "ot": 0.0, "portfolio": -10.30255661887528, "schedule": -3.77839511350756}}
medium0: {"median_scores": {"affine": 324328.8907431605, "base": 323354.305616628, "mix": 325553.2492166458, "ot": 324441.18610283226, "portfolio": 325650.2234495232, "schedule": 326641.8794759102}, "percent": {"affine": 0.3013985308388145, "mix": 0.6800415401379878, "ot": 0.3361268018780894, "portfolio": 0.7100316256859474, "schedule": 1.016709473842603}}
multiskill0: {"median_scores": {"affine": 58535.856331999006, "base": 58535.856331999006, "mix": 58535.856331999006, "ot": 58535.856331999006, "portfolio": 58535.856331999006, "schedule": 58535.856331999006}, "percent": {"affine": 0.0, "mix": 0.0, "ot": 0.0, "portfolio": 0.0, "schedule": 0.0}}
small0: {"median_scores": {"affine": 2437.0627724283304, "base": 2437.0627724283304, "mix": 2437.0627724283304, "ot": 2437.0627724283304, "portfolio": 2437.0627724283304, "schedule": 2437.0627724283304}, "percent": {"affine": 0.0, "mix": 0.0, "ot": 0.0, "portfolio": 0.0, "schedule": 0.0}}
tightA0: {"median_scores": {"affine": 91123.22848425282, "base": 91017.91595569423, "mix": 91529.54861547748, "ot": 91699.79546444492, "portfolio": 91699.79546444492, "schedule": 91529.54861547748}, "percent": {"affine": 0.11570527346489445, "mix": 0.5621230220567819, "ot": 0.7491706457908975, "portfolio": 0.7491706457908975, "schedule": 0.5621230220567819}}

## postfill_screen

Источник: ./experiments/clustering/logs/postfill_screen/results.json
Строк: 36

alphabig0: {"median_scores": {"base": 10490288.934470465, "postfill": 10196791.711831564, "postfill_all": 10591698.396613779}, "percent": {"postfill": -2.7977992262394835, "postfill_all": 0.9666984653786681}}
alphazero0: {"median_scores": {"base": 39985.45742252115, "postfill": 39985.45742252115, "postfill_all": 40069.06899005749}, "percent": {"postfill": 0.0, "postfill_all": 0.20910494196133556}}
anti0: {"median_scores": {"base": 92397.64748921874, "postfill": 92397.64748921874, "postfill_all": 92411.87865890822}, "percent": {"postfill": 0.0, "postfill_all": 0.015402090936489365}}
cluster0: {"median_scores": {"base": 35.37519021158633, "postfill": 35.37519021158633, "postfill_all": 35.37519021158633}, "percent": {"postfill": 0.0, "postfill_all": 0.0}}
deficit0: {"median_scores": {"base": 61.87886650439248, "postfill": 61.87886650439248, "postfill_all": 61.87886650439248}, "percent": {"postfill": 0.0, "postfill_all": 0.0}}
grid0: {"median_scores": {"base": 45.485812267793705, "postfill": 45.965125514097686, "postfill_all": 45.965125514097686}, "percent": {"postfill": 1.0537642891415677, "postfill_all": 1.0537642891415677}}
huge0: {"median_scores": {"base": 181099.6246675981, "postfill": 191130.63746347724, "postfill_all": 191130.63746347724}, "percent": {"postfill": 5.538947313828335, "postfill_all": 5.538947313828335}}
large0: {"median_scores": {"base": 74532.88662928282, "postfill": 74532.88662928282, "postfill_all": 70553.7103555575}, "percent": {"postfill": 0.0, "postfill_all": -5.338819484501167}}
medium0: {"median_scores": {"base": 325845.26553541824, "postfill": 314500.82159430376, "postfill_all": 326500.3769440689}, "percent": {"postfill": -3.481543278670518, "postfill_all": 0.20104984725624053}}
multiskill0: {"median_scores": {"base": 58535.856331999006, "postfill": 58535.856331999006, "postfill_all": 58535.856331999006}, "percent": {"postfill": 0.0, "postfill_all": 0.0}}
small0: {"median_scores": {"base": 2437.0627724283304, "postfill": 2437.0627724283304, "postfill_all": 2437.0627724283304}, "percent": {"postfill": 0.0, "postfill_all": 0.0}}
tightA0: {"median_scores": {"base": 91566.89189038765, "postfill": 91017.91595569423, "postfill_all": 91017.91595569423}, "percent": {"postfill": -0.5995354034191491, "postfill_all": -0.5995354034191491}}

## soft_repeat

Источник: ./experiments/clustering/logs/soft_repeat/results.json
Строк: 24

anti3: {"median_scores": {"base": 9712.372989409168, "soft": 9907.286976545074}, "percent": {"soft": 2.0068626621779107}}
huge0: {"median_scores": {"base": 322517.07846219116, "soft": 313095.0562270831}, "percent": {"soft": -2.9214025750306516}}
huge1: {"median_scores": {"base": 4012.009551126724, "soft": 4006.1565501126024}, "percent": {"soft": -0.14588701595882325}}
large0: {"median_scores": {"base": 76244.7590215529, "soft": 75065.83129196208}, "percent": {"soft": -1.5462410068835863}}

## soft_screen

Источник: ./experiments/clustering/logs/soft_screen/results.json
Строк: 24

alphabig0: {"median_scores": {"affine": 10617497.298709938, "base": 11155889.015800238, "soft": 11162980.969001787}, "percent": {"affine": -4.826076311155192, "soft": 0.06357138540464824}}
anti0: {"median_scores": {"affine": 92397.64748921874, "base": 92397.64748921874, "soft": 92397.64748921874}, "percent": {"affine": 0.0, "soft": 0.0}}
anti1: {"median_scores": {"affine": 238389.9378653995, "base": 238668.7579719087, "soft": 240623.6415096758}, "percent": {"affine": -0.11682304331680493, "soft": 0.8190781040546602}}
anti2: {"median_scores": {"affine": 262917.2971030247, "base": 260986.18677757104, "soft": 262215.3432666258}, "percent": {"affine": 0.7399281737080932, "soft": 0.4709661090616546}}
anti3: {"median_scores": {"affine": 9639.04961938991, "base": 10213.471865165451, "soft": 9663.025992559}, "percent": {"affine": -5.624162413710588, "soft": -5.389409985881766}}
grid0: {"median_scores": {"affine": 45.687787232724375, "base": 45.965125514097686, "soft": 45.687787232724375}, "percent": {"affine": -0.6033667443989699, "soft": -0.6033667443989699}}
huge0: {"median_scores": {"affine": 249228.09473016084, "base": 191130.63746347724, "soft": 297652.3929385861}, "percent": {"affine": 30.39672657283181, "soft": 55.732433527546796}}
large0: {"median_scores": {"affine": 74722.12267636255, "base": 74762.90692446454, "soft": 74567.54935758997}, "percent": {"affine": -0.0545514477429232, "soft": -0.26130279694974723}}

## territory_ip

Источник: ./experiments/clustering/logs/territory_ip/results.json
Строк: 8

[{"case": "anti0", "n": 600, "m": 10, "base": 92346.8715803789, "base_limit": 5.0, "source": "./experiments/clustering/logs/embedding_v2/anti0_base.solution.json", "matched": 92346.8715803789, "matched_wall": 5.240404144000422, "matched_limit": 5.437931528000263, "value": 92355.83130877004, "seconds": 0.4379315280002629, "status": "optimal", "candidates": 434, "variables": 520, "nodes": 1, "local_bound": 92355.83130877007, "solution": "./experiments/clustering/logs/territory_ip/anti0.solution.json"}, {"case": "anti1", "n": 600, "m": 10, "base": 222987.44817143417, "base_limit": 5.0, "source": "./experiments/clustering/logs/embedding_v2/anti1_base.solution.json", "matched": 237790.2653785368, "matched_wall": 6.708404473998598, "matched_limit": 6.840403086998776, "value": 224973.90525697387, "seconds": 1.8404030869987764, "status": "optimal", "candidates": 572, "variables": 607, "nodes": 1, "local_bound": 224973.90525697387, "solution": "./experiments/clustering/logs/territory_ip/anti1.solution.json"}, {"case": "tightA0", "n": 400, "m": 8, "base": 90958.87346017423, "base_limit": 5.0, "source": "./experiments/clustering/logs/embedding_v2/tightA0_base.solution.json", "matched": 91566.89189038765, "matched_wall": 6.85800365599971, "matched_limit": 7.024318007999682, "value": 92940.43175371307, "seconds": 2.024318007999682, "status": "timelimit", "candidates": 279, "variables": 370, "nodes": 1, "local_bound": 93072.55593485285, "solution": "./experiments/clustering/logs/territory_ip/tightA0.solution.json"}, {"case": "multiskill0", "n": 150, "m": 4, "base": 58535.856331999006, "base_limit": 5.0, "source": "./experiments/clustering/logs/embedding_v2/multiskill0_base.solution.json", "matched": 58535.856331999006, "matched_wall": 4.955184561000351, "matched_limit": 5.049379878000764, "value": 58535.856331999006, "seconds": 0.04937987800076371, "status": "optimal", "candidates": 125, "variables": 145, "nodes": 1, "local_bound": 58535.856331999006, "solution": "./experiments/clustering/logs/territory_ip/multiskill0.solution.json"}, {"case": "alphabig0", "n": 600, "m": 15, "base": 10118064.039163454, "base_limit": 5.0, "source": "./experiments/clustering/logs/embedding_v2/alphabig0_base.solution.json", "matched": 10196791.711831564, "matched_wall": 6.756246386999919, "matched_limit": 7.03129755000009, "value": 10118064.039163454, "seconds": 2.0312975500000903, "status": "timelimit", "candidates": 439, "variables": 627, "nodes": 1, "local_bound": 10559741.797504956, "solution": "./experiments/clustering/logs/territory_ip/alphabig0.solution.json"}, {"case": "medium0", "n": 600, "m": 8, "base": 322189.1256694718, "base_limit": 5.0, "source": "./experiments/clustering/logs/embedding_v2/medium0_base.solution.json", "matched": 323354.305616628, "matched_wall": 5.782237036999504, "matched_limit": 5.650916061998942, "value": 322189.1256694718, "seconds": 0.6509160619989416, "status": "optimal", "candidates": 571, "variables": 699, "nodes": 1, "local_bound": 322189.1256694715, "solution": "./experiments/clustering/logs/territory_ip/medium0.solution.json"}, {"case": "huge0", "n": 10000, "m": 25, "base": 191130.63746347724, "base_limit": 6.0, "source": "./experiments/clustering/logs/native_screen/huge0_base_s1.solution.json", "matched": 222139.5806285386, "matched_wall": 8.355816677001712, "matched_limit": 8.532255653999528, "value": 191130.63746347724, "seconds": 2.5322556539995276, "status": "timelimit", "candidates": 5020, "variables": 5379, "nodes": 0, "local_bound": 1e+20, "solution": "./experiments/clustering/logs/territory_ip/huge0.solution.json"}, {"case": "large0", "n": 3500, "m": 10, "base": 74532.88662928282, "base_limit": 6.0, "source": "./experiments/clustering/logs/native_screen/large0_base_s1.solution.json", "matched": 71266.81681978692, "matched_wall": 7.909183636000307, "matched_limit": 8.23629438700118, "value": 74532.88662928282, "seconds": 2.2362943870011804, "status": "timelimit", "candidates": 3271, "variables": 3560, "nodes": 1, "local_bound": 96430.33185015307, "solution": "./experiments/clustering/logs/territory_ip/large0.solution.json"}]

## territory_ip_corrected

Источник: ./experiments/clustering/logs/territory_ip_corrected/results.json
Строк: 2

[{"case": "huge0", "n": 10000, "m": 25, "base": 191130.63746347724, "base_limit": 6.0, "threads": 4, "source": "./experiments/clustering/logs/native_screen/huge0_base_s1.solution.json", "matched": 242882.41382417685, "matched_wall": 8.406708672000605, "matched_limit": 8.524809332999212, "value": 191130.63746347724, "seconds": 2.5248093329992116, "status": "timelimit", "candidates": 5020, "variables": 5379, "nodes": 0, "local_bound": 1e+20, "solution": "./experiments/clustering/logs/territory_ip_corrected/huge0.solution.json"}, {"case": "large0", "n": 3500, "m": 10, "base": 74532.88662928282, "base_limit": 6.0, "threads": 4, "source": "./experiments/clustering/logs/native_screen/large0_base_s1.solution.json", "matched": 75080.54037521283, "matched_wall": 8.252512205999665, "matched_limit": 8.297844945000179, "value": 74532.88662928282, "seconds": 2.297844945000179, "status": "timelimit", "candidates": 3271, "variables": 3560, "nodes": 1, "local_bound": 96430.33185015307, "solution": "./experiments/clustering/logs/territory_ip_corrected/large0.solution.json"}]

## territory_native

Источник: ./experiments/clustering/logs/territory_native/results.json
Строк: 24

alphazero0: {"median_scores": {"base": 40012.36579087662, "territory": 40013.179300322896}, "percent": {"territory": 0.002033145079516352}}
alphazero1: {"median_scores": {"base": 17086.847461029047, "territory": 17076.71698776716}, "percent": {"territory": -0.05928813542107614}}
alphazero2: {"median_scores": {"base": 189035.11683436765, "territory": 191033.78665865416}, "percent": {"territory": 1.0573008114877158}}
alphazero3: {"median_scores": {"base": 120434.30255443986, "territory": 119689.9052654444}, "percent": {"territory": -0.6180940755304953}}
