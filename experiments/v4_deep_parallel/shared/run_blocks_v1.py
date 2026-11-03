#!/usr/bin/env python3
"""Equal-affinity paired blocks, immutable provenance and optional anytime snapshots.

Run with the repository venv. Each (case, seed) block holds one CPU pair for
all variants; this is essential on heterogeneous and SMT machines.
"""
import concurrent.futures, fcntl, hashlib, json, os, random, re, signal
import subprocess, sys, threading, time
from pathlib import Path

# Serialize an observation copy without altering commands or subprocess env.
import sys as _report_sys
_REPORT_ROOT = next(p for p in Path(__file__).resolve().parents
                    if (p / 'tools/public_metadata.py').is_file())
_report_sys.path.insert(0, str(_REPORT_ROOT / 'tools'))
from public_metadata import public_json as _public_json
def report_json(value, **kwargs):
    return _public_json(value, _REPORT_ROOT, **kwargs)


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'task'))
from validate_solution import validate

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path, value):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(report_json(value, indent=2))
    tmp.replace(path)

def main():
    specpath = Path(sys.argv[1]).resolve()
    spec = json.loads(specpath.read_text())
    dest = ROOT / spec['destination']
    dest.mkdir(parents=True, exist_ok=False)
    allowed = set(os.sched_getaffinity(0))
    pairs = spec['cpu_pairs']
    flat = [c for pair in pairs for c in pair]
    assert len(set(flat)) == len(flat) and set(flat) <= allowed
    assert all(len(pair) == 2 for pair in pairs)
    configs = spec['variants']
    manifest = {'spec': spec, 'spec_sha256': sha(specpath),
        'runner_sha256': sha(Path(__file__)),
        'binaries': {k: sha(ROOT / v['binary']) for k, v in configs.items()},
        'inputs': {k: sha(ROOT / v) for k, v in spec['cases'].items()},
        'topology': subprocess.check_output(['lscpu', '-e=CPU,CORE,SOCKET,MAXMHZ'], text=True)}
    dump(dest / 'MANIFEST.json', manifest)
    clean = {k: v for k, v in os.environ.items() if k in ('PATH','HOME','LANG','LD_LIBRARY_PATH')}
    blocks = [(case, seed) for case in spec['cases'] for seed in spec['seeds']]
    random.Random(spec.get('order_seed', 791)).shuffle(blocks)
    results, guard = [], threading.Lock()

    def run_block(affinity, block):
        case, seed = block
        labels = list(configs)
        random.Random(f'{case}:{seed}:{spec.get("order_seed",791)}').shuffle(labels)
        for label in labels:
            config = configs[label]
            prefix = dest / f'{case}_{seed}_{label}'
            inp = ROOT / spec['cases'][case]
            out = prefix.with_suffix('.solution.json')
            err, resource = prefix.with_suffix('.stderr'), prefix.with_suffix('.resource')
            assert sha(ROOT / config['binary']) == manifest['binaries'][label]
            assert sha(inp) == manifest['inputs'][case]
            env = clean | config.get('env', {}) | {'NT':'2','SEED':str(seed)}
            seconds = spec['seconds']
            cmd = ['/usr/bin/time','-f','rss_kb=%M user=%U sys=%S','-o',str(resource),
                   'taskset','-c',','.join(map(str,affinity)),str(ROOT/config['binary']),
                   str(inp),str(out),str(seconds)]
            started = time.time()
            start = time.monotonic()
            pending = list(sorted(spec.get('snapshots', [])))
            snaps, timedout = [], False
            with err.open('w') as log:
                proc = subprocess.Popen(cmd, env=env, stderr=log,
                    stdout=subprocess.DEVNULL, start_new_session=True)
                while proc.poll() is None:
                    elapsed = time.monotonic() - start
                    if pending and elapsed >= pending[0]:
                        target = pending.pop(0)
                        try:
                            raw = out.read_bytes()
                            json.loads(raw)
                            snap = dest / f'{case}_{seed}_{label}.t{target}.solution.json'
                            snap.write_bytes(raw)
                            snaps.append({'target_seconds':target,'observed_seconds':elapsed,
                                          'file':str(snap.relative_to(ROOT)), 'sha256':sha(snap)})
                        except (OSError, ValueError) as exc:
                            snaps.append({'target_seconds':target,'observed_seconds':elapsed,'error':str(exc)})
                    if elapsed > seconds + 10:
                        os.killpg(proc.pid, signal.SIGKILL)
                        timedout = True
                        break
                    time.sleep(.08)
                rc = proc.wait()
            wall = time.monotonic() - start
            ended = time.time()
            value = validate(inp, out)
            valid = not isinstance(value, str)
            logtext = err.read_text()
            nt = re.search(r'threads=(\d+)', logtext)
            actual_nt = int(nt[1]) if nt else None
            badlog = bool(re.search(r'error:|VERIFY|INVALID', logtext))
            for snap in snaps:
                if 'file' in snap:
                    v = validate(inp, ROOT / snap['file'])
                    snap['valid'] = not isinstance(v, str)
                    snap['objective'] = v if snap['valid'] else None
                    if not snap['valid']: snap['validation_error'] = v
            row = {'case':case,'seed':seed,'variant':label,'started_unix':started,
                'ended_unix':ended,'rc':rc,'timeout':timedout,'wall':wall,'valid':valid,
                'objective':value if valid else None,'validation_error':value if not valid else None,
                'actual_nt':actual_nt,'error_log':badlog,'affinity':affinity,
                'success':rc==0 and not timedout and wall<=seconds+3 and valid and not badlog and actual_nt==2,
                'resource':resource.read_text() if resource.exists() else '', 'snapshots':snaps}
            dump(prefix.with_suffix('.json'), row)
            with guard:
                results.append(row)
                dump(dest/'results.json', results)
                print(len(results),len(blocks)*len(labels),case,seed,label,
                      round(row['objective'] or 0,6),row['success'],flush=True)

    def worker(index):
        affinity = pairs[index]
        with (dest / f'cpu_{affinity[0]}.lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            for block in blocks[index::len(pairs)]:
                run_block(affinity, block)

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(pairs)) as executor:
        futures = [executor.submit(worker, i) for i in range(len(pairs))]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    dump(dest / 'COMPLETE.json', {'expected':len(blocks)*len(configs),
        'completed':len(results),'success':sum(r['success'] for r in results)})

if __name__ == '__main__':
    main()
