"""Fresh visual transcription of all seven supplied screenshots, then reconciliation."""
from pathlib import Path
from decimal import Decimal, getcontext
import hashlib, json

getcontext().prec = 40
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sources = [
    ('ours', 'Наша команда', 'source_screenshot.png', 'results_from_screenshot.json',
     '108192662.61 10194392.71 1333030389.14 1493452.56 1326703940.00 90329488.28 218311557.72 1014141055.42 15292966.23 489183.48 193.12 252494.29'),
    ('second_team', 'Вторая команда', 'second_team_screenshot.png', 'second_team_results.json',
     '92899395.65 9416285.99 1081476673.06 1488871.87 1188649774.13 89445875.58 219953014.64 976360205.62 15136206.11 526060.24 212.77 253713.19'),
    ('submission_1666091', '№1666091', 'submission_1666091_screenshot.png', 'submission_1666091_results.json',
     '96551157.51 9837951.99 1369441572.60 1477655.27 1316486251.62 90510795.33 220548498.26 1017937624.16 8375516.75 489105.46 214.98 255504.96'),
    ('result_125759', '23.10, 12:57:59', 'result_125759_screenshot.png', 'result_125759_results.json',
     '24776692.42 10736377.44 1208535856.77 1493452.56 1310791533.36 90799571.89 220902391.00 1035059103.56 14710911.62 524199.75 215.13 254697.89'),
    ('result_20261025_edaa0255', 'Скриншот 25.10', 'result_20261025_edaa0255_screenshot.png', 'result_20261025_edaa0255_results.json',
     '45755145.39 10454703.68 1408540997.13 1493349.06 1319092164.13 91364177.12 221133586.90 989117217.86 12448390.60 512088.08 214.39 254251.97'),
    ('result_20261027_e2dbb990', 'Скриншот 27.10', 'result_20261027_e2dbb990_screenshot.png', 'result_20261027_e2dbb990_results.json',
     '24776692.42 8875764.74 804698825.42 1493452.56 1206621034.85 87865629.78 210152385.66 578970801.49 6681617.15 514567.93 215.56 250729.90'),
    ('partial_c23ce513', 'Фрагмент №1–3', 'partial_c23ce513_screenshot.png', 'partial_c23ce513_observation.json',
     '0.00 9156896.85 962082968.29'),
]
records, differences = [], []
for key, label, screenshot, old_file, raw in sources:
    values = raw.split()
    stored = json.loads((ROOT / old_file).read_text())
    previous = [x['value_as_displayed'] for x in stored['tests']]
    if values != previous:
        differences.append(dict(source=old_file, before=previous, visually_rechecked=values))
    assert hashlib.sha256((ROOT / screenshot).read_bytes()).hexdigest() == stored['source_sha256']
    records.append(dict(key=key, label=label, screenshot=screenshot,
                        screenshot_sha256=stored['source_sha256'], previous_record=old_file,
                        values=values, complete=len(values)==12))
assert len(records) == 7 and sum(x['complete'] for x in records) == 6
comparison = []
for i in range(12):
    seen = [(Decimal(x['values'][i]), x) for x in records if i < len(x['values'])]
    best = max(v for v, x in seen)
    ours = Decimal(records[0]['values'][i])
    comparison.append(dict(test=i+1, ours=str(ours), maximum=str(best),
                           absolute_gap=str(best-ours), normalized=str(ours/best),
                           gap_fraction=str((best-ours)/best),
                           required_improvement_fraction=str(best/ours-1),
                           leader_keys=[x['key'] for v, x in seen if v==best],
                           leader_labels=[x['label'] for v, x in seen if v==best]))
scores = {x['key']: str(sum((Decimal(x['values'][i])/Decimal(comparison[i]['maximum']) for i in range(12)), Decimal(0)))
          for x in records if x['complete']}
old_max = json.loads((ROOT / 'current_observed_maxima.json').read_text())
old_scores = json.loads((ROOT / 'current_normalized_scores.json').read_text())
max_differences = [dict(test=x['test'], before=old_max['tests'][i]['maximum'], recomputed=x['maximum'])
                   for i,x in enumerate(comparison) if Decimal(x['maximum']) != Decimal(old_max['tests'][i]['maximum'])]
score_differences = [k for k,v in scores.items() if abs(Decimal(v)-Decimal(old_scores['scores'][k])) > Decimal('1e-30')]
result = dict(review_date='2026-10-27', scope='Только верхние строки на12 тестов; максимум по всем присланным читаемым значениям.',
              exclusions=['Нижние строки с33 прогонами относятся к другому набору.',
                          'У фрагмента прочитаны только№1–3; обрезанный№4 не восстанавливался.',
                          'Фрагмент учтён для максимумов, но не для рейтинга.',
                          'Команды для неназванных посылок не отождествлялись.'],
              source_records=records, comparison=comparison, scores=scores,
              ranking=sorted(scores, key=lambda k:Decimal(scores[k]), reverse=True),
              source_differences=differences, maxima_differences=max_differences,
              score_differences=score_differences)
(HERE / 'verified_data.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print('Reviewed:7 screenshots,6 complete results,1 partial,75 readable values.')
print('Differences:',len(differences),'maxima:',len(max_differences),'scores:',len(score_differences))
for x in comparison:
    print(x['test'],x['ours'],x['maximum'],x['absolute_gap'],f"{Decimal(x['gap_fraction'])*100:.6f}%",', '.join(x['leader_labels']))
assert not differences and not max_differences and not score_differences
