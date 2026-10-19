#!/usr/bin/env python3
"""Эталон для --suite: долгие прогоны (разные конфигурации и зёрна) по 46 инстансам suite.

Пишет results/local/ref/runs.csv (каждый прогон; решения — в out/) и поднимает results/local/suite_best.csv
(только вверх). Итог — на сколько эталон выше прежнего «лучшего известного» по классам.
  python3 tools/ref.py [--par 8] [--nt 2] [--scale 1.0] [--only huge0,anti2] [--report]
Повторный запуск пропускает прогоны, уже записанные в runs.csv.
"""
import argparse, csv, json, os, re, shutil, statistics, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "results/local/ref"
SUITE = ROOT / "results/local/suite"
SUITE_BEST = ROOT / "results/local/suite_best.csv"
RUNS = HERE / "runs.csv"
OUT = HERE / "out"
LOCK = threading.Lock()

# (имя, env, зерно); у малых — первые три
CONFIGS = [("default", {}, 101), ("tlevel", {"TLEVEL": "1"}, 102),
           ("exact2", {"EXACT2": "1"}, 103), ("default", {}, 104)]


def plan(n_sites):
    """(лимит, число конфигураций) по размеру."""
    if n_sites <= 600:
        return 600, 3
    if n_sites <= 3500:
        return 900, 4
    return 1800, 4


def sites_count(p):
    return len(json.loads(p.read_text())["sites"])


def build(exe):
    mk = (ROOT / "submission/cpp/Makefile").read_text()
    flags = re.search(r"g\+\+ (.*?) -o solution main\.cpp", mk).group(1).split()
    cxx = os.environ.get("CXX") or shutil.which("g++")
    subprocess.run([cxx, *flags, "-o", str(exe), str(ROOT / "solver/solve.cpp")], check=True)


def load_best():
    if not SUITE_BEST.exists():
        return {}
    return {r["instance"]: float(r["objective"]) for r in csv.DictReader(SUITE_BEST.open())}


def report():
    old = {}
    old_f = HERE / "suite_best_before.csv"
    if old_f.exists():
        old = {r["instance"]: float(r["objective"]) for r in csv.DictReader(old_f.open())}
    runs = list(csv.DictReader(RUNS.open())) if RUNS.exists() else []
    by = {}
    for r in runs:
        if r["objective"]:
            by.setdefault(r["instance"], []).append((float(r["objective"]), r["config"], r["seed"]))
    cls = {}
    print(f"{'инстанс':>12} {'прежнее':>14} {'эталон':>14} {'прежнее/эталон':>14}  кто")
    for k in sorted(by):
        ref, cfg, seed = max(by[k])
        ref = max(ref, old.get(k, ref))
        ratio = old[k] / ref if k in old and ref > 0 else 1.0
        cls.setdefault(k.rstrip("0123456789"), []).append(ratio)
        who = f"{cfg}/{seed}" if max(by[k])[0] > old.get(k, float("-inf")) else "прежнее"
        print(f"{k:>12} {old.get(k, float('nan')):>14.6g} {ref:>14.6g} {ratio:>14.4f}  {who}")
    print("\nкласс: среднее прежнее/эталон (1.0 — эталон не нашёл лучше)")
    for c in sorted(cls):
        print(f"{c:>12} {statistics.mean(cls[c]):.4f}  min {min(cls[c]):.4f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--par", type=int, default=8)
    ap.add_argument("--nt", type=int, default=2)
    ap.add_argument("--scale", type=float, default=1.0, help="множитель лимитов")
    ap.add_argument("--only", default="")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.report:
        return report()
    OUT.mkdir(parents=True, exist_ok=True)
    if SUITE_BEST.exists() and not (HERE / "suite_best_before.csv").exists():
        shutil.copy(SUITE_BEST, HERE / "suite_best_before.csv")
    exe = HERE / "solve"
    build(exe)
    vpy = str(ROOT / ".venv/bin/python")
    done = set()
    if RUNS.exists():
        done = {(r["instance"], r["config"], r["seed"]) for r in csv.DictReader(RUNS.open())}
    else:
        RUNS.write_text("instance,config,seed,tl,nt,objective,wall,msg\n")
    insts = {p.stem[6:]: p for p in sorted(SUITE.glob("suite_*.json"))}
    if a.only:
        insts = {k: v for k, v in insts.items() if k in a.only.split(",")}
    jobs = []
    for k, p in insts.items():
        tl, nc = plan(sites_count(p))
        for name, env, seed in CONFIGS[:nc]:
            if (k, name, str(seed)) not in done:
                jobs.append((tl * a.scale, k, p, name, env, seed))
    jobs.sort(key=lambda j: -j[0])   # длинные первыми — плотнее упаковка
    total = sum(j[0] for j in jobs) / max(1, min(a.par, len(jobs)))
    print(f"{len(jobs)} прогонов, ~{total / 3600:.1f} ч при par={a.par}", flush=True)

    def run(job):
        tl, k, p, name, env, seed = job
        out = OUT / f"{k}_{name}_{seed}.json"
        e = dict(os.environ, NT=str(a.nt), SEED=str(seed), **env)
        t0 = time.time()
        r = subprocess.run([str(exe), str(p), str(out), str(tl)], capture_output=True, text=True, env=e)
        wall = time.time() - t0
        lines = subprocess.run([vpy, "-I", str(ROOT / "task/validate_solution.py"), str(p), str(out)],
                               capture_output=True, text=True).stdout.strip().splitlines()
        ok = lines and lines[0] != "FAIL"
        obj = lines[-1] if ok else ""
        msg = "" if ok else (lines[-1] if lines else f"rc={r.returncode}")[:80].replace(",", ";")
        with LOCK:
            with RUNS.open("a") as fh:
                fh.write(f"{k},{name},{seed},{tl:g},{a.nt},{obj},{wall:.1f},{msg}\n")
            best = load_best()   # поднять suite_best (только вверх)
            if ok and float(obj) > best.get(k, float("-inf")):
                best[k] = float(obj)
                tmp = SUITE_BEST.with_suffix(".tmp")
                with tmp.open("w", newline="") as fh:
                    w = csv.writer(fh)
                    w.writerow(["instance", "objective"])
                    for kk in sorted(best):
                        w.writerow([kk, repr(best[kk])])
                tmp.replace(SUITE_BEST)
        print(f"{time.strftime('%H:%M')} {k} {name}/{seed} {obj or msg} {wall:.0f}s", flush=True)

    with ThreadPoolExecutor(min(a.par, max(1, len(jobs)))) as ex:
        list(ex.map(run, jobs))
    report()


if __name__ == "__main__":
    main()
