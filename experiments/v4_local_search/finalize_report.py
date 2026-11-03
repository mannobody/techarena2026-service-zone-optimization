"""Finalize derived report only after every declared quality series is complete."""
import json,re
from pathlib import Path
R=Path(__file__).resolve().parent
D=json.loads((R/'FINAL_METRICS.json').read_text())
required={'development60_clean':96,'development60_v3':96,'holdout60_tail':48,'huge180':6,'open60_tail':30,'regression60_repeat':12,'development60_cycle_repeat':48,'holdout60_cycle':48,'package_cycle_synthetic':28,'holdout60_cycle_variance':12}
for name,n in required.items():assert D['quality'].get(name,{}).get('runs')==n,(name,'incomplete')
lines=['\n<!-- final-results -->','## Итоговые сравнения и решение\n','Устойчивого улучшения полного solver не подтверждено. Критерий отсутствия','регрессий по медианам входов не выполнен; новые алгоритмы не приняты в defaults.','Полезность отдельных ходов подтверждена на общих checkpoint и внутри финальной','стадии, но не означает общего превосходства за тот же wall-бюджет.\n','Δ% = 100·(candidate−base)/max(1,|base|) для одинакового case/seed. Каждая пара имеет','одинаковый вес; это локальная метрика, а не оценка скрытого сервера. σ — стандартное','отклонение по наблюдавшимся парам. Число успехов — обе стороны серии вместе.\n','| Серия / вариант | Успехи | mean Δ% | median Δ% | min Δ% | max Δ% | σ | W/T/L |','|---|---:|---:|---:|---:|---:|---:|---|']
for name in required:
 if name in ('package_cycle_synthetic',):continue
 q=D['quality'][name]
 for v,c in q['comparisons'].items():
  d=c['paired_pct'];lines.append(f"| {name} / {v} | {q['success']}/{q['runs']} | {d['mean']:+.4f} | {d['median']:+.4f} | {d['worst']:+.4f} | {d['best']:+.4f} | {d['std']:.4f} | {'/'.join(map(str,c['wtl']))} |")
lines+=['\nПоследняя дополнительная серия включает только alphabig/large; её среднее нельзя','смешивать с исходным восьмиклассовым holdout с тем же весом каждого запуска.\n','### Разброс на шести seed\n','| Класс | mean парных Δ% | median парных Δ% | min | max | Отношение медиан целей, Δ% |','|---|---:|---:|---:|---:|---:|']
for c,z in D['variance_six_seed']['comparisons']['cycle']['cases'].items():
 d=z['paired'];lines.append(f"| {c} | {d['mean']:+.4f} | {d['median']:+.4f} | {d['worst']:+.4f} | {d['best']:+.4f} | {z['median_delta_pct']:+.4f} |")
lines+=['\n### Собственная финальная стадия\n','| Серия | Вызовы | Улучшения | mean Δ% к своему входу | max Δ% | max выход за локальный дедлайн, с |','|---|---:|---:|---:|---:|---:|']
for name in ['development60_v3','holdout60_tail','huge180','development60_cycle_repeat','holdout60_cycle','holdout60_cycle_variance']:
 z=D['tail_traces'][name];lines.append(f"| {name} | {z['calls']} | {z['improvements']} | {z['mean_pct']:.6f} | {z['max_pct']:.6f} | {z['max_deadline_overrun']:.6f} |")
lines+=['\nПолный эффект и собственный прирост стадии измеряют разное. Даже с одинаковым seed','NT2 и wall-остановка дают разные траектории до финальной стадии; последнее улучшение','не может причинно объяснить большой уже существовавший разрыв с отдельным baseline.','Стадия также расходует часть времени прежнего boundary B&B. Ни одна из этих оговорок','не отменяет отрицательный итог критерия принятия.\n','### Время и память\n','Ниже диапазон/среднее по всем вариантам каждой серии; полные mean/median/min/max/σ','по вариантам и целям каждого входа находятся в соответствующих `SUMMARY.json`.\n','| Серия | wall min / mean / max, с | max RSS, MiB | Успехи |','|---|---:|---:|---:|']
for name in required:
 q=D['quality'][name];v=list(q['variants'].values());rows=json.loads((R/'logs'/name/'results.json').read_text());ws=[x['wall'] for x in rows];lines.append(f"| {name} | {min(ws):.3f} / {sum(ws)/len(ws):.3f} / {max(ws):.3f} | {max(x['max_rss_kb'] for x in v)/1024:.2f} | {q['success']}/{q['runs']} |")
A=json.loads((R/'RUN_AUDIT.json').read_text());assert not A['cpu_overlap_conflicts']
lines+=['\n`RUN_AUDIT.json` проверяет интервалы завершённых канонических запусков: пересечений','по выделенным CPU не найдено. Это не контроль посторонней нагрузки системы. Там же','сохранены различия конечных назначений между seed и число разных наборов офисов;','это разнообразие результатов, не измерение внутренней популяции GWW.\n','### Что остаётся открытым\n','Сильнее обосновано улучшать выбор геометрической окрестности и доступ к хорошим','бассейнам, чем заменять DP или включать всю MILP-архитектуру v5. Следующая проверяемая','гипотеза — выбор соседних зон по ожидаемой совместной выгоде при сохранении задач','и счётчик реально построенных стартов без одновременного сокращения всех чанков.','Эти изменения здесь **не реализованы и не объявлены улучшением**.','Для принятия потребуется новое сравнение после фиксации кода на новом holdout.\n']
p=R/'REPORT.md';full=p.read_text();s=full.split('<!-- final-results -->')[0].rstrip();suffix=full.split('<!-- /final-results -->',1)[1] if '<!-- /final-results -->' in full else '';p.write_text(s+'\n'+'\n'.join(lines)+'\n<!-- /final-results -->'+suffix)
print('final report written')
