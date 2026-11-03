#!/usr/bin/env python3
"""Seven frozen solvers, 30 diverse cases, TL250, NT2, five parallel slots.

Uses the existing frozen all-solvers inventory and runner; never edits them.
"""
import argparse
import collections
import copy
import ctypes
import fcntl
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / 'results/local/all_solvers_tl280'
DEFAULT_OUT = ROOT / 'results/local/compare7_30_tl250_j5'
SOLVERS = {
    'v4_exact': 'experiments/server_v4/artifacts/package/main.cpp',
    'v8': 'experiments/server_v8/artifacts/package/main.cpp',
    'exact_neighborhoods': 'experiments/v8_exact_neighborhoods/artifacts/final/main.cpp',
    'current_snapshot': 'solver/solve.cpp',
    'v6_hybrid': 'experiments/server_v6/artifacts/package/main.cpp',
    'geometry_robust': 'experiments/geometry_islands/artifacts/package_robust/main.cpp',
    'v5_2_regions_safe': 'experiments/milp_v5_boundaries/artifacts/package_safe/main.cpp',
}
QUOTAS = {'tiny': 4, 'small': 9, 'medium': 10, 'large': 4, 'huge': 3}
FEATURE_NAMES = ['log_sites', 'log_offices', 'log_workers_per_office', 'log_mean_tasks',
                 'log_max_tasks', 'unservable_site_fraction', 'multiskilled_worker_fraction',
                 'log_required_skills', 'signed_log_alpha_per_reward', 'site_balance_ratio',
                 'total_capacity_ratio', 'signed_log_office_cost_per_reward',
                 'duplicate_coordinate_fraction', 'log_bbox_aspect',
                 'signed_log_nearest_distance_per_reward', 'signed_log_road_to_euclidean',
                 'negative_individual_profit_fraction', 'exact_site_balance', 'zero_alpha']
ANCHORS = [f'task/instance{i}/instance.json' for i in range(5)] + [
    'experiments/v8_exact_neighborhoods/inputs/' + name + '.json' for name in
    ['cross_triangles', 'closed_office_witness', 'worker_budget_isolated', 'joint_open_workers']] + [
    'experiments/v4_perturbation/integration/inputs/holdout/anti.json',
    'experiments/v8_exact_neighborhoods/inputs/independent/multi_deficit.json']
SYMBOLS = ['Highs_create', 'Highs_destroy', 'Highs_getSizeofHighsInt',
           'Highs_setBoolOptionValue', 'Highs_setIntOptionValue', 'Highs_setDoubleOptionValue',
           'Highs_passMip', 'Highs_setSolution', 'Highs_getSolution', 'Highs_getIntInfoValue',
           'Highs_run', 'Highs_getModelStatus']


def load_runner(path):
    spec = importlib.util.spec_from_file_location('szo_frozen_benchmark', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = load_runner(ROOT / 'tools/benchmark_all.py')


def bucket(n):
    return ('tiny' if n < 30 else 'small' if n < 300 else 'medium' if n < 1500
            else 'large' if n < 5000 else 'huge')


def signed_log(x):
    return math.copysign(math.log1p(abs(x)), x)


def features(x):
    """Instance properties only: never reads scores, incumbents or winner labels."""
    sites, offices, workers = x['sites'], x['offices'], x['workers']
    n, m, w = len(sites), len(offices), len(workers)
    tasksets = [set(s['tasks']) for s in sites]
    available = set().union(*(set(v) for v in workers)) if workers else set()
    missing = sum(not skills <= available for skills in tasksets) / max(1, n)
    rewards = [s['reward'] for s in sites]
    scale = max(1e-9, sum(abs(r) for r in rewards) / max(1, n))
    tasks = [len(s['tasks']) for s in sites]
    costs = [o['cost'] for o in offices]
    capacities = [o['maxSize'] for o in offices]
    points = [(s['x'], s['y']) for s in sites + offices]
    dx = max((p[0] for p in points), default=0)-min((p[0] for p in points), default=0)
    dy = max((p[1] for p in points), default=0)-min((p[1] for p in points), default=0)
    aspect = max(dx, dy) / max(1e-12, min(dx, dy)) if points else 1
    duplicate = (len(points)-len(set(points))) / max(1, len(points))
    # Deterministic bounded sample; O(128*M), no pairwise N^2 geometry.
    sample = sorted({i*(n-1)//max(1, min(n, 128)-1) for i in range(min(n, 128))})
    nearest, ratios = [], []
    negative = 0
    for i in sample:
        if not offices:
            continue
        p = sites[i]
        d = min(x['distances'][j][i] for j in range(m))
        euclidean = min(math.hypot(p['x']-o['x'], p['y']-o['y']) for o in offices)
        nearest.append(d/scale)
        ratios.append(d/max(1e-12, euclidean))
        negative += d > p['reward']
    avg_tasks = sum(tasks)/max(1, n)
    vector = [math.log1p(n), math.log1p(m), math.log1p(w/max(1, m)),
              math.log1p(avg_tasks), math.log1p(max(tasks, default=0)),
              missing, sum(len(set(a)) > 1 for a in workers)/max(1, w),
              math.log1p(len(set().union(*tasksets)) if tasksets else 0),
              signed_log(x['balanceCoefficient']/scale),
              min(4, x['maxDifference']/max(1, n/max(1, m))),
              min(4, sum(capacities)/max(1, n)),
              signed_log(sum(costs)/max(1, m)/scale),
              duplicate, math.log1p(min(aspect, 1e12)),
              signed_log(sum(nearest)/max(1, len(nearest))),
              signed_log(sum(ratios)/max(1, len(ratios))),
              negative/max(1, len(sample)), float(x['maxDifference'] == 0),
              float(x['balanceCoefficient'] == 0)]
    return vector


def load_candidates(inventory, m):
    candidates = []
    for cid, case in sorted(m['cases'].items()):
        p = inventory / 'inputs' / (cid + '.json')
        if runner.sha(p) != case['sha256']:
            raise ValueError('Изменён вход каталога: ' + str(p))
        x = json.loads(p.read_text())
        candidates.append({'id': cid, 'bucket': bucket(len(x['sites'])),
                           'aliases': [a['path'] for a in case['aliases']],
                           'vector': features(x)})
    return candidates


def slot_counts(cid, seeds, jobs):
    counts = [0]*jobs
    for seed in seeds:
        index = int(runner.digest((cid+str(seed)).encode())[:8], 16) % jobs
        counts[index] += 1
    return counts


def choose_cases(candidates, seeds, jobs=5):
    by_id = {c['id']: c for c in candidates}
    for name, count in QUOTAS.items():
        if sum(c['bucket'] == name for c in candidates) < count:
            raise ValueError('В каталоге недостаточно тестов категории ' + name)
    lo = [min(c['vector'][j] for c in candidates) for j in range(len(candidates[0]['vector']))]
    hi = [max(c['vector'][j] for c in candidates) for j in range(len(lo))]
    z = {c['id']: [(v-lo[j])/max(1e-12, hi[j]-lo[j]) for j, v in enumerate(c['vector'])]
         for c in candidates}

    def distance(a, b):
        return sum((x-y)**2 for x, y in zip(z[a], z[b]))

    selected, mandatory, reasons = [], set(), {}
    for alias in ANCHORS:
        matches = [c for c in candidates if alias in c['aliases']]
        if len(matches) != 1:
            raise ValueError('Не найден однозначный обязательный тест: ' + alias)
        cid = matches[0]['id']
        if cid not in selected:
            selected.append(cid)
            mandatory.add(cid)
            reasons[cid] = ('published input' if alias.startswith('task/') else
                            'known regression / structural barrier' if alias.endswith(('anti.json', 'multi_deficit.json'))
                            else 'named diagnostic counterexample')
    counts = collections.Counter(by_id[c]['bucket'] for c in selected)
    if any(counts[k] > v for k, v in QUOTAS.items()):
        raise ValueError('Обязательные тесты превышают квоту')
    # Farthest-point sampling, subject to explicit size quotas.
    while len(selected) < sum(QUOTAS.values()):
        pool = [c['id'] for c in candidates if c['id'] not in selected
                and counts[c['bucket']] < QUOTAS[c['bucket']]]
        cid = max(pool, key=lambda c: (min(distance(c, s) for s in selected), c))
        selected.append(cid)
        counts[by_id[cid]['bucket']] += 1
        reasons[cid] = 'farthest feature distance under size quotas'
    # Keep the existing runner's fixed affinity rule; reduce imbalance by swaps
    # within the same size stratum. Mandatory inputs are never replaced.
    slotvec = {c: slot_counts(c, seeds, jobs) for c in by_id}
    loads = [sum(slotvec[c][i] for c in selected) for i in range(jobs)]
    for _ in range(40):
        loss = sum(v*v for v in loads)
        best = None
        for old in selected:
            if old in mandatory:
                continue
            peers = [s for s in selected if s != old]
            for new in by_id:
                if new in selected or by_id[new]['bucket'] != by_id[old]['bucket']:
                    continue
                after = [loads[i]-slotvec[old][i]+slotvec[new][i] for i in range(jobs)]
                improvement = loss-sum(v*v for v in after)
                if improvement <= 0:
                    continue
                diversity = min(distance(new, s) for s in peers)
                rank = (improvement, diversity, new, old)
                if best is None or rank > best[0]:
                    best = (rank, old, new, after)
        if best is None:
            break
        _, old, new, loads = best
        selected[selected.index(old)] = new
        del reasons[old]
        reasons[new] = 'affinity balance swap within same size stratum; feature-distance tie-break'
    return selected, reasons, loads


def prepare_library(out, original):
    dest = out / 'runtime/libhighs.so.1'
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(original.resolve(), dest)
    api = ctypes.CDLL(str(dest))
    for name in SYMBOLS:
        getattr(api, name)
    api.Highs_create.restype = ctypes.c_void_p
    api.Highs_create.argtypes = []
    api.Highs_destroy.argtypes = [ctypes.c_void_p]
    api.Highs_getSizeofHighsInt.argtypes = [ctypes.c_void_p]
    api.Highs_getSizeofHighsInt.restype = ctypes.c_int
    obj = api.Highs_create()
    if not obj:
        raise ValueError('HiGHS_create не создал объект')
    try:
        size = api.Highs_getSizeofHighsInt(obj)
    finally:
        api.Highs_destroy(obj)
    if size != 4:
        raise ValueError('v5.2 требует 32-bit HighsInt, найдено байт: ' + str(size))
    version = None
    if hasattr(api, 'Highs_version'):
        api.Highs_version.restype = ctypes.c_char_p
        version = api.Highs_version().decode()
    return {'file': 'runtime/libhighs.so.1', 'sha256': runner.sha(dest),
            'version': version, 'HighsInt_bytes': size, 'symbols_checked': SYMBOLS,
            'original': runner.public_record(str(original.resolve()), ROOT)}


def prepare(out, inventory, seeds, seconds, jobs, highs):
    original = runner.load_study(inventory)
    frozen_runner = inventory / 'runner_snapshot.py'
    if runner.sha(frozen_runner) != original['runner_sha256']:
        raise ValueError('Изменён замороженный runner каталога')
    if runner.sha(inventory / 'validator.py') != original['validator_sha256']:
        raise ValueError('Изменён замороженный валидатор каталога')
    candidates = load_candidates(inventory, original)
    selected, reasons, loads = choose_cases(candidates, seeds, jobs)
    m = copy.deepcopy(original)
    chosen = {}
    for label, alias in SOLVERS.items():
        matches = [v for v in original['variants'].values() if alias in v['aliases']]
        if len(matches) != 1:
            raise ValueError('Не найден однозначный решатель: ' + alias)
        v = copy.deepcopy(matches[0])
        v['aliases'] = [label, *v['aliases']]
        chosen[label] = v
    out.mkdir(parents=True, exist_ok=True)
    runner.atomic(out / 'SZO_STUDY.json', {'version': 1, 'state': 'preparing'})
    lib = prepare_library(out, highs)
    chosen['v5_2_regions_safe']['env'].update({'LD_LIBRARY_PATH': '${STUDY}/runtime',
                                             'MIP': '1', 'REGION': '1'})
    for label, v in chosen.items():
        v['id'] = runner.digest(runner.canonical({'source': v['source'], 'env': v['env']}))[:24]
    m['variants'] = {v['id']: v for v in chosen.values()}
    used_sources = {v['source'] for v in chosen.values()}
    m['sources'] = {k: v for k, v in original['sources'].items() if k in used_sources}
    m['cases'] = {cid: original['cases'][cid] for cid in selected}
    for sid, src in m['sources'].items():
        for name, expected in src['files'].items():
            source = inventory / 'sources' / sid / 'tree' / name
            if runner.sha(source) != expected:
                raise ValueError('Изменён снимок исходника: ' + str(source))
            target = out / 'sources' / sid / 'tree' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    for cid in selected:
        target = out / 'inputs' / (cid + '.json')
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if runner.sha(target) != m['cases'][cid]['sha256']:
                raise ValueError('Повреждён вход незавершённого профиля: ' + str(target))
        else:
            shutil.copyfile(inventory / 'inputs' / target.name, target)
        target.chmod(0o444)
    for a, b in [('validator.py', 'validator.py'), ('runner_snapshot.py', 'runner_snapshot.py')]:
        shutil.copyfile(inventory / a, out / b)
    shutil.copyfile(Path(__file__), out / 'profile_builder.py')
    shutil.copyfile(ROOT / 'tools/public_metadata.py', out / 'public_metadata.py')
    m.update({'created_unix': time.time(), 'root': '.', 'seconds': seconds,
              'seeds': seeds, 'cpu_pairs': runner.cpu_pairs(jobs),
              'snapshots': [60, 120, 150, 200, 240], 'excluded': [],
              'profile': {'name': 'compare7_30', 'inventory': runner.public_record(str(inventory), ROOT),
                          'inventory_sha256': runner.sha(inventory / 'manifest.json'),
                          'quotas': QUOTAS, 'slot_blocks': loads, 'feature_names': FEATURE_NAMES,
                          'wrapper_sha256': runner.sha(Path(__file__)), 'highs': lib}})
    m['notes'] += ['Frozen subset of the existing all-solvers study; current_snapshot is its saved solver/.',
                   'Case selection uses instance features and size quotas, never scores.',
                   'All selected cases are known development/regression data; no fresh holdout claim.',
                   'v5.2 uses packaged 32-bit HiGHS; LD_LIBRARY_PATH is explicit for that variant.']
    desc = {c['id']: c for c in candidates}
    selection = [{'id': cid, 'bucket': desc[cid]['bucket'], 'reason': reasons[cid],
                  'aliases': desc[cid]['aliases'], 'features': desc[cid]['vector'],
                  'stats': m['cases'][cid]['stats']} for cid in selected]
    runner.atomic(out / 'selection.json', selection)
    runner.atomic(out / 'PROFILE.json', m['profile'])
    for filename, fields, rows in [
            ('catalog_variants.csv', ['id', 'source', 'env', 'aliases'], m['variants'].values()),
            ('catalog_cases.csv', ['id', 'stats', 'aliases'], m['cases'].values())]:
        import csv
        with (out / filename).open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            writer.writerows({k: json.dumps(row[k], ensure_ascii=False) if isinstance(row[k], (list, dict))
                              else row[k] for k in fields} for row in rows)
    runner.atomic(out / 'manifest.json', m)
    runner.atomic(out / 'SZO_STUDY.json', {'version': 1, 'state': 'ready',
                                         'manifest_sha256': runner.sha(out / 'manifest.json')})
    return m


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['plan', 'run', 'status'], nargs='?', default='run')
    ap.add_argument('--out', type=Path, default=DEFAULT_OUT)
    ap.add_argument('--inventory', type=Path, default=INVENTORY)
    ap.add_argument('--seeds', help='Only when creating a profile; default 1,2,3')
    ap.add_argument('--seconds', type=float, help='Only when creating a profile; default 250')
    ap.add_argument('--jobs', type=int, help='Only when creating a profile; default 5')
    ap.add_argument('--highs', type=Path, default=ROOT / 'experiments/v8_exact_neighborhoods/offline_deps/highspy/libhighs.so.1')
    ap.add_argument('--hours', type=float)
    ap.add_argument('--max-runs', type=int)
    ap.add_argument('--retry-failed', action='store_true')
    args = ap.parse_args()
    seconds, jobs = args.seconds if args.seconds is not None else 250, args.jobs or 5
    if not math.isfinite(seconds) or seconds <= 0 or args.jobs is not None and args.jobs <= 0:
        ap.error('Некорректные TL/jobs')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    with (out / '.prepare.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            ap.error('Подготовка этого профиля уже выполняется')
        if (out / 'manifest.json').exists():
            m = runner.load_study(out)
            if m.get('profile', {}).get('name') != 'compare7_30':
                ap.error('Этот каталог принадлежит другому исследованию')
            if args.seeds and runner.parse_seeds(args.seeds) != m['seeds']:
                ap.error('Для других seeds нужен новый --out')
            if args.seconds is not None and args.seconds != m['seconds']:
                ap.error('Для другого TL нужен новый --out')
            if args.jobs is not None and args.jobs != len(m['cpu_pairs']):
                ap.error('Для другого jobs нужен новый --out')
        elif args.command == 'status':
            ap.error('Профиль пока не создан')
        else:
            print('Фиксирую 7 версий и выбираю 30 тестов по признакам входов...', flush=True)
            m = prepare(out, args.inventory.resolve(), runner.parse_seeds(args.seeds or '1,2,3'),
                        seconds, jobs, args.highs.resolve())
    lib = m['profile']['highs']
    if runner.sha(out / lib['file']) != lib['sha256']:
        raise ValueError('Изменена зафиксированная библиотека HiGHS')
    print('Профиль: 7 версий × 30 тестов ×', len(m['seeds']), 'seed;',
          'TL=', m['seconds'], 'jobs=', len(m['cpu_pairs']), flush=True)
    loads = m['profile']['slot_blocks']
    print('Блоков «тест × seed» по слотам:', loads,
          '; бюджет самого длинного слота, ч =', round(max(loads)*7*m['seconds']/3600, 2), flush=True)
    print('HiGHS', lib['version'], 'HighsInt_bytes=', lib['HighsInt_bytes'], flush=True)
    command = [sys.executable, '-u', str(out / 'runner_snapshot.py'), args.command,
               '--root', str(ROOT), '--out', str(out)]
    for flag, value in [('--hours', args.hours), ('--max-runs', args.max_runs)]:
        if value is not None:
            command += [flag, str(value)]
    if args.retry_failed:
        command.append('--retry-failed')
    # exec preserves Ctrl+C/SIGTERM handling in the original tested runner.
    os.execv(sys.executable, command)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, AttributeError) as e:
        print('Ошибка:', e, file=sys.stderr)
        sys.exit(2)
