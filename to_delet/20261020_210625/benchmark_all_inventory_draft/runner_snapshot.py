#!/usr/bin/env python3
"""Resumable all-source/all-input benchmark. See docs/benchmark-all-ru.md."""
import argparse
import ast
import concurrent.futures
import csv
import fcntl
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import platform
import posixpath
import random
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import zipfile

VERSION = 1
ROOT = Path(__file__).resolve().parents[1]
KEYS = {'sites', 'offices', 'workers', 'distances', 'maxDifference', 'balanceCoefficient'}
PRUNE = {'.git', '.venv', 'venv', 'offline_deps', '__pycache__', 'node_modules', 'to_delet'}
INCLUDE = re.compile(rb'^\s*#\s*include\s*"([^"\n]+)"', re.M)
MAIN = re.compile(rb'\bint\s+main\s*\([^)]*\)\s*\{')
FLAGS = ['-O3', '-std=c++17', '-pthread']
CONTROLLED = {'TL', 'NT', 'SEED', 'DBG'}
STOP = threading.Event()
PRINT_LOCK = threading.Lock()
LOCK_FDS = []


def say(*args):
    with PRINT_LOCK:
        print(*args, flush=True)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode()


def sha(path):
    return digest(path.read_bytes())


def atomic(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('wb') as f:
        f.write(canonical(obj) + b'\n')
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)
    # Make rename durable as well as file contents (local Linux filesystems).
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def walk(root, output):
    for base, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in PRUNE
                         and not (Path(base) / d).is_symlink()
                         and (Path(base) / d).resolve() != output
                         and not (Path(base) / d / 'SZO_STUDY.json').exists())
        for name in sorted(files):
            p = Path(base) / name
            if not p.is_symlink():
                yield p


def full_solver(raw, language):
    if language == 'python':
        try:
            nodes = list(ast.walk(ast.parse(raw)))
        except (SyntaxError, ValueError):
            return False
        strings = {n.value for n in nodes if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        argv3 = any(isinstance(n, ast.Subscript) and isinstance(n.value, ast.Attribute)
                    and isinstance(n.value.value, ast.Name) and n.value.value.id == 'sys'
                    and n.value.attr == 'argv' and isinstance(n.slice, ast.Constant)
                    and n.slice.value == 3 for n in nodes)
        return {'instance.json', 'solution.json', '__main__'} <= strings and argv3
    matches = list(MAIN.finditer(raw))
    if not matches:
        return False
    # Last main distinguishes full solvers from checkpoint/test wrappers that
    # include a full solver with a macro-renamed main.
    body = raw[matches[-1].end():matches[-1].end() + 700]
    return b'instance.json' in body and b'solution.json' in body and b'argv[3]' in body


def source_bundle(entry, reader):
    """Snapshot transitive quoted includes; keep paths and original directives."""
    files, active = {}, set()

    def visit(name):
        name = posixpath.normpath(name)
        if name in active:
            return b'/* recursive include */'
        raw = reader(name)
        files[name] = raw
        active.add(name)

        def expand(match):
            dep = posixpath.normpath(posixpath.join(posixpath.dirname(name),
                                                   match[1].decode()))
            return visit(dep)

        expanded = INCLUDE.sub(expand, raw)
        active.remove(name)
        return expanded

    expanded = visit(entry)
    return digest(expanded), files


def case_stats(x):
    sites, offices = x['sites'], x['offices']
    pts = [(p['x'], p['y']) for p in sites + offices]
    tasks = [len(s['tasks']) for s in sites]
    distances = [d for row in x['distances'] for d in row]
    def span(vals):
        return {'min': min(vals, default=0), 'max': max(vals, default=0),
                'mean': sum(vals) / len(vals) if vals else 0}
    return {'sites': len(sites), 'offices': len(offices), 'workers': len(x['workers']),
            'maxDifference': x['maxDifference'], 'balanceCoefficient': x['balanceCoefficient'],
            'tasks': span(tasks), 'total_tasks': sum(tasks),
            'rewards': span([s['reward'] for s in sites]), 'distances': span(distances),
            'capacity': span([o['maxSize'] for o in offices]),
            'office_cost': span([o['cost'] for o in offices]),
            'duplicate_coordinates': len(pts) - len(set(pts)),
            'x': span([p[0] for p in pts]), 'y': span([p[1] for p in pts])}


def cpu_pairs(jobs, specified=None):
    allowed = sorted(os.sched_getaffinity(0))
    topology, cores = {}, {}
    for cpu in allowed:
        p = Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
        core = ((p / 'physical_package_id').read_text().strip(),
                (p / 'core_id').read_text().strip())
        topology[cpu] = core
        cores.setdefault(core, []).append(cpu)
    if specified:
        pairs = [[int(v) for v in part.split(',')] for part in specified.split(';')]
        if len(pairs) != jobs or any(len(p) != 2 for p in pairs):
            raise ValueError('--cpus: одна пара двух CPU на каждый --jobs, например "18,19;20,21"')
    else:
        # Prefer non-SMT cores, then one logical CPU per remaining physical core.
        cpus = sorted((v[0] for v in cores.values()),
                      key=lambda c: (len(cores[topology[c]]) != 1, -c))
        if len(cpus) < jobs * 2:
            raise ValueError('Недостаточно разных физических ядер для NT=2 и выбранного --jobs')
        pairs = [sorted(cpus[i*2:i*2+2]) for i in range(jobs)]
    flat = [v for pair in pairs for v in pair]
    if len(set(flat)) != len(flat) or not set(flat) <= set(allowed):
        raise ValueError('CPU повторяются или недоступны текущему процессу')
    if len({topology[c] for c in flat}) != len(flat):
        raise ValueError('Выбраны SMT-потоки одного ядра: нужны разные физические ядра')
    return pairs


def host_info():
    cpu = Path('/proc/cpuinfo').read_text()
    model = re.search(r'^model name\s*:\s*(.*)', cpu, re.M)
    return {'node': platform.node(), 'machine': platform.machine(),
            'cpu_model': model[1] if model else '', 'platform': platform.platform()}


def discover(root, out, args):
    out.mkdir(parents=True, exist_ok=True)
    atomic(out / 'SZO_STUDY.json', {'version': VERSION, 'state': 'preparing'})
    candidates, sources, configs, cases, excluded, specs = {}, {}, {}, {}, [], []
    paths = list(walk(root, out))

    def add_source(alias, entry, reader, language='cpp'):
        try:
            effective, files = source_bundle(entry, reader) if language == 'cpp' else (
                digest(reader(entry)), {entry: reader(entry)})
            sid = language + '-' + effective[:24]
            if sid not in sources:
                dest = out / 'sources' / sid / 'tree'
                provenance = {}
                for name, raw in files.items():
                    # All dependencies must be in the repository/ZIP, not /tmp or home.
                    if name.startswith('/') or '..' in Path(name).parts:
                        raise ValueError('include вне снимка: ' + name)
                    target = dest / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(raw)
                    provenance[name] = digest(raw)
                sources[sid] = {'id': sid, 'effective_sha256': effective, 'entry': entry,
                                'language': language, 'files': provenance, 'aliases': []}
            sources[sid]['aliases'].append(alias)
            candidates[alias] = sid
            return sid
        except (OSError, KeyError, ValueError, UnicodeError, RecursionError) as e:
            excluded.append({'path': alias, 'reason': 'source_snapshot_error', 'detail': str(e)})
            return None

    for p in paths:
        rel = p.relative_to(root).as_posix()
        if p.suffix in {'.cpp', '.cc', '.cxx', '.py'}:
            raw = p.read_bytes()
            language = 'python' if p.suffix == '.py' else 'cpp'
            if full_solver(raw, language):
                def reader(name):
                    target = (root / name).resolve()
                    target.relative_to(root)
                    return target.read_bytes()
                add_source(rel, rel, reader, language)
            elif MAIN.search(raw) or (language == 'python' and rel.startswith('archive/')):
                excluded.append({'path': rel, 'reason': 'not_standalone_instance_solution_solver'})
        elif p.suffix == '.zip':
            try:
                with zipfile.ZipFile(p) as z:
                    for entry in sorted(z.namelist()):
                        if entry.endswith(('.cpp', '.cc', '.cxx')) and full_solver(z.read(entry), 'cpp'):
                            add_source(rel + '!' + entry, entry, z.read)
            except (OSError, ValueError, zipfile.BadZipFile, KeyError) as e:
                excluded.append({'path': rel, 'reason': 'zip_error', 'detail': str(e)})
        elif p.suffix == '.json':
            raw = p.read_bytes()
            if not raw.lstrip().startswith(b'{'):
                continue
            possible_case = all(('"' + k + '"').encode() in raw for k in KEYS)
            possible_spec = b'"variants"' in raw and b'"cases"' in raw
            if not (possible_case or possible_spec):
                continue
            try:
                obj = json.loads(raw)
                if not isinstance(obj, dict):
                    continue
                if KEYS <= obj.keys() and all(isinstance(obj[k], list) for k in
                                             ('sites', 'offices', 'workers', 'distances')):
                    content = canonical(obj)
                    cid = digest(content)
                    if cid not in cases:
                        dest = out / 'inputs' / (cid + '.json')
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(content)
                        cases[cid] = {'id': cid, 'sha256': cid, 'aliases': [], 'stats': case_stats(obj)}
                    cases[cid]['aliases'].append({'path': rel, 'raw_sha256': digest(raw)})
                if isinstance(obj.get('variants'), dict) and 'cases' in obj:
                    specs.append((rel, obj))
            except (ValueError, TypeError, KeyError) as e:
                excluded.append({'path': rel, 'reason': 'candidate_json_error', 'detail': str(e)})

    def config(sid, alias, env):
        env = {str(k): str(v) for k, v in env.items() if k not in CONTROLLED}
        vid = digest(canonical({'source': sid, 'env': env}))[:24]
        if vid not in configs:
            configs[vid] = {'id': vid, 'source': sid, 'env': env, 'aliases': []}
        if alias not in configs[vid]['aliases']:
            configs[vid]['aliases'].append(alias)

    for alias, sid in candidates.items():
        config(sid, alias, {})
    for specpath, spec in specs:
        if 'checkpoints' in spec:
            excluded.append({'path': specpath, 'reason': 'checkpoint_benchmark_not_full_solver'})
            continue
        for name, variant in spec['variants'].items():
            if not isinstance(variant, dict) or not isinstance(variant.get('source'), str):
                continue
            path = Path(variant['source'])
            if path.is_absolute():
                try:
                    path = path.relative_to(root)
                except ValueError:
                    continue
            alias = path.as_posix()
            if alias in candidates and isinstance(variant.get('env', {}), dict):
                config(candidates[alias], specpath + '#' + name, variant.get('env', {}))

    if not cases or not configs:
        raise ValueError('Не найдены самостоятельные решатели или тесты')
    cxx = shutil.which(os.environ.get('CXX', 'g++'))
    if not cxx:
        raise ValueError('Не найден g++ (или CXX)')
    compiler = subprocess.check_output([cxx, '--version'], text=True).splitlines()[0]
    validator = root / 'task/validate_solution.py'
    (out / 'validator.py').write_bytes(validator.read_bytes())
    (out / 'runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
    manifest = {'version': VERSION, 'created_unix': time.time(), 'root': str(root),
                'seconds': args.seconds if args.seconds is not None else 280.0,
                'seeds': parse_seeds(args.seeds or '1,2,3'),
                'cpu_pairs': cpu_pairs(args.jobs or 1, args.cpus), 'NT': 2,
                'hard_grace_seconds': 3.0, 'snapshots': [60, 120, 200, 260],
                'order_seed': 20261020, 'host': host_info(), 'compiler': cxx,
                'compiler_version': compiler, 'flags': FLAGS + ['-ldl'],
                'runner_sha256': sha(Path(__file__)), 'validator_sha256': sha(validator),
                'sources': sources, 'variants': configs, 'cases': cases, 'excluded': excluded,
                'notes': ['Existing inputs only; no new generated tests.',
                          'All old inputs, including holdouts, are known development/regression data.',
                          'Default full solvers plus env variants from full-run JSON specs.',
                          'DBG=1 NT=2; TL and SEED controlled by this study; no external warm starts.',
                          'Common O3 C++17 pthread dl build; original ZIP Makefiles are not executed.']}
    atomic(out / 'manifest.json', manifest)
    for filename, fields, rows in (
        ('catalog_variants.csv', ['id', 'source', 'env', 'aliases'], configs.values()),
        ('catalog_cases.csv', ['id', 'stats', 'aliases'], cases.values()),
        ('excluded.csv', ['path', 'reason', 'detail'], excluded),
    ):
        with (out / filename).open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            for row in rows:
                writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                                 for k, v in row.items() if k in fields})
    atomic(out / 'SZO_STUDY.json', {'version': VERSION, 'state': 'ready',
                                  'manifest_sha256': sha(out / 'manifest.json')})
    return manifest


def parse_seeds(s):
    seeds = [int(v) for v in s.split(',')]
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError('SEED должны быть уникальными целыми числами через запятую')
    return seeds


def load_study(out):
    marker = json.loads((out / 'SZO_STUDY.json').read_text())
    if marker.get('state') != 'ready':
        raise ValueError('Подготовка была прервана; укажите новый --out для повторного планирования')
    if marker['manifest_sha256'] != sha(out / 'manifest.json'):
        raise ValueError('manifest.json изменён; используйте отдельный --out для другого исследования')
    return json.loads((out / 'manifest.json').read_text())


def build_source(out, m, sid, retry=False):
    src = m['sources'][sid]
    base = out / 'sources' / sid
    for name, expected in src['files'].items():
        if sha(base / 'tree' / name) != expected:
            raise ValueError('Изменён снимок исходника: ' + str(base / 'tree' / name))
    record = base / 'build.json'
    if record.exists():
        old = json.loads(record.read_text())
        if old['ok'] and (src['language'] == 'python' or
                          (base / 'solution').exists() and sha(base / 'solution') == old['binary_sha256']):
            return old
        if not old['ok'] and not retry:
            return old
    if STOP.is_set():
        return None
    started = time.time()
    if src['language'] == 'python':
        check = subprocess.run([sys.executable, '-I', '-c', 'import numpy'], capture_output=True)
        result = {'ok': check.returncode == 0, 'language': 'python',
                  'interpreter': sys.executable, 'binary_sha256': sha(Path(sys.executable)),
                  'error': check.stderr.decode(errors='replace')[-2000:]}
    else:
        command = [m['compiler'], *FLAGS, '-o', str(base / 'solution'),
                   str(base / 'tree' / src['entry']), '-ldl']
        say('Сборка', sid, src['aliases'][0])
        with (base / 'build.log').open('wb') as log:
            proc = subprocess.Popen(command, stdout=log, stderr=log, start_new_session=True,
                                    pass_fds=tuple(LOCK_FDS))
            while proc.poll() is None:
                if STOP.wait(.1):
                    os.killpg(proc.pid, signal.SIGTERM)
                    try:
                        proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid, signal.SIGKILL)
                        proc.wait()
                    return None
            result = {'ok': proc.returncode == 0, 'rc': proc.returncode, 'command': command,
                      'binary_sha256': sha(base / 'solution') if proc.returncode == 0 else None}
    result.update({'wall_seconds': time.time() - started, 'built_unix': started,
                   'effective_sha256': src['effective_sha256']})
    atomic(record, result)
    return result


def validator_module(out):
    spec = importlib.util.spec_from_file_location('frozen_szo_validator', out / 'validator.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def analyse(out, inp, solution):
    """Official validation, then descriptive geometry; never feeds the solver."""
    v = validator_module(out)
    try:
        instance = v.Instance.load(inp)
        offices = v.load_solution(solution)
        value = v.validate_solution(instance, offices)
    except Exception as e:
        return {'valid': False, 'objective': None, 'validation_error': f'{type(e).__name__}: {e}'}
    if isinstance(value, str):
        return {'valid': False, 'objective': None, 'validation_error': value}
    result = {'valid': True, 'objective': float(value), 'validation_error': None}
    try:
        from shapely import MultiPoint, points, covers
        from shapely.geometry import mapping
        all_coords = [(s.x, s.y) for s in instance.sites] + [(o.x, o.y) for o in instance.offices]
        points_all = points(all_coords) if all_coords else []
        n = len(instance.sites)
        used_sites = {s for o in offices for s in o.sites}
        opened = {o.office_id for o in offices}
        zones, hulls = [], []
        reward = distance = cost = 0.0
        loads, counts = [], []
        for o in offices:
            office = instance.offices[o.office_id]
            coords = [(office.x, office.y)] + [(instance.sites[s].x, instance.sites[s].y) for s in o.sites]
            hull = MultiPoint(coords).convex_hull
            hulls.append(hull)
            cover_ids = [int(i) for i, yes in enumerate(covers(hull, points_all)) if yes]
            r = sum(instance.sites[s].reward for s in o.sites)
            d = sum(instance.distances[o.office_id][s] for s in o.sites)
            load = sum(len(instance.sites[s].tasks) for s in o.sites)
            reward += r
            distance += d
            cost += office.cost
            loads.append(load)
            counts.append(len(o.sites))
            zones.append({'office_id': o.office_id, 'sites': list(o.sites), 'workers': list(o.workers),
                          'count': len(o.sites), 'task_load': load, 'maxSize': office.maxSize,
                          'reward': r, 'distance': d, 'cost': office.cost,
                          'hull': mapping(hull), 'area': hull.area, 'perimeter': hull.length,
                          'covered_input_points': cover_ids,
                          'covered_unassigned_sites': sum(i < n and i not in used_sites for i in cover_ids),
                          'covered_closed_offices': sum(i >= n and i-n not in opened for i in cover_ids)})
        intersections = []
        for i in range(len(hulls)):
            for j in range(i):
                if hulls[i].intersects(hulls[j]):
                    cross = hulls[i].intersection(hulls[j])
                    intersections.append({'office_ids': [offices[j].office_id, offices[i].office_id],
                                          'area': cross.area, 'length': cross.length, 'type': cross.geom_type})
        imbalance = max(loads, default=0) - min(loads, default=0)
        result.update({'reward': reward, 'distance': distance, 'office_cost': cost,
                       'task_imbalance': imbalance, 'balance_penalty': instance.balanceCoefficient * imbalance,
                       'site_imbalance': max(counts, default=0) - min(counts, default=0),
                       'opened_offices': len(offices), 'assigned_sites': len(used_sites),
                       'assigned_workers': sum(len(o.workers) for o in offices), 'zones': zones,
                       'hull_intersections_without_shared_input_points': intersections})
    except Exception as e:
        result['geometry_analysis_error'] = f'{type(e).__name__}: {e}'
    return result


def clean_env(m, variant, seed):
    env = {k: os.environ[k] for k in ('PATH', 'LANG', 'LC_ALL') if k in os.environ}
    env.update(variant['env'])
    env.update({'TL': str(m['seconds']), 'NT': '2', 'SEED': str(seed), 'DBG': '1',
                'OMP_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '2',
                'MKL_NUM_THREADS': '2', 'NUMEXPR_NUM_THREADS': '2', 'PYTHONHASHSEED': str(seed % 2**32)})
    return env


def terminate(proc):
    # GNU time must survive to write resource usage. taskset execs the solver.
    try:
        children = Path(f'/proc/{proc.pid}/task/{proc.pid}/children').read_text().split()
        for child in children:
            try:
                os.kill(int(child), signal.SIGTERM)
            except ProcessLookupError:
                pass
    except OSError:
        pass
    try:
        proc.wait(timeout=1)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()
    # Also terminate descendants left behind by a misbehaving solver.
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def execute(out, m, variant, case, seed, pair, build):
    identity = {'variant': variant['id'], 'input': case['id'], 'seed': seed,
                'seconds': m['seconds'], 'cpus': pair, 'binary_sha256': build['binary_sha256'],
                'manifest_sha256': sha(out / 'manifest.json')}
    jid = digest(canonical(identity))
    jobdir = out / 'runs' / jid
    jobdir.mkdir(parents=True, exist_ok=True)
    attempt = jobdir / ('attempt-%04d' % (1 + len(list(jobdir.glob('attempt-*')))))
    attempt.mkdir()
    workspace = attempt / 'work'
    workspace.mkdir()
    inp = out / 'inputs' / (case['id'] + '.json')
    if sha(inp) != case['sha256']:
        raise ValueError('Изменён снимок входа: ' + str(inp))
    # Inputs are immutable and identical across runs. Hard links avoid keeping
    # hundreds of copies of every large distance matrix. Solvers only see instance.json.
    inp.chmod(0o444)
    try:
        os.link(inp, workspace / 'instance.json')
    except OSError:
        shutil.copyfile(inp, workspace / 'instance.json')
        (workspace / 'instance.json').chmod(0o444)
    src = m['sources'][variant['source']]
    base = out / 'sources' / src['id']
    if src['language'] == 'python':
        executable = [sys.executable, '-I', str(base / 'tree' / src['entry'])]
    else:
        if sha(base / 'solution') != build['binary_sha256']:
            raise ValueError('Изменён binary: ' + str(base / 'solution'))
        executable = [str(base / 'solution')]
    command = ['/usr/bin/time', '-f', 'rss_kb=%M\nuser_seconds=%U\nsystem_seconds=%S',
               '-o', str(attempt / 'resources.txt'), 'taskset', '-c', ','.join(map(str, pair)),
               *executable, 'instance.json', 'solution.json', str(m['seconds'])]
    atomic(attempt / 'started.json', {**identity, 'command': command, 'started_unix': time.time(),
                                     'env': clean_env(m, variant, seed)})
    start = time.monotonic()
    snapshots, pending = [], [t for t in m['snapshots'] if t < m['seconds']]
    timeout = interrupted = False
    with (attempt / 'stdout.log').open('wb') as stdout, (attempt / 'stderr.log').open('wb') as stderr:
        proc = subprocess.Popen(command, cwd=workspace, env=clean_env(m, variant, seed),
                                stdout=stdout, stderr=stderr, start_new_session=True,
                                pass_fds=tuple(LOCK_FDS))
        try:
            while proc.poll() is None:
                elapsed = time.monotonic() - start
                if STOP.is_set():
                    interrupted = True
                    terminate(proc)
                    break
                if elapsed >= m['seconds'] + m['hard_grace_seconds']:
                    timeout = True
                    terminate(proc)
                    break
                if pending and elapsed >= pending[0]:
                    target = pending.pop(0)
                    snap = {'target_seconds': target, 'observed_seconds': elapsed}
                    try:
                        raw = (workspace / 'solution.json').read_bytes()
                        json.loads(raw)  # A writer can be in the middle of publishing.
                        name = f't{target}.solution.json'
                        (attempt / name).write_bytes(raw)
                        snap['file'] = name
                    except (OSError, ValueError) as e:
                        snap['capture_error'] = str(e)
                    snapshots.append(snap)
                STOP.wait(.04)
            rc = proc.wait()
        except BaseException:
            terminate(proc)
            raise
    wall = time.monotonic() - start
    row = {'job_id': jid, **identity, 'variant_alias': variant['aliases'][0],
           'case_alias': case['aliases'][0]['path'], 'attempt': str(attempt.relative_to(out)),
           'rc': rc, 'wall_seconds': wall, 'nominal_overrun_seconds': max(0, wall-m['seconds']),
           'timeout': timeout, 'interrupted': interrupted,
           'completed_unix': time.time(), 'snapshots': snapshots, 'valid': False, 'objective': None}
    logtext = (attempt / 'stderr.log').read_text(errors='replace')
    thread_report = re.search(r'threads=(\d+)', logtext)
    row['reported_threads'] = int(thread_report[1]) if thread_report else None
    row['error_in_log'] = bool(re.search(r'error:|VERIFY|INVALID', logtext))
    resource = attempt / 'resources.txt'
    if resource.exists():
        text = resource.read_text()
        for name in ('rss_kb', 'user_seconds', 'system_seconds'):
            match = re.search(r'^' + name + r'=([0-9.]+)', text, re.M)
            row[name] = float(match[1]) if match else None
    if interrupted:
        row['status'] = 'interrupted'
        atomic(attempt / 'interrupted.json', row)
        return row
    try:
        analysis = analyse(out, inp, workspace / 'solution.json')
        atomic(attempt / 'analysis.json', analysis)
        row.update({k: analysis.get(k) for k in ('valid', 'objective', 'validation_error', 'reward',
                   'distance', 'office_cost', 'balance_penalty', 'task_imbalance', 'site_imbalance',
                   'opened_offices', 'assigned_sites', 'assigned_workers', 'geometry_analysis_error')})
        for snap in snapshots:
            if 'file' in snap:
                a = analyse(out, inp, attempt / snap['file'])
                atomic(attempt / (snap['file'] + '.analysis.json'), a)
                snap.update({k: a.get(k) for k in ('valid', 'objective', 'validation_error')})
        row['status'] = ('timeout' if timeout else 'runtime_error' if rc != 0 else
                         'invalid' if not row['valid'] else 'analysis_error' if
                         row.get('geometry_analysis_error') else 'ok')
    except Exception as e:
        row['status'] = 'analysis_error'
        row['validation_error'] = f'{type(e).__name__}: {e}'
    # Hash every retained output and log. A successful cache hit requires these.
    row['artifacts'] = {str(p.relative_to(out)): sha(p) for p in attempt.rglob('*') if p.is_file()}
    row['record_sha256'] = digest(canonical(row))
    atomic(jobdir / 'result.json', row)
    return row


def cache_valid(out, row, hash_cache=None):
    if row.get('interrupted') or not row.get('artifacts'):
        return False
    if row.get('record_sha256') != digest(canonical({k: v for k, v in row.items() if k != 'record_sha256'})):
        return False
    hash_cache = {} if hash_cache is None else hash_cache
    try:
        for name, expected in row['artifacts'].items():
            path = out / name
            stat = path.stat()
            key = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
            if key not in hash_cache:
                hash_cache[key] = sha(path)
            if hash_cache[key] != expected:
                return False
        return True
    except OSError:
        return False


def cached_rows(out):
    rows, hash_cache = {}, {}
    for path in sorted((out / 'runs').glob('*/result.json')):
        try:
            row = json.loads(path.read_text())
            if cache_valid(out, row, hash_cache):
                rows[row['job_id']] = row
            else:
                say('Повреждён/неполон кэш, будет повторён:', path.parent.name[:12])
        except (ValueError, OSError, KeyError):
            say('Не читается запись, будет повторена:', path)
    return rows


def select(items, patterns, case=False):
    if not patterns:
        return list(items.values())
    def matches(item):
        aliases = [a['path'] for a in item['aliases']] if case else item['aliases']
        return any(pattern in item['id'] or any(pattern in a for a in aliases) for pattern in patterns)
    chosen = [item for item in items.values() if matches(item)]
    if not chosen:
        raise ValueError('Фильтр ничего не выбрал: ' + ', '.join(patterns))
    return chosen


def export(out, m, rows):
    data = sorted(rows.values(), key=lambda r: (r['case_alias'], r['seed'], r['variant_alias']))
    # All large per-zone geometry is in attempt/analysis.json, not in this index.
    atomic(out / 'results.json', data)
    fields = ['job_id', 'status', 'variant', 'variant_alias', 'input', 'case_alias', 'seed',
              'seconds', 'cpus', 'valid', 'objective', 'wall_seconds', 'nominal_overrun_seconds',
              'rc', 'timeout', 'reported_threads', 'error_in_log', 'rss_kb', 'user_seconds', 'system_seconds', 'reward', 'distance',
              'office_cost', 'balance_penalty', 'task_imbalance', 'site_imbalance', 'opened_offices',
              'assigned_sites', 'assigned_workers', 'validation_error', 'attempt']
    tmp = out / 'summary.csv.tmp'
    with tmp.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(data)
    tmp.replace(out / 'summary.csv')
    statuses = {}
    for row in data:
        statuses[row['status']] = statuses.get(row['status'], 0) + 1
    expected = len(m['variants']) * len(m['cases']) * len(m['seeds'])
    atomic(out / 'progress.json', {'expected_full_study': expected, 'completed': len(data),
                                  'remaining': expected-len(data), 'statuses': statuses,
                                  'updated_unix': time.time()})
    return statuses


def print_plan(m, variants, cases, done=0):
    count = len(variants) * len(cases) * len(m['seeds'])
    hours = max(0, count-done) * m['seconds'] / len(m['cpu_pairs']) / 3600
    say(f"Исходников: {len(m['sources'])}; конфигураций выбрано: {len(variants)}/{len(m['variants'])}; "
        f"тестов: {len(cases)}/{len(m['cases'])}; seeds={m['seeds']}")
    say(f"TL={m['seconds']:g}, NT=2, CPU={m['cpu_pairs']}; запусков={count}; "
        f"бюджет, если каждый работает весь TL: {hours:.1f} ч ({hours/24:.1f} суток), "
        'без сборки и валидации')


def run(out, m, args, rows):
    if sha(Path(__file__)) != m['runner_sha256']:
        raise ValueError('Скрипт изменился после заморозки; используйте новый --out')
    if sha(out / 'validator.py') != m['validator_sha256']:
        raise ValueError('Изменён замороженный валидатор')
    if host_info() != m['host']:
        raise ValueError('Изменился компьютер/ОС: для сопоставимых измерений нужен новый --out')
    current_compiler = subprocess.check_output([m['compiler'], '--version'], text=True).splitlines()[0]
    if current_compiler != m['compiler_version']:
        raise ValueError('Изменился компилятор: нужен новый --out')
    for command in ('taskset', '/usr/bin/time'):
        if not shutil.which(command):
            raise ValueError('Не найден ' + command)
    try:
        import pydantic, shapely
        deps = {'python': sys.version, 'executable': sys.executable,
                'python_binary_sha256': sha(Path(sys.executable)),
                'pydantic': pydantic.__version__, 'shapely': shapely.__version__,
                'geos': shapely.geos_version_string}
        try:
            import numpy
            deps['numpy'] = numpy.__version__
        except ImportError:
            deps['numpy'] = None
    except ImportError as e:
        raise ValueError('Запускайте через .venv/bin/python (нужны pydantic и shapely)') from e
    dp = out / 'dependencies.json'
    if dp.exists() and json.loads(dp.read_text()) != deps:
        raise ValueError('Изменилась Python/validator среда: нужен новый --out')
    atomic(dp, deps)
    pairs = m['cpu_pairs']
    cpu_pairs(len(pairs), ';'.join(','.join(map(str, p)) for p in pairs))
    # Keep builds, validation and controller work off the benchmark cores,
    # including their SMT siblings, whenever spare physical cores exist.
    def core_of(cpu):
        p = Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
        return ((p / 'physical_package_id').read_text(), (p / 'core_id').read_text())
    benchmark_cores = {core_of(c) for pair in pairs for c in pair}
    controller_cpus = {c for c in os.sched_getaffinity(0) if core_of(c) not in benchmark_cores}
    if controller_cpus:
        os.sched_setaffinity(0, controller_cpus)
    else:
        say('Нет свободного ядра для контроллера/валидации; возможна конкуренция за CPU')
    variants, cases = select(m['variants'], args.solver), select(m['cases'], args.case, True)
    print_plan(m, variants, cases)
    started = time.monotonic()
    builds = {}
    for sid in sorted({v['source'] for v in variants}):
        if args.hours is not None and time.monotonic()-started >= args.hours*3600:
            say('Бюджет сессии исчерпан во время сборок; готовые сборки сохранены')
            return
        build = build_source(out, m, sid, args.retry_failed)
        if build is None:
            return
        builds[sid] = build
    blocked = [v['id'] for v in variants if not builds[v['source']]['ok']]
    atomic(out / 'blocked_variants.json', {'variants': blocked,
           'detail': 'See sources/<source>/build.json and build.log; no test runs counted as done.'})
    if blocked:
        say(f'Не собрались/нет зависимостей: {len(blocked)} конфигураций; см. blocked_variants.json')
    manifest_hash = sha(out / 'manifest.json')
    queue = [[] for _ in pairs]
    blocks = [(c, seed) for seed in m['seeds'] for c in cases]
    random.Random(m['order_seed']).shuffle(blocks)
    for case, seed in blocks:
        index = int(digest((case['id']+str(seed)).encode())[:8], 16) % len(pairs)
        order = list(variants)
        random.Random(f"{case['id']}:{seed}:{m['order_seed']}").shuffle(order)
        for variant in order:
            build = builds[variant['source']]
            if not build['ok']:
                continue
            jid = digest(canonical({'variant': variant['id'], 'input': case['id'], 'seed': seed,
                     'seconds': m['seconds'], 'cpus': pairs[index], 'binary_sha256': build['binary_sha256'],
                     'manifest_sha256': manifest_hash}))
            if jid in rows and (not args.retry_failed or rows[jid]['status'] == 'ok'):
                continue
            queue[index].append((variant, case, seed))
    remaining = sum(map(len, queue))
    say(f'В очереди: {remaining}; сохранённых результатов: {len(rows)}')
    guard = threading.Lock()
    claimed = completed = 0
    last_export = time.monotonic()
    # Shared lock names with the older runner avoid two studies timing on the same CPU.
    locks = []
    try:
        for cpu in sorted(c for p in pairs for c in p):
            f = open(f'/tmp/szo-perturbation-cpu{cpu}.lock', 'a')
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                f.close()
                raise ValueError(f'CPU {cpu} уже занят другим бенчмарком')
            locks.append(f)
        LOCK_FDS.extend(f.fileno() for f in locks)

        def worker(index):
            nonlocal claimed, completed, last_export
            for variant, case, seed in queue[index]:
                with guard:
                    if STOP.is_set() or args.max_runs is not None and claimed >= args.max_runs:
                        return
                    if args.hours is not None and time.monotonic()-started >= args.hours*3600:
                        return
                    claimed += 1
                    say(f"Старт #{claimed}: {case['aliases'][0]['path']} | "
                        f"{variant['aliases'][0]} | seed={seed}")
                row = execute(out, m, variant, case, seed, pairs[index], builds[variant['source']])
                with guard:
                    if row['interrupted']:
                        say('Прерван; повторится при следующем запуске:', row['job_id'][:12])
                        return
                    rows[row['job_id']] = row
                    completed += 1
                    with (out / 'events.jsonl').open('ab') as journal:
                        journal.write(canonical({k: row.get(k) for k in
                            ('job_id', 'status', 'objective', 'attempt', 'completed_unix')}) + b'\n')
                        journal.flush()
                        os.fsync(journal.fileno())
                    say(f"Готово {completed}/{remaining}: {row['status']} "
                        f"objective={row['objective']} wall={row['wall_seconds']:.2f}s")
                    if time.monotonic()-last_export >= 60:
                        export(out, m, rows)
                        last_export = time.monotonic()

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(pairs)) as pool:
            futures = [pool.submit(worker, i) for i in range(len(pairs))]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except BaseException:
                    STOP.set()
                    raise
    finally:
        for f in locks:
            if f.fileno() in LOCK_FDS:
                LOCK_FDS.remove(f.fileno())
        for f in locks:
            f.close()
        export(out, m, rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['plan', 'run', 'status'], nargs='?', default='run')
    ap.add_argument('--root', type=Path, default=ROOT)
    ap.add_argument('--out', type=Path, default=ROOT / 'results/local/all_solvers_tl280')
    ap.add_argument('--seconds', type=float, help='Только при создании study; default 280')
    ap.add_argument('--seeds', help='Только при создании study; default 1,2,3')
    ap.add_argument('--jobs', type=int, help='Только при создании study; default 1, NT=2')
    ap.add_argument('--cpus', help='Например "18,19" или "18,19;20,21"')
    ap.add_argument('--solver', action='append', default=[], help='Подстрока alias/id; можно повторять')
    ap.add_argument('--case', action='append', default=[], help='Подстрока alias/id; можно повторять')
    ap.add_argument('--max-runs', type=int, help='Остановиться после N новых запусков, включая ошибки')
    ap.add_argument('--hours', type=float, help='После N часов не начинать новые запуски; текущие завершить')
    ap.add_argument('--retry-failed', action='store_true', help='Повторять сохранённые ошибки и сборки')
    args = ap.parse_args(argv)
    if (args.seconds is not None and (not math.isfinite(args.seconds) or args.seconds <= 0)
            or args.jobs is not None and args.jobs <= 0
            or args.max_runs is not None and args.max_runs < 0
            or args.hours is not None and (not math.isfinite(args.hours) or args.hours < 0)):
        ap.error('Некорректный лимит времени/число запусков/потоков')
    out, root = args.out.resolve(), args.root.resolve()
    out.mkdir(parents=True, exist_ok=True)
    with (out / '.study.lock').open('a') as lock:
        read_only = False
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            if args.command != 'status':
                ap.error('Этот study уже запущен другим процессом')
            read_only = True
        if not read_only:
            # If the runner is killed with SIGKILL, descendants retain the lock
            # until they exit: a new session cannot overlap their measurements.
            LOCK_FDS.append(lock.fileno())
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            signal.signal(sig, lambda *_: STOP.set())
        if (out / 'manifest.json').exists():
            m = load_study(out)
            if args.seconds is not None and args.seconds != m['seconds']:
                ap.error('TL отличается от замороженного; задайте другой --out')
            if args.seeds is not None and parse_seeds(args.seeds) != m['seeds']:
                ap.error('SEED отличаются от замороженных; задайте другой --out')
            if args.jobs is not None and args.jobs != len(m['cpu_pairs']):
                ap.error('--jobs отличается от замороженного; задайте другой --out')
            if args.cpus and cpu_pairs(len(m['cpu_pairs']), args.cpus) != m['cpu_pairs']:
                ap.error('--cpus отличается от замороженного; задайте другой --out')
        elif args.command == 'status':
            ap.error('Исследование пока не создано: сначала plan или run')
        else:
            say('Сканирую исходники, ZIP и JSON; создаю замороженный каталог...')
            m = discover(root, out, args)
        variants, cases = select(m['variants'], args.solver), select(m['cases'], args.case, True)
        if args.command == 'plan':
            print_plan(m, variants, cases)
            say('Каталог:', out / 'manifest.json')
            return 0
        rows = cached_rows(out)
        if args.command == 'status':
            print_plan(m, variants, cases)
            statuses = {}
            for row in rows.values():
                statuses[row['status']] = statuses.get(row['status'], 0) + 1
            if not read_only:
                export(out, m, rows)
            say('Сохранено:', len(rows), 'Статусы:', statuses,
                '(бенчмарк ещё работает)' if read_only else '')
            say('Таблица:', out / 'summary.csv')
            return 0
        try:
            run(out, m, args, rows)
        finally:
            export(out, m, rows)
        say('Результаты:', out / 'summary.csv')
        return 130 if STOP.is_set() else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        print('Ошибка:', exc, file=sys.stderr)
        sys.exit(2)
