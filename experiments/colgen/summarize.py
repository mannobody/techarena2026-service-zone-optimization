"""Create human-readable tables, environment metadata and a relative-path manifest."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from bench_research import metadata

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from public_metadata import public_json
def report_json(value, **kwargs):
    return public_json(value, ROOT, **kwargs)


def run():
    chunks=['# Все измерения zone-pool экспериментов\n',
            'NT=1. Все значения цели проверены официальным валидатором. '
            'Время построения моделей входит в hybrid wall; валидация не входит. '
            'Бюджет matched baseline равен hybrid wall. Полные raw данные — JSON рядом.\n']
    for name,label in [('pool_pilot','Конечные зоны, 3 × TL=2 с, MIP=1 с'),
                       ('pool_collected','Best/elite зоны, 3 × TL=2 с, MIP=1 с'),
                       ('pool_long','Best/elite зоны, 3 × TL=10 с, MIP=2 с'),
                       ('pool_single','Best/elite зоны, 1 × TL=20 с, MIP=2 с')]:
        p=HERE/'logs'/f'{name}.json'
        if not p.exists():
            continue
        chunks += [f'## {label}\n',f'Источник: `{p.relative_to(ROOT)}`\n',
                   '| case | repeat | best seed | raw IP | final IP | matched baseline | hybrid wall | matched wall | raw/final columns | final status |\n',
                   '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|\n']
        for r in json.loads(p.read_text())['results']:
            chunks.append(f"| {r['case']} | {r['repeat']} | {r['best_short']:.6f} | {r['raw_ip']:.6f} | {r['hybrid']:.6f} | {r['matched_baseline']:.6f} | {r['hybrid_wall']:.3f} | {r['matched_wall']:.3f} | {r['pool_raw']}/{r['pool_final']} | {r['mip_status']} |\n")
        chunks.append('\n')
    (HERE/'logs/tables.md').write_text('\n'.join(chunks))
    env=metadata()
    env['recorded_utc']=datetime.now(timezone.utc).isoformat()
    env['compiler']=subprocess.check_output(['g++','--version'],text=True).splitlines()[0]
    env['pip_freeze']=subprocess.check_output(['/tmp/ta-colgen-venv/bin/pip','freeze'],text=True).splitlines()
    env['branch']=subprocess.check_output(['git','branch','--show-current'],cwd=HERE,text=True).strip()
    from pyscipopt import Model
    m=Model(); env['scip_version']='.'.join(str(v) for v in (m.getMajorVersion(),m.getMinorVersion(),m.getTechVersion()))
    (HERE/'logs/environment.json').write_text(report_json(env,indent=2))
    manifest=[]
    for p in sorted(HERE.rglob('*')):
        if not p.is_file() or 'artifacts' in p.parts or '__pycache__' in p.parts or p.name=='manifest.json':
            continue
        content=p.read_bytes()
        manifest.append(dict(path=str(p.relative_to(ROOT)),bytes=len(content),sha256=hashlib.sha256(content).hexdigest()))
    (HERE/'logs/manifest.json').write_text(report_json(manifest,indent=2))
    print(report_json(dict(files=len(manifest),bytes=sum(r['bytes'] for r in manifest),environment=env)))


if __name__=='__main__':
    run()
