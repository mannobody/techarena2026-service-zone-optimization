from pathlib import Path
import json, hashlib, subprocess, re, zipfile

H = Path(__file__).resolve().parent
R = H.parents[1]
checks = json.loads((H / 'CHECKS.json').read_text())
assert len(checks['tests']) == 2
assert all(t['rc'] == 0 for t in checks['tests'])
synth = (H / 'synth10.txt').read_text()
ab = (H / 'ab60.txt').read_text()
assert 'INVALID' not in synth + ab and ' TIME' not in synth + ab
rows = []
for line in ab.splitlines():
    cols = line.split()
    if len(cols) == 6 and cols[0].isdigit():
        rows.append(dict(instance=cols[0], median=float(cols[1]), maximum=float(cols[2]),
                         wall=float(cols[3]), baseline=float(cols[4]), delta=cols[5]))
assert len(rows) == 5
assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=R, text=True).strip() == checks['branch']
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=R, text=True).strip() == checks['base_sha']
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=R, text=True).strip()
with zipfile.ZipFile(R / 'dist/case03_cpp.zip') as z:
    assert hashlib.sha256(z.read('main.cpp')).hexdigest() == checks['source_sha256']
    assert z.read('Makefile') == (R / 'submission/cpp/Makefile').read_bytes()
flat = ''.join((R / 'solver' / line.split('"')[1]).read_text() if line.startswith('#include "') else line
               for line in (R / 'solver/solve.cpp').read_text().splitlines(True))
assert hashlib.sha256(flat.encode()).hexdigest() == checks['source_sha256']
summary = dict(checks=checks, rows=rows, index_empty=True, head_unchanged=True,
               zip_payload_unchanged=True, note='bench reports head validity; A/B compares per-instance medians')
(H / 'SUMMARY.json').write_text(json.dumps(summary, indent=2))
table = '| Вход | Медиана v4 | Медиана базы | Изменение | Max wall v4, с |\n|---|---:|---:|---:|---:|\n'
for row in rows:
    table += f"| {row['instance']} | {row['median']:.3f} | {row['baseline']:.3f} | {row['delta']} | {row['wall']:.1f} |\n"
regressions = any(float(row['delta'].rstrip('%')) < -1 for row in rows)
verdict = ('В A/B есть регрессия более 1% по медиане: перенос версии выполнен, но критерий '
           'репозитория о качестве перед PR не подтверждён. Это не основание заявлять улучшение.'
           if regressions else 'В этой проверке регрессий более 1% по медианам не обнаружено; '
           'дополнительное подтверждение качества выполняется в CI при открытии PR.')
doc = R / 'docs/v4.md'
text = doc.read_text()
old = ('Результаты текущего прогона будут добавлены после завершения. Для A/B используется\n'
       'локальная ссылка `origin/main`; базовый коммит фиксируется вместе с результатами.\n')
new = ('19 октября 2026: синтетика **28/28 VALID**, код возврата 0, без TIME по порогу\n'
       '`bench.py`. A/B: 5 входов × 3 seed для каждой версии, общий лимит 60 секунд,\n'
       'NT=3, `--par 6`, обе версии собраны с O3. Код возврата benchmark — 0; все 15\n'
       'кандидатных ответов валидны. База — локальная ссылка `origin/main`, коммит\n'
       f"`{checks['base_sha']}`; ссылка не обновлялась из сети.\n\n" + table + '\n' + verdict + '\n\n')
assert old in text
doc.write_text(text.replace(old, new))
journal = R / 'EXPERIMENTS.md'
text = journal.read_text()
assert 'Перенос замороженной v4 в основной solver' not in text
deltas = ', '.join(f"inst{row['instance']} {row['delta']}" for row in rows)
text += ('\n| 10-19 | Codex | research/service-zone-v4 | Перенос замороженной v4 в основной solver, O3 и документация | '
         f'Payload побайтово совпал с v4; ZIP пересобран. Synth10 NT3:28/28 VALID; A/B60 NT3 ×3 против 6878393: {deltas}; benchmark rc0. '
         f"Max wall кандидата {max(row['wall'] for row in rows):.1f}с | "
         + verdict + ' docs/v4.md; без staging, коммита и отправки |\n')
journal.write_text(text)
print(table)
print(verdict)
