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
        'sources': {k: sha(ROOT / v['source']) for k,v in configs.items()},
        'validator_sha256': sha(ROOT/'task/validate_solution.py'),
        'checkpoints': {k: sha(ROOT/v) for k,v in spec.get('checkpoints',{}).items()},
        'binaries': {k: sha(ROOT / v['binary']) for k, v in configs.items()},
        'inputs': {k: sha(ROOT / v) for k, v in spec['cases'].items()},
        'topology': subprocess.check_output(['lscpu', '-e=CPU,CORE,SOCKET,MAXMHZ'], text=True)}
    dump(dest / 'MANIFEST.json', manifest)
    clean = {k: v for k, v in os.environ.items() if k in ('PATH','HOME','LANG','LD_LIBRARY_PATH')}
    blocks = [(case, seed) for case in spec['cases'] for seed in spec['seeds']]
    random.Random(spec.get('order_seed', 791)).shuffle(blocks)
    results, guard = [], threading.Lock()
    completed=set()
    if spec.get('resume_from'):
        old=ROOT/spec['resume_from']; prior=json.loads((old/'MANIFEST.json').read_text())
        for k in ['sources','binaries','inputs','checkpoints']:
            assert prior.get(k)==manifest.get(k),(k,'resume provenance mismatch')
        for row in json.loads((old/'results.json').read_text()):
            row=dict(row,imported_from=str(old.relative_to(ROOT)))
            results.append(row);completed.add((row['case'],row['seed'],row['variant']))
        dump(dest/'results.json',results)

    def run_block(affinity, block):
        case, seed = block
        labels = list(configs)
        random.Random(f'{case}:{seed}:{spec.get("order_seed",791)}').shuffle(labels)
        for label in labels:
            if (case,seed,label) in completed:continue
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
                   str(inp)]
            if 'checkpoints' in spec:
                inc=ROOT/spec['checkpoints'][case]
                assert sha(inc)==manifest['checkpoints'][case]
                cmd += [str(inc),str(out),str(seconds),str(config.get('mode',0))]
            else: cmd += [str(out),str(seconds)]
            started = time.time()
            start = time.monotonic()
            pending = list(sorted(spec.get('snapshots', [])))
            snaps, timedout = [], False
            hard_stopped=False;hard_stop_at=None;solver_pid=None
            with err.open('w') as log:
                proc = subprocess.Popen(cmd, env=env, stderr=log,
                    stdout=subprocess.DEVNULL, start_new_session=True)
                while proc.poll() is None:
                    elapsed = time.monotonic() - start
                    if spec.get('hard_wall') and solver_pid is None:
                        try:
                            children=Path(f'/proc/{proc.pid}/task/{proc.pid}/children').read_text().split()
                            if children:solver_pid=int(children[0])
                        except (OSError,ValueError):pass
                    if spec.get('hard_wall') and not hard_stopped and elapsed>=seconds-.01:
                        if solver_pid is not None:
                            try:os.kill(solver_pid,signal.SIGTERM);hard_stopped=True;hard_stop_at=elapsed
                            except ProcessLookupError:pass
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
                    time.sleep(.004 if spec.get('hard_wall') else .08)
                rc = proc.wait()
            wall = time.monotonic() - start
            ended = time.time()
            try: value = validate(inp, out)
            except Exception as exc: value = f'validator exception: {type(exc).__name__}: {exc}'
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
                'solution_sha256':sha(out) if out.exists() else None, 'source_sha256':manifest['sources'][label],
                'resource':resource.read_text() if resource.exists() else '', 'snapshots':snaps}
            row['hard_stopped']=hard_stopped;row['hard_stop_at']=hard_stop_at
            row['within_nominal_plus_0.1']=wall<=seconds+.1
            row['nominal_overrun']=max(0,wall-seconds)
            if spec.get('hard_wall'):
                watchdog_inferred=bool(config.get('internal_watchdog') and actual_nt is None and rc==0 and wall>=seconds-.3)
                row['watchdog_exit_inferred']=watchdog_inferred
                row['success']=rc==0 and not timedout and wall<=seconds+.1 and valid and not badlog and (actual_nt==2 or hard_stopped or watchdog_inferred)
                row['thread_count_basis']='final log' if actual_nt is not None else 'NT=2 env; final log absent at budget stop'
            dump(prefix.with_suffix('.json'), row)
            with guard:
                results.append(row)
                dump(dest/'results.json', results)
                print(len(results),len(blocks)*len(labels),case,seed,label,
                      round(row['objective'] or 0,6),row['success'],flush=True)

    def worker(index):
        affinity = pairs[index]
        os.sched_setaffinity(0, set(affinity))
        locks=[]
        for cpu in sorted(affinity):
            lock=open(f'/tmp/szo-perturbation-cpu{cpu}.lock','w'); fcntl.flock(lock,fcntl.LOCK_EX); locks.append(lock)
        try:
            for block in blocks[index::len(pairs)]: run_block(affinity,block)
        finally:
            for lock in locks: lock.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(pairs)) as executor:
        futures = [executor.submit(worker, i) for i in range(len(pairs))]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    dump(dest / 'COMPLETE.json', {'expected':len(blocks)*len(configs),
        'completed':len(results),'success':sum(r['success'] for r in results)})

if __name__ == '__main__':
    main()
