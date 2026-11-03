"""Does the old deterministic allocator accept new validated incumbents?"""
from pathlib import Path
import json

HERE=Path(__file__).resolve().parent


def legacy_can_assign(obj,solution):
    used=set()
    for off in sorted(solution,key=lambda r:r['officeId']):
        need={k for s in off['sites'] for k in obj['sites'][s]['tasks']};have=set()
        for k in sorted(need):
            if k in have:continue
            choices=[w for w,sk in enumerate(obj['workers']) if w not in used and k in sk]
            if not choices:return False
            w=max(choices,key=lambda w:len((need-have)&set(obj['workers'][w])))
            used.add(w);have.update(obj['workers'][w])
    return True


if __name__=='__main__':
    rows=[]
    for x in json.loads((HERE/'logs/workers_v2/results.json').read_text())['results']:
        if x['variant']!='workers' or not x['case'].startswith('suite_multiskill'):continue
        obj=json.loads((HERE/'data'/(x['case']+'.json')).read_text());solution=json.loads(Path(x['solution']).read_text())
        rows.append(dict(case=x['case'],seed=x['seed'],score=x['score'],legacy_can_assign=legacy_can_assign(obj,solution)))
    (HERE/'logs/worker_barrier.json').write_text(json.dumps(rows,indent=2))
    print(f'Old allocator rejects {sum(not x["legacy_can_assign"] for x in rows)}/{len(rows)} new incumbents.')
