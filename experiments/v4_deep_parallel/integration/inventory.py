"""Read-only inventory of research artifacts; proposes no automatic deletion."""
import hashlib
import json
import subprocess
from pathlib import Path

R = Path(__file__).resolve().parent
LAB = R.parent
ROOT = R.parents[2]
records, cleanup, totals = [], [], {}
excluded = {LAB / 'INVENTORY.json', LAB / 'CLEANUP_CANDIDATES.md'}
for path in sorted(LAB.rglob('*')):
    if not path.is_file() or path in excluded:
        continue
    rel = str(path.relative_to(ROOT))
    size = path.stat().st_size
    group = path.relative_to(LAB).parts[0]
    totals.setdefault(group, {'files': 0, 'bytes': 0})
    totals[group]['files'] += 1
    totals[group]['bytes'] += size
    records.append({'path': rel, 'bytes': size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    reason = None
    if '__pycache__' in path.parts:
        reason = 'Python import cache; regenerated from retained .py sources.'
    elif path.suffix == '.normalized':
        reason = 'ELF comparison copy, reproducible from retained binary via objcopy; recorded hashes are preserved.'
    elif path.parent.name == 'zip_rebuild' and path.name in ('main.cpp', 'Makefile'):
        original = path.parent.parent / 'package' / path.name
        assert original.read_bytes() == path.read_bytes()
        reason = 'Byte-identical extracted copy of retained package file and ZIP payload.'
    if reason:
        cleanup.append({'path': rel, 'bytes': size, 'reason': reason})

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

baseline = ROOT / 'experiments/server_v4/artifacts/case03_cpp_server_v4_O3.zip'
assert hashlib.sha256(baseline.read_bytes()).hexdigest() == 'b4e9ace4ed6cffe53b932bb1d10f7ecdfdcc4170458afaf05e16b3068ebae953'
inventory = {'files': len(records), 'bytes': sum(x['bytes'] for x in records),
             'groups': totals, 'records': records, 'cleanup_candidates': cleanup,
             'git': {'branch': git('branch', '--show-current'), 'head': git('rev-parse', 'HEAD'),
                     'staged_paths': git('diff', '--cached', '--name-only'),
                     'tracked_deleted_paths': git('ls-files', '--deleted')},
             'baseline_zip_unchanged': True, 'deleted_in_this_task': []}
(LAB / 'INVENTORY.json').write_text(json.dumps(inventory, indent=2))
lines = ['# Необязательные кандидаты на очистку', '',
         '**Ничего не удалено. Разрешение на удаление не запрашивается, потому что очистка не выполняется.**', '',
         'Сохранены все проверенные бинарники, исходники, входы, ответы, логи, manifests,',
         'отрицательные результаты и оба ZIP. Проверенные бинарники оставлены намеренно:',
         'их удаление сделает исторические пути в manifests недоступными до восстановления.', '',
         'Ниже только воспроизводимые кеши и подтверждённые копии. Этот список сам по себе',
         'не является разрешением на удаление. Исторические manifests не переписываются.', '',
         '| Файл | Байт | Почему воспроизводим / дубликат |', '|---|---:|---|']
for x in cleanup:
    lines.append(f'| `{x["path"]}` | {x["bytes"]} | {x["reason"]} |')
lines += ['', f'Всего кандидатов: {len(cleanup)}, {sum(x["bytes"] for x in cleanup):,} байт.', '',
          'Полная инвентаризация с SHA256: `INVENTORY.json`.']
(LAB / 'CLEANUP_CANDIDATES.md').write_text('\n'.join(lines)+'\n')
print({k: inventory[k] for k in ['files', 'bytes', 'git', 'baseline_zip_unchanged']})
