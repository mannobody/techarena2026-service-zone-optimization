from pathlib import Path

# Serialize an observation copy without altering commands or subprocess env.
import sys as _report_sys
_REPORT_ROOT = next(p for p in Path(__file__).resolve().parents
                    if (p / 'tools/public_metadata.py').is_file())
_report_sys.path.insert(0, str(_REPORT_ROOT / 'tools'))
from public_metadata import public_json as _public_json
def report_json(value, **kwargs):
    return _public_json(value, _REPORT_ROOT, **kwargs)

import json,statistics,hashlib,difflib,subprocess,tempfile
H=Path(__file__).resolve().parent;R=H.parents[1]
def read(n):return json.loads((H/'logs'/n/'results.json').read_text())
full=read('full_holdout60')['results'];edges=read('candidate_edges60')['results'];post=read('native_post_relative60');mip=read('milp_hard60');highs=read('highs60');warm=read('milp_warm60')
assert len(full)==60 and len(edges)==21 and len(post)==45 and len(mip)==25 and len(highs)==7 and len(warm)==3
assert all(r['error'] is None and r['rc']==0 for r in full+edges+post)
assert all(not r.get('rejected') for r in mip+warm)
by={(r['case'],r['seed'],r['variant']):r for r in full};cases=sorted({r['case'] for r in full});deltas=[];table=[]
for c in cases:
 ds=[100*(by[c,s,'candidate']['score']-by[c,s,'base']['score'])/max(1e-9,abs(by[c,s,'base']['score'])) for s in [111,112,113]];deltas+=ds
 table.append('| '+c+' | '+' | '.join(f'{v:+.4f}%' for v in ds+[statistics.mean(ds),statistics.median(ds)])+' |')
pby={(r['case'],r['mode']):r for r in post};mt=[]
for c in ['controlled_dense_load','controlled_count_tight','controlled_many_sites','ordinary_huge0','ordinary_alphabig0','ordinary_latent0']:
 vals=[1000*pby[c,m]['stats']['dp_seconds']/pby[c,m]['stats']['repeats'] for m in ['0','2']]
 mt.append(f'| {c} | {vals[0]:.4f} | {vals[1]:.4f} | {vals[0]/vals[1]:.2f}× |')
ct=[]
for c in ['controlled_count_gap','controlled_dense_load','controlled_count_tight','controlled_gcd_large','controlled_many_sites']:
 a=next(r for r in mip if r['case']==c);b=next(r for r in highs if r['case']==c)
 ct.append(f"| {c} | {pby[c,'0']['score']:.6f} | {pby[c,'2']['score']:.6f} | {a['value']:.6f} / {a['process_wall']:.3f} с | {b['value']:.6f} / {b['process_wall']:.3f} с |")
summary=dict(runs=len(full),valid=len(full),mean_pair_pct=statistics.mean(deltas),median_pair_pct=statistics.median(deltas),worst_pair_pct=min(deltas),best_pair_pct=max(deltas),wins=sum(x>1e-8 for x in deltas),ties=sum(abs(x)<=1e-8 for x in deltas),losses=sum(x< -1e-8 for x in deltas),max_wall=max(r['wall'] for r in full),edge_valid=len(edges),edge_max_wall=max(r['wall'] for r in edges))
(H/'SUMMARY.json').write_text(report_json(summary,indent=2))
v=H.parent/'server_v4';vm=json.loads((v/'MANIFEST.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(vm['zip'])==vm['sha256']
assert all(sha(p)==s for p,s in vm['primary_snapshot'].items())
assert sha(H/'artifacts/relative_v1.cpp')==json.loads((H/'PREREGISTRATION.json').read_text())['sha256']
with tempfile.TemporaryDirectory(prefix='dp-patch-') as d:
 p=Path(d)/'main.cpp';p.write_bytes((v/'artifacts/package/main.cpp').read_bytes());subprocess.run(['patch','-p1','-i',str(H/'artifacts/v4_dp_experimental.patch')],cwd=d,check=True,capture_output=True);assert sha(p)==sha(H/'artifacts/relative_v1.cpp')
text=f'''# DP и MILP после сборки v4 — 19 октября 2026

## Результат

Серверная v4 остаётся зафиксированной: `../server_v4/artifacts/case03_cpp_server_v4_O3.zip`, SHA256 `{vm['sha256']}`. В неё вошли allocation reuse v3, genetic warm start, worker DFS, точная binary64-геометрия, spatial grid и final boundary B&B24. Флаги `-O3 -std=c++17`; default280 с. Package60 NT2 SEED101:36/36 VALID, B&B oracle96/96. На сервер ничего не отправлено. Подробности в `../server_v4/README.md`.

MILP действительно расширяет условную подзадачу: одновременно учитывает прибыль, нагрузку, количество сайтов и при необходимости работников. Но замена каждого вызова DP на MILP не обоснована: DP работает за миллисекунды, а MIP может исчерпать60 с. Реализованы и проверены оба подхода, а не только предложена модель.

Новый native DP ускоряет крупные вызовы, однако полный поиск требует отдельной оценки. На новых10 задачах ×3 seed при одинаковых60 с: среднее парное изменение **{summary['mean_pair_pct']:+.4f}%**, медиана **{summary['median_pair_pct']:+.4f}%**, wins/ties/losses **{summary['wins']}/{summary['ties']}/{summary['losses']}**, худшая пара **{summary['worst_pair_pct']:+.4f}%**. Поэтому экспериментальный DP не включён в v4. Это30 пар, а не доказательство поведения на скрытых данных.

## Что именно решает старый DP

В `solver/dp.h` для каждого открытого офиса строится `f_o[w]`: максимальная прибыль подмножества уже назначенных сайтов с суммарным числом задач ровноw. Работники и принадлежность сайтов фиксированы. Удаление сайтов сжимает выпуклую оболочку и сохраняет навыки/геометрическую допустимость. Это позволяет исключить геометрию из данной условной подзадачи.

Затем перебирается общее окно нагрузки[L,R], и каждый офис выбирает лучший уровень внутри окна; из суммы вычитается `alpha*(R-L)`. Можно закрывать офисы. При Wmax≤2500 перебираются все целые границы, иначе используется около600 узлов плюс текущие нагрузки.

Сложность рюкзака `O(Σ n_o W_o)`, хранения восстановления `O(Σ n_o W_o)` бит; есть отсечка бюджета200 млн переходов. Окна требуют `O(K G²)`, где K — число офисов, G — размер сетки. Отсечка применяется до построения DP.

Комментарий в исходнике о «точном выборе» требует оговорки: состояние не содержит число сайтов. Ограничение maxDifference исправляется позднее через `repair_sizes`, что может разрушить лучший баланс нагрузки. Грубая сетка также не гарантирует полного оптимума. При alpha≤0 код удаляет отрицательные сайты, после чего ремонт количества тоже может потерять прибыль.

Минимальный воспроизводимый контрпример `data/controlled/count_gap.json`: два офиса, веса сайтов[2,1,1], прибыли[100,−20,−20] и[−100,60,60], maxDifference0, alpha70. DP выбирает одинаковые нагрузки2, но разное количество сайтов1 и2. После ремонта получается90. Совместный выбор одного сайта в каждом офисе даёт `100+60−70=90`, а двух сайтов в каждом — `80+120−70=130`. MILP находит130; полный перебор подтверждает оптимум.

## Ускорение без внешних библиотек

В `src/window_v3.h` реализован проход по правой границе окна с монотонными стеками максимумов каждого офиса и деревом отрезков с прибавлением на диапазоне. Для фиксированногоR дерево хранит для каждогоL сумму лучших офисных вкладов минус штраф за ширину окна. При продвиженииR максимум каждого офиса меняется на суффиксе диапазоновL. Каждая запись стека добавляется/удаляется один раз; изменение диапазона стоитlogG. Итого **O(K G logG)**, дополнительная памятьO(KG+G). Для G≤128 оставлен прямой перебор: дерево не всегда окупает накладные расходы.

Сохранена семантика исходной сетки: значение точно вL и максимум по блокам `(grid[j−1],grid[j]]` обрабатываются отдельно. Отдельный счётчик недостижимых офисов нужен при allow_close=false. Отрицательные офисные вклады обнуляются только если закрытие разрешено. Это тот же целевой функционал сетки, но порядок обхода, разрешение равенств и точность арифметики могут менять выбранный набор.

Дополнительно используется общий gcd положительных чисел задач: веса делятся наg, alpha умножается наg. Это точная смена единиц нагрузки; для g>1 меняется и разрешение дискретной сетки. На специально созданном gcd_large старый DP пропускался из-за бюджета, а новый за14.09 мс получал134248.199183 вместо115744.783797 (+15.986%). MIP подтвердил тот же условный оптимум. Этот выигрыш нельзя переносить на веса с gcd1.

При разработке обнаружена численная ошибка v2: при alpha1e10 вычитание больших `alpha*absolute_load` давало618.099998474 вместо618.1. Сохранён проваленный oracle (`logs/window_oracle_v2.stderr`). v3 хранит относительные значения и вычитает только приращение ширины окна. Финальный oracle:3000 случайных задач, G≤400, отрицательные прибыли, пропущенные нагрузки, закрытие/без закрытия, крупныеalpha; совпадение с квадратичным эталоном. Первая версия также прошла10000 меньших задач. Это тестирование, не универсальная гарантия точности floating point.

Среднее время одного вызова, 5 повторов одного фиксированного состояния, NT1, O3; восстановление исходного Sol и официальный validator вне замера. Микрозамеры выполнены при нескольких процессах, абсолютные времена зависят от нагрузки машины.

| Задача | Старый DP, мс | Новый DP + gcd, мс | Отношение старый/новый |
|---|---:|---:|---:|
{chr(10).join(mt)}

45/45 выходов валидны. На всех10 обычных исходных состояниях результат выбора не изменился. Ускоряется не каждый размер: на маленьких DP накладные расходы могут преобладать. После оптимизации окон на10k основную долю занимает сам рюкзак.

## MILP: модель и область точности

Для каждого доступного сайту офиса вводится binary x_s, для офиса binary y_o. Здесь сайт имеет единственного владельца в заданной зоне. `n_o=Σx_s`, `w_o=Σtasks_s*x_s`. Ограничения: `y_o≤n_o≤capacity_o*y_o`, `x_s≤y_o`; для каждой упорядоченной пары офисов `n_o−n_p≤A+capacity_o*(2−y_o−y_p)`. Это включает баланс количества только для открытых офисов.

Непрерывные H,L с0≤L≤H≤T ограничивают нагрузки: `w_o≤H`, `L≤w_o+T*(1−y_o)`. T — безопасная верхняя граница суммы задач одного пула. Максимизируется `Σprofit_s*x_s−Σcost_o*y_o−alpha*(H−L)`. При alpha>0 оптимальный размах соответствует реальным крайним нагрузкам открытых офисов. Пустое решение допускается и имеет0.

Реализованы три пула: **assigned** — только уже назначенные сайты и те же работники; **territory** — также доступные сайты внутри текущей выпуклой оболочки, покрываемые текущими навыками; **joint** — тот же геометрический пул, но binary назначения работников с уникальностью работника и покрытием каждого требуемого навыка. Переносов между зонами и новых внешних границ здесь нет. Все полученные решения проверяются официальным валидатором, ухудшения отбрасываются.

SCIP и HiGHS независимо совпали с полным перебором на40 маленьких задачах каждый:12 сайтов,3 офиса, перебор4096 подмножеств, разныеA/alpha, нулевые веса и отрицательные прибыли. Статус optimal означает доказательство для данного условного пула в допусках MIP solver, не оптимальность полной геометрической задачи.

| Контролируемая задача | Старый DP | Новый DP | SCIP: score / wall | HiGHS с DP warm start: score / wall |
|---|---:|---:|---:|---:|
{chr(10).join(ct)}

На первых четырёх задачах оба MIP доказали условный оптимум. На many_sites оба остановлены внешним60-секундным deadline без доказательства. HiGHS дал435086.264244, то есть+0.38773% к DP433405.831705. SCIP без DP warm start дал433389.246292; с дополнительным стартом от DP —433414.273386. Поэтому результат зависит не только от формулировки, но и от solver/начального решения. Для HiGHS старт от DP использовался во всех7 случаях, для основной таблицы SCIP — исходный incumbent; отдельный SCIP warm эксперимент есть в `logs/milp_warm60`.

На10 обычных решениях assigned-MILP SCIP ничего не улучшил и доказал условную оптимальность. Добавление доступных сайтов внутри зоны дало alphabig0 +0.02572%, tightA0 +0.03689%, huge0 +0.00307%; multi/latent1 без прибавки. Joint не улучшил territory; на huge0 исчерпал лимит, сохранив исходное решение. Это аргумент в пользу редких расширенных окрестностей, а не вызова общего MIP на каждой итерации LNS.

Постобработка получает до60 с **после** построения incumbent: её score нельзя сравнивать с исходным полным solver как результат за одинаковое суммарное время. Сравнение полного native-кандидата ниже имеет равный общий бюджет.

## Полный solver: независимые60 секунд

До запуска зафиксированы исходник и SHA в `PREREGISTRATION.json`. Новые10 входов seeds241000+, latent242000/242001, solver seeds111/112/113, TL60, NT2, jobs6; baseline — frozen v4, candidate — relative_v1 с DP_MODE2. Тесты используют те же данные для пар, но многопоточность и расписание дают шум. Три seed недостаточны для уверенного ранжирования близких вариантов. Настройки не подгонялись после просмотра holdout.

| Задача | seed111 | seed112 | seed113 | Среднее парное | Медиана парная |
|---|---:|---:|---:|---:|---:|
{chr(10).join(table)}

Крупная регрессия разобрана отдельно: large0 имеет3500 сайтов, A116, alpha0.9318496. В seed111/112 база открыла9 офисов, кандидат8 — отсутствует офис5. Seed111: прибыль190292.9733 против173180.5403, стоимость11360.3401 против9694.4792, штраф209.6662 против215.2573. Почти вся потеря связана с выбором набора офисов и обслуживаемых сайтов, а не со штрафом за нагрузку. В seed113 оба нашли9 офисов, и кандидат выиграл0.8028%. Лог seed111 показывает5143 рассмотренных набора у базы против9964 у кандидата; простого объяснения «стало меньше итераций» нет. Это подтверждает разные траектории поиска, но не устанавливает первопричину: вклад порядка равных DP-решений, численной арифметики и расписания потоков отдельно не изолирован. Нельзя списывать воспроизводимый провал двух seed просто на шум. Для дальнейшего разбора нужен replay одинаковых промежуточных состояний с записью выбранных окон/сайтов и ремонтов, затем новое независимое A/B.

Все60/60 VALID; max wall {summary['max_wall']:.3f} с. Отдельно21/21 edge/precision VALID при60 с NT2, max wall {summary['edge_max_wall']:.3f} с. Все исходные результаты, stderr, входы и решения сохранены. Нельзя складывать ускорение DP и прирост полного score: алгоритм с ограничением времени иначе проходит случайные ветви и взаимодействует с shared elite.

## Лимит времени и воспроизводимость

Первые25 SCIP запусков имели только внутренний лимит: два process wall превысили60 с (66.133 и62.579). Эти сырые логи сохранены в `logs/milp60`, но итоговая таблица использует повтор **всех25 моделей** с внешним cutoff60, внутренним58 и сохранением валидных промежуточных решений. При прерывании возвращается checkpoint или исходное решение. ОС завершение/очистка дали максимум60.104 с для SCIP и60.116 с для HiGHS; это явно не утверждение wall≤60.000. Все25+3 SCIP и7 HiGHS итогов прошли validator. Native полный solver уложился в60 с по измеренному wall.

Среда: GCC16.2.1, Python `/tmp/ta-boundary-venv/bin/python`, numpy2.5.4, scipy1.18.1, highspy1.15.1, PySCIPOpt6.3.0. CPU affinity22 логических CPU, без pinning; full/edge частично шли одновременно, фоновые MIP могли кратко конкурировать заCPU. Сравнивать миллисекунды как стабильный hardware benchmark нельзя. Воспроизводятся входы/протокол, а не битовые результаты wall-limited многопоточного поиска.

Артефакты: `artifacts/relative_v1.cpp` и бинарник; `artifacts/post_relative.cpp`; `src/window_v3.h`; `milp_checkpoint.py`, `milp_warm.py`, `highs_selection.py`; `artifacts/v4_dp_experimental.patch`. Patch применяется только к распакованному v4/main.cpp, даёт байт-в-байт протестированный relative_v1.cpp. Он не применён к primary solver и не рекомендован как новая серверная default-сборка. Основные исходники сверены с snapshot v4 и не изменены. Полный перечень абсолютных путей к скриптам, исходникам, бинарникам, данным и логам — `PATHS.json`; корень исследования: `./experiments/dp_milp`.

Повтор полного A/B (новый tag, чтобы не затирать логи):

```sh
/tmp/ta-boundary-venv/bin/python experiments/dp_milp/bench_full.py --tag repeat_full60 --split full_holdout --variants base,candidate --seeds 111,112,113 --seconds 60 --threads 2 --jobs 6 --exe relative_v1
/tmp/ta-boundary-venv/bin/python experiments/dp_milp/bench_post.py --tag repeat_post60 --exe post_relative
```

Остальные runner-скрипты и параметры сохранены рядом. `SUMMARY.json` — агрегат full A/B; `MANIFEST.json` — абсолютные пути и hashes финальных исходников/логов. Прежние архивы и проваленные эксперименты сохранены. Коммитов, staging и server submission не было.

## Другие подходы и следующие обоснованные шаги

**Группировка одинаковых весов и max-plus свёртка.** В работе Grage–Jansen–Schumacher, WADS2025, описаны связь рюкзака со свёрткой и группировка одинаковых весов: отсортированные прибыли образуют вогнутые последовательности; приведён одномерный результат O(n+DW), D — число разных весов. Для наших частых весов1..5 это более предметное направление, чем общий MIP. Но нужно переносить алгоритм на exact-load состояния, отрицательные прибыли и восстановление; в текущем эксперименте он **не реализован**. [Статья, раздел1.2](https://drops.dagstuhl.de/storage/00lipics/lipics-vol349-wads2025/html/LIPIcs.WADS.2025.30/LIPIcs.WADS.2025.30.html).

**DP по количеству и нагрузке** `f_o[count][load]` исправляет выявленный дефект, но добавляет измерение. При равных весах количество уже определяется нагрузкой; при малом числе особых весов полезна специализация. Полная плотная таблица на больших n может оказаться тяжелее MIP. Это вывод из структуры нашей модели, не измеренный результат реализации.

**Разреженный DP** полезен при малом числе достижимых сумм; для весов1..5 суммы быстро уплотняются. Обычное правило доминирования «меньший вес и большая прибыль лучше» здесь неверно: другой офис может иметь нагрузку2, и состояние(нагрузка2, прибыль9) выигрывает у(нагрузка1, прибыль10) при большомalpha. Нагрузка — цель баланса, а не только расход вместимости.

**Редкий MILP-polish** перспективен для жёсткого count balance, большого диапазона нагрузок без полезногоgcd и расширенных territory/worker окрестностей. Нужны DP warm start, ограниченный пул переменных, жёсткий внешний deadline и checkpoint. HiGHS реализует MIP через branch-and-cut, поэтому отсутствие псевдополиномиальной осиW не означает предсказуемое время поиска. [Официальная документация HiGHS](https://ergo-code.github.io/HiGHS/dev/solvers/). SCIP предоставляет и отдельные knapsack routines; выбор MILP не отменяет специализированные алгоритмы внутри solver. [SCIP knapsack API](https://www.scipopt.org/doc/html/cons__knapsack_8h.php).

Практическое решение сейчас: загружать зафиксированную v4; ускоренный DP хранить как отдельный исследовательский кандидат; MILP использовать как проверочный oracle и перспективную редкую окрестность. Включение SCIP/HiGHS в серверный C++ требует отдельной проверки доступности библиотек и формата сборки; текущий ZIP не имеет этих зависимостей.
'''
(H/'REPORT.md').write_text(text)
paths=[H/'artifacts/relative_v1.cpp',H/'artifacts/post_relative.cpp',H/'artifacts/v4_dp_experimental.patch',H/'src/window_v3.h',H/'REPORT.md',H/'SUMMARY.json',H/'PREREGISTRATION.json',H/'PATHS.json',H/'logs/final_mip_validation.json']+[H/'logs'/n/'results.json' for n in ['full_holdout60','candidate_edges60','native_post_relative60','milp_hard60','milp_warm60','highs60']]
(H/'MANIFEST.json').write_text(report_json(dict(status='Research complete; v4 unchanged; no default integration',v4_sha256=vm['sha256'],primary_snapshot_unchanged=True,patch_reconstructs_tested_candidate=True,files={str(p):sha(p) for p in paths}),indent=2))
print(report_json(summary,indent=2))
