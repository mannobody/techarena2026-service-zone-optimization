from pathlib import Path
import json
H=Path(__file__).resolve().parent;md=['# Короткие геометрические ограничения в локальном SCIP','', 'Все лимиты60 с, SCIP1 поток, jobs3, radius16, ближайшая пара активных офисов, прежняя модель ресурсов без изменений. Одна детерминированная конфигурация SCIP (его seed не менялся), без повторов процесса. Параметры генераторов и базовые incumbents — в manifest и bench_anchor*.py. Это дополнительные локальные60 с; сравнение с полным solver за суммарные120 с не проводилось.','']
for tag in ['anchor60_v2','anchor_holdout60']:
 rows=json.loads((H/'logs'/tag/'results.json').read_text());assert len(rows)==(9 if tag=='anchor60_v2' else 6)
 md +=[f'## {tag}', '', '| Вход | Вариант | Цель | Δ incumbent | Время | Статус | Cuts | Nodes |','|---|---|---:|---:|---:|---|---:|---:|']
 for r in sorted(rows,key=lambda r:(r['case'],r['variant'])):
  assert 'error' not in r
  md.append(f'| {r["case"]} | {r["variant"]} | {r["value"]:.10g} | {100*(r["value"]/r["before"]-1):+.5f}% | {r["seconds"]:.3f} | {r["status"]} | {r["cuts"]} | {r["nodes"]} |')
 md+=['']
md +=['Все15 решений прошли официальный валидатор внутри local_mip.improve. Optimal относится к выбранной паре офисов, пулу кандидатов и Hamming-radius16, не ко всей исходной задаче.','', 'Первый запуск anchor60 не начал оптимизацию из-за отсутствующего SciPy:6 import failures сохранены. После установки scipy1.18.1 в /tmp/ta-boundary-venv выполнена отдельная серия anchor60_v2. SciPy/SCIP отсутствуют в конкурсном ZIP.','']
(H/'ANCHOR_RESULTS.md').write_text('\n'.join(md))
