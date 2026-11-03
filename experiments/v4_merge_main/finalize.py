from pathlib import Path
import hashlib, json, subprocess, zipfile

H = Path(__file__).resolve().parent
R = H.parents[1]
checks = json.loads((H / 'CHECKS.json').read_text())
assert checks['base_sha'] == json.loads((H / 'PARENTS.json').read_text())['main']
assert len(checks['tests']) == 2
assert [len(t['processes']) for t in checks['tests']] == [28, 30]
for test in checks['tests']:
    assert test['rc'] == 0
    assert all(p['rc'] == 0 and p['threads'] == '2' for p in test['processes'])
    text = (H / (test['tag'] + '.txt')).read_text()
    assert 'INVALID' not in text and ' TIME' not in text
geom = json.loads((H / 'geometry_state.json').read_text())
assert len(geom) == 4 and all(r['rc'] == 0 for r in geom)
rows = []
for line in (H / 'ab60.txt').read_text().splitlines():
    c = line.split()
    if len(c) == 6 and c[0].isdigit():
        rows.append(dict(instance=c[0], median=float(c[1]), maximum=float(c[2]), wall=float(c[3]),
                         baseline=float(c[4]), delta=c[5]))
assert len(rows) == 5
flat = ''.join((R / 'solver' / line.split('"')[1]).read_text() if line.startswith('#include "') else line
               for line in (R / 'solver/solve.cpp').read_text().splitlines(True))
with zipfile.ZipFile(R / 'dist/case03_cpp.zip') as z:
    assert sorted(z.namelist()) == ['Makefile', 'main.cpp']
    assert z.read('main.cpp') == flat.encode()
    assert z.read('Makefile') == (R / 'submission/cpp/Makefile').read_bytes()
source_hash = hashlib.sha256(flat.encode()).hexdigest()
processes = checks['tests'][1]['processes']
max_head = max(p['wall'] for p in processes if Path(p['command'][0]).name == 'solve')
max_base = max(p['wall'] for p in processes if Path(p['command'][0]).name == 'solve_base')
table = '| Вход | Медиана объединённой версии | Медиана main | Изменение |\n|---|---:|---:|---:|\n'
for row in rows:
    table += f"| {row['instance']} | {row['median']:.3f} | {row['baseline']:.3f} | {row['delta']} |\n"
doc = R / 'docs/v4.md'
s = doc.read_text()
old = ('(NT=2 на текущей машине), вместо NT=3 в исторической проверке выше. Результаты новых\n'
       'прогонов добавляются после завершения; прежние цифры не относятся к объединённой версии.\n')
marker = '(NT=2 на текущей машине), вместо NT=3 в исторической проверке выше.'
assert s.count(marker) == 1
new = ('(NT=2 на текущей машине), вместо NT=3 в исторической проверке выше.\n\n'
       'Проверки после разрешения конфликтов: синтетика 28/28 VALID, A/B60 × 3 seed —\n'
       '30/30 процессов завершились нормально, все 15 ответов объединённой версии валидны. Во всех запусках NT=2.\n'
       f'Максимальное время объединённой версии {max_head:.3f} с, базы {max_base:.3f} с.\n\n'
       + table + '\n'
       'Эти данные проверяют объединённую версию относительно актуального main; исторические\n'
       'цифры выше относятся к исходной v4. Небольшие различия могут лежать в пределах шума.\n'
       'Критерий устойчивого прироста на скрытых тестах этим прогоном не установлен.\n\n'
       f'SHA256 объединённого `main.cpp`: `{source_hash}`. Штатный ZIP пересобран и\n'
       'проверен через `make build` после распаковки.\n')
regressions = [r for r in rows if float(r['delta'].rstrip('%')) < -1]
if regressions:
    new += ('\n**Блокер качества перед merge:** в этом A/B есть регрессия более 1% по медиане ('
            + ', '.join('inst' + r['instance'] + ' ' + r['delta'] for r in regressions)
            + '). Правило main о недопустимости регрессий не выполнено. Разрешение конфликтов '
              'и проверки допустимости завершены, но эту серию нельзя считать успешной проверкой качества.\n')
doc.write_text(s[:s.index(marker)] + new)
journal = R / 'EXPERIMENTS.md'
s = journal.read_text()
assert 'Разрешение конфликтов v4 с main e600dde' not in s
deltas = ', '.join('inst' + r['instance'] + ' ' + r['delta'] for r in rows)
s += ('| 10-19 | Codex | research/service-zone-v4 | Разрешение конфликтов v4 с main e600dde: точная геометрия + кеш/defer, genetic + parallel phase1 | '
      f'Geometry state25600/25600; synth10 NT2:28/28 VALID; A/B60 NT2 ×3:30/30 процессов rc0, head15/15 VALID, {deltas}; max wall {max_head:.3f}с. ZIP rebuild OK | '
      + ('Регрессия >1%: критерий качества main НЕ выполнен; ' if regressions else '') + 'Изменения main сохранены, O3; docs/v4.md. Без коммита/push; качество на скрытых не доказано |\n')
journal.write_text(s)
(H / 'SUMMARY.json').write_text(json.dumps(dict(checks=checks,rows=rows,geometry_checks=25600,
    source_sha256=source_hash,max_head_wall=max_head,max_base_wall=max_base,zip_rebuilt=True),indent=2))
print(table)
print('Max wall head/base', max_head, max_base)
